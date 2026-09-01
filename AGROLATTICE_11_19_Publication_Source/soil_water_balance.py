"""Daily root-zone soil-water balance and irrigation scheduling utilities.

The calculations follow the FAO-56 single-crop-coefficient root-zone balance:
TAW = 1000 (theta_FC - theta_WP) Zr
RAW = p TAW
Ks = 1 above RAW; below RAW Ks declines linearly to zero at TAW
Dr_i = Dr_i-1 - (P - RO) - I - CR + ETc_adj + DP

This module is independent of Streamlit so it can be unit tested and reused.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

MODULE_VERSION = "1.1.0"
FAO56_ROOT_ZONE_URL = "https://www.fao.org/4/X0490E/x0490e0e.htm"
FAO56_SOURCE_NOTE = "FAO Irrigation and Drainage Paper 56, Chapter 8"

# Three directly traceable FAO-56 examples. They are broad texture-class
# screening values and are not substitutes for field/laboratory measurements.
SOIL_PRESETS: dict[str, dict[str, Any]] = {
    "Loamy sand — FAO screening": {
        "theta_fc": 0.15,
        "theta_wp": 0.06,
        "awc_mm_per_m": 90.0,
        "description": "FAO-56 worked-example representative values.",
        "evidence_grade": "A source / screening application",
        "source": FAO56_SOURCE_NOTE,
        "source_url": FAO56_ROOT_ZONE_URL,
    },
    "Silt — FAO screening": {
        "theta_fc": 0.32,
        "theta_wp": 0.15,
        "awc_mm_per_m": 170.0,
        "description": "FAO-56 worked-example representative values.",
        "evidence_grade": "A source / screening application",
        "source": FAO56_SOURCE_NOTE,
        "source_url": FAO56_ROOT_ZONE_URL,
    },
    "Silty clay — FAO screening": {
        "theta_fc": 0.35,
        "theta_wp": 0.23,
        "awc_mm_per_m": 120.0,
        "description": "FAO-56 worked-example representative values.",
        "evidence_grade": "A source / screening application",
        "source": FAO56_SOURCE_NOTE,
        "source_url": FAO56_ROOT_ZONE_URL,
    },
}

# FAO-56 Table 22 maximum effective rooting depth and p at ETc ~5 mm/day.
# Agave uses the FAO sisal entry only as an explicit proxy.
CROP_ROOT_DEFAULTS: dict[str, dict[str, Any]] = {
    "Maize": {"root_min_m": 1.0, "root_max_m": 1.7, "p": 0.55, "grade": "A", "basis": "FAO field maize"},
    "Coffee": {"root_min_m": 0.9, "root_max_m": 1.5, "p": 0.40, "grade": "A", "basis": "FAO coffee"},
    "Wheat": {"root_min_m": 1.0, "root_max_m": 1.5, "p": 0.55, "grade": "A", "basis": "FAO spring wheat"},
    "Beans": {"root_min_m": 0.6, "root_max_m": 0.9, "p": 0.45, "grade": "A", "basis": "FAO dry beans and pulses"},
    "Sorghum": {"root_min_m": 1.0, "root_max_m": 2.0, "p": 0.55, "grade": "A", "basis": "FAO grain sorghum"},
    "Avocado": {"root_min_m": 0.5, "root_max_m": 1.0, "p": 0.70, "grade": "A", "basis": "FAO avocado"},
    "Agave": {"root_min_m": 0.5, "root_max_m": 1.0, "p": 0.80, "grade": "C proxy", "basis": "FAO sisal proxy; local validation required"},
    "Tomato": {"root_min_m": 0.7, "root_max_m": 1.5, "p": 0.40, "grade": "A", "basis": "FAO tomato"},
    "Sugarcane": {"root_min_m": 1.2, "root_max_m": 2.0, "p": 0.65, "grade": "A", "basis": "FAO sugar cane"},
    "Barley": {"root_min_m": 1.0, "root_max_m": 1.5, "p": 0.55, "grade": "A", "basis": "FAO barley"},
    "Citrus": {"root_min_m": 1.2, "root_max_m": 1.5, "p": 0.50, "grade": "A", "basis": "FAO citrus, mature canopy"},
}

WATER_BALANCE_REQUIRED_POWER_PARAMETERS: tuple[str, ...] = (
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "RH2M",
    "WS2M",
    "ALLSKY_SFC_SW_DWN",
    "PS",
    "PRECTOTCORR",
)


class SoilWaterBalanceError(RuntimeError):
    """Raised when the root-zone model cannot be evaluated safely."""


@dataclass(frozen=True)
class SoilProfile:
    name: str
    theta_fc: float
    theta_wp: float
    source: str = "User supplied"
    source_url: str | None = None
    evidence_grade: str = "User supplied"

    @property
    def awc_mm_per_m(self) -> float:
        return 1000.0 * (float(self.theta_fc) - float(self.theta_wp))

    def validated(self) -> "SoilProfile":
        fc = float(self.theta_fc)
        wp = float(self.theta_wp)
        if not (0 < wp < fc < 0.8):
            raise ValueError("Require 0 < wilting point < field capacity < 0.8 m³ m⁻³.")
        if self.awc_mm_per_m < 10 or self.awc_mm_per_m > 500:
            raise ValueError("Available water capacity is outside a broad 10–500 mm m⁻¹ screening range.")
        return self


@dataclass(frozen=True)
class IrrigationStrategy:
    mode: str = "Rainfed"
    application_efficiency: float = 0.75
    trigger_fraction_of_raw: float = 1.0
    refill_fraction: float = 1.0
    maximum_gross_application_mm: float = 60.0
    fixed_interval_days: int = 7
    fixed_gross_application_mm: float = 25.0
    sensor_metric: str = "Volumetric water content (%)"
    sensor_trigger_threshold: float = 20.0
    sensor_stop_threshold: float | None = None
    sensor_max_age_days: int = 2

    def validated(self) -> "IrrigationStrategy":
        mode = str(self.mode)
        allowed = {"Rainfed", "Irrigate at RAW", "Deficit irrigation", "Fixed interval", "Uploaded schedule", "Sensor-triggered"}
        if mode not in allowed:
            raise ValueError(f"Unknown irrigation strategy: {mode}")
        if not 0 < float(self.application_efficiency) <= 1:
            raise ValueError("Application efficiency must be in (0, 1].")
        if not 0.1 <= float(self.trigger_fraction_of_raw) <= 2.0:
            raise ValueError("Trigger fraction must be between 0.1 and 2.0 × RAW.")
        if not 0 <= float(self.refill_fraction) <= 1:
            raise ValueError("Refill fraction must be between 0 and 1.")
        if float(self.maximum_gross_application_mm) < 0:
            raise ValueError("Maximum gross application cannot be negative.")
        if int(self.fixed_interval_days) < 1:
            raise ValueError("Fixed interval must be at least one day.")
        if str(self.sensor_metric) not in {"Volumetric water content (%)", "Volumetric water content (fraction)", "Soil water tension (kPa)", "Raw sensor value"}:
            raise ValueError(f"Unknown sensor metric: {self.sensor_metric}")
        if not np.isfinite(float(self.sensor_trigger_threshold)):
            raise ValueError("Sensor trigger threshold must be numeric.")
        if int(self.sensor_max_age_days) < 0 or int(self.sensor_max_age_days) > 30:
            raise ValueError("Sensor maximum age must be between 0 and 30 days.")
        return self


def soil_profile_from_preset(name: str) -> SoilProfile:
    if name not in SOIL_PRESETS:
        raise KeyError(f"Unknown soil preset: {name}")
    row = SOIL_PRESETS[name]
    return SoilProfile(
        name=name,
        theta_fc=float(row["theta_fc"]),
        theta_wp=float(row["theta_wp"]),
        source=str(row["source"]),
        source_url=str(row["source_url"]),
        evidence_grade=str(row["evidence_grade"]),
    ).validated()


def crop_root_defaults(crop: str) -> dict[str, Any]:
    default = CROP_ROOT_DEFAULTS.get(str(crop), None)
    if default is None:
        return {"root_min_m": 0.5, "root_max_m": 1.0, "p": 0.5, "grade": "Fallback", "basis": "Generic user-editable fallback"}
    return dict(default)


def _numeric_midpoint(value: Mapping[str, Any] | None) -> float | None:
    if not isinstance(value, Mapping):
        return None
    low = pd.to_numeric(value.get("min"), errors="coerce")
    high = pd.to_numeric(value.get("max"), errors="coerce")
    if pd.isna(low) and pd.isna(high):
        return None
    if pd.isna(low):
        low = high
    if pd.isna(high):
        high = low
    return float((float(low) + float(high)) / 2.0)


def available_water_profiles(library: Mapping[str, Any], crop: str) -> list[str]:
    record = (library.get("crops") or {}).get(crop, {})
    profiles = [str(row.get("profile")) for row in record.get("stage_water_parameters", []) if row.get("profile")]
    return list(dict.fromkeys(profiles))


def stage_parameter_rows(library: Mapping[str, Any], crop: str, profile: str) -> pd.DataFrame:
    record = (library.get("crops") or {}).get(crop, {})
    rows: list[dict[str, Any]] = []
    for row in record.get("stage_water_parameters", []):
        if str(row.get("profile")) != str(profile):
            continue
        stage = str(row.get("stage") or "Stage")
        if stage.casefold() in {"whole season", "harvest endpoint"}:
            continue
        duration = row.get("duration_days") or {}
        rows.append(
            {
                "Stage": stage,
                "Duration minimum (days)": pd.to_numeric(duration.get("min"), errors="coerce"),
                "Duration maximum (days)": pd.to_numeric(duration.get("max"), errors="coerce"),
                "Kc": _numeric_midpoint(row.get("kc")),
                "Ky": pd.to_numeric(row.get("ky"), errors="coerce"),
                "p": pd.to_numeric(row.get("depletion_fraction_p"), errors="coerce"),
                "Interpretation": str(row.get("interpretation") or ""),
                "Evidence grade": str(row.get("evidence_grade") or "Unspecified"),
                "Source IDs": ", ".join(str(item) for item in row.get("source_ids", [])),
            }
        )
    return pd.DataFrame(rows)


def whole_season_ky(library: Mapping[str, Any], crop: str, profile: str) -> float | None:
    record = (library.get("crops") or {}).get(crop, {})
    for row in record.get("stage_water_parameters", []):
        if str(row.get("profile")) == str(profile) and str(row.get("stage", "")).casefold() == "whole season":
            value = pd.to_numeric(row.get("ky"), errors="coerce")
            return None if pd.isna(value) else float(value)
    return None


def _duration_value(row: Mapping[str, Any], strategy: str, fallback: int | None = None) -> int | None:
    low = pd.to_numeric(row.get("Duration minimum (days)"), errors="coerce")
    high = pd.to_numeric(row.get("Duration maximum (days)"), errors="coerce")
    if pd.isna(low) and pd.isna(high):
        return fallback
    if pd.isna(low):
        low = high
    if pd.isna(high):
        high = low
    strategy_normalised = str(strategy).casefold()
    if strategy_normalised.startswith("min"):
        return max(1, int(round(float(low))))
    if strategy_normalised.startswith("max"):
        return max(1, int(round(float(high))))
    return max(1, int(round((float(low) + float(high)) / 2.0)))


def build_stage_schedule(
    library: Mapping[str, Any],
    crop: str,
    profile: str,
    planting_date: date | datetime | str,
    *,
    duration_strategy: str = "Midpoint",
    custom_season_days: int = 120,
    constant_kc: float | None = None,
    constant_p: float | None = None,
) -> pd.DataFrame:
    planting = pd.Timestamp(planting_date).normalize()
    table = stage_parameter_rows(library, crop, profile)
    usable_duration = table[["Duration minimum (days)", "Duration maximum (days)"]].notna().any(axis=1) if not table.empty else pd.Series(dtype=bool)

    if table.empty or not bool(usable_duration.any()):
        kc_values = pd.to_numeric(table.get("Kc"), errors="coerce") if not table.empty else pd.Series(dtype=float)
        kc = float(constant_kc) if constant_kc is not None else (float(kc_values.dropna().mean()) if kc_values.notna().any() else np.nan)
        p_values = pd.to_numeric(table.get("p"), errors="coerce") if not table.empty else pd.Series(dtype=float)
        p_value = float(constant_p) if constant_p is not None else (float(p_values.dropna().mean()) if p_values.notna().any() else np.nan)
        if not np.isfinite(kc):
            raise SoilWaterBalanceError(
                f"{crop} / {profile} has no validated Kc. Enter an explicit user-supplied Kc to run the model."
            )
        days = max(1, int(custom_season_days))
        return pd.DataFrame(
            [{
                "Stage": str(table.iloc[0]["Stage"]) if not table.empty else "User-defined season",
                "Start date": planting,
                "End date": planting + pd.Timedelta(days=days - 1),
                "Duration (days)": days,
                "Kc": kc,
                "Ky": float(pd.to_numeric(table.iloc[0].get("Ky"), errors="coerce")) if not table.empty and pd.notna(pd.to_numeric(table.iloc[0].get("Ky"), errors="coerce")) else np.nan,
                "p": p_value,
                "Interpretation": str(table.iloc[0].get("Interpretation", "")) if not table.empty else "User-defined constant crop coefficient",
                "Evidence grade": str(table.iloc[0].get("Evidence grade", "User supplied")) if not table.empty else "User supplied",
                "Source IDs": str(table.iloc[0].get("Source IDs", "")) if not table.empty else "",
                "Duration basis": "User-defined season length",
            }]
        )

    records: list[dict[str, Any]] = []
    current = planting
    for _, row in table.iterrows():
        duration = _duration_value(row, duration_strategy)
        if duration is None:
            continue
        kc = pd.to_numeric(row.get("Kc"), errors="coerce")
        if pd.isna(kc):
            continue
        end = current + pd.Timedelta(days=int(duration) - 1)
        records.append(
            {
                "Stage": row["Stage"],
                "Start date": current,
                "End date": end,
                "Duration (days)": int(duration),
                "Kc": float(kc),
                "Ky": float(row["Ky"]) if pd.notna(row["Ky"]) else np.nan,
                "p": float(row["p"]) if pd.notna(row["p"]) else np.nan,
                "Interpretation": row["Interpretation"],
                "Evidence grade": row["Evidence grade"],
                "Source IDs": row["Source IDs"],
                "Duration basis": str(duration_strategy),
            }
        )
        current = end + pd.Timedelta(days=1)
    if not records:
        raise SoilWaterBalanceError("No usable crop stages were available for the selected profile.")
    return pd.DataFrame(records)


def estimate_elevation_from_pressure_kpa(pressure_kpa: np.ndarray) -> np.ndarray:
    pressure = np.maximum(np.asarray(pressure_kpa, dtype=float), 1e-6)
    return 44330.0 * (1.0 - np.power(pressure / 101.325, 0.1903))


def calculate_fao56_eto_daily(frame: pd.DataFrame, latitude: float) -> pd.Series:
    required = ["DATE", "T2M", "T2M_MAX", "T2M_MIN", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN", "PS"]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise SoilWaterBalanceError(f"Daily weather is missing ETo inputs: {', '.join(missing)}")

    tmean = pd.to_numeric(frame["T2M"], errors="coerce").to_numpy(float)
    tmax = pd.to_numeric(frame["T2M_MAX"], errors="coerce").to_numpy(float)
    tmin = pd.to_numeric(frame["T2M_MIN"], errors="coerce").to_numpy(float)
    rh = np.clip(pd.to_numeric(frame["RH2M"], errors="coerce").to_numpy(float), 0.0, 100.0)
    wind = np.maximum(pd.to_numeric(frame["WS2M"], errors="coerce").to_numpy(float), 0.0)
    rs = np.maximum(pd.to_numeric(frame["ALLSKY_SFC_SW_DWN"], errors="coerce").to_numpy(float), 0.0)
    pressure = pd.to_numeric(frame["PS"], errors="coerce").to_numpy(float)

    es_max = 0.6108 * np.exp((17.27 * tmax) / (tmax + 237.3))
    es_min = 0.6108 * np.exp((17.27 * tmin) / (tmin + 237.3))
    es = (es_max + es_min) / 2.0
    ea = es * rh / 100.0
    delta = 4098.0 * (0.6108 * np.exp((17.27 * tmean) / (tmean + 237.3))) / np.power(tmean + 237.3, 2)
    gamma = 0.000665 * pressure

    lat_rad = math.radians(float(latitude))
    doy = pd.to_datetime(frame["DATE"]).dt.dayofyear.to_numpy(float)
    dr = 1.0 + 0.033 * np.cos((2.0 * np.pi / 365.0) * doy)
    declination = 0.409 * np.sin((2.0 * np.pi / 365.0) * doy - 1.39)
    omega = np.arccos(np.clip(-np.tan(lat_rad) * np.tan(declination), -1.0, 1.0))
    ra = (24.0 * 60.0 / np.pi) * 0.0820 * dr * (
        omega * np.sin(lat_rad) * np.sin(declination)
        + np.cos(lat_rad) * np.cos(declination) * np.sin(omega)
    )
    elevation = estimate_elevation_from_pressure_kpa(pressure)
    rso = np.maximum((0.75 + 2e-5 * elevation) * ra, 1e-6)
    relative_solar = np.clip(rs / rso, 0.0, 1.0)
    rns = (1.0 - 0.23) * rs
    rnl = 4.903e-9 * (np.power(tmax + 273.16, 4) + np.power(tmin + 273.16, 4)) / 2.0
    rnl *= (0.34 - 0.14 * np.sqrt(np.maximum(ea, 0.0))) * (1.35 * relative_solar - 0.35)
    rn = rns - rnl

    numerator = 0.408 * delta * rn + gamma * (900.0 / (tmean + 273.0)) * wind * np.maximum(es - ea, 0.0)
    denominator = delta + gamma * (1.0 + 0.34 * wind)
    eto = np.divide(numerator, denominator, out=np.full_like(numerator, np.nan), where=denominator > 0)
    eto = np.where(np.isfinite(eto), np.maximum(eto, 0.0), np.nan)
    return pd.Series(eto, index=frame.index, name="ETo (mm)")


def prepare_daily_weather(weather: pd.DataFrame, latitude: float) -> pd.DataFrame:
    if "DATE" not in weather.columns:
        raise SoilWaterBalanceError("Daily weather requires a DATE column.")
    frame = weather.copy()
    frame["DATE"] = pd.to_datetime(frame["DATE"], errors="coerce")
    frame = frame.dropna(subset=["DATE"]).sort_values("DATE").drop_duplicates("DATE", keep="last").reset_index(drop=True)
    frame["Precipitation (mm)"] = pd.to_numeric(frame.get("PRECTOTCORR"), errors="coerce").clip(lower=0)
    frame["ETo (mm)"] = calculate_fao56_eto_daily(frame, latitude)
    return frame


def assign_stage_parameters(
    daily: pd.DataFrame,
    schedule: pd.DataFrame,
    *,
    fallback_p: float,
    initial_root_depth_m: float,
    maximum_root_depth_m: float,
    dynamic_root_growth: bool = True,
) -> pd.DataFrame:
    frame = daily.copy()
    frame["DATE"] = pd.to_datetime(frame["DATE"], errors="coerce")
    frame["Stage"] = None
    frame["Kc"] = np.nan
    frame["Ky"] = np.nan
    frame["p base"] = np.nan
    frame["Stage evidence grade"] = None
    frame["Stage source IDs"] = None

    for _, row in schedule.iterrows():
        start = pd.Timestamp(row["Start date"])
        end = pd.Timestamp(row["End date"])
        mask = frame["DATE"].between(start, end)
        frame.loc[mask, "Stage"] = str(row["Stage"])
        frame.loc[mask, "Kc"] = float(row["Kc"])
        if pd.notna(row.get("Ky")):
            frame.loc[mask, "Ky"] = float(row["Ky"])
        p_value = pd.to_numeric(row.get("p"), errors="coerce")
        frame.loc[mask, "p base"] = float(p_value) if pd.notna(p_value) else float(fallback_p)
        frame.loc[mask, "Stage evidence grade"] = str(row.get("Evidence grade", ""))
        frame.loc[mask, "Stage source IDs"] = str(row.get("Source IDs", ""))

    frame = frame.loc[frame["Stage"].notna()].copy()
    if frame.empty:
        raise SoilWaterBalanceError("No daily records overlap the crop-stage schedule.")

    n = len(frame)
    initial_zr = max(0.05, float(initial_root_depth_m))
    maximum_zr = max(initial_zr, float(maximum_root_depth_m))
    if dynamic_root_growth and n > 1:
        # Reach maximum rooting depth by the beginning of the mid-season half
        # of the schedule; this is a transparent approximation to FAO Annex 8.
        midpoint_index = max(1, int(round(n * 0.5)))
        root_depth = np.empty(n, dtype=float)
        root_depth[:midpoint_index] = np.linspace(initial_zr, maximum_zr, midpoint_index)
        root_depth[midpoint_index:] = maximum_zr
    else:
        root_depth = np.full(n, maximum_zr, dtype=float)
    frame["Root depth (m)"] = root_depth
    return frame.reset_index(drop=True)


def calculate_runoff_mm(precipitation_mm: float, method: str, *, fixed_fraction: float = 0.0, curve_number: float = 75.0) -> float:
    p = max(0.0, float(precipitation_mm) if np.isfinite(precipitation_mm) else 0.0)
    method_normalised = str(method).casefold()
    if method_normalised.startswith("none"):
        return 0.0
    if method_normalised.startswith("fixed"):
        return p * float(np.clip(fixed_fraction, 0.0, 1.0))
    if "curve" in method_normalised or "nrcs" in method_normalised:
        cn = float(np.clip(curve_number, 30.0, 100.0))
        storage = 25400.0 / cn - 254.0
        initial_abstraction = 0.2 * storage
        if p <= initial_abstraction:
            return 0.0
        return float(np.clip((p - initial_abstraction) ** 2 / (p + 0.8 * storage), 0.0, p))
    raise ValueError(f"Unknown runoff method: {method}")


def water_stress_coefficient(depletion_mm: float, taw_mm: float, raw_mm: float) -> float:
    taw = max(float(taw_mm), 1e-9)
    raw = float(np.clip(raw_mm, 0.0, taw))
    depletion = float(np.clip(depletion_mm, 0.0, taw))
    if depletion <= raw:
        return 1.0
    denominator = max(taw - raw, 1e-9)
    return float(np.clip((taw - depletion) / denominator, 0.0, 1.0))


def _uploaded_irrigation_lookup(schedule: pd.DataFrame | None) -> dict[pd.Timestamp, float]:
    if schedule is None or schedule.empty:
        return {}
    if not {"Date", "Gross irrigation (mm)"}.issubset(schedule.columns):
        raise ValueError("Uploaded irrigation schedule must contain Date and Gross irrigation (mm).")
    frame = schedule.copy()
    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce").dt.normalize()
    frame["Gross irrigation (mm)"] = pd.to_numeric(frame["Gross irrigation (mm)"], errors="coerce")
    frame = frame.dropna(subset=["Date", "Gross irrigation (mm)"])
    return frame.groupby("Date")["Gross irrigation (mm)"].sum().clip(lower=0).to_dict()


def _sensor_irrigation_lookup(readings: pd.DataFrame | None) -> pd.DataFrame:
    """Normalise timestamped sensor readings to one last valid reading per day."""
    if readings is None or readings.empty:
        return pd.DataFrame(columns=["Date", "Sensor reading"])
    frame = readings.copy()
    date_col = next((column for column in ["Date", "DATE", "timestamp", "Timestamp"] if column in frame.columns), None)
    value_col = next((column for column in ["Sensor reading", "Value", "value", "Reading"] if column in frame.columns), None)
    if date_col is None or value_col is None:
        raise ValueError("Sensor irrigation data must contain a timestamp/date column and a numeric value column.")
    frame["_timestamp"] = pd.to_datetime(frame[date_col], errors="coerce", utc=True)
    frame["Sensor reading"] = pd.to_numeric(frame[value_col], errors="coerce")
    frame = frame.dropna(subset=["_timestamp", "Sensor reading"]).sort_values("_timestamp")
    if frame.empty:
        return pd.DataFrame(columns=["Date", "Sensor reading"])
    frame["Date"] = frame["_timestamp"].dt.tz_convert(None).dt.normalize()
    return frame.groupby("Date", as_index=False).tail(1)[["Date", "_timestamp", "Sensor reading"]].reset_index(drop=True)


def _sensor_triggered(metric: str, value: float, threshold: float) -> bool:
    if not np.isfinite(value):
        return False
    if str(metric) == "Soil water tension (kPa)":
        return float(value) >= float(threshold)
    return float(value) <= float(threshold)


def simulate_root_zone_balance(
    daily_drivers: pd.DataFrame,
    soil: SoilProfile,
    irrigation: IrrigationStrategy,
    *,
    initial_depletion_fraction: float = 0.20,
    runoff_method: str = "None",
    runoff_fraction: float = 0.0,
    curve_number: float = 75.0,
    capillary_rise_mm_day: float = 0.0,
    adjust_p_for_etc: bool = True,
    uploaded_irrigation_schedule: pd.DataFrame | None = None,
    sensor_irrigation_readings: pd.DataFrame | None = None,
    use_stress_adjusted_etc: bool = True,
) -> pd.DataFrame:
    soil = soil.validated()
    irrigation = irrigation.validated()
    frame = daily_drivers.copy().reset_index(drop=True)
    required = {"DATE", "Precipitation (mm)", "ETo (mm)", "Kc", "p base", "Root depth (m)", "Stage"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise SoilWaterBalanceError(f"Daily drivers are missing: {', '.join(missing)}")
    if frame.empty:
        raise SoilWaterBalanceError("No daily crop-season records were supplied.")

    initial_fraction = float(np.clip(initial_depletion_fraction, 0.0, 1.0))
    uploaded_lookup = _uploaded_irrigation_lookup(uploaded_irrigation_schedule)
    sensor_lookup = _sensor_irrigation_lookup(sensor_irrigation_readings)
    records: list[dict[str, Any]] = []
    previous_depletion: float | None = None
    previous_taw: float | None = None
    days_since_start = 0

    for _, row in frame.iterrows():
        current_date = pd.Timestamp(row["DATE"]).normalize()
        root_depth = max(0.05, float(row["Root depth (m)"]))
        taw = soil.awc_mm_per_m * root_depth
        if previous_depletion is None or previous_taw is None or previous_taw <= 0:
            dr_start = initial_fraction * taw
        else:
            # Newly explored soil is assumed to have the same relative depletion
            # as the previously explored root zone.
            dr_start = np.clip(previous_depletion / previous_taw * taw, 0.0, taw)

        eto = max(0.0, float(pd.to_numeric(row["ETo (mm)"], errors="coerce")))
        kc = max(0.0, float(pd.to_numeric(row["Kc"], errors="coerce")))
        etc_potential = eto * kc
        p_base = float(pd.to_numeric(row["p base"], errors="coerce"))
        if not np.isfinite(p_base):
            p_base = 0.5
        p_adjusted = p_base + 0.04 * (5.0 - etc_potential) if adjust_p_for_etc else p_base
        p_adjusted = float(np.clip(p_adjusted, 0.1, 0.8))
        raw = p_adjusted * taw

        precipitation = max(0.0, float(pd.to_numeric(row["Precipitation (mm)"], errors="coerce")))
        runoff = calculate_runoff_mm(precipitation, runoff_method, fixed_fraction=runoff_fraction, curve_number=curve_number)
        effective_rain = max(0.0, precipitation - runoff)
        capillary_rise = max(0.0, float(capillary_rise_mm_day))

        # Rain and capillary rise are considered before deciding whether an
        # irrigation is needed. Irrigation is applied before daily ET.
        dr_after_natural_inputs = max(0.0, dr_start - effective_rain - capillary_rise)
        forecast_ks = water_stress_coefficient(dr_after_natural_inputs, taw, raw)
        forecast_etc_actual = forecast_ks * etc_potential if use_stress_adjusted_etc else etc_potential
        forecast_end_depletion = min(taw, dr_after_natural_inputs + forecast_etc_actual)

        gross_irrigation = 0.0
        sensor_reading = np.nan
        sensor_reading_date = pd.NaT
        sensor_trigger = False
        sensor_data_status = "Not used"
        mode = irrigation.mode
        if mode == "Uploaded schedule":
            gross_irrigation = float(uploaded_lookup.get(current_date, 0.0))
        elif mode == "Sensor-triggered":
            if sensor_lookup.empty:
                sensor_data_status = "No sensor readings"
            else:
                eligible = sensor_lookup.loc[sensor_lookup["Date"].le(current_date)].copy()
                if eligible.empty:
                    sensor_data_status = "No reading on or before date"
                else:
                    latest_sensor = eligible.iloc[-1]
                    sensor_reading = float(latest_sensor["Sensor reading"])
                    sensor_reading_date = pd.Timestamp(latest_sensor["Date"]).normalize()
                    age_days = int((current_date - sensor_reading_date).days)
                    if age_days > int(irrigation.sensor_max_age_days):
                        sensor_data_status = f"Stale ({age_days} d)"
                    else:
                        sensor_data_status = "Fresh" if age_days == 0 else f"Carried forward {age_days} d"
                        sensor_trigger = _sensor_triggered(irrigation.sensor_metric, sensor_reading, irrigation.sensor_trigger_threshold)
                        if sensor_trigger:
                            gross_irrigation = float(irrigation.fixed_gross_application_mm)
        elif mode == "Fixed interval":
            if days_since_start % int(irrigation.fixed_interval_days) == 0:
                gross_irrigation = float(irrigation.fixed_gross_application_mm)
        elif mode in {"Irrigate at RAW", "Deficit irrigation"}:
            trigger = float(irrigation.trigger_fraction_of_raw) * raw
            if forecast_end_depletion >= trigger:
                desired_net = dr_after_natural_inputs * float(irrigation.refill_fraction)
                gross_irrigation = desired_net / float(irrigation.application_efficiency)

        gross_irrigation = min(max(0.0, gross_irrigation), float(irrigation.maximum_gross_application_mm))
        net_irrigation = gross_irrigation * float(irrigation.application_efficiency)
        application_loss = gross_irrigation - net_irrigation

        dr_before_et_unbounded = dr_start - effective_rain - net_irrigation - capillary_rise
        deep_percolation_before_et = max(0.0, -dr_before_et_unbounded)
        dr_before_et = max(0.0, dr_before_et_unbounded)
        ks = water_stress_coefficient(dr_before_et, taw, raw)
        etc_actual = ks * etc_potential if use_stress_adjusted_etc else etc_potential
        dr_end_unbounded = dr_before_et + etc_actual
        dr_end = float(np.clip(dr_end_unbounded, 0.0, taw))
        deep_percolation = deep_percolation_before_et + max(0.0, -dr_end_unbounded)
        unmet_et = max(0.0, etc_potential - etc_actual)

        records.append(
            {
                "Date": current_date,
                "Stage": row["Stage"],
                "Kc": kc,
                "Ky": pd.to_numeric(row.get("Ky"), errors="coerce"),
                "p base": p_base,
                "p adjusted": p_adjusted,
                "Root depth (m)": root_depth,
                "Field capacity (m³ m⁻³)": soil.theta_fc,
                "Wilting point (m³ m⁻³)": soil.theta_wp,
                "AWC (mm m⁻¹)": soil.awc_mm_per_m,
                "TAW (mm)": taw,
                "RAW (mm)": raw,
                "Depletion start (mm)": dr_start,
                "Precipitation (mm)": precipitation,
                "Runoff (mm)": runoff,
                "Effective rainfall (mm)": effective_rain,
                "Gross irrigation (mm)": gross_irrigation,
                "Net irrigation (mm)": net_irrigation,
                "Application loss (mm)": application_loss,
                "Capillary rise (mm)": capillary_rise,
                "ETo (mm)": eto,
                "Potential ETc (mm)": etc_potential,
                "Ks": ks,
                "Actual ETc (mm)": etc_actual,
                "Unmet ETc (mm)": unmet_et,
                "Deep percolation (mm)": deep_percolation,
                "Depletion end (mm)": dr_end,
                "Relative depletion": dr_end / taw if taw > 0 else np.nan,
                "Stress day": ks < 0.999,
                "Severe stress day": ks < 0.50,
                "Irrigation event": gross_irrigation > 0,
                "Irrigation strategy": mode,
                "Sensor metric": irrigation.sensor_metric if mode == "Sensor-triggered" else None,
                "Sensor reading": sensor_reading,
                "Sensor reading date": sensor_reading_date,
                "Sensor trigger threshold": irrigation.sensor_trigger_threshold if mode == "Sensor-triggered" else np.nan,
                "Sensor trigger met": bool(sensor_trigger),
                "Sensor data status": sensor_data_status,
                "Stage evidence grade": row.get("Stage evidence grade"),
                "Stage source IDs": row.get("Stage source IDs"),
            }
        )
        previous_depletion = dr_end
        previous_taw = taw
        days_since_start += 1

    result = pd.DataFrame(records)
    result["Cumulative precipitation (mm)"] = result["Precipitation (mm)"].cumsum()
    result["Cumulative effective rainfall (mm)"] = result["Effective rainfall (mm)"].cumsum()
    result["Cumulative gross irrigation (mm)"] = result["Gross irrigation (mm)"].cumsum()
    result["Cumulative actual ETc (mm)"] = result["Actual ETc (mm)"].cumsum()
    result["Cumulative potential ETc (mm)"] = result["Potential ETc (mm)"].cumsum()
    return result


def _relative_yield_factor(ky: float | None, eta: float, etm: float) -> float | None:
    if ky is None or not np.isfinite(ky) or etm <= 0:
        return None
    ratio = float(np.clip(eta / etm, 0.0, 1.0))
    return float(np.clip(1.0 - float(ky) * (1.0 - ratio), 0.0, 1.0))


def summarise_by_stage(balance: pd.DataFrame) -> pd.DataFrame:
    if balance is None or balance.empty:
        return pd.DataFrame()
    records: list[dict[str, Any]] = []
    for stage, group in balance.groupby("Stage", sort=False):
        potential = float(group["Potential ETc (mm)"].sum())
        actual = float(group["Actual ETc (mm)"].sum())
        ky_values = pd.to_numeric(group["Ky"], errors="coerce").dropna()
        ky = float(ky_values.iloc[0]) if not ky_values.empty else None
        yield_factor = _relative_yield_factor(ky, actual, potential)
        records.append(
            {
                "Stage": stage,
                "Start date": group["Date"].min(),
                "End date": group["Date"].max(),
                "Days": int(len(group)),
                "Mean Kc": float(group["Kc"].mean()),
                "Mean p": float(group["p adjusted"].mean()),
                "Mean TAW (mm)": float(group["TAW (mm)"].mean()),
                "Mean RAW (mm)": float(group["RAW (mm)"].mean()),
                "Precipitation (mm)": float(group["Precipitation (mm)"].sum()),
                "Effective rainfall (mm)": float(group["Effective rainfall (mm)"].sum()),
                "Gross irrigation (mm)": float(group["Gross irrigation (mm)"].sum()),
                "Potential ETc (mm)": potential,
                "Actual ETc (mm)": actual,
                "ET satisfaction (%)": 100.0 * actual / potential if potential > 0 else np.nan,
                "Stress days": int(group["Stress day"].sum()),
                "Severe stress days": int(group["Severe stress day"].sum()),
                "Minimum Ks": float(group["Ks"].min()),
                "Maximum depletion (mm)": float(group["Depletion end (mm)"].max()),
                "Deep percolation (mm)": float(group["Deep percolation (mm)"].sum()),
                "Ky": ky,
                "Relative yield factor": yield_factor,
                "Evidence grade": ", ".join(sorted(set(str(v) for v in group["Stage evidence grade"].dropna()))),
                "Source IDs": ", ".join(sorted(set(str(v) for v in group["Stage source IDs"].dropna() if str(v)))),
            }
        )
    return pd.DataFrame(records)


def summarise_season(balance: pd.DataFrame, *, seasonal_ky: float | None = None) -> dict[str, Any]:
    if balance is None or balance.empty:
        return {}
    potential = float(balance["Potential ETc (mm)"].sum())
    actual = float(balance["Actual ETc (mm)"].sum())
    first_stress = balance.loc[balance["Stress day"], "Date"]
    relative_yield = _relative_yield_factor(seasonal_ky, actual, potential)
    return {
        "Start date": balance["Date"].min(),
        "End date": balance["Date"].max(),
        "Season days": int(len(balance)),
        "Precipitation (mm)": float(balance["Precipitation (mm)"].sum()),
        "Effective rainfall (mm)": float(balance["Effective rainfall (mm)"].sum()),
        "Runoff (mm)": float(balance["Runoff (mm)"].sum()),
        "Gross irrigation (mm)": float(balance["Gross irrigation (mm)"].sum()),
        "Net irrigation (mm)": float(balance["Net irrigation (mm)"].sum()),
        "Irrigation events": int(balance["Irrigation event"].sum()),
        "Potential ETc (mm)": potential,
        "Actual ETc (mm)": actual,
        "ET satisfaction (%)": 100.0 * actual / potential if potential > 0 else np.nan,
        "Unmet ETc (mm)": float(balance["Unmet ETc (mm)"].sum()),
        "Stress days": int(balance["Stress day"].sum()),
        "Severe stress days": int(balance["Severe stress day"].sum()),
        "Stress-day percentage": 100.0 * float(balance["Stress day"].mean()),
        "First stress date": first_stress.iloc[0] if not first_stress.empty else pd.NaT,
        "Minimum Ks": float(balance["Ks"].min()),
        "Maximum depletion (mm)": float(balance["Depletion end (mm)"].max()),
        "Maximum relative depletion (%)": 100.0 * float(balance["Relative depletion"].max()),
        "Deep percolation (mm)": float(balance["Deep percolation (mm)"].sum()),
        "End depletion (mm)": float(balance["Depletion end (mm)"].iloc[-1]),
        "Seasonal Ky": seasonal_ky,
        "Relative yield factor": relative_yield,
    }


def simulate_historical_seasons(
    weather: pd.DataFrame,
    library: Mapping[str, Any],
    crop: str,
    profile: str,
    *,
    latitude: float,
    planting_month: int,
    planting_day: int,
    start_year: int,
    end_year: int,
    duration_strategy: str,
    custom_season_days: int,
    constant_kc: float | None,
    soil: SoilProfile,
    irrigation: IrrigationStrategy,
    initial_root_depth_m: float,
    maximum_root_depth_m: float,
    fallback_p: float,
    dynamic_root_growth: bool,
    initial_depletion_fraction: float,
    runoff_method: str,
    runoff_fraction: float,
    curve_number: float,
    capillary_rise_mm_day: float,
    adjust_p_for_etc: bool,
    minimum_completeness_percent: float = 90.0,
) -> pd.DataFrame:
    prepared_all = prepare_daily_weather(weather, latitude)
    records: list[dict[str, Any]] = []
    seasonal_ky = whole_season_ky(library, crop, profile)
    for year in range(int(start_year), int(end_year) + 1):
        try:
            planting = pd.Timestamp(date(year, int(planting_month), int(planting_day)))
        except ValueError:
            planting = pd.Timestamp(date(year, int(planting_month), 28))
        schedule = build_stage_schedule(
            library,
            crop,
            profile,
            planting,
            duration_strategy=duration_strategy,
            custom_season_days=custom_season_days,
            constant_kc=constant_kc,
            constant_p=fallback_p,
        )
        season_end = pd.Timestamp(schedule["End date"].max())
        subset = prepared_all.loc[prepared_all["DATE"].between(planting, season_end)].copy()
        expected_days = int((season_end - planting).days + 1)
        completeness = 100.0 * len(subset) / expected_days if expected_days else 0.0
        if completeness < float(minimum_completeness_percent):
            records.append({"Season year": year, "Status": "Incomplete", "Completeness (%)": completeness})
            continue
        drivers = assign_stage_parameters(
            subset,
            schedule,
            fallback_p=fallback_p,
            initial_root_depth_m=initial_root_depth_m,
            maximum_root_depth_m=maximum_root_depth_m,
            dynamic_root_growth=dynamic_root_growth,
        )
        balance = simulate_root_zone_balance(
            drivers,
            soil,
            irrigation,
            initial_depletion_fraction=initial_depletion_fraction,
            runoff_method=runoff_method,
            runoff_fraction=runoff_fraction,
            curve_number=curve_number,
            capillary_rise_mm_day=capillary_rise_mm_day,
            adjust_p_for_etc=adjust_p_for_etc,
        )
        summary = summarise_season(balance, seasonal_ky=seasonal_ky)
        summary.update({"Season year": year, "Status": "Complete", "Completeness (%)": completeness})
        records.append(summary)
    return pd.DataFrame(records)


def historical_percentile_table(summary: pd.DataFrame, target_year: int) -> pd.DataFrame:
    if summary is None or summary.empty:
        return pd.DataFrame()
    eligible = summary.loc[summary["Status"].eq("Complete")].copy()
    target = eligible.loc[eligible["Season year"].eq(int(target_year))]
    if target.empty:
        return pd.DataFrame()
    metrics = [
        "Precipitation (mm)",
        "Gross irrigation (mm)",
        "Potential ETc (mm)",
        "ET satisfaction (%)",
        "Stress days",
        "Severe stress days",
        "Maximum depletion (mm)",
        "Deep percolation (mm)",
        "Relative yield factor",
    ]
    records: list[dict[str, Any]] = []
    for metric in metrics:
        if metric not in eligible:
            continue
        values = pd.to_numeric(eligible[metric], errors="coerce").dropna()
        target_value = pd.to_numeric(target.iloc[0][metric], errors="coerce")
        if values.empty or pd.isna(target_value):
            continue
        percentile = 100.0 * (float((values < target_value).sum()) + 0.5 * float((values == target_value).sum())) / len(values)
        records.append(
            {
                "Metric": metric,
                "Target value": float(target_value),
                "Historical median": float(values.median()),
                "Historical 10th percentile": float(values.quantile(0.10)),
                "Historical 90th percentile": float(values.quantile(0.90)),
                "Target percentile": float(percentile),
                "Eligible seasons": int(len(values)),
            }
        )
    return pd.DataFrame(records)


def compare_balance_scenarios(scenarios: Mapping[str, pd.DataFrame], *, seasonal_ky: float | None = None) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for name, balance in scenarios.items():
        row = summarise_season(balance, seasonal_ky=seasonal_ky)
        row["Scenario"] = str(name)
        records.append(row)
    result = pd.DataFrame(records)
    if not result.empty and "Scenario" in result:
        result = result[["Scenario"] + [column for column in result.columns if column != "Scenario"]]
    return result


def module_metadata(
    *,
    crop: str,
    profile: str,
    soil: SoilProfile,
    irrigation: IrrigationStrategy,
    settings: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "module_version": MODULE_VERSION,
        "method": "FAO-56 single crop coefficient root-zone balance",
        "method_url": FAO56_ROOT_ZONE_URL,
        "crop": crop,
        "crop_profile": profile,
        "soil": asdict(soil),
        "soil_awc_mm_per_m": soil.awc_mm_per_m,
        "irrigation": asdict(irrigation),
        "settings": dict(settings),
        "limitations": [
            "Single-layer bucket model with uniform root-zone water content.",
            "No groundwater capillary rise unless entered explicitly.",
            "No salinity, waterlogging, layered-soil or hydraulic-conductivity simulation.",
            "NASA POWER values represent a grid cell rather than a field weather station.",
            "Generic soil presets are screening values; measured field capacity and wilting point are preferred.",
        ],
    }
