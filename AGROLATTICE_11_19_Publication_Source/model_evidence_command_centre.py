"""AGROLATTICE 11.15 Model Evidence Command Centre.

Scientific-governance workspace connecting datasets, persistent training runs,
immutable model versions, held-out validation, uncertainty/calibration,
explainability, applicability, benchmark evidence, predictions and outcomes.

The overview is intentionally lightweight. Model fitting, artifact loading,
permutation importance and benchmark execution occur only after explicit user
requests.
"""
from __future__ import annotations

import io
import json
import math
import zipfile
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import joblib
import numpy as np
import pandas as pd
import streamlit as st

from agricultural_validation import classification_metrics, regression_metrics
from navigation_state import consume_view_request, queue_view_request
from research_benchmarks import BENCHMARKS, benchmark_catalog, inspect_local_table
from research_registry import MODEL_STATUSES, ResearchEvidenceRegistry, ResearchRegistryError, json_value, sha256_file

MODULE_VERSION = "1.0.0"

VIEWS = [
    "Overview",
    "Models",
    "Training",
    "Validation",
    "Uncertainty & calibration",
    "Explainability",
    "Comparison & ensembles",
    "Benchmarks & transferability",
    "Evidence & reproducibility",
]


def _loads(value: Any, default: Any = None) -> Any:
    return json_value(value, default)


def _age_days(value: Any) -> float | None:
    stamp = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(stamp):
        return None
    return max(0.0, (pd.Timestamp.now(tz="UTC") - stamp).total_seconds() / 86400.0)


def _resolve_artifact(app_root: Path, model: Mapping[str, Any], version: Mapping[str, Any] | None = None) -> Path | None:
    raw = (version or {}).get("artifact_path") or model.get("artifact_path")
    if not raw:
        return None
    path = Path(str(raw))
    if not path.is_absolute():
        path = app_root / path
    return path


def _model_label(models: pd.DataFrame, model_id: str) -> str:
    row = models.loc[models["model_id"].astype(str).eq(str(model_id))]
    if row.empty:
        return str(model_id)[:8]
    r = row.iloc[0]
    return f"{r.get('name')} · {r.get('status')} · {str(model_id)[:8]}"


def _queue(view: str, notice: str | None = None) -> None:
    queue_view_request(
        st.session_state,
        request_key="model_evidence_view_request_11_14",
        target=view,
        notice_key="model_evidence_navigation_notice_11_14",
        notice=notice,
    )
    st.rerun()


def _context_predictions(registry: ResearchEvidenceRegistry, active_field_id: str | None, active_trial_id: str | None) -> pd.DataFrame:
    if active_trial_id:
        return registry.predictions(trial_id=str(active_trial_id), limit=10000)
    if active_field_id:
        return registry.predictions(field_id=str(active_field_id), limit=10000)
    return registry.predictions(limit=10000)


def _validation_summary(registry: ResearchEvidenceRegistry) -> pd.DataFrame:
    runs = registry.validation_runs(limit=10000)
    if runs.empty:
        return runs
    rows = []
    for _, run in runs.iterrows():
        metrics = _loads(run.get("metrics_json"), {}) or {}
        rows.append({
            "validation_id": run.get("validation_id"),
            "model_id": run.get("model_id"),
            "validation_type": run.get("validation_type"),
            "evidence_level": run.get("evidence_level"),
            "primary_metric": run.get("primary_metric"),
            "status": run.get("status"),
            "created_at": run.get("created_at"),
            **{str(k): v for k, v in metrics.items() if isinstance(v, (int, float, str, bool))},
        })
    return pd.DataFrame(rows)


def _priority_gaps(registry: ResearchEvidenceRegistry, models: pd.DataFrame, predictions: pd.DataFrame) -> list[dict[str, str]]:
    gaps: list[dict[str, str]] = []
    validations = registry.validation_runs(limit=10000)
    links = registry.prediction_outcome_links(limit=10000)
    if models.empty:
        return [{"title": "No registered research models", "detail": "Train a baseline model against measured outcomes before creating operational predictions.", "view": "Training"}]
    for _, model in models.head(50).iterrows():
        model_id = str(model["model_id"])
        mruns = validations.loc[validations["model_id"].astype(str).eq(model_id)] if not validations.empty else pd.DataFrame()
        name = str(model.get("name") or model_id[:8])
        status = str(model.get("status") or "Prototype")
        if mruns.empty:
            gaps.append({"title": f"{name} has no persistent validation run", "detail": "The model may have transient metrics, but no auditable held-out validation evidence is saved in the registry.", "view": "Validation"})
        else:
            levels = mruns["evidence_level"].astype(str).str.casefold()
            types = mruns["validation_type"].astype(str).str.casefold()
            external = bool(levels.str.contains("external|independent|cross-season|cross-site").any() or types.str.contains("loyo|loro|leave-one|cross-season|cross-site|external|unseen").any())
            if status in {"Internally validated", "Prototype"} and not external:
                gaps.append({"title": f"{name} needs transfer validation", "detail": "Current evidence does not document an independent/cross-season/cross-site holdout.", "view": "Validation"})
        if not str(model.get("uncertainty_method") or "").strip() and not (_loads(model.get("calibration_json"), {}) or {}):
            gaps.append({"title": f"{name} has no documented uncertainty/calibration assessment", "detail": "Point accuracy alone is not enough for operational decision support.", "view": "Uncertainty & calibration"})
        if not (_loads(model.get("applicability_json"), {}) or {}):
            gaps.append({"title": f"{name} lacks an applicability profile", "detail": "The registry cannot explain when the model is extrapolating without a training-support profile.", "view": "Models"})
    if not predictions.empty:
        ood = predictions["applicability_status"].astype(str).str.casefold().str.contains("out|extrap|low") if "applicability_status" in predictions else pd.Series(False, index=predictions.index)
        if int(ood.sum()):
            gaps.insert(0, {"title": f"{int(ood.sum())} registered predictions may be outside training support", "detail": "Inspect applicability before using these outputs in Crop Decisions or field recommendations.", "view": "Models"})
    if not predictions.empty:
        matched_ids = set(links.get("prediction_id", pd.Series(dtype=str)).astype(str)) if not links.empty else set()
        unmatched = predictions.loc[~predictions["prediction_id"].astype(str).isin(matched_ids)]
        if not unmatched.empty:
            gaps.append({"title": f"{len(unmatched)} prediction(s) have no linked measured outcome", "detail": "As outcomes arrive, link them to predictions so model drift and real deployment error can be measured.", "view": "Validation"})
    # De-duplicate similar messages and keep the command centre concise.
    unique=[]; seen=set()
    for item in gaps:
        key=(item["title"], item["view"])
        if key not in seen:
            unique.append(item); seen.add(key)
    return unique[:7]


