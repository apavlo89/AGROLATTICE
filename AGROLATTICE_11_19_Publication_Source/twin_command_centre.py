"""AGROLATTICE 11.9 Persistent Twin Command Centre.

A researcher-facing orchestration layer over the existing Persistent Twin,
Mechanistic Maize Twin, Field Operations, Maize Synchrony Lab and Research
Evidence registries.  The command centre deliberately keeps expensive remote
retrieval and model calibration behind explicit user actions.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any, Mapping
from navigation_state import consume_view_request, queue_view_request

import folium
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

from agrolattice_twin import (
    AgroLatticeTwinDatabase,
    _field_geometry,
    _loads,
    _num,
    _render_twin_root_zone_manager,
    _render_twin_satellite_manager,
    _render_twin_weather_manager,
    _resolve_bundle,
    _trial_geometry,
    _weather_frame,
    build_twin_state,
    generate_recommendations,
    next_season_design,
    simulate_scenarios,
    twin_boundary_map,
)
from maize_mechanistic_twin import (
    DEFAULT_PHYSIOLOGY,
    PUBLICATION_DOI,
    PhysiologyParameters,
    calibrate_parent_physiology,
    optimise_male_sowing_strategy,
    physiology_from_mapping,
    simulate_mfs,
)

MODULE_VERSION = "1.0.1"
VIEWS = [
    "Overview",
    "Spatial Twin",
    "Development & water",
    "Timeline",
    "Scenarios",
    "Measurements & copilot",
    "Evidence & validation",
    "Setup",
]


def _date_max(*frames: tuple[pd.DataFrame, list[str]]) -> date:
    values: list[pd.Timestamp] = []
    for frame, candidates in frames:
        if not isinstance(frame, pd.DataFrame) or frame.empty:
            continue
        for name in candidates:
            if name in frame.columns:
                values.extend(pd.to_datetime(frame[name], errors="coerce").dropna().tolist())
                break
    return max(values).date() if values else date.today()


def _active_link(db: AgroLatticeTwinDatabase) -> dict[str, Any] | None:
    links = db.links()
    if links.empty:
        return None
    options = links["link_id"].astype(str).tolist()
    labels = {
        str(row["link_id"]): str(row["name"])
        for _, row in links.iterrows()
    }
    current = str(st.session_state.get("agrolattice_active_twin_link_id") or "")
    if current not in options:
        current = options[0]
    selected = st.selectbox(
        "Active Twin",
        options,
        index=options.index(current),
        format_func=lambda value: labels.get(str(value), str(value)),
        key="twin_cc_active_selector",
    )
    st.session_state.agrolattice_active_twin_link_id = str(selected)
    return db.link(str(selected))


def _set_view(view: str) -> None:
    # Buttons are rendered after the navigation radio. Queue the request rather
    # than modifying either widget-owned state key in the same Streamlit run.
    queue_view_request(
        st.session_state,
        request_key="twin_cc_view_request",
        target=view,
    )


def _view_control() -> str:
    current = consume_view_request(
        st.session_state,
        request_key="twin_cc_view_request",
        widget_key="twin_cc_view_radio",
        mirror_key="twin_cc_view",
        options=VIEWS,
        default="Overview",
    )
    view = st.radio(
        "Twin workspace",
        VIEWS,
        index=VIEWS.index(current),
        horizontal=True,
        label_visibility="collapsed",
        key="twin_cc_view_radio",
    )
    st.session_state.twin_cc_view = view
    return view


def _parent_info(pollination_db, trial: Mapping[str, Any] | None, role: str) -> tuple[PhysiologyParameters, str, dict[str, Any]]:
    if not trial:
        return DEFAULT_PHYSIOLOGY, "Publication prior", {}
    role_name = "Male" if role.casefold().startswith("m") else "Female"
    parent = str((trial.get("male_parent") if role_name == "Male" else trial.get("female_parent")) or "").strip()
    if not parent:
        return DEFAULT_PHYSIOLOGY, "Publication prior", {"Parent line": "Unspecified", "Role": role_name}
    try:
        frame = pollination_db.parent_physiology([parent])
    except Exception:
        frame = pd.DataFrame()
    if not frame.empty:
        selected = frame.loc[frame["Role"].astype(str).str.casefold().eq(role_name.casefold())]
        if not selected.empty:
            row = selected.iloc[0].to_dict()
            params = physiology_from_mapping(row)
            method = str(row.get("Method") or "Stored physiology")
            source = str(row.get("Source") or "").strip()
            label = method + (f" · {source}" if source else "")
            return params, label, row
    return DEFAULT_PHYSIOLOGY, "Publication prior from Laurent et al. (2025)", {
        "Parent line": parent,
        "Role": role_name,
        **DEFAULT_PHYSIOLOGY.to_record(),
        "Method": "Publication prior",
        "Source": f"Laurent et al. 2025 DOI {PUBLICATION_DOI}",
        "Sample size": None,
    }


def _state_bundle(db, field_db, pollination_db, context, link, as_of=None):
    bundle = _resolve_bundle(link, field_db, pollination_db, context, db)
    if link.get("trial_id"):
        try:
            bundle["leaf_observations"] = pollination_db.leaf_observations(link.get("trial_id"))
        except Exception:
            bundle["leaf_observations"] = pd.DataFrame()
    else:
        bundle["leaf_observations"] = pd.DataFrame()
    bundle["field_observations"] = field_db.detailed_observations(bundle["field"].get("field_id")) if bundle.get("field") else pd.DataFrame()
    bundle["field_operations"] = field_db.detailed_operations(bundle["field"].get("field_id")) if bundle.get("field") else pd.DataFrame()
    weather = _weather_frame(context, bundle["weather"], bundle["trial"], bundle.get("twin_weather"))
    latest = _date_max(
        (weather, ["Date"]),
        (bundle["observations"], ["Date"]),
        (bundle["satellite"], ["Date", "Acquisition UTC"]),
        (bundle["root_zone"], ["Date"]),
    )
    if as_of is None:
        as_of = st.session_state.get("twin_cc_as_of", latest)
    try:
        as_of = pd.Timestamp(as_of).date()
    except Exception:
        as_of = latest
    st.session_state.twin_cc_as_of = as_of
    male_params, male_source, male_record = _parent_info(pollination_db, bundle.get("trial"), "Male")
    female_params, female_source, female_record = _parent_info(pollination_db, bundle.get("trial"), "Female")
    state, plot_states, manifest = build_twin_state(
        context=context,
        field=bundle["field"],
        trial=bundle["trial"],
        plots=bundle["plots"],
        observations=bundle["observations"],
        harvest=bundle["harvest"],
        trial_weather=bundle["weather"],
        twin_weather=bundle.get("twin_weather"),
        root_zone=bundle["root_zone"],
        satellite=bundle["satellite"],
        sensors=bundle["sensors"],
        sensor_readings=bundle["readings"],
        tasks=bundle["tasks"],
        alerts=bundle["alerts"],
        settings=db.settings(link["link_id"]),
        as_of=as_of,
        male_physiology=male_params,
        female_physiology=female_params,
        male_physiology_source=male_source,
        female_physiology_source=female_source,
    )
    st.session_state.agrolattice_twin_state = state
    st.session_state.agrolattice_twin_plot_states = plot_states
    st.session_state.agrolattice_twin_manifest = manifest
    return bundle, weather, state, plot_states, manifest, male_params, female_params, male_record, female_record


def _context_header(link, bundle, state) -> None:
    field = bundle.get("field") or {}
    trial = bundle.get("trial") or {}
    farm = str(field.get("farm_name") or "Unassigned research centre")
    field_name = str(field.get("name") or state.get("Field") or "Unlinked field")
    trial_name = str(trial.get("name") or "No trial linked")
    crop = str(state.get("Crop") or field.get("crop") or "Crop not set")
    year = field.get("season_year") or trial.get("season_year") or ""
    st.markdown(f"### {link.get('name')}")
    st.caption(f"{farm} → {field_name} → {trial_name} · {crop}{' · ' + str(year) if year else ''}")


def _metric(value: Any, fmt: str, missing: str = "NA") -> str:
    number = _num(value)
    return fmt.format(number) if np.isfinite(number) else missing


def _render_twin_pulse(state: Mapping[str, Any]) -> None:
    st.markdown("### Twin Pulse")
    rows = []
    model = state.get("Phenology model") or "No phenology model"
    male = state.get("Predicted male 50% flowering")
    female = state.get("Predicted female 50% silking")
    rows.append(("Development · Modelled", f"{model}; male anthesis {male or 'not reached/forecast unavailable'}, female silking {female or 'not reached/forecast unavailable'}."))
    ks = _num(state.get("Latest root-zone Ks"))
    if np.isfinite(ks):
        rows.append(("Water · Modelled", f"Root-zone stress coefficient Ks = {ks:.2f}."))
    ndvi = _num(state.get("Latest NDVI"))
    if np.isfinite(ndvi):
        rows.append(("Earth observation · Retrieved/derived", f"Latest field NDVI = {ndvi:.3f}."))
    gap = _num(state.get("Predicted synchrony gap (days)"))
    if np.isfinite(gap):
        rows.append(("Synchrony · Modelled", f"Male-minus-female timing gap = {gap:+.1f} day(s). Timing overlap does not guarantee pollen quantity or seed purity."))
    disagreement = _num(state.get("Model disagreement (days)"))
    if np.isfinite(disagreement):
        rows.append(("Model disagreement", f"Mechanistic and legacy/observed-target timing differ by about {disagreement:.1f} day(s) on average."))
    rows.append(("Field execution · Recorded", f"{int(state.get('Open tasks', 0))} open task(s), {int(state.get('Overdue tasks', 0))} overdue, {int(state.get('Open alerts', 0))} open alert(s)."))
    for label, text in rows:
        st.markdown(f"**{label}** — {text}")


def _state_chain(bundle, state, manifest) -> pd.DataFrame:
    return pd.DataFrame([
        {"Twin component": "Environment", "Status": "Ready" if manifest.get("weather_rows", 0) else "Missing", "Evidence": f"{manifest.get('weather_rows',0)} daily weather rows"},
        {"Twin component": "Soil / root zone", "Status": "Ready" if manifest.get("root_zone_rows", 0) else "Partial / missing", "Evidence": f"{manifest.get('root_zone_rows',0)} root-zone rows"},
        {"Twin component": "Crop development", "Status": "Modelled" if state.get("Phenology model") else "Missing", "Evidence": str(state.get("Phenology model") or "No model")},
        {"Twin component": "Phenology / stress", "Status": "Observed + modelled" if manifest.get("observation_rows", 0) else "Modelled only", "Evidence": f"{manifest.get('observation_rows',0)} flowering observation rows"},
        {"Twin component": "Management", "Status": "Recorded" if not bundle.get("field_operations", pd.DataFrame()).empty else "Partial / missing", "Evidence": f"{len(bundle.get('field_operations', pd.DataFrame()))} operation records"},
        {"Twin component": "EO / sensors", "Status": "Ready" if manifest.get("satellite_rows", 0) or manifest.get("sensor_rows", 0) else "Missing", "Evidence": f"{manifest.get('satellite_rows',0)} EO + {manifest.get('sensor_rows',0)} sensor rows"},
        {"Twin component": "Treatments", "Status": "Ready" if not bundle.get("plots", pd.DataFrame()).empty else "Not linked", "Evidence": f"{len(bundle.get('plots', pd.DataFrame()))} experimental units"},
        {"Twin component": "Phenotype", "Status": "Ready" if manifest.get("observation_rows", 0) else "Missing", "Evidence": "Field / trial observations"},
        {"Twin component": "Outcome", "Status": "Observed" if not bundle.get("harvest", pd.DataFrame()).empty else "Not yet observed", "Evidence": f"{len(bundle.get('harvest', pd.DataFrame()))} harvest rows"},
    ])


def _overview(db, field_db, pollination_db, research_registry, context, link) -> None:
    bundle, weather, state, plot_states, manifest, male_params, female_params, _, _ = _state_bundle(db, field_db, pollination_db, context, link)
    _context_header(link, bundle, state)
    as_of = st.date_input("Twin state date", value=st.session_state.get("twin_cc_as_of", date.today()), key="twin_cc_overview_asof")
    if as_of != st.session_state.get("twin_cc_as_of"):
        st.session_state.twin_cc_as_of = as_of
        st.rerun()

    cards = st.columns(4)
    with cards[0].container(border=True):
        st.markdown("**Crop development**")
        st.metric("Male flowering", _metric(state.get("Male progress (%)"), "{:.0f}%"))
        st.metric("Female silking", _metric(state.get("Female progress (%)"), "{:.0f}%"))
        st.caption(str(state.get("Phenology model") or "No phenology model"))
    with cards[1].container(border=True):
        st.markdown("**Environment**")
        st.metric("Root-zone Ks", _metric(state.get("Latest root-zone Ks"), "{:.2f}"))
        st.metric("Rain · 7 d", _metric(state.get("Rain last 7 days (mm)"), "{:.1f} mm"))
        st.caption(f"Heat days ≥35°C: {int(state.get('Heat days ≥35°C last 7 days', 0))}")
    with cards[2].container(border=True):
        st.markdown("**Synchrony / outcome**")
        st.metric("Timing gap", _metric(state.get("Predicted synchrony gap (days)"), "{:+.1f} d"))
        st.metric("Timing-overlap index", _metric(state.get("Estimated receptive-silk coverage (%)"), "{:.0f}%"))
        st.caption("Timing overlap is not pollen quantity or seed purity.")
    with cards[3].container(border=True):
        st.markdown("**Evidence quality**")
        st.metric("Data completeness", _metric(state.get("Data completeness score"), "{:.0f}/100"))
        st.metric("Model disagreement", _metric(state.get("Model disagreement (days)"), "{:.1f} d"))
        st.caption(f"Parameter uncertainty: {state.get('Parameter uncertainty') or 'Not estimated'}")

    left, right = st.columns([1.35, 1.0])
    with left:
        _render_twin_pulse(state)
    with right:
        st.markdown("### Most useful action now")
        recs = generate_recommendations(plot_states=plot_states, state=state)
        if not recs.empty:
            first = recs.iloc[0]
            st.info(f"**{first.get('Title')}**\n\n{first.get('Rationale')}\n\nSuggested measurement: {first.get('Suggested measurements')}")
            if st.button("Open Measurements & copilot", width="stretch", key="twin_cc_go_copilot"):
                _set_view("Measurements & copilot"); st.rerun()
        elif not manifest.get("weather_rows"):
            st.warning("Attach daily weather before relying on crop-development timing.")
            if st.button("Open Setup", width="stretch", key="twin_cc_go_setup"):
                _set_view("Setup"); st.rerun()
        else:
            st.success("No high-priority measurement prompt is currently generated from the saved state.")

    st.markdown("### Persistent Twin state chain")
    st.dataframe(_state_chain(bundle, state, manifest), hide_index=True, width="stretch")
    c1, c2, c3 = st.columns(3)
    if c1.button("Save research checkpoint", type="primary", width="stretch", key="twin_cc_checkpoint"):
        sid = db.save_snapshot(link["link_id"], as_of=st.session_state.get("twin_cc_as_of"), state=state, plot_states=plot_states, input_manifest=manifest)
        db.log_event(link["link_id"], event_type="Snapshot", title="Twin research checkpoint saved", event_time=st.session_state.get("twin_cc_as_of"), details={"snapshot_id": sid})
        st.success(f"Checkpoint saved: {sid[:12]}")
    if c2.button("Open Spatial Twin", width="stretch", key="twin_cc_go_map"):
        _set_view("Spatial Twin"); st.rerun()
    if c3.button("Open Evidence & validation", width="stretch", key="twin_cc_go_evidence"):
        _set_view("Evidence & validation"); st.rerun()


def _add_spatial_points(map_object, bundle, field_db, show_sensors, show_observations, show_operations):
    if show_sensors and isinstance(bundle.get("sensors"), pd.DataFrame) and not bundle["sensors"].empty:
        group = folium.FeatureGroup(name="Sensors", show=True)
        for _, row in bundle["sensors"].iterrows():
            lat, lon = _num(row.get("latitude")), _num(row.get("longitude"))
            if np.isfinite(lat) and np.isfinite(lon):
                folium.CircleMarker([lat, lon], radius=5, color="#0f766e", fill=True, tooltip=f"Sensor: {row.get('name','')} · {row.get('sensor_type','')}").add_to(group)
        group.add_to(map_object)
    if show_observations and isinstance(bundle.get("field_observations"), pd.DataFrame) and not bundle["field_observations"].empty:
        group = folium.FeatureGroup(name="Field observations", show=True)
        for _, row in bundle["field_observations"].head(1000).iterrows():
            lat, lon = _num(row.get("latitude")), _num(row.get("longitude"))
            if np.isfinite(lat) and np.isfinite(lon):
                label = row.get("category") or row.get("protocol_name") or "Observation"
                folium.CircleMarker([lat, lon], radius=4, color="#7c3aed", fill=True, tooltip=f"{label} · {row.get('observed_at','')}").add_to(group)
        group.add_to(map_object)
    if show_operations and isinstance(bundle.get("field_operations"), pd.DataFrame) and not bundle["field_operations"].empty:
        group = folium.FeatureGroup(name="Management operations", show=False)
        for _, row in bundle["field_operations"].head(500).iterrows():
            geom = _loads(row.get("geometry_json"), None)
            if geom:
                try:
                    folium.GeoJson(geom, tooltip=f"{row.get('category','Operation')} · {row.get('operation_date','')}").add_to(group)
                except Exception:
                    pass
        group.add_to(map_object)
    folium.LayerControl(collapsed=False).add_to(map_object)


def _spatial(db, field_db, pollination_db, research_registry, context, link) -> None:
    bundle, weather, state, plot_states, manifest, *_ = _state_bundle(db, field_db, pollination_db, context, link)
    _context_header(link, bundle, state)
    st.caption("The map is built only when this view is opened. Field geometry remains authoritative; trials and experimental units are linked spatial objects, not replacements for the field boundary.")
    controls = st.columns(4)
    metrics = [c for c in ["Inspection priority score", "Measurement uncertainty (%)", "Flowering-window criticality (%)", "Estimated overlap (%)", "Predicted seed set (%)", "Male flowering progress (%)", "Female silking progress (%)"] if c in plot_states.columns]
    metric = controls[0].selectbox("Treatment-unit layer", ["No analytical fill"] + metrics, key="twin_cc_map_metric") if metrics else "No analytical fill"
    show_sensors = controls[1].checkbox("Sensors", value=True, key="twin_cc_map_sensors")
    show_observations = controls[2].checkbox("Scouting / observations", value=True, key="twin_cc_map_obs")
    show_operations = controls[3].checkbox("Operation polygons", value=False, key="twin_cc_map_ops")
    map_object = twin_boundary_map(bundle.get("trial"), bundle.get("field"), bundle.get("plots"), plot_states=plot_states if not plot_states.empty else None, metric=None if metric == "No analytical fill" else metric)
    _add_spatial_points(map_object, bundle, field_db, show_sensors, show_observations, show_operations)
    st_folium(map_object, height=700, use_container_width=True, key="twin_cc_spatial_map")
    field_geom, trial_geom = _field_geometry(bundle.get("field")), _trial_geometry(bundle.get("trial"))
    qa = pd.DataFrame([
        {"Geometry": "Mapped field", "Available": bool(field_geom), "Area (ha)": (bundle.get("field") or {}).get("area_ha")},
        {"Geometry": "Maize trial", "Available": bool(trial_geom), "Area (ha)": (bundle.get("trial") or {}).get("field_area_ha")},
        {"Geometry": "Experimental units", "Available": not bundle.get("plots", pd.DataFrame()).empty, "Area (ha)": pd.to_numeric(bundle.get("plots", pd.DataFrame()).get("Area (ha)"), errors="coerce").sum() if not bundle.get("plots", pd.DataFrame()).empty else np.nan},
    ])
    st.dataframe(qa, hide_index=True, width="stretch")


def _development(db, field_db, pollination_db, research_registry, context, link) -> None:
    bundle, weather, state, plot_states, manifest, male_params, female_params, male_record, female_record = _state_bundle(db, field_db, pollination_db, context, link)
    _context_header(link, bundle, state)
    st.markdown("### Mechanistic maize development")
    if not bundle.get("trial"):
        st.info("No maize synchrony trial is linked. Environmental and generic Twin state remain available, but parent-specific mechanistic flowering requires a maize trial.")
    else:
        params = pd.DataFrame([
            {"Parent role": "Male", "Parent line": (bundle["trial"] or {}).get("male_parent"), **male_params.to_record(), "Source": state.get("Male physiology source")},
            {"Parent role": "Female", "Parent line": (bundle["trial"] or {}).get("female_parent"), **female_params.to_record(), "Source": state.get("Female physiology source")},
        ])
        st.dataframe(params, hide_index=True, width="stretch")
        st.caption("Publication priors are informative assumptions, not measurements of local inbred lines. Calibrated parameters remain explicitly labelled with their source and sample size.")

        timeline = go.Figure()
        for label, event, p05, p95 in [
            ("Male anthesis", state.get("Predicted male 50% flowering"), state.get("Male event P05"), state.get("Male event P95")),
            ("Female silking", state.get("Predicted female 50% silking"), state.get("Female event P05"), state.get("Female event P95")),
        ]:
            if event:
                event_ts = pd.Timestamp(event)
                timeline.add_trace(go.Scatter(x=[event_ts], y=[label], mode="markers", marker=dict(size=13), name=label))
                if p05 and p95:
                    timeline.add_trace(go.Scatter(x=[pd.Timestamp(p05), pd.Timestamp(p95)], y=[label, label], mode="lines", line=dict(width=8), name=f"{label} P05–P95", showlegend=False))
        timeline.update_layout(height=280, title="Predicted flowering timing and parameter-uncertainty interval when weather coverage permits", xaxis_title="Date", yaxis_title="")
        st.plotly_chart(timeline, width="stretch")

        if not weather.empty:
            frames = []
            trial = bundle["trial"] or {}
            sowings = [("Male", trial.get("female_sowing_date"), male_params)]
            # Prefer the median stored male sowing among treatment units.
            if not bundle["plots"].empty and "Male sowing" in bundle["plots"]:
                ms = pd.to_datetime(bundle["plots"]["Male sowing"], errors="coerce").dropna()
                male_sowing = ms.median() if not ms.empty else pd.to_datetime(trial.get("female_sowing_date"), errors="coerce")
            else:
                male_sowing = pd.to_datetime(trial.get("female_sowing_date"), errors="coerce")
            female_sowing = pd.to_datetime(trial.get("female_sowing_date"), errors="coerce")
            for role, sowing, pars in [("Male", male_sowing, male_params), ("Female", female_sowing, female_params)]:
                if pd.notna(sowing):
                    try:
                        sim, _ = simulate_mfs(weather, sowing, pars)
                        sim["Parent role"] = role
                        frames.append(sim)
                    except Exception:
                        pass
            if frames:
                development = pd.concat(frames, ignore_index=True)
                plot = development[["Date", "Parent role", "Predicted collared leaf number"]]
                st.plotly_chart(px.line(plot, x="Date", y="Predicted collared leaf number", color="Parent role", title="Mechanistic leaf-development trajectory"), width="stretch")
    cols = st.columns(2)
    with cols[0]:
        st.markdown("### Root-zone water")
        rz = bundle.get("root_zone", pd.DataFrame())
        if rz.empty:
            st.info("No persistent root-zone series is attached.")
        else:
            y = [c for c in ["Ks", "Relative depletion"] if c in rz.columns]
            if y:
                plot = rz[["Date", *y]].melt("Date", var_name="Signal", value_name="Value")
                st.plotly_chart(px.line(plot, x="Date", y="Value", color="Signal", title="Root-zone state"), width="stretch")
    with cols[1]:
        st.markdown("### Earth observation")
        sat = bundle.get("satellite", pd.DataFrame())
        if sat.empty:
            st.info("No persistent Sentinel-2 time series is attached.")
        else:
            y = [c for c in sat.columns if str(c).casefold() in {"ndvi mean", "ndvi median", "ndmi mean", "ndmi median"}]
            if y:
                plot = sat[["Date", *y]].melt("Date", var_name="Index", value_name="Value")
                st.plotly_chart(px.line(plot, x="Date", y="Value", color="Index", markers=True, title="Field-level EO trajectory"), width="stretch")
    st.warning("Mechanistic timing does not guarantee pollen quantity, fertilisation success, seed purity or final yield. Those outcomes require their own observations and validated outcome models.")


def _timeline(db, field_db, pollination_db, research_registry, context, link) -> None:
    bundle, weather, state, plot_states, manifest, male_params, female_params, *_ = _state_bundle(db, field_db, pollination_db, context, link)
    _context_header(link, bundle, state)
    st.markdown("### Time travel")
    all_dates = []
    for frame, cols in [(weather,["Date"]),(bundle.get("observations"),["Date"]),(bundle.get("field_operations"),["operation_date"]),(bundle.get("satellite"),["Date"]),(bundle.get("root_zone"),["Date"])]:
        if isinstance(frame, pd.DataFrame) and not frame.empty:
            for c in cols:
                if c in frame:
                    all_dates += pd.to_datetime(frame[c], errors="coerce").dropna().tolist(); break
    minimum = min(all_dates).date() if all_dates else date.today() - timedelta(days=30)
    maximum = max(all_dates).date() if all_dates else date.today()
    chosen = st.date_input("Reconstruct Twin state as of", value=st.session_state.get("twin_cc_as_of", maximum), min_value=minimum, max_value=max(maximum, date.today()), key="twin_cc_time_date")
    if chosen != st.session_state.get("twin_cc_as_of"):
        st.session_state.twin_cc_as_of = chosen
        st.rerun()
    metrics = st.columns(5)
    metrics[0].metric("Male progress", _metric(state.get("Male progress (%)"), "{:.0f}%"))
    metrics[1].metric("Female progress", _metric(state.get("Female progress (%)"), "{:.0f}%"))
    metrics[2].metric("Root-zone Ks", _metric(state.get("Latest root-zone Ks"), "{:.2f}"))
    metrics[3].metric("NDVI", _metric(state.get("Latest NDVI"), "{:.3f}"))
    metrics[4].metric("Data completeness", _metric(state.get("Data completeness score"), "{:.0f}/100"))

    events = db.events(link["link_id"])
    timeline_rows = []
    if not events.empty:
        for _, row in events.iterrows():
            timeline_rows.append({"When": row.get("event_time"), "Type": row.get("event_type"), "Event": row.get("title"), "Source": row.get("source")})
    ops = bundle.get("field_operations", pd.DataFrame())
    if isinstance(ops, pd.DataFrame) and not ops.empty:
        for _, row in ops.head(500).iterrows():
            timeline_rows.append({"When": row.get("operation_date"), "Type": "Management", "Event": row.get("category") or "Field operation", "Source": row.get("record_type") or "Field Operations"})
    obs = bundle.get("observations", pd.DataFrame())
    if isinstance(obs, pd.DataFrame) and not obs.empty:
        for _, row in obs.head(500).iterrows():
            timeline_rows.append({"When": row.get("Date"), "Type": "Phenotype observation", "Event": f"Flowering observation · {row.get('Plot','plot')}", "Source": "Maize Synchrony Lab"})
    pheno = bundle.get("phenology", pd.DataFrame())
    if isinstance(pheno, pd.DataFrame) and not pheno.empty:
        for _, row in pheno.head(500).iterrows():
            for col, label in [("Male flowering date","Observed male flowering"),("Female flowering date","Observed female flowering")]:
                if row.get(col):
                    timeline_rows.append({"When": row.get(col), "Type": "Phenology event", "Event": f"{label} · {row.get('Plot','plot')}", "Source": "Measured / recorded"})
    timeline_frame = pd.DataFrame(timeline_rows)
    if not timeline_frame.empty:
        timeline_frame["When"] = pd.to_datetime(timeline_frame["When"], errors="coerce")
        timeline_frame = timeline_frame.dropna(subset=["When"]).sort_values("When", ascending=False)
        st.dataframe(timeline_frame, hide_index=True, width="stretch")
    else:
        st.info("No timeline events have been recorded yet.")

    saved = db.snapshots(link["link_id"])
    if not saved.empty:
        decoded = []
        for _, row in saved.iterrows():
            item = _loads(row["state_json"], {})
            item["As of"] = row["as_of"]
            decoded.append(item)
        history = pd.DataFrame(decoded)
        metrics_to_plot = [c for c in ["Male progress (%)","Female progress (%)","Estimated receptive-silk coverage (%)","Composite state indicator","Data completeness score"] if c in history]
        if metrics_to_plot:
            plot = history[["As of", *metrics_to_plot]].melt("As of", var_name="Metric", value_name="Value")
            st.plotly_chart(px.line(plot, x="As of", y="Value", color="Metric", markers=True, title="Saved Twin checkpoints"), width="stretch")


def _scenarios(db, field_db, pollination_db, research_registry, context, link) -> None:
    bundle, weather, state, plot_states, manifest, male_params, female_params, *_ = _state_bundle(db, field_db, pollination_db, context, link)
    _context_header(link, bundle, state)
    st.markdown("### Mechanistic sowing-strategy explorer")
    trial = bundle.get("trial") or {}
    female_sowing = pd.to_datetime(trial.get("female_sowing_date"), errors="coerce")
    if bundle.get("trial") and not weather.empty and pd.notna(female_sowing):
        c = st.columns(4)
        min_offset = c[0].number_input("Minimum male offset (d)", -30, 30, -10, key="twin_cc_mech_min")
        max_offset = c[1].number_input("Maximum male offset (d)", -30, 30, 14, key="twin_cc_mech_max")
        strategy = c[2].selectbox("Male sowing strategy", ["Compare single and two-date strategies", "One male sowing date", "Two staggered male sowing dates"], key="twin_cc_mech_strategy")
        draws = c[3].selectbox("Parameter draws", [200, 500, 1000], index=1, key="twin_cc_mech_draws")
        if st.button("Run mechanistic synchrony strategy comparison", type="primary", key="twin_cc_mech_run", width="stretch"):
            try:
                result = optimise_male_sowing_strategy(weather, female_sowing, female_params, male_params, minimum_offset=int(min_offset), maximum_offset=int(max_offset), strategy=strategy, draws=int(draws))
                st.session_state.twin_cc_mechanistic_strategy = result
            except Exception as error:
                st.error(f"Mechanistic strategy comparison could not run: {error}")
        result = st.session_state.get("twin_cc_mechanistic_strategy")
        if isinstance(result, pd.DataFrame) and not result.empty:
            st.dataframe(result.head(30), hide_index=True, width="stretch")
            recommended = result.loc[result.get("Recommended", False).astype(bool)] if "Recommended" in result else pd.DataFrame()
            if not recommended.empty:
                st.success("Recommended rows maximise the paper-inspired timing objective under parameter uncertainty; they do not simulate pollen quantity or guarantee seed purity.")
                if st.button("Save mechanistic strategy scenario", key="twin_cc_save_mech"):
                    sid = db.save_scenario(link["link_id"], "Mechanistic male sowing strategy", {"method":"Laurent-derived mechanistic sowing optimisation", "draws": int(draws)}, result)
                    db.log_event(link["link_id"], event_type="Scenario", title="Mechanistic sowing strategy saved", details={"scenario_id":sid})
                    st.success(f"Scenario saved: {sid[:12]}")
    else:
        st.info("Attach weather and link a maize trial to activate mechanistic sowing-strategy analysis.")

    st.markdown("### Exploratory environment & management scenarios")
    st.caption("These scenarios use the transparent response approximation already present in AGROLATTICE. They are intentionally not presented as equivalent to a mechanistic crop simulation.")
    with st.form("twin_cc_exploratory_form"):
        name = st.text_input("Scenario name", value="Alternative management scenario")
        c1, c2, c3 = st.columns(3)
        temp = c1.number_input("Temperature change (°C)", -8.0, 8.0, 0.0, 0.5)
        rain = c2.number_input("Rainfall multiplier", 0.0, 3.0, 1.0, 0.1)
        irrigation = c3.number_input("Additional irrigation (mm)", -200.0, 500.0, 0.0, 5.0)
        c4, c5, c6 = st.columns(3)
        offset = c4.number_input("Male sowing-offset change (d)", -30, 30, 0)
        density = c5.number_input("Planting-density change (%)", -80.0, 100.0, 0.0, 5.0)
        heat = c6.number_input("Additional heat days", -20, 30, 0)
        run = st.form_submit_button("Compare and save exploratory scenario", type="primary", width="stretch")
    if run:
        result = simulate_scenarios(state=state, plot_states=plot_states, temperature_delta_c=float(temp), rainfall_multiplier=float(rain), irrigation_change_mm=float(irrigation), male_offset_change_days=int(offset), density_change_percent=float(density), heat_days_change=int(heat))
        sid = db.save_scenario(link["link_id"], name, {"temperature_delta_c":temp,"rainfall_multiplier":rain,"irrigation_change_mm":irrigation,"male_offset_change_days":offset,"density_change_percent":density,"heat_days_change":heat,"method":"Transparent exploratory response model"}, result)
        db.log_event(link["link_id"], event_type="Scenario", title=f"Exploratory scenario saved: {name}", details={"scenario_id":sid})
        st.session_state.agrolattice_twin_scenario = result
        st.success(f"Scenario saved: {sid[:12]}")
        st.dataframe(result, hide_index=True, width="stretch")

    saved = db.scenarios(link["link_id"])
    if not saved.empty:
        st.markdown("### Saved scenario library")
        st.dataframe(saved[[c for c in ["name","created_at"] if c in saved]], hide_index=True, width="stretch")

    analogue_results = context.get("climate_analogue_results")
    with st.expander("Persist current climate-analogue evidence", expanded=False):
        if isinstance(analogue_results, pd.DataFrame) and not analogue_results.empty:
            analogue_name = st.text_input("Analogue evidence name", value=f"Climate analogues saved {date.today().isoformat()}", key="twin_cc_analogue_name")
            if st.button("Save current analogue result to this Twin", key="twin_cc_save_analogue"):
                aid = db.save_analogue_season(link["link_id"], name=analogue_name, source="AGROLATTICE Climate Comparison Studio", settings={"saved_from_session":True}, data=analogue_results)
                st.success(f"Analogue evidence saved: {aid[:12]}")
        else:
            st.info("No climate-analogue result is currently available in the session. Run Climate Comparison Studio first, then return here to persist the selected evidence with the Twin.")
        saved_analogues = db.analogue_seasons(link["link_id"])
        if not saved_analogues.empty:
            st.dataframe(saved_analogues[["name","source","created_at"]], hide_index=True, width="stretch")


def _ensure_flowering_protocol(field_db) -> str:
    protocols = field_db.observation_protocols(active_only=True)
    if not protocols.empty:
        match = protocols.loc[protocols["name"].astype(str).str.casefold().eq("maize flowering synchrony")]
        if not match.empty:
            return str(match.iloc[0]["protocol_id"])
    return field_db.save_observation_protocol(
        "Maize Flowering Synchrony",
        [
            {"name":"male_shedding_pct","label":"Male shedding","unit":"%","type":"number"},
            {"name":"female_silking_pct","label":"Female silking","unit":"%","type":"number"},
            {"name":"female_receptive_pct","label":"Female receptive silks","unit":"%","type":"number"},
            {"name":"pollen_intensity","label":"Pollen intensity","unit":"0-5","type":"number"},
            {"name":"collared_leaf_number","label":"Collared leaf number","unit":"leaves","type":"number"},
        ],
        category="Phenology",
        description="AGROLATTICE protocol for hybrid-maize flowering synchrony field checks. Timing observations do not directly measure pollen quantity or seed purity.",
    )


def _copilot(db, field_db, pollination_db, research_registry, context, link) -> None:
    bundle, weather, state, plot_states, manifest, *_ = _state_bundle(db, field_db, pollination_db, context, link)
    _context_header(link, bundle, state)
    recs = generate_recommendations(plot_states=plot_states, state=state)
    st.markdown("### Next best measurements")
    st.caption("Priorities are transparent rules using flowering-window proximity, missing measurements, staleness and Twin uncertainty. They are not claimed to be a formal Bayesian information-gain optimiser.")
    if recs.empty:
        st.success("No priority measurement recommendation is currently generated.")
    else:
        st.dataframe(recs, hide_index=True, width="stretch")
        if bundle.get("field"):
            n = st.slider("Create field tasks for top recommendations", 1, min(10, len(recs)), min(3, len(recs)), key="twin_cc_task_n")
            if st.button("Create linked flowering-observation tasks", type="primary", key="twin_cc_create_tasks", width="stretch"):
                protocol_id = _ensure_flowering_protocol(field_db)
                created = 0
                for _, row in recs.head(n).iterrows():
                    task_id = field_db.create_task(
                        bundle["field"]["field_id"],
                        str(row.get("Title") or "Twin measurement"),
                        category="Phenology",
                        due_date=date.today().isoformat(),
                        priority=str(row.get("Priority") or "High"),
                        status="Open",
                        description=f"Twin rationale: {row.get('Rationale')} Suggested measurements: {row.get('Suggested measurements')}",
                        recurrence="None",
                        source="Persistent Twin 11.9",
                    )
                    field_db.save_task_details(
                        task_id,
                        trial_id=link.get("trial_id"),
                        experimental_unit_id=row.get("Plot ID"),
                        protocol_id=protocol_id,
                    )
                    created += 1
                db.log_event(link["link_id"], event_type="Field work", title=f"Created {created} Twin measurement task(s)", source="Field Operations", details={"protocol_id":protocol_id})
                st.success(f"Created {created} linked field task(s) using the Maize Flowering Synchrony observation protocol.")

        if research_registry is not None:
            choice = st.selectbox("Recommendation to send to the research decision ledger", list(range(len(recs))), format_func=lambda i: f"{recs.iloc[i].get('Priority')} · {recs.iloc[i].get('Title')}", key="twin_cc_ledger_rec")
            if st.button("Save selected recommendation to Recommendation → Action → Outcome ledger", key="twin_cc_to_ledger", width="stretch"):
                row = recs.iloc[int(choice)]
                rid = research_registry.save_recommendation({
                    "field_id": (bundle.get("field") or {}).get("field_id"),
                    "trial_id": link.get("trial_id"),
                    "experimental_unit_id": row.get("Plot ID"),
                    "action_type": str(row.get("Recommendation type") or "Twin measurement"),
                    "action_text": str(row.get("Title") or "Twin recommendation"),
                    "objective": "Reduce Twin uncertainty / verify field state",
                    "constraints": {"suggested_measurements": row.get("Suggested measurements")},
                    "status": "Proposed",
                    "provenance": {"source":"AGROLATTICE Persistent Twin 11.9", "twin_link_id":link["link_id"], "rationale":row.get("Rationale"), "score":row.get("Score")},
                })
                db.log_event(link["link_id"], event_type="Recommendation", title=f"Recommendation sent to decision ledger: {row.get('Title')}", details={"research_recommendation_id":rid})
                st.success(f"Research recommendation saved: {rid[:12]}")

    st.markdown("### Next-season experimental design")
    design, rationale = next_season_design(plot_states)
    st.caption(rationale)
    if not design.empty:
        st.dataframe(design, hide_index=True, width="stretch")


def _validation_status(male_source: str, female_source: str, research_registry, bundle) -> tuple[str, str]:
    sources = f"{male_source} {female_source}".casefold()
    if "calibrat" not in sources and "measured" not in sources:
        return "Prior only", "Parent physiology is still driven primarily by publication priors."
    if research_registry is not None and bundle.get("field"):
        try:
            preds = research_registry.predictions(field_id=bundle["field"]["field_id"], limit=50)
            if not preds.empty and "model_status" in preds and preds["model_status"].astype(str).str.casefold().isin({"externally validated","operationally eligible"}).any():
                return "Externally validated evidence present", "At least one registered field-linked model has external/operational validation status; verify it targets the same outcome before applying it to this Twin."
        except Exception:
            pass
    return "Locally calibrated", "Local physiology observations inform the Twin, but cross-season/cross-site validation is not automatically established."


def _evidence(db, field_db, pollination_db, research_registry, context, link) -> None:
    bundle, weather, state, plot_states, manifest, male_params, female_params, male_record, female_record = _state_bundle(db, field_db, pollination_db, context, link)
    _context_header(link, bundle, state)
    status, explanation = _validation_status(str(state.get("Male physiology source")), str(state.get("Female physiology source")), research_registry, bundle)
    cols = st.columns(4)
    cols[0].metric("Validation status", status)
    cols[1].metric("Data completeness", _metric(state.get("Data completeness score"), "{:.0f}/100"))
    cols[2].metric("Model disagreement", _metric(state.get("Model disagreement (days)"), "{:.1f} d"))
    cols[3].metric("Parameter uncertainty", str(state.get("Parameter uncertainty") or "NA"))
    st.info(explanation)

    st.markdown("### Evidence sources")
    evidence = pd.DataFrame([
        {"Component":"Weather","Evidence type":"Retrieved / attached","Rows":manifest.get("weather_rows"),"Freshness (d)":manifest.get("freshness_days",{}).get("weather_days"),"Source":manifest.get("weather_source")},
        {"Component":"Root-zone state","Evidence type":"Modelled","Rows":manifest.get("root_zone_rows"),"Freshness (d)":manifest.get("freshness_days",{}).get("root_zone_days"),"Source":manifest.get("root_zone_source")},
        {"Component":"Sentinel-2","Evidence type":"Retrieved + derived index","Rows":manifest.get("satellite_rows"),"Freshness (d)":manifest.get("freshness_days",{}).get("satellite_days"),"Source":manifest.get("satellite_source")},
        {"Component":"Flowering observations","Evidence type":"Measured / recorded","Rows":manifest.get("observation_rows"),"Freshness (d)":manifest.get("freshness_days",{}).get("observations_days"),"Source":"Maize Synchrony Lab"},
        {"Component":"Sensors","Evidence type":"Measured / imported","Rows":manifest.get("sensor_rows"),"Freshness (d)":manifest.get("freshness_days",{}).get("sensor_days"),"Source":"Field Operations"},
        {"Component":"Phenology model","Evidence type":"Mechanistic / fallback","Rows":None,"Freshness (d)":None,"Source":state.get("Target basis")},
    ])
    st.dataframe(evidence, hide_index=True, width="stretch")

    st.markdown("### Genotype physiology provenance")
    physiology = pd.DataFrame([
        {"Role":"Male","Parent":(bundle.get("trial") or {}).get("male_parent"),**male_params.to_record(),"Source":state.get("Male physiology source")},
        {"Role":"Female","Parent":(bundle.get("trial") or {}).get("female_parent"),**female_params.to_record(),"Source":state.get("Female physiology source")},
    ])
    st.dataframe(physiology, hide_index=True, width="stretch")
    calibrations = db.calibration_runs(link["link_id"])
    if not calibrations.empty:
        st.markdown("### Calibration audit")
        st.dataframe(calibrations[["parent_name","role","created_at"]], hide_index=True, width="stretch")

    if not bundle.get("harvest", pd.DataFrame()).empty:
        st.markdown("### Observed season outcomes")
        st.dataframe(bundle["harvest"], hide_index=True, width="stretch")

    if research_registry is not None:
        field_id = (bundle.get("field") or {}).get("field_id")
        trial_id = link.get("trial_id")
        try:
            predictions = research_registry.predictions(field_id=field_id, trial_id=trial_id, limit=100)
        except Exception:
            predictions = pd.DataFrame()
        if not predictions.empty:
            st.markdown("### Registered research predictions")
            display = [c for c in ["generated_at","model_name","model_status","target","prediction","prediction_text","lower_bound","upper_bound","uncertainty_method","applicability_status"] if c in predictions]
            st.dataframe(predictions[display], hide_index=True, width="stretch")
        try:
            recs = research_registry.recommendations(field_id=field_id, trial_id=trial_id)
        except Exception:
            recs = pd.DataFrame()
        if not recs.empty:
            st.markdown("### Recommendation → action evidence")
            st.dataframe(recs[[c for c in ["recommendation_id","action_type","action_text","status","created_at"] if c in recs]], hide_index=True, width="stretch")

    with st.expander("Advanced provenance manifest", expanded=False):
        st.json(manifest)
    st.download_button("Download complete Twin research package", db.export_package(link["link_id"]), file_name=f"agrolattice_twin_{link['link_id'][:8]}.zip", mime="application/zip", width="stretch")


def _calibration_frames(bundle, role: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    role_name = "Male" if role.casefold().startswith("m") else "Female"
    plots = bundle.get("plots", pd.DataFrame())
    phenology = bundle.get("phenology", pd.DataFrame())
    leaves = bundle.get("leaf_observations", pd.DataFrame())
    events_out = pd.DataFrame(columns=["Sowing date","Event date"])
    if isinstance(phenology, pd.DataFrame) and not phenology.empty and isinstance(plots, pd.DataFrame) and not plots.empty:
        merged = phenology.merge(plots[[c for c in ["Plot ID","Male sowing","Female sowing"] if c in plots]], on="Plot ID", how="left")
        event_col = "Male flowering date" if role_name == "Male" else "Female flowering date"
        sowing_col = "Male sowing" if role_name == "Male" else "Female sowing"
        if event_col in merged and sowing_col in merged:
            events_out = merged[[sowing_col,event_col]].rename(columns={sowing_col:"Sowing date",event_col:"Event date"}).dropna()
    leaf_out = pd.DataFrame(columns=["Sowing date","Observation date","Collared leaf number"])
    if isinstance(leaves, pd.DataFrame) and not leaves.empty:
        selected = leaves.loc[leaves["Parent role"].astype(str).str.casefold().eq(role_name.casefold())].copy() if "Parent role" in leaves else leaves.copy()
        sowing_col = "Male sowing" if role_name == "Male" else "Female sowing"
        if sowing_col in selected:
            leaf_out = selected[[sowing_col,"Observation date","Collared leaf number"]].rename(columns={sowing_col:"Sowing date"}).dropna(subset=["Sowing date","Observation date","Collared leaf number"])
    return events_out, leaf_out


def _setup(db, field_db, pollination_db, research_registry, context, link) -> None:
    bundle, weather, state, plot_states, manifest, male_params, female_params, male_record, female_record = _state_bundle(db, field_db, pollination_db, context, link)
    _context_header(link, bundle, state)
    section = st.selectbox("Setup section", ["Data sources", "Crop model & calibration", "Data readiness", "Export & advanced"], key="twin_cc_setup_section")
    if section == "Data sources":
        st.caption("Remote retrieval is never run simply because you opened the Twin. Each expensive request remains an explicit researcher action and the retrieved data are stored persistently with provenance.")
        with st.expander("Daily weather · NASA POWER / attached data", expanded=manifest.get("weather_rows",0)==0):
            _render_twin_weather_manager(db=db, link=link, bundle=bundle, context=context, key_prefix="twin_cc_setup", compact=False)
        bundle = _resolve_bundle(link, field_db, pollination_db, context, db)
        with st.expander("Root-zone water balance", expanded=manifest.get("root_zone_rows",0)==0):
            _render_twin_root_zone_manager(db=db, link=link, bundle=bundle, context=context, key_prefix="twin_cc_setup", compact=False)
        bundle = _resolve_bundle(link, field_db, pollination_db, context, db)
        with st.expander("Sentinel-2 field observations", expanded=manifest.get("satellite_rows",0)==0):
            _render_twin_satellite_manager(db=db, link=link, bundle=bundle, context=context, key_prefix="twin_cc_setup", compact=False)
    elif section == "Crop model & calibration":
        if not bundle.get("trial"):
            st.info("Link a maize synchrony trial to calibrate parent-specific mechanistic physiology.")
        else:
            st.markdown("### Current parent physiology")
            current = pd.DataFrame([
                {"Role":"Male","Parent":bundle["trial"].get("male_parent"),**male_params.to_record(),"Source":state.get("Male physiology source")},
                {"Role":"Female","Parent":bundle["trial"].get("female_parent"),**female_params.to_record(),"Source":state.get("Female physiology source")},
            ])
            st.dataframe(current, hide_index=True, width="stretch")
            st.caption("The Laurent et al. priors are biological prior distributions, not measurements of your local parent lines.")
            role = st.radio("Parent to calibrate", ["Male","Female"], horizontal=True, key="twin_cc_cal_role")
            prior = male_params if role == "Male" else female_params
            parent_name = str((bundle["trial"].get("male_parent") if role == "Male" else bundle["trial"].get("female_parent")) or "").strip()
            events, leaves = _calibration_frames(bundle, role)
            c = st.columns(3)
            c[0].metric("Flowering-event records", len(events))
            c[1].metric("Leaf-number records", len(leaves))
            c[2].metric("Prior source", state.get("Male physiology source") if role == "Male" else state.get("Female physiology source"))
            if st.button("Fit prior-regularised local physiology", type="primary", key="twin_cc_calibrate", width="stretch"):
                try:
                    result = calibrate_parent_physiology(weather, role=role, event_observations=events, leaf_observations=leaves, prior=prior)
                    st.session_state.twin_cc_calibration_result = {"role":role,"parent":parent_name,"result":result}
                except Exception as error:
                    st.error(f"Calibration could not run: {error}")
            saved = st.session_state.get("twin_cc_calibration_result")
            if isinstance(saved, dict) and saved.get("role") == role and saved.get("parent") == parent_name:
                result = saved["result"]
                fitted = result["parameters"]
                st.dataframe(pd.DataFrame([
                    {"Parameter":"tln","Prior":prior.tln,"Fitted":fitted.tln,"SD":fitted.tln_sd},
                    {"Parameter":"coblf","Prior":prior.coblf,"Fitted":fitted.coblf,"SD":fitted.coblf_sd},
                    {"Parameter":"ebR1 (g)","Prior":prior.eb_r1_g,"Fitted":fitted.eb_r1_g,"SD":fitted.eb_r1_sd},
                ]), hide_index=True, width="stretch")
                for warning in result.get("warnings",[]):
                    st.warning(warning)
                if st.button("Save fitted physiology to Maize Synchrony parent registry", key="twin_cc_save_calibration", width="stretch"):
                    pollination_db.upsert_parent_physiology(parent_name, role, fitted, method="Twin local calibration · prior-regularised nonlinear least squares", source=f"Persistent Twin {link.get('name')}", sample_size=int(result.get("event_records",0)+result.get("leaf_records",0)), notes="; ".join(result.get("warnings",[])))
                    db.save_calibration_run(link["link_id"], parent_name=parent_name, role=role, prior=prior.to_record(), fitted=fitted.to_record(), diagnostics={k:v for k,v in result.items() if k not in {"parameters"}})
                    st.success("Calibrated physiology saved with provenance. Reloading Twin state now uses the local parameters.")
                    st.session_state.pop("twin_cc_calibration_result", None)
                    st.rerun()
    elif section == "Data readiness":
        st.dataframe(_state_chain(bundle, state, manifest), hide_index=True, width="stretch")
        actions = []
        if not manifest.get("weather_rows"): actions.append("Attach/retrieve daily weather")
        if not manifest.get("root_zone_rows"): actions.append("Run persistent root-zone water balance")
        if not manifest.get("satellite_rows"): actions.append("Retrieve/process Sentinel-2")
        if bundle.get("trial") and not manifest.get("observation_rows"): actions.append("Collect flowering observations")
        if actions:
            st.warning("Recommended setup actions: " + "; ".join(actions))
        else:
            st.success("The core linked data streams required for the current Twin state are present.")
    else:
        st.download_button("Download complete Twin package", db.export_package(link["link_id"]), file_name=f"agrolattice_twin_{link['link_id'][:8]}.zip", mime="application/zip", width="stretch")
        counts = db.storage_counts(link["link_id"])
        st.dataframe(pd.DataFrame([{"Stored component":k,"Records":v} for k,v in counts.items()]), hide_index=True, width="stretch")
        with st.expander("Advanced destructive actions", expanded=False):
            st.warning("These controls delete only explicitly selected Twin-owned records. Field, trial and other protected research databases are not deleted here.")
            cats = st.multiselect("Twin-owned records to clear", ["snapshots","scenarios","recommendations","models","events","calibrations","analogues","weather","root_zone","satellite"], key="twin_cc_clear_categories")
            confirm = st.checkbox("I understand the selected Twin records will be permanently deleted", key="twin_cc_clear_confirm")
            if st.button("Clear selected Twin records", disabled=not(confirm and cats), key="twin_cc_clear_button"):
                removed = db.clear_link_records(link["link_id"], cats)
                st.success(f"Removed {sum(removed.values())} Twin-owned record(s).")
                st.rerun()


def _create_twin_panel(db, field_db, pollination_db) -> None:
    st.markdown("### Create a Persistent Twin")
    fields = field_db.fields()
    trials = pollination_db.list_trials()
    field_options = [""] + fields.get("field_id", pd.Series(dtype=str)).astype(str).tolist()
    field_labels = {str(r.get("field_id")): f"{r.get('farm_name')} → {r.get('name')}" for _, r in fields.iterrows()}
    trial_options = [""] + trials.get("trial_id", pd.Series(dtype=str)).astype(str).tolist()
    trial_labels = {str(r.get("trial_id")): str(r.get("name")) for _, r in trials.iterrows()}
    with st.form("twin_cc_create_form"):
        name = st.text_input("Twin name")
        field_id = st.selectbox("Mapped field", field_options, format_func=lambda x: "None" if not x else field_labels.get(x,x))
        trial_id = st.selectbox("Maize trial", trial_options, format_func=lambda x: "None" if not x else trial_labels.get(x,x))
        notes = st.text_area("Notes")
        submit = st.form_submit_button("Create / link Twin", type="primary", width="stretch")
    if submit:
        if not field_id and trial_id:
            try:
                trial = pollination_db.get_trial(trial_id)
                field_id = str((trial or {}).get("source_field_id") or "")
            except Exception:
                pass
        if not name.strip():
            st.error("Twin name is required.")
        elif not field_id and not trial_id:
            st.error("Select at least one mapped field or trial.")
        else:
            link_id = db.save_link(name=name.strip(), field_id=field_id or None, trial_id=trial_id or None, notes=notes)
            db.log_event(link_id, event_type="Twin", title="Persistent Twin created / linked", details={"field_id":field_id or None,"trial_id":trial_id or None})
            st.session_state.agrolattice_active_twin_link_id = link_id
            st.success("Persistent Twin created and activated.")
            st.rerun()


def render_twin_command_centre(*, db: AgroLatticeTwinDatabase, field_db, pollination_db, research_registry=None, context: Mapping[str, Any]) -> None:
    st.markdown("## Persistent Twin Command Centre")
    st.caption("A long-lived spatial field/season representation that keeps measured observations, mechanistic states, EO/sensor evidence, predictions, scenarios and recommendations distinguishable and auditable.")
    link = _active_link(db)
    if link is None:
        st.info("No Persistent Twin exists yet. Create one from an authoritative mapped field and/or linked experiment.")
        _create_twin_panel(db, field_db, pollination_db)
        return
    view = _view_control()
    renderer = {
        "Overview": _overview,
        "Spatial Twin": _spatial,
        "Development & water": _development,
        "Timeline": _timeline,
        "Scenarios": _scenarios,
        "Measurements & copilot": _copilot,
        "Evidence & validation": _evidence,
        "Setup": _setup,
    }[view]
    renderer(db, field_db, pollination_db, research_registry, context, link)
