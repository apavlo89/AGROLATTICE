"""AquaCrop integration helpers.

The executable simulation backend is AquaCrop-OSPy, an independent Python
implementation based on AquaCrop-OS. It is not the official FAO AquaCrop 7.x
stand-alone executable. The module keeps that distinction explicit and exports
all weather and configuration inputs used for each run.
"""
from __future__ import annotations

import importlib
import io
import json
import platform
import sys
import time
import traceback
import uuid
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

MODULE_VERSION = "1.0.0"


class AquaCropIntegrationError(RuntimeError):
    """Raised when simulation preparation or execution fails."""


AQUACROP_CROP_CANDIDATES: dict[str, list[str]] = {
    "Maize": ["Maize"],
    "Wheat": ["Wheat"],
    "Beans": ["DryBean", "Bean"],
    "Sorghum": ["Sorghum"],
    "Tomato": ["Tomato"],
    "Barley": ["Barley"],
    "Sugarcane": ["SugarCane", "Sugarcane"],
    "Coffee": [],
    "Avocado": [],
    "Agave": [],
    "Citrus": [],
}

SOIL_TYPE_OPTIONS = [
    "Sand",
    "LoamySand",
    "SandyLoam",
    "Loam",
    "SiltLoam",
    "Silt",
    "SandyClayLoam",
    "ClayLoam",
    "SiltyClayLoam",
    "SandyClay",
    "SiltyClay",
    "Clay",
]

IRRIGATION_METHODS = {
    "Rainfed": 0,
    "Soil-moisture targets": 1,
    "Fixed interval": 2,
    "Uploaded schedule": 3,
    "Net irrigation": 4,
    "Constant depth": 5,
}


def dependency_status() -> dict[str, Any]:
    status: dict[str, Any] = {
        "installed": False,
        "package": "aquacrop",
        "version": None,
        "python": platform.python_version(),
        "message": "AquaCrop-OSPy is not installed.",
        "official_fao_backend": False,
    }
    try:
        package = importlib.import_module("aquacrop")
        status["installed"] = True
        status["version"] = getattr(package, "__version__", None)
        status["message"] = "AquaCrop-OSPy is available."
    except Exception as error:
        status["error"] = f"{type(error).__name__}: {error}"
    return status


def _numeric_series(frame: pd.DataFrame, candidates: Sequence[str]) -> pd.Series:
    for candidate in candidates:
        if candidate in frame.columns:
            return pd.to_numeric(frame[candidate], errors="coerce")
    return pd.Series(np.nan, index=frame.index, dtype=float)


def prepare_weather(
    weather: pd.DataFrame,
    *,
    latitude: float | None = None,
    eto_calculator: Any | None = None,
) -> pd.DataFrame:
    """Convert AGROLATTICE daily weather evidence into AquaCrop-OSPy's weather structure."""
    if not isinstance(weather, pd.DataFrame) or weather.empty:
        raise AquaCropIntegrationError("Daily weather is empty.")
    frame = weather.copy()
    date_series = frame["DATE"] if "DATE" in frame.columns else frame.get("Date")
    if date_series is None:
        raise AquaCropIntegrationError("Daily weather requires a DATE column.")
    frame["Date"] = pd.to_datetime(date_series, errors="coerce")
    frame["MinTemp"] = _numeric_series(frame, ["T2M_MIN", "TEMPERATURE_MIN", "TMIN_C", "MinTemp"])
    frame["MaxTemp"] = _numeric_series(frame, ["T2M_MAX", "TEMPERATURE_MAX", "TMAX_C", "MaxTemp"])
    frame["Precipitation"] = _numeric_series(
        frame, ["PRECTOTCORR", "PRECIPITATION_AVG", "PRECIP_MM", "Precipitation (mm)", "Precipitation"]
    ).clip(lower=0)
    reference_et = _numeric_series(frame, ["ReferenceET", "EVAPOTRANSPIRATION", "ETo (mm)", "ETO_MM", "ETo"])
    if reference_et.isna().all() and eto_calculator is not None:
        if latitude is None:
            raise AquaCropIntegrationError("Latitude is required to calculate reference ET.")
        reference_et = pd.to_numeric(eto_calculator(frame, float(latitude)), errors="coerce")
    frame["ReferenceET"] = reference_et.clip(lower=0.1)
    output = frame[["Date", "MinTemp", "MaxTemp", "Precipitation", "ReferenceET"]].copy()
    output = output.dropna(subset=["Date"]).sort_values("Date").drop_duplicates("Date", keep="last")
    output = output.dropna(subset=["MinTemp", "MaxTemp", "Precipitation", "ReferenceET"])
    if output.empty:
        raise AquaCropIntegrationError("No complete daily rows remain after AquaCrop weather preparation.")
    output.insert(0, "Day", output["Date"].dt.day)
    output.insert(1, "Month", output["Date"].dt.month)
    output.insert(2, "Year", output["Date"].dt.year)
    return output[["Day", "Month", "Year", "MinTemp", "MaxTemp", "Precipitation", "ReferenceET", "Date"]]