def _render_overview(registry: ResearchEvidenceRegistry, models: pd.DataFrame, predictions: pd.DataFrame, active_field_id: str | None, active_trial_id: str | None) -> None:
    validations = registry.validation_runs(limit=10000)
    training = registry.training_runs()
    links = registry.prediction_outcome_links(limit=10000)
    operational = int(models["status"].astype(str).eq("Operationally eligible").sum()) if not models.empty else 0
    external = 0
    if not validations.empty:
        level = validations["evidence_level"].astype(str).str.casefold()
        vtype = validations["validation_type"].astype(str).str.casefold()
        external = int((level.str.contains("external|independent|cross-site|cross-season") | vtype.str.contains("loro|loyo|leave-one|external|cross-site|cross-season|unseen")).sum())
    ood = 0
    if not predictions.empty and "applicability_status" in predictions:
        ood = int(predictions["applicability_status"].astype(str).str.casefold().str.contains("out|extrap|low").sum())
    cards = st.columns(4)
    cards[0].metric("Registered models", len(models), f"{operational} operationally eligible")
    cards[1].metric("Validation evidence", len(validations), f"{external} transfer/external run(s)")
    cards[2].metric("Predictions in scope", len(predictions), f"{ood} applicability warning(s)" if ood else "No OOD flag")
    unmatched = max(0, len(predictions) - len(set(links.get("prediction_id", pd.Series(dtype=str)).astype(str)))) if not predictions.empty else 0
    cards[3].metric("Outcome loop", len(links), f"{unmatched} prediction(s) awaiting outcome")

    scope = "Portfolio"
    if active_trial_id: scope = f"Active trial · {str(active_trial_id)[:8]}"
    elif active_field_id: scope = f"Active field · {str(active_field_id)[:8]}"
    st.caption(f"Evidence scope: **{scope}**. This page reads saved summaries only; it does not train models or execute benchmarks automatically.")

    st.markdown("### Priority evidence gaps")
    gaps = _priority_gaps(registry, models, predictions)
    if not gaps:
        st.success("No obvious governance gap is flagged by the lightweight rules. This does not establish external validity or causal usefulness.")
    for idx, gap in enumerate(gaps, 1):
        left,right=st.columns([8,2])
        with left:
            st.markdown(f"**{idx}. {gap['title']}**")
            st.caption(gap["detail"])
        with right:
            if st.button(f"Open {gap['view']}", key=f"model_evidence_gap_{idx}", width="stretch"):
                _queue(gap["view"], gap["title"])
        if idx < len(gaps): st.divider()

    st.markdown("### Evidence matrix")
    if models.empty:
        st.info("No models registered yet.")
        return
    matrix=[]
    for _,m in models.iterrows():
        mid=str(m["model_id"]); vr=validations.loc[validations["model_id"].astype(str).eq(mid)] if not validations.empty else pd.DataFrame()
        types=" · ".join(vr["validation_type"].astype(str).drop_duplicates().head(3).tolist()) if not vr.empty else "—"
        matrix.append({
            "Model": m.get("name"), "Target": m.get("target"), "Status": m.get("status"),
            "Validation runs": len(vr), "Validation scope": types,
            "Uncertainty": "Yes" if str(m.get("uncertainty_method") or "").strip() else "No",
            "Applicability": "Yes" if (_loads(m.get("applicability_json"), {}) or {}) else "No",
            "Training runs": int(training["model_id"].astype(str).eq(mid).sum()) if not training.empty and "model_id" in training else 0,
        })
    st.dataframe(pd.DataFrame(matrix), hide_index=True, width="stretch")


def _filtered_models(models: pd.DataFrame) -> pd.DataFrame:
    if models.empty: return models
    cols=st.columns(4)
    statuses=["All"]+sorted(models["status"].dropna().astype(str).unique().tolist())
    families=["All"]+sorted(models["family"].dropna().astype(str).unique().tolist())
    targets=["All"]+sorted(models["target"].dropna().astype(str).unique().tolist())
    status=cols[0].selectbox("Status", statuses, key="me_model_status_filter")
    family=cols[1].selectbox("Family", families, key="me_model_family_filter")
    target=cols[2].selectbox("Target", targets, key="me_model_target_filter")
    text=cols[3].text_input("Search", key="me_model_text_filter")
    out=models.copy()
    if status!="All": out=out.loc[out["status"].astype(str).eq(status)]
    if family!="All": out=out.loc[out["family"].astype(str).eq(family)]
    if target!="All": out=out.loc[out["target"].astype(str).eq(target)]
    if text.strip():
        mask=out[[c for c in ["name","family","target","source_method"] if c in out]].astype(str).agg(" ".join,axis=1).str.contains(text.strip(),case=False,regex=False)
        out=out.loc[mask]
    return out


