"""AGROLATTICE 11.10 Climate & Earth Observation Command Centre.

This module reorganises the climate / EO workspace around a persistent mapped-field
context while preserving the existing scientific tools.  The overview is intentionally
lightweight: it reads saved summaries and small database records only.  Expensive NASA,
STAC, clustering, similarity and model operations remain explicit researcher actions.
"""
from __future__ import annotations

import json
import math
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from navigation_state import consume_view_request, queue_view_request

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

MODULE_VERSION = "1.0.1"

MONTH_ORDER = [
    "JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE",
    "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER",
]
MONTH_SHORT = {name: name[:3].title() for name in MONTH_ORDER}

VARIABLE_GROUPS: dict[str, tuple[str, ...]] = {
    "Temperature": (
        "TEMPERATURE", "TEMPERATURE_MAX", "TEMPERATURE_MIN",
        "SOIL_TEMP_LAYER1", "SOIL_TEMP_LAYER2",
    ),
    "Water & atmospheric demand": (
        "PRECIPITATION_AVG", "PRECIPITATION_MAX", "PRECIPITATION_MIN",
        "EVAPOTRANSPIRATION", "EVAPOTRANSPIRATION_ENERGY_FLUX", "EVAPORATION_LAND",
        "RELATIVE_HUMIDITY",
    ),
    "Radiation & cloud": (
        "SOLAR_RADIATION", "LONGWAVE_RADIATION", "CLEARNESS_INDEX", "CLOUD_AMOUNT_DAY",
    ),
    "Soil energy": ("SOIL_HEAT_FLUX",),
    "Wind & pressure": ("WIND_SPEED", "SURFACE_PRESSURE"),
}

# The installed dataset uses the canonical variables below.  Units are surfaced as
# provider/canonical units where they are stable; uncertain legacy/provider-specific
# quantities are deliberately labelled as such instead of inventing precision.
VARIABLE_UNITS: dict[str, str] = {
    "TEMPERATURE": "°C",
    "TEMPERATURE_MAX": "°C",
    "TEMPERATURE_MIN": "°C",
    "SOIL_TEMP_LAYER1": "°C",
    "SOIL_TEMP_LAYER2": "°C",
    "PRECIPITATION_AVG": "mm day⁻¹",
    "PRECIPITATION_MAX": "mm day⁻¹",
    "PRECIPITATION_MIN": "mm day⁻¹",
    "EVAPOTRANSPIRATION": "mm day⁻¹ (derived where available)",
    "EVAPOTRANSPIRATION_ENERGY_FLUX": "W m⁻² or provider unit",
    "EVAPORATION_LAND": "provider unit",
    "RELATIVE_HUMIDITY": "%",
    "SOLAR_RADIATION": "MJ m⁻² day⁻¹",
    "LONGWAVE_RADIATION": "MJ m⁻² day⁻¹",
    "CLEARNESS_INDEX": "ratio",
    "CLOUD_AMOUNT_DAY": "%",
    "SOIL_HEAT_FLUX": "W m⁻² or provider unit",
    "WIND_SPEED": "m s⁻¹",
    "SURFACE_PRESSURE": "kPa",
}

VARIABLE_LABELS: dict[str, str] = {
    "TEMPERATURE": "Mean air temperature",
    "TEMPERATURE_MAX": "Maximum air temperature",
    "TEMPERATURE_MIN": "Minimum air temperature",
    "SOIL_TEMP_LAYER1": "Soil temperature · layer 1",
    "SOIL_TEMP_LAYER2": "Soil temperature · layer 2",
    "PRECIPITATION_AVG": "Average precipitation",
    "PRECIPITATION_MAX": "Maximum precipitation",
    "PRECIPITATION_MIN": "Minimum precipitation",
    "EVAPOTRANSPIRATION": "Reference / derived evapotranspiration",
    "EVAPOTRANSPIRATION_ENERGY_FLUX": "Evapotranspiration energy flux",
    "EVAPORATION_LAND": "Land-surface evaporation",
    "RELATIVE_HUMIDITY": "Relative humidity",
    "SOLAR_RADIATION": "Solar radiation",
    "LONGWAVE_RADIATION": "Longwave radiation",
    "CLEARNESS_INDEX": "Clearness index",
    "CLOUD_AMOUNT_DAY": "Daytime cloud amount",
    "SOIL_HEAT_FLUX": "Soil heat flux",
    "WIND_SPEED": "Wind speed",
    "SURFACE_PRESSURE": "Surface pressure",
}


def _json_load(value: Any, default: Any = None) -> Any:
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list, tuple, int, float, bool)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def _json_safe(value: Any) -> Any:
    if isinstance(value, pd.DataFrame):
        return [_json_safe(row) for row in value.to_dict(orient="records")]
    if isinstance(value, pd.Series):
        return [_json_safe(v) for v in value.tolist()]
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def _age_text(timestamp: Any) -> str:
    stamp = pd.to_datetime(timestamp, errors="coerce", utc=True)
    if pd.isna(stamp):
        return "not available"
    delta = max(0.0, (pd.Timestamp.now(tz="UTC") - stamp).total_seconds())
    if delta < 3600:
        return f"{max(1, int(delta // 60))} min old"
    if delta < 86400:
        return f"{int(delta // 3600)} h old"
    return f"{int(delta // 86400)} d old"


