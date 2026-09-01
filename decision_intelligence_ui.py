"""Streamlit interface for AGROLATTICE Decision Intelligence & Optimisation (introduced in 11.5; current release 11.11)."""
from __future__ import annotations

import json
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from decision_intelligence import (
    MODULE_VERSION,
    DecisionIntelligenceError,
    build_crop_daily_drivers,
    causal_treatment_audit,
    choose_nutrient_candidate,
    evaluate_irrigation_policies,
    fit_nutrient_response_model,
    generate_irrigation_strategies,
    nutrient_candidate_grid,
    paired_state_assimilation,
    recommendation_outcome_table,
    scalar_state_assimilation,
    sequential_state_assimilation,
    select_irrigation_policy,
)
from research_data_hub import fetch_canonical_nasa_weather, field_coordinates
from research_registry import json_value
from soil_water_balance import IrrigationStrategy, SOIL_PRESETS, available_water_profiles, crop_root_defaults, soil_profile_from_preset


def _hub_table() -> tuple[pd.DataFrame | None, dict[str, Any]]:
    frame = st.session_state.get("research_data_frame_11_4")
    metadata = st.session_state.get("research_data_metadata_11_4") or {}
    return (frame.copy() if isinstance(frame, pd.DataFrame) else None, dict(metadata) if isinstance(metadata, dict) else {})


def _read_table(uploaded: Any) -> pd.DataFrame:
    if uploaded is None:
        return pd.DataFrame()
    name = str(getattr(uploaded, "name", "")).lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded)
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded)
    if name.endswith(".parquet"):
        return pd.read_parquet(uploaded)
    raise DecisionIntelligenceError("Unsupported table format.")


def _fields(field_db: Any) -> pd.DataFrame:
    if field_db is None:
        return pd.DataFrame()
    try:
        frame = field_db.fields()
        return frame if isinstance(frame, pd.DataFrame) else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def _field_selector(field_db: Any, key: str, *, allow_none: bool = False) -> tuple[str | None, dict[str, Any] | None]:
    fields = _fields(field_db)
    if fields.empty:
        st.info("No mapped fields are available. Create/select a field in Fields & Operations first.")
        return None, None
    ids = fields["field_id"].astype(str).tolist()
    active = st.session_state.get("field_ops_active_field_id")
    default = ids.index(str(active)) if active is not None and str(active) in ids else 0
    options = ([None] + ids) if allow_none else ids
    index = default + 1 if allow_none else default

    def label(value: str | None) -> str:
        if value is None:
            return "All fields / not field-specific"
        row = fields.loc[fields["field_id"].astype(str).eq(str(value))].iloc[0]
        farm = row.get("farm_name") or row.get("farm_id") or "Farm"
        crop = row.get("crop") or "crop not set"
        return f"{farm} · {row.get('name', value)} · {crop}"

    field_id = st.selectbox("Field", options, index=index, format_func=label, key=key)
    return (None, None) if field_id is None else (str(field_id), field_db.field(str(field_id)))