def weather_text(weather: pd.DataFrame) -> str:
    required = ["Day", "Month", "Year", "MinTemp", "MaxTemp", "Precipitation", "ReferenceET"]
    missing = [column for column in required if column not in weather.columns]
    if missing:
        raise AquaCropIntegrationError("AquaCrop weather is missing: " + ", ".join(missing))
    return weather[required].to_csv(sep=" ", index=False, float_format="%.4f")


def resolve_crop_name(app_crop: str, requested: str | None = None) -> str:
    candidates = []
    if requested:
        candidates.append(str(requested))
    candidates.extend(AQUACROP_CROP_CANDIDATES.get(str(app_crop), []))
    if not candidates:
        raise AquaCropIntegrationError(
            f"No built-in AquaCrop-OSPy crop mapping is registered for {app_crop}. "
            "Use a supported crop or supply a calibrated custom AquaCrop crop file outside this integration."
        )
    return candidates[0]


def _load_backend() -> dict[str, Any]:
    try:
        module = importlib.import_module("aquacrop")
        return {
            "module": module,
            "AquaCropModel": getattr(module, "AquaCropModel"),
            "Soil": getattr(module, "Soil"),
            "Crop": getattr(module, "Crop"),
            "InitialWaterContent": getattr(module, "InitialWaterContent"),
            "IrrigationManagement": getattr(module, "IrrigationManagement"),
        }
    except Exception as error:
        raise AquaCropIntegrationError(
            "AquaCrop-OSPy is not available. Run INSTALL_AQUACROP_OSPY.bat and restart the app. "
            f"Original error: {type(error).__name__}: {error}"
        ) from error


def build_irrigation_management(
    backend: Mapping[str, Any],
    *,
    method_name: str,
    application_efficiency_percent: float = 75.0,
    maximum_daily_irrigation_mm: float = 25.0,
    soil_moisture_targets: Sequence[float] = (70, 70, 70, 70),
    interval_days: int = 7,
    schedule: pd.DataFrame | None = None,
    net_irrigation_target_percent: float = 70.0,
    constant_depth_mm: float = 20.0,
) -> Any:
    cls = backend["IrrigationManagement"]
    method = IRRIGATION_METHODS.get(method_name)
    if method is None:
        raise AquaCropIntegrationError(f"Unsupported irrigation method: {method_name}")
    kwargs: dict[str, Any] = {
        "irrigation_method": int(method),
        "AppEff": float(application_efficiency_percent),
        "MaxIrr": float(maximum_daily_irrigation_mm),
    }
    if method == 1:
        kwargs["SMT"] = [float(value) for value in soil_moisture_targets]
    elif method == 2:
        kwargs["IrrInterval"] = int(interval_days)
    elif method == 3:
        if schedule is None or schedule.empty:
            raise AquaCropIntegrationError("Uploaded-schedule irrigation requires a non-empty schedule.")
        schedule_frame = schedule.copy()
        date_column = next((c for c in schedule_frame.columns if str(c).casefold() == "date"), None)
        depth_column = next(
            (c for c in schedule_frame.columns if "depth" in str(c).casefold() or "irrig" in str(c).casefold()),
            None,
        )
        if date_column is None or depth_column is None:
            raise AquaCropIntegrationError("Irrigation schedule requires Date and Depth columns.")
        kwargs["Schedule"] = pd.DataFrame(
            {
                "Date": pd.to_datetime(schedule_frame[date_column], errors="coerce"),
                "Depth": pd.to_numeric(schedule_frame[depth_column], errors="coerce"),
            }
        ).dropna()
    elif method == 4:
        kwargs["NetIrrSMT"] = float(net_irrigation_target_percent)
    elif method == 5:
        kwargs["depth"] = float(constant_depth_mm)
    try:
        return cls(**kwargs)
    except TypeError:
        # Older versions may not accept AppEff/MaxIrr for every method.
        fallback = {"irrigation_method": int(method)}
        for key in ("SMT", "IrrInterval", "Schedule", "NetIrrSMT", "depth"):
            if key in kwargs:
                fallback[key] = kwargs[key]
        return cls(**fallback)


def _extract_output(model: Any, method_names: Sequence[str]) -> pd.DataFrame | None:
    for method_name in method_names:
        method = getattr(model, method_name, None)
        if callable(method):
            try:
                value = method()
                if isinstance(value, pd.DataFrame):
                    return value.copy()
            except Exception:
                continue
    outputs = getattr(model, "_outputs", None)
    if outputs is not None:
        for attribute in method_names:
            value = getattr(outputs, attribute.replace("get_", ""), None)
            if isinstance(value, pd.DataFrame):
                return value.copy()
    return None