def _render_models(registry: ResearchEvidenceRegistry, app_root: Path) -> None:
    st.markdown("### Models · registry & evidence ladder")
    models=_filtered_models(registry.models())
    if models.empty:
        st.info("No models match the current filters.")
        return
    display=models[[c for c in ["model_id","name","family","target","task_type","status","uncertainty_method","code_version","updated_at"] if c in models]].copy()
    st.dataframe(display, hide_index=True, width="stretch")
    selected=st.selectbox("Inspect model", models["model_id"].astype(str).tolist(), format_func=lambda x:_model_label(models,x), key="me_model_selected")
    model=registry.model(selected) or {}
    versions=registry.model_versions(selected)
    validations=registry.validation_runs(model_id=selected)
    training=registry.training_runs(model_id=selected)
    history=registry.model_status_history(selected)
    health=registry.model_health_events(selected)
    detail=st.radio("Model detail", ["Summary","Validation","Versions & artifact","Applicability & drift","Status & health","Predictions","Advanced provenance"], horizontal=True, key="me_model_detail")

    if detail=="Summary":
        c1,c2,c3,c4=st.columns(4)
        c1.metric("Status", model.get("status") or "—")
        c2.metric("Validation runs", len(validations))
        c3.metric("Versions", len(versions))
        c4.metric("Predictions", len(registry.predictions(model_id=selected,limit=100000)))
        st.markdown(f"**Purpose/target:** {model.get('target')} · {model.get('task_type')}")
        st.markdown(f"**Method:** {model.get('source_method') or 'AGROLATTICE model'}")
        st.markdown(f"**Implementation relationship:** {model.get('implementation_type') or 'not documented'}")
        if model.get("source_citation"): st.caption(f"Source citation: {model.get('source_citation')}")
        features=_loads(model.get("feature_names_json"),[]) or []
        st.markdown("**Features:** "+(", ".join(map(str,features)) if features else "not documented"))
        limits=_loads(model.get("limitations_json"),[]) or []
        if limits:
            st.markdown("**Known limitations**")
            for item in limits: st.markdown(f"- {item}")
        if model.get("source_citation") or model.get("source_method"):
            with st.expander("Compare with source method / paper", expanded=False):
                st.markdown(f"**Source method:** {model.get('source_method') or 'not documented'}")
                st.markdown(f"**Citation:** {model.get('source_citation') or 'not documented'}")
                st.markdown(f"**AGROLATTICE relationship:** {model.get('implementation_type') or 'not documented'}")
                st.caption("A citation does not imply exact reproduction. Check the implementation relationship, validation protocol, data availability and limitations before comparing performance with a source publication.")
        app=_loads(model.get("applicability_json"),{}) or {}
        if app:
            with st.expander("Applicability profile", expanded=False): st.json(app)
    elif detail=="Validation":
        if validations.empty: st.warning("No persistent validation evidence saved for this model.")
        else:
            st.dataframe(_validation_summary(registry).loc[lambda d:d["model_id"].astype(str).eq(selected)], hide_index=True, width="stretch")
            run_id=st.selectbox("Inspect validation run", validations["validation_id"].astype(str).tolist(), key="me_validation_inspect")
            row=validations.loc[validations["validation_id"].astype(str).eq(run_id)].iloc[0]
            with st.expander("Split, leakage guards and fold metrics",expanded=True):
                st.json({"split_manifest":_loads(row.get("split_manifest_json"),[]),"leakage_guards":_loads(row.get("leakage_guards_json"),{}),"fold_metrics":_loads(row.get("fold_metrics_json"),[])})
    elif detail=="Versions & artifact":
        st.dataframe(versions,hide_index=True,width="stretch") if not versions.empty else st.info("No immutable model version has been registered yet; legacy models remain readable.")
        version=versions.iloc[0].to_dict() if not versions.empty else None
        artifact=_resolve_artifact(app_root,model,version)
        expected=(version or {}).get("artifact_sha256") if version else None
        if artifact and artifact.exists():
            actual=sha256_file(artifact)
            st.success(f"Artifact available · {artifact.name}")
            st.code(actual)
            if expected and actual!=expected: st.error("Artifact hash does not match the immutable model-version record. Do not load this model until the discrepancy is resolved.")
            elif expected: st.caption("Artifact SHA-256 verified against the registered version.")
        else: st.warning("Registered model artifact is unavailable at the stored path.")
        if version:
            with st.expander("Feature contract",expanded=False): st.json(_loads(version.get("feature_contract_json"),{}))
            with st.expander("Computational environment",expanded=False): st.json(_loads(version.get("environment_json"),{}))
    elif detail=="Applicability & drift":
        profile=_loads(model.get("applicability_json"),{}) or {}
        if profile:
            st.markdown("#### Training-support / applicability profile")
            st.json(profile)
        else:
            st.warning("No applicability profile is documented. New predictions cannot be defensibly labelled as interpolation versus extrapolation.")
        pred=registry.predictions(model_id=selected,limit=100000)
        if pred.empty:
            st.info("No registered predictions are available for applicability/drift monitoring.")
        else:
            status=pred.get("applicability_status",pd.Series(index=pred.index,dtype=str)).astype(str)
            ood=status.str.casefold().str.contains("out|extrap|low")
            c1,c2,c3=st.columns(3)
            c1.metric("Predictions",len(pred)); c2.metric("OOD / extrapolation flags",int(ood.sum())); c3.metric("OOD share",f"{float(ood.mean()):.1%}" if len(ood) else "—")
            cols=[c for c in ["generated_at","field_id","trial_id","season_year","target","prediction","prediction_text","applicability_status","applicability_score"] if c in pred]
            st.dataframe(pred[cols].head(2000),hide_index=True,width="stretch")
            links=registry.prediction_outcome_links(model_id=selected,limit=100000)
            numeric=links.loc[pd.to_numeric(links.get("observed_value"),errors="coerce").notna() & pd.to_numeric(links.get("prediction"),errors="coerce").notna()].copy() if not links.empty else pd.DataFrame()
            if not numeric.empty:
                numeric["Observed"]=pd.to_numeric(numeric["observed_value"],errors="coerce"); numeric["Predicted"]=pd.to_numeric(numeric["prediction"],errors="coerce")
                numeric["Absolute error"]=(numeric["Predicted"]-numeric["Observed"]).abs()
                recent=numeric.sort_values("matched_at").tail(min(50,len(numeric)))
                earlier=numeric.sort_values("matched_at").head(max(1,len(numeric)-len(recent))) if len(numeric)>len(recent) else pd.DataFrame()
                st.markdown("#### Outcome-linked deployment error")
                st.metric("Matched measured outcomes",len(numeric),f"Recent MAE {recent['Absolute error'].mean():.3g}")
                if not earlier.empty:
                    base=float(earlier["Absolute error"].mean()); current=float(recent["Absolute error"].mean())
                    delta=current-base
                    st.caption(f"Earlier linked MAE {base:.3g} · recent linked MAE {current:.3g} · change {delta:+.3g}. This is a monitoring diagnostic, not proof of temporal drift.")
                    if base>0 and current>base*1.25 and len(recent)>=10:
                        st.warning("Recent linked error is >25% above the earlier linked error. Review covariate shift, data quality and recalibration before calling this model stable.")
    elif detail=="Status & health":
        current=str(model.get("status") or "Prototype")
        desired=st.selectbox("Requested evidence status",MODEL_STATUSES,index=MODEL_STATUSES.index(current) if current in MODEL_STATUSES else 0,key="me_status_target")
        gate=registry.promotion_requirements(selected,desired)
        gate_df=pd.DataFrame(gate["requirements"])
        if not gate_df.empty: st.dataframe(gate_df.rename(columns={"requirement":"Evidence requirement","met":"Met"}),hide_index=True,width="stretch")
        rationale=st.text_area("Rationale / evidence interpretation",key="me_status_rationale")
        override=st.checkbox("Research-governance override (record permanently)",value=False,key="me_status_override")
        if override: st.warning("An override does not create missing validation evidence. It only records a human governance exception.")
        if st.button("Apply auditable status change",disabled=desired==current,key="me_status_apply"):
            try:
                registry.change_model_status(selected,desired,rationale=rationale,override=override,evidence={"app_version":"11.15"})
                st.success("Model status changed and appended to the audit history."); st.rerun()
            except Exception as error: st.error(str(error))
        st.markdown("#### Status history")
        st.dataframe(history[[c for c in ["changed_at","old_status","new_status","rationale","override_used"] if c in history]],hide_index=True,width="stretch") if not history.empty else st.caption("No post-11.15 status event recorded yet.")
        st.markdown("#### Model health")
        st.dataframe(health,hide_index=True,width="stretch") if not health.empty else st.caption("No drift/health event recorded.")
        with st.expander("Record model-health evidence",expanded=False):
            hs=st.selectbox("Health status",["Stable","Monitoring","Drift suspected","Recalibration recommended","Retraining recommended","Retired"],key="me_health_status")
            hc1,hc2,hc3=st.columns(3)
            metric_name=hc1.text_input("Monitoring metric (optional)",key="me_health_metric")
            metric_value=hc2.number_input("Current value",value=None,key="me_health_value")
            threshold=hc3.number_input("Review threshold",value=None,key="me_health_threshold")
            note=st.text_area("Evidence note",key="me_health_note")
            if st.button("Save health event",key="me_health_save"):
                registry.save_model_health_event({"model_id":selected,"health_status":hs,"metric_name":metric_name or None,"metric_value":metric_value,"threshold":threshold,"evidence":{"source":"Researcher review"},"note":note}); st.success("Health event saved."); st.rerun()
    elif detail=="Predictions":
        pred=registry.predictions(model_id=selected,limit=10000)
        st.dataframe(pred,hide_index=True,width="stretch") if not pred.empty else st.info("No registered predictions for this model.")
    else:
        card=registry.export_model_card(selected)
        st.json(card)
        st.download_button("Download model card JSON",json.dumps(card,indent=2,default=str),file_name=f"AGROLATTICE_model_card_{selected[:8]}.json",mime="application/json")


