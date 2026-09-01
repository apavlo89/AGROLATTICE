"""Current-season monitoring summaries for persistent agroclimate projects."""
from __future__ import annotations

from datetime import date
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

MODULE_VERSION = "1.0.0"


class LiveMonitorError(RuntimeError):
    """Raised when the live monitor cannot produce a defensible status."""


def current_stage(schedule: pd.DataFrame | None, as_of: date | str | pd.Timestamp) -> dict[str, Any]:
    timestamp = pd.Timestamp(as_of)
    if not isinstance(schedule, pd.DataFrame) or schedule.empty:
        return {"stage": None, "status": "No phenology schedule", "progress_percent": None}
    frame = schedule.copy()
    start_column = next((c for c in frame.columns if str(c).casefold() == "start date"), None)
    end_column = next((c for c in frame.columns if str(c).casefold() == "end date"), None)
    stage_column = next((c for c in frame.columns if str(c).casefold() == "stage"), None)
    if not all([start_column, end_column, stage_column]):
        return {"stage": None, "status": "Schedule columns unavailable", "progress_percent": None}
    frame["_start"] = pd.to_datetime(frame[start_column], errors="coerce")
    frame["_end"] = pd.to_datetime(frame[end_column], errors="coerce")
    active = frame[frame["_start"].le(timestamp) & frame["_end"].ge(timestamp)]
    if active.empty:
        if timestamp < frame["_start"].min():
            return {"stage": "Pre-planting", "status": "Season has not started", "progress_percent": 0.0}
        return {"stage": "Post-season", "status": "Expected crop cycle has ended", "progress_percent": 100.0}
    row = active.iloc[0]
    duration = max(1, int((row["_end"] - row["_start"]).days) + 1)
    elapsed = max(0, int((timestamp - row["_start"]).days) + 1)
    return {
        "stage": str(row[stage_column]),
        "status": "Active",
        "stage_start": row["_start"].date().isoformat(),
        "stage_end": row["_end"].date().isoformat(),
        "progress_percent": float(np.clip(100.0 * elapsed / duration, 0.0, 100.0)),
    }


def latest_satellite_observation(time_series: pd.DataFrame | None) -> dict[str, Any]:
    if not isinstance(time_series, pd.DataFrame) or time_series.empty:
        return {"available": False, "reason": "No processed satellite time series"}
    frame = time_series.copy()
    date_column = next((c for c in frame.columns if str(c).casefold() in {"date", "acquisition date"}), None)
    if date_column is None:
        return {"available": False, "reason": "Satellite date column unavailable"}
    frame["_date"] = pd.to_datetime(frame[date_column], errors="coerce")
    frame = frame.dropna(subset=["_date"]).sort_values("_date")
    if frame.empty:
        return {"available": False, "reason": "No dated satellite observations"}
    row = frame.iloc[-1]
    output: dict[str, Any] = {
        "available": True,
        "date": row["_date"].date().isoformat(),
        "age_days": int((pd.Timestamp(date.today()) - row["_date"].normalize()).days),
    }
    for index_name in ("NDVI", "EVI", "NDMI", "NDRE"):
        candidates = [c for c in frame.columns if index_name in str(c).upper() and "MEAN" in str(c).upper()]
        if not candidates:
            candidates = [c for c in frame.columns if str(c).upper() == index_name]
        if candidates:
            value = pd.to_numeric(pd.Series([row[candidates[0]]]), errors="coerce").iloc[0]
            output[index_name] = float(value) if pd.notna(value) else None
    clear_candidates = [c for c in frame.columns if "CLEAR" in str(c).upper() and "%" in str(c)]
    if clear_candidates:
        value = pd.to_numeric(pd.Series([row[clear_candidates[0]]]), errors="coerce").iloc[0]
        output["clear_percent"] = float(value) if pd.notna(value) else None
    return output


def weather_to_date_summary(weather: pd.DataFrame | None, planting_date: str | date) -> dict[str, Any]:
    if not isinstance(weather, pd.DataFrame) or weather.empty:
        return {"available": False, "reason": "No current daily weather"}
    frame = weather.copy()
    date_column = "DATE" if "DATE" in frame.columns else "Date" if "Date" in frame.columns else None
    if date_column is None:
        return {"available": False, "reason": "Weather date column unavailable"}
    frame["_date"] = pd.to_datetime(frame[date_column], errors="coerce")
    start = pd.Timestamp(planting_date)
    frame = frame[frame["_date"].ge(start)].copy()
    if frame.empty:
        return {"available": False, "reason": "No weather since planting"}
    def series(candidates: Sequence[str]) -> pd.Series:
        for candidate in candidates:
            if candidate in frame.columns:
                return pd.to_numeric(frame[candidate], errors="coerce")
        return pd.Series(np.nan, index=frame.index)
    rain = series(["PRECTOTCORR", "PRECIP_MM", "Precipitation (mm)"])
    gdd = series(["GDD_DAILY"])
    tmax = series(["T2M_MAX", "TMAX_C"])
    eto = series(["ETo (mm)", "ETO_MM", "ReferenceET"])
    return {
        "available": True,
        "first_date": frame["_date"].min().date().isoformat(),
        "last_date": frame["_date"].max().date().isoformat(),
        "days": int(frame["_date"].nunique()),
        "rainfall_mm": float(rain.sum(min_count=1)) if rain.notna().any() else None,
        "gdd": float(gdd.sum(min_count=1)) if gdd.notna().any() else None,
        "maximum_temperature_c": float(tmax.max()) if tmax.notna().any() else None,
        "reference_et_mm": float(eto.sum(min_count=1)) if eto.notna().any() else None,
        "last_weather_age_days": int((pd.Timestamp(date.today()) - frame["_date"].max().normalize()).days),
    }


