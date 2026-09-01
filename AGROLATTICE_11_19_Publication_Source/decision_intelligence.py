"""Decision intelligence, optimisation and causal-audit utilities introduced in AGROLATTICE 11.5 and carried forward in 11.6.

This module deliberately separates prediction from decision support.  It provides
transparent policy/scenario comparison, Pareto screening, scalar state
assimilation and observational treatment-effect diagnostics.  It does not send
commands to irrigation/fertiliser hardware and does not convert observational
associations into causal facts.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, KFold, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

from soil_water_balance import (
    IrrigationStrategy,
    SoilProfile,
    assign_stage_parameters,
    build_stage_schedule,
    crop_root_defaults,
    prepare_daily_weather,
    simulate_root_zone_balance,
    summarise_season,
    whole_season_ky,
)

MODULE_VERSION = "1.0.0"


class DecisionIntelligenceError(RuntimeError):
    """Raised when a decision analysis cannot be evaluated safely."""


@dataclass(frozen=True)
class IrrigationPolicyResult:
    table: pd.DataFrame
    details: dict[str, pd.DataFrame]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class NutrientModelResult:
    model: Any
    metrics: dict[str, float]
    validation_rows: pd.DataFrame
    feature_columns: list[str]
    target_column: str
    group_column: str | None
    n_column: str
    p_column: str
    k_column: str


@dataclass(frozen=True)
class CausalAuditResult:
    estimate: float
    lower_bound: float | None
    upper_bound: float | None
    method: str
    diagnostics: dict[str, Any]
    balance: pd.DataFrame
    unit_effects: pd.DataFrame
    placebo_p_value: float | None = None


def _finite(value: Any, default: float = np.nan) -> float:
    number = pd.to_numeric(value, errors="coerce")
    return float(number) if pd.notna(number) and np.isfinite(float(number)) else float(default)


def _normalise(values: pd.Series, *, higher_is_better: bool) -> pd.Series:
    series = pd.to_numeric(values, errors="coerce").astype(float)
    finite = series[np.isfinite(series)]
    if finite.empty:
        return pd.Series(np.nan, index=series.index, dtype=float)
    lo, hi = float(finite.min()), float(finite.max())
    if abs(hi - lo) < 1e-12:
        result = pd.Series(1.0, index=series.index, dtype=float)
    else:
        result = (series - lo) / (hi - lo)
    return result if higher_is_better else 1.0 - result


def pareto_mask(frame: pd.DataFrame, objectives: Sequence[tuple[str, str]]) -> pd.Series:
    """Return a non-dominated mask for mixed maximise/minimise objectives."""
    if frame is None or frame.empty:
        return pd.Series(dtype=bool)
    matrix = []
    valid = pd.Series(True, index=frame.index)
    for column, direction in objectives:
        if column not in frame:
            raise DecisionIntelligenceError(f"Pareto objective column {column!r} is missing.")
        values = pd.to_numeric(frame[column], errors="coerce").astype(float)
        valid &= np.isfinite(values)
        matrix.append(values.to_numpy() * (1.0 if str(direction).lower().startswith("max") else -1.0))
    if not matrix:
        return pd.Series(False, index=frame.index)
    arr = np.column_stack(matrix)
    mask = np.zeros(len(frame), dtype=bool)
    valid_pos = np.flatnonzero(valid.to_numpy())
    for i in valid_pos:
        candidate = arr[i]
        others = arr[valid_pos]
        dominated = np.any(np.all(others >= candidate, axis=1) & np.any(others > candidate, axis=1))
        mask[i] = not dominated
    return pd.Series(mask, index=frame.index)


def build_crop_daily_drivers(
    weather: pd.DataFrame,
    *,
    latitude: float,
    crop_library: Mapping[str, Any],
    crop: str,
    profile: str,
    planting_date: Any,
    duration_strategy: str = "Midpoint",
    custom_season_days: int = 120,
    constant_kc: float | None = None,
    constant_p: float | None = None,
    initial_root_depth_m: float | None = None,
    maximum_root_depth_m: float | None = None,
    dynamic_root_growth: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Prepare daily crop/root-zone drivers from NASA-compatible daily weather."""
    daily = prepare_daily_weather(weather, float(latitude))
    schedule = build_stage_schedule(
        crop_library,
        crop,
        profile,
        planting_date,
        duration_strategy=duration_strategy,
        custom_season_days=int(custom_season_days),
        constant_kc=constant_kc,
        constant_p=constant_p,
    )
    defaults = crop_root_defaults(crop)
    root_min = float(initial_root_depth_m if initial_root_depth_m is not None else defaults["root_min_m"])
    root_max = float(maximum_root_depth_m if maximum_root_depth_m is not None else defaults["root_max_m"])
    fallback_p = float(constant_p if constant_p is not None else defaults.get("p", 0.5))
    drivers = assign_stage_parameters(
        daily,
        schedule,
        fallback_p=fallback_p,
        initial_root_depth_m=root_min,
        maximum_root_depth_m=root_max,
        dynamic_root_growth=bool(dynamic_root_growth),
    )
    metadata = {
        "crop": crop,
        "profile": profile,
        "planting_date": str(pd.Timestamp(planting_date).date()),
        "duration_strategy": duration_strategy,
        "root_min_m": root_min,
        "root_max_m": root_max,
        "fallback_p": fallback_p,
        "whole_season_ky": whole_season_ky(crop_library, crop, profile),
        "scientific_note": "Daily drivers use FAO-56 ETo/root-zone logic and the selected validated/user-supplied crop parameters.",
    }
    return drivers, schedule, metadata


