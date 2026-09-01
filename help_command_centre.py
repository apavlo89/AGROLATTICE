"""AGROLATTICE 11.19 Help, onboarding and researcher-guidance command centre."""
from __future__ import annotations

from typing import Any, Callable, Mapping

import pandas as pd
import streamlit as st

from researcher_guidance import (
    EVIDENCE_TERMS, GLOSSARY, MODULE_VERSION as GUIDANCE_VERSION, REQUIREMENTS,
    TROUBLESHOOTING, WORKFLOWS, WORKSPACE_GUIDES, WORKSPACE_ORDER,
    readiness_rows, search_guidance, workflow_progress,
)

MODULE_VERSION = "1.0.0"


def _nonempty(frame: Any) -> bool:
    return isinstance(frame, pd.DataFrame) and not frame.empty


def _safe_frame(callable_obj: Callable[[], Any]) -> pd.DataFrame:
    try:
        value = callable_obj()
        return value if isinstance(value, pd.DataFrame) else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def _safe_record(callable_obj: Callable[[], Any]) -> Mapping[str, Any] | None:
    try:
        value = callable_obj()
        return value if isinstance(value, Mapping) else None
    except Exception:
        return None


def collect_guidance_state(
    *,
    context: Mapping[str, Any] | None,
    climate_dataset_ready: bool,
    field_db: Any = None,
    pollination_db: Any = None,
    twin_db: Any = None,
    research_registry: Any = None,
    reporting_db: Any = None,
    active_field_id: str | None = None,
    active_trial_id: str | None = None,
) -> dict[str, Any]:
    """Collect only small persisted summaries for onboarding/readiness.

    This function does not read the large country climate table, query NASA/STAC,
    run models or recompute the Twin.
    """
    context = dict(context or {})
    state: dict[str, Any] = {
        "country_dataset": bool(climate_dataset_ready),
        "research_context": any(str(context.get(k, "")).strip() not in {"", "Not selected", "None"} for k in ("Field", "Trial", "Project")),
        "mapped_field": False, "season": False, "trial": False, "trial_geometry": False,
        "observations": False, "twin": False, "weather": False, "eo": False,
        "root_zone": False, "analysis_data": False, "model": False, "validation": False,
        "outcomes": False, "report_evidence": False,
        "counts": {},
    }

    field = None
    if field_db is not None:
        fields = _safe_frame(lambda: field_db.fields())
        state["counts"]["fields"] = len(fields)
        if active_field_id:
            field = _safe_record(lambda: field_db.field(str(active_field_id)))
        if field:
            state["mapped_field"] = bool(str(field.get("geometry_json") or "").strip())
            state["season"] = bool(field.get("season_year") or str(field.get("crop") or "").strip())
            seasons = _safe_frame(lambda: field_db.seasons(str(active_field_id)))
            if _nonempty(seasons):
                state["season"] = True
        elif _nonempty(fields):
            # The installation contains mapped fields, but an active field is still
            # required for field-specific cross-workspace readiness.
            state["counts"]["mapped_fields_available"] = int(len(fields))

    trial = None
    if pollination_db is not None:
        trials = _safe_frame(lambda: pollination_db.list_trials())
        state["counts"]["trials"] = len(trials)
        state["trial"] = bool(active_trial_id or _nonempty(trials))
        if active_trial_id:
            trial = _safe_record(lambda: pollination_db.get_trial(str(active_trial_id)))
            if trial and not state["mapped_field"] and field_db is not None and trial.get("source_field_id"):
                linked_field = _safe_record(lambda: field_db.field(str(trial.get("source_field_id"))))
                if linked_field:
                    state["mapped_field"] = bool(str(linked_field.get("geometry_json") or "").strip())
                    state["season"] = state["season"] or bool(linked_field.get("season_year") or str(linked_field.get("crop") or "").strip())
            plots = _safe_frame(lambda: pollination_db.list_plots(str(active_trial_id)))
            state["trial_geometry"] = _nonempty(plots)
            observations = _safe_frame(lambda: pollination_db.observations(str(active_trial_id)))
            leaves = _safe_frame(lambda: pollination_db.leaf_observations(str(active_trial_id)))
            phenology = _safe_frame(lambda: pollination_db.phenology_events(str(active_trial_id)))
            harvest = _safe_frame(lambda: pollination_db.harvest(str(active_trial_id)))
            trial_weather = _safe_frame(lambda: pollination_db.weather(str(active_trial_id)))
            state["observations"] = any(_nonempty(x) for x in (observations, leaves, phenology))
            state["outcomes"] = _nonempty(harvest)
            state["weather"] = _nonempty(trial_weather)
            state["analysis_data"] = state["observations"] or state["outcomes"]
        elif _nonempty(trials):
            state["trial_geometry"] = False

    twin_link = None
    if twin_db is not None:
        links = _safe_frame(lambda: twin_db.links())
        state["counts"]["twins"] = len(links)
        if _nonempty(links):
            candidates = links.copy()
            if active_trial_id and "trial_id" in candidates:
                hit = candidates.loc[candidates["trial_id"].astype(str).eq(str(active_trial_id))]
                if not hit.empty:
                    twin_link = hit.iloc[0].to_dict()
            if twin_link is None and active_field_id and "field_id" in candidates:
                hit = candidates.loc[candidates["field_id"].astype(str).eq(str(active_field_id))]
                if not hit.empty:
                    twin_link = hit.iloc[0].to_dict()
            if twin_link is None and len(candidates) == 1:
                twin_link = candidates.iloc[0].to_dict()
        if twin_link:
            state["twin"] = True
            link_id = str(twin_link.get("link_id") or "")
            if link_id:
                state["weather"] = state["weather"] or bool(_safe_record(lambda: twin_db.weather_record(link_id)))
                state["eo"] = bool(_safe_record(lambda: twin_db.satellite_record(link_id)))
                state["root_zone"] = bool(_safe_record(lambda: twin_db.root_zone_record(link_id)))

    if research_registry is not None:
        models = _safe_frame(lambda: research_registry.models())
        validations = _safe_frame(lambda: research_registry.validation_runs(limit=20)) if hasattr(research_registry, "validation_runs") else pd.DataFrame()
        datasets = _safe_frame(lambda: research_registry.datasets())
        observations = _safe_frame(lambda: research_registry.observations(field_id=active_field_id, trial_id=active_trial_id, limit=50)) if hasattr(research_registry, "observations") else pd.DataFrame()
        acquisitions = _safe_frame(lambda: research_registry.data_acquisitions(field_id=active_field_id, limit=100)) if hasattr(research_registry, "data_acquisitions") else pd.DataFrame()
        outcomes = _safe_frame(lambda: research_registry.treatment_outcomes(field_id=active_field_id, trial_id=active_trial_id)) if hasattr(research_registry, "treatment_outcomes") else pd.DataFrame()
        state["counts"]["models"] = len(models)
        state["counts"]["validations"] = len(validations)
        state["model"] = _nonempty(models)
        state["validation"] = _nonempty(validations)
        state["analysis_data"] = state["analysis_data"] or _nonempty(datasets) or _nonempty(observations)
        state["outcomes"] = state["outcomes"] or _nonempty(outcomes)
        if _nonempty(acquisitions):
            cols = [c for c in ("source", "source_type") if c in acquisitions]
            text = acquisitions[cols].fillna("").astype(str).agg(" ".join, axis=1).str.casefold() if cols else pd.Series(dtype=str)
            state["weather"] = state["weather"] or bool(text.str.contains("nasa|weather", regex=True).any())
            state["eo"] = state["eo"] or bool(text.str.contains("sentinel|satellite|earth observation", regex=True).any())

    if reporting_db is not None:
        studies = _safe_frame(lambda: reporting_db.studies()) if hasattr(reporting_db, "studies") else pd.DataFrame()
        state["counts"]["reports"] = len(studies)
        state["report_evidence"] = _nonempty(studies) or state["analysis_data"] or state["outcomes"]
    else:
        state["report_evidence"] = state["analysis_data"] or state["outcomes"]

    return state