def _latest_acquisition(acquisitions: pd.DataFrame, keywords: tuple[str, ...]) -> dict[str, Any] | None:
    if not isinstance(acquisitions, pd.DataFrame) or acquisitions.empty:
        return None
    mask = pd.Series(False, index=acquisitions.index)
    for column in ("source", "source_type"):
        if column not in acquisitions:
            continue
        text = acquisitions[column].astype(str).str.casefold()
        for keyword in keywords:
            mask |= text.str.contains(keyword.casefold(), regex=False, na=False)
    subset = acquisitions.loc[mask].copy()
    if subset.empty:
        return None
    if "created_at" in subset:
        subset["_sort"] = pd.to_datetime(subset["created_at"], errors="coerce", utc=True)
        subset = subset.sort_values("_sort", ascending=False)
    return subset.iloc[0].to_dict()


def _haversine_km(lat1: float, lon1: float, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    r = 6371.0088
    p1 = np.radians(float(lat1))
    p2 = np.radians(lat2.astype(float))
    dp = np.radians(lat2.astype(float) - float(lat1))
    dl = np.radians(lon2.astype(float) - float(lon1))
    a = np.sin(dp / 2.0) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2.0) ** 2
    return 2.0 * r * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


def _nearest_location(field: Mapping[str, Any] | None, locations: pd.DataFrame) -> dict[str, Any] | None:
    if not field or locations is None or locations.empty:
        return None
    lat = pd.to_numeric(field.get("centroid_lat"), errors="coerce")
    lon = pd.to_numeric(field.get("centroid_lon"), errors="coerce")
    if pd.isna(lat) or pd.isna(lon):
        return None
    work = locations.dropna(subset=["lat", "lng"]).copy()
    if work.empty:
        return None
    distances = _haversine_km(float(lat), float(lon), work["lat"].to_numpy(), work["lng"].to_numpy())
    idx = int(np.nanargmin(distances))
    row = work.iloc[idx].to_dict()
    row["distance_km"] = float(distances[idx])
    return row


def _field_and_twin(field_db: Any, twin_db: Any, active_field_id: str | None) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    field = None
    link = None
    if active_field_id:
        try:
            field = field_db.field(str(active_field_id))
        except Exception:
            field = None
    if field:
        try:
            links = twin_db.links()
            if not links.empty and "field_id" in links:
                hit = links.loc[links["field_id"].astype(str).eq(str(active_field_id))]
                if not hit.empty:
                    link = hit.iloc[0].to_dict()
        except Exception:
            link = None
    return field, link


def _environment_snapshot(
    *, field_db: Any, twin_db: Any, registry: Any, active_field_id: str | None,
) -> dict[str, Any]:
    field, link = _field_and_twin(field_db, twin_db, active_field_id)
    acquisitions = pd.DataFrame()
    try:
        if active_field_id:
            acquisitions = registry.data_acquisitions(field_id=str(active_field_id), limit=100)
    except Exception:
        pass
    weather_acq = _latest_acquisition(acquisitions, ("weather", "nasa", "power", "climate"))
    eo_acq = _latest_acquisition(acquisitions, ("sentinel", "satellite", "earth observation", "eo"))

    weather_record = satellite_record = root_zone_record = None
    latest_snapshot = None
    if link:
        link_id = str(link.get("link_id"))
        try:
            weather_record = twin_db.weather_record(link_id)
        except Exception:
            pass
        try:
            satellite_record = twin_db.satellite_record(link_id)
        except Exception:
            pass
        try:
            root_zone_record = twin_db.root_zone_record(link_id)
        except Exception:
            pass
        try:
            snapshots = twin_db.snapshots(link_id)
            if not snapshots.empty:
                latest_snapshot = snapshots.iloc[-1].to_dict()
        except Exception:
            pass

    sensors = readings = pd.DataFrame()
    if active_field_id:
        try:
            sensors = field_db.sensors(str(active_field_id))
            readings = field_db.readings(field_id=str(active_field_id))
        except Exception:
            pass
    latest_sensor = None
    if isinstance(readings, pd.DataFrame) and not readings.empty and "timestamp" in readings:
        latest_sensor = pd.to_datetime(readings["timestamp"], errors="coerce", utc=True).max()

    return {
        "field": field,
        "twin_link": link,
        "weather_record": weather_record,
        "satellite_record": satellite_record,
        "root_zone_record": root_zone_record,
        "latest_twin_snapshot": latest_snapshot,
        "acquisitions": acquisitions,
        "weather_acquisition": weather_acq,
        "eo_acquisition": eo_acq,
        "sensors": sensors,
        "readings": readings,
        "latest_sensor": latest_sensor,
    }


