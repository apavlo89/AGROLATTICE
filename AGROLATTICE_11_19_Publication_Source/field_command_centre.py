from __future__ import annotations

import json
import math
from datetime import date, datetime, timedelta, timezone
from typing import Any, Mapping, Sequence
from uuid import uuid4

import folium
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from shapely.geometry import Point, mapping, shape
from shapely.ops import unary_union
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from streamlit_folium import st_folium

from field_operations_suite import (
    FieldOperationsDatabase,
    OBSERVATION_CATEGORIES,
    OPERATION_CATEGORIES,
    SENSOR_DEFAULT_UNITS,
    SENSOR_TYPES,
    TASK_CATEGORIES,
    TASK_PRIORITIES,
    TASK_STATUSES,
    _map_for_geometry,
    _render_field_map,
    geometry_area_hectares,
    geometry_feature,
    geometry_feature_collection,
    json_dumps,
    json_loads,
    render_data_exchange_page,
    render_farm_portfolio_page,
    slug,
    sensor_quality_report,
)
from local_boundary_editor import render_boundary_editor
from navigation_state import consume_view_request

MODULE_VERSION = "1.0.1"

BUILTIN_PROTOCOLS: dict[str, dict[str, Any]] = {
    "General crop scouting": {
        "category": "Crop condition",
        "description": "Rapid structured crop-condition observation.",
        "fields": [
            {"name": "stand_uniformity", "label": "Stand uniformity", "type": "score", "min": 1, "max": 5, "unit": "1-5"},
            {"name": "stress_fraction", "label": "Visible stress", "type": "number", "min": 0, "max": 100, "unit": "% plants"},
        ],
    },
    "Maize flowering": {
        "category": "Phenology",
        "description": "Field/trial flowering observation suitable for synchrony work.",
        "fields": [
            {"name": "anthesis_pct", "label": "Plants in anthesis", "type": "number", "min": 0, "max": 100, "unit": "%"},
            {"name": "silking_pct", "label": "Plants with visible silks", "type": "number", "min": 0, "max": 100, "unit": "%"},
            {"name": "leaf_number", "label": "Leaf number", "type": "number", "min": 0, "max": 40, "unit": "leaves"},
        ],
    },
    "Pest count": {
        "category": "Pest",
        "description": "Quantitative pest count with sampled plant count.",
        "fields": [
            {"name": "pest_count", "label": "Pests observed", "type": "number", "min": 0, "unit": "count"},
            {"name": "plants_examined", "label": "Plants examined", "type": "number", "min": 1, "unit": "plants"},
        ],
    },
    "Disease assessment": {
        "category": "Disease symptom",
        "description": "Disease incidence/severity observation; this records symptoms, not a laboratory diagnosis.",
        "fields": [
            {"name": "incidence_pct", "label": "Incidence", "type": "number", "min": 0, "max": 100, "unit": "% plants"},
            {"name": "severity_pct", "label": "Severity", "type": "number", "min": 0, "max": 100, "unit": "% affected tissue"},
        ],
    },
    "Plant / ear traits": {
        "category": "Crop condition",
        "description": "Quantitative plant and ear traits for field research.",
        "fields": [
            {"name": "plant_height_cm", "label": "Plant height", "type": "number", "min": 0, "unit": "cm"},
            {"name": "ear_height_cm", "label": "Ear height", "type": "number", "min": 0, "unit": "cm"},
            {"name": "ears_per_plant", "label": "Ears per plant", "type": "number", "min": 0, "unit": "ears/plant"},
        ],
    },
}

ALERT_TEMPLATES = {
    "Heat stress screen": ("weather", "Tmax", ">=", 35.0, "High", 1, 24, "Review crop-stage sensitivity; this is a weather threshold, not proof of injury."),
    "Root-zone depletion": ("root_zone", "Relative depletion", ">=", 0.80, "Urgent", 2, 24, "Modelled depletion threshold; verify soil profile and field conditions."),
    "Low soil moisture": ("sensor", "Soil moisture", "<=", 18.0, "High", 2, 12, "Replace with a field- and sensor-specific threshold before operational use."),
    "Rapid NDVI decline": ("satellite", "NDVI change (%)", "<=", -12.0, "High", 2, 72, "EO change signal; inspect clouds, phenology and field observations before interpretation."),
}

SOURCE_METRICS = {
    "weather": ["Tmax", "Tmin", "Temperature", "Relative humidity", "Precipitation"],
    "satellite": ["NDVI", "NDMI", "NDVI change (%)"],
    "root_zone": ["Ks", "Relative depletion"],
    "sensor": ["Soil moisture", "Soil temperature", "Air temperature", "Relative humidity", "Leaf wetness", "Canopy temperature"],
}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_time(value: Any) -> pd.Timestamp | None:
    ts = pd.to_datetime(value, errors="coerce", utc=True)
    return None if pd.isna(ts) else ts


