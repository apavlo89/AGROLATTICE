"""AGROLATTICE 11.12 Crop Decision Command Centre.

The module reorganises Crop Decisions around the active mapped field/season and a
research decision lifecycle.  The overview deliberately reads only persisted
summaries; NASA/STAC requests, crop-model runs, optimisation and ML fitting remain
explicit user actions in their dedicated tools.
"""
from __future__ import annotations

import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from navigation_state import consume_view_request, queue_view_request

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from agricultural_validation import applicability_score
from research_data_hub import aggregate_daily_weather, fetch_canonical_nasa_weather, field_coordinates, nasa_pest_covariates

MODULE_VERSION = "1.0.1"

EVIDENCE_BADGES = {
    "Observed": "🟢",
    "Measured": "🟢",
    "Retrieved": "🔵",
    "Derived": "🟣",
    "Mechanistic": "🟠",
    "ML prediction": "🟡",
    "Forecast": "🔷",
    "Scenario assumption": "⚪",
    "Recommendation": "🟤",
    "Actual operation": "✅",
}


def _loads(value: Any, default: Any = None) -> Any:
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list, tuple, int, float, bool)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def _age_label(value: Any) -> str:
    stamp = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(stamp):
        return "not available"
    seconds = max(0.0, (pd.Timestamp.now(tz="UTC") - stamp).total_seconds())
    if seconds < 3600:
        return f"{max(1, int(seconds // 60))} min old"
    if seconds < 86400:
        return f"{int(seconds // 3600)} h old"
    return f"{int(seconds // 86400)} d old"


def _record_time(record: Mapping[str, Any] | None, keys: tuple[str, ...]) -> Any:
    if not record:
        return None
    for key in keys:
        if record.get(key) not in (None, ""):
            return record.get(key)
    return None


def _active_field(field_db: Any, active_field_id: str | None) -> tuple[str | None, dict[str, Any] | None]:
    if not active_field_id:
        return None, None
    try:
        field = field_db.field(str(active_field_id))
    except Exception:
        return str(active_field_id), None
    return str(active_field_id), field