def _ensure_power_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Allow canonical AGROLATTICE weather columns to feed the FAO daily model."""
    work = frame.copy()
    aliases = {
        "T2M": "TEMPERATURE",
        "T2M_MAX": "TEMPERATURE_MAX",
        "T2M_MIN": "TEMPERATURE_MIN",
        "RH2M": "RELATIVE_HUMIDITY",
        "WS2M": "WIND_SPEED",
        "ALLSKY_SFC_SW_DWN": "SOLAR_RADIATION",
        "PS": "SURFACE_PRESSURE",
        "PRECTOTCORR": "PRECIPITATION_AVG",
    }
    if "DATE" not in work:
        date_col = next((c for c in ("Date", "date", "timestamp", "Timestamp") if c in work), None)
        if date_col:
            work["DATE"] = pd.to_datetime(work[date_col], errors="coerce")
    for raw, canonical in aliases.items():
        if raw not in work and canonical in work:
            work[raw] = work[canonical]
    return work


def _default_planting(field_db: Any, field_id: str | None) -> date:
    if field_db is not None and field_id:
        try:
            history = field_db.frame("SELECT * FROM crop_history WHERE field_id=? ORDER BY season_year DESC, created_at DESC", (field_id,))
            if not history.empty and "sowing_date" in history:
                dates = pd.to_datetime(history["sowing_date"], errors="coerce").dropna()
                if not dates.empty:
                    return dates.iloc[0].date()
        except Exception:
            pass
    today = date.today()
    return today - timedelta(days=90)


def _data_source_table(key: str, *, allow_registry_outcomes: bool = False, registry: Any | None = None) -> tuple[pd.DataFrame | None, str]:
    hub, _ = _hub_table()
    options = []
    if allow_registry_outcomes and registry is not None:
        options.append("Recommendation/outcome registry")
    if isinstance(hub, pd.DataFrame) and not hub.empty:
        options.append("Research Data Hub")
    options.append("Upload table")
    source = st.radio("Data source", options, horizontal=True, key=f"{key}_source")
    if source == "Research Data Hub":
        st.caption(f"Using **{st.session_state.get('research_data_name_11_4', 'Research Data Hub table')}** · {len(hub):,} rows × {len(hub.columns)} columns")
        return hub.copy(), source
    if source == "Recommendation/outcome registry":
        recs = registry.recommendations()
        outcomes = registry.treatment_outcomes()
        table = recommendation_outcome_table(recs, outcomes)
        if table.empty:
            st.info("No recommendation/outcome pairs have been recorded yet.")
            return pd.DataFrame(), source
        # Expand covariates into analysis-ready columns.
        expanded = []
        for value in table.get("covariates_json", pd.Series(["{}"] * len(table))):
            obj = json_value(value, {})
            expanded.append(obj if isinstance(obj, dict) else {})
        cov = pd.json_normalize(expanded).add_prefix("covariate.") if expanded else pd.DataFrame(index=table.index)
        table = pd.concat([table.reset_index(drop=True), cov.reset_index(drop=True)], axis=1)
        return table, source
    upload = st.file_uploader("Upload CSV, Excel or Parquet", type=["csv", "xlsx", "xls", "parquet"], key=f"{key}_upload")
    return (_read_table(upload), source) if upload is not None else (None, source)


def _parse_covariates(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for raw in str(text or "").splitlines():
        line = raw.strip()
        if not line or "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        number = pd.to_numeric(value, errors="coerce")
        result[key] = float(number) if pd.notna(number) else value
    return result


def _status_card(label: str, ok: bool, detail: str) -> None:
    icon = "✅" if ok else "⚠️"
    st.markdown(f"**{icon} {label}**  ")
    st.caption(detail)


def render_decision_intelligence_page(
    *,
    registry: Any,
    field_db: Any,
    crop_library: Mapping[str, Any],
    cache_dir: str | Path,
    selected_country: str,
    app_version: str,
) -> None:
    tabs = st.tabs([
        "Decision home",
        "Irrigation policy studio",
        "Nutrient optimisation",
        "State assimilation",
        "Recommendation trials",
        "Causal audit",
        "Methods & safeguards",
    ])

    with tabs[0]:
        summary = registry.summary()
        fields = _fields(field_db)
        cols = st.columns(5)
        cols[0].metric("Mapped fields", len(fields))
        cols[1].metric("Decision runs", getattr(summary, "decision_runs", 0))
        cols[2].metric("Recommendations", summary.recommendations)
        cols[3].metric("Treatment outcomes", summary.treatment_outcomes)
        cols[4].metric("Causal audits", getattr(summary, "causal_analyses", 0))
        st.markdown("### Research workflow")
        st.info(
            "**Compare → choose → record → apply (if approved) → measure → evaluate.** "
            "AGROLATTICE keeps model outputs, research recommendations, actual operations and measured outcomes separate so a researcher can audit what happened later."
        )
        readiness = st.columns(4)
        with readiness[0]:
            _status_card("Spatial context", not fields.empty, "Mapped field geometry is the anchor for weather, sensors, trials and decision records.")
        with readiness[1]:
            hub, _ = _hub_table()
            _status_card("Research Data Hub", isinstance(hub, pd.DataFrame) and not hub.empty, "Reuse NASA, field records, EO and session tables without export/re-upload.")
        with readiness[2]:
            _status_card("Outcome tracking", summary.recommendations > 0, "Save recommendations now so actual actions and outcomes can be linked later.")
        with readiness[3]:
            _status_card("Causal evidence", summary.treatment_outcomes >= 10, "At least several treated and comparison outcomes are needed before observational effect estimation is meaningful.")
        st.markdown("### What a researcher can do here")
        st.markdown(
            "- Compare irrigation strategies under the same weather/soil/crop assumptions and inspect Pareto-efficient alternatives.\n"
            "- Fit local N–P–K response surfaces from measured trial/field outcomes and optimise yield, margin or input use.\n"
            "- Assimilate an observation into an uncertain crop-model state without pretending the observation and model are identical evidence.\n"
            "- Persist recommendations, record whether they were followed, attach actual outcomes/covariates, then run balance/overlap-aware causal audits."
        )
        st.warning("Decision outputs remain research decision support until the underlying model/data have the validation status required for the intended field use. No hardware is controlled by this page.")

    with tabs[1]:
        st.markdown("### Irrigation policy studio")
        st.caption("Compare transparent root-zone policies rather than accepting one hidden recommendation. NASA POWER retrieval is built in; upload is only a fallback or a way to evaluate a forecast/scenario weather table.")
        field_id, field = _field_selector(field_db, "decision_irrigation_field")
        if field_id and field:
            crops = sorted((crop_library.get("crops") or {}).keys())
            field_crop = str(field.get("crop") or "")
            crop_index = crops.index(field_crop) if field_crop in crops else (crops.index("Maize") if "Maize" in crops else 0)
            setup = st.columns(4)
            crop = setup[0].selectbox("Crop", crops, index=crop_index, key="decision_irrigation_crop")
            profiles = available_water_profiles(crop_library, crop)
            if not profiles:
                profiles = ["User-defined"]
            profile = setup[1].selectbox("Crop water profile", profiles, key="decision_irrigation_profile")
            soil_name = setup[2].selectbox("Soil water profile", list(SOIL_PRESETS), key="decision_irrigation_soil")
            planting = setup[3].date_input("Planting / season start", value=_default_planting(field_db, field_id), key="decision_irrigation_planting")
            source_options = ["Retrieve NASA POWER for this field"]
            hub, hub_meta = _hub_table()
            if isinstance(hub, pd.DataFrame) and not hub.empty:
                source_options.insert(0, "Use Research Data Hub daily weather")
            source_options.append("Upload daily weather/scenario")
            weather_source = st.radio("Weather source", source_options, horizontal=True, key="decision_irrigation_weather_source")
            uploaded_weather = None
            end_date = date.today()
            if weather_source == "Retrieve NASA POWER for this field":
                c1, c2 = st.columns(2)
                start_date = c1.date_input("Weather start", value=planting, key="decision_irrigation_weather_start")
                end_date = c2.date_input("Weather end", value=min(date.today(), planting + timedelta(days=180)), max_value=date.today(), key="decision_irrigation_weather_end")
                st.caption("NASA POWER supplies gridded historical/near-real-time environmental data, not a future operational weather forecast.")
            elif weather_source == "Upload daily weather/scenario":
                uploaded = st.file_uploader("Daily weather/scenario table", type=["csv", "xlsx", "xls", "parquet"], key="decision_irrigation_weather_upload")
                uploaded_weather = _read_table(uploaded) if uploaded is not None else None
                st.caption("A future scenario/forecast table may be used, but AGROLATTICE records it as supplied scenario data rather than NASA observations.")
            with st.expander("Research controls · soil, roots, runoff and policy search", expanded=False):
                control = st.columns(4)
                duration_strategy = control[0].selectbox("Stage-duration assumption", ["Midpoint", "Minimum", "Maximum"], key="decision_irrigation_duration")
                efficiency = control[1].slider("Application efficiency", 0.30, 1.00, 0.85, 0.01, key="decision_irrigation_eff")
                max_app = control[2].number_input("Maximum gross event (mm)", 1.0, 200.0, 60.0, 1.0, key="decision_irrigation_maxapp")
                initial_depletion = control[3].slider("Initial depletion fraction", 0.0, 1.0, 0.20, 0.05, key="decision_irrigation_initdep")
                root_defaults = crop_root_defaults(crop)
                root = st.columns(4)
                root_min = root[0].number_input("Initial root depth (m)", 0.05, 3.0, float(root_defaults.get("root_min_m", 0.5)), 0.05, key="decision_irrigation_rootmin")
                root_max = root[1].number_input("Maximum root depth (m)", 0.05, 4.0, float(root_defaults.get("root_max_m", 1.0)), 0.05, key="decision_irrigation_rootmax")
                runoff_method = root[2].selectbox("Runoff", ["None", "Fixed fraction", "NRCS curve number"], key="decision_irrigation_runoff")
                curve_number = root[3].number_input("Curve number", 30.0, 100.0, 75.0, 1.0, disabled="curve" not in runoff_method.lower(), key="decision_irrigation_cn")
                fixed_runoff = st.slider("Fixed runoff fraction", 0.0, 1.0, 0.0, 0.05, disabled=not runoff_method.lower().startswith("fixed"), key="decision_irrigation_rofrac")
                search = st.columns(4)
                trigger_min, trigger_max = search[0].slider("RAW trigger search (×)", 0.4, 1.6, (0.7, 1.2), 0.1, key="decision_irrigation_trigger_range")
                refill_min, refill_max = search[1].slider("Deficit refill search", 0.2, 1.0, (0.4, 0.8), 0.1, key="decision_irrigation_refill_range")
                include_fixed = search[2].checkbox("Compare fixed schedules", value=True, key="decision_irrigation_fixed")
                include_deficit = search[3].checkbox("Compare deficit policies", value=True, key="decision_irrigation_deficit")
                st.markdown("##### Resource / operational constraints")
                constraint_cols = st.columns(4)
                use_water_cap = constraint_cols[0].checkbox("Seasonal irrigation allocation", value=False, key="decision_irrigation_use_water_cap")
                seasonal_water_limit = constraint_cols[1].number_input("Maximum seasonal gross irrigation (mm)", 0.0, 5000.0, 300.0, 10.0, disabled=not use_water_cap, key="decision_irrigation_water_cap")
                use_event_cap = constraint_cols[2].checkbox("Limit irrigation events", value=False, key="decision_irrigation_use_event_cap")
                maximum_events = constraint_cols[3].number_input("Maximum events", 0, 365, 20, 1, disabled=not use_event_cap, key="decision_irrigation_event_cap")
                st.caption("Constraints mark scenarios infeasible rather than silently removing them, so researchers can see why an attractive policy was excluded.")
                sensors = field_db.sensors(field_id) if field_db is not None else pd.DataFrame()
                moisture = sensors.loc[sensors["sensor_type"].astype(str).eq("Soil moisture")].copy() if not sensors.empty else pd.DataFrame()
                include_sensor = False
                sensor_id = None
                sensor_threshold = 20.0
                sensor_depth = 25.0
                sensor_max_age = 2
                if not moisture.empty:
                    st.markdown("##### Optional recorded sensor-threshold policy")
                    sensor_cols = st.columns(4)
                    include_sensor = sensor_cols[0].checkbox("Compare a soil-moisture sensor policy", value=False, key="decision_irrigation_sensor_include")
                    sensor_ids = moisture["sensor_id"].astype(str).tolist()
                    sensor_id = sensor_cols[1].selectbox("Sensor", sensor_ids, format_func=lambda sid: f"{moisture.loc[moisture.sensor_id.astype(str).eq(sid), 'name'].iloc[0]} · {moisture.loc[moisture.sensor_id.astype(str).eq(sid), 'depth_cm'].iloc[0] or 'surface'} cm · {moisture.loc[moisture.sensor_id.astype(str).eq(sid), 'unit'].iloc[0]}", disabled=not include_sensor, key="decision_irrigation_sensor_id")
                    sensor_threshold = sensor_cols[2].number_input("Trigger threshold", value=20.0, disabled=not include_sensor, key="decision_irrigation_sensor_threshold")
                    sensor_depth = sensor_cols[3].number_input("Gross application when triggered (mm)", 1.0, 200.0, 25.0, 1.0, disabled=not include_sensor, key="decision_irrigation_sensor_depth")
                    sensor_max_age = st.slider("Maximum sensor reading age carried forward (days)", 0, 14, 2, disabled=not include_sensor, key="decision_irrigation_sensor_maxage")
                    st.caption("Recorded readings are used only for the sensor-triggered comparison. AGROLATTICE does not send commands to a controller or pump.")
            objective = st.selectbox("Decision objective", ["Balanced water + yield + loss", "Maximise yield protection", "Minimise irrigation water", "Maximise irrigation-adjusted profit"], key="decision_irrigation_objective")
            economics = st.checkbox("Add economic comparison", value=False, key="decision_irrigation_economics")
            potential_yield = crop_price = water_cost = event_cost = None
            if economics:
                eco = st.columns(4)
                potential_yield = eco[0].number_input("Potential yield (t/ha)", 0.01, 100.0, 8.0, 0.1, key="decision_irrigation_potential_yield")
                crop_price = eco[1].number_input("Crop price / t", 0.0, 1000000.0, 250.0, 1.0, key="decision_irrigation_crop_price")
                water_cost = eco[2].number_input("Water cost / m³", 0.0, 10000.0, 0.05, 0.01, key="decision_irrigation_water_cost")
                event_cost = eco[3].number_input("Fixed cost / irrigation event / ha", 0.0, 100000.0, 0.0, 1.0, key="decision_irrigation_event_cost")
            run = st.button("Compare irrigation policies", type="primary", width="stretch", key="decision_irrigation_run")
            if run:
                try:
                    if weather_source == "Use Research Data Hub daily weather":
                        weather = hub.copy()
                        weather_meta = hub_meta
                    elif weather_source == "Upload daily weather/scenario":
                        if uploaded_weather is None or uploaded_weather.empty:
                            raise DecisionIntelligenceError("Upload a daily weather/scenario table first.")
                        weather = uploaded_weather.copy()
                        weather_meta = {"source": "User-supplied daily weather/scenario"}
                    else:
                        lat, lon = field_coordinates(field)
                        with st.spinner("Retrieving field-centroid NASA POWER daily weather..."):
                            acquired = fetch_canonical_nasa_weather(latitude=lat, longitude=lon, start_date=start_date, end_date=end_date, cache_dir=cache_dir)
                        weather = acquired.frame
                        weather_meta = acquired.metadata
                        # Persist the acquisition itself, not just the downstream decision, so a researcher can
                        # reconstruct exactly which environmental evidence informed a saved scenario.
                        registry.save_data_acquisition({
                            "source": "NASA POWER",
                            "source_type": "Automatically retrieved gridded daily weather",
                            "field_id": field_id,
                            "latitude": lat,
                            "longitude": lon,
                            "period_start": str(start_date),
                            "period_end": str(end_date),
                            "temporal_resolution": "daily",
                            "variables": list(weather.columns),
                            "request": {"purpose": "Irrigation policy comparison", "crop": crop, "profile": profile},
                            "provenance": {"retrieval_metadata": weather_meta, "app_version": app_version, "module_version": MODULE_VERSION},
                            "row_count": len(weather),
                            "status": "Completed",
                        })
                    weather = _ensure_power_columns(weather)
                    lat, lon = field_coordinates(field)
                    drivers, schedule, driver_meta = build_crop_daily_drivers(
                        weather, latitude=lat, crop_library=crop_library, crop=crop, profile=profile,
                        planting_date=planting, duration_strategy=duration_strategy,
                        initial_root_depth_m=root_min, maximum_root_depth_m=root_max,
                    )
                    trigger_values = np.round(np.arange(trigger_min, trigger_max + 1e-9, 0.1), 2).tolist()
                    refill_values = np.round(np.arange(refill_min, refill_max + 1e-9, 0.1), 2).tolist()
                    strategies = generate_irrigation_strategies(
                        application_efficiency=efficiency, max_gross_application_mm=max_app,
                        trigger_values=trigger_values, refill_values=refill_values,
                        include_fixed=include_fixed, include_deficit=include_deficit,
                    )
                    sensor_readings = None
                    if include_sensor and sensor_id:
                        sensor_readings = field_db.readings(sensor_id=str(sensor_id))
                        if sensor_readings.empty:
                            st.warning("The selected soil-moisture sensor has no readings, so the sensor-triggered policy was not added.")
                        else:
                            sensor_unit = str(moisture.loc[moisture.sensor_id.astype(str).eq(str(sensor_id)), "unit"].iloc[0]).casefold()
                            metric = "Volumetric water content (%)" if "%" in sensor_unit or "vwc" in sensor_unit else "Raw sensor value"
                            strategies.append((
                                f"Sensor trigger ≤ {sensor_threshold:g} · {sensor_depth:g} mm gross",
                                IrrigationStrategy(
                                    mode="Sensor-triggered", application_efficiency=efficiency,
                                    fixed_gross_application_mm=float(sensor_depth), maximum_gross_application_mm=max_app,
                                    sensor_metric=metric, sensor_trigger_threshold=float(sensor_threshold), sensor_max_age_days=int(sensor_max_age),
                                ),
                            ))
                    result = evaluate_irrigation_policies(
                        drivers, soil_profile_from_preset(soil_name), strategies,
                        seasonal_ky=driver_meta.get("whole_season_ky"), initial_depletion_fraction=initial_depletion,
                        runoff_method=runoff_method, runoff_fraction=fixed_runoff, curve_number=curve_number,
                        potential_yield_t_ha=potential_yield, crop_price_per_t=crop_price,
                        water_cost_per_m3=water_cost, fixed_event_cost_per_ha=float(event_cost or 0.0),
                        sensor_irrigation_readings=sensor_readings,
                        seasonal_water_limit_mm=float(seasonal_water_limit) if use_water_cap else None,
                        maximum_irrigation_events=int(maximum_events) if use_event_cap else None,
                    )
                    selected = select_irrigation_policy(result.table, objective)
                    st.session_state["decision_irrigation_result_11_5"] = result
                    st.session_state["decision_irrigation_selected_11_5"] = selected.to_dict()
                    st.session_state["decision_irrigation_context_11_5"] = {
                        "field_id": field_id, "crop": crop, "profile": profile, "soil": soil_name,
                        "weather_source": weather_meta, "driver_metadata": driver_meta, "objective": objective,
                        "constraints": {"efficiency": efficiency, "max_event_mm": max_app, "runoff_method": runoff_method, "sensor_policy_included": bool(include_sensor and sensor_id), "seasonal_water_limit_mm": float(seasonal_water_limit) if use_water_cap else None, "maximum_events": int(maximum_events) if use_event_cap else None},
                    }
                except Exception as error:
                    st.error(str(error))
            result = st.session_state.get("decision_irrigation_result_11_5")
            selected = st.session_state.get("decision_irrigation_selected_11_5")
            context = st.session_state.get("decision_irrigation_context_11_5") or {}
            if result is not None and context.get("field_id") == field_id:
                table = result.table.copy()
                metrics = st.columns(5)
                metrics[0].metric("Policies compared", len(table))
                metrics[1].metric("Feasible", int(table["Feasible"].sum()) if "Feasible" in table else len(table))
                metrics[2].metric("Pareto-efficient", int(table["Pareto"].sum()))
                metrics[3].metric("Lowest gross water", f"{table['Gross irrigation (mm)'].min():.0f} mm")
                metrics[4].metric("Highest ET satisfaction", f"{table['ET satisfaction (%)'].max():.1f}%")
                view_mode = st.radio("Scenario view", ["All policies", "Feasible only", "Pareto-efficient only"], horizontal=True, key="decision_irrigation_view")
                if view_mode == "Feasible only" and "Feasible" in table:
                    display = table.loc[table["Feasible"]].copy()
                elif view_mode == "Pareto-efficient only":
                    display = table.loc[table["Pareto"]].copy()
                else:
                    display = table.copy()
                cols = [c for c in ["Policy", "Feasible", "Constraint note", "Pareto", "Gross irrigation (mm)", "Irrigation events", "Stress days", "Severe stress days", "ET satisfaction (%)", "Relative yield factor", "Deep percolation (mm)", "Irrigation-adjusted margin (/ha)", "Balanced score"] if c in display]
                sort_cols = [c for c in ["Feasible", "Pareto", "Balanced score"] if c in display]
                st.dataframe(display[cols].sort_values(sort_cols, ascending=[False] * len(sort_cols)) if sort_cols else display[cols], hide_index=True, width="stretch")
                st.plotly_chart(px.scatter(table, x="Gross irrigation (mm)", y="ET satisfaction (%)", size="Irrigation events", symbol="Pareto", hover_name="Policy", title="Water–crop-stress trade-off"), width="stretch")
                if selected:
                    st.markdown("#### Objective-selected research scenario")
                    m = st.columns(4)
                    m[0].metric("Policy", str(selected.get("Policy")))
                    m[1].metric("Gross irrigation", f"{float(selected.get('Gross irrigation (mm)', 0)):.1f} mm")
                    m[2].metric("Stress days", int(selected.get("Stress days", 0)))
                    m[3].metric("ET satisfaction", f"{float(selected.get('ET satisfaction (%)', np.nan)):.1f}%")
                    st.warning("The selected policy is the best-scoring scenario under the objective and assumptions you chose; it is not automatically a field prescription.")
                    action_cols = st.columns(3)
                    if action_cols[0].button("Save policy comparison as decision run", key="decision_irrigation_save_run"):
                        run_id = registry.save_decision_run({
                            "decision_type": "Irrigation policy comparison", "field_id": field_id, "objective": objective,
                            "input_snapshot": context, "alternatives": table.drop(columns=["Strategy JSON"], errors="ignore").to_dict("records"),
                            "selected_alternative": selected, "constraints": context.get("constraints"),
                            "metrics": result.metadata, "provenance": {"app_version": app_version, "module_version": MODULE_VERSION},
                        })
                        st.success(f"Decision run saved: {run_id[:8]}")
                    if action_cols[1].button("Save selected policy as research recommendation", key="decision_irrigation_save_rec"):
                        rid = registry.save_recommendation({
                            "field_id": field_id, "action_type": "Irrigation policy",
                            "action_text": f"Research scenario: {selected.get('Policy')}",
                            "amount": float(selected.get("Gross irrigation (mm)")) if pd.notna(selected.get("Gross irrigation (mm)")) else None,
                            "unit": "seasonal gross mm", "objective": objective, "status": "Proposed",
                            "constraints": context.get("constraints"),
                            "provenance": {"source": "AGROLATTICE irrigation policy studio", "app_version": app_version, "selected_scenario": selected, "scientific_status": "Research recommendation; verify field state before operational use."},
                        })
                        st.session_state["decision_last_recommendation_11_5"] = rid
                        st.success(f"Research recommendation saved: {rid[:8]}")
                    action_cols[2].download_button("Download policy table", table.drop(columns=["Strategy JSON"], errors="ignore").to_csv(index=False).encode(), file_name=f"agrolattice_irrigation_policies_{field_id[:8]}.csv", mime="text/csv", width="stretch", key="decision_irrigation_download")

    with tabs[2]:
        st.markdown("### Local nutrient-response & Pareto optimisation")
        st.caption("Fit a response surface only from measured outcomes with actual nutrient-rate variation. Soil/tissue samples alone are not converted into universal fertiliser recommendations.")
        field_id, field = _field_selector(field_db, "decision_nutrient_field", allow_none=True)
        if field_id and field_db is not None:
            evidence_cols = st.columns(2)
            samples = field_db.nutrient_samples(field_id)
            operations = field_db.operations(field_id)
            fert_ops = operations.loc[operations.get("category", pd.Series(dtype=str)).astype(str).str.contains("fert", case=False, na=False)] if not operations.empty else pd.DataFrame()
            with evidence_cols[0]:
                st.markdown("**Existing nutrient samples**")
                st.dataframe(samples.tail(20), hide_index=True, width="stretch") if not samples.empty else st.caption("None recorded for this field.")
            with evidence_cols[1]:
                st.markdown("**Existing fertiliser operations**")
                st.dataframe(fert_ops.tail(20), hide_index=True, width="stretch") if not fert_ops.empty else st.caption("None recorded for this field.")
            st.caption("These records are shown for context. Product rates are not automatically converted to elemental N/P/K because formulation and units must be known explicitly.")
        table, source = _data_source_table("decision_nutrient")
        if isinstance(table, pd.DataFrame) and not table.empty:
            numeric = [c for c in table.columns if pd.to_numeric(table[c], errors="coerce").notna().sum() >= max(5, len(table) // 3)]
            if len(numeric) < 4:
                st.warning("The selected table needs measured outcome plus numeric N, P and K rate columns.")
            else:
                c1, c2, c3, c4 = st.columns(4)
                target = c1.selectbox("Measured outcome", numeric, key="decision_nutrient_target")
                n_col = c2.selectbox("N rate column", numeric, index=min(1, len(numeric)-1), key="decision_nutrient_n")
                p_col = c3.selectbox("P rate column", numeric, index=min(2, len(numeric)-1), key="decision_nutrient_p")
                k_col = c4.selectbox("K rate column", numeric, index=min(3, len(numeric)-1), key="decision_nutrient_k")
                excluded = {target, n_col, p_col, k_col}
                group_options = ["None"] + [c for c in table.columns if c not in excluded and table[c].nunique(dropna=True) >= 2]
                group = st.selectbox("Validation group (prefer site/season/trial)", group_options, key="decision_nutrient_group")
                covariates = st.multiselect("Additional numeric G×E×M covariates", [c for c in numeric if c not in excluded], key="decision_nutrient_covariates")
                if st.button("Fit leakage-aware nutrient response", type="primary", width="stretch", key="decision_nutrient_fit"):
                    try:
                        model = fit_nutrient_response_model(table, target_column=target, n_column=n_col, p_column=p_col, k_column=k_col, covariate_columns=covariates, group_column=None if group == "None" else group)
                        st.session_state["decision_nutrient_model_11_5"] = model
                        st.session_state["decision_nutrient_source_11_5"] = {"source": source, "field_id": field_id}
                    except Exception as error:
                        st.error(str(error))
                model = st.session_state.get("decision_nutrient_model_11_5")
                if model is not None:
                    mc = st.columns(4)
                    mc[0].metric("Validation RMSE", f"{model.metrics['rmse']:.3g}")
                    mc[1].metric("Validation MAE", f"{model.metrics['mae']:.3g}")
                    mc[2].metric("Validation R²", f"{model.metrics['r2']:.3f}" if np.isfinite(model.metrics['r2']) else "—")
                    mc[3].metric("Complete observations", int(model.metrics["n"]))
                    st.caption(model.metrics["protocol"])
                    with st.expander("Validation residuals", expanded=False):
                        st.dataframe(model.validation_rows, hide_index=True, width="stretch")
                    ranges = st.columns(4)
                    n_min, n_max = float(pd.to_numeric(table[n_col], errors="coerce").min()), float(pd.to_numeric(table[n_col], errors="coerce").max())
                    p_min, p_max = float(pd.to_numeric(table[p_col], errors="coerce").min()), float(pd.to_numeric(table[p_col], errors="coerce").max())
                    k_min, k_max = float(pd.to_numeric(table[k_col], errors="coerce").min()), float(pd.to_numeric(table[k_col], errors="coerce").max())
                    n_range = ranges[0].slider("N search range", min(n_min, n_max), max(n_min, n_max), (n_min, n_max), key="decision_nutrient_nrange") if n_max > n_min else (n_min, n_max)
                    p_range = ranges[1].slider("P search range", min(p_min, p_max), max(p_min, p_max), (p_min, p_max), key="decision_nutrient_prange") if p_max > p_min else (p_min, p_max)
                    k_range = ranges[2].slider("K search range", min(k_min, k_max), max(k_min, k_max), (k_min, k_max), key="decision_nutrient_krange") if k_max > k_min else (k_min, k_max)
                    steps = ranges[3].slider("Grid resolution / nutrient", 5, 25, 12, 1, key="decision_nutrient_steps")
                    fixed_values = {}
                    if covariates:
                        with st.expander("Scenario values for other G×E×M covariates", expanded=False):
                            st.caption("These are held fixed while N/P/K vary. Defaults are medians of the training table.")
                            cols = st.columns(min(4, len(covariates)))
                            for i, cov in enumerate(covariates):
                                median = float(pd.to_numeric(table[cov], errors="coerce").median())
                                fixed_values[cov] = cols[i % len(cols)].number_input(cov, value=median, key=f"decision_nutrient_fixed_{i}")
                    eco = st.columns(4)
                    output_price = eco[0].number_input("Outcome value / unit (optional)", 0.0, 1e9, 0.0, 1.0, key="decision_nutrient_price")
                    n_cost = eco[1].number_input("N cost / rate unit", 0.0, 1e9, 0.0, 0.1, key="decision_nutrient_ncost")
                    p_cost = eco[2].number_input("P cost / rate unit", 0.0, 1e9, 0.0, 0.1, key="decision_nutrient_pcost")
                    k_cost = eco[3].number_input("K cost / rate unit", 0.0, 1e9, 0.0, 0.1, key="decision_nutrient_kcost")
                    objective = st.selectbox("Optimisation objective", ["Balanced yield + lower input", "Maximum predicted yield", "Minimum nutrient input retaining 95% of maximum predicted yield", "Maximum input-adjusted margin"], key="decision_nutrient_objective")
                    if st.button("Generate Pareto nutrient scenarios", type="primary", width="stretch", key="decision_nutrient_opt"):
                        try:
                            grid = nutrient_candidate_grid(model, n_range=n_range, p_range=p_range, k_range=k_range, steps=steps, covariate_values=fixed_values, crop_price_per_output_unit=output_price if output_price > 0 else None, n_cost_per_unit=n_cost, p_cost_per_unit=p_cost, k_cost_per_unit=k_cost)
                            selected = choose_nutrient_candidate(grid, objective)
                            st.session_state["decision_nutrient_grid_11_5"] = grid
                            st.session_state["decision_nutrient_selected_11_5"] = selected.to_dict()
                            st.session_state["decision_nutrient_context_11_5"] = {"field_id": field_id, "target": target, "N": n_col, "P": p_col, "K": k_col, "covariates": fixed_values, "objective": objective, "validation": model.metrics}
                        except Exception as error:
                            st.error(str(error))
                    grid = st.session_state.get("decision_nutrient_grid_11_5")
                    selected = st.session_state.get("decision_nutrient_selected_11_5")
                    nctx = st.session_state.get("decision_nutrient_context_11_5") or {}
                    if isinstance(grid, pd.DataFrame) and not grid.empty and nctx.get("target") == target:
                        pareto = grid.loc[grid["Pareto"]].copy()
                        st.metric("Pareto-efficient nutrient combinations", len(pareto))
                        st.dataframe(pareto.sort_values("Balanced score", ascending=False).head(250), hide_index=True, width="stretch")
                        st.plotly_chart(px.scatter_3d(pareto, x=n_col, y=p_col, z=k_col, color="Predicted outcome", size="Total nutrient rate", title="Pareto-efficient N–P–K scenarios"), width="stretch")
                        if selected:
                            st.markdown("#### Objective-selected research scenario")
                            sc = st.columns(5)
                            sc[0].metric("N", f"{float(selected[n_col]):.2f}")
                            sc[1].metric("P", f"{float(selected[p_col]):.2f}")
                            sc[2].metric("K", f"{float(selected[k_col]):.2f}")
                            sc[3].metric("Predicted outcome", f"{float(selected['Predicted outcome']):.3g}")
                            sc[4].metric("Total rate", f"{float(selected['Total nutrient rate']):.2f}")
                            st.warning("This optimiser stays inside the observed nutrient-rate search range by default. It is only as transferable as the validation design and data support of the fitted response surface.")
                            actions = st.columns(3)
                            if actions[0].button("Save nutrient decision run", key="decision_nutrient_save_run"):
                                rid = registry.save_decision_run({"decision_type": "NPK response/Pareto optimisation", "field_id": field_id, "objective": objective, "input_snapshot": nctx, "alternatives": pareto.head(1000).to_dict("records"), "selected_alternative": selected, "constraints": {"N_range": n_range, "P_range": p_range, "K_range": k_range}, "metrics": model.metrics, "provenance": {"app_version": app_version, "method": "Second-order Ridge response surface + non-dominated screening"}})
                                st.success(f"Decision run saved: {rid[:8]}")
                            if actions[1].button("Save as research recommendation", key="decision_nutrient_save_rec"):
                                rid = registry.save_recommendation({"field_id": field_id, "action_type": "Nutrient scenario", "action_text": f"Research N/P/K scenario: {n_col}={selected[n_col]:.2f}, {p_col}={selected[p_col]:.2f}, {k_col}={selected[k_col]:.2f}", "objective": objective, "status": "Proposed", "constraints": {"search_ranges": {n_col: n_range, p_col: p_range, k_col: k_range}}, "provenance": {"source": "AGROLATTICE nutrient optimisation", "app_version": app_version, "selected_scenario": selected, "validation": model.metrics}})
                                st.session_state["decision_last_recommendation_11_5"] = rid
                                st.success(f"Research recommendation saved: {rid[:8]}")
                            actions[2].download_button("Download Pareto set", pareto.to_csv(index=False).encode(), file_name="agrolattice_nutrient_pareto.csv", mime="text/csv", width="stretch", key="decision_nutrient_download")

    with tabs[3]:
        st.markdown("### Observation-to-model state assimilation")
        st.caption("Use an observation to update an uncertain model/Twin state only when both refer to the same physical state and units, or a separately validated observation operator exists.")
        field_id, _ = _field_selector(field_db, "decision_assimilation_field", allow_none=True)
        mode = st.radio(
            "Assimilation mode",
            ["Single observation", "Time-varying model-state table", "Repeated-measurement static parameter"],
            horizontal=True, key="decision_assimilation_mode",
        )
        variable = st.text_input("State variable and unit", value="LAI (m²/m²)", key="decision_assimilation_variable")

        if mode == "Single observation":
            prior = st.columns(2)
            prior_mean = prior[0].number_input("Model prior mean", value=2.0, key="decision_assimilation_prior")
            prior_sd = prior[1].number_input("Model prior SD", min_value=1e-6, value=0.5, key="decision_assimilation_prior_sd")
            obs = st.columns(2)
            observation = obs[0].number_input("Observed value", value=2.4, key="decision_assimilation_obs")
            observation_sd = obs[1].number_input("Observation SD / measurement uncertainty", min_value=1e-6, value=0.25, key="decision_assimilation_obs_sd")
            if st.button("Assimilate observation", type="primary", width="stretch", key="decision_assimilation_run"):
                try:
                    result = scalar_state_assimilation(prior_mean, prior_sd, observation, observation_sd)
                    st.session_state["decision_assimilation_result_11_5"] = result
                except Exception as error:
                    st.error(str(error))
            result = st.session_state.get("decision_assimilation_result_11_5")
            if result:
                cols = st.columns(4)
                cols[0].metric("Prior", f"{result['prior_mean']:.3g} ± {result['prior_sd']:.3g}")
                cols[1].metric("Observation", f"{result['observation']:.3g} ± {result['observation_sd']:.3g}")
                cols[2].metric("Posterior", f"{result['posterior_mean']:.3g} ± {result['posterior_sd']:.3g}")
                cols[3].metric("Observation weight (gain)", f"{result['kalman_gain']:.2f}")
                if st.button("Save assimilation evidence", key="decision_assimilation_save"):
                    aid = registry.save_state_assimilation({"field_id": field_id, "state_variable": variable, **{k: result[k] for k in ["prior_mean", "prior_sd", "observation", "observation_sd", "posterior_mean", "posterior_sd"]}, "method": "Independent Gaussian scalar update", "provenance": {"app_version": app_version, "innovation": result["innovation"], "kalman_gain": result["kalman_gain"], "scientific_note": "Requires prior and observation to represent the same state/units."}})
                    st.success(f"Assimilation record saved: {aid[:8]}")

        elif mode == "Time-varying model-state table":
            st.info("Use this for an evolving state such as LAI, biomass or soil water when your table contains a model prior and uncertainty for each observation time. Each row is updated independently; a posterior is not incorrectly carried into the next biological time point.")
            table, _ = _data_source_table("decision_assimilation_dynamic")
            if isinstance(table, pd.DataFrame) and not table.empty:
                numeric = [c for c in table.columns if pd.to_numeric(table[c], errors="coerce").notna().sum() >= 2]
                if len(numeric) < 4:
                    st.warning("Time-varying assimilation needs numeric prior mean, prior SD, observed value and observation SD columns.")
                else:
                    cols = st.columns(4)
                    prior_mean_col = cols[0].selectbox("Model prior mean column", numeric, key="decision_assimilation_dyn_prior")
                    prior_sd_choices = [c for c in numeric if c != prior_mean_col]
                    prior_sd_col = cols[1].selectbox("Model prior SD column", prior_sd_choices, key="decision_assimilation_dyn_prior_sd")
                    obs_choices = [c for c in numeric if c not in {prior_mean_col, prior_sd_col}]
                    observation_col = cols[2].selectbox("Observation column", obs_choices, key="decision_assimilation_dyn_obs")
                    obs_sd_choices = [c for c in numeric if c not in {prior_mean_col, prior_sd_col, observation_col}]
                    observation_sd_col = cols[3].selectbox("Observation SD column", obs_sd_choices, key="decision_assimilation_dyn_obs_sd")
                    time_options = ["Row order"] + [c for c in table.columns if c not in {prior_mean_col, prior_sd_col, observation_col, observation_sd_col}]
                    time_choice = st.selectbox("Time/order column (optional)", time_options, key="decision_assimilation_dyn_time")
                    if st.button("Assimilate time-varying states", type="primary", width="stretch", key="decision_assimilation_dyn_run"):
                        try:
                            sequence = paired_state_assimilation(
                                table, prior_mean_column=prior_mean_col, prior_sd_column=prior_sd_col,
                                observation_column=observation_col, observation_sd_column=observation_sd_col,
                                time_column=None if time_choice == "Row order" else time_choice,
                            )
                            st.session_state["decision_assimilation_dynamic_11_5"] = sequence
                        except Exception as error:
                            st.error(str(error))
                    sequence = st.session_state.get("decision_assimilation_dynamic_11_5")
                    if isinstance(sequence, pd.DataFrame) and not sequence.empty:
                        st.dataframe(sequence, hide_index=True, width="stretch")
                        x_axis = "time" if "time" in sequence.columns else "row"
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=sequence[x_axis], y=sequence["prior_mean"], mode="lines+markers", name="Model prior", error_y={"type": "data", "array": sequence["prior_sd"], "visible": True}))
                        fig.add_trace(go.Scatter(x=sequence[x_axis], y=sequence["posterior_mean"], mode="lines+markers", name="Assimilated posterior", error_y={"type": "data", "array": sequence["posterior_sd"], "visible": True}))
                        fig.update_layout(title=f"Time-varying state assimilation · {variable}", xaxis_title=x_axis, yaxis_title=variable)
                        st.plotly_chart(fig, width="stretch")
                        if st.button("Save time-varying assimilation evidence", key="decision_assimilation_dyn_save"):
                            first, last = sequence.iloc[0], sequence.iloc[-1]
                            aid = registry.save_state_assimilation({
                                "field_id": field_id, "state_variable": variable,
                                "prior_mean": float(first["prior_mean"]), "prior_sd": float(first["prior_sd"]),
                                "observation": float(last["observation"]), "observation_sd": float(last["observation_sd"]),
                                "posterior_mean": float(last["posterior_mean"]), "posterior_sd": float(last["posterior_sd"]),
                                "method": "Independent time-varying Gaussian state updates", "sequence": sequence.to_dict("records"),
                                "provenance": {"app_version": app_version, "n_rows": len(sequence), "prior_mean_column": prior_mean_col, "prior_sd_column": prior_sd_col, "observation_column": observation_col, "observation_sd_column": observation_sd_col, "time_column": None if time_choice == "Row order" else time_choice, "scientific_note": "Each time point is updated against its own model prior; no posterior carry-forward is assumed."},
                            })
                            st.success(f"Time-varying assimilation evidence saved: {aid[:8]}")

        else:
            st.warning("Use recursive repeated-measurement assimilation only for repeated measurements of the SAME latent state or calibration parameter. Do not use it for an evolving crop state such as LAI unless a process/state-transition model has first propagated the prior between times.")
            prior = st.columns(2)
            prior_mean = prior[0].number_input("Initial prior mean", value=2.0, key="decision_assimilation_static_prior")
            prior_sd = prior[1].number_input("Initial prior SD", min_value=1e-6, value=0.5, key="decision_assimilation_static_prior_sd")
            table, _ = _data_source_table("decision_assimilation_static")
            if isinstance(table, pd.DataFrame) and not table.empty:
                numeric = [c for c in table.columns if pd.to_numeric(table[c], errors="coerce").notna().sum() >= 2]
                if len(numeric) < 2:
                    st.warning("Repeated-measurement assimilation needs observation and observation-SD columns.")
                else:
                    c1, c2, c3 = st.columns(3)
                    value_col = c1.selectbox("Observation value column", numeric, key="decision_assimilation_value_col")
                    sd_choices = [c for c in numeric if c != value_col]
                    sd_col = c2.selectbox("Observation SD column", sd_choices, key="decision_assimilation_sd_col")
                    time_options = ["Row order"] + [c for c in table.columns if c not in {value_col, sd_col}]
                    time_choice = c3.selectbox("Time/order column (optional)", time_options, key="decision_assimilation_time_col")
                    if st.button("Assimilate repeated measurements", type="primary", width="stretch", key="decision_assimilation_sequence"):
                        try:
                            sequence = sequential_state_assimilation(prior_mean, prior_sd, table, value_column=value_col, sd_column=sd_col, time_column=None if time_choice == "Row order" else time_choice)
                            st.session_state["decision_assimilation_sequence_11_5"] = sequence
                        except Exception as error:
                            st.error(str(error))
                    sequence = st.session_state.get("decision_assimilation_sequence_11_5")
                    if isinstance(sequence, pd.DataFrame) and not sequence.empty:
                        st.dataframe(sequence, hide_index=True, width="stretch")
                        x_axis = "time" if "time" in sequence.columns else "row"
                        st.plotly_chart(px.line(sequence, x=x_axis, y="posterior_mean", error_y="posterior_sd", markers=True, title=f"Recursive posterior · {variable}"), width="stretch")
                        if st.button("Save repeated-measurement assimilation evidence", key="decision_assimilation_sequence_save"):
                            last = sequence.iloc[-1]
                            aid = registry.save_state_assimilation({
                                "field_id": field_id, "state_variable": variable, "prior_mean": prior_mean, "prior_sd": prior_sd,
                                "observation": float(last["observation"]), "observation_sd": float(last["observation_sd"]),
                                "posterior_mean": float(last["posterior_mean"]), "posterior_sd": float(last["posterior_sd"]),
                                "method": "Recursive repeated-measurement Gaussian updates", "sequence": sequence.to_dict("records"),
                                "provenance": {"app_version": app_version, "n_observations": len(sequence), "value_column": value_col, "sd_column": sd_col, "time_column": None if time_choice == "Row order" else time_choice, "scientific_note": "Suitable only when observations update the same latent state/parameter; evolving states require time-varying priors or a process model."},
                            })
                            st.success(f"Repeated-measurement assimilation evidence saved: {aid[:8]}")

    with tabs[4]:
        st.markdown("### Recommendation → action → outcome ledger")
        st.caption("This is the bridge between decision support and field evidence. Recording a recommendation does not mean it was applied; recording an outcome does not prove the recommendation caused it.")
        field_id, field = _field_selector(field_db, "decision_trial_field", allow_none=True)
        with st.expander("Create a manual research recommendation", expanded=False):
            with st.form("decision_manual_recommendation"):
                cols = st.columns(4)
                action_type = cols[0].selectbox("Action type", ["Irrigation", "Nutrient", "Sowing", "Pest management", "Sampling", "Other"])
                amount = cols[1].number_input("Amount (optional)", value=0.0)
                unit = cols[2].text_input("Unit", value="")
                proposed_time = cols[3].date_input("Proposed date", value=date.today())
                text = st.text_area("Recommendation", placeholder="Describe the action, alternative or measurement to test.")
                objective = st.text_input("Objective", placeholder="e.g. reduce water while maintaining crop water status")
                constraints = st.text_area("Constraints / assumptions (one per line)", placeholder="max_event_mm=40\nwater_allocation_mm=250")
                save = st.form_submit_button("Save research recommendation", type="primary", width="stretch")
            if save and text.strip():
                rid = registry.save_recommendation({"field_id": field_id, "action_type": action_type, "action_text": text.strip(), "proposed_time": str(proposed_time), "amount": amount if amount != 0 else None, "unit": unit or None, "objective": objective or None, "constraints": _parse_covariates(constraints), "status": "Proposed", "provenance": {"source": "Manual AGROLATTICE research recommendation", "app_version": app_version}})
                st.success(f"Recommendation saved: {rid[:8]}")
        recommendations = registry.recommendations(field_id=field_id) if field_id else registry.recommendations()
        if recommendations.empty:
            st.info("No recommendations match this filter.")
        else:
            view_cols = [c for c in ["recommendation_id", "field_id", "action_type", "action_text", "proposed_time", "amount", "unit", "objective", "status", "created_at"] if c in recommendations]
            st.dataframe(recommendations[view_cols], hide_index=True, width="stretch")
            ids = recommendations["recommendation_id"].astype(str).tolist()
            rid = st.selectbox("Recommendation to update / follow up", ids, format_func=lambda x: f"{x[:8]} · {recommendations.loc[recommendations.recommendation_id.astype(str).eq(x), 'action_type'].iloc[0]} · {recommendations.loc[recommendations.recommendation_id.astype(str).eq(x), 'action_text'].iloc[0][:70]}", key="decision_trial_recommendation")
            status_col, task_col = st.columns(2)
            new_status = status_col.selectbox("Status", ["Proposed", "Accepted", "Rejected", "Applied", "Completed", "Superseded"], key="decision_trial_status")
            status_note = status_col.text_input(
                "Status note / reason (optional)",
                placeholder="e.g. accepted after irrigation allocation review; rejected because rain is forecast",
                key="decision_trial_status_note",
            )
            if status_col.button("Update status", key="decision_trial_update_status"):
                registry.update_recommendation_status(rid, new_status, status_note.strip() or None)
                st.success("Recommendation status updated and added to its audit trail.")
                st.rerun()
            history = registry.recommendation_status_history(rid)
            if not history.empty:
                with st.expander("Recommendation status history", expanded=False):
                    st.dataframe(history[[c for c in ["changed_at", "old_status", "new_status", "note"] if c in history.columns]], hide_index=True, width="stretch")
            if field_id and field is not None:
                confirmed = task_col.checkbox("I have reviewed field state and want an operational task", value=False, key="decision_trial_task_confirm")
                if task_col.button("Create Field Operations task", disabled=not confirmed, key="decision_trial_create_task"):
                    row = recommendations.loc[recommendations.recommendation_id.astype(str).eq(rid)].iloc[0]
                    field_db.create_task(field_id, row["action_text"], category="Irrigation" if "irrig" in str(row["action_type"]).lower() else "Other", due_date=str(row.get("proposed_time") or date.today()), priority="Normal", description=f"Created from research recommendation {rid}. Verify agronomic conditions before action.", source="AGROLATTICE Research Recommendation")
                    st.success("Field Operations task created. The original recommendation remains separately auditable.")
            st.markdown("#### Record actual action and measured outcome")
            with st.form("decision_trial_outcome"):
                followed = st.selectbox("Was the recommendation followed?", ["Yes", "No"])
                actual_action = st.text_area("Actual action taken", placeholder="Record what was actually done, including deviations from the recommendation.")
                action_time = st.date_input("Action date", value=date.today())
                oc = st.columns(3)
                outcome_variable = oc[0].text_input("Measured outcome", value="Yield")
                outcome_value = oc[1].number_input("Outcome value", value=0.0)
                outcome_unit = oc[2].text_input("Outcome unit", value="t/ha")
                measured_at = st.date_input("Outcome measurement date", value=date.today())
                covariates_text = st.text_area("Context/covariates (one name=value per line)", placeholder="season_year=2026\nplanting_density=85000\nrainfall_mm=420\ngenotype=LineA")
                save_outcome = st.form_submit_button("Save treatment/outcome record", type="primary", width="stretch")
            if save_outcome:
                rec = recommendations.loc[recommendations.recommendation_id.astype(str).eq(rid)].iloc[0]
                oid = registry.save_treatment_outcome({"recommendation_id": rid, "field_id": rec.get("field_id"), "trial_id": rec.get("trial_id"), "experimental_unit_id": rec.get("experimental_unit_id"), "recommendation_followed": followed == "Yes", "actual_action_text": actual_action, "action_time": str(action_time), "outcome_variable": outcome_variable, "outcome_value": outcome_value, "outcome_unit": outcome_unit, "measured_at": str(measured_at), "covariates": _parse_covariates(covariates_text), "provenance": {"source": "AGROLATTICE recommendation follow-up", "app_version": app_version}})
                st.success(f"Outcome saved: {oid[:8]}")
        outcomes = registry.treatment_outcomes(field_id=field_id) if field_id else registry.treatment_outcomes()
        if not outcomes.empty:
            with st.expander("Recorded outcomes", expanded=False):
                st.dataframe(outcomes, hide_index=True, width="stretch")

    with tabs[5]:
        st.markdown("### Observational recommendation-effect audit")
        st.warning("A causal estimator cannot manufacture exchangeability. Treat results as estimates under an explicit causal graph/adjustment assumption, not proof that the recommendation caused the outcome.")
        table, source = _data_source_table("decision_causal", allow_registry_outcomes=True, registry=registry)
        if isinstance(table, pd.DataFrame) and not table.empty:
            numeric = [c for c in table.columns if pd.to_numeric(table[c], errors="coerce").notna().sum() >= 5]
            # Researchers often encode treatment as Yes/No, Applied/Not applied, A/B, or True/False.
            # Do not force them to recode a legitimate binary treatment into numbers before analysis.
            treatment_candidates = [
                c for c in table.columns
                if table[c].dropna().nunique() == 2 and table[c].notna().sum() >= 5
            ]
            if source == "Recommendation/outcome registry":
                treatment_default = "recommendation_followed" if "recommendation_followed" in treatment_candidates else (treatment_candidates[0] if treatment_candidates else None)
                outcome_default = "outcome_value" if "outcome_value" in numeric else (numeric[0] if numeric else None)
            else:
                treatment_default = treatment_candidates[0] if treatment_candidates else None
                outcome_default = next((c for c in numeric if c != treatment_default), numeric[0] if numeric else None)
            if not treatment_candidates or not numeric:
                st.info("The selected data need a binary treatment column (numeric or categorical) and a numeric outcome.")
            else:
                cols = st.columns(4)
                treatment = cols[0].selectbox("Binary treatment / followed recommendation", treatment_candidates, index=treatment_candidates.index(treatment_default) if treatment_default in treatment_candidates else 0, key="decision_causal_treatment")
                treatment_levels = list(pd.unique(table[treatment].dropna()))
                preferred_level = next((v for v in treatment_levels if v is True or (isinstance(v, (int, float, np.integer, np.floating)) and float(v) == 1.0)), None)
                if preferred_level is None:
                    positive_labels = {"yes", "true", "treated", "followed", "applied", "accepted", "intervention", "exposed"}
                    preferred_level = next((v for v in treatment_levels if str(v).strip().casefold() in positive_labels), treatment_levels[-1])
                treated_level = cols[1].selectbox(
                    "Treated / intervention level", treatment_levels,
                    index=treatment_levels.index(preferred_level), key="decision_causal_treated_level",
                    help="The reported effect is this level minus the other level. Set it explicitly so labels such as Followed/Not followed are never interpreted alphabetically.",
                )
                outcome_choices = [c for c in numeric if c != treatment] or numeric
                outcome = cols[2].selectbox("Outcome", outcome_choices, index=outcome_choices.index(outcome_default) if outcome_default in outcome_choices else 0, key="decision_causal_outcome")
                method = cols[3].selectbox("Estimator", ["Doubly robust AIPW", "IPW", "Outcome regression T-learner", "Naive difference (diagnostic only)"], key="decision_causal_method")
                st.caption(f"Effect direction: **{treated_level} minus {next(v for v in treatment_levels if v != treated_level)}**. Positive estimates mean a higher outcome under the selected treated/intervention level.")
                covariate_candidates = []
                for candidate in table.columns:
                    if candidate in {treatment, outcome}:
                        continue
                    unique_count = int(table[candidate].nunique(dropna=True))
                    numeric_count = int(pd.to_numeric(table[candidate], errors="coerce").notna().sum())
                    if numeric_count >= 5 or 2 <= unique_count <= min(50, max(2, len(table) // 2)):
                        covariate_candidates.append(candidate)
                covariates = st.multiselect(
                    "Pre-treatment adjustment covariates", covariate_candidates, key="decision_causal_covariates",
                    help="Numeric covariates are used directly. Categorical covariates such as genotype, site or management class are reference-coded internally. Include only plausible pre-treatment confounders, not mediators or outcomes.",
                )
                group_candidates = ["None"] + [c for c in table.columns if c not in {treatment, outcome} and table[c].nunique(dropna=True) >= 2 and table[c].nunique(dropna=True) <= max(50, len(table)//2)]
                group_column = st.selectbox("Cluster/group for cross-fitting & bootstrap (optional)", group_candidates, key="decision_causal_group", help="Use Trial ID, field, site or season when observations within a group are not independent. Grouped resampling avoids pretending clustered rows are independent.")
                st.caption("Only include variables measured before treatment/recommendation. Conditioning on mediators or post-treatment variables can bias the estimate.")
                causal_rationale = st.text_area(
                    "Adjustment rationale / causal-graph notes (recommended)",
                    placeholder="Why are these variables plausible pre-treatment common causes? Note variables intentionally excluded as mediators, colliders or post-treatment measurements.",
                    key="decision_causal_rationale",
                    help="This note is saved with the audit so another researcher can review the identification assumptions rather than seeing only a statistical model.",
                )
                controls = st.columns(2)
                bootstrap = controls[0].slider("Bootstrap iterations", 0, 500, 200, 25, key="decision_causal_bootstrap")
                placebo = controls[1].slider("Treatment-shuffle placebo iterations", 0, 300, 100, 25, key="decision_causal_placebo")
                if st.button("Run causal audit", type="primary", width="stretch", key="decision_causal_run"):
                    try:
                        result = causal_treatment_audit(
                            table, treatment_column=treatment, outcome_column=outcome, covariates=covariates,
                            method=method, group_column=None if group_column == "None" else group_column,
                            treated_value=treated_level, bootstrap_iterations=bootstrap, placebo_iterations=placebo,
                        )
                        st.session_state["decision_causal_result_11_5"] = result
                        st.session_state["decision_causal_context_11_5"] = {"source": source, "treatment": treatment, "treated_level": str(treated_level), "outcome": outcome, "covariates": covariates, "method": method, "group_column": None if group_column == "None" else group_column, "adjustment_rationale": causal_rationale.strip()}
                    except Exception as error:
                        st.error(str(error))
                result = st.session_state.get("decision_causal_result_11_5")
                context = st.session_state.get("decision_causal_context_11_5") or {}
                if result is not None and context.get("treatment") == treatment and context.get("treated_level") == str(treated_level) and context.get("outcome") == outcome:
                    cards = st.columns(4)
                    cards[0].metric("Estimated average effect", f"{result.estimate:.4g}")
                    cards[1].metric("95% bootstrap interval", "—" if result.lower_bound is None else f"{result.lower_bound:.4g} to {result.upper_bound:.4g}")
                    cards[2].metric("IPW effective N", f"{result.diagnostics.get('effective_sample_size_ipw', np.nan):.1f}")
                    cards[3].metric("Placebo p-value", "—" if result.placebo_p_value is None else f"{result.placebo_p_value:.3f}")
                    if result.diagnostics.get("positivity_warning"):
                        st.error("Poor treatment overlap / positivity warning. The effect estimate may rely on extrapolation and should not be promoted.")
                    if result.balance is not None and not result.balance.empty:
                        st.markdown("#### Covariate balance")
                        st.dataframe(result.balance, hide_index=True, width="stretch")
                        st.caption("Categorical covariates are shown as encoded levels. As a rough diagnostic, |standardised mean difference| < 0.1 after weighting is often desired; this is not a guarantee of no unmeasured confounding.")
                    with st.expander("Unit-level diagnostics and propensity scores", expanded=False):
                        st.dataframe(result.unit_effects, hide_index=True, width="stretch")
                    st.markdown("#### Assumptions that must be defended")
                    for item in result.diagnostics.get("assumptions", []):
                        st.markdown(f"- {item}")
                    if st.button("Save causal audit", key="decision_causal_save"):
                        diagnostics_to_save = dict(result.diagnostics)
                        diagnostics_to_save["adjustment_rationale"] = context.get("adjustment_rationale", causal_rationale.strip())
                        aid = registry.save_causal_analysis({"name": f"{outcome} effect of {treatment}", "treatment": treatment, "outcome": outcome, "covariates": covariates, "group_column": None if group_column == "None" else group_column, "method": method, "assumptions": result.diagnostics.get("assumptions"), "diagnostics": diagnostics_to_save, "estimates": {"ate": result.estimate, "lower_95": result.lower_bound, "upper_95": result.upper_bound, "placebo_p": result.placebo_p_value}, "provenance": {"source": source, "treated_level": str(treated_level), "effect_direction": result.diagnostics.get("effect_direction"), "adjustment_rationale": context.get("adjustment_rationale", causal_rationale.strip()), "app_version": app_version, "module_version": MODULE_VERSION}})
                        st.success(f"Causal audit saved: {aid[:8]}")

    with tabs[6]:
        st.markdown("### Method boundaries")
        methods = pd.DataFrame([
            ["Irrigation policy studio", "FAO-style daily root-zone water balance + explicit policy grid + Pareto screening", "Scenario comparison; no pump/valve control. Ky-based relative yield is a water-stress proxy, not a calibrated yield forecast."],
            ["Nutrient optimisation", "Second-order empirical N/P/K response surface with Ridge regularisation + grouped/K-fold validation + non-dominated screening", "Requires measured outcome and rate variation. Does not infer nutrient recommendations from soil/tissue concentration alone."],
            ["State assimilation", "Independent Gaussian scalar update", "Prior and observation must represent the same state/units or a separately validated transformation."],
            ["Causal audit", "Naive, IPW, T-learner and doubly robust AIPW-style observational estimators + overlap/balance/placebo diagnostics", "Requires defensible pre-treatment adjustment set and positivity; unmeasured confounding remains possible."],
        ], columns=["Tool", "Implementation", "Scientific boundary"])
        st.dataframe(methods, hide_index=True, width="stretch")
        st.markdown("### Researcher safeguards")
        st.markdown(
            "- NASA POWER is retrieved automatically when useful, but remains gridded environmental data rather than local station measurement.\n"
            "- Recorded irrigation/fertiliser operations remain separate from recommendations.\n"
            "- Search ranges default to observed/calibrated support; extrapolation should be explicit.\n"
            "- Pareto alternatives are shown instead of hiding trade-offs behind one score.\n"
            "- A recommendation can become a Field Operations task only after an explicit user acknowledgement.\n"
            "- Treatment outcomes are persisted so effectiveness can be evaluated later rather than inferred from model accuracy."
        )
        st.caption(f"Decision Intelligence module {MODULE_VERSION} · country workspace: {selected_country} · app {app_version}")
