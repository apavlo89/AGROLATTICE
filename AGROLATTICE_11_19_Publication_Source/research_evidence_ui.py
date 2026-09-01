"""Streamlit research-model UI for AGROLATTICE 11.15 scientific model governance."""
from __future__ import annotations

import io
import json
import re
import uuid
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Sequence

import joblib
import numpy as np
import pandas as pd
import streamlit as st

from agricultural_validation import AgriculturalValidationError, applicability_score, build_protocol_folds
from multimodal_fusion import fit_fusion, fusion_manifest, predict_fusion
from pest_early_warning import (
    SOURCE_DOI as PEST_SOURCE_DOI,
    SOURCE_METHOD as PEST_SOURCE_METHOD,
    available_baselines as pest_available_baselines,
    compare_pest_models,
    dependency_status as pest_dependency_status,
    disease_risk_note,
    engineer_environmental_pest_features,
    fit_pest_model,
    recommended_feature_columns,
    resolve_paper_columns,
    shap_feature_importance,
    tune_catboost,
)
from phenology_service import (
    consensus_table,
    disagreement_summary,
    generic_gdd_stage_estimate,
    mechanistic_maize_estimate,
)
from research_benchmarks import benchmark_catalog, inspect_local_table
from research_models import (
    available_model_names,
    compare_models,
    conformal_half_width_from_oof,
    dependency_status as model_dependency_status,
    fit_final_model,
)
from research_registry import MODEL_STATUSES, ResearchEvidenceRegistry, json_value
from gxem_data_builder import build_maize_gxem_table
from hybrid_residual import fit_hybrid_residual, hybrid_manifest, predict_hybrid
from research_data_hub import (
    aggregate_daily_weather,
    fetch_canonical_nasa_weather,
    field_coordinates,
    field_record_tables,
    installed_climate_locations,
    installed_monthly_climate,
    merge_weather_with_labels,
    nasa_pest_covariates,
    table_profile,
)
from weak_supervised_yield import fit_weak_yield_model, predict_fine_resolution, weak_supervision_manifest

MODULE_VERSION = "3.0.0"


def _safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(text).strip()).strip("_") or "model"


def _read_uploaded_table(uploaded) -> pd.DataFrame:
    name = str(uploaded.name).casefold()
    payload = uploaded.getvalue()
    if name.endswith(".csv"):
        return pd.read_csv(io.BytesIO(payload))
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(payload))
    if name.endswith((".parquet", ".pq")):
        return pd.read_parquet(io.BytesIO(payload))
    raise ValueError("Upload CSV, Excel or Parquet.")


def _current_context_ids() -> tuple[str | None, str | None, int | None]:
    """Return the active spatial IDs and the best available project-season year.

    Field and pollination trial IDs use the same session keys as the existing
    Release 11.2 workspaces.  Season is deliberately treated as optional: the
    research registry must never invent a year when the active project does not
    provide one.
    """
    field_id = st.session_state.get("field_ops_active_field_id")
    trial_id = st.session_state.get("pollination_active_trial_id")
    season = None

    # Release 11.2 stores the active project as a dictionary whose season block
    # contains planting_date.  Retain the legacy key as a harmless fallback for
    # sessions created by early 11.3 development builds.
    candidates = [st.session_state.get("release10_context_season")]
    active_project = st.session_state.get("active_project")
    if isinstance(active_project, dict):
        project_season = active_project.get("season") or {}
        planting_date = project_season.get("planting_date") if isinstance(project_season, dict) else None
        if planting_date:
            candidates.append(str(planting_date)[:4])

    for candidate in candidates:
        try:
            if candidate not in (None, ""):
                season = int(candidate)
                break
        except (TypeError, ValueError):
            continue
    return (str(field_id) if field_id else None, str(trial_id) if trial_id else None, season)


def _render_data_readiness(
    frame: pd.DataFrame,
    *,
    target: str,
    features: Sequence[str],
    protocol: str,
    split_column: str | None = None,
    minimum_rows: int = 8,
    label: str = "Model data readiness",
) -> bool:
    """Render a compact, non-causal readiness check before model fitting."""
    observed = int(frame[target].notna().sum()) if target in frame else 0
    usable_features = [feature for feature in features if feature in frame]
    feature_complete = float(frame[usable_features].notna().mean().mean() * 100) if usable_features else 0.0
    split_levels = int(frame[split_column].dropna().nunique()) if split_column and split_column in frame else None
    with st.expander(label, expanded=False):
        columns = st.columns(4)
        columns[0].metric("Rows", len(frame))
        columns[1].metric("Observed target", observed)
        columns[2].metric("Predictors", len(usable_features))
        columns[3].metric("Mean feature completeness", f"{feature_complete:.1f}%")
        issues: list[str] = []
        if observed < minimum_rows:
            issues.append(f"Only {observed} observed outcomes are available; at least {minimum_rows} are required by this workflow.")
        if not usable_features:
            issues.append("No predictor features are selected.")
        if split_column and split_levels is not None:
            st.caption(f"{protocol} split column: {split_column} · {split_levels} distinct non-missing levels")
            if split_levels < 2:
                issues.append(f"{protocol} requires at least two distinct values in {split_column}.")
        if protocol == "Random diagnostic CV":
            st.warning("Random CV is retained as a diagnostic. Do not use it as evidence of transfer to unseen sites, seasons, fields, genotypes or future time periods.")
        if issues:
            for issue in issues:
                st.warning(issue)
        else:
            st.success("Minimum structural checks passed. This does not establish that sample size, representativeness or deployment coverage are scientifically adequate.")
    return observed >= minimum_rows and bool(usable_features) and (split_levels is None or split_levels >= 2)


def _dataset_registration(registry: ResearchEvidenceRegistry, frame: pd.DataFrame, uploaded, *, source_label: str) -> str | None:
    with st.expander("Register this dataset snapshot", expanded=False):
        name = st.text_input("Dataset name", value=Path(uploaded.name).stem, key=f"dataset_name_{source_label}")
        licence = st.text_input("Licence / access terms", value="User-provided; verify redistribution rights", key=f"dataset_licence_{source_label}")
        crop_scope = st.text_input("Crop scope", value="", key=f"dataset_crop_{source_label}")
        geography = st.text_input("Geography scope", value="", key=f"dataset_geo_{source_label}")
        if st.button("Register dataset metadata", key=f"register_dataset_{source_label}"):
            dataset_id = registry.register_dataset({
                "name": name,
                "dataset_type": "Uploaded research table",
                "source": source_label,
                "licence": licence,
                "crop_scope": crop_scope,
                "geography_scope": geography,
                "provenance": {"uploaded_filename": uploaded.name, "rows": len(frame), "columns": list(frame.columns)},
                "notes": "Raw uploaded bytes are not copied into the protected AGROLATTICE databases. Register a stable local source separately if long-term reproducibility is required.",
            })
            st.session_state[f"registered_dataset_{source_label}"] = dataset_id
            st.success(f"Dataset registered: {dataset_id[:8]}")
        return st.session_state.get(f"registered_dataset_{source_label}")



def _hub_table() -> tuple[pd.DataFrame | None, dict[str, Any]]:
    frame = st.session_state.get("research_data_frame_11_4")
    metadata = st.session_state.get("research_data_metadata_11_4") or {}
    return (frame if isinstance(frame, pd.DataFrame) else None, metadata if isinstance(metadata, dict) else {})


def _set_hub_table(frame: pd.DataFrame, metadata: Mapping[str, Any], *, name: str) -> None:
    st.session_state["research_data_frame_11_4"] = frame.copy()
    st.session_state["research_data_metadata_11_4"] = dict(metadata)
    st.session_state["research_data_name_11_4"] = str(name)
    # A newly selected/retrieved table is a new snapshot. Never retain the
    # dataset ID of a previously registered hub table.
    st.session_state.pop("research_data_dataset_id_11_4", None)


def _research_table_source(*, key: str, label: str = "Data source") -> tuple[pd.DataFrame | None, Any | None, str]:
    hub, hub_meta = _hub_table()
    gxem = st.session_state.get("gxem_table_11_4")
    choices = ["Upload external table"]
    if isinstance(gxem, pd.DataFrame) and not gxem.empty:
        choices.insert(0, "Experiment / G×E×M session table")
    if isinstance(hub, pd.DataFrame) and not hub.empty:
        choices.insert(0, "Research Data Hub session")
    source = st.radio(label, choices, horizontal=True, key=f"{key}_source")
    if source == "Research Data Hub session":
        st.caption(f"Using Data Hub table: {st.session_state.get('research_data_name_11_4','retrieved table')} · {len(hub):,} rows · {len(hub.columns)} columns")
        return hub.copy(), None, source
    if source == "Experiment / G×E×M session table":
        st.caption(f"Using analysis-ready experiment/G×E×M table · {len(gxem):,} rows · {len(gxem.columns)} columns. Trial/block/replicate identifiers remain available for grouped validation.")
        return gxem.copy(), None, source
    uploaded = st.file_uploader("External table", type=["csv", "xlsx", "xls", "parquet"], key=f"{key}_upload")
    return (_read_uploaded_table(uploaded), uploaded, source) if uploaded is not None else (None, None, source)


def _register_retrieved_dataset(registry: ResearchEvidenceRegistry, frame: pd.DataFrame, metadata: Mapping[str, Any], *, name: str) -> str:
    dataset_id = registry.register_dataset({
        "name": name,
        "dataset_type": str(metadata.get("dataset_type") or "Retrieved environmental/field table"),
        "source": str(metadata.get("source") or "AGROLATTICE Research Data Hub"),
        "source_version": str(metadata.get("source_version") or "11.4"),
        "licence": str(metadata.get("licence") or "Source-specific; see provenance"),
        "crop_scope": metadata.get("crop_scope"),
        "geography_scope": metadata.get("geography_scope"),
        "spatial_resolution": metadata.get("spatial_resolution"),
        "temporal_resolution": metadata.get("temporal_resolution"),
        "provenance": {**dict(metadata), "rows": len(frame), "columns": list(frame.columns)},
        "notes": str(metadata.get("scientific_note") or "Retrieved data retain source provenance. Environmental data are not agronomic outcome labels."),
    })
    st.session_state["research_data_dataset_id_11_4"] = dataset_id
    return dataset_id