def _status_icon(status: str) -> str:
    return {"Ready": "✅", "Partial": "⚠️", "Missing": "○"}.get(status, "•")


def render_workspace_requirements_panel(
    workspace: str,
    state: Mapping[str, Any],
    *,
    open_workspace: Callable[[str], None] | None = None,
    open_tool: Callable[[str], None] | None = None,
    expanded: bool = False,
) -> None:
    """Consistent context-aware 'What do I need?' panel used by core workspaces."""
    guide = WORKSPACE_GUIDES.get(workspace)
    if not guide:
        return
    rows = readiness_rows(workspace, state)
    with st.expander("What do I need here?", expanded=expanded):
        st.caption(guide["purpose"])
        if rows:
            columns = st.columns(min(3, len(rows)))
            for idx, row in enumerate(rows):
                with columns[idx % len(columns)]:
                    st.markdown(f"**{_status_icon(row['status'])} {row['label']}**")
                    st.caption(row["why"])
                    if row["status"] != "Ready":
                        if open_tool is not None and st.button("Open source tool", key=f"r1117_need_{workspace}_{idx}", width="stretch"):
                            open_tool(row["tool"])
                        elif open_workspace is not None and st.button(f"Open {row['workspace']}", key=f"r1117_need_ws_{workspace}_{idx}", width="stretch"):
                            open_workspace(row["workspace"])
        else:
            st.success("This workspace can be opened without prerequisite scientific data.")
        if guide.get("cautions"):
            st.markdown("**Scientific boundary**")
            for caution in guide["cautions"]:
                st.caption(f"• {caution}")
        st.caption("Evidence labels are standardised across AGROLATTICE: Observed · Recorded · Retrieved · Derived · Mechanistic · ML prediction · Forecast · Scenario · Recommendation · Actual operation · Outcome · Causal estimate.")


