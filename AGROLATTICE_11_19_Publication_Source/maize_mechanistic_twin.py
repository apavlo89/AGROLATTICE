"""Mechanistic maize flowering simulation for AGROLATTICE.

This module implements the equations disclosed by Laurent et al. (2025) for
the Maize Flowering Synchrony (MFS) crop-growth model.  It intentionally keeps
the mechanistic model independent from Streamlit so it can be tested, audited
and reused in exports.

The publication's original C++ Bayesian CGM-WGP sampler and commercial data
are not public.  AGROLATTICE therefore provides:

* the disclosed daily MFS simulator;
* prior-regularised phenotypic calibration;
* Monte-Carlo uncertainty and single/two-date male sowing optimisation; and
* an optional genomic-ridge bridge from SNP markers to calibrated physiology.

The genomic bridge is an approximation, not a reproduction of the paper's
Bayesian whole-genome prediction method.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
from scipy.optimize import least_squares
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


MODULE_VERSION = "1.0.0"
PUBLICATION_DOI = "10.1002/csc2.21453"

EMERGENCE_GDD = 30.6
LEAVES_AT_EMERGENCE = 2.5
EAR_GROWTH_LEAF_FRACTION = 0.67
ANTHESIS_AFTER_FINAL_LEAF_GDD = 40.0
EAR_INITIAL_BIOMASS_G = 0.01
EAR_MAX_BIOMASS_G = 5.0

PARAMETER_BOUNDS = {
    "tln": (10.0, 35.0),
    "coblf": (0.0005, 0.0040),
    "eb_r1_g": (0.05, 4.95),
}


class MechanisticMaizeError(RuntimeError):
    """Raised when a mechanistic simulation cannot be evaluated safely."""


@dataclass(frozen=True)
class PhysiologyParameters:
    """Genotype-specific MFS parameters with uncertainty.

    Priors follow the biologically informative values described by Laurent et
    al. (2025): tln ~ N(19, 2), coblf ~ N(0.0019, 0.00036), and the 50%
    silking ebR1 prior ~ N(2, 0.5).
    """

    tln: float = 19.0
    coblf: float = 0.0019
    eb_r1_g: float = 2.0
    tln_sd: float = 2.0
    coblf_sd: float = 0.00036
    eb_r1_sd: float = 0.5

    def validated(self) -> "PhysiologyParameters":
        values = asdict(self)
        for key in ("tln", "coblf", "eb_r1_g"):
            value = float(values[key])
            lower, upper = PARAMETER_BOUNDS[key]
            if not np.isfinite(value) or not lower <= value <= upper:
                raise MechanisticMaizeError(
                    f"{key} must be between {lower:g} and {upper:g}; received {value}."
                )
        for key in ("tln_sd", "coblf_sd", "eb_r1_sd"):
            value = float(values[key])
            if not np.isfinite(value) or value < 0:
                raise MechanisticMaizeError(f"{key} must be a finite non-negative value.")
        return self

    def to_record(self) -> dict[str, float]:
        return {key: float(value) for key, value in asdict(self.validated()).items()}


DEFAULT_PHYSIOLOGY = PhysiologyParameters()


def physiology_from_mapping(values: Mapping[str, Any] | None) -> PhysiologyParameters:
    values = dict(values or {})
    aliases = {
        "tln": ["tln", "TLN", "Total leaf number"],
        "coblf": ["coblf", "COBLF", "Coefficient of leaf appearance"],
        "eb_r1_g": ["eb_r1_g", "ebR1", "ebR1 (g)", "Ear biomass at R1 (g)"],
        "tln_sd": ["tln_sd", "TLN SD"],
        "coblf_sd": ["coblf_sd", "COBLF SD"],
        "eb_r1_sd": ["eb_r1_sd", "ebR1 SD"],
    }
    defaults = DEFAULT_PHYSIOLOGY.to_record()
    parsed: dict[str, float] = {}
    for canonical, candidates in aliases.items():
        raw = next((values.get(candidate) for candidate in candidates if values.get(candidate) not in (None, "")), defaults[canonical])
        parsed[canonical] = float(raw)
    return PhysiologyParameters(**parsed).validated()


def _weather_frame(weather: pd.DataFrame) -> pd.DataFrame:
    if weather is None or weather.empty:
        raise MechanisticMaizeError("Daily weather with Date and GDD daily is required.")
    output = weather.copy()
    date_column = next((name for name in ("Date", "DATE", "date", "weather_date") if name in output.columns), None)
    gdd_column = next((name for name in ("GDD daily", "gdd_daily", "GDD") if name in output.columns), None)
    if date_column is None or gdd_column is None:
        raise MechanisticMaizeError("Daily weather requires Date and GDD daily columns.")
    output["Date"] = pd.to_datetime(output[date_column], errors="coerce").dt.normalize()
    output["GDD daily"] = pd.to_numeric(output[gdd_column], errors="coerce").clip(lower=0)
    output = output.dropna(subset=["Date", "GDD daily"]).sort_values("Date").drop_duplicates("Date", keep="last")
    if output.empty:
        raise MechanisticMaizeError("Daily weather contains no usable Date/GDD rows.")
    return output.reset_index(drop=True)


def parameter_thermal_targets(parameters: PhysiologyParameters) -> dict[str, float]:
    """Return MFS thermal targets after emergence for one genotype."""
    p = parameters.validated()
    vn = p.tln * EAR_GROWTH_LEAF_FRACTION
    gdd_vn = math.log(vn / LEAVES_AT_EMERGENCE) / p.coblf
    gdd_final_leaf = math.log(p.tln / LEAVES_AT_EMERGENCE) / p.coblf
    gdd_grain_fill = gdd_final_leaf + ANTHESIS_AFTER_FINAL_LEAF_GDD
    gdd_hi = max(1e-6, gdd_grain_fill - gdd_vn)
    ear_growth_rate = math.log(EAR_MAX_BIOMASS_G / EAR_INITIAL_BIOMASS_G) / gdd_hi
    gdd_silking = gdd_vn + math.log(p.eb_r1_g / EAR_INITIAL_BIOMASS_G) / ear_growth_rate
    return {
        "Vn leaf number": vn,
        "GDD emergence to Vn": gdd_vn,
        "GDD emergence to final leaf": gdd_final_leaf,
        "GDD emergence to anthesis": gdd_grain_fill,
        "GDD emergence to silking": gdd_silking,
        "GDD Vn to grain filling": gdd_hi,
        "Ear growth rate": ear_growth_rate,
        "Planting GDD to anthesis": EMERGENCE_GDD + gdd_grain_fill,
        "Planting GDD to silking": EMERGENCE_GDD + gdd_silking,
    }


def _event_date_from_target(weather: pd.DataFrame, sowing_date: Any, target_gdd: float) -> pd.Timestamp | pd.NaT:
    prepared = _weather_frame(weather)
    sowing = pd.Timestamp(sowing_date).normalize()
    if sowing < prepared["Date"].min():
        return pd.NaT
    subset = prepared.loc[prepared["Date"].ge(sowing), ["Date", "GDD daily"]].copy()
    if subset.empty:
        return pd.NaT
    cumulative = subset["GDD daily"].cumsum().to_numpy(float)
    index = int(np.searchsorted(cumulative, float(target_gdd), side="left"))
    if index >= len(subset):
        return pd.NaT
    return pd.Timestamp(subset.iloc[index]["Date"])


def event_date(
    weather: pd.DataFrame,
    sowing_date: Any,
    parameters: PhysiologyParameters,
    role: str,
) -> pd.Timestamp | pd.NaT:
    targets = parameter_thermal_targets(parameters)
    role_key = str(role).strip().casefold()
    target = targets["Planting GDD to anthesis"] if role_key.startswith("m") else targets["Planting GDD to silking"]
    return _event_date_from_target(weather, sowing_date, target)


def simulate_mfs(
    weather: pd.DataFrame,
    sowing_date: Any,
    parameters: PhysiologyParameters,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Run the disclosed MFS equations day by day for one parent line."""
    prepared = _weather_frame(weather)
    p = parameters.validated()
    sowing = pd.Timestamp(sowing_date).normalize()
    if sowing < prepared["Date"].min():
        raise MechanisticMaizeError("Weather begins after the selected sowing date; earlier daily weather is required.")
    frame = prepared.loc[prepared["Date"].ge(sowing)].copy()
    if frame.empty:
        raise MechanisticMaizeError("Weather does not extend to or beyond the selected sowing date.")
    frame["Planting cumulative GDD"] = frame["GDD daily"].cumsum()
    frame["Post-emergence GDD"] = (frame["Planting cumulative GDD"] - EMERGENCE_GDD).clip(lower=0)
    targets = parameter_thermal_targets(p)
    post = frame["Post-emergence GDD"].to_numpy(float)
    leaf_number = LEAVES_AT_EMERGENCE * np.exp(post * p.coblf)
    leaf_number = np.where(frame["Planting cumulative GDD"].to_numpy(float) < EMERGENCE_GDD, 0.0, leaf_number)
    frame["Predicted collared leaf number"] = np.minimum(p.tln, leaf_number)
    ear_thermal = np.maximum(0.0, post - targets["GDD emergence to Vn"])
    ear_biomass = EAR_INITIAL_BIOMASS_G * np.exp(targets["Ear growth rate"] * ear_thermal)
    ear_biomass = np.where(post < targets["GDD emergence to Vn"], 0.0, ear_biomass)
    frame["Predicted ear biomass (g)"] = np.minimum(EAR_MAX_BIOMASS_G, ear_biomass)
    frame["Emergence reached"] = frame["Planting cumulative GDD"].ge(EMERGENCE_GDD)
    frame["Ear growth active"] = frame["Post-emergence GDD"].ge(targets["GDD emergence to Vn"])
    frame["Anthesis reached"] = frame["Planting cumulative GDD"].ge(targets["Planting GDD to anthesis"])
    frame["Silking reached"] = frame["Planting cumulative GDD"].ge(targets["Planting GDD to silking"])

    def first_date(column: str) -> pd.Timestamp | pd.NaT:
        selected = frame.loc[frame[column], "Date"]
        return pd.Timestamp(selected.iloc[0]) if not selected.empty else pd.NaT

    emergence = first_date("Emergence reached")
    anthesis = first_date("Anthesis reached")
    silking = first_date("Silking reached")
    summary = {
        "Sowing date": sowing.date().isoformat(),
        "Emergence date": emergence.date().isoformat() if pd.notna(emergence) else None,
        "Anthesis date": anthesis.date().isoformat() if pd.notna(anthesis) else None,
        "Silking date": silking.date().isoformat() if pd.notna(silking) else None,
        "Days sowing to anthesis": float((anthesis - sowing).days) if pd.notna(anthesis) else np.nan,
        "Days sowing to silking": float((silking - sowing).days) if pd.notna(silking) else np.nan,
        **p.to_record(),
        **targets,
        "Method": "Laurent et al. (2025) disclosed MFS equations",
        "DOI": PUBLICATION_DOI,
    }
    return frame, summary