def render_research_data_hub_page(
    *,
    registry: ResearchEvidenceRegistry,
    field_db: Any | None,
    climate_frame: pd.DataFrame | None,
    cache_dir: str | Path,
    selected_country: str,
) -> None:
    st.markdown("### Research Data Hub")
    st.caption("Retrieve environmental and existing AGROLATTICE data directly instead of rebuilding every research table by CSV. Weather retrieval reuses the established NASA POWER client and the full 19-variable AGROLATTICE climate profile. Measured outcomes such as yield, pest presence, phenotypes and seed purity are never invented from weather.")

    tabs = st.tabs(["NASA weather", "Installed climate dataset", "Field records", "Current app data", "Session table & provenance"])
    with tabs[0]:
        fields = field_db.fields() if field_db is not None else pd.DataFrame()
        mode_options = ["Manual coordinates"]
        if not fields.empty:
            mode_options.insert(0, "Mapped field")
        mode = st.radio("Location", mode_options, horizontal=True, key="datahub_nasa_location_mode")
        field_id = None
        if mode == "Mapped field":
            active = st.session_state.get("field_ops_active_field_id")
            ids = fields["field_id"].astype(str).tolist()
            default_index = ids.index(str(active)) if active and str(active) in ids else 0
            field_id = st.selectbox(
                "Field", ids, index=default_index,
                format_func=lambda value: f"{fields.loc[fields.field_id.astype(str).eq(str(value)), 'farm_name'].iloc[0]} · {fields.loc[fields.field_id.astype(str).eq(str(value)), 'name'].iloc[0]}",
                key="datahub_nasa_field",
            )
            field = field_db.field(str(field_id))
            lat, lon = field_coordinates(field)
            st.caption(f"Field centroid: {lat:.5f}, {lon:.5f}. The exact polygon remains authoritative for spatial EO; NASA POWER is a point/grid environmental estimate at the centroid.")
        else:
            c1, c2 = st.columns(2)
            lat = c1.number_input("Latitude", value=float(st.session_state.get("datahub_lat", 0.0)), format="%.6f", key="datahub_lat")
            lon = c2.number_input("Longitude", value=float(st.session_state.get("datahub_lon", 0.0)), format="%.6f", key="datahub_lon")
        c1, c2, c3 = st.columns(3)
        start = c1.date_input("Start date", value=date(date.today().year - 2, 1, 1), key="datahub_nasa_start")
        end = c2.date_input("End date", value=date.today(), key="datahub_nasa_end")
        frequency = c3.selectbox("Output resolution", ["Daily", "Weekly", "Monthly"], key="datahub_nasa_frequency")
        force = st.checkbox("Force refresh instead of using the local NASA cache", value=False, key="datahub_nasa_force")
        if st.button("Retrieve NASA POWER data", type="primary", key="datahub_fetch_nasa"):
            try:
                with st.spinner("Retrieving and harmonising NASA POWER weather..."):
                    acquired = fetch_canonical_nasa_weather(
                        latitude=float(lat), longitude=float(lon), start_date=start, end_date=end,
                        cache_dir=cache_dir, force_refresh=force,
                    )
                    output = aggregate_daily_weather(acquired.frame, frequency)
                meta = dict(acquired.metadata)
                meta.update({
                    "dataset_type": "Retrieved daily agroclimate" if frequency == "Daily" else f"Retrieved {frequency.lower()} agroclimate",
                    "temporal_resolution": frequency.lower(),
                    "geography_scope": selected_country,
                    "field_id": field_id,
                    "aggregation": frequency,
                })
                _set_hub_table(output, meta, name=f"NASA POWER {frequency} · {start} to {end}")
                st.success(f"Retrieved {len(output):,} {frequency.lower()} rows. Data are now available to Phenology, Pest Early Warning, Model Lab, Hybrid Twin Learning and Multimodal Fusion.")
            except Exception as error:
                st.error(str(error))
        hub, meta = _hub_table()
        if isinstance(hub, pd.DataFrame) and meta.get("source") == "NASA POWER Daily Point API":
            st.dataframe(hub.head(200), hide_index=True, width="stretch")
            st.json({k: v for k, v in meta.items() if k not in {"canonical_provenance", "request_metadata"}})

    with tabs[1]:
        locations = installed_climate_locations(climate_frame if isinstance(climate_frame, pd.DataFrame) else pd.DataFrame())
        if locations.empty:
            st.info(f"No installed country climate dataset is available for {selected_country}. Use Dataset updater to create/update it; NASA point retrieval above remains available.")
        else:
            labels = locations.apply(lambda r: f"{r.get('CITY','')} · {r.get('STATE','')}", axis=1).tolist()
            selected = st.selectbox("Installed location", range(len(locations)), format_func=lambda i: labels[i], key="datahub_installed_location")
            row = locations.iloc[int(selected)]
            location_mask = climate_frame['CITY'].astype(str).eq(str(row['CITY']))
            if 'STATE' in climate_frame.columns and pd.notna(row.get('STATE')):
                location_mask &= climate_frame['STATE'].astype(str).eq(str(row.get('STATE')))
            years = sorted(pd.to_numeric(climate_frame.loc[location_mask, 'Year'], errors='coerce').dropna().astype(int).unique().tolist())
            if years:
                c1, c2 = st.columns(2)
                start_year = c1.selectbox("Start year", years, index=0, key="datahub_installed_start")
                end_year = c2.selectbox("End year", years, index=len(years)-1, key="datahub_installed_end")
                if st.button("Load installed 19-variable climate history", key="datahub_load_installed"):
                    try:
                        acquired = installed_monthly_climate(climate_frame, city=str(row["CITY"]), state=str(row["STATE"]), start_year=int(start_year), end_year=int(end_year))
                        meta = dict(acquired.metadata); meta.update({"geography_scope": selected_country, "dataset_type": "Installed AGROLATTICE climate history"})
                        _set_hub_table(acquired.frame, meta, name=f"Installed climate · {row['CITY']} · {start_year}-{end_year}")
                        st.success(f"Loaded {len(acquired.frame):,} monthly rows from the installed {selected_country} dataset.")
                    except Exception as error:
                        st.error(str(error))

    with tabs[2]:
        if field_db is None:
            st.info("Field Operations database is unavailable in this context.")
        else:
            fields = field_db.fields()
            if fields.empty:
                st.info("No mapped fields exist yet. Create a field in Fields & Operations first.")
            else:
                active = st.session_state.get("field_ops_active_field_id")
                ids = fields["field_id"].astype(str).tolist()
                field_id = st.selectbox("Field", ids, index=ids.index(str(active)) if active and str(active) in ids else 0, format_func=lambda value: f"{fields.loc[fields.field_id.astype(str).eq(str(value)), 'farm_name'].iloc[0]} · {fields.loc[fields.field_id.astype(str).eq(str(value)), 'name'].iloc[0]}", key="datahub_records_field")
                tables = field_record_tables(field_db, field_id)
                options = [name for name, frame in tables.items() if isinstance(frame, pd.DataFrame) and not frame.empty]
                if not options:
                    st.info("This field currently has no saved scouting, operation, sensor, nutrient or crop-history records.")
                else:
                    table_name = st.selectbox("Existing record type", options, key="datahub_record_type")
                    frame = tables[table_name]
                    st.dataframe(frame.head(200), hide_index=True, width="stretch")
                    if st.button("Use these existing field records in Research Data Hub", key="datahub_use_field_records"):
                        meta = {
                            "source": "AGROLATTICE Field Operations database",
                            "dataset_type": f"Existing field {table_name}",
                            "field_id": field_id,
                            "temporal_resolution": "record/event",
                            "geography_scope": selected_country,
                            "scientific_note": "These are existing user records; measurement quality and semantics remain those entered in Field Operations.",
                        }
                        _set_hub_table(frame, meta, name=f"Field records · {table_name}")
                        st.success("Field records are now available to research tools without exporting/re-uploading CSV.")
                    if table_name == "observations" and cache_dir is not None and "observed_at" in frame.columns:
                        st.markdown("##### Enrich scouting observations with NASA weather")
                        st.caption("This attaches environmental covariates to existing scouting records by date. A scouting presence-only log is not a valid absence/no-pest training dataset unless true absence observations were actually recorded.")
                        tolerance = st.slider("Maximum date matching tolerance (days)", 0, 14, 3, key="datahub_obs_weather_tolerance")
                        if st.button("Retrieve NASA weather and join to scouting dates", key="datahub_enrich_observations"):
                            try:
                                field = field_db.field(str(field_id)); lat, lon = field_coordinates(field)
                                dates = pd.to_datetime(frame["observed_at"], errors="coerce").dropna()
                                if dates.empty:
                                    raise ValueError("Scouting observations have no valid dates.")
                                acquired = fetch_canonical_nasa_weather(latitude=lat, longitude=lon, start_date=(dates.min()-pd.Timedelta(days=tolerance)).date(), end_date=(dates.max()+pd.Timedelta(days=tolerance)).date(), cache_dir=cache_dir)
                                covariates, pest_meta = nasa_pest_covariates(acquired.frame)
                                merged = merge_weather_with_labels(frame, covariates, label_date_column="observed_at", tolerance_days=tolerance)
                                meta = {"source": "AGROLATTICE scouting observations + NASA POWER", "dataset_type": "Date-matched pest/scouting covariates", "field_id": field_id, "temporal_resolution": "scouting event with nearest daily weather", "geography_scope": selected_country, "pest_covariate_provenance": pest_meta, "scientific_note": "Labels are user-recorded scouting observations. Presence-only observations must not be treated as a complete pest/no-pest classification dataset."}
                                _set_hub_table(merged, meta, name="Scouting observations + NASA weather")
                                st.success(f"Joined weather to {len(merged):,} scouting rows. The joined table is now available to Pest Early Warning and Model Lab.")
                            except Exception as error:
                                st.error(str(error))

    with tabs[3]:
        candidates = []
        mapping = {
            "Daily weather session": "daily_weather_derived",
            "Raw daily weather session": "daily_weather_raw",
            "Sentinel-2 time series session": "satellite_time_series",
            "Root-zone balance session": "soil_water_balance_results",
            "Live monitor weather": "live_monitor_weather",
        }
        for label, key in mapping.items():
            value = st.session_state.get(key)
            if isinstance(value, pd.DataFrame) and not value.empty:
                candidates.append((label, key, value))
        if not candidates:
            st.info("No reusable Daily Weather, Satellite, Root-zone or Live Monitor table is currently in session. Run one of those existing AGROLATTICE tools, then return here.")
        else:
            selected_label = st.selectbox("Current AGROLATTICE data", [item[0] for item in candidates], key="datahub_current_source")
            label, key, frame = next(item for item in candidates if item[0] == selected_label)
            st.dataframe(frame.head(200), hide_index=True, width="stretch")
            if st.button("Use current app data in Research Data Hub", key="datahub_use_current"):
                _set_hub_table(frame, {"source": f"AGROLATTICE session: {label}", "dataset_type": "Current app-derived table", "session_key": key, "scientific_note": "Data provenance remains that of the originating AGROLATTICE workspace."}, name=label)
                st.success("Current app data are now available to research tools.")

    with tabs[4]:
        hub, meta = _hub_table()
        if hub is None or hub.empty:
            st.info("No Research Data Hub session table yet.")
        else:
            st.markdown(f"#### {st.session_state.get('research_data_name_11_4', 'Research data')}")
            p = table_profile(hub)
            c = st.columns(4)
            c[0].metric("Rows", p.get("rows", 0)); c[1].metric("Columns", p.get("columns", 0)); c[2].metric("Missing", f"{p.get('missing_percent',0):.1f}%"); c[3].metric("Dataset ID", str(st.session_state.get("research_data_dataset_id_11_4") or "Not registered")[:12])
            st.dataframe(hub.head(300), hide_index=True, width="stretch")
            st.json(meta)
            st.download_button("Download current Research Data Hub table", hub.to_csv(index=False).encode("utf-8"), file_name="agrolattice_research_data_hub.csv", mime="text/csv", key="datahub_download")
            if st.button("Register retrieved dataset + acquisition provenance", key="datahub_register"):
                dataset_id = _register_retrieved_dataset(registry, hub, meta, name=st.session_state.get("research_data_name_11_4", "Research Data Hub table"))
                registry.save_data_acquisition({
                    "dataset_id": dataset_id,
                    "source": meta.get("source", "AGROLATTICE Research Data Hub"),
                    "source_type": meta.get("dataset_type", "retrieved table"),
                    "field_id": meta.get("field_id"),
                    "trial_id": meta.get("trial_id"),
                    "latitude": meta.get("latitude"),
                    "longitude": meta.get("longitude"),
                    "period_start": meta.get("start_date") or p.get("date_min"),
                    "period_end": meta.get("end_date") or p.get("date_max"),
                    "temporal_resolution": meta.get("temporal_resolution"),
                    "variables": list(hub.columns),
                    "request": {k: meta.get(k) for k in ("aggregation", "requested_power_parameters", "city", "state") if k in meta},
                    "provenance": meta,
                    "row_count": len(hub),
                    "status": "Completed",
                })
                st.success(f"Dataset and acquisition provenance registered: {dataset_id[:8]}.")

