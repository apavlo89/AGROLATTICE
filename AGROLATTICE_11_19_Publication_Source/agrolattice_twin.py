"""AgroLattice Twin: live field digital twin and adaptive experiment copilot.

This module orchestrates existing weather, root-zone, satellite, field-operations,
and maize flowering-trial data into transparent current-state summaries,
scenario simulations, inspection priorities, and next-season design suggestions.

The twin deliberately distinguishes observed values, model-derived estimates, and
heuristic fallbacks. It does not autonomously control machinery or replace field
inspection, agronomic judgement, or independent model validation.
"""
from __future__ import annotations

import io
import json
import math
import sqlite3
import uuid
import zipfile
from contextlib import closing
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import folium
from branca.colormap import LinearColormap
from folium.plugins import Fullscreen, MeasureControl
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from streamlit_folium import st_folium

from daily_weather_phenology import (
    DEFAULT_POWER_PARAMETERS,
    POWER_PARAMETER_REGISTRY,
    fetch_nasa_power_daily,
)
from soil_water_balance import (
    CROP_ROOT_DEFAULTS,
    SOIL_PRESETS,
    IrrigationStrategy,
    SoilProfile,
    assign_stage_parameters,
    available_water_profiles,
    build_stage_schedule as build_soil_stage_schedule,
    crop_root_defaults,
    prepare_daily_weather as prepare_soil_daily_weather,
    simulate_root_zone_balance,
    soil_profile_from_preset,
    summarise_by_stage as summarise_root_zone_by_stage,
    summarise_season as summarise_root_zone_season,
    whole_season_ky as root_zone_whole_season_ky,
)

from maize_pollination_lab import (
    build_model_table,
    compute_plot_synchrony_metrics,
    prepare_weather,
    treatment_summary,
    experiment_plot_geometries,
)
from maize_mechanistic_twin import (
    DEFAULT_PHYSIOLOGY,
    PUBLICATION_DOI as MECHANISTIC_MAIZE_DOI,
    MechanisticMaizeError,
    PhysiologyParameters,
    calibrate_parent_physiology,
    event_date as mechanistic_event_date,
    optimise_male_sowing_strategy,
    parameter_thermal_targets,
    physiology_from_mapping,
    simulate_event_uncertainty,
    simulate_mfs,
)
from satellite_crop_monitoring import (
    DEFAULT_EXCLUDED_SCL,
    INDEX_REGISTRY as SATELLITE_INDEX_REGISTRY,
    SatelliteSearchConfig,
    dependency_status as satellite_dependency_status,
    geometry_centroid,
    geometry_hash,
    process_scene_collection,
    scene_catalog_table,
    scene_provider,
    search_sentinel2_scenes,
    select_scene_subset,
    validate_aoi_geometry,
)

MODULE_VERSION = "3.0.0"
DB_SCHEMA_VERSION = "3.0.0"