def root_zone_status(balance: pd.DataFrame | None) -> dict[str, Any]:
    if not isinstance(balance, pd.DataFrame) or balance.empty:
        return {"available": False, "reason": "No Module B root-zone simulation"}
    frame = balance.copy()
    date_column = "DATE" if "DATE" in frame.columns else "Date" if "Date" in frame.columns else None
    if date_column:
        frame["_date"] = pd.to_datetime(frame[date_column], errors="coerce")
        frame = frame.sort_values("_date")
    row = frame.iloc[-1]
    def first_value(candidates: Sequence[str]) -> float | None:
        for candidate in candidates:
            if candidate in frame.columns:
                value = pd.to_numeric(pd.Series([row[candidate]]), errors="coerce").iloc[0]
                return float(value) if pd.notna(value) else None
        return None
    depletion = first_value(["Root-zone depletion (mm)", "Dr end (mm)", "Depletion (mm)"])
    taw = first_value(["TAW (mm)"])
    raw = first_value(["RAW (mm)"])
    ks = first_value(["Ks", "Water stress coefficient"])
    relative = None
    if depletion is not None and taw not in (None, 0):
        relative = 100.0 * depletion / taw
    return {
        "available": True,
        "date": row.get("_date").date().isoformat() if date_column and pd.notna(row.get("_date")) else None,
        "depletion_mm": depletion,
        "taw_mm": taw,
        "raw_mm": raw,
        "relative_depletion_percent": relative,
        "ks": ks,
        "stress_active": bool(ks is not None and ks < 0.999) if ks is not None else None,
    }


def generate_alerts(
    *,
    stage: Mapping[str, Any],
    weather: Mapping[str, Any],
    root_zone: Mapping[str, Any],
    satellite: Mapping[str, Any],
    heat_threshold_c: float,
    satellite_stale_days: int = 20,
) -> list[dict[str, str]]:
    alerts: list[dict[str, str]] = []
    if weather.get("available"):
        age = weather.get("last_weather_age_days")
        if age is not None and age > 3:
            alerts.append({"level": "warning", "title": "Weather is stale", "message": f"Latest daily weather is {age} days old."})
        maximum = weather.get("maximum_temperature_c")
        if maximum is not None and maximum >= heat_threshold_c:
            alerts.append({"level": "warning", "title": "Heat threshold exceeded", "message": f"Maximum temperature since planting reached {maximum:.1f} °C."})
    else:
        alerts.append({"level": "info", "title": "Weather layer unavailable", "message": str(weather.get("reason"))})
    if root_zone.get("available"):
        if root_zone.get("stress_active"):
            alerts.append({"level": "error", "title": "Modelled root-zone stress", "message": f"Latest water-stress coefficient Ks is {root_zone.get('ks'):.2f}."})
        relative = root_zone.get("relative_depletion_percent")
        if relative is not None and relative >= 80:
            alerts.append({"level": "error", "title": "High root-zone depletion", "message": f"Modelled depletion is {relative:.0f}% of total available water."})
    else:
        alerts.append({"level": "info", "title": "Root-zone layer unavailable", "message": str(root_zone.get("reason"))})
    if satellite.get("available"):
        age = satellite.get("age_days")
        if age is not None and age > satellite_stale_days:
            alerts.append({"level": "warning", "title": "Satellite observation is stale", "message": f"Latest usable image is {age} days old."})
    else:
        alerts.append({"level": "info", "title": "Satellite layer unavailable", "message": str(satellite.get("reason"))})
    if stage.get("stage") == "Post-season":
        alerts.append({"level": "info", "title": "Expected season completed", "message": "The project crop cycle has passed its expected end date."})
    if not alerts:
        alerts.append({"level": "success", "title": "No configured alerts", "message": "No current threshold condition was triggered."})
    return alerts


def build_live_snapshot(
    *,
    project: Mapping[str, Any],
    schedule: pd.DataFrame | None,
    weather: pd.DataFrame | None,
    root_zone_balance: pd.DataFrame | None,
    satellite_time_series: pd.DataFrame | None,
    heat_threshold_c: float = 35.0,
    as_of: date | None = None,
) -> dict[str, Any]:
    as_of = as_of or date.today()
    planting = (project.get("season", {}) or {}).get("planting_date")
    if not planting:
        raise LiveMonitorError("The active project has no planting date.")
    stage_status = current_stage(schedule, as_of)
    weather_status = weather_to_date_summary(weather, planting)
    root_status = root_zone_status(root_zone_balance)
    satellite_status = latest_satellite_observation(satellite_time_series)
    alerts = generate_alerts(
        stage=stage_status,
        weather=weather_status,
        root_zone=root_status,
        satellite=satellite_status,
        heat_threshold_c=float(heat_threshold_c),
    )
    return {
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "as_of": str(as_of),
        "project_id": project.get("project_id"),
        "project_name": project.get("name"),
        "stage": stage_status,
        "weather": weather_status,
        "root_zone": root_status,
        "satellite": satellite_status,
        "alerts": alerts,
    }