def generate_irrigation_strategies(
    *,
    application_efficiency: float = 0.85,
    max_gross_application_mm: float = 60.0,
    trigger_values: Sequence[float] = (0.7, 0.9, 1.0, 1.2),
    refill_values: Sequence[float] = (0.4, 0.6, 0.8, 1.0),
    fixed_intervals: Sequence[int] = (3, 5, 7, 10),
    fixed_depths_mm: Sequence[float] = (15.0, 25.0, 35.0),
    include_rainfed: bool = True,
    include_raw: bool = True,
    include_deficit: bool = True,
    include_fixed: bool = True,
) -> list[tuple[str, IrrigationStrategy]]:
    """Create a transparent candidate set rather than a hidden optimiser."""
    eff = float(application_efficiency)
    max_app = float(max_gross_application_mm)
    candidates: list[tuple[str, IrrigationStrategy]] = []
    if include_rainfed:
        candidates.append(("Rainfed", IrrigationStrategy(mode="Rainfed", application_efficiency=eff, maximum_gross_application_mm=max_app)))
    if include_raw:
        for trigger in trigger_values:
            candidates.append((
                f"RAW trigger {float(trigger):.2f}× · full refill",
                IrrigationStrategy(
                    mode="Irrigate at RAW", application_efficiency=eff,
                    trigger_fraction_of_raw=float(trigger), refill_fraction=1.0,
                    maximum_gross_application_mm=max_app,
                ),
            ))
    if include_deficit:
        for trigger in trigger_values:
            for refill in refill_values:
                if refill >= 0.999:
                    continue
                candidates.append((
                    f"Deficit {float(trigger):.2f}× RAW · refill {float(refill):.0%}",
                    IrrigationStrategy(
                        mode="Deficit irrigation", application_efficiency=eff,
                        trigger_fraction_of_raw=float(trigger), refill_fraction=float(refill),
                        maximum_gross_application_mm=max_app,
                    ),
                ))
    if include_fixed:
        for interval in fixed_intervals:
            for depth in fixed_depths_mm:
                candidates.append((
                    f"Fixed every {int(interval)} d · {float(depth):.0f} mm gross",
                    IrrigationStrategy(
                        mode="Fixed interval", application_efficiency=eff,
                        fixed_interval_days=int(interval), fixed_gross_application_mm=float(depth),
                        maximum_gross_application_mm=max_app,
                    ),
                ))
    return candidates