# Release 10.7 keeps the original seven-variable daily-weather client available
# elsewhere in the application but gives the Twin the full AgroLattice climate
# profile. Fifteen values are requested directly from NASA POWER. Four additional
# canonical columns are derived or compatibility aliases, with their provenance
# recorded explicitly in the attachment metadata.
TWIN_POWER_PARAMETER_REGISTRY: dict[str, dict[str, str]] = {
    "T2M": {"label": "Mean temperature at 2 m", "unit": "°C", "canonical": "TEMPERATURE"},
    "T2M_MAX": {"label": "Maximum temperature at 2 m", "unit": "°C", "canonical": "TEMPERATURE_MAX"},
    "T2M_MIN": {"label": "Minimum temperature at 2 m", "unit": "°C", "canonical": "TEMPERATURE_MIN"},
    "RH2M": {"label": "Relative humidity at 2 m", "unit": "%", "canonical": "RELATIVE_HUMIDITY"},
    "PRECTOTCORR": {"label": "Corrected precipitation", "unit": "mm day⁻¹", "canonical": "PRECIPITATION_AVG"},
    "WS2M": {"label": "Wind speed at 2 m", "unit": "m s⁻¹", "canonical": "WIND_SPEED"},
    "ALLSKY_SFC_SW_DWN": {"label": "All-sky shortwave radiation", "unit": "MJ m⁻² day⁻¹", "canonical": "SOLAR_RADIATION"},
    "ALLSKY_SFC_LW_DWN": {"label": "All-sky longwave radiation", "unit": "MJ m⁻² day⁻¹", "canonical": "LONGWAVE_RADIATION"},
    "PS": {"label": "Surface pressure", "unit": "kPa", "canonical": "SURFACE_PRESSURE"},
    "ALLSKY_KT": {"label": "All-sky clearness index", "unit": "ratio", "canonical": "CLEARNESS_INDEX"},
    "TSOIL1": {"label": "Soil temperature layer 1", "unit": "°C", "canonical": "SOIL_TEMP_LAYER1"},
    "TSOIL2": {"label": "Soil temperature layer 2", "unit": "°C", "canonical": "SOIL_TEMP_LAYER2"},
    "EVLAND": {"label": "Land-surface evaporation", "unit": "kg m⁻² s⁻¹ or provider unit", "canonical": "EVAPORATION_LAND"},
    "CLOUD_AMT_DAY": {"label": "Daytime cloud amount", "unit": "%", "canonical": "CLOUD_AMOUNT_DAY"},
    "EVPTRNS": {"label": "Evapotranspiration energy flux", "unit": "W m⁻² or provider unit", "canonical": "EVAPOTRANSPIRATION_ENERGY_FLUX"},
}
TWIN_DEFAULT_POWER_PARAMETERS: tuple[str, ...] = tuple(TWIN_POWER_PARAMETER_REGISTRY)
TWIN_OPTIONAL_POWER_PARAMETERS: tuple[str, ...] = ("EVLAND", "CLOUD_AMT_DAY", "EVPTRNS")
TWIN_CORE_POWER_PARAMETERS: tuple[str, ...] = tuple(
    code for code in TWIN_DEFAULT_POWER_PARAMETERS if code not in TWIN_OPTIONAL_POWER_PARAMETERS
)
TWIN_CANONICAL_WEATHER_VARIABLES: tuple[str, ...] = (
    "CLEARNESS_INDEX",
    "CLOUD_AMOUNT_DAY",
    "EVAPORATION_LAND",
    "EVAPOTRANSPIRATION",
    "EVAPOTRANSPIRATION_ENERGY_FLUX",
    "LONGWAVE_RADIATION",
    "PRECIPITATION_AVG",
    "PRECIPITATION_MAX",
    "PRECIPITATION_MIN",
    "RELATIVE_HUMIDITY",
    "SOIL_HEAT_FLUX",
    "SOIL_TEMP_LAYER1",
    "SOIL_TEMP_LAYER2",
    "SOLAR_RADIATION",
    "SURFACE_PRESSURE",
    "TEMPERATURE",
    "TEMPERATURE_MAX",
    "TEMPERATURE_MIN",
    "WIND_SPEED",
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


class AgroLatticeTwinError(RuntimeError):
    """Raised when a digital-twin operation cannot be completed safely."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str, separators=(",", ":"))


def _loads(value: str | None, default: Any = None) -> Any:
    if value in (None, ""):
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def _to_timestamp(value: Any) -> pd.Timestamp | pd.NaT:
    return pd.to_datetime(value, errors="coerce")


def _num(value: Any, default: float = np.nan) -> float:
    result = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return float(result) if pd.notna(result) else float(default)


def _first_column(frame: pd.DataFrame | None, candidates: Sequence[str]) -> str | None:
    if not isinstance(frame, pd.DataFrame):
        return None
    lookup = {str(column).strip().casefold(): str(column) for column in frame.columns}
    for candidate in candidates:
        if candidate.casefold() in lookup:
            return lookup[candidate.casefold()]
    return None


def _dated_subset(frame: pd.DataFrame | None, as_of: Any, candidates: Sequence[str]) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return pd.DataFrame()
    column = _first_column(frame, candidates)
    if not column:
        return frame.copy()
    result = frame.copy()
    # Normalise both timezone-aware sensor timestamps and timezone-naive agronomic dates
    # to a common naive UTC timeline before filtering.
    result["__date"] = pd.to_datetime(result[column], errors="coerce", utc=True).dt.tz_localize(None)
    cutoff = pd.Timestamp(as_of).tz_localize(None) if pd.Timestamp(as_of).tzinfo is not None else pd.Timestamp(as_of)
    cutoff = cutoff.normalize() + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    return result.loc[result["__date"].notna() & result["__date"].le(cutoff)].sort_values("__date")


def _freshness_days(frame: pd.DataFrame | None, as_of: Any, candidates: Sequence[str]) -> float:
    subset = _dated_subset(frame, as_of, candidates)
    if subset.empty or "__date" not in subset:
        return np.nan
    return max(0.0, (pd.Timestamp(as_of).normalize() - subset["__date"].max().normalize()).days)


def _quality_label(score: float) -> str:
    if not np.isfinite(score):
        return "Unavailable"
    if score >= 80:
        return "High"
    if score >= 55:
        return "Moderate"
    return "Low"


@dataclass
class AgroLatticeTwinDatabase:
    path: Path

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialise()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def initialise(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY, value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS twin_links (
            link_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            field_id TEXT,
            trial_id TEXT,
            notes TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(field_id, trial_id)
        );
        CREATE TABLE IF NOT EXISTS twin_settings (
            link_id TEXT PRIMARY KEY,
            male_target_gdd REAL,
            female_target_gdd REAL,
            inspection_window_days INTEGER NOT NULL DEFAULT 7,
            stale_observation_days INTEGER NOT NULL DEFAULT 3,
            target_seed_set_percent REAL,
            uncertainty_alert_percent REAL NOT NULL DEFAULT 60,
            allow_heuristic_fallback INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(link_id) REFERENCES twin_links(link_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS snapshots (
            snapshot_id TEXT PRIMARY KEY,
            link_id TEXT NOT NULL,
            as_of TEXT NOT NULL,
            state_json TEXT NOT NULL,
            plot_states_json TEXT,
            input_manifest_json TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(link_id) REFERENCES twin_links(link_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS scenarios (
            scenario_id TEXT PRIMARY KEY,
            link_id TEXT NOT NULL,
            name TEXT NOT NULL,
            settings_json TEXT NOT NULL,
            results_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(link_id) REFERENCES twin_links(link_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS recommendations (
            recommendation_id TEXT PRIMARY KEY,
            link_id TEXT NOT NULL,
            generated_at TEXT NOT NULL,
            recommendation_type TEXT NOT NULL,
            priority TEXT NOT NULL,
            plot_id TEXT,
            title TEXT NOT NULL,
            rationale TEXT,
            status TEXT NOT NULL DEFAULT 'Open',
            details_json TEXT,
            FOREIGN KEY(link_id) REFERENCES twin_links(link_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS model_registry (
            model_id TEXT PRIMARY KEY,
            link_id TEXT NOT NULL,
            target TEXT NOT NULL,
            algorithm TEXT NOT NULL,
            training_rows INTEGER NOT NULL,
            metrics_json TEXT,
            feature_names_json TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(link_id) REFERENCES twin_links(link_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS twin_weather (
            link_id TEXT PRIMARY KEY,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            time_standard TEXT NOT NULL,
            parameters_json TEXT NOT NULL,
            data_json TEXT NOT NULL,
            metadata_json TEXT,
            request_json TEXT,
            source TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(link_id) REFERENCES twin_links(link_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS twin_satellite (
            link_id TEXT PRIMARY KEY,
            geometry_hash TEXT NOT NULL,
            geometry_json TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            indices_json TEXT NOT NULL,
            catalog_json TEXT,
            data_json TEXT NOT NULL,
            metadata_json TEXT,
            request_json TEXT,
            source TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(link_id) REFERENCES twin_links(link_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS twin_root_zone (
            link_id TEXT PRIMARY KEY,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            crop TEXT NOT NULL,
            profile TEXT,
            weather_updated_at TEXT,
            settings_json TEXT NOT NULL,
            data_json TEXT NOT NULL,
            stage_summary_json TEXT,
            season_summary_json TEXT,
            schedule_json TEXT,
            metadata_json TEXT,
            source TEXT NOT NULL,
            generated_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(link_id) REFERENCES twin_links(link_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS twin_events (
            event_id TEXT PRIMARY KEY,
            link_id TEXT NOT NULL,
            event_time TEXT NOT NULL,
            event_type TEXT NOT NULL,
            title TEXT NOT NULL,
            source TEXT,
            details_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            FOREIGN KEY(link_id) REFERENCES twin_links(link_id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_twin_events_link_time ON twin_events(link_id,event_time);
        CREATE TABLE IF NOT EXISTS calibration_runs (
            calibration_id TEXT PRIMARY KEY,
            link_id TEXT NOT NULL,
            parent_name TEXT NOT NULL,
            role TEXT NOT NULL,
            prior_json TEXT NOT NULL,
            fitted_json TEXT NOT NULL,
            diagnostics_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            FOREIGN KEY(link_id) REFERENCES twin_links(link_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS analogue_seasons (
            analogue_id TEXT PRIMARY KEY,
            link_id TEXT NOT NULL,
            name TEXT NOT NULL,
            source TEXT,
            settings_json TEXT NOT NULL DEFAULT '{}',
            data_json TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            FOREIGN KEY(link_id) REFERENCES twin_links(link_id) ON DELETE CASCADE
        );
        """
        with closing(self.connect()) as connection:
            connection.executescript(schema)
            connection.execute(
                "INSERT OR REPLACE INTO metadata(key,value) VALUES(?,?)",
                ("schema_version", DB_SCHEMA_VERSION),
            )
            connection.commit()

    def save_link(self, *, name: str, field_id: str | None, trial_id: str | None, notes: str = "") -> str:
        if not field_id and not trial_id:
            raise AgroLatticeTwinError("Select at least one mapped field or maize trial.")
        now = utc_now()
        with closing(self.connect()) as connection:
            row = connection.execute(
                "SELECT link_id FROM twin_links WHERE field_id IS ? AND trial_id IS ?",
                (field_id, trial_id),
            ).fetchone()
            link_id = str(row["link_id"]) if row else uuid.uuid4().hex
            connection.execute(
                """
                INSERT INTO twin_links(link_id,name,field_id,trial_id,notes,active,created_at,updated_at)
                VALUES(?,?,?,?,?,1,?,?)
                ON CONFLICT(link_id) DO UPDATE SET
                    name=excluded.name, field_id=excluded.field_id, trial_id=excluded.trial_id,
                    notes=excluded.notes, active=1, updated_at=excluded.updated_at
                """,
                (link_id, str(name).strip(), field_id, trial_id, str(notes), now, now),
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO twin_settings(
                    link_id,male_target_gdd,female_target_gdd,inspection_window_days,
                    stale_observation_days,target_seed_set_percent,uncertainty_alert_percent,
                    allow_heuristic_fallback,updated_at
                ) VALUES(?,?,?,7,3,90,60,1,?)
                """,
                (link_id, None, None, now),
            )
            connection.commit()
        return link_id

    def links(self) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            return pd.read_sql_query(
                "SELECT * FROM twin_links WHERE active=1 ORDER BY updated_at DESC, name",
                connection,
            )

    def link(self, link_id: str) -> dict[str, Any] | None:
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT * FROM twin_links WHERE link_id=?", (link_id,)).fetchone()
        return dict(row) if row else None

    def storage_counts(self, link_id: str) -> dict[str, int]:
        """Return the records owned by a Twin link."""
        with closing(self.connect()) as connection:
            return {
                "Settings": int(connection.execute("SELECT COUNT(*) FROM twin_settings WHERE link_id=?", (link_id,)).fetchone()[0]),
                "Saved snapshots": int(connection.execute("SELECT COUNT(*) FROM snapshots WHERE link_id=?", (link_id,)).fetchone()[0]),
                "Saved scenarios": int(connection.execute("SELECT COUNT(*) FROM scenarios WHERE link_id=?", (link_id,)).fetchone()[0]),
                "Recommendations": int(connection.execute("SELECT COUNT(*) FROM recommendations WHERE link_id=?", (link_id,)).fetchone()[0]),
                "Registered models": int(connection.execute("SELECT COUNT(*) FROM model_registry WHERE link_id=?", (link_id,)).fetchone()[0]),
                "Attached weather dataset": int(connection.execute("SELECT COUNT(*) FROM twin_weather WHERE link_id=?", (link_id,)).fetchone()[0]),
                "Attached satellite dataset": int(connection.execute("SELECT COUNT(*) FROM twin_satellite WHERE link_id=?", (link_id,)).fetchone()[0]),
                "Attached root-zone dataset": int(connection.execute("SELECT COUNT(*) FROM twin_root_zone WHERE link_id=?", (link_id,)).fetchone()[0]),
                "Twin timeline events": int(connection.execute("SELECT COUNT(*) FROM twin_events WHERE link_id=?", (link_id,)).fetchone()[0]),
                "Calibration audit runs": int(connection.execute("SELECT COUNT(*) FROM calibration_runs WHERE link_id=?", (link_id,)).fetchone()[0]),
                "Saved analogue seasons": int(connection.execute("SELECT COUNT(*) FROM analogue_seasons WHERE link_id=?", (link_id,)).fetchone()[0]),
            }

    def log_event(
        self,
        link_id: str,
        *,
        event_type: str,
        title: str,
        event_time: Any | None = None,
        source: str = "AGROLATTICE Twin",
        details: Mapping[str, Any] | None = None,
    ) -> str:
        event_id = uuid.uuid4().hex
        timestamp = pd.Timestamp(event_time if event_time is not None else utc_now())
        event_value = timestamp.isoformat()
        with closing(self.connect()) as connection:
            connection.execute(
                "INSERT INTO twin_events(event_id,link_id,event_time,event_type,title,source,details_json,created_at) VALUES(?,?,?,?,?,?,?,?)",
                (event_id, link_id, event_value, str(event_type), str(title), str(source or ""), _json(details or {}), utc_now()),
            )
            connection.commit()
        return event_id

    def events(self, link_id: str, *, limit: int = 2000) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            return pd.read_sql_query(
                "SELECT * FROM twin_events WHERE link_id=? ORDER BY event_time DESC,created_at DESC LIMIT ?",
                connection, params=(link_id, int(limit)),
            )

    def save_calibration_run(
        self,
        link_id: str,
        *,
        parent_name: str,
        role: str,
        prior: Mapping[str, Any],
        fitted: Mapping[str, Any],
        diagnostics: Mapping[str, Any] | None = None,
    ) -> str:
        calibration_id = uuid.uuid4().hex
        now = utc_now()
        with closing(self.connect()) as connection:
            connection.execute(
                "INSERT INTO calibration_runs(calibration_id,link_id,parent_name,role,prior_json,fitted_json,diagnostics_json,created_at) VALUES(?,?,?,?,?,?,?,?)",
                (calibration_id, link_id, str(parent_name), str(role), _json(prior), _json(fitted), _json(diagnostics or {}), now),
            )
            connection.commit()
        self.log_event(
            link_id, event_type="Calibration", title=f"{role} physiology calibrated: {parent_name}",
            event_time=now, source="Mechanistic Maize Twin", details={"calibration_id": calibration_id, **dict(diagnostics or {})},
        )
        return calibration_id

    def calibration_runs(self, link_id: str) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            return pd.read_sql_query(
                "SELECT * FROM calibration_runs WHERE link_id=? ORDER BY created_at DESC", connection, params=(link_id,),
            )

    def save_analogue_season(
        self, link_id: str, *, name: str, source: str = "", settings: Mapping[str, Any] | None = None, data: Any = None
    ) -> str:
        analogue_id = uuid.uuid4().hex
        now = utc_now()
        payload = data.to_dict(orient="records") if isinstance(data, pd.DataFrame) else (data or [])
        with closing(self.connect()) as connection:
            connection.execute(
                "INSERT INTO analogue_seasons(analogue_id,link_id,name,source,settings_json,data_json,created_at) VALUES(?,?,?,?,?,?,?)",
                (analogue_id, link_id, str(name), str(source or ""), _json(settings or {}), _json(payload), now),
            )
            connection.commit()
        self.log_event(link_id, event_type="Evidence", title=f"Climate analogue saved: {name}", event_time=now, source=source or "Climate analogue", details={"analogue_id": analogue_id})
        return analogue_id

    def analogue_seasons(self, link_id: str) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            return pd.read_sql_query(
                "SELECT * FROM analogue_seasons WHERE link_id=? ORDER BY created_at DESC", connection, params=(link_id,),
            )

    def delete_link(self, link_id: str) -> dict[str, int]:
        """Permanently delete a Twin and all records owned by it."""
        link = self.link(link_id)
        if not link:
            raise AgroLatticeTwinError("The selected AgroLattice Twin no longer exists.")
        counts = self.storage_counts(link_id)
        with closing(self.connect()) as connection:
            connection.execute("DELETE FROM twin_links WHERE link_id=?", (link_id,))
            connection.commit()
        return counts

    def clear_link_records(self, link_id: str, categories: Sequence[str]) -> dict[str, int]:
        """Clear selected saved Twin outputs while retaining the Twin link and calibration."""
        allowed = {
            "snapshots": "snapshots",
            "scenarios": "scenarios",
            "recommendations": "recommendations",
            "models": "model_registry",
            "weather": "twin_weather",
            "satellite": "twin_satellite",
            "root_zone": "twin_root_zone",
            "events": "twin_events",
            "calibrations": "calibration_runs",
            "analogues": "analogue_seasons",
        }
        removed: dict[str, int] = {}
        with closing(self.connect()) as connection:
            for category in categories:
                table = allowed.get(str(category))
                if not table:
                    continue
                count = int(connection.execute(f"SELECT COUNT(*) FROM {table} WHERE link_id=?", (link_id,)).fetchone()[0])
                connection.execute(f"DELETE FROM {table} WHERE link_id=?", (link_id,))
                removed[category] = count
            connection.commit()
        return removed

    def settings(self, link_id: str) -> dict[str, Any]:
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT * FROM twin_settings WHERE link_id=?", (link_id,)).fetchone()
        return dict(row) if row else {
            "link_id": link_id,
            "male_target_gdd": None,
            "female_target_gdd": None,
            "inspection_window_days": 7,
            "stale_observation_days": 3,
            "target_seed_set_percent": 90.0,
            "uncertainty_alert_percent": 60.0,
            "allow_heuristic_fallback": 1,
        }

    def save_settings(self, link_id: str, values: Mapping[str, Any]) -> None:
        now = utc_now()
        with closing(self.connect()) as connection:
            connection.execute(
                """
                INSERT INTO twin_settings(
                    link_id,male_target_gdd,female_target_gdd,inspection_window_days,
                    stale_observation_days,target_seed_set_percent,uncertainty_alert_percent,
                    allow_heuristic_fallback,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?)
                ON CONFLICT(link_id) DO UPDATE SET
                    male_target_gdd=excluded.male_target_gdd,
                    female_target_gdd=excluded.female_target_gdd,
                    inspection_window_days=excluded.inspection_window_days,
                    stale_observation_days=excluded.stale_observation_days,
                    target_seed_set_percent=excluded.target_seed_set_percent,
                    uncertainty_alert_percent=excluded.uncertainty_alert_percent,
                    allow_heuristic_fallback=excluded.allow_heuristic_fallback,
                    updated_at=excluded.updated_at
                """,
                (
                    link_id,
                    values.get("male_target_gdd"),
                    values.get("female_target_gdd"),
                    int(values.get("inspection_window_days", 7)),
                    int(values.get("stale_observation_days", 3)),
                    values.get("target_seed_set_percent"),
                    float(values.get("uncertainty_alert_percent", 60)),
                    int(bool(values.get("allow_heuristic_fallback", True))),
                    now,
                ),
            )
            connection.commit()

    def weather_record(self, link_id: str) -> dict[str, Any] | None:
        """Return metadata for the weather dataset persistently attached to a Twin."""
        with closing(self.connect()) as connection:
            row = connection.execute(
                "SELECT link_id,latitude,longitude,start_date,end_date,time_standard,parameters_json,metadata_json,request_json,source,fetched_at,updated_at FROM twin_weather WHERE link_id=?",
                (link_id,),
            ).fetchone()
        if not row:
            return None
        record = dict(row)
        record["parameters"] = _loads(record.pop("parameters_json", None), [])
        record["metadata"] = _loads(record.pop("metadata_json", None), {})
        record["request"] = _loads(record.pop("request_json", None), {})
        return record

    def weather(self, link_id: str) -> pd.DataFrame:
        """Load the current persistent daily-weather table for a Twin."""
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT data_json FROM twin_weather WHERE link_id=?", (link_id,)).fetchone()
        if not row or not row["data_json"]:
            return pd.DataFrame()
        try:
            frame = pd.read_json(io.StringIO(str(row["data_json"])), orient="table")
        except Exception:
            try:
                frame = pd.read_json(io.StringIO(str(row["data_json"])))
            except Exception:
                return pd.DataFrame()
        date_col = _first_column(frame, ["DATE", "Date", "date"])
        if not date_col:
            return pd.DataFrame()
        frame["DATE"] = pd.to_datetime(frame[date_col], errors="coerce").dt.tz_localize(None)
        if date_col != "DATE":
            frame = frame.drop(columns=[date_col], errors="ignore")
        return frame.dropna(subset=["DATE"]).sort_values("DATE").drop_duplicates("DATE", keep="last").reset_index(drop=True)

    def save_weather(
        self,
        link_id: str,
        frame: pd.DataFrame,
        *,
        latitude: float,
        longitude: float,
        parameters: Sequence[str],
        time_standard: str,
        metadata: Mapping[str, Any] | None = None,
        request: Mapping[str, Any] | None = None,
        source: str = "NASA POWER Daily Point API",
        merge: bool = True,
    ) -> dict[str, Any]:
        """Persist, merge and attach daily weather to a Twin.

        New non-missing values replace matching dates while older columns and values are
        retained. Set merge=False when the field location changed and the previous series
        should be replaced rather than combined.
        """
        if not self.link(link_id):
            raise AgroLatticeTwinError("The selected AgroLattice Twin no longer exists.")
        if not isinstance(frame, pd.DataFrame) or frame.empty:
            raise AgroLatticeTwinError("No daily weather rows were supplied.")
        incoming = frame.copy()
        date_col = _first_column(incoming, ["DATE", "Date", "date"])
        if not date_col:
            raise AgroLatticeTwinError("The weather table does not contain a date column.")
        incoming["DATE"] = pd.to_datetime(incoming[date_col], errors="coerce").dt.tz_localize(None)
        if date_col != "DATE":
            incoming = incoming.drop(columns=[date_col], errors="ignore")
        incoming = incoming.dropna(subset=["DATE"]).sort_values("DATE").drop_duplicates("DATE", keep="last")
        if incoming.empty:
            raise AgroLatticeTwinError("The weather table did not contain any valid dates.")

        existing_record = self.weather_record(link_id) if merge else None
        existing = self.weather(link_id) if merge else pd.DataFrame()
        if not existing.empty:
            old = existing.set_index("DATE")
            new = incoming.set_index("DATE")
            combined = new.combine_first(old).sort_index().reset_index()
        else:
            combined = incoming.reset_index(drop=True)
        combined = combined.sort_values("DATE").drop_duplicates("DATE", keep="last").reset_index(drop=True)
        start_date = pd.to_datetime(combined["DATE"], errors="coerce").min().date().isoformat()
        end_date = pd.to_datetime(combined["DATE"], errors="coerce").max().date().isoformat()
        now = utc_now()
        chunk_downloads = [
            item.get("downloaded_utc")
            for item in (metadata or {}).get("chunks", [])
            if isinstance(item, Mapping) and item.get("downloaded_utc")
        ]
        fetched_at = str((metadata or {}).get("downloaded_utc") or (chunk_downloads[-1] if chunk_downloads else now))
        parameter_union = list(dict.fromkeys([
            *list((existing_record or {}).get("parameters") or []),
            *(str(parameter) for parameter in parameters),
        ]))
        with closing(self.connect()) as connection:
            connection.execute(
                """
                INSERT INTO twin_weather(
                    link_id,latitude,longitude,start_date,end_date,time_standard,
                    parameters_json,data_json,metadata_json,request_json,source,fetched_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(link_id) DO UPDATE SET
                    latitude=excluded.latitude, longitude=excluded.longitude,
                    start_date=excluded.start_date, end_date=excluded.end_date,
                    time_standard=excluded.time_standard, parameters_json=excluded.parameters_json,
                    data_json=excluded.data_json, metadata_json=excluded.metadata_json,
                    request_json=excluded.request_json, source=excluded.source,
                    fetched_at=excluded.fetched_at, updated_at=excluded.updated_at
                """,
                (
                    link_id, float(latitude), float(longitude), start_date, end_date,
                    str(time_standard).upper(), _json(parameter_union),
                    combined.to_json(orient="table", date_format="iso"), _json(dict(metadata or {})),
                    _json(dict(request or {})), str(source), fetched_at, now,
                ),
            )
            connection.commit()
        return {
            "rows": int(len(combined)),
            "start_date": start_date,
            "end_date": end_date,
            "latitude": float(latitude),
            "longitude": float(longitude),
            "updated_at": now,
        }

    def clear_weather(self, link_id: str) -> int:
        """Remove the weather dataset attached to a Twin while retaining the Twin itself."""
        with closing(self.connect()) as connection:
            count = int(connection.execute("SELECT COUNT(*) FROM twin_weather WHERE link_id=?", (link_id,)).fetchone()[0])
            connection.execute("DELETE FROM twin_weather WHERE link_id=?", (link_id,))
            connection.commit()
        return count


    def satellite_record(self, link_id: str) -> dict[str, Any] | None:
        """Return metadata for the Sentinel-2 time series attached to a Twin."""
        with closing(self.connect()) as connection:
            row = connection.execute(
                """
                SELECT link_id,geometry_hash,geometry_json,start_date,end_date,indices_json,
                       metadata_json,request_json,source,fetched_at,updated_at
                FROM twin_satellite WHERE link_id=?
                """,
                (link_id,),
            ).fetchone()
        if not row:
            return None
        record = dict(row)
        record["geometry"] = _loads(record.pop("geometry_json", None), {})
        record["indices"] = _loads(record.pop("indices_json", None), [])
        record["metadata"] = _loads(record.pop("metadata_json", None), {})
        record["request"] = _loads(record.pop("request_json", None), {})
        return record

    @staticmethod
    def _read_frame_json(value: str | None) -> pd.DataFrame:
        if not value:
            return pd.DataFrame()
        try:
            return pd.read_json(io.StringIO(str(value)), orient="table")
        except Exception:
            try:
                return pd.read_json(io.StringIO(str(value)))
            except Exception:
                return pd.DataFrame()

    def satellite(self, link_id: str) -> pd.DataFrame:
        """Load the persistent Sentinel-2 field-index time series for a Twin."""
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT data_json FROM twin_satellite WHERE link_id=?", (link_id,)).fetchone()
        frame = self._read_frame_json(row["data_json"] if row else None)
        if frame.empty:
            return frame
        date_col = _first_column(frame, ["Date", "Acquisition UTC", "date"])
        if date_col:
            frame["Date"] = pd.to_datetime(frame[date_col], errors="coerce", utc=True).dt.tz_localize(None)
            if date_col != "Date":
                frame = frame.drop(columns=[date_col], errors="ignore")
        scene_col = _first_column(frame, ["Scene ID", "scene_id"])
        if scene_col and scene_col != "Scene ID":
            frame = frame.rename(columns={scene_col: "Scene ID"})
        if "Date" in frame:
            frame = frame.sort_values("Date", na_position="last")
        if "Scene ID" in frame:
            frame = frame.drop_duplicates("Scene ID", keep="last")
        return frame.reset_index(drop=True)

    def satellite_catalog(self, link_id: str) -> pd.DataFrame:
        """Load the searchable Sentinel-2 catalogue provenance attached to a Twin."""
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT catalog_json FROM twin_satellite WHERE link_id=?", (link_id,)).fetchone()
        frame = self._read_frame_json(row["catalog_json"] if row else None)
        if frame.empty:
            return frame
        date_col = _first_column(frame, ["Date", "Acquisition UTC", "date"])
        if date_col:
            frame["Date"] = pd.to_datetime(frame[date_col], errors="coerce", utc=True).dt.tz_localize(None)
            if date_col != "Date":
                frame = frame.drop(columns=[date_col], errors="ignore")
        if "Scene ID" in frame:
            frame = frame.drop_duplicates("Scene ID", keep="last")
        if "Date" in frame:
            frame = frame.sort_values("Date", na_position="last")
        return frame.reset_index(drop=True)

    @staticmethod
    def _normalise_satellite_frame(frame: pd.DataFrame) -> pd.DataFrame:
        result = frame.copy()
        date_col = _first_column(result, ["Date", "Acquisition UTC", "date"])
        if not date_col:
            raise AgroLatticeTwinError("The satellite table does not contain an acquisition date.")
        result["Date"] = pd.to_datetime(result[date_col], errors="coerce", utc=True).dt.tz_localize(None)
        if date_col != "Date":
            result = result.drop(columns=[date_col], errors="ignore")
        scene_col = _first_column(result, ["Scene ID", "scene_id"])
        if scene_col and scene_col != "Scene ID":
            result = result.rename(columns={scene_col: "Scene ID"})
        if "Scene ID" not in result:
            result["Scene ID"] = result["Date"].dt.strftime("scene-%Y%m%dT%H%M%S")
        missing_scene = result["Scene ID"].isna() | result["Scene ID"].astype(str).str.strip().eq("")
        if missing_scene.any():
            result.loc[missing_scene, "Scene ID"] = (
                result.loc[missing_scene, "Date"].dt.strftime("scene-%Y%m%dT%H%M%S")
                + "-"
                + result.loc[missing_scene].index.astype(str)
            )
        return (
            result.dropna(subset=["Date"])
            .sort_values(["Date", "Scene ID"], na_position="last")
            .drop_duplicates("Scene ID", keep="last")
            .reset_index(drop=True)
        )

    @staticmethod
    def _merge_scene_frames(existing: pd.DataFrame, incoming: pd.DataFrame) -> pd.DataFrame:
        if existing.empty:
            return incoming.reset_index(drop=True)
        old = existing.set_index("Scene ID")
        new = incoming.set_index("Scene ID")
        combined = new.combine_first(old).reset_index()
        return (
            combined.sort_values(["Date", "Scene ID"], na_position="last")
            .drop_duplicates("Scene ID", keep="last")
            .reset_index(drop=True)
        )

    def save_satellite(
        self,
        link_id: str,
        frame: pd.DataFrame,
        *,
        geometry: Mapping[str, Any],
        indices: Sequence[str],
        catalog: pd.DataFrame | None = None,
        metadata: Mapping[str, Any] | None = None,
        request: Mapping[str, Any] | None = None,
        source: str = "Sentinel-2 Level-2A public STAC catalogues",
        merge: bool = True,
    ) -> dict[str, Any]:
        """Persist and merge processed Sentinel-2 field observations for one Twin.

        Scene IDs are the merge key. New non-missing values replace matching scene
        values while previously calculated index columns remain available. A geometry
        mismatch is never merged silently; select replacement after editing a boundary.
        """
        if not self.link(link_id):
            raise AgroLatticeTwinError("The selected AgroLattice Twin no longer exists.")
        if not isinstance(frame, pd.DataFrame) or frame.empty:
            raise AgroLatticeTwinError("No processed Sentinel-2 observations were supplied.")
        valid_geometry = validate_aoi_geometry(geometry)
        current_hash = geometry_hash(valid_geometry)
        existing_record = self.satellite_record(link_id) if merge else None
        if existing_record and existing_record.get("geometry_hash") != current_hash:
            raise AgroLatticeTwinError(
                "The stored satellite series belongs to a different field boundary. "
                "Select Replace stored series before attaching imagery for the edited geometry."
            )
        incoming = self._normalise_satellite_frame(frame)
        if incoming.empty:
            raise AgroLatticeTwinError("The processed satellite table contains no valid acquisition dates.")
        existing = self.satellite(link_id) if merge else pd.DataFrame()
        combined = self._merge_scene_frames(existing, incoming) if not existing.empty else incoming

        incoming_catalog = pd.DataFrame()
        if isinstance(catalog, pd.DataFrame) and not catalog.empty:
            incoming_catalog = self._normalise_satellite_frame(catalog)
        existing_catalog = self.satellite_catalog(link_id) if merge else pd.DataFrame()
        if not incoming_catalog.empty and not existing_catalog.empty:
            combined_catalog = self._merge_scene_frames(existing_catalog, incoming_catalog)
        elif not incoming_catalog.empty:
            combined_catalog = incoming_catalog
        else:
            combined_catalog = existing_catalog

        start_date = pd.to_datetime(combined["Date"], errors="coerce").min().date().isoformat()
        end_date = pd.to_datetime(combined["Date"], errors="coerce").max().date().isoformat()
        index_union = list(dict.fromkeys([
            *list((existing_record or {}).get("indices") or []),
            *(str(name) for name in indices),
        ]))
        now = utc_now()
        fetched_at = str((metadata or {}).get("fetched_at") or (metadata or {}).get("generated_utc") or now)
        with closing(self.connect()) as connection:
            connection.execute(
                """
                INSERT INTO twin_satellite(
                    link_id,geometry_hash,geometry_json,start_date,end_date,indices_json,
                    catalog_json,data_json,metadata_json,request_json,source,fetched_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(link_id) DO UPDATE SET
                    geometry_hash=excluded.geometry_hash, geometry_json=excluded.geometry_json,
                    start_date=excluded.start_date, end_date=excluded.end_date,
                    indices_json=excluded.indices_json, catalog_json=excluded.catalog_json,
                    data_json=excluded.data_json, metadata_json=excluded.metadata_json,
                    request_json=excluded.request_json, source=excluded.source,
                    fetched_at=excluded.fetched_at, updated_at=excluded.updated_at
                """,
                (
                    link_id, current_hash, _json(valid_geometry), start_date, end_date,
                    _json(index_union),
                    combined_catalog.to_json(orient="table", date_format="iso") if not combined_catalog.empty else None,
                    combined.to_json(orient="table", date_format="iso"),
                    _json(dict(metadata or {})), _json(dict(request or {})),
                    str(source), fetched_at, now,
                ),
            )
            connection.commit()
        usable = combined
        if "Status" in usable:
            usable = usable.loc[usable["Status"].astype(str).str.casefold().eq("usable")]
        return {
            "rows": int(len(combined)),
            "usable_rows": int(len(usable)),
            "start_date": start_date,
            "end_date": end_date,
            "geometry_hash": current_hash,
            "updated_at": now,
        }

    def clear_satellite(self, link_id: str) -> int:
        """Remove only the persistent Sentinel-2 attachment owned by a Twin."""
        with closing(self.connect()) as connection:
            count = int(connection.execute("SELECT COUNT(*) FROM twin_satellite WHERE link_id=?", (link_id,)).fetchone()[0])
            connection.execute("DELETE FROM twin_satellite WHERE link_id=?", (link_id,))
            connection.commit()
        return count

    def root_zone_record(self, link_id: str) -> dict[str, Any] | None:
        """Return metadata and settings for the root-zone series attached to a Twin."""
        with closing(self.connect()) as connection:
            row = connection.execute(
                """
                SELECT link_id,start_date,end_date,crop,profile,weather_updated_at,
                       settings_json,season_summary_json,metadata_json,source,
                       generated_at,updated_at
                FROM twin_root_zone WHERE link_id=?
                """,
                (link_id,),
            ).fetchone()
        if not row:
            return None
        record = dict(row)
        record["settings"] = _loads(record.pop("settings_json", None), {})
        record["season_summary"] = _loads(record.pop("season_summary_json", None), {})
        record["metadata"] = _loads(record.pop("metadata_json", None), {})
        return record

    def root_zone(self, link_id: str) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT data_json FROM twin_root_zone WHERE link_id=?", (link_id,)).fetchone()
        frame = self._read_frame_json(row["data_json"] if row else None)
        if frame.empty:
            return frame
        date_col = _first_column(frame, ["Date", "DATE", "date"])
        if date_col:
            frame["Date"] = pd.to_datetime(frame[date_col], errors="coerce").dt.tz_localize(None)
            if date_col != "Date":
                frame = frame.drop(columns=[date_col], errors="ignore")
        return frame.dropna(subset=["Date"]).sort_values("Date").drop_duplicates("Date", keep="last").reset_index(drop=True)

    def root_zone_stage_summary(self, link_id: str) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT stage_summary_json FROM twin_root_zone WHERE link_id=?", (link_id,)).fetchone()
        return self._read_frame_json(row["stage_summary_json"] if row else None)

    def root_zone_schedule(self, link_id: str) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT schedule_json FROM twin_root_zone WHERE link_id=?", (link_id,)).fetchone()
        return self._read_frame_json(row["schedule_json"] if row else None)

    def save_root_zone(
        self,
        link_id: str,
        balance: pd.DataFrame,
        *,
        stage_summary: pd.DataFrame | None,
        season_summary: Mapping[str, Any] | None,
        schedule: pd.DataFrame | None,
        crop: str,
        profile: str | None,
        settings: Mapping[str, Any],
        metadata: Mapping[str, Any] | None,
        weather_updated_at: str | None,
        source: str = "FAO-56 single-layer root-zone balance",
    ) -> dict[str, Any]:
        if not self.link(link_id):
            raise AgroLatticeTwinError("The selected AgroLattice Twin no longer exists.")
        if not isinstance(balance, pd.DataFrame) or balance.empty:
            raise AgroLatticeTwinError("No root-zone balance rows were supplied.")
        frame = balance.copy()
        date_col = _first_column(frame, ["Date", "DATE", "date"])
        if not date_col:
            raise AgroLatticeTwinError("The root-zone table does not contain a date column.")
        frame["Date"] = pd.to_datetime(frame[date_col], errors="coerce").dt.tz_localize(None)
        if date_col != "Date":
            frame = frame.drop(columns=[date_col], errors="ignore")
        frame = frame.dropna(subset=["Date"]).sort_values("Date").drop_duplicates("Date", keep="last")
        if frame.empty:
            raise AgroLatticeTwinError("The root-zone table contains no valid dates.")
        start_date = frame["Date"].min().date().isoformat()
        end_date = frame["Date"].max().date().isoformat()
        now = utc_now()
        with closing(self.connect()) as connection:
            connection.execute(
                """
                INSERT INTO twin_root_zone(
                    link_id,start_date,end_date,crop,profile,weather_updated_at,
                    settings_json,data_json,stage_summary_json,season_summary_json,
                    schedule_json,metadata_json,source,generated_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(link_id) DO UPDATE SET
                    start_date=excluded.start_date,end_date=excluded.end_date,
                    crop=excluded.crop,profile=excluded.profile,
                    weather_updated_at=excluded.weather_updated_at,
                    settings_json=excluded.settings_json,data_json=excluded.data_json,
                    stage_summary_json=excluded.stage_summary_json,
                    season_summary_json=excluded.season_summary_json,
                    schedule_json=excluded.schedule_json,metadata_json=excluded.metadata_json,
                    source=excluded.source,generated_at=excluded.generated_at,
                    updated_at=excluded.updated_at
                """,
                (
                    link_id,start_date,end_date,str(crop),str(profile or ""),weather_updated_at,
                    _json(dict(settings)),frame.to_json(orient="table",date_format="iso"),
                    stage_summary.to_json(orient="table",date_format="iso") if isinstance(stage_summary,pd.DataFrame) and not stage_summary.empty else None,
                    _json(dict(season_summary or {})),
                    schedule.to_json(orient="table",date_format="iso") if isinstance(schedule,pd.DataFrame) and not schedule.empty else None,
                    _json(dict(metadata or {})),str(source),now,now,
                ),
            )
            connection.commit()
        return {"rows": int(len(frame)), "start_date": start_date, "end_date": end_date, "updated_at": now}

    def clear_root_zone(self, link_id: str) -> int:
        with closing(self.connect()) as connection:
            count = int(connection.execute("SELECT COUNT(*) FROM twin_root_zone WHERE link_id=?", (link_id,)).fetchone()[0])
            connection.execute("DELETE FROM twin_root_zone WHERE link_id=?", (link_id,))
            connection.commit()
        return count

    def save_snapshot(
        self,
        link_id: str,
        *,
        as_of: Any,
        state: Mapping[str, Any],
        plot_states: pd.DataFrame | None,
        input_manifest: Mapping[str, Any],
    ) -> str:
        snapshot_id = uuid.uuid4().hex
        with closing(self.connect()) as connection:
            connection.execute(
                "INSERT INTO snapshots VALUES(?,?,?,?,?,?,?)",
                (
                    snapshot_id,
                    link_id,
                    str(pd.Timestamp(as_of).date()),
                    _json(state),
                    plot_states.to_json(orient="records", date_format="iso") if isinstance(plot_states, pd.DataFrame) else None,
                    _json(input_manifest),
                    utc_now(),
                ),
            )
            connection.commit()
        return snapshot_id

    def snapshots(self, link_id: str) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            return pd.read_sql_query(
                "SELECT snapshot_id,link_id,as_of,state_json,plot_states_json,input_manifest_json,created_at FROM snapshots WHERE link_id=? ORDER BY as_of,created_at",
                connection,
                params=(link_id,),
            )

    def save_scenario(self, link_id: str, name: str, settings: Mapping[str, Any], results: pd.DataFrame) -> str:
        scenario_id = uuid.uuid4().hex
        with closing(self.connect()) as connection:
            connection.execute(
                "INSERT INTO scenarios VALUES(?,?,?,?,?,?)",
                (scenario_id, link_id, str(name), _json(settings), results.to_json(orient="records", date_format="iso"), utc_now()),
            )
            connection.commit()
        return scenario_id

    def scenarios(self, link_id: str) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            return pd.read_sql_query(
                "SELECT * FROM scenarios WHERE link_id=? ORDER BY created_at DESC",
                connection,
                params=(link_id,),
            )

    def replace_recommendations(self, link_id: str, rows: Sequence[Mapping[str, Any]]) -> None:
        with closing(self.connect()) as connection:
            connection.execute("DELETE FROM recommendations WHERE link_id=? AND status='Open'", (link_id,))
            for row in rows:
                connection.execute(
                    "INSERT INTO recommendations VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (
                        uuid.uuid4().hex,
                        link_id,
                        utc_now(),
                        str(row.get("Recommendation type", "Inspection")),
                        str(row.get("Priority", "Medium")),
                        row.get("Plot ID"),
                        str(row.get("Title", "Field action")),
                        str(row.get("Rationale", "")),
                        "Open",
                        _json(dict(row)),
                    ),
                )
            connection.commit()

    def recommendations(self, link_id: str) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            return pd.read_sql_query(
                "SELECT * FROM recommendations WHERE link_id=? ORDER BY CASE priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END, generated_at DESC",
                connection,
                params=(link_id,),
            )

    def update_recommendation(self, recommendation_id: str, status: str) -> None:
        with closing(self.connect()) as connection:
            connection.execute("UPDATE recommendations SET status=? WHERE recommendation_id=?", (status, recommendation_id))
            connection.commit()

    def register_model(self, link_id: str, *, target: str, algorithm: str, training_rows: int, metrics: Mapping[str, Any], features: Sequence[str]) -> str:
        model_id = uuid.uuid4().hex
        with closing(self.connect()) as connection:
            connection.execute(
                "INSERT INTO model_registry VALUES(?,?,?,?,?,?,?,?)",
                (model_id, link_id, target, algorithm, int(training_rows), _json(metrics), _json(list(features)), utc_now()),
            )
            connection.commit()
        return model_id

    def model_registry(self, link_id: str) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            return pd.read_sql_query(
                "SELECT * FROM model_registry WHERE link_id=? ORDER BY created_at DESC",
                connection,
                params=(link_id,),
            )

    def export_package(self, link_id: str) -> bytes:
        link = self.link(link_id) or {}
        settings = self.settings(link_id)
        snapshots = self.snapshots(link_id)
        scenarios = self.scenarios(link_id)
        recommendations = self.recommendations(link_id)
        models = self.model_registry(link_id)
        events = self.events(link_id)
        calibrations = self.calibration_runs(link_id)
        analogues = self.analogue_seasons(link_id)
        weather = self.weather(link_id)
        weather_record = self.weather_record(link_id)
        satellite = self.satellite(link_id)
        satellite_catalog = self.satellite_catalog(link_id)
        satellite_record = self.satellite_record(link_id)
        root_zone = self.root_zone(link_id)
        root_zone_stage = self.root_zone_stage_summary(link_id)
        root_zone_schedule = self.root_zone_schedule(link_id)
        root_zone_record = self.root_zone_record(link_id)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("twin_link.json", json.dumps(link, indent=2, ensure_ascii=False, default=str))
            archive.writestr("twin_settings.json", json.dumps(settings, indent=2, ensure_ascii=False, default=str))
            archive.writestr("snapshots.csv", snapshots.to_csv(index=False))
            archive.writestr("scenarios.csv", scenarios.to_csv(index=False))
            archive.writestr("recommendations.csv", recommendations.to_csv(index=False))
            archive.writestr("model_registry.csv", models.to_csv(index=False))
            archive.writestr("twin_events.csv", events.to_csv(index=False))
            archive.writestr("calibration_runs.csv", calibrations.to_csv(index=False))
            archive.writestr("analogue_seasons.csv", analogues.to_csv(index=False))
            if not weather.empty:
                archive.writestr("weather/daily_weather.csv", weather.to_csv(index=False))
            if weather_record:
                archive.writestr("weather/weather_attachment.json", json.dumps(weather_record, indent=2, ensure_ascii=False, default=str))
            if not satellite.empty:
                archive.writestr("satellite/sentinel2_index_time_series.csv", satellite.to_csv(index=False))
            if not satellite_catalog.empty:
                archive.writestr("satellite/sentinel2_scene_catalog.csv", satellite_catalog.to_csv(index=False))
            if satellite_record:
                archive.writestr("satellite/satellite_attachment.json", json.dumps(satellite_record, indent=2, ensure_ascii=False, default=str))
            if not root_zone.empty:
                archive.writestr("root_zone/daily_root_zone_balance.csv", root_zone.to_csv(index=False))
            if not root_zone_stage.empty:
                archive.writestr("root_zone/stage_summary.csv", root_zone_stage.to_csv(index=False))
            if not root_zone_schedule.empty:
                archive.writestr("root_zone/crop_stage_schedule.csv", root_zone_schedule.to_csv(index=False))
            if root_zone_record:
                archive.writestr("root_zone/root_zone_attachment.json", json.dumps(root_zone_record, indent=2, ensure_ascii=False, default=str))
            archive.writestr(
                "README.txt",
                "AgroLattice Twin export. Estimates and heuristic recommendations require agronomic review and independent validation before operational use.\n",
            )
        return buffer.getvalue()



def _canonicalise_twin_weather(frame: pd.DataFrame, latitude: float) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Return raw NASA columns plus all 19 canonical AgroLattice weather columns.

    Daily precipitation is one daily total. The three precipitation compatibility
    columns therefore share that daily value; their min/mean/max distinction is
    created only when daily rows are aggregated to monthly climatology. Daily soil
    heat flux follows the FAO-56 daily convention G=0 and is labelled as an
    assumption rather than an observed NASA value.
    """
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return pd.DataFrame(), {}
    result = frame.copy()
    date_col = _first_column(result, ["DATE", "Date", "date"])
    if not date_col:
        raise AgroLatticeTwinError("The NASA weather table has no date column.")
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

    eto_status = "Unavailable because one or more FAO-56 weather drivers were missing."
    required_eto = {"T2M", "T2M_MAX", "T2M_MIN", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN", "PS", "PRECTOTCORR"}
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
    provenance["SOIL_HEAT_FLUX"]["note"] = "Daily FAO-56 convention: G is assumed to be 0 MJ m⁻² day⁻¹; this is not a direct NASA observation."
    provenance["PRECIPITATION_MIN"]["note"] = "Daily compatibility alias of PRECTOTCORR; monthly minima are calculated only during aggregation."
    provenance["PRECIPITATION_MAX"]["note"] = "Daily compatibility alias of PRECTOTCORR; monthly maxima are calculated only during aggregation."
    return result.reset_index(drop=True), provenance


def _merge_weather_frames(frames: Sequence[pd.DataFrame]) -> pd.DataFrame:
    valid = []
    for frame in frames:
        if not isinstance(frame, pd.DataFrame) or frame.empty:
            continue
        item = frame.copy()
        date_col = _first_column(item, ["DATE", "Date", "date"])
        if not date_col:
            continue
        item["DATE"] = pd.to_datetime(item[date_col], errors="coerce").dt.tz_localize(None)
        if date_col != "DATE":
            item = item.drop(columns=[date_col], errors="ignore")
        item = item.dropna(subset=["DATE"]).set_index("DATE")
        valid.append(item)
    if not valid:
        return pd.DataFrame()
    combined = valid[0]
    for item in valid[1:]:
        combined = item.combine_first(combined)
    return combined.sort_index().reset_index()


def _fetch_twin_weather_profile(
    *,
    latitude: float,
    longitude: float,
    start_date: date,
    end_date: date,
    cache_dir: Path,
    parameters: Sequence[str],
    time_standard: str,
    force_refresh: bool,
    progress_callback=None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Fetch the requested Twin profile and tolerate unavailable legacy parameters.

    A full request is attempted first. If NASA rejects a legacy optional parameter,
    the core profile is retained and each optional parameter is attempted separately.
    """
    requested = list(dict.fromkeys(str(code).upper() for code in parameters if str(code).strip()))
    try:
        raw, metadata = fetch_nasa_power_daily(
            latitude, longitude, start_date, end_date, cache_dir,
            parameters=requested, time_standard=time_standard,
            force_refresh=force_refresh, progress_callback=progress_callback,
        )
        canonical, provenance = _canonicalise_twin_weather(raw, latitude)
        metadata = dict(metadata)
        metadata.update({
            "canonical_variables": list(TWIN_CANONICAL_WEATHER_VARIABLES),
            "canonical_provenance": provenance,
            "failed_optional_parameters": [],
        })
        return canonical, metadata
    except Exception as full_error:
        core = [code for code in requested if code not in TWIN_OPTIONAL_POWER_PARAMETERS]
        optional = [code for code in requested if code in TWIN_OPTIONAL_POWER_PARAMETERS]
        if not core:
            raise
        base, base_meta = fetch_nasa_power_daily(
            latitude, longitude, start_date, end_date, cache_dir,
            parameters=core, time_standard=time_standard,
            force_refresh=force_refresh, progress_callback=progress_callback,
        )
        frames = [base]
        optional_meta: list[dict[str, Any]] = []
        failures: list[dict[str, str]] = []
        for code in optional:
            try:
                extra, meta = fetch_nasa_power_daily(
                    latitude, longitude, start_date, end_date, cache_dir,
                    parameters=[code], time_standard=time_standard,
                    force_refresh=force_refresh,
                )
                frames.append(extra)
                optional_meta.append({"parameter": code, "metadata": meta})
            except Exception as error:
                failures.append({"parameter": code, "error": f"{type(error).__name__}: {error}"})
        merged = _merge_weather_frames(frames)
        canonical, provenance = _canonicalise_twin_weather(merged, latitude)
        metadata = dict(base_meta)
        metadata.update({
            "canonical_variables": list(TWIN_CANONICAL_WEATHER_VARIABLES),
            "canonical_provenance": provenance,
            "optional_parameter_requests": optional_meta,
            "failed_optional_parameters": failures,
            "full_profile_retry_reason": f"{type(full_error).__name__}: {full_error}",
        })
        return canonical, metadata

def _weather_frame(
    context: Mapping[str, Any],
    trial_weather: pd.DataFrame | None,
    trial: Mapping[str, Any] | None,
    twin_weather: pd.DataFrame | None = None,
) -> pd.DataFrame:
    if isinstance(twin_weather, pd.DataFrame) and not twin_weather.empty:
        candidate = twin_weather
    elif isinstance(trial_weather, pd.DataFrame) and not trial_weather.empty:
        candidate = trial_weather
    else:
        candidate = context.get("daily_weather")
    if not isinstance(candidate, pd.DataFrame) or candidate.empty:
        return pd.DataFrame()
    base = _num((trial or {}).get("base_temperature_c"), 10.0)
    upper = _num((trial or {}).get("upper_temperature_c"), 30.0)
    try:
        return prepare_weather(candidate, base_temperature_c=base, upper_temperature_c=upper)
    except Exception:
        frame = candidate.copy()
        date_col = _first_column(frame, ["Date", "DATE", "date"])
        if not date_col:
            return pd.DataFrame()
        frame["Date"] = pd.to_datetime(frame[date_col], errors="coerce")
        tmin_col = _first_column(frame, ["Tmin", "T2M_MIN", "Temperature min", "Tmin (°C)"])
        tmax_col = _first_column(frame, ["Tmax", "T2M_MAX", "Temperature max", "Tmax (°C)"])
        if tmin_col and tmax_col:
            low = pd.to_numeric(frame[tmin_col], errors="coerce").clip(lower=base, upper=upper)
            high = pd.to_numeric(frame[tmax_col], errors="coerce").clip(lower=base, upper=upper)
            frame["GDD daily"] = ((low + high) / 2.0 - base).clip(lower=0)
        return frame.dropna(subset=["Date"]).sort_values("Date")


def _sum_between(weather: pd.DataFrame, start: Any, end: Any, column: str) -> float:
    if weather.empty or column not in weather:
        return np.nan
    start_ts, end_ts = _to_timestamp(start), _to_timestamp(end)
    if pd.isna(start_ts) or pd.isna(end_ts):
        return np.nan
    subset = weather.loc[pd.to_datetime(weather["Date"], errors="coerce").between(start_ts, end_ts)]
    return float(pd.to_numeric(subset[column], errors="coerce").sum(min_count=1)) if not subset.empty else np.nan


def _mean_recent(weather: pd.DataFrame, as_of: Any, column: str, days: int = 7) -> float:
    if weather.empty or column not in weather:
        return np.nan
    subset = _dated_subset(weather, as_of, ["Date", "DATE"])
    if subset.empty:
        return np.nan
    return float(pd.to_numeric(subset.tail(max(1, days))[column], errors="coerce").mean())


def _projected_event(as_of: Any, accumulated: float, target: float, recent_rate: float) -> tuple[float, pd.Timestamp | pd.NaT]:
    if not all(np.isfinite(value) for value in [accumulated, target, recent_rate]) or recent_rate <= 0:
        return np.nan, pd.NaT
    remaining = max(0.0, target - accumulated)
    days = remaining / recent_rate
    return float(days), pd.Timestamp(as_of).normalize() + pd.Timedelta(days=float(days))


def _latest_numeric(frame: pd.DataFrame | None, as_of: Any, date_candidates: Sequence[str], value_candidates: Sequence[str]) -> float:
    subset = _dated_subset(frame, as_of, date_candidates)
    if subset.empty:
        return np.nan
    column = _first_column(subset, value_candidates)
    if not column:
        return np.nan
    values = pd.to_numeric(subset[column], errors="coerce").dropna()
    return float(values.iloc[-1]) if not values.empty else np.nan


def _observed_gdd_targets(metrics: pd.DataFrame) -> tuple[float, float, str]:
    if not isinstance(metrics, pd.DataFrame) or metrics.empty:
        return np.nan, np.nan, "No observed plot-level GDD targets"
    male_col = _first_column(metrics, ["Male GDD to 50% pollen shed", "Male GDD to 50% shedding"])
    female_col = _first_column(metrics, ["Female GDD to 50% silking"])
    male = float(pd.to_numeric(metrics[male_col], errors="coerce").median()) if male_col else np.nan
    female = float(pd.to_numeric(metrics[female_col], errors="coerce").median()) if female_col else np.nan
    n = min(
        int(pd.to_numeric(metrics[male_col], errors="coerce").notna().sum()) if male_col else 0,
        int(pd.to_numeric(metrics[female_col], errors="coerce").notna().sum()) if female_col else 0,
    )
    return male, female, f"Observed median from {n} plots" if n else "No complete observed plot targets"


def build_twin_state(
    *,
    context: Mapping[str, Any],
    field: Mapping[str, Any] | None,
    trial: Mapping[str, Any] | None,
    plots: pd.DataFrame,
    observations: pd.DataFrame,
    harvest: pd.DataFrame,
    trial_weather: pd.DataFrame,
    twin_weather: pd.DataFrame | None,
    root_zone: pd.DataFrame,
    satellite: pd.DataFrame,
    sensors: pd.DataFrame,
    sensor_readings: pd.DataFrame,
    tasks: pd.DataFrame,
    alerts: pd.DataFrame,
    settings: Mapping[str, Any],
    as_of: Any,
    male_physiology: Mapping[str, Any] | PhysiologyParameters | None = None,
    female_physiology: Mapping[str, Any] | PhysiologyParameters | None = None,
    male_physiology_source: str | None = None,
    female_physiology_source: str | None = None,
) -> tuple[dict[str, Any], pd.DataFrame, dict[str, Any]]:
    as_of_ts = pd.Timestamp(as_of).normalize()
    weather = _weather_frame(context, trial_weather, trial, twin_weather)
    weather_to_date = _dated_subset(weather, as_of_ts, ["Date", "DATE"])
    root_zone_to_date = _dated_subset(root_zone, as_of_ts, ["Date", "DATE"])
    satellite_analysis = satellite.copy() if isinstance(satellite, pd.DataFrame) else pd.DataFrame()
    if not satellite_analysis.empty and "Status" in satellite_analysis:
        satellite_analysis = satellite_analysis.loc[
            satellite_analysis["Status"].astype(str).str.casefold().eq("usable")
        ].copy()
    satellite_to_date = _dated_subset(satellite_analysis, as_of_ts, ["Date", "Acquisition UTC"])
    observations_to_date = _dated_subset(observations, as_of_ts, ["Date", "Observation date"])

    plot_metrics = pd.DataFrame()
    daily_curves = pd.DataFrame()
    if isinstance(observations_to_date, pd.DataFrame) and not observations_to_date.empty:
        try:
            plot_metrics, daily_curves = compute_plot_synchrony_metrics(observations_to_date, weather if not weather.empty else None)
        except Exception:
            plot_metrics, daily_curves = pd.DataFrame(), pd.DataFrame()

    observed_male_target, observed_female_target, observed_target_basis = _observed_gdd_targets(plot_metrics)
    configured_male = _num(settings.get("male_target_gdd"))
    configured_female = _num(settings.get("female_target_gdd"))
    legacy_male_target = configured_male if np.isfinite(configured_male) else observed_male_target
    legacy_female_target = configured_female if np.isfinite(configured_female) else observed_female_target
    if not np.isfinite(legacy_male_target):
        legacy_male_target = 650.0
    if not np.isfinite(legacy_female_target):
        legacy_female_target = 670.0

    female_sowing = _to_timestamp((trial or {}).get("female_sowing_date"))
    male_sowing = pd.NaT
    if isinstance(plots, pd.DataFrame) and not plots.empty:
        male_sowing_col = _first_column(plots, ["Male sowing"])
        if male_sowing_col:
            dates = pd.to_datetime(plots[male_sowing_col], errors="coerce").dropna()
            if not dates.empty:
                male_sowing = dates.median()
    if pd.isna(male_sowing) and pd.notna(female_sowing):
        male_sowing = female_sowing

    male_gdd = _sum_between(weather, male_sowing, as_of_ts, "GDD daily") if pd.notna(male_sowing) else np.nan
    female_gdd = _sum_between(weather, female_sowing, as_of_ts, "GDD daily") if pd.notna(female_sowing) else np.nan
    recent_gdd_rate = _mean_recent(weather, as_of_ts, "GDD daily", 7)

    male_params = male_physiology if isinstance(male_physiology, PhysiologyParameters) else physiology_from_mapping(male_physiology) if male_physiology else DEFAULT_PHYSIOLOGY
    female_params = female_physiology if isinstance(female_physiology, PhysiologyParameters) else physiology_from_mapping(female_physiology) if female_physiology else DEFAULT_PHYSIOLOGY
    mechanistic_active = bool(trial and not weather.empty and pd.notna(female_sowing) and pd.notna(male_sowing))
    male_event_uncertainty: dict[str, Any] = {}
    female_event_uncertainty: dict[str, Any] = {}
    model_disagreement_days = np.nan
    if mechanistic_active:
        try:
            male_target = float(parameter_thermal_targets(male_params)["Planting GDD to anthesis"])
            female_target = float(parameter_thermal_targets(female_params)["Planting GDD to silking"])
            target_basis = f"Mechanistic maize physiology (Laurent et al. 2025; DOI {MECHANISTIC_MAIZE_DOI})"
            reached_male = mechanistic_event_date(weather_to_date, male_sowing, male_params, "Male")
            reached_female = mechanistic_event_date(weather_to_date, female_sowing, female_params, "Female")
            male_days, projected_male = _projected_event(as_of_ts, male_gdd, male_target, recent_gdd_rate)
            female_days, projected_female = _projected_event(as_of_ts, female_gdd, female_target, recent_gdd_rate)
            male_date = reached_male if pd.notna(reached_male) and reached_male <= as_of_ts else projected_male
            female_date = reached_female if pd.notna(reached_female) and reached_female <= as_of_ts else projected_female
            try:
                _, male_event_uncertainty = simulate_event_uncertainty(weather_to_date, male_sowing, male_params, "Male", draws=300, random_state=42)
            except Exception:
                male_event_uncertainty = {}
            try:
                _, female_event_uncertainty = simulate_event_uncertainty(weather_to_date, female_sowing, female_params, "Female", draws=300, random_state=43)
            except Exception:
                female_event_uncertainty = {}
            _, legacy_male_date = _projected_event(as_of_ts, male_gdd, legacy_male_target, recent_gdd_rate)
            _, legacy_female_date = _projected_event(as_of_ts, female_gdd, legacy_female_target, recent_gdd_rate)
            disagreements = []
            if pd.notna(male_date) and pd.notna(legacy_male_date):
                disagreements.append(abs((male_date - legacy_male_date).total_seconds()) / 86400.0)
            if pd.notna(female_date) and pd.notna(legacy_female_date):
                disagreements.append(abs((female_date - legacy_female_date).total_seconds()) / 86400.0)
            if disagreements:
                model_disagreement_days = float(np.mean(disagreements))
        except Exception:
            mechanistic_active = False

    if not mechanistic_active:
        male_target = legacy_male_target
        female_target = legacy_female_target
        target_basis = observed_target_basis if (np.isfinite(observed_male_target) and np.isfinite(observed_female_target)) else "Legacy transparent GDD target fallback (650/670 if uncalibrated)"
        male_days, male_date = _projected_event(as_of_ts, male_gdd, male_target, recent_gdd_rate)
        female_days, female_date = _projected_event(as_of_ts, female_gdd, female_target, recent_gdd_rate)

    predicted_gap = (male_date - female_date).total_seconds() / 86400.0 if pd.notna(male_date) and pd.notna(female_date) else np.nan

    precip_col = _first_column(weather_to_date, ["Rainfall (mm)", "Precipitation (mm)", "PRECTOTCORR", "Rain (mm)"])
    tmean_col = _first_column(weather_to_date, ["Tmean (°C)", "Tmean", "T2M", "Temperature mean", "Temperature (°C)"])
    tmax_col = _first_column(weather_to_date, ["Tmax", "T2M_MAX", "Temperature max", "Tmax (°C)"])
    rain_7 = float(pd.to_numeric(weather_to_date.tail(7)[precip_col], errors="coerce").sum(min_count=1)) if precip_col and not weather_to_date.empty else np.nan
    mean_temp_7 = float(pd.to_numeric(weather_to_date.tail(7)[tmean_col], errors="coerce").mean()) if tmean_col and not weather_to_date.empty else np.nan
    heat_days_7 = int((pd.to_numeric(weather_to_date.tail(7)[tmax_col], errors="coerce") >= 35).sum()) if tmax_col and not weather_to_date.empty else 0

    latest_ks = _latest_numeric(root_zone_to_date, as_of_ts, ["Date"], ["Ks"])
    latest_depletion = _latest_numeric(root_zone_to_date, as_of_ts, ["Date"], ["Relative depletion"])
    latest_ndvi = _latest_numeric(satellite_to_date, as_of_ts, ["Date", "Acquisition UTC"], ["NDVI mean", "NDVI median"])
    latest_ndmi = _latest_numeric(satellite_to_date, as_of_ts, ["Date", "Acquisition UTC"], ["NDMI mean", "NDMI median"])

    open_tasks = 0
    overdue_tasks = 0
    if isinstance(tasks, pd.DataFrame) and not tasks.empty:
        status_col = _first_column(tasks, ["status"])
        due_col = _first_column(tasks, ["due_date", "Due date"])
        task_subset = tasks.copy()
        if status_col:
            open_mask = ~task_subset[status_col].astype(str).str.casefold().isin({"completed", "cancelled", "closed"})
            open_tasks = int(open_mask.sum())
            if due_col:
                due = pd.to_datetime(task_subset[due_col], errors="coerce")
                overdue_tasks = int((open_mask & due.notna() & due.lt(as_of_ts)).sum())
    open_alerts = 0
    if isinstance(alerts, pd.DataFrame) and not alerts.empty:
        status_col = _first_column(alerts, ["status"])
        open_alerts = int((~alerts[status_col].astype(str).str.casefold().isin({"resolved", "closed"})).sum()) if status_col else len(alerts)

    freshness = {
        "weather_days": _freshness_days(weather, as_of_ts, ["Date", "DATE"]),
        "root_zone_days": _freshness_days(root_zone, as_of_ts, ["Date"]),
        "satellite_days": _freshness_days(satellite_analysis, as_of_ts, ["Date", "Acquisition UTC"]),
        "observations_days": _freshness_days(observations, as_of_ts, ["Date", "Observation date"]),
        "sensor_days": _freshness_days(sensor_readings, as_of_ts, ["timestamp", "Timestamp"]),
    }
    source_scores = []
    for key, age in freshness.items():
        if np.isfinite(age):
            expected = 12 if key == "satellite_days" else 3
            source_scores.append(max(0.0, 100.0 - 100.0 * age / max(expected * 3, 1)))
    data_quality = float(np.mean(source_scores)) if source_scores else 0.0

    stress_penalty = 0.0
    if np.isfinite(latest_ks):
        stress_penalty += max(0.0, 1.0 - latest_ks) * 45.0
    if heat_days_7:
        stress_penalty += min(20.0, heat_days_7 * 4.0)
    synchrony_penalty = min(40.0, abs(predicted_gap) * 7.0) if np.isfinite(predicted_gap) else 20.0
    estimated_overlap = float(np.clip(100.0 - synchrony_penalty - stress_penalty, 0.0, 100.0))

    health_components = []
    if np.isfinite(latest_ks):
        health_components.append(100.0 * np.clip(latest_ks, 0, 1))
    if np.isfinite(latest_ndvi):
        health_components.append(100.0 * np.clip((latest_ndvi + 0.1) / 0.9, 0, 1))
    if np.isfinite(latest_depletion):
        health_components.append(100.0 * np.clip(1.0 - latest_depletion, 0, 1))
    health_score = float(np.mean(health_components)) if health_components else np.nan

    uncertainty = 100.0 - data_quality
    if not np.isfinite(observed_male_target) or not np.isfinite(observed_female_target):
        uncertainty += 15.0
    if not np.isfinite(latest_ks):
        uncertainty += 8.0
    if not np.isfinite(latest_ndvi):
        uncertainty += 5.0
    uncertainty = float(np.clip(uncertainty, 5.0, 100.0))

    field_name = str((field or {}).get("name") or (trial or {}).get("site_name") or "Unlinked field")
    female_parent_lines = [str(value) for value in ((trial or {}).get("female_parent_levels") or [(trial or {}).get("female_parent")]) if str(value or "").strip()]
    male_parent_lines = [str(value) for value in ((trial or {}).get("male_parent_levels") or [(trial or {}).get("male_parent")]) if str(value or "").strip()]
    parent_pairings = (trial or {}).get("parent_pairings") or []
    state = {
        "As of": as_of_ts.date().isoformat(),
        "Field": field_name,
        "Trial": (trial or {}).get("name"),
        "Crop": (field or {}).get("crop") or (context.get("active_project") or {}).get("season", {}).get("crop") or "Maize",
        "Male parent": (trial or {}).get("male_parent"),
        "Female parent": (trial or {}).get("female_parent"),
        "Male parent lines": ", ".join(male_parent_lines) if male_parent_lines else None,
        "Female parent lines": ", ".join(female_parent_lines) if female_parent_lines else None,
        "Parent combinations": len(parent_pairings) if parent_pairings else (1 if female_parent_lines and male_parent_lines else 0),
        "Phenology model": "Mechanistic maize" if mechanistic_active else "Legacy transparent GDD target",
        "Mechanistic maize DOI": MECHANISTIC_MAIZE_DOI if mechanistic_active else None,
        "Male physiology source": male_physiology_source or ("Publication prior" if mechanistic_active else None),
        "Female physiology source": female_physiology_source or ("Publication prior" if mechanistic_active else None),
        "Male physiology parameters": male_params.to_record() if mechanistic_active else None,
        "Female physiology parameters": female_params.to_record() if mechanistic_active else None,
        "Male target GDD": male_target,
        "Female target GDD": female_target,
        "Legacy male target GDD": legacy_male_target,
        "Legacy female target GDD": legacy_female_target,
        "Target basis": target_basis,
        "Male accumulated GDD": male_gdd,
        "Female accumulated GDD": female_gdd,
        "Male progress (%)": 100.0 * male_gdd / male_target if np.isfinite(male_gdd) and male_target > 0 else np.nan,
        "Female progress (%)": 100.0 * female_gdd / female_target if np.isfinite(female_gdd) and female_target > 0 else np.nan,
        "Predicted male 50% flowering": male_date.date().isoformat() if pd.notna(male_date) else None,
        "Predicted female 50% silking": female_date.date().isoformat() if pd.notna(female_date) else None,
        "Male event P05": male_event_uncertainty.get("P05 event date"),
        "Male event P95": male_event_uncertainty.get("P95 event date"),
        "Female event P05": female_event_uncertainty.get("P05 event date"),
        "Female event P95": female_event_uncertainty.get("P95 event date"),
        "Model disagreement (days)": model_disagreement_days,
        "Predicted synchrony gap (days)": predicted_gap,
        "Estimated receptive-silk coverage (%)": estimated_overlap,
        "Recent GDD/day": recent_gdd_rate,
        "Rain last 7 days (mm)": rain_7,
        "Mean temperature last 7 days (°C)": mean_temp_7,
        "Heat days ≥35°C last 7 days": heat_days_7,
        "Latest root-zone Ks": latest_ks,
        "Latest relative depletion": latest_depletion,
        "Latest NDVI": latest_ndvi,
        "Latest NDMI": latest_ndmi,
        "Composite state indicator": health_score,
        "Health score": health_score,
        "Data completeness score": data_quality,
        "Data quality score": data_quality,
        "Parameter uncertainty": "Prior-driven" if mechanistic_active and all((male_physiology_source or "").casefold().find(token) < 0 for token in ["calibrated", "measured"]) and all((female_physiology_source or "").casefold().find(token) < 0 for token in ["calibrated", "measured"]) else ("Locally informed" if mechanistic_active else "Not estimated"),
        "Data uncertainty proxy (%)": uncertainty,
        "Uncertainty (%)": uncertainty,
        "Open tasks": open_tasks,
        "Overdue tasks": overdue_tasks,
        "Open alerts": open_alerts,
        "Weather observations": len(weather_to_date),
        "Field observations": len(observations_to_date),
        "Satellite observations": len(satellite_to_date),
        "Root-zone days": len(root_zone_to_date),
    }

    plot_states = build_plot_state_table(
        trial=trial,
        plots=plots,
        observations=observations_to_date,
        harvest=harvest,
        weather=weather,
        plot_metrics=plot_metrics,
        settings=settings,
        as_of=as_of_ts,
        male_target=male_target,
        female_target=female_target,
        recent_gdd_rate=recent_gdd_rate,
        latest_ks=latest_ks,
    )

    manifest = {
        "weather_rows": len(weather_to_date),
        "weather_source": "Persistent Twin weather" if isinstance(twin_weather, pd.DataFrame) and not twin_weather.empty else ("Trial weather" if isinstance(trial_weather, pd.DataFrame) and not trial_weather.empty else "Active session weather"),
        "root_zone_rows": len(root_zone_to_date),
        "root_zone_source": str(getattr(root_zone, "attrs", {}).get("agrolattice_source", "Persistent Twin root-zone" if not root_zone_to_date.empty else "Unavailable")),
        "satellite_rows": len(satellite_to_date),
        "satellite_source": str(getattr(satellite, "attrs", {}).get("agrolattice_source") or "Active session satellite"),
        "observation_rows": len(observations_to_date),
        "plot_rows": len(plots),
        "harvest_rows": len(harvest),
        "sensor_rows": len(sensor_readings),
        "freshness_days": freshness,
        "target_basis": target_basis,
        "phenology_model": state.get("Phenology model"),
        "mechanistic_maize_doi": state.get("Mechanistic maize DOI"),
        "male_physiology_source": state.get("Male physiology source"),
        "female_physiology_source": state.get("Female physiology source"),
        "model_disagreement_days": state.get("Model disagreement (days)"),
        "module_version": MODULE_VERSION,
    }
    return state, plot_states, manifest


def build_plot_state_table(
    *,
    trial: Mapping[str, Any] | None,
    plots: pd.DataFrame,
    observations: pd.DataFrame,
    harvest: pd.DataFrame,
    weather: pd.DataFrame,
    plot_metrics: pd.DataFrame,
    settings: Mapping[str, Any],
    as_of: Any,
    male_target: float,
    female_target: float,
    recent_gdd_rate: float,
    latest_ks: float,
) -> pd.DataFrame:
    if not isinstance(plots, pd.DataFrame) or plots.empty:
        return pd.DataFrame()
    table = plots.copy()
    if isinstance(plot_metrics, pd.DataFrame) and not plot_metrics.empty:
        common = "Plot ID" if "Plot ID" in table and "Plot ID" in plot_metrics else "Plot"
        table = table.merge(plot_metrics, on=common, how="left", suffixes=("", " metric"))
    if isinstance(harvest, pd.DataFrame) and not harvest.empty:
        common = "Plot ID" if "Plot ID" in table and "Plot ID" in harvest else "Plot"
        keep = [column for column in harvest.columns if column not in table.columns or column == common]
        table = table.merge(harvest[keep], on=common, how="left")

    latest_obs = pd.DataFrame()
    if isinstance(observations, pd.DataFrame) and not observations.empty:
        obs = observations.copy()
        obs["__date"] = pd.to_datetime(obs[_first_column(obs, ["Date", "Observation date"])], errors="coerce")
        sort_keys = [key for key in ["Plot ID", "Plot"] if key in obs]
        if sort_keys:
            latest_obs = obs.sort_values("__date").groupby(sort_keys[0], as_index=False).tail(1)
            keep = [column for column in latest_obs.columns if column not in table.columns or column in sort_keys]
            table = table.merge(latest_obs[keep], on=sort_keys[0], how="left")

    stale_days = int(settings.get("stale_observation_days", 3))
    as_of_ts = pd.Timestamp(as_of).normalize()
    date_col = _first_column(table, ["Date", "Observation date", "__date"])
    if date_col:
        table["Days since observation"] = (as_of_ts - pd.to_datetime(table[date_col], errors="coerce").dt.normalize()).dt.days
    else:
        table["Days since observation"] = np.nan

    male_sowing_col = _first_column(table, ["Male sowing"])
    female_sowing_col = _first_column(table, ["Female sowing"])
    male_progress = []
    female_progress = []
    days_to_male = []
    days_to_female = []
    for _, row in table.iterrows():
        male_gdd = _sum_between(weather, row.get(male_sowing_col) if male_sowing_col else None, as_of_ts, "GDD daily")
        female_gdd = _sum_between(weather, row.get(female_sowing_col) if female_sowing_col else None, as_of_ts, "GDD daily")
        male_progress.append(100.0 * male_gdd / male_target if np.isfinite(male_gdd) and male_target > 0 else np.nan)
        female_progress.append(100.0 * female_gdd / female_target if np.isfinite(female_gdd) and female_target > 0 else np.nan)
        md, _ = _projected_event(as_of_ts, male_gdd, male_target, recent_gdd_rate)
        fd, _ = _projected_event(as_of_ts, female_gdd, female_target, recent_gdd_rate)
        days_to_male.append(md)
        days_to_female.append(fd)
    table["Male flowering progress (%)"] = male_progress
    table["Female silking progress (%)"] = female_progress
    table["Estimated days to male 50%"] = days_to_male
    table["Estimated days to female 50%"] = days_to_female

    male_obs_col = _first_column(table, ["Male shedding (%)"])
    female_obs_col = _first_column(table, ["Female silking (%)"])
    receptive_col = _first_column(table, ["Female receptive silks (%)"])
    gap_col = _first_column(table, ["Male–female 50% synchrony gap (days)", "Synchrony gap (days)"])
    overlap_col = _first_column(table, ["Female receptivity covered by pollen (%)", "Overlap coverage (%)"])
    stress_col = _first_column(table, ["Crop stress score (0-5)", "Average crop-stress score"])

    missing_measurements = pd.Series(0.0, index=table.index)
    for column in [male_obs_col, female_obs_col, receptive_col]:
        if column:
            missing_measurements += pd.to_numeric(table[column], errors="coerce").isna().astype(float)
        else:
            missing_measurements += 1.0
    missing_measurements = 100.0 * missing_measurements / 3.0
    staleness = pd.to_numeric(table["Days since observation"], errors="coerce")
    staleness_score = np.where(staleness.notna(), np.clip(100.0 * staleness / max(stale_days * 3, 1), 0, 100), 100.0)
    male_distance = np.abs(pd.to_numeric(table["Male flowering progress (%)"], errors="coerce") - 50.0)
    female_distance = np.abs(pd.to_numeric(table["Female silking progress (%)"], errors="coerce") - 50.0)
    criticality = np.clip(100.0 - np.minimum(male_distance, female_distance) * 2.0, 0, 100)
    if stress_col:
        stress_score = 20.0 * pd.to_numeric(table[stress_col], errors="coerce").fillna(0).clip(0, 5)
    else:
        stress_score = pd.Series(max(0.0, (1.0 - latest_ks) * 100.0) if np.isfinite(latest_ks) else 20.0, index=table.index)
    table["Measurement uncertainty (%)"] = np.clip(0.45 * missing_measurements + 0.35 * staleness_score + 0.20 * stress_score, 0, 100)
    table["Flowering-window criticality (%)"] = criticality
    table["Inspection priority score"] = np.clip(
        0.45 * table["Measurement uncertainty (%)"] + 0.40 * table["Flowering-window criticality (%)"] + 0.15 * stress_score,
        0,
        100,
    )
    table["Inspection priority"] = pd.cut(
        table["Inspection priority score"],
        bins=[-np.inf, 35, 60, 80, np.inf],
        labels=["Low", "Medium", "High", "Critical"],
    ).astype(str)

    if gap_col:
        table["Estimated synchrony gap (days)"] = pd.to_numeric(table[gap_col], errors="coerce")
    else:
        table["Estimated synchrony gap (days)"] = pd.to_numeric(table["Estimated days to male 50%"], errors="coerce") - pd.to_numeric(table["Estimated days to female 50%"], errors="coerce")
    if overlap_col:
        table["Estimated overlap (%)"] = pd.to_numeric(table[overlap_col], errors="coerce")
    else:
        gap = pd.to_numeric(table["Estimated synchrony gap (days)"], errors="coerce").abs()
        table["Estimated overlap (%)"] = np.clip(100.0 - gap * 12.0 - stress_score * 0.25, 0, 100)

    seed_col = _first_column(table, ["Seed-set percentage", "Seed set (%)"])
    model_method = "Transparent heuristic"
    table["Predicted seed set (%)"] = np.clip(10.0 + 0.82 * pd.to_numeric(table["Estimated overlap (%)"], errors="coerce") + 8.0 * (latest_ks if np.isfinite(latest_ks) else 0.8), 0, 100)
    if seed_col:
        complete = table.loc[pd.to_numeric(table[seed_col], errors="coerce").notna()].copy()
        feature_candidates = [
            "Male offset (days)",
            "Sowing density (plants/ha)",
            "Estimated synchrony gap (days)",
            "Estimated overlap (%)",
            "Measurement uncertainty (%)",
        ]
        features = [column for column in feature_candidates if column in table]
        if len(complete) >= 8 and len(features) >= 2:
            X = complete[features].apply(pd.to_numeric, errors="coerce")
            y = pd.to_numeric(complete[seed_col], errors="coerce")
            pipe = Pipeline([("imputer", SimpleImputer(strategy="median")), ("model", RandomForestRegressor(n_estimators=300, min_samples_leaf=2, random_state=42, n_jobs=-1))])
            pipe.fit(X, y)
            table["Predicted seed set (%)"] = np.clip(pipe.predict(table[features].apply(pd.to_numeric, errors="coerce")), 0, 100)
            transformed = pipe.named_steps["imputer"].transform(table[features].apply(pd.to_numeric, errors="coerce"))
            tree_predictions = np.vstack([tree.predict(transformed) for tree in pipe.named_steps["model"].estimators_])
            table["Outcome-model uncertainty (SD)"] = np.std(tree_predictions, axis=0)
            model_method = f"Random forest calibrated from {len(complete)} completed plots"
    table["Seed-set prediction method"] = model_method
    return table


def simulate_scenarios(
    *,
    state: Mapping[str, Any],
    plot_states: pd.DataFrame,
    temperature_delta_c: float,
    rainfall_multiplier: float,
    irrigation_change_mm: float,
    male_offset_change_days: int,
    density_change_percent: float,
    heat_days_change: int,
) -> pd.DataFrame:
    base_gap = _num(state.get("Predicted synchrony gap (days)"), 0.0)
    base_ks = _num(state.get("Latest root-zone Ks"), 0.8)
    base_overlap = _num(state.get("Estimated receptive-silk coverage (%)"), 70.0)
    base_seed = float(pd.to_numeric(plot_states.get("Predicted seed set (%)"), errors="coerce").mean()) if isinstance(plot_states, pd.DataFrame) and "Predicted seed set (%)" in plot_states else np.clip(10 + 0.82 * base_overlap + 8 * base_ks, 0, 100)
    recent_rate = _num(state.get("Recent GDD/day"), 10.0)
    male_days = _num((pd.to_numeric(plot_states.get("Estimated days to male 50%"), errors="coerce").median() if isinstance(plot_states, pd.DataFrame) and "Estimated days to male 50%" in plot_states else np.nan), 10.0)
    female_days = _num((pd.to_numeric(plot_states.get("Estimated days to female 50%"), errors="coerce").median() if isinstance(plot_states, pd.DataFrame) and "Estimated days to female 50%" in plot_states else np.nan), 10.0)

    adjusted_rate = max(0.1, recent_rate + float(temperature_delta_c))
    male_thermal_shift = male_days * recent_rate / adjusted_rate - male_days
    female_thermal_shift = female_days * recent_rate / adjusted_rate - female_days
    scenario_gap = base_gap + float(male_offset_change_days) + male_thermal_shift - female_thermal_shift
    scenario_ks = float(np.clip(base_ks + irrigation_change_mm / 120.0 + 0.08 * (rainfall_multiplier - 1.0), 0.0, 1.0))
    stress_penalty = max(0.0, 1.0 - scenario_ks) * 35.0
    heat_penalty = max(0, int(heat_days_change)) * 3.0
    scenario_overlap = float(np.clip(100.0 - abs(scenario_gap) * 12.0 - stress_penalty - heat_penalty, 0, 100))
    density_penalty = max(0.0, abs(float(density_change_percent)) - 10.0) * 0.12
    scenario_seed = float(np.clip(base_seed + 0.72 * (scenario_overlap - base_overlap) + 14.0 * (scenario_ks - base_ks) - heat_penalty - density_penalty, 0, 100))

    rows = [
        {
            "Scenario": "Baseline",
            "Temperature change (°C)": 0.0,
            "Rainfall multiplier": 1.0,
            "Additional irrigation (mm)": 0.0,
            "Male sowing-offset change (days)": 0,
            "Planting-density change (%)": 0.0,
            "Additional heat days": 0,
            "Predicted synchrony gap (days)": base_gap,
            "Expected overlap (%)": base_overlap,
            "Water-stress coefficient": base_ks,
            "Predicted seed set (%)": base_seed,
            "Method": "Current twin state",
        },
        {
            "Scenario": "Alternative",
            "Temperature change (°C)": float(temperature_delta_c),
            "Rainfall multiplier": float(rainfall_multiplier),
            "Additional irrigation (mm)": float(irrigation_change_mm),
            "Male sowing-offset change (days)": int(male_offset_change_days),
            "Planting-density change (%)": float(density_change_percent),
            "Additional heat days": int(heat_days_change),
            "Predicted synchrony gap (days)": scenario_gap,
            "Expected overlap (%)": scenario_overlap,
            "Water-stress coefficient": scenario_ks,
            "Predicted seed set (%)": scenario_seed,
            "Method": "Transparent scenario response model",
        },
    ]
    frame = pd.DataFrame(rows)
    for metric in ["Predicted synchrony gap (days)", "Expected overlap (%)", "Water-stress coefficient", "Predicted seed set (%)"]:
        frame[f"Change in {metric}"] = frame[metric] - frame.loc[0, metric]
    return frame


def generate_recommendations(
    *,
    plot_states: pd.DataFrame,
    state: Mapping[str, Any],
    max_plots: int = 8,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if isinstance(plot_states, pd.DataFrame) and not plot_states.empty:
        ranking = plot_states.sort_values("Inspection priority score", ascending=False).head(max(1, int(max_plots)))
        for _, row in ranking.iterrows():
            score = _num(row.get("Inspection priority score"), 0)
            priority = "Critical" if score >= 80 else "High" if score >= 60 else "Medium" if score >= 35 else "Low"
            missing = []
            for label in ["Male shedding (%)", "Female silking (%)", "Female receptive silks (%)", "Male plant height (cm)", "Female plant height (cm)"]:
                if label not in row or pd.isna(row.get(label)):
                    missing.append(label)
            criticality = _num(row.get("Flowering-window criticality (%)"), 0)
            rationale = [f"Inspection priority score {score:.0f}/100."]
            if criticality >= 60:
                rationale.append("The plot is close to the predicted flowering window.")
            if missing:
                rationale.append("Missing: " + ", ".join(missing[:3]) + ("…" if len(missing) > 3 else "") + ".")
            days = _num(row.get("Days since observation"))
            if np.isfinite(days):
                rationale.append(f"Last field observation was {days:.0f} day(s) ago.")
            rows.append({
                "Recommendation type": "Plot inspection",
                "Priority": priority,
                "Plot ID": row.get("Plot ID"),
                "Plot": row.get("Plot"),
                "Title": f"Inspect {row.get('Plot', 'priority plot')}",
                "Rationale": " ".join(rationale),
                "Suggested measurements": ", ".join(missing) if missing else "Flowering percentages, pollen intensity, crop stress and plant height",
                "Score": score,
            })
    uncertainty = _num(state.get("Uncertainty (%)"), 100)
    if uncertainty >= 60:
        rows.append({
            "Recommendation type": "Data quality",
            "Priority": "High",
            "Plot ID": None,
            "Plot": None,
            "Title": "Reduce twin uncertainty",
            "Rationale": f"Current twin uncertainty is {uncertainty:.0f}%. Refresh stale field observations and verify weather, root-zone and satellite links before relying on recommendations.",
            "Suggested measurements": "Update daily flowering observations and inspect data-source freshness",
            "Score": uncertainty,
        })
    gap = _num(state.get("Predicted synchrony gap (days)"))
    if np.isfinite(gap) and abs(gap) >= 2:
        direction = "later" if gap < 0 else "earlier"
        rows.append({
            "Recommendation type": "Synchrony watch",
            "Priority": "High",
            "Plot ID": None,
            "Plot": None,
            "Title": "Verify flowering synchrony",
            "Rationale": f"The twin estimates a {gap:+.1f}-day male-minus-female flowering gap. Verify both parental flowering curves before changing management or future sowing offsets.",
            "Suggested measurements": f"Increase flowering observations; evaluate planting the male {direction} in a future replicated treatment",
            "Score": min(100, 50 + abs(gap) * 10),
        })
    return pd.DataFrame(rows).sort_values(["Score", "Priority"], ascending=[False, True]) if rows else pd.DataFrame()


def next_season_design(plot_states: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    if not isinstance(plot_states, pd.DataFrame) or plot_states.empty or "Male offset (days)" not in plot_states:
        return pd.DataFrame(), "No mapped treatment data are available."
    outcome_col = _first_column(plot_states, ["Seed-set percentage", "Predicted seed set (%)", "Pure seed (%)", "Seed yield (t/ha)"])
    if not outcome_col:
        offsets = sorted(pd.to_numeric(plot_states["Male offset (days)"], errors="coerce").dropna().astype(int).unique().tolist())
        if not offsets:
            return pd.DataFrame(), "No sowing offsets are available."
        center = int(round(np.median(offsets)))
        candidates = sorted(set([center - 2, center - 1, center, center + 1, center + 2, min(offsets), max(offsets)]))
        return pd.DataFrame({"Recommended offset (days)": candidates, "Purpose": ["Dense central learning" if abs(value-center) <= 2 else "Retain range anchor" for value in candidates]}), "No completed outcome data; recommendation preserves the observed range and adds denser central offsets."
    frame = plot_states[["Male offset (days)", outcome_col]].copy()
    frame["Male offset (days)"] = pd.to_numeric(frame["Male offset (days)"], errors="coerce")
    frame[outcome_col] = pd.to_numeric(frame[outcome_col], errors="coerce")
    frame = frame.dropna()
    if frame.empty:
        return pd.DataFrame(), "No complete offset-outcome pairs are available."
    summary = frame.groupby("Male offset (days)")[outcome_col].agg(["mean", "std", "count"]).reset_index()
    summary["SE"] = summary["std"] / np.sqrt(summary["count"].clip(lower=1))
    best = int(round(summary.loc[summary["mean"].idxmax(), "Male offset (days)"]))
    tested_min, tested_max = int(summary["Male offset (days)"].min()), int(summary["Male offset (days)"].max())
    candidates = sorted(set([best - 2, best - 1, best, best + 1, best + 2, tested_min, tested_max, 0]))
    result = pd.DataFrame({"Recommended offset (days)": candidates})
    result["Purpose"] = result["Recommended offset (days)"].map(lambda value: "Refine near current optimum" if abs(value-best) <= 2 else "Range/control anchor")
    result["Inside tested range"] = result["Recommended offset (days)"].between(tested_min, tested_max)
    return result, f"Exploratory design centred on the best observed {outcome_col} at {best:+d} days; retain blocking and independent replication."


def _metric_colour(value: float, minimum: float, maximum: float) -> str:
    if not np.isfinite(value):
        return "#9ca3af"
    if maximum <= minimum:
        return "#2563eb"
    ratio = float(np.clip((value - minimum) / (maximum - minimum), 0, 1))
    red = int(220 * ratio + 35 * (1-ratio))
    green = int(65 * ratio + 150 * (1-ratio))
    blue = int(55 * ratio + 220 * (1-ratio))
    return f"#{red:02x}{green:02x}{blue:02x}"


def _field_geometry(field: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not field:
        return None
    value = _loads(field.get("geometry_json"), field.get("geometry"))
    if not value:
        value = field.get("geometry")
    try:
        return validate_aoi_geometry(value) if value else None
    except Exception:
        return None


def _trial_geometry(trial: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not trial:
        return None
    value = trial.get("field_geometry") or _loads(trial.get("field_geometry_json"), None)
    try:
        return validate_aoi_geometry(value) if value else None
    except Exception:
        return None


def _geometry_bounds(geometry: Mapping[str, Any] | None) -> tuple[float, float, float, float] | None:
    """Return min-latitude, min-longitude, max-latitude, max-longitude."""
    if not geometry:
        return None
    coordinates = geometry.get("coordinates")
    points: list[tuple[float, float]] = []

    def walk(value: Any) -> None:
        if isinstance(value, (list, tuple)):
            if len(value) >= 2 and all(isinstance(item, (int, float, np.integer, np.floating)) for item in value[:2]):
                points.append((float(value[1]), float(value[0])))
            else:
                for item in value:
                    walk(item)

    walk(coordinates)
    if not points:
        return None
    latitudes = [point[0] for point in points]
    longitudes = [point[1] for point in points]
    return min(latitudes), min(longitudes), max(latitudes), max(longitudes)


def _plot_geometry(row: Mapping[str, Any]) -> dict[str, Any] | None:
    for key in ["Geometry", "geometry", "geometry_json"]:
        value = row.get(key)
        if key.endswith("_json"):
            value = _loads(value, None)
        if isinstance(value, Mapping):
            try:
                return validate_aoi_geometry(value)
            except Exception:
                continue
    return None


def twin_boundary_map(
    trial: Mapping[str, Any] | None,
    field: Mapping[str, Any] | None,
    plots: pd.DataFrame | None = None,
    *,
    plot_states: pd.DataFrame | None = None,
    metric: str | None = None,
) -> folium.Map:
    """Render the authoritative Twin field/trial geometry and internal plots.

    The mapped field is the parent spatial object. A linked trial can either match
    it exactly or occupy a contained subsection. Plot polygons are shown even when
    no analytical metric is available, so every saved Twin has a persistent visual
    representation of the land and experiment it represents.
    """
    field_geometry = _field_geometry(field)
    trial_geometry = _trial_geometry(trial)
    geometries = [geometry for geometry in [field_geometry, trial_geometry] if geometry]
    if geometries:
        centres = [geometry_centroid(geometry) for geometry in geometries]
        lat = float(np.mean([value[0] for value in centres]))
        lon = float(np.mean([value[1] for value in centres]))
    else:
        lat, lon = 19.43, -99.13

    map_object = folium.Map(location=[lat, lon], zoom_start=17, tiles=None, control_scale=True)
    folium.TileLayer("OpenStreetMap", name="Roads & places", show=True).add_to(map_object)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite imagery",
        show=False,
    ).add_to(map_object)
    folium.TileLayer("CartoDB positron", name="Light map", show=False).add_to(map_object)
    Fullscreen().add_to(map_object)
    MeasureControl(
        primary_length_unit="meters",
        secondary_length_unit="kilometers",
        primary_area_unit="sqmeters",
        secondary_area_unit="hectares",
    ).add_to(map_object)

    same_geometry = bool(
        field_geometry
        and trial_geometry
        and geometry_hash(field_geometry) == geometry_hash(trial_geometry)
    )
    if same_geometry:
        folium.GeoJson(
            field_geometry,
            name="Mapped field + trial boundary (exact match)",
            style_function=lambda _: {
                "color": "#166534", "weight": 4, "fillColor": "#22c55e", "fillOpacity": 0.08,
            },
            tooltip="Mapped field and maize-trial boundary — exact stored match",
        ).add_to(map_object)
    else:
        if field_geometry:
            field_name = str((field or {}).get("name") or "Mapped field")
            field_area = _num((field or {}).get("area_ha"))
            area_text = f" · {field_area:.3f} ha" if np.isfinite(field_area) else ""
            folium.GeoJson(
                field_geometry,
                name="Mapped field boundary",
                style_function=lambda _: {
                    "color": "#1d4ed8", "weight": 4, "fillColor": "#60a5fa", "fillOpacity": 0.06,
                },
                tooltip=f"Mapped field: {field_name}{area_text}",
            ).add_to(map_object)
        if trial_geometry:
            trial_name = str((trial or {}).get("name") or "Maize trial")
            boundary_mode = str((trial or {}).get("boundary_mode") or "Independent trial boundary")
            trial_area = _num((trial or {}).get("field_area_ha"))
            area_text = f" · {trial_area:.3f} ha" if np.isfinite(trial_area) else ""
            folium.GeoJson(
                trial_geometry,
                name="Maize-trial boundary",
                style_function=lambda _: {
                    "color": "#c2410c", "weight": 4, "dashArray": "8 6",
                    "fillColor": "#fb923c", "fillOpacity": 0.08,
                },
                tooltip=f"Trial: {trial_name} · {boundary_mode}{area_text}",
            ).add_to(map_object)

    plot_frame = plot_states if isinstance(plot_states, pd.DataFrame) and not plot_states.empty else plots
    if isinstance(plot_frame, pd.DataFrame) and not plot_frame.empty:
        # Experiment plots are block-level spatial containers. Their smaller
        # treatment units are the randomised observational units.
        for parent in experiment_plot_geometries(plot_frame):
            folium.GeoJson(
                parent["geometry"],
                name=f"Experiment plot {parent['label']}",
                style_function=lambda _: {
                    "color": "#111827", "weight": 4, "dashArray": "9 5", "fillOpacity": 0.01,
                },
                tooltip=f"Experiment plot {parent['label']} · {parent['units']} treatment units",
            ).add_to(map_object)
        values = pd.Series(dtype=float)
        if metric and metric in plot_frame.columns:
            values = pd.to_numeric(plot_frame[metric], errors="coerce")
        minimum = float(values.min()) if not values.empty and values.notna().any() else 0.0
        maximum = float(values.max()) if not values.empty and values.notna().any() else 1.0
        for _, row in plot_frame.iterrows():
            geom = _plot_geometry(row)
            if not geom:
                continue
            plot_name = str(row.get("Treatment unit") or row.get("Plot") or row.get("plot_code") or row.get("Plot ID") or "Treatment unit")
            treatment = str(row.get("Treatment") or row.get("treatment_label") or "").strip()
            block = str(row.get("Experiment plot") or row.get("Block") or row.get("block_no") or "").strip()
            female_parent = str(row.get("Female parent") or "").strip()
            male_parent = str(row.get("Male parent") or "").strip()
            parent_combination = str(row.get("Parent combination") or row.get("Variety / genotype") or "").strip()
            variety = parent_combination
            density = _num(row.get("Sowing density (plants/ha)"))
            sowing_date = str(row.get("Sowing date") or row.get("Female sowing") or "").strip()
            sowing_difference = _num(row.get("Male–female sowing difference (days)"))
            if metric and metric in plot_frame.columns:
                value = _num(row.get(metric))
                colour = _metric_colour(value, minimum, maximum)
                metric_text = f"<br>{metric}: {value:.2f}" if np.isfinite(value) else f"<br>{metric}: unavailable"
                fill_opacity = 0.55
            else:
                colour = "#7c3aed"
                metric_text = ""
                fill_opacity = 0.18
            details = "".join([
                f"<br>Experiment plot: {block}" if block else "",
                f"<br>Treatment: {treatment}" if treatment else "",
                f"<br>Female parent: {female_parent}" if female_parent else "",
                f"<br>Male parent: {male_parent}" if male_parent else "",
                f"<br>Parent combination: {parent_combination}" if parent_combination else "",
                f"<br>Sowing density: {density:,.0f} plants/ha" if np.isfinite(density) else "",
                f"<br>Sowing date: {sowing_date}" if sowing_date else "",
                f"<br>Male–female difference: {sowing_difference:+.0f} d" if np.isfinite(sowing_difference) else "",
            ])
            folium.GeoJson(
                geom,
                name=f"Treatment unit {plot_name}",
                style_function=lambda _, c=colour, opacity=fill_opacity: {
                    "color": c, "weight": 2, "fillColor": c, "fillOpacity": opacity,
                },
                tooltip=f"{plot_name}{details}{metric_text}",
            ).add_to(map_object)
        if metric and not values.empty and values.notna().any():
            LinearColormap(["#2396dc", "#dc4137"], vmin=minimum, vmax=maximum, caption=metric).add_to(map_object)

    centroid_geometry = trial_geometry or field_geometry
    if centroid_geometry:
        centroid_lat, centroid_lon = geometry_centroid(centroid_geometry)
        folium.CircleMarker(
            [centroid_lat, centroid_lon], radius=5, color="#111827", fill=True,
            fill_color="#ffffff", fill_opacity=1.0, tooltip="Twin analysis centroid",
        ).add_to(map_object)

    bounds = [_geometry_bounds(geometry) for geometry in geometries]
    bounds = [value for value in bounds if value]
    if bounds:
        minimum_lat = min(value[0] for value in bounds)
        minimum_lon = min(value[1] for value in bounds)
        maximum_lat = max(value[2] for value in bounds)
        maximum_lon = max(value[3] for value in bounds)
        map_object.fit_bounds([[minimum_lat, minimum_lon], [maximum_lat, maximum_lon]], padding=(24, 24))

    folium.LayerControl(collapsed=False).add_to(map_object)
    return map_object


def plot_state_map(trial: Mapping[str, Any] | None, field: Mapping[str, Any] | None, plot_states: pd.DataFrame, metric: str) -> folium.Map:
    """Backward-compatible plot-intelligence map backed by the full Twin map."""
    return twin_boundary_map(trial, field, plot_states=plot_states, metric=metric)


def _twin_coordinates(bundle: Mapping[str, Any]) -> tuple[float, float, str] | tuple[None, None, str]:
    field = bundle.get("field") or {}
    trial = bundle.get("trial") or {}
    for row, source in [(field, "mapped-field centroid"), (trial, "maize-trial centroid")]:
        lat = _num(row.get("centroid_lat"))
        lon = _num(row.get("centroid_lon"))
        if np.isfinite(lat) and np.isfinite(lon):
            return float(lat), float(lon), source
    for geometry, source in [
        (_loads(field.get("geometry_json"), field.get("geometry")), "mapped-field geometry"),
        (trial.get("field_geometry"), "maize-trial geometry"),
    ]:
        if geometry:
            try:
                lat, lon = geometry_centroid(validate_aoi_geometry(geometry))
                return float(lat), float(lon), source
            except Exception:
                pass
    return None, None, "No mapped centroid"



def _twin_geometry(bundle: Mapping[str, Any]) -> tuple[dict[str, Any] | None, str]:
    """Return the exact polygon to use for Twin satellite extraction."""
    field = bundle.get("field") or {}
    trial = bundle.get("trial") or {}
    candidates = [
        (_loads(field.get("geometry_json"), field.get("geometry")), "mapped-field boundary"),
        (trial.get("field_geometry"), "maize-trial boundary"),
    ]
    for value, source in candidates:
        if not value:
            continue
        try:
            return validate_aoi_geometry(value), source
        except Exception:
            continue
    return None, "No mapped field boundary"


def _twin_satellite_default_start(bundle: Mapping[str, Any]) -> date:
    return max(date(2017, 1, 1), _twin_weather_default_start(bundle))


def _sync_satellite_to_session(
    frame: pd.DataFrame,
    record: Mapping[str, Any],
    geometry: Mapping[str, Any],
    catalog: pd.DataFrame | None = None,
) -> None:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return
    st.session_state.satellite_time_series = frame.copy()
    st.session_state.satellite_aoi_geometry = dict(geometry)
    st.session_state.satellite_aoi_metadata = {
        "Source": "Persistent AgroLattice Twin satellite attachment",
        "Geometry hash": record.get("geometry_hash"),
        "Twin ID": record.get("link_id"),
    }
    st.session_state.satellite_processing_config = dict(record.get("request") or {})
    if isinstance(catalog, pd.DataFrame) and not catalog.empty:
        st.session_state.satellite_scene_catalog = catalog.copy()


def _satellite_mean_columns(frame: pd.DataFrame, indices: Sequence[str]) -> list[str]:
    lookup = {str(column).casefold(): str(column) for column in frame.columns}
    columns: list[str] = []
    for name in indices:
        for candidate in [f"{name} Mean", f"{name} mean", f"{name} Median", f"{name} median"]:
            match = lookup.get(candidate.casefold())
            if match and match not in columns:
                columns.append(match)
                break
    return columns


def _render_twin_satellite_manager(
    *,
    db: AgroLatticeTwinDatabase,
    link: Mapping[str, Any],
    bundle: Mapping[str, Any],
    context: Mapping[str, Any],
    key_prefix: str,
    compact: bool = False,
) -> None:
    """Search, process and persist Sentinel-2 observations for one Twin."""
    link_id = str(link["link_id"])
    ui_key = f"{key_prefix}_{link_id[:10]}"
    frame = db.satellite(link_id)
    catalog = db.satellite_catalog(link_id)
    record = db.satellite_record(link_id) or {}
    geometry, geometry_source = _twin_geometry(bundle)
    title = "Satellite data for this Twin"

    if compact:
        status = f"{len(frame):,} stored observations" if not frame.empty else "missing"
        st.caption(f"**{title}:** {status}")
    else:
        st.markdown(f"### {title}")
        st.caption(
            "Search Sentinel-2 Level-2A imagery for the exact linked field polygon, process field-level vegetation indices, "
            "and store the results inside the Twin database. The attached time series survives app restarts and is used automatically by Live state, snapshots, scenarios and the adaptive copilot."
        )

    missing_dependencies = [name for name, available in satellite_dependency_status().items() if not available]
    if missing_dependencies:
        st.error(
            "Twin satellite collection requires these geospatial packages: "
            + ", ".join(missing_dependencies)
            + ". Run INSTALL_SATELLITE_DEPENDENCIES.bat and restart AgroLattice."
        )
        if frame.empty:
            return

    if geometry is None:
        st.error("This Twin has no valid polygon boundary. Map the field or maize trial first, then return here.")
        return
    current_hash = geometry_hash(geometry)
    geometry_changed = bool(record and record.get("geometry_hash") and record.get("geometry_hash") != current_hash)

    if not frame.empty:
        usable = frame
        if "Status" in usable:
            usable = usable.loc[usable["Status"].astype(str).str.casefold().eq("usable")]
        latest = pd.to_datetime(usable.get("Date"), errors="coerce").max() if not usable.empty else pd.NaT
        metric_cols = st.columns(5)
        metric_cols[0].metric("Stored scenes", f"{len(frame):,}")
        metric_cols[1].metric("Usable scenes", f"{len(usable):,}")
        metric_cols[2].metric("First date", str(record.get("start_date") or pd.to_datetime(frame["Date"]).min().date()))
        metric_cols[3].metric("Latest date", str(record.get("end_date") or (latest.date() if pd.notna(latest) else "NA")))
        metric_cols[4].metric("Indices", ", ".join(record.get("indices") or []) or "NA")
        if geometry_changed:
            st.warning(
                "The linked field boundary has changed since the stored Sentinel-2 series was created. "
                "Select Replace stored series before collecting imagery for the new polygon; AgroLattice will not merge observations across different geometries."
            )
        else:
            st.success(f"Persistent Twin satellite data are linked to the current {geometry_source}.")
        with st.expander("Preview attached Sentinel-2 time series", expanded=False):
            mean_columns = _satellite_mean_columns(usable, record.get("indices") or []) if not usable.empty else []
            if mean_columns:
                plot = usable[["Date", *mean_columns]].melt("Date", var_name="Index", value_name="Field value")
                plot["Index"] = plot["Index"].str.replace(" Mean", "", regex=False).str.replace(" Median", "", regex=False)
                figure = px.line(plot, x="Date", y="Field value", color="Index", markers=True, title="Attached field-level Sentinel-2 indices")
                figure.update_yaxes(range=[-1, 1.25])
                st.plotly_chart(figure, width="stretch")
            st.dataframe(frame.tail(60), hide_index=True, width="stretch")
            downloads = st.columns(2)
            downloads[0].download_button(
                "Download attached satellite CSV",
                frame.to_csv(index=False).encode("utf-8"),
                file_name=f"agrolattice_twin_{link_id[:8]}_sentinel2.csv",
                mime="text/csv",
                key=f"{ui_key}_satellite_download",
                width="stretch",
            )
            if not catalog.empty:
                downloads[1].download_button(
                    "Download attached scene catalogue",
                    catalog.to_csv(index=False).encode("utf-8"),
                    file_name=f"agrolattice_twin_{link_id[:8]}_sentinel2_catalog.csv",
                    mime="text/csv",
                    key=f"{ui_key}_satellite_catalog_download",
                    width="stretch",
                )

    default_start = _twin_satellite_default_start(bundle)
    if record and record.get("start_date"):
        try:
            default_start = min(default_start, pd.Timestamp(record["start_date"]).date())
        except Exception:
            pass
    today = date.today()
    default_start = min(default_start, today)

    with st.expander("Search, process or update Sentinel-2", expanded=frame.empty):
        latitude, longitude = geometry_centroid(geometry)
        st.info(
            f"The exact {geometry_source} is selected automatically. Centroid: {latitude:.5f}, {longitude:.5f}. "
            "The field polygon—not a point buffer—is used to calculate the attached index statistics."
        )
        date_cols = st.columns(2)
        start_date = date_cols[0].date_input(
            "Satellite start date",
            value=default_start,
            min_value=date(2015, 6, 23),
            max_value=today,
            key=f"{ui_key}_satellite_start",
            help="Use the crop-season start or an earlier baseline date. Sentinel-2 coverage begins in 2015, with more consistent Level-2A coverage in later years.",
        )
        end_date = date_cols[1].date_input(
            "Satellite end date",
            value=today,
            min_value=date(2015, 6, 23),
            max_value=today,
            key=f"{ui_key}_satellite_end",
            help="Usually choose today. Return later and run the same workflow to extend the stored Twin series.",
        )
        first_row = st.columns(4)
        maximum_cloud = float(first_row[0].slider(
            "Maximum scene cloud (%)", 0, 100, 50, 5,
            key=f"{ui_key}_satellite_cloud",
            help="Catalogue-level cloud cover for the whole Sentinel-2 tile. Field-level clear pixels are checked again during processing.",
        ))
        maximum_items = int(first_row[1].number_input(
            "Maximum catalogue items", 10, 1000, 300, 10,
            key=f"{ui_key}_satellite_items",
            help="Caps the number of search results returned before the scene-selection rule is applied.",
        ))
        provider = first_row[2].selectbox(
            "Catalogue provider",
            ["Automatic failover", "Earth Search", "Planetary Computer"],
            key=f"{ui_key}_satellite_provider",
            help="Automatic failover tries Earth Search and uses Planetary Computer when needed.",
        )
        scene_rule = first_row[3].selectbox(
            "Scene-selection rule",
            ["Lowest-cloud scene per month", "Evenly sample maximum N", "Lowest-cloud maximum N", "All search results"],
            index=1,
            key=f"{ui_key}_satellite_rule",
            help="Even sampling gives broad seasonal coverage; lowest-cloud per month gives a compact long-term series.",
        )

        second_row = st.columns(4)
        selected_indices = second_row[0].multiselect(
            "Vegetation indices",
            list(SATELLITE_INDEX_REGISTRY),
            default=[name for name in ["NDVI", "NDMI"] if name in SATELLITE_INDEX_REGISTRY],
            key=f"{ui_key}_satellite_indices",
            help="NDVI summarises green canopy vigour. NDMI is sensitive to canopy moisture conditions but is not direct root-zone soil moisture.",
        )
        max_scenes = int(second_row[1].number_input(
            "Maximum scenes to process", 1, 300, 24, 1,
            key=f"{ui_key}_satellite_max_scenes",
            help="Raster processing can take time. Twenty-four scenes normally provide useful seasonal coverage without processing every acquisition.",
        ))
        resolution = float(second_row[2].selectbox(
            "Analysis resolution (m)", [10, 20, 30, 60], index=1,
            key=f"{ui_key}_satellite_resolution",
            help="Twenty metres balances detail and processing demand. Small plots may still contain mixed pixels.",
        ))
        minimum_usable = float(second_row[3].slider(
            "Minimum clear field pixels (%)", 1, 100, 30, 1,
            key=f"{ui_key}_satellite_min_clear",
            help="Scenes below this field-level clear-pixel threshold remain in the audit table but are not used as usable Twin observations.",
        ))
        advanced = st.columns(4)
        include_water = advanced[0].checkbox(
            "Include SCL water pixels", value=False,
            key=f"{ui_key}_satellite_water",
            help="Normally leave off for crop fields. Enable only when water pixels are genuinely part of the analysis area.",
        )
        force_refresh = advanced[1].checkbox(
            "Ignore processed-scene cache", value=False,
            key=f"{ui_key}_satellite_force",
            help="Reprocess scenes instead of using identical locally cached field/index calculations.",
        )
        replace_existing = advanced[2].checkbox(
            "Replace stored series", value=geometry_changed,
            key=f"{ui_key}_satellite_replace",
            help="Required after changing the field boundary. Otherwise newly processed scenes are merged by Sentinel-2 Scene ID.",
        )
        maximum_pixels = int(advanced[3].number_input(
            "Maximum pixels per scene", 50_000, 5_000_000, 2_000_000, 50_000,
            key=f"{ui_key}_satellite_pixels",
            help="A safety limit on raster size. Reduce it when memory is constrained or increase it for a large field at fine resolution.",
        ))

        if st.button(
            "Search, process and attach Sentinel-2 to this Twin",
            type="primary",
            key=f"{ui_key}_satellite_collect",
            width="stretch",
            help="Search public Sentinel-2 catalogues, process the selected scenes over the exact Twin polygon, save the time series permanently and use it immediately in Twin calculations.",
        ):
            if start_date > end_date:
                st.error("Satellite start date must not be after the end date.")
            elif not selected_indices:
                st.error("Select at least one vegetation index.")
            elif missing_dependencies:
                st.error("Install the satellite dependencies before collecting imagery.")
            else:
                progress = st.progress(0.0, text="Searching Sentinel-2 catalogues...")
                status_box = st.empty()
                try:
                    search_config = SatelliteSearchConfig(
                        start_date=str(start_date),
                        end_date=str(end_date),
                        maximum_scene_cloud_percent=maximum_cloud,
                        maximum_items=maximum_items,
                        provider_preference=provider,
                    )
                    items = search_sentinel2_scenes(geometry, search_config)
                    if not items:
                        progress.empty()
                        st.warning("No Sentinel-2 scenes matched this polygon, date range and cloud threshold.")
                        return
                    scene_catalog = scene_catalog_table(items)
                    subset = select_scene_subset(items, scene_rule, max_scenes)
                    if not subset:
                        progress.empty()
                        st.warning("The scene-selection rule did not select any scenes for processing.")
                        return
                    excluded_scl = set(DEFAULT_EXCLUDED_SCL)
                    if include_water:
                        excluded_scl.discard(6)
                    cache_dir = Path(context.get("satellite_cache_dir") or (db.path.parent / "sentinel2_crop_monitoring"))

                    def callback(position: int, total: int, scene_id: str) -> None:
                        progress.progress(position / max(total, 1), text=f"Processing Sentinel-2 scene {position}/{total}")
                        status_box.caption(scene_id)

                    processed = process_scene_collection(
                        subset,
                        geometry,
                        selected_indices,
                        cache_dir,
                        resolution_m=resolution,
                        minimum_usable_pixel_percent=minimum_usable,
                        excluded_scl_classes=excluded_scl,
                        maximum_pixels=maximum_pixels,
                        force_refresh=force_refresh,
                        progress_callback=callback,
                    )
                    providers = sorted({scene_provider(item) for item in items if scene_provider(item) != "Unknown"})
                    metadata = {
                        "generated_utc": utc_now(),
                        "providers": providers,
                        "searched_scenes": len(items),
                        "processed_scenes": len(subset),
                        "geometry_source": geometry_source,
                    }
                    request = {
                        "Twin": link.get("name"),
                        "Twin ID": link_id,
                        "Country": context.get("selected_country"),
                        "Geometry source": geometry_source,
                        "Geometry hash": current_hash,
                        "Start date": str(start_date),
                        "End date": str(end_date),
                        "Maximum scene cloud (%)": maximum_cloud,
                        "Maximum catalogue items": maximum_items,
                        "Catalogue provider": provider,
                        "Providers used": providers,
                        "Scene-selection rule": scene_rule,
                        "Maximum scenes processed": max_scenes,
                        "Indices": selected_indices,
                        "Analysis resolution (m)": resolution,
                        "Minimum clear field pixels (%)": minimum_usable,
                        "Excluded SCL classes": sorted(excluded_scl),
                    }
                    result = db.save_satellite(
                        link_id,
                        processed,
                        geometry=geometry,
                        indices=selected_indices,
                        catalog=scene_catalog,
                        metadata=metadata,
                        request=request,
                        merge=not replace_existing,
                    )
                    attached = db.satellite(link_id)
                    attached_record = db.satellite_record(link_id) or {}
                    _sync_satellite_to_session(attached, attached_record, geometry, db.satellite_catalog(link_id))
                    progress.progress(1.0, text="Twin satellite data saved.")
                    st.success(
                        f"Sentinel-2 attached permanently: {result['rows']:,} stored scenes, "
                        f"{result['usable_rows']:,} usable, from {result['start_date']} to {result['end_date']}."
                    )
                    st.rerun()
                except Exception as error:
                    progress.empty()
                    st.error(f"Twin satellite retrieval failed: {type(error).__name__}: {error}")

    if not frame.empty:
        with st.expander("Remove attached satellite data", expanded=False):
            st.warning(
                "This removes only the persistent Sentinel-2 series owned by this Twin. "
                "It does not delete the field, trial, processed-scene cache or standalone Satellite Crop Monitoring exports."
            )
            confirm = st.checkbox(
                "I understand that the attached Twin satellite history will be deleted",
                key=f"{ui_key}_satellite_clear_confirm",
            )
            if st.button(
                "Delete attached Twin satellite data",
                disabled=not confirm,
                key=f"{ui_key}_satellite_clear",
                width="stretch",
            ):
                db.clear_satellite(link_id)
                st.success("Attached Twin satellite history deleted.")
                st.rerun()


def _twin_weather_default_start(bundle: Mapping[str, Any]) -> date:
    candidates: list[pd.Timestamp] = []
    trial = bundle.get("trial") or {}
    trial_date = _to_timestamp(trial.get("female_sowing_date"))
    if pd.notna(trial_date):
        candidates.append(trial_date)
    plots = bundle.get("plots")
    if isinstance(plots, pd.DataFrame) and not plots.empty:
        for column_name in ["Female sowing", "Male sowing", "female_sowing_date", "male_sowing_date"]:
            column = _first_column(plots, [column_name])
            if column:
                candidates.extend(pd.to_datetime(plots[column], errors="coerce").dropna().tolist())
    if candidates:
        return min(pd.Timestamp(value).date() for value in candidates)
    field = bundle.get("field") or {}
    year = int(_num(field.get("season_year"), date.today().year))
    year = min(max(year, 1981), date.today().year)
    return date(year, 1, 1)


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    values = [lat1, lon1, lat2, lon2]
    if not all(np.isfinite(_num(value)) for value in values):
        return np.nan
    radius = 6371.0088
    p1, p2 = math.radians(float(lat1)), math.radians(float(lat2))
    dp = math.radians(float(lat2) - float(lat1))
    dl = math.radians(float(lon2) - float(lon1))
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))


def _sync_weather_to_session(frame: pd.DataFrame, record: Mapping[str, Any], trial: Mapping[str, Any] | None) -> None:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return
    st.session_state.daily_weather_raw = frame.copy()
    st.session_state.daily_weather_metadata = dict(record.get("metadata") or {})
    st.session_state.daily_weather_request = dict(record.get("request") or {})
    base = _num((trial or {}).get("base_temperature_c"), 10.0)
    upper = _num((trial or {}).get("upper_temperature_c"), 30.0)
    try:
        st.session_state.phenology_weather = prepare_weather(frame, base_temperature_c=base, upper_temperature_c=upper)
    except Exception:
        pass


def _render_twin_weather_manager(
    *,
    db: AgroLatticeTwinDatabase,
    link: Mapping[str, Any],
    bundle: Mapping[str, Any],
    context: Mapping[str, Any],
    key_prefix: str,
    compact: bool = False,
) -> None:
    """Render direct, persistent NASA POWER acquisition for one Twin."""
    link_id = str(link["link_id"])
    ui_key = f"{key_prefix}_{link_id[:10]}"
    frame = db.weather(link_id)
    record = db.weather_record(link_id) or {}
    latitude, longitude, coordinate_source = _twin_coordinates(bundle)
    title = "Weather for this Twin"
    if compact:
        if not frame.empty:
            status = f"{len(frame):,} days · {record.get('start_date')} to {record.get('end_date')}"
        elif isinstance(bundle.get("weather"), pd.DataFrame) and not bundle.get("weather").empty:
            status = "not yet attached; linked trial weather is available as a fallback"
        elif isinstance(context.get("daily_weather"), pd.DataFrame) and not context.get("daily_weather").empty:
            status = "not yet attached; active-session weather is available temporarily"
        else:
            status = "missing"
        st.caption(f"**{title}:** {status}")
    else:
        st.markdown(f"### {title}")
        st.caption(
            "Collect NASA POWER daily weather from the linked field centroid and save it inside the Twin database. "
            "The attached series remains available after restarting AgroLattice and is used automatically by Live state, scenarios and the adaptive copilot."
        )

    if latitude is None or longitude is None:
        st.error("This Twin has no usable field or trial centroid. Map the field boundary first, then return here.")
        return

    location_distance = np.nan
    if record:
        location_distance = _distance_km(latitude, longitude, _num(record.get("latitude")), _num(record.get("longitude")))
    if not frame.empty:
        status_cols = st.columns(4)
        status_cols[0].metric("Stored days", f"{len(frame):,}")
        status_cols[1].metric("First date", str(record.get("start_date") or pd.to_datetime(frame["DATE"]).min().date()))
        status_cols[2].metric("Last date", str(record.get("end_date") or pd.to_datetime(frame["DATE"]).max().date()))
        status_cols[3].metric("Location", f"{latitude:.4f}, {longitude:.4f}")
        if np.isfinite(location_distance) and location_distance > 0.25:
            st.warning(
                f"The mapped centroid is now {location_distance:.2f} km from the coordinates used for the stored weather. "
                "This can happen after editing the field boundary. Replace the series rather than merging it."
            )
        else:
            st.success(f"Persistent Twin weather is ready and linked to the current {coordinate_source}.")
        available_canonical = sum(
            1 for variable in TWIN_CANONICAL_WEATHER_VARIABLES
            if variable in frame and pd.to_numeric(frame[variable], errors="coerce").notna().any()
        )
        st.caption(f"Canonical weather coverage: {available_canonical}/19 variables contain data; all 19 columns are retained in the attachment.")
        with st.expander("Preview attached daily weather", expanded=False):
            canonical_tab, raw_tab, provenance_tab = st.tabs(["Canonical 19 variables", "NASA source columns", "Variable provenance"])
            with canonical_tab:
                canonical_columns = ["DATE"] + [name for name in TWIN_CANONICAL_WEATHER_VARIABLES if name in frame]
                st.dataframe(frame[canonical_columns].tail(60), hide_index=True, width="stretch")
            with raw_tab:
                raw_columns = ["DATE"] + [code for code in TWIN_POWER_PARAMETER_REGISTRY if code in frame]
                st.dataframe(frame[raw_columns].tail(60), hide_index=True, width="stretch")
            with provenance_tab:
                provenance = (record.get("metadata") or {}).get("canonical_provenance") or {}
                rows = []
                for variable in TWIN_CANONICAL_WEATHER_VARIABLES:
                    item = provenance.get(variable, {}) if isinstance(provenance, Mapping) else {}
                    rows.append({"Variable": variable, "Source": item.get("source", TWIN_CANONICAL_SOURCE_MAP.get(variable)), "Available rows": item.get("available_rows"), "Note": item.get("note", "")})
                st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
            st.download_button(
                "Download attached weather CSV",
                frame.to_csv(index=False).encode("utf-8"),
                file_name=f"agrolattice_twin_{link_id[:8]}_weather.csv",
                mime="text/csv",
                key=f"{ui_key}_weather_download",
                width="stretch",
            )

    default_start = _twin_weather_default_start(bundle)
    if record and record.get("start_date"):
        try:
            default_start = min(default_start, pd.Timestamp(record["start_date"]).date())
        except Exception:
            pass
    today = date.today()
    default_end = today
    if default_start > default_end:
        default_start = default_end

    with st.expander("Collect or update weather", expanded=frame.empty):
        st.info(
            f"Coordinates are filled automatically from the {coordinate_source}: "
            f"{latitude:.5f}, {longitude:.5f}. The start date defaults to the earliest linked sowing date when available."
        )
        date_cols = st.columns(2)
        start_date = date_cols[0].date_input(
            "Weather start date",
            value=default_start,
            min_value=date(1981, 1, 1),
            max_value=today,
            key=f"{ui_key}_weather_start",
            help="Use a date on or before the earliest male or female sowing date so the Twin can calculate complete GDD accumulation.",
        )
        end_date = date_cols[1].date_input(
            "Weather end date",
            value=default_end,
            min_value=date(1981, 1, 1),
            max_value=today,
            key=f"{ui_key}_weather_end",
            help="Usually choose today. Return later and update the series as the season progresses.",
        )
        parameter_labels = {
            f"{code} — {details['label']} ({details['canonical']})": code
            for code, details in TWIN_POWER_PARAMETER_REGISTRY.items()
        }
        default_labels = list(parameter_labels)
        selected_labels = st.multiselect(
            "NASA POWER source variables",
            list(parameter_labels),
            default=default_labels,
            key=f"{ui_key}_weather_parameters",
            help=(
                "All 15 direct NASA POWER variables are selected by default. AgroLattice then creates the full 19-variable "
                "canonical Twin profile, including FAO-56 ETo and transparent precipitation/soil-heat compatibility columns."
            ),
        )
        selected_parameters = [parameter_labels[label] for label in selected_labels]
        st.caption(
            "Full Twin weather profile: 15 direct NASA POWER variables + 4 explicitly labelled derived/compatibility variables = 19 canonical variables."
        )
        option_cols = st.columns(3)
        time_standard = option_cols[0].selectbox(
            "Time standard",
            ["LST", "UTC"],
            key=f"{ui_key}_weather_time_standard",
            help="LST uses local solar time and is normally the clearest choice for crop-development work.",
        )
        force_refresh = option_cols[1].checkbox(
            "Ignore NASA cache",
            value=False,
            key=f"{ui_key}_weather_force",
            help="Download again instead of reusing an identical request already stored in the local cache.",
        )
        replace_existing = option_cols[2].checkbox(
            "Replace stored series",
            value=bool(np.isfinite(location_distance) and location_distance > 0.25),
            key=f"{ui_key}_weather_replace",
            help="Use this after moving or redrawing the field. Otherwise new dates are merged into the existing Twin weather table.",
        )
        if st.button(
            "Collect and attach weather to this Twin",
            type="primary",
            key=f"{ui_key}_weather_fetch",
            width="stretch",
            help="Fetch NASA POWER daily data at the mapped centroid, persist it to this Twin and immediately use it in all Twin calculations.",
        ):
            if start_date > end_date:
                st.error("Weather start date must not be after the end date.")
            elif not selected_parameters:
                st.error("Select at least one weather variable.")
            else:
                cache_dir = Path(context.get("daily_weather_cache_dir") or (db.path.parent / "nasa_power_daily"))
                progress = st.progress(0.0, text="Preparing NASA POWER request...")
                def callback(index: int, total: int, message: str) -> None:
                    progress.progress(min(1.0, index / max(total, 1)), text=message)
                try:
                    raw, metadata = _fetch_twin_weather_profile(
                        latitude=latitude,
                        longitude=longitude,
                        start_date=start_date,
                        end_date=end_date,
                        cache_dir=cache_dir,
                        parameters=selected_parameters,
                        time_standard=time_standard,
                        force_refresh=force_refresh,
                        progress_callback=callback,
                    )
                    request = {
                        "Twin": link.get("name"),
                        "Twin ID": link_id,
                        "Country": context.get("selected_country"),
                        "Coordinate source": coordinate_source,
                        "Latitude": latitude,
                        "Longitude": longitude,
                        "Start date": str(start_date),
                        "End date": str(end_date),
                        "Parameters": selected_parameters,
                        "Time standard": time_standard,
                    }
                    result = db.save_weather(
                        link_id,
                        raw,
                        latitude=latitude,
                        longitude=longitude,
                        parameters=selected_parameters,
                        time_standard=time_standard,
                        metadata=metadata,
                        request=request,
                        merge=not replace_existing,
                    )
                    attached = db.weather(link_id)
                    attached_record = db.weather_record(link_id) or {}
                    _sync_weather_to_session(attached, attached_record, bundle.get("trial"))
                    progress.progress(1.0, text="Twin weather saved.")
                    st.success(
                        f"Weather attached permanently: {result['rows']:,} daily rows from "
                        f"{result['start_date']} to {result['end_date']}."
                    )
                    st.rerun()
                except Exception as error:
                    progress.empty()
                    st.error(f"Twin weather retrieval failed: {type(error).__name__}: {error}")

    if not frame.empty:
        with st.expander("Remove attached weather", expanded=False):
            st.warning("This removes only the persistent weather series owned by this Twin. It does not delete the field, trial, NASA cache or country climate dataset.")
            confirm = st.checkbox("I understand that the attached Twin weather will be deleted", key=f"{ui_key}_weather_clear_confirm")
            if st.button("Delete attached Twin weather", disabled=not confirm, key=f"{ui_key}_weather_clear", width="stretch"):
                db.clear_weather(link_id)
                st.success("Attached Twin weather deleted.")
                st.rerun()


def _root_zone_default_crop(bundle: Mapping[str, Any], library: Mapping[str, Any]) -> str:
    trial = bundle.get("trial") or {}
    field = bundle.get("field") or {}
    candidates = [
        "Maize" if trial else None,
        field.get("current_crop"), field.get("crop"),
        (bundle.get("active_project") or {}).get("crop") if isinstance(bundle.get("active_project"), Mapping) else None,
    ]
    available = list((library.get("crops") or {}).keys())
    normalised = {str(name).casefold(): str(name) for name in available}
    for candidate in candidates:
        if candidate and str(candidate).casefold() in normalised:
            return normalised[str(candidate).casefold()]
    return "Maize" if "Maize" in available else (available[0] if available else "Maize")


def _root_zone_irrigation_upload(uploaded_file) -> pd.DataFrame:
    if uploaded_file is None:
        return pd.DataFrame()
    frame = pd.read_csv(uploaded_file)
    date_col = _first_column(frame, ["Date", "DATE", "date"])
    amount_col = _first_column(frame, ["Gross irrigation (mm)", "Irrigation (mm)", "Amount (mm)"])
    if not date_col or not amount_col:
        raise AgroLatticeTwinError("Irrigation CSV must contain Date and Gross irrigation (mm).")
    result = pd.DataFrame({
        "Date": pd.to_datetime(frame[date_col], errors="coerce"),
        "Gross irrigation (mm)": pd.to_numeric(frame[amount_col], errors="coerce"),
    }).dropna()
    return result


def _render_twin_root_zone_manager(
    *,
    db: AgroLatticeTwinDatabase,
    link: Mapping[str, Any],
    bundle: Mapping[str, Any],
    context: Mapping[str, Any],
    key_prefix: str,
    compact: bool = False,
) -> None:
    link_id = str(link["link_id"])
    ui_key = f"{key_prefix}_{link_id[:10]}"
    balance = db.root_zone(link_id)
    record = db.root_zone_record(link_id) or {}
    weather = db.weather(link_id)
    weather_record = db.weather_record(link_id) or {}

    if compact:
        status = f"{len(balance):,} days · {record.get('start_date')} to {record.get('end_date')}" if not balance.empty else "missing"
        st.caption(f"**Root-zone water for this Twin:** {status}")
    else:
        st.markdown("### Root-zone water for this Twin")
        st.caption(
            "Run the FAO-56 daily soil-water balance directly from the Twin's persistent weather, save every daily row, "
            "and reuse it after restarting AgroLattice. Re-run the balance after extending weather or changing soil, crop or irrigation assumptions."
        )

    if weather.empty:
        st.warning("Attach Twin weather first. The root-zone model uses the Twin's saved daily temperature, radiation, humidity, wind, pressure and precipitation.")
        return

    if not balance.empty:
        status_cols = st.columns(5)
        status_cols[0].metric("Stored days", f"{len(balance):,}")
        status_cols[1].metric("First date", str(record.get("start_date")))
        status_cols[2].metric("Last date", str(record.get("end_date")))
        latest_ks = pd.to_numeric(balance.get("Ks"), errors="coerce").dropna()
        status_cols[3].metric("Latest Ks", f"{latest_ks.iloc[-1]:.2f}" if not latest_ks.empty else "NA")
        stress_days = int(pd.Series(balance.get("Stress day", False)).fillna(False).astype(bool).sum())
        status_cols[4].metric("Stress days", f"{stress_days:,}")
        if weather_record.get("updated_at") and record.get("weather_updated_at") and str(weather_record.get("updated_at")) != str(record.get("weather_updated_at")):
            st.warning("Twin weather has changed since this root-zone series was generated. Re-run the root-zone model to incorporate the new dates or variables.")
        else:
            st.success("Persistent Twin root-zone data are ready and used automatically by Live state, scenarios and the adaptive copilot.")
        with st.expander("Preview attached root-zone series", expanded=False):
            chart = go.Figure()
            chart.add_trace(go.Scatter(x=balance["Date"], y=balance.get("Depletion end (mm)"), name="Depletion", mode="lines"))
            chart.add_trace(go.Scatter(x=balance["Date"], y=balance.get("RAW (mm)"), name="RAW", mode="lines", line={"dash": "dash"}))
            chart.add_trace(go.Scatter(x=balance["Date"], y=balance.get("TAW (mm)"), name="TAW", mode="lines", line={"dash": "dot"}))
            chart.update_layout(title="Persistent Twin root-zone depletion", xaxis_title="Date", yaxis_title="Water depth (mm)", hovermode="x unified")
            st.plotly_chart(chart, width="stretch")
            st.dataframe(balance.tail(90), hide_index=True, width="stretch")
            st.download_button("Download attached root-zone CSV", balance.to_csv(index=False).encode("utf-8"), file_name=f"agrolattice_twin_{link_id[:8]}_root_zone.csv", mime="text/csv", key=f"{ui_key}_root_download", width="stretch")

    library = context.get("validated_crop_library") if isinstance(context.get("validated_crop_library"), Mapping) else {"crops": {}}
    crop_options = sorted((library.get("crops") or {}).keys()) or sorted(CROP_ROOT_DEFAULTS)
    default_crop = _root_zone_default_crop(bundle, library)
    default_crop_index = crop_options.index(default_crop) if default_crop in crop_options else 0
    saved_settings = record.get("settings") or {}

    with st.expander("Run or update root-zone balance", expanded=balance.empty):
        crop = st.selectbox("Crop", crop_options, index=default_crop_index, key=f"{ui_key}_root_crop", help="Select the crop whose stage-specific Kc, rooting and depletion assumptions should be used.")
        profiles = available_water_profiles(library, crop) if library.get("crops") else []
        if profiles:
            saved_profile = str(record.get("profile") or saved_settings.get("profile") or profiles[0])
            profile = st.selectbox("Water-parameter profile", profiles, index=profiles.index(saved_profile) if saved_profile in profiles else 0, key=f"{ui_key}_root_profile")
            custom_days = 120
            constant_kc = None
        else:
            profile = "User-defined fallback"
            fallback_cols = st.columns(2)
            custom_days = int(fallback_cols[0].number_input("Simulation length (days)", 1, 730, int(saved_settings.get("custom_season_days", 120)), key=f"{ui_key}_root_days"))
            constant_kc = float(fallback_cols[1].number_input("Constant Kc", 0.05, 2.0, float(saved_settings.get("constant_kc", 1.0)), 0.01, key=f"{ui_key}_root_kc"))
            st.warning("No validated stage profile is available for this crop. The constant Kc and user-defined duration are explicit fallback assumptions.")

        default_start = _twin_weather_default_start(bundle)
        weather_min = pd.to_datetime(weather["DATE"], errors="coerce").min().date()
        weather_max = pd.to_datetime(weather["DATE"], errors="coerce").max().date()
        default_start = min(max(default_start, weather_min), weather_max)
        try:
            planting_value = pd.Timestamp(saved_settings.get("planting_date") or default_start).date()
        except Exception:
            planting_value = default_start
        planting_value = min(max(planting_value, weather_min), weather_max)
        planting_date = st.date_input("Planting or season start date", value=planting_value, min_value=weather_min, max_value=weather_max, key=f"{ui_key}_root_planting")
        duration_strategy = st.selectbox("Stage-duration choice", ["Midpoint", "Minimum", "Maximum"], index=["Midpoint","Minimum","Maximum"].index(saved_settings.get("duration_strategy","Midpoint")) if saved_settings.get("duration_strategy","Midpoint") in ["Midpoint","Minimum","Maximum"] else 0, key=f"{ui_key}_root_duration")

        roots = crop_root_defaults(crop)
        root_cols = st.columns(4)
        initial_root = float(root_cols[0].number_input("Initial root depth (m)", 0.05, 3.0, float(saved_settings.get("initial_root_depth_m", min(0.20, roots["root_min_m"]))), 0.05, key=f"{ui_key}_root_initial"))
        max_root = float(root_cols[1].number_input("Maximum root depth (m)", 0.10, 4.0, float(saved_settings.get("maximum_root_depth_m", (roots["root_min_m"]+roots["root_max_m"])/2)), 0.05, key=f"{ui_key}_root_max"))
        fallback_p = float(root_cols[2].number_input("Fallback depletion fraction p", 0.10, 0.80, float(saved_settings.get("fallback_p", roots["p"])), 0.01, key=f"{ui_key}_root_p"))
        dynamic_roots = root_cols[3].checkbox("Dynamic root growth", value=bool(saved_settings.get("dynamic_root_growth", True)), key=f"{ui_key}_root_dynamic")

        soil_modes = ["FAO screening preset", "Custom field capacity and wilting point"]
        saved_soil_mode = str(saved_settings.get("soil_mode") or soil_modes[0])
        soil_mode = st.radio("Soil-water input", soil_modes, index=soil_modes.index(saved_soil_mode) if saved_soil_mode in soil_modes else 0, horizontal=True, key=f"{ui_key}_root_soil_mode")
        if soil_mode == "FAO screening preset":
            preset_names = list(SOIL_PRESETS)
            saved_preset = saved_settings.get("soil_preset") or preset_names[0]
            preset = st.selectbox("Soil texture preset", preset_names, index=preset_names.index(saved_preset) if saved_preset in preset_names else 0, key=f"{ui_key}_root_soil_preset")
            soil = soil_profile_from_preset(preset)
            theta_fc, theta_wp = soil.theta_fc, soil.theta_wp
        else:
            soil_cols = st.columns(2)
            theta_fc = float(soil_cols[0].number_input("Field capacity (m³ m⁻³)", 0.01, 0.70, float(saved_settings.get("theta_fc", 0.30)), 0.01, key=f"{ui_key}_root_fc"))
            theta_wp = float(soil_cols[1].number_input("Permanent wilting point (m³ m⁻³)", 0.001, 0.60, float(saved_settings.get("theta_wp", 0.15)), 0.01, key=f"{ui_key}_root_wp"))
            preset = None
            soil = SoilProfile(name="Twin custom soil", theta_fc=theta_fc, theta_wp=theta_wp, source="User supplied", evidence_grade="User supplied").validated()

        hyd_cols = st.columns(4)
        initial_depletion = float(hyd_cols[0].slider("Initial depletion (% TAW)", 0, 100, int(round(100*float(saved_settings.get("initial_depletion_fraction",0.20)))), 1, key=f"{ui_key}_root_depletion"))/100.0
        runoff_method = hyd_cols[1].selectbox("Runoff method", ["None", "Fixed fraction", "NRCS curve number"], index=["None","Fixed fraction","NRCS curve number"].index(saved_settings.get("runoff_method","None")) if saved_settings.get("runoff_method","None") in ["None","Fixed fraction","NRCS curve number"] else 0, key=f"{ui_key}_root_runoff")
        runoff_fraction = float(hyd_cols[2].slider("Runoff fraction", 0.0, 0.9, float(saved_settings.get("runoff_fraction",0.0)), 0.05, disabled=runoff_method!="Fixed fraction", key=f"{ui_key}_root_runoff_fraction"))
        curve_number = float(hyd_cols[3].number_input("NRCS curve number", 30, 100, int(saved_settings.get("curve_number",75)), 1, disabled=runoff_method!="NRCS curve number", key=f"{ui_key}_root_cn"))

        irrigation_options = ["Rainfed", "Irrigate at RAW", "Deficit irrigation", "Sensor-triggered", "Fixed interval", "Uploaded schedule"]
        saved_irrigation_mode = saved_settings.get("irrigation_mode", "Rainfed")
        irrigation_mode = st.selectbox(
            "Irrigation strategy", irrigation_options,
            index=irrigation_options.index(saved_irrigation_mode) if saved_irrigation_mode in irrigation_options else 0,
            key=f"{ui_key}_root_irrigation",
            help="Sensor-triggered simulates automatic irrigation from a registered soil-moisture sensor threshold. It does not send commands to physical pumps or valves.",
        )
        irr_cols = st.columns(4)
        efficiency = float(irr_cols[0].number_input("Application efficiency", 0.10, 1.00, float(saved_settings.get("application_efficiency",0.75)), 0.05, key=f"{ui_key}_root_eff"))
        max_application = float(irr_cols[1].number_input("Maximum gross application (mm)", 0.0, 250.0, float(saved_settings.get("maximum_gross_application_mm",60.0)), 1.0, key=f"{ui_key}_root_max_app"))
        interval = int(irr_cols[2].number_input("Fixed interval (days)", 1, 60, int(saved_settings.get("fixed_interval_days",7)), 1, disabled=irrigation_mode!="Fixed interval", key=f"{ui_key}_root_interval"))
        fixed_amount = float(irr_cols[3].number_input("Fixed gross application (mm)", 0.0, 250.0, float(saved_settings.get("fixed_gross_application_mm",25.0)), 1.0, disabled=irrigation_mode not in {"Fixed interval","Sensor-triggered"}, key=f"{ui_key}_root_fixed"))
        strategy_cols = st.columns(2)
        trigger = float(strategy_cols[0].number_input("Trigger as × RAW", 0.1, 2.0, float(saved_settings.get("trigger_fraction_of_raw",1.0)), 0.05, disabled=irrigation_mode not in {"Irrigate at RAW","Deficit irrigation"}, key=f"{ui_key}_root_trigger"))
        refill = float(strategy_cols[1].number_input("Refill fraction", 0.0, 1.0, float(saved_settings.get("refill_fraction",1.0 if irrigation_mode=="Irrigate at RAW" else 0.5)), 0.05, disabled=irrigation_mode not in {"Irrigate at RAW","Deficit irrigation"}, key=f"{ui_key}_root_refill"))
        sensor_readings_for_model = pd.DataFrame()
        sensor_id = None
        sensor_name = ""
        sensor_metric = str(saved_settings.get("sensor_metric") or "Volumetric water content (%)")
        sensor_threshold = float(saved_settings.get("sensor_trigger_threshold", 20.0))
        sensor_max_age = int(saved_settings.get("sensor_max_age_days", 2))
        if irrigation_mode == "Sensor-triggered":
            st.info("This option reproduces threshold-based automatic irrigation in the persistent Twin. Register/import the real sensor under Sensors, irrigation & nutrition first. The result is a simulation and audit trail, not a hardware command.")
            sensor_table = bundle.get("sensors") if isinstance(bundle.get("sensors"), pd.DataFrame) else pd.DataFrame()
            if not sensor_table.empty and "sensor_type" in sensor_table:
                moisture_mask = sensor_table["sensor_type"].astype(str).str.contains("moisture|tension|water", case=False, regex=True)
                sensor_table = sensor_table.loc[moisture_mask].copy()
            if sensor_table.empty:
                st.warning("No soil-moisture or soil-water-tension sensor is registered for this Twin's mapped field.")
            else:
                sensor_labels = {
                    f"{row.get('name')} · {row.get('sensor_type')} · {row.get('unit') or 'unit'} · {row.get('depth_cm') or 'depth NA'} cm": str(row.get("sensor_id"))
                    for _, row in sensor_table.iterrows()
                }
                saved_sensor_id = str(saved_settings.get("sensor_id") or "")
                label_values = list(sensor_labels)
                default_sensor_index = next((i for i,label in enumerate(label_values) if sensor_labels[label] == saved_sensor_id), 0)
                selected_sensor_label = st.selectbox("Controlling soil sensor", label_values, index=default_sensor_index, key=f"{ui_key}_root_sensor")
                sensor_id = sensor_labels[selected_sensor_label]
                sensor_row = sensor_table.loc[sensor_table["sensor_id"].astype(str).eq(sensor_id)].iloc[0]
                sensor_name = str(sensor_row.get("name") or sensor_id)
                metric_options = ["Volumetric water content (%)", "Volumetric water content (fraction)", "Soil water tension (kPa)", "Raw sensor value"]
                sensor_cols = st.columns(3)
                sensor_metric = sensor_cols[0].selectbox("Sensor interpretation", metric_options, index=metric_options.index(sensor_metric) if sensor_metric in metric_options else 0, key=f"{ui_key}_root_sensor_metric")
                threshold_default = sensor_threshold
                sensor_threshold = float(sensor_cols[1].number_input("Irrigation trigger threshold", value=float(threshold_default), step=0.5, key=f"{ui_key}_root_sensor_threshold", help="VWC triggers when the reading is at or below the threshold. Soil-water tension triggers when the reading is at or above the threshold."))
                sensor_max_age = int(sensor_cols[2].number_input("Maximum reading age (days)", 0, 30, sensor_max_age, 1, key=f"{ui_key}_root_sensor_age"))
                all_readings = bundle.get("readings") if isinstance(bundle.get("readings"), pd.DataFrame) else pd.DataFrame()
                if not all_readings.empty and "sensor_id" in all_readings:
                    sensor_readings_for_model = all_readings.loc[all_readings["sensor_id"].astype(str).eq(sensor_id), [column for column in ["timestamp", "value"] if column in all_readings]].copy()
                st.caption(f"Available readings for selected sensor: {len(sensor_readings_for_model):,}. Fixed gross application when triggered: {fixed_amount:.1f} mm.")
                if sensor_readings_for_model.empty:
                    st.warning("The selected sensor has no imported readings. The model will not create sensor-triggered irrigation events until readings are available.")
        uploaded = st.file_uploader("Optional irrigation schedule CSV", type=["csv"], key=f"{ui_key}_root_upload", help="Required only for Uploaded schedule. Columns: Date and Gross irrigation (mm).") if irrigation_mode=="Uploaded schedule" else None
        capillary = float(st.number_input("Capillary rise (mm day⁻¹)", 0.0, 20.0, float(saved_settings.get("capillary_rise_mm_day",0.0)), 0.1, key=f"{ui_key}_root_capillary"))
        adjust_p = st.checkbox("Adjust p for daily ETc", value=bool(saved_settings.get("adjust_p_for_etc",True)), key=f"{ui_key}_root_adjust_p")

        if st.button("Run and attach root-zone balance to this Twin", type="primary", key=f"{ui_key}_root_run", width="stretch"):
            try:
                schedule = build_soil_stage_schedule(library, crop, profile, planting_date, duration_strategy=duration_strategy, custom_season_days=custom_days, constant_kc=constant_kc, constant_p=fallback_p)
                requested_end = pd.to_datetime(schedule["End date"], errors="coerce").max()
                available_weather = weather.loc[pd.to_datetime(weather["DATE"], errors="coerce").between(pd.Timestamp(planting_date), min(requested_end, pd.Timestamp(weather_max)))].copy()
                if available_weather.empty:
                    raise AgroLatticeTwinError("Attached weather does not overlap the selected crop schedule.")
                prepared = prepare_soil_daily_weather(available_weather, float(weather_record.get("latitude") or _twin_coordinates(bundle)[0]))
                drivers = assign_stage_parameters(prepared, schedule, fallback_p=fallback_p, initial_root_depth_m=initial_root, maximum_root_depth_m=max_root, dynamic_root_growth=dynamic_roots)
                irrigation = IrrigationStrategy(
                    mode=irrigation_mode, application_efficiency=efficiency, trigger_fraction_of_raw=trigger,
                    refill_fraction=refill, maximum_gross_application_mm=max_application,
                    fixed_interval_days=interval, fixed_gross_application_mm=fixed_amount,
                    sensor_metric=sensor_metric, sensor_trigger_threshold=sensor_threshold, sensor_max_age_days=sensor_max_age,
                ).validated()
                uploaded_schedule = _root_zone_irrigation_upload(uploaded)
                result = simulate_root_zone_balance(drivers, soil, irrigation, initial_depletion_fraction=initial_depletion, runoff_method=runoff_method, runoff_fraction=runoff_fraction, curve_number=curve_number, capillary_rise_mm_day=capillary, adjust_p_for_etc=adjust_p, uploaded_irrigation_schedule=uploaded_schedule, sensor_irrigation_readings=sensor_readings_for_model)
                stage_summary = summarise_root_zone_by_stage(result)
                seasonal_ky = root_zone_whole_season_ky(library, crop, profile) if profiles else None
                season_summary = summarise_root_zone_season(result, seasonal_ky=seasonal_ky)
                settings = {
                    "crop": crop, "profile": profile, "planting_date": str(planting_date), "duration_strategy": duration_strategy,
                    "custom_season_days": custom_days, "constant_kc": constant_kc,
                    "initial_root_depth_m": initial_root, "maximum_root_depth_m": max_root, "fallback_p": fallback_p,
                    "dynamic_root_growth": dynamic_roots, "soil_mode": soil_mode, "soil_preset": preset,
                    "theta_fc": theta_fc, "theta_wp": theta_wp, "initial_depletion_fraction": initial_depletion,
                    "runoff_method": runoff_method, "runoff_fraction": runoff_fraction, "curve_number": curve_number,
                    "irrigation_mode": irrigation_mode, "application_efficiency": efficiency,
                    "maximum_gross_application_mm": max_application, "fixed_interval_days": interval,
                    "fixed_gross_application_mm": fixed_amount, "trigger_fraction_of_raw": trigger,
                    "refill_fraction": refill, "sensor_id": sensor_id, "sensor_name": sensor_name,
                    "sensor_metric": sensor_metric, "sensor_trigger_threshold": sensor_threshold,
                    "sensor_max_age_days": sensor_max_age, "capillary_rise_mm_day": capillary, "adjust_p_for_etc": adjust_p,
                }
                metadata = {
                    "Twin": link.get("name"), "Twin ID": link_id, "weather_attachment_updated_at": weather_record.get("updated_at"),
                    "weather_start": weather_record.get("start_date"), "weather_end": weather_record.get("end_date"),
                    "available_weather_rows": len(available_weather), "model": "FAO-56 single-layer root-zone balance",
                    "limitations": "Screening model; replace generic soil, rooting and irrigation assumptions with local measurements before operational use. Sensor-triggered mode simulates controller logic and does not operate physical pumps or valves.",
                }
                saved = db.save_root_zone(link_id, result, stage_summary=stage_summary, season_summary=season_summary, schedule=schedule, crop=crop, profile=profile, settings=settings, metadata=metadata, weather_updated_at=weather_record.get("updated_at"))
                st.session_state.soil_water_balance_results = result.copy()
                st.session_state.soil_water_stage_summary = stage_summary.copy()
                st.session_state.soil_water_season_summary = season_summary
                st.success(f"Root-zone balance attached permanently: {saved['rows']:,} daily rows from {saved['start_date']} to {saved['end_date']}.")
                st.rerun()
            except Exception as error:
                st.error(f"Twin root-zone simulation failed: {type(error).__name__}: {error}")

    if not balance.empty:
        with st.expander("Remove attached root-zone data", expanded=False):
            st.warning("This removes only the root-zone series owned by this Twin. It does not delete weather, the field, trial or irrigation source file.")
            confirm = st.checkbox("I understand that the attached Twin root-zone history will be deleted", key=f"{ui_key}_root_clear_confirm")
            if st.button("Delete attached Twin root-zone data", disabled=not confirm, key=f"{ui_key}_root_clear", width="stretch"):
                db.clear_root_zone(link_id)
                st.success("Attached Twin root-zone history deleted.")
                st.rerun()

def _select_link(db: AgroLatticeTwinDatabase, key: str) -> dict[str, Any] | None:
    links = db.links()
    if links.empty:
        st.info("No AgroLattice Twin has been configured yet. Create one in Twin configuration & data.")
        return None
    options = links["link_id"].astype(str).tolist()
    labels = dict(zip(links["link_id"].astype(str), links["name"].astype(str)))
    selected = st.selectbox("AgroLattice Twin", options, format_func=lambda value: labels.get(value, value), key=key)
    return db.link(selected)


def _resolve_bundle(link: Mapping[str, Any], field_db, pollination_db, context: Mapping[str, Any], twin_db: AgroLatticeTwinDatabase | None = None) -> dict[str, Any]:
    trial = pollination_db.get_trial(link.get("trial_id")) if link.get("trial_id") else None
    effective_field_id = link.get("field_id") or ((trial or {}).get("source_field_id") if trial else None)
    field = field_db.field(effective_field_id) if effective_field_id else None
    plots = pollination_db.list_plots(link.get("trial_id")) if link.get("trial_id") else pd.DataFrame()
    observations = pollination_db.observations(link.get("trial_id")) if link.get("trial_id") else pd.DataFrame()
    phenology = pollination_db.phenology_events(link.get("trial_id")) if link.get("trial_id") else pd.DataFrame()
    harvest = pollination_db.harvest(link.get("trial_id")) if link.get("trial_id") else pd.DataFrame()
    weather = pollination_db.weather(link.get("trial_id")) if link.get("trial_id") else pd.DataFrame()
    twin_weather = twin_db.weather(str(link.get("link_id"))) if twin_db is not None and link.get("link_id") else pd.DataFrame()
    twin_satellite = twin_db.satellite(str(link.get("link_id"))) if twin_db is not None and link.get("link_id") else pd.DataFrame()
    twin_root_zone = twin_db.root_zone(str(link.get("link_id"))) if twin_db is not None and link.get("link_id") else pd.DataFrame()
    satellite_links = pollination_db.satellite_links(link.get("trial_id")) if link.get("trial_id") else pd.DataFrame()
    tasks = field_db.tasks(effective_field_id) if effective_field_id else pd.DataFrame()
    alerts = field_db.alerts(effective_field_id) if effective_field_id else pd.DataFrame()
    sensors = field_db.sensors(effective_field_id) if effective_field_id else pd.DataFrame()
    readings = field_db.readings(field_id=effective_field_id) if effective_field_id else pd.DataFrame()
    if isinstance(twin_root_zone, pd.DataFrame) and not twin_root_zone.empty:
        root_zone = twin_root_zone.copy()
        root_zone.attrs["agrolattice_source"] = "Persistent Twin root-zone"
    else:
        root_zone = context.get("root_zone") if isinstance(context.get("root_zone"), pd.DataFrame) else pd.DataFrame()
        if isinstance(root_zone, pd.DataFrame) and not root_zone.empty:
            root_zone = root_zone.copy()
            root_zone.attrs["agrolattice_source"] = "Active session root-zone"
    if isinstance(twin_satellite, pd.DataFrame) and not twin_satellite.empty:
        satellite = twin_satellite.copy()
        satellite.attrs["agrolattice_source"] = "Persistent Twin satellite"
    else:
        satellite = context.get("satellite_time_series") if isinstance(context.get("satellite_time_series"), pd.DataFrame) else pd.DataFrame()
        if isinstance(satellite, pd.DataFrame) and not satellite.empty:
            satellite = satellite.copy()
            satellite.attrs["agrolattice_source"] = "Active session satellite"
    if satellite.empty and not satellite_links.empty:
        # The trial link table may contain serialized time-series rows.
        frames = []
        for column in ["time_series_json", "Time series JSON", "Time series", "data_json"]:
            if column in satellite_links:
                for value in satellite_links[column].dropna():
                    try:
                        frames.append(pd.read_json(io.StringIO(str(value))))
                    except Exception:
                        pass
        if frames:
            satellite = pd.concat(frames, ignore_index=True)
            satellite.attrs["agrolattice_source"] = "Maize-trial satellite link"
    return {
        "field": field,
        "trial": trial,
        "plots": plots,
        "observations": observations,
        "phenology": phenology,
        "harvest": harvest,
        "weather": weather,
        "twin_weather": twin_weather,
        "twin_satellite": twin_satellite,
        "twin_root_zone": twin_root_zone,
        "satellite_links": satellite_links,
        "tasks": tasks,
        "alerts": alerts,
        "sensors": sensors,
        "readings": readings,
        "root_zone": root_zone,
        "satellite": satellite,
    }


def render_live_twin_page(*, db: AgroLatticeTwinDatabase, field_db, pollination_db, context: Mapping[str, Any]) -> None:
    st.markdown("## AgroLattice Twin")
    st.caption("Live field state, plot-level crop development, uncertainty and operational priorities from the app's verified data streams.")
    link = _select_link(db, "twin_live_link")
    if not link:
        return
    bundle = _resolve_bundle(link, field_db, pollination_db, context, db)
    settings = db.settings(link["link_id"])
    weather = _weather_frame(context, bundle["weather"], bundle["trial"], bundle.get("twin_weather"))
    if weather.empty:
        st.warning("No daily weather is attached to this Twin. Collect it here; you no longer need to leave the Twin workspace.")
    with st.container(border=True):
        _render_twin_weather_manager(db=db, link=link, bundle=bundle, context=context, key_prefix="twin_live", compact=True)
    weather = _weather_frame(context, bundle["weather"], bundle["trial"], db.weather(str(link["link_id"])))
    bundle = _resolve_bundle(link, field_db, pollination_db, context, db)
    if bundle["root_zone"].empty:
        st.warning("No persistent root-zone series is attached to this Twin. Run and save it here from the Twin's attached weather.")
    with st.container(border=True):
        _render_twin_root_zone_manager(db=db, link=link, bundle=bundle, context=context, key_prefix="twin_live", compact=True)
    bundle = _resolve_bundle(link, field_db, pollination_db, context, db)
    if bundle["satellite"].empty:
        st.warning("No Sentinel-2 time series is attached to this Twin. Search and attach it here; you no longer need to leave the Twin workspace.")
    with st.container(border=True):
        _render_twin_satellite_manager(db=db, link=link, bundle=bundle, context=context, key_prefix="twin_live", compact=True)
    bundle = _resolve_bundle(link, field_db, pollination_db, context, db)
    date_values = []
    for frame, candidates in [(weather, ["Date"]), (bundle["observations"], ["Date"]), (bundle["satellite"], ["Date"]), (bundle["root_zone"], ["Date"])]:
        if isinstance(frame, pd.DataFrame) and not frame.empty:
            column = _first_column(frame, candidates)
            if column:
                date_values.extend(pd.to_datetime(frame[column], errors="coerce").dropna().tolist())
    latest_date = max(date_values).date() if date_values else date.today()
    as_of = st.date_input("Twin state date", value=latest_date, key="twin_live_asof")
    state, plot_states, manifest = build_twin_state(
        context=context,
        field=bundle["field"],
        trial=bundle["trial"],
        plots=bundle["plots"],
        observations=bundle["observations"],
        harvest=bundle["harvest"],
        trial_weather=bundle["weather"],
        twin_weather=bundle.get("twin_weather"),
        root_zone=bundle["root_zone"],
        satellite=bundle["satellite"],
        sensors=bundle["sensors"],
        sensor_readings=bundle["readings"],
        tasks=bundle["tasks"],
        alerts=bundle["alerts"],
        settings=settings,
        as_of=as_of,
    )
    st.session_state.agrolattice_twin_state = state
    st.session_state.agrolattice_twin_plot_states = plot_states
    st.session_state.agrolattice_twin_manifest = manifest

    metrics = st.columns(6)
    if bundle["trial"]:
        metrics[0].metric("Male flowering progress", f"{_num(state.get('Male progress (%)')):.0f}%" if np.isfinite(_num(state.get('Male progress (%)'))) else "NA")
        metrics[1].metric("Female silking progress", f"{_num(state.get('Female progress (%)')):.0f}%" if np.isfinite(_num(state.get('Female progress (%)'))) else "NA")
        metrics[2].metric("Synchrony gap", f"{_num(state.get('Predicted synchrony gap (days)')):+.1f} d" if np.isfinite(_num(state.get('Predicted synchrony gap (days)'))) else "NA")
        metrics[3].metric("Expected overlap", f"{_num(state.get('Estimated receptive-silk coverage (%)')):.0f}%")
    else:
        metrics[0].metric("Root-zone Ks", f"{_num(state.get('Latest root-zone Ks')):.2f}" if np.isfinite(_num(state.get('Latest root-zone Ks'))) else "NA")
        metrics[1].metric("Latest NDVI", f"{_num(state.get('Latest NDVI')):.2f}" if np.isfinite(_num(state.get('Latest NDVI'))) else "NA")
        metrics[2].metric("Open tasks", int(state.get("Open tasks", 0)))
        metrics[3].metric("Open alerts", int(state.get("Open alerts", 0)))
    metrics[4].metric("Field health", f"{_num(state.get('Health score')):.0f}/100" if np.isfinite(_num(state.get('Health score'))) else "NA")
    metrics[5].metric("Twin uncertainty", f"{_num(state.get('Uncertainty (%)')):.0f}%")

    current_tab, boundary_tab, map_tab, evidence_tab, history_tab = st.tabs(["Current state", "Boundary & layout", "Plot intelligence map", "Evidence & provenance", "Saved history"])
    with current_tab:
        left, right = st.columns([1.25, 1])
        with left:
            if bundle["trial"]:
                st.markdown("### Flowering forecast")
                forecast = pd.DataFrame([
                    {"Parent": "Male", "Target GDD": state.get("Male target GDD"), "Accumulated GDD": state.get("Male accumulated GDD"), "Progress (%)": state.get("Male progress (%)"), "Predicted event": state.get("Predicted male 50% flowering")},
                    {"Parent": "Female", "Target GDD": state.get("Female target GDD"), "Accumulated GDD": state.get("Female accumulated GDD"), "Progress (%)": state.get("Female progress (%)"), "Predicted event": state.get("Predicted female 50% silking")},
                ])
                st.dataframe(forecast, hide_index=True, width="stretch")
                st.caption(str(state.get("Target basis")))
                if not plot_states.empty:
                    chart_data = plot_states[[column for column in ["Plot", "Male flowering progress (%)", "Female silking progress (%)"] if column in plot_states]].melt(id_vars=["Plot"], var_name="Series", value_name="Progress (%)")
                    fig = px.bar(chart_data, x="Plot", y="Progress (%)", color="Series", barmode="group", title="Estimated plot-level flowering progress")
                    fig.update_layout(height=430)
                    st.plotly_chart(fig, width="stretch")
            else:
                st.markdown("### Generic field twin")
                st.info("This twin is linked to a mapped field but not to a maize flowering trial. Environmental state, tasks, alerts and sensors remain available. Link a trial to activate parent-specific flowering, plot synchrony and adaptive experimental design.")
                st.dataframe(pd.DataFrame([
                    {"Signal": "Weather observations", "Records": state.get("Weather observations")},
                    {"Signal": "Root-zone days", "Records": state.get("Root-zone days")},
                    {"Signal": "Satellite observations", "Records": state.get("Satellite observations")},
                    {"Signal": "Field observations", "Records": state.get("Field observations")},
                ]), hide_index=True, width="stretch")
        with right:
            st.markdown("### Environmental state")
            environment = pd.DataFrame([
                {"Signal": "Root-zone stress coefficient (Ks)", "Value": state.get("Latest root-zone Ks"), "Interpretation": "1 = no modelled water stress"},
                {"Signal": "Relative root-zone depletion", "Value": state.get("Latest relative depletion"), "Interpretation": "Higher values indicate greater depletion"},
                {"Signal": "Latest NDVI", "Value": state.get("Latest NDVI"), "Interpretation": "Canopy greenness; not a diagnosis"},
                {"Signal": "Latest NDMI", "Value": state.get("Latest NDMI"), "Interpretation": "Canopy moisture proxy"},
                {"Signal": "Rain in last 7 days (mm)", "Value": state.get("Rain last 7 days (mm)"), "Interpretation": "Weather input"},
                {"Signal": "Heat days ≥35°C", "Value": state.get("Heat days ≥35°C last 7 days"), "Interpretation": "Recent heat exposure"},
            ])
            st.dataframe(environment, hide_index=True, width="stretch")
            st.markdown("### Operations")
            ops = st.columns(3)
            ops[0].metric("Open tasks", int(state.get("Open tasks", 0)))
            ops[1].metric("Overdue", int(state.get("Overdue tasks", 0)))
            ops[2].metric("Open alerts", int(state.get("Open alerts", 0)))
            if st.button("Save current twin snapshot", type="primary", width="stretch", key="twin_save_snapshot"):
                snapshot_id = db.save_snapshot(link["link_id"], as_of=as_of, state=state, plot_states=plot_states, input_manifest=manifest)
                st.success(f"Snapshot saved: {snapshot_id[:12]}")


    with boundary_tab:
        st.markdown("### Saved Twin boundary, experiment plots and treatment units")
        st.caption(
            "This is the authoritative spatial representation currently linked to the Twin. "
            "It is view-only here: edit the mapped field under Fields & Operations or synchronise the trial under Maize Synchrony Lab."
        )
        field_geometry = _field_geometry(bundle["field"])
        trial_geometry = _trial_geometry(bundle["trial"])
        if not field_geometry and not trial_geometry:
            st.warning("This Twin has no saved polygon boundary. Link it to a mapped field or a mapped maize trial.")
        else:
            field_area = _num((bundle["field"] or {}).get("area_ha"))
            trial_area = _num((bundle["trial"] or {}).get("field_area_ha"))
            centroid_lat, centroid_lon, centroid_source = _twin_coordinates(bundle)
            if field_geometry and trial_geometry:
                relation = (
                    "Exact mapped-field match"
                    if geometry_hash(field_geometry) == geometry_hash(trial_geometry)
                    else str((bundle["trial"] or {}).get("boundary_mode") or "Different stored boundaries")
                )
            elif field_geometry:
                relation = "Mapped field only"
            else:
                relation = "Maize-trial boundary only"
            cards = st.columns(4)
            cards[0].metric("Field area", f"{field_area:,.3f} ha" if np.isfinite(field_area) else "NA")
            cards[1].metric("Trial area", f"{trial_area:,.3f} ha" if np.isfinite(trial_area) else "NA")
            cards[2].metric("Treatment units", int(len(bundle["plots"])))
            cards[3].metric("Boundary relation", relation)
            if centroid_lat is not None and centroid_lon is not None:
                st.caption(f"Analysis centroid: {float(centroid_lat):.6f}, {float(centroid_lon):.6f} · Source: {centroid_source}")
            boundary_map = twin_boundary_map(bundle["trial"], bundle["field"], bundle["plots"])
            st_folium(boundary_map, height=650, use_container_width=True, key="twin_saved_boundary_map")
            downloads = st.columns(2)
            if field_geometry:
                downloads[0].download_button(
                    "Download mapped-field boundary",
                    json.dumps(field_geometry, indent=2).encode("utf-8"),
                    file_name="twin_mapped_field_boundary.geojson",
                    mime="application/geo+json",
                    width="stretch",
                    key="twin_download_field_boundary",
                )
            if trial_geometry:
                downloads[1].download_button(
                    "Download maize-trial boundary",
                    json.dumps(trial_geometry, indent=2).encode("utf-8"),
                    file_name="twin_maize_trial_boundary.geojson",
                    mime="application/geo+json",
                    width="stretch",
                    key="twin_download_trial_boundary",
                )

    with map_tab:
        if plot_states.empty or "Geometry" not in plot_states:
            st.info("No plot-level analytical layer is available yet. The saved field/trial boundary is still shown below.")
            st_folium(
                twin_boundary_map(bundle["trial"], bundle["field"], bundle["plots"]),
                height=600, use_container_width=True, key="twin_state_boundary_fallback_map",
            )
        else:
            numeric = [column for column in ["Inspection priority score", "Measurement uncertainty (%)", "Flowering-window criticality (%)", "Estimated overlap (%)", "Predicted seed set (%)", "Male flowering progress (%)", "Female silking progress (%)"] if column in plot_states]
            metric = st.selectbox("Map metric", numeric, key="twin_map_metric")
            map_object = plot_state_map(bundle["trial"], bundle["field"], plot_states, metric)
            st_folium(map_object, height=650, use_container_width=True, key="twin_state_map")
            display = [column for column in ["Experiment plot", "Treatment unit", "Plot", "Treatment", "Female parent", "Male parent", "Parent combination", "Variety / genotype", "Sowing density (plants/ha)", "Sowing date", "Male–female sowing difference (days)", "Male offset (days)", metric, "Inspection priority", "Days since observation", "Seed-set prediction method"] if column in plot_states]
            st.dataframe(plot_states[display].sort_values(metric, ascending=False), hide_index=True, width="stretch")

    with evidence_tab:
        st.markdown("### Data-source manifest")
        st.json(manifest)
        evidence = pd.DataFrame([
            {"Component": "Weather", "Rows": manifest.get("weather_rows"), "Freshness (days)": manifest.get("freshness_days", {}).get("weather_days"), "Source": manifest.get("weather_source")},
            {"Component": "Root-zone balance", "Rows": manifest.get("root_zone_rows"), "Freshness (days)": manifest.get("freshness_days", {}).get("root_zone_days"), "Source": manifest.get("root_zone_source")},
            {"Component": "Sentinel-2", "Rows": manifest.get("satellite_rows"), "Freshness (days)": manifest.get("freshness_days", {}).get("satellite_days"), "Source": manifest.get("satellite_source")},
            {"Component": "Field observations", "Rows": manifest.get("observation_rows"), "Freshness (days)": manifest.get("freshness_days", {}).get("observations_days")},
            {"Component": "Sensors", "Rows": manifest.get("sensor_rows"), "Freshness (days)": manifest.get("freshness_days", {}).get("sensor_days")},
        ])
        st.dataframe(evidence, hide_index=True, width="stretch")
        st.warning("Observed, modelled and heuristic values are intentionally mixed only with explicit labels. A high uncertainty score means the twin should guide inspection—not replace it.")

    with history_tab:
        saved = db.snapshots(link["link_id"])
        if saved.empty:
            st.info("No saved twin snapshots yet.")
        else:
            decoded = []
            for _, row in saved.iterrows():
                item = _loads(row["state_json"], {})
                item.update({"Snapshot ID": row["snapshot_id"], "Created": row["created_at"]})
                decoded.append(item)
            history = pd.DataFrame(decoded)
            st.dataframe(history, hide_index=True, width="stretch")
            timeline_metrics = [column for column in ["Male progress (%)", "Female progress (%)", "Estimated receptive-silk coverage (%)", "Health score", "Uncertainty (%)"] if column in history]
            if timeline_metrics and "As of" in history:
                chart = history[["As of"] + timeline_metrics].melt("As of", var_name="Metric", value_name="Value")
                st.plotly_chart(px.line(chart, x="As of", y="Value", color="Metric", markers=True, title="Saved twin history"), width="stretch")


def render_scenario_page(*, db: AgroLatticeTwinDatabase, field_db, pollination_db, context: Mapping[str, Any]) -> None:
    st.markdown("## AgroLattice Scenario Studio")
    st.caption("Compare a baseline twin state with transparent changes in weather, water, planting timing and density.")
    link = _select_link(db, "twin_scenario_link")
    if not link:
        return
    bundle = _resolve_bundle(link, field_db, pollination_db, context, db)
    settings = db.settings(link["link_id"])
    weather = _weather_frame(context, bundle["weather"], bundle["trial"], bundle.get("twin_weather"))
    latest = pd.to_datetime(weather["Date"], errors="coerce").max().date() if not weather.empty else date.today()
    as_of = st.date_input("Baseline state date", value=latest, key="twin_scenario_asof")
    state, plot_states, manifest = build_twin_state(
        context=context, field=bundle["field"], trial=bundle["trial"], plots=bundle["plots"], observations=bundle["observations"], harvest=bundle["harvest"], trial_weather=bundle["weather"], twin_weather=bundle.get("twin_weather"), root_zone=bundle["root_zone"], satellite=bundle["satellite"], sensors=bundle["sensors"], sensor_readings=bundle["readings"], tasks=bundle["tasks"], alerts=bundle["alerts"], settings=settings, as_of=as_of,
    )
    time_tab, scenario_tab, analogue_tab = st.tabs(["Time-travel twin", "What-if simulator", "Historical-state comparison"])
    with time_tab:
        if weather.empty:
            st.info("Load daily weather to use the time-travel slider.")
        else:
            min_date = pd.to_datetime(weather["Date"], errors="coerce").min().date()
            max_date = pd.to_datetime(weather["Date"], errors="coerce").max().date()
            selected = st.slider("Move through the season", min_value=min_date, max_value=max_date, value=min(max_date, as_of), format="YYYY-MM-DD", key="twin_time_slider")
            time_state, time_plots, _ = build_twin_state(
                context=context, field=bundle["field"], trial=bundle["trial"], plots=bundle["plots"], observations=bundle["observations"], harvest=bundle["harvest"], trial_weather=bundle["weather"], twin_weather=bundle.get("twin_weather"), root_zone=bundle["root_zone"], satellite=bundle["satellite"], sensors=bundle["sensors"], sensor_readings=bundle["readings"], tasks=bundle["tasks"], alerts=bundle["alerts"], settings=settings, as_of=selected,
            )
            cols = st.columns(5)
            cols[0].metric("Date", str(selected))
            cols[1].metric("Male progress", f"{_num(time_state.get('Male progress (%)')):.0f}%" if np.isfinite(_num(time_state.get('Male progress (%)'))) else "NA")
            cols[2].metric("Female progress", f"{_num(time_state.get('Female progress (%)')):.0f}%" if np.isfinite(_num(time_state.get('Female progress (%)'))) else "NA")
            cols[3].metric("Overlap", f"{_num(time_state.get('Estimated receptive-silk coverage (%)')):.0f}%")
            cols[4].metric("Uncertainty", f"{_num(time_state.get('Uncertainty (%)')):.0f}%")
            if not time_plots.empty and "Geometry" in time_plots:
                map_object = plot_state_map(bundle["trial"], bundle["field"], time_plots, "Flowering-window criticality (%)")
                st_folium(map_object, height=600, use_container_width=True, key=f"twin_time_map_{selected}")

    with scenario_tab:
        with st.form("twin_scenario_form"):
            scenario_name = st.text_input("Scenario name", value="Alternative management scenario")
            controls = st.columns(3)
            temp_delta = controls[0].slider("Temperature change (°C)", -4.0, 6.0, 0.0, 0.5)
            rainfall_multiplier = controls[1].slider("Rainfall multiplier", 0.0, 2.0, 1.0, 0.1)
            irrigation_change = controls[2].slider("Additional irrigation (mm)", -50.0, 100.0, 0.0, 5.0)
            controls2 = st.columns(3)
            offset_change = controls2[0].slider("Male sowing-offset change (days)", -10, 10, 0, 1, disabled=not bool(bundle["trial"]))
            density_change = controls2[1].slider("Planting-density change (%)", -30.0, 30.0, 0.0, 5.0)
            heat_days_change = controls2[2].slider("Additional heat days ≥35°C", -5, 10, 0, 1)
            run = st.form_submit_button("Run scenario", type="primary", width="stretch")
        if run:
            result = simulate_scenarios(
                state=state,
                plot_states=plot_states,
                temperature_delta_c=temp_delta,
                rainfall_multiplier=rainfall_multiplier,
                irrigation_change_mm=irrigation_change,
                male_offset_change_days=offset_change,
                density_change_percent=density_change,
                heat_days_change=heat_days_change,
            )
            st.session_state.agrolattice_twin_scenario = result
            st.session_state.agrolattice_twin_scenario_settings = {
                "name": scenario_name,
                "temperature_delta_c": temp_delta,
                "rainfall_multiplier": rainfall_multiplier,
                "irrigation_change_mm": irrigation_change,
                "male_offset_change_days": offset_change,
                "density_change_percent": density_change,
                "heat_days_change": heat_days_change,
                "as_of": str(as_of),
            }
        result = st.session_state.get("agrolattice_twin_scenario")
        if isinstance(result, pd.DataFrame) and not result.empty:
            st.dataframe(result, hide_index=True, width="stretch")
            comparison = result.melt(id_vars=["Scenario"], value_vars=["Expected overlap (%)", "Predicted seed set (%)"], var_name="Outcome", value_name="Value")
            st.plotly_chart(px.bar(comparison, x="Outcome", y="Value", color="Scenario", barmode="group", title="Baseline versus alternative"), width="stretch")
            alternative = result.loc[result["Scenario"].eq("Alternative")].iloc[0]
            baseline = result.loc[result["Scenario"].eq("Baseline")].iloc[0]
            if alternative["Predicted seed set (%)"] > baseline["Predicted seed set (%)"]:
                st.success(f"The alternative improves the exploratory seed-set estimate by {alternative['Predicted seed set (%)'] - baseline['Predicted seed set (%)']:.1f} percentage points.")
            else:
                st.warning(f"The alternative reduces the exploratory seed-set estimate by {baseline['Predicted seed set (%)'] - alternative['Predicted seed set (%)']:.1f} percentage points.")
            st.caption("This simulator is a transparent decision-support layer. It does not prove causal effects and should not be extrapolated beyond tested conditions without validation.")
            if st.button("Save scenario", type="primary", width="stretch", key="twin_save_scenario"):
                settings_payload = st.session_state.get("agrolattice_twin_scenario_settings") or {"name": "Saved scenario"}
                scenario_id = db.save_scenario(link["link_id"], settings_payload.get("name", "Saved scenario"), settings_payload, result)
                st.success(f"Scenario saved: {scenario_id[:12]}")

    with analogue_tab:
        analogue_results = context.get("climate_analogue_results")
        analogue_changes = context.get("climate_analogue_changes")
        if isinstance(analogue_results, pd.DataFrame) and not analogue_results.empty:
            st.markdown("### Climate-analogue context")
            st.caption("These are imported from the Climate analogues page. They contextualise the twin; they do not replace plot-level observations.")
            st.dataframe(analogue_results.head(25), hide_index=True, width="stretch")
            if isinstance(analogue_changes, pd.DataFrame) and not analogue_changes.empty:
                with st.expander("Analogue change table"):
                    st.dataframe(analogue_changes.head(100), hide_index=True, width="stretch")
        else:
            st.info("Run Climate analogues to add historical climate context to this page.")
        st.markdown("### Saved digital-twin states")
        snapshots = db.snapshots(link["link_id"])
        if snapshots.empty:
            st.info("Save twin snapshots at different dates or seasons to compare historical states.")
        else:
            decoded = []
            for _, row in snapshots.iterrows():
                item = _loads(row["state_json"], {})
                decoded.append({
                    "As of": item.get("As of"),
                    "Health score": item.get("Health score"),
                    "Overlap (%)": item.get("Estimated receptive-silk coverage (%)"),
                    "Synchrony gap (days)": item.get("Predicted synchrony gap (days)"),
                    "Ks": item.get("Latest root-zone Ks"),
                    "NDVI": item.get("Latest NDVI"),
                    "Uncertainty (%)": item.get("Uncertainty (%)"),
                })
            history = pd.DataFrame(decoded)
            st.dataframe(history, hide_index=True, width="stretch")
            metric = st.selectbox("Comparison metric", [column for column in history.columns if column != "As of"], key="twin_history_metric")
            st.plotly_chart(px.line(history, x="As of", y=metric, markers=True, title=f"Twin history: {metric}"), width="stretch")


def render_copilot_page(*, db: AgroLatticeTwinDatabase, field_db, pollination_db, context: Mapping[str, Any]) -> None:
    st.markdown("## AgroLattice Adaptive Experiment Copilot")
    st.caption("Prioritise field measurements, reduce uncertainty, create inspection tasks and refine the next experimental design.")
    link = _select_link(db, "twin_copilot_link")
    if not link:
        return
    bundle = _resolve_bundle(link, field_db, pollination_db, context, db)
    settings = db.settings(link["link_id"])
    weather = _weather_frame(context, bundle["weather"], bundle["trial"], bundle.get("twin_weather"))
    latest = pd.to_datetime(weather["Date"], errors="coerce").max().date() if not weather.empty else date.today()
    as_of = st.date_input("Recommendation date", value=latest, key="twin_copilot_asof")
    state, plot_states, manifest = build_twin_state(
        context=context, field=bundle["field"], trial=bundle["trial"], plots=bundle["plots"], observations=bundle["observations"], harvest=bundle["harvest"], trial_weather=bundle["weather"], twin_weather=bundle.get("twin_weather"), root_zone=bundle["root_zone"], satellite=bundle["satellite"], sensors=bundle["sensors"], sensor_readings=bundle["readings"], tasks=bundle["tasks"], alerts=bundle["alerts"], settings=settings, as_of=as_of,
    )
    inspect_tab, design_tab, task_tab, register_tab = st.tabs(["What to measure next", "Next-season design", "Create field tasks", "Recommendation register"])
    with inspect_tab:
        maximum = st.slider("Maximum plots to prioritise", 3, 20, 8, 1, key="twin_max_recommendations")
        recommendations = generate_recommendations(plot_states=plot_states, state=state, max_plots=maximum)
        st.session_state.agrolattice_twin_recommendations = recommendations
        if recommendations.empty:
            st.info("No plot-level recommendation can be generated yet. Link the twin to a mapped maize trial and enter observations.")
        else:
            display = [column for column in ["Priority", "Plot", "Title", "Suggested measurements", "Rationale", "Score"] if column in recommendations]
            st.dataframe(recommendations[display], hide_index=True, width="stretch")
            if not plot_states.empty and "Geometry" in plot_states:
                st_folium(plot_state_map(bundle["trial"], bundle["field"], plot_states, "Inspection priority score"), height=600, use_container_width=True, key="twin_copilot_map")
            if st.button("Save current recommendations", type="primary", width="stretch", key="twin_save_recommendations"):
                db.replace_recommendations(link["link_id"], recommendations.to_dict(orient="records"))
                st.success("Recommendations saved to the twin register.")

    with design_tab:
        design, rationale = next_season_design(plot_states)
        st.markdown("### Suggested sowing-offset set")
        st.write(rationale)
        if design.empty:
            st.info("More treatment and outcome data are needed.")
        else:
            st.dataframe(design, hide_index=True, width="stretch")
            st.warning("Treat this as an adaptive-design proposal. The agricultural investigators must decide the final range, blocks, replication, seed availability, isolation and operational feasibility.")
        if not plot_states.empty and "Male offset (days)" in plot_states:
            outcome = _first_column(plot_states, ["Seed-set percentage", "Predicted seed set (%)", "Pure seed (%)"])
            if outcome:
                chart = plot_states.groupby("Male offset (days)", as_index=False)[outcome].agg(["mean", "std", "count"]).reset_index()
                fig = px.scatter(chart, x="Male offset (days)", y="mean", size="count", error_y="std", title=f"Observed/predicted response: {outcome}")
                st.plotly_chart(fig, width="stretch")

    with task_tab:
        recommendations = st.session_state.get("agrolattice_twin_recommendations")
        if not link.get("field_id"):
            st.info("Link this twin to a Field Operations field before creating tasks.")
        elif not isinstance(recommendations, pd.DataFrame) or recommendations.empty:
            st.info("Generate recommendations in the first tab.")
        else:
            task_rows = recommendations.loc[recommendations["Recommendation type"].eq("Plot inspection")].copy()
            task_rows["Create"] = True
            edited = st.data_editor(task_rows[["Create", "Priority", "Plot", "Title", "Suggested measurements"]], hide_index=True, width="stretch", key="twin_task_editor")
            due_date = st.date_input("Task due date", value=pd.Timestamp(as_of).date() + pd.Timedelta(days=1), key="twin_task_due")
            assignee = st.text_input("Assign to", value="", key="twin_task_assignee")
            if st.button("Create selected inspection tasks", type="primary", width="stretch", key="twin_create_tasks"):
                selected = edited.loc[edited["Create"].fillna(False).astype(bool)]
                created = 0
                for _, row in selected.iterrows():
                    field_db.create_task(
                        link["field_id"],
                        str(row["Title"]),
                        category="AgroLattice Twin inspection",
                        assigned_to=assignee,
                        due_date=str(due_date),
                        priority=str(row["Priority"]),
                        status="Ready",
                        description=str(row["Suggested measurements"]),
                        recurrence="None",
                        source="AgroLattice Adaptive Experiment Copilot",
                    )
                    created += 1
                st.success(f"Created {created} field task(s).")

    with register_tab:
        saved = db.recommendations(link["link_id"])
        if saved.empty:
            st.info("No saved recommendations.")
        else:
            st.dataframe(saved.drop(columns=["details_json"], errors="ignore"), hide_index=True, width="stretch")
            open_ids = saved.loc[saved["status"].eq("Open"), "recommendation_id"].astype(str).tolist()
            if open_ids:
                selected_id = st.selectbox("Recommendation to close", open_ids, key="twin_close_recommendation")
                if st.button("Mark resolved", width="stretch", key="twin_resolve_recommendation"):
                    db.update_recommendation(selected_id, "Resolved")
                    st.rerun()


def render_configuration_page(*, db: AgroLatticeTwinDatabase, field_db, pollination_db, context: Mapping[str, Any]) -> None:
    st.markdown("## AgroLattice Twin configuration & data")
    st.caption("Link mapped fields and trials, calibrate flowering targets, inspect data readiness and export the complete twin record.")
    configure_tab, settings_tab, weather_tab, root_zone_tab, satellite_tab, readiness_tab, export_tab = st.tabs(["Create/link twin", "Calibration settings", "Twin weather", "Twin root zone", "Twin satellite", "Data readiness", "Export & model registry"])
    fields = field_db.fields()
    trials = pollination_db.list_trials()
    with configure_tab:
        field_options = [""] + (fields["field_id"].astype(str).tolist() if not fields.empty else [])
        field_labels = {}
        if not fields.empty:
            for _, row in fields.iterrows():
                farm = str(row.get("farm_name") or "Farm")
                area = pd.to_numeric(pd.Series([row.get("area_ha")]), errors="coerce").iloc[0]
                area_text = f" · {float(area):,.3f} ha" if pd.notna(area) else ""
                field_labels[str(row["field_id"])] = f"{farm} · {row.get('name', row['field_id'])}{area_text}"
        trial_id_col = _first_column(trials, ["trial_id", "Trial ID"])
        trial_name_col = _first_column(trials, ["name", "Trial"])
        trial_options = [""] + (trials[trial_id_col].astype(str).tolist() if not trials.empty and trial_id_col else [])
        trial_labels = dict(zip(trials[trial_id_col].astype(str), trials[trial_name_col].astype(str))) if not trials.empty and trial_id_col and trial_name_col else {}
        trial_id = st.selectbox(
            "Maize flowering trial", trial_options,
            format_func=lambda value: "No trial selected" if not value else trial_labels.get(value, value),
            key="twin_create_trial_select",
            help="Trials created from an existing mapped field carry that exact field ID and geometry fingerprint into the Twin automatically.",
        )
        selected_trial = pollination_db.get_trial(trial_id) if trial_id else None
        inherited_field_id = str((selected_trial or {}).get("source_field_id") or "")
        inherited_field = field_db.field(inherited_field_id) if inherited_field_id else None
        if inherited_field:
            field_id = inherited_field_id
            st.success(
                "Mapped field inherited exactly from the maize trial: "
                + field_labels.get(field_id, str(inherited_field.get("name") or field_id))
            )
            trial_hash = geometry_hash((selected_trial or {}).get("field_geometry")) if (selected_trial or {}).get("field_geometry") else None
            field_hash = geometry_hash(inherited_field.get("geometry"))
            boundary_mode = str((selected_trial or {}).get("boundary_mode") or "Exact mapped field")
            if boundary_mode == "Exact mapped field" and trial_hash != field_hash:
                st.warning("The linked mapped-field boundary changed after the trial was created. Synchronise the trial under Maize Synchrony Lab → Trial setup → Spatial linkage before creating the Twin.")
            elif boundary_mode == "Field subsection":
                st.info("This trial is a linked subsection of the mapped field. The parent field is inherited automatically while the trial keeps its smaller experimental boundary.")
        else:
            field_id = st.selectbox(
                "Mapped field", field_options,
                format_func=lambda value: "No field selected" if not value else field_labels.get(value, value),
                key="twin_create_field_select",
                help="Older or independent trials do not yet carry a mapped-field link, so select the correct field manually.",
            )
            if trial_id and selected_trial and not inherited_field_id:
                st.warning("This older trial has no exact mapped-field link. Add one in Maize Synchrony Lab → Trial setup → Spatial linkage to prevent future geometry mismatches.")
        preview_field = inherited_field or (field_db.field(field_id) if field_id else None)
        if preview_field or selected_trial:
            with st.expander("Preview exact Twin boundary", expanded=True):
                st.caption(
                    "The blue outline is the mapped field. An orange dashed outline is a trial subsection; "
                    "an exact full-field trial is shown as one green matching boundary."
                )
                preview_plots = pollination_db.list_plots(trial_id) if trial_id else pd.DataFrame()
                preview_map = twin_boundary_map(selected_trial, preview_field, preview_plots)
                preview_key = f"twin_create_boundary_preview_{field_id or 'none'}_{trial_id or 'none'}"
                st_folium(preview_map, height=520, use_container_width=True, key=preview_key)

        suggested_parts = []
        if field_id:
            suggested_parts.append(field_labels.get(field_id, "Field"))
        if trial_id:
            suggested_parts.append(trial_labels.get(trial_id, "Trial"))
        suggested_name = " · ".join(suggested_parts) if suggested_parts else "AgroLattice Twin"
        with st.form("twin_create_link_form"):
            name = st.text_input("Twin name", value=suggested_name)
            notes = st.text_area("Notes", value="")
            create = st.form_submit_button("Create or update twin", type="primary", width="stretch")
        if create:
            link_id = db.save_link(name=name, field_id=field_id or None, trial_id=trial_id or None, notes=notes)
            st.success(f"Twin ready: {link_id[:12]}")
        links = db.links()
        if not links.empty:
            st.dataframe(links, hide_index=True, width="stretch")
            with st.expander("Delete an AgroLattice Twin", expanded=False):
                st.warning("This permanently deletes the selected Twin link together with its calibration settings, saved snapshots, scenarios, recommendations, registered models and attached weather, root-zone and satellite data. It does not delete the underlying field or maize trial.")
                twin_labels = {f"{row['name']} · {str(row['link_id'])[:8]}": str(row["link_id"]) for _, row in links.iterrows()}
                twin_label = st.selectbox("Twin to delete", list(twin_labels), key="twin_delete_link_select")
                twin_id = twin_labels[twin_label]
                twin_row = links.loc[links["link_id"].astype(str).eq(twin_id)].iloc[0]
                twin_counts = db.storage_counts(twin_id)
                st.dataframe(pd.DataFrame([{"Record type": key, "Will be deleted": value} for key, value in twin_counts.items()]), hide_index=True, width="stretch")
                typed_twin_name = st.text_input("Type the exact Twin name to confirm", key="twin_delete_link_name")
                confirm_twin = st.checkbox("I understand that this Twin deletion cannot be undone", key="twin_delete_link_confirm")
                if st.button("Delete AgroLattice Twin", type="primary", disabled=not (confirm_twin and typed_twin_name == str(twin_row["name"])), key="twin_delete_link_button", width="stretch"):
                    deleted = db.delete_link(twin_id)
                    for key in ["agrolattice_twin_state", "agrolattice_twin_plot_states", "agrolattice_twin_scenario", "agrolattice_twin_recommendations"]:
                        st.session_state.pop(key, None)
                    st.success(f"Twin deleted. {sum(deleted.values()):,} owned records were removed.")
                    st.rerun()

    with settings_tab:
        link = _select_link(db, "twin_settings_link")
        if link:
            current = db.settings(link["link_id"])
            bundle = _resolve_bundle(link, field_db, pollination_db, context, db)
            observed_male = observed_female = np.nan
            if not bundle["observations"].empty:
                try:
                    metrics, _ = compute_plot_synchrony_metrics(bundle["observations"], _weather_frame(context, bundle["weather"], bundle["trial"], bundle.get("twin_weather")))
                    observed_male, observed_female, basis = _observed_gdd_targets(metrics)
                    st.info(f"Observed target suggestion: male {observed_male:.1f} GDD; female {observed_female:.1f} GDD. {basis}" if np.isfinite(observed_male) and np.isfinite(observed_female) else basis)
                except Exception as error:
                    st.info(f"Observed target suggestion unavailable: {error}")
            with st.form("twin_settings_form"):
                cols = st.columns(2)
                male_target = cols[0].number_input("Male 50% flowering target GDD", min_value=100.0, max_value=2500.0, value=float(current.get("male_target_gdd") or (observed_male if np.isfinite(observed_male) else 650.0)), step=5.0)
                female_target = cols[1].number_input("Female 50% silking target GDD", min_value=100.0, max_value=2500.0, value=float(current.get("female_target_gdd") or (observed_female if np.isfinite(observed_female) else 670.0)), step=5.0)
                cols2 = st.columns(3)
                inspection_window = cols2[0].number_input("Critical inspection window (days)", 1, 21, int(current.get("inspection_window_days", 7)))
                stale_days = cols2[1].number_input("Observation becomes stale after (days)", 1, 14, int(current.get("stale_observation_days", 3)))
                uncertainty_alert = cols2[2].slider("Uncertainty alert threshold (%)", 20, 95, int(current.get("uncertainty_alert_percent", 60)))
                target_seed = st.number_input("Target seed-set percentage", 0.0, 100.0, float(current.get("target_seed_set_percent") or 90.0), 1.0)
                fallback = st.checkbox("Allow clearly labelled heuristic fallback when calibrated models are unavailable", value=bool(current.get("allow_heuristic_fallback", 1)))
                save = st.form_submit_button("Save twin settings", type="primary", width="stretch")
            if save:
                db.save_settings(link["link_id"], {
                    "male_target_gdd": male_target,
                    "female_target_gdd": female_target,
                    "inspection_window_days": inspection_window,
                    "stale_observation_days": stale_days,
                    "target_seed_set_percent": target_seed,
                    "uncertainty_alert_percent": uncertainty_alert,
                    "allow_heuristic_fallback": fallback,
                })
                st.success("Twin settings saved.")

    with weather_tab:
        link = _select_link(db, "twin_weather_link")
        if link:
            bundle = _resolve_bundle(link, field_db, pollination_db, context, db)
            _render_twin_weather_manager(db=db, link=link, bundle=bundle, context=context, key_prefix="twin_config", compact=False)

    with root_zone_tab:
        link = _select_link(db, "twin_root_zone_link")
        if link:
            bundle = _resolve_bundle(link, field_db, pollination_db, context, db)
            _render_twin_root_zone_manager(db=db, link=link, bundle=bundle, context=context, key_prefix="twin_config", compact=False)

    with satellite_tab:
        link = _select_link(db, "twin_satellite_link")
        if link:
            bundle = _resolve_bundle(link, field_db, pollination_db, context, db)
            _render_twin_satellite_manager(db=db, link=link, bundle=bundle, context=context, key_prefix="twin_config", compact=False)

    with readiness_tab:
        link = _select_link(db, "twin_readiness_link")
        if link:
            bundle = _resolve_bundle(link, field_db, pollination_db, context, db)
            rows = [
                {"Component": "Mapped field", "Status": "Ready" if bundle["field"] else "Optional/missing", "Records": 1 if bundle["field"] else 0, "Purpose": "Field geometry and field operations"},
                {"Component": "Maize trial", "Status": "Ready" if bundle["trial"] else "Optional/missing", "Records": 1 if bundle["trial"] else 0, "Purpose": "Parental lines, plots and flowering model"},
                {"Component": "Mapped plots", "Status": "Ready" if not bundle["plots"].empty else "Missing", "Records": len(bundle["plots"]), "Purpose": "Plot-level twin and adaptive sampling"},
                {"Component": "Flowering observations", "Status": "Ready" if not bundle["observations"].empty else "Missing", "Records": len(bundle["observations"]), "Purpose": "Observed flowering curves"},
                {"Component": "Harvest outcomes", "Status": "Ready" if not bundle["harvest"].empty else "Not yet available", "Records": len(bundle["harvest"]), "Purpose": "Outcome-model calibration"},
                {"Component": "Daily weather", "Status": "Ready" if not _weather_frame(context, bundle["weather"], bundle["trial"], bundle.get("twin_weather")).empty else "Missing — use Twin weather tab", "Records": len(_weather_frame(context, bundle["weather"], bundle["trial"], bundle.get("twin_weather"))), "Purpose": "Persistent GDD and weather exposure"},
                {"Component": "Root-zone balance", "Status": "Ready" if not bundle["root_zone"].empty else "Missing — use Twin root zone tab", "Records": len(bundle["root_zone"]), "Purpose": "Persistent water-stress state"},
                {"Component": "Sentinel-2", "Status": "Ready" if not bundle["satellite"].empty else "Missing — use Twin satellite tab", "Records": len(bundle["satellite"]), "Purpose": "Persistent canopy vigour and moisture covariates"},
                {"Component": "Sensors", "Status": "Ready" if not bundle["readings"].empty else "Optional/missing", "Records": len(bundle["readings"]), "Purpose": "Local field measurements"},
            ]
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
            if bundle["field"] and bundle["trial"]:
                field_geom = _loads(bundle["field"].get("geometry_json"), None)
                trial_geom = bundle["trial"].get("field_geometry")
                if field_geom and trial_geom:
                    match = geometry_hash(validate_aoi_geometry(field_geom)) == geometry_hash(validate_aoi_geometry(trial_geom))
                    st.success("Field and trial geometries match exactly.") if match else st.warning("Field and trial geometry hashes differ. Verify that they represent the same experiment before interpreting combined data.")

    with export_tab:
        link = _select_link(db, "twin_export_link")
        if link:
            st.download_button("Download complete AgroLattice Twin package", db.export_package(link["link_id"]), file_name="agrolattice_twin_package.zip", mime="application/zip", width="stretch")
            registry = db.model_registry(link["link_id"])
            if registry.empty:
                st.info("No twin-specific fitted model has been registered yet. The live twin can still use observed targets and explicitly labelled transparent fallbacks.")
            else:
                st.dataframe(registry, hide_index=True, width="stretch")
            scenarios = db.scenarios(link["link_id"])
            if not scenarios.empty:
                st.markdown("### Saved scenarios")
                st.dataframe(scenarios.drop(columns=["settings_json", "results_json"], errors="ignore"), hide_index=True, width="stretch")
            with st.expander("Clear selected saved Twin outputs", expanded=False):
                st.caption("Use this when you want to keep the Twin link and calibration but remove selected stored records, including attached weather or Sentinel-2 history if required.")
                clear_categories = st.multiselect(
                    "Stored Twin records to clear",
                    ["Saved snapshots", "Saved scenarios", "Recommendations", "Registered models", "Attached weather", "Attached root zone", "Attached satellite"],
                    key="twin_clear_output_categories",
                )
                mapping = {
                    "Saved snapshots": "snapshots",
                    "Saved scenarios": "scenarios",
                    "Recommendations": "recommendations",
                    "Registered models": "models",
                    "Attached weather": "weather",
                    "Attached root zone": "root_zone",
                    "Attached satellite": "satellite",
                }
                confirm_clear = st.checkbox("I understand that the selected stored records will be permanently deleted", key="twin_clear_outputs_confirm")
                if st.button("Clear selected Twin outputs", disabled=not (confirm_clear and clear_categories), key="twin_clear_outputs_button", width="stretch"):
                    removed = db.clear_link_records(link["link_id"], [mapping[item] for item in clear_categories])
                    st.success(f"Cleared {sum(removed.values()):,} stored Twin records.")
                    st.rerun()


def twin_session_artifacts() -> dict[str, Any]:
    return {
        "agrolattice_twin_state": st.session_state.get("agrolattice_twin_state"),
        "agrolattice_twin_plot_states": st.session_state.get("agrolattice_twin_plot_states"),
        "agrolattice_twin_scenario": st.session_state.get("agrolattice_twin_scenario"),
        "agrolattice_twin_recommendations": st.session_state.get("agrolattice_twin_recommendations"),
    }