def render_research_registry_page(*, registry: ResearchEvidenceRegistry, app_version: str) -> None:
    st.markdown("### Research Model & Evidence Registry")
    st.caption("Additive Research Evidence registry for datasets, data acquisitions, models, predictions, recommendations, treatment outcomes, decision runs, state assimilation and causal audits. Release 11.7 keeps the protected Field Operations, Pollination Lab and Twin database schemas unchanged.")
    summary = registry.summary()
    cols = st.columns(5)
    for col, label, value in zip(cols, ["Datasets", "Acquisitions", "Models", "Predictions", "Observations"], [summary.datasets, summary.data_acquisitions, summary.models, summary.predictions, summary.observations]):
        col.metric(label, value)
    cols2 = st.columns(5)
    for col, label, value in zip(cols2, ["Recommendations", "Treatment outcomes", "Decision runs", "Causal audits", "Benchmark runs"], [summary.recommendations, summary.treatment_outcomes, getattr(summary, "decision_runs", 0), getattr(summary, "causal_analyses", 0), summary.benchmark_runs]):
        col.metric(label, value)
    integrity = registry.integrity_check()
    if integrity["integrity_check"] == "ok" and not integrity["foreign_key_issues"]:
        st.success(f"Research registry integrity check passed · schema {integrity['schema_version']}")
    else:
        st.error(f"Registry integrity issue: {integrity}")

    tabs = st.tabs(["Models", "Predictions", "Datasets", "Data acquisitions", "Observations", "Recommendations & outcomes", "Decision evidence", "Benchmark runs", "Model cards"])
    with tabs[0]:
        models = registry.models()
        if models.empty:
            st.info("No research models registered yet. Use Research Model Lab or Pest Early Warning to create one.")
        else:
            display = models[[c for c in ["model_id", "name", "family", "target", "task_type", "status", "source_method", "uncertainty_method", "updated_at"] if c in models]].copy()
            st.dataframe(display, hide_index=True, width="stretch")
            model_id = st.selectbox("Model to update", models["model_id"].tolist(), format_func=lambda x: f"{models.loc[models.model_id.eq(x), 'name'].iloc[0]} · {x[:8]}", key="registry_model_update")
            current_status = str(models.loc[models.model_id.eq(model_id), "status"].iloc[0])
            status = st.selectbox("Requested evidence status", MODEL_STATUSES, index=MODEL_STATUSES.index(current_status) if current_status in MODEL_STATUSES else 0)
            gate = registry.promotion_requirements(model_id, status)
            if gate.get("requirements"):
                st.dataframe(pd.DataFrame(gate["requirements"]).rename(columns={"requirement":"Evidence requirement","met":"Met"}), hide_index=True, width="stretch")
            rationale = st.text_area("Status-change rationale", key="registry_status_rationale")
            override = st.checkbox("Governance override (permanently audited)", key="registry_status_override")
            st.warning("Promotion never creates evidence. Missing gates block promotion unless an explicit written governance override is recorded.")
            if st.button("Apply auditable evidence status", key="registry_update_status", disabled=status == current_status):
                try:
                    registry.change_model_status(model_id, status, rationale=rationale, override=override, evidence={"source":"Legacy Research Registry UI"})
                    st.success("Model status updated and appended to model-status history.")
                    st.rerun()
                except Exception as error:
                    st.error(str(error))

    with tabs[1]:
        predictions = registry.predictions(limit=2000)
        if predictions.empty:
            st.info("No registered predictions.")
        else:
            st.dataframe(predictions[[c for c in ["generated_at", "model_name", "model_status", "field_id", "trial_id", "target", "prediction", "prediction_text", "class_probabilities_json", "lower_bound", "upper_bound", "uncertainty_method", "applicability_status", "applicability_score"] if c in predictions]], hide_index=True, width="stretch")

    with tabs[2]:
        datasets = registry.datasets()
        st.dataframe(datasets, hide_index=True, width="stretch") if not datasets.empty else st.info("No datasets registered.")

    with tabs[3]:
        acquisitions = registry.data_acquisitions(limit=2000)
        st.dataframe(acquisitions, hide_index=True, width="stretch") if not acquisitions.empty else st.info("No retrieved-data acquisition provenance recorded yet.")

    with tabs[4]:
        observations = registry.observations(limit=5000)
        if observations.empty:
            st.info("No canonical research observations registered yet.")
        else:
            st.dataframe(observations[[c for c in ["observed_at", "entity_type", "field_id", "trial_id", "experimental_unit_id", "variable", "value_numeric", "value_text", "unit", "evidence_type", "spatial_support", "temporal_resolution", "quality_flag", "source"] if c in observations]], hide_index=True, width="stretch")

    with tabs[5]:
        recommendations = registry.recommendations()
        outcomes = registry.treatment_outcomes()
        st.markdown("#### Recommendations")
        if recommendations.empty:
            st.info("No universal research recommendations recorded. AGROLATTICE records recommendations separately from measured/applied actions so later causal audits remain possible.")
        else:
            st.dataframe(recommendations, hide_index=True, width="stretch")
            history = registry.recommendation_status_history()
            if not history.empty:
                with st.expander("Recommendation status audit trail", expanded=False):
                    st.dataframe(history[[c for c in ["changed_at", "recommendation_id", "old_status", "new_status", "note"] if c in history.columns]], hide_index=True, width="stretch")
                    st.caption("Status changes are append-only evidence events; the recommendation record itself remains distinct from any applied operation or measured outcome.")
        with st.expander("Record a research recommendation", expanded=False):
            active_field, active_trial, _ = _current_context_ids()
            with st.form("registry_new_recommendation"):
                action_type = st.text_input("Action type", value="measurement")
                action_text = st.text_area("Recommended action", value="")
                objective = st.text_input("Objective", value="")
                proposed_time = st.text_input("Proposed timing / date", value="")
                amount = st.number_input("Amount (optional)", value=0.0, step=0.1)
                unit = st.text_input("Unit (optional)", value="")
                constraints_text = st.text_area("Constraints / assumptions", value="Human review required")
                submitted = st.form_submit_button("Save proposed recommendation")
            if submitted:
                if not action_type.strip() or not action_text.strip():
                    st.error("Action type and recommended action are required.")
                else:
                    recommendation_id = registry.save_recommendation({
                        "field_id": active_field, "trial_id": active_trial, "action_type": action_type, "action_text": action_text,
                        "proposed_time": proposed_time or None, "amount": amount if unit else None, "unit": unit or None,
                        "objective": objective or None, "constraints": {"notes": constraints_text}, "status": "Proposed",
                        "provenance": {"source": "Manual Research Registry entry", "scientific_note": "Recommendation is distinct from an applied treatment."},
                    })
                    st.success(f"Recommendation recorded: {recommendation_id[:8]}")
                    st.rerun()


        recommendations = registry.recommendations()
        if not recommendations.empty:
            with st.expander("Record an observed outcome for a recommendation", expanded=False):
                recommendation_id = st.selectbox(
                    "Recommendation", recommendations["recommendation_id"].tolist(),
                    format_func=lambda value: f"{recommendations.loc[recommendations.recommendation_id.eq(value), 'action_type'].iloc[0]} · {value[:8]}",
                    key="registry_outcome_recommendation",
                )
                with st.form("registry_new_outcome"):
                    followed = st.selectbox("Was the recommendation followed?", ["Unknown", "Yes", "No"])
                    actual_action = st.text_area("Actual action / treatment", value="")
                    outcome_variable = st.text_input("Observed outcome variable", value="")
                    outcome_value_text = st.text_input("Observed numeric value", value="")
                    outcome_unit = st.text_input("Outcome unit", value="")
                    measured_date = st.date_input("Measurement date", value=date.today())
                    covariate_notes = st.text_area("Important covariates / context", value="")
                    outcome_submitted = st.form_submit_button("Save observed outcome")
                if outcome_submitted:
                    if not outcome_variable.strip():
                        st.error("Observed outcome variable is required.")
                    else:
                        try:
                            outcome_value = float(outcome_value_text) if outcome_value_text.strip() else None
                        except Exception:
                            st.error("Observed numeric value must be a number or blank.")
                        else:
                            recommendation_row = recommendations.loc[recommendations["recommendation_id"].eq(recommendation_id)].iloc[0]
                            registry.save_treatment_outcome({
                                "recommendation_id": recommendation_id, "field_id": recommendation_row.get("field_id"),
                                "trial_id": recommendation_row.get("trial_id"), "experimental_unit_id": recommendation_row.get("experimental_unit_id"),
                                "recommendation_followed": None if followed == "Unknown" else followed == "Yes",
                                "actual_action_text": actual_action or None, "outcome_variable": outcome_variable, "outcome_value": outcome_value,
                                "outcome_unit": outcome_unit or None, "measured_at": measured_date.isoformat(),
                                "covariates": {"notes": covariate_notes},
                                "provenance": {"source": "Manual Research Registry outcome entry", "scientific_note": "Observed association; causal effect not established."},
                            })
                            st.success("Observed outcome recorded separately from the recommendation.")
                            st.rerun()


        st.markdown("#### Recorded treatment / recommendation outcomes")
        if outcomes.empty:
            st.caption("No outcomes have been linked to recommendations yet.")
        else:
            st.dataframe(outcomes, hide_index=True, width="stretch")
            st.caption("A recorded outcome does not by itself establish a causal treatment effect.")

    with tabs[6]:
        st.markdown("#### Decision optimisation runs")
        decision_runs = registry.decision_runs(limit=2000)
        if decision_runs.empty:
            st.info("No saved decision runs yet. Use Decision Intelligence & Research Optimisation to compare and persist alternatives.")
        else:
            summary_cols = [c for c in ["decision_run_id", "decision_type", "field_id", "trial_id", "objective", "status", "created_at"] if c in decision_runs]
            st.dataframe(decision_runs[summary_cols], hide_index=True, width="stretch")
            run_id = st.selectbox("Inspect decision run", decision_runs["decision_run_id"].astype(str).tolist(), key="registry_decision_run_inspect")
            run = decision_runs.loc[decision_runs["decision_run_id"].astype(str).eq(run_id)].iloc[0]
            with st.expander("Decision inputs, alternatives and provenance", expanded=False):
                left, right = st.columns(2)
                left.markdown("**Selected alternative**")
                left.json(json_value(run.get("selected_alternative_json"), {}))
                right.markdown("**Constraints / assumptions**")
                right.json(json_value(run.get("constraints_json"), {}))
                st.markdown("**Input snapshot**")
                st.json(json_value(run.get("input_snapshot_json"), {}))
                alternatives = json_value(run.get("alternatives_json"), [])
                if isinstance(alternatives, list) and alternatives:
                    st.markdown("**Saved alternatives**")
                    st.dataframe(pd.DataFrame(alternatives), hide_index=True, width="stretch")
                st.markdown("**Metrics & provenance**")
                st.json({"metrics": json_value(run.get("metrics_json"), {}), "provenance": json_value(run.get("provenance_json"), {})})

        st.markdown("#### State assimilation records")
        assimilations = registry.state_assimilations(limit=2000)
        if assimilations.empty:
            st.info("No state-assimilation evidence recorded yet.")
        else:
            summary_cols = [c for c in ["assimilation_id", "field_id", "trial_id", "state_variable", "prior_mean", "prior_sd", "posterior_mean", "posterior_sd", "method", "created_at"] if c in assimilations]
            st.dataframe(assimilations[summary_cols], hide_index=True, width="stretch")
            assimilation_id = st.selectbox("Inspect assimilation", assimilations["assimilation_id"].astype(str).tolist(), key="registry_assimilation_inspect")
            row = assimilations.loc[assimilations["assimilation_id"].astype(str).eq(assimilation_id)].iloc[0]
            sequence = json_value(row.get("sequence_json"), [])
            with st.expander("Assimilation sequence & provenance", expanded=False):
                if isinstance(sequence, list) and sequence:
                    st.dataframe(pd.DataFrame(sequence), hide_index=True, width="stretch")
                else:
                    st.caption("Single-state update; no multi-row sequence was stored.")
                st.json(json_value(row.get("provenance_json"), {}))

        st.markdown("#### Causal audits")
        causal = registry.causal_analyses(limit=2000)
        if causal.empty:
            st.info("No observational causal audits recorded yet.")
        else:
            summary_cols = [c for c in ["analysis_id", "name", "field_id", "trial_id", "treatment", "outcome", "group_column", "method", "created_at"] if c in causal]
            st.dataframe(causal[summary_cols], hide_index=True, width="stretch")
            analysis_id = st.selectbox("Inspect causal audit", causal["analysis_id"].astype(str).tolist(), key="registry_causal_inspect")
            row = causal.loc[causal["analysis_id"].astype(str).eq(analysis_id)].iloc[0]
            with st.expander("Causal assumptions, diagnostics and estimates", expanded=False):
                st.markdown("**Effect estimates**")
                st.json(json_value(row.get("estimates_json"), {}))
                st.markdown("**Assumptions**")
                assumptions = json_value(row.get("assumptions_json"), [])
                for assumption in assumptions if isinstance(assumptions, list) else []:
                    st.markdown(f"- {assumption}")
                st.markdown("**Diagnostics**")
                st.json(json_value(row.get("diagnostics_json"), {}))
                st.markdown("**Provenance**")
                st.json(json_value(row.get("provenance_json"), {}))

    with tabs[7]:
        runs = registry.benchmark_runs()
        if runs.empty:
            st.info("No external benchmark runs registered yet.")
        else:
            st.dataframe(runs, hide_index=True, width="stretch")

    with tabs[8]:
        models = registry.models()
        if not models.empty:
            selected = st.selectbox("Model card", models["model_id"].tolist(), format_func=lambda x: f"{models.loc[models.model_id.eq(x), 'name'].iloc[0]} · {x[:8]}", key="registry_model_card")
            card = registry.export_model_card(selected)
            st.json(card)
            st.download_button("Download model card JSON", json.dumps(card, indent=2, default=str), file_name=f"AGROLATTICE_model_card_{selected[:8]}.json", mime="application/json")


def _model_ranking_stability(manifest: Mapping[str, Any], primary_metric: str) -> pd.DataFrame:
    """Summarise fold/repeat ranking stability without declaring an absolute winner."""
    by_model = dict(manifest.get("fold_metrics_by_model") or {})
    rows = []
    for model_name, records in by_model.items():
        for record in records or []:
            value = record.get(primary_metric)
            if value is None:
                # Some summary labels use human-friendly aliases.
                aliases = {
                    "R2": "R2", "CCC": "CCC", "ROC AUC": "ROC AUC", "PR AUC": "PR AUC",
                    "Brier": "Brier", "Macro F1": "Macro F1", "Weighted F1": "Weighted F1",
                    "Balanced accuracy": "Balanced accuracy", "RMSE": "RMSE", "MAE": "MAE",
                }
                value = record.get(aliases.get(primary_metric, primary_metric))
            try:
                numeric = float(value)
            except Exception:
                continue
            if not np.isfinite(numeric):
                continue
            rows.append({"Model": model_name, "Fold": record.get("Fold"), "Metric": numeric})
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    higher_is_better = primary_metric in {"R2", "CCC", "ROC AUC", "PR AUC", "Macro F1", "Weighted F1", "Balanced accuracy"}
    frame["Rank"] = frame.groupby("Fold")["Metric"].rank(method="average", ascending=not higher_is_better)
    summary = frame.groupby("Model", as_index=False).agg(
        Folds=("Rank", "count"),
        **{"Median rank": ("Rank", "median"), "Mean rank": ("Rank", "mean"), "Rank SD": ("Rank", "std")},
    )
    wins = frame.loc[frame["Rank"].eq(1)].groupby("Model").size().rename("Fold wins")
    summary = summary.merge(wins, on="Model", how="left").fillna({"Fold wins": 0})
    summary["Fold wins"] = summary["Fold wins"].astype(int)
    return summary.sort_values(["Mean rank", "Model"]).reset_index(drop=True)