def evaluate_irrigation_policies(
    daily_drivers: pd.DataFrame,
    soil: SoilProfile,
    strategies: Sequence[tuple[str, IrrigationStrategy]],
    *,
    seasonal_ky: float | None = None,
    initial_depletion_fraction: float = 0.20,
    runoff_method: str = "None",
    runoff_fraction: float = 0.0,
    curve_number: float = 75.0,
    capillary_rise_mm_day: float = 0.0,
    adjust_p_for_etc: bool = True,
    potential_yield_t_ha: float | None = None,
    crop_price_per_t: float | None = None,
    water_cost_per_m3: float | None = None,
    fixed_event_cost_per_ha: float = 0.0,
    sensor_irrigation_readings: pd.DataFrame | None = None,
    seasonal_water_limit_mm: float | None = None,
    maximum_irrigation_events: int | None = None,
) -> IrrigationPolicyResult:
    if daily_drivers is None or daily_drivers.empty:
        raise DecisionIntelligenceError("No daily crop/root-zone drivers were supplied.")
    if not strategies:
        raise DecisionIntelligenceError("At least one irrigation strategy is required.")
    summaries: list[dict[str, Any]] = []
    details: dict[str, pd.DataFrame] = {}
    for label, strategy in strategies:
        balance = simulate_root_zone_balance(
            daily_drivers, soil, strategy,
            initial_depletion_fraction=float(initial_depletion_fraction),
            runoff_method=runoff_method, runoff_fraction=float(runoff_fraction),
            curve_number=float(curve_number), capillary_rise_mm_day=float(capillary_rise_mm_day),
            adjust_p_for_etc=bool(adjust_p_for_etc),
            sensor_irrigation_readings=sensor_irrigation_readings if strategy.mode == "Sensor-triggered" else None,
        )
        summary = summarise_season(balance, seasonal_ky=seasonal_ky)
        gross_mm = _finite(summary.get("Gross irrigation (mm)"), 0.0)
        events = int(_finite(summary.get("Irrigation events"), 0.0))
        relative_yield = _finite(summary.get("Relative yield factor"))
        et_satisfaction = _finite(summary.get("ET satisfaction (%)"))
        row = {
            "Policy": label,
            "Mode": strategy.mode,
            "Gross irrigation (mm)": gross_mm,
            "Irrigation events": events,
            "Stress days": int(_finite(summary.get("Stress days"), 0)),
            "Severe stress days": int(_finite(summary.get("Severe stress days"), 0)),
            "Minimum Ks": _finite(summary.get("Minimum Ks")),
            "ET satisfaction (%)": et_satisfaction,
            "Deep percolation (mm)": _finite(summary.get("Deep percolation (mm)"), 0.0),
            "End depletion (mm)": _finite(summary.get("End depletion (mm)")),
            "Relative yield factor": relative_yield,
            "Strategy JSON": asdict(strategy),
        }
        if potential_yield_t_ha is not None and np.isfinite(relative_yield):
            row["Yield proxy (t/ha)"] = float(potential_yield_t_ha) * relative_yield
        else:
            row["Yield proxy (t/ha)"] = np.nan
        if water_cost_per_m3 is not None:
            # 1 mm over 1 ha = 10 m3.
            water_cost = gross_mm * 10.0 * float(water_cost_per_m3)
            row["Water cost (/ha)"] = water_cost
        else:
            water_cost = 0.0
            row["Water cost (/ha)"] = np.nan
        operation_cost = events * float(fixed_event_cost_per_ha)
        row["Event cost (/ha)"] = operation_cost if fixed_event_cost_per_ha else np.nan
        if crop_price_per_t is not None and np.isfinite(row["Yield proxy (t/ha)"]):
            revenue = row["Yield proxy (t/ha)"] * float(crop_price_per_t)
            row["Gross revenue (/ha)"] = revenue
            row["Irrigation-adjusted margin (/ha)"] = revenue - water_cost - operation_cost
        else:
            row["Gross revenue (/ha)"] = np.nan
            row["Irrigation-adjusted margin (/ha)"] = np.nan
        summaries.append(row)
        details[label] = balance
    table = pd.DataFrame(summaries)
    feasible = pd.Series(True, index=table.index, dtype=bool)
    constraint_notes: list[list[str]] = [[] for _ in range(len(table))]
    if seasonal_water_limit_mm is not None:
        water_limit = float(seasonal_water_limit_mm)
        if water_limit < 0:
            raise DecisionIntelligenceError("Seasonal irrigation-water limit cannot be negative.")
        exceeded = pd.to_numeric(table["Gross irrigation (mm)"], errors="coerce") > water_limit + 1e-9
        feasible &= ~exceeded
        for pos in np.flatnonzero(exceeded.to_numpy()):
            constraint_notes[pos].append(f"seasonal water > {water_limit:g} mm")
    if maximum_irrigation_events is not None:
        event_limit = int(maximum_irrigation_events)
        if event_limit < 0:
            raise DecisionIntelligenceError("Maximum irrigation events cannot be negative.")
        exceeded = pd.to_numeric(table["Irrigation events"], errors="coerce") > event_limit
        feasible &= ~exceeded
        for pos in np.flatnonzero(exceeded.to_numpy()):
            constraint_notes[pos].append(f"events > {event_limit}")
    table["Feasible"] = feasible
    table["Constraint note"] = ["; ".join(notes) if notes else "Within configured constraints" for notes in constraint_notes]
    yield_basis = "Relative yield factor" if table["Relative yield factor"].notna().any() else "ET satisfaction (%)"
    table["Pareto"] = False
    if feasible.any():
        table.loc[feasible, "Pareto"] = pareto_mask(
            table.loc[feasible], [(yield_basis, "max"), ("Gross irrigation (mm)", "min"), ("Deep percolation (mm)", "min")]
        )
    table["Water-saving score"] = _normalise(table["Gross irrigation (mm)"], higher_is_better=False)
    table["Yield-protection score"] = _normalise(table[yield_basis], higher_is_better=True)
    table["Loss-control score"] = _normalise(table["Deep percolation (mm)"], higher_is_better=False)
    table["Balanced score"] = table[["Water-saving score", "Yield-protection score", "Loss-control score"]].mean(axis=1)
    if table["Irrigation-adjusted margin (/ha)"].notna().any():
        table["Profit score"] = _normalise(table["Irrigation-adjusted margin (/ha)"], higher_is_better=True)
    else:
        table["Profit score"] = np.nan
    metadata = {
        "candidate_count": len(table),
        "pareto_count": int(table["Pareto"].sum()),
        "yield_basis": yield_basis,
        "seasonal_ky": seasonal_ky,
        "economic_inputs_present": bool(crop_price_per_t is not None and potential_yield_t_ha is not None),
        "seasonal_water_limit_mm": seasonal_water_limit_mm,
        "maximum_irrigation_events": maximum_irrigation_events,
        "feasible_count": int(table["Feasible"].sum()),
        "scientific_note": "This is a scenario/policy comparison using the AGROLATTICE FAO-style root-zone model. Relative yield is a Ky water-stress proxy when a seasonal Ky exists, not a calibrated yield forecast.",
    }
    return IrrigationPolicyResult(table=table, details=details, metadata=metadata)


def select_irrigation_policy(table: pd.DataFrame, objective: str) -> pd.Series:
    if table is None or table.empty:
        raise DecisionIntelligenceError("No irrigation policy table is available.")
    candidate_table = table.loc[table["Feasible"].astype(bool)].copy() if "Feasible" in table else table.copy()
    if candidate_table.empty:
        raise DecisionIntelligenceError("No irrigation policy satisfies the configured operational/resource constraints.")
    key = str(objective).casefold()
    if "profit" in key and candidate_table.get("Profit score", pd.Series(dtype=float)).notna().any():
        column = "Profit score"
    elif "water" in key:
        column = "Water-saving score"
    elif "yield" in key:
        column = "Yield-protection score"
    else:
        column = "Balanced score"
    values = pd.to_numeric(candidate_table[column], errors="coerce")
    if values.notna().sum() == 0:
        raise DecisionIntelligenceError(f"Objective {objective!r} cannot be scored with the available inputs.")
    return candidate_table.loc[values.idxmax()].copy()


def scalar_state_assimilation(prior_mean: float, prior_sd: float, observation: float, observation_sd: float) -> dict[str, float]:
    """Independent Gaussian observation update for a comparable state variable."""
    pm, ps = float(prior_mean), float(prior_sd)
    obs, osd = float(observation), float(observation_sd)
    if ps <= 0 or osd <= 0:
        raise DecisionIntelligenceError("Prior and observation standard deviations must be > 0.")
    prior_var, obs_var = ps ** 2, osd ** 2
    gain = prior_var / (prior_var + obs_var)
    posterior_mean = pm + gain * (obs - pm)
    posterior_var = (1.0 - gain) * prior_var
    return {
        "prior_mean": pm, "prior_sd": ps, "observation": obs, "observation_sd": osd,
        "kalman_gain": gain, "posterior_mean": posterior_mean, "posterior_sd": float(np.sqrt(max(posterior_var, 0.0))),
        "innovation": obs - pm,
    }