def run_aquacrop_ospy(
    *,
    weather: pd.DataFrame,
    simulation_start: str,
    simulation_end: str,
    app_crop: str,
    planting_date: str,
    soil_type: str,
    initial_water_content: str = "FC",
    irrigation_method: str = "Rainfed",
    irrigation_options: Mapping[str, Any] | None = None,
    crop_name: str | None = None,
) -> dict[str, Any]:
    backend = _load_backend()
    crop_resolved = resolve_crop_name(app_crop, crop_name)
    weather_model = weather.copy()
    if "Date" not in weather_model.columns:
        raise AquaCropIntegrationError("Prepared AquaCrop weather requires Date.")
    weather_model = weather_model[["MinTemp", "MaxTemp", "Precipitation", "ReferenceET", "Date"]].copy()
    weather_model["Date"] = pd.to_datetime(weather_model["Date"], errors="coerce")
    options = dict(irrigation_options or {})
    irrigation = build_irrigation_management(
        backend,
        method_name=irrigation_method,
        application_efficiency_percent=float(options.get("application_efficiency_percent", 75.0)),
        maximum_daily_irrigation_mm=float(options.get("maximum_daily_irrigation_mm", 25.0)),
        soil_moisture_targets=options.get("soil_moisture_targets", [70, 70, 70, 70]),
        interval_days=int(options.get("interval_days", 7)),
        schedule=options.get("schedule"),
        net_irrigation_target_percent=float(options.get("net_irrigation_target_percent", 70.0)),
        constant_depth_mm=float(options.get("constant_depth_mm", 20.0)),
    )
    try:
        soil = backend["Soil"](soil_type=str(soil_type))
    except TypeError:
        soil = backend["Soil"](str(soil_type))
    crop = backend["Crop"](crop_resolved, planting_date=pd.Timestamp(planting_date).strftime("%m/%d"))
    initial = backend["InitialWaterContent"](value=[str(initial_water_content)])
    model = backend["AquaCropModel"](
        sim_start_time=pd.Timestamp(simulation_start).strftime("%Y/%m/%d"),
        sim_end_time=pd.Timestamp(simulation_end).strftime("%Y/%m/%d"),
        weather_df=weather_model,
        soil=soil,
        crop=crop,
        initial_water_content=initial,
        irrigation_management=irrigation,
    )
    started = time.time()
    model.run_model(till_termination=True)
    runtime = time.time() - started
    final_stats = _extract_output(model, ["get_simulation_results", "final_stats"])
    water_flux = _extract_output(model, ["get_water_flux", "water_flux"])
    water_storage = _extract_output(model, ["get_water_storage", "water_storage"])
    crop_growth = _extract_output(model, ["get_crop_growth", "crop_growth"])
    if final_stats is None:
        raise AquaCropIntegrationError("AquaCrop completed but no simulation-results table was exposed.")
    return {
        "run_id": str(uuid.uuid4()),
        "timestamp": pd.Timestamp.utcnow().isoformat(),
        "backend": "AquaCrop-OSPy",
        "backend_version": dependency_status().get("version"),
        "official_fao_backend": False,
        "crop": crop_resolved,
        "soil_type": soil_type,
        "planting_date": str(planting_date),
        "simulation_start": str(simulation_start),
        "simulation_end": str(simulation_end),
        "irrigation_method": irrigation_method,
        "runtime_seconds": runtime,
        "final_stats": final_stats,
        "water_flux": water_flux,
        "water_storage": water_storage,
        "crop_growth": crop_growth,
    }


def run_export_bytes(run: Mapping[str, Any], weather: pd.DataFrame, configuration: Mapping[str, Any]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("aquacrop_weather.txt", weather_text(weather))
        archive.writestr("configuration.json", json.dumps(configuration, indent=2, default=str))
        archive.writestr(
            "run_metadata.json",
            json.dumps(
                {k: v for k, v in run.items() if not isinstance(v, pd.DataFrame)},
                indent=2,
                default=str,
            ),
        )
        for key in ("final_stats", "water_flux", "water_storage", "crop_growth"):
            value = run.get(key)
            if isinstance(value, pd.DataFrame):
                archive.writestr(f"{key}.csv", value.to_csv(index=False))
        archive.writestr(
            "README.txt",
            "Simulation generated with AquaCrop-OSPy, an independent implementation based on AquaCrop-OS. "
            "It is not the official FAO AquaCrop 7.x executable.\n",
        )
    return buffer.getvalue()


def preparation_export_bytes(weather: pd.DataFrame, configuration: Mapping[str, Any]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("aquacrop_weather.txt", weather_text(weather))
        archive.writestr("simulation_configuration.json", json.dumps(configuration, indent=2, default=str))
        archive.writestr(
            "README.txt",
            "This package contains harmonised daily weather and transparent configuration metadata. "
            "It is not a complete official FAO AquaCrop project file because official crop, soil and management "
            "files must be selected or calibrated in AquaCrop.\n",
        )
    return buffer.getvalue()
