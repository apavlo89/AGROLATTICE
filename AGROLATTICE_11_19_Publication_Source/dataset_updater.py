"""Resumable NASA POWER updater for the AgroLattice Research Tool.

Version 7.4 adds country-aware and installation-keyword compatibility while retaining
Version 7.3 candidate validation, so pre-existing historical anomalies are
reported as warnings rather than incorrectly blocking a clean incremental update.

The module is deliberately independent of Streamlit. It updates the canonical
long-format climate dataset used by the app and can also generate mixed-format
exports. Requests are made through the existing daily-weather client, cached on
disk, aggregated to calendar months, validated, checkpointed, and merged only
when the user explicitly finalises and installs a candidate dataset.
"""

from __future__ import annotations

import calendar
import hashlib
import json
import math
import os
import shutil
import time
import zipfile
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from daily_weather_phenology import DailyWeatherError, fetch_nasa_power_daily


NASA_POWER_DAILY_DOCS = "https://power.larc.nasa.gov/docs/services/api/temporal/daily/"
NASA_POWER_PARAMETER_DOCS = "https://power.larc.nasa.gov/parameters/"

CORE_POWER_PARAMETERS: tuple[str, ...] = (
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "RH2M",
    "PRECTOTCORR",
    "WS2M",
    "ALLSKY_SFC_SW_DWN",
    "ALLSKY_SFC_LW_DWN",
    "PS",
    "ALLSKY_KT",
    "TSOIL1",
    "TSOIL2",
)

LEGACY_OPTIONAL_PARAMETERS: tuple[str, ...] = (
    "EVLAND",
    "CLOUD_AMT_DAY",
    "EVPTRNS",
)

POWER_TO_APP_VARIABLE: dict[str, str] = {
    "T2M": "TEMPERATURE",
    "T2M_MAX": "TEMPERATURE_MAX",
    "T2M_MIN": "TEMPERATURE_MIN",
    "RH2M": "RELATIVE_HUMIDITY",
    "WS2M": "WIND_SPEED",
    "ALLSKY_SFC_SW_DWN": "SOLAR_RADIATION",
    "ALLSKY_SFC_LW_DWN": "LONGWAVE_RADIATION",
    "PS": "SURFACE_PRESSURE",
    "ALLSKY_KT": "CLEARNESS_INDEX",
    "TSOIL1": "SOIL_TEMP_LAYER1",
    "TSOIL2": "SOIL_TEMP_LAYER2",
    "EVLAND": "EVAPORATION_LAND",
    "CLOUD_AMT_DAY": "CLOUD_AMOUNT_DAY",
    "EVPTRNS": "EVAPOTRANSPIRATION_ENERGY_FLUX",
}

CANONICAL_COLUMNS: tuple[str, ...] = (
    "CITY",
    "STATE",
    "Year",
    "Month",
    "Variable",
    "Value",
)

MONTHS_UPPER: tuple[str, ...] = tuple(calendar.month_name[index].upper() for index in range(1, 13))
MONTH_NUMBER: dict[str, int] = {name: index for index, name in enumerate(MONTHS_UPPER, start=1)}

VALUE_RANGES: dict[str, tuple[float | None, float | None]] = {
    "TEMPERATURE": (-90.0, 65.0),
    "TEMPERATURE_MAX": (-90.0, 70.0),
    "TEMPERATURE_MIN": (-100.0, 60.0),
    "RELATIVE_HUMIDITY": (0.0, 100.0),
    "PRECIPITATION_AVG": (0.0, 500.0),
    "PRECIPITATION_MIN": (0.0, 500.0),
    "PRECIPITATION_MAX": (0.0, 1000.0),
    "WIND_SPEED": (0.0, 100.0),
    "SOLAR_RADIATION": (0.0, 45.0),
    "LONGWAVE_RADIATION": (0.0, 60.0),
    "SURFACE_PRESSURE": (40.0, 110.0),
    "CLEARNESS_INDEX": (0.0, 1.5),
    "SOIL_TEMP_LAYER1": (-80.0, 80.0),
    "SOIL_TEMP_LAYER2": (-80.0, 80.0),
    "EVAPOTRANSPIRATION": (0.0, 30.0),
    "EVAPORATION_LAND": (0.0, 100.0),
    "CLOUD_AMOUNT_DAY": (0.0, 100.0),
}


class DatasetUpdateError(RuntimeError):
    """Raised when an update job cannot be safely completed."""


@dataclass(frozen=True)
class UpdateConfiguration:
    start_date: str
    end_date: str
    parameters: tuple[str, ...]
    minimum_monthly_coverage_percent: float
    include_partial_final_month: bool
    merge_mode: str
    grid_deduplication: bool
    request_delay_seconds: float
    source_dataset: str
    source_dataset_sha256: str
    location_count: int
    grid_count: int
    target_country: str = "Mexico"


@dataclass
class BatchResult:
    attempted_grids: int
    completed_grids: int
    failed_grids: int
    rows_written: int
    completed_total: int
    remaining_total: int
    failures: list[dict]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _replace_file_with_retries(
    temporary: str | Path,
    target: str | Path,
    *,
    attempts: int = 8,
    initial_delay_seconds: float = 0.15,
) -> Path:
    """Replace a file safely, retrying transient Windows/OneDrive locks."""
    temporary_path = Path(temporary)
    target_path = Path(target)
    last_error: Exception | None = None

    for attempt in range(max(1, int(attempts))):
        try:
            os.replace(temporary_path, target_path)
            return target_path
        except (PermissionError, OSError) as error:
            last_error = error
            if attempt >= attempts - 1:
                break
            time.sleep(initial_delay_seconds * (attempt + 1))

    raise DatasetUpdateError(
        f"Could not replace {target_path.name} after {attempts} attempts. "
        "Close programs using the file or pause OneDrive synchronisation, then retry. "
        f"Original error: {last_error}"
    )


