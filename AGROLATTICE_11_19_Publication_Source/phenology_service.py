"""Central phenology service for AGROLATTICE 11.4.

The service keeps observed events, generic thermal-time estimates and the
Release 11.0 mechanistic maize model distinct.  A consensus record is a
traceable summary of available evidence, not a claim that disagreements have
been resolved biologically.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from daily_weather_phenology import calculate_daily_gdd
from maize_mechanistic_twin import (
    DEFAULT_PHYSIOLOGY,
    MechanisticMaizeError,
    PhysiologyParameters,
    simulate_event_uncertainty,
    simulate_mfs,
)

MODULE_VERSION = "1.0.0"


class PhenologyServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class PhenologyEstimate:
    source: str
    method: str
    stage: str
    stage_probability: float | None
    accumulated_gdd: float | None
    next_stage: str | None
    gdd_to_next_stage: float | None
    predicted_date: str | None
    lower_date: str | None
    upper_date: str | None
    evidence_type: str
    notes: str | None = None


def _date_column(frame: pd.DataFrame) -> str:
    for name in ("DATE", "Date", "date", "weather_date"):
        if name in frame.columns:
            return name
    raise PhenologyServiceError("Daily weather needs a date column.")


def harmonise_weather_for_gdd(
    weather: pd.DataFrame,
    *,
    base_temperature_c: float,
    upper_temperature_c: float | None = None,
) -> pd.DataFrame:
    if weather is None or weather.empty:
        raise PhenologyServiceError("Daily weather is required.")
    frame = weather.copy()
    dcol = _date_column(frame)
    frame["Date"] = pd.to_datetime(frame[dcol], errors="coerce").dt.normalize()

    def numeric(candidates: Sequence[str]) -> pd.Series:
        for column in candidates:
            if column in frame:
                return pd.to_numeric(frame[column], errors="coerce")
        return pd.Series(np.nan, index=frame.index, dtype=float)

    tmean = numeric(("TMEAN_C", "T2M", "TEMPERATURE", "tmean_c", "Temperature"))
    tmax = numeric(("TMAX_C", "T2M_MAX", "TEMPERATURE_MAX", "tmax_c", "Maximum temperature"))
    tmin = numeric(("TMIN_C", "T2M_MIN", "TEMPERATURE_MIN", "tmin_c", "Minimum temperature"))
    tmean = tmean.fillna((tmax + tmin) / 2.0)
    frame["GDD daily"] = calculate_daily_gdd(
        tmean,
        tmax,
        tmin,
        base_temperature_c=float(base_temperature_c),
        upper_temperature_c=upper_temperature_c,
        method="modified_average",
    )
    frame = frame.dropna(subset=["Date"]).sort_values("Date").drop_duplicates("Date", keep="last")
    return frame[["Date", "GDD daily"]].reset_index(drop=True)


def thermal_time_since_planting(
    weather: pd.DataFrame,
    planting_date: Any,
    *,
    as_of: Any | None = None,
    base_temperature_c: float,
    upper_temperature_c: float | None = None,
) -> float:
    prepared = harmonise_weather_for_gdd(weather, base_temperature_c=base_temperature_c, upper_temperature_c=upper_temperature_c)
    planting = pd.Timestamp(planting_date).normalize()
    cutoff = pd.Timestamp(as_of).normalize() if as_of is not None else prepared["Date"].max()
    selected = prepared.loc[prepared["Date"].between(planting, cutoff), "GDD daily"]
    return float(selected.fillna(0).sum())


def generic_gdd_stage_estimate(
    weather: pd.DataFrame,
    planting_date: Any,
    stage_targets: Mapping[str, float],
    *,
    as_of: Any | None = None,
    base_temperature_c: float,
    upper_temperature_c: float | None = None,
) -> PhenologyEstimate:
    if not stage_targets:
        raise PhenologyServiceError("At least one stage GDD target is required.")
    accumulated = thermal_time_since_planting(
        weather, planting_date, as_of=as_of,
        base_temperature_c=base_temperature_c, upper_temperature_c=upper_temperature_c,
    )
    ordered = sorted(((str(stage), float(target)) for stage, target in stage_targets.items()), key=lambda item: item[1])
    reached = [item for item in ordered if accumulated >= item[1]]
    current = reached[-1][0] if reached else "Pre-emergence / before first supplied stage"
    next_items = [item for item in ordered if item[1] > accumulated]
    next_stage, gdd_to_next = (next_items[0][0], max(0.0, next_items[0][1] - accumulated)) if next_items else (None, None)

    predicted_date = None
    if next_items:
        prepared = harmonise_weather_for_gdd(weather, base_temperature_c=base_temperature_c, upper_temperature_c=upper_temperature_c)
        planting = pd.Timestamp(planting_date).normalize()
        subset = prepared.loc[prepared["Date"].ge(planting)].copy()
        subset["Cumulative GDD"] = subset["GDD daily"].fillna(0).cumsum()
        hit = subset.loc[subset["Cumulative GDD"].ge(next_items[0][1]), "Date"]
        predicted_date = hit.iloc[0].date().isoformat() if not hit.empty else None
    return PhenologyEstimate(
        source="Thermal-time service",
        method="User/validated crop GDD thresholds",
        stage=current,
        stage_probability=None,
        accumulated_gdd=accumulated,
        next_stage=next_stage,
        gdd_to_next_stage=gdd_to_next,
        predicted_date=predicted_date,
        lower_date=None,
        upper_date=None,
        evidence_type="Model output",
        notes="Threshold-based phenology is an estimate and should be checked against crop observations.",
    )


def mechanistic_maize_estimate(
    weather: pd.DataFrame,
    sowing_date: Any,
    *,
    role: str,
    parameters: PhysiologyParameters = DEFAULT_PHYSIOLOGY,
    as_of: Any | None = None,
    uncertainty_draws: int = 500,
) -> tuple[PhenologyEstimate, pd.DataFrame, dict[str, Any]]:
    prepared = harmonise_weather_for_gdd(weather, base_temperature_c=10.0, upper_temperature_c=30.0)
    simulation, summary = simulate_mfs(prepared, sowing_date, parameters)
    cutoff = pd.Timestamp(as_of).normalize() if as_of is not None else simulation["Date"].max()
    current_rows = simulation.loc[simulation["Date"].le(cutoff)]
    row = current_rows.iloc[-1] if not current_rows.empty else simulation.iloc[0]
    role_key = str(role).casefold()
    if role_key.startswith("m"):
        stage = "Anthesis" if bool(row["Anthesis reached"]) else ("Final-leaf development" if float(row["Predicted collared leaf number"]) >= parameters.tln * 0.95 else "Vegetative")
        event_name = "Anthesis"
        predicted = summary.get("Anthesis date")
    else:
        stage = "Silking" if bool(row["Silking reached"]) else ("Ear growth" if bool(row["Ear growth active"]) else "Vegetative")
        event_name = "50% silking"
        predicted = summary.get("Silking date")
    uncertainty = {}
    lower = upper = None
    try:
        _, uncertainty = simulate_event_uncertainty(prepared, sowing_date, parameters, role, draws=uncertainty_draws)
        predicted = uncertainty.get("Median event date") or predicted
        lower = uncertainty.get("P05 event date")
        upper = uncertainty.get("P95 event date")
    except MechanisticMaizeError as error:
        uncertainty = {"warning": str(error)}
    estimate = PhenologyEstimate(
        source="Mechanistic Maize Twin",
        method="Laurent et al. (2025)-inspired disclosed MFS equations",
        stage=stage,
        stage_probability=None,
        accumulated_gdd=float(row.get("Planting cumulative GDD", np.nan)),
        next_stage=None if stage == event_name else event_name,
        gdd_to_next_stage=None,
        predicted_date=predicted,
        lower_date=lower,
        upper_date=upper,
        evidence_type="Model output",
        notes="Publication priors are not measurements of local parent lines; timing does not guarantee pollen quantity or seed purity.",
    )
    return estimate, simulation, {**summary, "uncertainty": uncertainty}


def observed_event_estimates(events: pd.DataFrame, *, date_column: str = "Date", stage_column: str = "Stage") -> list[PhenologyEstimate]:
    if events is None or events.empty or date_column not in events or stage_column not in events:
        return []
    rows = []
    for _, record in events.iterrows():
        observed = pd.to_datetime(record.get(date_column), errors="coerce")
        stage = str(record.get(stage_column) or "").strip()
        if pd.isna(observed) or not stage:
            continue
        rows.append(PhenologyEstimate(
            source="Field observation",
            method="Observed phenology event",
            stage=stage,
            stage_probability=1.0,
            accumulated_gdd=None,
            next_stage=None,
            gdd_to_next_stage=None,
            predicted_date=observed.date().isoformat(),
            lower_date=None,
            upper_date=None,
            evidence_type="Measured",
            notes=None,
        ))
    return rows


def consensus_table(estimates: Sequence[PhenologyEstimate]) -> pd.DataFrame:
    records = []
    for estimate in estimates:
        records.append({
            "Source": estimate.source,
            "Method": estimate.method,
            "Evidence type": estimate.evidence_type,
            "Stage": estimate.stage,
            "Stage probability": estimate.stage_probability,
            "Accumulated GDD": estimate.accumulated_gdd,
            "Next stage": estimate.next_stage,
            "GDD to next stage": estimate.gdd_to_next_stage,
            "Date / median forecast": estimate.predicted_date,
            "Lower date": estimate.lower_date,
            "Upper date": estimate.upper_date,
            "Notes": estimate.notes,
        })
    return pd.DataFrame(records)


def disagreement_summary(estimates: Sequence[PhenologyEstimate]) -> dict[str, Any]:
    dates = []
    stages = []
    for estimate in estimates:
        if estimate.predicted_date:
            value = pd.to_datetime(estimate.predicted_date, errors="coerce")
            if pd.notna(value):
                dates.append(value)
        if estimate.stage:
            stages.append(estimate.stage)
    date_range = None
    if len(dates) >= 2:
        date_range = int((max(dates) - min(dates)).days)
    return {
        "sources": int(len(estimates)),
        "distinct_stage_labels": int(len(set(stages))),
        "forecast_date_range_days": date_range,
        "interpretation": "Differences between observed, mechanistic and learned/threshold estimates are evidence to investigate, not values to average automatically.",
    }
