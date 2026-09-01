"""Daily weather retrieval and crop phenology utilities.

This module is intentionally independent of Streamlit so its calculations can be
unit-tested and reused by scripts or APIs. NASA POWER requests use the public
Daily Point API and are cached locally as compressed JSON payloads.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import math
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

NASA_POWER_DAILY_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
NASA_POWER_EARLIEST_DATE = date(1981, 1, 1)

POWER_PARAMETER_REGISTRY: dict[str, dict[str, str]] = {
    "T2M": {
        "label": "Mean temperature at 2 m",
        "expected_unit": "°C",
        "description": "Daily mean near-surface air temperature.",
    },
    "T2M_MAX": {
        "label": "Maximum temperature at 2 m",
        "expected_unit": "°C",
        "description": "Daily maximum near-surface air temperature.",
    },
    "T2M_MIN": {
        "label": "Minimum temperature at 2 m",
        "expected_unit": "°C",
        "description": "Daily minimum near-surface air temperature.",
    },
    "PRECTOTCORR": {
        "label": "Corrected precipitation",
        "expected_unit": "mm day⁻¹",
        "description": "Bias-corrected daily precipitation total supplied by POWER.",
    },
    "ALLSKY_SFC_SW_DWN": {
        "label": "All-sky surface shortwave radiation",
        "expected_unit": "MJ m⁻² day⁻¹",
        "description": "Daily solar radiation incident on a horizontal surface.",
    },
    "RH2M": {
        "label": "Relative humidity at 2 m",
        "expected_unit": "%",
        "description": "Daily mean relative humidity near the surface.",
    },
    "WS2M": {
        "label": "Wind speed at 2 m",
        "expected_unit": "m s⁻¹",
        "description": "Daily mean wind speed at 2 m.",
    },
}

DEFAULT_POWER_PARAMETERS: tuple[str, ...] = tuple(POWER_PARAMETER_REGISTRY)


class DailyWeatherError(RuntimeError):
    """Raised for retrieval, parsing, or calculation failures."""


@dataclass(frozen=True)
class PowerRequestSpec:
    latitude: float
    longitude: float
    start_date: date
    end_date: date
    parameters: tuple[str, ...]
    time_standard: str = "LST"
    community: str = "AG"

    def validated(self) -> "PowerRequestSpec":
        if not -90 <= float(self.latitude) <= 90:
            raise ValueError("Latitude must be between -90 and 90 degrees.")
        if not -180 <= float(self.longitude) <= 180:
            raise ValueError("Longitude must be between -180 and 180 degrees.")
        if self.start_date > self.end_date:
            raise ValueError("The start date must not be after the end date.")
        if self.start_date < NASA_POWER_EARLIEST_DATE:
            raise ValueError("NASA POWER daily data are requested from 1981-01-01 onward.")
        if self.end_date > date.today() + timedelta(days=1):
            raise ValueError("The end date cannot be in the future.")
        requested = tuple(dict.fromkeys(str(p).strip().upper() for p in self.parameters if str(p).strip()))
        if not requested:
            raise ValueError("Select at least one NASA POWER parameter.")
        if len(requested) > 20:
            raise ValueError("NASA POWER permits at most 20 parameters in one point request.")
        if self.time_standard.upper() not in {"LST", "UTC"}:
            raise ValueError("Time standard must be LST or UTC.")
        return PowerRequestSpec(
            latitude=float(self.latitude),
            longitude=float(self.longitude),
            start_date=self.start_date,
            end_date=self.end_date,
            parameters=requested,
            time_standard=self.time_standard.upper(),
            community=self.community.upper(),
        )


def _as_date(value: date | datetime | str | pd.Timestamp) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    parsed = pd.to_datetime(value, errors="raise")
    return parsed.date()


def build_power_daily_url(spec: PowerRequestSpec) -> str:
    spec = spec.validated()
    query = urlencode(
        {
            "parameters": ",".join(spec.parameters),
            "community": spec.community,
            "longitude": f"{spec.longitude:.6f}",
            "latitude": f"{spec.latitude:.6f}",
            "start": spec.start_date.strftime("%Y%m%d"),
            "end": spec.end_date.strftime("%Y%m%d"),
            "format": "JSON",
            "time-standard": spec.time_standard,
        }
    )
    return f"{NASA_POWER_DAILY_URL}?{query}"


def _request_cache_key(spec: PowerRequestSpec) -> str:
    spec = spec.validated()
    payload = {
        "latitude": round(spec.latitude, 5),
        "longitude": round(spec.longitude, 5),
        "start": spec.start_date.isoformat(),
        "end": spec.end_date.isoformat(),
        "parameters": sorted(spec.parameters),
        "time_standard": spec.time_standard,
        "community": spec.community,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _cache_path(cache_dir: str | Path, spec: PowerRequestSpec) -> Path:
    path = Path(cache_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path / f"power_daily_{_request_cache_key(spec)}.json.gz"


def _read_cache(path: Path) -> dict | None:
    try:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _write_cache(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with gzip.open(temporary, "wt", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False, separators=(",", ":"))
    temporary.replace(path)


def _friendly_http_error(error: HTTPError) -> str:
    try:
        body = error.read().decode("utf-8", errors="replace")
    except Exception:
        body = ""
    suffix = f" Details: {body[:400]}" if body else ""
    if error.code == 422:
        return "NASA POWER rejected the request parameters (HTTP 422)." + suffix
    if error.code == 429:
        return "NASA POWER temporarily rate-limited the request (HTTP 429). Use the local cache and retry later."
    return f"NASA POWER returned HTTP {error.code}." + suffix


def fetch_power_payload(
    spec: PowerRequestSpec,
    cache_dir: str | Path,
    *,
    force_refresh: bool = False,
    timeout_seconds: int = 90,
    max_attempts: int = 3,
) -> tuple[dict, dict]:
    """Fetch one NASA POWER request and return payload plus cache metadata."""
    spec = spec.validated()
    path = _cache_path(cache_dir, spec)
    if path.exists() and not force_refresh:
        cached = _read_cache(path)
        if cached and isinstance(cached.get("payload"), dict):
            return cached["payload"], {
                "cache_hit": True,
                "cache_file": str(path),
                "downloaded_utc": cached.get("downloaded_utc"),
                "request_url": cached.get("request_url", build_power_daily_url(spec)),
            }

    url = build_power_daily_url(spec)
    last_error: Exception | None = None
    for attempt in range(1, max(1, int(max_attempts)) + 1):
        request = Request(
            url,
            headers={
                "User-Agent": "MexicoAgroclimateResearchTool/6.0 (research application)",
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=max(10, int(timeout_seconds))) as response:
                payload = json.loads(response.read().decode("utf-8"))
            record = {
                "downloaded_utc": datetime.now(timezone.utc).isoformat(),
                "request_url": url,
                "request": {
                    "latitude": spec.latitude,
                    "longitude": spec.longitude,
                    "start_date": spec.start_date.isoformat(),
                    "end_date": spec.end_date.isoformat(),
                    "parameters": list(spec.parameters),
                    "time_standard": spec.time_standard,
                    "community": spec.community,
                },
                "payload": payload,
            }
            _write_cache(path, record)
            return payload, {
                "cache_hit": False,
                "cache_file": str(path),
                "downloaded_utc": record["downloaded_utc"],
                "request_url": url,
            }
        except HTTPError as error:
            last_error = DailyWeatherError(_friendly_http_error(error))
            if error.code not in {429, 500, 502, 503, 504}:
                break
        except URLError as error:
            last_error = DailyWeatherError(
                f"Could not connect to NASA POWER: {getattr(error, 'reason', error)}"
            )
        except (TimeoutError, json.JSONDecodeError) as error:
            last_error = DailyWeatherError(f"NASA POWER response could not be read: {error}")
        if attempt < max_attempts:
            time.sleep(min(8, 2 ** (attempt - 1)))

    raise last_error or DailyWeatherError("NASA POWER request failed for an unknown reason.")


def parse_power_daily_payload(payload: Mapping) -> tuple[pd.DataFrame, dict]:
    """Parse the POWER JSON structure into one row per date."""
    try:
        parameter_block = payload["properties"]["parameter"]
    except Exception as error:
        messages = payload.get("messages") if isinstance(payload, Mapping) else None
        raise DailyWeatherError(
            f"NASA POWER response did not contain daily parameter data. Messages: {messages}"
        ) from error

    if not isinstance(parameter_block, Mapping) or not parameter_block:
        raise DailyWeatherError("NASA POWER returned an empty parameter block.")

    date_keys: set[str] = set()
    for values in parameter_block.values():
        if isinstance(values, Mapping):
            date_keys.update(str(key) for key in values)
    valid_dates = sorted(key for key in date_keys if len(key) == 8 and key.isdigit())
    if not valid_dates:
        raise DailyWeatherError("NASA POWER returned no parseable daily dates.")

    frame = pd.DataFrame({"DATE": pd.to_datetime(valid_dates, format="%Y%m%d", errors="coerce")})
    for parameter, values in parameter_block.items():
        if not isinstance(values, Mapping):
            continue
        frame[str(parameter).upper()] = [values.get(key, np.nan) for key in valid_dates]

    for column in frame.columns.difference(["DATE"]):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame.loc[frame[column] <= -900, column] = np.nan

    frame = frame.dropna(subset=["DATE"]).sort_values("DATE").drop_duplicates("DATE").reset_index(drop=True)

    metadata = {
        "header": payload.get("header", {}),
        "messages": payload.get("messages", []),
        "geometry": payload.get("geometry", {}),
        "parameter_metadata": payload.get("parameters", {}),
        "available_parameters": [c for c in frame.columns if c != "DATE"],
        "start_date": frame["DATE"].min().date().isoformat(),
        "end_date": frame["DATE"].max().date().isoformat(),
        "row_count": int(len(frame)),
    }
    return frame, metadata


def _chunk_specs(spec: PowerRequestSpec, years_per_chunk: int = 5) -> list[PowerRequestSpec]:
    spec = spec.validated()
    years_per_chunk = max(1, int(years_per_chunk))
    chunks: list[PowerRequestSpec] = []
    cursor = spec.start_date
    while cursor <= spec.end_date:
        chunk_end_year = min(spec.end_date.year, cursor.year + years_per_chunk - 1)
        chunk_end = min(spec.end_date, date(chunk_end_year, 12, 31))
        chunks.append(
            PowerRequestSpec(
                latitude=spec.latitude,
                longitude=spec.longitude,
                start_date=cursor,
                end_date=chunk_end,
                parameters=spec.parameters,
                time_standard=spec.time_standard,
                community=spec.community,
            )
        )
        cursor = chunk_end + timedelta(days=1)
    return chunks


def fetch_nasa_power_daily(
    latitude: float,
    longitude: float,
    start_date: date | datetime | str,
    end_date: date | datetime | str,
    cache_dir: str | Path,
    *,
    parameters: Sequence[str] = DEFAULT_POWER_PARAMETERS,
    time_standard: str = "LST",
    force_refresh: bool = False,
    years_per_chunk: int = 5,
    timeout_seconds: int = 90,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Retrieve a date range, chunking long requests and reusing disk cache."""
    base_spec = PowerRequestSpec(
        latitude=float(latitude),
        longitude=float(longitude),
        start_date=_as_date(start_date),
        end_date=_as_date(end_date),
        parameters=tuple(parameters),
        time_standard=time_standard,
    ).validated()

    chunks = _chunk_specs(base_spec, years_per_chunk=years_per_chunk)
    frames: list[pd.DataFrame] = []
    chunk_metadata: list[dict] = []
    for index, chunk in enumerate(chunks, start=1):
        if progress_callback:
            progress_callback(index, len(chunks), f"Fetching {chunk.start_date} to {chunk.end_date}")
        payload, cache_meta = fetch_power_payload(
            chunk,
            cache_dir,
            force_refresh=force_refresh,
            timeout_seconds=timeout_seconds,
        )
        frame, parsed_meta = parse_power_daily_payload(payload)
        frames.append(frame)
        chunk_metadata.append({**cache_meta, **parsed_meta})

    combined = (
        pd.concat(frames, ignore_index=True)
        .sort_values("DATE")
        .drop_duplicates("DATE", keep="last")
        .reset_index(drop=True)
    )
    expected_days = (base_spec.end_date - base_spec.start_date).days + 1
    metadata = {
        "source": "NASA POWER Daily Point API",
        "source_url": NASA_POWER_DAILY_URL,
        "latitude": base_spec.latitude,
        "longitude": base_spec.longitude,
        "start_date": base_spec.start_date.isoformat(),
        "end_date": base_spec.end_date.isoformat(),
        "time_standard": base_spec.time_standard,
        "community": base_spec.community,
        "parameters": list(base_spec.parameters),
        "expected_days": expected_days,
        "received_days": int(len(combined)),
        "completeness_percent": 100.0 * len(combined) / expected_days if expected_days else np.nan,
        "all_from_cache": bool(chunk_metadata) and all(item.get("cache_hit") for item in chunk_metadata),
        "chunks": chunk_metadata,
    }
    return combined, metadata


