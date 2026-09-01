from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_EFFECTIVE_PRECIPITATION_FRACTION = 0.80


def load_validated_crop_library(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Validated crop parameter library not found: {path}. "
            "Place validated_crop_defaults_mexico.json beside the app script."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "crops" not in data or "sources" not in data:
        raise ValueError("The validated crop parameter JSON has an unsupported schema.")
    return data


def _normalise(value: str) -> str:
    return " ".join(str(value).casefold().replace("/", " ").replace("-", " ").split())


def _midpoint(value: dict[str, Any] | None) -> float | None:
    if not isinstance(value, dict):
        return None
    numbers = [value.get("min"), value.get("max")]
    numbers = [float(number) for number in numbers if number is not None and pd.notna(number)]
    if not numbers:
        return None
    return float(np.mean(numbers))


def _duration_midpoint(value: dict[str, Any] | None) -> float | None:
    return _midpoint(value)


def get_default_crop_profile(library: dict[str, Any], crop: str) -> dict[str, Any] | None:
    crop_data = library.get("crops", {}).get(crop, {})
    profiles = crop_data.get("profiles", [])
    if not profiles:
        return None
    for profile in profiles:
        if str(profile.get("default_for_app", "")).strip().casefold() == "yes":
            return profile
    return profiles[0]


def get_crop_profiles(library: dict[str, Any], crop: str) -> list[dict[str, Any]]:
    return list(library.get("crops", {}).get(crop, {}).get("profiles", []))


def get_stage_parameter_rows(library: dict[str, Any], crop: str) -> list[dict[str, Any]]:
    return list(library.get("crops", {}).get(crop, {}).get("stage_water_parameters", []))


def _stage_alias(crop: str, app_stage: str) -> str | None:
    explicit = {
        "Maize": {
            "Planting / establishment": "Initial",
            "Vegetative growth": "Development",
            "Reproductive / flowering": "Mid-season",
            "Grain filling": "Late season",
            "Harvest period": "Harvest endpoint",
            "Full growing season": "Whole season",
        },
        "Wheat": {
            "Establishment": "Initial",
            "Vegetative growth": "Development",
            "Flowering / grain filling": "Mid-season",
            "Full growing season": "Whole season",
        },
        "Beans": {
            "Establishment": "Initial",
            "Flowering / pod set": "Development",
            "Pod filling": "Mid-season",
            "Full growing season": "Whole season",
        },
        "Sorghum": {
            "Establishment": "Initial",
            "Vegetative growth": "Development",
            "Flowering / grain filling": "Mid-season",
            "Full growing season": "Whole season",
        },
        "Tomato": {
            "Establishment": "Initial",
            "Flowering / fruit set": "Development",
            "Fruit development": "Mid-season",
            "Full growing season": "Whole season",
        },
        "Sugarcane": {
            "Establishment": "Planting to 25% canopy",
            "Grand growth": "Peak use",
            "Maturation": "Ripening",
            "Full growing season": "Whole season",
        },
        "Barley": {
            "Establishment": "Initial",
            "Vegetative growth": "Development",
            "Heading / grain filling": "Mid-season",
            "Full growing season": "Whole season",
        },
        "Avocado": {
            "Flowering": "Seasonal orchard coefficient",
            "Fruit development": "Seasonal orchard coefficient",
            "Full productive season": "Seasonal orchard coefficient",
        },
        "Citrus": {
            "Flowering / fruit set": "Annual/monthly orchard coefficient",
            "Fruit development": "Annual/monthly orchard coefficient",
            "Full productive season": "Annual/monthly orchard coefficient",
        },
    }
    if crop in explicit and app_stage in explicit[crop]:
        return explicit[crop][app_stage]

    stage_norm = _normalise(app_stage)
    if "full" in stage_norm or "whole" in stage_norm:
        return "Whole season"
    if any(token in stage_norm for token in ("plant", "establish", "initial")):
        return "Initial"
    if any(token in stage_norm for token in ("vegetative", "development")):
        return "Development"
    if any(token in stage_norm for token in ("flower", "heading", "fruit set", "pod set")):
        return "Mid-season"
    if any(token in stage_norm for token in ("fill", "matur", "ripen")):
        return "Late season"
    if "harvest" in stage_norm:
        return "Harvest endpoint"
    return None


def _select_stage_parameter(
    library: dict[str, Any],
    crop: str,
    app_stage: str,
) -> dict[str, Any] | None:
    rows = get_stage_parameter_rows(library, crop)
    if not rows:
        return None

    alias = _stage_alias(crop, app_stage)
    if alias:
        alias_norm = _normalise(alias)
        for row in rows:
            if _normalise(row.get("stage", "")) == alias_norm:
                return row

    app_norm = _normalise(app_stage)
    for row in rows:
        row_norm = _normalise(row.get("stage", ""))
        if app_norm and (app_norm in row_norm or row_norm in app_norm):
            return row

    return None


def _weighted_season_kc(stage_rows: list[dict[str, Any]]) -> float | None:
    weighted_values: list[tuple[float, float]] = []
    unweighted: list[float] = []
    for row in stage_rows:
        stage_name = _normalise(row.get("stage", ""))
        if "whole season" in stage_name or "harvest endpoint" in stage_name:
            continue
        kc = _midpoint(row.get("kc"))
        if kc is None:
            continue
        duration = _duration_midpoint(row.get("duration_days"))
        unweighted.append(kc)
        if duration is not None and duration > 0:
            weighted_values.append((kc, duration))
    if weighted_values:
        numerator = sum(kc * duration for kc, duration in weighted_values)
        denominator = sum(duration for _, duration in weighted_values)
        return float(numerator / denominator) if denominator else None
    if unweighted:
        return float(np.mean(unweighted))
    return None


def _crop_kc_fallback(library: dict[str, Any], crop: str) -> tuple[float | None, str, str | None]:
    rows = get_stage_parameter_rows(library, crop)
    if not rows:
        return None, "No validated Kc available", None

    if crop == "Coffee":
        # Research synthesis recommendation for a productive, full-sun orchard.
        return 0.95, "Productive full-sun coffee research prior", "B"

    selected = rows[0]
    kc = _midpoint(selected.get("kc"))
    return kc, selected.get("stage", "Crop coefficient"), selected.get("evidence_grade")


def get_validated_kc_default(
    library: dict[str, Any],
    crop: str,
    app_stage: str,
) -> tuple[float | None, float | None, float | None, str, str | None, list[str]]:
    rows = get_stage_parameter_rows(library, crop)
    selected = _select_stage_parameter(library, crop, app_stage)
    if selected is not None:
        kc = _midpoint(selected.get("kc"))
        if kc is None and _normalise(selected.get("stage", "")) == "whole season":
            kc = _weighted_season_kc(rows)
        return (
            kc,
            float(selected["ky"]) if selected.get("ky") is not None else None,
            float(selected["depletion_fraction_p"]) if selected.get("depletion_fraction_p") is not None else None,
            str(selected.get("stage", app_stage)),
            selected.get("evidence_grade"),
            list(selected.get("source_ids", [])),
        )

    kc, label, grade = _crop_kc_fallback(library, crop)
    profile = get_default_crop_profile(library, crop) or {}
    return kc, None, None, label, grade, list(profile.get("source_ids", []))


def _status_from_grade(grade: str | None, ready: bool = True) -> str:
    text = str(grade or "").upper()
    if not ready or text == "D":
        return "Insufficient evidence — no numerical default imposed"
    if "A" in text and "C" not in text:
        return "Validated official or direct field-supported default"
    if "B" in text:
        return "Literature-supported screening default"
    if "C" in text:
        return "Transparent proxy requiring local validation"
    return "Evidence status not classified"


def build_validated_thresholds(
    library: dict[str, Any],
    seasonal_windows: dict[str, dict[str, list[str]]],
    legacy_thresholds: dict[str, dict[str, dict[str, Any]]],
) -> tuple[dict[str, dict[str, dict[str, Any]]], dict[str, Any]]:
    output = deepcopy(legacy_thresholds)
    provenance: dict[str, Any] = {}

    for crop, stages in seasonal_windows.items():
        crop_data = library.get("crops", {}).get(crop)
        if not crop_data:
            continue
        profile = get_default_crop_profile(library, crop)
        if profile is None:
            continue

        temperature = profile.get("temperature", {}) or {}
        rainfall = profile.get("rainfall_envelope", {}) or {}
        water_requirement = profile.get("crop_water_requirement", {}) or {}
        profile_grade = profile.get("evidence_grade")
        profile_sources = list(profile.get("source_ids", []))

        output.setdefault(crop, {})
        provenance.setdefault(crop, {})

        for app_stage in stages:
            legacy = deepcopy(output.get(crop, {}).get(app_stage, {}))
            kc, ky, depletion_p, source_stage, stage_grade, stage_sources = get_validated_kc_default(
                library, crop, app_stage
            )

            temp_values = [
                temperature.get("absolute_min_c"),
                temperature.get("optimal_min_c"),
                temperature.get("optimal_max_c"),
                temperature.get("absolute_max_c"),
            ]
            rain_values = [
                rainfall.get("absolute_min_mm"),
                rainfall.get("optimal_min_mm"),
                rainfall.get("optimal_max_mm"),
                rainfall.get("absolute_max_mm"),
            ]
            temperature_ready = all(value is not None for value in temp_values)
            rainfall_ready = all(value is not None for value in rain_values)
            water_ready = kc is not None

            thresholds = {
                **legacy,
                "temp_min_abs": float(temp_values[0]) if temperature_ready else float(legacy.get("temp_min_abs", 0.0)),
                "temp_min_opt": float(temp_values[1]) if temperature_ready else float(legacy.get("temp_min_opt", 0.0)),
                "temp_max_opt": float(temp_values[2]) if temperature_ready else float(legacy.get("temp_max_opt", 0.0)),
                "temp_max_abs": float(temp_values[3]) if temperature_ready else float(legacy.get("temp_max_abs", 0.0)),
                "precip_min_abs": float(rain_values[0]) if rainfall_ready else float(legacy.get("precip_min_abs", 0.0)),
                "precip_min_opt": float(rain_values[1]) if rainfall_ready else float(legacy.get("precip_min_opt", 0.0)),
                "precip_max_opt": float(rain_values[2]) if rainfall_ready else float(legacy.get("precip_max_opt", 0.0)),
                "precip_max_abs": float(rain_values[3]) if rainfall_ready else float(legacy.get("precip_max_abs", 0.0)),
                "water_deficit_abs": float(legacy.get("water_deficit_abs", -9999.0)),
                "water_deficit_opt": float(legacy.get("water_deficit_opt", 0.0)),
                "parameter_method": "validated_fao_etc",
                "water_method": "fao_etc_ky" if water_ready else "not_available",
                "temperature_scoring_enabled": bool(temperature_ready),
                "precipitation_scoring_enabled": bool(rainfall_ready),
                "water_scoring_enabled": bool(water_ready),
                "kc_default": float(kc) if kc is not None else None,
                "ky_default": float(ky) if ky is not None else None,
                "depletion_fraction_p": float(depletion_p) if depletion_p is not None else None,
                "effective_precipitation_fraction": DEFAULT_EFFECTIVE_PRECIPITATION_FRACTION,
                "source_stage": source_stage,
                "profile_name": profile.get("profile_name", crop),
                "scientific_name": profile.get("scientific_name", ""),
                "parameter_evidence_grade": stage_grade or profile_grade or "Unclassified",
                "parameter_status": _status_from_grade(stage_grade or profile_grade, ready=(temperature_ready or rainfall_ready or water_ready)),
                "source_ids": sorted(set(profile_sources + stage_sources)),
                "temperature_basis": temperature.get("basis", ""),
                "rainfall_basis": rainfall.get("basis", ""),
                "crop_water_requirement_min_mm": water_requirement.get("min_mm"),
                "crop_water_requirement_max_mm": water_requirement.get("max_mm"),
                "crop_water_requirement_period": water_requirement.get("period"),
                "profile_notes": profile.get("notes", ""),
                "planting_calendar_status": "Default months are illustrative only. Select locally appropriate months or an official SIAP/INIFAP calendar.",
            }
            output[crop][app_stage] = thresholds
            provenance[crop][app_stage] = {
                "profile": profile,
                "stage_parameter": _select_stage_parameter(library, crop, app_stage),
                "thresholds": thresholds,
            }

    return output, provenance


def trapezoid_suitability(
    value: float,
    minimum_absolute: float,
    minimum_optimal: float,
    maximum_optimal: float,
    maximum_absolute: float,
) -> float:
    if pd.isna(value):
        return np.nan
    if value < minimum_absolute or value > maximum_absolute:
        return 0.0
    if minimum_optimal <= value <= maximum_optimal:
        return 100.0
    if value < minimum_optimal:
        denominator = minimum_optimal - minimum_absolute
        return 100.0 if abs(denominator) < 1e-12 else float((value - minimum_absolute) / denominator * 100.0)
    denominator = maximum_absolute - maximum_optimal
    return 100.0 if abs(denominator) < 1e-12 else float((maximum_absolute - value) / denominator * 100.0)


def _legacy_water_score(water_deficit: float, absolute: float, optimal: float) -> float:
    if pd.isna(water_deficit):
        return np.nan
    if water_deficit >= optimal:
        return 100.0
    if water_deficit <= absolute:
        return 0.0
    denominator = optimal - absolute
    return 100.0 if abs(denominator) < 1e-12 else float((water_deficit - absolute) / denominator * 100.0)


def _classify(score: float) -> str:
    if pd.isna(score):
        return "Unknown"
    if score >= 80:
        return "Highly suitable"
    if score >= 60:
        return "Suitable"
    if score >= 40:
        return "Marginal"
    if score >= 20:
        return "Poor"
    return "Unsuitable"


def compute_crop_window_suitability_table(
    df_long: pd.DataFrame,
    crop: str,
    stage: str,
    year: int,
    months: list[str],
    aggregation_method: str,
    thresholds: dict[str, Any],
    month_days: dict[str, int],
) -> pd.DataFrame:
    required_variables = [
        "TEMPERATURE",
        "TEMPERATURE_MAX",
        "TEMPERATURE_MIN",
        "PRECIPITATION_AVG",
        "EVAPOTRANSPIRATION",
        "SOLAR_RADIATION",
        "SOIL_TEMP_LAYER1",
    ]
    selected_months = [str(month).upper() for month in months]
    filtered = df_long[
        df_long["Year"].eq(int(year))
        & df_long["Month"].isin(selected_months)
        & df_long["Variable"].isin(required_variables)
    ].copy()
    if filtered.empty:
        return pd.DataFrame()

    monthly = (
        filtered.groupby(["CITY", "STATE", "Month", "Variable"], as_index=False)["Value"]
        .mean()
        .pivot_table(index=["CITY", "STATE", "Month"], columns="Variable", values="Value", aggfunc="mean")
        .reset_index()
    )
    for variable in required_variables:
        if variable not in monthly.columns:
            monthly[variable] = np.nan

    monthly["Days"] = monthly["Month"].map(month_days).fillna(30)
    monthly["Precipitation Total"] = monthly["PRECIPITATION_AVG"] * monthly["Days"]
    monthly["ETo Total"] = monthly["EVAPOTRANSPIRATION"] * monthly["Days"]

    aggregated = monthly.groupby(["CITY", "STATE"], as_index=False).agg(
        **{
            "Mean Temperature (°C)": ("TEMPERATURE", "mean"),
            "Mean Temp Max (°C)": ("TEMPERATURE_MAX", "mean"),
            "Mean Temp Min (°C)": ("TEMPERATURE_MIN", "mean"),
            "Mean Daily Precipitation (mm/day)": ("PRECIPITATION_AVG", "mean"),
            "Seasonal Precipitation Total (mm)": ("Precipitation Total", lambda values: values.sum(min_count=1)),
            "Mean Daily ETo (mm/day)": ("EVAPOTRANSPIRATION", "mean"),
            "Seasonal ETo Total (mm)": ("ETo Total", lambda values: values.sum(min_count=1)),
            "Mean Solar Radiation": ("SOLAR_RADIATION", "mean"),
            "Mean Soil Temp Layer 1 (°C)": ("SOIL_TEMP_LAYER1", "mean"),
            "N Months Available": ("Month", "nunique"),
        }
    )

    annual_precip = df_long[
        df_long["Year"].eq(int(year))
        & df_long["Variable"].eq("PRECIPITATION_AVG")
    ].copy()
    if not annual_precip.empty:
        annual_precip["Days"] = annual_precip["Month"].map(month_days).fillna(30)
        annual_precip["Annual Precipitation"] = annual_precip["Value"] * annual_precip["Days"]
        annual_precip = annual_precip.groupby(["CITY", "STATE"], as_index=False)["Annual Precipitation"].sum(min_count=1)
        annual_precip = annual_precip.rename(columns={"Annual Precipitation": "Annual Precipitation Total (mm)"})
        aggregated = aggregated.merge(annual_precip, on=["CITY", "STATE"], how="left")
    else:
        aggregated["Annual Precipitation Total (mm)"] = np.nan

    aggregated["Water Deficit P - ETo (mm)"] = (
        aggregated["Seasonal Precipitation Total (mm)"] - aggregated["Seasonal ETo Total (mm)"]
    )

    kc = thresholds.get("kc_default")
    ky = thresholds.get("ky_default")
    effective_fraction = float(thresholds.get("effective_precipitation_fraction", DEFAULT_EFFECTIVE_PRECIPITATION_FRACTION))
    if kc is not None and pd.notna(kc):
        aggregated["Crop Coefficient Kc"] = float(kc)
        aggregated["Crop ETc Total (mm)"] = aggregated["Seasonal ETo Total (mm)"] * float(kc)
        aggregated["Effective Precipitation (mm)"] = aggregated["Seasonal Precipitation Total (mm)"] * effective_fraction
        aggregated["Water Adequacy ETa / ETm"] = np.where(
            aggregated["Crop ETc Total (mm)"].abs() > 1e-12,
            aggregated["Effective Precipitation (mm)"] / aggregated["Crop ETc Total (mm)"],
            np.nan,
        )
    else:
        aggregated["Crop Coefficient Kc"] = np.nan
        aggregated["Crop ETc Total (mm)"] = np.nan
        aggregated["Effective Precipitation (mm)"] = aggregated["Seasonal Precipitation Total (mm)"] * effective_fraction
        aggregated["Water Adequacy ETa / ETm"] = np.nan

    aggregated["Yield Response Factor Ky"] = float(ky) if ky is not None and pd.notna(ky) else np.nan

    def calculate_components(row: pd.Series) -> pd.Series:
        if thresholds.get("temperature_scoring_enabled", True):
            temperature_score = trapezoid_suitability(
                row["Mean Temperature (°C)"],
                float(thresholds["temp_min_abs"]),
                float(thresholds["temp_min_opt"]),
                float(thresholds["temp_max_opt"]),
                float(thresholds["temp_max_abs"]),
            )
        else:
            temperature_score = np.nan

        if thresholds.get("precipitation_scoring_enabled", True):
            rainfall_value = row.get("Annual Precipitation Total (mm)", np.nan)
            precipitation_score = trapezoid_suitability(
                rainfall_value,
                float(thresholds["precip_min_abs"]),
                float(thresholds["precip_min_opt"]),
                float(thresholds["precip_max_opt"]),
                float(thresholds["precip_max_abs"]),
            )
        else:
            precipitation_score = np.nan

        method = str(thresholds.get("water_method", "legacy_deficit"))
        relative_yield = np.nan
        if method.startswith("fao_etc") and thresholds.get("water_scoring_enabled", False):
            ratio = row.get("Water Adequacy ETa / ETm", np.nan)
            if pd.isna(ratio):
                water_score = np.nan
            else:
                bounded_ratio = float(np.clip(ratio, 0.0, 1.0))
                if ky is not None and pd.notna(ky):
                    relative_yield = float(np.clip(1.0 - float(ky) * (1.0 - bounded_ratio), 0.0, 1.0))
                    water_score = relative_yield * 100.0
                else:
                    water_score = bounded_ratio * 100.0
                    relative_yield = bounded_ratio
        elif method == "not_available":
            water_score = np.nan
        else:
            water_score = _legacy_water_score(
                row["Water Deficit P - ETo (mm)"],
                float(thresholds.get("water_deficit_abs", -500.0)),
                float(thresholds.get("water_deficit_opt", 0.0)),
            )

        scores = {
            "Temperature": temperature_score,
            "Broad rainfall envelope": precipitation_score,
            "FAO water adequacy": water_score,
        }
        available = {name: value for name, value in scores.items() if value is not None and pd.notna(value)}
        if not available:
            overall = np.nan
            limiting = "Unavailable"
        elif aggregation_method == "Mean of components":
            overall = float(np.mean(list(available.values())))
            limiting = min(available, key=available.get)
        else:
            limiting = min(available, key=available.get)
            overall = float(available[limiting])

        return pd.Series(
            {
                "Temperature Suitability (%)": temperature_score,
                "Precipitation Suitability (%)": precipitation_score,
                "Water Balance Suitability (%)": water_score,
                "Water Adequacy Suitability (%)": water_score,
                "Relative Water-Limited Yield (%)": relative_yield * 100.0 if pd.notna(relative_yield) else np.nan,
                "Overall Suitability (%)": overall,
                "Suitability Class": _classify(overall),
                "Limiting Factor": limiting,
            }
        )

    components = aggregated.apply(calculate_components, axis=1)
    result = pd.concat([aggregated, components], axis=1)
    result.insert(2, "Location", result["CITY"] + " (" + result["STATE"] + ")")
    result["Crop"] = crop
    result["Seasonal Window"] = stage
    result["Year"] = int(year)
    result["Months Included"] = ", ".join(months)
    result["N Months Selected"] = len(months)
    result["Parameter Method"] = thresholds.get("parameter_method", "legacy_custom_thresholds")
    result["Parameter Profile"] = thresholds.get("profile_name", "Custom / legacy profile")
    result["Parameter Evidence Grade"] = thresholds.get("parameter_evidence_grade", "User supplied")
    result["Parameter Status"] = thresholds.get("parameter_status", "User-supplied or legacy profile")
    result["Parameter Source IDs"] = ", ".join(thresholds.get("source_ids", []))
    result["Effective Precipitation Fraction"] = effective_fraction
    return result.sort_values("Overall Suitability (%)", ascending=False, na_position="last").reset_index(drop=True)


def crop_profile_summary(library: dict[str, Any], crop: str, profile_name: str | None = None) -> dict[str, Any]:
    profiles = get_crop_profiles(library, crop)
    if not profiles:
        return {}
    profile = next((item for item in profiles if item.get("profile_name") == profile_name), None) if profile_name else None
    profile = profile or get_default_crop_profile(library, crop) or profiles[0]
    temperature = profile.get("temperature", {}) or {}
    rainfall = profile.get("rainfall_envelope", {}) or {}
    water = profile.get("crop_water_requirement", {}) or {}
    duration = profile.get("crop_duration_days", {}) or {}
    return {
        "Crop": crop,
        "Profile": profile.get("profile_name"),
        "Scientific name": profile.get("scientific_name"),
        "Temperature absolute minimum (°C)": temperature.get("absolute_min_c"),
        "Temperature optimum minimum (°C)": temperature.get("optimal_min_c"),
        "Temperature optimum maximum (°C)": temperature.get("optimal_max_c"),
        "Temperature absolute maximum (°C)": temperature.get("absolute_max_c"),
        "Rainfall absolute minimum (mm)": rainfall.get("absolute_min_mm"),
        "Rainfall optimum minimum (mm)": rainfall.get("optimal_min_mm"),
        "Rainfall optimum maximum (mm)": rainfall.get("optimal_max_mm"),
        "Rainfall absolute maximum (mm)": rainfall.get("absolute_max_mm"),
        "Crop water requirement minimum (mm)": water.get("min_mm"),
        "Crop water requirement maximum (mm)": water.get("max_mm"),
        "Water requirement period": water.get("period"),
        "Crop duration minimum (days)": duration.get("min"),
        "Crop duration maximum (days)": duration.get("max"),
        "Evidence grade": profile.get("evidence_grade"),
        "Implementation status": profile.get("implementation_status"),
        "Temperature basis": temperature.get("basis"),
        "Rainfall basis": rainfall.get("basis"),
        "Notes": profile.get("notes"),
        "Source IDs": ", ".join(profile.get("source_ids", [])),
    }


def stage_parameter_table(library: dict[str, Any], crop: str) -> pd.DataFrame:
    rows = []
    for item in get_stage_parameter_rows(library, crop):
        rows.append(
            {
                "Stage": item.get("stage"),
                "Interpretation": item.get("interpretation"),
                "Duration min (days)": (item.get("duration_days") or {}).get("min"),
                "Duration max (days)": (item.get("duration_days") or {}).get("max"),
                "Kc min": (item.get("kc") or {}).get("min"),
                "Kc max": (item.get("kc") or {}).get("max"),
                "Kc default": _midpoint(item.get("kc")),
                "Ky": item.get("ky"),
                "Depletion fraction p": item.get("depletion_fraction_p"),
                "Evidence grade": item.get("evidence_grade"),
                "Source IDs": ", ".join(item.get("source_ids", [])),
            }
        )
    return pd.DataFrame(rows)


def source_table(library: dict[str, Any], source_ids: list[str] | None = None) -> pd.DataFrame:
    sources = library.get("sources", {})
    wanted = source_ids or list(sources)
    rows = []
    for source_id in wanted:
        source = sources.get(source_id)
        if not source:
            continue
        rows.append(
            {
                "Source ID": source_id,
                "Citation": source.get("citation"),
                "Organisation": source.get("organization"),
                "Year": source.get("year"),
                "Source type": source.get("source_type"),
                "Supports": source.get("supports"),
                "Evidence grade": source.get("quality"),
                "URL": source.get("url"),
            }
        )
    return pd.DataFrame(rows)