def _unique_temporary_path(target: Path, label: str = "tmp") -> Path:
    token = f"{os.getpid()}_{time.time_ns()}"
    return target.with_name(f"{target.name}.{token}.{label}")


def atomic_write_text(path: str | Path, text: str) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = _unique_temporary_path(target, "tmp")
    try:
        temporary.write_text(text, encoding="utf-8")
        return _replace_file_with_retries(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_write_csv(frame: pd.DataFrame, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = _unique_temporary_path(target, "tmp")
    try:
        frame.to_csv(temporary, index=False)
        return _replace_file_with_retries(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def clean_long_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    missing = set(CANONICAL_COLUMNS).difference(frame.columns)
    if missing:
        raise DatasetUpdateError(f"Climate dataset is missing required columns: {sorted(missing)}")
    cleaned = frame.loc[:, list(CANONICAL_COLUMNS)].copy()
    cleaned["CITY"] = cleaned["CITY"].astype(str).str.strip()
    cleaned["STATE"] = cleaned["STATE"].astype(str).str.strip()
    cleaned["Month"] = cleaned["Month"].astype(str).str.upper().str.strip()
    cleaned["Variable"] = cleaned["Variable"].astype(str).str.upper().str.strip()
    cleaned["Year"] = pd.to_numeric(cleaned["Year"], errors="coerce")
    cleaned["Value"] = pd.to_numeric(cleaned["Value"], errors="coerce")
    cleaned = cleaned.dropna(subset=list(CANONICAL_COLUMNS))
    cleaned["Year"] = cleaned["Year"].astype(int)
    cleaned = cleaned[cleaned["Month"].isin(MONTHS_UPPER)]
    return cleaned.reset_index(drop=True)


def latest_dataset_month(frame: pd.DataFrame) -> date | None:
    if frame.empty:
        return None
    years = pd.to_numeric(frame["Year"], errors="coerce")
    months = frame["Month"].astype(str).str.upper().map(MONTH_NUMBER)
    valid = pd.DataFrame({"year": years, "month": months}).dropna()
    if valid.empty:
        return None
    latest = valid.sort_values(["year", "month"]).iloc[-1]
    year = int(latest["year"])
    month = int(latest["month"])
    return date(year, month, calendar.monthrange(year, month)[1])


def month_start_after(value: date | None) -> date:
    if value is None:
        return date(1981, 1, 1)
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def last_complete_month_end(reference_date: date | None = None, lag_days: int = 7) -> date:
    reference = reference_date or date.today()
    safe_date = reference - timedelta(days=max(0, int(lag_days)))
    first_of_month = safe_date.replace(day=1)
    return first_of_month - timedelta(days=1)


def normalise_locations(
    climate_frame: pd.DataFrame,
    cities_frame: pd.DataFrame,
    *,
    scope: str = "existing",
    selected_states: Sequence[str] | None = None,
    selected_locations: Sequence[str] | None = None,
    country: str = "Mexico",
) -> pd.DataFrame:
    required = {"country", "city_ascii", "lat", "lng", "admin_name"}
    missing = required.difference(cities_frame.columns)
    if missing:
        raise DatasetUpdateError(f"worldcities.csv is missing columns: {sorted(missing)}")

    cities = (
        cities_frame.loc[
            cities_frame["country"].astype(str).str.casefold().eq(str(country).casefold()),
            ["city_ascii", "admin_name", "lat", "lng"],
        ]
        .rename(columns={"city_ascii": "CITY", "admin_name": "STATE"})
        .dropna(subset=["CITY", "lat", "lng"])
        .assign(
            CITY=lambda x: x["CITY"].astype(str).str.strip(),
            STATE=lambda x: x["STATE"].fillna(str(country)).astype(str).str.strip().replace("", str(country)),
            lat=lambda x: pd.to_numeric(x["lat"], errors="coerce"),
            lng=lambda x: pd.to_numeric(x["lng"], errors="coerce"),
        )
        .dropna(subset=["lat", "lng"])
        .drop_duplicates(["CITY", "STATE"], keep="first")
    )

    scope_key = str(scope).strip().casefold()
    if scope_key in {"all_country", "all_mexico"}:
        locations = cities.copy()
    else:
        existing = climate_frame[["CITY", "STATE"]].drop_duplicates()
        locations = existing.merge(cities, on=["CITY", "STATE"], how="inner", validate="one_to_one")

    if selected_states:
        state_set = {str(value).strip() for value in selected_states}
        locations = locations[locations["STATE"].isin(state_set)]

    locations["Location"] = locations["CITY"] + " (" + locations["STATE"] + ")"
    if selected_locations:
        selected_set = {str(value) for value in selected_locations}
        locations = locations[locations["Location"].isin(selected_set)]

    return locations.sort_values(["STATE", "CITY"]).reset_index(drop=True)


def _nearest_grid_coordinate(value: float, step: float) -> float:
    return round(float(value) / float(step)) * float(step)


def add_power_grid_keys(
    locations: pd.DataFrame,
    *,
    deduplicate: bool = True,
    meteorology_lat_step: float = 0.5,
    meteorology_lon_step: float = 0.625,
) -> pd.DataFrame:
    result = locations.copy()
    if deduplicate:
        result["REQUEST_LAT"] = result["lat"].map(lambda value: _nearest_grid_coordinate(value, meteorology_lat_step))
        result["REQUEST_LON"] = result["lng"].map(lambda value: _nearest_grid_coordinate(value, meteorology_lon_step))
        result["GRID_KEY"] = result.apply(
            lambda row: f"{float(row['REQUEST_LAT']):+.3f}_{float(row['REQUEST_LON']):+.3f}", axis=1
        )
    else:
        result["REQUEST_LAT"] = result["lat"].astype(float)
        result["REQUEST_LON"] = result["lng"].astype(float)
        result["GRID_KEY"] = result.apply(
            lambda row: f"{row['CITY']}|{row['STATE']}|{float(row['lat']):.5f}|{float(row['lng']):.5f}", axis=1
        )
    return result


def build_grid_plan(locations: pd.DataFrame) -> pd.DataFrame:
    required = {"GRID_KEY", "REQUEST_LAT", "REQUEST_LON", "CITY", "STATE", "lat", "lng"}
    missing = required.difference(locations.columns)
    if missing:
        raise DatasetUpdateError(f"Location plan is missing fields: {sorted(missing)}")
    rows: list[dict] = []
    for grid_key, group in locations.groupby("GRID_KEY", sort=True):
        rows.append(
            {
                "GRID_KEY": str(grid_key),
                "REQUEST_LAT": float(group["REQUEST_LAT"].iloc[0]),
                "REQUEST_LON": float(group["REQUEST_LON"].iloc[0]),
                "LOCATION_COUNT": int(len(group)),
                "Locations": group[["CITY", "STATE", "lat", "lng"]].to_dict("records"),
            }
        )
    return pd.DataFrame(rows).sort_values("GRID_KEY").reset_index(drop=True)


def configuration_fingerprint(configuration: UpdateConfiguration) -> str:
    payload = json.dumps(asdict(configuration), sort_keys=True, separators=(",", ":"), default=list)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def estimate_elevation_from_pressure_kpa(pressure_kpa: pd.Series | np.ndarray) -> np.ndarray:
    pressure = np.asarray(pressure_kpa, dtype=float)
    pressure = np.clip(pressure, 20.0, 110.0)
    return 44330.0 * (1.0 - np.power(pressure / 101.3, 0.1903))


def calculate_fao56_eto_daily(frame: pd.DataFrame, latitude: float) -> pd.Series:
    """Calculate FAO-56 reference evapotranspiration from POWER daily inputs.

    The calculation uses mean relative humidity because POWER RH2M is a daily
    mean. Soil heat flux is set to zero at the daily time step, as commonly
    applied in the FAO-56 daily formulation.
    """
    required = {
        "T2M",
        "T2M_MAX",
        "T2M_MIN",
        "RH2M",
        "WS2M",
        "ALLSKY_SFC_SW_DWN",
        "PS",
    }
    missing = required.difference(frame.columns)
    if missing:
        return pd.Series(np.nan, index=frame.index, name="ETO_FAO56")

    tmean = pd.to_numeric(frame["T2M"], errors="coerce").to_numpy(float)
    tmax = pd.to_numeric(frame["T2M_MAX"], errors="coerce").to_numpy(float)
    tmin = pd.to_numeric(frame["T2M_MIN"], errors="coerce").to_numpy(float)
    rh = np.clip(pd.to_numeric(frame["RH2M"], errors="coerce").to_numpy(float), 0.0, 100.0)
    wind = np.maximum(pd.to_numeric(frame["WS2M"], errors="coerce").to_numpy(float), 0.0)
    rs_mj = np.maximum(pd.to_numeric(frame["ALLSKY_SFC_SW_DWN"], errors="coerce").to_numpy(float), 0.0)
    pressure = pd.to_numeric(frame["PS"], errors="coerce").to_numpy(float)

    es_tmax = 0.6108 * np.exp((17.27 * tmax) / (tmax + 237.3))
    es_tmin = 0.6108 * np.exp((17.27 * tmin) / (tmin + 237.3))
    es = (es_tmax + es_tmin) / 2.0
    ea = np.maximum(es * rh / 100.0, 0.0)
    delta = 4098.0 * (0.6108 * np.exp((17.27 * tmean) / (tmean + 237.3))) / np.power(tmean + 237.3, 2)
    gamma = 0.000665 * pressure

    rs = rs_mj  # NASA POWER AG daily radiation is already supplied as MJ m-2 day-1.
    latitude_radians = math.radians(float(latitude))
    day_of_year = pd.to_datetime(frame["DATE"]).dt.dayofyear.to_numpy(float)
    dr = 1.0 + 0.033 * np.cos((2.0 * np.pi / 365.0) * day_of_year)
    solar_declination = 0.409 * np.sin((2.0 * np.pi / 365.0) * day_of_year - 1.39)
    acos_argument = np.clip(-np.tan(latitude_radians) * np.tan(solar_declination), -1.0, 1.0)
    sunset_hour_angle = np.arccos(acos_argument)
    ra = (
        (24.0 * 60.0 / np.pi)
        * 0.0820
        * dr
        * (
            sunset_hour_angle * np.sin(latitude_radians) * np.sin(solar_declination)
            + np.cos(latitude_radians) * np.cos(solar_declination) * np.sin(sunset_hour_angle)
        )
    )

    elevation = estimate_elevation_from_pressure_kpa(pressure)
    rso = np.maximum((0.75 + 2e-5 * elevation) * ra, 1e-6)
    relative_solar = np.clip(rs / rso, 0.0, 1.0)
    rns = (1.0 - 0.23) * rs
    sigma = 4.903e-9
    rnl = (
        sigma
        * (np.power(tmax + 273.16, 4) + np.power(tmin + 273.16, 4))
        / 2.0
        * (0.34 - 0.14 * np.sqrt(np.maximum(ea, 0.0)))
        * (1.35 * relative_solar - 0.35)
    )
    rn = rns - rnl
    soil_heat_flux = 0.0

    numerator = (
        0.408 * delta * (rn - soil_heat_flux)
        + gamma * (900.0 / (tmean + 273.0)) * wind * np.maximum(es - ea, 0.0)
    )
    denominator = delta + gamma * (1.0 + 0.34 * wind)
    eto = np.divide(numerator, denominator, out=np.full_like(numerator, np.nan), where=denominator > 0)
    eto = np.where(np.isfinite(eto), np.maximum(eto, 0.0), np.nan)
    return pd.Series(eto, index=frame.index, name="ETO_FAO56")


def _coverage_sufficient(series: pd.Series, expected_days: int, threshold_percent: float) -> bool:
    if expected_days <= 0:
        return False
    available = int(pd.to_numeric(series, errors="coerce").notna().sum())
    return (100.0 * available / expected_days) >= float(threshold_percent)


def _month_expected_days(year: int, month: int, start_date: date, end_date: date) -> int:
    month_start = date(year, month, 1)
    month_end = date(year, month, calendar.monthrange(year, month)[1])
    effective_start = max(month_start, start_date)
    effective_end = min(month_end, end_date)
    if effective_start > effective_end:
        return 0
    return (effective_end - effective_start).days + 1


def aggregate_daily_to_monthly_long(
    daily_frame: pd.DataFrame,
    *,
    start_date: date,
    end_date: date,
    latitude: float,
    minimum_coverage_percent: float = 90.0,
    include_partial_final_month: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if "DATE" not in daily_frame.columns:
        raise DatasetUpdateError("Daily NASA data do not contain a DATE column.")
    daily = daily_frame.copy()
    daily["DATE"] = pd.to_datetime(daily["DATE"], errors="coerce")
    daily = daily.dropna(subset=["DATE"]).sort_values("DATE")
    daily = daily[(daily["DATE"].dt.date >= start_date) & (daily["DATE"].dt.date <= end_date)]
    if daily.empty:
        raise DatasetUpdateError("NASA POWER returned no daily observations in the requested interval.")

    daily["ETO_FAO56"] = calculate_fao56_eto_daily(daily, latitude)
    daily["Year"] = daily["DATE"].dt.year.astype(int)
    daily["MonthNumber"] = daily["DATE"].dt.month.astype(int)

    records: list[dict] = []
    audit_rows: list[dict] = []
    first_month_start = date(start_date.year, start_date.month, 1)
    first_month_is_partial = start_date.day > 1
    final_month_start = date(end_date.year, end_date.month, 1)
    final_month_is_partial = end_date.day < calendar.monthrange(end_date.year, end_date.month)[1]

    for (year, month_number), group in daily.groupby(["Year", "MonthNumber"], sort=True):
        year = int(year)
        month_number = int(month_number)
        month_start = date(year, month_number, 1)
        if not include_partial_final_month and (
            (first_month_is_partial and month_start == first_month_start)
            or (final_month_is_partial and month_start == final_month_start)
        ):
            continue
        expected_days = _month_expected_days(year, month_number, start_date, end_date)
        month_name = calendar.month_name[month_number].upper()

        aggregations: list[tuple[str, str, str]] = []
        for source, target in POWER_TO_APP_VARIABLE.items():
            if source in group.columns:
                aggregations.append((source, target, "mean"))
        if "PRECTOTCORR" in group.columns:
            aggregations.extend(
                [
                    ("PRECTOTCORR", "PRECIPITATION_AVG", "mean"),
                    ("PRECTOTCORR", "PRECIPITATION_MIN", "min"),
                    ("PRECTOTCORR", "PRECIPITATION_MAX", "max"),
                ]
            )
        if "ETO_FAO56" in group.columns:
            aggregations.append(("ETO_FAO56", "EVAPOTRANSPIRATION", "mean"))

        for source, target, method in aggregations:
            values = pd.to_numeric(group[source], errors="coerce")
            coverage_percent = 100.0 * values.notna().sum() / expected_days if expected_days else 0.0
            accepted = _coverage_sufficient(values, expected_days, minimum_coverage_percent)
            value = np.nan
            if accepted:
                if method == "min":
                    value = values.min(skipna=True)
                elif method == "max":
                    value = values.max(skipna=True)
                else:
                    value = values.mean(skipna=True)
            audit_rows.append(
                {
                    "Year": year,
                    "Month": month_name,
                    "SourceParameter": source,
                    "Variable": target,
                    "Aggregation": method,
                    "ExpectedDays": expected_days,
                    "AvailableDays": int(values.notna().sum()),
                    "CoveragePercent": float(coverage_percent),
                    "Accepted": bool(accepted and np.isfinite(value)),
                }
            )
            if accepted and np.isfinite(value):
                records.append(
                    {
                        "Year": year,
                        "Month": month_name,
                        "Variable": target,
                        "Value": float(value),
                    }
                )

    result = pd.DataFrame(records, columns=["Year", "Month", "Variable", "Value"])
    audit = pd.DataFrame(audit_rows)
    return result, audit


def replicate_monthly_for_locations(monthly: pd.DataFrame, locations: Sequence[Mapping]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for location in locations:
        block = monthly.copy()
        block.insert(0, "STATE", str(location["STATE"]).strip())
        block.insert(0, "CITY", str(location["CITY"]).strip())
        frames.append(block)
    if not frames:
        return pd.DataFrame(columns=list(CANONICAL_COLUMNS))
    return pd.concat(frames, ignore_index=True).loc[:, list(CANONICAL_COLUMNS)]


def validate_update_rows(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    cleaned = clean_long_dataset(frame)
    key_columns = ["CITY", "STATE", "Year", "Month", "Variable"]
    duplicate_mask = cleaned.duplicated(key_columns, keep=False)
    duplicate_rows = cleaned.loc[duplicate_mask].copy()

    issue_rows: list[dict] = []
    for variable, group in cleaned.groupby("Variable"):
        low, high = VALUE_RANGES.get(str(variable), (None, None))
        values = pd.to_numeric(group["Value"], errors="coerce")
        mask = pd.Series(False, index=group.index)
        if low is not None:
            mask |= values < low
        if high is not None:
            mask |= values > high
        for index in group.index[mask]:
            row = cleaned.loc[index]
            issue_rows.append(
                {
                    "CITY": row["CITY"],
                    "STATE": row["STATE"],
                    "Year": int(row["Year"]),
                    "Month": row["Month"],
                    "Variable": row["Variable"],
                    "Value": float(row["Value"]),
                    "Issue": f"Outside broad validation range {low} to {high}",
                }
            )

    issues = pd.DataFrame(issue_rows)
    return duplicate_rows, issues


def _append_csv(frame: pd.DataFrame, path: Path) -> None:
    if frame.empty:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, mode="a", header=not path.exists(), index=False)


def initialise_job(
    job_dir: str | Path,
    configuration: UpdateConfiguration,
    grid_plan: pd.DataFrame,
    *,
    reset: bool = False,
) -> dict:
    root = Path(job_dir)
    root.mkdir(parents=True, exist_ok=True)
    checkpoint_path = root / "checkpoint.json"
    staging_path = root / "staging_update_long.csv"
    audit_path = root / "monthly_coverage_audit.csv"
    log_path = root / "request_log.csv"
    plan_path = root / "grid_plan.json"

    fingerprint = configuration_fingerprint(configuration)
    if checkpoint_path.exists() and not reset:
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if checkpoint.get("configuration_fingerprint") != fingerprint:
            raise DatasetUpdateError(
                "An existing update job uses different settings. Reset the job before changing dates, locations, parameters, or merge mode."
            )
        return checkpoint

    if reset:
        for path in [checkpoint_path, staging_path, audit_path, log_path, plan_path]:
            path.unlink(missing_ok=True)

    plan_records = grid_plan.to_dict("records")
    atomic_write_text(plan_path, json.dumps(plan_records, ensure_ascii=False, indent=2))
    checkpoint = {
        "schema_version": 1,
        "created_utc": utc_now_iso(),
        "updated_utc": utc_now_iso(),
        "configuration": asdict(configuration),
        "configuration_fingerprint": fingerprint,
        "completed_grid_keys": [],
        "failed_attempts": {},
        "staging_rows": 0,
        "status": "ready",
    }
    atomic_write_text(checkpoint_path, json.dumps(checkpoint, ensure_ascii=False, indent=2))
    return checkpoint


def load_job(job_dir: str | Path) -> tuple[dict | None, pd.DataFrame | None]:
    root = Path(job_dir)
    checkpoint_path = root / "checkpoint.json"
    plan_path = root / "grid_plan.json"
    if not checkpoint_path.exists() or not plan_path.exists():
        return None, None
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    plan = pd.DataFrame(json.loads(plan_path.read_text(encoding="utf-8")))
    return checkpoint, plan


def run_job_batch(
    job_dir: str | Path,
    cache_dir: str | Path,
    *,
    batch_size: int = 10,
    force_refresh: bool = False,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> BatchResult:
    root = Path(job_dir)
    checkpoint, plan = load_job(root)
    if checkpoint is None or plan is None:
        raise DatasetUpdateError("No update job exists. Create a job before processing a batch.")

    configuration = checkpoint["configuration"]
    start_date = date.fromisoformat(configuration["start_date"])
    end_date = date.fromisoformat(configuration["end_date"])
    parameters = tuple(configuration["parameters"])
    coverage = float(configuration["minimum_monthly_coverage_percent"])
    include_partial = bool(configuration["include_partial_final_month"])
    completed = set(checkpoint.get("completed_grid_keys", []))
    pending = plan[~plan["GRID_KEY"].astype(str).isin(completed)].head(max(1, int(batch_size)))

    failures: list[dict] = []
    completed_now = 0
    rows_written = 0
    staging_path = root / "staging_update_long.csv"
    audit_path = root / "monthly_coverage_audit.csv"
    log_path = root / "request_log.csv"

    for position, (_, plan_row) in enumerate(pending.iterrows(), start=1):
        grid_key = str(plan_row["GRID_KEY"])
        current_rows_written = 0
        if progress_callback:
            progress_callback(position, len(pending), f"Downloading grid {grid_key}")
        requested_parameters = parameters
        fallback_used = False
        try:
            try:
                daily, metadata = fetch_nasa_power_daily(
                    latitude=float(plan_row["REQUEST_LAT"]),
                    longitude=float(plan_row["REQUEST_LON"]),
                    start_date=start_date,
                    end_date=end_date,
                    cache_dir=cache_dir,
                    parameters=requested_parameters,
                    time_standard="LST",
                    force_refresh=force_refresh,
                    years_per_chunk=2,
                    timeout_seconds=120,
                )
            except DailyWeatherError:
                optional_requested = set(requested_parameters).intersection(LEGACY_OPTIONAL_PARAMETERS)
                if not optional_requested:
                    raise
                fallback_used = True
                requested_parameters = tuple(parameter for parameter in requested_parameters if parameter not in optional_requested)
                daily, metadata = fetch_nasa_power_daily(
                    latitude=float(plan_row["REQUEST_LAT"]),
                    longitude=float(plan_row["REQUEST_LON"]),
                    start_date=start_date,
                    end_date=end_date,
                    cache_dir=cache_dir,
                    parameters=requested_parameters,
                    time_standard="LST",
                    force_refresh=force_refresh,
                    years_per_chunk=2,
                    timeout_seconds=120,
                )

            monthly, audit = aggregate_daily_to_monthly_long(
                daily,
                start_date=start_date,
                end_date=end_date,
                latitude=float(plan_row["REQUEST_LAT"]),
                minimum_coverage_percent=coverage,
                include_partial_final_month=include_partial,
            )
            locations = plan_row["Locations"]
            if isinstance(locations, str):
                locations = json.loads(locations)
            replicated = replicate_monthly_for_locations(monthly, locations)
            duplicates, issues = validate_update_rows(replicated)
            if not duplicates.empty:
                raise DatasetUpdateError(f"Generated {len(duplicates)} duplicate update rows for grid {grid_key}.")
            if not issues.empty:
                issue_preview = issues.head(5).to_dict("records")
                raise DatasetUpdateError(f"Generated values outside broad validation ranges: {issue_preview}")

            audit = audit.copy()
            audit.insert(0, "GRID_KEY", grid_key)
            audit.insert(1, "REQUEST_LAT", float(plan_row["REQUEST_LAT"]))
            audit.insert(2, "REQUEST_LON", float(plan_row["REQUEST_LON"]))
            _append_csv(replicated, staging_path)
            _append_csv(audit, audit_path)
            _append_csv(
                pd.DataFrame(
                    [
                        {
                            "TimestampUTC": utc_now_iso(),
                            "GRID_KEY": grid_key,
                            "Status": "Completed",
                            "LocationCount": int(plan_row["LOCATION_COUNT"]),
                            "RowsWritten": int(len(replicated)),
                            "ReceivedDays": metadata.get("received_days"),
                            "CompletenessPercent": metadata.get("completeness_percent"),
                            "AllFromCache": metadata.get("all_from_cache"),
                            "FallbackToCoreParameters": fallback_used,
                            "Message": "",
                        }
                    ]
                ),
                log_path,
            )
            completed.add(grid_key)
            completed_now += 1
            current_rows_written = int(len(replicated))
            rows_written += current_rows_written
        except Exception as error:
            failure = {
                "GRID_KEY": grid_key,
                "REQUEST_LAT": float(plan_row["REQUEST_LAT"]),
                "REQUEST_LON": float(plan_row["REQUEST_LON"]),
                "Message": f"{type(error).__name__}: {error}",
            }
            failures.append(failure)
            failed_attempts = checkpoint.setdefault("failed_attempts", {})
            failed_attempts[grid_key] = int(failed_attempts.get(grid_key, 0)) + 1
            _append_csv(
                pd.DataFrame(
                    [
                        {
                            "TimestampUTC": utc_now_iso(),
                            "GRID_KEY": grid_key,
                            "Status": "Failed",
                            "LocationCount": int(plan_row["LOCATION_COUNT"]),
                            "RowsWritten": 0,
                            "ReceivedDays": np.nan,
                            "CompletenessPercent": np.nan,
                            "AllFromCache": False,
                            "FallbackToCoreParameters": False,
                            "Message": failure["Message"],
                        }
                    ]
                ),
                log_path,
            )

        checkpoint["completed_grid_keys"] = sorted(completed)
        checkpoint["staging_rows"] = int(checkpoint.get("staging_rows", 0)) + current_rows_written
        checkpoint["updated_utc"] = utc_now_iso()
        checkpoint["status"] = "processing"
        atomic_write_text(root / "checkpoint.json", json.dumps(checkpoint, ensure_ascii=False, indent=2))
        if 'replicated' in locals():
            del replicated
        delay_seconds = max(0.0, float(configuration.get("request_delay_seconds", 1.5)))
        if position < len(pending) and delay_seconds > 0:
            time.sleep(delay_seconds)

    remaining = max(0, len(plan) - len(completed))
    checkpoint["status"] = "download_complete" if remaining == 0 else "processing"
    checkpoint["updated_utc"] = utc_now_iso()
    if staging_path.exists():
        try:
            checkpoint["staging_rows"] = max(0, sum(1 for _ in staging_path.open("r", encoding="utf-8")) - 1)
        except OSError:
            pass
    atomic_write_text(root / "checkpoint.json", json.dumps(checkpoint, ensure_ascii=False, indent=2))

    return BatchResult(
        attempted_grids=int(len(pending)),
        completed_grids=completed_now,
        failed_grids=len(failures),
        rows_written=rows_written,
        completed_total=len(completed),
        remaining_total=remaining,
        failures=failures,
    )


def deduplicate_long(frame: pd.DataFrame, keep: str = "last") -> pd.DataFrame:
    key = ["CITY", "STATE", "Year", "Month", "Variable"]
    return frame.drop_duplicates(key, keep=keep).reset_index(drop=True)


def sort_long(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["_month_number"] = result["Month"].map(MONTH_NUMBER)
    result = result.sort_values(["STATE", "CITY", "Year", "_month_number", "Variable"])
    return result.drop(columns="_month_number").reset_index(drop=True)


def to_mixed_format(long_frame: pd.DataFrame) -> pd.DataFrame:
    mixed = (
        long_frame.pivot_table(
            index=["CITY", "STATE", "Year", "Month"],
            columns="Variable",
            values="Value",
            aggfunc="first",
        )
        .reset_index()
    )
    mixed.columns.name = None
    mixed["_month_number"] = mixed["Month"].map(MONTH_NUMBER)
    mixed = mixed.sort_values(["STATE", "CITY", "Year", "_month_number"]).drop(columns="_month_number")
    fixed = ["CITY", "STATE", "Year", "Month"]
    variables = sorted(column for column in mixed.columns if column not in fixed)
    return mixed[fixed + variables].reset_index(drop=True)


def to_legacy_wide_format(long_frame: pd.DataFrame) -> pd.DataFrame:
    copy = long_frame.copy()
    copy["Var_Month_Year"] = (
        copy["Variable"].astype(str)
        + "_"
        + copy["Month"].astype(str)
        + "_"
        + copy["Year"].astype(str)
    )
    wide = (
        copy.pivot_table(
            index=["CITY", "STATE"],
            columns="Var_Month_Year",
            values="Value",
            aggfunc="first",
        )
        .reset_index()
    )
    wide.columns.name = None
    return wide


def finalise_candidate(
    job_dir: str | Path,
    source_dataset_path: str | Path,
    *,
    create_mixed: bool = True,
    create_legacy_wide: bool = False,
) -> dict:
    root = Path(job_dir)
    checkpoint, plan = load_job(root)
    if checkpoint is None or plan is None:
        raise DatasetUpdateError("No update job exists.")
    staging_path = root / "staging_update_long.csv"
    if not staging_path.exists():
        raise DatasetUpdateError("No staged update rows exist. Process at least one successful batch first.")

    expected_source_hash = str(checkpoint.get("configuration", {}).get("source_dataset_sha256", "") or "")
    actual_source_hash = sha256_file(source_dataset_path)
    if expected_source_hash and actual_source_hash != expected_source_hash:
        raise DatasetUpdateError(
            "The active climate dataset changed after this update job was created. Reset the updater and create a new job so rows are merged against the current file."
        )

    existing = clean_long_dataset(pd.read_csv(source_dataset_path))
    original_row_count = int(len(existing))
    key = ["CITY", "STATE", "Year", "Month", "Variable"]

    # Validate the historical source independently. Existing legacy values are
    # preserved and audited, but they do not make a clean incremental update fail.
    source_duplicates, source_issues = validate_update_rows(existing)
    if not source_duplicates.empty:
        source_duplicates = source_duplicates.copy()
        source_duplicates["Origin"] = "Pre-existing source duplicate"
        atomic_write_csv(source_duplicates, root / "source_duplicate_audit.csv")

    staging = deduplicate_long(clean_long_dataset(pd.read_csv(staging_path)), keep="last")
    duplicate_staging, staging_issues = validate_update_rows(staging)
    if not duplicate_staging.empty:
        duplicate_staging = duplicate_staging.copy()
        duplicate_staging["Origin"] = "Introduced by staged update"
        atomic_write_csv(duplicate_staging, root / "staging_duplicate_errors.csv")
        raise DatasetUpdateError(
            f"Staging data contain {len(duplicate_staging)} duplicate keys. "
            "Download staging_duplicate_errors.csv from the audit tab."
        )
    if not staging_issues.empty:
        staging_issues = staging_issues.copy()
        staging_issues["Origin"] = "Introduced by staged update"
        atomic_write_csv(staging_issues, root / "staging_validation_errors.csv")
        raise DatasetUpdateError(
            f"Staging data contain {len(staging_issues)} values outside broad validation ranges. "
            "Download staging_validation_errors.csv from the audit tab."
        )

    merge_mode = str(checkpoint["configuration"].get("merge_mode", "fill_missing"))
    if merge_mode == "replace_selected_period":
        replacement_keys = staging[key].drop_duplicates()
        existing_for_merge = existing.merge(replacement_keys.assign(_replace=True), on=key, how="left")
        existing_for_merge = existing_for_merge[existing_for_merge["_replace"].isna()].drop(columns="_replace")
        combined = pd.concat([existing_for_merge, staging], ignore_index=True)
    else:
        combined = pd.concat([existing, staging], ignore_index=True)
        combined = deduplicate_long(combined, keep="first")

    combined = sort_long(
        deduplicate_long(
            combined,
            keep="last" if merge_mode == "replace_selected_period" else "first",
        )
    )
    duplicates, candidate_issues = validate_update_rows(combined)
    if not duplicates.empty:
        duplicates = duplicates.copy()
        duplicates["Origin"] = "Candidate duplicate"
        atomic_write_csv(duplicates, root / "candidate_duplicate_errors.csv")
        raise DatasetUpdateError(
            f"Candidate dataset contains {len(duplicates)} duplicate keys. "
            "Download candidate_duplicate_errors.csv from the audit tab."
        )

    # Distinguish anomalies already present in the source dataset from values
    # introduced by this update. The staging rows have already passed strict
    # validation, so only genuinely new candidate issues should block finalisation.
    issue_columns = ["CITY", "STATE", "Year", "Month", "Variable", "Value", "Issue"]
    if candidate_issues.empty:
        candidate_validation_audit = pd.DataFrame(columns=issue_columns + ["Origin"])
        legacy_candidate_issues = candidate_issues.copy()
        new_candidate_issues = candidate_issues.copy()
    else:
        source_issue_keys = (
            source_issues[key]
            .drop_duplicates()
            .assign(_preexisting_issue=True)
            if not source_issues.empty
            else pd.DataFrame(columns=key + ["_preexisting_issue"])
        )
        candidate_validation_audit = candidate_issues.merge(
            source_issue_keys,
            on=key,
            how="left",
        )
        candidate_validation_audit["Origin"] = np.where(
            candidate_validation_audit["_preexisting_issue"].fillna(False),
            "Pre-existing source value",
            "Introduced by update",
        )
        candidate_validation_audit = candidate_validation_audit.drop(columns=["_preexisting_issue"])
        legacy_candidate_issues = candidate_validation_audit[
            candidate_validation_audit["Origin"] == "Pre-existing source value"
        ].copy()
        new_candidate_issues = candidate_validation_audit[
            candidate_validation_audit["Origin"] == "Introduced by update"
        ].copy()

    atomic_write_csv(candidate_validation_audit, root / "candidate_validation_audit.csv")

    if not new_candidate_issues.empty:
        atomic_write_csv(new_candidate_issues, root / "candidate_new_validation_errors.csv")
        raise DatasetUpdateError(
            f"Candidate dataset contains {len(new_candidate_issues)} newly introduced values "
            "outside broad validation ranges. Download candidate_new_validation_errors.csv "
            "from the audit tab before installation."
        )

    candidate_long = root / "candidate_agroclimate_longformat.csv"
    atomic_write_csv(combined, candidate_long)
    candidate_mixed = None
    candidate_wide = None
    if create_mixed:
        candidate_mixed = root / "candidate_agroclimate_mixedformat.csv"
        atomic_write_csv(to_mixed_format(combined), candidate_mixed)
    if create_legacy_wide:
        candidate_wide = root / "candidate_agroclimate_wideformat.csv"
        atomic_write_csv(to_legacy_wide_format(combined), candidate_wide)

    latest = latest_dataset_month(combined)
    added_keys = staging[key].drop_duplicates()
    manifest = {
        "schema_version": 1,
        "created_utc": utc_now_iso(),
        "source_dataset": str(Path(source_dataset_path).resolve()),
        "source_sha256": sha256_file(source_dataset_path),
        "candidate_long": str(candidate_long.resolve()),
        "candidate_long_sha256": sha256_file(candidate_long),
        "candidate_mixed": str(candidate_mixed.resolve()) if candidate_mixed else None,
        "candidate_wide": str(candidate_wide.resolve()) if candidate_wide else None,
        "merge_mode": merge_mode,
        "original_rows": original_row_count,
        "staged_rows": int(len(staging)),
        "candidate_rows": int(len(combined)),
        "staged_unique_keys": int(len(added_keys)),
        "preexisting_validation_warnings": int(len(legacy_candidate_issues)),
        "new_validation_errors": int(len(new_candidate_issues)),
        "source_duplicate_rows_detected": int(len(source_duplicates)),
        "validation_policy": (
            "Newly staged NASA values are validated strictly. Values already present "
            "in the historical source dataset are preserved and reported as legacy warnings."
        ),
        "locations": int(combined[["CITY", "STATE"]].drop_duplicates().shape[0]),
        "variables": sorted(combined["Variable"].unique().tolist()),
        "coverage_start_year": int(combined["Year"].min()),
        "coverage_end_month": latest.isoformat() if latest else None,
        "configuration": checkpoint["configuration"],
        "target_country": str(checkpoint.get("configuration", {}).get("target_country", "Mexico")),
        "parameter_provenance": {
            "source": "NASA POWER Daily Point API",
            "source_docs": NASA_POWER_DAILY_DOCS,
            "parameter_dictionary": NASA_POWER_PARAMETER_DOCS,
            "eto_method": "FAO-56 Penman-Monteith calculated from daily POWER AG inputs; ALLSKY_SFC_SW_DWN is treated as MJ m-2 day-1; daily soil heat flux set to zero; mean RH used for actual vapour pressure approximation.",
            "monthly_aggregation": "Daily means aggregated by arithmetic mean; precipitation minimum and maximum are daily extrema within each calendar month.",
        },
    }
    manifest_path = root / "candidate_manifest.json"
    atomic_write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2))

    package_path = root / "candidate_dataset_package.zip"
    package_temp = package_path.with_suffix(".zip.tmp")
    with zipfile.ZipFile(package_temp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.write(candidate_long, arcname="agroclimate_longformat.csv")
        if candidate_mixed is not None:
            archive.write(candidate_mixed, arcname="agroclimate_mixedformat.csv")
        if candidate_wide is not None:
            archive.write(candidate_wide, arcname="agroclimate_wideformat.csv")
        archive.write(manifest_path, arcname="candidate_manifest.json")
        for optional_name in [
            "staging_update_long.csv",
            "monthly_coverage_audit.csv",
            "request_log.csv",
            "candidate_validation_audit.csv",
            "source_duplicate_audit.csv",
            "staging_validation_errors.csv",
            "candidate_new_validation_errors.csv",
            "staging_duplicate_errors.csv",
            "candidate_duplicate_errors.csv",
        ]:
            optional_path = root / optional_name
            if optional_path.exists():
                archive.write(optional_path, arcname=f"audit/{optional_name}")
    _replace_file_with_retries(package_temp, package_path)
    manifest["candidate_package"] = str(package_path.resolve())
    manifest["candidate_package_sha256"] = sha256_file(package_path)
    atomic_write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2))

    checkpoint["status"] = "candidate_ready"
    checkpoint["candidate_manifest"] = str(manifest_path)
    checkpoint["updated_utc"] = utc_now_iso()
    atomic_write_text(root / "checkpoint.json", json.dumps(checkpoint, ensure_ascii=False, indent=2))
    return manifest


def install_candidate(
    job_dir: str | Path,
    target_dataset_path: str | Path,
    *,
    backup_dir: str | Path,
    similarity_cache_path: str | Path | None = None,
    target_similarity_cache_path: str | Path | None = None,
) -> dict:
    # ``target_similarity_cache_path`` is retained as a backwards-compatible
    # alias for the accidental Release 9 call site. The documented API remains
    # ``similarity_cache_path``.
    if similarity_cache_path is None and target_similarity_cache_path is not None:
        similarity_cache_path = target_similarity_cache_path

    root = Path(job_dir)
    candidate = root / "candidate_agroclimate_longformat.csv"
    manifest_path = root / "candidate_manifest.json"
    if not candidate.exists() or not manifest_path.exists():
        raise DatasetUpdateError("Finalise a candidate dataset before installation.")

    target = Path(target_dataset_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    backups = Path(backup_dir)
    backups.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backups / f"{target.stem}_backup_{timestamp}{target.suffix}"
    if target.exists():
        shutil.copy2(target, backup_path)

    temporary = target.with_suffix(target.suffix + ".installing")
    shutil.copy2(candidate, temporary)
    if sha256_file(temporary) != sha256_file(candidate):
        temporary.unlink(missing_ok=True)
        raise DatasetUpdateError("Candidate copy failed checksum verification; the active dataset was not changed.")
    _replace_file_with_retries(temporary, target)

    if similarity_cache_path:
        Path(similarity_cache_path).unlink(missing_ok=True)

    installation = {
        "installed_utc": utc_now_iso(),
        "target_dataset": str(target.resolve()),
        "target_sha256": sha256_file(target),
        "backup_dataset": str(backup_path.resolve()) if backup_path.exists() else None,
        "candidate_manifest": json.loads(manifest_path.read_text(encoding="utf-8")),
    }
    installation_path = root / "installation_record.json"
    atomic_write_text(installation_path, json.dumps(installation, ensure_ascii=False, indent=2))

    checkpoint, _ = load_job(root)
    if checkpoint is not None:
        checkpoint["status"] = "installed"
        checkpoint["installation_record"] = str(installation_path)
        checkpoint["updated_utc"] = utc_now_iso()
        atomic_write_text(root / "checkpoint.json", json.dumps(checkpoint, ensure_ascii=False, indent=2))
    return installation


def reset_job(job_dir: str | Path) -> int:
    root = Path(job_dir)
    if not root.exists():
        return 0
    removed = 0
    for path in root.glob("*"):
        if path.is_file():
            path.unlink(missing_ok=True)
            removed += 1
    return removed


def job_inventory(job_dir: str | Path) -> pd.DataFrame:
    root = Path(job_dir)
    rows: list[dict] = []
    if not root.exists():
        return pd.DataFrame(columns=["File", "SizeMB", "Modified"])
    for path in sorted(root.glob("*")):
        if path.is_file():
            stat = path.stat()
            rows.append(
                {
                    "File": path.name,
                    "SizeMB": stat.st_size / (1024 * 1024),
                    "Modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                }
            )
    return pd.DataFrame(rows)