def _active_season(field_db: Any, field_id: str | None, field: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not field_id:
        return None
    try:
        seasons = field_db.seasons(str(field_id))
    except Exception:
        seasons = pd.DataFrame()
    if isinstance(seasons, pd.DataFrame) and not seasons.empty:
        target_year = pd.to_numeric((field or {}).get("season_year"), errors="coerce")
        if pd.notna(target_year) and "season_year" in seasons:
            hit = seasons.loc[pd.to_numeric(seasons["season_year"], errors="coerce").eq(int(target_year))]
            if not hit.empty:
                return hit.sort_values("updated_at" if "updated_at" in hit else "season_year").iloc[-1].to_dict()
        sort_cols = [column for column in ("season_year", "updated_at", "created_at") if column in seasons]
        return seasons.sort_values(sort_cols).iloc[-1].to_dict() if sort_cols else seasons.iloc[-1].to_dict()
    # Backward-compatible field context. Do not invent sowing/harvest dates.
    if field:
        return {
            "season_id": None,
            "field_id": field_id,
            "season_year": field.get("season_year"),
            "crop": field.get("crop"),
            "genotype": field.get("variety"),
            "sowing_date": None,
            "harvest_date": None,
            "status": "Field-level context",
            "irrigation_system": field.get("irrigation_system"),
        }
    return None


def _twin_link(twin_db: Any, field_id: str | None) -> dict[str, Any] | None:
    if not field_id:
        return None
    try:
        links = twin_db.links()
        if not isinstance(links, pd.DataFrame) or links.empty or "field_id" not in links:
            return None
        hit = links.loc[links["field_id"].astype(str).eq(str(field_id))]
        if hit.empty:
            return None
        active = hit.loc[pd.to_numeric(hit.get("active"), errors="coerce").fillna(0).eq(1)] if "active" in hit else hit
        return (active.iloc[0] if not active.empty else hit.iloc[0]).to_dict()
    except Exception:
        return None


def _find_nested(payload: Any, candidates: tuple[str, ...]) -> Any:
    wanted = {c.casefold() for c in candidates}
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            if str(key).casefold() in wanted and value not in (None, "", [], {}):
                return value
        for value in payload.values():
            found = _find_nested(value, candidates)
            if found not in (None, "", [], {}):
                return found
    elif isinstance(payload, list):
        for value in payload:
            found = _find_nested(value, candidates)
            if found not in (None, "", [], {}):
                return found
    return None


def _twin_snapshot(twin_db: Any, link: Mapping[str, Any] | None) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if not link:
        return None, {}
    link_id = str(link.get("link_id"))
    try:
        frame = twin_db.snapshots(link_id)
    except Exception:
        return None, {}
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return None, {}
    row = frame.sort_values("created_at" if "created_at" in frame else "as_of").iloc[-1].to_dict()
    state = _loads(row.get("state_json"), {}) or {}
    return row, state if isinstance(state, dict) else {}


def _latest_twin_records(twin_db: Any, link: Mapping[str, Any] | None) -> dict[str, Any]:
    result = {"weather": None, "root": None, "satellite": None}
    if not link:
        return result
    link_id = str(link.get("link_id"))
    for key, method in (("weather", "weather_record"), ("root", "root_zone_record"), ("satellite", "satellite_record")):
        try:
            result[key] = getattr(twin_db, method)(link_id)
        except Exception:
            result[key] = None
    return result


def _field_tables(field_db: Any, field_id: str | None) -> dict[str, pd.DataFrame]:
    tables: dict[str, pd.DataFrame] = {}
    if not field_id:
        return {name: pd.DataFrame() for name in ("tasks", "alerts", "observations", "operations", "nutrients", "sensors", "readings", "history")}
    calls = {
        "tasks": ("tasks", (field_id,)),
        "alerts": ("alerts", (field_id,)),
        "observations": ("observations", (field_id,)),
        "operations": ("operations", (field_id,)),
        "nutrients": ("nutrient_samples", (field_id,)),
        "sensors": ("sensors", (field_id,)),
        "readings": ("readings", (), {"field_id": field_id}),
    }
    for name, spec in calls.items():
        method = spec[0]
        args = spec[1]
        kwargs = spec[2] if len(spec) > 2 else {}
        try:
            value = getattr(field_db, method)(*args, **kwargs)
            tables[name] = value if isinstance(value, pd.DataFrame) else pd.DataFrame()
        except Exception:
            tables[name] = pd.DataFrame()
    try:
        tables["history"] = field_db.frame("SELECT * FROM crop_history WHERE field_id=? ORDER BY season_year DESC, created_at DESC", (field_id,))
    except Exception:
        tables["history"] = pd.DataFrame()
    return tables


def _research_tables(registry: Any, field_id: str | None) -> dict[str, pd.DataFrame]:
    result: dict[str, pd.DataFrame] = {}
    calls = {
        "predictions": ("predictions", {"field_id": field_id, "limit": 250}),
        "recommendations": ("recommendations", {"field_id": field_id}),
        "outcomes": ("treatment_outcomes", {"field_id": field_id}),
        "acquisitions": ("data_acquisitions", {"field_id": field_id, "limit": 250}),
        "decision_runs": ("decision_runs", {"field_id": field_id, "limit": 250}),
    }
    for name, (method, kwargs) in calls.items():
        try:
            value = getattr(registry, method)(**{k: v for k, v in kwargs.items() if v is not None})
            result[name] = value if isinstance(value, pd.DataFrame) else pd.DataFrame()
        except Exception:
            result[name] = pd.DataFrame()
    try:
        result["models"] = registry.models()
    except Exception:
        result["models"] = pd.DataFrame()
    return result


def _latest_acquisition(frame: pd.DataFrame, keywords: tuple[str, ...]) -> dict[str, Any] | None:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return None
    text = pd.Series("", index=frame.index)
    for column in ("source", "source_type"):
        if column in frame:
            text = text + " " + frame[column].astype(str).str.casefold()
    mask = pd.Series(False, index=frame.index)
    for word in keywords:
        mask |= text.str.contains(word.casefold(), regex=False, na=False)
    subset = frame.loc[mask].copy()
    if subset.empty:
        return None
    for col in ("period_end", "created_at"):
        if col in subset:
            subset["__sort"] = pd.to_datetime(subset[col], errors="coerce", utc=True)
            subset = subset.sort_values("__sort", ascending=False)
            break
    return subset.iloc[0].to_dict()


def _latest_observation_age(observations: pd.DataFrame) -> tuple[Any, str]:
    if not isinstance(observations, pd.DataFrame) or observations.empty:
        return None, "No field scouting recorded"
    col = next((c for c in ("observed_at", "created_at") if c in observations), None)
    if not col:
        return None, "Field scouting available"
    stamp = pd.to_datetime(observations[col], errors="coerce", utc=True).max()
    return stamp, _age_label(stamp)


def _root_zone_summary(twin_db: Any, link: Mapping[str, Any] | None) -> dict[str, Any]:
    if not link:
        return {}
    try:
        frame = twin_db.root_zone(str(link.get("link_id")))
    except Exception:
        return {}
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return {}
    row = frame.iloc[-1]
    def first(names: tuple[str, ...]):
        for name in names:
            if name in row.index and pd.notna(row[name]):
                return row[name]
        return None
    return {
        "date": first(("DATE", "Date", "date")),
        "ks": first(("Ks", "KS", "Crop water stress coefficient")),
        "depletion": first(("Relative depletion", "Relative depletion fraction", "Depletion fraction")),
        "raw": first(("RAW (mm)", "RAW")),
        "dr": first(("Depletion (mm)", "Dr (mm)", "Dr")),
    }


def _model_status_counts(models: pd.DataFrame) -> dict[str, int]:
    if not isinstance(models, pd.DataFrame) or models.empty or "status" not in models:
        return {}
    return models["status"].astype(str).value_counts().to_dict()


def _evidence_badge(kind: str, text: str) -> str:
    return f"{EVIDENCE_BADGES.get(kind, '•')} **{kind}** · {text}"


def _render_context_card(field: Mapping[str, Any] | None, season: Mapping[str, Any] | None, link: Mapping[str, Any] | None) -> None:
    if not field:
        st.info("Select a mapped field in the workspace context to make Crop Decisions field-aware.")
        return
    crop = (season or {}).get("crop") or field.get("crop") or "Crop not set"
    genotype = (season or {}).get("genotype") or field.get("variety") or "genotype not set"
    season_year = (season or {}).get("season_year") or field.get("season_year") or "season not set"
    twin = (link or {}).get("name") or "No linked Twin"
    st.caption("Active crop-decision context")
    st.markdown(f"**{field.get('farm_name') or 'Research field'} → {field.get('name')} → {crop} · {genotype} · {season_year} → {twin}**")


def _render_decision_pulse(
    *, field: Mapping[str, Any], season: Mapping[str, Any] | None, state: Mapping[str, Any],
    root: Mapping[str, Any], field_tables: Mapping[str, pd.DataFrame], research: Mapping[str, pd.DataFrame],
) -> None:
    crop = (season or {}).get("crop") or field.get("crop") or "Not set"
    stage = _find_nested(state, ("crop_stage", "stage", "development_stage", "phenology_stage")) or "Stage not saved"
    anthesis = _find_nested(state, ("male_anthesis_date", "anthesis_date", "predicted_anthesis"))
    silking = _find_nested(state, ("female_silking_date", "silking_date", "predicted_silking"))
    ks = pd.to_numeric(root.get("ks"), errors="coerce")
    water_text = "No saved root-zone state" if pd.isna(ks) else ("little/no modelled water stress" if float(ks) >= 0.95 else ("mild modelled water stress" if float(ks) >= 0.80 else "substantial modelled water stress"))

    predictions = research.get("predictions", pd.DataFrame())
    recommendations = research.get("recommendations", pd.DataFrame())
    outcomes = research.get("outcomes", pd.DataFrame())
    observations = field_tables.get("observations", pd.DataFrame())
    alerts = field_tables.get("alerts", pd.DataFrame())
    open_alerts = 0
    if isinstance(alerts, pd.DataFrame) and not alerts.empty and "status" in alerts:
        open_alerts = int((~alerts["status"].astype(str).str.casefold().eq("resolved")).sum())
    open_recs = 0
    if isinstance(recommendations, pd.DataFrame) and not recommendations.empty and "status" in recommendations:
        closed = {"rejected", "completed", "superseded"}
        open_recs = int((~recommendations["status"].astype(str).str.casefold().isin(closed)).sum())

    cards = st.columns(4)
    with cards[0]:
        st.markdown("#### 🌱 Crop state")
        st.markdown(f"**{crop}**")
        st.caption(f"Stage: {stage}")
        if anthesis or silking:
            st.caption(f"Flowering: anthesis {anthesis or '—'} · silking {silking or '—'}")
        st.caption("Mechanistic/observed state is shown only when saved in the Twin.")
    with cards[1]:
        st.markdown("#### 💧 Water")
        st.markdown("**" + (f"Ks {float(ks):.2f}" if pd.notna(ks) else "No current Ks") + "**")
        st.caption(water_text)
        if root.get("date") is not None:
            st.caption(f"Saved state: {root.get('date')}")
    with cards[2]:
        st.markdown("#### 🩺 Crop health")
        st.markdown(f"**{open_alerts} open alert{'s' if open_alerts != 1 else ''}**")
        _, scout_age = _latest_observation_age(observations)
        st.caption(f"Latest scouting: {scout_age}")
        pest_pred = pd.DataFrame()
        if isinstance(predictions, pd.DataFrame) and not predictions.empty:
            mask = predictions.get("target", pd.Series(dtype=str)).astype(str).str.contains("pest|disease", case=False, regex=True, na=False)
            pest_pred = predictions.loc[mask]
        st.caption("Pest model evidence: " + ("available" if not pest_pred.empty else "none saved for this field"))
    with cards[3]:
        st.markdown("#### 📋 Decision evidence")
        st.markdown(f"**{open_recs} active recommendation{'s' if open_recs != 1 else ''}**")
        st.caption(f"{len(outcomes):,} measured outcome record(s) linked")
        st.caption(f"{len(predictions):,} registered prediction(s) linked")


def _priority_actions(
    *, field: Mapping[str, Any], season: Mapping[str, Any] | None, twin_records: Mapping[str, Any],
    root: Mapping[str, Any], field_tables: Mapping[str, pd.DataFrame], research: Mapping[str, pd.DataFrame],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if not (season or {}).get("sowing_date"):
        actions.append({"priority": 1, "title": "Record the season and sowing date", "detail": "Phenology, stage-specific climate exposure and crop-model simulations need an explicit crop-season anchor.", "area": "Crop & planting"})

    weather_rec = twin_records.get("weather")
    weather_end = _record_time(weather_rec, ("end_date", "updated_at", "fetched_at"))
    weather_ts = pd.to_datetime(weather_end, errors="coerce", utc=True)
    if pd.isna(weather_ts) or (pd.Timestamp.now(tz="UTC") - weather_ts).days > 3:
        actions.append({"priority": 2, "title": "Review / update field weather evidence", "detail": f"Latest saved Twin weather: {_age_label(weather_end)}. Reuse existing evidence when adequate; retrieve again only when stale or incomplete.", "area": "Crop & planting"})

    ks = pd.to_numeric(root.get("ks"), errors="coerce")
    if pd.notna(ks) and float(ks) < 0.90:
        actions.append({"priority": 2, "title": "Compare irrigation strategies", "detail": f"Latest modelled root-zone Ks is {float(ks):.2f}. Inspect measured soil moisture and rainfall/forecast assumptions before acting.", "area": "Water & irrigation"})

    observations = field_tables.get("observations", pd.DataFrame())
    obs_stamp, _ = _latest_observation_age(observations)
    if obs_stamp is None or (pd.Timestamp.now(tz="UTC") - pd.Timestamp(obs_stamp)).days > 7:
        actions.append({"priority": 3, "title": "Refresh field scouting evidence", "detail": "The latest field observation is missing or more than seven days old. Environmental or EO risk signals should be verified in the field.", "area": "Pest & crop health"})

    nutrients = field_tables.get("nutrients", pd.DataFrame())
    if not isinstance(nutrients, pd.DataFrame) or nutrients.empty:
        actions.append({"priority": 4, "title": "Check nutrient evidence readiness", "detail": "No structured nutrient sample is linked to the active field. Do not generate a nutrient-rate recommendation from generic assumptions alone.", "area": "Nutrition"})

    recs = research.get("recommendations", pd.DataFrame())
    outcomes = research.get("outcomes", pd.DataFrame())
    if isinstance(recs, pd.DataFrame) and not recs.empty:
        active = recs.loc[recs.get("status", pd.Series(dtype=str)).astype(str).str.casefold().isin({"accepted", "applied"})]
        outcome_ids = set(outcomes.get("recommendation_id", pd.Series(dtype=str)).astype(str)) if isinstance(outcomes, pd.DataFrame) and not outcomes.empty else set()
        pending = active.loc[~active["recommendation_id"].astype(str).isin(outcome_ids)] if "recommendation_id" in active else pd.DataFrame()
        if not pending.empty:
            actions.append({"priority": 1, "title": "Record outcomes for applied decisions", "detail": f"{len(pending)} accepted/applied recommendation(s) have no linked measured outcome yet. Closing this loop is essential for decision-effectiveness research.", "area": "Recommendations & outcomes"})

    models = research.get("models", pd.DataFrame())
    operational = models.loc[models.get("status", pd.Series(dtype=str)).astype(str).eq("Operationally eligible")] if isinstance(models, pd.DataFrame) and not models.empty else pd.DataFrame()
    if operational.empty:
        actions.append({"priority": 5, "title": "No operationally eligible predictive model", "detail": "Research models may still be explored, but Crop Decisions should not present them as operational recommendations until their validation status supports use.", "area": "Yield & economics"})

    return sorted(actions, key=lambda item: item["priority"])[:6]


def _goto(area: str, action: Mapping[str, Any] | None = None) -> None:
    """Queue a Crop Decisions route for the next rerun.

    The navigation radio owns ``crop_decision_command_view_radio``. Writing only
    to the historical mirror key was being overwritten by the radio's persisted
    widget value on rerun, which made Priority Decision buttons appear inert.
    """
    notice = None
    if action:
        notice = {
            "area": area,
            "title": str(action.get("title") or "Priority action"),
            "detail": str(action.get("detail") or ""),
        }
    queue_view_request(
        st.session_state,
        request_key="crop_decision_command_view_request",
        target=area,
        notice_key="crop_decision_navigation_notice",
        notice=notice,
    )
    st.rerun()


def _render_priority_actions(actions: list[dict[str, Any]]) -> None:
    st.markdown("### Priority decisions & evidence gaps")
    if not actions:
        st.success("No obvious evidence gap is currently flagged by the lightweight decision rules. This does not mean the crop has no agronomic risk.")
        return
    for index, action in enumerate(actions, 1):
        cols = st.columns([8, 2])
        with cols[0]:
            st.markdown(f"**{index}. {action['title']}**")
            st.caption(action["detail"])
        with cols[1]:
            if st.button(f"Open {action['area']}", key=f"crop_decision_priority_{index}", width="stretch"):
                _goto(action["area"], action)
        if index < len(actions):
            st.divider()


def _render_data_readiness(twin_records: Mapping[str, Any], field_tables: Mapping[str, pd.DataFrame], research: Mapping[str, pd.DataFrame]) -> None:
    st.markdown("### Decision data readiness")
    acquisitions = research.get("acquisitions", pd.DataFrame())
    weather_acq = _latest_acquisition(acquisitions, ("weather", "nasa", "power", "climate"))
    eo_acq = _latest_acquisition(acquisitions, ("sentinel", "satellite", "earth observation", "eo"))
    observations = field_tables.get("observations", pd.DataFrame())
    nutrients = field_tables.get("nutrients", pd.DataFrame())
    sensors = field_tables.get("sensors", pd.DataFrame())
    cards = st.columns(5)
    items = [
        ("Weather", twin_records.get("weather") or weather_acq, "Retrieved"),
        ("Root-zone", twin_records.get("root"), "Derived"),
        ("Earth observation", twin_records.get("satellite") or eo_acq, "Retrieved"),
        ("Field observations", None if observations.empty else {"created_at": observations.iloc[0].get("observed_at")}, "Observed"),
        ("Nutrient / sensor evidence", None if nutrients.empty and sensors.empty else {"created_at": date.today()}, "Measured"),
    ]
    for card, (label, record, kind) in zip(cards, items):
        with card:
            st.markdown(f"**{label}**")
            if record:
                stamp = _record_time(record, ("period_end", "end_date", "updated_at", "fetched_at", "created_at"))
                st.caption(_evidence_badge(kind, _age_label(stamp)))
            else:
                st.caption("⚠️ Missing / not linked")


def _render_recent_decisions(research: Mapping[str, pd.DataFrame]) -> None:
    st.markdown("### Decision inbox")
    recs = research.get("recommendations", pd.DataFrame())
    if not isinstance(recs, pd.DataFrame) or recs.empty:
        st.info("No research recommendations are linked to the active field yet. Predictions remain separate from recommendations.")
        return
    cols = [c for c in ("created_at", "action_type", "action_text", "status", "proposed_time", "expected_effect", "lower_bound", "upper_bound") if c in recs]
    show = recs[cols].head(8).copy()
    st.dataframe(show, hide_index=True, width="stretch")
    st.caption("Recommendation status is a research workflow state. It is not evidence that the action improved the crop.")


def _render_decision_timeline(field_tables: Mapping[str, pd.DataFrame], research: Mapping[str, pd.DataFrame]) -> None:
    """Compact persisted timeline of evidence, decisions, actions and outcomes.

    This is intentionally a read-only synthesis of existing records. It does not
    infer that a later outcome was caused by an earlier recommendation.
    """
    events: list[dict[str, Any]] = []

    def add_events(frame: pd.DataFrame, *, kind: str, date_cols: tuple[str, ...], title_cols: tuple[str, ...], detail_cols: tuple[str, ...] = ()) -> None:
        if not isinstance(frame, pd.DataFrame) or frame.empty:
            return
        date_col = next((c for c in date_cols if c in frame.columns), None)
        if not date_col:
            return
        for _, row in frame.head(150).iterrows():
            stamp = pd.to_datetime(row.get(date_col), errors="coerce", utc=True)
            if pd.isna(stamp):
                continue
            title = next((str(row.get(c)) for c in title_cols if c in frame.columns and pd.notna(row.get(c)) and str(row.get(c)).strip()), kind)
            details = [str(row.get(c)) for c in detail_cols if c in frame.columns and pd.notna(row.get(c)) and str(row.get(c)).strip()]
            events.append({"When": stamp, "Type": kind, "Event": title, "Detail": " · ".join(details)})

    add_events(field_tables.get("operations", pd.DataFrame()), kind="Actual / planned operation", date_cols=("operation_date", "started_at", "created_at"), title_cols=("operation", "operation_type", "product"), detail_cols=("status", "rate", "unit", "water_mm"))
    add_events(field_tables.get("observations", pd.DataFrame()), kind="Observed", date_cols=("observed_at", "created_at"), title_cols=("observation_type", "category", "protocol_name"), detail_cols=("severity", "value", "unit", "notes"))
    add_events(research.get("recommendations", pd.DataFrame()), kind="Recommendation", date_cols=("created_at", "proposed_time"), title_cols=("action_text", "action_type"), detail_cols=("status", "amount", "unit"))
    add_events(research.get("outcomes", pd.DataFrame()), kind="Measured outcome", date_cols=("observed_at", "outcome_date", "created_at"), title_cols=("outcome_name", "outcome_type", "metric"), detail_cols=("value", "unit", "followed_recommendation"))
    add_events(research.get("predictions", pd.DataFrame()), kind="Model prediction", date_cols=("generated_at", "created_at"), title_cols=("target", "model_name"), detail_cols=("prediction", "prediction_text", "applicability_status"))

    st.markdown("### Crop decision timeline")
    if not events:
        st.caption("No persisted operations, observations, recommendations, outcomes or predictions are available for a decision timeline yet.")
        return
    timeline = pd.DataFrame(events).sort_values("When", ascending=False).head(40)
    timeline["When"] = timeline["When"].dt.strftime("%Y-%m-%d %H:%M")
    st.dataframe(timeline, hide_index=True, width="stretch")
    st.caption("Chronology provides research context only. Temporal order does not establish that a recommendation or operation caused a later outcome.")


def _render_overview(
    *, field: Mapping[str, Any] | None, season: Mapping[str, Any] | None, link: Mapping[str, Any] | None,
    state: Mapping[str, Any], twin_records: Mapping[str, Any], root: Mapping[str, Any],
    field_tables: Mapping[str, pd.DataFrame], research: Mapping[str, pd.DataFrame],
) -> None:
    if not field:
        st.info("Choose an active mapped field using **Change context** above. The command centre will then reuse its season, Twin, field records and persisted evidence.")
        return
    _render_context_card(field, season, link)
    _render_decision_pulse(field=field, season=season, state=state, root=root, field_tables=field_tables, research=research)
    st.divider()
    actions = _priority_actions(field=field, season=season, twin_records=twin_records, root=root, field_tables=field_tables, research=research)
    left, right = st.columns([3, 2])
    with left:
        _render_priority_actions(actions)
    with right:
        _render_data_readiness(twin_records, field_tables, research)
        st.markdown("### Evidence status")
        counts = _model_status_counts(research.get("models", pd.DataFrame()))
        st.caption(f"Operationally eligible models: **{counts.get('Operationally eligible', 0)}**")
        st.caption(f"Externally validated models: **{counts.get('Externally validated', 0)}**")
        st.caption(f"Registered field predictions: **{len(research.get('predictions', pd.DataFrame()))}**")
    st.divider()
    _render_recent_decisions(research)
    st.divider()
    _render_decision_timeline(field_tables, research)


def _season_table(field_db: Any, field_id: str | None) -> pd.DataFrame:
    if not field_id:
        return pd.DataFrame()
    try:
        frame = field_db.seasons(field_id)
        return frame if isinstance(frame, pd.DataFrame) else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def _render_crop_profile_manager(profile_registry: Any, crop_library: Mapping[str, Any], selected_country: str, season: Mapping[str, Any] | None) -> None:
    st.markdown("### Crop profile manager")
    st.caption("Validated library records remain source material. Research profiles are explicit, versioned adaptations and never silently overwrite validated defaults.")
    profiles = profile_registry.profiles()
    if not profiles.empty:
        view_cols = [c for c in ("name", "crop", "cultivar", "country", "region", "evidence_grade", "status", "current_version", "updated_at") if c in profiles]
        st.dataframe(profiles[view_cols], hide_index=True, width="stretch")
        with st.expander("Inspect, version or clone an existing research profile", expanded=False):
            ids = profiles["profile_id"].astype(str).tolist()
            labels = {str(row["profile_id"]): f"{row.get('name')} · v{row.get('current_version')}" for _, row in profiles.iterrows()}
            selected_id = st.selectbox("Research profile", ids, format_func=lambda value: labels.get(value, value), key="crop_decision_profile_existing")
            selected_profile = profile_registry.profile(selected_id) or {}
            versions = profile_registry.versions(selected_id)
            if not versions.empty:
                cols = [c for c in ("version_number", "source_citation", "change_note", "created_by", "created_at") if c in versions]
                st.dataframe(versions[cols], hide_index=True, width="stretch")
            current_parameters = selected_profile.get("parameters") or {}
            with st.form("crop_decision_profile_version_form"):
                profile_name = st.text_input("Profile name", value=str(selected_profile.get("name") or ""))
                cultivar_edit = st.text_input("Cultivar / genotype", value=str(selected_profile.get("cultivar") or ""))
                region_edit = st.text_input("Region / site", value=str(selected_profile.get("region") or ""))
                grade_edit = st.selectbox("Evidence grade", ["Researcher supplied", "Local measured", "Locally calibrated", "Literature adaptation", "Screening assumption"], index=0 if str(selected_profile.get("evidence_grade")) not in ["Researcher supplied", "Local measured", "Locally calibrated", "Literature adaptation", "Screening assumption"] else ["Researcher supplied", "Local measured", "Locally calibrated", "Literature adaptation", "Screening assumption"].index(str(selected_profile.get("evidence_grade"))))
                citation_edit = st.text_input("Citation / protocol / dataset reference", value=str(selected_profile.get("source_citation") or ""))
                parameters_edit = st.text_area("Parameters (JSON)", value=json.dumps(current_parameters, indent=2, default=str), height=180)
                change_note = st.text_input("Change note", value="Updated researcher profile")
                save_version = st.form_submit_button("Save new version", type="primary", width="stretch")
            if save_version:
                try:
                    parsed = json.loads(parameters_edit or "{}")
                    if not isinstance(parsed, dict):
                        raise ValueError("Parameters must be a JSON object.")
                    profile_registry.save_profile({
                        "profile_id": selected_id, "name": profile_name, "crop": selected_profile.get("crop"),
                        "cultivar": cultivar_edit or None, "country": selected_profile.get("country"), "region": region_edit or None,
                        "source_profile": selected_profile.get("source_profile"), "source_citation": citation_edit or None,
                        "evidence_grade": grade_edit, "status": selected_profile.get("status") or "Research",
                        "author": selected_profile.get("author"), "notes": selected_profile.get("notes"),
                    }, parameters=parsed, change_note=change_note or "Updated researcher profile")
                    st.success("New crop-profile version saved; prior versions were retained.")
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not save crop-profile version: {error}")
            clone_name = st.text_input("Clone as", value=f"{selected_profile.get('name', 'Profile')} · clone", key="crop_decision_profile_clone_name")
            if st.button("Clone selected profile", key="crop_decision_profile_clone"):
                try:
                    profile_registry.clone_profile(selected_id, name=clone_name, country=selected_profile.get("country"), region=selected_profile.get("region"))
                    st.success("Profile cloned as an independent research profile.")
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not clone profile: {error}")
    crop_names = sorted((crop_library.get("crops") or {}).keys())
    default_crop = str((season or {}).get("crop") or "")
    if default_crop not in crop_names and crop_names:
        default_crop = crop_names[0]
    with st.expander("Create a versioned research crop/cultivar profile", expanded=False):
        with st.form("crop_decision_profile_create"):
            cols = st.columns(3)
            crop = cols[0].selectbox("Crop", crop_names, index=crop_names.index(default_crop) if default_crop in crop_names else 0)
            cultivar = cols[1].text_input("Cultivar / genotype", value=str((season or {}).get("genotype") or ""))
            region = cols[2].text_input("Region / site", value="")
            name = st.text_input("Profile name", value=f"{crop} · {cultivar or 'research profile'} · {selected_country}")
            source_profile = st.text_input("Source / parent profile", value="Validated library + researcher adaptation")
            source_citation = st.text_input("Citation / protocol / dataset reference", value="")
            evidence_grade = st.selectbox("Evidence grade", ["Researcher supplied", "Local measured", "Locally calibrated", "Literature adaptation", "Screening assumption"])
            parameters_text = st.text_area("Parameters (JSON)", value="{}", help="Store only parameters you intentionally override or add; provenance should explain each local value.")
            notes = st.text_area("Notes / applicability")
            submitted = st.form_submit_button("Save versioned profile", type="primary", width="stretch")
        if submitted:
            try:
                parameters = json.loads(parameters_text or "{}")
                if not isinstance(parameters, dict):
                    raise ValueError("Parameters must be a JSON object.")
                profile_registry.save_profile(
                    {
                        "name": name, "crop": crop, "cultivar": cultivar or None, "country": selected_country,
                        "region": region or None, "source_profile": source_profile, "source_citation": source_citation or None,
                        "evidence_grade": evidence_grade, "status": "Research", "notes": notes or None,
                    },
                    parameters=parameters,
                    change_note="Created in Crop Decisions 11.12",
                )
                st.success("Research crop profile saved with provenance and version history.")
                st.rerun()
            except Exception as error:
                st.error(f"Could not save crop profile: {error}")


def _longest_dry_run(values: pd.Series, threshold_mm: float = 1.0) -> int:
    longest = current = 0
    for value in pd.to_numeric(values, errors="coerce").fillna(np.inf).lt(float(threshold_mm)):
        if bool(value):
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return int(longest)


def _daily_sowing_risk_table(
    weather: pd.DataFrame, *, candidate_month_days: list[tuple[int, int]], horizon_days: int,
    sensitive_start_day: int, sensitive_end_day: int, heat_threshold_c: float,
    base_temperature_c: float, upper_temperature_c: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    work = weather.copy()
    work["DATE"] = pd.to_datetime(work.get("DATE"), errors="coerce")
    work = work.dropna(subset=["DATE"]).sort_values("DATE")
    tmax_col = next((c for c in ("TEMPERATURE_MAX", "T2M_MAX") if c in work), None)
    tmin_col = next((c for c in ("TEMPERATURE_MIN", "T2M_MIN") if c in work), None)
    rain_col = next((c for c in ("PRECIPITATION_AVG", "PRECTOTCORR") if c in work), None)
    eto_col = next((c for c in ("EVAPOTRANSPIRATION", "ETO", "ETo") if c in work), None)
    if not tmax_col or not tmin_col or not rain_col:
        raise ValueError("Daily sowing-date analysis requires maximum/minimum temperature and precipitation.")
    years = sorted(work["DATE"].dt.year.unique())
    rows: list[dict[str, Any]] = []
    for month, day in candidate_month_days:
        label = f"{month:02d}-{day:02d}"
        for year in years:
            try:
                planting = pd.Timestamp(year=int(year), month=int(month), day=int(day))
            except ValueError:
                continue
            end = planting + pd.Timedelta(days=int(horizon_days) - 1)
            season_weather = work.loc[work["DATE"].between(planting, end)].copy()
            if len(season_weather) < max(20, int(horizon_days * 0.85)):
                continue
            tmax = pd.to_numeric(season_weather[tmax_col], errors="coerce")
            tmin = pd.to_numeric(season_weather[tmin_col], errors="coerce")
            mean = (tmax.clip(upper=float(upper_temperature_c)) + tmin.clip(lower=float(base_temperature_c), upper=float(upper_temperature_c))) / 2.0
            gdd = (mean - float(base_temperature_c)).clip(lower=0)
            rain = pd.to_numeric(season_weather[rain_col], errors="coerce").clip(lower=0)
            eto = pd.to_numeric(season_weather[eto_col], errors="coerce").clip(lower=0) if eto_col else pd.Series(np.nan, index=season_weather.index)
            day_after = (season_weather["DATE"] - planting).dt.days
            sensitive = season_weather.loc[day_after.between(int(sensitive_start_day), int(sensitive_end_day))]
            sensitive_tmax = pd.to_numeric(sensitive[tmax_col], errors="coerce") if not sensitive.empty else pd.Series(dtype=float)
            rows.append({
                "Candidate": label, "Year": int(year), "Planting date": planting.date(),
                "Season rainfall (mm)": float(rain.sum(min_count=1)),
                "Season ETo (mm)": float(eto.sum(min_count=1)) if eto.notna().any() else np.nan,
                "Climate water balance (mm)": float(rain.sum(min_count=1) - eto.sum(min_count=1)) if eto.notna().any() else np.nan,
                "GDD over horizon": float(gdd.sum(min_count=1)),
                "Sensitive-window heat days": int((sensitive_tmax >= float(heat_threshold_c)).sum()),
                "Sensitive-window Tmax (°C)": float(sensitive_tmax.max()) if sensitive_tmax.notna().any() else np.nan,
                "Longest dry spell (d)": _longest_dry_run(rain),
                "Coverage (%)": float(100.0 * len(season_weather) / max(1, int(horizon_days))),
            })
    detail = pd.DataFrame(rows)
    if detail.empty:
        return detail, detail
    summary_rows = []
    for candidate, group in detail.groupby("Candidate"):
        heat = pd.to_numeric(group["Sensitive-window heat days"], errors="coerce")
        wb = pd.to_numeric(group["Climate water balance (mm)"], errors="coerce")
        dry = pd.to_numeric(group["Longest dry spell (d)"], errors="coerce")
        summary_rows.append({
            "Candidate": candidate, "Historical years": int(group["Year"].nunique()),
            "Median heat days": float(heat.median()), "P90 heat days": float(heat.quantile(0.90)),
            "Years with ≥1 heat day (%)": float(100.0 * heat.gt(0).mean()),
            "Median rainfall (mm)": float(pd.to_numeric(group["Season rainfall (mm)"], errors="coerce").median()),
            "Median water balance (mm)": float(wb.median()) if wb.notna().any() else np.nan,
            "P10 water balance (mm)": float(wb.quantile(0.10)) if wb.notna().any() else np.nan,
            "Median longest dry spell (d)": float(dry.median()), "P90 longest dry spell (d)": float(dry.quantile(0.90)),
            "Median GDD": float(pd.to_numeric(group["GDD over horizon"], errors="coerce").median()),
        })
    return pd.DataFrame(summary_rows).sort_values(["P90 heat days", "P90 longest dry spell (d)", "Candidate"]), detail


def _render_daily_sowing_date_risk(
    *, field: Mapping[str, Any] | None, season: Mapping[str, Any] | None, cache_dir: str | Path | None,
) -> None:
    st.markdown("### Daily sowing-date climate risk explorer")
    st.caption("Compare candidate sowing dates across historical daily weather. This reports climate exposure distributions; it is not a cultivar-specific yield optimiser or official sowing calendar.")
    if not field or cache_dir is None:
        st.info("Select a mapped field to use the daily historical sowing-date explorer.")
        return
    try:
        lat, lon = field_coordinates(field)
    except Exception as error:
        st.info(f"Field coordinates are unavailable: {error}")
        return
    crop = str((season or {}).get("crop") or field.get("crop") or "Crop")
    today = date.today()
    default_end_year = today.year - 1
    default_start_year = max(1981, default_end_year - 14)
    row1 = st.columns(4)
    start_year = int(row1[0].number_input("Historical start year", 1981, default_end_year, default_start_year, 1, key="crop_decision_sowing_start_year"))
    end_year = int(row1[1].number_input("Historical end year", start_year, default_end_year, default_end_year, 1, key="crop_decision_sowing_end_year"))
    horizon = int(row1[2].number_input("Crop-season horizon (days)", 30, 365, 150 if crop.casefold() == "maize" else 120, 5, key="crop_decision_sowing_horizon"))
    step = int(row1[3].selectbox("Candidate spacing", [7, 14, 21, 28], index=1, key="crop_decision_sowing_step"))
    row2 = st.columns(4)
    candidate_start = row2[0].date_input("Candidate window start", value=date(2000, 3, 1), key="crop_decision_sowing_window_start")
    candidate_end = row2[1].date_input("Candidate window end", value=date(2000, 7, 1), key="crop_decision_sowing_window_end")
    sensitive_start = int(row2[2].number_input("Sensitive window starts (days after sowing)", 0, horizon - 1, 45 if crop.casefold() == "maize" else 35, 1, key="crop_decision_sensitive_start"))
    sensitive_end = int(row2[3].number_input("Sensitive window ends", sensitive_start, horizon - 1, min(horizon - 1, 90 if crop.casefold() == "maize" else 75), 1, key="crop_decision_sensitive_end"))
    row3 = st.columns(3)
    heat_threshold = float(row3[0].number_input("Heat threshold (°C)", 20.0, 55.0, 35.0, 0.5, key="crop_decision_sowing_heat"))
    base_temp = float(row3[1].number_input("GDD base (°C)", -5.0, 30.0, 10.0, 0.5, key="crop_decision_sowing_base"))
    upper_temp = float(row3[2].number_input("GDD upper cap (°C)", base_temp + 1.0, 60.0, 30.0, 0.5, key="crop_decision_sowing_cap"))
    if candidate_end < candidate_start:
        st.warning("Candidate window end must not precede its start.")
        return
    if st.button("Retrieve historical daily weather & compare sowing dates", type="primary", width="stretch", key="crop_decision_sowing_run"):
        try:
            acquired = fetch_canonical_nasa_weather(
                latitude=float(lat), longitude=float(lon), start_date=date(start_year, 1, 1),
                end_date=date(end_year, 12, 31), cache_dir=cache_dir,
            )
            candidates = []
            pointer = pd.Timestamp(candidate_start)
            end_pointer = pd.Timestamp(candidate_end)
            while pointer <= end_pointer:
                candidates.append((int(pointer.month), int(pointer.day)))
                pointer += pd.Timedelta(days=step)
            summary, detail = _daily_sowing_risk_table(
                acquired.frame, candidate_month_days=candidates, horizon_days=horizon,
                sensitive_start_day=sensitive_start, sensitive_end_day=sensitive_end,
                heat_threshold_c=heat_threshold, base_temperature_c=base_temp, upper_temperature_c=upper_temp,
            )
            st.session_state["crop_decision_sowing_summary"] = summary
            st.session_state["crop_decision_sowing_detail"] = detail
            st.session_state["crop_decision_sowing_provenance"] = acquired.metadata
        except Exception as error:
            st.error(f"Sowing-date comparison failed: {type(error).__name__}: {error}")
    summary = st.session_state.get("crop_decision_sowing_summary")
    detail = st.session_state.get("crop_decision_sowing_detail")
    if isinstance(summary, pd.DataFrame) and not summary.empty:
        st.dataframe(summary, hide_index=True, width="stretch")
        st.plotly_chart(px.line(summary.sort_values("Candidate"), x="Candidate", y=["P90 heat days", "P90 longest dry spell (d)"], markers=True, title="Bad-year climate exposure by candidate sowing date"), width="stretch")
        if isinstance(detail, pd.DataFrame) and not detail.empty:
            selected_candidate = st.selectbox("Inspect candidate across years", summary["Candidate"].astype(str).tolist(), key="crop_decision_sowing_inspect")
            st.dataframe(detail.loc[detail["Candidate"].astype(str).eq(str(selected_candidate))], hide_index=True, width="stretch")
        st.info("Interpret candidates from the component distributions rather than a single opaque score. Heat thresholds, sensitive-window timing and GDD settings are explicit assumptions unless calibrated for the local cultivar.")


def _render_crop_planting(
    *, field_db: Any, field_id: str | None, field: Mapping[str, Any] | None, season: Mapping[str, Any] | None,
    profile_registry: Any, crop_library: Mapping[str, Any], selected_country: str, cache_dir: str | Path | None, callbacks: Mapping[str, Callable[[], None]],
) -> None:
    _render_context_card(field, season, None)
    if field_id:
        seasons = _season_table(field_db, field_id)
        st.markdown("### Field-season record")
        if seasons.empty:
            st.warning("No structured field-season record exists yet. Add one in Fields & Operations before treating stage-specific decisions as field-specific.")
        else:
            cols = [c for c in ("season_year", "crop", "genotype", "sowing_date", "harvest_date", "status", "irrigation_system") if c in seasons]
            st.dataframe(seasons[cols], hide_index=True, width="stretch")
    if selected_country.casefold() == "mexico":
        st.info("For Mexico, local planting/calendar decisions should be checked against relevant official SIAP/INIFAP or equivalent local agronomic guidance. AGROLATTICE screening outputs are not an official sowing calendar.")
    else:
        st.info(f"For {selected_country}, confirm planting windows against the relevant local extension, research or official crop-calendar authority. Mexico-specific calendar assumptions are not used as global defaults.")
    _render_crop_profile_manager(profile_registry, crop_library, selected_country, season)
    st.divider()
    analysis = st.radio(
        "Crop & planting analysis",
        ["Daily sowing-date climate risk", "Daily weather & phenology", "Phenology service", "Planting & crop planning", "Seasonal suitability", "Suitability stability"],
        horizontal=True, key="crop_decision_crop_planting_analysis",
    )
    st.divider()
    if analysis == "Daily sowing-date climate risk":
        _render_daily_sowing_date_risk(field=field, season=season, cache_dir=cache_dir)
    else:
        callback = {
            "Daily weather & phenology": callbacks["daily_weather"],
            "Phenology service": callbacks["phenology"],
            "Planting & crop planning": callbacks["planning"],
            "Seasonal suitability": callbacks["suitability"],
            "Suitability stability": callbacks["stability"],
        }[analysis]
        callback()


def _render_water(
    *, field: Mapping[str, Any] | None, season: Mapping[str, Any] | None, root: Mapping[str, Any], field_tables: Mapping[str, pd.DataFrame],
    research: Mapping[str, pd.DataFrame], callbacks: Mapping[str, Callable[[], None]],
) -> None:
    _render_context_card(field, season, None)
    ks = pd.to_numeric(root.get("ks"), errors="coerce")
    operations = field_tables.get("operations", pd.DataFrame())
    irrigation_ops = pd.DataFrame()
    if isinstance(operations, pd.DataFrame) and not operations.empty:
        text = operations.get("category", pd.Series(dtype=str)).astype(str).str.casefold()
        irrigation_ops = operations.loc[text.str.contains("irrig", regex=False, na=False) | pd.to_numeric(operations.get("water_mm"), errors="coerce").fillna(0).gt(0)]
    decision_runs = research.get("decision_runs", pd.DataFrame())
    water_runs = decision_runs.loc[decision_runs.get("decision_type", pd.Series(dtype=str)).astype(str).str.contains("irrig|water", case=False, regex=True, na=False)] if not decision_runs.empty else pd.DataFrame()
    cards = st.columns(4)
    cards[0].metric("Saved root-zone Ks", "—" if pd.isna(ks) else f"{float(ks):.2f}")
    cards[1].metric("Recorded irrigation operations", len(irrigation_ops))
    cards[2].metric("Saved irrigation decision runs", len(water_runs))
    cards[3].metric("Irrigation system", str((season or {}).get("irrigation_system") or (field or {}).get("irrigation_system") or "Not set"))
    st.caption("Recorded irrigation, modelled water state and recommended irrigation remain separate evidence types.")
    view = st.radio("Water decision workspace", ["Root-zone water balance", "Irrigation policy & optimisation"], horizontal=True, key="crop_decision_water_view")
    st.divider()
    callbacks["soil_water"]() if view == "Root-zone water balance" else callbacks["decision_intelligence"]()


def _render_nutrition(
    *, field: Mapping[str, Any] | None, season: Mapping[str, Any] | None, field_tables: Mapping[str, pd.DataFrame], callbacks: Mapping[str, Callable[[], None]],
) -> None:
    _render_context_card(field, season, None)
    samples = field_tables.get("nutrients", pd.DataFrame())
    operations = field_tables.get("operations", pd.DataFrame())
    fert = pd.DataFrame()
    if isinstance(operations, pd.DataFrame) and not operations.empty:
        text = operations.get("category", pd.Series(dtype=str)).astype(str).str.casefold()
        fert = operations.loc[text.str.contains("fert|nutri", regex=True, na=False)]
    history = field_tables.get("history", pd.DataFrame())
    observed_outcomes = int(pd.to_numeric(history.get("yield_t_ha", pd.Series(dtype=float)), errors="coerce").notna().sum()) if isinstance(history, pd.DataFrame) and not history.empty else 0
    rate_series = pd.to_numeric(fert.get("rate", pd.Series(dtype=float)), errors="coerce") if isinstance(fert, pd.DataFrame) and not fert.empty else pd.Series(dtype=float)
    distinct_rates = int(rate_series.dropna().round(8).nunique())
    unique_dates = samples.get("sample_date", pd.Series(dtype=str)).nunique() if not samples.empty else 0
    readiness = "Not ready"
    if distinct_rates >= 3 and observed_outcomes >= 2:
        readiness = "Potentially analysable"
    elif distinct_rates >= 2 or observed_outcomes:
        readiness = "Partial evidence"
    cards = st.columns(5)
    cards[0].metric("Structured nutrient samples", len(samples))
    cards[1].metric("Recorded nutrient operations", len(fert))
    cards[2].metric("Distinct recorded rates", distinct_rates)
    cards[3].metric("Observed yield outcomes", observed_outcomes)
    cards[4].metric("Response readiness", readiness)
    st.warning("Soil/tissue nutrient concentration alone is not a fertilizer-rate recommendation. Optimisation requires measured N/P/K rate variation, defensible units/formulation, independent treatments and an outcome response under leakage-safe validation.")
    if readiness != "Potentially analysable":
        st.info("AGROLATTICE will not infer an N/P/K optimum from concentration data or one/few application rates. Use trial/Research Data Hub data with explicit elemental rates and outcomes when available.")
    if not samples.empty:
        cols = [c for c in ("sample_date", "sample_type", "nitrogen", "phosphorus", "potassium", "ph", "ec", "organic_matter") if c in samples]
        st.dataframe(samples[cols].head(100), hide_index=True, width="stretch")
    if not fert.empty:
        with st.expander("Recorded nutrient operations", expanded=False):
            st.dataframe(fert.head(100), hide_index=True, width="stretch")
    st.divider(); callbacks["decision_intelligence"]()


def _pest_models(models: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(models, pd.DataFrame) or models.empty:
        return pd.DataFrame()
    text = models.get("target", pd.Series(dtype=str)).astype(str) + " " + models.get("name", pd.Series(dtype=str)).astype(str) + " " + models.get("family", pd.Series(dtype=str)).astype(str)
    return models.loc[text.str.contains("pest|disease|insect", case=False, regex=True, na=False)].copy()


def _operational_pest_inference(
    *, field: Mapping[str, Any] | None, field_id: str | None, operational: pd.DataFrame, registry: Any,
    cache_dir: str | Path | None, app_root: str | Path | None,
) -> None:
    st.markdown("### Assess active-field environmental pest risk")
    if not field or not field_id:
        st.info("Select a mapped field before running operational pest-risk inference.")
        return
    if operational.empty:
        st.info("No pest/disease model is marked **Operationally eligible**. Prototype models remain available for development under Advanced, but Crop Decisions will not promote them to operational inference.")
        return
    if cache_dir is None or app_root is None:
        st.info("Runtime paths required for operational inference are unavailable.")
        return
    labels = {str(row["model_id"]): f"{row.get('name')} · {row.get('target')}" for _, row in operational.iterrows()}
    model_id = st.selectbox("Eligible model", list(labels), format_func=lambda value: labels[value], key="crop_decision_pest_operational_model")
    model_row = operational.loc[operational["model_id"].astype(str).eq(str(model_id))].iloc[0].to_dict()
    artifact = str(model_row.get("artifact_path") or "").strip()
    features = _loads(model_row.get("feature_names_json"), []) or []
    profile = _loads(model_row.get("applicability_json"), {}) or {}
    checks = st.columns(4)
    checks[0].metric("Model status", str(model_row.get("status") or "—"))
    checks[1].metric("Required predictors", len(features))
    checks[2].metric("Target", str(model_row.get("target") or "—"))
    checks[3].metric("Uncertainty", str(model_row.get("uncertainty_method") or "Not calibrated")[:28])
    if not artifact:
        st.warning("This model card has no loadable artifact path. Refit/register the model before operational use.")
        return
    artifact_path = Path(app_root) / artifact
    if not artifact_path.exists():
        st.warning(f"Registered model artifact is missing: {artifact}")
        return
    try:
        lat, lon = field_coordinates(field)
    except Exception as error:
        st.warning(f"The mapped field does not have usable coordinates: {error}")
        return
    controls = st.columns(3)
    end = controls[1].date_input("Environmental period end", value=date.today(), key="crop_decision_pest_end")
    start_default = max(date(1981, 1, 1), end - timedelta(days=42))
    start = controls[0].date_input("Environmental period start", value=start_default, max_value=end, key="crop_decision_pest_start")
    resolution = controls[2].selectbox("Prediction-row resolution", ["Weekly", "Daily", "Monthly"], key="crop_decision_pest_resolution")
    st.caption("The model receives only predictors it was trained on. AGROLATTICE will not fabricate morning/evening relative humidity, pest counts or other unavailable variables to force compatibility.")
    if st.button("Retrieve environmental evidence & assess risk", type="primary", width="stretch", key="crop_decision_pest_operational_run"):
        try:
            if start > end:
                raise ValueError("Start date must not be after end date.")
            acquired = fetch_canonical_nasa_weather(latitude=float(lat), longitude=float(lon), start_date=start, end_date=end, cache_dir=cache_dir)
            environmental = aggregate_daily_weather(acquired.frame, resolution)
            engineered, feature_meta = nasa_pest_covariates(environmental)
            missing = [feature for feature in features if feature not in engineered.columns]
            if missing:
                raise ValueError("Eligible model requires predictors unavailable from the selected NASA-compatible source: " + ", ".join(missing))
            import joblib
            model = joblib.load(artifact_path)
            X = engineered[features]
            predicted = model.predict(X)
            output = environmental.copy().reset_index(drop=True)
            for feature in features:
                if feature not in output.columns:
                    output[feature] = X[feature].reset_index(drop=True)
            output["Predicted pest class"] = predicted
            probabilities: dict[str, np.ndarray] = {}
            if hasattr(model, "predict_proba"):
                proba = np.asarray(model.predict_proba(X))
                classes = getattr(model, "classes_", None)
                if classes is None and hasattr(model, "named_steps"):
                    classes = getattr(model.named_steps.get("model"), "classes_", None)
                if classes is not None and proba.ndim == 2 and proba.shape[1] == len(classes):
                    for i, label in enumerate(classes):
                        probabilities[str(label)] = proba[:, i]
                        output[f"P({label})"] = proba[:, i]
                    output["Max class probability"] = proba.max(axis=1)
            app = applicability_score(X, profile)
            output = pd.concat([output, app.reset_index(drop=True)], axis=1)
            st.session_state["crop_decision_operational_pest_output"] = output
            st.session_state["crop_decision_operational_pest_context"] = {
                "model_id": model_id, "features": features, "feature_meta": feature_meta, "field_id": field_id,
                "resolution": resolution, "source_metadata": acquired.metadata,
            }
        except Exception as error:
            st.error(f"Operational pest-risk assessment failed: {type(error).__name__}: {error}")
    output = st.session_state.get("crop_decision_operational_pest_output")
    context = st.session_state.get("crop_decision_operational_pest_context") or {}
    if isinstance(output, pd.DataFrame) and not output.empty and str(context.get("model_id")) == str(model_id) and str(context.get("field_id")) == str(field_id):
        st.dataframe(output.tail(30), hide_index=True, width="stretch")
        latest = output.iloc[-1]
        status = str(latest.get("Applicability status") or "Unknown")
        pmax = pd.to_numeric(latest.get("Max class probability"), errors="coerce")
        summary = st.columns(4)
        summary[0].metric("Latest predicted class", str(latest.get("Predicted pest class")))
        summary[1].metric("Max class probability", "—" if pd.isna(pmax) else f"{float(pmax):.2f}")
        summary[2].metric("Applicability", status)
        summary[3].metric("Support score", f"{float(latest.get('Applicability score (%)', np.nan)):.0f}%" if pd.notna(pd.to_numeric(latest.get('Applicability score (%)'), errors='coerce')) else "—")
        if status != "Within support":
            st.warning("This prediction is not fully within the model's recorded training support. Do not promote it to an intervention without field confirmation and model review.")
        if st.button("Register latest pest-risk prediction", key="crop_decision_pest_register_latest"):
            label = str(latest.get("Predicted pest class"))
            class_probabilities = {}
            for column in output.columns:
                if str(column).startswith("P(") and str(column).endswith(")") and pd.notna(latest.get(column)):
                    class_probabilities[str(column)[2:-1]] = float(latest[column])
            pid = registry.save_prediction({
                "model_id": model_id, "entity_type": "Field", "entity_id": field_id, "field_id": field_id,
                "season_year": (field or {}).get("season_year"), "target": model_row.get("target"),
                "prediction_text": label, "class_probabilities": class_probabilities,
                "uncertainty_method": model_row.get("uncertainty_method") or "Class probabilities; calibration must be checked",
                "applicability_status": latest.get("Applicability status"), "applicability_score": latest.get("Applicability score (%)"),
                "input_snapshot": {feature: latest.get(feature) if feature in latest else None for feature in features},
                "provenance": {"source": "Crop Decisions operational pest-risk inference", "environmental_source": "NASA POWER canonical weather", "aggregation": context.get("resolution"), "app_version": "11.12", "scientific_boundary": "Risk prediction is not pest confirmation or disease diagnosis."},
            })
            st.success(f"Latest pest-risk prediction registered ({pid[:8]}).")


def _render_pest(
    *, field: Mapping[str, Any] | None, field_id: str | None, season: Mapping[str, Any] | None, field_tables: Mapping[str, pd.DataFrame], research: Mapping[str, pd.DataFrame], callbacks: Mapping[str, Callable[[], None]], registry: Any, cache_dir: str | Path | None, app_root: str | Path | None,
) -> None:
    _render_context_card(field, season, None)
    models = _pest_models(research.get("models", pd.DataFrame()))
    preds = research.get("predictions", pd.DataFrame())
    pest_preds = pd.DataFrame()
    if not preds.empty:
        pest_preds = preds.loc[preds.get("target", pd.Series(dtype=str)).astype(str).str.contains("pest|disease|insect", case=False, regex=True, na=False)]
    observations = field_tables.get("observations", pd.DataFrame())
    pest_obs = pd.DataFrame()
    if not observations.empty:
        pest_obs = observations.loc[observations.get("category", pd.Series(dtype=str)).astype(str).str.contains("pest|disease|insect", case=False, regex=True, na=False)]
    operational = models.loc[models.get("status", pd.Series(dtype=str)).astype(str).eq("Operationally eligible")] if not models.empty else pd.DataFrame()
    cards = st.columns(4)
    cards[0].metric("Pest/disease models", len(models))
    cards[1].metric("Operationally eligible", len(operational))
    cards[2].metric("Field-linked risk predictions", len(pest_preds))
    cards[3].metric("Pest/disease scouting records", len(pest_obs))
    st.info("**Risk prediction ≠ pest confirmation ≠ disease diagnosis.** Crop Decisions shows registered evidence first; model development remains a research workflow under Models & Evidence / advanced pest modelling.")
    _operational_pest_inference(field=field, field_id=field_id, operational=operational, registry=registry, cache_dir=cache_dir, app_root=app_root)
    if not pest_preds.empty:
        cols = [c for c in ("generated_at", "target", "prediction", "prediction_text", "lower_bound", "upper_bound", "applicability_status", "model_name", "model_status") if c in pest_preds]
        st.markdown("### Latest field risk evidence")
        st.dataframe(pest_preds[cols].head(10), hide_index=True, width="stretch")
    elif not operational.empty:
        st.warning("An operationally eligible pest model exists, but no saved field prediction is linked to this field. Run inference only after its required predictors and applicability checks are satisfied.")
    if not pest_obs.empty:
        with st.expander("Recent field observations", expanded=False):
            st.dataframe(pest_obs.head(50), hide_index=True, width="stretch")
    st.divider()
    with st.expander("Advanced · Build or validate an environmental pest model", expanded=False):
        callbacks["pest_builder"]()


def _render_yield_evidence(research: Mapping[str, pd.DataFrame], field_tables: Mapping[str, pd.DataFrame]) -> None:
    st.markdown("### Yield evidence comparison")
    predictions = research.get("predictions", pd.DataFrame())
    if not predictions.empty:
        yield_preds = predictions.loc[predictions.get("target", pd.Series(dtype=str)).astype(str).str.contains("yield|seed set|seed purity", case=False, regex=True, na=False)].copy()
    else:
        yield_preds = pd.DataFrame()
    history = field_tables.get("history", pd.DataFrame())
    rows: list[dict[str, Any]] = []
    if not yield_preds.empty:
        for _, row in yield_preds.head(30).iterrows():
            value = row.get("prediction") if pd.notna(pd.to_numeric(row.get("prediction"), errors="coerce")) else row.get("prediction_text")
            rows.append({
                "Evidence": "Registered prediction", "Source / model": row.get("model_name") or row.get("model_family"),
                "Target": row.get("target"), "Value": value, "Lower": row.get("lower_bound"), "Upper": row.get("upper_bound"),
                "Validation status": row.get("model_status"), "Applicability": row.get("applicability_status"), "When": row.get("generated_at"),
            })
    if isinstance(history, pd.DataFrame) and not history.empty and "yield_t_ha" in history:
        for _, row in history.loc[pd.to_numeric(history["yield_t_ha"], errors="coerce").notna()].head(15).iterrows():
            rows.append({
                "Evidence": "Observed harvest", "Source / model": "Field crop history", "Target": "Yield",
                "Value": row.get("yield_t_ha"), "Lower": None, "Upper": None, "Validation status": "Observed", "Applicability": "Field outcome", "When": row.get("harvest_date") or row.get("season_year"),
            })
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        if len({str(r.get('Source / model')) for r in rows if r.get('Evidence') == 'Registered prediction'}) > 1:
            st.caption("Different model estimates are intentionally not averaged. Model disagreement is evidence and should be investigated against inputs, calibration and validation scope.")
    else:
        st.info("No field-linked observed yield or registered yield prediction is available yet.")


def _render_yield_economics(
    *, field: Mapping[str, Any] | None, season: Mapping[str, Any] | None, field_tables: Mapping[str, pd.DataFrame], research: Mapping[str, pd.DataFrame], callbacks: Mapping[str, Callable[[], None]],
) -> None:
    _render_context_card(field, season, None)
    _render_yield_evidence(research, field_tables)
    operations = field_tables.get("operations", pd.DataFrame())
    if isinstance(operations, pd.DataFrame) and not operations.empty:
        cost = pd.to_numeric(operations.get("cost"), errors="coerce").sum(min_count=1)
        water = pd.to_numeric(operations.get("water_mm"), errors="coerce").sum(min_count=1)
        st.caption(f"Recorded operations context: cost total {('—' if pd.isna(cost) else f'{float(cost):,.2f}')} · recorded irrigation depth {('—' if pd.isna(water) else f'{float(water):,.1f} mm')}. These are historical records, not automatically complete production economics.")
    view = st.radio("Yield & economics tool", ["Climate yield-potential screening", "Water productivity & economics"], horizontal=True, key="crop_decision_yield_econ_view")
    st.divider(); callbacks["yield_screen"]() if view.startswith("Climate") else callbacks["economics"]()


def _render_model_guide(field: Mapping[str, Any] | None, season: Mapping[str, Any] | None, research: Mapping[str, pd.DataFrame]) -> None:
    crop = str((season or {}).get("crop") or (field or {}).get("crop") or "crop")
    st.markdown("### Which model should I use?")
    guide = pd.DataFrame([
        ["Transparent climate screening", "Limited local outcome data; pre-season environmental screening", "Not a calibrated yield forecast"],
        ["Root-zone / AquaCrop", "Water-focused field-season simulation with weather, crop and soil inputs", "Calibrate soil/crop/management before predictive use"],
        ["Mechanistic Maize Twin", "Maize flowering / parent synchrony", "Timing model; does not guarantee pollen amount, purity or yield"],
        ["DSSAT / APSIM", "Detailed process modelling when cultivar, soil and management files are defensible", "External model configuration must be reviewed"],
        ["Registered ML model", "Local prediction when validation and applicability support the active field", "Use status and applicability; do not promote a prototype"],
    ], columns=["Model family", "Best fit", "Scientific boundary"])
    st.dataframe(guide, hide_index=True, width="stretch")
    models = research.get("models", pd.DataFrame())
    if not models.empty:
        relevant = models.loc[models.get("target", pd.Series(dtype=str)).astype(str).str.contains("yield|phenology|flower|water|pest", case=False, regex=True, na=False)]
        if not relevant.empty:
            st.markdown(f"### Registered models potentially relevant to {crop}")
            cols = [c for c in ("name", "family", "target", "status", "source_method", "implementation_type", "updated_at") if c in relevant]
            st.dataframe(relevant[cols].head(30), hide_index=True, width="stretch")


def _render_crop_models(
    *, field: Mapping[str, Any] | None, season: Mapping[str, Any] | None, research: Mapping[str, pd.DataFrame], callbacks: Mapping[str, Callable[[], None]],
) -> None:
    _render_context_card(field, season, None)
    _render_model_guide(field, season, research)
    view = st.radio("Crop model workflow", ["AquaCrop", "DSSAT & APSIM"], horizontal=True, key="crop_decision_model_view")
    st.divider(); callbacks["aquacrop"]() if view == "AquaCrop" else callbacks["external_models"]()


def _render_recommendations(
    *, field: Mapping[str, Any] | None, season: Mapping[str, Any] | None, field_id: str | None, registry: Any, research: Mapping[str, pd.DataFrame], callbacks: Mapping[str, Callable[[], None]],
) -> None:
    _render_context_card(field, season, None)
    recs = research.get("recommendations", pd.DataFrame())
    outcomes = research.get("outcomes", pd.DataFrame())
    st.markdown("### Recommendation → action → outcome")
    if recs.empty:
        st.info("No recommendations linked to this field. Optimisation/model outputs are not automatically converted to agronomic recommendations.")
    else:
        status_counts = recs.get("status", pd.Series(dtype=str)).astype(str).value_counts()
        cols = st.columns(5)
        for col, status in zip(cols, ["Proposed", "Accepted", "Applied", "Completed", "Rejected"]):
            col.metric(status, int(status_counts.get(status, 0)))
        display = [c for c in ("recommendation_id", "created_at", "action_type", "action_text", "proposed_time", "amount", "unit", "status", "expected_effect") if c in recs]
        st.dataframe(recs[display].head(100), hide_index=True, width="stretch")
        outcome_ids = set(outcomes.get("recommendation_id", pd.Series(dtype=str)).astype(str)) if not outcomes.empty else set()
        applied = recs.loc[recs.get("status", pd.Series(dtype=str)).astype(str).str.casefold().isin({"accepted", "applied", "completed"})]
        pending = applied.loc[~applied["recommendation_id"].astype(str).isin(outcome_ids)] if "recommendation_id" in applied else pd.DataFrame()
        if not pending.empty:
            st.warning(f"{len(pending)} accepted/applied/completed recommendation(s) still have no linked measured outcome.")
    st.caption("The detailed Recommendation Trials and Causal Audit tools below preserve treatment status history, actual action, measured outcome, overlap diagnostics and causal assumptions.")
    st.divider(); callbacks["decision_intelligence"]()


def render_crop_decision_command_centre(
    *,
    field_db: Any,
    twin_db: Any,
    registry: Any,
    profile_registry: Any,
    crop_library: Mapping[str, Any],
    selected_country: str,
    app_version: str,
    active_field_id: str | None,
    cache_dir: str | Path | None = None,
    app_root: str | Path | None = None,
    callbacks: Mapping[str, Callable[[], None]],
) -> None:
    field_id, field = _active_field(field_db, active_field_id)
    season = _active_season(field_db, field_id, field)
    link = _twin_link(twin_db, field_id)
    snapshot, state = _twin_snapshot(twin_db, link)
    twin_records = _latest_twin_records(twin_db, link)
    root = _root_zone_summary(twin_db, link)
    field_tables = _field_tables(field_db, field_id)
    research = _research_tables(registry, field_id)

    if field:
        _render_context_card(field, season, link)
    else:
        st.caption("Crop Decisions can still run global/screening tools, but a mapped active field is required for the integrated decision workflow.")

    options = [
        "Overview", "Crop & planting", "Water & irrigation", "Nutrition", "Pest & crop health",
        "Yield & economics", "Crop models", "Recommendations & outcomes",
    ]
    current = consume_view_request(
        st.session_state,
        request_key="crop_decision_command_view_request",
        widget_key="crop_decision_command_view_radio",
        mirror_key="crop_decision_command_view",
        options=options,
        default="Overview",
    )
    selected = st.radio("Decision area", options, index=options.index(current), horizontal=True, key="crop_decision_command_view_radio")
    st.session_state["crop_decision_command_view"] = selected
    st.divider()

    notice = st.session_state.get("crop_decision_navigation_notice")
    if isinstance(notice, Mapping) and notice.get("area") == selected:
        st.info(f"Opened from priority action: **{notice.get('title', 'Priority action')}**\n\n{notice.get('detail', '')}")
        st.session_state.pop("crop_decision_navigation_notice", None)

    if selected == "Overview":
        _render_overview(field=field, season=season, link=link, state=state, twin_records=twin_records, root=root, field_tables=field_tables, research=research)
    elif selected == "Crop & planting":
        _render_crop_planting(field_db=field_db, field_id=field_id, field=field, season=season, profile_registry=profile_registry, crop_library=crop_library, selected_country=selected_country, cache_dir=cache_dir, callbacks=callbacks)
    elif selected == "Water & irrigation":
        _render_water(field=field, season=season, root=root, field_tables=field_tables, research=research, callbacks=callbacks)
    elif selected == "Nutrition":
        _render_nutrition(field=field, season=season, field_tables=field_tables, callbacks=callbacks)
    elif selected == "Pest & crop health":
        _render_pest(field=field, field_id=field_id, season=season, field_tables=field_tables, research=research, callbacks=callbacks, registry=registry, cache_dir=cache_dir, app_root=app_root)
    elif selected == "Yield & economics":
        _render_yield_economics(field=field, season=season, field_tables=field_tables, research=research, callbacks=callbacks)
    elif selected == "Crop models":
        _render_crop_models(field=field, season=season, research=research, callbacks=callbacks)
    else:
        _render_recommendations(field=field, season=season, field_id=field_id, registry=registry, research=research, callbacks=callbacks)

    st.divider()
    st.caption(
        f"Crop Decision Command Centre {MODULE_VERSION} · {selected_country} workspace · {app_version}. "
        "Opening the workspace does not automatically fetch weather/EO, fit models, run crop simulations or execute an optimisation."
    )