def saturation_vapour_pressure_kpa(temperature_c: pd.Series | np.ndarray | float):
    values = np.asarray(temperature_c, dtype=float)
    return 0.6108 * np.exp((17.27 * values) / (values + 237.3))


def calculate_vpd_kpa(temperature_c, relative_humidity_percent):
    temperature = np.asarray(temperature_c, dtype=float)
    humidity = np.clip(np.asarray(relative_humidity_percent, dtype=float), 0.0, 100.0)
    vpd = saturation_vapour_pressure_kpa(temperature) * (1.0 - humidity / 100.0)
    return np.maximum(vpd, 0.0)


def calculate_daily_gdd(
    tmean_c,
    tmax_c,
    tmin_c,
    *,
    base_temperature_c: float,
    upper_temperature_c: float | None = None,
    method: str = "modified_average",
) -> np.ndarray:
    """Calculate daily growing degree days using simple or modified averaging."""
    base = float(base_temperature_c)
    method_key = str(method).strip().casefold()
    mean = np.asarray(tmean_c, dtype=float)
    maximum = np.asarray(tmax_c, dtype=float)
    minimum = np.asarray(tmin_c, dtype=float)

    if method_key in {"simple", "simple_average", "mean"}:
        thermal_mean = mean.copy()
        missing = ~np.isfinite(thermal_mean)
        thermal_mean[missing] = (maximum[missing] + minimum[missing]) / 2.0
    elif method_key in {"modified", "modified_average", "capped"}:
        adjusted_min = np.maximum(minimum, base)
        adjusted_max = maximum.copy()
        if upper_temperature_c is not None and np.isfinite(float(upper_temperature_c)):
            adjusted_max = np.minimum(adjusted_max, float(upper_temperature_c))
        adjusted_max = np.maximum(adjusted_max, base)
        thermal_mean = (adjusted_max + adjusted_min) / 2.0
        missing = ~np.isfinite(thermal_mean)
        fallback = mean.copy()
        if upper_temperature_c is not None and np.isfinite(float(upper_temperature_c)):
            fallback = np.minimum(fallback, float(upper_temperature_c))
        thermal_mean[missing] = fallback[missing]
    else:
        raise ValueError("GDD method must be 'simple_average' or 'modified_average'.")

    gdd = np.maximum(0.0, thermal_mean - base)
    gdd[~np.isfinite(thermal_mean)] = np.nan
    return gdd