def render_model_lab_page(*, registry: ResearchEvidenceRegistry, artifact_dir: str | Path, app_version: str) -> None:
    """Registry-backed, leakage-aware training workflow.

    Every attempted candidate is persisted as a training run.  Only a selected
    candidate becomes a registered model, and its held-out evidence is stored as
    a validation run rather than disappearing with Streamlit session state.
    """
    st.markdown("### Training · Research Model Lab")
    st.caption("Data → outcome → predictors → validation design → candidate models → held-out evidence → registered model. Preprocessing is fitted inside training folds; random row CV remains diagnostic only.")
    dep = model_dependency_status()
    st.caption("Optional backends: " + " · ".join(f"{name} {'✓' if item.available else '—'}" for name, item in dep.items()))

    frame, uploaded, source = _research_table_source(key="research_model", label="Training data source")
    if frame is None or frame.empty:
        st.info("Use Research Data Hub / an experiment-built table, or upload an external research table containing measured outcomes. Environmental retrieval cannot create missing phenotype or yield labels.")
        return
    st.dataframe(frame.head(50), hide_index=True, width="stretch")
    dataset_id = st.session_state.get("research_data_dataset_id_11_4") if source == "Research Data Hub session" else _dataset_registration(registry, frame, uploaded, source_label="research_model_lab")
    columns = list(frame.columns)

    st.markdown("#### 1 · Scientific objective")
    template = st.selectbox("Modelling template", ["General agricultural prediction", "Experimental yield", "Maize synchrony", "Pest risk", "Phenology timing", "Sensor/root-zone state", "EO/subfield prediction"], key="research_template_11_14")
    template_guidance = {
        "Experimental yield": "Prefer trial/field grouping, LOYO/LORO or a frozen deployment-like holdout; preserve block/experimental-unit identifiers.",
        "Maize synchrony": "Prefer leave-one-season/site/parent-pair-out validation. Random row splits can memorise parent combinations.",
        "Pest risk": "Prefer site/year holdouts and probability calibration. Risk prediction is not field confirmation or pesticide advice.",
        "Phenology timing": "Prefer future-season/site holdouts and retain genotype/plant grouping for repeated observations.",
        "Sensor/root-zone state": "Prefer forward-time validation; random time-point splits can leak autocorrelation.",
        "EO/subfield prediction": "Prefer field/spatial-block holdouts. Random neighbouring pixels are leakage-prone.",
    }
    if template in template_guidance: st.caption(template_guidance[template])
    goal = st.selectbox("Analysis goal", ["Prediction", "Exploratory association", "Mechanistic residual correction (use Hybrid Twin Learning)", "Treatment-effect estimation (use causal evidence)"] , key="research_goal_11_14")
    target = st.selectbox("Observed target", columns, key="research_target")
    task = st.radio("Task", ["Regression", "Classification"], horizontal=True, key="research_task")
    features = st.multiselect("Predictor features", [c for c in columns if c != target], default=[c for c in columns if c != target][: min(12, max(0, len(columns)-1))], key="research_features")

    st.markdown("#### 2 · Validation design")
    protocol_options = [
        "Grouped CV", "Repeated grouped holdout", "Leave-one-field/site/trial-out", "LOYO", "LORO", "Leave-one-genotype-out",
        "Leave-one-parent-pair-out", "Spatial block holdout", "Frozen group holdout", "Forward time", "Random diagnostic CV",
    ]
    protocol_label = st.selectbox("Primary validation protocol", protocol_options, key="research_protocol_11_14")
    group = year = region = date_col = None
    holdout_value = None
    protocol = protocol_label
    if protocol_label in {"Grouped CV", "Repeated grouped holdout", "Leave-one-field/site/trial-out", "Leave-one-genotype-out", "Leave-one-parent-pair-out", "Spatial block holdout"}:
        group = st.selectbox("Grouping column kept together across folds", columns, key="research_group")
        if protocol_label == "Repeated grouped holdout":
            protocol = "Repeated grouped holdout"
        elif protocol_label != "Grouped CV":
            protocol = "Leave-one-group-out"
    elif protocol_label == "Frozen group holdout":
        group = st.selectbox("Grouping column", columns, key="research_frozen_group")
        values = frame[group].dropna().astype(str).value_counts().index.tolist()
        holdout_value = st.selectbox("Reserved holdout group (not used for development folds)", values, key="research_frozen_value") if values else None
        protocol = "Frozen group holdout"
    elif protocol_label == "LOYO":
        year = st.selectbox("Year / season column", columns, key="research_year")
    elif protocol_label == "LORO":
        region = st.selectbox("Region / site column", columns, key="research_region")
    elif protocol_label == "Forward time":
        date_col = st.selectbox("Date column", columns, key="research_date")
    readiness_split = group or year or region or date_col
    seed = int(st.number_input("Reproducible split/model seed", min_value=0, max_value=2_147_483_647, value=42, step=1, key="research_seed_11_14"))
    n_splits = int(st.slider("Folds / repeated holdouts", min_value=2, max_value=10, value=5, key="research_n_splits_11_14"))
    test_fraction = 0.20
    if protocol_label == "Repeated grouped holdout":
        test_fraction = float(st.slider("Held-out group fraction per repeat", min_value=0.10, max_value=0.50, value=0.20, step=0.05, key="research_group_test_fraction_11_14"))
    primary_metric_options = ["RMSE", "MAE", "CCC", "R2"] if task == "Regression" else ["Macro F1", "Weighted F1", "Balanced accuracy", "ROC AUC", "Brier"]
    primary_metric = st.selectbox("Primary metric declared before comparison", primary_metric_options, key="research_primary_metric_11_14")
    st.caption("Repeated measurements from the same plant/experimental unit/plot must use an appropriate grouping column. Spatial pixels should use field/spatial-block holdouts, not random pixel CV.")
    _render_data_readiness(frame, target=target, features=features, protocol=protocol_label, split_column=readiness_split, minimum_rows=8)
    with st.expander("Preview validation split before training", expanded=False):
        try:
            preview_frame = frame.loc[frame[target].notna()].reset_index(drop=True)
            preview_folds = build_protocol_folds(
                preview_frame, protocol=protocol, target_column=target, group_column=group, year_column=year,
                region_column=region, date_column=date_col, holdout_value=holdout_value, task_type=task,
                n_splits=n_splits, random_state=seed, test_fraction=test_fraction,
            )
            preview_rows=[]
            for fold in preview_folds:
                row={"Fold":fold.fold,"Split":fold.label,"Train N":len(fold.train_index),"Test N":len(fold.test_index)}
                if group and group in preview_frame:
                    row["Train groups"] = int(preview_frame.iloc[fold.train_index][group].nunique(dropna=True))
                    row["Test groups"] = int(preview_frame.iloc[fold.test_index][group].nunique(dropna=True))
                    overlap=set(preview_frame.iloc[fold.train_index][group].dropna().astype(str)) & set(preview_frame.iloc[fold.test_index][group].dropna().astype(str))
                    row["Group overlap"] = len(overlap)
                preview_rows.append(row)
            st.dataframe(pd.DataFrame(preview_rows), hide_index=True, width="stretch")
            if any(r.get("Group overlap",0) for r in preview_rows): st.error("Grouping leakage detected in the proposed split; do not train until resolved.")
        except Exception as preview_error:
            st.warning(f"Split preview unavailable: {preview_error}")

    st.markdown("#### 3 · Candidate models")
    available = available_model_names(task)
    selected_models = st.multiselect("Models", available, default=[m for m in ["Ridge" if task == "Regression" else "Logistic regression", "Random forest", "CatBoost"] if m in available], key="research_models")
    run_clicked = st.button("Run leakage-safe comparison", type="primary", disabled=not features or not selected_models or goal.startswith("Mechanistic") or goal.startswith("Treatment"), key="research_compare")
    if run_clicked:
        started = pd.Timestamp.utcnow().isoformat()
        settings = {
            "started_at": started, "template": template, "goal": goal, "target": target, "task": task, "features": features, "protocol_label": protocol_label,
            "protocol": protocol, "group": group, "year": year, "region": region, "date": date_col,
            "random_state": seed, "primary_metric": primary_metric, "holdout_value": holdout_value, "n_splits": n_splits, "test_fraction": test_fraction,
        }
        try:
            with st.spinner("Evaluating held-out folds..."):
                summary, detail, manifest = compare_models(
                    frame, target_column=target, feature_columns=features, task_type=task, model_names=selected_models,
                    protocol=protocol, group_column=group, year_column=year, region_column=region, date_column=date_col,
                    holdout_value=holdout_value, n_splits=n_splits, random_state=seed, test_fraction=test_fraction,
                )
            run_ids = {}
            for model_name in selected_models:
                row = summary.loc[summary["Model"].eq(model_name)].iloc[0].to_dict() if model_name in summary["Model"].tolist() else {"Model": model_name, "Status": "Failed"}
                run_ids[model_name] = registry.save_training_run({
                    "dataset_id": dataset_id, "started_at": started, "completed_at": pd.Timestamp.utcnow().isoformat(),
                    "status": str(row.get("Status") or "Completed"), "settings": {**settings, "candidate_model": model_name},
                    "split_summary": manifest.get("folds", []), "leakage_guards": manifest.get("leakage_guards", {}),
                    "metrics": row, "notes": str(row.get("Failure") or "Candidate comparison run; model is not registered unless explicitly selected."),
                })
            st.session_state.research_model_result = {
                "summary": summary, "detail": detail, "manifest": manifest, "frame": frame, "target": target, "features": features,
                "task": task, "dataset_id": dataset_id, "run_ids": run_ids, "settings": settings,
            }
        except Exception as error:
            for model_name in selected_models:
                registry.save_training_run({
                    "dataset_id": dataset_id, "started_at": started, "completed_at": pd.Timestamp.utcnow().isoformat(), "status": "Failed",
                    "settings": {**settings, "candidate_model": model_name}, "split_summary": {},
                    "leakage_guards": {"preprocessing_inside_folds": True}, "metrics": {}, "notes": str(error),
                })
            st.error(str(error))

    result = st.session_state.get("research_model_result")
    if not result:
        return
    st.markdown("#### 4 · Held-out evidence")
    st.dataframe(result["summary"], hide_index=True, width="stretch")
    failures = result["manifest"].get("failures", {})
    if failures:
        st.warning("Some candidates failed. Their failed training runs were retained in the registry rather than discarded.")
        st.dataframe(pd.DataFrame([{"Model": k, "Failure": v} for k, v in failures.items()]), hide_index=True, width="stretch")
    stability = _model_ranking_stability(result["manifest"], result["settings"]["primary_metric"])
    if not stability.empty:
        st.markdown("##### Model-ranking stability across held-out folds/repeats")
        st.dataframe(stability, hide_index=True, width="stretch")
        st.caption("Small performance differences with unstable ranks should not be interpreted as a definitive model winner.")
    with st.expander("Validation split manifest & leakage guards", expanded=False):
        st.json({k: v for k, v in result["manifest"].items() if k not in {"fold_metrics_by_model"}})

    completed = result["summary"].loc[result["summary"].get("Status", pd.Series(index=result["summary"].index, dtype=str)).astype(str).eq("Completed"), "Model"].tolist() if "Status" in result["summary"] else result["summary"]["Model"].tolist()
    if not completed:
        st.error("No candidate completed successfully.")
        return
    model_choice = st.selectbox("Final candidate", completed, key="research_final_model")
    if st.button("Fit, version and register candidate", key="research_fit_register"):
        estimator, profile = fit_final_model(result["frame"], target_column=result["target"], feature_columns=result["features"], task_type=result["task"], model_name=model_choice, random_state=int(result["settings"]["random_state"]))
        artifacts = Path(artifact_dir); artifacts.mkdir(parents=True, exist_ok=True)
        model_id = str(uuid.uuid4())
        path = artifacts / f"{_safe_name(model_choice)}_{model_id[:8]}.joblib"
        joblib.dump(estimator, path)
        metric_row = result["summary"].loc[result["summary"]["Model"].eq(model_choice)].iloc[0].to_dict()
        uncertainty_method = None; conformal = None
        if result["task"] == "Regression":
            conformal = conformal_half_width_from_oof(result["detail"][model_choice], coverage=0.90)
            if conformal is not None:
                uncertainty_method = "90% out-of-fold absolute-residual conformal-style interval; coverage must be independently checked"
        registered = registry.register_model({
            "model_id": model_id, "name": f"{model_choice} · {result['target']}", "family": model_choice, "target": result["target"], "task_type": result["task"],
            "status": "Prototype", "source_method": "AGROLATTICE leakage-safe baseline framework", "implementation_type": "AGROLATTICE implementation",
            "training_dataset_id": result.get("dataset_id"), "training_scope": {"rows": len(result["frame"]), "analysis_goal": result["settings"]["goal"]},
            "required_modalities": [], "feature_names": result["features"],
            "preprocessing": {"imputation": "training-fold median/mode", "categorical": "training-fold one-hot where required"},
            "validation_protocol": result["manifest"], "metrics": metric_row, "calibration": {}, "uncertainty_method": uncertainty_method,
            "applicability": profile, "limitations": ["Research candidate. Validation scope governs applicability.", "Random diagnostic CV is not external validation."],
            "artifact_path": str(path.relative_to(Path(artifact_dir).parent.parent)),
            "dependency_versions": {name: item.version for name, item in model_dependency_status().items() if item.available}, "code_version": app_version,
        })
        # Bind the previously persisted candidate training run to the registered model.
        run_id = result.get("run_ids", {}).get(model_choice)
        if run_id:
            registry.save_training_run({
                "run_id": run_id, "model_id": registered, "dataset_id": result.get("dataset_id"),
                "started_at": result["settings"].get("started_at") or pd.Timestamp.utcnow().isoformat(), "completed_at": pd.Timestamp.utcnow().isoformat(), "status": "Completed",
                "settings": {**result["settings"], "candidate_model": model_choice}, "split_summary": result["manifest"].get("folds", []),
                "leakage_guards": result["manifest"].get("leakage_guards", {}), "metrics": metric_row,
                "artifact_path": str(path.relative_to(Path(artifact_dir).parent.parent)), "notes": "Selected candidate registered as a model version.",
            })
        # Persist held-out fold evidence.
        validation_id = registry.save_validation_run({
            "model_id": registered, "dataset_id": result.get("dataset_id"), "validation_type": result["settings"]["protocol_label"],
            "evidence_level": "Internal" if result["settings"]["protocol_label"] == "Random diagnostic CV" else "Cross-group internal",
            "primary_metric": result["settings"]["primary_metric"], "metrics": metric_row,
            "fold_metrics": result["manifest"].get("fold_metrics_by_model", {}).get(model_choice, []),
            "predictions": result["detail"][model_choice].to_dict(orient="records"), "split_manifest": result["manifest"].get("folds", []),
            "calibration": {}, "uncertainty": {"method": uncertainty_method, "half_width_90": conformal}, "applicability": profile,
            "leakage_guards": result["manifest"].get("leakage_guards", {}), "status": "Completed",
            "notes": "Out-of-fold validation generated during candidate comparison. Evidence level reflects the selected split, not an independent external dataset.",
        })
        # Freeze the analysis-table provenance and feature contract used by this scientific result.
        snapshot_id = None
        if result.get("dataset_id"):
            snapshot_id = registry.save_dataset_snapshot({
                "dataset_id": result.get("dataset_id"),
                "name": f"Training snapshot · {model_choice} · {result['target']}",
                "row_count": int(len(result["frame"])),
                "entity_count": None,
                "manifest": {
                    "columns": list(result["frame"].columns), "target": result["target"], "features": result["features"],
                    "validation_settings": result["settings"], "split_manifest": result["manifest"].get("folds", []),
                    "scientific_note": "This freezes the transformation/provenance manifest. Raw bytes are immutable only when the parent dataset also records a stable local path/hash.",
                },
            })
        feature_contract = {}
        for feature in result["features"]:
            series = result["frame"][feature]
            numeric = pd.to_numeric(series, errors="coerce")
            common = {"role": "predictor", "missing_fraction": float(series.isna().mean()), "missing_policy": "fit-time fold-contained imputation", "unit": "not declared in source table", "source_expectation": "same semantic variable and spatial/temporal support as training analysis table"}
            if numeric.notna().mean() >= 0.95:
                feature_contract[feature] = {**common, "type": "numeric", "min": None if numeric.dropna().empty else float(numeric.min()), "max": None if numeric.dropna().empty else float(numeric.max())}
            else:
                feature_contract[feature] = {**common, "type": "categorical", "levels": [str(v) for v in series.dropna().astype(str).value_counts().head(100).index.tolist()]}
        import platform, sys, sklearn
        environment = {
            "python": sys.version.split()[0], "platform": platform.platform(), "agrolattice": app_version,
            "numpy": np.__version__, "pandas": pd.__version__, "scikit_learn": sklearn.__version__, "joblib": getattr(joblib, "__version__", None),
            "optional_dependencies": {name: item.version for name, item in model_dependency_status().items() if item.available},
            "random_seed": int(result["settings"]["random_state"]),
        }
        version_id = registry.register_model_version({
            "model_id": registered, "version_number": 1, "dataset_snapshot_id": snapshot_id, "artifact_path": str(path),
            "environment": environment, "feature_contract": feature_contract,
            "notes": f"Initial registered version. Validation run {validation_id[:8]}.",
        })
        st.session_state.research_fitted_model = {"model_id": registered, "version_id": version_id, "estimator": estimator, "profile": profile, "features": result["features"], "target": result["target"], "task": result["task"], "conformal": conformal}
        st.success(f"Registered prototype model {registered[:8]} · immutable version v1 · training and validation evidence retained.")

    fitted = st.session_state.get("research_fitted_model")
    if fitted:
        with st.expander("Predict new rows and register predictions", expanded=False):
            prediction_upload = st.file_uploader("Prediction table", type=["csv", "xlsx", "xls", "parquet"], key="research_predict_upload")
            if prediction_upload:
                new = _read_uploaded_table(prediction_upload)
                missing = [c for c in fitted["features"] if c not in new]
                if missing:
                    st.error("Missing model features: " + ", ".join(missing))
                else:
                    pred = fitted["estimator"].predict(new[fitted["features"]])
                    output = new.copy(); output["AGROLATTICE prediction"] = pred
                    probability_columns: list[str] = []
                    if fitted["task"].casefold().startswith("class") and hasattr(fitted["estimator"], "predict_proba"):
                        try:
                            probabilities = np.asarray(fitted["estimator"].predict_proba(new[fitted["features"]]))
                            classes = getattr(fitted["estimator"], "classes_", None)
                            if classes is None and hasattr(fitted["estimator"], "named_steps"):
                                classes = getattr(fitted["estimator"].named_steps.get("model"), "classes_", None)
                            if classes is not None and probabilities.ndim == 2 and probabilities.shape[1] == len(classes):
                                for index, label in enumerate(classes):
                                    column = f"P(class={label})"; output[column] = probabilities[:, index]; probability_columns.append(column)
                        except Exception as probability_error:
                            st.caption(f"Class probabilities unavailable: {probability_error}")
                    app = applicability_score(new[fitted["features"]], fitted["profile"])
                    output = pd.concat([output.reset_index(drop=True), app.reset_index(drop=True)], axis=1)
                    if fitted.get("conformal") is not None and not fitted["task"].casefold().startswith("class"):
                        output["Prediction lower"] = pd.to_numeric(output["AGROLATTICE prediction"], errors="coerce") - fitted["conformal"]
                        output["Prediction upper"] = pd.to_numeric(output["AGROLATTICE prediction"], errors="coerce") + fitted["conformal"]
                    st.dataframe(output, hide_index=True, width="stretch")
                    field_id, trial_id, season_year = _current_context_ids()
                    if st.button("Register these predictions to active context", key="research_register_predictions"):
                        for _, row in output.iterrows():
                            is_classification = fitted["task"].casefold().startswith("class")
                            class_probabilities = {column[len("P(class="):-1]: float(row[column]) for column in probability_columns if pd.notna(row.get(column))}
                            prediction_value = None if is_classification else pd.to_numeric(pd.Series([row["AGROLATTICE prediction"]]), errors="coerce").iloc[0]
                            registry.save_prediction({
                                "model_id": fitted["model_id"], "entity_type": "Field" if field_id else ("Trial" if trial_id else "Unlinked research row"),
                                "entity_id": field_id or trial_id, "field_id": field_id, "trial_id": trial_id, "season_year": season_year, "target": fitted["target"],
                                "prediction": None if pd.isna(prediction_value) else float(prediction_value), "prediction_text": str(row["AGROLATTICE prediction"]) if is_classification else None,
                                "class_probabilities": class_probabilities, "lower_bound": row.get("Prediction lower"), "upper_bound": row.get("Prediction upper"),
                                "uncertainty_method": "Out-of-fold residual interval" if fitted.get("conformal") is not None else ("Class probabilities; calibration must be checked" if is_classification else None),
                                "applicability_status": row.get("Applicability status"), "applicability_score": row.get("Applicability score (%)"),
                                "input_snapshot": {c: row.get(c) for c in fitted["features"]}, "provenance": {"source": "Research Model Lab", "uploaded_prediction_file": prediction_upload.name, "model_version_id": fitted.get("version_id")},
                            })
                        st.success(f"Registered {len(output)} predictions.")