def _sample_physiology(parameters: PhysiologyParameters, draws: int, rng: np.random.Generator) -> pd.DataFrame:
    p = parameters.validated()
    rows = {
        "tln": rng.normal(p.tln, max(p.tln_sd, 1e-9), int(draws)),
        "coblf": rng.normal(p.coblf, max(p.coblf_sd, 1e-12), int(draws)),
        "eb_r1_g": rng.normal(p.eb_r1_g, max(p.eb_r1_sd, 1e-9), int(draws)),
    }
    frame = pd.DataFrame(rows)
    for column, bounds in PARAMETER_BOUNDS.items():
        frame[column] = frame[column].clip(*bounds)
    return frame


def _sample_event_dates(
    weather: pd.DataFrame,
    sowing_date: Any,
    samples: pd.DataFrame,
    role: str,
) -> np.ndarray:
    prepared = _weather_frame(weather)
    sowing = pd.Timestamp(sowing_date).normalize()
    if sowing < prepared["Date"].min():
        return np.full(len(samples), np.datetime64("NaT"), dtype="datetime64[ns]")
    subset = prepared.loc[prepared["Date"].ge(sowing), ["Date", "GDD daily"]]
    if subset.empty:
        return np.full(len(samples), np.datetime64("NaT"), dtype="datetime64[ns]")
    cumulative = subset["GDD daily"].cumsum().to_numpy(float)
    dates = subset["Date"].to_numpy(dtype="datetime64[ns]")
    tln = samples["tln"].to_numpy(float)
    coblf = samples["coblf"].to_numpy(float)
    eb = samples["eb_r1_g"].to_numpy(float)
    gdd_vn = np.log((EAR_GROWTH_LEAF_FRACTION * tln) / LEAVES_AT_EMERGENCE) / coblf
    gdd_final = np.log(tln / LEAVES_AT_EMERGENCE) / coblf
    gdd_grain = gdd_final + ANTHESIS_AFTER_FINAL_LEAF_GDD
    if str(role).strip().casefold().startswith("m"):
        targets = EMERGENCE_GDD + gdd_grain
    else:
        gdd_hi = np.maximum(1e-6, gdd_grain - gdd_vn)
        growth_rate = math.log(EAR_MAX_BIOMASS_G / EAR_INITIAL_BIOMASS_G) / gdd_hi
        targets = EMERGENCE_GDD + gdd_vn + np.log(eb / EAR_INITIAL_BIOMASS_G) / growth_rate
    indices = np.searchsorted(cumulative, targets, side="left")
    output = np.full(len(samples), np.datetime64("NaT"), dtype="datetime64[ns]")
    valid = indices < len(dates)
    output[valid] = dates[indices[valid]]
    return output