def _record_date(record: Mapping[str, Any] | None, preferred: tuple[str, ...]) -> str | None:
    if not record:
        return None
    for key in preferred:
        value = record.get(key)
        if value not in (None, ""):
            stamp = pd.to_datetime(value, errors="coerce")
            if pd.notna(stamp):
                return str(stamp.date())
            return str(value)
    return None


def _metric_status(latest: Any, *, current_threshold_days: int, historical: bool = False) -> tuple[str, str]:
    stamp = pd.to_datetime(latest, errors="coerce", utc=True)
    if pd.isna(stamp):
        return "Missing", "warn"
    if historical:
        return "Stored", "good"
    days = max(0.0, (pd.Timestamp.now(tz="UTC") - stamp).total_seconds() / 86400.0)
    if days <= current_threshold_days:
        return "Current", "good"
    if days <= current_threshold_days * 3:
        return "Aging", "warn"
    return "Stale", "bad"


def _tone_icon(tone: str) -> str:
    return {"good": "✅", "warn": "⚠️", "bad": "🔴", "neutral": "◻️"}.get(tone, "•")


def _active_context_caption(field: Mapping[str, Any] | None, country: str, context: Mapping[str, Any]) -> str:
    parts = [country]
    if field:
        if field.get("farm_name"):
            parts.append(str(field.get("farm_name")))
        parts.append(str(field.get("name") or "Field"))
        if field.get("crop"):
            parts.append(str(field.get("crop")))
        if field.get("season_year"):
            parts.append(str(field.get("season_year")))
    else:
        for key in ("Field", "Crop", "Season"):
            value = context.get(key)
            if value and str(value) != "Not selected":
                parts.append(str(value))
    return "  ›  ".join(parts)


def _choose_view(options: list[str]) -> str:
    key = "release11_10_climate_command_view"
    legacy = st.session_state.get("release10_climate_workspace_view")
    mapping = {
        "Comparison studio": "Climate Comparison",
        "Spatial patterns": "Climate Zones & Transferability",
        "Climate risk": "Climate Risk",
        "Satellite monitoring": "Earth Observation",
    }
    current = st.session_state.get(key)
    if current == "Spatial & Transferability":
        st.session_state[key] = "Climate Zones & Transferability"
    elif current not in options and legacy in mapping:
        st.session_state[key] = mapping[legacy]
    default = consume_view_request(
        st.session_state,
        request_key="release11_10_climate_command_view_request",
        widget_key=key,
        options=options,
        default=options[0],
    )
    if hasattr(st, "segmented_control"):
        try:
            value = st.segmented_control("Workspace view", options, default=default, selection_mode="single", key=key, width="stretch")
        except TypeError:
            value = st.segmented_control("Workspace view", options, default=default, selection_mode="single", key=key)
        return value or default
    return st.selectbox("Workspace view", options, index=options.index(default), key=key)


def _preload_field_for_satellite(field: Mapping[str, Any] | None) -> bool:
    if not field or not field.get("geometry"):
        return False
    geometry = field.get("geometry")
    st.session_state["satellite_aoi_geometry"] = geometry
    st.session_state["satellite_aoi_metadata"] = {
        "Area source": "Mapped AGROLATTICE field",
        "Location": field.get("name") or "Mapped field",
        "Field ID": field.get("field_id"),
        "Farm / research centre": field.get("farm_name"),
        "Area (ha)": field.get("area_ha"),
        "Centroid latitude": field.get("centroid_lat"),
        "Centroid longitude": field.get("centroid_lon"),
    }
    st.session_state["satellite_aoi_mode"] = "Use current session field"
    if "satellite_field_name" not in st.session_state:
        st.session_state["satellite_field_name"] = str(field.get("name") or "Mapped field")
    return True