def render_pest_early_warning_page(*, registry: ResearchEvidenceRegistry, artifact_dir: str | Path, app_version: str, field_db: Any | None = None, cache_dir: str | Path | None = None) -> None:
    st.markdown("### Environmental Pest & Disease Early Warning")
    st.caption("Independent AGROLATTICE adaptation of Wadhwa & Malik (2024). Environmental pest risk is an early-warning signal, not field confirmation of a pest or disease.")
    deps = pest_dependency_status()
    st.caption("Research backends: " + " · ".join(f"{k} {'✓' if v else '—'}" for k, v in deps.items()))
    raw, uploaded, source = _research_table_source(key="pest_training", label="Pest-model training data")
    if raw is None or raw.empty:
        st.info("Use Research Data Hub to retrieve NASA/installed/field data, or upload a labelled pest/weather table. Weather can be retrieved automatically, but supervised training still requires measured pest/absence labels.")
        return
    mapping = resolve_paper_columns(raw)
    feature_meta: dict[str, Any]
    try:
        if all(name in mapping for name in ("MaxT", "MinT", "RH1", "RH2")):
            frame, feature_meta = engineer_environmental_pest_features(raw, column_map=mapping)
            features_default = recommended_feature_columns(frame, mapping)
            st.caption("Source-paper-style environmental columns detected; Wadhwa & Malik feature engineering is available.")
        else:
            frame, feature_meta = nasa_pest_covariates(raw)
            features_default = [c for c in ["NASA_Tmax", "NASA_Tmin", "NASA_RHmean", "NASA_Rainfall", "NASA_Wind", "NASA_SolarRadiation", "NASA_Evaporation", "Temp_Diff", "Avg_Hum", "VPD"] if c in frame]
            st.info("Using the NASA-compatible reduced feature set. Mean NASA RH is not silently substituted for the source paper's morning/evening RH measurements; Hum_Diff is therefore not fabricated.")
    except Exception as error:
        st.error("Could not construct environmental pest covariates: " + str(error)); return
    st.write("Environmental feature provenance", feature_meta)
    st.dataframe(frame.head(50), hide_index=True, width="stretch")
    dataset_id = st.session_state.get("research_data_dataset_id_11_4") if source == "Research Data Hub session" else _dataset_registration(registry, frame, uploaded, source_label="pest_early_warning")
    target = st.selectbox("Pest class / observed outcome", list(frame.columns), key="pest_target")
    features = st.multiselect("Environmental predictors", [c for c in frame.columns if c != target], default=features_default, key="pest_features")
    protocol = st.selectbox("Validation protocol", ["Grouped CV", "LOYO", "LORO", "Forward time", "Random diagnostic CV"], key="pest_protocol")
    group = year = region = date_col = None
    if protocol == "Grouped CV": group = st.selectbox("Site/field group", list(frame.columns), key="pest_group")
    elif protocol == "LOYO": year = st.selectbox("Year/season", list(frame.columns), key="pest_year")
    elif protocol == "LORO": region = st.selectbox("Region/site", list(frame.columns), key="pest_region")
    elif protocol == "Forward time": date_col = st.selectbox("Date", list(frame.columns), key="pest_date")
    resampling = st.selectbox("Class imbalance handling", ["Class weights / model balancing", "SMOTE-ENN inside training folds"], key="pest_resampling")
    readiness_split = group or year or region or date_col
    _render_data_readiness(frame, target=target, features=features, protocol=protocol, split_column=readiness_split, minimum_rows=20, label="Pest-model data readiness")
    models = pest_available_baselines()
    default = [m for m in ["Random forest", "XGBoost", "CatBoost", "Balanced random forest"] if m in models]
    chosen = st.multiselect("Baseline models", models, default=default, key="pest_models")
    if st.button("Evaluate pest models", type="primary", disabled=not features or not chosen, key="pest_evaluate"):
        with st.spinner("Running held-out agricultural validation..."):
            summary, details, manifest = compare_pest_models(frame, target_column=target, feature_columns=features, model_names=chosen, protocol=protocol, group_column=group, year_column=year, region_column=region, date_column=date_col, resampling=resampling)
        st.session_state.pest_results = {
            "summary": summary, "details": details, "manifest": manifest, "frame": frame, "target": target,
            "features": features, "dataset_id": dataset_id, "feature_meta": feature_meta, "resampling": resampling,
            "protocol": protocol, "group": group, "year": year, "region": region, "date_col": date_col,
        }
    result = st.session_state.get("pest_results")
    if not result:
        return
    st.dataframe(result["summary"], hide_index=True, width="stretch")
    st.json(result["manifest"])
    if "CatBoost" in result["summary"]["Model"].tolist() and deps.get("optuna"):
        with st.expander("Optional CatBoost Optuna tuning", expanded=False):
            trials = st.slider("Optuna trials", 3, 30, 10, key="pest_optuna_trials")
            if st.button("Tune CatBoost", key="pest_tune"):
                best, history = tune_catboost(
                    result["frame"], target_column=result["target"], feature_columns=result["features"], protocol=result["protocol"],
                    group_column=result.get("group"), year_column=result.get("year"), region_column=result.get("region"),
                    date_column=result.get("date_col"), n_trials=trials,
                )
                st.session_state.pest_tuning = {"best": best, "history": history}
            if st.session_state.get("pest_tuning"):
                st.json(st.session_state.pest_tuning["best"])
                st.dataframe(st.session_state.pest_tuning["history"], hide_index=True, width="stretch")
    candidate = st.selectbox("Final pest model", result["summary"]["Model"].tolist(), key="pest_final")
    if st.button("Fit and register pest-risk model", key="pest_fit"):
        model, profile = fit_pest_model(
            result["frame"], target_column=result["target"], feature_columns=result["features"],
            model_name=candidate, resampling=result["resampling"],
        )
        model_id = str(uuid.uuid4()); artifacts = Path(artifact_dir); artifacts.mkdir(parents=True, exist_ok=True)
        path = artifacts / f"pest_{_safe_name(candidate)}_{model_id[:8]}.joblib"; joblib.dump(model, path)
        metric_row = result["summary"].loc[result["summary"]["Model"].eq(candidate)].iloc[0].to_dict()
        registry.register_model({
            "model_id": model_id, "name": f"Pest early warning · {candidate}", "family": candidate, "target": result["target"], "task_type": "Classification", "status": "Prototype",
            "source_method": PEST_SOURCE_METHOD, "source_citation": PEST_SOURCE_DOI, "implementation_type": "Independent AGROLATTICE adaptation",
            "training_dataset_id": result.get("dataset_id"), "training_scope": {"rows": len(result["frame"])}, "required_modalities": ["environmental/weather"], "feature_names": result["features"],
            "preprocessing": {"feature_engineering": result["feature_meta"], "imbalance": result["resampling"]}, "validation_protocol": result["manifest"], "metrics": metric_row,
            "calibration": {}, "uncertainty_method": "Class probabilities; calibration must be checked before interpreting as risk probability", "applicability": profile,
            "limitations": ["Pest risk is not a disease diagnosis.", "Source-paper generalisability does not establish global AGROLATTICE generalisability.", "Model explanations are predictive, not causal."],
            "artifact_path": str(path.relative_to(Path(artifact_dir).parent.parent)), "dependency_versions": {}, "code_version": app_version,
        })
        st.session_state.pest_fitted = {"model": model, "model_id": model_id, "profile": profile, "features": result["features"], "target": result["target"], "frame": result["frame"], "feature_meta": result["feature_meta"]}
        st.success(f"Registered pest-risk prototype {model_id[:8]}.")
    fitted = st.session_state.get("pest_fitted")
    if fitted:
        if st.button("Compute SHAP feature importance", key="pest_shap"):
            try:
                importance = shap_feature_importance(fitted["model"], fitted["frame"][fitted["features"]])
                st.session_state.pest_shap = importance
            except Exception as error:
                st.warning(str(error))
        if isinstance(st.session_state.get("pest_shap"), pd.DataFrame):
            st.dataframe(st.session_state.pest_shap, hide_index=True, width="stretch")
            st.caption("SHAP values explain the fitted model; they do not establish that a weather variable causes pest occurrence.")
        with st.expander("Forecast pest risk for new environmental rows", expanded=False):
            forecast_sources = ["Upload environmental table"]
            hub, _hub_meta = _hub_table()
            if isinstance(hub, pd.DataFrame) and not hub.empty:
                forecast_sources.insert(0, "Research Data Hub session")
            fields = field_db.fields() if field_db is not None else pd.DataFrame()
            if cache_dir is not None and not fields.empty:
                forecast_sources.insert(0, "Retrieve NASA weather for mapped field")
            prediction_source = st.radio("Forecast covariate source", forecast_sources, horizontal=True, key="pest_prediction_source")
            prediction_raw = None
            prediction_provenance: dict[str, Any] = {"source": prediction_source, "source_doi": PEST_SOURCE_DOI}
            if prediction_source == "Research Data Hub session":
                prediction_raw = hub.copy()
                prediction_provenance["data_hub_metadata"] = _hub_meta
            elif prediction_source == "Retrieve NASA weather for mapped field":
                ids = fields["field_id"].astype(str).tolist()
                active = st.session_state.get("field_ops_active_field_id")
                selected_field = st.selectbox("Field", ids, index=ids.index(str(active)) if active and str(active) in ids else 0, format_func=lambda value: f"{fields.loc[fields.field_id.astype(str).eq(str(value)), 'farm_name'].iloc[0]} · {fields.loc[fields.field_id.astype(str).eq(str(value)), 'name'].iloc[0]}", key="pest_prediction_field")
                frow = field_db.field(str(selected_field)); lat, lon = field_coordinates(frow)
                c1, c2, c3 = st.columns(3)
                start_date = c1.date_input("Weather start", value=date(date.today().year, 1, 1), key="pest_prediction_start")
                end_date = c2.date_input("Weather end", value=date.today(), key="pest_prediction_end")
                resolution = c3.selectbox("Forecast-row resolution", ["Daily", "Weekly", "Monthly"], key="pest_prediction_resolution")
                if st.button("Retrieve forecast covariates", key="pest_prediction_fetch"):
                    try:
                        acquired = fetch_canonical_nasa_weather(latitude=lat, longitude=lon, start_date=start_date, end_date=end_date, cache_dir=cache_dir)
                        prediction_raw = aggregate_daily_weather(acquired.frame, resolution)
                        st.session_state["pest_prediction_retrieved_11_4"] = prediction_raw
                        st.session_state["pest_prediction_retrieved_meta_11_4"] = {**acquired.metadata, "field_id": selected_field, "aggregation": resolution}
                    except Exception as error:
                        st.error(str(error))
                if prediction_raw is None and isinstance(st.session_state.get("pest_prediction_retrieved_11_4"), pd.DataFrame):
                    prediction_raw = st.session_state.get("pest_prediction_retrieved_11_4")
                    prediction_provenance.update(st.session_state.get("pest_prediction_retrieved_meta_11_4") or {})
            else:
                prediction_upload = st.file_uploader("New environmental table", type=["csv", "xlsx", "xls", "parquet"], key="pest_prediction_upload")
                if prediction_upload is not None:
                    prediction_raw = _read_uploaded_table(prediction_upload)
                    prediction_provenance["uploaded_prediction_file"] = prediction_upload.name

            if isinstance(prediction_raw, pd.DataFrame) and not prediction_raw.empty:
                prediction_frame = prediction_raw.copy().reset_index(drop=True)
                missing_before = [column for column in fitted["features"] if column not in prediction_frame.columns]
                if missing_before:
                    # Try exact source-paper engineering first, then the NASA-compatible path.
                    try:
                        if all(name in resolve_paper_columns(prediction_frame) for name in ("MaxT", "MinT", "RH1", "RH2")):
                            prediction_frame, _ = engineer_environmental_pest_features(prediction_frame)
                        else:
                            prediction_frame, _ = nasa_pest_covariates(prediction_frame)
                    except Exception as engineering_error:
                        st.caption(f"Automatic environmental feature engineering could not complete: {engineering_error}")
                missing = [column for column in fitted["features"] if column not in prediction_frame.columns]
                if missing:
                    st.error("Retrieved/new data are missing trained model features: " + ", ".join(missing))
                    st.warning("This usually means the fitted model was trained on source-specific variables that the new source does not measure. AGROLATTICE will not fabricate morning/evening RH or other missing variables to force compatibility.")
                else:
                    pest_pred = fitted["model"].predict(prediction_frame[fitted["features"]])
                    pest_output = prediction_raw.copy().reset_index(drop=True)
                    pest_output["Predicted pest class"] = pest_pred
                    probability_columns: list[str] = []
                    if hasattr(fitted["model"], "predict_proba"):
                        try:
                            probabilities = np.asarray(fitted["model"].predict_proba(prediction_frame[fitted["features"]]))
                            classes = getattr(fitted["model"], "classes_", None)
                            if classes is None and hasattr(fitted["model"], "named_steps"):
                                classes = getattr(fitted["model"].named_steps.get("model"), "classes_", None)
                            if classes is not None and probabilities.ndim == 2 and probabilities.shape[1] == len(classes):
                                for index, label in enumerate(classes):
                                    column = f"P(class={label})"
                                    pest_output[column] = probabilities[:, index]
                                    probability_columns.append(column)
                                pest_output["Max class probability"] = probabilities.max(axis=1)
                        except Exception as probability_error:
                            st.caption(f"Class probabilities unavailable: {probability_error}")
                    app = applicability_score(prediction_frame[fitted["features"]], fitted["profile"])
                    pest_output = pd.concat([pest_output, app.reset_index(drop=True)], axis=1)
                    pest_output["Associated disease-risk context"] = [(disease_risk_note(str(label)) or {}).get("associated_risk") for label in pest_pred]
                    st.dataframe(pest_output, hide_index=True, width="stretch")
                    st.caption("Probabilities are predictive model outputs and require calibration checks. Associated disease-risk context is not disease confirmation.")
                    field_id, trial_id, season_year = _current_context_ids()
                    if st.button("Register pest forecasts to active context", key="pest_register_predictions"):
                        for row_index, row in pest_output.iterrows():
                            class_probabilities = {column[len("P(class="):-1]: float(row[column]) for column in probability_columns if pd.notna(row.get(column))}
                            registry.save_prediction({
                                "model_id": fitted["model_id"], "entity_type": "Field" if field_id else ("Trial" if trial_id else "Unlinked research row"),
                                "entity_id": field_id or trial_id, "field_id": field_id, "trial_id": trial_id, "season_year": season_year,
                                "target": fitted["target"], "prediction_text": str(row["Predicted pest class"]),
                                "class_probabilities": class_probabilities, "uncertainty_method": "Class probabilities; calibration must be checked",
                                "applicability_status": row.get("Applicability status"), "applicability_score": row.get("Applicability score (%)"),
                                "input_snapshot": {column: prediction_frame.iloc[row_index].get(column) for column in fitted["features"]},
                                "provenance": prediction_provenance,
                            })
                        st.success(f"Registered {len(pest_output)} pest forecasts.")

        st.markdown("#### Source-paper pest–disease association guardrail")
        for pest in ["Green Leafhopper", "Yellow Stem Borer"]:
            note = disease_risk_note(pest)
            st.write(f"**{pest}:** {note['associated_risk']} — {note['note']}")