def _paired_from_registered(registry: ResearchEvidenceRegistry, model: Mapping[str,Any]) -> tuple[pd.DataFrame,list[dict[str,Any]]]:
    mid=str(model["model_id"]); target=str(model.get("target") or "")
    pred=registry.predictions(model_id=mid,limit=100000)
    obs=registry.observations(limit=100000)
    matches=[]; rows=[]
    if pred.empty or obs.empty: return pd.DataFrame(),matches
    obs=obs.loc[obs["variable"].astype(str).str.casefold().eq(target.casefold())].copy()
    if obs.empty: return pd.DataFrame(),matches
    obs["_observed_at"] = pd.to_datetime(obs.get("observed_at"),errors="coerce",utc=True)
    existing_links=registry.prediction_outcome_links(model_id=mid,limit=100000)
    existing_pairs={(str(r.get("prediction_id")),str(r.get("observation_id"))) for _,r in existing_links.iterrows()} if not existing_links.empty else set()
    for _,p in pred.iterrows():
        cand=obs.copy()
        # Prefer the narrowest spatial entity that can be resolved.
        entity_type=str(p.get("entity_type") or "").casefold(); entity_id=str(p.get("entity_id") or "")
        if "experimental" in entity_type and entity_id and "experimental_unit_id" in cand:
            hit=cand.loc[cand["experimental_unit_id"].astype(str).eq(entity_id)]
            if not hit.empty: cand=hit
        if p.get("trial_id") not in (None,"") and "trial_id" in cand:
            hit=cand.loc[cand["trial_id"].astype(str).eq(str(p.get("trial_id")))]
            if not hit.empty: cand=hit
        elif p.get("field_id") not in (None,"") and "field_id" in cand:
            hit=cand.loc[cand["field_id"].astype(str).eq(str(p.get("field_id")))]
            if not hit.empty: cand=hit
        elif not ("experimental" in entity_type and entity_id):
            continue
        # A prediction for a declared season should not silently attach to another year.
        season=p.get("season_year")
        if season not in (None,""):
            hit=cand.loc[cand["_observed_at"].dt.year.eq(int(season))]
            if not hit.empty: cand=hit
        cand=cand.sort_values([c for c in ["_observed_at","created_at"] if c in cand],ascending=False)
        if cand.empty: continue
        o=cand.iloc[0]
        observed=o.get("value_numeric") if pd.notna(o.get("value_numeric")) else o.get("value_text")
        predicted=p.get("prediction") if pd.notna(p.get("prediction")) else p.get("prediction_text")
        probabilities=_loads(p.get("class_probabilities_json"),{}) or {}
        generated=pd.to_datetime(p.get("generated_at"),errors="coerce",utc=True); observed_at=o.get("_observed_at")
        chronology="Unknown"
        if pd.notna(generated) and pd.notna(observed_at): chronology="Prospective order" if generated<=observed_at else "Prediction record generated after observation"
        rows.append({"Prediction ID":p.get("prediction_id"),"Observation ID":o.get("observation_id"),"Observed":observed,"Predicted":predicted,"Probabilities":probabilities or None,"Lower":p.get("lower_bound"),"Upper":p.get("upper_bound"),"Field":p.get("field_id"),"Trial":p.get("trial_id"),"Season":p.get("season_year"),"Prediction time":p.get("generated_at"),"Observation time":o.get("observed_at"),"Chronology":chronology})
        pair=(str(p.get("prediction_id")),str(o.get("observation_id")))
        if pair not in existing_pairs:
            matches.append({"prediction_id":p.get("prediction_id"),"observation_id":o.get("observation_id"),"observed_value":o.get("value_numeric"),"observed_text":o.get("value_text"),"unit":o.get("unit"),"matching_basis":"Canonical target + spatial context + season where available; latest matching observation","provenance":{"target":target,"chronology":chronology,"researcher_review_required":True}})
    return pd.DataFrame(rows),matches



def _compute_validation_metrics(paired: pd.DataFrame, task_type: str) -> dict[str,Any]:
    if paired.empty: return {}
    if str(task_type).casefold().startswith("class"):
        probability_rows=[]; classes=[]
        if "Probabilities" in paired:
            dicts=[]
            for value in paired["Probabilities"]:
                d=_loads(value,{}) if isinstance(value,str) else (value if isinstance(value,dict) else {})
                dicts.append(d or {}); classes.extend([str(k) for k in (d or {})])
            classes=sorted(set(classes))
            if classes and all(all(cls in d for cls in classes) for d in dicts):
                probability_rows=np.asarray([[float(d[cls]) for cls in classes] for d in dicts],dtype=float)
        if len(probability_rows):
            return classification_metrics(paired["Observed"].astype(str),paired["Predicted"].astype(str),probability_rows,classes)
        return classification_metrics(paired["Observed"],paired["Predicted"])
    return regression_metrics(paired["Observed"],paired["Predicted"])



def _render_validation(registry: ResearchEvidenceRegistry) -> None:
    st.markdown("### Validation · measured outcomes against registered predictions")
    models=registry.models()
    if models.empty: st.info("Register a model first."); return
    mid=st.selectbox("Model",models["model_id"].astype(str).tolist(),format_func=lambda x:_model_label(models,x),key="me_val_model")
    model=registry.model(mid) or {}
    existing=registry.validation_runs(model_id=mid)
    if not existing.empty:
        st.markdown("#### Existing validation evidence")
        st.dataframe(_validation_summary(registry).loc[lambda d:d["model_id"].astype(str).eq(mid)],hide_index=True,width="stretch")
    source=st.radio("New validation source",["Match registered predictions to canonical observations","Upload independent paired table"],horizontal=True,key="me_val_source")
    paired=pd.DataFrame(); matches=[]; uploaded=None
    if source.startswith("Match"):
        paired,matches=_paired_from_registered(registry,model)
        if paired.empty: st.info("No target-matched field/trial observations can currently be paired with this model's registered predictions.")
        else: st.dataframe(paired,hide_index=True,width="stretch")
    else:
        uploaded=st.file_uploader("Paired validation table",type=["csv","xlsx","xls","parquet"],key="me_val_upload")
        if uploaded:
            try:
                name=uploaded.name.lower(); raw=uploaded.getvalue()
                if name.endswith(".csv"): df=pd.read_csv(io.BytesIO(raw))
                elif name.endswith((".xlsx",".xls")): df=pd.read_excel(io.BytesIO(raw))
                else: df=pd.read_parquet(io.BytesIO(raw))
                oc=st.selectbox("Observed column",list(df.columns),key="me_val_obs_col")
                pc=st.selectbox("Predicted column",[c for c in df.columns if c!=oc],key="me_val_pred_col")
                lc=st.selectbox("Lower interval (optional)",["—"]+list(df.columns),key="me_val_low")
                uc=st.selectbox("Upper interval (optional)",["—"]+list(df.columns),key="me_val_up")
                paired=pd.DataFrame({"Observed":df[oc],"Predicted":df[pc]})
                if lc!="—": paired["Lower"]=df[lc]
                if uc!="—": paired["Upper"]=df[uc]
                if str(model.get("task_type")).casefold().startswith("class"):
                    candidate_prob=[c for c in df.columns if c not in {oc,pc} and (str(c).startswith("P(class=") or str(c).startswith("prob_"))]
                    prob_cols=st.multiselect("Class-probability columns (optional; names should encode class labels)",list(df.columns),default=candidate_prob,key="me_val_prob_cols")
                    if prob_cols:
                        def _prob_label(col):
                            s=str(col)
                            return s[len("P(class="):-1] if s.startswith("P(class=") and s.endswith(")") else (s[len("prob_"):] if s.startswith("prob_") else s)
                        paired["Probabilities"]=[{_prob_label(c):float(row[c]) for c in prob_cols if pd.notna(row[c])} for _,row in df.iterrows()]
                st.dataframe(paired.head(500),hide_index=True,width="stretch")
            except Exception as error: st.error(str(error)); paired=pd.DataFrame()
    if paired.empty: return
    if "Chronology" in paired and paired["Chronology"].astype(str).str.contains("after observation",case=False).any():
        st.warning("Some prediction records were generated after the matched observation. They may be retrospective validation records rather than prospective forecasts; do not interpret them as deployment performance without reviewing provenance.")
    metrics=_compute_validation_metrics(paired,str(model.get("task_type")))
    st.markdown("#### Performance")
    st.dataframe(pd.DataFrame([metrics]),hide_index=True,width="stretch")
    if str(model.get("task_type")).casefold().startswith("class"):
        try:
            confusion=pd.crosstab(paired["Observed"].astype(str),paired["Predicted"].astype(str),rownames=["Observed"],colnames=["Predicted"],dropna=False)
            st.markdown("##### Confusion matrix"); st.dataframe(confusion,width="stretch")
        except Exception: pass
    if {"Lower","Upper"}.issubset(paired.columns):
        o=pd.to_numeric(paired["Observed"],errors="coerce"); lo=pd.to_numeric(paired["Lower"],errors="coerce"); up=pd.to_numeric(paired["Upper"],errors="coerce")
        valid=o.notna()&lo.notna()&up.notna()
        if valid.any():
            coverage=float(((o[valid]>=lo[valid])&(o[valid]<=up[valid])).mean())
            width=float((up[valid]-lo[valid]).mean())
            st.caption(f"Empirical interval coverage: **{coverage:.1%}** · mean width **{width:.3g}**. Coverage is evidence; the nominal interval label alone is not.")
    level=st.selectbox("Evidence level",["Diagnostic","Internal cross-validation","Cross-season","Cross-site","Unseen genotype/parent pair","Independent external","Benchmark"],key="me_val_level")
    primary=st.text_input("Primary metric declared for this validation",value="RMSE" if str(model.get("task_type")).casefold().startswith("reg") else "Macro F1",key="me_val_primary")
    note=st.text_area("Validation notes / independence statement",key="me_val_notes")
    if st.button("Save validation evidence",type="primary",key="me_val_save"):
        validation_id=registry.save_validation_run({"model_id":mid,"dataset_id":None,"validation_type":source,"evidence_level":level,"primary_metric":primary,"metrics":metrics,"fold_metrics":[],"predictions":paired.to_dict(orient="records"),"split_manifest":{"source":source},"calibration":{},"uncertainty":{},"applicability":{},"leakage_guards":{"independent_pairing_declared":level not in {"Diagnostic"}},"status":"Completed","notes":note})
        for match in matches:
            try: registry.save_prediction_outcome_link(match)
            except Exception: pass
        st.success(f"Validation evidence saved · {validation_id[:8]}. Model status is not changed automatically."); st.rerun()