def _render_overview(
    *, snapshot: Mapping[str, Any], country: str, context: Mapping[str, Any], dataset_status: Mapping[str, Any],
    runtime_summary: Mapping[str, Any], open_destination: Callable[[str, str | None], None] | None,
    quick_update_weather: Callable[[Mapping[str, Any]], Mapping[str, Any] | None] | None = None,
) -> None:
    field = snapshot.get("field") or {}
    st.markdown("### Environmental Pulse")
    historical = False
    season = pd.to_numeric(field.get("season_year"), errors="coerce") if field else np.nan
    if pd.notna(season):
        historical = int(season) < date.today().year

    weather_rec = snapshot.get("weather_record") or snapshot.get("weather_acquisition") or {}
    eo_rec = snapshot.get("satellite_record") or snapshot.get("eo_acquisition") or {}
    root_rec = snapshot.get("root_zone_record") or {}
    weather_latest = _record_date(weather_rec, ("end_date", "period_end", "updated_at", "created_at"))
    eo_latest = _record_date(eo_rec, ("end_date", "period_end", "updated_at", "created_at"))
    root_latest = _record_date(root_rec, ("end_date", "updated_at", "created_at"))
    sensor_latest = snapshot.get("latest_sensor")

    cards = st.columns(4)
    w_status, w_tone = _metric_status(weather_latest, current_threshold_days=3, historical=historical)
    cards[0].metric("Weather", w_status, weather_latest or "No saved field weather")
    e_status, e_tone = _metric_status(eo_latest, current_threshold_days=12, historical=historical)
    cards[1].metric("Earth observation", e_status, eo_latest or "No saved Sentinel-2")
    r_status, r_tone = _metric_status(root_latest, current_threshold_days=3, historical=historical)
    cards[2].metric("Root zone", r_status, root_latest or "No saved root-zone state")
    s_status, s_tone = _metric_status(sensor_latest, current_threshold_days=2, historical=historical)
    cards[3].metric("Field sensors", s_status, _age_text(sensor_latest) if sensor_latest is not None else "No readings")

    with st.container(border=True):
        st.markdown(f"**{_active_context_caption(field or None, country, context)}**")
        if field:
            source_bits = [
                f"mapped area {float(field.get('area_ha') or 0):.2f} ha" if field.get("area_ha") else None,
                f"crop {field.get('crop')}" if field.get("crop") else None,
                f"season {field.get('season_year')}" if field.get("season_year") else None,
            ]
            st.caption(" · ".join(bit for bit in source_bits if bit) or "Mapped field context")
        else:
            st.info("Select a mapped field in the workspace context to connect climate, EO, sensors and Twin evidence automatically.")

        status_rows = [
            ("Weather", w_status, w_tone, weather_latest, "Retrieved / persisted field weather"),
            ("Sentinel-2", e_status, e_tone, eo_latest, "EO-derived field observation"),
            ("Root zone", r_status, r_tone, root_latest, "Modelled water state"),
            ("Sensors", s_status, s_tone, sensor_latest, "Measured field observations"),
        ]
        for name, status, tone, latest, source in status_rows:
            cols = st.columns([1.5, 1, 2.8])
            cols[0].markdown(f"**{_tone_icon(tone)} {name}**")
            cols[1].markdown(f"**{status}**")
            cols[2].caption(f"{source} · latest {latest if latest is not None else 'not available'}")

    st.markdown("### Research actions")
    actions = st.columns(5)
    if actions[0].button("Update NASA weather", type="primary", width="stretch", key="climate10_quick_weather"):
        if not field:
            st.warning("Select a mapped field before retrieving field weather.")
        elif quick_update_weather is None:
            st.info("Quick weather update is unavailable in this runtime; open the Research Data Hub instead.")
        else:
            try:
                result = quick_update_weather(field)
                if result:
                    st.success(f"Weather updated through {result.get('end_date')}; {result.get('rows', 0):,} daily row(s).")
            except Exception as error:
                st.error(f"Field weather update failed: {type(error).__name__}: {error}")
    if actions[1].button("Update field EO", width="stretch", key="climate10_open_eo"):
        if _preload_field_for_satellite(field or None):
            queue_view_request(
                st.session_state,
                request_key="release11_10_climate_command_view_request",
                target="Earth Observation",
            )
            st.rerun()
        else:
            st.warning("Select a mapped field before preloading an EO analysis area.")
    if actions[2].button("Research Data Hub", width="stretch", key="climate10_open_data_hub"):
        if open_destination:
            open_destination("settings", "Research Data Hub")
    if actions[3].button("Open Twin", width="stretch", key="climate10_open_twin"):
        if open_destination:
            open_destination("twin", None)
    if actions[4].button("Open field", width="stretch", key="climate10_open_field"):
        if open_destination:
            open_destination("fields", None)

    st.markdown("### Installed environmental data")
    metrics = st.columns(5)
    metrics[0].metric("Country dataset", country)
    metrics[1].metric("Climate rows", f"{int(runtime_summary.get('rows') or 0):,}")
    metrics[2].metric("Locations", f"{int(dataset_status.get('locations') or 0):,}")
    metrics[3].metric("Variables", f"{int(runtime_summary.get('variables') or 0):,} / 19")
    years = dataset_status.get("years") or []
    metrics[4].metric("Historical coverage", f"{min(years)}–{max(years)}" if years else "Not installed")
    st.caption(
        "Overview reads saved summaries only. It does not call NASA POWER, search STAC catalogues, run climate similarity, fit models or process imagery on page entry."
    )


def _location_subset(climate_frame: pd.DataFrame, city: str, state: str, country: str, signature: Any) -> pd.DataFrame:
    key = f"climate10_location_cache::{country}::{signature}::{city}::{state}"
    cached = st.session_state.get(key)
    if isinstance(cached, pd.DataFrame):
        return cached
    prefix = "climate10_location_cache::"
    stale_keys = [k for k in st.session_state.keys() if str(k).startswith(prefix) and f"::{signature}::" not in str(k)]
    for stale in stale_keys[:20]:
        st.session_state.pop(stale, None)
    subset = climate_frame.loc[
        climate_frame["CITY"].eq(str(city)) & climate_frame["STATE"].eq(str(state)),
        [column for column in ["CITY", "STATE", "Year", "Month", "Variable", "Value"] if column in climate_frame],
    ].copy()
    st.session_state[key] = subset
    return subset