def add_daily_derived_metrics(
    weather: pd.DataFrame,
    *,
    base_temperature_c: float,
    upper_temperature_c: float | None = None,
    gdd_method: str = "modified_average",
    dry_day_threshold_mm: float = 1.0,
) -> pd.DataFrame:
    """Add harmonised temperature, precipitation, VPD, and GDD columns."""
    if "DATE" not in weather.columns:
        raise ValueError("Daily weather data must contain a DATE column.")
    frame = weather.copy()
    frame["DATE"] = pd.to_datetime(frame["DATE"], errors="coerce")
    frame = frame.dropna(subset=["DATE"]).sort_values("DATE").reset_index(drop=True)

    tmean = pd.to_numeric(frame.get("T2M"), errors="coerce") if "T2M" in frame else pd.Series(np.nan, index=frame.index)
    tmax = pd.to_numeric(frame.get("T2M_MAX"), errors="coerce") if "T2M_MAX" in frame else pd.Series(np.nan, index=frame.index)
    tmin = pd.to_numeric(frame.get("T2M_MIN"), errors="coerce") if "T2M_MIN" in frame else pd.Series(np.nan, index=frame.index)
    derived_mean = (tmax + tmin) / 2.0
    tmean = tmean.fillna(derived_mean)

    frame["TMEAN_C"] = tmean
    frame["TMAX_C"] = tmax
    frame["TMIN_C"] = tmin
    frame["PRECIP_MM"] = (
        pd.to_numeric(frame.get("PRECTOTCORR"), errors="coerce")
        if "PRECTOTCORR" in frame
        else np.nan
    )
    frame["RH_PERCENT"] = (
        pd.to_numeric(frame.get("RH2M"), errors="coerce") if "RH2M" in frame else np.nan
    )
    frame["WIND_M_S"] = (
        pd.to_numeric(frame.get("WS2M"), errors="coerce") if "WS2M" in frame else np.nan
    )
    frame["SOLAR_MJ_M2_DAY"] = (
        pd.to_numeric(frame.get("ALLSKY_SFC_SW_DWN"), errors="coerce")
        if "ALLSKY_SFC_SW_DWN" in frame
        else np.nan
    )

    if np.isfinite(pd.to_numeric(frame["RH_PERCENT"], errors="coerce")).any():
        frame["VPD_KPA"] = calculate_vpd_kpa(frame["TMEAN_C"], frame["RH_PERCENT"])
    else:
        frame["VPD_KPA"] = np.nan

    frame["GDD_DAILY"] = calculate_daily_gdd(
        frame["TMEAN_C"],
        frame["TMAX_C"],
        frame["TMIN_C"],
        base_temperature_c=base_temperature_c,
        upper_temperature_c=upper_temperature_c,
        method=gdd_method,
    )
    frame["GDD_CUMULATIVE"] = frame["GDD_DAILY"].fillna(0.0).cumsum()
    frame["YEAR"] = frame["DATE"].dt.year
    frame["MONTH"] = frame["DATE"].dt.month
    frame["DAY_OF_YEAR"] = frame["DATE"].dt.dayofyear
    frame["DRY_DAY"] = frame["PRECIP_MM"].fillna(np.inf) < float(dry_day_threshold_mm)
    frame["RAIN_DAY"] = frame["PRECIP_MM"].fillna(-np.inf) >= float(dry_day_threshold_mm)
    return frame


