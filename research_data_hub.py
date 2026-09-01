"""Research data acquisition and harmonisation for AGROLATTICE 11.4.

The hub reuses AGROLATTICE's established NASA POWER daily client, the installed
country-level 19-variable climate dataset, mapped field coordinates, field
sensors/operations and current EO session outputs.  It deliberately separates
retrieved environmental covariates from measured agronomic outcomes: NASA
weather cannot manufacture pest labels, yield observations or phenotypes.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from daily_weather_phenology import DailyWeatherError, fetch_nasa_power_daily
from soil_water_balance import prepare_daily_weather as prepare_soil_daily_weather

# Kept Streamlit-free so retrieval/model workflows can be tested and reused
# outside the UI. These are the same established NASA POWER -> AGROLATTICE
# mappings used by the Persistent Twin.
TWIN_POWER_PARAMETER_REGISTRY: dict[str, dict[str, str]] = {
    "T2M": {"canonical": "TEMPERATURE"},
    "T2M_MAX": {"canonical": "TEMPERATURE_MAX"},
    "T2M_MIN": {"canonical": "TEMPERATURE_MIN"},
    "RH2M": {"canonical": "RELATIVE_HUMIDITY"},
    "PRECTOTCORR": {"canonical": "PRECIPITATION_AVG"},
    "WS2M": {"canonical": "WIND_SPEED"},
    "ALLSKY_SFC_SW_DWN": {"canonical": "SOLAR_RADIATION"},
    "ALLSKY_SFC_LW_DWN": {"canonical": "LONGWAVE_RADIATION"},
    "PS": {"canonical": "SURFACE_PRESSURE"},
    "ALLSKY_KT": {"canonical": "CLEARNESS_INDEX"},
    "TSOIL1": {"canonical": "SOIL_TEMP_LAYER1"},
    "TSOIL2": {"canonical": "SOIL_TEMP_LAYER2"},
    "EVLAND": {"canonical": "EVAPORATION_LAND"},
    "CLOUD_AMT_DAY": {"canonical": "CLOUD_AMOUNT_DAY"},
    "EVPTRNS": {"canonical": "EVAPOTRANSPIRATION_ENERGY_FLUX"},
}
TWIN_DEFAULT_POWER_PARAMETERS: tuple[str, ...] = tuple(TWIN_POWER_PARAMETER_REGISTRY)
TWIN_CANONICAL_WEATHER_VARIABLES: tuple[str, ...] = (
    "CLEARNESS_INDEX", "CLOUD_AMOUNT_DAY", "EVAPORATION_LAND",
    "EVAPOTRANSPIRATION", "EVAPOTRANSPIRATION_ENERGY_FLUX",
    "LONGWAVE_RADIATION", "PRECIPITATION_AVG", "PRECIPITATION_MAX",
    "PRECIPITATION_MIN", "RELATIVE_HUMIDITY", "SOIL_HEAT_FLUX",
    "SOIL_TEMP_LAYER1", "SOIL_TEMP_LAYER2", "SOLAR_RADIATION",
    "SURFACE_PRESSURE", "TEMPERATURE", "TEMPERATURE_MAX",
    "TEMPERATURE_MIN", "WIND_SPEED",
)
TWIN_CANONICAL_SOURCE_MAP: dict[str, str] = {
    details["canonical"]: code for code, details in TWIN_POWER_PARAMETER_REGISTRY.items()
}
TWIN_CANONICAL_SOURCE_MAP.update({
    "EVAPOTRANSPIRATION": "FAO56_ET0_DERIVED",
    "PRECIPITATION_MIN": "PRECTOTCORR_DAILY_ALIAS",
    "PRECIPITATION_MAX": "PRECTOTCORR_DAILY_ALIAS",
    "SOIL_HEAT_FLUX": "FAO56_DAILY_G_ASSUMPTION",
})

MODULE_VERSION = "1.0.0"
SOURCE_NASA = "NASA POWER Daily Point API"
SOURCE_INSTALLED = "AGROLATTICE installed country agroclimate dataset"


class ResearchDataHubError(RuntimeError):
    pass


@dataclass(frozen=True)
class AcquiredTable:
    frame: pd.DataFrame
    metadata: dict[str, Any]




def _canonicalise_weather(frame: pd.DataFrame, latitude: float) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Map NASA POWER columns onto the established 19-variable AGROLATTICE profile.

    Daily precipitation min/max are compatibility aliases of the daily total;
    real interval extrema are created only by aggregation. Soil heat flux uses
    the transparent FAO-56 daily G=0 convention.
    """
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return pd.DataFrame(), {}
    result = frame.copy()
    date_col = next((c for c in ("DATE", "Date", "date") if c in result.columns), None)
    if not date_col:
        raise ResearchDataHubError("The NASA weather table has no date column.")
    result["DATE"] = pd.to_datetime(result[date_col], errors="coerce").dt.tz_localize(None)
    if date_col != "DATE":
        result = result.drop(columns=[date_col], errors="ignore")
    result = result.dropna(subset=["DATE"]).sort_values("DATE").drop_duplicates("DATE", keep="last")

    for canonical, source in TWIN_CANONICAL_SOURCE_MAP.items():
        if source in result.columns:
            result[canonical] = pd.to_numeric(result[source], errors="coerce")
    if "PRECTOTCORR" in result:
        precipitation = pd.to_numeric(result["PRECTOTCORR"], errors="coerce").clip(lower=0)
        result["PRECIPITATION_AVG"] = precipitation
        result["PRECIPITATION_MIN"] = precipitation
        result["PRECIPITATION_MAX"] = precipitation

    required_eto = {"T2M", "T2M_MAX", "T2M_MIN", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN", "PS", "PRECTOTCORR"}
    eto_status = "Unavailable because one or more FAO-56 weather drivers were missing."
    if required_eto.issubset(result.columns):
        try:
            prepared = prepare_soil_daily_weather(result, float(latitude))
            result["EVAPOTRANSPIRATION"] = pd.to_numeric(prepared["ETo (mm)"], errors="coerce")
            eto_status = "Derived daily FAO-56 reference evapotranspiration (ETo)."
        except Exception as error:
            result["EVAPOTRANSPIRATION"] = np.nan
            eto_status = f"FAO-56 ETo derivation failed: {type(error).__name__}: {error}"
    else:
        result["EVAPOTRANSPIRATION"] = np.nan

    result["SOIL_HEAT_FLUX"] = 0.0
    for variable in TWIN_CANONICAL_WEATHER_VARIABLES:
        if variable not in result.columns:
            result[variable] = np.nan
    provenance = {
        variable: {
            "source": TWIN_CANONICAL_SOURCE_MAP.get(variable),
            "available_rows": int(pd.to_numeric(result[variable], errors="coerce").notna().sum()),
        }
        for variable in TWIN_CANONICAL_WEATHER_VARIABLES
    }
    provenance["EVAPOTRANSPIRATION"]["note"] = eto_status
    provenance["SOIL_HEAT_FLUX"]["note"] = "Daily FAO-56 convention: G=0 MJ m^-2 day^-1; not a direct NASA observation."
    provenance["PRECIPITATION_MIN"]["note"] = "Daily compatibility alias of PRECTOTCORR; interval minima are calculated during aggregation."
    provenance["PRECIPITATION_MAX"]["note"] = "Daily compatibility alias of PRECTOTCORR; interval maxima are calculated during aggregation."
    return result.reset_index(drop=True), provenance


def field_coordinates(field: Mapping[str, Any] | None) -> tuple[float, float]:
    if not field:
        raise ResearchDataHubError("A mapped field is required.")
    try:
        lat = float(field.get("centroid_lat"))
        lon = float(field.get("centroid_lon"))
    except Exception as error:
        raise ResearchDataHubError("The selected field has no valid centroid coordinates.") from error
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ResearchDataHubError("The selected field has invalid centroid coordinates.")
    return lat, lon


def fetch_canonical_nasa_weather(
    *,
    latitude: float,
    longitude: float,
    start_date: date | datetime | str,
    end_date: date | datetime | str,
    cache_dir: str | Path,
    force_refresh: bool = False,
    time_standard: str = "LST",
) -> AcquiredTable:
    """Retrieve the established AGROLATTICE full weather profile from NASA POWER.

    The three historically less reliable optional POWER variables are retried
    independently if the combined request is rejected.  Missing optional
    variables remain missing; they are never fabricated.
    """
    requested = list(TWIN_DEFAULT_POWER_PARAMETERS)
    optional = {"EVLAND", "CLOUD_AMT_DAY", "EVPTRNS"}
    errors: list[dict[str, str]] = []
    frames: list[pd.DataFrame] = []
    chunk_meta: list[dict[str, Any]] = []
    try:
        raw, meta = fetch_nasa_power_daily(
            latitude, longitude, start_date, end_date, cache_dir,
            parameters=requested, time_standard=time_standard,
            force_refresh=force_refresh,
        )
        frames = [raw]
        chunk_meta = [meta]
    except Exception as full_error:
        core = [p for p in requested if p not in optional]
        raw, meta = fetch_nasa_power_daily(
            latitude, longitude, start_date, end_date, cache_dir,
            parameters=core, time_standard=time_standard,
            force_refresh=force_refresh,
        )
        frames = [raw]
        chunk_meta = [meta]
        errors.append({"scope": "full_profile", "error": f"{type(full_error).__name__}: {full_error}"})
        for parameter in sorted(optional):
            try:
                extra, extra_meta = fetch_nasa_power_daily(
                    latitude, longitude, start_date, end_date, cache_dir,
                    parameters=[parameter], time_standard=time_standard,
                    force_refresh=force_refresh,
                )
                frames.append(extra)
                chunk_meta.append(extra_meta)
            except Exception as error:
                errors.append({"scope": parameter, "error": f"{type(error).__name__}: {error}"})

    if not frames:
        raise ResearchDataHubError("NASA POWER returned no usable weather table.")
    merged = frames[0].copy()
    merged["DATE"] = pd.to_datetime(merged["DATE"], errors="coerce")
    merged = merged.set_index("DATE")
    for extra in frames[1:]:
        item = extra.copy()
        item["DATE"] = pd.to_datetime(item["DATE"], errors="coerce")
        item = item.set_index("DATE")
        for column in item.columns:
            if column not in merged:
                merged[column] = item[column]
            else:
                merged[column] = merged[column].combine_first(item[column])
    merged = merged.reset_index().sort_values("DATE").drop_duplicates("DATE", keep="last")
    canonical, provenance = _canonicalise_weather(merged, float(latitude))
    metadata = {
        "source": SOURCE_NASA,
        "latitude": float(latitude),
        "longitude": float(longitude),
        "start_date": str(pd.Timestamp(start_date).date()),
        "end_date": str(pd.Timestamp(end_date).date()),
        "time_standard": time_standard,
        "requested_power_parameters": requested,
        "canonical_variables": list(TWIN_CANONICAL_WEATHER_VARIABLES),
        "canonical_provenance": provenance,
        "request_metadata": chunk_meta,
        "retrieval_warnings": errors,
        "scientific_note": "NASA POWER values are gridded environmental estimates. Derived/compatibility variables retain their provenance and are not local station measurements.",
    }
    return AcquiredTable(canonical, metadata)


def aggregate_daily_weather(frame: pd.DataFrame, frequency: str) -> pd.DataFrame:
    """Aggregate daily weather without silently changing extensive variables."""
    if frame is None or frame.empty:
        return pd.DataFrame()
    frequency_key = str(frequency).strip().casefold()
    if frequency_key.startswith("day"):
        return frame.copy().reset_index(drop=True)
    rule = "W-MON" if frequency_key.startswith("week") else "MS"
    work = frame.copy()
    dcol = next((c for c in ("DATE", "Date", "date") if c in work), None)
    if not dcol:
        raise ResearchDataHubError("Weather aggregation requires a date column.")
    work["DATE"] = pd.to_datetime(work[dcol], errors="coerce")
    work = work.dropna(subset=["DATE"]).set_index("DATE")

    # Precipitation and reference ET are interval totals; most other variables
    # are means. Daily precipitation min/max aliases are replaced by true
    # interval extrema when aggregating.
    sum_columns = {"PRECTOTCORR", "PRECIPITATION_AVG", "EVAPOTRANSPIRATION"}
    max_columns = {"T2M_MAX", "TEMPERATURE_MAX", "PRECIPITATION_MAX"}
    min_columns = {"T2M_MIN", "TEMPERATURE_MIN", "PRECIPITATION_MIN"}
    aggregations: dict[str, str] = {}
    for column in work.columns:
        if not pd.api.types.is_numeric_dtype(work[column]):
            continue
        if column in sum_columns:
            aggregations[column] = "sum"
        elif column in max_columns:
            aggregations[column] = "max"
        elif column in min_columns:
            aggregations[column] = "min"
        else:
            aggregations[column] = "mean"
    result = work.resample(rule).agg(aggregations).reset_index()
    if frequency_key.startswith("week"):
        result["PERIOD_END"] = result["DATE"] + pd.Timedelta(days=6)
        result["Year"] = result["DATE"].dt.year
        result["Week"] = result["DATE"].dt.isocalendar().week.astype(int)
    else:
        result["Year"] = result["DATE"].dt.year
        result["Month"] = result["DATE"].dt.month
    return result


def nasa_pest_covariates(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Create pest-ready covariates that are genuinely available from NASA data.

    Wadhwa & Malik used morning/evening RH, sunshine hours and evaporation. NASA
    POWER's standard daily profile does not provide the same morning/evening RH
    measurements.  Therefore this function does *not* clone RH2M into RH1/RH2.
    It creates only scientifically defensible reduced features plus VPD based on
    mean RH. Models trained on the original paper columns remain incompatible
    unless those exact variables are supplied from a suitable source.
    """
    work = frame.copy()
    aliases = {
        "Tmax": next((c for c in ("TEMPERATURE_MAX", "T2M_MAX") if c in work), None),
        "Tmin": next((c for c in ("TEMPERATURE_MIN", "T2M_MIN") if c in work), None),
        "Tmean": next((c for c in ("TEMPERATURE", "T2M") if c in work), None),
        "RHmean": next((c for c in ("RELATIVE_HUMIDITY", "RH2M") if c in work), None),
        "Rainfall": next((c for c in ("PRECIPITATION_AVG", "PRECTOTCORR") if c in work), None),
        "Wind": next((c for c in ("WIND_SPEED", "WS2M") if c in work), None),
        "Solar": next((c for c in ("SOLAR_RADIATION", "ALLSKY_SFC_SW_DWN") if c in work), None),
        "Evaporation": next((c for c in ("EVAPORATION_LAND", "EVLAND") if c in work), None),
    }
    required = ["Tmax", "Tmin", "RHmean"]
    missing = [key for key in required if not aliases[key]]
    if missing:
        raise ResearchDataHubError("NASA pest covariates require temperature maximum/minimum and mean relative humidity.")
    tmax = pd.to_numeric(work[aliases["Tmax"]], errors="coerce")
    tmin = pd.to_numeric(work[aliases["Tmin"]], errors="coerce")
    rh = pd.to_numeric(work[aliases["RHmean"]], errors="coerce").clip(0, 100)
    tmean = pd.to_numeric(work[aliases["Tmean"]], errors="coerce") if aliases["Tmean"] else (tmax + tmin) / 2.0
    work["Temp_Diff"] = tmax - tmin
    work["Avg_Hum"] = rh
    es = 0.6108 * np.exp((17.27 * tmean) / (tmean + 237.3))
    work["VPD"] = (es * (1 - rh / 100.0)).clip(lower=0)
    # Explicit aliases simplify training with retrieved data without pretending
    # they are source-paper morning/evening observations.
    work["NASA_Tmax"] = tmax
    work["NASA_Tmin"] = tmin
    work["NASA_RHmean"] = rh
    if aliases["Rainfall"]:
        work["NASA_Rainfall"] = pd.to_numeric(work[aliases["Rainfall"]], errors="coerce")
    if aliases["Wind"]:
        work["NASA_Wind"] = pd.to_numeric(work[aliases["Wind"]], errors="coerce")
    if aliases["Solar"]:
        work["NASA_SolarRadiation"] = pd.to_numeric(work[aliases["Solar"]], errors="coerce")
    if aliases["Evaporation"]:
        work["NASA_Evaporation"] = pd.to_numeric(work[aliases["Evaporation"]], errors="coerce")
    meta = {
        "source": SOURCE_NASA,
        "resolved_columns": aliases,
        "engineered_features": {
            "Temp_Diff": "Tmax - Tmin",
            "Avg_Hum": "NASA POWER mean RH2M",
            "VPD": "Magnus saturation vapour pressure from mean temperature and mean RH",
        },
        "compatibility_note": "NASA POWER does not reproduce the source paper's morning/evening RH measurements or sunshine-hours variable. NASA-derived models should be trained and validated on the NASA-compatible feature set rather than silently substituting paper variables.",
    }
    return work, meta


def installed_climate_locations(climate_frame: pd.DataFrame) -> pd.DataFrame:
    if climate_frame is None or climate_frame.empty:
        return pd.DataFrame(columns=["CITY", "STATE", "lat", "lng"])
    cols = [c for c in ("CITY", "STATE", "lat", "lng") if c in climate_frame]
    return climate_frame[cols].drop_duplicates().sort_values([c for c in ("STATE", "CITY") if c in cols]).reset_index(drop=True)


def installed_monthly_climate(
    climate_frame: pd.DataFrame,
    *,
    city: str,
    state: str | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
) -> AcquiredTable:
    if climate_frame is None or climate_frame.empty:
        raise ResearchDataHubError("The selected country has no installed historical climate dataset.")
    work = climate_frame.copy()
    mask = work["CITY"].astype(str).eq(str(city))
    if state is not None and "STATE" in work:
        mask &= work["STATE"].astype(str).eq(str(state))
    work = work.loc[mask]
    if start_year is not None:
        work = work.loc[pd.to_numeric(work["Year"], errors="coerce").ge(int(start_year))]
    if end_year is not None:
        work = work.loc[pd.to_numeric(work["Year"], errors="coerce").le(int(end_year))]
    if work.empty:
        raise ResearchDataHubError("No installed climate rows match this location/year range.")
    id_cols = [c for c in ("CITY", "STATE", "Year", "Month", "lat", "lng") if c in work]
    wide = work.pivot_table(index=id_cols, columns="Variable", values="Value", aggfunc="mean").reset_index()
    wide.columns.name = None
    month_lookup = {name.upper(): index for index, name in enumerate([
        "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"
    ], 1)}
    if "Month" in wide:
        wide["MonthNumber"] = wide["Month"].astype(str).str.upper().map(month_lookup)
        wide["DATE"] = pd.to_datetime(dict(year=pd.to_numeric(wide["Year"], errors="coerce"), month=wide["MonthNumber"], day=1), errors="coerce")
        wide = wide.sort_values("DATE")
    meta = {
        "source": SOURCE_INSTALLED,
        "city": city,
        "state": state,
        "start_year": start_year,
        "end_year": end_year,
        "variables": sorted(set(work["Variable"].astype(str))),
        "temporal_resolution": "monthly",
        "scientific_note": "Installed values retain their original AGROLATTICE/NASA-derived provenance and spatial support; they are not local station measurements unless the source dataset says otherwise.",
    }
    return AcquiredTable(wide.reset_index(drop=True), meta)


def field_record_tables(field_db: Any, field_id: str) -> dict[str, pd.DataFrame]:
    """Retrieve existing AGROLATTICE field records without modifying them."""
    if field_db is None or not field_id:
        return {}
    tables: dict[str, pd.DataFrame] = {}
    for name, method in (
        ("observations", "observations"),
        ("operations", "operations"),
        ("sensors", "sensors"),
        ("sensor_readings", "readings"),
        ("nutrient_samples", "nutrient_samples"),
    ):
        try:
            fn = getattr(field_db, method)
            if method == "readings":
                frame = fn(field_id=field_id)
            else:
                frame = fn(field_id)
            tables[name] = frame if isinstance(frame, pd.DataFrame) else pd.DataFrame()
        except Exception:
            tables[name] = pd.DataFrame()
    try:
        tables["crop_history"] = field_db.frame(
            "SELECT * FROM crop_history WHERE field_id=? ORDER BY season_year", (field_id,)
        )
    except Exception:
        tables["crop_history"] = pd.DataFrame()
    return tables


def merge_weather_with_labels(
    labels: pd.DataFrame,
    weather: pd.DataFrame,
    *,
    label_date_column: str,
    weather_date_column: str = "DATE",
    tolerance_days: int = 3,
) -> pd.DataFrame:
    """As-of merge observed labels with environmental covariates.

    Labels remain the authoritative measured records. Weather is attached to the
    nearest preceding/nearby period within the chosen tolerance.
    """
    if label_date_column not in labels or weather_date_column not in weather:
        raise ResearchDataHubError("Both label and weather date columns are required for merging.")
    left = labels.copy()
    right = weather.copy()
    left["_merge_date"] = pd.to_datetime(left[label_date_column], errors="coerce")
    right["_merge_date"] = pd.to_datetime(right[weather_date_column], errors="coerce")
    left = left.dropna(subset=["_merge_date"]).sort_values("_merge_date")
    right = right.dropna(subset=["_merge_date"]).sort_values("_merge_date")
    right = right.drop(columns=[weather_date_column], errors="ignore")
    merged = pd.merge_asof(
        left, right, on="_merge_date", direction="nearest",
        tolerance=pd.Timedelta(days=max(0, int(tolerance_days))), suffixes=("", "_weather"),
    )
    return merged.rename(columns={"_merge_date": "MatchedDate"})


def table_profile(frame: pd.DataFrame) -> dict[str, Any]:
    if frame is None:
        return {"rows": 0, "columns": 0}
    return {
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "date_min": _date_extreme(frame, "min"),
        "date_max": _date_extreme(frame, "max"),
        "missing_percent": float(frame.isna().mean().mean() * 100) if frame.size else 0.0,
    }


def _date_extreme(frame: pd.DataFrame, which: str) -> str | None:
    for column in ("DATE", "Date", "date", "timestamp", "observed_at", "operation_date"):
        if column in frame:
            values = pd.to_datetime(frame[column], errors="coerce").dropna()
            if not values.empty:
                value = values.min() if which == "min" else values.max()
                return value.isoformat()
    return None