def _open_button(label: str, workspace: str, tool: str | None, *, key: str, open_workspace, open_tool) -> None:
    if st.button(label, key=key, width="stretch"):
        if tool and open_tool is not None:
            open_tool(tool)
        elif open_workspace is not None:
            open_workspace(workspace)


def _render_start_here(state: Mapping[str, Any], context: Mapping[str, Any], open_workspace, open_tool) -> None:
    st.markdown("### Researcher start here")
    st.write("AGROLATTICE is designed around persistent spatial research context. Build the field/season first, then let experiments, Twins, models and reports reuse that context instead of recreating it in separate CSV workflows.")
    cols = st.columns(4)
    counts = state.get("counts", {})
    cols[0].metric("Mapped fields", int(counts.get("fields", 0)))
    cols[1].metric("Experiments", int(counts.get("trials", 0)))
    cols[2].metric("Persistent Twins", int(counts.get("twins", 0)))
    cols[3].metric("Registered models", int(counts.get("models", 0)))
    st.caption("Active context: " + " · ".join(f"{k}: {v}" for k, v in context.items() if str(v) not in {"", "Not selected", "None"}))

    flows = [workflow_progress(key, state) for key in ("first_field", "first_trial", "persistent_twin", "model_validation", "publication")]
    st.markdown("#### Suggested guided workflows")
    columns = st.columns(3)
    for idx, flow in enumerate(flows):
        with columns[idx % 3]:
            with st.container(border=True):
                st.markdown(f"**{flow['title']}**")
                st.progress(float(flow["progress"]))
                st.caption(f"{flow['ready']} of {flow['total']} readiness steps detected")
                missing = next((x for x in flow["steps"] if x["status"] != "Ready"), None)
                if missing:
                    st.caption(f"Next: {missing['title']}")
                    _open_button("Open next step", missing["workspace"], missing["tool"], key=f"r1117_start_flow_{idx}", open_workspace=open_workspace, open_tool=open_tool)
                else:
                    st.success("Core readiness steps complete.")

    st.markdown("#### How AGROLATTICE evidence should read")
    st.info("A field measurement is **Observed**. NASA/Sentinel are **Retrieved**. GDD/VPD are **Derived**. Crop-model outputs are **Mechanistic**. Statistical/ML outputs are **ML predictions**. Future values are **Forecasts**. A proposed action is a **Recommendation**; it becomes an **Actual operation** only when recorded as applied.")


