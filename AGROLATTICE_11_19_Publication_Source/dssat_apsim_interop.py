"""DSSAT and APSIM interoperability for the AgroLattice Research Tool.

The module deliberately avoids rewriting fixed-format DSSAT experiment records.
It creates weather/run packages, executes user-supplied prepared simulations, and
parses common outputs. APSIM configuration uses its documented command language.
"""
from __future__ import annotations

import io
import json
import os
import re
import shutil
import sqlite3
import subprocess
import tempfile
import time
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

MODULE_VERSION = "1.0.0"


class InteroperabilityError(RuntimeError):
    """Raised when an external-model workflow cannot be completed safely."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _column(frame: pd.DataFrame, candidates: Sequence[str]) -> pd.Series:
    lookup = {str(c).casefold(): c for c in frame.columns}
    for candidate in candidates:
        if candidate.casefold() in lookup:
            return frame[lookup[candidate.casefold()]]
    return pd.Series(np.nan, index=frame.index)


def prepare_daily_weather(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalise AGROLATTICE persisted/session or uploaded daily weather for model export."""
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise InteroperabilityError("Daily weather data are empty.")
    output = pd.DataFrame()
    output["Date"] = pd.to_datetime(_column(frame, ["DATE", "Date", "date"]), errors="coerce")
    output["Tmin"] = pd.to_numeric(_column(frame, ["T2M_MIN", "TEMPERATURE_MIN", "MinTemp", "TMIN", "Minimum temperature"]), errors="coerce")
    output["Tmax"] = pd.to_numeric(_column(frame, ["T2M_MAX", "TEMPERATURE_MAX", "MaxTemp", "TMAX", "Maximum temperature"]), errors="coerce")
    output["Rain"] = pd.to_numeric(_column(frame, ["PRECTOTCORR", "PRECIPITATION_AVG", "Precipitation", "RAIN", "Rain"]), errors="coerce")
    output["Solar"] = pd.to_numeric(_column(frame, ["ALLSKY_SFC_SW_DWN", "SOLAR_RADIATION", "Solar", "SRAD", "Radn"]), errors="coerce")
    output["ETo"] = pd.to_numeric(_column(frame, ["ETO", "ETo", "ReferenceET", "EVAPOTRANSPIRATION"]), errors="coerce")
    output = output.dropna(subset=["Date", "Tmin", "Tmax", "Rain", "Solar"]).sort_values("Date").drop_duplicates("Date")
    if output.empty:
        raise InteroperabilityError("No complete Date/Tmin/Tmax/Rain/Solar rows remain.")
    output["Rain"] = output["Rain"].clip(lower=0)
    output["Solar"] = output["Solar"].clip(lower=0)
    output["Year"] = output["Date"].dt.year.astype(int)
    output["Day"] = output["Date"].dt.dayofyear.astype(int)
    return output.reset_index(drop=True)


def _climate_constants(weather: pd.DataFrame) -> tuple[float, float]:
    daily_mean = (weather["Tmax"] + weather["Tmin"]) / 2
    tav = float(daily_mean.mean())
    monthly = weather.assign(Month=weather["Date"].dt.month).groupby("Month")[["Tmax", "Tmin"]].mean()
    monthly_mean = monthly.mean(axis=1)
    amp = float((monthly_mean.max() - monthly_mean.min()) / 2) if len(monthly_mean) > 1 else 0.0
    return tav, amp


def dssat_weather_text(
    frame: pd.DataFrame,
    *,
    station_code: str,
    station_name: str,
    latitude: float,
    longitude: float,
    elevation_m: float = 0.0,
) -> str:
    weather = prepare_daily_weather(frame)
    code = re.sub(r"[^A-Za-z0-9]", "", station_code.upper())[:4].ljust(4, "X")
    tav, amp = _climate_constants(weather)
    lines = [
        f"*WEATHER DATA : {station_name}",
        "",
        "@ INSI      LAT     LONG  ELEV   TAV   AMP REFHT WNDHT",
        f"  {code:<4} {latitude:8.3f} {longitude:8.3f} {elevation_m:5.0f} {tav:5.1f} {amp:5.1f}  2.00  2.00",
        "@DATE  SRAD  TMAX  TMIN  RAIN",
    ]
    for row in weather.itertuples(index=False):
        date_code = f"{int(row.Year):04d}{int(row.Day):03d}"
        lines.append(f"{date_code:>7} {float(row.Solar):5.1f} {float(row.Tmax):5.1f} {float(row.Tmin):5.1f} {float(row.Rain):5.1f}")
    return "\n".join(lines) + "\n"