def longest_true_run(values: Iterable[bool]) -> int:
    longest = 0
    current = 0
    for value in values:
        if bool(value):
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return int(longest)


def weather_event_summary(
    daily: pd.DataFrame,
    *,
    heat_threshold_c: float,
    severe_heat_threshold_c: float,
    frost_threshold_c: float = 0.0,
    dry_day_threshold_mm: float = 1.0,
    heavy_rain_threshold_mm: float = 25.0,
    high_vpd_threshold_kpa: float = 2.0,
) -> tuple[dict, pd.DataFrame]:
    """Summarise daily exposure and return event flags."""
    frame = daily.copy()
    precip = pd.to_numeric(frame.get("PRECIP_MM"), errors="coerce")
    tmax = pd.to_numeric(frame.get("TMAX_C"), errors="coerce")
    tmin = pd.to_numeric(frame.get("TMIN_C"), errors="coerce")
    vpd = pd.to_numeric(frame.get("VPD_KPA"), errors="coerce")

    frame["HEAT_DAY"] = tmax >= float(heat_threshold_c)
    frame["SEVERE_HEAT_DAY"] = tmax >= float(severe_heat_threshold_c)
    frame["FROST_DAY"] = tmin <= float(frost_threshold_c)
    frame["DRY_DAY"] = precip < float(dry_day_threshold_mm)
    frame["HEAVY_RAIN_DAY"] = precip >= float(heavy_rain_threshold_mm)
    frame["HIGH_VPD_DAY"] = vpd >= float(high_vpd_threshold_kpa)

    summary = {
        "Days represented": int(len(frame)),
        "Start date": frame["DATE"].min() if len(frame) else pd.NaT,
        "End date": frame["DATE"].max() if len(frame) else pd.NaT,
        "Mean temperature (°C)": float(pd.to_numeric(frame.get("TMEAN_C"), errors="coerce").mean()),
        "Maximum temperature (°C)": float(tmax.max()),
        "Minimum temperature (°C)": float(tmin.min()),
        "Total precipitation (mm)": float(precip.sum(min_count=1)),
        "Total GDD": float(pd.to_numeric(frame.get("GDD_DAILY"), errors="coerce").sum(min_count=1)),
        "Heat days": int(frame["HEAT_DAY"].fillna(False).sum()),
        "Severe heat days": int(frame["SEVERE_HEAT_DAY"].fillna(False).sum()),
        "Frost days": int(frame["FROST_DAY"].fillna(False).sum()),
        "Dry days": int(frame["DRY_DAY"].fillna(False).sum()),
        "Longest dry spell (days)": longest_true_run(frame["DRY_DAY"].fillna(False)),
        "Heavy-rain days": int(frame["HEAVY_RAIN_DAY"].fillna(False).sum()),
        "Maximum one-day precipitation (mm)": float(precip.max()),
        "Mean VPD (kPa)": float(vpd.mean()),
        "High-VPD days": int(frame["HIGH_VPD_DAY"].fillna(False).sum()),
        "Mean solar radiation (MJ m⁻² day⁻¹)": float(pd.to_numeric(frame.get("SOLAR_MJ_M2_DAY"), errors="coerce").mean()),
        "Mean wind speed (m s⁻¹)": float(pd.to_numeric(frame.get("WIND_M_S"), errors="coerce").mean()),
    }
    return summary, frame