def _render_uncertainty(registry: ResearchEvidenceRegistry) -> None:
    st.markdown("### Uncertainty & calibration")
    models=registry.models()
    if models.empty: st.info("No models registered."); return
    mid=st.selectbox("Model",models["model_id"].astype(str).tolist(),format_func=lambda x:_model_label(models,x),key="me_unc_model")
    model=registry.model(mid) or {}
    runs=registry.validation_runs(model_id=mid)
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Declared uncertainty",str(model.get("uncertainty_method") or "None"))
    c2.metric("Calibration metadata","Yes" if (_loads(model.get("calibration_json"),{}) or {}) else "No")
    c3.metric("Validation runs",len(runs))
    c4.metric("Applicability profile","Yes" if (_loads(model.get("applicability_json"),{}) or {}) else "No")
    st.caption("AGROLATTICE keeps measurement/data uncertainty, parameter uncertainty, aleatoric uncertainty, epistemic/model disagreement, conformal intervals and OOD/applicability distinct. A heuristic confidence score is not substituted for a calibrated interval.")
    if runs.empty: return
    rid=st.selectbox("Validation run",runs["validation_id"].astype(str).tolist(),key="me_unc_run")
    run=runs.loc[runs["validation_id"].astype(str).eq(rid)].iloc[0]
    preds=pd.DataFrame(_loads(run.get("predictions_json"),[]) or [])
    uncertainty=_loads(run.get("uncertainty_json"),{}) or {}
    if str(model.get("task_type")).casefold().startswith("reg") and not preds.empty and {"Observed","Predicted"}.issubset(preds.columns):
        half=uncertainty.get("half_width_90")
        if half not in (None,""):
            o=pd.to_numeric(preds["Observed"],errors="coerce"); p=pd.to_numeric(preds["Predicted"],errors="coerce"); valid=o.notna()&p.notna()
            if valid.any():
                coverage=float(((o[valid]>=p[valid]-float(half))&(o[valid]<=p[valid]+float(half))).mean())
                st.metric("Empirical OOF coverage of stored 90% half-width",f"{coverage:.1%}")
                if coverage<0.85: st.warning("Coverage is materially below 90%; recalibration or a different uncertainty method should be considered.")
    elif str(model.get("task_type")).casefold().startswith("class") and not preds.empty and "Probabilities" in preds:
        # Binary reliability summary where fold predictions contain probability dictionaries.
        probs=[]; truths=[]
        for _,row in preds.iterrows():
            d=row.get("Probabilities")
            if isinstance(d,str): d=_loads(d,{})
            if isinstance(d,dict) and len(d)==2:
                labels=list(d); positive=labels[-1]
                probs.append(float(d[positive])); truths.append(float(str(row.get("Observed"))==positive))
        if probs:
            cal=pd.DataFrame({"p":probs,"y":truths}); cal["bin"]=pd.cut(cal["p"],bins=np.linspace(0,1,6),include_lowest=True)
            table=cal.groupby("bin",observed=False).agg(N=("y","size"),Mean_probability=("p","mean"),Observed_frequency=("y","mean")).reset_index()
            st.dataframe(table,hide_index=True,width="stretch")
            st.caption("Reliability bins are descriptive held-out evidence, not post-hoc recalibration of the deployed artifact.")
    with st.expander("Stored uncertainty/calibration/applicability provenance",expanded=False):
        st.json({"uncertainty":uncertainty,"calibration":_loads(run.get("calibration_json"),{}),"applicability":_loads(run.get("applicability_json"),{})})


