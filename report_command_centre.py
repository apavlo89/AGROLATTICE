"""AGROLATTICE 11.15 Research Reporting & Publication Command Centre."""
from __future__ import annotations

import hashlib
import io
import json
import os
import platform
import re
import sqlite3
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import pandas as pd
import streamlit as st

from publication_builder import (
    MANUSCRIPT_PRESETS,
    METHODS_REGISTRY,
    REPORT_PRESETS,
    audit_claim_text,
    build_publication_package,
    figure_png,
    figure_svg,
    manuscript_word_counts,
    multi_panel_png,
    manuscript_markdown,
    new_study_template,
    report_audit,
)
from reporting_registry import ReportingRegistry, sha256_bytes, stable_json

MODULE_VERSION = "1.0.0"

REPORT_TYPES = list(REPORT_PRESETS)
EVIDENCE_TYPES = ["Measured", "Retrieved", "Derived", "Mechanistic", "Predictive", "Scenario", "Recommendation", "Observed outcome", "Causal estimate"]
REPORT_NAV = ["Overview", "Report Builder", "Publications", "Tables & Figures", "Evidence & Claims", "Reproducibility", "Report Library"]


def _safe_frame(value: Any) -> pd.DataFrame:
    if isinstance(value, pd.DataFrame):
        return value.copy()
    if isinstance(value, Mapping):
        return pd.DataFrame([dict(value)]) if value else pd.DataFrame()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        try:
            return pd.DataFrame(list(value))
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def _json_value(value: Any, default: Any = None) -> Any:
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value) if value not in (None, "") else default
    except Exception:
        return default


def _frame_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8")


def _file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sqlite_schema_info(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "exists": False}
    out: dict[str, Any] = {"path": str(path), "exists": True, "size_bytes": path.stat().st_size}
    try:
        with sqlite3.connect(path) as conn:
            out["integrity_check"] = conn.execute("PRAGMA integrity_check").fetchone()[0]
            out["foreign_key_violations"] = len(conn.execute("PRAGMA foreign_key_check").fetchall())
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
            out["tables"] = {table: int(conn.execute(f'SELECT COUNT(*) FROM "{str(table).replace(chr(34), chr(34)*2)}"').fetchone()[0]) for table in tables}
            if "metadata" in tables:
                try:
                    out["metadata"] = dict(conn.execute("SELECT key,value FROM metadata").fetchall())
                except Exception:
                    pass
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def _normalise_scope(field_db, pollination_db, twin_db, active_field_id: str | None, active_trial_id: str | None) -> dict[str, Any]:
    scope: dict[str, Any] = {"field_id": active_field_id, "trial_id": active_trial_id}
    fields = field_db.fields() if field_db is not None else pd.DataFrame()
    trials = pollination_db.list_trials() if pollination_db is not None else pd.DataFrame()
    if active_trial_id and pollination_db is not None:
        try:
            trial = pollination_db.get_trial(str(active_trial_id))
            if trial:
                scope["trial_name"] = trial.get("name") or trial.get("trial_name")
                scope["season_year"] = trial.get("season_year")
                scope["crop"] = trial.get("crop") or "Maize"
                scope["field_id"] = trial.get("field_id") or scope.get("field_id")
        except Exception:
            pass
    if scope.get("field_id") and field_db is not None:
        try:
            field = field_db.field(str(scope["field_id"]))
            if field:
                scope["field_name"] = field.get("name")
                scope["farm_id"] = field.get("farm_id")
                scope["crop"] = scope.get("crop") or field.get("crop")
                scope["variety"] = field.get("variety") or field.get("genotype")
                scope["season_year"] = scope.get("season_year") or field.get("season_year")
                try:
                    farm = field_db.farm(str(field.get("farm_id"))) if field.get("farm_id") else None
                    if farm:
                        scope["farm_name"] = farm.get("name")
                except Exception:
                    pass
        except Exception:
            pass
    if twin_db is not None:
        try:
            links = twin_db.links()
            if not links.empty:
                candidates = links.copy()
                if scope.get("trial_id") and "trial_id" in candidates.columns:
                    hit = candidates[candidates["trial_id"].astype(str) == str(scope["trial_id"])]
                else:
                    hit = pd.DataFrame()
                if hit.empty and scope.get("field_id") and "field_id" in candidates.columns:
                    hit = candidates[candidates["field_id"].astype(str) == str(scope["field_id"])]
                if not hit.empty:
                    row = hit.iloc[0].to_dict()
                    scope["twin_id"] = row.get("link_id")
                    scope["twin_name"] = row.get("name")
        except Exception:
            pass
    scope["available_field_count"] = int(len(fields))
    scope["available_trial_count"] = int(len(trials))
    return scope


def _scope_label(scope: Mapping[str, Any]) -> str:
    parts = [scope.get("farm_name"), scope.get("field_name"), scope.get("crop"), scope.get("season_year"), scope.get("trial_name"), scope.get("twin_name")]
    return " → ".join(str(p) for p in parts if p not in (None, "", "nan")) or "Portfolio / unscoped report"