def simulate_event_uncertainty(
    weather: pd.DataFrame,
    sowing_date: Any,
    parameters: PhysiologyParameters,
    role: str,
    *,
    draws: int = 500,
    random_state: int = 42,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    rng = np.random.default_rng(int(random_state))
    samples = _sample_physiology(parameters, max(50, int(draws)), rng)
    dates = _sample_event_dates(weather, sowing_date, samples, role)
    result = samples.copy()
    result["Event date"] = pd.to_datetime(dates)
    complete = result["Event date"].dropna()
    if complete.empty:
        raise MechanisticMaizeError("Weather does not extend far enough to reach the simulated event.")
    ordinal = complete.map(pd.Timestamp.toordinal).to_numpy(float)
    summary = {
        "Role": role,
        "Median event date": pd.Timestamp.fromordinal(int(round(np.median(ordinal)))).date().isoformat(),
        "P05 event date": pd.Timestamp.fromordinal(int(round(np.quantile(ordinal, 0.05)))).date().isoformat(),
        "P95 event date": pd.Timestamp.fromordinal(int(round(np.quantile(ordinal, 0.95)))).date().isoformat(),
        "Complete draws": int(len(complete)),
        "Requested draws": int(draws),
    }
    return result, summary


def optimise_male_sowing_strategy(
    weather: pd.DataFrame,
    female_sowing_date: Any,
    female_parameters: PhysiologyParameters,
    male_parameters: PhysiologyParameters,
    *,
    minimum_offset: int = -10,
    maximum_offset: int = 14,
    strategy: str = "Compare single and two-date strategies",
    minimum_pair_spacing: int = 2,
    maximum_pair_spacing: int = 10,
    draws: int = 500,
    random_state: int = 42,
) -> pd.DataFrame:
    """Optimise one or two male sowing dates against uncertainty in flowering.

    The score targets pollen-shed timing at two points around female silking
    (-2 and +2 days), mirroring the operational example in Laurent et al.
    (2025).  It does not claim to simulate pollen quantity.
    """
    if int(minimum_offset) > int(maximum_offset):
        raise MechanisticMaizeError("Minimum offset cannot exceed maximum offset.")
    rng = np.random.default_rng(int(random_state))
    count = max(100, int(draws))
    female_samples = _sample_physiology(female_parameters, count, rng)
    male_samples = _sample_physiology(male_parameters, count, rng)
    female_dates = _sample_event_dates(weather, female_sowing_date, female_samples, "Female")
    female_ord = pd.to_datetime(female_dates).map(lambda value: value.toordinal() if pd.notna(value) else np.nan).to_numpy(float)
    offsets = list(range(int(minimum_offset), int(maximum_offset) + 1))
    gap_by_offset: dict[int, np.ndarray] = {}
    event_date_by_offset: dict[int, str | None] = {}
    female_sowing = pd.Timestamp(female_sowing_date).normalize()
    for offset in offsets:
        male_sowing = female_sowing + pd.Timedelta(days=int(offset))
        male_dates = _sample_event_dates(weather, male_sowing, male_samples, "Male")
        male_time = pd.to_datetime(male_dates)
        male_ord = male_time.map(lambda value: value.toordinal() if pd.notna(value) else np.nan).to_numpy(float)
        gap_by_offset[offset] = male_ord - female_ord
        complete_ord = male_ord[np.isfinite(male_ord)]
        event_date_by_offset[offset] = (
            pd.Timestamp.fromordinal(int(round(float(np.median(complete_ord))))).date().isoformat()
            if complete_ord.size else None
        )

    rows: list[dict[str, Any]] = []

    def score_gaps(gaps: Sequence[np.ndarray]) -> dict[str, float]:
        matrix = np.vstack(gaps)
        finite = np.all(np.isfinite(matrix), axis=0)
        matrix = matrix[:, finite]
        if matrix.shape[1] == 0:
            return {"Objective score": np.nan, "P(any shed within ±2 d)": np.nan, "P(brackets silking)": np.nan, "Complete draws": 0}
        early = np.max(np.exp(-0.5 * ((matrix + 2.0) / 1.5) ** 2), axis=0)
        late = np.max(np.exp(-0.5 * ((matrix - 2.0) / 1.5) ** 2), axis=0)
        any_close = np.any(np.abs(matrix) <= 2.0, axis=0)
        brackets = (np.min(matrix, axis=0) <= 0.0) & (np.max(matrix, axis=0) >= 0.0) if matrix.shape[0] > 1 else np.abs(matrix[0]) <= 1.0
        return {
            "Objective score": float(np.mean((early + late) / 2.0)),
            "P(any shed within ±2 d)": float(np.mean(any_close)),
            "P(brackets silking)": float(np.mean(brackets)),
            "Complete draws": int(matrix.shape[1]),
        }

    include_single = strategy != "Two staggered male sowing dates"
    include_pair = strategy != "One male sowing date"
    if include_single:
        for offset in offsets:
            rows.append({
                "Strategy": "One male sowing date",
                "Offset 1 (days)": offset,
                "Offset 2 (days)": np.nan,
                "Male sowing 1": (female_sowing + pd.Timedelta(days=offset)).date().isoformat(),
                "Male sowing 2": None,
                "Median anthesis 1": event_date_by_offset[offset],
                "Median anthesis 2": None,
                **score_gaps([gap_by_offset[offset]]),
            })
    if include_pair:
        for first_index, first in enumerate(offsets):
            for second in offsets[first_index + 1:]:
                spacing = second - first
                if not int(minimum_pair_spacing) <= spacing <= int(maximum_pair_spacing):
                    continue
                rows.append({
                    "Strategy": "Two staggered male sowing dates",
                    "Offset 1 (days)": first,
                    "Offset 2 (days)": second,
                    "Male sowing 1": (female_sowing + pd.Timedelta(days=first)).date().isoformat(),
                    "Male sowing 2": (female_sowing + pd.Timedelta(days=second)).date().isoformat(),
                    "Median anthesis 1": event_date_by_offset[first],
                    "Median anthesis 2": event_date_by_offset[second],
                    **score_gaps([gap_by_offset[first], gap_by_offset[second]]),
                })
    result = pd.DataFrame(rows)
    if result.empty:
        raise MechanisticMaizeError("No sowing strategies satisfy the selected range and spacing constraints.")
    result["Recommended"] = False
    for label, group in result.groupby("Strategy"):
        if group["Objective score"].notna().any():
            result.loc[group["Objective score"].idxmax(), "Recommended"] = True
    return result.sort_values(["Strategy", "Objective score"], ascending=[True, False]).reset_index(drop=True)


def _leaf_prediction_at_date(
    weather: pd.DataFrame,
    sowing_date: Any,
    observation_date: Any,
    tln: float,
    coblf: float,
) -> float:
    prepared = _weather_frame(weather)
    start = pd.Timestamp(sowing_date).normalize()
    end = pd.Timestamp(observation_date).normalize()
    cumulative = float(prepared.loc[prepared["Date"].between(start, end), "GDD daily"].sum())
    if cumulative < EMERGENCE_GDD:
        return 0.0
    return float(min(tln, LEAVES_AT_EMERGENCE * math.exp((cumulative - EMERGENCE_GDD) * coblf)))


def calibrate_parent_physiology(
    weather: pd.DataFrame,
    *,
    role: str,
    event_observations: pd.DataFrame | None = None,
    leaf_observations: pd.DataFrame | None = None,
    prior: PhysiologyParameters = DEFAULT_PHYSIOLOGY,
) -> dict[str, Any]:
    """Calibrate MFS parameters with informative-prior regularisation."""
    prepared = _weather_frame(weather)
    prior = prior.validated()
    events = pd.DataFrame() if event_observations is None else event_observations.copy()
    leaves = pd.DataFrame() if leaf_observations is None else leaf_observations.copy()
    if events.empty and leaves.empty:
        raise MechanisticMaizeError("Calibration requires flowering-event or repeated leaf-number observations.")

    def residuals(theta: np.ndarray) -> np.ndarray:
        p = PhysiologyParameters(
            tln=float(theta[0]), coblf=float(theta[1]), eb_r1_g=float(theta[2]),
            tln_sd=prior.tln_sd, coblf_sd=prior.coblf_sd, eb_r1_sd=prior.eb_r1_sd,
        )
        values: list[float] = []
        if not events.empty:
            for _, row in events.iterrows():
                observed = pd.to_datetime(row.get("Event date"), errors="coerce")
                sowing = pd.to_datetime(row.get("Sowing date"), errors="coerce")
                if pd.isna(observed) or pd.isna(sowing):
                    continue
                predicted = event_date(prepared, sowing, p, role)
                if pd.notna(predicted):
                    values.append(float((predicted - observed).days) / 2.0)
        if not leaves.empty:
            for _, row in leaves.iterrows():
                observed_leaf = pd.to_numeric(pd.Series([row.get("Collared leaf number")]), errors="coerce").iloc[0]
                sowing = pd.to_datetime(row.get("Sowing date"), errors="coerce")
                observed_date = pd.to_datetime(row.get("Observation date"), errors="coerce")
                if pd.isna(observed_leaf) or pd.isna(sowing) or pd.isna(observed_date):
                    continue
                predicted_leaf = _leaf_prediction_at_date(prepared, sowing, observed_date, p.tln, p.coblf)
                values.append(float(predicted_leaf - observed_leaf))
        # Informative priors stabilise non-identifiable parameter combinations.
        values.extend([
            (p.tln - prior.tln) / max(prior.tln_sd, 1e-6),
            (p.coblf - prior.coblf) / max(prior.coblf_sd, 1e-9),
            (p.eb_r1_g - prior.eb_r1_g) / max(prior.eb_r1_sd, 1e-6),
        ])
        return np.asarray(values, dtype=float)

    lower = np.array([PARAMETER_BOUNDS["tln"][0], PARAMETER_BOUNDS["coblf"][0], PARAMETER_BOUNDS["eb_r1_g"][0]])
    upper = np.array([PARAMETER_BOUNDS["tln"][1], PARAMETER_BOUNDS["coblf"][1], PARAMETER_BOUNDS["eb_r1_g"][1]])
    fit = least_squares(residuals, np.array([prior.tln, prior.coblf, prior.eb_r1_g]), bounds=(lower, upper), max_nfev=800)
    theta = fit.x
    base_sd = np.array([prior.tln_sd, prior.coblf_sd, prior.eb_r1_sd], dtype=float)
    estimated_sd = base_sd.copy()
    try:
        jacobian = fit.jac
        covariance = np.linalg.pinv(jacobian.T @ jacobian)
        scale = max(1.0, float(np.sum(fit.fun ** 2) / max(1, len(fit.fun) - len(theta))))
        candidate = np.sqrt(np.maximum(0.0, np.diag(covariance) * scale))
        estimated_sd = np.minimum(base_sd, np.maximum(candidate, base_sd * 0.10))
    except Exception:
        pass
    parameters = PhysiologyParameters(
        tln=float(theta[0]), coblf=float(theta[1]), eb_r1_g=float(theta[2]),
        tln_sd=float(estimated_sd[0]), coblf_sd=float(estimated_sd[1]), eb_r1_sd=float(estimated_sd[2]),
    ).validated()
    warnings: list[str] = []
    if len(events) < 3:
        warnings.append("Fewer than three flowering-event records; parameter estimates remain strongly prior-driven.")
    if len(leaves) < 4:
        warnings.append("Fewer than four repeated leaf-number records; tln and coblf may not be separately identifiable.")
    if str(role).strip().casefold().startswith("m"):
        warnings.append("Male anthesis does not identify ebR1; its estimate is retained mainly from the prior.")
    return {
        "parameters": parameters,
        "success": bool(fit.success),
        "message": str(fit.message),
        "objective": float(np.sum(fit.fun ** 2)),
        "event_records": int(len(events)),
        "leaf_records": int(len(leaves)),
        "warnings": warnings,
        "method": "Prior-regularised nonlinear least squares",
        "publication_doi": PUBLICATION_DOI,
    }


def genomic_physiology_bridge(
    markers: pd.DataFrame,
    physiology: pd.DataFrame,
    *,
    parent_column: str = "Parent line",
    alpha: float = 10.0,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Predict physiological parameters from SNP markers with genomic ridge.

    At least eight calibrated parents are required.  Marker columns should be
    coded 0/1/2; other numeric dosage values are accepted after coercion.
    """
    if markers is None or markers.empty or physiology is None or physiology.empty:
        raise MechanisticMaizeError("SNP-marker and calibrated-physiology tables are required.")
    if parent_column not in markers.columns or parent_column not in physiology.columns:
        raise MechanisticMaizeError(f"Both files require a {parent_column!r} column.")
    marker_columns = [column for column in markers.columns if column != parent_column]
    numeric_markers = markers[marker_columns].apply(pd.to_numeric, errors="coerce")
    usable_markers = [column for column in numeric_markers.columns if numeric_markers[column].notna().sum() >= 2 and numeric_markers[column].nunique(dropna=True) >= 2]
    if not usable_markers:
        raise MechanisticMaizeError("No polymorphic numeric SNP-marker columns were found.")
    marker_frame = pd.concat([markers[[parent_column]].astype(str), numeric_markers[usable_markers]], axis=1)
    targets = [column for column in ("tln", "coblf", "eb_r1_g") if column in physiology.columns]
    if len(targets) != 3:
        raise MechanisticMaizeError("Physiology table requires tln, coblf and eb_r1_g columns.")
    joined = marker_frame.merge(physiology[[parent_column] + targets], on=parent_column, how="left")
    training = joined.dropna(subset=targets).copy()
    if len(training) < 8:
        raise MechanisticMaizeError("At least eight parents with calibrated physiology and SNP data are required.")
    X_train = training[usable_markers]
    X_all = joined[usable_markers]
    folds = min(5, len(training))
    splitter = KFold(n_splits=folds, shuffle=True, random_state=int(random_state))
    predictions = joined[[parent_column]].copy()
    metrics: list[dict[str, Any]] = []
    for target in targets:
        model = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("ridge", Ridge(alpha=float(alpha))),
        ])
        y = training[target].to_numpy(float)
        cv_predictions = cross_val_predict(model, X_train, y, cv=splitter)
        metrics.append({
            "Parameter": target,
            "N calibrated parents": int(len(training)),
            "SNP markers": int(len(usable_markers)),
            "MAE": float(mean_absolute_error(y, cv_predictions)),
            "RMSE": float(math.sqrt(mean_squared_error(y, cv_predictions))),
            "R²": float(r2_score(y, cv_predictions)) if len(y) >= 3 and np.std(y) > 0 else np.nan,
            "Validation": f"{folds}-fold parent-level CV",
        })
        model.fit(X_train, y)
        predicted = model.predict(X_all)
        predicted = np.clip(predicted, *PARAMETER_BOUNDS[target])
        predictions[f"Predicted {target}"] = predicted
        predictions[f"Observed {target}"] = pd.to_numeric(joined[target], errors="coerce")
    predictions["Prediction method"] = "Genomic ridge approximation"
    predictions["Publication method reproduced"] = False
    return predictions, pd.DataFrame(metrics)


def method_manifest() -> dict[str, Any]:
    return {
        "module_version": MODULE_VERSION,
        "publication_doi": PUBLICATION_DOI,
        "emergence_gdd": EMERGENCE_GDD,
        "leaves_at_emergence": LEAVES_AT_EMERGENCE,
        "ear_growth_leaf_fraction": EAR_GROWTH_LEAF_FRACTION,
        "anthesis_after_final_leaf_gdd": ANTHESIS_AFTER_FINAL_LEAF_GDD,
        "ear_initial_biomass_g": EAR_INITIAL_BIOMASS_G,
        "ear_max_biomass_g": EAR_MAX_BIOMASS_G,
        "default_priors": DEFAULT_PHYSIOLOGY.to_record(),
        "genomic_bridge": "Ridge approximation; not the proprietary Bayesian CGM-WGP implementation",
    }