def _render_field_climate(
    *, climate_frame: pd.DataFrame, locations: pd.DataFrame, snapshot: Mapping[str, Any], country: str,
    available_variables: list[str], years: list[int], runtime_summary: Mapping[str, Any],
) -> None:
    st.markdown("### 19-variable Field Climate Explorer")
    st.caption(
        "Explore the installed canonical agroclimate history without uploading a CSV. When a mapped field is active, the nearest installed climate location is offered as the default reference; this is gridded/location climate evidence, not an on-field weather-station measurement."
    )
    if climate_frame is None or climate_frame.empty or not years:
        st.warning(f"No installed historical climate dataset is available for {country}. Use Data & Settings → Dataset updater.")
        return

    field = snapshot.get("field") or None
    nearest = _nearest_location(field, locations)
    labels = locations["Location"].astype(str).tolist() if "Location" in locations else []
    default_index = 0
    if nearest and labels:
        nearest_label = str(nearest.get("Location") or f"{nearest.get('CITY')} ({nearest.get('STATE')})")
        if nearest_label in labels:
            default_index = labels.index(nearest_label)
    selected_label = st.selectbox("Climate reference", labels, index=default_index, key="climate10_field_reference")
    selected = locations.loc[locations["Location"].astype(str).eq(selected_label)].iloc[0]
    city, state = str(selected["CITY"]), str(selected["STATE"])
    if field and nearest:
        st.caption(f"Nearest installed reference to the mapped field centroid: **{nearest.get('Location')}**, approximately {nearest.get('distance_km', float('nan')):.1f} km away.")

    subset = _location_subset(climate_frame, city, state, country, runtime_summary.get("source_mtime_ns"))
    if subset.empty:
        st.warning("The selected location has no installed climate rows.")
        return

    controls = st.columns([1.25, 1.65, 1.0])
    group = controls[0].selectbox("Variable family", list(VARIABLE_GROUPS), key="climate10_variable_group")
    group_vars = [v for v in VARIABLE_GROUPS[group] if v in available_variables]
    if not group_vars:
        group_vars = [v for v in available_variables if v in subset["Variable"].unique().tolist()]
    variable = controls[1].selectbox(
        "Variable",
        group_vars,
        format_func=lambda value: f"{VARIABLE_LABELS.get(value, value.replace('_', ' ').title())} · {VARIABLE_UNITS.get(value, 'dataset-native unit')}",
        key="climate10_variable",
    )
    available_years = sorted(pd.to_numeric(subset["Year"], errors="coerce").dropna().astype(int).unique().tolist())
    default_year = available_years[-1]
    selected_year = controls[2].selectbox("Highlight year", available_years, index=len(available_years) - 1, key="climate10_highlight_year")

    data = subset.loc[subset["Variable"].astype(str).eq(variable)].copy()
    data["Year"] = pd.to_numeric(data["Year"], errors="coerce")
    data["Value"] = pd.to_numeric(data["Value"], errors="coerce")
    data["Month"] = data["Month"].astype(str).str.upper()
    data = data.dropna(subset=["Year", "Value"]).copy()
    data["Year"] = data["Year"].astype(int)
    data["Month order"] = data["Month"].map({m: i + 1 for i, m in enumerate(MONTH_ORDER)})
    data["Month label"] = data["Month"].map(MONTH_SHORT)

    selected_year_frame = data.loc[data["Year"].eq(int(selected_year))].sort_values("Month order")
    climatology = data.groupby(["Month", "Month order"], dropna=False)["Value"].agg(["mean", "std", "count"]).reset_index().sort_values("Month order")
    climatology["Month label"] = climatology["Month"].map(MONTH_SHORT)
    merged = climatology.merge(selected_year_frame[["Month", "Value"]].rename(columns={"Value": "Selected year"}), on="Month", how="left")

    left, right = st.columns([1.55, 1.0])
    with left:
        figure = go.Figure()
        figure.add_trace(go.Scatter(x=merged["Month label"], y=merged["mean"], mode="lines+markers", name="Long-term mean"))
        figure.add_trace(go.Scatter(x=merged["Month label"], y=merged["Selected year"], mode="lines+markers", name=str(selected_year)))
        if merged["std"].notna().any():
            upper = merged["mean"] + merged["std"]
            lower = merged["mean"] - merged["std"]
            figure.add_trace(go.Scatter(x=merged["Month label"], y=upper, mode="lines", line={"width": 0}, showlegend=False, hoverinfo="skip"))
            figure.add_trace(go.Scatter(x=merged["Month label"], y=lower, mode="lines", fill="tonexty", line={"width": 0}, name="±1 SD", hoverinfo="skip"))
        figure.update_layout(title=f"{VARIABLE_LABELS.get(variable, variable)} · {city}", yaxis_title=VARIABLE_UNITS.get(variable, "Dataset-native unit"), xaxis_title="Month")
        st.plotly_chart(figure, width="stretch")
    with right:
        annual = data.groupby("Year", as_index=False)["Value"].mean().rename(columns={"Value": "Annual mean"})
        st.plotly_chart(px.line(annual, x="Year", y="Annual mean", markers=True, title="Annual mean trajectory"), width="stretch")

    heatmap = data.pivot_table(index="Year", columns="Month order", values="Value", aggfunc="mean").sort_index()
    if not heatmap.empty:
        heatmap = heatmap.reindex(columns=range(1, 13))
        fig = px.imshow(
            heatmap,
            aspect="auto",
            labels={"x": "Month", "y": "Year", "color": VARIABLE_UNITS.get(variable, "Value")},
            x=[MONTH_SHORT[m] for m in MONTH_ORDER],
            y=heatmap.index.astype(str),
            title="Year × month climate history",
        )
        st.plotly_chart(fig, width="stretch")

    coverage = (
        subset.groupby("Variable", dropna=False)
        .agg(Rows=("Value", "size"), Years=("Year", "nunique"), Months=("Month", "nunique"), Missing=("Value", lambda s: int(pd.to_numeric(s, errors="coerce").isna().sum())))
        .reset_index()
    )
    coverage["Label"] = coverage["Variable"].map(lambda v: VARIABLE_LABELS.get(str(v), str(v).replace("_", " ").title()))
    coverage["Unit"] = coverage["Variable"].map(lambda v: VARIABLE_UNITS.get(str(v), "dataset-native unit"))
    with st.expander("Data coverage & provenance", expanded=False):
        st.dataframe(coverage[["Label", "Variable", "Unit", "Years", "Months", "Rows", "Missing"]], hide_index=True, width="stretch")
        st.caption("Source: installed AGROLATTICE country agroclimate dataset. Spatial support is the selected installed location/grid representation; it should not be described as an on-field measurement unless independently validated against local observations.")

    sensors = snapshot.get("sensors")
    readings = snapshot.get("readings")
    if isinstance(sensors, pd.DataFrame) and not sensors.empty:
        st.markdown("### Local field observations")
        st.caption("Sensor observations are shown alongside the gridded climate reference, not silently merged with it.")
        latest_rows = []
        if isinstance(readings, pd.DataFrame) and not readings.empty:
            work = readings.copy()
            work["timestamp"] = pd.to_datetime(work["timestamp"], errors="coerce", utc=True)
            work = work.sort_values("timestamp")
            latest_rows = work.groupby("sensor_id", as_index=False).tail(1).to_dict(orient="records")
        if latest_rows:
            display = pd.DataFrame(latest_rows)
            columns = [c for c in ["sensor_name", "sensor_type", "value", "unit", "depth_cm", "timestamp", "quality_flag", "source"] if c in display]
            st.dataframe(display[columns], hide_index=True, width="stretch")
        else:
            st.info("Sensors are registered for this field but no readings are available yet.")