def _render_explainability(registry: ResearchEvidenceRegistry, app_root: Path, callbacks: Mapping[str,Callable[[],None]]) -> None:
    st.markdown("### Explainability · predictive interpretation")
    models=registry.models()
    if models.empty: st.info("No models registered."); return
    mid=st.selectbox("Model",models["model_id"].astype(str).tolist(),format_func=lambda x:_model_label(models,x),key="me_xai_model")
    model=registry.model(mid) or {}; version=registry.latest_model_version(mid)
    st.warning("Feature importance, SHAP, PDP and permutation analyses describe predictive behaviour under the evaluated data distribution. They are not causal treatment effects.")
    feature_contract=_loads((version or {}).get("feature_contract_json"),{}) or {}
    if feature_contract: st.dataframe(pd.DataFrame([{"Feature":k,**(v if isinstance(v,dict) else {"contract":v})} for k,v in feature_contract.items()]),hide_index=True,width="stretch")
    artifact=_resolve_artifact(app_root,model,version)
    if not artifact or not artifact.exists(): st.info("The model artifact is not available locally, so new explanation calculations cannot run."); return
    expected=(version or {}).get("artifact_sha256") if version else None
    if expected and sha256_file(artifact)!=expected: st.error("Artifact hash mismatch. Explainability is disabled to protect provenance."); return
    uploaded=st.file_uploader("Evaluation/explanation table",type=["csv","xlsx","xls","parquet"],key="me_xai_upload")
    if not uploaded:
        st.caption("Upload data only when existing registered/snapshot data are unavailable. The feature contract above defines expected inputs.")
        if callbacks.get("advanced_pest"): 
            if st.button("Open advanced pest SHAP workflow",key="me_xai_pest"): callbacks["advanced_pest"]()
        return
    try:
        raw=uploaded.getvalue(); name=uploaded.name.lower()
        frame=pd.read_csv(io.BytesIO(raw)) if name.endswith(".csv") else (pd.read_excel(io.BytesIO(raw)) if name.endswith((".xlsx",".xls")) else pd.read_parquet(io.BytesIO(raw)))
        features=_loads(model.get("feature_names_json"),[]) or []
        missing=[c for c in features if c not in frame]
        if missing: st.error("Missing model features: "+", ".join(missing)); return
        estimator=joblib.load(artifact)
        target_options=["—"]+[c for c in frame.columns if c not in features]
        target=st.selectbox("Measured outcome for permutation importance (optional)",target_options,key="me_xai_target")
        if target!="—" and st.button("Compute held-table permutation importance",key="me_xai_perm"):
            from sklearn.inspection import permutation_importance
            sample=frame.dropna(subset=[target]).head(5000)
            result=permutation_importance(estimator,sample[features],sample[target],n_repeats=8,random_state=42,n_jobs=-1)
            imp=pd.DataFrame({"Feature":features,"Importance mean":result.importances_mean,"Importance SD":result.importances_std}).sort_values("Importance mean",ascending=False)
            st.dataframe(imp,hide_index=True,width="stretch")
        numeric=[c for c in features if pd.to_numeric(frame[c],errors="coerce").notna().mean()>=0.95]
        if numeric:
            feature=st.selectbox("Partial-dependence feature",numeric,key="me_xai_pdp_feature")
            if st.button("Compute partial dependence",key="me_xai_pdp"):
                try:
                    from sklearn.inspection import partial_dependence
                    pdp=partial_dependence(estimator,frame[features].head(2000),[feature],kind="average")
                    grid=np.asarray(pdp.get("grid_values",pdp.get("values"))[0]); avg=np.asarray(pdp["average"])
                    values=avg[0] if avg.ndim>1 else avg
                    st.line_chart(pd.DataFrame({feature:grid,"Partial dependence":values}).set_index(feature))
                except Exception as error: st.error(f"Partial dependence unavailable for this estimator: {error}")
    except Exception as error: st.error(str(error))


def _latest_validation_predictions(registry: ResearchEvidenceRegistry, model_id: str) -> tuple[dict[str,Any]|None,pd.DataFrame]:
    runs=registry.validation_runs(model_id=model_id)
    if runs.empty: return None,pd.DataFrame()
    for _,row in runs.iterrows():
        data=_loads(row.get("predictions_json"),[]) or []
        if data:
            return row.to_dict(),pd.DataFrame(data)
    return None,pd.DataFrame()


def _render_comparison(registry: ResearchEvidenceRegistry, callbacks: Mapping[str,Callable[[],None]]) -> None:
    st.markdown("### Comparison & model disagreement")
    models=registry.models()
    if models.empty: st.info("No registered models."); return
    target=st.selectbox("Target",sorted(models["target"].dropna().astype(str).unique()),key="me_cmp_target")
    compatible=models.loc[models["target"].astype(str).eq(target)]
    selected=st.multiselect("Registered models",compatible["model_id"].astype(str).tolist(),format_func=lambda x:_model_label(compatible,x),key="me_cmp_models")
    if len(selected)<2: st.info("Select at least two models predicting the same target."); return
    manifests=[]; frames=[]
    for mid in selected:
        run,df=_latest_validation_predictions(registry,mid)
        if run is None or df.empty: continue
        manifests.append((mid,run)); frames.append((mid,df))
    if len(frames)<2: st.warning("At least two selected models need saved row-level validation predictions."); return
    # Valid pairing requires the same registered dataset and held-out row identifiers.
    dataset_ids={str((run or {}).get("dataset_id")) for _,run in manifests}
    if len(dataset_ids)>1:
        st.error("Selected models were validated on different registered datasets. AGROLATTICE will not manufacture a paired ensemble comparison."); return
    merged=None
    for mid,df in frames:
        if not {"Row","Observed","Predicted"}.issubset(df.columns): continue
        part=df[["Row","Observed","Predicted"]].rename(columns={"Predicted":str(mid)})
        merged=part if merged is None else merged.merge(part,on=["Row","Observed"],how="inner")
    if merged is None or merged.empty: st.error("No common held-out rows are available across the selected model validations."); return
    pred_cols=[str(mid) for mid in selected if str(mid) in merged]
    if len(pred_cols)<2: return
    numeric=merged[pred_cols].apply(pd.to_numeric,errors="coerce")
    merged["Model disagreement SD"]=numeric.std(axis=1,ddof=0)
    st.metric("Paired held-out rows",len(merged))
    st.dataframe(merged[["Row","Observed","Model disagreement SD"]+pred_cols].head(1000),hide_index=True,width="stretch")
    st.caption("Disagreement is evidence of model uncertainty/structural difference. It is not itself a calibrated prediction interval.")
    if str(compatible.loc[compatible["model_id"].astype(str).eq(selected[0]),"task_type"].iloc[0]).casefold().startswith("reg"):
        diag=merged.copy(); diag["Equal-weight diagnostic mean"]=numeric.mean(axis=1)
        metrics=regression_metrics(diag["Observed"],diag["Equal-weight diagnostic mean"])
        st.dataframe(pd.DataFrame([{"Diagnostic equal-weight OOF ensemble":True,**metrics}]),hide_index=True,width="stretch")
        st.warning("This equal-weight calculation is a diagnostic on already-held-out base predictions. It is not registered as a validated ensemble. Learned weights/stacking require a separate nested or out-of-fold meta-training design.")
    # Paired bootstrap differences quantify whether point-estimate model rankings are stable on the common held-out rows.
    reference=pred_cols[0]
    if len(merged)>=8:
        rng=np.random.default_rng(42); boot=[]
        observed_numeric=pd.to_numeric(merged["Observed"],errors="coerce")
        valid_obs=observed_numeric.notna()
        if valid_obs.sum()>=8:
            base_frame=merged.loc[valid_obs].reset_index(drop=True); obs=observed_numeric.loc[valid_obs].to_numpy(float)
            for other in pred_cols[1:]:
                refp=pd.to_numeric(base_frame[reference],errors="coerce").to_numpy(float); othp=pd.to_numeric(base_frame[other],errors="coerce").to_numpy(float)
                valid=np.isfinite(obs)&np.isfinite(refp)&np.isfinite(othp)
                if valid.sum()<8: continue
                oo,rr,qq=obs[valid],refp[valid],othp[valid]; deltas=[]
                for _ in range(1000):
                    ix=rng.integers(0,len(oo),len(oo))
                    rmse_r=float(np.sqrt(np.mean((rr[ix]-oo[ix])**2))); rmse_q=float(np.sqrt(np.mean((qq[ix]-oo[ix])**2)))
                    deltas.append(rmse_q-rmse_r)
                lo,med,hi=np.quantile(deltas,[0.025,0.5,0.975])
                boot.append({"Reference":reference,"Comparator":other,"ΔRMSE comparator-reference":float(np.mean(deltas)),"Bootstrap median":float(med),"95% CI low":float(lo),"95% CI high":float(hi)})
            if boot:
                st.markdown("##### Paired model-difference uncertainty")
                st.dataframe(pd.DataFrame(boot),hide_index=True,width="stretch")
                st.caption("Intervals are paired bootstrap diagnostics on the common held-out rows. A CI spanning zero indicates the observed ranking is not clearly separated on this evidence set.")
    if callbacks.get("legacy_ensemble"):
        with st.expander("Advanced legacy ensemble workbench",expanded=False):
            st.caption("Use only when its input alignment and weighting protocol are scientifically appropriate. Registry-native pairing above is preferred.")
            if st.button("Load advanced ensemble workbench",key="me_cmp_legacy"): callbacks["legacy_ensemble"]()