def render_phenology_service_page(*, registry: ResearchEvidenceRegistry, field_db: Any | None = None, cache_dir: str | Path | None = None) -> None:
    st.markdown("### Central Phenology Service")
    st.caption("Phenology can now retrieve weather directly for a mapped field through NASA POWER, reuse the Research Data Hub or existing Daily Weather session, or accept a local table. Measured phenology and model outputs remain explicitly distinct.")

    choices = []
    fields = field_db.fields() if field_db is not None else pd.DataFrame()
    if cache_dir is not None and not fields.empty:
        choices.append("Retrieve NASA weather for mapped field")
    hub, hub_meta = _hub_table()
    if isinstance(hub, pd.DataFrame) and not hub.empty:
        choices.append("Research Data Hub session")
    daily = st.session_state.get("daily_weather_derived")
    if isinstance(daily, pd.DataFrame) and not daily.empty:
        choices.append("Current Daily Weather session")
    choices.append("Upload daily weather")
    source = st.radio("Weather source", choices, horizontal=True, key="phenology_weather_source_11_4")
    weather = None
    weather_meta: dict[str, Any] = {"source": source}

    if source == "Retrieve NASA weather for mapped field":
        ids = fields["field_id"].astype(str).tolist()
        active = st.session_state.get("field_ops_active_field_id")
        selected_field = st.selectbox("Field", ids, index=ids.index(str(active)) if active and str(active) in ids else 0, format_func=lambda value: f"{fields.loc[fields.field_id.astype(str).eq(str(value)), 'farm_name'].iloc[0]} · {fields.loc[fields.field_id.astype(str).eq(str(value)), 'name'].iloc[0]}", key="phenology_nasa_field")
        field = field_db.field(str(selected_field)); lat, lon = field_coordinates(field)
        default_sowing = date.today()
        active_project = st.session_state.get("active_project")
        if isinstance(active_project, dict):
            season_block = active_project.get("season") or {}
            if isinstance(season_block, dict) and season_block.get("planting_date"):
                parsed_planting = pd.to_datetime(season_block.get("planting_date"), errors="coerce")
                if pd.notna(parsed_planting):
                    default_sowing = parsed_planting.date()
        sowing_hint = st.date_input("Planting/sowing date for retrieval range", value=default_sowing, key="phenology_retrieval_sowing")
        end = st.date_input("Weather end date", value=date.today(), key="phenology_retrieval_end")
        if st.button("Retrieve phenology weather", key="phenology_fetch_nasa"):
            try:
                acquired = fetch_canonical_nasa_weather(latitude=lat, longitude=lon, start_date=sowing_hint, end_date=end, cache_dir=cache_dir)
                st.session_state["phenology_weather_retrieved_11_4"] = acquired.frame
                st.session_state["phenology_weather_meta_11_4"] = {**acquired.metadata, "field_id": selected_field}
            except Exception as error:
                st.error(str(error))
        weather = st.session_state.get("phenology_weather_retrieved_11_4")
        weather_meta = st.session_state.get("phenology_weather_meta_11_4") or weather_meta
    elif source == "Research Data Hub session":
        weather = hub.copy(); weather_meta = hub_meta
    elif source == "Current Daily Weather session":
        weather = daily.copy(); weather_meta = st.session_state.get("daily_weather_metadata") or weather_meta
    else:
        uploaded = st.file_uploader("Daily weather table", type=["csv", "xlsx", "xls"], key="phenology_weather_upload")
        if uploaded:
            weather = _read_uploaded_table(uploaded); weather_meta = {"source": "Uploaded daily weather", "filename": uploaded.name}

    if not isinstance(weather, pd.DataFrame) or weather.empty:
        st.info("Retrieve or load daily weather first. Mechanistic maize requires weather from sowing through the event horizon; NASA retrieval above can provide it directly from the mapped field centroid.")
        return
    declared_resolution = str(weather_meta.get("temporal_resolution") or "").strip().casefold()
    if declared_resolution and not declared_resolution.startswith("day"):
        st.error(f"Phenology requires daily weather. The selected Research Data Hub table is labelled {declared_resolution!r}; AGROLATTICE will not treat weekly/monthly climate summaries as daily observations.")
        return
    try:
        date_column = next((c for c in ("DATE", "Date", "date", "weather_date") if c in weather.columns), None)
        if date_column:
            spacing = pd.to_datetime(weather[date_column], errors="coerce").dropna().sort_values().diff().dt.days.dropna()
            if not spacing.empty and float(spacing.median()) > 2.0:
                st.error("Phenology requires a daily time series. The selected dates are spaced more than two days apart on average; use direct NASA daily retrieval or Daily Weather instead of a coarse climate summary.")
                return
    except Exception:
        pass
    st.caption(f"Weather rows: {len(weather):,} · source: {weather_meta.get('source', source)}")
    with st.expander("Weather used by the phenology service", expanded=False):
        st.dataframe(weather.head(120), hide_index=True, width="stretch")
        st.json({k: v for k, v in weather_meta.items() if k not in {"request_metadata", "canonical_provenance"}})

    mode = st.radio("Phenology model", ["Generic GDD thresholds", "Mechanistic maize"], horizontal=True, key="phenology_mode")
    sowing = st.date_input("Planting / sowing date", value=date.today(), key="phenology_sowing")
    if mode == "Generic GDD thresholds":
        base = st.number_input("Base temperature (°C)", value=10.0, key="phenology_base")
        upper = st.number_input("Upper temperature cap (°C)", value=30.0, key="phenology_upper")
        text = st.text_area("Stage targets as Stage:GDD, one per line", value="Emergence:100\nVegetative:500\nFlowering:900\nMaturity:1500", key="phenology_targets")
        targets = {}
        try:
            for line in text.splitlines():
                if not line.strip():
                    continue
                stage, value = line.split(":", 1); targets[stage.strip()] = float(value.strip())
        except Exception:
            st.error("Use one Stage:GDD entry per line."); return
        if st.button("Estimate phenology", key="phenology_estimate_generic"):
            estimate = generic_gdd_stage_estimate(weather, sowing, targets, base_temperature_c=base, upper_temperature_c=upper)
            st.session_state.phenology_estimates_11_4 = [estimate]
    else:
        role = st.radio("Parent role", ["Female", "Male"], horizontal=True, key="phenology_role")
        draws = st.slider("Uncertainty draws", 100, 1500, 500, 100, key="phenology_draws")
        if st.button("Run mechanistic maize phenology", key="phenology_maize"):
            try:
                estimate, simulation, summary = mechanistic_maize_estimate(weather, sowing, role=role, uncertainty_draws=draws)
                st.session_state.phenology_estimates_11_4 = [estimate]
                st.session_state.phenology_simulation_11_4 = simulation
                st.session_state.phenology_summary_11_4 = summary
            except Exception as error:
                st.error(str(error))
    estimates = st.session_state.get("phenology_estimates_11_4") or []
    if estimates:
        table = consensus_table(estimates)
        st.dataframe(table, hide_index=True, width="stretch")
        st.json(disagreement_summary(estimates))
        if isinstance(st.session_state.get("phenology_simulation_11_4"), pd.DataFrame):
            with st.expander("Mechanistic daily trajectory", expanded=False):
                st.dataframe(st.session_state.phenology_simulation_11_4.tail(120), hide_index=True, width="stretch")
        field_id, trial_id, _ = _current_context_ids()
        if st.button("Register phenology evidence to active context", key="phenology_register"):
            rows = []
            for estimate in estimates:
                rows.append({
                    "entity_type": "Field" if field_id else ("Trial" if trial_id else "Unlinked research context"), "field_id": field_id, "trial_id": trial_id,
                    "observed_at": estimate.predicted_date, "variable": "Phenology stage", "value_text": estimate.stage, "evidence_type": estimate.evidence_type,
                    "source": estimate.source, "provenance": {"method": estimate.method, "weather": weather_meta, "lower_date": estimate.lower_date, "upper_date": estimate.upper_date, "notes": estimate.notes},
                })
            registry.add_observations(rows)
            st.success(f"Registered {len(rows)} phenology evidence record(s).")