def _age_label(value: Any) -> str:
    ts = _parse_time(value)
    if ts is None:
        return "not available"
    days = max(0, int((_now_utc() - ts.to_pydatetime()).total_seconds() // 86400))
    if days == 0:
        hours = max(0, int((_now_utc() - ts.to_pydatetime()).total_seconds() // 3600))
        return "today" if hours == 0 else f"{hours} h ago"
    return f"{days} d ago"


def _active_field(db: FieldOperationsDatabase) -> tuple[str | None, dict | None]:
    fields = db.fields()
    if fields.empty:
        return None, None
    labels = {f"{r['farm_name']} → {r['name']} · {float(r.get('area_ha') or 0):.2f} ha": str(r["field_id"]) for _, r in fields.iterrows()}
    active = str(st.session_state.get("field_ops_active_field_id") or "")
    default = next((label for label, field_id in labels.items() if field_id == active), list(labels)[0])
    top = st.columns([5, 1])
    selected = top[0].selectbox("Active field", list(labels), index=list(labels).index(default), key="field_command_active_field")
    field_id = labels[selected]
    st.session_state.field_ops_active_field_id = field_id
    field = db.field(field_id)
    if top[1].button("Refresh", width="stretch", key="field_command_refresh"):
        st.rerun()
    return field_id, field


def _trial_context(context: Mapping[str, Any], field_id: str) -> tuple[pd.DataFrame, str | None]:
    pollination_db = context.get("pollination_db")
    if pollination_db is None:
        return pd.DataFrame(), None
    try:
        trials = pollination_db.list_trials()
        if trials.empty or "Source field ID" not in trials:
            return pd.DataFrame(), None
        field_trials = trials.loc[trials["Source field ID"].astype(str).eq(str(field_id))].copy()
        active = field_trials.loc[field_trials.get("Status", pd.Series(dtype=str)).astype(str).eq("Active")] if not field_trials.empty else field_trials
        selected = active.iloc[0] if not active.empty else (field_trials.iloc[0] if not field_trials.empty else None)
        return field_trials, str(selected["Trial ID"]) if selected is not None else None
    except Exception:
        return pd.DataFrame(), None


def _research_freshness(context: Mapping[str, Any], field_id: str) -> dict[str, dict[str, Any]]:
    out = {
        "Weather": {"timestamp": None, "status": "Missing", "source": "—"},
        "Satellite": {"timestamp": None, "status": "Missing", "source": "—"},
        "Twin/root-zone": {"timestamp": None, "status": "Missing", "source": "—"},
    }
    registry = context.get("research_registry")
    if registry is not None:
        try:
            acq = registry.data_acquisitions(field_id=field_id, limit=100)
            if not acq.empty:
                text = (acq.get("source", "").astype(str) + " " + acq.get("source_type", "").astype(str)).str.lower()
                for label, keys in [("Weather", ("nasa", "power", "weather")), ("Satellite", ("sentinel", "satellite", "earth observation", "eo"))]:
                    mask = pd.Series(False, index=acq.index)
                    for key in keys:
                        mask |= text.str.contains(key, na=False)
                    rows = acq.loc[mask]
                    if not rows.empty:
                        row = rows.iloc[0]
                        ts = row.get("period_end") or row.get("created_at")
                        out[label] = {"timestamp": ts, "status": str(row.get("status") or "Available"), "source": str(row.get("source") or row.get("source_type") or "Evidence registry")}
        except Exception:
            pass
    twin_db = context.get("twin_db")
    if twin_db is not None:
        try:
            links = twin_db.links()
            matches = links.loc[links.get("field_id", pd.Series(dtype=str)).astype(str).eq(str(field_id))]
            if not matches.empty:
                link = matches.iloc[0]
                snapshots = twin_db.snapshots(str(link["link_id"]))
                if not snapshots.empty:
                    row = snapshots.iloc[-1]
                    out["Twin/root-zone"] = {"timestamp": row.get("as_of") or row.get("created_at"), "status": "Saved", "source": str(link.get("name") or "Persistent Twin")}
                root = twin_db.root_zone_record(str(link["link_id"]))
                if root:
                    out["Twin/root-zone"] = {"timestamp": root.get("updated_at") or root.get("created_at"), "status": "Saved", "source": str(link.get("name") or "Persistent Twin")}
        except Exception:
            pass
    return out


def _field_pulse(db: FieldOperationsDatabase, context: Mapping[str, Any], field_id: str, field: Mapping[str, Any]) -> dict[str, Any]:
    tasks = db.tasks(field_id)
    alerts = db.alerts(field_id)
    observations = db.observations(field_id)
    operations = db.operations(field_id)
    sensors = db.sensors(field_id)
    readings = db.readings(field_id=field_id)
    freshness = _research_freshness(context, field_id)
    trials, active_trial_id = _trial_context(context, field_id)
    today = date.today()
    open_tasks = tasks.loc[~tasks["status"].isin(["Completed", "Cancelled"])] if not tasks.empty else tasks
    overdue = 0
    if not open_tasks.empty:
        due = pd.to_datetime(open_tasks["due_date"], errors="coerce")
        overdue = int((due.dt.date < today).fillna(False).sum())
    open_alerts = alerts.loc[alerts["status"].astype(str).ne("Resolved")] if not alerts.empty else alerts
    latest_op = operations.iloc[0].to_dict() if not operations.empty else None
    latest_obs = observations.iloc[0].to_dict() if not observations.empty else None
    latest_reading = readings.iloc[-1].to_dict() if not readings.empty else None
    sensor_stale = 0
    if not sensors.empty:
        latest_by = readings.groupby("sensor_id")["timestamp"].max() if not readings.empty else pd.Series(dtype="datetime64[ns, UTC]")
        for sid in sensors.loc[sensors["status"].astype(str).eq("Active"), "sensor_id"].astype(str):
            ts = latest_by.get(sid)
            if ts is None or pd.isna(ts) or (_now_utc() - pd.Timestamp(ts).to_pydatetime()).days > 7:
                sensor_stale += 1
    return {
        "tasks": tasks,
        "open_tasks": len(open_tasks),
        "overdue": overdue,
        "alerts": alerts,
        "open_alerts": len(open_alerts),
        "observations": observations,
        "operations": operations,
        "sensors": sensors,
        "active_sensors": int(sensors["status"].astype(str).eq("Active").sum()) if not sensors.empty else 0,
        "sensor_stale": sensor_stale,
        "latest_reading": latest_reading,
        "latest_operation": latest_op,
        "latest_observation": latest_obs,
        "freshness": freshness,
        "trials": trials,
        "active_trial_id": active_trial_id,
    }


def _render_context_strip(field: Mapping[str, Any], pulse: Mapping[str, Any]) -> None:
    crop = str(field.get("crop") or "Crop not set")
    genotype = str(field.get("variety") or "—")
    season = str(field.get("season_year") or "—")
    trial_label = "No linked trial"
    trials = pulse.get("trials")
    if isinstance(trials, pd.DataFrame) and not trials.empty:
        active = trials.loc[trials.get("Status", pd.Series(dtype=str)).astype(str).eq("Active")]
        row = active.iloc[0] if not active.empty else trials.iloc[0]
        trial_label = f"{row.get('Name') or row.get('Trial name') or row.get('Trial ID')} · {row.get('Status') or '—'}"
    st.caption(f"**{field.get('farm_name')} → {field.get('name')}** · {crop} · genotype/variety {genotype} · season {season} · {trial_label}")


def _render_overview(db: FieldOperationsDatabase, context: Mapping[str, Any], field_id: str, field: Mapping[str, Any], pulse: Mapping[str, Any]) -> None:
    st.markdown("### Field Pulse")
    cards = st.columns(6)
    cards[0].metric("Area", f"{float(field.get('area_ha') or 0):,.2f} ha")
    cards[1].metric("Open work", pulse["open_tasks"], delta=f"{pulse['overdue']} overdue" if pulse["overdue"] else None, delta_color="inverse")
    cards[2].metric("Open alerts", pulse["open_alerts"])
    cards[3].metric("Sensors", pulse["active_sensors"], delta=f"{pulse['sensor_stale']} stale" if pulse["sensor_stale"] else None, delta_color="inverse")
    cards[4].metric("Weather", _age_label(pulse["freshness"]["Weather"]["timestamp"]))
    cards[5].metric("EO", _age_label(pulse["freshness"]["Satellite"]["timestamp"]))

    left, right = st.columns([1.35, 1])
    with left:
        st.markdown("#### What needs attention")
        actions: list[tuple[str, str]] = []
        if pulse["overdue"]:
            actions.append(("🔴", f"{pulse['overdue']} overdue field task(s) need rescheduling, completion or cancellation."))
        if pulse["open_alerts"]:
            actions.append(("🟠", f"{pulse['open_alerts']} unresolved alert(s) need acknowledgement and field verification."))
        if pulse["sensor_stale"]:
            actions.append(("🟡", f"{pulse['sensor_stale']} active sensor(s) have no reading in the last 7 days."))
        weather_ts = _parse_time(pulse["freshness"]["Weather"]["timestamp"])
        if weather_ts is None:
            actions.append(("🟡", "No persisted field-linked weather acquisition is recorded. Retrieve/reuse weather in the Research Data Hub."))
        elif (_now_utc() - weather_ts.to_pydatetime()).days > 7 and int(field.get("season_year") or date.today().year) >= date.today().year:
            actions.append(("🟡", f"Field-linked weather evidence is {_age_label(weather_ts)}; update if this is an active season."))
        eo_ts = _parse_time(pulse["freshness"]["Satellite"]["timestamp"])
        if eo_ts is None:
            actions.append(("⚪", "No persisted Sentinel/EO acquisition is linked to this field yet."))
        if pulse.get("active_trial_id") and pulse["latest_observation"] is None:
            actions.append(("🧪", "An experiment is linked but no field scouting/phenology observation is recorded here yet."))
        if not actions:
            st.success("No immediate operational issue is visible in the saved field record.")
        else:
            for icon, message in actions[:6]:
                st.markdown(f"{icon} {message}")

        st.markdown("#### Recent activity")
        timeline = db.field_timeline(field_id).head(8)
        if timeline.empty:
            st.info("No field activity has been recorded yet.")
        else:
            for row in timeline.to_dict("records"):
                ts = pd.to_datetime(row.get("timestamp"), errors="coerce")
                when = ts.strftime("%d %b %Y") if pd.notna(ts) else "—"
                st.markdown(f"**{when} · {row.get('type')} · {row.get('title')}**")
                if row.get("detail"):
                    st.caption(str(row.get("detail"))[:220])
    with right:
        st.markdown("#### Data freshness & completeness")
        fresh_rows = []
        for name, item in pulse["freshness"].items():
            fresh_rows.append({"Evidence": name, "Latest": _age_label(item.get("timestamp")), "Status": item.get("status"), "Source": item.get("source")})
        latest_sensor = pulse.get("latest_reading") or {}
        fresh_rows.append({"Evidence": "Sensors", "Latest": _age_label(latest_sensor.get("timestamp")), "Status": "Available" if latest_sensor else "Missing", "Source": latest_sensor.get("sensor_name") or "—"})
        latest_obs = pulse.get("latest_observation") or {}
        fresh_rows.append({"Evidence": "Scouting", "Latest": _age_label(latest_obs.get("observed_at")), "Status": "Available" if latest_obs else "Missing", "Source": latest_obs.get("category") or "—"})
        st.dataframe(pd.DataFrame(fresh_rows), hide_index=True, width="stretch")

        st.markdown("#### Latest management")
        op = pulse.get("latest_operation")
        if op:
            st.markdown(f"**{op.get('operation_date')} · {op.get('category')}**")
            st.caption(" · ".join([x for x in [str(op.get("product") or ""), f"{op.get('water_mm')} mm" if op.get("water_mm") else "", str(op.get("notes") or "")[:120]] if x]))
        else:
            st.info("No operation has been recorded for this field.")

    st.markdown("#### Portfolio Attention")
    attention = db.portfolio_attention()
    if not attention.empty:
        attention["attention_score"] = attention["open_alerts"] * 3 + attention["severe_observations"] * 2 + attention["overdue_tasks"] * 2 + attention["open_tasks"]
        display = attention.sort_values(["attention_score", "overdue_tasks"], ascending=False).rename(columns={
            "farm_name": "Organisation", "field_name": "Field", "area_ha": "Area (ha)", "crop": "Crop", "open_tasks": "Open tasks",
            "overdue_tasks": "Overdue", "open_alerts": "Open alerts", "severe_observations": "Severe observations", "active_sensors": "Sensors",
            "latest_reading": "Latest sensor reading", "attention_score": "Attention score",
        })
        cols = [c for c in ["Organisation","Field","Crop","Area (ha)","Open tasks","Overdue","Open alerts","Severe observations","Sensors","Latest sensor reading","Attention score"] if c in display]
        st.dataframe(display[cols], hide_index=True, width="stretch")
        st.caption("Attention score is a transparent triage count, not a crop-loss probability or agronomic risk probability.")


def _geometry_qa(db: FieldOperationsDatabase, field: Mapping[str, Any]) -> pd.DataFrame:
    geom = shape(field["geometry"])
    rows = [
        {"Check": "Geometry valid", "Result": "Pass" if geom.is_valid else "Review", "Detail": geom.geom_type},
        {"Check": "Area", "Result": "Information", "Detail": f"{float(field.get('area_ha') or 0):,.3f} ha"},
    ]
    farm = db.farm(str(field["farm_id"]))
    if farm and farm.get("geometry"):
        parent = shape(farm["geometry"])
        rows.append({"Check": "Inside organisation boundary", "Result": "Pass" if parent.buffer(1e-10).covers(geom) else "Review", "Detail": str(farm.get("name"))})
    siblings = db.fields(str(field["farm_id"]))
    overlaps = []
    for row in siblings.to_dict("records"):
        if str(row["field_id"]) == str(field["field_id"]):
            continue
        other = shape(json_loads(row.get("geometry_json")))
        inter = geom.intersection(other)
        if not inter.is_empty and inter.area > 1e-12:
            overlaps.append(str(row.get("name")))
    rows.append({"Check": "Sibling-field overlap", "Result": "Pass" if not overlaps else "Review", "Detail": "None" if not overlaps else ", ".join(overlaps)})
    return pd.DataFrame(rows)


def _render_map(db: FieldOperationsDatabase, context: Mapping[str, Any], field_id: str, field: Mapping[str, Any]) -> None:
    st.markdown("### Authoritative spatial workspace")
    opts = st.columns(5)
    show_obs = opts[0].checkbox("Scouting", True, key="field_map_obs")
    show_sensors = opts[1].checkbox("Sensors", True, key="field_map_sensors")
    show_samples = opts[2].checkbox("Nutrient samples", True, key="field_map_samples")
    show_sampling = opts[3].checkbox("Sampling designs", True, key="field_map_sampling")
    show_prescriptions = opts[4].checkbox("Prescriptions", True, key="field_map_rx")
    observations = db.observations(field_id) if show_obs else pd.DataFrame()
    sensors = db.sensors(field_id) if show_sensors else pd.DataFrame()
    nutrient = db.detailed_nutrient_samples(field_id) if show_samples else pd.DataFrame()
    sampling = db.sampling_points(field_id) if show_sampling else pd.DataFrame()
    prescriptions = db.prescriptions(field_id) if show_prescriptions else pd.DataFrame()

    m = _map_for_geometry(field["geometry"], zoom=17, satellite_default=True)
    folium.GeoJson(field["geometry"], name="Authoritative field boundary", style_function=lambda _: {"color":"#14532d","weight":5,"fillColor":"#22c55e","fillOpacity":0.06}, tooltip=f"Field · {field['name']}").add_to(m)
    # experiment overlays
    pollination_db = context.get("pollination_db")
    if pollination_db is not None:
        try:
            trials, _ = _trial_context(context, field_id)
            for _, tr in trials.iterrows():
                trial = pollination_db.get_trial(str(tr["Trial ID"]))
                tg = trial.get("field_geometry")
                if tg:
                    folium.GeoJson(tg, name=f"Trial · {trial.get('name')}", style_function=lambda _:{"color":"#c2410c","weight":3,"dashArray":"8 5","fillOpacity":0.03}, tooltip=f"{trial.get('name')} · {trial.get('status')}").add_to(m)
                units = pollination_db.list_plots(str(tr["Trial ID"]))
                for _, unit in units.iterrows() if not units.empty else []:
                    ug = unit.get("Geometry")
                    if isinstance(ug, Mapping):
                        folium.GeoJson(ug, name="Experimental units", style_function=lambda _:{"color":"#7c3aed","weight":1,"fillColor":"#a78bfa","fillOpacity":0.18}, tooltip=str(unit.get("Treatment unit") or unit.get("Plot") or "Experimental unit")).add_to(m)
        except Exception:
            pass
    if not observations.empty:
        for row in observations.dropna(subset=["latitude","longitude"]).to_dict("records"):
            folium.CircleMarker([float(row["latitude"]),float(row["longitude"])], radius=5, color="#dc2626", fill=True, tooltip=f"Scouting · {row.get('category')}", popup=str(row.get("notes") or "")).add_to(m)
    if not sensors.empty:
        for row in sensors.dropna(subset=["latitude","longitude"]).to_dict("records"):
            folium.Marker([float(row["latitude"]),float(row["longitude"])], tooltip=f"Sensor · {row.get('name')}", popup=f"{row.get('sensor_type')} · {row.get('depth_cm') or '—'} cm").add_to(m)
    if not nutrient.empty:
        for row in nutrient.dropna(subset=["latitude","longitude"]).to_dict("records"):
            folium.CircleMarker([float(row["latitude"]),float(row["longitude"])], radius=5, color="#92400e", fill=True, tooltip=f"Sample · {row.get('sample_type')}", popup=f"{row.get('sample_date')} · {row.get('external_sample_id') or row.get('sample_id')}").add_to(m)
    if not sampling.empty:
        for row in sampling.to_dict("records"):
            folium.CircleMarker([float(row["latitude"]),float(row["longitude"])], radius=3, color="#0f766e", fill=True, tooltip=f"Sampling point · {row.get('sampling_point_id')}").add_to(m)
    if not prescriptions.empty:
        for row in prescriptions.to_dict("records"):
            g=json_loads(row.get("geometry_json"))
            if g:
                folium.GeoJson(g, name="Prescription", style_function=lambda _:{"color":"#a16207","weight":2,"fillColor":"#facc15","fillOpacity":0.18}, tooltip=f"{row.get('name')} · {row.get('zone_label')} · {row.get('rate')} {row.get('rate_unit')}").add_to(m)
    try:
        minx,miny,maxx,maxy=shape(field["geometry"]).bounds
        m.fit_bounds([[miny,minx],[maxy,maxx]],padding=(30,30))
    except Exception: pass
    st_folium(m, use_container_width=True, height=650, key="field_command_map")

    qa_left, qa_right = st.columns([1,1])
    with qa_left:
        st.markdown("#### Geometry QA")
        st.dataframe(_geometry_qa(db, field), hide_index=True, width="stretch")
    with qa_right:
        st.markdown("#### Boundary export")
        feature = geometry_feature(field["geometry"], {"field_id":field_id,"name":field["name"],"area_ha":field.get("area_ha")})
        st.download_button("Download authoritative field GeoJSON", json_dumps(feature).encode(), file_name=f"{slug(field['name'])}_boundary.geojson", mime="application/geo+json", width="stretch")
        st.caption("Boundary editing and destructive administration are kept under Administration so normal map use cannot accidentally alter geometry.")


def _trial_unit_options(context: Mapping[str, Any], field_id: str) -> tuple[dict[str, str | None], dict[str, str | None]]:
    trial_options={"Field only":None}; unit_options={"No experimental unit":None}
    pollination_db=context.get("pollination_db")
    if pollination_db is None: return trial_options,unit_options
    try:
        trials,_=_trial_context(context,field_id)
        for _,tr in trials.iterrows():
            trial_id=str(tr["Trial ID"]); label=f"{tr.get('Name') or trial_id} · {tr.get('Status') or '—'}"; trial_options[label]=trial_id
        if len(trial_options)>1:
            first=next(v for v in trial_options.values() if v)
            units=pollination_db.list_plots(first)
            for _,u in units.iterrows() if not units.empty else []:
                uid=str(u.get("Treatment unit") or u.get("Plot") or u.name)
                unit_options[f"{u.get('Experiment plot') or u.get('Block') or 'Plot'} → {uid}"]=uid
    except Exception: pass
    return trial_options,unit_options


def _render_work(db: FieldOperationsDatabase, context: Mapping[str, Any], field_id: str, field: Mapping[str, Any]) -> None:
    work_mode = st.radio("Work view", ["Tasks", "Scouting & measurements", "Observation protocols"], horizontal=True, key="field_work_mode")
    if work_mode == "Tasks":
        tasks=db.tasks(field_id); open_tasks=tasks.loc[~tasks["status"].isin(["Completed","Cancelled"])] if not tasks.empty else tasks
        cards=st.columns(4); cards[0].metric("Open",len(open_tasks)); cards[1].metric("Completed",int(tasks["status"].eq("Completed").sum()) if not tasks.empty else 0)
        if not open_tasks.empty:
            due=pd.to_datetime(open_tasks["due_date"],errors="coerce"); cards[2].metric("Overdue",int((due.dt.date<date.today()).fillna(False).sum()))
        else: cards[2].metric("Overdue",0)
        cards[3].metric("Recurring",int(tasks["recurrence"].astype(str).ne("None").sum()) if not tasks.empty else 0)
        users=db.users(); assignees=[""]+users.loc[users["active"].eq(1),"name"].astype(str).tolist() if not users.empty else [""]
        trial_options,unit_options=_trial_unit_options(context,field_id)
        with st.expander("Create task", expanded=tasks.empty):
            with st.form("field_command_task_create"):
                c=st.columns(4); title=c[0].text_input("Task title"); category=c[1].selectbox("Category",TASK_CATEGORIES); assigned=c[2].selectbox("Assigned to",assignees); due=c[3].date_input("Due",date.today()+timedelta(days=1))
                c2=st.columns(4); priority=c2[0].selectbox("Priority",TASK_PRIORITIES,index=1); recurrence=c2[1].selectbox("Repeat",["None","Daily","Weekly","Fortnightly","Monthly"]); trlab=c2[2].selectbox("Trial link",list(trial_options)); unitlab=c2[3].selectbox("Experimental unit",list(unit_options))
                desc=st.text_area("Instructions / acceptance criteria"); save=st.form_submit_button("Create task",type="primary",width="stretch")
            if save:
                if not title.strip(): st.error("Task title is required.")
                else:
                    tid=db.create_task(field_id,title,category=category,assigned_to=assigned,due_date=str(due),priority=priority,status="Planned",recurrence=recurrence,description=desc)
                    db.save_task_details(tid,trial_id=trial_options[trlab],experimental_unit_id=unit_options[unitlab]); st.success("Task created."); st.rerun()
        if not tasks.empty:
            st.dataframe(tasks,hide_index=True,width="stretch")
            labels={f"{r['title']} · {r['status']} · due {r['due_date']}":str(r["task_id"]) for _,r in tasks.iterrows()}
            selected=st.selectbox("Edit / complete task",list(labels),key="field_task_edit_select"); tid=labels[selected]
            current=tasks.loc[tasks["task_id"].astype(str).eq(tid)].iloc[0]
            with st.form("field_task_edit_form"):
                c=st.columns(4); etitle=c[0].text_input("Title",value=str(current["title"])); ecat=c[1].selectbox("Category",TASK_CATEGORIES,index=TASK_CATEGORIES.index(current["category"]) if current["category"] in TASK_CATEGORIES else 0); eass=c[2].text_input("Assigned to",value=str(current.get("assigned_to") or "")); edue=c[3].date_input("Due date",value=pd.to_datetime(current.get("due_date"),errors="coerce").date() if pd.notna(pd.to_datetime(current.get("due_date"),errors="coerce")) else date.today())
                c2=st.columns(3); eprio=c2[0].selectbox("Priority",TASK_PRIORITIES,index=TASK_PRIORITIES.index(current["priority"]) if current["priority"] in TASK_PRIORITIES else 1); estat=c2[1].selectbox("Status",TASK_STATUSES,index=TASK_STATUSES.index(current["status"]) if current["status"] in TASK_STATUSES else 0); erec=c2[2].selectbox("Repeat",["None","Daily","Weekly","Fortnightly","Monthly"],index=["None","Daily","Weekly","Fortnightly","Monthly"].index(current["recurrence"]) if current["recurrence"] in ["None","Daily","Weekly","Fortnightly","Monthly"] else 0)
                edesc=st.text_area("Instructions",value=str(current.get("description") or "")); completion=st.text_area("Completion note / correction rationale"); who=st.text_input("Updated by")
                save_edit=st.form_submit_button("Save task changes",type="primary",width="stretch")
            if save_edit:
                old_status=str(current["status"]); db.update_task(tid,title=etitle,category=ecat,assigned_to=eass,due_date=str(edue),priority=eprio,status=estat,description=edesc,recurrence=erec,user_name=who)
                if estat != old_status: db.update_task_status(tid,estat,who,completion)
                elif completion: db.save_task_details(tid,completion_notes=completion)
                st.success("Task updated. Recurring tasks create the next occurrence only when completed."); st.rerun()
    elif work_mode == "Observation protocols":
        st.markdown("### Reusable observation protocols")
        st.caption("Protocols make repeated field measurements consistent. They define what to record; they do not determine biological meaning automatically.")
        protocols=db.observation_protocols(active_only=False)
        if not protocols.empty: st.dataframe(protocols.drop(columns=["fields_json","fields"],errors="ignore"),hide_index=True,width="stretch")
        with st.expander("Create protocol",expanded=protocols.empty):
            base=st.selectbox("Start from template",["Blank"]+list(BUILTIN_PROTOCOLS),key="protocol_template")
            template=BUILTIN_PROTOCOLS.get(base,{"category":"Custom","description":"","fields":[]})
            name=st.text_input("Protocol name",value="" if base=="Blank" else base,key="protocol_name")
            category=st.text_input("Category",value=str(template.get("category") or "Custom"),key="protocol_category")
            description=st.text_area("Purpose / instructions",value=str(template.get("description") or ""),key="protocol_desc")
            default_lines="\n".join(f"{f['label']}|{f.get('unit','')}" for f in template.get("fields",[]))
            fields_text=st.text_area("Measurements — one per line as Label|Unit",value=default_lines,key="protocol_fields")
            if st.button("Save protocol",type="primary",width="stretch",key="protocol_save"):
                fields=[]
                for line in fields_text.splitlines():
                    if not line.strip(): continue
                    parts=[x.strip() for x in line.split("|",1)]; label=parts[0]; unit=parts[1] if len(parts)>1 else ""
                    fields.append({"name":slug(label),"label":label,"type":"number","unit":unit})
                if not name.strip() or not fields: st.error("Provide a name and at least one measurement.")
                else: db.save_observation_protocol(name,fields,category=category,description=description); st.success("Protocol saved."); st.rerun()
    else:
        st.markdown("### Scouting & research measurements")
        protocols=db.observation_protocols(); protocol_choices={"Ad-hoc observation":None}
        if not protocols.empty:
            protocol_choices.update({str(r["name"]):str(r["protocol_id"]) for _,r in protocols.iterrows()})
        for name,data in BUILTIN_PROTOCOLS.items(): protocol_choices.setdefault(f"Template · {name}",f"builtin:{name}")
        selected_protocol=st.selectbox("Observation protocol",list(protocol_choices),key="field_obs_protocol")
        protocol_id=protocol_choices[selected_protocol]; protocol_fields=[]; default_category="Crop condition"
        if protocol_id and protocol_id.startswith("builtin:"):
            tmpl=BUILTIN_PROTOCOLS[protocol_id.split(":",1)[1]]; protocol_fields=tmpl["fields"]; default_category=tmpl["category"]
        elif protocol_id:
            row=protocols.loc[protocols["protocol_id"].astype(str).eq(protocol_id)].iloc[0]; protocol_fields=row["fields"]; default_category=str(row.get("category") or "Crop condition")
        trial_options,unit_options=_trial_unit_options(context,field_id)
        st.markdown("#### Location")
        location_mode=st.radio("Location source",["Field centroid","Click map","Enter coordinates"],horizontal=True,key="obs_location_mode")
        lat=float(field["centroid_lat"]); lon=float(field["centroid_lon"])
        if location_mode=="Click map":
            m=_map_for_geometry(field["geometry"],zoom=17,satellite_default=True); folium.GeoJson(field["geometry"],style_function=lambda _:{"weight":4,"fillOpacity":0.04}).add_to(m)
            state=st_folium(m,use_container_width=True,height=420,key="obs_location_map",returned_objects=["last_clicked"]); clicked=(state or {}).get("last_clicked")
            if clicked: lat=float(clicked["lat"]); lon=float(clicked["lng"]); st.success(f"Location selected: {lat:.6f}, {lon:.6f}")
            else: st.caption("Click inside the field to place this observation. Until clicked, the field centroid is used.")
        elif location_mode=="Enter coordinates":
            c=st.columns(2); lat=c[0].number_input("Latitude",value=lat,format="%.7f",key="obs_lat"); lon=c[1].number_input("Longitude",value=lon,format="%.7f",key="obs_lon")
        with st.form("field_obs_form"):
            c=st.columns(5); od=c[0].date_input("Date",date.today()); ot=c[1].time_input("Time",datetime.now().time().replace(microsecond=0)); cat=c[2].selectbox("Type",OBSERVATION_CATEGORIES,index=OBSERVATION_CATEGORIES.index(default_category) if default_category in OBSERVATION_CATEGORIES else 0); sev=c[3].slider("Severity",1,5,2); observer=c[4].text_input("Observer")
            c2=st.columns(3); trial_lab=c2[0].selectbox("Trial",list(trial_options)); unit_lab=c2[1].selectbox("Experimental unit",list(unit_options)); plant_tag=c2[2].text_input("Tagged plant / observation ID")
            measurements={}
            if protocol_fields:
                st.caption("Protocol measurements")
                cols=st.columns(min(3,len(protocol_fields)))
                for i,f in enumerate(protocol_fields):
                    label=f"{f.get('label',f.get('name'))} ({f.get('unit')})" if f.get('unit') else str(f.get('label',f.get('name')))
                    number_kwargs = {}
                    if f.get("min") is not None:
                        number_kwargs["min_value"] = float(f.get("min"))
                    if f.get("max") is not None:
                        number_kwargs["max_value"] = float(f.get("max"))
                    measurements[f.get("name")]=cols[i%len(cols)].number_input(label,value=0.0,key=f"obs_measure_{i}",**number_kwargs)
            notes=st.text_area("Observation notes"); recommendation=st.text_area("Follow-up / recommendation (optional)"); photo=st.file_uploader("Photo",type=["jpg","jpeg","png","webp"],key="field_obs_photo"); follow=st.checkbox("Create follow-up task")
            save=st.form_submit_button("Save observation",type="primary",width="stretch")
        if save:
            if not shape(field["geometry"]).buffer(1e-10).covers(Point(float(lon),float(lat))): st.error("Observation location is outside the authoritative field boundary.")
            else:
                photo_path=db.save_attachment(photo.getvalue(),photo.name) if photo else ""; observed_at=datetime.combine(od,ot).isoformat()
                oid=db.create_observation(field_id,observed_at=observed_at,category=cat,severity=sev,latitude=lat,longitude=lon,notes=notes,recommendation=recommendation,photo_path=photo_path,created_by=observer)
                stored_protocol_id = protocol_id
                if (protocol_id or "").startswith("builtin:"):
                    builtin_name = str(protocol_id).split(":",1)[1]
                    builtin = BUILTIN_PROTOCOLS[builtin_name]
                    stored_protocol_id = f"builtin_{slug(builtin_name)}"
                    db.save_observation_protocol(builtin_name, builtin["fields"], protocol_id=stored_protocol_id, category=builtin["category"], description=builtin["description"])
                db.save_observation_details(oid,trial_id=trial_options[trial_lab],experimental_unit_id=unit_options[unit_lab],plant_tag=plant_tag,protocol_id=stored_protocol_id,measurements=measurements)
                if follow: db.create_task(field_id,f"Follow up: {cat}",category="Scouting",assigned_to=observer,due_date=str(date.today()+timedelta(days=1)),priority="High" if sev>=4 else "Normal",description=f"Observation {oid}: {notes}",source="Scouting observation")
                st.success("Observation saved with spatial and protocol provenance."); st.rerun()
        obs=db.detailed_observations(field_id)
        if not obs.empty: st.dataframe(obs.drop(columns=["measurement_json"],errors="ignore"),hide_index=True,width="stretch")


def _render_operations(db: FieldOperationsDatabase, context: Mapping[str, Any], field_id: str, field: Mapping[str, Any]) -> None:
    st.markdown("### Management operations")
    st.caption("Recommendation, planned work and actual field operation are separate records. Use Actual only for work that was really performed.")
    geometry_mode=st.radio("Treated spatial support",["Whole field","Custom polygon"],horizontal=True,key="operation_geometry_mode")
    operation_geometry=field["geometry"]
    if geometry_mode=="Custom polygon":
        operation_geometry=render_boundary_editor(key="operation_custom_geometry",center=(float(field["centroid_lat"]),float(field["centroid_lon"])),reference_geometries=[field["geometry"]],zoom=17,height=430,satellite_default=True) or None
        if operation_geometry:
            if not shape(field["geometry"]).buffer(1e-10).covers(shape(operation_geometry)): st.error("Custom operation polygon extends outside the authoritative field boundary.")
            else: st.success(f"Custom treated area: {geometry_area_hectares(operation_geometry):.3f} ha")
    registry=context.get("research_registry"); rec_choices={"No linked recommendation":None}
    if registry is not None:
        try:
            recs=registry.recommendations(field_id=field_id)
            for _,r in recs.iterrows(): rec_choices[f"{r.get('action_type')} · {str(r.get('action_text'))[:70]} · {r.get('status')}"]=str(r["recommendation_id"])
        except Exception: pass
    with st.form("field_operation_form"):
        c=st.columns(5); op_date=c[0].date_input("Date",date.today()); record_type=c[1].selectbox("Record type",["Actual","Planned"]); category=c[2].selectbox("Operation",OPERATION_CATEGORIES); product=c[3].text_input("Product / material"); operator=c[4].text_input("Operator")
        c2=st.columns(5); rate=c2[0].number_input("Rate",min_value=0.0,value=0.0); unit=c2[1].text_input("Rate unit",value="kg/ha"); water=c2[2].number_input("Water (mm)",min_value=0.0,value=0.0); cost=c2[3].number_input("Cost",min_value=0.0,value=0.0); rec_lab=c2[4].selectbox("Linked recommendation",list(rec_choices))
        c3=st.columns(4); purpose=c3[0].text_input("Purpose"); equipment=c3[1].text_input("Equipment"); method=c3[2].text_input("Application method"); active=c3[3].text_input("Active ingredient")
        c4=st.columns(3); batch=c4[0].text_input("Batch / lot"); start=c4[1].text_input("Start time (HH:MM)"); end=c4[2].text_input("End time (HH:MM)")
        notes=st.text_area("Operation notes / deviations / safety constraints"); save=st.form_submit_button("Record operation",type="primary",width="stretch")
    if save:
        if not operation_geometry: st.error("Provide a valid treated geometry.")
        elif not shape(field["geometry"]).buffer(1e-10).covers(shape(operation_geometry)): st.error("Treated geometry must stay inside the field.")
        else:
            oid=db.create_operation(field_id,operation_date=str(op_date),category=category,product=product,rate=rate or None,rate_unit=unit,treated_area_ha=geometry_area_hectares(operation_geometry),water_mm=water or None,cost=cost or None,operator=operator,notes=notes)
            db.save_operation_details(oid,start_time=start.strip() or None,end_time=end.strip() or None,purpose=purpose,equipment=equipment,method=method,active_ingredient=active,batch_lot=batch,recommendation_id=rec_choices[rec_lab],record_type=record_type,geometry=operation_geometry)
            st.success("Operation recorded with spatial support and provenance."); st.rerun()
    ops=db.detailed_operations(field_id)
    if not ops.empty:
        st.dataframe(ops.drop(columns=["geometry_json","weather_json"],errors="ignore"),hide_index=True,width="stretch")
        summary=ops.groupby("category",as_index=False).agg(Events=("operation_id","count"),Cost=("cost","sum"),Water_mm=("water_mm","sum")); st.plotly_chart(px.bar(summary,x="category",y="Events",title="Recorded operations"),width="stretch")


def _render_sensors_samples(db: FieldOperationsDatabase, context: Mapping[str, Any], field_id: str, field: Mapping[str, Any]) -> None:
    mode=st.radio("Measurement system",["Sensor dashboard","Readings & import","Sensor lifecycle","Nutrient / soil / tissue samples","Irrigation status"],horizontal=True,key="sensor_sample_mode")
    sensors=db.sensors(field_id); readings=db.readings(field_id=field_id)
    if mode=="Sensor dashboard":
        if sensors.empty: st.info("No sensors registered.")
        else:
            rows=[]
            for s in sensors.to_dict("records"):
                r=readings.loc[readings["sensor_id"].astype(str).eq(str(s["sensor_id"]))] if not readings.empty else pd.DataFrame(); checked,summary=sensor_quality_report(r,s["sensor_type"])
                latest=r.iloc[-1] if not r.empty else None; age=_age_label(latest.get("timestamp") if latest is not None else None)
                rows.append({"Sensor":s["name"],"Type":s["sensor_type"],"Depth cm":s.get("depth_cm"),"Status":s.get("status"),"Latest":latest.get("value") if latest is not None else None,"Unit":s.get("unit"),"Age":age,"Rows":summary["rows"],"QC missing":summary["missing"],"Stale >7d":summary["stale"]})
            st.dataframe(pd.DataFrame(rows),hide_index=True,width="stretch")
            soil=sensors.loc[sensors["sensor_type"].eq("Soil moisture")]
            if not soil.empty and not readings.empty:
                ids=set(soil["sensor_id"].astype(str)); plot=readings.loc[readings["sensor_id"].astype(str).isin(ids)].copy()
                if not plot.empty: st.plotly_chart(px.line(plot,x="timestamp",y="value",color="sensor_name",title="Soil moisture profile through time"),width="stretch")
    elif mode=="Readings & import":
        if sensors.empty: st.info("Register a sensor in Sensor lifecycle first.")
        else:
            labels={f"{r['name']} · {r['sensor_type']} · {r.get('depth_cm') or 'surface'} cm":str(r["sensor_id"]) for _,r in sensors.iterrows()}; lab=st.selectbox("Sensor",list(labels)); sid=labels[lab]
            upload=st.file_uploader("Upload readings CSV",type=["csv"],key="sensor_import_file")
            if upload:
                raw=pd.read_csv(upload); st.dataframe(raw.head(30),hide_index=True,width="stretch"); c=st.columns(2); tcol=c[0].selectbox("Timestamp column",list(raw.columns)); vcol=c[1].selectbox("Value column",[x for x in raw.columns if x!=tcol])
                if st.button("Import readings",type="primary",width="stretch"):
                    report=db.import_sensor_readings(sid,raw,tcol,vcol); st.success(f"{report['inserted']} new, {report['updated']} updated, {report['invalid']} invalid excluded."); st.rerun()
            rr=db.readings(sensor_id=sid)
            if not rr.empty: st.plotly_chart(px.line(rr,x="timestamp",y="value",title=lab),width="stretch"); st.dataframe(rr.tail(500),hide_index=True,width="stretch")
            st.caption("Release 11.8 preserves generic CSV import. Reusable vendor/API connectors remain data-source specific and are not invented without a documented endpoint.")
    elif mode=="Sensor lifecycle":
        with st.expander("Register sensor",expanded=sensors.empty):
            with st.form("sensor_register"):
                c=st.columns(4); name=c[0].text_input("Name"); typ=c[1].selectbox("Type",SENSOR_TYPES); unit=c[2].text_input("Unit",value=SENSOR_DEFAULT_UNITS[SENSOR_TYPES[0]]); depth=c[3].number_input("Depth cm",min_value=0.0,value=0.0)
                c2=st.columns(3); lat=c2[0].number_input("Latitude",value=float(field["centroid_lat"]),format="%.7f"); lon=c2[1].number_input("Longitude",value=float(field["centroid_lon"]),format="%.7f"); installed=c2[2].date_input("Installed",date.today())
                source=st.text_input("Manufacturer / station / source"); note=st.text_area("Installation & calibration note"); save=st.form_submit_button("Register sensor",type="primary",width="stretch")
            if save:
                sid=db.create_sensor(field_id,name,typ,unit=unit or SENSOR_DEFAULT_UNITS.get(typ),depth_cm=depth or None,latitude=lat,longitude=lon,source=source,calibration_note=note); db.save_sensor_details(sid,installed_at=str(installed)); st.success("Sensor registered."); st.rerun()
        if not sensors.empty:
            labels={f"{r['name']} · {r['sensor_type']} · {r['status']}":str(r["sensor_id"]) for _,r in sensors.iterrows()}; lab=st.selectbox("Manage sensor",list(labels)); sid=labels[lab]; row=sensors.loc[sensors["sensor_id"].astype(str).eq(sid)].iloc[0]
            c=st.columns(3); status=c[0].selectbox("Lifecycle",["Active","Maintenance","Retired"],index=["Active","Maintenance","Retired"].index(row["status"]) if row["status"] in ["Active","Maintenance","Retired"] else 0); depth=c[1].number_input("Depth cm",min_value=0.0,value=float(row.get("depth_cm") or 0)); retired=c[2].date_input("Retirement date",value=None)
            if st.button("Save sensor lifecycle",width="stretch"):
                db.update_sensor(sid,status=status,depth_cm=depth or None,retired_at=str(retired) if retired else None); st.success("Sensor updated without deleting historical readings."); st.rerun()
            with st.form("sensor_calibration"):
                cc=st.columns(3); cd=cc[0].date_input("Calibration date",date.today()); method=cc[1].text_input("Method"); reference=cc[2].text_input("Reference standard"); result=st.text_input("Result / adjustment"); notes=st.text_area("Calibration notes"); savec=st.form_submit_button("Add calibration record",width="stretch")
            if savec: db.add_sensor_calibration(sid,str(cd),method=method,reference=reference,result=result,notes=notes); st.success("Calibration event saved."); st.rerun()
            cal=db.sensor_calibrations(sid)
            if not cal.empty: st.dataframe(cal,hide_index=True,width="stretch")
    elif mode=="Nutrient / soil / tissue samples":
        with st.form("structured_sample_form"):
            c=st.columns(4); sample_date=c[0].date_input("Sample date",date.today()); sample_type=c[1].selectbox("Type",["Soil","Tissue","Water","Fertiliser"]); ext=c[2].text_input("Sample ID / barcode"); stage=c[3].text_input("Growth stage")
            c2=st.columns(4); dfrom=c2[0].number_input("Depth from (cm)",min_value=0.0,value=0.0); dto=c2[1].number_input("Depth to (cm)",min_value=0.0,value=30.0); tissue=c2[2].text_input("Tissue / plant part"); lab=c2[3].text_input("Laboratory")
            c3=st.columns(4); lat=c3[0].number_input("Latitude",value=float(field["centroid_lat"]),format="%.7f"); lon=c3[1].number_input("Longitude",value=float(field["centroid_lon"]),format="%.7f"); method=c3[2].text_input("Analytical method"); dl=c3[3].text_input("Detection limit")
            v=st.columns(6); n=v[0].number_input("N",value=0.0); p=v[1].number_input("P",value=0.0); k=v[2].number_input("K",value=0.0); ph=v[3].number_input("pH",0.0,14.0,7.0); ec=v[4].number_input("EC",min_value=0.0,value=0.0); om=v[5].number_input("Organic matter %",min_value=0.0,value=0.0)
            c4=st.columns(4); nu=c4[0].text_input("N unit"); pu=c4[1].text_input("P unit"); ku=c4[2].text_input("K unit"); ecu=c4[3].text_input("EC unit",value="dS/m")
            notes=st.text_area("Notes"); save=st.form_submit_button("Save sample",type="primary",width="stretch")
        if save:
            sid=db.add_nutrient_sample(field_id,sample_date=str(sample_date),sample_type=sample_type,latitude=lat,longitude=lon,nitrogen=n or None,phosphorus=p or None,potassium=k or None,ph=ph or None,ec=ec or None,organic_matter=om or None,notes=notes)
            db.save_nutrient_sample_details(sid,external_sample_id=ext,depth_from_cm=dfrom,depth_to_cm=dto,tissue_part=tissue,growth_stage=stage,laboratory=lab,analytical_method=method,units={"N":nu,"P":pu,"K":ku,"EC":ecu},detection_limit=dl); st.success("Structured sample saved."); st.rerun()
        samples=db.detailed_nutrient_samples(field_id)
        if not samples.empty: st.dataframe(samples.drop(columns=["units_json"],errors="ignore"),hide_index=True,width="stretch")
    else:
        from field_operations_suite import irrigation_advisory
        advisory=irrigation_advisory(context,field,db); c=st.columns(4); c[0].metric("Source",advisory["source"]); c[1].metric("Status",advisory["status"]); c[2].metric("Urgency",advisory["urgency"]); c[3].metric("Net depth","—" if advisory["recommended_mm"] is None else f"{advisory['recommended_mm']:.1f} mm")
        st.info(advisory["reason"]); st.caption("Use Crop Decisions → Decision intelligence & optimisation for policy comparison and constrained irrigation research. This compact field view does not control hardware.")


def _persistent_health_metrics(db: FieldOperationsDatabase, context: Mapping[str, Any], field_id: str) -> list[dict[str, Any]]:
    rows=[]; freshness=_research_freshness(context,field_id)
    for name,item in freshness.items(): rows.append({"Signal":name,"Latest":_age_label(item.get("timestamp")),"Source":item.get("source"),"Interpretation":"Persisted evidence status"})
    readings=db.readings(field_id=field_id)
    if not readings.empty:
        latest=readings.sort_values("timestamp").groupby("sensor_id",as_index=False).tail(1)
        for r in latest.to_dict("records")[:8]: rows.append({"Signal":f"Sensor · {r.get('sensor_name')}","Latest":f"{r.get('value')} {r.get('unit') or ''}","Source":r.get('sensor_type'),"Interpretation":_age_label(r.get('timestamp'))})
    registry=context.get("research_registry")
    if registry is not None:
        try:
            preds=registry.predictions(field_id=field_id,limit=5)
            for r in preds.to_dict("records"):
                value=r.get("prediction") if pd.notna(r.get("prediction")) else r.get("prediction_text")
                rows.append({"Signal":f"Model · {r.get('target')}","Latest":value,"Source":r.get('model_name'),"Interpretation":f"Modelled · {_age_label(r.get('generated_at'))}"})
        except Exception: pass
    return rows


def _render_crop_health(db: FieldOperationsDatabase, context: Mapping[str, Any], field_id: str, field: Mapping[str, Any]) -> None:
    mode=st.radio("Crop-health view",["Field health","Alert rules","Incidents","Portfolio attention"],horizontal=True,key="crop_health_mode")
    if mode=="Field health":
        rows=_persistent_health_metrics(db,context,field_id)
        if rows: st.dataframe(pd.DataFrame(rows),hide_index=True,width="stretch")
        else: st.info("No persistent health evidence is linked yet.")
        st.markdown("#### Data actions")
        st.info("Weather and EO retrieval remain explicit researcher actions. Use Climate & Earth Observation / Research Data Hub to retrieve them; Release 11.8 reads the persisted result here after retrieval rather than relying only on current-session state.")
    elif mode=="Alert rules":
        rules=db.alert_rules(); st.dataframe(rules,hide_index=True,width="stretch") if not rules.empty else None
        template=st.selectbox("Rule template",["Custom"]+list(ALERT_TEMPLATES),key="alert_template")
        if template=="Custom": source=st.selectbox("Source",list(SOURCE_METRICS),key="alert_source"); metric=st.selectbox("Metric",SOURCE_METRICS[source],key="alert_metric"); op=st.selectbox("Operator",["<=",">=","<",">"]); threshold=st.number_input("Threshold",value=0.0); severity=st.selectbox("Severity",["Low","Normal","High","Urgent"],index=2); persistence=st.number_input("Consecutive evaluations",1,10,1); cooldown=st.number_input("Cooldown hours",1,720,24); note=st.text_area("Scientific interpretation / caveat")
        else:
            source,metric,op,threshold,severity,persistence,cooldown,note=ALERT_TEMPLATES[template]; st.caption(f"{source} · {metric} {op} {threshold} · {severity}")
        stage=st.text_input("Crop-stage restriction (optional)"); name=st.text_input("Rule name",value=template if template!="Custom" else "")
        if st.button("Save alert rule",type="primary",width="stretch"):
            if not name.strip(): st.error("Rule name is required.")
            else:
                rid=db.save_rule(name=name,source=source,metric=metric,operator=op,threshold=float(threshold),severity=severity,window_days=1,enabled=True,notes=note); db.save_alert_rule_details(rid,persistence_count=int(persistence),cooldown_hours=int(cooldown),crop_stage=stage); st.success("Rule saved. Persistence/cooldown are recorded as explicit rule metadata; evaluation must use enough sequential evidence before acting."); st.rerun()
    elif mode=="Incidents":
        alerts=db.alerts(field_id)
        if alerts.empty: st.info("No alert incidents for this field.")
        else:
            st.dataframe(alerts,hide_index=True,width="stretch"); labels={f"{r['alert_type']} · {r['status']} · {str(r['created_at'])[:10]}":str(r["alert_id"]) for _,r in alerts.iterrows()}; lab=st.selectbox("Incident",list(labels)); aid=labels[lab]
            action=st.selectbox("Action",["Acknowledge","Resolve","Mark false positive","Snooze 24 h","Create scouting task"]); note=st.text_area("Finding / resolution note"); who=st.text_input("Recorded by")
            if st.button("Apply incident action",type="primary",width="stretch"):
                if action=="Acknowledge": db.update_alert_status(aid,"Acknowledged",who); db.save_alert_details(aid,acknowledged_at=datetime.now(timezone.utc).isoformat(),resolution_notes=note)
                elif action=="Resolve": db.update_alert_status(aid,"Resolved",who); db.save_alert_details(aid,resolution_notes=note)
                elif action=="Mark false positive": db.update_alert_status(aid,"Resolved",who); db.save_alert_details(aid,false_positive=1,resolution_notes=note)
                elif action=="Snooze 24 h": db.save_alert_details(aid,snoozed_until=(_now_utc()+timedelta(hours=24)).isoformat(),resolution_notes=note)
                else: db.create_task(field_id,"Scout alert incident",category="Scouting",assigned_to=who,due_date=str(date.today()),priority="High",description=note,source=f"Alert {aid}")
                st.success("Incident updated with an audit trail."); st.rerun()
    else:
        att=db.portfolio_attention();
        if att.empty: st.info("No fields.")
        else:
            att["Attention score"]=att["open_alerts"]*3+att["severe_observations"]*2+att["overdue_tasks"]*2+att["open_tasks"]
            st.dataframe(att.sort_values("Attention score",ascending=False),hide_index=True,width="stretch"); st.caption("Portfolio Attention replaces the old field leaderboard and uses one batch SQL summary instead of many per-field queries.")


def _random_points_in_polygon(geom, n: int, rng: np.random.Generator) -> list[Point]:
    minx,miny,maxx,maxy=geom.bounds; points=[]; attempts=0
    while len(points)<n and attempts<max(1000,n*500):
        p=Point(rng.uniform(minx,maxx),rng.uniform(miny,maxy)); attempts+=1
        if geom.covers(p): points.append(p)
    return points


def _sampling_design(geometry: Mapping[str, Any], design: str, count: int, spacing_m: float, inset_m: float, seed: int) -> pd.DataFrame:
    from field_operations_suite import generate_sampling_grid
    geom=shape(geometry)
    if design=="Systematic grid": return generate_sampling_grid(geometry,spacing_m,inset_m)
    rng=np.random.default_rng(seed); points=[]
    if design=="Random": points=_random_points_in_polygon(geom,count,rng)
    elif design=="Stratified random":
        minx,miny,maxx,maxy=geom.bounds; side=max(1,int(math.ceil(math.sqrt(count)))); cells=[]
        for i in range(side):
            for j in range(side):
                from shapely.geometry import box
                cell=box(minx+i*(maxx-minx)/side,miny+j*(maxy-miny)/side,minx+(i+1)*(maxx-minx)/side,miny+(j+1)*(maxy-miny)/side).intersection(geom)
                if not cell.is_empty: cells.append(cell)
        rng.shuffle(cells)
        for cell in cells[:count]:
            pts=_random_points_in_polygon(cell,1,rng)
            if pts: points.extend(pts)
        if len(points)<count: points.extend(_random_points_in_polygon(geom,count-len(points),rng))
    return pd.DataFrame([{"sample_id":uuid4().hex[:10],"latitude":p.y,"longitude":p.x,"stratum":design} for p in points])


def _render_precision(db: FieldOperationsDatabase, context: Mapping[str, Any], field_id: str, field: Mapping[str, Any]) -> None:
    mode=st.radio("Precision workflow",["Management-zone exploration","Sampling design","Saved prescriptions"],horizontal=True,key="precision_mode")
    if mode=="Sampling design":
        c=st.columns(5); design=c[0].selectbox("Design",["Systematic grid","Random","Stratified random"]); count=int(c[1].number_input("Target samples",1,10000,30)); spacing=c[2].number_input("Grid spacing m",5.0,1000.0,50.0,5.0); inset=c[3].number_input("Edge inset m",0.0,500.0,5.0,1.0); seed=int(c[4].number_input("Random seed",0,999999,42))
        st.caption("For systematic grids, spacing controls count. For random/stratified designs, target sample count controls count.")
        if st.button("Generate design",type="primary",width="stretch"):
            try: st.session_state.field_sampling_preview=_sampling_design(field["geometry"],design,count,spacing,inset,seed); st.session_state.field_sampling_meta={"design":design,"field_id":field_id}
            except Exception as e: st.error(str(e))
        grid=st.session_state.get("field_sampling_preview"); meta=st.session_state.get("field_sampling_meta") or {}
        if isinstance(grid,pd.DataFrame) and not grid.empty and meta.get("field_id")==field_id:
            st.metric("Generated locations",len(grid)); st.dataframe(grid,hide_index=True,width="stretch")
            m=_map_for_geometry(field["geometry"],zoom=17,satellite_default=True); folium.GeoJson(field["geometry"],style_function=lambda _:{"weight":4,"fillOpacity":0.04}).add_to(m)
            for r in grid.to_dict("records"): folium.CircleMarker([r["latitude"],r["longitude"]],radius=4,fill=True,tooltip=r["sample_id"]).add_to(m)
            st_folium(m,use_container_width=True,height=520,key="sampling_preview_map")
            name=st.text_input("Design name",value=f"{design} {date.today()}")
            if st.button("Save sampling design",width="stretch"):
                n=db.save_sampling_points(field_id,grid,name,design); st.success(f"Saved {n} persistent sampling points."); st.rerun()
        saved=db.sampling_points(field_id)
        if not saved.empty: st.markdown("#### Saved sampling points"); st.dataframe(saved,hide_index=True,width="stretch")
    elif mode=="Management-zone exploration":
        st.info("Release 11.8 treats K-means outputs as exploratory point clusters unless independent interpolation/zone validation supports contiguous management zones.")
        source=st.selectbox("Point data source",["Existing nutrient samples","Upload point CSV"])
        points=pd.DataFrame()
        if source=="Existing nutrient samples":
            samples=db.detailed_nutrient_samples(field_id)
            if not samples.empty:
                points=samples.rename(columns={"nitrogen":"N","phosphorus":"P","potassium":"K","organic_matter":"Organic matter"})
            else: st.info("No georeferenced nutrient samples yet.")
        else:
            upload=st.file_uploader("Point CSV",type=["csv"],key="precision_points_upload")
            if upload: points=pd.read_csv(upload)
        if not points.empty and {"latitude","longitude"}.issubset(points.columns):
            numeric=[c for c in points.columns if c not in {"latitude","longitude"} and pd.to_numeric(points[c],errors="coerce").notna().sum()>=4]
            if numeric:
                selected=st.multiselect("Variables",numeric,default=numeric[:min(3,len(numeric))]); c=st.columns(3); k=int(c[0].slider("Clusters",2,min(6,max(2,len(points)-1)),3)); use_pca=c[1].checkbox("PCA before clustering",value=len(selected)>3); seed=int(c[2].number_input("Seed",0,999999,42))
                if st.button("Explore clusters",type="primary",width="stretch") and selected:
                    work=points.dropna(subset=["latitude","longitude"]+selected).copy(); X=work[selected].apply(pd.to_numeric,errors="coerce").dropna(); work=work.loc[X.index]
                    inside=work.apply(lambda r: shape(field["geometry"]).covers(Point(float(r["longitude"]),float(r["latitude"]))),axis=1); work=work.loc[inside]; X=X.loc[work.index]
                    if len(work)<=k: st.error("Need more in-field complete samples than clusters.")
                    else:
                        Xs=StandardScaler().fit_transform(X); Xfit=PCA(n_components=min(len(selected),3),random_state=seed).fit_transform(Xs) if use_pca and len(selected)>1 else Xs; model=KMeans(n_clusters=k,random_state=seed,n_init=20).fit(Xfit); work["cluster"]=model.labels_+1; sil=silhouette_score(Xfit,model.labels_) if len(set(model.labels_))>1 else np.nan; st.metric("Silhouette",f"{sil:.3f}" if np.isfinite(sil) else "—"); st.dataframe(work[["latitude","longitude"]+selected+["cluster"]],hide_index=True,width="stretch"); st.warning("Clusters describe similarity among sampled points. They are not automatically continuous prescription polygons and should not be treated as validated rate zones.")
            else: st.warning("No numeric variables with enough observations.")
    else:
        rx=db.prescriptions(field_id); st.dataframe(rx.drop(columns=["geometry_json"],errors="ignore"),hide_index=True,width="stretch") if not rx.empty else st.info("No saved prescriptions.")


def _render_history(db: FieldOperationsDatabase, context: Mapping[str, Any], field_id: str, field: Mapping[str, Any]) -> None:
    st.markdown("### Field / season history")
    mode=st.radio("History view",["Timeline","Seasons","Exports & offline pack"],horizontal=True,key="history_mode")
    if mode=="Timeline":
        timeline=db.field_timeline(field_id)
        if timeline.empty: st.info("No history yet.")
        else:
            types=st.multiselect("Event types",sorted(timeline["type"].dropna().unique()),default=sorted(timeline["type"].dropna().unique())); view=timeline.loc[timeline["type"].isin(types)]
            for row in view.head(100).to_dict("records"):
                ts=pd.to_datetime(row.get("timestamp"),errors="coerce"); st.markdown(f"**{ts.strftime('%d %b %Y') if pd.notna(ts) else '—'} · {row.get('type')} · {row.get('title')}**"); st.caption(str(row.get("detail") or "")[:260])
            st.download_button("Download field diary CSV",view.to_csv(index=False).encode(),file_name=f"{slug(field['name'])}_field_diary.csv",mime="text/csv",width="stretch")
    elif mode=="Seasons":
        seasons=db.seasons(field_id); history=db.frame("SELECT * FROM crop_history WHERE field_id=? ORDER BY season_year DESC",(field_id,))
        if not seasons.empty: st.dataframe(seasons,hide_index=True,width="stretch")
        elif not history.empty: st.info("Legacy crop-history records are present. Create a structured season below when you next edit the field season."); st.dataframe(history,hide_index=True,width="stretch")
        with st.form("field_season_form"):
            c=st.columns(4); year=int(c[0].number_input("Season",1900,2200,int(field.get("season_year") or date.today().year))); crop=c[1].text_input("Crop",value=str(field.get("crop") or "")); genotype=c[2].text_input("Genotype / variety",value=str(field.get("variety") or "")); status=c[3].selectbox("Status",["Planned","Active","Completed","Archived"],index=1)
            c2=st.columns(3); sow=c2[0].date_input("Sowing",value=None); harv=c2[1].date_input("Harvest",value=None); irrig=c2[2].text_input("Irrigation system",value=str(field.get("irrigation_system") or "")); notes=st.text_area("Season notes"); save=st.form_submit_button("Save structured season",type="primary",width="stretch")
        if save:
            if not crop.strip(): st.error("Crop is required.")
            else: db.save_season(field_id,year,crop,genotype=genotype,sowing_date=str(sow) if sow else None,harvest_date=str(harv) if harv else None,status=status,irrigation_system=irrig,notes=notes); st.success("Season saved without altering previous seasons."); st.rerun()
        st.caption("Persistent properties such as field geometry and soil context remain at field level; crop/genotype and management belong to each season.")
    else:
        render_data_exchange_page(db,context)


def render_field_command_centre(db: FieldOperationsDatabase, context: Mapping[str, Any]) -> None:
    fields=db.fields()
    if fields.empty:
        st.info("No mapped field exists yet. Create the research centre/farm and authoritative field boundary below.")
        render_farm_portfolio_page(db,context)
        return
    field_id,field=_active_field(db)
    if not field_id or not field: return
    pulse=_field_pulse(db,context,field_id,field); _render_context_strip(field,pulse)
    sections=["Overview","Map","Work & scouting","Operations","Sensors & samples","Crop health","Precision","History","Administration"]
    current=consume_view_request(
        st.session_state,
        request_key="field_command_section_request",
        widget_key="field_command_section",
        options=sections,
        default="Overview",
    )
    section=st.radio("Field workspace",sections,index=sections.index(current),horizontal=True,key="field_command_section",label_visibility="collapsed")
    st.divider()
    if section=="Overview": _render_overview(db,context,field_id,field,pulse)
    elif section=="Map": _render_map(db,context,field_id,field)
    elif section=="Work & scouting": _render_work(db,context,field_id,field)
    elif section=="Operations": _render_operations(db,context,field_id,field)
    elif section=="Sensors & samples": _render_sensors_samples(db,context,field_id,field)
    elif section=="Crop health": _render_crop_health(db,context,field_id,field)
    elif section=="Precision": _render_precision(db,context,field_id,field)
    elif section=="History": _render_history(db,context,field_id,field)
    else:
        st.warning("Administration can edit or delete authoritative records. Normal field work is intentionally kept outside this section.")
        render_farm_portfolio_page(db,context)
