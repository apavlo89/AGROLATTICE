from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import math
import sqlite3
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from uuid import uuid4

import folium
from branca.element import Element, MacroElement
from jinja2 import Template
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from folium.plugins import Draw, Fullscreen, HeatMap, MeasureControl
from pyproj import CRS, Transformer
from shapely.geometry import Point, Polygon, mapping, shape
from shapely.ops import transform as shapely_transform, unary_union
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from streamlit_folium import st_folium
from local_boundary_editor import render_boundary_editor

MODULE_VERSION = "8.0.0"
DB_SCHEMA_VERSION = "8.0.0"

ROLE_OPTIONS = ["Administrator", "Agronomist", "Researcher", "Field worker", "Viewer"]
ORGANISATION_TYPES = ["Farm", "Agricultural research centre"]
TASK_STATUSES = ["Planned", "Ready", "In progress", "Blocked", "Completed", "Cancelled"]
TASK_PRIORITIES = ["Low", "Normal", "High", "Urgent"]
TASK_CATEGORIES = [
    "Scouting", "Sowing", "Irrigation", "Fertilisation", "Spraying", "Sampling",
    "Phenology", "Harvest", "Maintenance", "Trial operation", "Other",
]
OBSERVATION_CATEGORIES = [
    "Crop condition", "Pest", "Disease symptom", "Weed", "Water stress", "Nutrient symptom",
    "Emergence", "Phenology", "Lodging", "Soil condition", "Irrigation issue", "Other",
]
OPERATION_CATEGORIES = [
    "Sowing", "Irrigation", "Fertiliser", "Crop protection", "Cultivation", "Sampling",
    "Detasselling", "Harvest", "Machinery", "Other",
]
SENSOR_TYPES = [
    "Soil moisture", "Soil temperature", "Soil EC/salinity", "Air temperature",
    "Relative humidity", "Rain gauge", "Solar radiation", "Wind speed", "Leaf wetness",
    "Canopy temperature", "Water meter", "Nitrate", "Other",
]
SENSOR_DEFAULT_UNITS = {
    "Soil moisture": "% VWC", "Soil temperature": "°C", "Soil EC/salinity": "dS/m",
    "Air temperature": "°C", "Relative humidity": "%", "Rain gauge": "mm",
    "Solar radiation": "MJ/m²/day", "Wind speed": "m/s", "Leaf wetness": "%",
    "Canopy temperature": "°C", "Water meter": "m³", "Nitrate": "mg/L", "Other": "unit",
}
DEFAULT_ALERT_RULES = [
    ("NDVI decline", "satellite", "NDVI change (%)", "<=", -12.0, "High", 14, "Detect a substantial decline relative to the preceding observation."),
    ("Low NDMI", "satellite", "NDMI", "<=", 0.10, "High", 7, "Potential canopy or surface-moisture stress signal; verify in the field."),
    ("Root-zone stress", "root_zone", "Ks", "<=", 0.70, "High", 3, "FAO-style stress coefficient below the configured threshold."),
    ("Severe root-zone depletion", "root_zone", "Relative depletion", ">=", 0.80, "Urgent", 2, "Modelled depletion approaching total available water."),
    ("High temperature", "weather", "Tmax", ">=", 35.0, "High", 1, "Heat threshold; crop-stage sensitivity must be assessed separately."),
    ("Low soil moisture", "sensor", "Soil moisture", "<=", 18.0, "High", 1, "Demonstration threshold only; replace with a site- and sensor-specific threshold."),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def slug(text: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in str(text)).strip("_")
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned or "item"


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def json_loads(value: Any, default: Any = None) -> Any:
    if value is None or value == "":
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def normalise_geojson_geometry(value: Any) -> dict:
    if value is None:
        raise ValueError("No geometry was supplied.")
    if isinstance(value, str):
        value = json.loads(value)
    if isinstance(value, Mapping) and value.get("type") == "FeatureCollection":
        features = value.get("features") or []
        if len(features) != 1:
            raise ValueError("The file must contain exactly one field geometry.")
        value = features[0]
    if isinstance(value, Mapping) and value.get("type") == "Feature":
        value = value.get("geometry")
    geom = shape(value)
    if geom.geom_type not in {"Polygon", "MultiPolygon"}:
        raise ValueError("A field boundary must be a Polygon or MultiPolygon.")
    if geom.is_empty or not geom.is_valid:
        repaired = geom.buffer(0)
        if repaired.is_empty or not repaired.is_valid:
            raise ValueError("The field geometry is empty or invalid.")
        geom = repaired
    return mapping(geom)


def geometry_hash(geometry: Mapping[str, Any]) -> str:
    return hashlib.sha256(json_dumps(normalise_geojson_geometry(geometry)).encode("utf-8")).hexdigest()[:16]


def geometry_centroid(geometry: Mapping[str, Any]) -> tuple[float, float]:
    centroid = shape(normalise_geojson_geometry(geometry)).centroid
    return float(centroid.y), float(centroid.x)


def geometry_area_hectares(geometry: Mapping[str, Any]) -> float:
    geom = shape(normalise_geojson_geometry(geometry))
    lon, lat = geom.centroid.x, geom.centroid.y
    zone = max(1, min(60, int((lon + 180) // 6) + 1))
    epsg = 32600 + zone if lat >= 0 else 32700 + zone
    transformer = Transformer.from_crs(CRS.from_epsg(4326), CRS.from_epsg(epsg), always_xy=True)
    projected = shapely_transform(transformer.transform, geom)
    return float(projected.area / 10000.0)


def geometry_feature(geometry: Mapping[str, Any], properties: Mapping[str, Any] | None = None) -> dict:
    return {"type": "Feature", "properties": dict(properties or {}), "geometry": normalise_geojson_geometry(geometry)}


def geometry_feature_collection(features: Sequence[dict]) -> dict:
    return {"type": "FeatureCollection", "features": list(features)}


def _drawn_geometry(map_state: Mapping[str, Any] | None) -> dict | None:
    if not map_state:
        return None
    drawing = map_state.get("last_active_drawing") or map_state.get("last_drawn")
    if not drawing:
        drawings = map_state.get("all_drawings") or []
        drawing = drawings[-1] if drawings else None
    if not drawing:
        return None
    try:
        return normalise_geojson_geometry(drawing)
    except Exception:
        return None


def _geometry_from_project(project: Mapping[str, Any] | None) -> dict | None:
    if not isinstance(project, Mapping):
        return None
    candidates = [
        project.get("field_geometry"),
        (project.get("location") or {}).get("field_geometry"),
        (project.get("satellite") or {}).get("aoi_geometry"),
        (project.get("modules") or {}).get("satellite_aoi_geometry"),
    ]
    for candidate in candidates:
        if candidate:
            try:
                return normalise_geojson_geometry(candidate)
            except Exception:
                pass
    return None


def _source_geometry(context: Mapping[str, Any], source: str) -> dict | None:
    if source == "Current project":
        return _geometry_from_project(context.get("active_project"))
    if source == "Satellite crop monitoring":
        candidate = context.get("satellite_geometry")
    elif source == "Maize flowering trial":
        candidate = context.get("pollination_geometry")
    else:
        candidate = None
    try:
        return normalise_geojson_geometry(candidate) if candidate else None
    except Exception:
        return None


class FieldOperationsDatabase:
    def __init__(self, database_path: str | Path, attachment_root: str | Path | None = None):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.attachment_root = Path(attachment_root or self.database_path.parent / "attachments")
        self.attachment_root.mkdir(parents=True, exist_ok=True)
        self._initialise()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialise(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS farms (
            farm_id TEXT PRIMARY KEY, name TEXT NOT NULL, country TEXT, admin_area TEXT,
            manager TEXT, notes TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            entity_type TEXT NOT NULL DEFAULT 'Farm', geometry_json TEXT, geometry_hash TEXT,
            centroid_lat REAL, centroid_lon REAL, area_ha REAL
        );
        CREATE TABLE IF NOT EXISTS fields (
            field_id TEXT PRIMARY KEY, farm_id TEXT NOT NULL, name TEXT NOT NULL, code TEXT,
            geometry_json TEXT NOT NULL, geometry_hash TEXT NOT NULL, centroid_lat REAL, centroid_lon REAL,
            area_ha REAL, crop TEXT, variety TEXT, season_year INTEGER, irrigation_system TEXT,
            soil_type TEXT, status TEXT, notes TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            FOREIGN KEY(farm_id) REFERENCES farms(farm_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS crop_history (
            history_id TEXT PRIMARY KEY, field_id TEXT NOT NULL, season_year INTEGER NOT NULL,
            crop TEXT NOT NULL, variety TEXT, sowing_date TEXT, harvest_date TEXT, yield_t_ha REAL,
            notes TEXT, created_at TEXT NOT NULL,
            FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT, role TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS field_access (
            user_id TEXT NOT NULL, field_id TEXT NOT NULL, permission TEXT NOT NULL,
            PRIMARY KEY(user_id, field_id),
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY, field_id TEXT NOT NULL, title TEXT NOT NULL, category TEXT,
            assigned_to TEXT, due_date TEXT, priority TEXT, status TEXT, description TEXT,
            recurrence TEXT, source TEXT, created_at TEXT NOT NULL, completed_at TEXT,
            FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS observations (
            observation_id TEXT PRIMARY KEY, field_id TEXT NOT NULL, task_id TEXT, observed_at TEXT NOT NULL,
            category TEXT, severity INTEGER, latitude REAL, longitude REAL, notes TEXT,
            recommendation TEXT, photo_path TEXT, status TEXT, created_by TEXT, created_at TEXT NOT NULL,
            FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE,
            FOREIGN KEY(task_id) REFERENCES tasks(task_id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS operations (
            operation_id TEXT PRIMARY KEY, field_id TEXT NOT NULL, operation_date TEXT NOT NULL,
            category TEXT, product TEXT, rate REAL, rate_unit TEXT, treated_area_ha REAL,
            water_mm REAL, cost REAL, operator TEXT, notes TEXT, created_at TEXT NOT NULL,
            FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS sensors (
            sensor_id TEXT PRIMARY KEY, field_id TEXT NOT NULL, name TEXT NOT NULL, sensor_type TEXT NOT NULL,
            unit TEXT, depth_cm REAL, latitude REAL, longitude REAL, source TEXT, status TEXT,
            calibration_note TEXT, created_at TEXT NOT NULL,
            FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS sensor_readings (
            reading_id TEXT PRIMARY KEY, sensor_id TEXT NOT NULL, timestamp TEXT NOT NULL, value REAL,
            quality_flag TEXT, source TEXT, created_at TEXT NOT NULL,
            UNIQUE(sensor_id, timestamp),
            FOREIGN KEY(sensor_id) REFERENCES sensors(sensor_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS nutrient_samples (
            sample_id TEXT PRIMARY KEY, field_id TEXT NOT NULL, sample_date TEXT NOT NULL, sample_type TEXT,
            latitude REAL, longitude REAL, nitrogen REAL, phosphorus REAL, potassium REAL, ph REAL,
            ec REAL, organic_matter REAL, notes TEXT, created_at TEXT NOT NULL,
            FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS alert_rules (
            rule_id TEXT PRIMARY KEY, name TEXT NOT NULL, source TEXT NOT NULL, metric TEXT NOT NULL,
            operator TEXT NOT NULL, threshold REAL NOT NULL, severity TEXT NOT NULL,
            window_days INTEGER, enabled INTEGER NOT NULL DEFAULT 1, notes TEXT, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS alerts (
            alert_id TEXT PRIMARY KEY, field_id TEXT NOT NULL, rule_id TEXT, source TEXT,
            alert_type TEXT, severity TEXT, message TEXT, metric TEXT, value REAL, threshold REAL,
            status TEXT, fingerprint TEXT UNIQUE, created_at TEXT NOT NULL, resolved_at TEXT,
            FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE,
            FOREIGN KEY(rule_id) REFERENCES alert_rules(rule_id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS prescriptions (
            prescription_id TEXT PRIMARY KEY, field_id TEXT NOT NULL, name TEXT NOT NULL,
            variable TEXT, rate_unit TEXT, zone_label TEXT, rate REAL, geometry_json TEXT,
            source_metric TEXT, created_at TEXT NOT NULL,
            FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            audit_id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, entity_type TEXT,
            entity_id TEXT, user_name TEXT, details_json TEXT, created_at TEXT NOT NULL
        );
        """
        with self.connect() as con:
            con.executescript(schema)
            farm_columns = {str(row[1]) for row in con.execute("PRAGMA table_info(farms)").fetchall()}
            for column_name, declaration in [
                ("entity_type", "TEXT NOT NULL DEFAULT 'Farm'"),
                ("geometry_json", "TEXT"),
                ("geometry_hash", "TEXT"),
                ("centroid_lat", "REAL"),
                ("centroid_lon", "REAL"),
                ("area_ha", "REAL"),
            ]:
                if column_name not in farm_columns:
                    con.execute(f"ALTER TABLE farms ADD COLUMN {column_name} {declaration}")
            con.execute("UPDATE farms SET entity_type='Farm' WHERE entity_type IS NULL OR TRIM(entity_type)=''")

            # Release 11.8 adds research-workflow detail in additive extension tables.
            # Core Release 11.7 tables are deliberately not rewritten so existing user data,
            # foreign keys and legacy import/export paths remain backward compatible.
            con.executescript("""
            CREATE TABLE IF NOT EXISTS field_seasons (
                season_id TEXT PRIMARY KEY, field_id TEXT NOT NULL, season_year INTEGER NOT NULL,
                crop TEXT NOT NULL, genotype TEXT, sowing_date TEXT, harvest_date TEXT, status TEXT,
                irrigation_system TEXT, notes TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                UNIQUE(field_id, season_year, crop, genotype),
                FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS task_details (
                task_id TEXT PRIMARY KEY, completion_notes TEXT, parent_task_id TEXT, trial_id TEXT,
                experimental_unit_id TEXT, protocol_id TEXT, updated_at TEXT NOT NULL,
                FOREIGN KEY(task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS observation_protocols (
                protocol_id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT, description TEXT,
                fields_json TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS observation_details (
                observation_id TEXT PRIMARY KEY, trial_id TEXT, experimental_unit_id TEXT, plant_tag TEXT,
                protocol_id TEXT, measurement_json TEXT, updated_at TEXT NOT NULL,
                FOREIGN KEY(observation_id) REFERENCES observations(observation_id) ON DELETE CASCADE,
                FOREIGN KEY(protocol_id) REFERENCES observation_protocols(protocol_id) ON DELETE SET NULL
            );
            CREATE TABLE IF NOT EXISTS operation_details (
                operation_id TEXT PRIMARY KEY, start_time TEXT, end_time TEXT, purpose TEXT, equipment TEXT,
                method TEXT, active_ingredient TEXT, batch_lot TEXT, recommendation_id TEXT,
                record_type TEXT NOT NULL DEFAULT 'Actual', geometry_json TEXT, weather_json TEXT, updated_at TEXT NOT NULL,
                FOREIGN KEY(operation_id) REFERENCES operations(operation_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS sensor_details (
                sensor_id TEXT PRIMARY KEY, installed_at TEXT, retired_at TEXT, updated_at TEXT NOT NULL,
                FOREIGN KEY(sensor_id) REFERENCES sensors(sensor_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS sensor_calibrations (
                calibration_id TEXT PRIMARY KEY, sensor_id TEXT NOT NULL, calibration_date TEXT NOT NULL,
                method TEXT, reference TEXT, result TEXT, notes TEXT, created_at TEXT NOT NULL,
                FOREIGN KEY(sensor_id) REFERENCES sensors(sensor_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS nutrient_sample_details (
                sample_id TEXT PRIMARY KEY, external_sample_id TEXT, depth_from_cm REAL, depth_to_cm REAL,
                tissue_part TEXT, growth_stage TEXT, laboratory TEXT, analytical_method TEXT, units_json TEXT,
                detection_limit TEXT, updated_at TEXT NOT NULL,
                FOREIGN KEY(sample_id) REFERENCES nutrient_samples(sample_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS alert_rule_details (
                rule_id TEXT PRIMARY KEY, persistence_count INTEGER NOT NULL DEFAULT 1, cooldown_hours INTEGER NOT NULL DEFAULT 24,
                crop_stage TEXT, updated_at TEXT NOT NULL,
                FOREIGN KEY(rule_id) REFERENCES alert_rules(rule_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS alert_details (
                alert_id TEXT PRIMARY KEY, acknowledged_at TEXT, snoozed_until TEXT, resolution_notes TEXT,
                false_positive INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL,
                FOREIGN KEY(alert_id) REFERENCES alerts(alert_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS alert_rule_state (
                field_id TEXT NOT NULL, rule_id TEXT NOT NULL, consecutive_count INTEGER NOT NULL DEFAULT 0,
                last_value REAL, last_evaluated_at TEXT, last_alert_at TEXT,
                PRIMARY KEY(field_id, rule_id),
                FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE,
                FOREIGN KEY(rule_id) REFERENCES alert_rules(rule_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS sampling_points (
                sampling_point_id TEXT PRIMARY KEY, field_id TEXT NOT NULL, design_name TEXT, design_type TEXT,
                latitude REAL NOT NULL, longitude REAL NOT NULL, stratum TEXT, status TEXT NOT NULL DEFAULT 'Planned',
                sampled_at TEXT, notes TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_field_seasons_field_year ON field_seasons(field_id, season_year);
            CREATE INDEX IF NOT EXISTS idx_sampling_points_field ON sampling_points(field_id);
            CREATE INDEX IF NOT EXISTS idx_observation_details_protocol ON observation_details(protocol_id);
            CREATE INDEX IF NOT EXISTS idx_sensor_calibrations_sensor ON sensor_calibrations(sensor_id, calibration_date);
            """)
            existing = con.execute("SELECT COUNT(*) FROM alert_rules").fetchone()[0]
            if existing == 0:
                for name, source, metric, operator, threshold, severity, window, notes in DEFAULT_ALERT_RULES:
                    con.execute(
                        "INSERT INTO alert_rules VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (uuid4().hex, name, source, metric, operator, threshold, severity, window, 1, notes, utc_now()),
                    )

    def execute(self, sql: str, params: Sequence[Any] = ()) -> None:
        with self.connect() as con:
            con.execute(sql, tuple(params))

    def frame(self, sql: str, params: Sequence[Any] = ()) -> pd.DataFrame:
        with self.connect() as con:
            return pd.read_sql_query(sql, con, params=tuple(params))

    def audit(self, action: str, entity_type: str = "", entity_id: str = "", user_name: str = "", details: Any = None) -> None:
        self.execute(
            "INSERT INTO audit_log(action, entity_type, entity_id, user_name, details_json, created_at) VALUES (?,?,?,?,?,?)",
            (action, entity_type, entity_id, user_name, json_dumps(details or {}), utc_now()),
        )

    def create_farm(
        self,
        name: str,
        country: str = "",
        admin_area: str = "",
        manager: str = "",
        notes: str = "",
        *,
        entity_type: str = "Farm",
        geometry: Mapping[str, Any] | None = None,
    ) -> str:
        clean_name = str(name or "").strip()
        if not clean_name:
            raise ValueError("Organisation name is required.")
        clean_type = str(entity_type or "Farm").strip()
        if clean_type not in ORGANISATION_TYPES:
            raise ValueError("Organisation type must be Farm or Agricultural research centre.")
        geom = normalise_geojson_geometry(geometry) if geometry else None
        geom_json = json_dumps(geom) if geom else None
        geom_hash = geometry_hash(geom) if geom else None
        centroid_lat = centroid_lon = area_ha = None
        if geom:
            centroid_lat, centroid_lon = geometry_centroid(geom)
            area_ha = geometry_area_hectares(geom)
        farm_id = uuid4().hex
        now = utc_now()
        self.execute(
            """INSERT INTO farms(
                farm_id,name,country,admin_area,manager,notes,created_at,updated_at,
                entity_type,geometry_json,geometry_hash,centroid_lat,centroid_lon,area_ha
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                farm_id, clean_name, str(country or "").strip(), str(admin_area or "").strip(),
                str(manager or "").strip(), str(notes or "").strip(), now, now, clean_type,
                geom_json, geom_hash, centroid_lat, centroid_lon, area_ha,
            ),
        )
        self.audit(
            "create", "farm", farm_id, manager,
            {"name": clean_name, "entity_type": clean_type, "area_ha": area_ha},
        )
        return farm_id

    def farms(self) -> pd.DataFrame:
        return self.frame("SELECT * FROM farms ORDER BY entity_type, name")

    def farm(self, farm_id: str) -> dict | None:
        frame = self.frame("SELECT * FROM farms WHERE farm_id=?", (farm_id,))
        if frame.empty:
            return None
        payload = frame.iloc[0].to_dict()
        payload["geometry"] = json_loads(payload.get("geometry_json"), None)
        return payload

    def update_farm(
        self,
        farm_id: str,
        *,
        name: str,
        country: str = "",
        admin_area: str = "",
        manager: str = "",
        notes: str = "",
        entity_type: str = "Farm",
        geometry: Mapping[str, Any] | None = None,
        boundary_action: str = "keep",
        user_name: str = "",
    ) -> None:
        """Edit an organisation while preserving its ID, fields and dependent records."""
        existing = self.farm(farm_id)
        if not existing:
            raise ValueError("The selected organisation no longer exists.")
        clean_name = str(name or "").strip()
        if not clean_name:
            raise ValueError("Organisation name is required.")
        clean_type = str(entity_type or "Farm").strip()
        if clean_type not in ORGANISATION_TYPES:
            raise ValueError("Organisation type must be Farm or Agricultural research centre.")
        action = str(boundary_action or "keep").strip().casefold()
        if action not in {"keep", "replace", "remove"}:
            raise ValueError("Unknown organisation-boundary action.")
        if action == "replace":
            if not geometry:
                raise ValueError("Draw, upload or derive a valid replacement organisation boundary.")
            geom = normalise_geojson_geometry(geometry)
            geom_json = json_dumps(geom)
            geom_hash = geometry_hash(geom)
            centroid_lat, centroid_lon = geometry_centroid(geom)
            area_ha = geometry_area_hectares(geom)
        elif action == "remove":
            geom_json = geom_hash = centroid_lat = centroid_lon = area_ha = None
        else:
            geom_json = existing.get("geometry_json")
            geom_hash = existing.get("geometry_hash")
            centroid_lat = existing.get("centroid_lat")
            centroid_lon = existing.get("centroid_lon")
            area_ha = existing.get("area_ha")
        after = {
            "name": clean_name,
            "country": str(country or "").strip(),
            "admin_area": str(admin_area or "").strip(),
            "manager": str(manager or "").strip(),
            "notes": str(notes or "").strip(),
            "entity_type": clean_type,
            "geometry_json": geom_json,
            "geometry_hash": geom_hash,
            "centroid_lat": centroid_lat,
            "centroid_lon": centroid_lon,
            "area_ha": area_ha,
        }
        before = {key: existing.get(key) for key in after}
        self.execute(
            """UPDATE farms SET name=?, country=?, admin_area=?, manager=?, notes=?, entity_type=?,
               geometry_json=?, geometry_hash=?, centroid_lat=?, centroid_lon=?, area_ha=?, updated_at=?
               WHERE farm_id=?""",
            (
                after["name"], after["country"], after["admin_area"], after["manager"], after["notes"],
                after["entity_type"], after["geometry_json"], after["geometry_hash"], after["centroid_lat"],
                after["centroid_lon"], after["area_ha"], utc_now(), farm_id,
            ),
        )
        changed = [key for key in after if str(before.get(key) or "") != str(after.get(key) or "")]
        self.audit(
            "update", "farm", farm_id, user_name or after["manager"],
            {"before": before, "after": after, "changed_fields": changed, "boundary_action": action},
        )

    def create_field(self, farm_id: str, name: str, geometry: Mapping[str, Any], **metadata: Any) -> str:
        geom = normalise_geojson_geometry(geometry)
        lat, lon = geometry_centroid(geom)
        area = geometry_area_hectares(geom)
        field_id = uuid4().hex
        now = utc_now()
        self.execute(
            """INSERT INTO fields(field_id,farm_id,name,code,geometry_json,geometry_hash,centroid_lat,centroid_lon,area_ha,
            crop,variety,season_year,irrigation_system,soil_type,status,notes,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                field_id, farm_id, name.strip(), metadata.get("code", ""), json_dumps(geom), geometry_hash(geom),
                lat, lon, area, metadata.get("crop", ""), metadata.get("variety", ""), metadata.get("season_year"),
                metadata.get("irrigation_system", ""), metadata.get("soil_type", ""), metadata.get("status", "Active"),
                metadata.get("notes", ""), now, now,
            ),
        )
        self.audit("create", "field", field_id, metadata.get("user_name", ""), {"name": name, "area_ha": area})
        return field_id

    def fields(self, farm_id: str | None = None) -> pd.DataFrame:
        query = """SELECT f.*, a.name AS farm_name FROM fields f JOIN farms a ON a.farm_id=f.farm_id"""
        params: list[Any] = []
        if farm_id:
            query += " WHERE f.farm_id=?"
            params.append(farm_id)
        query += " ORDER BY a.name, f.name"
        return self.frame(query, params)

    def field(self, field_id: str) -> dict | None:
        df = self.frame("SELECT f.*, a.name AS farm_name FROM fields f JOIN farms a ON a.farm_id=f.farm_id WHERE field_id=?", (field_id,))
        if df.empty:
            return None
        row = df.iloc[0].to_dict()
        row["geometry"] = json_loads(row.get("geometry_json"))
        return row

    def update_field(
        self,
        field_id: str,
        *,
        farm_id: str,
        name: str,
        geometry: Mapping[str, Any] | None = None,
        **metadata: Any,
    ) -> None:
        """Edit field metadata or geometry while preserving the field ID and child records."""
        existing = self.field(field_id)
        if not existing:
            raise ValueError("The selected field no longer exists.")
        if not self.farm(str(farm_id)):
            raise ValueError("The selected destination farm no longer exists.")
        clean_name = str(name or "").strip()
        if not clean_name:
            raise ValueError("Field name is required.")

        geom = normalise_geojson_geometry(geometry) if geometry is not None else existing.get("geometry")
        if not geom:
            raise ValueError("A valid field boundary is required.")
        lat, lon = geometry_centroid(geom)
        area = geometry_area_hectares(geom)
        after = {
            "farm_id": str(farm_id),
            "name": clean_name,
            "code": str(metadata.get("code", existing.get("code") or "") or "").strip(),
            "geometry_json": json_dumps(geom),
            "geometry_hash": geometry_hash(geom),
            "centroid_lat": lat,
            "centroid_lon": lon,
            "area_ha": area,
            "crop": str(metadata.get("crop", existing.get("crop") or "") or "").strip(),
            "variety": str(metadata.get("variety", existing.get("variety") or "") or "").strip(),
            "season_year": metadata.get("season_year", existing.get("season_year")),
            "irrigation_system": str(metadata.get("irrigation_system", existing.get("irrigation_system") or "") or "").strip(),
            "soil_type": str(metadata.get("soil_type", existing.get("soil_type") or "") or "").strip(),
            "status": str(metadata.get("status", existing.get("status") or "Active") or "Active").strip(),
            "notes": str(metadata.get("notes", existing.get("notes") or "") or "").strip(),
        }
        before = {key: existing.get(key) for key in after if key != "geometry_json"}
        before["geometry_hash"] = existing.get("geometry_hash")
        self.execute(
            """UPDATE fields SET farm_id=?, name=?, code=?, geometry_json=?, geometry_hash=?,
            centroid_lat=?, centroid_lon=?, area_ha=?, crop=?, variety=?, season_year=?,
            irrigation_system=?, soil_type=?, status=?, notes=?, updated_at=? WHERE field_id=?""",
            (
                after["farm_id"], after["name"], after["code"], after["geometry_json"],
                after["geometry_hash"], after["centroid_lat"], after["centroid_lon"],
                after["area_ha"], after["crop"], after["variety"], after["season_year"],
                after["irrigation_system"], after["soil_type"], after["status"],
                after["notes"], utc_now(), field_id,
            ),
        )
        comparable_after = {key: value for key, value in after.items() if key != "geometry_json"}
        changed = [
            key for key in comparable_after
            if str(before.get(key) or "") != str(comparable_after.get(key) or "")
        ]
        self.audit(
            "update", "field", field_id, str(metadata.get("user_name", "") or ""),
            {
                "before": before,
                "after": comparable_after,
                "changed_fields": changed,
                "boundary_changed": str(existing.get("geometry_hash") or "") != str(after["geometry_hash"]),
            },
        )

    def field_dependency_counts(self, field_id: str) -> dict[str, int]:
        """Return the records that will be removed with a field."""
        table_map = {
            "Crop-history records": "crop_history",
            "Tasks": "tasks",
            "Scouting observations": "observations",
            "Operations": "operations",
            "Sensors": "sensors",
            "Nutrient samples": "nutrient_samples",
            "Alerts": "alerts",
            "Prescriptions": "prescriptions",
            "User access assignments": "field_access",
        }
        counts: dict[str, int] = {}
        with self.connect() as con:
            for label, table in table_map.items():
                counts[label] = int(con.execute(f"SELECT COUNT(*) FROM {table} WHERE field_id=?", (field_id,)).fetchone()[0])
            counts["Sensor readings"] = int(con.execute(
                "SELECT COUNT(*) FROM sensor_readings WHERE sensor_id IN (SELECT sensor_id FROM sensors WHERE field_id=?)",
                (field_id,),
            ).fetchone()[0])
        return counts

    def farm_dependency_counts(self, farm_id: str) -> dict[str, int]:
        """Return the field and child-record totals that will be removed with a farm."""
        fields = self.fields(farm_id)
        totals: dict[str, int] = {"Fields": int(len(fields))}
        for field_id in fields.get("field_id", pd.Series(dtype=str)).astype(str).tolist():
            for label, count in self.field_dependency_counts(field_id).items():
                totals[label] = totals.get(label, 0) + int(count)
        return totals

    def external_field_dependency_counts(self, field_id: str) -> dict[str, int]:
        """Cross-database links that must block destructive field deletion."""
        root = self.database_path.parent.parent
        counts = {"Linked maize trials": 0, "Persistent Twin links": 0, "External dependency check errors": 0}
        pollination_path = root / "pollination_lab" / "maize_flowering_trials.sqlite"
        if pollination_path.exists():
            try:
                con = sqlite3.connect(f"file:{pollination_path.as_posix()}?mode=ro", uri=True)
                try:
                    if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='trials'").fetchone():
                        counts["Linked maize trials"] = int(con.execute(
                            "SELECT COUNT(*) FROM trials WHERE source_field_id=?", (field_id,)
                        ).fetchone()[0])
                finally:
                    con.close()
            except sqlite3.Error:
                counts["External dependency check errors"] += 1
        twin_path = root / "agrolattice_twin" / "agrolattice_twin.sqlite"
        if twin_path.exists():
            try:
                con = sqlite3.connect(f"file:{twin_path.as_posix()}?mode=ro", uri=True)
                try:
                    if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='twin_links'").fetchone():
                        counts["Persistent Twin links"] = int(con.execute(
                            "SELECT COUNT(*) FROM twin_links WHERE field_id=?", (field_id,)
                        ).fetchone()[0])
                finally:
                    con.close()
            except sqlite3.Error:
                counts["External dependency check errors"] += 1
        return counts

    def external_farm_dependency_counts(self, farm_id: str) -> dict[str, int]:
        totals = {"Linked maize trials": 0, "Persistent Twin links": 0, "External dependency check errors": 0}
        for field_id in self.fields(farm_id).get("field_id", pd.Series(dtype=str)).astype(str).tolist():
            for label, count in self.external_field_dependency_counts(field_id).items():
                totals[label] = totals.get(label, 0) + int(count)
        return totals

    def _attachment_paths_for_fields(self, field_ids: Sequence[str]) -> list[Path]:
        if not field_ids:
            return []
        placeholders = ",".join("?" for _ in field_ids)
        frame = self.frame(
            f"SELECT photo_path FROM observations WHERE field_id IN ({placeholders}) AND photo_path IS NOT NULL AND photo_path<>''",
            tuple(field_ids),
        )
        paths: list[Path] = []
        for value in frame.get("photo_path", pd.Series(dtype=str)).dropna().astype(str):
            candidate = Path(value)
            if not candidate.is_absolute():
                candidate = self.database_path.parent / candidate
            try:
                candidate.resolve().relative_to(self.attachment_root.resolve())
            except Exception:
                continue
            paths.append(candidate)
        return paths

    def delete_field(self, field_id: str, *, user_name: str = "") -> dict[str, int]:
        """Permanently delete one field only when no Trial/Twin references would be orphaned."""
        field = self.field(field_id)
        if not field:
            raise ValueError("The selected field no longer exists.")
        external = self.external_field_dependency_counts(field_id)
        blocking = {key: value for key, value in external.items() if value}
        if blocking:
            detail = ", ".join(f"{key}: {value}" for key, value in blocking.items())
            raise ValueError(
                "Field deletion is blocked because external research objects still reference it (" + detail + "). "
                "Archive the field or remove/reassign those Trial/Twin links first."
            )
        counts = self.field_dependency_counts(field_id)
        attachments = self._attachment_paths_for_fields([field_id])
        with self.connect() as con:
            con.execute("DELETE FROM fields WHERE field_id=?", (field_id,))
            con.execute(
                "INSERT INTO audit_log(action,entity_type,entity_id,user_name,details_json,created_at) VALUES (?,?,?,?,?,?)",
                ("delete", "field", field_id, user_name, json_dumps({"name": field.get("name"), "deleted_records": counts}), utc_now()),
            )
            con.commit()
        for path in attachments:
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass
        return counts

    def delete_farm(self, farm_id: str, *, user_name: str = "") -> dict[str, int]:
        """Permanently delete an organisation only when no Trial/Twin links would be orphaned."""
        external = self.external_farm_dependency_counts(farm_id)
        blocking = {key: value for key, value in external.items() if value}
        if blocking:
            detail = ", ".join(f"{key}: {value}" for key, value in blocking.items())
            raise ValueError(
                "Organisation deletion is blocked because contained fields are referenced externally (" + detail + "). "
                "Archive it or remove/reassign those Trial/Twin links first."
            )
        farms = self.farms()
        match = farms.loc[farms["farm_id"].astype(str).eq(str(farm_id))]
        if match.empty:
            raise ValueError("The selected farm no longer exists.")
        name = str(match.iloc[0]["name"])
        field_ids = self.fields(farm_id).get("field_id", pd.Series(dtype=str)).astype(str).tolist()
        counts = self.farm_dependency_counts(farm_id)
        attachments = self._attachment_paths_for_fields(field_ids)
        with self.connect() as con:
            con.execute("DELETE FROM farms WHERE farm_id=?", (farm_id,))
            con.execute(
                "INSERT INTO audit_log(action,entity_type,entity_id,user_name,details_json,created_at) VALUES (?,?,?,?,?,?)",
                ("delete", "farm", farm_id, user_name, json_dumps({"name": name, "deleted_records": counts}), utc_now()),
            )
            con.commit()
        for path in attachments:
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass
        return counts

    def add_crop_history(self, field_id: str, season_year: int, crop: str, **values: Any) -> str:
        history_id = uuid4().hex
        self.execute(
            "INSERT INTO crop_history VALUES (?,?,?,?,?,?,?,?,?,?)",
            (history_id, field_id, int(season_year), crop, values.get("variety", ""), values.get("sowing_date"),
             values.get("harvest_date"), values.get("yield_t_ha"), values.get("notes", ""), utc_now()),
        )
        self.audit("create", "crop_history", history_id, values.get("user_name", ""), {"field_id": field_id, "crop": crop})
        return history_id

    def create_user(self, name: str, email: str, role: str) -> str:
        user_id = uuid4().hex
        self.execute("INSERT INTO users VALUES (?,?,?,?,?,?)", (user_id, name.strip(), email.strip(), role, 1, utc_now()))
        self.audit("create", "user", user_id, name, {"role": role})
        return user_id

    def users(self) -> pd.DataFrame:
        return self.frame("SELECT * FROM users ORDER BY active DESC, name")

    def grant_access(self, user_id: str, field_id: str, permission: str) -> None:
        self.execute("INSERT OR REPLACE INTO field_access VALUES (?,?,?)", (user_id, field_id, permission))
        self.audit("grant_access", "field", field_id, "", {"user_id": user_id, "permission": permission})

    def create_task(self, field_id: str, title: str, **values: Any) -> str:
        task_id = uuid4().hex
        self.execute(
            "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (task_id, field_id, title.strip(), values.get("category", "Other"), values.get("assigned_to", ""),
             values.get("due_date"), values.get("priority", "Normal"), values.get("status", "Planned"),
             values.get("description", ""), values.get("recurrence", "None"), values.get("source", "Manual"),
             utc_now(), None),
        )
        self.audit("create", "task", task_id, values.get("assigned_to", ""), {"field_id": field_id, "title": title})
        return task_id

    def update_task_status(self, task_id: str, status: str, user_name: str = "", completion_notes: str = "") -> None:
        completed = utc_now() if status == "Completed" else None
        self.execute("UPDATE tasks SET status=?, completed_at=? WHERE task_id=?", (status, completed, task_id))
        self.execute(
            "INSERT OR REPLACE INTO task_details(task_id,completion_notes,parent_task_id,trial_id,experimental_unit_id,protocol_id,updated_at) "
            "VALUES (?, ?, COALESCE((SELECT parent_task_id FROM task_details WHERE task_id=?), NULL), "
            "COALESCE((SELECT trial_id FROM task_details WHERE task_id=?), NULL), "
            "COALESCE((SELECT experimental_unit_id FROM task_details WHERE task_id=?), NULL), "
            "COALESCE((SELECT protocol_id FROM task_details WHERE task_id=?), NULL), ?)",
            (task_id, completion_notes, task_id, task_id, task_id, task_id, utc_now()),
        )
        self.audit("status_change", "task", task_id, user_name, {"status": status, "completion_notes": completion_notes})
        if status == "Completed":
            row = self.frame("SELECT * FROM tasks WHERE task_id=?", (task_id,))
            if not row.empty:
                task = row.iloc[0].to_dict()
                recurrence = str(task.get("recurrence") or "None")
                due = pd.to_datetime(task.get("due_date"), errors="coerce")
                offsets = {"Daily": timedelta(days=1), "Weekly": timedelta(days=7), "Fortnightly": timedelta(days=14), "Monthly": None}
                if recurrence in offsets and pd.notna(due):
                    if recurrence == "Monthly":
                        next_due = (due + pd.DateOffset(months=1)).date()
                    else:
                        next_due = (due.to_pydatetime() + offsets[recurrence]).date()
                    source = f"Recurring from {task_id}"
                    duplicate = self.frame(
                        "SELECT task_id FROM tasks WHERE field_id=? AND due_date=? AND title=? AND status NOT IN ('Completed','Cancelled')",
                        (task.get("field_id"), str(next_due), task.get("title")),
                    )
                    if duplicate.empty:
                        child_id = self.create_task(
                            str(task.get("field_id")), str(task.get("title")), category=task.get("category"),
                            assigned_to=task.get("assigned_to"), due_date=str(next_due), priority=task.get("priority"),
                            status="Planned", recurrence=recurrence, description=task.get("description"), source=source,
                        )
                        self.save_task_details(child_id, parent_task_id=task_id)

    def tasks(self, field_id: str | None = None) -> pd.DataFrame:
        query = """SELECT t.*, f.name AS field_name, a.name AS farm_name FROM tasks t
                   JOIN fields f ON f.field_id=t.field_id JOIN farms a ON a.farm_id=f.farm_id"""
        params: list[Any] = []
        if field_id:
            query += " WHERE t.field_id=?"
            params.append(field_id)
        query += " ORDER BY CASE t.priority WHEN 'Urgent' THEN 0 WHEN 'High' THEN 1 WHEN 'Normal' THEN 2 ELSE 3 END, t.due_date, t.created_at DESC"
        return self.frame(query, params)

    def save_attachment(self, data: bytes, filename: str) -> str:
        extension = Path(filename).suffix.lower()[:10]
        digest = hashlib.sha256(data).hexdigest()[:20]
        path = self.attachment_root / f"{digest}{extension}"
        if not path.exists():
            path.write_bytes(data)
        return str(path.relative_to(self.database_path.parent))

    def create_observation(self, field_id: str, **values: Any) -> str:
        observation_id = uuid4().hex
        self.execute(
            "INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (observation_id, field_id, values.get("task_id") or None, values.get("observed_at") or utc_now(),
             values.get("category", "Crop condition"), int(values.get("severity", 1)), values.get("latitude"),
             values.get("longitude"), values.get("notes", ""), values.get("recommendation", ""),
             values.get("photo_path", ""), values.get("status", "Open"), values.get("created_by", ""), utc_now()),
        )
        self.audit("create", "observation", observation_id, values.get("created_by", ""), {"field_id": field_id, "category": values.get("category")})
        return observation_id

    def observations(self, field_id: str | None = None) -> pd.DataFrame:
        query = """SELECT o.*, f.name AS field_name, a.name AS farm_name, t.title AS task_title FROM observations o
                   JOIN fields f ON f.field_id=o.field_id JOIN farms a ON a.farm_id=f.farm_id
                   LEFT JOIN tasks t ON t.task_id=o.task_id"""
        params: list[Any] = []
        if field_id:
            query += " WHERE o.field_id=?"
            params.append(field_id)
        query += " ORDER BY o.observed_at DESC"
        return self.frame(query, params)

    def create_operation(self, field_id: str, **values: Any) -> str:
        operation_id = uuid4().hex
        self.execute(
            "INSERT INTO operations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (operation_id, field_id, values.get("operation_date") or str(date.today()), values.get("category", "Other"),
             values.get("product", ""), values.get("rate"), values.get("rate_unit", ""), values.get("treated_area_ha"),
             values.get("water_mm"), values.get("cost"), values.get("operator", ""), values.get("notes", ""), utc_now()),
        )
        self.audit("create", "operation", operation_id, values.get("operator", ""), {"field_id": field_id, "category": values.get("category")})
        return operation_id

    def operations(self, field_id: str | None = None) -> pd.DataFrame:
        query = """SELECT o.*, f.name AS field_name, a.name AS farm_name FROM operations o
                   JOIN fields f ON f.field_id=o.field_id JOIN farms a ON a.farm_id=f.farm_id"""
        params: list[Any] = []
        if field_id:
            query += " WHERE o.field_id=?"
            params.append(field_id)
        query += " ORDER BY o.operation_date DESC, o.created_at DESC"
        return self.frame(query, params)

    def create_sensor(self, field_id: str, name: str, sensor_type: str, **values: Any) -> str:
        sensor_id = uuid4().hex
        self.execute(
            "INSERT INTO sensors VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (sensor_id, field_id, name.strip(), sensor_type, values.get("unit", SENSOR_DEFAULT_UNITS.get(sensor_type, "unit")),
             values.get("depth_cm"), values.get("latitude"), values.get("longitude"), values.get("source", "Manual/import"),
             values.get("status", "Active"), values.get("calibration_note", ""), utc_now()),
        )
        self.audit("create", "sensor", sensor_id, "", {"field_id": field_id, "sensor_type": sensor_type})
        return sensor_id

    def sensors(self, field_id: str | None = None) -> pd.DataFrame:
        query = """SELECT s.*, f.name AS field_name, a.name AS farm_name FROM sensors s
                   JOIN fields f ON f.field_id=s.field_id JOIN farms a ON a.farm_id=f.farm_id"""
        params: list[Any] = []
        if field_id:
            query += " WHERE s.field_id=?"
            params.append(field_id)
        query += " ORDER BY f.name, s.name"
        return self.frame(query, params)

    def import_sensor_readings(self, sensor_id: str, frame: pd.DataFrame, timestamp_col: str, value_col: str, source: str = "CSV import") -> dict:
        data = frame[[timestamp_col, value_col]].copy()
        data.columns = ["timestamp", "value"]
        data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce", utc=True)
        data["value"] = pd.to_numeric(data["value"], errors="coerce")
        invalid = int(data[["timestamp", "value"]].isna().any(axis=1).sum())
        data = data.dropna().drop_duplicates("timestamp", keep="last").sort_values("timestamp")
        inserted = 0
        updated = 0
        with self.connect() as con:
            for row in data.itertuples(index=False):
                timestamp = row.timestamp.isoformat()
                existing = con.execute("SELECT reading_id FROM sensor_readings WHERE sensor_id=? AND timestamp=?", (sensor_id, timestamp)).fetchone()
                if existing:
                    con.execute("UPDATE sensor_readings SET value=?, quality_flag=?, source=?, created_at=? WHERE reading_id=?",
                                (float(row.value), "Unchecked", source, utc_now(), existing[0]))
                    updated += 1
                else:
                    con.execute("INSERT INTO sensor_readings VALUES (?,?,?,?,?,?,?)",
                                (uuid4().hex, sensor_id, timestamp, float(row.value), "Unchecked", source, utc_now()))
                    inserted += 1
        self.audit("import", "sensor_readings", sensor_id, "", {"inserted": inserted, "updated": updated, "invalid": invalid})
        return {"inserted": inserted, "updated": updated, "invalid": invalid, "rows": len(data)}

    def readings(self, sensor_id: str | None = None, field_id: str | None = None) -> pd.DataFrame:
        query = """SELECT r.*, s.name AS sensor_name, s.sensor_type, s.unit, s.depth_cm, s.field_id, f.name AS field_name
                   FROM sensor_readings r JOIN sensors s ON s.sensor_id=r.sensor_id JOIN fields f ON f.field_id=s.field_id"""
        params: list[Any] = []
        where = []
        if sensor_id:
            where.append("r.sensor_id=?")
            params.append(sensor_id)
        if field_id:
            where.append("s.field_id=?")
            params.append(field_id)
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY r.timestamp"
        frame = self.frame(query, params)
        if not frame.empty:
            frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
        return frame

    def add_nutrient_sample(self, field_id: str, **values: Any) -> str:
        sample_id = uuid4().hex
        self.execute(
            "INSERT INTO nutrient_samples VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (sample_id, field_id, values.get("sample_date") or str(date.today()), values.get("sample_type", "Soil"),
             values.get("latitude"), values.get("longitude"), values.get("nitrogen"), values.get("phosphorus"),
             values.get("potassium"), values.get("ph"), values.get("ec"), values.get("organic_matter"),
             values.get("notes", ""), utc_now()),
        )
        self.audit("create", "nutrient_sample", sample_id, "", {"field_id": field_id})
        return sample_id

    def nutrient_samples(self, field_id: str | None = None) -> pd.DataFrame:
        query = "SELECT * FROM nutrient_samples"
        params: list[Any] = []
        if field_id:
            query += " WHERE field_id=?"
            params.append(field_id)
        query += " ORDER BY sample_date DESC"
        return self.frame(query, params)

    def alert_rules(self) -> pd.DataFrame:
        return self.frame("SELECT * FROM alert_rules ORDER BY source, name")

    def save_rule(self, **values: Any) -> str:
        rule_id = values.get("rule_id") or uuid4().hex
        self.execute(
            "INSERT OR REPLACE INTO alert_rules VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (rule_id, values["name"], values["source"], values["metric"], values["operator"], float(values["threshold"]),
             values["severity"], int(values.get("window_days", 1)), 1 if values.get("enabled", True) else 0,
             values.get("notes", ""), values.get("created_at") or utc_now()),
        )
        self.audit("save", "alert_rule", rule_id, "", values)
        return rule_id

    def create_alert(self, field_id: str, rule: Mapping[str, Any], value: float, message: str) -> bool:
        day = str(date.today())
        fingerprint = hashlib.sha256(f"{field_id}|{rule.get('rule_id')}|{day}|{round(float(value), 4)}".encode()).hexdigest()
        try:
            self.execute(
                "INSERT INTO alerts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (uuid4().hex, field_id, rule.get("rule_id"), rule.get("source"), rule.get("name"), rule.get("severity"),
                 message, rule.get("metric"), float(value), float(rule.get("threshold")), "Open", fingerprint, utc_now(), None),
            )
            return True
        except sqlite3.IntegrityError:
            return False

    def alerts(self, field_id: str | None = None) -> pd.DataFrame:
        query = """SELECT a.*, f.name AS field_name, farms.name AS farm_name FROM alerts a
                   JOIN fields f ON f.field_id=a.field_id JOIN farms ON farms.farm_id=f.farm_id"""
        params: list[Any] = []
        if field_id:
            query += " WHERE a.field_id=?"
            params.append(field_id)
        query += " ORDER BY CASE a.status WHEN 'Open' THEN 0 WHEN 'Acknowledged' THEN 1 ELSE 2 END, a.created_at DESC"
        return self.frame(query, params)

    def update_alert_status(self, alert_id: str, status: str, user_name: str = "") -> None:
        resolved = utc_now() if status == "Resolved" else None
        self.execute("UPDATE alerts SET status=?, resolved_at=? WHERE alert_id=?", (status, resolved, alert_id))
        self.audit("status_change", "alert", alert_id, user_name, {"status": status})

    def save_prescriptions(self, field_id: str, name: str, variable: str, rate_unit: str, zones: pd.DataFrame) -> int:
        count = 0
        with self.connect() as con:
            for row in zones.to_dict("records"):
                con.execute(
                    "INSERT INTO prescriptions VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (uuid4().hex, field_id, name, variable, rate_unit, str(row.get("zone_label")), float(row.get("rate")),
                     json_dumps(row.get("geometry")), str(row.get("source_metric", "")), utc_now()),
                )
                count += 1
        self.audit("create", "prescription", field_id, "", {"name": name, "zones": count})
        return count

    def prescriptions(self, field_id: str | None = None) -> pd.DataFrame:
        query = "SELECT * FROM prescriptions"
        params: list[Any] = []
        if field_id:
            query += " WHERE field_id=?"
            params.append(field_id)
        query += " ORDER BY created_at DESC"
        return self.frame(query, params)

    def audit_log(self, limit: int = 2000) -> pd.DataFrame:
        return self.frame("SELECT * FROM audit_log ORDER BY audit_id DESC LIMIT ?", (int(limit),))

    def portfolio_summary(self) -> dict:
        with self.connect() as con:
            return {
                "farms": con.execute("SELECT COUNT(*) FROM farms").fetchone()[0],
                "fields": con.execute("SELECT COUNT(*) FROM fields").fetchone()[0],
                "area_ha": con.execute("SELECT COALESCE(SUM(area_ha),0) FROM fields WHERE status='Active'").fetchone()[0],
                "open_tasks": con.execute("SELECT COUNT(*) FROM tasks WHERE status NOT IN ('Completed','Cancelled')").fetchone()[0],
                "open_alerts": con.execute("SELECT COUNT(*) FROM alerts WHERE status!='Resolved'").fetchone()[0],
                "observations": con.execute("SELECT COUNT(*) FROM observations").fetchone()[0],
                "sensors": con.execute("SELECT COUNT(*) FROM sensors WHERE status='Active'").fetchone()[0],
            }

    def field_timeline(self, field_id: str) -> pd.DataFrame:
        frames = []
        task = self.frame("SELECT COALESCE(completed_at, created_at) AS timestamp, 'Task' AS type, title AS title, status AS detail FROM tasks WHERE field_id=?", (field_id,))
        observation = self.frame("SELECT observed_at AS timestamp, 'Observation' AS type, category AS title, notes AS detail FROM observations WHERE field_id=?", (field_id,))
        operation = self.frame("SELECT operation_date AS timestamp, 'Operation' AS type, category AS title, TRIM(COALESCE(product,'') || ' ' || COALESCE(notes,'')) AS detail FROM operations WHERE field_id=?", (field_id,))
        crop = self.frame("SELECT COALESCE(sowing_date, created_at) AS timestamp, 'Crop season' AS type, crop AS title, COALESCE(variety,'') AS detail FROM crop_history WHERE field_id=?", (field_id,))
        season = self.frame("SELECT COALESCE(sowing_date, created_at) AS timestamp, 'Structured season' AS type, crop AS title, TRIM(COALESCE(genotype,'') || ' · ' || COALESCE(status,'')) AS detail FROM field_seasons WHERE field_id=?", (field_id,))
        nutrient = self.frame("SELECT sample_date AS timestamp, 'Sample' AS type, COALESCE(sample_type,'Sample') AS title, COALESCE(notes,'') AS detail FROM nutrient_samples WHERE field_id=?", (field_id,))
        alert = self.frame("SELECT created_at AS timestamp, 'Alert' AS type, COALESCE(alert_type,'Alert') AS title, COALESCE(message,'') AS detail FROM alerts WHERE field_id=?", (field_id,))
        sampling = self.frame("SELECT created_at AS timestamp, 'Sampling design' AS type, COALESCE(design_name,'Sampling design') AS title, COALESCE(design_type,'') AS detail FROM sampling_points WHERE field_id=? GROUP BY design_name,design_type,created_at", (field_id,))
        for frame in (task, observation, operation, crop, season, nutrient, alert, sampling):
            if not frame.empty:
                frames.append(frame)
        if not frames:
            return pd.DataFrame(columns=["timestamp", "type", "title", "detail"])
        combined = pd.concat(frames, ignore_index=True)
        combined["timestamp"] = pd.to_datetime(combined["timestamp"], errors="coerce")
        return combined.sort_values("timestamp", ascending=False)

    def export_database_bytes(self) -> bytes:
        return self.database_path.read_bytes()

    # ---------------- Release 11.8 additive research-workflow extensions ----------------
    def save_season(self, field_id: str, season_year: int, crop: str, **values: Any) -> str:
        season_id = str(values.get("season_id") or uuid4().hex)
        now = utc_now()
        self.execute(
            "INSERT OR REPLACE INTO field_seasons(season_id,field_id,season_year,crop,genotype,sowing_date,harvest_date,status,irrigation_system,notes,created_at,updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,COALESCE((SELECT created_at FROM field_seasons WHERE season_id=?),?),?)",
            (season_id, field_id, int(season_year), crop.strip(), values.get("genotype", ""), values.get("sowing_date"),
             values.get("harvest_date"), values.get("status", "Active"), values.get("irrigation_system", ""), values.get("notes", ""),
             season_id, now, now),
        )
        self.audit("save", "field_season", season_id, values.get("user_name", ""), {"field_id": field_id, "season_year": season_year, "crop": crop})
        return season_id

    def seasons(self, field_id: str | None = None) -> pd.DataFrame:
        sql = "SELECT s.*, f.name AS field_name, a.name AS farm_name FROM field_seasons s JOIN fields f ON f.field_id=s.field_id JOIN farms a ON a.farm_id=f.farm_id"
        params: list[Any] = []
        if field_id:
            sql += " WHERE s.field_id=?"; params.append(field_id)
        sql += " ORDER BY s.season_year DESC, s.updated_at DESC"
        return self.frame(sql, params)

    def save_task_details(self, task_id: str, **values: Any) -> None:
        existing = self.frame("SELECT * FROM task_details WHERE task_id=?", (task_id,))
        current = existing.iloc[0].to_dict() if not existing.empty else {}
        payload = {key: values.get(key, current.get(key)) for key in ["completion_notes","parent_task_id","trial_id","experimental_unit_id","protocol_id"]}
        self.execute(
            "INSERT OR REPLACE INTO task_details(task_id,completion_notes,parent_task_id,trial_id,experimental_unit_id,protocol_id,updated_at) VALUES (?,?,?,?,?,?,?)",
            (task_id, payload["completion_notes"], payload["parent_task_id"], payload["trial_id"], payload["experimental_unit_id"], payload["protocol_id"], utc_now()),
        )

    def task_details(self, task_id: str | None = None) -> pd.DataFrame:
        sql = "SELECT t.*, d.completion_notes,d.parent_task_id,d.trial_id,d.experimental_unit_id,d.protocol_id,d.updated_at AS detail_updated_at FROM tasks t LEFT JOIN task_details d ON d.task_id=t.task_id"
        params: list[Any] = []
        if task_id: sql += " WHERE t.task_id=?"; params.append(task_id)
        return self.frame(sql, params)

    def update_task(self, task_id: str, **values: Any) -> None:
        current = self.frame("SELECT * FROM tasks WHERE task_id=?", (task_id,))
        if current.empty: raise ValueError("Task not found.")
        row = current.iloc[0].to_dict()
        columns = ["title","category","assigned_to","due_date","priority","status","description","recurrence"]
        payload = {c: values.get(c, row.get(c)) for c in columns}
        self.execute(
            "UPDATE tasks SET title=?,category=?,assigned_to=?,due_date=?,priority=?,status=?,description=?,recurrence=? WHERE task_id=?",
            tuple(payload[c] for c in columns) + (task_id,),
        )
        self.save_task_details(task_id, trial_id=values.get("trial_id"), experimental_unit_id=values.get("experimental_unit_id"), protocol_id=values.get("protocol_id"))
        self.audit("update", "task", task_id, values.get("user_name", ""), payload)

    def save_observation_protocol(self, name: str, fields: Sequence[Mapping[str, Any]], **values: Any) -> str:
        protocol_id = str(values.get("protocol_id") or uuid4().hex); now = utc_now()
        self.execute(
            "INSERT OR REPLACE INTO observation_protocols(protocol_id,name,category,description,fields_json,active,created_at,updated_at) "
            "VALUES (?,?,?,?,?,?,COALESCE((SELECT created_at FROM observation_protocols WHERE protocol_id=?),?),?)",
            (protocol_id, name.strip(), values.get("category", "Custom"), values.get("description", ""), json_dumps(list(fields)),
             1 if values.get("active", True) else 0, protocol_id, now, now),
        )
        self.audit("save", "observation_protocol", protocol_id, "", {"name": name})
        return protocol_id

    def observation_protocols(self, active_only: bool = True) -> pd.DataFrame:
        sql = "SELECT * FROM observation_protocols" + (" WHERE active=1" if active_only else "") + " ORDER BY name"
        frame = self.frame(sql)
        if not frame.empty: frame["fields"] = frame["fields_json"].apply(lambda v: json_loads(v, []))
        return frame

    def save_observation_details(self, observation_id: str, **values: Any) -> None:
        self.execute(
            "INSERT OR REPLACE INTO observation_details(observation_id,trial_id,experimental_unit_id,plant_tag,protocol_id,measurement_json,updated_at) VALUES (?,?,?,?,?,?,?)",
            (observation_id, values.get("trial_id"), values.get("experimental_unit_id"), values.get("plant_tag"), values.get("protocol_id"), json_dumps(values.get("measurements") or {}), utc_now()),
        )

    def detailed_observations(self, field_id: str | None = None) -> pd.DataFrame:
        sql = "SELECT o.*,d.trial_id,d.experimental_unit_id,d.plant_tag,d.protocol_id,d.measurement_json,p.name AS protocol_name FROM observations o LEFT JOIN observation_details d ON d.observation_id=o.observation_id LEFT JOIN observation_protocols p ON p.protocol_id=d.protocol_id"
        params: list[Any] = []
        if field_id: sql += " WHERE o.field_id=?"; params.append(field_id)
        sql += " ORDER BY o.observed_at DESC"
        return self.frame(sql, params)

    def save_operation_details(self, operation_id: str, **values: Any) -> None:
        self.execute(
            "INSERT OR REPLACE INTO operation_details(operation_id,start_time,end_time,purpose,equipment,method,active_ingredient,batch_lot,recommendation_id,record_type,geometry_json,weather_json,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (operation_id, values.get("start_time"), values.get("end_time"), values.get("purpose"), values.get("equipment"), values.get("method"),
             values.get("active_ingredient"), values.get("batch_lot"), values.get("recommendation_id"), values.get("record_type", "Actual"),
             json_dumps(values.get("geometry")) if values.get("geometry") else None, json_dumps(values.get("weather")) if values.get("weather") else None, utc_now()),
        )

    def detailed_operations(self, field_id: str | None = None) -> pd.DataFrame:
        sql = "SELECT o.*,d.start_time,d.end_time,d.purpose,d.equipment,d.method,d.active_ingredient,d.batch_lot,d.recommendation_id,d.record_type,d.geometry_json,d.weather_json FROM operations o LEFT JOIN operation_details d ON d.operation_id=o.operation_id"
        params: list[Any] = []
        if field_id: sql += " WHERE o.field_id=?"; params.append(field_id)
        sql += " ORDER BY o.operation_date DESC,o.created_at DESC"
        return self.frame(sql, params)

    def save_sensor_details(self, sensor_id: str, **values: Any) -> None:
        current = self.frame("SELECT * FROM sensor_details WHERE sensor_id=?", (sensor_id,))
        row = current.iloc[0].to_dict() if not current.empty else {}
        self.execute("INSERT OR REPLACE INTO sensor_details(sensor_id,installed_at,retired_at,updated_at) VALUES (?,?,?,?)",
                     (sensor_id, values.get("installed_at", row.get("installed_at")), values.get("retired_at", row.get("retired_at")), utc_now()))

    def update_sensor(self, sensor_id: str, **values: Any) -> None:
        current = self.frame("SELECT * FROM sensors WHERE sensor_id=?", (sensor_id,))
        if current.empty: raise ValueError("Sensor not found.")
        row = current.iloc[0].to_dict(); cols=["name","sensor_type","unit","depth_cm","latitude","longitude","source","status","calibration_note"]
        payload={c:values.get(c,row.get(c)) for c in cols}
        self.execute("UPDATE sensors SET name=?,sensor_type=?,unit=?,depth_cm=?,latitude=?,longitude=?,source=?,status=?,calibration_note=? WHERE sensor_id=?", tuple(payload[c] for c in cols)+(sensor_id,))
        detail_updates = {}
        if values.get("installed_at") is not None:
            detail_updates["installed_at"] = values.get("installed_at")
        if values.get("retired_at") is not None:
            detail_updates["retired_at"] = values.get("retired_at")
        if detail_updates:
            self.save_sensor_details(sensor_id, **detail_updates)
        self.audit("update", "sensor", sensor_id, "", payload)

    def add_sensor_calibration(self, sensor_id: str, calibration_date: str, **values: Any) -> str:
        calibration_id=uuid4().hex
        self.execute("INSERT INTO sensor_calibrations VALUES (?,?,?,?,?,?,?,?)", (calibration_id,sensor_id,calibration_date,values.get("method",""),values.get("reference",""),values.get("result",""),values.get("notes",""),utc_now()))
        self.audit("create","sensor_calibration",calibration_id,"",{"sensor_id":sensor_id})
        return calibration_id

    def sensor_calibrations(self, sensor_id: str | None = None) -> pd.DataFrame:
        sql="SELECT c.*,s.name AS sensor_name FROM sensor_calibrations c JOIN sensors s ON s.sensor_id=c.sensor_id"; params=[]
        if sensor_id: sql+=" WHERE c.sensor_id=?"; params.append(sensor_id)
        sql+=" ORDER BY c.calibration_date DESC"; return self.frame(sql,params)

    def save_nutrient_sample_details(self, sample_id: str, **values: Any) -> None:
        self.execute(
            "INSERT OR REPLACE INTO nutrient_sample_details(sample_id,external_sample_id,depth_from_cm,depth_to_cm,tissue_part,growth_stage,laboratory,analytical_method,units_json,detection_limit,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (sample_id,values.get("external_sample_id"),values.get("depth_from_cm"),values.get("depth_to_cm"),values.get("tissue_part"),values.get("growth_stage"),
             values.get("laboratory"),values.get("analytical_method"),json_dumps(values.get("units") or {}),values.get("detection_limit"),utc_now()),
        )

    def detailed_nutrient_samples(self, field_id: str | None = None) -> pd.DataFrame:
        sql="SELECT n.*,d.external_sample_id,d.depth_from_cm,d.depth_to_cm,d.tissue_part,d.growth_stage,d.laboratory,d.analytical_method,d.units_json,d.detection_limit FROM nutrient_samples n LEFT JOIN nutrient_sample_details d ON d.sample_id=n.sample_id"; params=[]
        if field_id: sql+=" WHERE n.field_id=?"; params.append(field_id)
        sql+=" ORDER BY n.sample_date DESC"; return self.frame(sql,params)

    def save_alert_rule_details(self, rule_id: str, **values: Any) -> None:
        self.execute("INSERT OR REPLACE INTO alert_rule_details(rule_id,persistence_count,cooldown_hours,crop_stage,updated_at) VALUES (?,?,?,?,?)",
                     (rule_id,int(values.get("persistence_count",1)),int(values.get("cooldown_hours",24)),values.get("crop_stage",""),utc_now()))

    def save_alert_details(self, alert_id: str, **values: Any) -> None:
        current=self.frame("SELECT * FROM alert_details WHERE alert_id=?",(alert_id,)); row=current.iloc[0].to_dict() if not current.empty else {}
        self.execute("INSERT OR REPLACE INTO alert_details(alert_id,acknowledged_at,snoozed_until,resolution_notes,false_positive,updated_at) VALUES (?,?,?,?,?,?)",
                     (alert_id,values.get("acknowledged_at",row.get("acknowledged_at")),values.get("snoozed_until",row.get("snoozed_until")),values.get("resolution_notes",row.get("resolution_notes")),int(values.get("false_positive",row.get("false_positive") or 0)),utc_now()))

    def save_sampling_points(self, field_id: str, points: pd.DataFrame, design_name: str, design_type: str) -> int:
        now=utc_now(); count=0
        with self.connect() as con:
            for row in points.to_dict("records"):
                con.execute("INSERT INTO sampling_points(sampling_point_id,field_id,design_name,design_type,latitude,longitude,stratum,status,sampled_at,notes,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                            (str(row.get("sample_id") or uuid4().hex),field_id,design_name,design_type,float(row["latitude"]),float(row["longitude"]),str(row.get("stratum") or ""),"Planned",None,"",now,now)); count+=1
        self.audit("create","sampling_design",field_id,"",{"design_name":design_name,"design_type":design_type,"points":count}); return count

    def sampling_points(self, field_id: str | None = None) -> pd.DataFrame:
        sql="SELECT * FROM sampling_points"; params=[]
        if field_id: sql+=" WHERE field_id=?"; params.append(field_id)
        sql+=" ORDER BY created_at DESC,sampling_point_id"; return self.frame(sql,params)

    def portfolio_attention(self) -> pd.DataFrame:
        return self.frame("""
        SELECT f.field_id,a.name AS farm_name,f.name AS field_name,f.area_ha,f.crop,f.variety,f.season_year,f.status,
               COALESCE(t.open_tasks,0) AS open_tasks,COALESCE(t.overdue_tasks,0) AS overdue_tasks,
               COALESCE(al.open_alerts,0) AS open_alerts,COALESCE(ob.severe_observations,0) AS severe_observations,
               COALESCE(se.active_sensors,0) AS active_sensors,se.latest_reading
        FROM fields f JOIN farms a ON a.farm_id=f.farm_id
        LEFT JOIN (SELECT field_id, SUM(CASE WHEN status NOT IN ('Completed','Cancelled') THEN 1 ELSE 0 END) open_tasks,
                  SUM(CASE WHEN status NOT IN ('Completed','Cancelled') AND due_date < date('now') THEN 1 ELSE 0 END) overdue_tasks FROM tasks GROUP BY field_id) t ON t.field_id=f.field_id
        LEFT JOIN (SELECT field_id, SUM(CASE WHEN status!='Resolved' THEN 1 ELSE 0 END) open_alerts FROM alerts GROUP BY field_id) al ON al.field_id=f.field_id
        LEFT JOIN (SELECT field_id, SUM(CASE WHEN severity>=4 THEN 1 ELSE 0 END) severe_observations FROM observations GROUP BY field_id) ob ON ob.field_id=f.field_id
        LEFT JOIN (SELECT s.field_id,SUM(CASE WHEN s.status='Active' THEN 1 ELSE 0 END) active_sensors,MAX(r.timestamp) latest_reading FROM sensors s LEFT JOIN sensor_readings r ON r.sensor_id=s.sensor_id GROUP BY s.field_id) se ON se.field_id=f.field_id
        ORDER BY a.name,f.name
        """)


# ------------------------------ analytics ------------------------------

def sensor_quality_report(frame: pd.DataFrame, sensor_type: str = "") -> tuple[pd.DataFrame, dict]:
    if frame is None or frame.empty:
        return pd.DataFrame(), {"rows": 0, "valid": 0, "duplicates": 0, "missing": 0, "stale": True, "flatline": False}
    data = frame.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce", utc=True)
    data["value"] = pd.to_numeric(data["value"], errors="coerce")
    data["quality_flag"] = "Good"
    data.loc[data["timestamp"].isna() | data["value"].isna(), "quality_flag"] = "Invalid"
    duplicates = data.duplicated("timestamp", keep=False)
    data.loc[duplicates & data["quality_flag"].eq("Good"), "quality_flag"] = "Duplicate timestamp"
    ranges = {
        "Soil moisture": (0, 100), "Soil temperature": (-20, 70), "Air temperature": (-50, 70),
        "Relative humidity": (0, 100), "Rain gauge": (0, 1000), "Wind speed": (0, 100),
        "Leaf wetness": (0, 100), "Soil EC/salinity": (0, 100), "Nitrate": (0, 10000),
    }
    if sensor_type in ranges:
        low, high = ranges[sensor_type]
        out = ~data["value"].between(low, high) & data["value"].notna()
        data.loc[out, "quality_flag"] = "Outside broad physical range"
    valid_values = data.loc[data["quality_flag"].eq("Good"), "value"]
    flatline = bool(len(valid_values) >= 10 and valid_values.tail(10).nunique(dropna=True) <= 1)
    latest = data["timestamp"].max()
    stale = bool(pd.isna(latest) or latest < pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=7))
    summary = {
        "rows": int(len(data)), "valid": int(data["quality_flag"].eq("Good").sum()),
        "duplicates": int(duplicates.sum()), "missing": int(data[["timestamp", "value"]].isna().any(axis=1).sum()),
        "stale": stale, "flatline": flatline, "latest": latest,
    }
    return data, summary


def _compare(value: float, operator: str, threshold: float) -> bool:
    if operator == "<=":
        return value <= threshold
    if operator == "<":
        return value < threshold
    if operator == ">=":
        return value >= threshold
    if operator == ">":
        return value > threshold
    if operator == "==":
        return value == threshold
    raise ValueError(f"Unsupported operator: {operator}")


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return float(2 * radius * math.asin(math.sqrt(a)))


def _project_matches_field(context: Mapping[str, Any], field: Mapping[str, Any], tolerance_km: float = 10.0) -> bool:
    project = context.get("active_project")
    if not isinstance(project, Mapping):
        return False
    project_geometry = _geometry_from_project(project)
    if project_geometry:
        try:
            return geometry_hash(project_geometry) == str(field.get("geometry_hash"))
        except Exception:
            pass
    location = project.get("location") or {}
    lat = location.get("latitude") or location.get("lat")
    lon = location.get("longitude") or location.get("lon") or location.get("lng")
    try:
        return _distance_km(float(lat), float(lon), float(field["centroid_lat"]), float(field["centroid_lon"])) <= tolerance_km
    except Exception:
        return False


def _satellite_matches_field(context: Mapping[str, Any], field: Mapping[str, Any]) -> bool:
    geometry = context.get("satellite_geometry")
    if not geometry:
        return False
    try:
        return geometry_hash(geometry) == str(field.get("geometry_hash"))
    except Exception:
        return False


def latest_metrics_from_context(context: Mapping[str, Any], db: FieldOperationsDatabase, field_id: str) -> dict[str, float]:
    metrics: dict[str, float] = {}
    field = db.field(field_id) or {}
    satellite = context.get("satellite_time_series")
    if _satellite_matches_field(context, field) and isinstance(satellite, pd.DataFrame) and not satellite.empty:
        sat = satellite.copy()
        date_cols = [c for c in sat.columns if str(c).casefold() in {"date", "datetime", "acquisition date", "acquisition_date"}]
        if date_cols:
            sat[date_cols[0]] = pd.to_datetime(sat[date_cols[0]], errors="coerce")
            sat = sat.sort_values(date_cols[0])
        for index_name in ["NDVI", "NDMI", "EVI", "NDRE", "MSAVI"]:
            matches = [c for c in sat.columns if str(c).strip().upper() == index_name]
            if matches:
                values = pd.to_numeric(sat[matches[0]], errors="coerce").dropna()
                if not values.empty:
                    metrics[index_name] = float(values.iloc[-1])
                    if index_name == "NDVI" and len(values) >= 2 and values.iloc[-2] != 0:
                        metrics["NDVI change (%)"] = float(100 * (values.iloc[-1] - values.iloc[-2]) / abs(values.iloc[-2]))
    root = context.get("root_zone")
    project_matches = _project_matches_field(context, field)
    if project_matches and isinstance(root, pd.DataFrame) and not root.empty:
        root = root.copy()
        for source_col, metric in [("Ks", "Ks"), ("Relative depletion", "Relative depletion"), ("Depletion end (mm)", "Depletion end (mm)")]:
            if source_col in root.columns:
                vals = pd.to_numeric(root[source_col], errors="coerce").dropna()
                if not vals.empty:
                    metrics[metric] = float(vals.iloc[-1])
    weather = context.get("daily_weather")
    if project_matches and isinstance(weather, pd.DataFrame) and not weather.empty:
        for metric, aliases in {
            "Tmax": ["Tmax", "T2M_MAX", "Maximum temperature", "Temperature maximum"],
            "Tmin": ["Tmin", "T2M_MIN", "Minimum temperature", "Temperature minimum"],
            "Rain": ["Rain", "PRECTOTCORR", "Precipitation", "Precipitation (mm)"],
        }.items():
            col = next((c for c in aliases if c in weather.columns), None)
            if col:
                vals = pd.to_numeric(weather[col], errors="coerce").dropna()
                if not vals.empty:
                    metrics[metric] = float(vals.iloc[-1])
    readings = db.readings(field_id=field_id)
    if not readings.empty:
        latest = readings.sort_values("timestamp").groupby("sensor_type", as_index=False).tail(1)
        for row in latest.to_dict("records"):
            if pd.notna(row.get("value")):
                metrics[str(row.get("sensor_type"))] = float(row["value"])
    return metrics


def evaluate_alert_rules(db: FieldOperationsDatabase, field_id: str, metrics: Mapping[str, float]) -> dict:
    rules = db.alert_rules()
    generated = 0
    evaluated = 0
    details = []
    now = pd.Timestamp.now(tz="UTC")
    for rule in rules.to_dict("records"):
        if not int(rule.get("enabled", 1)):
            continue
        metric = str(rule.get("metric"))
        if metric not in metrics or not np.isfinite(metrics[metric]):
            continue
        evaluated += 1
        value = float(metrics[metric])
        triggered = _compare(value, str(rule["operator"]), float(rule["threshold"]))
        detail = db.frame("SELECT * FROM alert_rule_details WHERE rule_id=?", (rule.get("rule_id"),))
        persistence = int(detail.iloc[0].get("persistence_count") or 1) if not detail.empty else 1
        cooldown_hours = int(detail.iloc[0].get("cooldown_hours") or 24) if not detail.empty else 24
        state = db.frame("SELECT * FROM alert_rule_state WHERE field_id=? AND rule_id=?", (field_id, rule.get("rule_id")))
        previous_count = int(state.iloc[0].get("consecutive_count") or 0) if not state.empty else 0
        last_alert = pd.to_datetime(state.iloc[0].get("last_alert_at"), errors="coerce", utc=True) if not state.empty else pd.NaT
        consecutive = previous_count + 1 if triggered else 0
        cooldown_clear = bool(pd.isna(last_alert) or now - last_alert >= pd.Timedelta(hours=cooldown_hours))
        should_alert = bool(triggered and consecutive >= persistence and cooldown_clear)
        details.append({
            "Rule": rule["name"], "Metric": metric, "Value": value,
            "Threshold": f"{rule['operator']} {rule['threshold']}", "Triggered now": triggered,
            "Consecutive": f"{consecutive}/{persistence}", "Cooldown clear": cooldown_clear, "Alert eligible": should_alert,
        })
        alert_created = False
        if should_alert:
            message = (
                f"{rule['name']}: {metric}={value:.3g}, threshold {rule['operator']} {float(rule['threshold']):.3g}; "
                f"trigger persisted for {consecutive} evaluation(s). Verify conditions before acting."
            )
            alert_created = db.create_alert(field_id, rule, value, message)
            generated += int(alert_created)
        db.execute(
            "INSERT OR REPLACE INTO alert_rule_state(field_id,rule_id,consecutive_count,last_value,last_evaluated_at,last_alert_at) VALUES (?,?,?,?,?,?)",
            (field_id, rule.get("rule_id"), consecutive, value, now.isoformat(), now.isoformat() if alert_created else (None if state.empty else state.iloc[0].get("last_alert_at"))),
        )
    return {"evaluated": evaluated, "generated": generated, "details": pd.DataFrame(details)}


def irrigation_advisory(context: Mapping[str, Any], field: Mapping[str, Any], db: FieldOperationsDatabase) -> dict:
    root = context.get("root_zone")
    project_matches = _project_matches_field(context, field)
    result = {
        "source": "Unavailable", "status": "Insufficient data", "recommended_mm": None,
        "urgency": "Unknown", "reason": "Run Soil-water balance or connect a calibrated soil-moisture sensor.",
    }
    if project_matches and isinstance(root, pd.DataFrame) and not root.empty and {"Depletion end (mm)", "RAW (mm)", "TAW (mm)"}.issubset(root.columns):
        row = root.iloc[-1]
        depletion = float(pd.to_numeric(row.get("Depletion end (mm)"), errors="coerce"))
        raw = float(pd.to_numeric(row.get("RAW (mm)"), errors="coerce"))
        taw = float(pd.to_numeric(row.get("TAW (mm)"), errors="coerce"))
        if np.isfinite(depletion) and np.isfinite(raw) and np.isfinite(taw):
            trigger = depletion >= raw
            refill = max(0.0, depletion - 0.20 * taw)
            result.update({
                "source": "Soil-water balance", "status": "Trigger reached" if trigger else "No trigger",
                "recommended_mm": float(refill) if trigger else 0.0,
                "urgency": "High" if depletion >= 0.8 * taw else ("Medium" if trigger else "Low"),
                "reason": f"Latest modelled depletion is {depletion:.1f} mm; RAW is {raw:.1f} mm and TAW is {taw:.1f} mm.",
            })
            return result
    readings = db.readings(field_id=str(field.get("field_id")))
    sensors = db.sensors(str(field.get("field_id")))
    moisture_ids = sensors.loc[sensors["sensor_type"].eq("Soil moisture"), "sensor_id"].tolist() if not sensors.empty else []
    if moisture_ids and not readings.empty:
        moisture = readings[readings["sensor_id"].isin(moisture_ids)].sort_values("timestamp")
        if not moisture.empty:
            latest = float(moisture.iloc[-1]["value"])
            result.update({
                "source": "Soil-moisture sensor", "status": "Review threshold",
                "recommended_mm": None, "urgency": "High" if latest <= 18 else "Low",
                "reason": f"Latest soil-moisture reading is {latest:.1f} {moisture.iloc[-1].get('unit','')}. A calibrated field-capacity/RAW threshold is required before calculating an irrigation depth.",
            })
    return result


def generate_sampling_grid(geometry: Mapping[str, Any], spacing_m: float, inset_m: float = 0.0) -> pd.DataFrame:
    geom = shape(normalise_geojson_geometry(geometry))
    lon, lat = geom.centroid.x, geom.centroid.y
    zone = max(1, min(60, int((lon + 180) // 6) + 1))
    epsg = 32600 + zone if lat >= 0 else 32700 + zone
    to_local = Transformer.from_crs(4326, epsg, always_xy=True)
    to_wgs = Transformer.from_crs(epsg, 4326, always_xy=True)
    local = shapely_transform(to_local.transform, geom)
    if inset_m:
        local = local.buffer(-float(inset_m))
        if local.is_empty:
            raise ValueError("The inset is larger than the field geometry.")
    minx, miny, maxx, maxy = local.bounds
    rows = []
    x_values = np.arange(minx + spacing_m / 2, maxx, spacing_m)
    y_values = np.arange(miny + spacing_m / 2, maxy, spacing_m)
    count = 0
    for x in x_values:
        for y in y_values:
            point = Point(float(x), float(y))
            if local.contains(point):
                lon_wgs, lat_wgs = to_wgs.transform(x, y)
                count += 1
                rows.append({"sample_id": f"S{count:04d}", "latitude": lat_wgs, "longitude": lon_wgs, "geometry": mapping(Point(lon_wgs, lat_wgs))})
    return pd.DataFrame(rows)


def build_management_zones(points: pd.DataFrame, geometry: Mapping[str, Any], value_column: str, n_zones: int, rate_low: float, rate_high: float) -> pd.DataFrame:
    required = {"latitude", "longitude", value_column}
    if not required.issubset(points.columns):
        raise ValueError(f"Point data must contain {sorted(required)}")
    data = points.copy()
    data["latitude"] = pd.to_numeric(data["latitude"], errors="coerce")
    data["longitude"] = pd.to_numeric(data["longitude"], errors="coerce")
    data[value_column] = pd.to_numeric(data[value_column], errors="coerce")
    data = data.dropna(subset=["latitude", "longitude", value_column])
    field_shape = shape(normalise_geojson_geometry(geometry))
    data = data[data.apply(lambda r: field_shape.covers(Point(r["longitude"], r["latitude"])), axis=1)]
    if len(data) < max(6, n_zones * 2):
        raise ValueError("Not enough valid in-field samples for the requested number of zones.")
    features = data[[value_column]].to_numpy()
    scaled = StandardScaler().fit_transform(features)
    model = KMeans(n_clusters=int(n_zones), random_state=42, n_init=20)
    data["cluster"] = model.fit_predict(scaled)
    cluster_means = data.groupby("cluster")[value_column].mean().sort_values()
    rank_map = {cluster: rank + 1 for rank, cluster in enumerate(cluster_means.index)}
    data["zone_rank"] = data["cluster"].map(rank_map)
    data["zone_label"] = data["zone_rank"].map(lambda x: f"Zone {int(x)}")
    if n_zones == 1:
        data["rate"] = float((rate_low + rate_high) / 2)
    else:
        data["rate"] = rate_low + (data["zone_rank"] - 1) * (rate_high - rate_low) / (n_zones - 1)
    data["source_metric"] = value_column
    # Point-buffer polygons provide a generic, transparent prescription surface without pretending to be a machine-ready raster.
    lon, lat = field_shape.centroid.x, field_shape.centroid.y
    zone = max(1, min(60, int((lon + 180) // 6) + 1))
    epsg = 32600 + zone if lat >= 0 else 32700 + zone
    to_local = Transformer.from_crs(4326, epsg, always_xy=True)
    to_wgs = Transformer.from_crs(epsg, 4326, always_xy=True)
    local_field = shapely_transform(to_local.transform, field_shape)
    local_points = [Point(*to_local.transform(float(r.longitude), float(r.latitude))) for r in data.itertuples()]
    # Use a conservative buffer derived from median nearest-neighbour spacing.
    distances = []
    for i, p in enumerate(local_points):
        nearest = min((p.distance(q) for j, q in enumerate(local_points) if j != i), default=25.0)
        distances.append(nearest)
    radius = max(2.0, float(np.nanmedian(distances)) * 0.55)
    geometries = []
    for p in local_points:
        cell = p.buffer(radius).intersection(local_field)
        geometries.append(mapping(shapely_transform(to_wgs.transform, cell)))
    data["geometry"] = geometries
    return data.reset_index(drop=True)


def offline_field_pack(db: FieldOperationsDatabase, field_id: str, context: Mapping[str, Any] | None = None) -> bytes:
    field = db.field(field_id)
    if not field:
        raise ValueError("Field not found.")
    tasks = db.tasks(field_id)
    observations = db.observations(field_id)
    operations = db.operations(field_id)
    sensors = db.sensors(field_id)
    readings = db.readings(field_id=field_id)
    timeline = db.field_timeline(field_id)
    field_geojson = geometry_feature_collection([geometry_feature(field["geometry"], {"field_id": field_id, "name": field["name"]})])
    observation_template = pd.DataFrame(columns=[
        "external_id", "observed_at", "category", "severity_1_5", "latitude", "longitude", "notes", "recommendation", "created_by"
    ])
    task_update_template = tasks[["task_id", "title", "status"]].copy() if not tasks.empty else pd.DataFrame(columns=["task_id", "title", "status"])
    operation_template = pd.DataFrame(columns=[
        "operation_date", "category", "product", "rate", "rate_unit", "treated_area_ha",
        "water_mm", "cost", "operator", "notes"
    ])
    with io.BytesIO() as buffer:
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("README_FIELD_PACK.txt", (
                "Offline Field Pack\n\n"
                "1. Keep field_boundary.geojson on the mobile device for navigation.\n"
                "2. Add new scouting rows to observation_import_template.csv.\n"
                "3. Update only the status column in task_status_updates.csv.\n"
                "4. Import the completed files through Data exchange & audit.\n"
                "5. This package is a file-based offline workflow; it is not automatic cloud synchronisation.\n"
            ))
            zf.writestr("manifest.json", json_dumps({"module_version": MODULE_VERSION, "generated_utc": utc_now(), "field": {k: v for k, v in field.items() if k not in {"geometry_json", "geometry"}}}))
            zf.writestr("field_boundary.geojson", json_dumps(field_geojson))
            zf.writestr("tasks.csv", tasks.to_csv(index=False))
            zf.writestr("task_status_updates.csv", task_update_template.to_csv(index=False))
            zf.writestr("observation_import_template.csv", observation_template.to_csv(index=False))
            zf.writestr("operation_import_template.csv", operation_template.to_csv(index=False))
            zf.writestr("observations.csv", observations.to_csv(index=False))
            zf.writestr("operations.csv", operations.to_csv(index=False))
            zf.writestr("sensors.csv", sensors.to_csv(index=False))
            zf.writestr("sensor_readings.csv", readings.to_csv(index=False))
            zf.writestr("field_timeline.csv", timeline.to_csv(index=False))
            if context:
                sat = context.get("satellite_time_series")
                root = context.get("root_zone")
                weather = context.get("daily_weather")
                if isinstance(sat, pd.DataFrame):
                    zf.writestr("linked_satellite_time_series.csv", sat.to_csv(index=False))
                if isinstance(root, pd.DataFrame):
                    zf.writestr("linked_root_zone_balance.csv", root.to_csv(index=False))
                if isinstance(weather, pd.DataFrame):
                    zf.writestr("linked_daily_weather.csv", weather.to_csv(index=False))
        return buffer.getvalue()


def field_report_package(db: FieldOperationsDatabase, field_id: str, context: Mapping[str, Any] | None = None) -> bytes:
    field = db.field(field_id)
    if not field:
        raise ValueError("Field not found.")
    context = context or {}
    tasks = db.tasks(field_id)
    observations = db.observations(field_id)
    operations = db.operations(field_id)
    sensors = db.sensors(field_id)
    alerts = db.alerts(field_id)
    metrics = latest_metrics_from_context(context, db, field_id)
    map_obj = _map_for_geometry(field["geometry"])
    folium.GeoJson(
        geometry_feature(field["geometry"], {"name": field["name"], "farm": field["farm_name"], "area_ha": field["area_ha"]}),
        style_function=lambda _: {"weight": 3, "fillOpacity": 0.15},
        tooltip=folium.GeoJsonTooltip(fields=["farm", "name", "area_ha"]),
    ).add_to(map_obj)
    for row in observations.dropna(subset=["latitude", "longitude"]).to_dict("records") if not observations.empty else []:
        folium.CircleMarker([float(row["latitude"]), float(row["longitude"])], radius=4 + int(row.get("severity") or 1),
                            popup=html.escape(str(row.get("notes") or "")), fill=True).add_to(map_obj)
    for row in sensors.dropna(subset=["latitude", "longitude"]).to_dict("records") if not sensors.empty else []:
        folium.Marker([float(row["latitude"]), float(row["longitude"])], tooltip=str(row.get("name"))).add_to(map_obj)
    map_html = map_obj.get_root().render()
    summary_rows = [
        ("Farm", field.get("farm_name")), ("Field", field.get("name")), ("Code", field.get("code")),
        ("Area (ha)", f"{float(field.get('area_ha') or 0):.3f}"), ("Crop", field.get("crop")),
        ("Variety", field.get("variety")), ("Season", field.get("season_year")),
        ("Irrigation", field.get("irrigation_system")), ("Soil", field.get("soil_type")),
        ("Open tasks", int((~tasks["status"].isin(["Completed", "Cancelled"])).sum()) if not tasks.empty else 0),
        ("Open alerts", int(alerts["status"].ne("Resolved").sum()) if not alerts.empty else 0),
        ("Observations", len(observations)), ("Sensors", len(sensors)),
    ]
    metric_html = pd.DataFrame([{"Metric": k, "Latest value": v} for k, v in metrics.items()]).to_html(index=False) if metrics else "<p>No verified linked metrics available.</p>"
    def table_html(frame: pd.DataFrame, columns: Sequence[str] | None = None, limit: int = 100) -> str:
        if frame is None or frame.empty:
            return "<p>No records.</p>"
        view = frame.copy()
        if columns:
            view = view[[c for c in columns if c in view.columns]]
        return view.head(limit).to_html(index=False, escape=True)
    report_html = f"""<!doctype html>
<html><head><meta charset='utf-8'><title>{html.escape(str(field['name']))} field report</title>
<style>body{{font-family:Arial,sans-serif;max-width:1200px;margin:32px auto;padding:0 24px;color:#1f2933}}
h1,h2{{color:#234f33}}table{{border-collapse:collapse;width:100%;margin:12px 0 28px}}th,td{{border:1px solid #d9e2e8;padding:7px;text-align:left}}th{{background:#edf4ef}}
.notice{{background:#fff7d6;border-left:4px solid #d39e00;padding:12px}}iframe{{width:100%;height:620px;border:1px solid #ddd}}</style></head><body>
<h1>{html.escape(str(field['farm_name']))} — {html.escape(str(field['name']))}</h1>
<p>Generated {html.escape(utc_now())} with Field Operations Suite {MODULE_VERSION}.</p>
<div class='notice'>This report summarises recorded data and linked app results. Alerts and advisories require field verification and agronomic review.</div>
<h2>Field summary</h2>{pd.DataFrame(summary_rows, columns=['Item','Value']).to_html(index=False, escape=True)}
<h2>Latest verified linked metrics</h2>{metric_html}
<h2>Open and recent tasks</h2>{table_html(tasks, ['title','category','assigned_to','due_date','priority','status','description'])}
<h2>Recent alerts</h2>{table_html(alerts, ['created_at','severity','alert_type','metric','value','threshold','status','message'])}
<h2>Recent scouting observations</h2>{table_html(observations, ['observed_at','category','severity','latitude','longitude','notes','recommendation','created_by'])}
<h2>Recent operations and inputs</h2>{table_html(operations, ['operation_date','category','product','rate','rate_unit','treated_area_ha','water_mm','cost','operator','notes'])}
<h2>Field map</h2><p>Open <strong>field_map.html</strong> from the same report folder for the interactive map.</p>
</body></html>"""
    with io.BytesIO() as buffer:
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("field_report.html", report_html)
            zf.writestr("field_map.html", map_html)
            zf.writestr("field_boundary.geojson", json_dumps(geometry_feature_collection([geometry_feature(field["geometry"], {"field_id": field_id, "name": field["name"]})])))
            zf.writestr("latest_metrics.csv", pd.DataFrame([{"Metric": k, "Latest value": v} for k, v in metrics.items()]).to_csv(index=False))
            zf.writestr("tasks.csv", tasks.to_csv(index=False))
            zf.writestr("alerts.csv", alerts.to_csv(index=False))
            zf.writestr("observations.csv", observations.to_csv(index=False))
            zf.writestr("operations.csv", operations.to_csv(index=False))
            zf.writestr("sensors.csv", sensors.to_csv(index=False))
        return buffer.getvalue()


def full_operations_export(db: FieldOperationsDatabase) -> bytes:
    tables = [
        "farms", "fields", "crop_history", "users", "field_access", "tasks", "observations", "operations",
        "sensors", "sensor_readings", "nutrient_samples", "alert_rules", "alerts", "prescriptions", "audit_log",
    ]
    with io.BytesIO() as buffer:
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json_dumps({"module_version": MODULE_VERSION, "generated_utc": utc_now(), "tables": tables}))
            zf.writestr("field_operations.sqlite", db.export_database_bytes())
            for table in tables:
                try:
                    frame = db.frame(f"SELECT * FROM {table}")
                    zf.writestr(f"tables/{table}.csv", frame.to_csv(index=False))
                except Exception as error:
                    zf.writestr(f"errors/{table}.txt", str(error))
            if db.attachment_root.exists():
                for file in db.attachment_root.rglob("*"):
                    if file.is_file():
                        zf.write(file, f"attachments/{file.name}")
        return buffer.getvalue()


# ------------------------------ UI helpers ------------------------------

def _field_selector(db: FieldOperationsDatabase, key: str, include_all: bool = False) -> tuple[str | None, dict | None]:
    fields = db.fields()
    if fields.empty:
        st.info("Create a farm/research centre and mapped field first.")
        return None, None
    labels = {f"{r['farm_name']} · {r['name']} ({float(r['area_ha'] or 0):.2f} ha)": str(r["field_id"]) for _, r in fields.iterrows()}
    options = list(labels)
    if include_all:
        options = ["All fields"] + options
    active_id = str(st.session_state.get("field_ops_active_field_id") or "")
    default_label = next((label for label, value in labels.items() if value == active_id), None)
    default_index = options.index(default_label) if default_label in options else 0
    selected = st.selectbox("Field", options, index=default_index, key=key)
    if selected == "All fields":
        return None, None
    field_id = labels[selected]
    st.session_state.field_ops_active_field_id = field_id
    return field_id, db.field(field_id)


def _map_for_geometry(geometry: Mapping[str, Any] | None = None, zoom: int = 15, *, satellite_default: bool = False, measurement: bool = True) -> folium.Map:
    if geometry:
        lat, lon = geometry_centroid(geometry)
    else:
        lat, lon = st.session_state.get("agrolattice_active_country_map_centre", (19.4326, -99.1332))
    m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles=None, control_scale=True)
    folium.TileLayer("OpenStreetMap", name="Roads & places", overlay=False, control=True, show=not satellite_default).add_to(m)
    folium.TileLayer("CartoDB positron", name="Light map", overlay=False, control=True, show=False).add_to(m)
    folium.TileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        name="Satellite imagery", attr="Esri, Maxar, Earthstar Geographics, and the GIS User Community",
        overlay=False, control=True, show=satellite_default, max_zoom=20,
    ).add_to(m)
    if measurement:
        MeasureControl(
            position="topleft", primary_length_unit="meters", secondary_length_unit="kilometers",
            primary_area_unit="sqmeters", secondary_area_unit="hectares",
            active_color="#dc2626", completed_color="#2563eb",
        ).add_to(m)
    Fullscreen().add_to(m)
    folium.LayerControl(collapsed=False, position="topright").add_to(m)
    return m


def _metric_draw_options() -> dict[str, Any]:
    return {
        "polyline": {"metric": True, "feet": False, "showLength": True},
        "rectangle": {"metric": True, "feet": False, "showArea": True},
        "polygon": {"allowIntersection": False, "metric": True, "feet": False, "showArea": True, "showLength": True},
        "circle": False, "circlemarker": False, "marker": False,
    }


class _LiveDrawDistance(MacroElement):
    _template = Template(
        """
        {% macro script(this, kwargs) %}
        (function() {
          var map = {{ this._parent.get_name() }};
          var active = false, drawType = null, fixedPoints = [], rectangleStart = null;
          var box = L.control({position: 'bottomleft'});
          box.onAdd = function() {
            var div = L.DomUtil.create('div', 'leaflet-bar');
            div.style.background = 'rgba(255,255,255,0.96)';
            div.style.padding = '7px 10px';
            div.style.font = '600 12px/1.35 system-ui, sans-serif';
            div.style.color = '#111827';
            div.style.minWidth = '215px';
            div.style.display = 'none';
            this._container = div; return div;
          };
          box.addTo(map);
          function metres(value) {
            if (!isFinite(value)) return '—';
            return value >= 1000 ? (value / 1000).toFixed(3) + ' km' : value.toFixed(value < 100 ? 1 : 0) + ' m';
          }
          function refresh(group) {
            fixedPoints = [];
            if (group) group.eachLayer(function(layer) { if (layer.getLatLng) fixedPoints.push(layer.getLatLng()); });
          }
          function fixedLength() {
            var total = 0;
            for (var i = 1; i < fixedPoints.length; i++) total += map.distance(fixedPoints[i - 1], fixedPoints[i]);
            return total;
          }
          map.on(L.Draw.Event.DRAWSTART, function(e) {
            active = true; drawType = e.layerType; fixedPoints = []; rectangleStart = null;
            box._container.style.display = 'block';
            box._container.innerHTML = 'Click the first corner; distances are in metres';
          });
          map.on(L.Draw.Event.DRAWVERTEX, function(e) { refresh(e.layers); });
          map.on('mousedown', function(e) {
            if (active && drawType === 'rectangle' && rectangleStart === null) rectangleStart = e.latlng;
          });
          map.on('mousemove', function(e) {
            if (!active || !box._container) return;
            if (drawType === 'rectangle' && rectangleStart !== null) {
              var horizontal = L.latLng(rectangleStart.lat, e.latlng.lng);
              var vertical = L.latLng(e.latlng.lat, rectangleStart.lng);
              var width = map.distance(rectangleStart, horizontal);
              var height = map.distance(rectangleStart, vertical);
              var perimeter = 2 * (width + height);
              var area = width * height;
              var areaLabel = area >= 10000 ? (area / 10000).toFixed(3) + ' ha' : area.toFixed(area < 100 ? 1 : 0) + ' m²';
              box._container.innerHTML = '<strong>Width:</strong> ' + metres(width) + '<br><strong>Height:</strong> ' + metres(height) + '<br><strong>Provisional perimeter:</strong> ' + metres(perimeter) + '<br><strong>Provisional area:</strong> ' + areaLabel;
              return;
            }
            if (fixedPoints.length === 0) return;
            var edge = map.distance(fixedPoints[fixedPoints.length - 1], e.latlng);
            var openTotal = fixedLength() + edge;
            var label = '<strong>Current edge:</strong> ' + metres(edge) + '<br><strong>Drawn length:</strong> ' + metres(openTotal);
            if ((drawType === 'polygon' || drawType === 'rectangle') && fixedPoints.length > 1) {
              label += '<br><strong>Provisional perimeter:</strong> ' + metres(openTotal + map.distance(e.latlng, fixedPoints[0]));
            }
            box._container.innerHTML = label;
          });
          function stop() { active = false; drawType = null; fixedPoints = []; rectangleStart = null; if (box._container) box._container.style.display = 'none'; }
          map.on(L.Draw.Event.DRAWSTOP, stop);
          map.on(L.Draw.Event.CREATED, stop);
        })();
        {% endmacro %}
        """
    )
    def __init__(self) -> None:
        super().__init__(); self._name = "LiveDrawDistance"


def _add_live_draw_distance(map_object: folium.Map) -> folium.Map:
    _LiveDrawDistance().add_to(map_object)
    return map_object


def _farm_factor_colour(value: Any) -> str:
    palette = ["#2563eb", "#7c3aed", "#c2410c", "#15803d", "#be123c", "#0f766e", "#a16207", "#475569"]
    digest = hashlib.sha256(str(value).encode("utf-8")).hexdigest()
    return palette[int(digest[:8], 16) % len(palette)]


def _render_field_map(
    db: FieldOperationsDatabase,
    selected_field_id: str | None = None,
    observations: pd.DataFrame | None = None,
    sensors: pd.DataFrame | None = None,
    key: str = "field_map",
    *,
    farm_id: str | None = None,
    pollination_db=None,
    trial_statuses: Sequence[str] = ("Active",),
    show_treatment_units: bool = True,
    map_height: int = 650,
) -> str | None:
    """Render an organisation/field portfolio map and return a clicked field ID."""
    fields = db.fields(farm_id=farm_id) if farm_id else db.fields()
    organisation = db.farm(farm_id) if farm_id else None
    organisation_geometry = (organisation or {}).get("geometry")
    if fields.empty and not organisation_geometry:
        st.info("No organisation boundary or mapped fields are available yet.")
        return None

    field_ids = set(fields.get("field_id", pd.Series(dtype=str)).astype(str))
    selected_field = db.field(selected_field_id) if selected_field_id and str(selected_field_id) in field_ids else None
    initial_geometry = (
        selected_field.get("geometry") if selected_field else organisation_geometry
        or (json_loads(fields.iloc[0]["geometry_json"]) if not fields.empty else None)
    )
    map_obj = _map_for_geometry(initial_geometry, zoom=17 if selected_field else 15, satellite_default=True)

    all_geometries: list[Mapping[str, Any]] = []
    if organisation_geometry:
        all_geometries.append(organisation_geometry)
        organisation_tooltip = (
            f"{organisation.get('entity_type') or 'Farm'} · {organisation.get('name')} · "
            f"{float(organisation.get('area_ha') or 0):,.3f} ha"
        )
        folium.GeoJson(
            organisation_geometry,
            name=f"{organisation.get('entity_type') or 'Farm'} boundary · {organisation.get('name')}",
            style_function=lambda _: {
                "color": "#047857", "weight": 5, "dashArray": "10 6",
                "fillColor": "#34d399", "fillOpacity": 0.035,
            },
            tooltip=organisation_tooltip,
            popup=organisation_tooltip,
        ).add_to(map_obj)

    field_tooltip_to_id: dict[str, str] = {}
    organisation_shape = shape(organisation_geometry) if organisation_geometry else None
    for row in fields.to_dict("records"):
        geom = json_loads(row["geometry_json"])
        if not geom:
            continue
        all_geometries.append(geom)
        active = str(row["field_id"]) == str(selected_field_id)
        outside_parent = False
        if organisation_shape is not None:
            try:
                outside_parent = not organisation_shape.buffer(1e-10).covers(shape(geom))
            except Exception:
                outside_parent = False
        colour = "#dc2626" if outside_parent else "#1d4ed8"
        fill = "#f87171" if outside_parent else "#60a5fa"
        tooltip = f"Field · {row['name']}"
        field_tooltip_to_id[tooltip] = str(row["field_id"])
        popup = "<br>".join([
            f"<b>{html.escape(str(row.get('farm_name') or 'Organisation'))}</b>",
            f"Field: {html.escape(str(row.get('name') or ''))}",
            f"Code: {html.escape(str(row.get('code') or '—'))}",
            f"Area: {float(row.get('area_ha') or 0):,.3f} ha",
            f"Crop: {html.escape(str(row.get('crop') or '—'))}",
            "⚠ Outside saved organisation boundary" if outside_parent else "Inside saved organisation boundary" if organisation_geometry else "No organisation boundary saved",
        ])
        folium.GeoJson(
            geometry_feature(geom, {"name": row["name"], "area_ha": row["area_ha"]}),
            name=f"Field · {row['name']}",
            style_function=lambda _feature, active=active, c=colour, f=fill: {
                "color": c, "weight": 5 if active else 3,
                "fillColor": f, "fillOpacity": 0.22 if active else 0.09,
            },
            highlight_function=lambda _feature: {"weight": 6, "fillOpacity": 0.24},
            tooltip=tooltip,
            popup=popup,
        ).add_to(map_obj)
        folium.Marker(
            [float(row["centroid_lat"]), float(row["centroid_lon"])],
            tooltip=tooltip,
            popup=popup,
            icon=folium.DivIcon(
                html=(
                    '<div style="white-space:nowrap;background:rgba(255,255,255,.93);border:1px solid #64748b;'
                    'border-radius:5px;padding:2px 5px;font:600 11px system-ui;color:#0f172a;">'
                    + html.escape(str(row["name"])) + '</div>'
                )
            ),
        ).add_to(map_obj)

    experiment_count = 0
    treatment_unit_count = 0
    if pollination_db is not None and field_ids:
        try:
            trials = pollination_db.list_trials()
            if not trials.empty:
                statuses = {str(value) for value in trial_statuses}
                trials = trials.loc[trials["Source field ID"].astype(str).isin(field_ids)]
                if statuses and "Status" in trials:
                    trials = trials.loc[trials["Status"].astype(str).isin(statuses)]
                for _, trial_row in trials.iterrows():
                    trial = pollination_db.get_trial(str(trial_row["Trial ID"]))
                    trial_geometry = trial.get("field_geometry")
                    female_lines = trial.get("female_parent_levels") or [trial.get("female_parent")]
                    male_lines = trial.get("male_parent_levels") or [trial.get("male_parent")]
                    parent_label = f"{len(female_lines)} female line(s) · {len(male_lines)} male line(s)"
                    if trial_geometry:
                        experiment_count += 1
                        folium.GeoJson(
                            trial_geometry,
                            name=f"Experiment · {trial.get('name')}",
                            style_function=lambda _: {
                                "color": "#c2410c", "weight": 4, "dashArray": "8 5",
                                "fillColor": "#fb923c", "fillOpacity": 0.04,
                            },
                            tooltip=f"{trial.get('name')} · {trial.get('status','Active')} · {parent_label}",
                        ).add_to(map_obj)
                    units = pollination_db.list_plots(str(trial_row["Trial ID"]))
                    if show_treatment_units and not units.empty:
                        group_col = "Experiment plot" if "Experiment plot" in units else "Block"
                        for parent_name, group in units.groupby(group_col, sort=False):
                            try:
                                parent_geometry = mapping(unary_union([
                                    shape(item) for item in group["Geometry"].tolist() if isinstance(item, Mapping)
                                ]).convex_hull)
                                folium.GeoJson(
                                    parent_geometry,
                                    name=f"Experiment plot · {trial.get('name')} · {parent_name}",
                                    style_function=lambda _: {
                                        "color": "#111827", "weight": 3,
                                        "dashArray": "5 4", "fillOpacity": 0.01,
                                    },
                                    tooltip=(
                                        f"{trial.get('name')} · experiment plot {parent_name} · "
                                        f"{len(group)} treatment units"
                                    ),
                                ).add_to(map_obj)
                            except Exception:
                                pass
                        for _, unit in units.iterrows():
                            geometry = unit.get("Geometry")
                            if not isinstance(geometry, Mapping):
                                continue
                            treatment_unit_count += 1
                            colour_value = (
                                unit.get("Parent combination") or unit.get("Variety / genotype")
                                or unit.get("Treatment") or unit.get("Male offset (days)")
                            )
                            colour = _farm_factor_colour(colour_value)
                            tooltip_lines = [
                                f"<b>Trial:</b> {trial.get('name')}",
                                f"<b>Experiment plot:</b> {unit.get('Experiment plot') or unit.get('Block')}",
                                f"<b>Treatment unit:</b> {unit.get('Treatment unit') or unit.get('Plot')}",
                                f"<b>Female parent:</b> {unit.get('Female parent') or '—'}",
                                f"<b>Male parent:</b> {unit.get('Male parent') or '—'}",
                                f"<b>Parent combination:</b> {unit.get('Parent combination') or unit.get('Variety / genotype') or '—'}",
                                f"<b>Density:</b> {unit.get('Sowing density (plants/ha)') or '—'}",
                                f"<b>Sowing date:</b> {unit.get('Sowing date') or unit.get('Female sowing') or '—'}",
                                f"<b>Male–female difference:</b> {unit.get('Male–female sowing difference (days)') if pd.notna(unit.get('Male–female sowing difference (days)')) else unit.get('Male offset (days)')} d",
                            ]
                            tooltip_html = "<br>".join(tooltip_lines)
                            folium.GeoJson(
                                geometry,
                                name=f"Treatment unit · {trial.get('name')} · {unit.get('Treatment unit') or unit.get('Plot')}",
                                style_function=lambda _, c=colour: {
                                    "color": c, "weight": 2,
                                    "fillColor": c, "fillOpacity": 0.38,
                                },
                                tooltip=tooltip_html,
                                popup=tooltip_html,
                            ).add_to(map_obj)
        except Exception as error:
            st.warning(f"Experiment overlays could not be loaded: {type(error).__name__}: {error}")

    if isinstance(observations, pd.DataFrame) and not observations.empty:
        for row in observations.dropna(subset=["latitude", "longitude"]).to_dict("records"):
            folium.CircleMarker(
                [float(row["latitude"]), float(row["longitude"])], radius=4 + int(row.get("severity") or 1),
                popup=f"{row.get('category','Observation')}<br>{row.get('notes','')}", tooltip="Scouting observation",
                fill=True,
            ).add_to(map_obj)
    if isinstance(sensors, pd.DataFrame) and not sensors.empty:
        for row in sensors.dropna(subset=["latitude", "longitude"]).to_dict("records"):
            folium.Marker(
                [float(row["latitude"]), float(row["longitude"])],
                popup=f"{row.get('name')}<br>{row.get('sensor_type')}<br>{row.get('depth_cm') or ''} cm",
                tooltip="Sensor", icon=folium.Icon(icon="signal", prefix="fa"),
            ).add_to(map_obj)

    target_geometries = []
    if selected_field and selected_field.get("geometry"):
        target_geometries = [selected_field["geometry"]]
    elif all_geometries:
        target_geometries = all_geometries
    try:
        minx, miny, maxx, maxy = unary_union([shape(item) for item in target_geometries]).bounds
        map_obj.fit_bounds([[miny, minx], [maxy, maxx]], padding=(35, 35))
    except Exception:
        pass

    st.caption(
        f"Map overlay: {len(fields)} mapped fields · {experiment_count} selected-status maize experiments · "
        f"{treatment_unit_count} treatment units. Click a field polygon or its label to focus it."
    )
    result = st_folium(
        map_obj, use_container_width=True, height=int(map_height), key=key,
        returned_objects=["last_object_clicked_tooltip"],
    )
    clicked = (result or {}).get("last_object_clicked_tooltip")
    return field_tooltip_to_id.get(str(clicked))


def _download_dataframe(label: str, frame: pd.DataFrame, filename: str, key: str) -> None:
    st.download_button(label, frame.to_csv(index=False).encode("utf-8"), file_name=filename, mime="text/csv", key=key, width="stretch")


# ------------------------------ page renderers ------------------------------

def render_farm_portfolio_page(db: FieldOperationsDatabase, context: Mapping[str, Any]) -> None:
    summary = db.portfolio_summary()
    cards = st.columns(7)
    cards[0].metric("Organisations", summary["farms"])
    cards[1].metric("Fields", summary["fields"])
    cards[2].metric("Active area", f"{summary['area_ha']:,.1f} ha")
    cards[3].metric("Open tasks", summary["open_tasks"])
    cards[4].metric("Open alerts", summary["open_alerts"])
    cards[5].metric("Observations", summary["observations"])
    cards[6].metric("Active sensors", summary["sensors"])

    portfolio_tab, field_tab, seasons_tab, team_tab, map_tab = st.tabs([
        "Farms & research centres", "Fields", "Crop history", "Team & access", "Portfolio map",
    ])

    with portfolio_tab:
        farms = db.farms()
        st.markdown("### Select and inspect a farm or agricultural research centre")
        if farms.empty:
            st.info("Create the first farm or agricultural research centre below.")
        else:
            organisation_labels = {
                f"{row.get('entity_type') or 'Farm'} · {row['name']} · {row.get('country') or ''}": str(row["farm_id"])
                for _, row in farms.iterrows()
            }
            selected_label = st.selectbox(
                "Farm / agricultural research centre", list(organisation_labels),
                key="ops_selected_organisation",
            )
            selected_farm_id = organisation_labels[selected_label]
            selected_farm = db.farm(selected_farm_id) or {}
            selected_fields = db.fields(selected_farm_id)
            organisation_cards = st.columns(5)
            organisation_cards[0].metric("Type", selected_farm.get("entity_type") or "Farm")
            organisation_cards[1].metric("Mapped fields", len(selected_fields))
            organisation_cards[2].metric(
                "Organisation boundary", f"{float(selected_farm.get('area_ha') or 0):,.3f} ha"
                if selected_farm.get("geometry") else "Not mapped",
            )
            organisation_cards[3].metric(
                "Field area total", f"{float(pd.to_numeric(selected_fields.get('area_ha'), errors='coerce').sum() if not selected_fields.empty else 0):,.3f} ha",
            )
            organisation_cards[4].metric("Manager / PI", selected_farm.get("manager") or "—")
            st.caption(
                "The green dashed outline is the complete farm/research-centre boundary. Blue polygons are its fields. "
                "Orange and coloured overlays are selected-status maize experiments and treatment units."
            )
            focus_options = ["All fields"]
            focus_lookup: dict[str, str] = {}
            if not selected_fields.empty:
                for _, row in selected_fields.iterrows():
                    label = f"{row['name']} · {float(row.get('area_ha') or 0):,.3f} ha"
                    focus_options.append(label)
                    focus_lookup[label] = str(row["field_id"])
            active_field_id = str(st.session_state.get("field_ops_active_field_id") or "")
            focus_index = next(
                (idx for idx, label in enumerate(focus_options) if focus_lookup.get(label) == active_field_id), 0
            )
            focus_cols = st.columns([2, 2, 1])
            focus_widget_key = f"ops_org_focus_field_{selected_farm_id}"
            pending_focus_key = f"ops_org_pending_focus_{selected_farm_id}"
            pending_focus_id = st.session_state.pop(pending_focus_key, None)
            if pending_focus_id:
                pending_label = next((label for label, field_id in focus_lookup.items() if field_id == str(pending_focus_id)), "All fields")
                st.session_state[focus_widget_key] = pending_label
            focus_label = focus_cols[0].selectbox(
                "Focus the map on a saved field", focus_options, index=focus_index,
                key=focus_widget_key,
            )
            trial_statuses = focus_cols[1].multiselect(
                "Experiment statuses", ["Planned", "Active", "Completed", "Archived"],
                default=["Active"], key=f"ops_org_trial_statuses_{selected_farm_id}",
            )
            show_units = focus_cols[2].checkbox(
                "Treatment units", value=True, key=f"ops_org_show_units_{selected_farm_id}",
            )
            focused_field_id = focus_lookup.get(focus_label)
            clicked_field_id = _render_field_map(
                db, focused_field_id, key=f"ops_organisation_map_{selected_farm_id}",
                farm_id=selected_farm_id, pollination_db=context.get("pollination_db"),
                trial_statuses=trial_statuses, show_treatment_units=show_units, map_height=610,
            )
            if clicked_field_id and clicked_field_id != focused_field_id:
                st.session_state.field_ops_active_field_id = clicked_field_id
                st.session_state[pending_focus_key] = clicked_field_id
                st.rerun()
            if focused_field_id:
                st.session_state.field_ops_active_field_id = focused_field_id
            if not selected_fields.empty:
                field_display = selected_fields[[
                    column for column in [
                        "name", "code", "area_ha", "crop", "variety", "season_year",
                        "irrigation_system", "soil_type", "status", "centroid_lat", "centroid_lon",
                    ] if column in selected_fields.columns
                ]].rename(columns={
                    "name": "Field", "code": "Code", "area_ha": "Area (ha)", "crop": "Crop",
                    "variety": "Variety / genotype", "season_year": "Season", "irrigation_system": "Irrigation",
                    "soil_type": "Soil", "status": "Status", "centroid_lat": "Latitude", "centroid_lon": "Longitude",
                })
                st.dataframe(field_display, hide_index=True, width="stretch")

        with st.expander("Create a farm or agricultural research centre", expanded=farms.empty):
            create_type = st.selectbox(
                "Organisation type", ORGANISATION_TYPES, key="ops_create_organisation_type",
            )
            create_boundary_source = st.radio(
                "Complete organisation boundary",
                ["Draw on satellite map", "Upload GeoJSON", "Create without a boundary"],
                horizontal=True, key="ops_create_organisation_boundary_source",
            )
            create_geometry = None
            if create_boundary_source == "Draw on satellite map":
                st.caption("Draw the outer boundary of the complete farm or research centre, not an individual field.")
                centre = st.session_state.get("agrolattice_active_country_map_centre", (19.45, -98.90))
                create_geometry = render_boundary_editor(
                    key="ops_create_organisation_boundary_map", center=centre,
                    zoom=14, height=500, satellite_default=True,
                )
            elif create_boundary_source == "Upload GeoJSON":
                create_upload = st.file_uploader(
                    "Organisation-boundary GeoJSON", type=["geojson", "json"],
                    key="ops_create_organisation_geojson",
                )
                if create_upload:
                    try:
                        create_geometry = normalise_geojson_geometry(json.loads(create_upload.getvalue()))
                    except Exception as error:
                        st.error(str(error))
            if create_geometry:
                st.success(f"Complete organisation boundary captured: {geometry_area_hectares(create_geometry):,.3f} ha")
            create_cols = st.columns(4)
            create_name = create_cols[0].text_input("Name", key="ops_create_organisation_name")
            create_country = create_cols[1].text_input(
                "Country", value=str(context.get("selected_country") or "Mexico"),
                key="ops_create_organisation_country",
            )
            create_admin = create_cols[2].text_input(
                "State / administrative area", key="ops_create_organisation_admin",
            )
            create_manager = create_cols[3].text_input(
                "Manager / principal investigator", key="ops_create_organisation_manager",
            )
            create_notes = st.text_area("Notes", key="ops_create_organisation_notes")
            if st.button(
                f"Create {create_type.lower()}", type="primary", width="stretch",
                key="ops_create_organisation_button",
            ):
                try:
                    created_id = db.create_farm(
                        create_name, create_country, create_admin, create_manager, create_notes,
                        entity_type=create_type, geometry=create_geometry,
                    )
                    st.session_state.field_ops_active_farm_id = created_id
                    st.success(f"{create_type} created.")
                    st.rerun()
                except Exception as error:
                    st.error(str(error))

        farms = db.farms()
        if not farms.empty:
            with st.expander("Edit an existing farm or research centre", expanded=False):
                edit_labels = {
                    f"{row.get('entity_type') or 'Farm'} · {row['name']} · {row.get('country') or ''}": str(row["farm_id"])
                    for _, row in farms.iterrows()
                }
                edit_label = st.selectbox("Organisation to edit", list(edit_labels), key="ops_edit_farm_select")
                edit_id = edit_labels[edit_label]
                edit_farm = db.farm(edit_id) or {}
                edit_fields = db.fields(edit_id)
                edit_type = st.selectbox(
                    "Organisation type", ORGANISATION_TYPES,
                    index=ORGANISATION_TYPES.index(edit_farm.get("entity_type")) if edit_farm.get("entity_type") in ORGANISATION_TYPES else 0,
                    key=f"ops_edit_farm_type_{edit_id}",
                )
                boundary_mode = st.radio(
                    "Complete organisation boundary",
                    ["Keep current boundary", "Redraw on satellite map", "Upload replacement GeoJSON", "Use union of mapped fields", "Remove saved boundary"],
                    horizontal=True, key=f"ops_edit_farm_boundary_mode_{edit_id}",
                )
                replacement_geometry = None
                boundary_action = "keep"
                if boundary_mode == "Redraw on satellite map":
                    boundary_action = "replace"
                    centre = geometry_centroid(edit_farm["geometry"]) if edit_farm.get("geometry") else st.session_state.get("agrolattice_active_country_map_centre", (19.45, -98.90))
                    references = []
                    for _, field_row in edit_fields.iterrows():
                        field_geom = json_loads(field_row.get("geometry_json"))
                        if field_geom:
                            references.append({"geometry": field_geom, "label": f"Field · {field_row.get('name')}", "color": "#2563eb", "weight": 2})
                    replacement_geometry = render_boundary_editor(
                        key=f"ops_edit_farm_boundary_map_{edit_id}", center=centre,
                        initial_geometry=edit_farm.get("geometry"), reference_geometries=references,
                        zoom=15, height=520, satellite_default=True,
                    )
                elif boundary_mode == "Upload replacement GeoJSON":
                    boundary_action = "replace"
                    edit_upload = st.file_uploader(
                        "Replacement organisation-boundary GeoJSON", type=["geojson", "json"],
                        key=f"ops_edit_farm_geojson_{edit_id}",
                    )
                    if edit_upload:
                        try:
                            replacement_geometry = normalise_geojson_geometry(json.loads(edit_upload.getvalue()))
                        except Exception as error:
                            st.error(str(error))
                elif boundary_mode == "Use union of mapped fields":
                    boundary_action = "replace"
                    geometries = [
                        json_loads(value) for value in edit_fields.get("geometry_json", pd.Series(dtype=str)).tolist()
                        if json_loads(value)
                    ]
                    if geometries:
                        replacement_geometry = mapping(unary_union([shape(item) for item in geometries]).convex_hull)
                        st.info(
                            "The proposed boundary is the convex hull of all mapped fields. Review it carefully; "
                            "roads, buildings or unused land between fields may be included."
                        )
                        preview_map = _map_for_geometry(replacement_geometry, zoom=15, satellite_default=True)
                        folium.GeoJson(
                            replacement_geometry, name="Proposed organisation boundary",
                            style_function=lambda _: {"color": "#047857", "weight": 5, "fillOpacity": 0.04},
                        ).add_to(preview_map)
                        st_folium(
                            preview_map, use_container_width=True, height=440,
                            key=f"ops_edit_farm_union_preview_{edit_id}", returned_objects=[],
                        )
                    else:
                        st.warning("This organisation has no mapped fields from which to derive a boundary.")
                elif boundary_mode == "Remove saved boundary":
                    boundary_action = "remove"
                if replacement_geometry:
                    st.success(f"Replacement boundary area: {geometry_area_hectares(replacement_geometry):,.3f} ha")
                edit_cols = st.columns(4)
                edit_name = edit_cols[0].text_input(
                    "Name", value=str(edit_farm.get("name") or ""), key=f"ops_edit_farm_name_{edit_id}",
                )
                edit_country = edit_cols[1].text_input(
                    "Country", value=str(edit_farm.get("country") or context.get("selected_country") or "Mexico"),
                    key=f"ops_edit_farm_country_{edit_id}",
                )
                edit_admin = edit_cols[2].text_input(
                    "State / administrative area", value=str(edit_farm.get("admin_area") or ""),
                    key=f"ops_edit_farm_admin_{edit_id}",
                )
                edit_manager = edit_cols[3].text_input(
                    "Manager / principal investigator", value=str(edit_farm.get("manager") or ""),
                    key=f"ops_edit_farm_manager_{edit_id}",
                )
                edit_notes = st.text_area(
                    "Notes", value=str(edit_farm.get("notes") or ""), key=f"ops_edit_farm_notes_{edit_id}",
                )
                if st.button(
                    "Save organisation changes", type="primary", width="stretch",
                    key=f"ops_edit_farm_save_{edit_id}",
                ):
                    try:
                        db.update_farm(
                            edit_id, name=edit_name, country=edit_country, admin_area=edit_admin,
                            manager=edit_manager, notes=edit_notes, entity_type=edit_type,
                            geometry=replacement_geometry, boundary_action=boundary_action,
                            user_name=edit_manager,
                        )
                        st.success("Organisation updated. Existing field IDs and records were preserved.")
                        st.rerun()
                    except Exception as error:
                        st.error(str(error))

            with st.expander("Delete a farm or research centre", expanded=False):
                st.warning(
                    "Deleting an organisation permanently deletes every field inside it and all associated tasks, "
                    "observations, operations, sensors, alerts, prescriptions and crop-history records."
                )
                delete_labels = {
                    f"{row.get('entity_type') or 'Farm'} · {row['name']} · {row.get('country') or ''}": str(row["farm_id"])
                    for _, row in farms.iterrows()
                }
                selected_delete_label = st.selectbox(
                    "Organisation to delete", list(delete_labels), key="ops_delete_farm_select",
                )
                selected_delete_id = delete_labels[selected_delete_label]
                selected_delete_row = farms.loc[farms["farm_id"].astype(str).eq(selected_delete_id)].iloc[0]
                dependency_counts = db.farm_dependency_counts(selected_delete_id)
                external_counts = db.external_farm_dependency_counts(selected_delete_id)
                st.dataframe(
                    pd.DataFrame(
                        [{"Record type": key, "Count": value, "Effect": "Will be deleted"} for key, value in dependency_counts.items()]
                        + [{"Record type": key, "Count": value, "Effect": "Blocks deletion if > 0"} for key, value in external_counts.items()]
                    ),
                    hide_index=True, width="stretch",
                )
                external_block = any(external_counts.values())
                if external_block:
                    st.warning("Deletion is blocked until linked maize trials and Persistent Twins are removed/reassigned. Archiving is safer for research records.")
                typed_name = st.text_input("Type the exact name to confirm", key="ops_delete_farm_name")
                confirm_delete = st.checkbox(
                    "I understand that this deletion cannot be undone", key="ops_delete_farm_confirm",
                )
                if st.button(
                    "Delete organisation and all contained fields", type="primary",
                    disabled=not (confirm_delete and typed_name == str(selected_delete_row["name"])) or external_block,
                    key="ops_delete_farm_button", width="stretch",
                ):
                    try:
                        deleted = db.delete_farm(selected_delete_id)
                    except Exception as error:
                        st.error(str(error))
                        st.stop()
                    active_field = st.session_state.get("field_ops_active_field_id")
                    if active_field and active_field not in db.fields().get("field_id", pd.Series(dtype=str)).astype(str).tolist():
                        st.session_state.pop("field_ops_active_field_id", None)
                    st.success(f"Organisation deleted. {sum(deleted.values()):,} dependent records were removed.")
                    st.rerun()

    with field_tab:
        farms = db.farms()
        if farms.empty:
            st.info("Create a farm or agricultural research centre first.")
        else:
            organisation_labels = {
                f"{row.get('entity_type') or 'Farm'} · {row['name']}": str(row["farm_id"])
                for _, row in farms.iterrows()
            }
            selected_org_label = st.selectbox(
                "Assign/view fields for", list(organisation_labels), key="ops_fields_selected_organisation",
            )
            selected_org_id = organisation_labels[selected_org_label]
            fields = db.fields(selected_org_id)
            if not fields.empty:
                display = fields.drop(columns=["geometry_json"], errors="ignore")
                st.dataframe(display, hide_index=True, width="stretch")
            source = st.radio(
                "Boundary source", ["Draw on map", "Upload GeoJSON", "Current project", "Satellite crop monitoring", "Maize flowering trial"],
                horizontal=True, key="ops_field_geometry_source",
            )
            geometry = None
            if source == "Draw on map":
                parent = db.farm(selected_org_id) or {}
                st.caption(
                    "Draw one field inside the green farm/research-centre boundary. Use the layer control to switch "
                    "between satellite imagery and roads."
                )
                centre = geometry_centroid(parent["geometry"]) if parent.get("geometry") else st.session_state.get("agrolattice_active_country_map_centre", (19.45, -98.90))
                references = [{"geometry": parent["geometry"], "label": "Complete organisation boundary", "color": "#047857", "weight": 5}] if parent.get("geometry") else []
                geometry = render_boundary_editor(
                    key="ops_field_draw_map", center=centre, reference_geometries=references,
                    zoom=16, height=520, satellite_default=True,
                )
                if geometry:
                    st.success(f"Field boundary captured: {geometry_area_hectares(geometry):.3f} ha")
                    if parent.get("geometry"):
                        try:
                            if not shape(parent["geometry"]).buffer(1e-10).covers(shape(geometry)):
                                st.warning("Part of this field lies outside the saved organisation boundary. You may still save it, but review both boundaries.")
                        except Exception:
                            pass
            elif source == "Upload GeoJSON":
                upload = st.file_uploader(
                    "GeoJSON containing one Polygon or MultiPolygon", type=["geojson", "json"], key="ops_field_geojson_upload",
                )
                if upload:
                    try:
                        geometry = normalise_geojson_geometry(json.loads(upload.getvalue()))
                        st.success(f"Boundary loaded: {geometry_area_hectares(geometry):.3f} ha")
                    except Exception as error:
                        st.error(str(error))
            else:
                geometry = _source_geometry(context, source)
                if geometry:
                    st.success(f"Boundary available: {geometry_area_hectares(geometry):.3f} ha")
                else:
                    st.warning(f"No geometry is currently available from {source}.")
            with st.form("ops_create_field_form"):
                cols = st.columns(4)
                field_name = cols[0].text_input("Field name")
                field_code = cols[1].text_input("Field code")
                season_year = int(cols[2].number_input("Season year", 1900, 2200, date.today().year))
                status = cols[3].selectbox("Field status", ["Active", "Planned", "Fallow", "Archived"])
                cols2 = st.columns(4)
                crop = cols2[0].text_input("Current crop")
                variety = cols2[1].text_input("Variety / genotype")
                irrigation = cols2[2].selectbox(
                    "Irrigation system", ["Unknown", "Rainfed", "Drip", "Sprinkler", "Pivot", "Furrow", "Sensor-triggered automatic", "Other"],
                )
                soil = cols2[3].text_input("Soil type / series")
                notes = st.text_area("Field notes")
                create = st.form_submit_button("Create mapped field", type="primary", width="stretch")
            if create:
                if not field_name.strip():
                    st.error("Field name is required.")
                elif not geometry:
                    st.error("Draw, upload or select a valid field boundary first.")
                else:
                    field_id = db.create_field(
                        selected_org_id, field_name, geometry, code=field_code, crop=crop,
                        variety=variety, season_year=season_year, irrigation_system=irrigation,
                        soil_type=soil, status=status, notes=notes,
                    )
                    st.session_state.field_ops_active_field_id = field_id
                    st.success("Field created and activated.")
                    st.rerun()

            all_fields = db.fields()
            if not all_fields.empty:
                with st.expander("Edit an existing mapped field", expanded=False):
                    edit_field_labels = {f"{row['farm_name']} · {row['name']}": str(row["field_id"]) for _, row in all_fields.iterrows()}
                    edit_field_label = st.selectbox("Field to edit", list(edit_field_labels), key="ops_edit_field_select")
                    edit_field_id = edit_field_labels[edit_field_label]
                    current_field = db.field(edit_field_id) or {}
                    current_geometry = current_field.get("geometry")
                    info_cols = st.columns(4)
                    info_cols[0].metric("Current area", f"{float(current_field.get('area_ha') or 0):,.3f} ha")
                    info_cols[1].metric("Centroid latitude", f"{float(current_field.get('centroid_lat') or 0):.5f}")
                    info_cols[2].metric("Centroid longitude", f"{float(current_field.get('centroid_lon') or 0):.5f}")
                    info_cols[3].metric("Dependent records", sum(db.field_dependency_counts(edit_field_id).values()))
                    st.caption("Editing preserves the field ID and all linked tasks, observations, sensors, operations, crop history, alerts, prescriptions and Twin references.")

                    boundary_mode = st.radio(
                        "Boundary update",
                        ["Keep existing boundary", "Redraw on map", "Upload replacement GeoJSON", "Use current project", "Use Satellite crop monitoring", "Use maize flowering trial"],
                        horizontal=True, key=f"ops_edit_field_boundary_mode_{edit_field_id}",
                    )
                    replacement_geometry = None
                    if boundary_mode == "Redraw on map":
                        parent = db.farm(str(current_field.get("farm_id"))) if current_field.get("farm_id") else None
                        centre = geometry_centroid(current_geometry) if current_geometry else st.session_state.get("agrolattice_active_country_map_centre", (19.45, -98.90))
                        references = [{"geometry": parent["geometry"], "label": "Complete organisation boundary", "color": "#047857", "weight": 5}] if parent and parent.get("geometry") else []
                        replacement_geometry = render_boundary_editor(
                            key=f"ops_edit_field_draw_{edit_field_id}", center=centre,
                            initial_geometry=current_geometry, reference_geometries=references,
                            zoom=17, height=520, satellite_default=True,
                        )
                    elif boundary_mode == "Upload replacement GeoJSON":
                        edit_upload = st.file_uploader("Replacement GeoJSON", type=["geojson", "json"], key=f"ops_edit_field_upload_{edit_field_id}")
                        if edit_upload:
                            try:
                                replacement_geometry = normalise_geojson_geometry(json.loads(edit_upload.getvalue()))
                            except Exception as error:
                                st.error(str(error))
                    elif boundary_mode == "Use current project":
                        replacement_geometry = _source_geometry(context, "Current project")
                    elif boundary_mode == "Use Satellite crop monitoring":
                        replacement_geometry = _source_geometry(context, "Satellite crop monitoring")
                    elif boundary_mode == "Use maize flowering trial":
                        replacement_geometry = _source_geometry(context, "Maize flowering trial")
                    if replacement_geometry:
                        st.success(f"Replacement boundary ready: {geometry_area_hectares(replacement_geometry):.3f} ha")

                    all_farms = db.farms()
                    edit_farm_labels = {
                        f"{row.get('entity_type') or 'Farm'} · {row['name']} · {row.get('country') or ''}": str(row["farm_id"])
                        for _, row in all_farms.iterrows()
                    }
                    farm_names = list(edit_farm_labels)
                    current_farm_index = next((index for index, label in enumerate(farm_names) if edit_farm_labels[label] == str(current_field.get("farm_id"))), 0)
                    edit_cols = st.columns(4)
                    edit_farm_name = edit_cols[0].selectbox("Organisation", farm_names, index=current_farm_index, key=f"ops_edit_field_farm_{edit_field_id}")
                    edit_field_name = edit_cols[1].text_input("Field name", value=str(current_field.get("name") or ""), key=f"ops_edit_field_name_{edit_field_id}")
                    edit_field_code = edit_cols[2].text_input("Field code", value=str(current_field.get("code") or ""), key=f"ops_edit_field_code_{edit_field_id}")
                    edit_season = int(edit_cols[3].number_input("Season year", 1900, 2200, int(current_field.get("season_year") or date.today().year), key=f"ops_edit_field_season_{edit_field_id}"))
                    edit_cols2 = st.columns(4)
                    edit_crop = edit_cols2[0].text_input("Current crop", value=str(current_field.get("crop") or ""), key=f"ops_edit_field_crop_{edit_field_id}")
                    edit_variety = edit_cols2[1].text_input("Variety / genotype", value=str(current_field.get("variety") or ""), key=f"ops_edit_field_variety_{edit_field_id}")
                    irrigation_options = ["Unknown", "Rainfed", "Drip", "Sprinkler", "Pivot", "Furrow", "Sensor-triggered automatic", "Other"]
                    current_irrigation = str(current_field.get("irrigation_system") or "Unknown")
                    edit_irrigation = edit_cols2[2].selectbox("Irrigation system", irrigation_options, index=irrigation_options.index(current_irrigation) if current_irrigation in irrigation_options else 0, key=f"ops_edit_field_irrigation_{edit_field_id}")
                    edit_soil = edit_cols2[3].text_input("Soil type / series", value=str(current_field.get("soil_type") or ""), key=f"ops_edit_field_soil_{edit_field_id}")
                    edit_status = st.selectbox("Field status", ["Active", "Planned", "Fallow", "Archived"], index=["Active", "Planned", "Fallow", "Archived"].index(str(current_field.get("status") or "Active")) if str(current_field.get("status") or "Active") in ["Active", "Planned", "Fallow", "Archived"] else 0, key=f"ops_edit_field_status_{edit_field_id}")
                    edit_field_notes = st.text_area("Field notes", value=str(current_field.get("notes") or ""), key=f"ops_edit_field_notes_{edit_field_id}")
                    if st.button("Save field changes", type="primary", width="stretch", key=f"ops_edit_field_save_{edit_field_id}"):
                        if boundary_mode != "Keep existing boundary" and not replacement_geometry:
                            st.error("Select or draw a valid replacement boundary, or choose Keep existing boundary.")
                        else:
                            try:
                                db.update_field(
                                    edit_field_id, farm_id=edit_farm_labels[edit_farm_name], name=edit_field_name,
                                    geometry=replacement_geometry if boundary_mode != "Keep existing boundary" else None,
                                    code=edit_field_code, crop=edit_crop, variety=edit_variety, season_year=edit_season,
                                    irrigation_system=edit_irrigation, soil_type=edit_soil, status=edit_status,
                                    notes=edit_field_notes,
                                )
                                st.session_state.field_ops_active_field_id = edit_field_id
                                st.success("Field updated. Its identifier and all dependent records were preserved.")
                                st.rerun()
                            except Exception as error:
                                st.error(str(error))

                with st.expander("Delete a mapped field", expanded=False):
                    st.warning("Deleting a field permanently removes its crop history, tasks, observations, operations, sensors and readings, nutrient samples, alerts, prescriptions and access assignments.")
                    delete_labels = {f"{row['farm_name']} · {row['name']}": str(row["field_id"]) for _, row in all_fields.iterrows()}
                    delete_field_label = st.selectbox("Field to delete", list(delete_labels), key="ops_delete_field_select")
                    delete_field_id = delete_labels[delete_field_label]
                    selected_field = all_fields.loc[all_fields["field_id"].astype(str).eq(delete_field_id)].iloc[0]
                    field_counts = db.field_dependency_counts(delete_field_id)
                    external_counts = db.external_field_dependency_counts(delete_field_id)
                    st.dataframe(
                        pd.DataFrame(
                            [{"Record type": key, "Count": value, "Effect": "Will be deleted"} for key, value in field_counts.items()]
                            + [{"Record type": key, "Count": value, "Effect": "Blocks deletion if > 0"} for key, value in external_counts.items()]
                        ),
                        hide_index=True, width="stretch",
                    )
                    external_block = any(external_counts.values())
                    if external_block:
                        st.warning("Deletion is blocked until linked maize trials and Persistent Twins are removed/reassigned. Use Archived status when you need to retain provenance.")
                    typed_field_name = st.text_input("Type the exact field name to confirm", key="ops_delete_field_name")
                    confirm_field = st.checkbox("I understand that this field deletion cannot be undone", key="ops_delete_field_confirm")
                    if st.button("Delete field and dependent records", type="primary", disabled=not (confirm_field and typed_field_name == str(selected_field["name"])) or external_block, key="ops_delete_field_button", width="stretch"):
                        try:
                            deleted = db.delete_field(delete_field_id)
                        except Exception as error:
                            st.error(str(error))
                            st.stop()
                        if st.session_state.get("field_ops_active_field_id") == delete_field_id:
                            st.session_state.pop("field_ops_active_field_id", None)
                        st.success(f"Field deleted. {sum(deleted.values()):,} dependent records were removed.")
                        st.rerun()

    with seasons_tab:
        field_id, field = _field_selector(db, "ops_crop_history_field")
        if field_id:
            history = db.frame("SELECT * FROM crop_history WHERE field_id=? ORDER BY season_year DESC", (field_id,))
            if not history.empty:
                st.dataframe(history, hide_index=True, width="stretch")
            with st.form("ops_crop_history_form"):
                cols = st.columns(4)
                year = int(cols[0].number_input("Season", 1900, 2200, int(field.get("season_year") or date.today().year)))
                crop = cols[1].text_input("Crop", value=str(field.get("crop") or ""))
                variety = cols[2].text_input("Variety", value=str(field.get("variety") or ""))
                yield_value = cols[3].number_input("Yield (t/ha, optional)", min_value=0.0, value=0.0, step=0.1)
                dates = st.columns(2)
                sowing = dates[0].date_input("Sowing date", value=None)
                harvest = dates[1].date_input("Harvest date", value=None)
                notes = st.text_area("Season notes")
                save = st.form_submit_button("Add crop-history record", type="primary", width="stretch")
            if save:
                if not crop.strip():
                    st.error("Crop is required.")
                else:
                    db.add_crop_history(field_id, year, crop, variety=variety, sowing_date=str(sowing) if sowing else None, harvest_date=str(harvest) if harvest else None, yield_t_ha=yield_value or None, notes=notes)
                    st.success("Crop-history record saved.")
                    st.rerun()

    with team_tab:
        users = db.users()
        if not users.empty:
            st.dataframe(users, hide_index=True, width="stretch")
        with st.form("ops_user_form"):
            cols = st.columns(3)
            name = cols[0].text_input("Name")
            email = cols[1].text_input("Email")
            role = cols[2].selectbox("Workflow role", ROLE_OPTIONS)
            create = st.form_submit_button("Create local user profile", width="stretch")
        if create:
            if name.strip():
                db.create_user(name, email, role)
                st.success("User profile created.")
                st.rerun()
            else:
                st.error("Name is required.")
        st.info("These are workflow roles and field assignments inside the local app. They are not secure login authentication or cloud identity management.")
        users = db.users()
        fields = db.fields()
        if not users.empty and not fields.empty:
            user_labels = {f"{r['name']} · {r['role']}": str(r["user_id"]) for _, r in users.iterrows()}
            field_labels = {f"{r['farm_name']} · {r['name']}": str(r["field_id"]) for _, r in fields.iterrows()}
            cols = st.columns(3)
            user_label = cols[0].selectbox("User", list(user_labels), key="ops_access_user")
            field_label = cols[1].selectbox("Field", list(field_labels), key="ops_access_field")
            permission = cols[2].selectbox("Permission", ["View", "Record observations", "Manage field", "Administer"])
            if st.button("Assign field access", width="stretch", key="ops_grant_access"):
                db.grant_access(user_labels[user_label], field_labels[field_label], permission)
                st.success("Field access recorded.")

    with map_tab:
        st.markdown("### Organisation, field and active-experiment map")
        st.caption(
            "Select one farm or agricultural research centre. The map fits its complete boundary and fields; selecting "
            "or clicking a saved field zooms directly to that boundary."
        )
        farms_for_map = db.farms()
        if farms_for_map.empty:
            st.info("Create a farm or agricultural research centre first.")
        else:
            farm_labels = {
                f"{row.get('entity_type') or 'Farm'} · {row.get('name')} · {row.get('country') or ''}": str(row.get("farm_id"))
                for _, row in farms_for_map.iterrows()
            }
            selected_farm_label = st.selectbox("Organisation to display", list(farm_labels), key="ops_portfolio_map_farm")
            selected_farm_id = farm_labels[selected_farm_label]
            map_fields = db.fields(selected_farm_id)
            field_options = ["All fields"]
            field_lookup = {}
            for _, row in map_fields.iterrows():
                label = f"{row['name']} · {float(row.get('area_ha') or 0):,.3f} ha"
                field_options.append(label)
                field_lookup[label] = str(row["field_id"])
            map_cols = st.columns([2, 2, 1])
            portfolio_focus_key = f"ops_portfolio_focus_{selected_farm_id}"
            portfolio_pending_key = f"ops_portfolio_pending_focus_{selected_farm_id}"
            pending_portfolio_id = st.session_state.pop(portfolio_pending_key, None)
            if pending_portfolio_id:
                pending_label = next((label for label, field_id in field_lookup.items() if field_id == str(pending_portfolio_id)), "All fields")
                st.session_state[portfolio_focus_key] = pending_label
            focus_label = map_cols[0].selectbox("Focus field", field_options, key=portfolio_focus_key)
            trial_statuses = map_cols[1].multiselect("Experiment statuses", ["Planned", "Active", "Completed", "Archived"], default=["Active"], key="ops_portfolio_trial_statuses")
            show_units = map_cols[2].checkbox("Treatment units", value=True, key="ops_portfolio_show_units")
            focused_id = field_lookup.get(focus_label)
            clicked_id = _render_field_map(
                db, focused_id, key=f"ops_portfolio_map_{selected_farm_id}", farm_id=selected_farm_id,
                pollination_db=context.get("pollination_db"), trial_statuses=trial_statuses,
                show_treatment_units=show_units,
            )
            if clicked_id and clicked_id != focused_id:
                st.session_state.field_ops_active_field_id = clicked_id
                st.session_state[portfolio_pending_key] = clicked_id
                st.rerun()
            if focused_id:
                st.session_state.field_ops_active_field_id = focused_id


def render_tasks_scouting_page(db: FieldOperationsDatabase, context: Mapping[str, Any]) -> None:
    field_id, field = _field_selector(db, "ops_tasks_field")
    if not field_id:
        return
    tasks_tab, scouting_tab, operations_tab, diary_tab = st.tabs(["Tasks", "Scouting", "Operations & inputs", "Field diary"])

    with tasks_tab:
        tasks = db.tasks(field_id)
        open_count = int((~tasks["status"].isin(["Completed", "Cancelled"])).sum()) if not tasks.empty else 0
        overdue = 0
        if not tasks.empty:
            due = pd.to_datetime(tasks["due_date"], errors="coerce")
            overdue = int(((due.dt.date < date.today()) & ~tasks["status"].isin(["Completed", "Cancelled"])).sum())
        cards = st.columns(3)
        cards[0].metric("Open tasks", open_count)
        cards[1].metric("Overdue", overdue)
        cards[2].metric("Completed", int(tasks["status"].eq("Completed").sum()) if not tasks.empty else 0)
        with st.form("ops_task_form"):
            cols = st.columns(4)
            title = cols[0].text_input("Task title")
            category = cols[1].selectbox("Category", TASK_CATEGORIES)
            assigned = cols[2].text_input("Assigned to")
            due = cols[3].date_input("Due date", value=date.today() + timedelta(days=1))
            cols2 = st.columns(3)
            priority = cols2[0].selectbox("Priority", TASK_PRIORITIES, index=1)
            status = cols2[1].selectbox("Status", TASK_STATUSES)
            recurrence = cols2[2].selectbox("Repeat", ["None", "Daily", "Weekly", "Fortnightly", "Monthly"])
            description = st.text_area("Instructions / acceptance criteria")
            submit = st.form_submit_button("Create task", type="primary", width="stretch")
        if submit:
            if title.strip():
                db.create_task(field_id, title, category=category, assigned_to=assigned, due_date=str(due), priority=priority, status=status, recurrence=recurrence, description=description)
                st.success("Task created.")
                st.rerun()
            else:
                st.error("Task title is required.")
        tasks = db.tasks(field_id)
        if not tasks.empty:
            filters = st.columns(3)
            statuses = filters[0].multiselect("Show statuses", TASK_STATUSES, default=["Planned", "Ready", "In progress", "Blocked"])
            priorities = filters[1].multiselect("Priorities", TASK_PRIORITIES, default=TASK_PRIORITIES)
            category_filter = filters[2].multiselect("Categories", TASK_CATEGORIES, default=[])
            view = tasks[tasks["status"].isin(statuses) & tasks["priority"].isin(priorities)]
            if category_filter:
                view = view[view["category"].isin(category_filter)]
            st.dataframe(view, hide_index=True, width="stretch")
            labels = {f"{r['title']} · {r['status']} · due {r['due_date']}": str(r["task_id"]) for _, r in tasks.iterrows()}
            selected = st.selectbox("Update a task", list(labels), key="ops_task_update_select")
            cols = st.columns(2)
            new_status = cols[0].selectbox("New status", TASK_STATUSES, key="ops_task_new_status")
            user = cols[1].text_input("Updated by", key="ops_task_updated_by")
            if st.button("Update task status", width="stretch", key="ops_task_status_button"):
                db.update_task_status(labels[selected], new_status, user)
                st.success("Task updated.")
                st.rerun()

    with scouting_tab:
        observations = db.observations(field_id)
        field_lat = float(field.get("centroid_lat"))
        field_lon = float(field.get("centroid_lon"))
        tasks = db.tasks(field_id)
        task_labels = {"No linked task": None}
        if not tasks.empty:
            task_labels.update({f"{r['title']} ({r['status']})": str(r["task_id"]) for _, r in tasks.iterrows()})
        with st.form("ops_scouting_form"):
            cols = st.columns(5)
            observed_date = cols[0].date_input("Observation date", value=date.today())
            observed_time = cols[1].time_input("Observation time", value=datetime.now().time().replace(microsecond=0))
            category = cols[2].selectbox("Observation type", OBSERVATION_CATEGORIES)
            severity = cols[3].slider("Severity", 1, 5, 2)
            created_by = cols[4].text_input("Observer")
            observed_at = datetime.combine(observed_date, observed_time)
            location_mode = st.radio("Location", ["Field centroid", "Enter GPS coordinates"], horizontal=True)
            loc_cols = st.columns(2)
            lat = loc_cols[0].number_input("Latitude", value=field_lat, format="%.7f", disabled=location_mode == "Field centroid")
            lon = loc_cols[1].number_input("Longitude", value=field_lon, format="%.7f", disabled=location_mode == "Field centroid")
            linked = st.selectbox("Linked task", list(task_labels))
            notes = st.text_area("Observation notes")
            recommendation = st.text_area("Recommended follow-up")
            photo = st.file_uploader("Photo (optional)", type=["jpg", "jpeg", "png", "webp"], key="ops_observation_photo")
            create_task = st.checkbox("Create a follow-up scouting task")
            submit = st.form_submit_button("Save observation", type="primary", width="stretch")
        if submit:
            photo_path = db.save_attachment(photo.getvalue(), photo.name) if photo is not None else ""
            observation_id = db.create_observation(
                field_id, task_id=task_labels[linked], observed_at=(observed_at or datetime.now()).isoformat(),
                category=category, severity=severity, latitude=lat, longitude=lon, notes=notes,
                recommendation=recommendation, photo_path=photo_path, created_by=created_by,
            )
            if create_task:
                db.create_task(field_id, f"Follow up: {category}", category="Scouting", assigned_to=created_by,
                               due_date=str(date.today() + timedelta(days=1)), priority="High" if severity >= 4 else "Normal",
                               description=f"Observation {observation_id}: {notes}\nRecommended follow-up: {recommendation}", source="Scouting observation")
            st.success("Observation saved.")
            st.rerun()
        observations = db.observations(field_id)
        if not observations.empty:
            st.dataframe(observations, hide_index=True, width="stretch")
            _render_field_map(db, field_id, observations=observations, key="ops_scouting_map")
            _download_dataframe("Download scouting observations", observations, f"{slug(field['name'])}_scouting.csv", "ops_download_scouting")

    with operations_tab:
        with st.form("ops_operation_form"):
            cols = st.columns(4)
            operation_date = cols[0].date_input("Operation date", value=date.today())
            category = cols[1].selectbox("Operation", OPERATION_CATEGORIES)
            product = cols[2].text_input("Product / material / implement")
            operator = cols[3].text_input("Operator")
            cols2 = st.columns(5)
            rate = cols2[0].number_input("Rate", min_value=0.0, value=0.0)
            rate_unit = cols2[1].text_input("Rate unit", value="kg/ha")
            area = cols2[2].number_input("Treated area (ha)", min_value=0.0, value=float(field.get("area_ha") or 0.0))
            water = cols2[3].number_input("Water / irrigation (mm)", min_value=0.0, value=0.0)
            cost = cols2[4].number_input("Cost", min_value=0.0, value=0.0)
            notes = st.text_area("Operation notes, weather constraints and safety record")
            save = st.form_submit_button("Log operation", type="primary", width="stretch")
        if save:
            db.create_operation(field_id, operation_date=str(operation_date), category=category, product=product,
                                rate=rate or None, rate_unit=rate_unit, treated_area_ha=area or None, water_mm=water or None,
                                cost=cost or None, operator=operator, notes=notes)
            st.success("Operation recorded.")
            st.rerun()
        operations = db.operations(field_id)
        if not operations.empty:
            st.dataframe(operations, hide_index=True, width="stretch")
            summary = operations.groupby("category", as_index=False).agg(Events=("operation_id", "count"), Cost=("cost", "sum"), Water_mm=("water_mm", "sum"))
            st.plotly_chart(px.bar(summary, x="category", y="Events", title="Recorded operations by category"), width="stretch")

    with diary_tab:
        timeline = db.field_timeline(field_id)
        if timeline.empty:
            st.info("No field-history records yet.")
        else:
            st.dataframe(timeline, hide_index=True, width="stretch")
            _download_dataframe("Download complete field diary", timeline, f"{slug(field['name'])}_field_diary.csv", "ops_download_diary")


def render_sensors_irrigation_page(db: FieldOperationsDatabase, context: Mapping[str, Any]) -> None:
    field_id, field = _field_selector(db, "ops_sensor_field")
    if not field_id:
        return
    registry_tab, readings_tab, qc_tab, irrigation_tab, nutrition_tab = st.tabs(["Sensor registry", "Readings", "Quality control", "Irrigation advisory", "Nutrition samples"])

    with registry_tab:
        sensors = db.sensors(field_id)
        if not sensors.empty:
            st.dataframe(sensors, hide_index=True, width="stretch")
        with st.form("ops_sensor_form"):
            cols = st.columns(4)
            name = cols[0].text_input("Sensor name")
            sensor_type = cols[1].selectbox("Sensor type", SENSOR_TYPES)
            unit = cols[2].text_input("Unit", value=SENSOR_DEFAULT_UNITS[SENSOR_TYPES[0]])
            depth = cols[3].number_input("Depth (cm, optional)", min_value=0.0, value=0.0)
            loc = st.columns(2)
            latitude = loc[0].number_input("Latitude", value=float(field["centroid_lat"]), format="%.7f")
            longitude = loc[1].number_input("Longitude", value=float(field["centroid_lon"]), format="%.7f")
            source = st.text_input("Source / manufacturer / station ID")
            calibration = st.text_area("Calibration and installation notes")
            save = st.form_submit_button("Register sensor", type="primary", width="stretch")
        if save:
            if name.strip():
                db.create_sensor(field_id, name, sensor_type, unit=unit or SENSOR_DEFAULT_UNITS.get(sensor_type), depth_cm=depth or None,
                                 latitude=latitude, longitude=longitude, source=source, calibration_note=calibration)
                st.success("Sensor registered.")
                st.rerun()
            else:
                st.error("Sensor name is required.")
        sensors = db.sensors(field_id)
        _render_field_map(db, field_id, sensors=sensors, key="ops_sensor_map")

    with readings_tab:
        sensors = db.sensors(field_id)
        if sensors.empty:
            st.info("Register a sensor first.")
        else:
            labels = {f"{r['name']} · {r['sensor_type']} · {r['depth_cm'] or 'surface'} cm": str(r["sensor_id"]) for _, r in sensors.iterrows()}
            selected = st.selectbox("Sensor", list(labels), key="ops_reading_sensor")
            sensor_id = labels[selected]
            upload = st.file_uploader("Upload readings CSV", type=["csv"], key="ops_sensor_readings_upload")
            if upload is not None:
                try:
                    raw = pd.read_csv(upload)
                    st.dataframe(raw.head(50), hide_index=True, width="stretch")
                    cols = st.columns(2)
                    timestamp_col = cols[0].selectbox("Timestamp column", list(raw.columns), key="ops_sensor_timestamp_col")
                    numeric_candidates = [c for c in raw.columns if c != timestamp_col]
                    value_col = cols[1].selectbox("Value column", numeric_candidates, key="ops_sensor_value_col")
                    if st.button("Import sensor readings", type="primary", width="stretch", key="ops_import_sensor_readings"):
                        report = db.import_sensor_readings(sensor_id, raw, timestamp_col, value_col)
                        st.success(f"Imported {report['inserted']} new and updated {report['updated']} readings; {report['invalid']} invalid rows were excluded.")
                        st.rerun()
                except Exception as error:
                    st.error(f"Could not import readings: {error}")
            template = pd.DataFrame({"timestamp": [datetime.now(timezone.utc).isoformat()], "value": [0.0]})
            _download_dataframe("Download readings template", template, "sensor_readings_template.csv", "ops_sensor_template")
            readings = db.readings(sensor_id=sensor_id)
            if not readings.empty:
                st.plotly_chart(px.line(readings, x="timestamp", y="value", title=f"{selected}"), width="stretch")
                st.dataframe(readings.tail(500), hide_index=True, width="stretch")

    with qc_tab:
        sensors = db.sensors(field_id)
        if sensors.empty:
            st.info("No sensors registered.")
        else:
            rows = []
            detailed = {}
            for sensor in sensors.to_dict("records"):
                readings = db.readings(sensor_id=sensor["sensor_id"])
                checked, summary = sensor_quality_report(readings, sensor["sensor_type"])
                rows.append({
                    "Sensor": sensor["name"], "Type": sensor["sensor_type"], "Rows": summary["rows"],
                    "Valid": summary["valid"], "Duplicates": summary["duplicates"], "Missing": summary["missing"],
                    "Stale >7 days": summary["stale"], "Flatline last 10": summary["flatline"], "Latest": summary.get("latest"),
                })
                detailed[sensor["name"]] = checked
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
            selected = st.selectbox("Inspect quality flags", list(detailed), key="ops_qc_sensor")
            st.dataframe(detailed[selected].tail(1000), hide_index=True, width="stretch")
            st.caption("Broad physical-range checks detect obvious data errors only. They do not replace calibration, installation QA or agronomic validation.")

    with irrigation_tab:
        advisory = irrigation_advisory(context, field, db)
        cols = st.columns(4)
        cols[0].metric("Data source", advisory["source"])
        cols[1].metric("Status", advisory["status"])
        cols[2].metric("Urgency", advisory["urgency"])
        cols[3].metric("Suggested net depth", "—" if advisory["recommended_mm"] is None else f"{advisory['recommended_mm']:.1f} mm")
        st.info(advisory["reason"])
        if advisory["recommended_mm"] is not None and advisory["recommended_mm"] > 0:
            efficiency = st.slider("Application efficiency", 0.30, 1.00, 0.85, 0.01, key="ops_irrigation_efficiency")
            gross = advisory["recommended_mm"] / efficiency
            st.metric("Estimated gross application", f"{gross:.1f} mm")
            if st.button("Create irrigation task from advisory", type="primary", width="stretch", key="ops_irrigation_task"):
                db.create_task(field_id, f"Irrigate {field['name']}: approximately {gross:.1f} mm gross", category="Irrigation",
                               due_date=str(date.today()), priority="High", description=advisory["reason"], source="Irrigation advisory")
                st.success("Irrigation task created.")
        st.warning("This is a transparent decision-support calculation, not automatic irrigation control. Confirm the soil profile, root depth, forecast rainfall, system capacity and field observations before applying water.")

    with nutrition_tab:
        with st.form("ops_nutrient_form"):
            cols = st.columns(4)
            sample_date = cols[0].date_input("Sample date", value=date.today())
            sample_type = cols[1].selectbox("Sample type", ["Soil", "Tissue", "Water", "Fertiliser"])
            latitude = cols[2].number_input("Latitude", value=float(field["centroid_lat"]), format="%.7f")
            longitude = cols[3].number_input("Longitude", value=float(field["centroid_lon"]), format="%.7f")
            vals = st.columns(6)
            nitrogen = vals[0].number_input("N", value=0.0)
            phosphorus = vals[1].number_input("P", value=0.0)
            potassium = vals[2].number_input("K", value=0.0)
            ph = vals[3].number_input("pH", min_value=0.0, max_value=14.0, value=7.0)
            ec = vals[4].number_input("EC", min_value=0.0, value=0.0)
            organic = vals[5].number_input("Organic matter (%)", min_value=0.0, value=0.0)
            notes = st.text_area("Laboratory method, units, depth and notes")
            save = st.form_submit_button("Save sample", type="primary", width="stretch")
        if save:
            db.add_nutrient_sample(field_id, sample_date=str(sample_date), sample_type=sample_type, latitude=latitude, longitude=longitude,
                                   nitrogen=nitrogen or None, phosphorus=phosphorus or None, potassium=potassium or None,
                                   ph=ph or None, ec=ec or None, organic_matter=organic or None, notes=notes)
            st.success("Sample saved.")
            st.rerun()
        samples = db.nutrient_samples(field_id)
        if not samples.empty:
            st.dataframe(samples, hide_index=True, width="stretch")
            st.caption("Units and laboratory methods are intentionally stored in notes because agronomic sufficiency ranges depend on crop, tissue, growth stage, soil method and laboratory protocol.")


def render_crop_intelligence_page(db: FieldOperationsDatabase, context: Mapping[str, Any]) -> None:
    field_id, field = _field_selector(db, "ops_intelligence_field")
    if not field_id:
        return
    dashboard_tab, rules_tab, alerts_tab, leaderboard_tab = st.tabs(["Field health", "Alert rules", "Alerts", "Field leaderboard"])

    with dashboard_tab:
        satellite_linked = _satellite_matches_field(context, field)
        project_linked = _project_matches_field(context, field)
        if isinstance(context.get("satellite_time_series"), pd.DataFrame) and not satellite_linked:
            st.warning("A satellite time series is loaded, but its AOI does not exactly match this field boundary, so it is excluded from this dashboard.")
        if (isinstance(context.get("root_zone"), pd.DataFrame) or isinstance(context.get("daily_weather"), pd.DataFrame)) and not project_linked:
            st.warning("Weather or root-zone results are loaded for a different or unverified project location, so they are excluded from this field dashboard.")
        metrics = latest_metrics_from_context(context, db, field_id)
        if metrics:
            cols = st.columns(min(6, max(1, len(metrics))))
            for index, (metric, value) in enumerate(metrics.items()):
                cols[index % len(cols)].metric(metric, f"{value:.3g}")
            st.dataframe(pd.DataFrame([{"Metric": k, "Latest value": v} for k, v in metrics.items()]), hide_index=True, width="stretch")
            if st.button("Evaluate enabled alert rules", type="primary", width="stretch", key="ops_evaluate_alerts"):
                result = evaluate_alert_rules(db, field_id, metrics)
                st.session_state.ops_last_alert_evaluation = result["details"]
                st.success(f"Evaluated {result['evaluated']} rules and created {result['generated']} new alerts.")
            if isinstance(st.session_state.get("ops_last_alert_evaluation"), pd.DataFrame):
                st.dataframe(st.session_state.ops_last_alert_evaluation, hide_index=True, width="stretch")
        else:
            st.info("No linked satellite, root-zone, weather or sensor metrics are available. Run those modules or import sensor readings first.")
        satellite = context.get("satellite_time_series")
        if satellite_linked and isinstance(satellite, pd.DataFrame) and not satellite.empty:
            numeric = [c for c in satellite.columns if pd.to_numeric(satellite[c], errors="coerce").notna().sum() >= 2]
            date_col = next((c for c in satellite.columns if str(c).casefold() in {"date", "datetime", "acquisition date", "acquisition_date"}), None)
            if date_col and numeric:
                selected = st.multiselect("Satellite indices", numeric, default=[c for c in numeric if str(c).upper() in {"NDVI", "NDMI", "EVI", "NDRE"}][:3])
                if selected:
                    long = satellite[[date_col] + selected].melt(id_vars=[date_col], var_name="Index", value_name="Value")
                    st.plotly_chart(px.line(long, x=date_col, y="Value", color="Index", title="Linked satellite-index trends"), width="stretch")

    with rules_tab:
        rules = db.alert_rules()
        st.dataframe(rules, hide_index=True, width="stretch")
        with st.form("ops_rule_form"):
            cols = st.columns(4)
            name = cols[0].text_input("Rule name")
            source = cols[1].selectbox("Source", ["satellite", "root_zone", "weather", "sensor"])
            metric = cols[2].text_input("Metric name", value="NDVI")
            operator = cols[3].selectbox("Operator", ["<=", "<", ">=", ">", "=="])
            cols2 = st.columns(4)
            threshold = cols2[0].number_input("Threshold", value=0.0)
            severity = cols2[1].selectbox("Severity", ["Low", "Medium", "High", "Urgent"])
            window = int(cols2[2].number_input("Window (days)", 1, 365, 7))
            enabled = cols2[3].checkbox("Enabled", value=True)
            notes = st.text_area("Interpretation and validation note")
            save = st.form_submit_button("Save alert rule", type="primary", width="stretch")
        if save:
            if name.strip() and metric.strip():
                db.save_rule(name=name, source=source, metric=metric, operator=operator, threshold=threshold,
                             severity=severity, window_days=window, enabled=enabled, notes=notes)
                st.success("Rule saved.")
                st.rerun()
            else:
                st.error("Rule name and metric are required.")
        st.warning("Rules flag measurements and model outputs; they do not diagnose a disease, nutrient deficiency or irrigation requirement by themselves.")

    with alerts_tab:
        alerts = db.alerts(field_id)
        if alerts.empty:
            st.info("No alerts for this field.")
        else:
            st.dataframe(alerts, hide_index=True, width="stretch")
            labels = {f"{r['severity']} · {r['alert_type']} · {r['status']} · {r['created_at'][:10]}": str(r["alert_id"]) for _, r in alerts.iterrows()}
            selected = st.selectbox("Update alert", list(labels), key="ops_alert_update")
            cols = st.columns(2)
            status = cols[0].selectbox("Status", ["Open", "Acknowledged", "Resolved"])
            user = cols[1].text_input("Updated by")
            if st.button("Update alert status", width="stretch", key="ops_alert_status_button"):
                db.update_alert_status(labels[selected], status, user)
                st.success("Alert updated.")
                st.rerun()

    with leaderboard_tab:
        fields = db.fields()
        rows = []
        for row in fields.to_dict("records"):
            field_metrics = latest_metrics_from_context(context, db, row["field_id"]) if row["field_id"] == field_id else {}
            open_tasks = db.frame("SELECT COUNT(*) AS n FROM tasks WHERE field_id=? AND status NOT IN ('Completed','Cancelled')", (row["field_id"],)).iloc[0]["n"]
            open_alerts = db.frame("SELECT COUNT(*) AS n FROM alerts WHERE field_id=? AND status!='Resolved'", (row["field_id"],)).iloc[0]["n"]
            severe_obs = db.frame("SELECT COUNT(*) AS n FROM observations WHERE field_id=? AND severity>=4", (row["field_id"],)).iloc[0]["n"]
            rows.append({"Farm": row["farm_name"], "Field": row["name"], "Area (ha)": row["area_ha"], "Crop": row["crop"],
                         "Open tasks": open_tasks, "Open alerts": open_alerts, "Severe observations": severe_obs,
                         "Latest NDVI": field_metrics.get("NDVI"), "Latest Ks": field_metrics.get("Ks")})
        leaderboard = pd.DataFrame(rows)
        if not leaderboard.empty:
            leaderboard["Attention score"] = leaderboard["Open alerts"] * 3 + leaderboard["Severe observations"] * 2 + leaderboard["Open tasks"]
            st.dataframe(leaderboard.sort_values("Attention score", ascending=False), hide_index=True, width="stretch")
            st.caption("The attention score is an operational triage count, not a crop-loss probability.")


def render_precision_zones_page(db: FieldOperationsDatabase, context: Mapping[str, Any]) -> None:
    field_id, field = _field_selector(db, "ops_precision_field")
    if not field_id:
        return
    zones_tab, sampling_tab, prescriptions_tab = st.tabs(["Management zones", "Sampling grid", "Saved prescriptions"])

    with zones_tab:
        st.info("Create generic management zones from georeferenced point samples such as soil tests, yield-monitor points, drone samples or exported satellite pixels. Field-average Sentinel-2 time series cannot create within-field zones by themselves.")
        upload = st.file_uploader("Upload point CSV with latitude, longitude and one or more numeric variables", type=["csv"], key="ops_zone_points")
        if upload is not None:
            try:
                points = pd.read_csv(upload)
                st.dataframe(points.head(100), hide_index=True, width="stretch")
                numeric = [c for c in points.columns if c not in {"latitude", "longitude"} and pd.to_numeric(points[c], errors="coerce").notna().sum() >= 4]
                if not numeric:
                    st.error("No suitable numeric variable was found.")
                else:
                    cols = st.columns(5)
                    value_col = cols[0].selectbox("Zoning variable", numeric)
                    n_zones = int(cols[1].slider("Zones", 2, 5, 3))
                    direction = cols[2].selectbox("Rate response", ["Higher rate in higher-value zones", "Higher rate in lower-value zones"])
                    low_rate = cols[3].number_input("Minimum rate", min_value=0.0, value=50.0)
                    high_rate = cols[4].number_input("Maximum rate", min_value=0.0, value=150.0)
                    rate_unit = st.text_input("Rate unit", value="kg/ha")
                    if st.button("Build management zones", type="primary", width="stretch", key="ops_build_zones"):
                        zones = build_management_zones(points, field["geometry"], value_col, n_zones, low_rate, high_rate)
                        if direction == "Higher rate in lower-value zones":
                            zones["rate"] = high_rate + low_rate - zones["rate"]
                        st.session_state.ops_management_zones = zones
                        st.session_state.ops_management_zone_metadata = {"field_id": field_id, "variable": value_col, "unit": rate_unit}
                        st.success(f"Created {n_zones} zones from {len(zones)} in-field samples.")
            except Exception as error:
                st.error(str(error))
        zones = st.session_state.get("ops_management_zones")
        metadata = st.session_state.get("ops_management_zone_metadata") or {}
        if isinstance(zones, pd.DataFrame) and not zones.empty and metadata.get("field_id") == field_id:
            summary = zones.groupby("zone_label", as_index=False).agg(Samples=("zone_label", "size"), Mean_value=(metadata["variable"], "mean"), Rate=("rate", "mean"))
            st.dataframe(summary, hide_index=True, width="stretch")
            map_obj = _map_for_geometry(field["geometry"])
            folium.GeoJson(geometry_feature(field["geometry"], {"name": field["name"]}), style_function=lambda _: {"weight": 3, "fillOpacity": 0.02}).add_to(map_obj)
            for row in zones.to_dict("records"):
                folium.GeoJson(geometry_feature(row["geometry"], {"zone": row["zone_label"], "value": row[metadata["variable"]], "rate": row["rate"]}),
                               tooltip=folium.GeoJsonTooltip(fields=["zone", "value", "rate"]), style_function=lambda _: {"weight": 1, "fillOpacity": 0.45}).add_to(map_obj)
            st_folium(map_obj, use_container_width=True, height=560, key="ops_zones_map")
            features = [geometry_feature(r["geometry"], {"zone_label": r["zone_label"], metadata["variable"]: r[metadata["variable"]], "rate": r["rate"], "rate_unit": metadata["unit"]}) for r in zones.to_dict("records")]
            geojson_bytes = json_dumps(geometry_feature_collection(features)).encode("utf-8")
            downloads = st.columns(2)
            downloads[0].download_button("Download generic prescription GeoJSON", geojson_bytes, file_name=f"{slug(field['name'])}_prescription.geojson", mime="application/geo+json", width="stretch", key="ops_download_zone_geojson")
            downloads[1].download_button("Download zone samples CSV", zones.drop(columns=["geometry"], errors="ignore").to_csv(index=False).encode(), file_name=f"{slug(field['name'])}_zones.csv", mime="text/csv", width="stretch", key="ops_download_zone_csv")
            prescription_name = st.text_input("Prescription name", value=f"{metadata['variable']} management zones")
            if st.button("Save prescription", width="stretch", key="ops_save_prescription"):
                db.save_prescriptions(field_id, prescription_name, metadata["variable"], metadata["unit"], zones)
                st.success("Prescription saved.")
            st.warning("The GeoJSON is a transparent generic exchange file, not a calibrated controller- or machinery-specific prescription. Verify agronomic rates, spatial interpolation and equipment format before field use.")

    with sampling_tab:
        cols = st.columns(2)
        spacing = cols[0].number_input("Grid spacing (m)", min_value=5.0, max_value=1000.0, value=50.0, step=5.0)
        inset = cols[1].number_input("Boundary inset (m)", min_value=0.0, max_value=500.0, value=5.0, step=1.0)
        if st.button("Generate sampling grid", type="primary", width="stretch", key="ops_sampling_grid"):
            try:
                grid = generate_sampling_grid(field["geometry"], spacing, inset)
                st.session_state.ops_sampling_grid = grid
                st.success(f"Generated {len(grid)} sample locations.")
            except Exception as error:
                st.error(str(error))
        grid = st.session_state.get("ops_sampling_grid")
        if isinstance(grid, pd.DataFrame) and not grid.empty:
            st.dataframe(grid.drop(columns=["geometry"], errors="ignore"), hide_index=True, width="stretch")
            map_obj = _map_for_geometry(field["geometry"])
            folium.GeoJson(geometry_feature(field["geometry"], {"name": field["name"]}), style_function=lambda _: {"weight": 3, "fillOpacity": 0.04}).add_to(map_obj)
            for row in grid.to_dict("records"):
                folium.CircleMarker([row["latitude"], row["longitude"]], radius=4, tooltip=row["sample_id"], fill=True).add_to(map_obj)
            st_folium(map_obj, use_container_width=True, height=560, key="ops_sampling_map")
            features = [geometry_feature(r["geometry"], {"sample_id": r["sample_id"]}) for r in grid.to_dict("records")]
            downloads = st.columns(2)
            downloads[0].download_button("Download sampling points CSV", grid.drop(columns=["geometry"]).to_csv(index=False).encode(), file_name=f"{slug(field['name'])}_sampling_grid.csv", mime="text/csv", width="stretch", key="ops_sampling_csv")
            downloads[1].download_button("Download sampling points GeoJSON", json_dumps(geometry_feature_collection(features)).encode(), file_name=f"{slug(field['name'])}_sampling_grid.geojson", mime="application/geo+json", width="stretch", key="ops_sampling_geojson")

    with prescriptions_tab:
        prescriptions = db.prescriptions(field_id)
        if prescriptions.empty:
            st.info("No saved prescriptions.")
        else:
            st.dataframe(prescriptions.drop(columns=["geometry_json"], errors="ignore"), hide_index=True, width="stretch")


def render_data_exchange_page(db: FieldOperationsDatabase, context: Mapping[str, Any]) -> None:
    field_tab, import_tab, backup_tab, audit_tab = st.tabs(["Offline field pack", "Offline import", "Backup & integrations", "Audit log"])

    with field_tab:
        field_id, field = _field_selector(db, "ops_pack_field")
        if field_id:
            package = offline_field_pack(db, field_id, context)
            downloads = st.columns(2)
            downloads[0].download_button("Download offline field pack", package, file_name=f"{slug(field['name'])}_offline_field_pack.zip", mime="application/zip", width="stretch", key="ops_offline_pack_download")
            report = field_report_package(db, field_id, context)
            downloads[1].download_button("Download custom field report", report, file_name=f"{slug(field['name'])}_field_report.zip", mime="application/zip", width="stretch", key="ops_field_report_download")
            st.markdown("The field pack supports disconnected data capture. The custom report contains an HTML summary, interactive map, current tasks, alerts, scouting, operations and linked metrics.")

    with import_tab:
        field_id, field = _field_selector(db, "ops_import_field")
        if field_id:
            st.markdown("### Import completed scouting observations")
            observations_upload = st.file_uploader("Completed observation_import_template.csv", type=["csv"], key="ops_offline_observation_import")
            if observations_upload is not None:
                try:
                    observations = pd.read_csv(observations_upload)
                    required = {"observed_at", "category", "severity_1_5", "latitude", "longitude", "notes"}
                    missing = required.difference(observations.columns)
                    if missing:
                        st.error(f"Missing columns: {sorted(missing)}")
                    else:
                        st.dataframe(observations.head(100), hide_index=True, width="stretch")
                        if st.button("Import offline observations", type="primary", width="stretch", key="ops_import_offline_observations"):
                            imported = 0
                            for row in observations.to_dict("records"):
                                db.create_observation(field_id, observed_at=row.get("observed_at"), category=row.get("category"),
                                                      severity=int(row.get("severity_1_5") or 1), latitude=row.get("latitude"), longitude=row.get("longitude"),
                                                      notes=row.get("notes", ""), recommendation=row.get("recommendation", ""), created_by=row.get("created_by", ""))
                                imported += 1
                            st.success(f"Imported {imported} observations.")
                            st.rerun()
                except Exception as error:
                    st.error(str(error))
            st.markdown("### Import task-status updates")
            task_upload = st.file_uploader("Completed task_status_updates.csv", type=["csv"], key="ops_offline_task_import")
            if task_upload is not None:
                try:
                    task_updates = pd.read_csv(task_upload)
                    if {"task_id", "status"}.issubset(task_updates.columns):
                        st.dataframe(task_updates, hide_index=True, width="stretch")
                        if st.button("Import task updates", width="stretch", key="ops_import_task_updates"):
                            valid = 0
                            for row in task_updates.to_dict("records"):
                                if str(row.get("status")) in TASK_STATUSES:
                                    db.update_task_status(str(row["task_id"]), str(row["status"]), "Offline import")
                                    valid += 1
                            st.success(f"Applied {valid} task-status updates.")
                            st.rerun()
                    else:
                        st.error("The task update file must contain task_id and status.")
                except Exception as error:
                    st.error(str(error))
            st.markdown("### Import completed field operations")
            operation_upload = st.file_uploader("Completed operation_import_template.csv", type=["csv"], key="ops_offline_operation_import")
            if operation_upload is not None:
                try:
                    operation_rows = pd.read_csv(operation_upload)
                    required = {"operation_date", "category"}
                    missing = required.difference(operation_rows.columns)
                    if missing:
                        st.error(f"Missing columns: {sorted(missing)}")
                    else:
                        st.dataframe(operation_rows.head(100), hide_index=True, width="stretch")
                        if st.button("Import field operations", width="stretch", key="ops_import_operations"):
                            imported = 0
                            for row in operation_rows.to_dict("records"):
                                db.create_operation(
                                    field_id, operation_date=row.get("operation_date"), category=row.get("category"),
                                    product=row.get("product", ""), rate=row.get("rate"), rate_unit=row.get("rate_unit", ""),
                                    treated_area_ha=row.get("treated_area_ha"), water_mm=row.get("water_mm"), cost=row.get("cost"),
                                    operator=row.get("operator", "Offline import"), notes=row.get("notes", ""),
                                )
                                imported += 1
                            st.success(f"Imported {imported} field-operation records.")
                            st.rerun()
                except Exception as error:
                    st.error(str(error))

    with backup_tab:
        package = full_operations_export(db)
        st.download_button("Download complete operations backup", package, file_name=f"field_operations_backup_{date.today()}.zip", mime="application/zip", width="stretch", key="ops_full_backup")
        st.markdown("### API-ready exchange schema")
        schema = {
            "module_version": MODULE_VERSION,
            "resources": {
                "farms": ["farm_id", "name", "country", "admin_area"],
                "fields": ["field_id", "farm_id", "name", "geometry_json", "crop", "season_year"],
                "tasks": ["task_id", "field_id", "title", "assigned_to", "due_date", "status"],
                "observations": ["observation_id", "field_id", "observed_at", "category", "severity", "latitude", "longitude", "notes"],
                "sensor_readings": ["sensor_id", "timestamp", "value", "quality_flag"],
                "alerts": ["alert_id", "field_id", "source", "severity", "metric", "value", "status"],
            },
            "note": "This desktop release exports an integration-ready schema but does not expose a network API or implement authentication.",
        }
        st.json(schema)
        st.download_button("Download integration schema JSON", json_dumps(schema).encode(), file_name="field_operations_integration_schema.json", mime="application/json", width="stretch", key="ops_schema_download")

    with audit_tab:
        audit = db.audit_log()
        if audit.empty:
            st.info("No audit records.")
        else:
            st.dataframe(audit, hide_index=True, width="stretch")
            _download_dataframe("Download audit log", audit, "field_operations_audit_log.csv", "ops_audit_download")


def render_competitor_feature_guide() -> None:
    st.markdown("### What this release adds")
    rows = [
        ("Farm and field hierarchy", "Mapped farms, fields, crop seasons and field histories", "Implemented locally"),
        ("Team workflow", "Local user profiles, field permissions, task assignment and status tracking", "Workflow roles; no secure authentication"),
        ("Field scouting", "Geolocated structured observations, photos, severity, follow-up tasks and maps", "Implemented"),
        ("Operational diary", "Irrigation, fertiliser, crop protection, machinery and harvest records", "Implemented"),
        ("Connected data", "Generic sensor registry, CSV readings, quality checks, weather/root-zone/satellite linking", "Implemented through import and app state"),
        ("Risk alerts", "Configurable thresholds across satellite, weather, sensors and root-zone outputs", "Implemented; not disease diagnosis"),
        ("Irrigation support", "Root-zone-trigger advisory and task generation", "Implemented; no automatic control"),
        ("Nutrition records", "Soil/tissue/water samples with method notes", "Implemented; no universal sufficiency diagnosis"),
        ("Management zones", "Point-based clustering, VRA-style generic GeoJSON and CSV exports", "Implemented; not machinery-specific"),
        ("Sampling", "Field-contained regular sampling grids with CSV and GeoJSON", "Implemented"),
        ("Offline fieldwork", "Downloadable field packs and re-import of observations/task status", "File-based offline workflow"),
        ("Audit and backup", "SQLite backup, table exports, attachments and audit log", "Implemented"),
        ("REST API / live cloud sync", "Secure multi-tenant network services", "Not included in a local Streamlit package"),
        ("Machinery telematics", "Direct John Deere/ISOBUS/controller connectors", "Not included; generic exchange only"),
        ("Automated disease models", "Crop/pathogen-specific validated epidemiology", "Not included; configurable risk rules only"),
    ]
    st.dataframe(pd.DataFrame(rows, columns=["Capability", "Release 6 implementation", "Boundary"]), hide_index=True, width="stretch")
    st.info("The suite deliberately distinguishes implemented desktop functionality from cloud, hardware and agronomic services that require external infrastructure, licensing or crop-specific validation.")