def render_external_benchmarks_page(*, registry: ResearchEvidenceRegistry) -> None:
    st.markdown("### External Agricultural Benchmarks")
    st.caption("CropNet, YieldSAT and WorldCereal are external resources. AGROLATTICE stores provenance and local benchmark results; it does not bundle or silently download large datasets.")
    st.dataframe(benchmark_catalog(), hide_index=True, width="stretch")
    uploaded = st.file_uploader("Optional local benchmark table", type=["csv", "xlsx", "xls", "parquet"], key="benchmark_upload")
    if uploaded:
        frame = _read_uploaded_table(uploaded)
        inspection = inspect_local_table(frame)
        st.json(inspection)
        benchmark = st.selectbox("Benchmark family / source", ["CropNet", "YieldSAT", "WorldCereal", "Other external benchmark"], key="benchmark_family")
        if st.button("Register local benchmark snapshot metadata", key="benchmark_register"):
            dataset_id = registry.register_dataset({
                "name": f"{benchmark} · {uploaded.name}", "dataset_type": "External benchmark", "source": benchmark,
                "licence": "Verify upstream dataset licence before redistribution", "provenance": {"uploaded_filename": uploaded.name, "inspection": inspection},
                "notes": "Release 11.4 benchmark connector records provenance and validation runs; it does not claim the local file reproduces the official benchmark unless official split definitions are followed.",
            })
            st.success(f"Registered external benchmark metadata {dataset_id[:8]}.")


def render_multimodal_fusion_page(*, registry: ResearchEvidenceRegistry, artifact_dir: str | Path, app_version: str) -> None:
    st.markdown("### Adaptive Multimodal Fusion")
    st.caption("Release 11.4 adds sample-specific reliability gating. Each modality is validated out-of-fold; an error model then predicts when that modality is likely to be more or less reliable. Weights are predictive reliability signals, not causal importance, and this remains an independent AGROLATTICE adaptation rather than an exact reproduction of the neural gated-fusion paper.")
    frame, uploaded, source = _research_table_source(key="fusion", label="Multimodal training data")
    if frame is None or frame.empty:
        st.info("Build a table in Research Data Hub (NASA weather, sensors, EO, field records) or upload an already-joined multimodal table. The target must be a measured outcome; AGROLATTICE does not infer missing yield labels from covariates.")
        return
    columns = list(frame.columns)
    st.dataframe(frame.head(80), hide_index=True, width="stretch")
    target = st.selectbox("Observed target", columns, key="fusion_target")
    st.caption("Define at least two non-overlapping modality groups as JSON, for example {\"weather\":[\"TEMPERATURE\",\"PRECIPITATION_AVG\"],\"soil\":[\"pH\",\"clay\"],\"EO\":[\"NDVI\"]}.")
    default_groups = {"weather": [], "soil": [], "EO": [], "management": [], "sensors": [], "phenology": []}
    text = st.text_area("Feature groups JSON", value=json.dumps(default_groups, indent=2), height=220, key="fusion_groups")
    try:
        groups = json.loads(text)
    except Exception:
        st.error("Feature groups must be valid JSON."); return
    protocol = st.selectbox("Validation protocol", ["Grouped CV", "LOYO", "LORO", "Forward time", "Random diagnostic CV"], key="fusion_protocol")
    group = year = region = date_col = None
    if protocol == "Grouped CV": group = st.selectbox("Group column", columns, key="fusion_group")
    elif protocol == "LOYO": year = st.selectbox("Year column", columns, key="fusion_year")
    elif protocol == "LORO": region = st.selectbox("Region column", columns, key="fusion_region")
    elif protocol == "Forward time": date_col = st.selectbox("Date column", columns, key="fusion_date")
    gating = st.radio("Fusion strategy", ["Adaptive reliability gating", "Global held-out inverse-RMSE weights"], horizontal=True, key="fusion_gating")
    fusion_features = [column for values in groups.values() if isinstance(values, list) for column in values] if isinstance(groups, dict) else []
    readiness_split = group or year or region or date_col
    _render_data_readiness(frame, target=target, features=fusion_features, protocol=protocol, split_column=readiness_split, minimum_rows=12, label="Fusion data readiness")
    if st.button("Fit adaptive multimodal fusion", type="primary", key="fusion_fit"):
        try:
            fitted = fit_fusion(frame, target_column=target, feature_groups=groups, protocol=protocol, group_column=group, year_column=year, region_column=region, date_column=date_col, gating_mode=gating)
            prediction = predict_fusion(fitted, frame)
            st.session_state.fusion_11_4 = {"fitted": fitted, "prediction": prediction, "frame": frame, "target": target, "protocol": protocol, "group": group, "year": year, "region": region, "date_col": date_col, "dataset_id": st.session_state.get("research_data_dataset_id_11_4") if source == "Research Data Hub session" else None}
        except Exception as error:
            st.error(str(error))
    result = st.session_state.get("fusion_11_4")
    if result:
        fitted = result["fitted"]
        st.markdown("#### Held-out modality performance")
        st.dataframe(fitted.validation_metrics, hide_index=True, width="stretch")
        st.write("Global held-out fallback weights", fitted.weights)
        preview = result["prediction"].head(200)
        st.markdown("#### Adaptive predictions and per-row modality weights")
        st.dataframe(preview, hide_index=True, width="stretch")
        weight_cols = [c for c in preview.columns if c.endswith(" fusion weight")]
        if weight_cols:
            st.bar_chart(preview[weight_cols].mean().sort_values(ascending=False))
        st.json(fusion_manifest(fitted))
        st.caption("Inter-modality SD is disagreement, not a calibrated confidence interval. A modality receiving a high gate weight does not mean that modality causally drives yield.")
        if st.button("Register fusion prototype", key="fusion_register"):
            model_id = str(uuid.uuid4()); artifacts = Path(artifact_dir); artifacts.mkdir(parents=True, exist_ok=True)
            path = artifacts / f"adaptive_multimodal_fusion_{model_id[:8]}.joblib"; joblib.dump(fitted, path)
            registry.register_model({
                "model_id": model_id, "name": f"Adaptive multimodal fusion · {result['target']}", "family": "Adaptive multimodal fusion", "target": result["target"], "task_type": "Regression",
                "status": "Prototype", "source_method": "Adaptive multimodal gated-fusion literature", "implementation_type": "Independent AGROLATTICE CPU reliability-gating adaptation",
                "training_dataset_id": result.get("dataset_id"), "required_modalities": list(fitted.feature_groups), "feature_names": [c for cols in fitted.feature_groups.values() for c in cols],
                "preprocessing": fusion_manifest(fitted), "validation_protocol": {"protocol": result.get("protocol"), "group_column": result.get("group"), "year_column": result.get("year"), "region_column": result.get("region"), "date_column": result.get("date_col")}, "metrics": fitted.validation_metrics.to_dict(orient="records"),
                "calibration": {}, "uncertainty_method": "Inter-modality disagreement only (not calibrated)", "applicability": {},
                "limitations": ["Not an exact neural-paper reproduction.", "Gate weights are predictive reliability, not causal modality importance.", "Inter-modality SD is disagreement, not predictive confidence."],
                "artifact_path": str(path.relative_to(Path(artifact_dir).parent.parent)), "code_version": app_version,
            })
            st.success(f"Registered adaptive fusion prototype {model_id[:8]}.")