def stage_duration_profiles(crop_record: Mapping) -> dict[str, list[dict]]:
    """Extract usable stage-duration profiles from the validated crop registry."""
    profiles: dict[str, list[dict]] = {}
    for row in crop_record.get("stage_water_parameters", []) if isinstance(crop_record, Mapping) else []:
        duration = row.get("duration_days") or {}
        minimum = pd.to_numeric(duration.get("min"), errors="coerce")
        maximum = pd.to_numeric(duration.get("max"), errors="coerce")
        if pd.isna(minimum) and pd.isna(maximum):
            continue
        name = str(row.get("profile") or "Default profile")
        profiles.setdefault(name, []).append(
            {
                "Stage": str(row.get("stage") or "Stage"),
                "Duration minimum (days)": float(minimum) if pd.notna(minimum) else np.nan,
                "Duration maximum (days)": float(maximum) if pd.notna(maximum) else np.nan,
                "Interpretation": str(row.get("interpretation") or ""),
                "Evidence grade": str(row.get("evidence_grade") or "Unspecified"),
                "Source IDs": ", ".join(str(item) for item in row.get("source_ids", [])),
            }
        )
    return profiles


def build_duration_stage_schedule(
    planting_date: date | datetime | str,
    stage_rows: Sequence[Mapping],
    *,
    duration_strategy: str = "midpoint",
) -> pd.DataFrame:
    """Predict stage boundaries from validated day-duration ranges."""
    current = _as_date(planting_date)
    strategy = str(duration_strategy).strip().casefold()
    records: list[dict] = []
    for row in stage_rows:
        minimum = pd.to_numeric(row.get("Duration minimum (days)"), errors="coerce")
        maximum = pd.to_numeric(row.get("Duration maximum (days)"), errors="coerce")
        if pd.isna(minimum) and pd.isna(maximum):
            continue
        if pd.isna(minimum):
            minimum = maximum
        if pd.isna(maximum):
            maximum = minimum
        if strategy in {"minimum", "min", "short"}:
            duration = int(round(float(minimum)))
        elif strategy in {"maximum", "max", "long"}:
            duration = int(round(float(maximum)))
        else:
            duration = int(round((float(minimum) + float(maximum)) / 2.0))
        duration = max(1, duration)
        end = current + timedelta(days=duration - 1)
        records.append(
            {
                "Stage": str(row.get("Stage", "Stage")),
                "Start date": pd.Timestamp(current),
                "End date": pd.Timestamp(end),
                "Duration (days)": duration,
                "Duration basis": strategy if strategy else "midpoint",
                "Interpretation": row.get("Interpretation", ""),
                "Evidence grade": row.get("Evidence grade", ""),
                "Source IDs": row.get("Source IDs", ""),
            }
        )
        current = end + timedelta(days=1)
    return pd.DataFrame(records)