def _render_earth_observation(
    *, snapshot: Mapping[str, Any], satellite_page: Callable[[], None], open_destination: Callable[[str, str | None], None] | None,
    quick_update_eo: Callable[[Mapping[str, Any]], Mapping[str, Any] | None] | None = None,
) -> None:
    field = snapshot.get("field") or None
    st.markdown("### Earth Observation Command Centre")
    st.caption("Use the authoritative mapped field polygon automatically when available. Catalogue search and scene processing remain explicit actions so opening the workspace stays fast.")
    if field:
        with st.container(border=True):
            cols = st.columns([2.3, 1, 1, 1])
            cols[0].markdown(f"**{field.get('farm_name') or 'Research centre'} → {field.get('name') or 'Mapped field'}**")
            cols[0].caption(f"{float(field.get('area_ha') or 0):.2f} ha · {field.get('crop') or 'crop not recorded'} · season {field.get('season_year') or 'not recorded'}")
            if cols[1].button("Use mapped field", width="stretch", key="climate10_use_field_eo"):
                _preload_field_for_satellite(field)
                st.rerun()
            if cols[2].button("Quick update EO", type="primary", width="stretch", key="climate10_quick_update_eo"):
                if quick_update_eo is None:
                    st.info("Quick update is unavailable in this runtime; use the full Sentinel-2 workflow below.")
                else:
                    try:
                        result = quick_update_eo(field)
                        if result:
                            st.success(f"EO update complete: {result.get('usable_rows', result.get('rows', 0))} usable scene(s), latest {result.get('end_date') or 'date not recorded'}.")
                    except Exception as error:
                        st.error(f"Quick EO update failed: {type(error).__name__}: {error}")
            if cols[3].button("Open Twin", width="stretch", key="climate10_eo_open_twin") and open_destination:
                open_destination("twin", None)
        _preload_field_for_satellite(field)
    else:
        st.info("No mapped field is active. Satellite Monitoring will offer city buffers, custom coordinates, GeoJSON upload and interactive drawing.")

    eo_record = snapshot.get("satellite_record") or snapshot.get("eo_acquisition")
    if eo_record:
        latest = _record_date(eo_record, ("end_date", "period_end", "updated_at", "created_at"))
        st.success(f"Saved field-linked EO evidence is available through {latest or 'an unspecified date'}.")
    else:
        st.warning("No persisted field-linked EO evidence was found for this active field yet.")

    st.divider()
    satellite_page()