def collect_persistent_artifacts(*, field_db, pollination_db, twin_db, registry, scope: Mapping[str, Any], limit: int = 5000) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    """Collect reportable evidence from persisted stores only; no remote calls."""
    frames: dict[str, pd.DataFrame] = {}
    field_id = scope.get("field_id")
    trial_id = scope.get("trial_id")
    twin_id = scope.get("twin_id")

    if field_db is not None and field_id:
        getters = [
            ("field.identity", lambda: _safe_frame(field_db.field(str(field_id)))),
            ("field.seasons", lambda: field_db.seasons(str(field_id))),
            ("field.timeline", lambda: field_db.field_timeline(str(field_id))),
            ("field.operations", lambda: field_db.detailed_operations(str(field_id))),
            ("field.scouting_observations", lambda: field_db.detailed_observations(str(field_id))),
            ("field.sensors", lambda: field_db.sensors(str(field_id))),
            ("field.nutrient_samples", lambda: field_db.detailed_nutrient_samples(str(field_id))),
            ("field.alerts", lambda: field_db.alerts(str(field_id))),
            ("field.sampling_points", lambda: field_db.sampling_points(str(field_id))),
            ("field.prescriptions", lambda: field_db.prescriptions(str(field_id))),
        ]
        for name, getter in getters:
            try:
                value = getter()
                if isinstance(value, pd.DataFrame) and not value.empty:
                    frames[name] = value.head(limit).copy()
            except Exception:
                pass

    if pollination_db is not None and trial_id:
        getters = [
            ("experiment.trial", lambda: _safe_frame(pollination_db.get_trial(str(trial_id)))),
            ("experiment.protocol", lambda: _safe_frame(pollination_db.experiment_protocol(str(trial_id)))),
            ("experiment.protocol_versions", lambda: pollination_db.protocol_versions(str(trial_id))),
            ("experiment.factors", lambda: pollination_db.factor_definitions(str(trial_id))),
            ("experiment.design_versions", lambda: pollination_db.design_versions(str(trial_id))),
            ("experiment.experimental_units", lambda: pollination_db.list_plots(str(trial_id))),
            ("experiment.flowering_observations", lambda: pollination_db.observations(str(trial_id))),
            ("experiment.leaf_observations", lambda: pollination_db.leaf_observations(str(trial_id))),
            ("experiment.phenology_events", lambda: pollination_db.phenology_events(str(trial_id))),
            ("experiment.harvest_outcomes", lambda: pollination_db.harvest(str(trial_id))),
            ("experiment.weather", lambda: pollination_db.weather(str(trial_id))),
            ("experiment.satellite_links", lambda: pollination_db.satellite_links(str(trial_id))),
            ("experiment.measurement_requirements", lambda: pollination_db.measurement_requirements(str(trial_id))),
            ("experiment.data_completeness", lambda: pollination_db.data_completeness_matrix(str(trial_id))),
            ("experiment.audit", lambda: pollination_db.trial_audit(str(trial_id))),
        ]
        for name, getter in getters:
            try:
                value = getter()
                if isinstance(value, pd.DataFrame) and not value.empty:
                    frames[name] = value.head(limit).copy()
            except Exception:
                pass

    if twin_db is not None and twin_id:
        getters = [
            ("twin.identity", lambda: _safe_frame(twin_db.link(str(twin_id)))),
            ("twin.snapshots", lambda: twin_db.snapshots(str(twin_id))),
            ("twin.events", lambda: twin_db.events(str(twin_id), limit=limit)),
            ("twin.calibration_runs", lambda: twin_db.calibration_runs(str(twin_id))),
            ("twin.analogue_seasons", lambda: twin_db.analogue_seasons(str(twin_id))),
            ("twin.root_zone", lambda: twin_db.root_zone(str(twin_id))),
            ("twin.root_zone_stage_summary", lambda: twin_db.root_zone_stage_summary(str(twin_id))),
            ("twin.satellite", lambda: twin_db.satellite(str(twin_id))),
            ("twin.weather", lambda: twin_db.weather(str(twin_id))),
            ("twin.recommendations", lambda: twin_db.recommendations(str(twin_id))),
            ("twin.model_registry", lambda: twin_db.model_registry(str(twin_id))),
        ]
        for name, getter in getters:
            try:
                value = getter()
                if isinstance(value, pd.DataFrame) and not value.empty:
                    frames[name] = value.head(limit).copy()
            except Exception:
                pass

    relevant_model_ids: set[str] = set()
    if registry is not None:
        try:
            acquisitions = registry.data_acquisitions(field_id=str(field_id), limit=1000) if field_id else pd.DataFrame()
            if not acquisitions.empty:
                frames["evidence.data_acquisitions"] = acquisitions
        except Exception:
            pass
        try:
            predictions = registry.predictions(field_id=str(field_id) if field_id else None, trial_id=str(trial_id) if trial_id else None, limit=limit)
            if not predictions.empty:
                frames["evidence.predictions"] = predictions
                if "model_id" in predictions.columns:
                    relevant_model_ids |= set(predictions["model_id"].dropna().astype(str))
        except Exception:
            pass
        for name, getter in [
            ("evidence.recommendations", lambda: registry.recommendations(field_id=str(field_id) if field_id else None, trial_id=str(trial_id) if trial_id else None)),
            ("evidence.treatment_outcomes", lambda: registry.treatment_outcomes(field_id=str(field_id) if field_id else None, trial_id=str(trial_id) if trial_id else None)),
            ("evidence.decision_runs", lambda: registry.decision_runs(field_id=str(field_id) if field_id else None, limit=1000)),
            ("evidence.causal_analyses", lambda: registry.causal_analyses(field_id=str(field_id) if field_id else None, limit=1000)),
        ]:
            try:
                value = getter()
                if isinstance(value, pd.DataFrame) and not value.empty:
                    frames[name] = value.head(limit)
            except Exception:
                pass
        if relevant_model_ids:
            models = registry.models()
            if not models.empty and "model_id" in models.columns:
                subset = models[models["model_id"].astype(str).isin(relevant_model_ids)].copy()
                if not subset.empty:
                    frames["models.registered_models"] = subset
            runs, validations, versions, health = [], [], [], []
            for model_id in sorted(relevant_model_ids):
                for target, method in [(runs, registry.training_runs), (validations, registry.validation_runs), (versions, registry.model_versions), (health, registry.model_health_events)]:
                    try:
                        frame = method(model_id=model_id) if method.__name__ in ("training_runs", "validation_runs") else method(model_id)
                        if isinstance(frame, pd.DataFrame) and not frame.empty:
                            target.append(frame)
                    except Exception:
                        pass
            if runs:
                frames["models.training_runs"] = pd.concat(runs, ignore_index=True).head(limit)
            if validations:
                frames["models.validation_runs"] = pd.concat(validations, ignore_index=True).head(limit)
            if versions:
                frames["models.model_versions"] = pd.concat(versions, ignore_index=True).head(limit)
            if health:
                frames["models.health_events"] = pd.concat(health, ignore_index=True).head(limit)

    manifest = {
        "scope": dict(scope),
        "artifacts": {
            name: {
                "rows": int(len(frame)),
                "columns": [str(c) for c in frame.columns],
                "sha256_csv": sha256_bytes(_frame_bytes(frame)),
            }
            for name, frame in frames.items()
        },
        "counts": {
            "artifacts": len(frames),
            "rows": int(sum(len(f) for f in frames.values())),
            "training_runs": int(len(frames.get("models.training_runs", pd.DataFrame()))),
            "validation_runs": int(len(frames.get("models.validation_runs", pd.DataFrame()))),
            "predictions": int(len(frames.get("evidence.predictions", pd.DataFrame()))),
            "outcomes": int(len(frames.get("evidence.treatment_outcomes", pd.DataFrame())) + len(frames.get("experiment.harvest_outcomes", pd.DataFrame()))),
        },
    }
    return frames, manifest