def build_gdd_stage_schedule(
    daily: pd.DataFrame,
    planting_date: date | datetime | str,
    stage_targets: Sequence[Mapping],
) -> pd.DataFrame:
    """Predict stage-end dates from user-supplied cumulative GDD targets."""
    planting = pd.Timestamp(_as_date(planting_date))
    frame = daily.copy()
    frame["DATE"] = pd.to_datetime(frame["DATE"], errors="coerce")
    frame = frame.loc[frame["DATE"] >= planting].sort_values("DATE").copy()
    frame["GDD_FROM_PLANTING"] = pd.to_numeric(frame.get("GDD_DAILY"), errors="coerce").fillna(0.0).cumsum()
    if frame.empty:
        raise ValueError("No daily weather records are available on or after the planting date.")

    cleaned: list[tuple[str, float, str]] = []
    for row in stage_targets:
        target = pd.to_numeric(row.get("Cumulative GDD target"), errors="coerce")
        if pd.isna(target) or float(target) <= 0:
            continue
        cleaned.append((str(row.get("Stage") or "Stage"), float(target), str(row.get("Source / note") or "User supplied")))
    if not cleaned:
        raise ValueError("Enter at least one positive cumulative GDD target.")
    cleaned.sort(key=lambda item: item[1])

    records: list[dict] = []
    stage_start = planting
    previous_target = 0.0
    for stage, target, source_note in cleaned:
        reached = frame.loc[frame["GDD_FROM_PLANTING"] >= target]
        if reached.empty:
            end_date = pd.NaT
            days = np.nan
            achieved = float(frame["GDD_FROM_PLANTING"].max())
        else:
            end_date = reached.iloc[0]["DATE"]
            days = int((end_date - stage_start).days + 1)
            achieved = float(reached.iloc[0]["GDD_FROM_PLANTING"])
        records.append(
            {
                "Stage": stage,
                "Start date": stage_start,
                "End date": end_date,
                "Duration (days)": days,
                "Cumulative GDD target": target,
                "Cumulative GDD achieved": achieved,
                "Target reached": bool(pd.notna(end_date)),
                "Source / note": source_note,
                "Stage GDD increment": target - previous_target,
            }
        )
        if pd.notna(end_date):
            stage_start = end_date + pd.Timedelta(days=1)
        previous_target = target
    return pd.DataFrame(records)