def _render_benchmarks(registry: ResearchEvidenceRegistry, app_root: Path, callbacks: Mapping[str,Callable[[],None]]) -> None:
    st.markdown("### Benchmarks & transferability")
    st.caption("AGROLATTICE never silently downloads large benchmark datasets. Verify size, licence and official split definitions before retrieval or redistribution.")
    st.dataframe(benchmark_catalog(),hide_index=True,width="stretch")
    models=registry.models()
    uploaded=st.file_uploader("Local benchmark/subset table",type=["csv","xlsx","xls","parquet"],key="me_bench_upload")
    if not uploaded or models.empty:
        runs=registry.benchmark_runs()
        if not runs.empty:
            st.markdown("#### Saved benchmark evidence"); st.dataframe(runs,hide_index=True,width="stretch")
        return
    raw=uploaded.getvalue(); name=uploaded.name.lower()
    frame=pd.read_csv(io.BytesIO(raw)) if name.endswith(".csv") else (pd.read_excel(io.BytesIO(raw)) if name.endswith((".xlsx",".xls")) else pd.read_parquet(io.BytesIO(raw)))
    inspection=inspect_local_table(frame)
    st.dataframe(pd.DataFrame([{"Rows":inspection["rows"],"Columns":inspection["columns"],**inspection["likely_columns"]}]),hide_index=True,width="stretch")
    benchmark=st.selectbox("Benchmark family",list(BENCHMARKS)+["Other external benchmark"],key="me_bench_family")
    split_status=st.selectbox("Reproduction status",["Official split reproduced","Approximate local subset","Schema-compatible but non-official split","Custom external holdout"],key="me_bench_status")
    mid=st.selectbox("Registered model",models["model_id"].astype(str).tolist(),format_func=lambda x:_model_label(models,x),key="me_bench_model")
    model=registry.model(mid) or {}; version=registry.latest_model_version(mid); artifact=_resolve_artifact(app_root,model,version)
    features=_loads(model.get("feature_names_json"),[]) or []
    missing=[c for c in features if c not in frame]
    target=str(model.get("target") or "")
    if target not in frame.columns: st.warning(f"Measured target column `{target}` is absent. This table can be registered as a snapshot but cannot score this model.")
    if missing: st.error("Benchmark table is missing model features: "+", ".join(missing)); return
    if not artifact or not artifact.exists(): st.error("Model artifact unavailable."); return
    expected=(version or {}).get("artifact_sha256") if version else None
    if expected and sha256_file(artifact)!=expected: st.error("Artifact hash mismatch; benchmark execution blocked."); return
    if st.button("Execute local benchmark evaluation",type="primary",key="me_bench_run",disabled=target not in frame.columns):
        try:
            estimator=joblib.load(artifact); pred=estimator.predict(frame[features]); paired=pd.DataFrame({"Observed":frame[target],"Predicted":pred})
            metrics=_compute_validation_metrics(paired,str(model.get("task_type")))
            dataset_id=registry.register_dataset({"name":f"{benchmark} · {uploaded.name}","dataset_type":"External benchmark snapshot","source":benchmark,"licence":"Verify upstream licence before redistribution","provenance":{"uploaded_filename":uploaded.name,"inspection":inspection,"reproduction_status":split_status},"notes":"Local benchmark execution; reproduction status declared by researcher."})
            run_id=registry.save_benchmark_run({"benchmark_name":benchmark,"model_id":mid,"dataset_id":dataset_id,"protocol":split_status,"settings":{"features":features,"target":target},"metrics":metrics,"applicability":{},"notes":"AGROLATTICE does not claim official reproduction unless the official split and preprocessing were actually followed."})
            st.success(f"Benchmark run saved · {run_id[:8]}"); st.dataframe(pd.DataFrame([metrics]),hide_index=True,width="stretch")
        except Exception as error: st.error(str(error))
    if callbacks.get("external_benchmark_legacy"):
        with st.expander("Benchmark metadata / legacy adapter",expanded=False):
            if st.button("Open metadata adapter",key="me_bench_legacy"): callbacks["external_benchmark_legacy"]()


def _repro_zip(registry: ResearchEvidenceRegistry, model_id: str, app_root: Path, include_artifact: bool) -> bytes:
    card=registry.export_model_card(model_id); model=registry.model(model_id) or {}; version=registry.latest_model_version(model_id)
    artifact=_resolve_artifact(app_root,model,version)
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("model_card.json",json.dumps(card,indent=2,default=str))
        z.writestr("training_runs.json",registry.training_runs(model_id=model_id).to_json(orient="records",indent=2))
        z.writestr("validation_runs.json",registry.validation_runs(model_id=model_id).to_json(orient="records",indent=2))
        z.writestr("model_versions.json",registry.model_versions(model_id).to_json(orient="records",indent=2))
        z.writestr("status_history.json",registry.model_status_history(model_id).to_json(orient="records",indent=2))
        z.writestr("prediction_outcome_links.json",registry.prediction_outcome_links(model_id=model_id).to_json(orient="records",indent=2))
        z.writestr("model_health_events.json",registry.model_health_events(model_id).to_json(orient="records",indent=2))
        dataset_id=model.get("training_dataset_id")
        if dataset_id: z.writestr("dataset_snapshots.json",registry.dataset_snapshots(dataset_id=dataset_id,limit=10000).to_json(orient="records",indent=2))
        z.writestr("README.txt","AGROLATTICE 11.15 reproducibility package. Evidence status reflects saved validation scope; predictive explanation is not causal evidence. Verify dataset and artifact licences before redistribution. Raw training data are not silently included.\n")
        if include_artifact and artifact and artifact.exists(): z.write(artifact,arcname=f"artifact/{artifact.name}")
    return buffer.getvalue()