def _render_guided_workflows(state: Mapping[str, Any], open_workspace, open_tool) -> None:
    st.markdown("### Guided workflows")
    labels = {flow["title"]: key for key, flow in WORKFLOWS.items()}
    selected = st.selectbox("Workflow", list(labels), key="r1117_help_workflow")
    progress = workflow_progress(labels[selected], state)
    st.caption(progress["goal"])
    st.progress(float(progress["progress"]))
    for idx, step in enumerate(progress["steps"]):
        with st.container(border=True):
            cols = st.columns([0.5, 4.7, 1.4])
            cols[0].markdown(f"### {_status_icon(step['status'])}")
            cols[1].markdown(f"**{idx + 1}. {step['title']}**")
            cols[1].caption(step["detail"])
            cols[1].caption(f"Destination: {step['workspace']} → {step['tool']}")
            with cols[2]:
                _open_button("Open", step["workspace"], step["tool"], key=f"r1117_flow_open_{labels[selected]}_{idx}", open_workspace=open_workspace, open_tool=open_tool)
    st.caption("Readiness is derived from persisted records only. A green step means the required record/evidence exists; it does not certify its scientific quality or completeness.")


def _render_workspace_guides(state: Mapping[str, Any], open_workspace, open_tool) -> None:
    st.markdown("### Workspace guides")
    workspace = st.selectbox("Workspace", WORKSPACE_ORDER, key="r1117_help_workspace")
    guide = WORKSPACE_GUIDES[workspace]
    st.write(guide["purpose"])
    cols = st.columns(2)
    with cols[0]:
        st.markdown("**Questions this workspace should answer**")
        for q in guide["questions"]:
            st.markdown(f"- {q}")
        st.markdown("**Typical outputs**")
        for x in guide["outputs"]:
            st.markdown(f"- {x}")
    with cols[1]:
        st.markdown("**What you need**")
        rows = readiness_rows(workspace, state)
        if not rows:
            st.caption("No prerequisite scientific dataset is required to open this workspace.")
        for idx, row in enumerate(rows):
            st.markdown(f"{_status_icon(row['status'])} **{row['label']}** — {row['status']}")
            st.caption(row["why"])
            if row["status"] != "Ready" and open_tool is not None:
                if st.button(f"Open {row['tool']}", key=f"r1117_wsreq_{workspace}_{idx}", width="stretch"):
                    open_tool(row["tool"])
        if open_workspace is not None and workspace != "Help":
            if st.button(f"Open {workspace}", key=f"r1117_open_workspace_{workspace}", type="primary", width="stretch"):
                open_workspace(workspace)
    st.markdown("**Scientific boundaries**")
    for caution in guide.get("cautions", []):
        st.warning(caution)


def _render_data_requirements(state: Mapping[str, Any], open_tool) -> None:
    st.markdown("### Data requirements & readiness")
    st.caption("This matrix tells you which persistent records exist and where missing prerequisites can be created/retrieved. It does not run retrieval or analysis automatically.")
    rows = []
    for key, meta in REQUIREMENTS.items():
        status = "Ready" if state.get(key) is True else (str(state.get(key)).title() if str(state.get(key)).casefold() in {"partial", "review", "stale"} else "Missing")
        rows.append({"Requirement": meta["label"], "Status": status, "Why it matters": meta["why"], "Workspace": meta["workspace"], "Tool": meta["tool"]})
    frame = pd.DataFrame(rows)
    st.dataframe(frame, hide_index=True, width="stretch")
    missing = frame.loc[frame["Status"].ne("Ready")]
    if not missing.empty and open_tool is not None:
        choices = [f"{r['Requirement']} → {r['Tool']}" for _, r in missing.iterrows()]
        mapping = {f"{r['Requirement']} → {r['Tool']}": r["Tool"] for _, r in missing.iterrows()}
        choice = st.selectbox("Open a source for missing data", choices, key="r1117_missing_source")
        if st.button("Open source", key="r1117_missing_source_button", type="primary"):
            open_tool(mapping[choice])


def _render_scientific_labels() -> None:
    st.markdown("### Scientific labels & interpretation")
    st.write("These labels have one meaning across Fields, Twin, Climate/EO, Crop Decisions, Experiments, Models & Evidence and Reports.")
    columns = st.columns(2)
    for idx, (label, info) in enumerate(EVIDENCE_TERMS.items()):
        with columns[idx % 2]:
            with st.container(border=True):
                st.markdown(f"**{label}**")
                st.write(info["definition"])
                st.caption(f"Caution: {info['caution']}")
    st.markdown("#### Wording safeguards")
    st.markdown("- **Predictive importance/SHAP/attention/gating** → predictive explanation, not causal importance.\n- **Climate similarity** → environmental resemblance under a specified metric, not agronomic equivalence.\n- **Mechanistic** → explicit process assumptions, not automatic validation.\n- **Validated** → state the site/season/genotype/deployment scope.\n- **Recommendation** → proposed action; record the operation separately if applied.\n- **Causal estimate** → report the causal graph/adjustment assumptions, overlap and uncertainty.")