def summarise_stage_exposure(
    daily: pd.DataFrame,
    schedule: pd.DataFrame,
    *,
    heat_threshold_c: float,
    severe_heat_threshold_c: float,
    frost_threshold_c: float,
    dry_day_threshold_mm: float,
    heavy_rain_threshold_mm: float,
    high_vpd_threshold_kpa: float,
) -> pd.DataFrame:
    """Summarise weather exposure within each predicted crop stage."""
    if schedule is None or schedule.empty:
        return pd.DataFrame()
    weather = daily.copy()
    weather["DATE"] = pd.to_datetime(weather["DATE"], errors="coerce")
    records: list[dict] = []
    for _, row in schedule.iterrows():
        start = pd.to_datetime(row.get("Start date"), errors="coerce")
        end = pd.to_datetime(row.get("End date"), errors="coerce")
        if pd.isna(start) or pd.isna(end):
            records.append({"Stage": row.get("Stage"), "Start date": start, "End date": end, "Status": "Stage target not reached"})
            continue
        subset = weather.loc[weather["DATE"].between(start, end)].copy()
        if subset.empty:
            records.append({"Stage": row.get("Stage"), "Start date": start, "End date": end, "Status": "No weather data"})
            continue
        summary, _ = weather_event_summary(
            subset,
            heat_threshold_c=heat_threshold_c,
            severe_heat_threshold_c=severe_heat_threshold_c,
            frost_threshold_c=frost_threshold_c,
            dry_day_threshold_mm=dry_day_threshold_mm,
            heavy_rain_threshold_mm=heavy_rain_threshold_mm,
            high_vpd_threshold_kpa=high_vpd_threshold_kpa,
        )
        records.append(
            {
                "Stage": row.get("Stage"),
                "Start date": start,
                "End date": end,
                "Status": "Complete",
                **summary,
            }
        )
    return pd.DataFrame(records)


def _safe_anchor_date(year: int, month: int, day: int) -> date:
    try:
        return date(int(year), int(month), int(day))
    except ValueError:
        if int(month) == 2 and int(day) == 29:
            return date(int(year), 2, 28)
        raise


def build_historical_season_summary(
    raw_daily: pd.DataFrame,
    *,
    planting_month: int,
    planting_day: int,
    season_length_days: int,
    start_year: int,
    end_year: int,
    base_temperature_c: float,
    upper_temperature_c: float | None,
    gdd_method: str,
    heat_threshold_c: float,
    severe_heat_threshold_c: float,
    frost_threshold_c: float,
    dry_day_threshold_mm: float,
    heavy_rain_threshold_mm: float,
    high_vpd_threshold_kpa: float,
    minimum_completeness_percent: float = 90.0,
) -> pd.DataFrame:
    """Create same-planting-date seasonal summaries for historical years."""
    frame = raw_daily.copy()
    frame["DATE"] = pd.to_datetime(frame["DATE"], errors="coerce")
    frame = frame.dropna(subset=["DATE"]).sort_values("DATE")
    length = max(1, int(season_length_days))
    records: list[dict] = []
    for anchor_year in range(int(start_year), int(end_year) + 1):
        anchor = _safe_anchor_date(anchor_year, planting_month, planting_day)
        finish = anchor + timedelta(days=length - 1)
        subset = frame.loc[frame["DATE"].between(pd.Timestamp(anchor), pd.Timestamp(finish))].copy()
        completeness = 100.0 * len(subset) / length
        if completeness < float(minimum_completeness_percent):
            continue
        derived = add_daily_derived_metrics(
            subset,
            base_temperature_c=base_temperature_c,
            upper_temperature_c=upper_temperature_c,
            gdd_method=gdd_method,
            dry_day_threshold_mm=dry_day_threshold_mm,
        )
        summary, _ = weather_event_summary(
            derived,
            heat_threshold_c=heat_threshold_c,
            severe_heat_threshold_c=severe_heat_threshold_c,
            frost_threshold_c=frost_threshold_c,
            dry_day_threshold_mm=dry_day_threshold_mm,
            heavy_rain_threshold_mm=heavy_rain_threshold_mm,
            high_vpd_threshold_kpa=high_vpd_threshold_kpa,
        )
        records.append(
            {
                "Season year": anchor_year,
                "Planting date": pd.Timestamp(anchor),
                "Season end": pd.Timestamp(finish),
                "Completeness (%)": completeness,
                **summary,
            }
        )
    return pd.DataFrame(records)