def sequential_state_assimilation(
    prior_mean: float, prior_sd: float, observations: pd.DataFrame, *,
    value_column: str, sd_column: str, time_column: str | None = None,
) -> pd.DataFrame:
    if observations is None or observations.empty:
        raise DecisionIntelligenceError("No observations were supplied for assimilation.")
    if value_column not in observations or sd_column not in observations:
        raise DecisionIntelligenceError("Assimilation requires observation value and uncertainty columns.")
    mean, sd = float(prior_mean), float(prior_sd)
    rows = []
    for index, row in observations.iterrows():
        value = _finite(row[value_column])
        obs_sd = _finite(row[sd_column])
        if not np.isfinite(value) or not np.isfinite(obs_sd) or obs_sd <= 0:
            continue
        update = scalar_state_assimilation(mean, sd, value, obs_sd)
        record = {"row": index, **update}
        if time_column and time_column in observations.columns:
            record["time"] = row[time_column]
        rows.append(record)
        mean, sd = update["posterior_mean"], update["posterior_sd"]
    if not rows:
        raise DecisionIntelligenceError("No valid observations with positive uncertainty were available.")
    return pd.DataFrame(rows)


def paired_state_assimilation(
    frame: pd.DataFrame, *, prior_mean_column: str, prior_sd_column: str,
    observation_column: str, observation_sd_column: str, time_column: str | None = None,
) -> pd.DataFrame:
    """Assimilate observations against a time-varying model prior independently by row.

    This is safer than recursively carrying a posterior forward when the underlying crop
    state itself changes over time (for example LAI or biomass).
    """
    required = [prior_mean_column, prior_sd_column, observation_column, observation_sd_column]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise DecisionIntelligenceError(f"Time-varying assimilation is missing columns: {missing}")
    rows: list[dict[str, Any]] = []
    for index, row in frame.iterrows():
        values = [_finite(row[column]) for column in required]
        if not all(np.isfinite(value) for value in values):
            continue
        pm, ps, obs, osd = values
        if ps <= 0 or osd <= 0:
            continue
        update = scalar_state_assimilation(pm, ps, obs, osd)
        record: dict[str, Any] = {"row": index, **update}
        if time_column and time_column in frame.columns:
            record["time"] = row[time_column]
        rows.append(record)
    if not rows:
        raise DecisionIntelligenceError("No valid rows had finite priors/observations with positive uncertainty.")
    return pd.DataFrame(rows)


def _nutrient_pipeline(alpha: float = 1.0) -> Pipeline:
    return Pipeline([
        ("poly", PolynomialFeatures(degree=2, include_bias=False)),
        ("scale", StandardScaler()),
        ("model", Ridge(alpha=float(alpha))),
    ])


