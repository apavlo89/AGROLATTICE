"""Lightweight Home-page research command-centre logic for AGROLATTICE 11.7.

The module contains only small, deterministic transformations of already-persisted
metadata.  It deliberately does not fetch NASA POWER, query STAC, read the large
country climate CSV, train models, or run the Twin.  Home must remain fast.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

MODULE_VERSION = "1.0.0"

CLOSED_TASK_STATUSES = {"completed", "cancelled", "closed"}
CLOSED_ALERT_STATUSES = {"resolved", "closed"}
CLOSED_RECOMMENDATION_STATUSES = {"rejected", "completed", "superseded", "cancelled"}


def _timestamp(value: Any) -> pd.Timestamp | None:
    if value in (None, ""):
        return None
    try:
        result = pd.to_datetime(value, errors="coerce", utc=True)
    except Exception:
        return None
    if isinstance(result, pd.DatetimeIndex):
        return None
    if pd.isna(result):
        return None
    return pd.Timestamp(result)


def age_days(value: Any, *, now: Any | None = None) -> float | None:
    stamp = _timestamp(value)
    reference = _timestamp(now) if now is not None else pd.Timestamp.now(tz="UTC")
    if stamp is None or reference is None:
        return None
    return max(0.0, float((reference - stamp).total_seconds() / 86400.0))


def freshness_status(
    name: str,
    latest: Any,
    *,
    fresh_days: float,
    warn_days: float,
    now: Any | None = None,
    source: str = "",
    missing_detail: str = "No persistent data are attached.",
) -> dict[str, Any]:
    age = age_days(latest, now=now)
    if age is None:
        return {
            "name": name,
            "status": "Missing",
            "tone": "bad",
            "latest": None,
            "age_days": None,
            "detail": missing_detail,
            "source": source,
        }
    if age <= fresh_days:
        status, tone = "Current", "good"
    elif age <= warn_days:
        status, tone = "Review", "warn"
    else:
        status, tone = "Stale", "bad"
    stamp = _timestamp(latest)
    return {
        "name": name,
        "status": status,
        "tone": tone,
        "latest": stamp.date().isoformat() if stamp is not None else str(latest),
        "age_days": age,
        "detail": f"Latest {name.casefold()} record is {age:.0f} day(s) old.",
        "source": source,
    }


def _status_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if frame is None or frame.empty or column not in frame:
        return pd.Series(dtype=str)
    return frame[column].astype(str).str.strip().str.casefold()


def open_task_summary(tasks: pd.DataFrame, *, now: Any | None = None) -> dict[str, int]:
    if tasks is None or tasks.empty:
        return {"open": 0, "overdue": 0, "due_soon": 0}
    status = _status_series(tasks, "status")
    open_mask = ~status.isin(CLOSED_TASK_STATUSES) if not status.empty else pd.Series(True, index=tasks.index)
    due = pd.to_datetime(tasks.get("due_date"), errors="coerce", utc=True)
    reference = _timestamp(now) if now is not None else pd.Timestamp.now(tz="UTC")
    if reference is None:
        reference = pd.Timestamp.now(tz="UTC")
    overdue = int((open_mask & due.notna() & due.lt(reference.normalize())).sum())
    due_soon = int((open_mask & due.notna() & due.ge(reference.normalize()) & due.le(reference.normalize() + pd.Timedelta(days=7))).sum())
    return {"open": int(open_mask.sum()), "overdue": overdue, "due_soon": due_soon}


def open_alert_count(alerts: pd.DataFrame) -> int:
    if alerts is None or alerts.empty:
        return 0
    status = _status_series(alerts, "status")
    return int((~status.isin(CLOSED_ALERT_STATUSES)).sum()) if not status.empty else int(len(alerts))


def latest_date(frame: pd.DataFrame | None, candidates: Sequence[str]) -> Any:
    if frame is None or frame.empty:
        return None
    for column in candidates:
        if column in frame:
            values = pd.to_datetime(frame[column], errors="coerce", utc=True).dropna()
            if not values.empty:
                return values.max()
    return None


def _action(priority: int, title: str, detail: str, page: str, *, tool: str | None = None, kind: str = "Research") -> dict[str, Any]:
    return {
        "priority": int(priority),
        "title": title,
        "detail": detail,
        "page": page,
        "tool": tool,
        "kind": kind,
    }


def build_priority_actions(
    *,
    dataset_ready: bool,
    has_context: bool,
    field_name: str | None,
    tasks: pd.DataFrame | None,
    alerts: pd.DataFrame | None,
    freshness: Sequence[Mapping[str, Any]],
    trial_status: str | None = None,
    trial_observations: pd.DataFrame | None = None,
    latest_model: Mapping[str, Any] | None = None,
    latest_prediction: Mapping[str, Any] | None = None,
    recommendations: pd.DataFrame | None = None,
    treatment_outcomes: pd.DataFrame | None = None,
    twin_state: Mapping[str, Any] | None = None,
    now: Any | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    task_summary = open_task_summary(tasks if isinstance(tasks, pd.DataFrame) else pd.DataFrame(), now=now)
    alert_count = open_alert_count(alerts if isinstance(alerts, pd.DataFrame) else pd.DataFrame())

    if not dataset_ready:
        actions.append(_action(100, "Install or update the country climate dataset", "Historical climate analyses need the selected country's canonical 19-variable dataset.", "settings", tool="Dataset updater", kind="Data"))
    if not has_context:
        actions.append(_action(95, "Select a field, project or trial", "Home becomes field- and season-aware once a research context is active.", "fields", kind="Context"))
    if task_summary["overdue"]:
        actions.append(_action(92, f"Review {task_summary['overdue']} overdue field task(s)", f"{field_name or 'The active workspace'} has work whose due date has passed.", "fields", tool="Tasks, scouting & operations", kind="Operations"))
    elif task_summary["due_soon"]:
        actions.append(_action(72, f"Prepare for {task_summary['due_soon']} task(s) due within 7 days", "Review upcoming sampling, scouting or management work before it becomes overdue.", "fields", tool="Tasks, scouting & operations", kind="Operations"))
    if alert_count:
        actions.append(_action(90, f"Review {alert_count} open crop-health alert(s)", "Alerts should be acknowledged, investigated and resolved against field evidence.", "fields", tool="Crop health, rules & alerts", kind="Field evidence"))

    by_name = {str(row.get("name")): row for row in freshness}
    weather = by_name.get("Weather")
    if has_context and weather and weather.get("status") in {"Missing", "Stale"}:
        actions.append(_action(86, "Retrieve current field weather", "Daily weather is missing or stale. Use the Research Data Hub/NASA POWER rather than preparing a CSV AGROLATTICE can retrieve itself.", "all_tools", tool="Research Data Hub", kind="Data"))
    satellite = by_name.get("Satellite")
    if has_context and satellite and satellite.get("status") in {"Missing", "Stale"}:
        actions.append(_action(74, "Update satellite observations", "The active field has no recent persistent EO observation. Search Sentinel-2 for the mapped polygon and review clear-scene quality.", "climate", tool="Satellite crop monitoring", kind="Earth observation"))
    root_zone = by_name.get("Root zone")
    if has_context and root_zone and root_zone.get("status") == "Missing":
        actions.append(_action(63, "Establish a root-zone water state", "Attach or generate a root-zone balance so water-stress interpretation is linked to the active field rather than inferred from rainfall alone.", "crop", tool="Soil-water balance", kind="Water"))

    trial_status_clean = str(trial_status or "").strip().casefold()
    if trial_status_clean in {"active", "planned"}:
        obs_latest = latest_date(trial_observations, ["Date", "Observation date", "observation_date"])
        obs_age = age_days(obs_latest, now=now)
        if obs_age is None:
            actions.append(_action(84, "Begin repeated trial observations", "The active trial has no flowering observations yet. Repeated plot-level measurements are needed for synchrony calibration.", "experiments", tool="Maize flowering trials & field data", kind="Experiment"))
        elif obs_age > 7:
            actions.append(_action(82, "Update trial flowering observations", f"The most recent flowering observation is {obs_age:.0f} day(s) old.", "experiments", tool="Maize flowering trials & field data", kind="Experiment"))

    if latest_model:
        model_status = str(latest_model.get("status") or "").strip()
        if model_status.casefold() == "prototype":
            actions.append(_action(70, "Validate the latest research model", f"{latest_model.get('name') or 'The latest model'} is still marked Prototype. Run grouped/site/year-aware validation before operational use.", "evidence", tool="Validation Centre", kind="Evidence"))
    if latest_prediction:
        applicability = str(latest_prediction.get("applicability_status") or "").strip()
        if applicability and applicability.casefold() not in {"within training support", "in domain", "within scope", "acceptable", "ok"}:
            actions.append(_action(88, "Review prediction applicability", f"The latest registered prediction is flagged '{applicability}'. Inspect training scope and uncertainty before acting on it.", "evidence", tool="Research Model & Evidence Registry", kind="Evidence"))

    if isinstance(recommendations, pd.DataFrame) and not recommendations.empty:
        status = _status_series(recommendations, "status")
        active = recommendations.loc[~status.isin(CLOSED_RECOMMENDATION_STATUSES)].copy() if not status.empty else recommendations.copy()
        if not active.empty:
            outcome_ids: set[str] = set()
            if isinstance(treatment_outcomes, pd.DataFrame) and not treatment_outcomes.empty and "recommendation_id" in treatment_outcomes:
                outcome_ids = set(treatment_outcomes["recommendation_id"].dropna().astype(str))
            candidates = active.loc[active["status"].astype(str).str.casefold().isin({"accepted", "applied", "completed"})] if "status" in active else pd.DataFrame()
            missing_outcome = 0
            if not candidates.empty and "recommendation_id" in candidates:
                missing_outcome = sum(str(value) not in outcome_ids for value in candidates["recommendation_id"].dropna())
            if missing_outcome:
                actions.append(_action(76, f"Record outcomes for {missing_outcome} acted-on recommendation(s)", "Closing the recommendation → action → outcome loop is required for later effectiveness and causal audits.", "crop", tool="Decision Intelligence & Research Optimisation", kind="Evidence"))

    if twin_state:
        uncertainty = pd.to_numeric(pd.Series([twin_state.get("Uncertainty (%)")]), errors="coerce").iloc[0]
        observations = pd.to_numeric(pd.Series([twin_state.get("Field observations")]), errors="coerce").iloc[0]
        if pd.notna(uncertainty) and float(uncertainty) >= 60 and (pd.isna(observations) or float(observations) < 3):
            actions.append(_action(89, "Collect a high-value phenology observation", "Twin uncertainty is high and local observations are sparse. A flowering/leaf-development observation is more useful now than another model rerun.", "experiments", tool="Maize flowering trials & field data", kind="Next measurement"))

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in sorted(actions, key=lambda item: (-int(item["priority"]), item["title"])):
        key = row["title"].casefold()
        if key not in seen:
            deduped.append(row)
            seen.add(key)
        if len(deduped) >= int(limit):
            break
    return deduped


def next_best_measurement(*, twin_state: Mapping[str, Any] | None, freshness: Sequence[Mapping[str, Any]], trial_active: bool) -> dict[str, str] | None:
    by_name = {str(row.get("name")): row for row in freshness}
    if twin_state:
        uncertainty = pd.to_numeric(pd.Series([twin_state.get("Uncertainty (%)")]), errors="coerce").iloc[0]
        field_obs = pd.to_numeric(pd.Series([twin_state.get("Field observations")]), errors="coerce").iloc[0]
        male_progress = pd.to_numeric(pd.Series([twin_state.get("Male progress (%)")]), errors="coerce").iloc[0]
        female_progress = pd.to_numeric(pd.Series([twin_state.get("Female progress (%)")]), errors="coerce").iloc[0]
        if trial_active and pd.notna(uncertainty) and float(uncertainty) >= 45:
            near_flowering = any(pd.notna(value) and 65 <= float(value) <= 120 for value in (male_progress, female_progress))
            if near_flowering:
                return {"title": "Record male shedding and female silking", "reason": "Flowering is approaching/underway and these direct observations reduce synchrony uncertainty."}
            if pd.isna(field_obs) or float(field_obs) < 3:
                return {"title": "Record a plot-level phenology observation", "reason": "The Twin has sparse local observations, so another measurement is more informative than another model run."}
    sensor = by_name.get("Sensors")
    root_zone = by_name.get("Root zone")
    if root_zone and root_zone.get("status") == "Missing" and (not sensor or sensor.get("status") in {"Missing", "Stale"}):
        return {"title": "Measure soil moisture/root-zone condition", "reason": "Water-state evidence is currently missing, limiting stress interpretation and irrigation research."}
    weather = by_name.get("Weather")
    if weather and weather.get("status") in {"Missing", "Stale"}:
        return {"title": "Retrieve daily weather", "reason": "Phenology, water balance and pest-risk workflows depend on current environmental forcing."}
    satellite = by_name.get("Satellite")
    if satellite and satellite.get("status") in {"Missing", "Stale"}:
        return {"title": "Acquire a recent clear satellite observation", "reason": "A new canopy observation can test whether the crop trajectory is consistent with the Twin."}
    return None


def build_recent_activity(
    *,
    field_timeline: pd.DataFrame | None = None,
    data_acquisitions: pd.DataFrame | None = None,
    predictions: pd.DataFrame | None = None,
    recommendations: pd.DataFrame | None = None,
    limit: int = 6,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if isinstance(field_timeline, pd.DataFrame) and not field_timeline.empty:
        for record in field_timeline.head(50).to_dict("records"):
            rows.append({"timestamp": record.get("timestamp"), "type": record.get("type") or "Field", "title": record.get("title") or "Field record", "detail": record.get("detail") or ""})
    if isinstance(data_acquisitions, pd.DataFrame) and not data_acquisitions.empty:
        for record in data_acquisitions.head(20).to_dict("records"):
            rows.append({"timestamp": record.get("created_at"), "type": "Data", "title": f"Retrieved {record.get('source_type') or 'dataset'}", "detail": str(record.get("source") or "")})
    if isinstance(predictions, pd.DataFrame) and not predictions.empty:
        for record in predictions.head(20).to_dict("records"):
            rows.append({"timestamp": record.get("generated_at"), "type": "Prediction", "title": str(record.get("target") or "Model prediction"), "detail": str(record.get("model_name") or record.get("model_family") or "")})
    if isinstance(recommendations, pd.DataFrame) and not recommendations.empty:
        for record in recommendations.head(20).to_dict("records"):
            rows.append({"timestamp": record.get("updated_at") or record.get("created_at"), "type": "Recommendation", "title": str(record.get("action_type") or "Recommendation"), "detail": str(record.get("status") or "")})
    if not rows:
        return pd.DataFrame(columns=["timestamp", "type", "title", "detail"])
    frame = pd.DataFrame(rows)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    frame = frame.dropna(subset=["timestamp"]).sort_values("timestamp", ascending=False).drop_duplicates(["timestamp", "type", "title"], keep="first")
    return frame.head(int(limit)).reset_index(drop=True)


def build_upcoming_timeline(
    *,
    tasks: pd.DataFrame | None,
    twin_state: Mapping[str, Any] | None,
    trial: Mapping[str, Any] | None,
    now: Any | None = None,
    days: int = 14,
    limit: int = 7,
) -> pd.DataFrame:
    reference = _timestamp(now) if now is not None else pd.Timestamp.now(tz="UTC")
    if reference is None:
        reference = pd.Timestamp.now(tz="UTC")
    start = reference.normalize()
    end = start + pd.Timedelta(days=int(days))
    rows: list[dict[str, Any]] = []
    if isinstance(tasks, pd.DataFrame) and not tasks.empty:
        status = _status_series(tasks, "status")
        open_mask = ~status.isin(CLOSED_TASK_STATUSES) if not status.empty else pd.Series(True, index=tasks.index)
        due = pd.to_datetime(tasks.get("due_date"), errors="coerce", utc=True)
        for idx in tasks.index[open_mask & due.notna() & due.ge(start) & due.le(end)]:
            record = tasks.loc[idx]
            rows.append({"date": due.loc[idx], "type": "Task", "title": str(record.get("title") or "Field task"), "detail": str(record.get("category") or "")})
    if twin_state:
        for key, title in (("Predicted male 50% flowering", "Predicted male 50% flowering"), ("Predicted female 50% silking", "Predicted female 50% silking")):
            event = _timestamp(twin_state.get(key))
            if event is not None and start <= event <= end:
                rows.append({"date": event, "type": "Modelled", "title": title, "detail": "Mechanistic/Twin timing estimate; observe rather than assume."})
    if trial:
        sowing = _timestamp(trial.get("female_sowing_date"))
        if sowing is not None and start <= sowing <= end:
            rows.append({"date": sowing, "type": "Trial", "title": "Female sowing date", "detail": str(trial.get("name") or "Active trial")})
    if not rows:
        return pd.DataFrame(columns=["date", "type", "title", "detail"])
    frame = pd.DataFrame(rows).sort_values("date").drop_duplicates(["date", "type", "title"], keep="first")
    return frame.head(int(limit)).reset_index(drop=True)