def apsim_met_text(
    frame: pd.DataFrame,
    *,
    site_name: str,
    latitude: float,
    longitude: float,
) -> str:
    weather = prepare_daily_weather(frame)
    tav, amp = _climate_constants(weather)
    lines = [
        "[weather.met.weather]",
        f"! site = {site_name}",
        f"latitude = {latitude:.5f} (DECIMAL DEGREES)",
        f"longitude = {longitude:.5f} (DECIMAL DEGREES)",
        f"tav = {tav:.3f} (oC)",
        f"amp = {amp:.3f} (oC)",
        "year day radn maxt mint rain",
        "() () (MJ/m2/day) (oC) (oC) (mm)",
    ]
    for row in weather.itertuples(index=False):
        lines.append(f"{int(row.Year):4d} {int(row.Day):3d} {float(row.Solar):8.3f} {float(row.Tmax):7.3f} {float(row.Tmin):7.3f} {float(row.Rain):7.3f}")
    return "\n".join(lines) + "\n"


def apsim_command_text(
    *,
    base_apsimx: str,
    output_apsimx: str,
    weather_filename: str,
    start_date: str,
    end_date: str,
    weather_selector: str = "[Weather]",
    clock_selector: str = "[Clock]",
) -> str:
    return "\n".join([
        f"load {base_apsimx}",
        f"{weather_selector}.FileName={weather_filename}",
        f"{clock_selector}.Start={start_date}",
        f"{clock_selector}.End={end_date}",
        f"save {output_apsimx}",
        "run",
        "",
    ])