def report_readiness(report_type: str, frames: Mapping[str, pd.DataFrame], scope: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    def status(name: str, condition: bool, message_ok: str, message_missing: str, partial: bool = False) -> tuple[str, dict[str, str]]:
        state = "Complete" if condition else ("Incomplete" if partial else "Missing")
        return name, {"status": state, "message": message_ok if condition else message_missing}

    checks: dict[str, dict[str, str]] = {}
    if report_type in ("Experiment report", "Maize Synchrony report", "G×E×M analysis report", "Full scientific manuscript") and scope.get("trial_id"):
        for key, val in [
            status("Protocol", "experiment.protocol" in frames, "Protocol is stored.", "No persistent experiment protocol found."),
            status("Randomisation/design", "experiment.design_versions" in frames or "experiment.experimental_units" in frames, "Design evidence is available.", "Randomisation/design evidence is missing."),
            status("Experimental-unit map", "experiment.experimental_units" in frames, "Experimental units are stored.", "No experimental units are stored."),
            status("Weather", "experiment.weather" in frames or "twin.weather" in frames or "evidence.data_acquisitions" in frames, "Environmental evidence is available.", "Field/trial weather evidence is missing."),
            status("Flowering observations", "experiment.flowering_observations" in frames, "Flowering observations are available.", "Flowering observations are missing."),
            status("Harvest outcomes", "experiment.harvest_outcomes" in frames, "Harvest outcomes are available.", "Harvest outcomes are not yet complete/available."),
        ]:
            checks[key] = val
    elif report_type == "Persistent Twin season report":
        for key, val in [
            status("Twin linkage", "twin.identity" in frames, "Persistent Twin is linked.", "No active Persistent Twin is linked."),
            status("Weather", "twin.weather" in frames, "Twin weather is persisted.", "Twin weather is missing."),
            status("Root zone", "twin.root_zone" in frames, "Root-zone state is persisted.", "Root-zone evidence is missing."),
            status("Earth observation", "twin.satellite" in frames, "EO evidence is persisted.", "EO evidence is missing."),
            status("State history", "twin.snapshots" in frames or "twin.events" in frames, "Twin history is available.", "No Twin state history is stored."),
        ]:
            checks[key] = val
    elif report_type == "Field season report":
        for key, val in [
            status("Mapped field", "field.identity" in frames, "Field metadata are available.", "No active mapped field."),
            status("Operations", "field.operations" in frames, "Operations are recorded.", "No field operations are recorded."),
            status("Scouting", "field.scouting_observations" in frames, "Scouting observations are available.", "No scouting observations are stored."),
            status("Environmental evidence", "twin.weather" in frames or "evidence.data_acquisitions" in frames, "Environmental evidence is available.", "Environmental evidence is missing."),
        ]:
            checks[key] = val
    elif report_type == "Model validation report":
        for key, val in [
            status("Registered model", "models.registered_models" in frames, "Relevant registered model evidence is available.", "No model linked to the current prediction scope."),
            status("Training provenance", "models.training_runs" in frames, "Training runs are persisted.", "Training-run provenance is missing."),
            status("Held-out validation", "models.validation_runs" in frames, "Validation evidence is available.", "No validation runs are linked."),
            status("Prediction/outcome evidence", "evidence.predictions" in frames and ("evidence.treatment_outcomes" in frames or "experiment.harvest_outcomes" in frames), "Predictions and measured outcomes are available.", "Prediction/outcome closure is incomplete."),
        ]:
            checks[key] = val
    else:
        checks["Persistent evidence"] = {"status": "Complete" if frames else "Missing", "message": f"{len(frames)} persisted evidence artifacts available." if frames else "No persistent evidence is available for the selected scope."}
    return checks


def infer_methods(frames: Mapping[str, pd.DataFrame]) -> list[str]:
    methods: list[str] = []
    keys = " ".join(frames).casefold()
    mapping = [
        ("weather", "NASA-derived agroclimate data"),
        ("phenology", "Daily weather and phenology"),
        ("root_zone", "Root-zone soil-water balance"),
        ("satellite", "Sentinel-2 Earth observation"),
        ("design", "Experimental design and randomisation"),
        ("validation", "Agricultural grouped validation"),
        ("causal", "Recommendation causal audit"),
    ]
    for token, method in mapping:
        if token in keys:
            methods.append(method)
    models = frames.get("models.registered_models")
    if isinstance(models, pd.DataFrame) and not models.empty:
        text = " ".join(models.astype(str).fillna("").values.ravel()).casefold()
        for token, method in [
            ("mechanistic maize", "Mechanistic Maize Twin"), ("catboost", "Environmental pest-risk modelling"),
            ("weak", "Weakly supervised spatial yield"), ("fusion", "Adaptive multimodal fusion"),
            ("residual", "Hybrid mechanistic + ML residual learning"), ("aquacrop", "AquaCrop-OSPy"),
            ("dssat", "DSSAT interoperability"), ("apsim", "APSIM interoperability"),
        ]:
            if token in text:
                methods.append(method)
    return list(dict.fromkeys(methods))


def limitation_suggestions(report_type: str, readiness: Mapping[str, Mapping[str, str]], frames: Mapping[str, pd.DataFrame]) -> list[str]:
    suggestions = []
    for name, info in readiness.items():
        if info.get("status") != "Complete":
            suggestions.append(f"{name}: {info.get('message')}")
    if "twin.weather" in frames or "experiment.weather" in frames:
        suggestions.append("Gridded/retrieved weather should not be interpreted as a local weather-station measurement unless the source actually is a station record.")
    if "twin.satellite" in frames or "experiment.satellite_links" in frames:
        suggestions.append("Earth-observation inference is limited by spatial resolution, cloud/quality filtering and the number of usable observations in the selected season.")
    if "models.registered_models" in frames and "models.validation_runs" not in frames:
        suggestions.append("A registered predictive model is present without linked held-out validation evidence in the selected report scope.")
    if report_type == "Maize Synchrony report":
        suggestions.append("Flowering timing synchrony does not by itself guarantee pollen quantity, fertilisation, seed purity or harvest outcome.")
        suggestions.append("Publication-informed maize physiology priors are not measurements of the local parent lines unless locally calibrated observations are recorded.")
    return list(dict.fromkeys(suggestions))


def _report_context_selector(field_db, pollination_db, twin_db, default_scope: Mapping[str, Any]) -> dict[str, Any]:
    scope = dict(default_scope)
    mode = st.selectbox("Report scope", ["Active context", "Specific field", "Specific experiment", "Specific Twin", "Portfolio"], key="report15_scope_mode")
    if mode == "Portfolio":
        return {"scope_mode": "Portfolio"}
    if mode == "Specific field":
        fields = field_db.fields() if field_db is not None else pd.DataFrame()
        if not fields.empty:
            label_col = "name" if "name" in fields.columns else fields.columns[0]
            opts = fields.to_dict("records")
            choice = st.selectbox("Field", opts, format_func=lambda r: str(r.get(label_col) or r.get("field_id")), key="report15_scope_field")
            return _normalise_scope(field_db, pollination_db, twin_db, str(choice.get("field_id")), None)
    if mode == "Specific experiment":
        trials = pollination_db.list_trials() if pollination_db is not None else pd.DataFrame()
        if not trials.empty:
            opts = trials.to_dict("records")
            choice = st.selectbox("Experiment", opts, format_func=lambda r: str(r.get("name") or r.get("trial_name") or r.get("trial_id")), key="report15_scope_trial")
            return _normalise_scope(field_db, pollination_db, twin_db, choice.get("field_id"), str(choice.get("trial_id")))
    if mode == "Specific Twin":
        links = twin_db.links() if twin_db is not None else pd.DataFrame()
        if not links.empty:
            opts = links.to_dict("records")
            choice = st.selectbox("Persistent Twin", opts, format_func=lambda r: str(r.get("name") or r.get("link_id")), key="report15_scope_twin")
            selected = _normalise_scope(field_db, pollination_db, twin_db, choice.get("field_id"), choice.get("trial_id"))
            selected["twin_id"] = str(choice.get("link_id"))
            selected["twin_name"] = choice.get("name")
            return selected
    return scope


def _artifact_catalog_frame(frames: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    return pd.DataFrame([
        {"Artifact": name, "Rows": len(frame), "Columns": len(frame.columns), "Preview columns": ", ".join(map(str, frame.columns[:10])) + (" …" if len(frame.columns) > 10 else "")}
        for name, frame in frames.items()
    ])


def _saved_artifact_frames(reporting_db: ReportingRegistry, study_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tables, figures = [], []
    rows = reporting_db.artifacts(study_id)
    if rows.empty:
        return tables, figures
    records = rows.to_dict("records")
    svg_by_title: dict[str, bytes] = {}
    for row in records:
        if str(row.get("kind") or "") == "figure_svg":
            path = Path(str(row.get("file_path") or ""))
            if path.exists():
                try:
                    svg_by_title[str(row.get("title") or "")] = path.read_bytes()
                except Exception:
                    pass
    for row in records:
        kind = str(row.get("kind") or "")
        path = Path(str(row.get("file_path") or ""))
        source = _json_value(row.get("source_json"), {})
        settings = _json_value(row.get("settings_json"), {})
        if kind == "table" and path.exists():
            try:
                frame = pd.read_csv(path)
                tables.append({"artifact_id": row.get("artifact_id"), "title": row.get("title"), "caption": row.get("caption") or "", "frame": frame, "source": source, "settings": settings})
            except Exception:
                pass
        elif kind == "figure" and path.exists():
            try:
                title = str(row.get("title") or "")
                figures.append({"artifact_id": row.get("artifact_id"), "title": title, "caption": row.get("caption") or "", "png": path.read_bytes(), "svg": svg_by_title.get(title), "source": source, "settings": settings})
            except Exception:
                pass
    return tables, figures


def _build_reproducibility_manifest(*, app_root: Path, app_version: str, study: Mapping[str, Any], scope: Mapping[str, Any], snapshot: Mapping[str, Any] | None, frames: Mapping[str, pd.DataFrame], methods: Sequence[str], include_climate_hash: bool = False) -> dict[str, Any]:
    db_paths = {
        "field_operations": app_root / "field_operations" / "field_operations.sqlite",
        "experiments": app_root / "pollination_lab" / "maize_flowering_trials.sqlite",
        "persistent_twin": app_root / "agrolattice_twin" / "agrolattice_twin.sqlite",
        "research_evidence": app_root / "models_evidence" / "research_evidence.sqlite",
        "crop_profiles": app_root / "models_evidence" / "crop_profiles.sqlite",
        "reporting": app_root / "reports" / "reporting.sqlite",
    }
    manifest: dict[str, Any] = {
        "app_version": app_version,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "study_id": study.get("study_id"),
        "scope": dict(scope),
        "evidence_snapshot_id": snapshot.get("snapshot_id") if snapshot else None,
        "evidence_snapshot_sha256": snapshot.get("manifest_sha256") if snapshot else None,
        "selected_methods": list(methods),
        "python": sys.version,
        "platform": platform.platform(),
        "databases": {name: _sqlite_schema_info(path) for name, path in db_paths.items()},
        "artifact_signatures": {name: {"rows": len(frame), "sha256_csv": sha256_bytes(_frame_bytes(frame))} for name, frame in frames.items()},
    }
    if include_climate_hash:
        candidates = list((app_root / "Datasets" / "countries").glob("*/agroclimate_longformat.csv"))
        manifest["installed_climate_datasets"] = [{"path": str(p.relative_to(app_root)), "size_bytes": p.stat().st_size, "sha256": _file_sha256(p)} for p in candidates]
    else:
        candidates = list((app_root / "Datasets" / "countries").glob("*/agroclimate_longformat.csv"))
        manifest["installed_climate_datasets"] = [{"path": str(p.relative_to(app_root)), "size_bytes": p.stat().st_size, "mtime_ns": p.stat().st_mtime_ns, "sha256": "not calculated in lightweight mode"} for p in candidates]
    return manifest


def _render_overview(reporting_db: ReportingRegistry, studies: pd.DataFrame, frames: Mapping[str, pd.DataFrame], readiness: Mapping[str, Mapping[str, str]], scope: Mapping[str, Any], report_type: str) -> None:
    summary = reporting_db.summary()
    snapshots = reporting_db.snapshots()
    exports = 0
    if not studies.empty:
        for sid in studies["study_id"].astype(str).head(100):
            try:
                exports += len(reporting_db.exports(sid))
            except Exception:
                pass
    cols = st.columns(4)
    cols[0].metric("Reports", summary.get("studies", 0))
    cols[1].metric("Frozen evidence snapshots", summary.get("evidence_snapshots", 0))
    cols[2].metric("Registered claims", summary.get("claims", 0))
    cols[3].metric("Export packages", exports)
    st.markdown("### Report readiness")
    if not readiness:
        st.info("Choose a field, experiment, Twin or report type to evaluate readiness.")
    else:
        for name, info in readiness.items():
            icon = "✅" if info.get("status") == "Complete" else "⚠️" if info.get("status") == "Incomplete" else "❌"
            st.markdown(f"{icon} **{name}** — {info.get('message')}")
    st.markdown("### Priority reporting issues")
    gaps = [(name, info) for name, info in readiness.items() if info.get("status") != "Complete"]
    if gaps:
        for name, info in gaps[:6]:
            st.warning(f"{name}: {info.get('message')}")
    else:
        st.success("No major report-readiness gaps were detected in the persisted evidence currently visible to this scope. This does not replace scientific review.")
    st.caption(f"Scope: {_scope_label(scope)} · Report type: {report_type} · {len(frames)} persistent evidence artifacts available")
    if not studies.empty:
        st.markdown("### Recent reports")
        st.dataframe(studies.head(8), width="stretch", hide_index=True)


def _render_report_builder(reporting_db: ReportingRegistry, frames: Mapping[str, pd.DataFrame], scope: Mapping[str, Any], default_report_type: str, legacy_study_root: Path) -> None:
    st.markdown("### Report Builder")
    st.caption("Build reports from persisted AGROLATTICE evidence. CSV upload is optional and intended for genuinely external data, not as a prerequisite for data the platform already stores.")
    studies = reporting_db.studies()
    create = st.toggle("Create a new report", value=studies.empty, key="report15_create_toggle")
    if create:
        cols = st.columns([3, 2])
        title = cols[0].text_input("Report title", value=f"{default_report_type} — {_scope_label(scope)}"[:140], key="report15_new_title")
        report_type = cols[1].selectbox("Report type", REPORT_TYPES, index=REPORT_TYPES.index(default_report_type) if default_report_type in REPORT_TYPES else 0, key="report15_new_type")
        if st.button("Create report", type="primary", key="report15_create"):
            template = new_study_template(title=title, report_type=report_type)
            template["scope"] = dict(scope)
            study_id = reporting_db.save_study({**template, "manuscript": {k: template.get(k, "") for k in template if k in ("abstract_background","abstract_methods","abstract_results","abstract_conclusion","introduction","methods_notes","results","discussion","limitations","conclusion","acknowledgements","funding","conflicts","ethics_permissions","data_availability","code_availability","research_question","study_design","keywords")}})
            st.session_state["report15_active_study_id"] = study_id
            st.success("Report created.")
            st.rerun()
    else:
        if not studies.empty:
            opts = studies.to_dict("records")
            active = st.selectbox("Active report", opts, format_func=lambda r: f"{r.get('title')} · {r.get('manuscript_status')} · {r.get('report_type')}", key="report15_builder_study")
            st.session_state["report15_active_study_id"] = str(active.get("study_id"))
    with st.expander("Import older Release-3 JSON studies", expanded=False):
        st.caption("Legacy study JSON files are imported into the 11.15 reporting registry without deleting or changing the original files.")
        if st.button("Import legacy studies", key="report15_import_legacy"):
            result = reporting_db.import_legacy_studies(legacy_study_root)
            st.success(f"Found {result['found']}; imported {result['imported']}; already present {result['skipped']}; failed {result['failed']}.")
    st.markdown("### Persistent evidence available")
    catalog = _artifact_catalog_frame(frames)
    if catalog.empty:
        st.warning("No persisted evidence artifacts are available for the current scope.")
    else:
        st.dataframe(catalog, width="stretch", hide_index=True)


def _current_study(reporting_db: ReportingRegistry) -> dict[str, Any] | None:
    study_id = st.session_state.get("report15_active_study_id")
    if not study_id:
        studies = reporting_db.studies()
        if studies.empty:
            return None
        study_id = str(studies.iloc[0]["study_id"])
        st.session_state["report15_active_study_id"] = study_id
    return reporting_db.study(str(study_id))


def _render_publications(reporting_db: ReportingRegistry, readiness: Mapping[str, Mapping[str, str]], frames: Mapping[str, pd.DataFrame]) -> None:
    study = _current_study(reporting_db)
    if not study:
        st.info("Create or select a report in Report Builder first.")
        return
    manuscript = dict(study.get("manuscript") or {})
    st.markdown(f"### {study.get('title')}")
    cols = st.columns([2, 2, 2])
    report_type = cols[0].selectbox("Report type", REPORT_TYPES, index=REPORT_TYPES.index(study.get("report_type")) if study.get("report_type") in REPORT_TYPES else 0, key="report15_pub_type")
    preset = cols[1].selectbox("Manuscript preset", list(MANUSCRIPT_PRESETS), key="report15_manuscript_preset")
    status = cols[2].selectbox("Manuscript status", ["Draft", "Internal review", "Submitted", "Revision", "Final"], index=["Draft", "Internal review", "Submitted", "Revision", "Final"].index(study.get("manuscript_status")) if study.get("manuscript_status") in ["Draft", "Internal review", "Submitted", "Revision", "Final"] else 0, key="report15_status")
    st.caption(MANUSCRIPT_PRESETS[preset])
    author_text = st.text_input("Authors", value=", ".join(a.get("name", "") if isinstance(a, Mapping) else str(a) for a in study.get("authors", [])), key="report15_authors")
    affiliation_text = st.text_area("Affiliations (one per line)", value="\n".join(map(str, study.get("affiliations", []))), height=80, key="report15_affiliations")
    c1, c2, c3 = st.columns(3)
    corresponding = c1.text_input("Corresponding author", value=study.get("corresponding_author") or "", key="report15_corresponding")
    orcid = c2.text_input("Corresponding ORCID", value=study.get("corresponding_orcid") or "", key="report15_orcid")
    journal = c3.text_input("Target journal", value=study.get("target_journal") or "", key="report15_journal")
    st.markdown("#### Structured abstract")
    a1, a2 = st.columns(2)
    manuscript["abstract_background"] = a1.text_area("Background", value=manuscript.get("abstract_background") or "", height=120, key="report15_abs_bg")
    manuscript["abstract_methods"] = a2.text_area("Methods", value=manuscript.get("abstract_methods") or "", height=120, key="report15_abs_methods")
    a3, a4 = st.columns(2)
    manuscript["abstract_results"] = a3.text_area("Results", value=manuscript.get("abstract_results") or "", height=120, key="report15_abs_results")
    manuscript["abstract_conclusion"] = a4.text_area("Conclusions", value=manuscript.get("abstract_conclusion") or "", height=120, key="report15_abs_conclusion")
    st.markdown("#### Manuscript sections")
    manuscript["introduction"] = st.text_area("Introduction", value=manuscript.get("introduction") or "", height=180, key="report15_intro")
    manuscript["study_design"] = st.text_area("Study design", value=manuscript.get("study_design") or "", height=100, key="report15_design")
    manuscript["research_question"] = st.text_area("Research question / objective", value=manuscript.get("research_question") or "", height=80, key="report15_question")
    manuscript["methods_notes"] = st.text_area("Additional method details", value=manuscript.get("methods_notes") or "", height=140, key="report15_methods")
    manuscript["results"] = st.text_area("Results narrative", value=manuscript.get("results") or "", height=180, key="report15_results")
    manuscript["discussion"] = st.text_area("Discussion", value=manuscript.get("discussion") or "", height=180, key="report15_discussion")
    suggestions = limitation_suggestions(report_type, readiness, frames)
    if suggestions:
        with st.expander("Evidence-derived limitation suggestions", expanded=False):
            for suggestion in suggestions:
                st.markdown(f"- {suggestion}")
            st.caption("These are candidate limitations derived from current evidence gaps. The author decides whether and how they apply.")
    manuscript["limitations"] = st.text_area("Limitations", value=manuscript.get("limitations") or "", height=150, key="report15_limitations")
    manuscript["conclusion"] = st.text_area("Conclusions", value=manuscript.get("conclusion") or "", height=130, key="report15_conclusion")
    for label, key in [("Acknowledgements", "acknowledgements"), ("Funding", "funding"), ("Conflicts of interest", "conflicts"), ("Ethics / permissions", "ethics_permissions"), ("Data availability", "data_availability"), ("Code availability", "code_availability")]:
        manuscript[key] = st.text_area(label, value=manuscript.get(key) or "", height=80, key=f"report15_{key}")
    keyword_text = st.text_input("Keywords", value=", ".join(manuscript.get("keywords") or []), key="report15_keywords")
    manuscript["keywords"] = [k.strip() for k in keyword_text.split(",") if k.strip()]
    counts = manuscript_word_counts(manuscript)
    metrics = st.columns(4)
    metrics[0].metric("Abstract words", counts.get("abstract_total", 0))
    metrics[1].metric("Main-text words", counts.get("main_text", 0))
    metrics[2].metric("Tables", len(reporting_db.artifacts(study["study_id"], "table")))
    metrics[3].metric("Figures", len(reporting_db.artifacts(study["study_id"], "figure")))
    with st.expander("Reading preview", expanded=False):
        preview_study = {**study, **manuscript, "authors": [{"name": a.strip()} for a in author_text.split(",") if a.strip()], "affiliations": [a.strip() for a in affiliation_text.splitlines() if a.strip()], "corresponding_author": corresponding, "journal": journal, "report_type": report_type}
        preview = manuscript_markdown(study=preview_study, selected_methods=[], tables=[], figures=[], reproducibility={"preview": True}, citations=[], claims=[])
        # Keep the preview readable; the export remains the canonical full manuscript package.
        st.markdown(preview.replace("```json\n{\n  \"preview\": true\n}\n```", "_Reproducibility manifest is added when the report package is built._"))
    if st.button("Save manuscript draft", type="primary", key="report15_save_manuscript"):
        reporting_db.save_study({**study, "report_type": report_type, "manuscript_status": status, "authors": [{"name": a.strip()} for a in author_text.split(",") if a.strip()], "affiliations": [a.strip() for a in affiliation_text.splitlines() if a.strip()], "corresponding_author": corresponding, "corresponding_orcid": orcid, "target_journal": journal, "manuscript": manuscript})
        st.success("Manuscript draft saved.")
    st.markdown("#### Version history")
    snapshots = reporting_db.snapshots(study["study_id"])
    snap_opts = [None] + (snapshots.to_dict("records") if not snapshots.empty else [])
    snap = st.selectbox("Evidence snapshot for new version", snap_opts, format_func=lambda r: "No frozen snapshot" if r is None else f"{r.get('created_at')} · {r.get('label')} · {str(r.get('manifest_sha256'))[:10]}", key="report15_version_snapshot")
    vcols = st.columns([2, 2, 4])
    version_label = vcols[0].text_input("Version label", value="", placeholder="e.g. Submitted version", key="report15_version_label")
    version_author = vcols[1].text_input("Version author", value=corresponding, key="report15_version_author")
    version_notes = vcols[2].text_input("Reason for revision", value="", key="report15_version_notes")
    if st.button("Freeze new report version", key="report15_create_version"):
        current = reporting_db.study(study["study_id"]) or study
        version_id = reporting_db.create_version(study["study_id"], manuscript=current.get("manuscript") or manuscript, snapshot_id=snap.get("snapshot_id") if isinstance(snap, Mapping) else None, label=version_label, status=status, notes=version_notes, author=version_author)
        st.success(f"Created immutable report version {version_id[:8]}.")
    versions = reporting_db.versions(study["study_id"])
    if not versions.empty:
        st.dataframe(versions[[c for c in ["version_number", "label", "manuscript_status", "evidence_snapshot_id", "author", "created_at"] if c in versions.columns]], width="stretch", hide_index=True)


def _render_tables_figures(reporting_db: ReportingRegistry, frames: Mapping[str, pd.DataFrame]) -> None:
    study = _current_study(reporting_db)
    if not study:
        st.info("Create/select a report first.")
        return
    if not frames:
        st.warning("No persisted evidence tables are available in this scope.")
        return
    choice = st.selectbox("Evidence artifact", list(frames), key="report15_artifact_choice")
    frame = frames[choice]
    st.dataframe(frame.head(100), width="stretch", hide_index=True)
    mode = st.radio("Build", ["Publication table", "Figure", "Multi-panel figure"], horizontal=True, key="report15_artifact_mode")
    snapshot_id = None  # New table/figure artifacts describe the current evidence; do not retroactively attach them to an older frozen snapshot.
    if mode == "Publication table":
        selected_columns = st.multiselect("Columns", list(frame.columns), default=list(frame.columns[: min(10, len(frame.columns))]), key="report15_table_columns")
        cols = st.columns([3, 2, 1])
        title = cols[0].text_input("Table title", value=choice.split(".")[-1].replace("_", " ").title(), key="report15_table_title")
        caption = cols[1].text_input("Caption", value=f"Persisted AGROLATTICE evidence from {choice}.", key="report15_table_caption")
        decimals = cols[2].number_input("Decimals", 0, 8, 3, key="report15_table_decimals")
        rename_text = st.text_area("Optional column renaming (JSON object)", value="{}", height=70, key="report15_table_rename")
        if st.button("Register publication table", type="primary", key="report15_register_table"):
            try:
                rename = json.loads(rename_text or "{}")
                output = frame[selected_columns].copy()
                for column in output.select_dtypes(include=[np.number]).columns:
                    output[column] = output[column].round(int(decimals))
                output = output.rename(columns={str(k): str(v) for k, v in rename.items()})
                reporting_db.save_artifact(study["study_id"], kind="table", title=title, caption=caption, source={"artifact": choice, "scope": study.get("scope")}, settings={"columns": selected_columns, "decimals": int(decimals), "rename": rename}, data=_frame_bytes(output), suffix=".csv", snapshot_id=snapshot_id)
                st.success("Publication table registered with source/settings provenance.")
            except Exception as exc:
                st.error(f"Could not register table: {exc}")
    elif mode == "Figure":
        chart_types = ["Line", "Scatter", "Bar", "Box", "Violin", "Error bars", "Observed vs predicted", "Residuals", "Time series with interval", "Calibration", "ROC", "Precision-recall", "Confusion matrix", "PCA / climate space", "Spatial points"]
        chart_type = st.selectbox("Figure type", chart_types, key="report15_chart_type")
        columns = list(frame.columns)
        x = st.selectbox("X / observed column", columns, key="report15_x")
        numeric_candidates = [c for c in columns if pd.to_numeric(frame[c], errors="coerce").notna().sum() > 0]
        y = st.multiselect("Y / predicted column(s)", columns, default=numeric_candidates[:1], key="report15_y")
        group = st.selectbox("Group", ["None"] + columns, key="report15_group")
        c1, c2 = st.columns(2)
        lower = c1.selectbox("Lower interval (optional)", ["None"] + numeric_candidates, key="report15_lower")
        upper = c2.selectbox("Upper / error column (optional)", ["None"] + numeric_candidates, key="report15_upper")
        title = st.text_input("Figure title", value=choice.split(".")[-1].replace("_", " ").title(), key="report15_fig_title")
        caption = st.text_area("Figure caption", value=f"AGROLATTICE evidence from {choice}. Interpret according to the stored spatial/temporal support and provenance.", height=80, key="report15_fig_caption")
        dpi = st.selectbox("Output DPI", [300, 600], key="report15_dpi")
        if st.button("Generate and register figure", type="primary", key="report15_register_figure"):
            try:
                kwargs = dict(chart_type=chart_type, x_column=x, y_columns=y, group_column=None if group == "None" else group, title=title, lower_column=None if lower == "None" else lower, upper_column=None if upper == "None" else upper, error_column=None if upper == "None" else upper)
                raw = figure_png(frame, dpi=int(dpi), **kwargs)
                svg = figure_svg(frame, **kwargs)
                fig_source = {"artifact": choice, "scope": study.get("scope")}
                fig_settings = {"chart_type": chart_type, "x": x, "y": y, "group": group, "lower": lower, "upper": upper, "dpi": dpi}
                reporting_db.save_artifact(study["study_id"], kind="figure", title=title, caption=caption, source=fig_source, settings=fig_settings, data=raw, suffix=".png", snapshot_id=snapshot_id)
                reporting_db.save_artifact(study["study_id"], kind="figure_svg", title=title, caption=caption, source=fig_source, settings=fig_settings, data=svg, suffix=".svg", snapshot_id=snapshot_id)
                source_columns = list(dict.fromkeys([c for c in [x] + list(y) + ([] if group == "None" else [group]) + ([] if lower == "None" else [lower]) + ([] if upper == "None" else [upper]) if c in frame.columns]))
                if source_columns:
                    reporting_db.save_artifact(study["study_id"], kind="table", title=f"Figure data — {title}", caption=f"Underlying data used to generate {title}.", source=fig_source, settings={"purpose": "figure source data", "figure_settings": fig_settings}, data=_frame_bytes(frame[source_columns]), suffix=".csv", snapshot_id=snapshot_id)
                st.image(raw, caption=caption)
                st.download_button("Download vector SVG", svg, file_name=f"{re.sub(r'[^A-Za-z0-9_-]+','_',title or 'figure')}.svg", mime="image/svg+xml", key="report15_download_svg")
                st.success("Figure registered as 300/600-dpi PNG plus vector SVG, with underlying CSV and reproducible settings.")
            except Exception as exc:
                st.error(f"Could not create figure: {type(exc).__name__}: {exc}")
    else:
        figures = reporting_db.artifacts(study["study_id"], "figure")
        if figures.empty:
            st.info("Register at least one figure first.")
        else:
            options = figures.to_dict("records")
            selected = st.multiselect("Panels (up to 6)", options, format_func=lambda r: str(r.get("title")), max_selections=6, key="report15_panels")
            title = st.text_input("Multi-panel title", value="Multi-panel figure", key="report15_panel_title")
            caption = st.text_area("Multi-panel caption", value="", key="report15_panel_caption")
            if st.button("Assemble multi-panel figure", disabled=not selected, key="report15_make_panel"):
                raws, labels = [], []
                for idx, row in enumerate(selected):
                    path = Path(str(row.get("file_path") or ""))
                    if path.exists():
                        raws.append(path.read_bytes())
                        labels.append(chr(65 + idx))
                raw = multi_panel_png(raws, labels=labels, dpi=300)
                reporting_db.save_artifact(study["study_id"], kind="figure", title=title, caption=caption, source={"component_artifact_ids": [r.get("artifact_id") for r in selected]}, settings={"layout": "automatic", "panel_labels": labels}, data=raw, suffix=".png", snapshot_id=snapshot_id)
                st.image(raw, caption=caption or title)
    st.markdown("### Standard scientific tables")
    st.caption("Generate common report tables directly from the persisted evidence currently visible to the report scope. The source artifact remains recorded.")
    standard_options = [name for name in [
        "experiment.factors", "experiment.experimental_units", "experiment.flowering_observations", "experiment.harvest_outcomes",
        "models.training_runs", "models.validation_runs", "models.registered_models", "twin.calibration_runs", "twin.root_zone_stage_summary",
        "field.operations", "field.scouting_observations", "evidence.predictions", "evidence.treatment_outcomes"
    ] if name in frames]
    if standard_options:
        standard_choice = st.selectbox("Standard evidence table", standard_options, key="report15_standard_table")
        if st.button("Register standard table", key="report15_register_standard"):
            standard_frame = frames[standard_choice].copy()
            reporting_db.save_artifact(study["study_id"], kind="table", title=standard_choice.split(".")[-1].replace("_", " ").title(), caption=f"Persisted AGROLATTICE evidence from {standard_choice}.", source={"artifact": standard_choice, "standard_table": True}, settings={"generated": "standard scientific table"}, data=_frame_bytes(standard_frame), suffix=".csv")
            st.success("Standard table registered.")
            st.rerun()
    else:
        st.caption("No standard table source is available in the selected scope yet.")
    saved = reporting_db.artifacts(study["study_id"])
    if not saved.empty:
        st.markdown("### Registered tables & figures")
        st.dataframe(saved[[c for c in ["kind", "title", "caption", "sha256", "created_at"] if c in saved.columns]], width="stretch", hide_index=True)


def _freeze_snapshot(reporting_db: ReportingRegistry, study: Mapping[str, Any], frames: Mapping[str, pd.DataFrame], scope: Mapping[str, Any], readiness: Mapping[str, Any]) -> str:
    artifact_manifest = {name: {"rows": len(frame), "columns": list(map(str, frame.columns)), "sha256_csv": sha256_bytes(_frame_bytes(frame))} for name, frame in frames.items()}
    manifest = {"scope": dict(scope), "readiness": dict(readiness), "artifacts": artifact_manifest, "counts": {"artifacts": len(frames), "rows": int(sum(len(f) for f in frames.values())), "training_runs": len(frames.get("models.training_runs", pd.DataFrame())), "validation_runs": len(frames.get("models.validation_runs", pd.DataFrame()))}, "frozen_utc": datetime.now(timezone.utc).isoformat()}
    snapshot_id = reporting_db.save_snapshot(study["study_id"], label=f"Evidence freeze {datetime.now().strftime('%Y-%m-%d %H:%M')}", scope=scope, manifest=manifest)
    for name, frame in frames.items():
        reporting_db.save_artifact(study["study_id"], kind="snapshot_table", title=name, caption="Immutable report-evidence snapshot table.", source={"artifact": name}, settings={"frozen": True}, data=_frame_bytes(frame), suffix=".csv", snapshot_id=snapshot_id)
    return snapshot_id


def _render_evidence_claims(reporting_db: ReportingRegistry, frames: Mapping[str, pd.DataFrame], scope: Mapping[str, Any], readiness: Mapping[str, Any]) -> None:
    study = _current_study(reporting_db)
    if not study:
        st.info("Create/select a report first.")
        return
    snapshots = reporting_db.snapshots(study["study_id"])
    cols = st.columns([3, 1])
    cols[0].markdown("### Evidence snapshots")
    if cols[1].button("Freeze current evidence", type="primary", key="report15_freeze"):
        snapshot_id = _freeze_snapshot(reporting_db, study, frames, scope, readiness)
        st.success(f"Frozen evidence snapshot {snapshot_id[:8]}. Subsequent database changes will not alter the snapshot-table files or their recorded hashes.")
        st.rerun()
    if not snapshots.empty:
        st.dataframe(snapshots[[c for c in ["snapshot_id", "label", "manifest_sha256", "created_at"] if c in snapshots.columns]], width="stretch", hide_index=True)
    st.markdown("### Claim ledger")
    c1, c2 = st.columns([3, 1])
    claim_text = c1.text_area("Scientific claim", placeholder="Example: Male sowing strategy A reduced the observed synchrony gap relative to current practice.", key="report15_claim_text")
    evidence_type = c2.selectbox("Evidence type", EVIDENCE_TYPES, key="report15_claim_type")
    source_reference = st.text_input("Evidence source", placeholder="e.g. Table artifact ID, validation run ID, mixed-model result, causal analysis ID", key="report15_claim_source")
    statistic = st.text_input("Effect/statistic and uncertainty", placeholder="e.g. Δ=-1.4 d; 95% CI -2.2 to -0.6; n=48", key="report15_claim_stat")
    notes = st.text_area("Claim notes", value="", height=70, key="report15_claim_notes")
    warnings = audit_claim_text(claim_text, evidence_type=evidence_type, statistic=statistic, source_reference=source_reference) if claim_text else []
    for warning in warnings:
        st.warning(warning)
    if st.button("Add claim to ledger", disabled=not claim_text.strip(), key="report15_add_claim"):
        reporting_db.save_claim(study["study_id"], text=claim_text, evidence_type=evidence_type, source_reference=source_reference, statistic=statistic, status="Needs review" if warnings else "Evidence linked", notes=notes)
        st.success("Claim saved.")
        st.rerun()
    claims = reporting_db.claims(study["study_id"])
    if not claims.empty:
        st.dataframe(claims[[c for c in ["claim_text", "evidence_type", "source_reference", "statistic", "status", "updated_at"] if c in claims.columns]], width="stretch", hide_index=True)
    st.markdown("### Results Builder")
    st.caption("Generate a checked numerical result block from a selected persisted table. This creates a draft statement for author review; it is not automatically inserted into the manuscript.")
    numeric_sources = {name: frame for name, frame in frames.items() if isinstance(frame, pd.DataFrame) and any(pd.to_numeric(frame[c], errors="coerce").notna().sum() > 0 for c in frame.columns)}
    if numeric_sources:
        result_source = st.selectbox("Result source", list(numeric_sources), key="report15_result_source")
        result_frame = numeric_sources[result_source]
        numeric_cols = [c for c in result_frame.columns if pd.to_numeric(result_frame[c], errors="coerce").notna().sum() > 0]
        result_col = st.selectbox("Numeric variable", numeric_cols, key="report15_result_col")
        group_candidates = [c for c in result_frame.columns if c != result_col and result_frame[c].nunique(dropna=True) <= 30]
        result_group = st.selectbox("Optional grouping", ["None"] + group_candidates, key="report15_result_group")
        values = pd.to_numeric(result_frame[result_col], errors="coerce")
        if result_group == "None":
            n = int(values.notna().sum()); mean = float(values.mean()) if n else float("nan"); sd = float(values.std(ddof=1)) if n > 1 else float("nan")
            draft_result = f"{result_col}: n={n}, mean={mean:.3g}" + (f", SD={sd:.3g}." if np.isfinite(sd) else ".")
        else:
            summaries=[]
            for group, subset in result_frame.groupby(result_group, dropna=False):
                v=pd.to_numeric(subset[result_col],errors="coerce"); n=int(v.notna().sum())
                if n: summaries.append(f"{group}: n={n}, mean={float(v.mean()):.3g}")
            draft_result = f"{result_col} by {result_group}: " + "; ".join(summaries[:12]) + "."
        st.code(draft_result, language=None)
        if st.button("Use this as a new claim draft", key="report15_result_to_claim"):
            reporting_db.save_claim(study["study_id"], text=draft_result, evidence_type="Derived", source_reference=result_source, statistic=draft_result, status="Needs author interpretation", notes="Generated by Results Builder from persisted evidence; descriptive summary only.")
            st.success("Result block added to the claim ledger for review.")
            st.rerun()
    st.markdown("### Citation Library")
    citations = reporting_db.citations()
    linked = reporting_db.study_citations(study["study_id"])
    if not citations.empty:
        options = citations.to_dict("records")
        choice = st.selectbox("Available citation", options, format_func=lambda r: f"{r.get('authors')} ({r.get('year')}) · {r.get('title')}", key="report15_citation_choice")
        purpose = st.text_input("Citation purpose", value="Method / background", key="report15_citation_purpose")
        if st.button("Link citation to report", key="report15_link_citation"):
            reporting_db.link_citation(study["study_id"], str(choice.get("citation_id")), purpose)
            st.rerun()
    with st.expander("Add a manual citation", expanded=False):
        c1, c2 = st.columns(2)
        doi = c1.text_input("DOI (optional)", key="report15_manual_doi")
        year = c2.number_input("Year", min_value=1800, max_value=2100, value=datetime.now().year, key="report15_manual_year")
        authors = st.text_input("Authors", key="report15_manual_authors")
        title = st.text_input("Title", key="report15_manual_title")
        journal = st.text_input("Journal / source", key="report15_manual_journal")
        bibtex = st.text_area("BibTeX (optional)", key="report15_manual_bibtex")
        ris = st.text_area("RIS (optional)", key="report15_manual_ris")
        if st.button("Add citation", disabled=not title.strip(), key="report15_add_citation"):
            cid = reporting_db.add_citation({"doi": doi, "year": int(year), "authors": authors, "title": title, "journal": journal, "bibtex": bibtex, "ris": ris, "source": "User-added citation"})
            reporting_db.link_citation(study["study_id"], cid, "User-selected")
            st.success("Citation added and linked.")
            st.rerun()
    if not linked.empty:
        st.dataframe(linked[[c for c in ["authors", "year", "title", "journal", "doi", "purpose"] if c in linked.columns]], width="stretch", hide_index=True)


def _render_reproducibility(reporting_db: ReportingRegistry, app_root: Path, app_version: str, frames: Mapping[str, pd.DataFrame], scope: Mapping[str, Any], readiness: Mapping[str, Any], ai_audit_callback: Callable[[Mapping[str, Any]], None] | None = None) -> None:
    study = _current_study(reporting_db)
    if not study:
        st.info("Create/select a report first.")
        return
    snapshots = reporting_db.snapshots(study["study_id"])
    snapshot = reporting_db.snapshot(str(snapshots.iloc[0]["snapshot_id"])) if not snapshots.empty else None
    inferred = infer_methods(frames)
    selected_methods = st.multiselect("Methods used in this report", list(METHODS_REGISTRY), default=inferred, key="report15_methods_selected")
    if selected_methods:
        method_rows = []
        for method in selected_methods:
            record = METHODS_REGISTRY.get(method, {})
            method_rows.append({"Method": method, "AGROLATTICE relationship": record.get("relationship"), "Source/reference": " | ".join(record.get("references", []))})
        st.dataframe(pd.DataFrame(method_rows), width="stretch", hide_index=True)
        st.caption("Use this table to compare the implemented/adapted method with its source. A paper citation does not imply exact reproduction of proprietary data, code, training procedures or validation scope.")
    include_climate_hash = st.checkbox("Calculate SHA-256 for installed country climate files when building package (slower for very large files)", value=False, key="report15_hash_climate")
    manifest = _build_reproducibility_manifest(app_root=app_root, app_version=app_version, study=study, scope=scope, snapshot=snapshot, frames=frames, methods=selected_methods, include_climate_hash=False)
    manifest["readiness"] = dict(readiness)
    st.markdown("### Reproducibility status")
    db_rows = []
    for name, record in manifest["databases"].items():
        db_rows.append({"Database": name, "Exists": record.get("exists"), "Schema": (record.get("metadata") or {}).get("schema_version"), "Integrity": record.get("integrity_check"), "FK violations": record.get("foreign_key_violations")})
    st.dataframe(pd.DataFrame(db_rows), width="stretch", hide_index=True)
    st.caption("Raw manifests are available below for audit, but the researcher-facing summary is shown first.")
    with st.expander("Advanced provenance manifest", expanded=False):
        st.json(manifest)
    tables, figures = _saved_artifact_frames(reporting_db, study["study_id"])
    claims_df = reporting_db.claims(study["study_id"])
    claims = claims_df.to_dict("records") if not claims_df.empty else []
    citations_df = reporting_db.study_citations(study["study_id"])
    citations = citations_df.to_dict("records") if not citations_df.empty else []
    audit_rows = report_audit({**study, **(study.get("manuscript") or {}), "journal": study.get("target_journal")}, claims=claims, figure_count=len(figures), table_count=len(tables), citation_count=len(citations), snapshot_present=bool(snapshot), evidence_manifest={**manifest, "readiness": readiness, "counts": {"training_runs": len(frames.get("models.training_runs", pd.DataFrame()))}})
    st.markdown("### Scientific reporting audit")
    if audit_rows:
        audit_frame = pd.DataFrame(audit_rows)
        st.dataframe(audit_frame, width="stretch", hide_index=True)
    else:
        st.success("No automated report-audit warnings were generated. Author/statistical review is still required.")
    if ai_audit_callback is not None:
        with st.expander("Optional AI-assisted evidence audit", expanded=False):
            st.caption("AI output is a draft audit of the frozen/current evidence. It must not invent measurements, significance or references and requires author review.")
            ai_audit_callback({"study": study, "scope": scope, "readiness": readiness, "claims": claims, "audit": audit_rows, "manifest_summary": {"snapshot": snapshot, "methods": selected_methods}})
    st.markdown("### Build research package")
    privacy = st.radio("Privacy profile", ["Internal research package", "Public package"], horizontal=True, key="report15_privacy")
    redaction = {"coordinates": False, "field_names": False, "genotypes": False, "researcher_names": False}
    if privacy == "Public package":
        rcols = st.columns(4)
        redaction["coordinates"] = rcols[0].checkbox("Redact exact coordinates", value=True, key="report15_redact_coord")
        redaction["field_names"] = rcols[1].checkbox("Redact private field names", value=True, key="report15_redact_fields")
        redaction["genotypes"] = rcols[2].checkbox("Redact genotype identifiers", value=False, key="report15_redact_genotypes")
        redaction["researcher_names"] = rcols[3].checkbox("Redact researcher names", value=False, key="report15_redact_people")
        st.info("The export will record the exact redaction rules applied. Review the package before public release; automated column-name matching cannot guarantee de-identification of every free-text field.")
    if st.button("Build complete reproducibility package", type="primary", key="report15_build_package"):
        manifest = _build_reproducibility_manifest(app_root=app_root, app_version=app_version, study=study, scope=scope, snapshot=snapshot, frames=frames, methods=selected_methods, include_climate_hash=include_climate_hash)
        manifest["readiness"] = dict(readiness)
        package_study = {**study, **(study.get("manuscript") or {}), "authors": study.get("authors") or [], "affiliations": study.get("affiliations") or [], "journal": study.get("target_journal"), "report_type": study.get("report_type")}
        package = build_publication_package(study=package_study, selected_methods=selected_methods, selected_tables=tables, figures=figures, reproducibility=manifest, citations=citations, claims=claims, privacy_profile=privacy, redaction_options=redaction, package_type="AGROLATTICE research reproduction package")
        latest_version = reporting_db.latest_version(study["study_id"])
        export_id = reporting_db.save_export(study["study_id"], package_type="Complete reproducibility package", privacy_profile=privacy, data=package, manifest=manifest, version_id=latest_version.get("version_id") if latest_version else None)
        st.session_state["report15_package_bytes"] = package
        st.session_state["report15_package_name"] = f"{re.sub(r'[^A-Za-z0-9_-]+','_',study.get('short_title') or 'agrolattice_report')}_package.zip"
        st.success(f"Package built and registered as {export_id[:8]}.")
    if st.session_state.get("report15_package_bytes"):
        st.download_button("Download research package", st.session_state["report15_package_bytes"], file_name=st.session_state.get("report15_package_name", "agrolattice_report_package.zip"), mime="application/zip", width="stretch", key="report15_download_package")
    exports = reporting_db.exports(study["study_id"])
    if not exports.empty:
        st.markdown("### Export history")
        st.dataframe(exports[[c for c in ["package_type", "privacy_profile", "sha256", "created_at"] if c in exports.columns]], width="stretch", hide_index=True)


def _render_library(reporting_db: ReportingRegistry) -> None:
    st.markdown("### Report Library")
    studies = reporting_db.studies()
    if studies.empty:
        st.info("No reports have been created yet.")
        return
    query = st.text_input("Search reports", value="", key="report15_library_search")
    view = studies.copy()
    if query.strip():
        mask = view.astype(str).apply(lambda col: col.str.contains(query, case=False, na=False)).any(axis=1)
        view = view[mask]
    st.dataframe(view, width="stretch", hide_index=True)
    options = view.to_dict("records")
    if options:
        selected = st.selectbox("Open report", options, format_func=lambda r: f"{r.get('title')} · {r.get('report_type')} · {r.get('updated_at')}", key="report15_library_open")
        if st.button("Set as active report", key="report15_set_active"):
            st.session_state["report15_active_study_id"] = str(selected.get("study_id"))
            st.session_state["report15_nav"] = "Publications"
            st.rerun()
        sid = str(selected.get("study_id"))
        cols = st.columns(4)
        cols[0].metric("Versions", len(reporting_db.versions(sid)))
        cols[1].metric("Snapshots", len(reporting_db.snapshots(sid)))
        cols[2].metric("Claims", len(reporting_db.claims(sid)))
        cols[3].metric("Exports", len(reporting_db.exports(sid)))
        with st.expander("Audit trail", expanded=False):
            audit = reporting_db.audit_log(sid, limit=500)
            st.dataframe(audit, width="stretch", hide_index=True)


def render_report_command_centre(*, reporting_db: ReportingRegistry, app_root: str | Path, app_version: str, field_db, pollination_db, twin_db, research_registry, active_field_id: str | None = None, active_trial_id: str | None = None, legacy_study_root: str | Path | None = None, ai_audit_callback: Callable[[Mapping[str, Any]], None] | None = None) -> None:
    app_root = Path(app_root)
    default_scope = _normalise_scope(field_db, pollination_db, twin_db, active_field_id, active_trial_id)
    st.markdown("## Reports & Publication")
    st.caption("Convert persistent field, experiment, Twin, model and decision evidence into traceable scientific reports, manuscripts, figures and reproducibility packages.")
    with st.container(border=True):
        scope = _report_context_selector(field_db, pollination_db, twin_db, default_scope)
        st.markdown(f"**Active reporting context:** {_scope_label(scope)}")
    frames, manifest = collect_persistent_artifacts(field_db=field_db, pollination_db=pollination_db, twin_db=twin_db, registry=research_registry, scope=scope)
    studies = reporting_db.studies()
    active_study = _current_study(reporting_db)
    default_type = active_study.get("report_type") if active_study else ("Maize Synchrony report" if scope.get("trial_id") else "Field season report" if scope.get("field_id") else "Full scientific manuscript")
    report_type = default_type if default_type in REPORT_TYPES else "Full scientific manuscript"
    readiness = report_readiness(report_type, frames, scope)
    nav = st.radio("Report workspace", REPORT_NAV, horizontal=True, key="report15_nav")
    st.divider()
    if nav == "Overview":
        _render_overview(reporting_db, studies, frames, readiness, scope, report_type)
    elif nav == "Report Builder":
        _render_report_builder(reporting_db, frames, scope, report_type, Path(legacy_study_root or app_root / "study_store"))
    elif nav == "Publications":
        _render_publications(reporting_db, readiness, frames)
    elif nav == "Tables & Figures":
        _render_tables_figures(reporting_db, frames)
    elif nav == "Evidence & Claims":
        _render_evidence_claims(reporting_db, frames, scope, readiness)
    elif nav == "Reproducibility":
        _render_reproducibility(reporting_db, app_root, app_version, frames, scope, readiness, ai_audit_callback=ai_audit_callback)
    else:
        _render_library(reporting_db)