def fit_nutrient_response_model(
    frame: pd.DataFrame,
    *,
    target_column: str,
    n_column: str,
    p_column: str,
    k_column: str,
    covariate_columns: Sequence[str] = (),
    group_column: str | None = None,
    alpha: float = 1.0,
) -> NutrientModelResult:
    required = [target_column, n_column, p_column, k_column, *covariate_columns]
    missing = [c for c in required if c not in frame]
    if missing:
        raise DecisionIntelligenceError(f"Nutrient response data are missing columns: {missing}")
    work = frame.copy()
    features = [n_column, p_column, k_column, *[c for c in covariate_columns if c not in {n_column, p_column, k_column}]]
    for c in [target_column, *features]:
        work[c] = pd.to_numeric(work[c], errors="coerce")
    subset = [target_column, *features]
    if group_column and group_column in work:
        subset.append(group_column)
    work = work.dropna(subset=subset).reset_index(drop=True)
    if len(work) < max(12, len(features) * 2 + 4):
        raise DecisionIntelligenceError("Too few complete observations for a defensible empirical nutrient-response model. Aim for at least 12 and preferably replicated/site-season observations.")
    if work[n_column].nunique() < 3 and work[p_column].nunique() < 3 and work[k_column].nunique() < 3:
        raise DecisionIntelligenceError("The dataset contains too little nutrient-rate variation to estimate a response surface.")
    X = work[features].to_numpy(float)
    y = work[target_column].to_numpy(float)
    model = _nutrient_pipeline(alpha)
    predictions = np.full(len(work), np.nan)
    fold_ids = np.full(len(work), -1, dtype=int)
    if group_column and group_column in work and work[group_column].nunique() >= 2:
        groups = work[group_column].astype(str).to_numpy()
        n_splits = min(5, len(np.unique(groups)))
        splitter = GroupKFold(n_splits=n_splits)
        splits = splitter.split(X, y, groups)
        protocol = f"GroupKFold({n_splits}) by {group_column}"
    else:
        n_splits = min(5, max(2, len(work) // 4))
        splitter = KFold(n_splits=n_splits, shuffle=True, random_state=42)
        splits = splitter.split(X, y)
        protocol = f"KFold({n_splits}) diagnostic; use site/season groups when available"
    for fold, (train, test) in enumerate(splits):
        fitted = clone(model).fit(X[train], y[train])
        predictions[test] = fitted.predict(X[test])
        fold_ids[test] = fold
    valid = np.isfinite(predictions)
    metrics = {
        "rmse": float(np.sqrt(mean_squared_error(y[valid], predictions[valid]))),
        "mae": float(mean_absolute_error(y[valid], predictions[valid])),
        "r2": float(r2_score(y[valid], predictions[valid])) if valid.sum() >= 2 else np.nan,
        "n": int(len(work)),
        "protocol": protocol,
    }
    model.fit(X, y)
    validation = work[[target_column] + ([group_column] if group_column and group_column in work else [])].copy()
    validation["Prediction"] = predictions
    validation["Residual"] = validation[target_column] - validation["Prediction"]
    validation["Fold"] = fold_ids
    return NutrientModelResult(
        model=model, metrics=metrics, validation_rows=validation,
        feature_columns=features, target_column=target_column, group_column=group_column if group_column in work else None,
        n_column=n_column, p_column=p_column, k_column=k_column,
    )


def nutrient_candidate_grid(
    model_result: NutrientModelResult,
    *,
    n_range: tuple[float, float], p_range: tuple[float, float], k_range: tuple[float, float],
    steps: int = 15,
    covariate_values: Mapping[str, float] | None = None,
    crop_price_per_output_unit: float | None = None,
    n_cost_per_unit: float = 0.0, p_cost_per_unit: float = 0.0, k_cost_per_unit: float = 0.0,
) -> pd.DataFrame:
    steps = int(np.clip(int(steps), 3, 60))
    n_values = np.linspace(float(n_range[0]), float(n_range[1]), steps)
    p_values = np.linspace(float(p_range[0]), float(p_range[1]), steps)
    k_values = np.linspace(float(k_range[0]), float(k_range[1]), steps)
    rows = []
    fixed = dict(covariate_values or {})
    for n in n_values:
        for p in p_values:
            for k in k_values:
                row = {model_result.n_column: n, model_result.p_column: p, model_result.k_column: k}
                for feature in model_result.feature_columns:
                    if feature not in row:
                        if feature not in fixed:
                            raise DecisionIntelligenceError(f"A fixed value is required for covariate {feature!r} when generating nutrient scenarios.")
                        row[feature] = float(fixed[feature])
                rows.append(row)
    grid = pd.DataFrame(rows)
    X = grid[model_result.feature_columns].to_numpy(float)
    grid["Predicted outcome"] = model_result.model.predict(X)
    grid["Total nutrient rate"] = grid[model_result.n_column] + grid[model_result.p_column] + grid[model_result.k_column]
    grid["Nutrient input cost"] = (
        grid[model_result.n_column] * float(n_cost_per_unit)
        + grid[model_result.p_column] * float(p_cost_per_unit)
        + grid[model_result.k_column] * float(k_cost_per_unit)
    )
    if crop_price_per_output_unit is not None:
        grid["Gross value"] = grid["Predicted outcome"] * float(crop_price_per_output_unit)
        grid["Input-adjusted margin"] = grid["Gross value"] - grid["Nutrient input cost"]
    else:
        grid["Gross value"] = np.nan
        grid["Input-adjusted margin"] = np.nan
    objectives = [("Predicted outcome", "max"), ("Total nutrient rate", "min")]
    if grid["Input-adjusted margin"].notna().any():
        objectives.append(("Input-adjusted margin", "max"))
    grid["Pareto"] = pareto_mask(grid, objectives)
    grid["Yield score"] = _normalise(grid["Predicted outcome"], higher_is_better=True)
    grid["Input score"] = _normalise(grid["Total nutrient rate"], higher_is_better=False)
    grid["Margin score"] = _normalise(grid["Input-adjusted margin"], higher_is_better=True) if grid["Input-adjusted margin"].notna().any() else np.nan
    score_cols = ["Yield score", "Input score"] + (["Margin score"] if grid["Margin score"].notna().any() else [])
    grid["Balanced score"] = grid[score_cols].mean(axis=1)
    return grid


def choose_nutrient_candidate(grid: pd.DataFrame, objective: str, *, yield_retention_percent: float = 95.0) -> pd.Series:
    if grid is None or grid.empty:
        raise DecisionIntelligenceError("No nutrient scenario grid is available.")
    key = str(objective).casefold()
    if "margin" in key or "profit" in key:
        if grid["Input-adjusted margin"].notna().sum() == 0:
            raise DecisionIntelligenceError("Profit optimisation requires crop/output price inputs.")
        idx = pd.to_numeric(grid["Input-adjusted margin"], errors="coerce").idxmax()
    elif "minimum" in key or "input" in key:
        best = float(pd.to_numeric(grid["Predicted outcome"], errors="coerce").max())
        threshold = best * float(yield_retention_percent) / 100.0
        eligible = grid[pd.to_numeric(grid["Predicted outcome"], errors="coerce") >= threshold]
        idx = pd.to_numeric(eligible["Total nutrient rate"], errors="coerce").idxmin()
    elif "yield" in key:
        idx = pd.to_numeric(grid["Predicted outcome"], errors="coerce").idxmax()
    else:
        idx = pd.to_numeric(grid["Balanced score"], errors="coerce").idxmax()
    return grid.loc[idx].copy()


def _standardised_mean_difference(x_t: np.ndarray, x_c: np.ndarray, wt_t: np.ndarray | None = None, wt_c: np.ndarray | None = None) -> float:
    def wmean(x, w):
        return float(np.average(x, weights=w)) if w is not None else float(np.mean(x))
    def wvar(x, w):
        if w is None:
            return float(np.var(x, ddof=1)) if len(x) > 1 else 0.0
        m = np.average(x, weights=w)
        return float(np.average((x - m) ** 2, weights=w))
    mt, mc = wmean(x_t, wt_t), wmean(x_c, wt_c)
    pooled = np.sqrt(max((wvar(x_t, wt_t) + wvar(x_c, wt_c)) / 2.0, 1e-12))
    return float((mt - mc) / pooled)


def _causal_arrays(
    frame: pd.DataFrame, treatment_column: str, outcome_column: str, covariates: Sequence[str],
    group_column: str | None = None, treated_value: Any | None = None,
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray, np.ndarray | None, list[str]]:
    required = [treatment_column, outcome_column, *covariates]
    if group_column:
        required.append(group_column)
    required = list(dict.fromkeys(required))
    missing = [c for c in required if c not in frame]
    if missing:
        raise DecisionIntelligenceError(f"Causal audit is missing columns: {missing}")
    work = frame[required].copy()
    work[outcome_column] = pd.to_numeric(work[outcome_column], errors="coerce")
    # Drop rows with missing treatment/outcome/adjustment variables. Categorical
    # pre-treatment covariates are retained and one-hot encoded rather than silently
    # coerced to NaN; this is important for genotype, management, site and season factors.
    work = work.dropna(subset=required).reset_index(drop=True)
    if work.empty:
        raise DecisionIntelligenceError("No complete observations remain after requiring treatment, outcome and selected pre-treatment covariates.")

    unique = list(pd.unique(work[treatment_column]))
    if len(unique) != 2:
        raise DecisionIntelligenceError("Treatment must be binary (two observed values).")
    if treated_value is None:
        preferred = None
        for candidate in unique:
            if candidate is True or (isinstance(candidate, (int, float, np.integer, np.floating)) and float(candidate) == 1.0):
                preferred = candidate; break
        if preferred is None:
            positive_labels = {"yes", "true", "treated", "followed", "applied", "accepted", "intervention", "exposed"}
            for candidate in unique:
                if str(candidate).strip().casefold() in positive_labels:
                    preferred = candidate; break
        treated_value = preferred if preferred is not None else sorted(unique, key=lambda value: str(value))[-1]
    matches = [candidate for candidate in unique if candidate == treated_value or str(candidate) == str(treated_value)]
    if len(matches) != 1:
        raise DecisionIntelligenceError(f"Treated level {treated_value!r} is not one of the two observed treatment values: {unique!r}.")
    treated_level = matches[0]
    control_level = next(candidate for candidate in unique if candidate != treated_level)
    mapping = {control_level: 0, treated_level: 1}
    t = work[treatment_column].map(mapping).to_numpy(int)
    y = work[outcome_column].to_numpy(float)

    design_parts: list[pd.DataFrame] = []
    feature_names: list[str] = []
    for covariate in covariates:
        raw = work[covariate]
        numeric = pd.to_numeric(raw, errors="coerce")
        if numeric.notna().all():
            part = pd.DataFrame({str(covariate): numeric.astype(float)})
        else:
            # Reference coding keeps the design compact while still allowing categorical
            # confounders. The omitted first level is the reference category.
            part = pd.get_dummies(raw.astype(str), prefix=str(covariate), drop_first=True, dtype=float)
        if not part.empty:
            design_parts.append(part.reset_index(drop=True))
            feature_names.extend([str(column) for column in part.columns])
    if design_parts:
        X = pd.concat(design_parts, axis=1).to_numpy(float)
    else:
        X = np.zeros((len(work), 1), dtype=float)
        feature_names = []
    groups = work[group_column].astype(str).to_numpy() if group_column else None
    if t.sum() < 5 or (len(t) - t.sum()) < 5:
        raise DecisionIntelligenceError("Causal audit requires at least 5 treated and 5 comparison observations; more are strongly preferred.")
    return work, t, y, X, groups, feature_names

def _fit_propensity(X: np.ndarray, t: np.ndarray) -> tuple[np.ndarray, Any]:
    if X.shape[1] == 1 and np.allclose(X, 0):
        p = np.full(len(t), np.mean(t), dtype=float)
        return p, None
    model = Pipeline([("scale", StandardScaler()), ("logit", LogisticRegression(max_iter=2000, class_weight=None))])
    model.fit(X, t)
    propensity = model.predict_proba(X)[:, 1]
    return np.clip(propensity, 0.02, 0.98), model


def _outcome_models(X: np.ndarray, t: np.ndarray, y: np.ndarray, random_state: int = 42) -> tuple[np.ndarray, np.ndarray]:
    # Separate flexible response models (T-learner). Random forest avoids imposing
    # a linear treatment-covariate response while remaining CPU-friendly.
    m0 = RandomForestRegressor(n_estimators=300, min_samples_leaf=max(2, len(y) // 100), random_state=random_state, n_jobs=-1)
    m1 = RandomForestRegressor(n_estimators=300, min_samples_leaf=max(2, len(y) // 100), random_state=random_state + 1, n_jobs=-1)
    m0.fit(X[t == 0], y[t == 0])
    m1.fit(X[t == 1], y[t == 1])
    return m0.predict(X), m1.predict(X)


def _crossfit_nuisance(
    X: np.ndarray, t: np.ndarray, y: np.ndarray, *, groups: np.ndarray | None = None, random_state: int = 42
) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    n = len(y)
    propensity = np.full(n, np.nan, dtype=float)
    m0 = np.full(n, np.nan, dtype=float)
    m1 = np.full(n, np.nan, dtype=float)
    if groups is not None and len(np.unique(groups)) >= 2:
        n_splits = min(5, len(np.unique(groups)))
        splitter = GroupKFold(n_splits=n_splits)
        split_iter = splitter.split(X, t, groups)
        protocol = f"Group cross-fitting ({n_splits} folds)"
    else:
        minority = int(min(t.sum(), len(t) - t.sum()))
        n_splits = min(5, max(2, minority))
        splitter = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
        split_iter = splitter.split(X, t)
        protocol = f"Stratified cross-fitting ({n_splits} folds)"
    for fold, (train, test) in enumerate(split_iter):
        if len(np.unique(t[train])) < 2:
            raise DecisionIntelligenceError("A cross-fitting training fold contains only one treatment class. Use fewer/group-compatible folds or collect more comparison observations.")
        p_train, p_model = _fit_propensity(X[train], t[train])
        if p_model is None:
            propensity[test] = np.mean(t[train])
        else:
            propensity[test] = p_model.predict_proba(X[test])[:, 1]
        leaf = max(2, len(train) // 100)
        model0 = RandomForestRegressor(n_estimators=80, min_samples_leaf=leaf, random_state=random_state + fold * 7, n_jobs=-1)
        model1 = RandomForestRegressor(n_estimators=80, min_samples_leaf=leaf, random_state=random_state + fold * 7 + 1, n_jobs=-1)
        if np.sum(t[train] == 0) < 3 or np.sum(t[train] == 1) < 3:
            raise DecisionIntelligenceError("Too few treated/comparison observations within a cross-fitting fold for outcome models.")
        model0.fit(X[train][t[train] == 0], y[train][t[train] == 0])
        model1.fit(X[train][t[train] == 1], y[train][t[train] == 1])
        m0[test] = model0.predict(X[test])
        m1[test] = model1.predict(X[test])
    if not (np.isfinite(propensity).all() and np.isfinite(m0).all() and np.isfinite(m1).all()):
        raise DecisionIntelligenceError("Cross-fitting did not produce complete nuisance predictions.")
    return np.clip(propensity, 0.02, 0.98), m0, m1, protocol


def _ate_once(
    frame: pd.DataFrame, treatment_column: str, outcome_column: str, covariates: Sequence[str], method: str,
    group_column: str | None = None, random_state: int = 42, treated_value: Any | None = None,
) -> tuple[float, dict[str, Any], pd.DataFrame, pd.DataFrame]:
    work, t, y, X, groups, feature_names = _causal_arrays(frame, treatment_column, outcome_column, covariates, group_column, treated_value)
    propensity, m0, m1, crossfit_protocol = _crossfit_nuisance(X, t, y, groups=groups, random_state=random_state)
    p_t = propensity[t == 1]
    p_c = propensity[t == 0]
    overlap_low = max(float(np.quantile(p_t, 0.01)), float(np.quantile(p_c, 0.01)))
    overlap_high = min(float(np.quantile(p_t, 0.99)), float(np.quantile(p_c, 0.99)))
    ipw = t / propensity + (1 - t) / (1 - propensity)
    ess = float((ipw.sum() ** 2) / np.sum(ipw ** 2))
    key = str(method).casefold()
    if "naive" in key:
        unit_effect = np.full(len(y), np.nan)
        estimate = float(y[t == 1].mean() - y[t == 0].mean())
    elif "ipw" in key and "doubly" not in key and "aipw" not in key:
        treated_mean = np.sum(t * y / propensity) / np.sum(t / propensity)
        control_mean = np.sum((1 - t) * y / (1 - propensity)) / np.sum((1 - t) / (1 - propensity))
        estimate = float(treated_mean - control_mean)
        unit_effect = np.full(len(y), estimate)
    elif "outcome" in key or "t-learner" in key:
        unit_effect = m1 - m0
        estimate = float(np.mean(unit_effect))
    else:
        unit_effect = (m1 - m0) + t * (y - m1) / propensity - (1 - t) * (y - m0) / (1 - propensity)
        estimate = float(np.mean(unit_effect))
    balance_rows = []
    for j, feature_name in enumerate(feature_names):
        x = X[:, j]
        raw = _standardised_mean_difference(x[t == 1], x[t == 0])
        weights_t = 1.0 / propensity[t == 1]
        weights_c = 1.0 / (1.0 - propensity[t == 0])
        weighted = _standardised_mean_difference(x[t == 1], x[t == 0], weights_t, weights_c)
        balance_rows.append({"Covariate / encoded level": feature_name, "Raw SMD": raw, "IPW SMD": weighted, "|Raw SMD|": abs(raw), "|IPW SMD|": abs(weighted)})
    balance = pd.DataFrame(balance_rows)
    units = work.copy()
    units["Treatment binary"] = t
    units["Outcome"] = y
    units["Propensity"] = propensity
    units["IPW"] = ipw
    units["Predicted outcome if control"] = m0
    units["Predicted outcome if treated"] = m1
    units["Unit effect score"] = unit_effect
    diagnostics = {
        "n": len(y), "treated_n": int(t.sum()), "control_n": int(len(t) - t.sum()),
        "propensity_min": float(propensity.min()), "propensity_max": float(propensity.max()),
        "overlap_interval_1_99pct": [overlap_low, overlap_high],
        "effective_sample_size_ipw": ess,
        "max_abs_raw_smd": float(balance["|Raw SMD|"].max()) if not balance.empty else None,
        "max_abs_ipw_smd": float(balance["|IPW SMD|"].max()) if not balance.empty else None,
        "positivity_warning": bool(propensity.min() <= 0.03 or propensity.max() >= 0.97 or overlap_high <= overlap_low),
        "crossfit_protocol": crossfit_protocol,
        "group_column": group_column,
        "original_covariates": list(covariates),
        "expanded_design_features": feature_names,
        "treated_value": str(work.loc[t == 1, treatment_column].iloc[0]),
        "control_value": str(work.loc[t == 0, treatment_column].iloc[0]),
        "effect_direction": f"treated ({work.loc[t == 1, treatment_column].iloc[0]}) minus control ({work.loc[t == 0, treatment_column].iloc[0]})",
    }
    return estimate, diagnostics, balance, units

def causal_treatment_audit(
    frame: pd.DataFrame,
    *,
    treatment_column: str,
    outcome_column: str,
    covariates: Sequence[str],
    method: str = "Doubly robust AIPW",
    group_column: str | None = None,
    treated_value: Any | None = None,
    bootstrap_iterations: int = 200,
    random_state: int = 42,
    placebo_iterations: int = 100,
) -> CausalAuditResult:
    estimate, diagnostics, balance, units = _ate_once(
        frame, treatment_column, outcome_column, covariates, method,
        group_column=group_column, random_state=random_state, treated_value=treated_value,
    )
    rng = np.random.default_rng(int(random_state))
    bootstrap_values: list[float] = []
    key = str(method).casefold()
    score = pd.to_numeric(units.get("Unit effect score"), errors="coerce")
    # Fast uncertainty calculation: nuisance models are cross-fitted once, then
    # estimated effect scores are resampled.  This avoids hundreds of expensive
    # refits while keeping clustering explicit.  It is labelled as an
    # effect-score bootstrap rather than a full model-refit bootstrap.
    for _ in range(max(0, int(bootstrap_iterations))):
        if "naive" in key:
            if group_column and group_column in units and units[group_column].dropna().nunique() >= 2:
                groups = units[group_column].dropna().astype(str).unique()
                draws = rng.choice(groups, size=len(groups), replace=True)
                pieces = [units.loc[units[group_column].astype(str).eq(g)] for g in draws]
                sample = pd.concat(pieces, ignore_index=True)
            else:
                idx = rng.integers(0, len(units), len(units))
                sample = units.iloc[idx]
            treated = sample.loc[sample["Treatment binary"].eq(1), "Outcome"]
            control = sample.loc[sample["Treatment binary"].eq(0), "Outcome"]
            if len(treated) and len(control):
                bootstrap_values.append(float(treated.mean() - control.mean()))
        else:
            valid = units.loc[score.notna()].copy()
            valid["_effect_score"] = score.loc[score.notna()].to_numpy()
            if valid.empty:
                continue
            if group_column and group_column in valid and valid[group_column].dropna().nunique() >= 2:
                groups = valid[group_column].dropna().astype(str).unique()
                draws = rng.choice(groups, size=len(groups), replace=True)
                values = []
                for g in draws:
                    values.extend(valid.loc[valid[group_column].astype(str).eq(g), "_effect_score"].tolist())
                if values:
                    bootstrap_values.append(float(np.mean(values)))
            else:
                values = valid["_effect_score"].to_numpy(float)
                idx = rng.integers(0, len(values), len(values))
                bootstrap_values.append(float(np.mean(values[idx])))
    lower = upper = None
    if len(bootstrap_values) >= max(20, int(bootstrap_iterations) // 4):
        lower, upper = [float(v) for v in np.quantile(bootstrap_values, [0.025, 0.975])]

    # Cheap refutation diagnostic: residualise the outcome on the stated
    # pre-treatment covariates using Ridge, then compare treatment groups after
    # randomly permuting treatment labels. This is a placebo diagnostic, not the
    # primary causal estimator.
    placebo_values: list[float] = []
    try:
        work, t, y, X, _groups, _feature_names = _causal_arrays(frame, treatment_column, outcome_column, covariates, group_column, treated_value)
        if covariates:
            residual_model = Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=1.0))]).fit(X, y)
            residual = y - residual_model.predict(X)
        else:
            residual = y - np.mean(y)
        observed_residual_diff = float(residual[t == 1].mean() - residual[t == 0].mean())
        for _ in range(max(0, int(placebo_iterations))):
            perm = rng.permutation(t)
            if perm.sum() and (len(perm) - perm.sum()):
                placebo_values.append(abs(float(residual[perm == 1].mean() - residual[perm == 0].mean())))
        placebo_p = float((1 + np.sum(np.asarray(placebo_values) >= abs(observed_residual_diff))) / (1 + len(placebo_values))) if placebo_values else None
    except Exception:
        placebo_p = None

    diagnostics["bootstrap_successful"] = len(bootstrap_values)
    diagnostics["bootstrap_unit"] = "group/cluster" if group_column else "row"
    diagnostics["interval_method"] = "Nonparametric bootstrap of cross-fitted estimated effect scores; nuisance models are not refit inside each bootstrap draw."
    diagnostics["placebo_successful"] = len(placebo_values)
    diagnostics["placebo_method"] = "Treatment-label permutation on outcome residuals after Ridge adjustment for the stated covariates; refutation diagnostic only."
    diagnostics["assumptions"] = [
        "Consistency: the recorded treatment corresponds to a well-defined intervention.",
        "Conditional exchangeability: included covariates adequately block relevant confounding paths.",
        "Positivity/overlap: treated and comparison observations exist across relevant covariate support.",
        "No interference between experimental units unless explicitly modelled.",
        "Measurement and model specification are sufficiently accurate for the intended interpretation.",
    ]
    return CausalAuditResult(
        estimate=estimate, lower_bound=lower, upper_bound=upper, method=method,
        diagnostics=diagnostics, balance=balance, unit_effects=units,
        placebo_p_value=placebo_p,
    )

def recommendation_outcome_table(recommendations: pd.DataFrame, outcomes: pd.DataFrame) -> pd.DataFrame:
    """Build an analysis table while retaining the recommendation/outcome distinction."""
    if recommendations is None or recommendations.empty or outcomes is None or outcomes.empty:
        return pd.DataFrame()
    left = recommendations.copy()
    right = outcomes.copy()
    return right.merge(left, on="recommendation_id", how="left", suffixes=("_outcome", "_recommendation"))