def common_executable_candidates() -> dict[str, list[str]]:
    candidates: dict[str, list[str]] = {"DSSAT": [], "APSIM": []}
    for root in [Path("C:/DSSAT48"), Path("C:/DSSAT485"), Path("C:/DSSAT")]:
        for name in ["DSCSM048.EXE", "DSCSM048.exe", "DSCSM047.EXE"]:
            candidates["DSSAT"].append(str(root / name))
    program_files = [Path(os.environ.get("ProgramFiles", "C:/Program Files")), Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"))]
    for root in program_files:
        if root.exists():
            for path in root.glob("APSIM*/bin/Models.exe"):
                candidates["APSIM"].append(str(path))
    return candidates


def executable_status(path: str | Path | None, model: str) -> dict[str, Any]:
    value = Path(path) if path else None
    return {
        "model": model,
        "path": str(value) if value else None,
        "exists": bool(value and value.exists()),
        "is_file": bool(value and value.is_file()),
    }


def safe_extract_zip(data: bytes, destination: str | Path) -> Path:
    target = Path(destination)
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for member in archive.infolist():
            resolved = (target / member.filename).resolve()
            if target.resolve() not in resolved.parents and resolved != target.resolve():
                raise InteroperabilityError("ZIP archive contains an unsafe path.")
        archive.extractall(target)
    return target


def run_external_model(
    command: Sequence[str],
    *,
    working_directory: str | Path,
    timeout_seconds: int = 900,
) -> dict[str, Any]:
    cwd = Path(working_directory)
    if not cwd.exists():
        raise InteroperabilityError(f"Working directory does not exist: {cwd}")
    started = time.time()
    try:
        result = subprocess.run(
            [str(value) for value in command],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=max(30, int(timeout_seconds)),
            shell=False,
        )
    except subprocess.TimeoutExpired as error:
        raise InteroperabilityError(f"External model exceeded the {timeout_seconds}-second timeout.") from error
    return {
        "command": [str(value) for value in command],
        "working_directory": str(cwd),
        "return_code": int(result.returncode),
        "stdout": result.stdout,
        "stderr": result.stderr,
        "runtime_seconds": float(time.time() - started),
        "completed_utc": utc_now_iso(),
    }


def run_dssat(
    *,
    executable: str | Path,
    crop_module: str,
    batch_filename: str,
    working_directory: str | Path,
    external_control_filename: str | None = None,
    timeout_seconds: int = 900,
) -> dict[str, Any]:
    exe = Path(executable)
    if not exe.exists():
        raise InteroperabilityError(f"DSSAT executable not found: {exe}")
    command = [str(exe), str(crop_module), "B", str(batch_filename)]
    if external_control_filename:
        command.append(str(external_control_filename))
    return run_external_model(command, working_directory=working_directory, timeout_seconds=timeout_seconds)


def run_apsim(
    *,
    models_executable: str | Path,
    working_directory: str | Path,
    apsimx_filename: str | None = None,
    command_filename: str | None = None,
    export_csv: bool = True,
    timeout_seconds: int = 900,
) -> dict[str, Any]:
    exe = Path(models_executable)
    if not exe.exists():
        raise InteroperabilityError(f"APSIM Models executable not found: {exe}")
    if command_filename:
        command = [str(exe), "--apply", str(command_filename)]
    elif apsimx_filename:
        command = [str(exe), str(apsimx_filename)]
        if export_csv:
            command.append("--csv")
    else:
        raise InteroperabilityError("Provide an APSIMX filename or command filename.")
    return run_external_model(command, working_directory=working_directory, timeout_seconds=timeout_seconds)


def parse_apsim_database(path: str | Path) -> dict[str, pd.DataFrame]:
    database = Path(path)
    if not database.exists():
        raise InteroperabilityError(f"APSIM database not found: {database}")
    tables: dict[str, pd.DataFrame] = {}
    with sqlite3.connect(database) as connection:
        names = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name", connection)["name"].tolist()
        for name in names:
            if str(name).startswith("_"):
                continue
            try:
                tables[str(name)] = pd.read_sql_query(f'SELECT * FROM "{name}"', connection)
            except Exception:
                continue
    return tables


def parse_output_directory(directory: str | Path, model: str) -> dict[str, Any]:
    root = Path(directory)
    output: dict[str, Any] = {"model": model, "files": [], "tables": {}}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        output["files"].append({"name": str(path.relative_to(root)), "size": path.stat().st_size})
        suffix = path.suffix.casefold()
        try:
            if suffix == ".csv":
                output["tables"][str(path.relative_to(root))] = pd.read_csv(path)
            elif suffix == ".db" and model.upper() == "APSIM":
                for name, frame in parse_apsim_database(path).items():
                    output["tables"][f"{path.name}:{name}"] = frame
        except Exception:
            continue
    return output


def interoperability_package(
    *,
    model: str,
    weather_filename: str,
    weather_text: str,
    metadata: Mapping[str, Any],
    base_files: Mapping[str, bytes] | None = None,
    command_files: Mapping[str, str] | None = None,
) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(weather_filename, weather_text)
        archive.writestr("metadata.json", json.dumps(dict(metadata), indent=2, default=str))
        for name, data in (base_files or {}).items():
            archive.writestr(name, data)
        for name, text in (command_files or {}).items():
            archive.writestr(name, text)
        archive.writestr("README.txt", f"{model} interoperability package generated by AgroLattice. Review model-specific crop, cultivar, soil and management inputs before execution.\n")
    return buffer.getvalue()


def run_export_package(run: Mapping[str, Any], parsed: Mapping[str, Any] | None = None) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("run_metadata.json", json.dumps(dict(run), indent=2, default=str))
        if parsed:
            archive.writestr("output_inventory.json", json.dumps(parsed.get("files", []), indent=2, default=str))
            for name, frame in (parsed.get("tables", {}) or {}).items():
                if isinstance(frame, pd.DataFrame):
                    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", name)[:120]
                    archive.writestr(f"tables/{safe}.csv", frame.to_csv(index=False))
    return buffer.getvalue()