def _render_evidence(registry: ResearchEvidenceRegistry, app_root: Path, callbacks: Mapping[str,Callable[[],None]]) -> None:
    st.markdown("### Evidence & reproducibility")
    sub=st.radio("Evidence view",["Evidence graph","Training runs","Datasets & snapshots","Reproducibility package","Decision/causal evidence","Advanced registry"],horizontal=True,key="me_evidence_sub")
    if sub=="Evidence graph":
        models=registry.models(); train=registry.training_runs(); vals=registry.validation_runs(limit=10000); pred=registry.predictions(limit=10000); rec=registry.recommendations(); out=registry.treatment_outcomes()
        edges=[]
        for _,r in train.iterrows():
            if r.get("dataset_id"): edges.append({"From":f"Dataset {str(r.get('dataset_id'))[:8]}","Relation":"trained","To":f"Model {str(r.get('model_id') or 'unregistered')[:8]}"})
        for _,r in vals.iterrows(): edges.append({"From":f"Model {str(r.get('model_id'))[:8]}","Relation":"validated by","To":f"Validation {str(r.get('validation_id'))[:8]}"})
        for _,r in pred.iterrows(): edges.append({"From":f"Model {str(r.get('model_id'))[:8]}","Relation":"generated","To":f"Prediction {str(r.get('prediction_id'))[:8]}"})
        for _,r in rec.iterrows():
            if r.get("prediction_id"): edges.append({"From":f"Prediction {str(r.get('prediction_id'))[:8]}","Relation":"informed","To":f"Recommendation {str(r.get('recommendation_id'))[:8]}"})
        for _,r in out.iterrows():
            if r.get("recommendation_id"): edges.append({"From":f"Recommendation {str(r.get('recommendation_id'))[:8]}","Relation":"followed by measured","To":f"Outcome {str(r.get('outcome_id'))[:8]}"})
        st.dataframe(pd.DataFrame(edges),hide_index=True,width="stretch") if edges else st.info("The evidence graph will populate as datasets, runs, models, predictions, recommendations and outcomes are linked.")
    elif sub=="Training runs":
        runs=registry.training_runs(); st.dataframe(runs,hide_index=True,width="stretch") if not runs.empty else st.info("No persistent training runs yet.")
        if not runs.empty:
            failed=runs.loc[~runs["status"].astype(str).str.casefold().eq("completed")]
            if not failed.empty: st.caption(f"{len(failed)} failed/non-completed run(s) are retained as scientific provenance rather than discarded.")
    elif sub=="Datasets & snapshots":
        datasets=registry.datasets(); st.dataframe(datasets,hide_index=True,width="stretch") if not datasets.empty else st.info("No datasets registered.")
        snaps=registry.dataset_snapshots(limit=2000); st.markdown("#### Immutable snapshots"); st.dataframe(snaps,hide_index=True,width="stretch") if not snaps.empty else st.caption("No dataset snapshot records yet.")
        if not datasets.empty:
            did=st.selectbox("Dataset to snapshot",datasets["dataset_id"].astype(str).tolist(),key="me_dataset_snapshot_id")
            row=datasets.loc[datasets["dataset_id"].astype(str).eq(did)].iloc[0]
            local=str(row.get("local_path") or "").strip(); p=Path(local) if local else None
            if p and not p.is_absolute(): p=app_root/p
            note=st.text_input("Snapshot name",value=f"{row.get('name')} · frozen manifest",key="me_dataset_snapshot_name")
            if st.button("Register immutable dataset snapshot manifest",key="me_dataset_snapshot_save"):
                registry.save_dataset_snapshot({"dataset_id":did,"name":note,"manifest":{"dataset":row.to_dict(),"scientific_note":"Snapshot manifest freezes provenance; raw bytes are only frozen if local_path/hash identify an immutable local file."},"local_path":str(p) if p and p.exists() else None,"sha256":sha256_file(p) if p and p.exists() and p.is_file() else row.get("sha256")})
                st.success("Dataset snapshot manifest saved."); st.rerun()
    elif sub=="Reproducibility package":
        models=registry.models()
        if models.empty: st.info("No model available."); return
        mid=st.selectbox("Model package",models["model_id"].astype(str).tolist(),format_func=lambda x:_model_label(models,x),key="me_repro_model")
        include=st.checkbox("Include local model artifact in ZIP",value=False,key="me_repro_include_artifact")
        payload=_repro_zip(registry,mid,app_root,include)
        st.download_button("Download reproducibility package",payload,file_name=f"AGROLATTICE_model_{mid[:8]}_reproducibility.zip",mime="application/zip")
        st.caption("Package contains model card, immutable versions, training runs, validation evidence, status history and prediction–outcome links. Raw training data are not silently redistributed.")
    elif sub=="Decision/causal evidence":
        if callbacks.get("decision_causal"): callbacks["decision_causal"]()
    else:
        if callbacks.get("registry_legacy"): callbacks["registry_legacy"]()


def render_model_evidence_command_centre(
    *,
    registry: ResearchEvidenceRegistry,
    app_root: str | Path,
    app_version: str,
    active_field_id: str | None = None,
    active_trial_id: str | None = None,
    callbacks: Mapping[str,Callable[[],None]] | None = None,
) -> None:
    callbacks=dict(callbacks or {}); app_root=Path(app_root)
    requested=consume_view_request(st.session_state,request_key="model_evidence_view_request_11_14",widget_key="model_evidence_view_radio_11_14",options=VIEWS,default="Overview",mirror_key="model_evidence_view_11_14")
    st.markdown("### Model Evidence Command Centre")
    st.caption("Scientific governance for model training, validation, calibration, applicability, prediction outcomes and reproducibility. Evidence status is auditable; promotion never creates missing evidence.")
    notice=st.session_state.pop("model_evidence_navigation_notice_11_14",None)
    if notice: st.info(f"Opened from evidence gap: {notice}")
    view=st.radio("Models & Evidence",VIEWS,index=VIEWS.index(requested),horizontal=True,key="model_evidence_view_radio_11_14",label_visibility="collapsed")
    st.session_state["model_evidence_view_11_14"]=view
    st.divider()

    models=registry.models()
    scope_options=["Portfolio"]
    if active_field_id: scope_options.append("Active field")
    if active_trial_id: scope_options.append("Active trial")
    scope=st.selectbox("Evidence scope",scope_options,key="model_evidence_scope_11_14",label_visibility="collapsed")
    scope_field=active_field_id if scope=="Active field" else None
    scope_trial=active_trial_id if scope=="Active trial" else None
    predictions=_context_predictions(registry,scope_field,scope_trial) if scope!="Portfolio" else registry.predictions(limit=10000)
    if view=="Overview": _render_overview(registry,models,predictions,scope_field,scope_trial)
    elif view=="Models": _render_models(registry,app_root)
    elif view=="Training":
        st.markdown("### Training sources & modelling templates")
        st.caption("Prefer analysis tables assembled from AGROLATTICE Fields / Experiments / Twins over re-uploading data the platform already owns. External tables remain supported when they are genuinely external.")
        cols=st.columns(5)
        shortcuts=[("Research Data Hub","data_hub"),("Cross-trial G×E×M","gxem"),("Multimodal fusion","multimodal"),("Mechanistic residual","hybrid"),("Weak supervision","weak_supervision")]
        for col,(label,key) in zip(cols,shortcuts):
            with col:
                if st.button(label,key=f"me_training_shortcut_{key}",width="stretch") and callbacks.get(key): callbacks[key]()
        st.divider()
        if callbacks.get("training"): callbacks["training"]()
    elif view=="Validation": _render_validation(registry)
    elif view=="Uncertainty & calibration": _render_uncertainty(registry)
    elif view=="Explainability": _render_explainability(registry,app_root,callbacks)
    elif view=="Comparison & ensembles": _render_comparison(registry,callbacks)
    elif view=="Benchmarks & transferability": _render_benchmarks(registry,app_root,callbacks)
    elif view=="Evidence & reproducibility": _render_evidence(registry,app_root,callbacks)