def _render_glossary(render_contextual_help: Callable[[], None] | None) -> None:
    st.markdown("### Terminology & contextual help")
    query = st.text_input("Search terminology", placeholder="e.g. experimental unit, ebR1, OOD, RAW, parent pair", key="r1117_glossary_search")
    terms = dict(GLOSSARY)
    q = query.strip().casefold()
    if q:
        terms = {k: v for k, v in terms.items() if q in k.casefold() or q in v.casefold()}
    if terms:
        for term, definition in sorted(terms.items()):
            st.markdown(f"**{term}**")
            st.caption(definition)
    else:
        st.info("No glossary term matched. Try a shorter scientific term or use Search across Help.")
    if render_contextual_help is not None:
        st.divider()
        render_contextual_help()


def _render_troubleshooting() -> None:
    st.markdown("### Troubleshooting")
    issue = st.selectbox("Problem", list(TROUBLESHOOTING), key="r1117_help_trouble")
    item = TROUBLESHOOTING[issue]
    st.caption(item["symptoms"])
    for idx, step in enumerate(item["steps"], start=1):
        st.markdown(f"**{idx}.** {step}")
    st.warning("Avoid: " + item["avoid"])
    st.info("For a reproducible bug report, record the AGROLATTICE release, workspace, active field/trial, exact button/action, visible error, and whether the issue persists after a normal browser refresh. Do not delete scientific data as a troubleshooting step.")


def _render_search() -> None:
    st.markdown("### Search Help")
    query = st.text_input("Search help, workflows, troubleshooting and glossary", placeholder="e.g. satellite cloud, model leakage, silking, backup", key="r1117_help_search")
    hits = search_guidance(query)
    if query and not hits:
        st.info("No help entry matched. Try fewer words or search All Tools for a specific analytical capability.")
    for hit in hits[:30]:
        with st.container(border=True):
            st.markdown(f"**{hit['title']}** · `{hit['kind']}`")
            st.caption(hit["detail"])


def render_help_command_centre(
    *,
    app_version: str,
    context: Mapping[str, Any],
    state: Mapping[str, Any],
    open_workspace: Callable[[str], None] | None = None,
    open_tool: Callable[[str], None] | None = None,
    render_contextual_help: Callable[[], None] | None = None,
    render_current_guide: Callable[[], None] | None = None,
    render_release_notes: Callable[[], None] | None = None,
    render_publication_reference: Callable[[], None] | None = None,
) -> None:
    """Render the 11.19 Help, onboarding and guidance workspace."""
    st.caption(f"Help Command Centre {MODULE_VERSION} · guidance rules {GUIDANCE_VERSION} · {app_version}")
    views = ["Start Here", "Guided workflows", "Workspace guides", "Data requirements", "Scientific labels", "Terminology", "Troubleshooting", "Search", "Publication reference", "Release & guide"]
    selected = st.radio("Help view", views, horizontal=True, key="release11_17_help_view", label_visibility="collapsed")
    st.divider()
    if selected == "Start Here":
        _render_start_here(state, context, open_workspace, open_tool)
    elif selected == "Guided workflows":
        _render_guided_workflows(state, open_workspace, open_tool)
    elif selected == "Workspace guides":
        _render_workspace_guides(state, open_workspace, open_tool)
    elif selected == "Data requirements":
        _render_data_requirements(state, open_tool)
    elif selected == "Scientific labels":
        _render_scientific_labels()
    elif selected == "Terminology":
        _render_glossary(render_contextual_help)
    elif selected == "Troubleshooting":
        _render_troubleshooting()
    elif selected == "Search":
        _render_search()
    elif selected == "Publication reference":
        if render_publication_reference is not None:
            render_publication_reference()
        else:
            st.info("Publication-reference material is not available in this installation.")
    else:
        if render_current_guide is not None:
            render_current_guide()
        if render_release_notes is not None:
            with st.expander("Release notes", expanded=False):
                render_release_notes()