def percentile_rank(values: Sequence[float], target: float) -> float:
    array = pd.to_numeric(pd.Series(values), errors="coerce").dropna().to_numpy(dtype=float)
    if not len(array) or not np.isfinite(target):
        return np.nan
    below = np.sum(array < target)
    equal = np.sum(array == target)
    return float(100.0 * (below + 0.5 * equal) / len(array))


def historical_percentile_comparison(
    season_table: pd.DataFrame,
    target_year: int,
    metrics: Sequence[str] | None = None,
) -> pd.DataFrame:
    if season_table is None or season_table.empty:
        return pd.DataFrame()
    target = season_table.loc[season_table["Season year"].eq(int(target_year))]
    if target.empty:
        return pd.DataFrame()
    if metrics is None:
        metrics = [
            "Total precipitation (mm)",
            "Total GDD",
            "Heat days",
            "Severe heat days",
            "Frost days",
            "Dry days",
            "Longest dry spell (days)",
            "Mean VPD (kPa)",
        ]
    records: list[dict] = []
    for metric in metrics:
        if metric not in season_table:
            continue
        value = pd.to_numeric(target.iloc[0][metric], errors="coerce")
        distribution = pd.to_numeric(season_table[metric], errors="coerce")
        records.append(
            {
                "Metric": metric,
                "Target value": float(value) if pd.notna(value) else np.nan,
                "Historical median": float(distribution.median()),
                "Historical 10th percentile": float(distribution.quantile(0.10)),
                "Historical 90th percentile": float(distribution.quantile(0.90)),
                "Target percentile": percentile_rank(distribution, float(value)) if pd.notna(value) else np.nan,
                "Historical seasons": int(distribution.notna().sum()),
            }
        )
    return pd.DataFrame(records)


def cache_inventory(cache_dir: str | Path) -> pd.DataFrame:
    directory = Path(cache_dir)
    if not directory.exists():
        return pd.DataFrame(columns=["File", "Size (KB)", "Modified UTC"])
    records = []
    for path in sorted(directory.glob("power_daily_*.json.gz")):
        stat = path.stat()
        records.append(
            {
                "File": path.name,
                "Size (KB)": stat.st_size / 1024.0,
                "Modified UTC": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            }
        )
    return pd.DataFrame(records)


def clear_daily_weather_cache(cache_dir: str | Path) -> int:
    directory = Path(cache_dir)
    removed = 0
    if directory.exists():
        for path in directory.glob("power_daily_*.json.gz"):
            try:
                path.unlink()
                removed += 1
            except OSError:
                pass
    return removed


__all__ = [
    "NASA_POWER_DAILY_URL",
    "NASA_POWER_EARLIEST_DATE",
    "POWER_PARAMETER_REGISTRY",
    "DEFAULT_POWER_PARAMETERS",
    "DailyWeatherError",
    "PowerRequestSpec",
    "build_power_daily_url",
    "fetch_nasa_power_daily",
    "parse_power_daily_payload",
    "add_daily_derived_metrics",
    "calculate_daily_gdd",
    "calculate_vpd_kpa",
    "weather_event_summary",
    "stage_duration_profiles",
    "build_duration_stage_schedule",
    "build_gdd_stage_schedule",
    "summarise_stage_exposure",
    "build_historical_season_summary",
    "historical_percentile_comparison",
    "cache_inventory",
    "clear_daily_weather_cache",
]