def _save_session_analysis_bundle(*, registry: Any, artifact_dir: Path, field: Mapping[str, Any] | None, country: str) -> tuple[str, Path] | None:
    keys = {
        "climate_similarity": st.session_state.get("similarity_results"),
        "climate_analogue_results": st.session_state.get("analogue_results"),
        "climate_analogue_changes": st.session_state.get("analogue_change_table"),
        "climate_trends": st.session_state.get("trend_results"),
        "climate_anomalies": st.session_state.get("anomaly_results"),
        "climate_variability": st.session_state.get("variability_results"),
        "satellite_time_series": st.session_state.get("satellite_time_series"),
        "satellite_processing_config": st.session_state.get("satellite_processing_config"),
        "satellite_stage_summary": st.session_state.get("satellite_stage_summary"),
    }
    available = {name: value for name, value in keys.items() if value is not None and not (isinstance(value, pd.DataFrame) and value.empty)}
    if not available:
        return None
    snapshot_id = uuid.uuid4().hex
    folder = Path(artifact_dir) / "climate_earth_observation"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"climate_eo_snapshot_{snapshot_id}.json"
    payload = {
        "snapshot_id": snapshot_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "country": country,
        "field": {k: _json_safe(v) for k, v in (field or {}).items() if k not in {"geometry_json", "geometry"}},
        "analyses": {name: _json_safe(value) for name, value in available.items()},
        "scientific_note": "Session analyses are persisted for provenance. Their interpretation remains subject to the method-specific assumptions and validation limits shown in AGROLATTICE.",
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    dataset_id = registry.register_dataset({
        "name": f"Climate & EO analysis snapshot · {field.get('name') if field else country}",
        "dataset_type": "Climate / Earth observation evidence snapshot",
        "source": "AGROLATTICE 11.10 Climate & EO Command Centre",
        "source_version": MODULE_VERSION,
        "local_path": str(path),
        "crop_scope": field.get("crop") if field else None,
        "geography_scope": field.get("name") if field else country,
        "spatial_resolution": "Mixed; preserved in source analysis metadata",
        "temporal_resolution": "Mixed",
        "provenance": {"country": country, "field_id": field.get("field_id") if field else None, "analyses": list(available)},
        "notes": "Persisted user-approved analysis snapshot. It does not convert climate similarity, EO indices or heuristic risk scores into causal or field-validated agronomic evidence.",
    })
    registry.save_data_acquisition({
        "dataset_id": dataset_id,
        "source": "AGROLATTICE Climate & EO Command Centre",
        "source_type": "Saved analysis snapshot",
        "field_id": field.get("field_id") if field else None,
        "latitude": field.get("centroid_lat") if field else None,
        "longitude": field.get("centroid_lon") if field else None,
        "variables": list(available),
        "request": {"action": "Persist session climate/EO analyses"},
        "provenance": {"artifact": str(path), "module_version": MODULE_VERSION},
        "row_count": 1,
        "status": "Completed",
    })
    return dataset_id, path


def _render_evidence_data(
    *, snapshot: Mapping[str, Any], registry: Any, artifact_dir: Path, country: str,
    dataset_status: Mapping[str, Any], runtime_summary: Mapping[str, Any], open_destination: Callable[[str, str | None], None] | None,
) -> None:
    field = snapshot.get("field") or None
    st.markdown("### Evidence & Data")
    st.caption("Keep source, spatial support, temporal support and measured/modelled status visible. Raw technical metadata remain available without dominating normal research use.")

    cards = st.columns(4)
    cards[0].metric("Installed climate rows", f"{int(runtime_summary.get('rows') or 0):,}")
    cards[1].metric("Canonical variables", f"{int(runtime_summary.get('variables') or 0)} / 19")
    acquisitions = snapshot.get("acquisitions")
    cards[2].metric("Field-linked acquisitions", f"{len(acquisitions):,}" if isinstance(acquisitions, pd.DataFrame) else "0")
    cards[3].metric("Runtime strategy", str(runtime_summary.get("cache_strategy") or "process-local cache"))

    st.markdown("#### Field-linked provenance")
    if isinstance(acquisitions, pd.DataFrame) and not acquisitions.empty:
        display = acquisitions.copy()
        for column in ("variables_json", "request_json", "provenance_json"):
            if column in display:
                display[column] = display[column].astype(str).str.slice(0, 180)
        columns = [c for c in ["created_at", "source", "source_type", "period_start", "period_end", "temporal_resolution", "row_count", "status", "variables_json"] if c in display]
        st.dataframe(display[columns], hide_index=True, width="stretch")
    else:
        st.info("No Research Evidence acquisitions are linked to the active field yet.")

    twin_rows = []
    for label, record, evidence in [
        ("Twin weather", snapshot.get("weather_record"), "Retrieved / derived"),
        ("Twin satellite", snapshot.get("satellite_record"), "EO-derived"),
        ("Twin root zone", snapshot.get("root_zone_record"), "Modelled"),
    ]:
        if record:
            twin_rows.append({"Source": label, "Evidence class": evidence, "Start": record.get("start_date"), "End": record.get("end_date"), "Updated": record.get("updated_at"), "Provider/source": record.get("source")})
    if twin_rows:
        st.markdown("#### Persistent Twin environmental attachments")
        st.dataframe(pd.DataFrame(twin_rows), hide_index=True, width="stretch")

    st.markdown("#### Persist current climate / EO analyses")
    st.caption("Similarity, analogue, trend, anomaly and satellite results often begin as session analyses. Save a provenance snapshot when a result becomes part of a research record.")
    if st.button("Save current climate / EO evidence snapshot", type="primary", width="stretch", key="climate10_save_snapshot"):
        try:
            saved = _save_session_analysis_bundle(registry=registry, artifact_dir=artifact_dir, field=field, country=country)
            if saved is None:
                st.warning("No climate or EO analysis result is currently available in this session to save.")
            else:
                _, path = saved
                st.success(f"Evidence snapshot saved and registered: {path.name}")
        except Exception as error:
            st.error(f"Could not save the evidence snapshot: {type(error).__name__}: {error}")

    buttons = st.columns(3)
    if buttons[0].button("Open Research Data Hub", width="stretch", key="climate10_evidence_datahub") and open_destination:
        open_destination("settings", "Research Data Hub")
    if buttons[1].button("Open Research Registry", width="stretch", key="climate10_evidence_registry") and open_destination:
        open_destination("evidence", "Research Model & Evidence Registry")
    if buttons[2].button("Dataset updater", width="stretch", key="climate10_evidence_updater") and open_destination:
        open_destination("settings", "Dataset updater")

    with st.expander("Installed dataset technical summary", expanded=False):
        st.json({"dataset_status": _json_safe(dataset_status), "runtime": _json_safe(runtime_summary)})


def render_climate_earth_command_centre(
    *,
    climate_frame: pd.DataFrame,
    locations: pd.DataFrame,
    country: str,
    available_variables: list[str],
    years: list[int],
    dataset_status: Mapping[str, Any],
    runtime_summary: Mapping[str, Any],
    field_db: Any,
    twin_db: Any,
    registry: Any,
    artifact_dir: str | Path,
    active_field_id: str | None,
    context: Mapping[str, Any],
    comparison_page: Callable[[], None],
    spatial_page: Callable[[], None],
    risk_page: Callable[[], None],
    satellite_page: Callable[[], None],
    open_destination: Callable[[str, str | None], None] | None = None,
    quick_update_weather: Callable[[Mapping[str, Any]], Mapping[str, Any] | None] | None = None,
    quick_update_eo: Callable[[Mapping[str, Any]], Mapping[str, Any] | None] | None = None,
) -> None:
    """Render the consolidated 11.10 Climate & EO workspace."""
    snapshot = _environment_snapshot(
        field_db=field_db,
        twin_db=twin_db,
        registry=registry,
        active_field_id=str(active_field_id) if active_field_id else None,
    )
    field = snapshot.get("field") or None

    st.caption(_active_context_caption(field, country, context))
    options = [
        "Overview",
        "Field Climate",
        "Climate Comparison",
        "Climate Zones & Transferability",
        "Climate Risk",
        "Earth Observation",
        "Evidence & Data",
    ]
    view = _choose_view(options)
    st.divider()

    if view == "Overview":
        _render_overview(
            snapshot=snapshot,
            country=country,
            context=context,
            dataset_status=dataset_status,
            runtime_summary=runtime_summary,
            open_destination=open_destination,
            quick_update_weather=quick_update_weather,
        )
    elif view == "Field Climate":
        _render_field_climate(
            climate_frame=climate_frame,
            locations=locations,
            snapshot=snapshot,
            country=country,
            available_variables=available_variables,
            years=years,
            runtime_summary=runtime_summary,
        )
    elif view == "Climate Comparison":
        st.info("Research workflow: choose the reference environment and period → define variables / crop profile → inspect similarity → explain the match → test robustness → save important results under Evidence & Data.")
        comparison_page()
    elif view == "Climate Zones & Transferability":
        st.info(
            "Discover recurring climate environments, see where they occur, and examine whether a field or trial site "
            "falls inside climate space represented elsewhere. These groups support environmental comparison; they are "
            "not official agroecological zones."
        )
        spatial_page()
    elif view == "Climate Risk":
        crop = field.get("crop") if field else context.get("Crop")
        season = field.get("season_year") if field else context.get("Season")
        st.info(f"Risk context: crop **{crop or 'not selected'}**, season **{season or 'not selected'}**. Keep hazard exposure separate from inferred crop consequence unless a validated response model supports that consequence.")
        risk_page()
    elif view == "Earth Observation":
        _render_earth_observation(snapshot=snapshot, satellite_page=satellite_page, open_destination=open_destination, quick_update_eo=quick_update_eo)
    else:
        _render_evidence_data(
            snapshot=snapshot,
            registry=registry,
            artifact_dir=Path(artifact_dir),
            country=country,
            dataset_status=dataset_status,
            runtime_summary=runtime_summary,
            open_destination=open_destination,
        )