def render_hybrid_twin_learning_page(*, registry: ResearchEvidenceRegistry, artifact_dir: str | Path, app_version: str) -> None:
    st.markdown("### Hybrid Mechanistic + ML Twin Learning")
    st.caption("Learn systematic residual error around an existing mechanistic/crop-model prediction instead of replacing useful biology with a black box. The residual correction is accepted only when it improves held-out RMSE under the selected agricultural validation protocol.")
    frame, uploaded, source = _research_table_source(key="hybrid", label="Hybrid training data")
    if frame is None or frame.empty:
        st.info("Use Research Data Hub or upload a table containing a measured outcome, a mechanistic/base prediction and candidate residual features such as weather, soil, EO, genotype or management.")
        return
    st.dataframe(frame.head(80), hide_index=True, width="stretch")
    columns = list(frame.columns)
    observed = st.selectbox("Measured outcome", columns, key="hybrid_observed")
    base = st.selectbox("Mechanistic / crop-model baseline prediction", [c for c in columns if c != observed], key="hybrid_base")
    features = st.multiselect("Residual-correction predictors", [c for c in columns if c not in {observed, base}], default=[c for c in columns if c not in {observed, base}][:12], key="hybrid_features")
    protocol = st.selectbox("Validation protocol", ["Grouped CV", "LOYO", "LORO", "Forward time", "Random diagnostic CV"], key="hybrid_protocol")
    group = year = region = date_col = None
    if protocol == "Grouped CV": group = st.selectbox("Field/site/trial group", columns, key="hybrid_group")
    elif protocol == "LOYO": year = st.selectbox("Year/season", columns, key="hybrid_year")
    elif protocol == "LORO": region = st.selectbox("Region/site", columns, key="hybrid_region")
    elif protocol == "Forward time": date_col = st.selectbox("Date", columns, key="hybrid_date")
    model_options = [m for m in available_model_names("Regression") if m in {"Ridge", "Random forest", "Extra trees", "HistGradientBoosting", "XGBoost", "LightGBM", "CatBoost", "TabPFN"}]
    residual_model = st.selectbox("Residual model", model_options, index=model_options.index("Random forest") if "Random forest" in model_options else 0, key="hybrid_model")
    _render_data_readiness(frame, target=observed, features=features, protocol=protocol, split_column=group or year or region or date_col, minimum_rows=12, label="Hybrid-learning readiness")
    if st.button("Evaluate hybrid correction", type="primary", key="hybrid_fit"):
        try:
            fitted = fit_hybrid_residual(frame, observed_column=observed, base_prediction_column=base, feature_columns=features, protocol=protocol, group_column=group, year_column=year, region_column=region, date_column=date_col, residual_model_name=residual_model)
            st.session_state.hybrid_11_4 = {
                "fitted": fitted, "frame": frame, "observed": observed,
                "dataset_id": st.session_state.get("research_data_dataset_id_11_4") if source == "Research Data Hub session" else None,
                "protocol": protocol, "group": group, "year": year, "region": region,
                "date_col": date_col, "residual_model": residual_model,
            }
        except Exception as error:
            st.error(str(error))
    result = st.session_state.get("hybrid_11_4")
    if result:
        fitted = result["fitted"]
        st.dataframe(fitted.validation, hide_index=True, width="stretch")
        c1, c2 = st.columns(2)
        c1.metric("Held-out RMSE improvement", f"{fitted.improvement.get('RMSE improvement (%)', float('nan')):.2f}%")
        c2.metric("Promotion guard", "PASS" if fitted.accepted else "FAIL")
        if fitted.accepted:
            st.success("Residual correction improved held-out RMSE. It remains a research model until validation scope justifies promotion.")
        else:
            st.warning("Residual correction did not improve held-out RMSE. AGROLATTICE will not present this correction as an improvement over the mechanistic/base model.")
        st.json(hybrid_manifest(fitted))
        preview = predict_hybrid(fitted, result["frame"])
        st.dataframe(preview.head(200), hide_index=True, width="stretch")
        if st.button("Register hybrid research model", key="hybrid_register"):
            model_id = str(uuid.uuid4()); artifacts = Path(artifact_dir); artifacts.mkdir(parents=True, exist_ok=True)
            path = artifacts / f"hybrid_residual_{model_id[:8]}.joblib"; joblib.dump(fitted, path)
            registry.register_model({
                "model_id": model_id, "name": f"Hybrid residual correction · {result['observed']}", "family": "Mechanistic + ML residual", "target": result["observed"], "task_type": "Regression", "status": "Prototype",
                "source_method": "AGROLATTICE mechanistic + residual-learning architecture", "implementation_type": "AGROLATTICE hybrid implementation", "training_dataset_id": result.get("dataset_id"),
                "required_modalities": [], "feature_names": fitted.feature_columns, "preprocessing": hybrid_manifest(fitted), "validation_protocol": {"protocol": result.get("protocol"), "group": result.get("group"), "year": result.get("year"), "region": result.get("region"), "date": result.get("date_col")},
                "metrics": fitted.validation.to_dict(orient="records"), "calibration": {}, "uncertainty_method": None, "applicability": {},
                "limitations": ["Residual correction does not replace or validate the mechanistic model.", "Only promote when held-out improvement persists across independent site/seasons."],
                "artifact_path": str(path.relative_to(Path(artifact_dir).parent.parent)), "code_version": app_version,
            })
            st.success(f"Registered hybrid prototype {model_id[:8]}.")


def render_weak_supervised_yield_page(*, registry: ResearchEvidenceRegistry, artifact_dir: str | Path, app_version: str) -> None:
    st.markdown("### Weakly Supervised Spatial Yield")
    st.caption("Learn a fine-resolution response surface from coarse field/region yield labels using aggregate-consistency supervision. Fine-scale outputs are explicitly labelled model estimates; aggregate agreement does not prove 10 m / subplot accuracy.")
    frame, uploaded, source = _research_table_source(key="weak_yield", label="Fine-resolution covariate table")
    if frame is None or frame.empty:
        st.info("Use Research Data Hub or upload a table with multiple fine rows per labelled field/region. Each supervision group must carry one authoritative aggregate yield label.")
        return
    columns = list(frame.columns)
    group = st.selectbox("Aggregate supervision group (field/region/season)", columns, key="weak_group")
    target = st.selectbox("Observed aggregate yield label", [c for c in columns if c != group], key="weak_target")
    numeric_candidates = [c for c in columns if c not in {group, target} and pd.to_numeric(frame[c], errors="coerce").notna().mean() >= 0.5]
    features = st.multiselect("Fine-resolution covariates", numeric_candidates, default=numeric_candidates[:10], key="weak_features")
    alpha = st.number_input("Ridge regularisation α", min_value=0.0, value=1.0, step=0.1, key="weak_alpha")
    if st.button("Fit aggregate-consistency model", type="primary", key="weak_fit"):
        try:
            fitted = fit_weak_yield_model(frame, group_column=group, aggregate_target_column=target, feature_columns=features, alpha=alpha)
            fine, aggregated = predict_fine_resolution(fitted, frame)
            st.session_state.weak_yield_11_4 = {"fitted": fitted, "fine": fine, "aggregated": aggregated, "dataset_id": st.session_state.get("research_data_dataset_id_11_4") if source == "Research Data Hub session" else None}
        except Exception as error:
            st.error(str(error))
    result = st.session_state.get("weak_yield_11_4")
    if result:
        fitted = result["fitted"]
        st.json(weak_supervision_manifest(fitted))
        st.markdown("#### Leave-one-aggregate-group-out validation")
        st.dataframe(fitted.validation_table, hide_index=True, width="stretch")
        st.markdown("#### Fine-scale estimates")
        st.dataframe(result["fine"].head(300), hide_index=True, width="stretch")
        if not result["aggregated"].empty:
            st.markdown("#### Re-aggregated fine estimates")
            st.dataframe(result["aggregated"], hide_index=True, width="stretch")
        st.warning("Do not call the fine-scale surface measured yield. Independent fine-resolution yield observations are required before validating spatial accuracy.")
        if st.button("Register weak-supervision prototype", key="weak_register"):
            model_id = str(uuid.uuid4()); artifacts = Path(artifact_dir); artifacts.mkdir(parents=True, exist_ok=True)
            path = artifacts / f"weak_spatial_yield_{model_id[:8]}.joblib"; joblib.dump(fitted, path)
            registry.register_model({
                "model_id": model_id, "name": f"Weak spatial yield · {fitted.target_column}", "family": "Weak supervision / aggregate consistency", "target": fitted.target_column, "task_type": "Regression", "status": "Prototype",
                "source_method": "Paudel et al.-inspired weakly supervised spatial yield modelling", "implementation_type": "Independent AGROLATTICE transparent ridge baseline", "training_dataset_id": result.get("dataset_id"),
                "required_modalities": [], "feature_names": fitted.feature_columns, "preprocessing": weak_supervision_manifest(fitted), "validation_protocol": {"protocol": "Leave-one-aggregate-group-out"},
                "metrics": dict(fitted.validation_table.attrs), "calibration": {}, "uncertainty_method": None, "applicability": {},
                "limitations": ["Fine-scale predictions are not independently validated by aggregate labels.", "This is an AGROLATTICE baseline, not an exact reproduction of the paper's neural framework."],
                "artifact_path": str(path.relative_to(Path(artifact_dir).parent.parent)), "code_version": app_version,
            })
            st.success(f"Registered weak-supervision prototype {model_id[:8]}.")


def render_gxem_data_builder_page(*, registry: ResearchEvidenceRegistry, pollination_db: Any) -> None:
    st.markdown("### G×E×M Research Dataset Builder")
    st.caption("Assemble analysis-ready experimental-unit records directly from Maize Synchrony Lab instead of exporting and re-uploading trial CSVs. Trial, field, block and replicate identifiers are retained so validation can respect experimental structure.")
    trials = pollination_db.list_trials()
    if trials.empty:
        st.info("No Maize Synchrony Lab trials are stored yet.")
        return
    trial_ids = trials["Trial ID"].astype(str).tolist()
    selected = st.multiselect("Trials", trial_ids, default=trial_ids, format_func=lambda value: f"{trials.loc[trials['Trial ID'].astype(str).eq(str(value)), 'Trial'].iloc[0]} · {trials.loc[trials['Trial ID'].astype(str).eq(str(value)), 'Year'].iloc[0]}", key="gxem_trials")
    if st.button("Build G×E×M experimental-unit table", type="primary", key="gxem_build"):
        try:
            frame, meta = build_maize_gxem_table(pollination_db, selected)
            st.session_state.gxem_table_11_4 = frame
            st.session_state.gxem_meta_11_4 = meta
            _set_hub_table(frame, {"source": "AGROLATTICE Maize Synchrony Lab", "dataset_type": "G×E×M experimental-unit view", "trial_ids": selected, "temporal_resolution": "experimental unit / season", "scientific_note": meta.get("validation_guardrail")}, name="Maize G×E×M experimental-unit table")
        except Exception as error:
            st.error(str(error))
    frame = st.session_state.get("gxem_table_11_4")
    meta = st.session_state.get("gxem_meta_11_4") or {}
    if isinstance(frame, pd.DataFrame) and not frame.empty:
        st.json(meta)
        st.dataframe(frame.head(400), hide_index=True, width="stretch")
        st.download_button("Download G×E×M table", frame.to_csv(index=False).encode("utf-8"), file_name="agrolattice_maize_gxem_experimental_units.csv", mime="text/csv", key="gxem_download")
        if st.button("Register G×E×M dataset metadata", key="gxem_register"):
            dataset_id = _register_retrieved_dataset(registry, frame, {"source": "AGROLATTICE Maize Synchrony Lab", "dataset_type": "G×E×M experimental-unit view", "trial_ids": selected, "temporal_resolution": "experimental unit / season", "scientific_note": meta.get("validation_guardrail")}, name="Maize G×E×M experimental-unit table")
            st.success(f"Registered G×E×M dataset {dataset_id[:8]}. It is also the current Research Data Hub table.")


def render_twin_research_evidence_page(*, registry: ResearchEvidenceRegistry) -> None:
    st.markdown("### Registered Research Evidence")
    field_id, trial_id, _ = _current_context_ids()
    if not field_id and not trial_id:
        st.info("Select an active field or trial to see registered research predictions and recommendations for this Twin context.")
        return

    # A Twin can have a field context and an active trial simultaneously.  The
    # registry API deliberately treats multiple filters as AND, so query each
    # spatial link independently here and take their union.  This prevents a
    # valid field-level prediction from disappearing merely because a trial is
    # also selected (and vice versa).
    prediction_frames: list[pd.DataFrame] = []
    recommendation_frames: list[pd.DataFrame] = []
    if field_id:
        prediction_frames.append(registry.predictions(field_id=field_id, limit=1000))
        recommendation_frames.append(registry.recommendations(field_id=field_id))
    if trial_id:
        prediction_frames.append(registry.predictions(trial_id=trial_id, limit=1000))
        recommendation_frames.append(registry.recommendations(trial_id=trial_id))

    predictions = pd.concat([f for f in prediction_frames if not f.empty], ignore_index=True) if any(not f.empty for f in prediction_frames) else pd.DataFrame()
    if not predictions.empty and "prediction_id" in predictions:
        predictions = predictions.drop_duplicates(subset=["prediction_id"]).sort_values("generated_at", ascending=False).head(1000)

    if predictions.empty:
        st.info("No research-registry predictions are linked to this active context yet.")
    else:
        st.dataframe(predictions[[c for c in ["generated_at", "model_name", "model_status", "target", "prediction", "prediction_text", "class_probabilities_json", "lower_bound", "upper_bound", "uncertainty_method", "applicability_status", "applicability_score"] if c in predictions]], hide_index=True, width="stretch")
        unvalidated = predictions.loc[~predictions["model_status"].isin(["Externally validated", "Operationally eligible"])]
        if not unvalidated.empty:
            st.warning("One or more predictions come from Prototype/Internal models. They are evidence for research interpretation, not automatically operational recommendations.")

    recs = pd.concat([f for f in recommendation_frames if not f.empty], ignore_index=True) if any(not f.empty for f in recommendation_frames) else pd.DataFrame()
    if not recs.empty and "recommendation_id" in recs:
        recs = recs.drop_duplicates(subset=["recommendation_id"])
    st.markdown("#### Research recommendations")
    if recs.empty:
        st.caption("None recorded in the universal Research Evidence recommendation registry.")
    else:
        st.dataframe(recs, hide_index=True, width="stretch")
