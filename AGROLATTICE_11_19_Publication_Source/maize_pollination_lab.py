"""Maize Flowering Synchrony Lab for the AgroLattice Research Tool.

The module supports field-trial design, map-based field and plot geometry,
parental-line flowering observations, synchrony metrics, satellite linkage,
group-aware predictive modelling, and exploratory sowing-offset optimisation.

Scientific scope
----------------
This module is designed for hybrid-maize seed-production research where pollen
shed from a male parent must overlap silk emergence/receptivity of a female
parent. It does not replace agronomic supervision, genetic-purity controls, or
independent field validation.
"""
from __future__ import annotations

import hashlib
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
from typing import Any, Iterable, Mapping, Sequence
from itertools import product

import folium
from branca.element import Element, MacroElement
from folium.plugins import Draw, Fullscreen, MeasureControl
from jinja2 import Template
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from streamlit_folium import st_folium
from local_boundary_editor import render_boundary_editor

from maize_mechanistic_twin import (
    DEFAULT_PHYSIOLOGY,
    MechanisticMaizeError,
    PhysiologyParameters,
    calibrate_parent_physiology,
    genomic_physiology_bridge,
    method_manifest as mechanistic_method_manifest,
    optimise_male_sowing_strategy,
    physiology_from_mapping,
    simulate_event_uncertainty,
    simulate_mfs,
)

from satellite_crop_monitoring import (
    geometry_area_hectares,
    geometry_centroid,
    geometry_geojson_bytes,
    geometry_hash,
    validate_aoi_geometry,
)

try:
    from shapely import affinity
    from shapely.geometry import box, mapping, shape
    from shapely.ops import transform, unary_union
except Exception:  # pragma: no cover - dependency status is checked in the UI
    affinity = box = mapping = shape = transform = unary_union = None

MODULE_VERSION = "3.0.0"
DB_SCHEMA_VERSION = "3.0.0"


class PollinationLabError(RuntimeError):
    """Raised when a pollination-lab operation cannot be completed safely."""


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


def slugify(value: str, fallback: str = "trial") -> str:
    import re

    token = re.sub(r"[^a-zA-Z0-9]+", "-", str(value or "").strip()).strip("-").lower()
    return token[:80] or fallback


def _add_base_layers(map_object: folium.Map, *, satellite_default: bool = False, collapsed: bool = False) -> folium.Map:
    """Add named road, light and satellite basemaps with an explicit toggle."""
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="Roads & places",
        overlay=False,
        control=True,
        show=not satellite_default,
    ).add_to(map_object)
    folium.TileLayer(
        tiles="CartoDB positron",
        name="Light map",
        overlay=False,
        control=True,
        show=False,
    ).add_to(map_object)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        name="Satellite imagery",
        attr="Esri, Maxar, Earthstar Geographics, and the GIS User Community",
        overlay=False,
        control=True,
        show=satellite_default,
        max_zoom=20,
    ).add_to(map_object)
    folium.LayerControl(collapsed=collapsed, position="topright").add_to(map_object)
    return map_object


def _add_distance_measurement(map_object: folium.Map) -> folium.Map:
    """Add a metre-based ruler and area tool to a Folium map."""
    MeasureControl(
        position="topleft",
        primary_length_unit="meters",
        secondary_length_unit="kilometers",
        primary_area_unit="sqmeters",
        secondary_area_unit="hectares",
        active_color="#dc2626",
        completed_color="#2563eb",
    ).add_to(map_object)
    return map_object


class _LiveDrawDistance(MacroElement):
    """Leaflet control showing the active edge and provisional perimeter while drawing."""

    _template = Template(
        """
        {% macro script(this, kwargs) %}
        (function() {
          var map = {{ this._parent.get_name() }};
          var active = false;
          var drawType = null;
          var fixedPoints = [];
          var rectangleStart = null;
          var box = L.control({position: 'bottomleft'});
          box.onAdd = function() {
            var div = L.DomUtil.create('div', 'leaflet-bar');
            div.style.background = 'rgba(255,255,255,0.96)';
            div.style.padding = '7px 10px';
            div.style.font = '600 12px/1.35 system-ui, sans-serif';
            div.style.color = '#111827';
            div.style.minWidth = '215px';
            div.style.display = 'none';
            div.innerHTML = 'Move the cursor to measure';
            this._container = div;
            return div;
          };
          box.addTo(map);

          function metres(value) {
            if (!isFinite(value)) return '—';
            if (value >= 1000) return (value / 1000).toFixed(3) + ' km';
            return value.toFixed(value < 100 ? 1 : 0) + ' m';
          }
          function refreshPoints(layerGroup) {
            fixedPoints = [];
            if (!layerGroup) return;
            layerGroup.eachLayer(function(layer) {
              if (layer.getLatLng) fixedPoints.push(layer.getLatLng());
            });
          }
          function fixedLength() {
            var total = 0;
            for (var i = 1; i < fixedPoints.length; i++) {
              total += map.distance(fixedPoints[i - 1], fixedPoints[i]);
            }
            return total;
          }

          map.on(L.Draw.Event.DRAWSTART, function(e) {
            active = true; drawType = e.layerType; fixedPoints = []; rectangleStart = null;
            box._container.style.display = 'block';
            box._container.innerHTML = 'Click the first corner; distances are in metres';
          });
          map.on(L.Draw.Event.DRAWVERTEX, function(e) {
            refreshPoints(e.layers);
          });
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
              var closing = map.distance(e.latlng, fixedPoints[0]);
              label += '<br><strong>Provisional perimeter:</strong> ' + metres(openTotal + closing);
            }
            box._container.innerHTML = label;
          });
          function stop() {
            active = false; drawType = null; fixedPoints = []; rectangleStart = null;
            if (box._container) box._container.style.display = 'none';
          }
          map.on(L.Draw.Event.DRAWSTOP, stop);
          map.on(L.Draw.Event.CREATED, stop);
        })();
        {% endmacro %}
        """
    )

    def __init__(self) -> None:
        super().__init__()
        self._name = "LiveDrawDistance"


def _add_live_draw_distance(map_object: folium.Map) -> folium.Map:
    _LiveDrawDistance().add_to(map_object)
    return map_object


def _draw_options() -> dict[str, Any]:
    """Leaflet.draw options with live metric length/perimeter and area labels."""
    return {
        "polyline": {"metric": True, "feet": False, "showLength": True},
        "rectangle": {"metric": True, "feet": False, "showArea": True},
        "polygon": {
            "allowIntersection": False,
            "metric": True,
            "feet": False,
            "showArea": True,
            "showLength": True,
        },
        "circle": False,
        "circlemarker": False,
        "marker": False,
    }


def geometry_union(geometries: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if shape is None or unary_union is None or mapping is None:
        raise PollinationLabError("Shapely is required for plot geometry operations.")
    valid = [shape(validate_aoi_geometry(item)) for item in geometries]
    if not valid:
        raise PollinationLabError("No valid geometries were supplied.")
    combined = unary_union(valid)
    return validate_aoi_geometry(mapping(combined))


def plot_is_inside_field(plot_geometry: Mapping[str, Any], field_geometry: Mapping[str, Any]) -> bool:
    if shape is None:
        return True
    field = shape(validate_aoi_geometry(field_geometry))
    plot = shape(validate_aoi_geometry(plot_geometry))
    # A tiny buffer protects against numerical precision at shared boundaries.
    return bool(field.buffer(1e-10).covers(plot))


def _geometry_feature(geometry: Mapping[str, Any], properties: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {
        "type": "Feature",
        "properties": dict(properties or {}),
        "geometry": validate_aoi_geometry(geometry),
    }


def _feature_collection(features: Sequence[Mapping[str, Any]]) -> bytes:
    return json.dumps(
        {"type": "FeatureCollection", "features": list(features)},
        indent=2,
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS parent_lines (
    parent_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL,
    maturity_notes TEXT,
    source TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS trials (
    trial_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    project_id TEXT,
    site_name TEXT,
    season_year INTEGER,
    female_parent TEXT NOT NULL,
    male_parent TEXT NOT NULL,
    female_parent_levels_json TEXT,
    male_parent_levels_json TEXT,
    parent_pairings_json TEXT,
    parent_pairing_mode TEXT,
    sowing_density_levels_json TEXT,
    sowing_date_levels_json TEXT,
    sowing_offset_levels_json TEXT,
    female_sowing_date TEXT NOT NULL,
    design_type TEXT NOT NULL,
    blocks INTEGER NOT NULL,
    replicates_per_treatment INTEGER NOT NULL,
    row_ratio TEXT,
    planting_density_plants_ha REAL,
    primary_outcome TEXT,
    base_temperature_c REAL NOT NULL,
    upper_temperature_c REAL NOT NULL,
    field_geometry_json TEXT,
    field_area_ha REAL,
    centroid_lat REAL,
    centroid_lon REAL,
    source_field_id TEXT,
    source_field_geometry_hash TEXT,
    source_field_snapshot_json TEXT,
    boundary_mode TEXT,
    status TEXT NOT NULL DEFAULT 'Active',
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS plots (
    plot_id TEXT PRIMARY KEY,
    trial_id TEXT NOT NULL REFERENCES trials(trial_id) ON DELETE CASCADE,
    plot_label TEXT NOT NULL,
    experiment_plot_label TEXT,
    treatment_unit_label TEXT,
    block INTEGER NOT NULL,
    replicate INTEGER NOT NULL,
    treatment_label TEXT NOT NULL,
    male_sowing_offset_days INTEGER NOT NULL,
    sowing_density_plants_ha REAL,
    female_parent TEXT,
    male_parent TEXT,
    parent_combination TEXT,
    variety_genotype TEXT,
    sowing_date TEXT,
    factor_levels_json TEXT,
    female_sowing_date TEXT NOT NULL,
    male_sowing_date TEXT NOT NULL,
    geometry_json TEXT NOT NULL,
    area_ha REAL,
    centroid_lat REAL,
    centroid_lon REAL,
    created_at TEXT NOT NULL,
    UNIQUE(trial_id, plot_label)
);
CREATE TABLE IF NOT EXISTS flowering_observations (
    observation_id TEXT PRIMARY KEY,
    trial_id TEXT NOT NULL REFERENCES trials(trial_id) ON DELETE CASCADE,
    plot_id TEXT NOT NULL REFERENCES plots(plot_id) ON DELETE CASCADE,
    observation_date TEXT NOT NULL,
    male_plants_assessed INTEGER,
    male_shedding_percent REAL,
    male_pollen_intensity REAL,
    female_plants_assessed INTEGER,
    female_silking_percent REAL,
    female_receptive_percent REAL,
    crop_stress_score REAL,
    male_plant_height_cm REAL,
    female_plant_height_cm REAL,
    detasselling_complete INTEGER,
    notes TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(plot_id, observation_date)
);
CREATE TABLE IF NOT EXISTS plot_phenology_events (
    event_id TEXT PRIMARY KEY,
    trial_id TEXT NOT NULL REFERENCES trials(trial_id) ON DELETE CASCADE,
    plot_id TEXT NOT NULL REFERENCES plots(plot_id) ON DELETE CASCADE,
    male_flowering_initiation_date TEXT,
    male_flowering_date TEXT,
    female_flowering_initiation_date TEXT,
    female_flowering_date TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(plot_id)
);
CREATE TABLE IF NOT EXISTS harvest_outcomes (
    harvest_id TEXT PRIMARY KEY,
    trial_id TEXT NOT NULL REFERENCES trials(trial_id) ON DELETE CASCADE,
    plot_id TEXT NOT NULL REFERENCES plots(plot_id) ON DELETE CASCADE,
    harvest_date TEXT,
    ears_harvested REAL,
    kernels_per_ear REAL,
    kernel_rows_per_ear REAL,
    filled_kernels REAL,
    unfilled_kernels REAL,
    seed_set_percent REAL,
    seed_yield_kg_plot REAL,
    seed_yield_t_ha REAL,
    thousand_kernel_weight_g REAL,
    germination_percent REAL,
    genetic_purity_percent REAL,
    pure_seed_percent REAL,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(plot_id)
);
CREATE TABLE IF NOT EXISTS parent_physiology (
    physiology_id TEXT PRIMARY KEY,
    parent_name TEXT NOT NULL,
    role TEXT NOT NULL,
    tln REAL NOT NULL,
    coblf REAL NOT NULL,
    eb_r1_g REAL NOT NULL,
    tln_sd REAL NOT NULL,
    coblf_sd REAL NOT NULL,
    eb_r1_sd REAL NOT NULL,
    method TEXT NOT NULL,
    source TEXT,
    sample_size INTEGER,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(parent_name, role)
);
CREATE TABLE IF NOT EXISTS leaf_development_observations (
    leaf_observation_id TEXT PRIMARY KEY,
    trial_id TEXT NOT NULL REFERENCES trials(trial_id) ON DELETE CASCADE,
    plot_id TEXT NOT NULL REFERENCES plots(plot_id) ON DELETE CASCADE,
    observation_date TEXT NOT NULL,
    plant_tag TEXT NOT NULL,
    parent_role TEXT NOT NULL DEFAULT 'Female',
    collared_leaf_number REAL,
    final_total_leaf_number REAL,
    ear_biomass_g REAL,
    ear_length_mm REAL,
    developmental_stage TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(plot_id, observation_date, plant_tag)
);
CREATE TABLE IF NOT EXISTS weather_daily (
    trial_id TEXT NOT NULL REFERENCES trials(trial_id) ON DELETE CASCADE,
    weather_date TEXT NOT NULL,
    tmin_c REAL,
    tmax_c REAL,
    tmean_c REAL,
    precipitation_mm REAL,
    solar_radiation_mj_m2 REAL,
    reference_et_mm REAL,
    gdd_daily REAL,
    source TEXT,
    PRIMARY KEY(trial_id, weather_date)
);
CREATE TABLE IF NOT EXISTS satellite_links (
    link_id TEXT PRIMARY KEY,
    trial_id TEXT NOT NULL REFERENCES trials(trial_id) ON DELETE CASCADE,
    target_label TEXT NOT NULL,
    plot_ids_json TEXT NOT NULL,
    geometry_hash TEXT NOT NULL,
    geometry_json TEXT NOT NULL,
    processing_metadata_json TEXT,
    time_series_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS model_runs (
    run_id TEXT PRIMARY KEY,
    trial_id TEXT NOT NULL REFERENCES trials(trial_id) ON DELETE CASCADE,
    target TEXT NOT NULL,
    grouping TEXT,
    settings_json TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    predictions_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS experiment_protocols (
    protocol_id TEXT PRIMARY KEY,
    trial_id TEXT NOT NULL UNIQUE REFERENCES trials(trial_id) ON DELETE CASCADE,
    objective TEXT,
    hypotheses TEXT,
    primary_outcome TEXT,
    secondary_outcomes_json TEXT,
    planned_analysis TEXT,
    design_notes TEXT,
    protocol_version INTEGER NOT NULL DEFAULT 1,
    locked_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS experiment_protocol_versions (
    protocol_version_id TEXT PRIMARY KEY,
    protocol_id TEXT NOT NULL,
    trial_id TEXT NOT NULL REFERENCES trials(trial_id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    objective TEXT,
    hypotheses TEXT,
    primary_outcome TEXT,
    secondary_outcomes_json TEXT,
    planned_analysis TEXT,
    design_notes TEXT,
    locked_at TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(trial_id, version_number)
);
CREATE TABLE IF NOT EXISTS trial_factor_definitions (
    factor_id TEXT PRIMARY KEY,
    trial_id TEXT NOT NULL REFERENCES trials(trial_id) ON DELETE CASCADE,
    factor_name TEXT NOT NULL,
    factor_type TEXT NOT NULL,
    role TEXT,
    levels_json TEXT,
    unit TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(trial_id, factor_name)
);
CREATE TABLE IF NOT EXISTS design_versions (
    design_version_id TEXT PRIMARY KEY,
    trial_id TEXT NOT NULL REFERENCES trials(trial_id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    random_seed INTEGER,
    algorithm TEXT NOT NULL,
    constraints_json TEXT,
    factor_matrix_json TEXT,
    allocation_manifest_json TEXT,
    status TEXT NOT NULL DEFAULT 'Draft',
    created_at TEXT NOT NULL,
    UNIQUE(trial_id, version_number)
);
CREATE TABLE IF NOT EXISTS trial_measurement_requirements (
    requirement_id TEXT PRIMARY KEY,
    trial_id TEXT NOT NULL REFERENCES trials(trial_id) ON DELETE CASCADE,
    protocol_id TEXT,
    measurement_name TEXT NOT NULL,
    timing_label TEXT,
    due_date TEXT,
    scope TEXT NOT NULL DEFAULT 'Experimental unit',
    required INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS trial_audit_log (
    audit_id TEXT PRIMARY KEY,
    trial_id TEXT REFERENCES trials(trial_id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    user_name TEXT,
    details_json TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_plots_trial ON plots(trial_id);
CREATE INDEX IF NOT EXISTS idx_obs_trial_date ON flowering_observations(trial_id, observation_date);
CREATE INDEX IF NOT EXISTS idx_phenology_trial ON plot_phenology_events(trial_id);
CREATE INDEX IF NOT EXISTS idx_harvest_trial ON harvest_outcomes(trial_id);
CREATE INDEX IF NOT EXISTS idx_leaf_trial_date ON leaf_development_observations(trial_id, observation_date);
CREATE INDEX IF NOT EXISTS idx_parent_physiology_name ON parent_physiology(parent_name, role);
CREATE INDEX IF NOT EXISTS idx_satellite_trial ON satellite_links(trial_id);
CREATE INDEX IF NOT EXISTS idx_protocol_trial ON experiment_protocols(trial_id);
CREATE INDEX IF NOT EXISTS idx_protocol_versions_trial ON experiment_protocol_versions(trial_id, version_number);
CREATE INDEX IF NOT EXISTS idx_factor_trial ON trial_factor_definitions(trial_id);
CREATE INDEX IF NOT EXISTS idx_design_version_trial ON design_versions(trial_id, version_number);
CREATE INDEX IF NOT EXISTS idx_measurement_requirement_trial ON trial_measurement_requirements(trial_id);
CREATE INDEX IF NOT EXISTS idx_trial_audit ON trial_audit_log(trial_id, created_at);
"""


@dataclass
class PollinationDatabase:
    path: Path

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialise()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def initialise(self) -> None:
        with closing(self.connect()) as connection:
            connection.executescript(SCHEMA_SQL)
            self._migrate_schema(connection)
            connection.execute(
                "INSERT OR REPLACE INTO metadata(key, value) VALUES(?, ?)",
                ("schema_version", DB_SCHEMA_VERSION),
            )

    @staticmethod
    def _column_names(connection: sqlite3.Connection, table: str) -> set[str]:
        return {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}

    @classmethod
    def _ensure_column(cls, connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        if column not in cls._column_names(connection, table):
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    @classmethod
    def _migrate_schema(cls, connection: sqlite3.Connection) -> None:
        """Upgrade existing Release 5/6 databases without deleting user data."""
        cls._ensure_column(connection, "flowering_observations", "male_plant_height_cm", "REAL")
        cls._ensure_column(connection, "flowering_observations", "female_plant_height_cm", "REAL")
        cls._ensure_column(connection, "harvest_outcomes", "kernel_rows_per_ear", "REAL")
        cls._ensure_column(connection, "harvest_outcomes", "pure_seed_percent", "REAL")
        cls._ensure_column(connection, "trials", "source_field_id", "TEXT")
        cls._ensure_column(connection, "trials", "source_field_geometry_hash", "TEXT")
        cls._ensure_column(connection, "trials", "source_field_snapshot_json", "TEXT")
        cls._ensure_column(connection, "trials", "boundary_mode", "TEXT")
        cls._ensure_column(connection, "trials", "status", "TEXT NOT NULL DEFAULT 'Active'")
        cls._ensure_column(connection, "trials", "female_parent_levels_json", "TEXT")
        cls._ensure_column(connection, "trials", "male_parent_levels_json", "TEXT")
        cls._ensure_column(connection, "trials", "parent_pairings_json", "TEXT")
        cls._ensure_column(connection, "trials", "parent_pairing_mode", "TEXT")
        cls._ensure_column(connection, "trials", "sowing_density_levels_json", "TEXT")
        cls._ensure_column(connection, "trials", "sowing_date_levels_json", "TEXT")
        cls._ensure_column(connection, "trials", "sowing_offset_levels_json", "TEXT")
        cls._ensure_column(connection, "plots", "experiment_plot_label", "TEXT")
        cls._ensure_column(connection, "plots", "treatment_unit_label", "TEXT")
        cls._ensure_column(connection, "plots", "sowing_density_plants_ha", "REAL")
        cls._ensure_column(connection, "plots", "female_parent", "TEXT")
        cls._ensure_column(connection, "plots", "male_parent", "TEXT")
        cls._ensure_column(connection, "plots", "parent_combination", "TEXT")
        cls._ensure_column(connection, "plots", "variety_genotype", "TEXT")
        cls._ensure_column(connection, "plots", "sowing_date", "TEXT")
        cls._ensure_column(connection, "plots", "factor_levels_json", "TEXT")
        cls._ensure_column(connection, "leaf_development_observations", "parent_role", "TEXT NOT NULL DEFAULT 'Female'")
        connection.execute("UPDATE trials SET status='Active' WHERE status IS NULL OR TRIM(status)=''")
        legacy_trials = connection.execute(
            "SELECT trial_id, female_parent, male_parent, female_sowing_date, planting_density_plants_ha, "
            "female_parent_levels_json, male_parent_levels_json, parent_pairings_json, parent_pairing_mode, "
            "sowing_density_levels_json, sowing_date_levels_json, sowing_offset_levels_json FROM trials"
        ).fetchall()
        for legacy in legacy_trials:
            female = str(legacy[1] or "").strip()
            male = str(legacy[2] or "").strip()
            updates = {
                "female_parent_levels_json": legacy[5] or _json([female] if female else []),
                "male_parent_levels_json": legacy[6] or _json([male] if male else []),
                "parent_pairings_json": legacy[7] or _json([{
                    "female_parent": female, "male_parent": male,
                    "parent_combination": f"{female} × {male}".strip(" ×"),
                }]),
                "parent_pairing_mode": legacy[8] or "Legacy single pairing",
                "sowing_density_levels_json": legacy[9] or _json([legacy[4]] if legacy[4] is not None else []),
                "sowing_date_levels_json": legacy[10] or _json([str(legacy[3])] if legacy[3] else []),
                "sowing_offset_levels_json": legacy[11] or _json([0]),
            }
            connection.execute(
                """UPDATE trials SET female_parent_levels_json=?, male_parent_levels_json=?, parent_pairings_json=?,
                   parent_pairing_mode=?, sowing_density_levels_json=?, sowing_date_levels_json=?,
                   sowing_offset_levels_json=? WHERE trial_id=?""",
                (updates["female_parent_levels_json"], updates["male_parent_levels_json"],
                 updates["parent_pairings_json"], updates["parent_pairing_mode"],
                 updates["sowing_density_levels_json"], updates["sowing_date_levels_json"],
                 updates["sowing_offset_levels_json"], legacy[0]),
            )
        connection.execute("UPDATE plots SET experiment_plot_label='B' || printf('%02d', block) WHERE experiment_plot_label IS NULL OR TRIM(experiment_plot_label)=''")
        connection.execute("UPDATE plots SET treatment_unit_label=plot_label WHERE treatment_unit_label IS NULL OR TRIM(treatment_unit_label)=''")
        connection.execute("UPDATE plots SET sowing_date=female_sowing_date WHERE sowing_date IS NULL OR TRIM(sowing_date)=''")
        connection.execute("UPDATE plots SET female_parent=(SELECT female_parent FROM trials WHERE trials.trial_id=plots.trial_id) WHERE female_parent IS NULL OR TRIM(female_parent)=''")
        connection.execute("UPDATE plots SET male_parent=(SELECT male_parent FROM trials WHERE trials.trial_id=plots.trial_id) WHERE male_parent IS NULL OR TRIM(male_parent)=''")
        connection.execute("UPDATE plots SET parent_combination=COALESCE(NULLIF(variety_genotype,''), female_parent || ' × ' || male_parent) WHERE parent_combination IS NULL OR TRIM(parent_combination)=''")
        connection.execute("UPDATE plots SET variety_genotype=parent_combination WHERE variety_genotype IS NULL OR TRIM(variety_genotype)=''")

    def upsert_parent(self, name: str, role: str, maturity_notes: str = "", source: str = "") -> str:
        name = str(name).strip()
        if not name:
            raise PollinationLabError("Parent-line name is required.")
        now = utc_now()
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT parent_id FROM parent_lines WHERE name = ?", (name,)).fetchone()
            parent_id = row["parent_id"] if row else str(uuid.uuid4())
            connection.execute(
                """
                INSERT INTO parent_lines(parent_id, name, role, maturity_notes, source, created_at, updated_at)
                VALUES(?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    role=excluded.role,
                    maturity_notes=excluded.maturity_notes,
                    source=excluded.source,
                    updated_at=excluded.updated_at
                """,
                (parent_id, name, role, maturity_notes, source, now, now),
            )
        return parent_id

    def list_parents(self) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            return pd.read_sql_query("SELECT * FROM parent_lines ORDER BY name", connection)

    def upsert_parent_physiology(
        self,
        parent_name: str,
        role: str,
        parameters: PhysiologyParameters | Mapping[str, Any],
        *,
        method: str = "User-entered informative prior",
        source: str = "",
        sample_size: int | None = None,
        notes: str = "",
    ) -> str:
        parent_name = str(parent_name or "").strip()
        role = "Male" if str(role).strip().casefold().startswith("m") else "Female"
        if not parent_name:
            raise PollinationLabError("Parent-line name is required for physiology parameters.")
        params = parameters if isinstance(parameters, PhysiologyParameters) else physiology_from_mapping(parameters)
        values = params.validated().to_record()
        sample_value = pd.to_numeric(pd.Series([sample_size]), errors="coerce").iloc[0]
        sample_value = int(sample_value) if pd.notna(sample_value) else None
        now = utc_now()
        with closing(self.connect()) as connection:
            existing = connection.execute(
                "SELECT physiology_id, created_at FROM parent_physiology WHERE parent_name=? AND role=?",
                (parent_name, role),
            ).fetchone()
            physiology_id = str(existing["physiology_id"]) if existing else str(uuid.uuid4())
            created_at = str(existing["created_at"]) if existing else now
            connection.execute(
                """
                INSERT INTO parent_physiology(
                    physiology_id, parent_name, role, tln, coblf, eb_r1_g,
                    tln_sd, coblf_sd, eb_r1_sd, method, source, sample_size,
                    notes, created_at, updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(parent_name, role) DO UPDATE SET
                    tln=excluded.tln, coblf=excluded.coblf, eb_r1_g=excluded.eb_r1_g,
                    tln_sd=excluded.tln_sd, coblf_sd=excluded.coblf_sd,
                    eb_r1_sd=excluded.eb_r1_sd, method=excluded.method,
                    source=excluded.source, sample_size=excluded.sample_size,
                    notes=excluded.notes, updated_at=excluded.updated_at
                """,
                (
                    physiology_id, parent_name, role, values["tln"], values["coblf"], values["eb_r1_g"],
                    values["tln_sd"], values["coblf_sd"], values["eb_r1_sd"], str(method), str(source),
                    sample_value, str(notes), created_at, now,
                ),
            )
        return physiology_id

    def parent_physiology(self, parent_names: Sequence[str] | None = None) -> pd.DataFrame:
        query = """
            SELECT physiology_id AS 'Physiology ID', parent_name AS 'Parent line', role AS 'Role',
                   tln AS 'tln', coblf AS 'coblf', eb_r1_g AS 'eb_r1_g',
                   tln_sd AS 'tln_sd', coblf_sd AS 'coblf_sd', eb_r1_sd AS 'eb_r1_sd',
                   method AS 'Method', source AS 'Source', sample_size AS 'Sample size',
                   notes AS 'Notes', updated_at AS 'Updated'
            FROM parent_physiology
        """
        params: tuple[Any, ...] = ()
        if parent_names:
            cleaned = [str(value) for value in parent_names if str(value).strip()]
            placeholders = ",".join("?" for _ in cleaned)
            query += f" WHERE parent_name IN ({placeholders})"
            params = tuple(cleaned)
        query += " ORDER BY role, parent_name"
        with closing(self.connect()) as connection:
            return pd.read_sql_query(query, connection, params=params)

    def physiology_for_parent(self, parent_name: str, role: str) -> PhysiologyParameters:
        frame = self.parent_physiology([parent_name])
        role_name = "Male" if str(role).strip().casefold().startswith("m") else "Female"
        selected = frame.loc[frame["Role"].astype(str).eq(role_name)] if not frame.empty else frame
        if selected.empty:
            return DEFAULT_PHYSIOLOGY
        return physiology_from_mapping(selected.iloc[0].to_dict())

    def create_trial(self, payload: Mapping[str, Any]) -> str:
        female_levels = _parse_text_levels(payload.get("female_parent_levels") or payload.get("female_parent") or "")
        male_levels = _parse_text_levels(payload.get("male_parent_levels") or payload.get("male_parent") or "")
        if not str(payload.get("name", "")).strip():
            raise PollinationLabError("Trial name is required.")
        if not female_levels or not male_levels:
            raise PollinationLabError("Enter at least one female parent line and one male parent line.")
        pairing_mode = str(payload.get("parent_pairing_mode") or PARENT_PAIRING_MODES[0])
        pairings_payload = payload.get("parent_pairings")
        pairings = build_parent_combinations(
            female_levels, male_levels, pairing_mode=pairing_mode, explicit_pairings=pairings_payload
        )
        density_levels = [float(value) for value in (payload.get("sowing_density_levels") or []) if value not in (None, "")]
        if not density_levels and payload.get("planting_density_plants_ha") not in (None, ""):
            density_levels = [float(payload.get("planting_density_plants_ha"))]
        sowing_date_levels = [str(value) for value in (payload.get("sowing_date_levels") or []) if str(value).strip()]
        if not sowing_date_levels and payload.get("female_sowing_date"):
            sowing_date_levels = [str(payload.get("female_sowing_date"))]
        sowing_date_levels = _parse_date_levels(",".join(sowing_date_levels), date.today())
        offset_levels = [int(value) for value in (payload.get("sowing_offset_levels") or [0])]
        if not offset_levels:
            offset_levels = [0]
        trial_id = str(payload.get("trial_id") or uuid.uuid4())
        geometry = payload.get("field_geometry")
        area = lat = lon = None
        geometry_json = None
        if geometry is not None:
            geometry = validate_aoi_geometry(geometry)
            geometry_json = _json(geometry)
            area = geometry_area_hectares(geometry)
            lat, lon = geometry_centroid(geometry)
        source_snapshot = payload.get("source_field_snapshot")
        if source_snapshot is not None:
            source_snapshot = validate_aoi_geometry(source_snapshot)
        source_field_id = str(payload.get("source_field_id") or "").strip() or None
        source_hash = str(payload.get("source_field_geometry_hash") or "").strip() or None
        if source_snapshot is not None and not source_hash:
            source_hash = geometry_hash(source_snapshot)
        boundary_mode = str(payload.get("boundary_mode") or "Independent boundary").strip()
        primary_female = female_levels[0]
        primary_male = male_levels[0]
        primary_sowing = sowing_date_levels[0]
        primary_density = density_levels[0] if density_levels else None
        now = utc_now()
        with closing(self.connect()) as connection:
            connection.execute(
                """
                INSERT INTO trials(
                    trial_id, name, project_id, site_name, season_year, female_parent, male_parent,
                    female_parent_levels_json, male_parent_levels_json, parent_pairings_json, parent_pairing_mode,
                    sowing_density_levels_json, sowing_date_levels_json, sowing_offset_levels_json,
                    female_sowing_date, design_type, blocks, replicates_per_treatment, row_ratio,
                    planting_density_plants_ha, primary_outcome, base_temperature_c,
                    upper_temperature_c, field_geometry_json, field_area_ha, centroid_lat,
                    centroid_lon, source_field_id, source_field_geometry_hash,
                    source_field_snapshot_json, boundary_mode, status, notes, created_at, updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    trial_id, str(payload["name"]), payload.get("project_id"), payload.get("site_name"),
                    int(payload.get("season_year") or pd.Timestamp(primary_sowing).year),
                    primary_female, primary_male, _json(female_levels), _json(male_levels), _json(pairings), pairing_mode,
                    _json(density_levels), _json(sowing_date_levels), _json(offset_levels), primary_sowing,
                    str(payload.get("design_type", "Randomised complete block")), int(payload.get("blocks", 3)),
                    int(payload.get("replicates_per_treatment", 1)), str(payload.get("row_ratio", "4 female : 2 male")),
                    primary_density, str(payload.get("primary_outcome", "Seed-set percentage")),
                    float(payload.get("base_temperature_c", 10.0)), float(payload.get("upper_temperature_c", 30.0)),
                    geometry_json, area, lat, lon, source_field_id, source_hash,
                    _json(source_snapshot) if source_snapshot is not None else None, boundary_mode,
                    str(payload.get("status", "Active")), str(payload.get("notes", "")), now, now,
                ),
            )
        for parent in female_levels:
            self.upsert_parent(parent, "Female")
        for parent in male_levels:
            self.upsert_parent(parent, "Male")
        return trial_id

    @staticmethod
    def _normalise_factor_design(
        *,
        female_parent_levels: Sequence[str],
        male_parent_levels: Sequence[str],
        parent_pairings: Sequence[Mapping[str, Any]],
        parent_pairing_mode: str,
        sowing_density_levels: Sequence[float],
        sowing_date_levels: Sequence[str],
        sowing_offset_levels: Sequence[int],
    ) -> dict[str, Any]:
        females = _parse_text_levels(female_parent_levels)
        males = _parse_text_levels(male_parent_levels)
        pairings = build_parent_combinations(
            females, males, pairing_mode=parent_pairing_mode, explicit_pairings=parent_pairings
        )
        densities = [float(value) for value in sowing_density_levels]
        dates = _parse_date_levels(",".join(str(value) for value in sowing_date_levels), date.today())
        offsets = [int(value) for value in sowing_offset_levels]
        if not dates or not offsets:
            raise PollinationLabError("At least one sowing date and one sowing-date difference are required.")
        return {
            "females": females, "males": males, "pairings": pairings,
            "pairing_mode": str(parent_pairing_mode), "densities": densities,
            "dates": dates, "offsets": offsets,
        }

    @staticmethod
    def _factor_signature_from_trial(trial: Mapping[str, Any]) -> str:
        payload = {
            "females": list(trial.get("female_parent_levels") or []),
            "males": list(trial.get("male_parent_levels") or []),
            "pairings": list(trial.get("parent_pairings") or []),
            "pairing_mode": str(trial.get("parent_pairing_mode") or ""),
            "densities": [float(value) for value in (trial.get("sowing_density_levels") or [])],
            "dates": [str(value) for value in (trial.get("sowing_date_levels") or [])],
            "offsets": [int(value) for value in (trial.get("sowing_offset_levels") or [])],
        }
        return _json(payload)

    @staticmethod
    def _factor_signature(normalised: Mapping[str, Any]) -> str:
        payload = {
            "females": list(normalised["females"]), "males": list(normalised["males"]),
            "pairings": list(normalised["pairings"]), "pairing_mode": str(normalised["pairing_mode"]),
            "densities": [float(value) for value in normalised["densities"]],
            "dates": [str(value) for value in normalised["dates"]],
            "offsets": [int(value) for value in normalised["offsets"]],
        }
        return _json(payload)

    @staticmethod
    def _apply_factor_design(connection: sqlite3.Connection, trial_id: str, design: Mapping[str, Any]) -> None:
        exists = connection.execute("SELECT 1 FROM trials WHERE trial_id=?", (trial_id,)).fetchone()
        if not exists:
            raise PollinationLabError("Trial not found.")
        connection.execute(
            """UPDATE trials SET female_parent=?, male_parent=?, female_parent_levels_json=?,
               male_parent_levels_json=?, parent_pairings_json=?, parent_pairing_mode=?,
               sowing_density_levels_json=?, sowing_date_levels_json=?, sowing_offset_levels_json=?,
               female_sowing_date=?, planting_density_plants_ha=?, updated_at=? WHERE trial_id=?""",
            (
                design["females"][0], design["males"][0], _json(design["females"]), _json(design["males"]),
                _json(design["pairings"]), design["pairing_mode"], _json(design["densities"]),
                _json(design["dates"]), _json(design["offsets"]), design["dates"][0],
                design["densities"][0] if design["densities"] else None, utc_now(), trial_id,
            ),
        )
        now = utc_now()
        for name, role in [(name, "Female") for name in design["females"]] + [(name, "Male") for name in design["males"]]:
            row = connection.execute("SELECT parent_id, created_at FROM parent_lines WHERE name=?", (name,)).fetchone()
            parent_id = str(row["parent_id"]) if row else str(uuid.uuid4())
            created_at = str(row["created_at"]) if row else now
            connection.execute(
                """INSERT INTO parent_lines(parent_id,name,role,maturity_notes,source,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?)
                   ON CONFLICT(name) DO UPDATE SET role=excluded.role, updated_at=excluded.updated_at""",
                (parent_id, name, role, "", "", created_at, now),
            )

    def update_trial_factor_design(
        self,
        trial_id: str,
        *,
        female_parent_levels: Sequence[str],
        male_parent_levels: Sequence[str],
        parent_pairings: Sequence[Mapping[str, Any]],
        parent_pairing_mode: str,
        sowing_density_levels: Sequence[float],
        sowing_date_levels: Sequence[str],
        sowing_offset_levels: Sequence[int],
    ) -> None:
        design = self._normalise_factor_design(
            female_parent_levels=female_parent_levels, male_parent_levels=male_parent_levels,
            parent_pairings=parent_pairings, parent_pairing_mode=parent_pairing_mode,
            sowing_density_levels=sowing_density_levels, sowing_date_levels=sowing_date_levels,
            sowing_offset_levels=sowing_offset_levels,
        )
        trial = self.get_trial(trial_id)
        with closing(self.connect()) as connection:
            plot_count = int(connection.execute("SELECT COUNT(*) FROM plots WHERE trial_id=?", (trial_id,)).fetchone()[0])
            if plot_count and self._factor_signature(design) != self._factor_signature_from_trial(trial):
                raise PollinationLabError(
                    "This trial already has a saved treatment-unit map. Changing factor levels separately would make the "
                    "declared design disagree with the mapped assignments. Change the levels in Plot map & randomisation "
                    "and save the new randomisation atomically instead."
                )
            connection.execute("BEGIN IMMEDIATE")
            try:
                self._apply_factor_design(connection, trial_id, design)
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise

    def update_trial_geometry(self, trial_id: str, geometry: Mapping[str, Any]) -> None:
        geometry = validate_aoi_geometry(geometry)
        area = geometry_area_hectares(geometry)
        lat, lon = geometry_centroid(geometry)
        with closing(self.connect()) as connection:
            connection.execute(
                "UPDATE trials SET field_geometry_json=?, field_area_ha=?, centroid_lat=?, centroid_lon=?, updated_at=? WHERE trial_id=?",
                (_json(geometry), area, lat, lon, utc_now(), trial_id),
            )

    def update_trial_spatial_link(
        self,
        trial_id: str,
        *,
        source_field_id: str,
        source_field_geometry: Mapping[str, Any],
        boundary_mode: str,
        trial_geometry: Mapping[str, Any] | None = None,
    ) -> None:
        """Link a trial to a mapped field without invalidating saved experimental units.

        The field/trial relationship is validated *before* anything is committed. If
        treatment-unit polygons already exist, every one of them must remain contained
        by the proposed trial boundary; otherwise the re-link is rejected and the
        existing spatial state is left unchanged.
        """
        source_geometry = validate_aoi_geometry(source_field_geometry)
        mode = str(boundary_mode or "Exact mapped field").strip()
        if mode not in {"Exact mapped field", "Field subsection"}:
            raise PollinationLabError(f"Unknown trial boundary mode: {boundary_mode}")
        geometry = source_geometry if mode == "Exact mapped field" else validate_aoi_geometry(trial_geometry or source_geometry)
        if shape is None:
            raise PollinationLabError("Shapely is required to verify safe trial spatial linkage.")
        if mode == "Field subsection" and not shape(source_geometry).buffer(1e-10).covers(shape(geometry)):
            raise PollinationLabError("The trial subsection extends outside the selected mapped field.")
        area = geometry_area_hectares(geometry)
        lat, lon = geometry_centroid(geometry)
        with closing(self.connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                exists = connection.execute("SELECT 1 FROM trials WHERE trial_id=?", (trial_id,)).fetchone()
                if not exists:
                    raise PollinationLabError("Trial not found.")
                saved_plots = connection.execute(
                    "SELECT plot_label, geometry_json FROM plots WHERE trial_id=? ORDER BY plot_label", (trial_id,)
                ).fetchall()
                outside_labels: list[str] = []
                target_shape = shape(geometry).buffer(1e-10)
                for row in saved_plots:
                    plot_geometry = _loads(row["geometry_json"], None)
                    if not plot_geometry or not target_shape.covers(shape(validate_aoi_geometry(plot_geometry))):
                        outside_labels.append(str(row["plot_label"]))
                if outside_labels:
                    preview = ", ".join(outside_labels[:8])
                    suffix = "" if len(outside_labels) <= 8 else f" (+{len(outside_labels) - 8} more)"
                    raise PollinationLabError(
                        f"Spatial re-link blocked: {len(outside_labels)} saved treatment unit(s) would fall outside "
                        f"the proposed trial boundary ({preview}{suffix}). Keep the current boundary or deliberately "
                        "create/rebuild a compatible plot map before changing the trial's spatial parent."
                    )
                connection.execute(
                    """UPDATE trials SET field_geometry_json=?, field_area_ha=?, centroid_lat=?, centroid_lon=?,
                       source_field_id=?, source_field_geometry_hash=?, source_field_snapshot_json=?,
                       boundary_mode=?, updated_at=? WHERE trial_id=?""",
                    (
                        _json(geometry), area, lat, lon, str(source_field_id), geometry_hash(source_geometry),
                        _json(source_geometry), mode, utc_now(), trial_id,
                    ),
                )
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise

    def spatial_link_status(self, trial_id: str, field: Mapping[str, Any] | None) -> dict[str, Any]:
        trial = self.get_trial(trial_id)
        trial_geometry = trial.get("field_geometry")
        field_geometry = (field or {}).get("geometry")
        current_hash = geometry_hash(field_geometry) if field_geometry else None
        trial_hash = geometry_hash(trial_geometry) if trial_geometry else None
        source_hash = trial.get("source_field_geometry_hash")
        contained = None
        if trial_geometry and field_geometry and shape is not None:
            try:
                contained = bool(shape(field_geometry).buffer(1e-10).covers(shape(trial_geometry)))
            except Exception:
                contained = None
        return {
            "trial_geometry_hash": trial_hash,
            "source_geometry_hash": source_hash,
            "current_field_geometry_hash": current_hash,
            "exact_match": bool(trial_hash and current_hash and trial_hash == current_hash),
            "source_changed": bool(source_hash and current_hash and source_hash != current_hash),
            "trial_inside_field": contained,
            "boundary_mode": trial.get("boundary_mode") or "Independent boundary",
        }

    def list_trials(self) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            frame = pd.read_sql_query(
                """
                SELECT trial_id AS 'Trial ID', name AS 'Trial', site_name AS 'Site', season_year AS 'Year',
                       female_parent AS 'Female parent', male_parent AS 'Male parent',
                       female_parent_levels_json, male_parent_levels_json, parent_pairings_json,
                       female_sowing_date AS 'Female sowing', blocks AS 'Blocks',
                       primary_outcome AS 'Primary outcome', field_area_ha AS 'Field area (ha)',
                       source_field_id AS 'Source field ID', boundary_mode AS 'Boundary mode',
                       status AS 'Status', updated_at AS 'Updated'
                FROM trials ORDER BY updated_at DESC
                """,
                connection,
            )
        if not frame.empty:
            frame["Female lines"] = frame.apply(
                lambda row: ", ".join(_loads(row.get("female_parent_levels_json"), [row.get("Female parent")]) or []), axis=1
            )
            frame["Male lines"] = frame.apply(
                lambda row: ", ".join(_loads(row.get("male_parent_levels_json"), [row.get("Male parent")]) or []), axis=1
            )
            frame["Parent combinations"] = frame["parent_pairings_json"].map(lambda value: len(_loads(value, []) or []))
            frame = frame.drop(columns=["female_parent_levels_json", "male_parent_levels_json", "parent_pairings_json"])
        return frame

    def get_trial(self, trial_id: str) -> dict[str, Any]:
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT * FROM trials WHERE trial_id=?", (trial_id,)).fetchone()
        if row is None:
            raise PollinationLabError("Trial not found.")
        payload = dict(row)
        payload["field_geometry"] = _loads(payload.pop("field_geometry_json"), None)
        payload["source_field_snapshot"] = _loads(payload.pop("source_field_snapshot_json", None), None)
        payload["female_parent_levels"] = _loads(payload.pop("female_parent_levels_json", None), None) or [payload.get("female_parent")]
        payload["male_parent_levels"] = _loads(payload.pop("male_parent_levels_json", None), None) or [payload.get("male_parent")]
        payload["parent_pairings"] = _loads(payload.pop("parent_pairings_json", None), None) or build_parent_combinations(
            payload["female_parent_levels"], payload["male_parent_levels"], pairing_mode="Match lines by position"
        )
        payload["sowing_density_levels"] = _loads(payload.pop("sowing_density_levels_json", None), None)
        if not payload["sowing_density_levels"] and payload.get("planting_density_plants_ha") is not None:
            payload["sowing_density_levels"] = [payload.get("planting_density_plants_ha")]
        payload["sowing_date_levels"] = _loads(payload.pop("sowing_date_levels_json", None), None) or [payload.get("female_sowing_date")]
        payload["sowing_offset_levels"] = _loads(payload.pop("sowing_offset_levels_json", None), None) or [0]
        payload["parent_pairing_mode"] = payload.get("parent_pairing_mode") or "Legacy single pairing"
        return payload

    def update_trial_status(self, trial_id: str, status: str) -> None:
        allowed = {"Draft", "Designed", "Randomised", "Field-Ready", "Data Collection", "Completed", "Analysed", "Archived", "Planned", "Active"}
        clean = str(status or "Active").strip().title()
        if clean not in allowed:
            raise PollinationLabError(f"Unknown trial status: {status}")
        with closing(self.connect()) as connection:
            connection.execute("UPDATE trials SET status=?, updated_at=? WHERE trial_id=?", (clean, utc_now(), trial_id))

    def update_trial_design_settings(self, trial_id: str, *, design_type: str, blocks: int, replicates_per_treatment: int, user_name: str = "") -> None:
        """Update declared design settings only before plot-linked research data lock the allocation."""
        allowed = {
            "Completely randomised", "Randomised complete block", "Factorial RCBD",
            "Split-plot", "Strip-plot", "Incomplete block / lattice", "Custom",
        }
        design = str(design_type).strip()
        if design not in allowed:
            raise PollinationLabError(f"Unsupported design family: {design}")
        blocks_i = int(blocks)
        reps_i = int(replicates_per_treatment)
        if blocks_i < 1 or reps_i < 1:
            raise PollinationLabError("Blocks and replicates per treatment must both be at least 1.")
        current = self.get_trial(trial_id)
        changed = (
            str(current.get("design_type") or "") != design
            or int(current.get("blocks") or 0) != blocks_i
            or int(current.get("replicates_per_treatment") or 0) != reps_i
        )
        if changed and not self.list_plots(trial_id).empty:
            raise PollinationLabError(
                "Design settings cannot be changed while a mapped randomisation exists. Remove/rebuild the allocation deliberately before field data collection, "
                "or clone/create a new design version; AGROLATTICE will not silently make the factor declaration disagree with saved experimental units."
            )
        dependencies = {k: v for k, v in self.trial_plot_dependency_counts(trial_id).items() if v}
        if changed and dependencies:
            detail = ", ".join(f"{k}: {v}" for k, v in dependencies.items())
            raise PollinationLabError(
                "Design settings are locked because plot-linked research data already exist (" + detail + "). "
                "Create a new experiment/design version rather than changing the declared randomisation structure."
            )
        with closing(self.connect()) as connection:
            connection.execute(
                "UPDATE trials SET design_type=?, blocks=?, replicates_per_treatment=?, updated_at=? WHERE trial_id=?",
                (design, blocks_i, reps_i, utc_now(), trial_id),
            )
        self.audit_trial(
            trial_id, "design_settings_updated", "trial", trial_id, user_name=user_name,
            details={"design_type": design, "blocks": blocks_i, "replicates_per_treatment": reps_i},
        )


    def audit_trial(self, trial_id: str | None, event_type: str, entity_type: str, entity_id: str | None = None, *, user_name: str = "", details: Mapping[str, Any] | None = None) -> str:
        audit_id = str(uuid.uuid4())
        with closing(self.connect()) as connection:
            connection.execute(
                "INSERT INTO trial_audit_log(audit_id,trial_id,event_type,entity_type,entity_id,user_name,details_json,created_at) VALUES(?,?,?,?,?,?,?,?)",
                (audit_id, trial_id, str(event_type), str(entity_type), entity_id, str(user_name), _json(dict(details or {})), utc_now()),
            )
        return audit_id

    def trial_audit(self, trial_id: str | None = None) -> pd.DataFrame:
        query = "SELECT * FROM trial_audit_log"
        params: tuple[Any, ...] = ()
        if trial_id:
            query += " WHERE trial_id=?"
            params = (trial_id,)
        query += " ORDER BY created_at DESC"
        with closing(self.connect()) as connection:
            frame = pd.read_sql_query(query, connection, params=params)
        if not frame.empty:
            frame["details"] = frame["details_json"].map(lambda value: _loads(value, {}))
        return frame

    def upsert_experiment_protocol(self, trial_id: str, *, objective: str = "", hypotheses: str = "", primary_outcome: str = "", secondary_outcomes: Sequence[str] | None = None, planned_analysis: str = "", design_notes: str = "", lock: bool = False, user_name: str = "") -> str:
        now = utc_now()
        with closing(self.connect()) as connection:
            existing = connection.execute("SELECT * FROM experiment_protocols WHERE trial_id=?", (trial_id,)).fetchone()
            protocol_id = str(existing["protocol_id"]) if existing else str(uuid.uuid4())
            version = (int(existing["protocol_version"] or 1) + 1) if existing else 1
            locked_at = (str(existing["locked_at"]) if existing and existing["locked_at"] else None)
            if lock and not locked_at:
                locked_at = now
            connection.execute(
                """INSERT INTO experiment_protocols(protocol_id,trial_id,objective,hypotheses,primary_outcome,secondary_outcomes_json,planned_analysis,design_notes,protocol_version,locked_at,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(trial_id) DO UPDATE SET objective=excluded.objective,hypotheses=excluded.hypotheses,primary_outcome=excluded.primary_outcome,
                   secondary_outcomes_json=excluded.secondary_outcomes_json,planned_analysis=excluded.planned_analysis,design_notes=excluded.design_notes,
                   protocol_version=excluded.protocol_version,locked_at=COALESCE(experiment_protocols.locked_at,excluded.locked_at),updated_at=excluded.updated_at""",
                (protocol_id, trial_id, str(objective), str(hypotheses), str(primary_outcome), _json(list(secondary_outcomes or [])), str(planned_analysis), str(design_notes), version, locked_at, str(existing["created_at"]) if existing else now, now),
            )
            connection.execute(
                """INSERT INTO experiment_protocol_versions(
                       protocol_version_id,protocol_id,trial_id,version_number,objective,hypotheses,primary_outcome,
                       secondary_outcomes_json,planned_analysis,design_notes,locked_at,created_at
                   ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (str(uuid.uuid4()), protocol_id, trial_id, version, str(objective), str(hypotheses),
                 str(primary_outcome), _json(list(secondary_outcomes or [])), str(planned_analysis),
                 str(design_notes), locked_at, now),
            )
        self.audit_trial(trial_id, "protocol_saved", "experiment_protocol", protocol_id, user_name=user_name, details={"version": version, "locked": bool(locked_at)})
        return protocol_id

    def experiment_protocol(self, trial_id: str) -> dict[str, Any] | None:
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT * FROM experiment_protocols WHERE trial_id=?", (trial_id,)).fetchone()
        if row is None:
            return None
        payload = dict(row)
        payload["secondary_outcomes"] = _loads(payload.pop("secondary_outcomes_json", None), [])
        return payload

    def protocol_versions(self, trial_id: str) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            frame = pd.read_sql_query(
                "SELECT * FROM experiment_protocol_versions WHERE trial_id=? ORDER BY version_number DESC",
                connection, params=(trial_id,),
            )
        if not frame.empty:
            frame["secondary_outcomes"] = frame["secondary_outcomes_json"].map(lambda value: _loads(value, []))
        return frame

    def save_factor_definitions(self, trial_id: str, factors: Sequence[Mapping[str, Any]], *, user_name: str = "") -> None:
        now = utc_now()
        cleaned: list[dict[str, Any]] = []
        for factor in factors:
            name = str(factor.get("factor_name") or factor.get("name") or "").strip()
            if not name:
                continue
            cleaned.append({
                "factor_id": str(factor.get("factor_id") or uuid.uuid4()), "factor_name": name,
                "factor_type": str(factor.get("factor_type") or factor.get("type") or "Categorical"),
                "role": str(factor.get("role") or "Treatment"), "levels": list(factor.get("levels") or []),
                "unit": str(factor.get("unit") or ""), "notes": str(factor.get("notes") or ""),
            })
        with closing(self.connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute("DELETE FROM trial_factor_definitions WHERE trial_id=?", (trial_id,))
                for factor in cleaned:
                    connection.execute(
                        "INSERT INTO trial_factor_definitions(factor_id,trial_id,factor_name,factor_type,role,levels_json,unit,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (factor["factor_id"], trial_id, factor["factor_name"], factor["factor_type"], factor["role"], _json(factor["levels"]), factor["unit"], factor["notes"], now, now),
                    )
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        self.audit_trial(trial_id, "factors_saved", "factor_definitions", trial_id, user_name=user_name, details={"count": len(cleaned)})

    def factor_definitions(self, trial_id: str) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            frame = pd.read_sql_query("SELECT * FROM trial_factor_definitions WHERE trial_id=? ORDER BY factor_name", connection, params=(trial_id,))
        if not frame.empty:
            frame["levels"] = frame["levels_json"].map(lambda value: _loads(value, []))
        return frame

    def save_design_version(self, trial_id: str, *, random_seed: int | None, algorithm: str, constraints: Mapping[str, Any] | None, factor_matrix: Sequence[Mapping[str, Any]] | None, allocation_manifest: Sequence[Mapping[str, Any]] | None, status: str = "Randomised", user_name: str = "") -> str:
        with closing(self.connect()) as connection:
            version = int(connection.execute("SELECT COALESCE(MAX(version_number),0)+1 FROM design_versions WHERE trial_id=?", (trial_id,)).fetchone()[0])
            design_id = str(uuid.uuid4())
            connection.execute(
                "INSERT INTO design_versions(design_version_id,trial_id,version_number,random_seed,algorithm,constraints_json,factor_matrix_json,allocation_manifest_json,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (design_id, trial_id, version, random_seed, str(algorithm), _json(dict(constraints or {})), _json(list(factor_matrix or [])), _json(list(allocation_manifest or [])), str(status), utc_now()),
            )
        self.audit_trial(trial_id, "design_version_saved", "design_version", design_id, user_name=user_name, details={"version": version, "algorithm": algorithm, "random_seed": random_seed})
        return design_id

    def design_versions(self, trial_id: str) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            frame = pd.read_sql_query("SELECT * FROM design_versions WHERE trial_id=? ORDER BY version_number DESC", connection, params=(trial_id,))
        for column in ("constraints_json", "factor_matrix_json", "allocation_manifest_json"):
            if not frame.empty and column in frame:
                frame[column.removesuffix("_json")] = frame[column].map(lambda value: _loads(value, [] if column != "constraints_json" else {}))
        return frame

    def save_measurement_requirement(self, trial_id: str, measurement_name: str, *, protocol_id: str | None = None, timing_label: str = "", due_date: str | None = None, scope: str = "Experimental unit", required: bool = True, notes: str = "", requirement_id: str | None = None, user_name: str = "") -> str:
        requirement_id = str(requirement_id or uuid.uuid4())
        now = utc_now()
        with closing(self.connect()) as connection:
            connection.execute(
                """INSERT INTO trial_measurement_requirements(requirement_id,trial_id,protocol_id,measurement_name,timing_label,due_date,scope,required,notes,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(requirement_id) DO UPDATE SET protocol_id=excluded.protocol_id,measurement_name=excluded.measurement_name,timing_label=excluded.timing_label,due_date=excluded.due_date,scope=excluded.scope,required=excluded.required,notes=excluded.notes,updated_at=excluded.updated_at""",
                (requirement_id, trial_id, protocol_id, str(measurement_name), str(timing_label), due_date, str(scope), 1 if required else 0, str(notes), now, now),
            )
        self.audit_trial(trial_id, "measurement_requirement_saved", "measurement_requirement", requirement_id, user_name=user_name, details={"measurement": measurement_name, "due_date": due_date})
        return requirement_id

    def measurement_requirements(self, trial_id: str) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            return pd.read_sql_query("SELECT * FROM trial_measurement_requirements WHERE trial_id=? ORDER BY due_date, measurement_name", connection, params=(trial_id,))

    def data_completeness_matrix(self, trial_id: str) -> pd.DataFrame:
        plots = self.list_plots(trial_id)
        if plots.empty:
            return pd.DataFrame()
        plot_ids = plots["Plot ID"].astype(str).tolist()
        obs = self.observations(trial_id)
        leaf = self.leaf_observations(trial_id)
        harvest = self.harvest(trial_id)
        phenology = self.phenology_events(trial_id)
        rows = []
        for _, plot in plots.iterrows():
            pid = str(plot["Plot ID"])
            rows.append({
                "Experimental unit": plot.get("Treatment unit") or plot.get("Plot"),
                "Plot": plot.get("Plot"),
                "Block": plot.get("Block"),
                "Flowering observations": int((obs.get("Plot ID", pd.Series(dtype=str)).astype(str) == pid).sum()) if not obs.empty else 0,
                "Tagged-plant observations": int((leaf.get("Plot ID", pd.Series(dtype=str)).astype(str) == pid).sum()) if not leaf.empty else 0,
                "Flowering dates": bool((phenology.get("Plot ID", pd.Series(dtype=str)).astype(str) == pid).any()) if not phenology.empty else False,
                "Harvest outcome": bool((harvest.get("Plot ID", pd.Series(dtype=str)).astype(str) == pid).any()) if not harvest.empty else False,
            })
        return pd.DataFrame(rows)

    def trial_plot_dependency_counts(self, trial_id: str) -> dict[str, int]:
        table_map = {
            "Flowering observations": "flowering_observations",
            "Flowering-date records": "plot_phenology_events",
            "Harvest outcomes": "harvest_outcomes",
            "Leaf/ear observations": "leaf_development_observations",
            "Satellite links": "satellite_links",
            "Model runs": "model_runs",
        }
        with closing(self.connect()) as connection:
            return {
                label: int(connection.execute(f"SELECT COUNT(*) FROM {table} WHERE trial_id=?", (trial_id,)).fetchone()[0])
                for label, table in table_map.items()
            }

    def trial_deletion_counts(self, trial_id: str) -> dict[str, int]:
        """Return every trial-scoped record class that a hard delete would remove."""
        table_map = {
            "Treatment units": "plots",
            "Flowering observations": "flowering_observations",
            "Flowering-date records": "plot_phenology_events",
            "Harvest outcomes": "harvest_outcomes",
            "Leaf/ear observations": "leaf_development_observations",
            "Daily weather rows": "weather_daily",
            "Satellite links": "satellite_links",
            "Model runs": "model_runs",
            "Experiment protocol": "experiment_protocols",
            "Protocol versions": "experiment_protocol_versions",
            "Factor definitions": "trial_factor_definitions",
            "Design versions": "design_versions",
            "Measurement requirements": "trial_measurement_requirements",
            "Audit events": "trial_audit_log",
        }
        with closing(self.connect()) as connection:
            exists = connection.execute("SELECT 1 FROM trials WHERE trial_id=?", (trial_id,)).fetchone()
            if not exists:
                raise PollinationLabError("Trial not found.")
            return {
                label: int(connection.execute(f"SELECT COUNT(*) FROM {table} WHERE trial_id=?", (trial_id,)).fetchone()[0])
                for label, table in table_map.items()
            }

    def _twin_link_count(self, trial_id: str) -> int:
        twin_path = self.path.parent.parent / "agrolattice_twin" / "agrolattice_twin.sqlite"
        if not twin_path.exists():
            return 0
        try:
            connection = sqlite3.connect(f"file:{twin_path.as_posix()}?mode=ro", uri=True)
            try:
                table = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='twin_links'").fetchone()
                if not table:
                    return 0
                return int(connection.execute("SELECT COUNT(*) FROM twin_links WHERE trial_id=?", (trial_id,)).fetchone()[0])
            finally:
                connection.close()
        except sqlite3.Error as error:
            raise PollinationLabError(
                f"Could not verify Persistent Twin dependencies safely: {error}. Trial deletion is disabled until the Twin database can be checked."
            ) from error

    def delete_trial(
        self,
        trial_id: str,
        *,
        confirmation_name: str | None = None,
        allow_cascade: bool = False,
    ) -> None:
        """Hard-delete a trial only after explicit confirmation for data-bearing trials.

        Empty accidental trial shells may still be removed directly. Once any plot,
        weather, observation, outcome, satellite link or model run exists, callers must
        deliberately opt into the cascade and provide the exact trial name.
        """
        twin_links = self._twin_link_count(trial_id)
        if twin_links:
            raise PollinationLabError(
                f"This trial is linked to {twin_links} Persistent Twin(s). Archive the trial or remove/reassign the Twin link before deletion."
            )
        trial = self.get_trial(trial_id)
        counts = self.trial_deletion_counts(trial_id)
        data_bearing = any(int(value) > 0 for value in counts.values())
        if data_bearing:
            if not allow_cascade:
                raise PollinationLabError(
                    "This trial contains research records. Archive it instead, or use the protected hard-delete workflow "
                    "that displays affected-record counts and requires the exact trial name."
                )
            if str(confirmation_name or "").strip() != str(trial.get("name") or "").strip():
                raise PollinationLabError("Hard deletion requires typing the exact trial name.")
        with closing(self.connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                deleted = connection.execute("DELETE FROM trials WHERE trial_id=?", (trial_id,)).rowcount
                if not deleted:
                    raise PollinationLabError("Trial not found.")
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise

    @staticmethod
    def _replace_plots_in_connection(
        connection: sqlite3.Connection,
        trial_id: str,
        rows: Sequence[Mapping[str, Any]],
        *,
        field_geometry: Mapping[str, Any] | None,
    ) -> None:
        now = utc_now()
        prepared: list[dict[str, Any]] = []
        geometries = [row["geometry"] for row in rows]
        validated_geometries = validate_treatment_unit_geometries(geometries, field_geometry=field_geometry)
        labels = [str(row["plot_label"]) for row in rows]
        if len(labels) != len(set(labels)):
            raise PollinationLabError("Treatment-unit labels must be unique within a trial.")
        existing_rows = connection.execute(
            "SELECT plot_id, plot_label FROM plots WHERE trial_id=?", (trial_id,)
        ).fetchall()
        existing_by_label = {str(row["plot_label"]): str(row["plot_id"]) for row in existing_rows}
        for row, geometry in zip(rows, validated_geometries):
            payload = dict(row)
            payload["geometry"] = geometry
            payload["plot_id"] = existing_by_label.get(str(row["plot_label"])) or str(row.get("plot_id") or uuid.uuid4())
            prepared.append(payload)
        for row in prepared:
            geometry = row["geometry"]
            area = geometry_area_hectares(geometry)
            lat, lon = geometry_centroid(geometry)
            female_parent = str(row.get("female_parent") or "")
            male_parent = str(row.get("male_parent") or "")
            parent_combination = str(
                row.get("parent_combination") or row.get("variety_genotype")
                or f"{female_parent} × {male_parent}".strip(" ×")
            )
            connection.execute(
                """
                INSERT INTO plots(plot_id, trial_id, plot_label, experiment_plot_label, treatment_unit_label,
                                  block, replicate, treatment_label, male_sowing_offset_days,
                                  sowing_density_plants_ha, female_parent, male_parent, parent_combination,
                                  variety_genotype, sowing_date, factor_levels_json, female_sowing_date,
                                  male_sowing_date, geometry_json, area_ha, centroid_lat, centroid_lon, created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(plot_id) DO UPDATE SET
                    plot_label=excluded.plot_label, experiment_plot_label=excluded.experiment_plot_label,
                    treatment_unit_label=excluded.treatment_unit_label, block=excluded.block, replicate=excluded.replicate,
                    treatment_label=excluded.treatment_label, male_sowing_offset_days=excluded.male_sowing_offset_days,
                    sowing_density_plants_ha=excluded.sowing_density_plants_ha, female_parent=excluded.female_parent,
                    male_parent=excluded.male_parent, parent_combination=excluded.parent_combination,
                    variety_genotype=excluded.variety_genotype, sowing_date=excluded.sowing_date,
                    factor_levels_json=excluded.factor_levels_json, female_sowing_date=excluded.female_sowing_date,
                    male_sowing_date=excluded.male_sowing_date, geometry_json=excluded.geometry_json,
                    area_ha=excluded.area_ha, centroid_lat=excluded.centroid_lat, centroid_lon=excluded.centroid_lon
                """,
                (
                    row["plot_id"], trial_id, str(row["plot_label"]),
                    str(row.get("experiment_plot_label") or f"B{int(row['block']):02d}"),
                    str(row.get("treatment_unit_label") or row["plot_label"]), int(row["block"]),
                    int(row["replicate"]), str(row["treatment_label"]), int(row["male_sowing_offset_days"]),
                    float(row["sowing_density_plants_ha"]) if row.get("sowing_density_plants_ha") not in (None, "") else None,
                    female_parent, male_parent, parent_combination, parent_combination,
                    str(row.get("sowing_date") or row["female_sowing_date"]), _json(row.get("factor_levels") or {}),
                    str(row["female_sowing_date"]), str(row["male_sowing_date"]), _json(geometry),
                    area, lat, lon, now,
                ),
            )
        keep_ids = [row["plot_id"] for row in prepared]
        if keep_ids:
            placeholders = ",".join("?" for _ in keep_ids)
            connection.execute(
                f"DELETE FROM plots WHERE trial_id=? AND plot_id NOT IN ({placeholders})",
                (trial_id, *keep_ids),
            )
        else:
            connection.execute("DELETE FROM plots WHERE trial_id=?", (trial_id,))

    def replace_plots(self, trial_id: str, rows: Sequence[Mapping[str, Any]]) -> None:
        dependencies = self.trial_plot_dependency_counts(trial_id)
        blocking = {key: value for key, value in dependencies.items() if value}
        if blocking:
            detail = ", ".join(f"{key}: {value}" for key, value in blocking.items())
            raise PollinationLabError(
                "The plot map cannot be re-randomised because plot-linked research data already exist (" + detail + "). "
                "Create a new trial/design version or remove those records deliberately first; AGROLATTICE will not cascade-delete them."
            )
        trial = self.get_trial(trial_id)
        with closing(self.connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                self._replace_plots_in_connection(connection, trial_id, rows, field_geometry=trial.get("field_geometry"))
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise

    def save_factor_design_and_plots(
        self,
        trial_id: str,
        rows: Sequence[Mapping[str, Any]],
        *,
        female_parent_levels: Sequence[str],
        male_parent_levels: Sequence[str],
        parent_pairings: Sequence[Mapping[str, Any]],
        parent_pairing_mode: str,
        sowing_density_levels: Sequence[float],
        sowing_date_levels: Sequence[str],
        sowing_offset_levels: Sequence[int],
    ) -> None:
        """Atomically save factor metadata and the mapped randomisation.

        No trial metadata is changed unless all spatial validation and plot writes succeed.
        """
        design = self._normalise_factor_design(
            female_parent_levels=female_parent_levels, male_parent_levels=male_parent_levels,
            parent_pairings=parent_pairings, parent_pairing_mode=parent_pairing_mode,
            sowing_density_levels=sowing_density_levels, sowing_date_levels=sowing_date_levels,
            sowing_offset_levels=sowing_offset_levels,
        )
        trial = self.get_trial(trial_id)
        treatment_count = max(len(design["densities"]), 1) * len(design["pairings"]) * len(design["dates"]) * len(design["offsets"])
        expected_rows = int(trial.get("blocks") or 0) * int(trial.get("replicates_per_treatment") or 0) * treatment_count
        if len(rows) != expected_rows:
            raise PollinationLabError(
                f"Mapped design requires exactly {expected_rows} treatment units for the selected factors, blocks and replicates; received {len(rows)}."
            )
        dependencies = self.trial_plot_dependency_counts(trial_id)
        blocking = {key: value for key, value in dependencies.items() if value}
        if blocking:
            detail = ", ".join(f"{key}: {value}" for key, value in blocking.items())
            raise PollinationLabError(
                "The mapped design is locked because plot-linked research data already exist (" + detail + "). "
                "Create a new trial/design version rather than relabelling collected observations."
            )
        # Validate before opening the transaction so malformed geometry cannot partially alter the design.
        validate_treatment_unit_geometries([row["geometry"] for row in rows], field_geometry=trial.get("field_geometry"))
        with closing(self.connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                self._apply_factor_design(connection, trial_id, design)
                self._replace_plots_in_connection(connection, trial_id, rows, field_geometry=trial.get("field_geometry"))
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise

    def list_plots(self, trial_id: str) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            frame = pd.read_sql_query(
                """
                SELECT plot_id AS 'Plot ID', plot_label AS 'Plot',
                       COALESCE(experiment_plot_label, 'B' || printf('%02d', block)) AS 'Experiment plot',
                       COALESCE(treatment_unit_label, plot_label) AS 'Treatment unit',
                       block AS 'Block', replicate AS 'Replicate', treatment_label AS 'Treatment',
                       sowing_density_plants_ha AS 'Sowing density (plants/ha)',
                       female_parent AS 'Female parent', male_parent AS 'Male parent',
                       COALESCE(parent_combination, variety_genotype) AS 'Parent combination',
                       COALESCE(variety_genotype, parent_combination) AS 'Variety / genotype',
                       COALESCE(sowing_date, female_sowing_date) AS 'Sowing date',
                       male_sowing_offset_days AS 'Male–female sowing difference (days)',
                       male_sowing_offset_days AS 'Male offset (days)',
                       female_sowing_date AS 'Female sowing', male_sowing_date AS 'Male sowing', factor_levels_json,
                       area_ha AS 'Area (ha)', centroid_lat AS 'Latitude', centroid_lon AS 'Longitude', geometry_json
                FROM plots WHERE trial_id=? ORDER BY plot_label
                """,
                connection,
                params=(trial_id,),
            )
        if not frame.empty:
            frame["Geometry"] = frame["geometry_json"].map(lambda value: _loads(value, None))
            frame["Factor levels"] = frame["factor_levels_json"].map(lambda value: _loads(value, {}))
            frame = frame.drop(columns=["geometry_json", "factor_levels_json"])
        return frame

    def upsert_observations(self, trial_id: str, frame: pd.DataFrame) -> tuple[int, list[str]]:
        if frame is None or frame.empty:
            return 0, ["No observation rows were supplied."]
        columns = {str(column).strip().casefold(): column for column in frame.columns}
        required_aliases = {
            "plot": ["plot", "plot id", "plot_label"],
            "date": ["observation date", "date", "observation_date"],
        }
        resolved: dict[str, str] = {}
        for canonical, aliases in required_aliases.items():
            for alias in aliases:
                if alias in columns:
                    resolved[canonical] = columns[alias]
                    break
            if canonical not in resolved:
                return 0, [f"Missing required column: {canonical}"]
        plot_table = self.list_plots(trial_id)
        if plot_table.empty:
            return 0, ["The trial has no saved plots."]
        label_to_id = dict(zip(plot_table["Plot"].astype(str), plot_table["Plot ID"].astype(str)))
        id_set = set(plot_table["Plot ID"].astype(str))

        def col(*aliases: str) -> str | None:
            for alias in aliases:
                if alias.casefold() in columns:
                    return columns[alias.casefold()]
            return None

        mappings = {
            "male_plants_assessed": col("male plants assessed", "male_plants_assessed"),
            "male_shedding_percent": col("male shedding (%)", "male shedding percent", "male_shedding_percent"),
            "male_pollen_intensity": col("pollen intensity (0-5)", "male pollen intensity", "male_pollen_intensity"),
            "female_plants_assessed": col("female plants assessed", "female_plants_assessed"),
            "female_silking_percent": col("female silking (%)", "female silking percent", "female_silking_percent"),
            "female_receptive_percent": col("female receptive silks (%)", "female receptive percent", "female_receptive_percent"),
            "crop_stress_score": col("crop stress score (0-5)", "crop stress score", "crop_stress_score"),
            "male_plant_height_cm": col("male plant height (cm)", "male height (cm)", "male_plant_height_cm"),
            "female_plant_height_cm": col("female plant height (cm)", "female height (cm)", "female_plant_height_cm"),
            "detasselling_complete": col("detasselling complete", "detasselling_complete"),
            "notes": col("notes"),
        }
        inserted = 0
        issues: list[str] = []
        with closing(self.connect()) as connection:
            for index, row in frame.iterrows():
                raw_plot = str(row[resolved["plot"]]).strip()
                plot_id = raw_plot if raw_plot in id_set else label_to_id.get(raw_plot)
                observation_date = pd.to_datetime(row[resolved["date"]], errors="coerce")
                if not plot_id or pd.isna(observation_date):
                    issues.append(f"Row {index + 2}: invalid plot or date.")
                    continue

                def number(key: str, integer: bool = False) -> float | int | None:
                    source = mappings[key]
                    if source is None:
                        return None
                    value = pd.to_numeric(pd.Series([row[source]]), errors="coerce").iloc[0]
                    if pd.isna(value):
                        return None
                    return int(value) if integer else float(value)

                values = {
                    "male_plants_assessed": number("male_plants_assessed", True),
                    "male_shedding_percent": number("male_shedding_percent"),
                    "male_pollen_intensity": number("male_pollen_intensity"),
                    "female_plants_assessed": number("female_plants_assessed", True),
                    "female_silking_percent": number("female_silking_percent"),
                    "female_receptive_percent": number("female_receptive_percent"),
                    "crop_stress_score": number("crop_stress_score"),
                    "male_plant_height_cm": number("male_plant_height_cm"),
                    "female_plant_height_cm": number("female_plant_height_cm"),
                    "detasselling_complete": None,
                    "notes": str(row[mappings["notes"]]) if mappings["notes"] and pd.notna(row[mappings["notes"]]) else "",
                }
                if mappings["detasselling_complete"]:
                    raw = str(row[mappings["detasselling_complete"]]).strip().casefold()
                    values["detasselling_complete"] = int(raw in {"1", "true", "yes", "y", "complete"})
                for key in ["male_shedding_percent", "female_silking_percent", "female_receptive_percent"]:
                    if values[key] is not None and not 0 <= float(values[key]) <= 100:
                        issues.append(f"Row {index + 2}: {key} outside 0–100; row skipped.")
                        plot_id = None
                        break
                if not plot_id:
                    continue
                connection.execute(
                    """
                    INSERT INTO flowering_observations(
                        observation_id, trial_id, plot_id, observation_date, male_plants_assessed,
                        male_shedding_percent, male_pollen_intensity, female_plants_assessed,
                        female_silking_percent, female_receptive_percent, crop_stress_score,
                        male_plant_height_cm, female_plant_height_cm, detasselling_complete, notes, created_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(plot_id, observation_date) DO UPDATE SET
                        male_plants_assessed=excluded.male_plants_assessed,
                        male_shedding_percent=excluded.male_shedding_percent,
                        male_pollen_intensity=excluded.male_pollen_intensity,
                        female_plants_assessed=excluded.female_plants_assessed,
                        female_silking_percent=excluded.female_silking_percent,
                        female_receptive_percent=excluded.female_receptive_percent,
                        crop_stress_score=excluded.crop_stress_score,
                        male_plant_height_cm=excluded.male_plant_height_cm,
                        female_plant_height_cm=excluded.female_plant_height_cm,
                        detasselling_complete=excluded.detasselling_complete,
                        notes=excluded.notes
                    """,
                    (
                        str(uuid.uuid4()), trial_id, plot_id, observation_date.date().isoformat(),
                        values["male_plants_assessed"], values["male_shedding_percent"], values["male_pollen_intensity"],
                        values["female_plants_assessed"], values["female_silking_percent"], values["female_receptive_percent"],
                        values["crop_stress_score"], values["male_plant_height_cm"], values["female_plant_height_cm"],
                        values["detasselling_complete"], values["notes"], utc_now(),
                    ),
                )
                inserted += 1
        return inserted, issues

    def observations(self, trial_id: str) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            return pd.read_sql_query(
                """
                SELECT o.observation_id AS 'Observation ID', o.plot_id AS 'Plot ID', p.plot_label AS 'Plot',
                       p.block AS 'Block', p.replicate AS 'Replicate', p.treatment_label AS 'Treatment',
                       p.male_sowing_offset_days AS 'Male offset (days)', p.female_sowing_date AS 'Female sowing',
                       p.male_sowing_date AS 'Male sowing', o.observation_date AS 'Date',
                       o.male_plants_assessed AS 'Male plants assessed', o.male_shedding_percent AS 'Male shedding (%)',
                       o.male_pollen_intensity AS 'Pollen intensity (0-5)',
                       o.female_plants_assessed AS 'Female plants assessed', o.female_silking_percent AS 'Female silking (%)',
                       o.female_receptive_percent AS 'Female receptive silks (%)',
                       o.crop_stress_score AS 'Crop stress score (0-5)',
                       o.male_plant_height_cm AS 'Male plant height (cm)',
                       o.female_plant_height_cm AS 'Female plant height (cm)',
                       o.detasselling_complete AS 'Detasselling complete', o.notes AS 'Notes'
                FROM flowering_observations o JOIN plots p ON o.plot_id=p.plot_id
                WHERE o.trial_id=? ORDER BY o.observation_date, p.plot_label
                """,
                connection,
                params=(trial_id,),
            )

    def upsert_leaf_observations(self, trial_id: str, frame: pd.DataFrame) -> tuple[int, list[str]]:
        if frame is None or frame.empty:
            return 0, ["No leaf-development rows were supplied."]
        columns = {str(column).strip().casefold(): column for column in frame.columns}

        def find(*aliases: str) -> str | None:
            return next((columns[value.casefold()] for value in aliases if value.casefold() in columns), None)

        plot_source = find("plot", "plot id", "plot_label")
        date_source = find("observation date", "date", "observation_date")
        leaf_source = find("collared leaf number", "leaf number", "collared_leaf_number")
        if plot_source is None or date_source is None or leaf_source is None:
            return 0, ["Leaf observations require Plot, Observation date and Collared leaf number columns."]
        tag_source = find("plant tag", "plant id", "plant_tag")
        role_source = find("parent role", "role", "parent_role")
        final_source = find("final total leaf number", "total leaf number", "tln observed", "final_total_leaf_number")
        ear_biomass_source = find("ear biomass (g)", "ear biomass", "ear_biomass_g")
        ear_length_source = find("ear length (mm)", "ear length", "ear_length_mm")
        stage_source = find("developmental stage", "stage", "developmental_stage")
        notes_source = find("notes")
        plots = self.list_plots(trial_id)
        labels = dict(zip(plots["Plot"].astype(str), plots["Plot ID"].astype(str)))
        identifiers = set(plots["Plot ID"].astype(str))
        inserted = 0
        issues: list[str] = []

        def numeric(row: pd.Series, source: str | None) -> float | None:
            if source is None:
                return None
            value = pd.to_numeric(pd.Series([row[source]]), errors="coerce").iloc[0]
            return float(value) if pd.notna(value) else None

        with closing(self.connect()) as connection:
            for index, row in frame.iterrows():
                raw_plot = str(row[plot_source]).strip()
                plot_id = raw_plot if raw_plot in identifiers else labels.get(raw_plot)
                observed = pd.to_datetime(row[date_source], errors="coerce")
                collared = numeric(row, leaf_source)
                plant_tag = str(row[tag_source]).strip() if tag_source and pd.notna(row[tag_source]) else "P1"
                parent_role = str(row[role_source]).strip().title() if role_source and pd.notna(row[role_source]) else "Female"
                if parent_role not in {"Female", "Male"}:
                    issues.append(f"Row {index + 2}: Parent role must be Female or Male.")
                    continue
                if not plot_id:
                    issues.append(f"Row {index + 2}: unknown plot {raw_plot}.")
                    continue
                if pd.isna(observed) or collared is None or not 0 <= collared <= 40:
                    issues.append(f"Row {index + 2}: invalid date or collared leaf number outside 0–40.")
                    continue
                final_leaf = numeric(row, final_source)
                ear_biomass = numeric(row, ear_biomass_source)
                ear_length = numeric(row, ear_length_source)
                if final_leaf is not None and not 0 <= final_leaf <= 40:
                    issues.append(f"Row {index + 2}: final total leaf number is outside 0–40.")
                    continue
                if ear_biomass is not None and not 0 <= ear_biomass <= 20:
                    issues.append(f"Row {index + 2}: ear biomass is outside the broad 0–20 g validation range.")
                    continue
                now = utc_now()
                connection.execute(
                    """
                    INSERT INTO leaf_development_observations(
                        leaf_observation_id, trial_id, plot_id, observation_date, plant_tag, parent_role,
                        collared_leaf_number, final_total_leaf_number, ear_biomass_g,
                        ear_length_mm, developmental_stage, notes, created_at, updated_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(plot_id, observation_date, plant_tag) DO UPDATE SET
                        parent_role=excluded.parent_role,
                        collared_leaf_number=excluded.collared_leaf_number,
                        final_total_leaf_number=excluded.final_total_leaf_number,
                        ear_biomass_g=excluded.ear_biomass_g,
                        ear_length_mm=excluded.ear_length_mm,
                        developmental_stage=excluded.developmental_stage,
                        notes=excluded.notes, updated_at=excluded.updated_at
                    """,
                    (
                        str(uuid.uuid4()), trial_id, plot_id, observed.date().isoformat(), plant_tag, parent_role,
                        collared, final_leaf, ear_biomass, ear_length,
                        str(row[stage_source]).strip() if stage_source and pd.notna(row[stage_source]) else "",
                        str(row[notes_source]).strip() if notes_source and pd.notna(row[notes_source]) else "",
                        now, now,
                    ),
                )
                inserted += 1
        return inserted, issues

    def leaf_observations(self, trial_id: str) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            frame = pd.read_sql_query(
                """
                SELECT l.leaf_observation_id AS 'Leaf observation ID', l.plot_id AS 'Plot ID',
                       p.plot_label AS 'Plot', p.female_parent AS 'Female parent', p.male_parent AS 'Male parent',
                       p.female_sowing_date AS 'Female sowing', p.male_sowing_date AS 'Male sowing',
                       l.observation_date AS 'Observation date', l.plant_tag AS 'Plant tag', l.parent_role AS 'Parent role',
                       l.collared_leaf_number AS 'Collared leaf number',
                       l.final_total_leaf_number AS 'Final total leaf number',
                       l.ear_biomass_g AS 'Ear biomass (g)', l.ear_length_mm AS 'Ear length (mm)',
                       l.developmental_stage AS 'Developmental stage', l.notes AS 'Notes'
                FROM leaf_development_observations l JOIN plots p ON l.plot_id=p.plot_id
                WHERE l.trial_id=? ORDER BY l.observation_date, p.plot_label, l.plant_tag
                """,
                connection,
                params=(trial_id,),
            )
        if not frame.empty:
            frame["Observation date"] = pd.to_datetime(frame["Observation date"])
        return frame

    def upsert_phenology_events(self, trial_id: str, frame: pd.DataFrame) -> tuple[int, list[str]]:
        if frame is None or frame.empty:
            return 0, ["No flowering-date rows were supplied."]
        columns = {str(column).strip().casefold(): column for column in frame.columns}
        plot_source = next((columns[key] for key in ["plot", "plot id", "plot_label"] if key in columns), None)
        if plot_source is None:
            return 0, ["Missing Plot column."]
        plots = self.list_plots(trial_id)
        label_to_id = dict(zip(plots["Plot"].astype(str), plots["Plot ID"].astype(str)))
        id_set = set(plots["Plot ID"].astype(str))

        def find(*aliases: str) -> str | None:
            return next((columns[a.casefold()] for a in aliases if a.casefold() in columns), None)

        mapping_columns = {
            "male_flowering_initiation_date": find("male flowering initiation date", "male initiation date", "male_flowering_initiation_date"),
            "male_flowering_date": find("male flowering date", "male full flowering date", "male_flowering_date"),
            "female_flowering_initiation_date": find("female flowering initiation date", "female initiation date", "female_flowering_initiation_date"),
            "female_flowering_date": find("female flowering date", "female full flowering date", "female_flowering_date"),
            "notes": find("notes"),
        }
        inserted = 0
        issues: list[str] = []

        def parsed_date(value: Any) -> str | None:
            parsed = pd.to_datetime(value, errors="coerce")
            return parsed.date().isoformat() if pd.notna(parsed) else None

        with closing(self.connect()) as connection:
            for index, row in frame.iterrows():
                raw_plot = str(row[plot_source]).strip()
                plot_id = raw_plot if raw_plot in id_set else label_to_id.get(raw_plot)
                if not plot_id:
                    issues.append(f"Row {index + 2}: unknown plot {raw_plot}.")
                    continue
                values = {key: parsed_date(row[source]) if source and pd.notna(row[source]) and str(row[source]).strip() else None for key, source in mapping_columns.items() if key != "notes"}
                for parent in ["male", "female"]:
                    initiation = pd.to_datetime(values.get(f"{parent}_flowering_initiation_date"), errors="coerce")
                    flowering = pd.to_datetime(values.get(f"{parent}_flowering_date"), errors="coerce")
                    if pd.notna(initiation) and pd.notna(flowering) and flowering < initiation:
                        issues.append(f"Row {index + 2}: {parent} flowering date precedes initiation; row skipped.")
                        plot_id = None
                        break
                if not plot_id:
                    continue
                now = utc_now()
                connection.execute(
                    """
                    INSERT INTO plot_phenology_events(
                        event_id, trial_id, plot_id, male_flowering_initiation_date, male_flowering_date,
                        female_flowering_initiation_date, female_flowering_date, notes, created_at, updated_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(plot_id) DO UPDATE SET
                        male_flowering_initiation_date=excluded.male_flowering_initiation_date,
                        male_flowering_date=excluded.male_flowering_date,
                        female_flowering_initiation_date=excluded.female_flowering_initiation_date,
                        female_flowering_date=excluded.female_flowering_date,
                        notes=excluded.notes, updated_at=excluded.updated_at
                    """,
                    (
                        str(uuid.uuid4()), trial_id, plot_id, values.get("male_flowering_initiation_date"),
                        values.get("male_flowering_date"), values.get("female_flowering_initiation_date"),
                        values.get("female_flowering_date"),
                        str(row[mapping_columns["notes"]]) if mapping_columns["notes"] and pd.notna(row[mapping_columns["notes"]]) else "",
                        now, now,
                    ),
                )
                inserted += 1
        return inserted, issues

    def phenology_events(self, trial_id: str) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            return pd.read_sql_query(
                """
                SELECT e.plot_id AS 'Plot ID', p.plot_label AS 'Plot', p.block AS 'Block',
                       p.treatment_label AS 'Treatment', p.male_sowing_offset_days AS 'Male offset (days)',
                       e.male_flowering_initiation_date AS 'Male flowering initiation date',
                       e.male_flowering_date AS 'Male flowering date',
                       e.female_flowering_initiation_date AS 'Female flowering initiation date',
                       e.female_flowering_date AS 'Female flowering date', e.notes AS 'Flowering-date notes'
                FROM plot_phenology_events e JOIN plots p ON e.plot_id=p.plot_id
                WHERE e.trial_id=? ORDER BY p.plot_label
                """,
                connection,
                params=(trial_id,),
            )

    def upsert_harvest(self, trial_id: str, frame: pd.DataFrame) -> tuple[int, list[str]]:
        if frame is None or frame.empty:
            return 0, ["No harvest rows were supplied."]
        columns = {str(column).strip().casefold(): column for column in frame.columns}
        plot_source = next((columns[key] for key in ["plot", "plot id", "plot_label"] if key in columns), None)
        if plot_source is None:
            return 0, ["Missing Plot column."]
        plots = self.list_plots(trial_id)
        label_to_id = dict(zip(plots["Plot"].astype(str), plots["Plot ID"].astype(str)))
        id_set = set(plots["Plot ID"].astype(str))

        def find(*aliases: str) -> str | None:
            return next((columns[a.casefold()] for a in aliases if a.casefold() in columns), None)

        mapping_columns = {
            "harvest_date": find("harvest date", "harvest_date"),
            "ears_harvested": find("ears harvested", "ears_harvested"),
            "kernels_per_ear": find("kernels per ear", "kernels_per_ear"),
            "kernel_rows_per_ear": find("kernel rows per ear", "rows per ear", "lines per ear", "kernel_rows_per_ear"),
            "filled_kernels": find("filled kernels", "filled_kernels"),
            "unfilled_kernels": find("unfilled kernels", "unfilled_kernels"),
            "seed_set_percent": find("seed set (%)", "seed-set percentage", "seed_set_percent"),
            "seed_yield_kg_plot": find("seed yield (kg/plot)", "seed_yield_kg_plot"),
            "seed_yield_t_ha": find("seed yield (t/ha)", "seed_yield_t_ha"),
            "thousand_kernel_weight_g": find("1000-kernel weight (g)", "thousand_kernel_weight_g"),
            "germination_percent": find("germination (%)", "germination_percent"),
            "genetic_purity_percent": find("genetic purity (%)", "genetic_purity_percent"),
            "pure_seed_percent": find("pure seed (%)", "pure seed percent", "pure_seed_percent"),
            "notes": find("notes"),
        }
        inserted = 0
        issues: list[str] = []
        with closing(self.connect()) as connection:
            for index, row in frame.iterrows():
                raw_plot = str(row[plot_source]).strip()
                plot_id = raw_plot if raw_plot in id_set else label_to_id.get(raw_plot)
                if not plot_id:
                    issues.append(f"Row {index + 2}: unknown plot {raw_plot}.")
                    continue

                def numeric(key: str) -> float | None:
                    source = mapping_columns[key]
                    if source is None:
                        return None
                    value = pd.to_numeric(pd.Series([row[source]]), errors="coerce").iloc[0]
                    return float(value) if pd.notna(value) else None

                harvest_date = None
                if mapping_columns["harvest_date"]:
                    parsed = pd.to_datetime(row[mapping_columns["harvest_date"]], errors="coerce")
                    harvest_date = parsed.date().isoformat() if pd.notna(parsed) else None
                seed_set = numeric("seed_set_percent")
                filled = numeric("filled_kernels")
                unfilled = numeric("unfilled_kernels")
                if seed_set is None and filled is not None and unfilled is not None and filled + unfilled > 0:
                    seed_set = 100.0 * filled / (filled + unfilled)
                now = utc_now()
                connection.execute(
                    """
                    INSERT INTO harvest_outcomes(
                        harvest_id, trial_id, plot_id, harvest_date, ears_harvested, kernels_per_ear,
                        kernel_rows_per_ear, filled_kernels, unfilled_kernels, seed_set_percent, seed_yield_kg_plot,
                        seed_yield_t_ha, thousand_kernel_weight_g, germination_percent,
                        genetic_purity_percent, pure_seed_percent, notes, created_at, updated_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(plot_id) DO UPDATE SET
                        harvest_date=excluded.harvest_date, ears_harvested=excluded.ears_harvested,
                        kernels_per_ear=excluded.kernels_per_ear, kernel_rows_per_ear=excluded.kernel_rows_per_ear,
                        filled_kernels=excluded.filled_kernels,
                        unfilled_kernels=excluded.unfilled_kernels, seed_set_percent=excluded.seed_set_percent,
                        seed_yield_kg_plot=excluded.seed_yield_kg_plot, seed_yield_t_ha=excluded.seed_yield_t_ha,
                        thousand_kernel_weight_g=excluded.thousand_kernel_weight_g,
                        germination_percent=excluded.germination_percent,
                        genetic_purity_percent=excluded.genetic_purity_percent,
                        pure_seed_percent=excluded.pure_seed_percent,
                        notes=excluded.notes, updated_at=excluded.updated_at
                    """,
                    (
                        str(uuid.uuid4()), trial_id, plot_id, harvest_date, numeric("ears_harvested"),
                        numeric("kernels_per_ear"), numeric("kernel_rows_per_ear"), filled, unfilled, seed_set, numeric("seed_yield_kg_plot"),
                        numeric("seed_yield_t_ha"), numeric("thousand_kernel_weight_g"), numeric("germination_percent"),
                        numeric("genetic_purity_percent"), numeric("pure_seed_percent"),
                        str(row[mapping_columns["notes"]]) if mapping_columns["notes"] else "",
                        now, now,
                    ),
                )
                inserted += 1
        return inserted, issues

    def harvest(self, trial_id: str) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            return pd.read_sql_query(
                """
                SELECT h.plot_id AS 'Plot ID', p.plot_label AS 'Plot', p.block AS 'Block',
                       p.treatment_label AS 'Treatment', p.male_sowing_offset_days AS 'Male offset (days)',
                       h.harvest_date AS 'Harvest date', h.ears_harvested AS 'Ears harvested',
                       h.kernels_per_ear AS 'Kernels per ear', h.kernel_rows_per_ear AS 'Kernel rows per ear',
                       h.filled_kernels AS 'Filled kernels',
                       h.unfilled_kernels AS 'Unfilled kernels', h.seed_set_percent AS 'Seed set (%)',
                       h.seed_yield_kg_plot AS 'Seed yield (kg/plot)', h.seed_yield_t_ha AS 'Seed yield (t/ha)',
                       h.thousand_kernel_weight_g AS '1000-kernel weight (g)',
                       h.germination_percent AS 'Germination (%)', h.genetic_purity_percent AS 'Genetic purity (%)',
                       h.pure_seed_percent AS 'Pure seed (%)', h.notes AS 'Notes'
                FROM harvest_outcomes h JOIN plots p ON h.plot_id=p.plot_id
                WHERE h.trial_id=? ORDER BY p.plot_label
                """,
                connection,
                params=(trial_id,),
            )

    def replace_weather(self, trial_id: str, frame: pd.DataFrame, source: str) -> int:
        prepared = prepare_weather(frame, base_temperature_c=self.get_trial(trial_id)["base_temperature_c"], upper_temperature_c=self.get_trial(trial_id)["upper_temperature_c"])
        with closing(self.connect()) as connection:
            connection.execute("DELETE FROM weather_daily WHERE trial_id=?", (trial_id,))
            for _, row in prepared.iterrows():
                connection.execute(
                    """
                    INSERT INTO weather_daily(trial_id, weather_date, tmin_c, tmax_c, tmean_c,
                        precipitation_mm, solar_radiation_mj_m2, reference_et_mm, gdd_daily, source)
                    VALUES(?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        trial_id, row["Date"].date().isoformat(), row["Tmin (°C)"], row["Tmax (°C)"],
                        row["Tmean (°C)"], row["Rainfall (mm)"], row["Solar radiation (MJ/m²/day)"],
                        row["Reference ET (mm)"], row["GDD daily"], source,
                    ),
                )
        return len(prepared)

    def weather(self, trial_id: str) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            frame = pd.read_sql_query(
                """
                SELECT weather_date AS 'Date', tmin_c AS 'Tmin (°C)', tmax_c AS 'Tmax (°C)',
                       tmean_c AS 'Tmean (°C)', precipitation_mm AS 'Rainfall (mm)',
                       solar_radiation_mj_m2 AS 'Solar radiation (MJ/m²/day)',
                       reference_et_mm AS 'Reference ET (mm)', gdd_daily AS 'GDD daily', source AS 'Source'
                FROM weather_daily WHERE trial_id=? ORDER BY weather_date
                """,
                connection,
                params=(trial_id,),
            )
        if not frame.empty:
            frame["Date"] = pd.to_datetime(frame["Date"])
        return frame

    def add_satellite_link(
        self,
        trial_id: str,
        *,
        target_label: str,
        plot_ids: Sequence[str],
        geometry: Mapping[str, Any],
        time_series: pd.DataFrame,
        processing_metadata: Mapping[str, Any] | None,
    ) -> str:
        if not isinstance(time_series, pd.DataFrame) or time_series.empty:
            raise PollinationLabError("No satellite time series is available.")
        link_id = str(uuid.uuid4())
        geometry = validate_aoi_geometry(geometry)
        with closing(self.connect()) as connection:
            connection.execute(
                """
                INSERT INTO satellite_links(link_id, trial_id, target_label, plot_ids_json, geometry_hash,
                                            geometry_json, processing_metadata_json, time_series_json, created_at)
                VALUES(?,?,?,?,?,?,?,?,?)
                """,
                (
                    link_id, trial_id, target_label, _json(list(plot_ids)), geometry_hash(geometry), _json(geometry),
                    _json(dict(processing_metadata or {})), time_series.to_json(orient="records", date_format="iso"), utc_now(),
                ),
            )
        return link_id

    def satellite_links(self, trial_id: str) -> pd.DataFrame:
        with closing(self.connect()) as connection:
            return pd.read_sql_query(
                """
                SELECT link_id AS 'Link ID', target_label AS 'Target', plot_ids_json AS 'Plot IDs',
                       geometry_hash AS 'Geometry hash', processing_metadata_json AS 'Processing metadata',
                       time_series_json AS 'Time series', created_at AS 'Created'
                FROM satellite_links WHERE trial_id=? ORDER BY created_at DESC
                """,
                connection,
                params=(trial_id,),
            )

    def save_model_run(self, trial_id: str, target: str, grouping: str, settings: Mapping[str, Any], metrics: pd.DataFrame, predictions: pd.DataFrame) -> str:
        run_id = str(uuid.uuid4())
        with closing(self.connect()) as connection:
            connection.execute(
                "INSERT INTO model_runs(run_id, trial_id, target, grouping, settings_json, metrics_json, predictions_json, created_at) VALUES(?,?,?,?,?,?,?,?)",
                (run_id, trial_id, target, grouping, _json(dict(settings)), metrics.to_json(orient="records"), predictions.to_json(orient="records", date_format="iso"), utc_now()),
            )
        return run_id

    def export_trial_package(self, trial_id: str) -> bytes:
        trial = self.get_trial(trial_id)
        plots = self.list_plots(trial_id)
        observations = self.observations(trial_id)
        leaf_observations = self.leaf_observations(trial_id)
        phenology_events = self.phenology_events(trial_id)
        harvest = self.harvest(trial_id)
        weather = self.weather(trial_id)
        satellite = self.satellite_links(trial_id)
        experiment_protocol = self.experiment_protocol(trial_id) or {}
        experiment_protocol_versions = self.protocol_versions(trial_id)
        factors = self.factor_definitions(trial_id)
        design_versions = self.design_versions(trial_id)
        measurement_requirements = self.measurement_requirements(trial_id)
        audit = self.trial_audit(trial_id)
        completeness = self.data_completeness_matrix(trial_id)
        parent_names = sorted(set(plots.get("Female parent", pd.Series(dtype=str)).dropna().astype(str)) | set(plots.get("Male parent", pd.Series(dtype=str)).dropna().astype(str)))
        physiology = self.parent_physiology(parent_names)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("trial/trial.json", json.dumps(trial, indent=2, ensure_ascii=False, default=str))
            archive.writestr("trial/plots.csv", plots.drop(columns=["Geometry"], errors="ignore").to_csv(index=False))
            archive.writestr("trial/flowering_observations.csv", observations.to_csv(index=False))
            archive.writestr("trial/leaf_development_observations.csv", leaf_observations.to_csv(index=False))
            archive.writestr("trial/plot_flowering_dates.csv", phenology_events.to_csv(index=False))
            archive.writestr("trial/harvest_outcomes.csv", harvest.to_csv(index=False))
            archive.writestr("trial/weather_daily.csv", weather.to_csv(index=False))
            archive.writestr("trial/parent_physiology.csv", physiology.to_csv(index=False))
            archive.writestr("trial/mechanistic_method_manifest.json", json.dumps(mechanistic_method_manifest(), indent=2))
            archive.writestr("trial/satellite_links.csv", satellite.drop(columns=["Time series"], errors="ignore").to_csv(index=False))
            archive.writestr("trial/experiment_protocol.json", json.dumps(experiment_protocol, indent=2, ensure_ascii=False, default=str))
            archive.writestr("trial/experiment_protocol_versions.csv", experiment_protocol_versions.to_csv(index=False))
            archive.writestr("trial/factor_definitions.csv", factors.to_csv(index=False))
            archive.writestr("trial/design_versions.csv", design_versions.drop(columns=["constraints_json","factor_matrix_json","allocation_manifest_json"], errors="ignore").to_csv(index=False))
            archive.writestr("trial/measurement_requirements.csv", measurement_requirements.to_csv(index=False))
            archive.writestr("trial/data_completeness.csv", completeness.to_csv(index=False))
            archive.writestr("trial/audit_log.csv", audit.drop(columns=["details_json"], errors="ignore").to_csv(index=False))
            features = []
            if trial.get("field_geometry"):
                features.append(_geometry_feature(trial["field_geometry"], {"feature_type": "experiment_field", "trial_id": trial_id}))
            for _, row in plots.iterrows():
                features.append(_geometry_feature(row["Geometry"], {"feature_type": "plot", "plot_id": row["Plot ID"], "plot_label": row["Plot"], "treatment": row["Treatment"]}))
            archive.writestr("trial/field_and_plots.geojson", _feature_collection(features))
            archive.writestr("README.txt", "Portable AGROLATTICE 11.15 Experiment Command Centre trial package. Review all records before analysis. The disclosed MFS equations are implemented; the optional genomic-ridge bridge is not the publication's proprietary Bayesian CGM-WGP sampler. Satellite data are linked to the exact stored AOI hash.\n")
        return buffer.getvalue()


# -----------------------------------------------------------------------------
# Data preparation and synchrony metrics
# -----------------------------------------------------------------------------


def _numeric_from(frame: pd.DataFrame, candidates: Sequence[str], default: float = np.nan) -> pd.Series:
    for candidate in candidates:
        if candidate in frame.columns:
            return pd.to_numeric(frame[candidate], errors="coerce")
    return pd.Series(default, index=frame.index, dtype=float)


def prepare_weather(frame: pd.DataFrame, *, base_temperature_c: float = 10.0, upper_temperature_c: float = 30.0) -> pd.DataFrame:
    if frame is None or frame.empty:
        raise PollinationLabError("Daily weather is empty.")
    output = frame.copy()
    date_source = next((column for column in ["Date", "DATE", "date"] if column in output.columns), None)
    if date_source is None:
        raise PollinationLabError("Daily weather requires a Date column.")
    output["Date"] = pd.to_datetime(output[date_source], errors="coerce")
    output["Tmin (°C)"] = _numeric_from(output, ["Tmin (°C)", "T2M_MIN", "TMIN_C", "MinTemp"])
    output["Tmax (°C)"] = _numeric_from(output, ["Tmax (°C)", "T2M_MAX", "TMAX_C", "MaxTemp"])
    output["Tmean (°C)"] = _numeric_from(output, ["Tmean (°C)", "TMEAN_C", "T2M"])
    output["Tmean (°C)"] = output["Tmean (°C)"].fillna((output["Tmin (°C)"] + output["Tmax (°C)"]) / 2.0)
    output["Rainfall (mm)"] = _numeric_from(output, ["Rainfall (mm)", "PRECIP_MM", "PRECTOTCORR", "Precipitation"] ,0).clip(lower=0)
    output["Solar radiation (MJ/m²/day)"] = _numeric_from(output, ["Solar radiation (MJ/m²/day)", "ALLSKY_SFC_SW_DWN", "Solar radiation"])
    output["Reference ET (mm)"] = _numeric_from(output, ["Reference ET (mm)", "ETo (mm)", "ETO_MM", "ReferenceET"])
    capped_min = output["Tmin (°C)"].clip(lower=base_temperature_c, upper=upper_temperature_c)
    capped_max = output["Tmax (°C)"].clip(lower=base_temperature_c, upper=upper_temperature_c)
    output["GDD daily"] = (((capped_min + capped_max) / 2.0) - base_temperature_c).clip(lower=0)
    output = output.dropna(subset=["Date", "Tmin (°C)", "Tmax (°C)"]).sort_values("Date").drop_duplicates("Date", keep="last")
    return output[["Date", "Tmin (°C)", "Tmax (°C)", "Tmean (°C)", "Rainfall (mm)", "Solar radiation (MJ/m²/day)", "Reference ET (mm)", "GDD daily"]]


def threshold_event_date(dates: Sequence[pd.Timestamp], values: Sequence[float], threshold: float) -> pd.Timestamp | pd.NaT:
    frame = pd.DataFrame({"Date": pd.to_datetime(dates, errors="coerce"), "Value": pd.to_numeric(pd.Series(values), errors="coerce")}).dropna().sort_values("Date")
    if frame.empty:
        return pd.NaT
    reached = frame.loc[frame["Value"].ge(float(threshold))]
    if reached.empty:
        return pd.NaT
    current = reached.iloc[0]
    current_index = frame.index.get_loc(current.name)
    if current_index == 0 or current["Value"] == threshold:
        return pd.Timestamp(current["Date"])
    previous = frame.iloc[current_index - 1]
    if current["Value"] <= previous["Value"]:
        return pd.Timestamp(current["Date"])
    fraction = (threshold - previous["Value"]) / (current["Value"] - previous["Value"])
    return pd.Timestamp(previous["Date"]) + (pd.Timestamp(current["Date"]) - pd.Timestamp(previous["Date"])) * float(np.clip(fraction, 0, 1))


def _gdd_between(weather: pd.DataFrame, start: Any, end: Any) -> float:
    if weather is None or weather.empty or pd.isna(pd.to_datetime(start, errors="coerce")) or pd.isna(pd.to_datetime(end, errors="coerce")):
        return float("nan")
    start_date = pd.Timestamp(start).normalize()
    end_date = pd.Timestamp(end).normalize()
    subset = weather.loc[pd.to_datetime(weather["Date"]).dt.normalize().between(start_date, end_date)]
    return float(pd.to_numeric(subset["GDD daily"], errors="coerce").sum(min_count=1)) if not subset.empty else float("nan")


def compute_plot_synchrony_metrics(observations: pd.DataFrame, weather: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    if observations is None or observations.empty:
        return pd.DataFrame(), pd.DataFrame()
    data = observations.copy()
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    numeric_columns = ["Male shedding (%)", "Pollen intensity (0-5)", "Female silking (%)", "Female receptive silks (%)", "Crop stress score (0-5)", "Male plant height (cm)", "Female plant height (cm)"]
    for column in numeric_columns:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    data["Male activity (%)"] = data["Male shedding (%)"]
    if "Pollen intensity (0-5)" in data.columns:
        intensity_percent = data["Pollen intensity (0-5)"] / 5.0 * 100.0
        data["Male activity (%)"] = data["Male activity (%)"].fillna(intensity_percent)
    data["Female receptive (%)"] = data["Female receptive silks (%)"].fillna(data["Female silking (%)"])
    data["Daily overlap (%)"] = np.minimum(data["Male activity (%)"], data["Female receptive (%)"])
    data["Daily overlap proportion"] = data["Daily overlap (%)"] / 100.0
    weather_prepared = weather if isinstance(weather, pd.DataFrame) and not weather.empty and "GDD daily" in weather.columns else None
    rows: list[dict[str, Any]] = []
    for plot_id, subset in data.groupby("Plot ID"):
        subset = subset.sort_values("Date")
        male_dates = {threshold: threshold_event_date(subset["Date"], subset["Male shedding (%)"], threshold) for threshold in [10, 50, 90]}
        female_dates = {threshold: threshold_event_date(subset["Date"], subset["Female silking (%)"], threshold) for threshold in [10, 50, 90]}
        receptive_dates = {threshold: threshold_event_date(subset["Date"], subset["Female receptive (%)"], threshold) for threshold in [10, 50, 90]}
        male_50 = male_dates[50]
        female_50 = female_dates[50]
        central_gap = (male_50 - female_50).total_seconds() / 86400.0 if pd.notna(male_50) and pd.notna(female_50) else np.nan
        female_receptivity_sum = subset["Female receptive (%)"].sum(min_count=1)
        coverage = 100.0 * subset["Daily overlap (%)"].sum(min_count=1) / female_receptivity_sum if pd.notna(female_receptivity_sum) and female_receptivity_sum > 0 else np.nan
        observed_dates = pd.Series(subset["Date"].dropna().dt.normalize().unique()).sort_values()
        observation_days = int(len(observed_dates))
        if observation_days:
            expected_days = int((pd.Timestamp(observed_dates.iloc[-1]) - pd.Timestamp(observed_dates.iloc[0])).days) + 1
            completeness = 100.0 * observation_days / max(expected_days, 1)
            gaps = pd.Series(observed_dates).diff().dt.days.dropna()
            largest_gap = float(gaps.max()) if not gaps.empty else 1.0
            missing_days = max(expected_days - observation_days, 0)
        else:
            expected_days, completeness, largest_gap, missing_days = 0, np.nan, np.nan, 0
        # Each recorded daily observation contributes at most one day-equivalent. Missing dates are not
        # silently interpolated, so overlap remains an observed-day metric rather than a false elapsed-time integral.
        observed_overlap_days = subset["Daily overlap proportion"].sum(min_count=1)
        female_sowing = pd.to_datetime(subset["Female sowing"].iloc[0], errors="coerce")
        male_sowing = pd.to_datetime(subset["Male sowing"].iloc[0], errors="coerce")
        row = {
            "Plot ID": plot_id,
            "Plot": subset["Plot"].iloc[0],
            "Block": subset["Block"].iloc[0],
            "Treatment": subset["Treatment"].iloc[0],
            "Male offset (days)": subset["Male offset (days)"].iloc[0],
            "Observation days": observation_days,
            "Observation window days": expected_days,
            "Observation completeness (%)": completeness,
            "Missing observation days": missing_days,
            "Largest observation gap (days)": largest_gap,
            "Male 10% date": male_dates[10],
            "Male 50% date": male_50,
            "Male 90% date": male_dates[90],
            "Female 10% silking date": female_dates[10],
            "Female 50% silking date": female_50,
            "Female 90% silking date": female_dates[90],
            "Female 50% receptive date": receptive_dates[50],
            "Synchrony gap (days; male50 - female50)": central_gap,
            "Absolute synchrony gap (days)": abs(central_gap) if pd.notna(central_gap) else np.nan,
            "Overlap area (equivalent full-overlap days)": observed_overlap_days,
            "Overlap metric basis": "Observed days only; missing dates are not interpolated",
            "Female receptivity covered by pollen (%)": coverage,
            "Peak male activity (%)": subset["Male activity (%)"].max(),
            "Peak female receptivity (%)": subset["Female receptive (%)"].max(),
            "Mean crop stress score": subset["Crop stress score (0-5)"].mean(),
            "Mean male plant height (cm)": subset["Male plant height (cm)"].mean() if "Male plant height (cm)" in subset else np.nan,
            "Maximum male plant height (cm)": subset["Male plant height (cm)"].max() if "Male plant height (cm)" in subset else np.nan,
            "Mean female plant height (cm)": subset["Female plant height (cm)"].mean() if "Female plant height (cm)" in subset else np.nan,
            "Maximum female plant height (cm)": subset["Female plant height (cm)"].max() if "Female plant height (cm)" in subset else np.nan,
            "Days from male sowing to male 50%": (male_50.normalize() - male_sowing.normalize()).days if pd.notna(male_50) and pd.notna(male_sowing) else np.nan,
            "Days from female sowing to female 50%": (female_50.normalize() - female_sowing.normalize()).days if pd.notna(female_50) and pd.notna(female_sowing) else np.nan,
        }
        if weather_prepared is not None:
            row["Male GDD to 50%"] = _gdd_between(weather_prepared, male_sowing, male_50)
            row["Female GDD to 50%"] = _gdd_between(weather_prepared, female_sowing, female_50)
            row["Thermal requirement difference (GDD)"] = row["Male GDD to 50%"] - row["Female GDD to 50%"] if pd.notna(row["Male GDD to 50%"]) and pd.notna(row["Female GDD to 50%"]) else np.nan
        rows.append(row)
    return pd.DataFrame(rows), data


def treatment_summary(plot_metrics: pd.DataFrame, harvest: pd.DataFrame | None = None) -> pd.DataFrame:
    if plot_metrics is None or plot_metrics.empty:
        return pd.DataFrame()
    data = plot_metrics.copy()
    if isinstance(harvest, pd.DataFrame) and not harvest.empty:
        columns = [column for column in ["Plot ID", "Seed set (%)", "Seed yield (t/ha)", "Germination (%)", "Genetic purity (%)", "Pure seed (%)", "Kernel rows per ear"] if column in harvest.columns]
        data = data.merge(harvest[columns], on="Plot ID", how="left")
    aggregations: dict[str, tuple[str, str]] = {
        "Treatment units": ("Plot ID", "nunique"),
        "Mean synchrony gap (days)": ("Synchrony gap (days; male50 - female50)", "mean"),
        "Mean absolute gap (days)": ("Absolute synchrony gap (days)", "mean"),
        "Mean overlap days": ("Overlap area (equivalent full-overlap days)", "mean"),
        "Mean receptivity covered (%)": ("Female receptivity covered by pollen (%)", "mean"),
        "Mean stress score": ("Mean crop stress score", "mean"),
    }
    for column, output in [("Seed set (%)", "Mean seed set (%)"), ("Seed yield (t/ha)", "Mean seed yield (t/ha)"), ("Germination (%)", "Mean germination (%)"), ("Genetic purity (%)", "Mean genetic purity (%)"), ("Pure seed (%)", "Mean pure seed (%)"), ("Kernel rows per ear", "Mean kernel rows per ear")]:
        if column in data.columns:
            aggregations[output] = (column, "mean")
    grouping = [column for column in ["Female parent", "Male parent", "Parent combination", "Sowing density (plants/ha)", "Sowing date", "Male–female sowing difference (days)"] if column in data.columns]
    if not grouping:
        grouping = [column for column in ["Treatment", "Male offset (days)"] if column in data.columns]
    result = data.groupby(grouping, dropna=False).agg(**aggregations).reset_index()
    sort_columns = [column for column in ["Sowing date", "Female parent", "Male parent", "Parent combination", "Sowing density (plants/ha)", "Male–female sowing difference (days)", "Male offset (days)"] if column in result.columns]
    return result.sort_values(sort_columns, kind="stable") if sort_columns else result


def _template_identity(plots: pd.DataFrame) -> pd.DataFrame:
    if plots is None or plots.empty:
        return pd.DataFrame(columns=["Treatment unit", "Experiment plot", "Treatment", "Female parent", "Male parent", "Parent combination", "Sowing density (plants/ha)", "Variety / genotype", "Sowing date", "Male–female sowing difference (days)"])
    result = pd.DataFrame()
    result["Treatment unit"] = plots.get("Treatment unit", plots.get("Plot", pd.Series(dtype=str)))
    result["Experiment plot"] = plots.get("Experiment plot", plots.get("Block", pd.Series(dtype=str)))
    for column in ["Treatment", "Female parent", "Male parent", "Parent combination", "Sowing density (plants/ha)", "Variety / genotype", "Sowing date", "Male–female sowing difference (days)"]:
        result[column] = plots[column] if column in plots else np.nan
    # Preserve the legacy import identifier expected by existing databases.
    result["Plot"] = plots.get("Plot", result["Treatment unit"])
    return result


def observation_template(plots: pd.DataFrame, observation_date: date | None = None) -> bytes:
    observation_date = observation_date or date.today()
    identity = _template_identity(plots)
    columns = ["Plot", "Treatment unit", "Experiment plot", "Treatment", "Female parent", "Male parent", "Parent combination", "Sowing density (plants/ha)", "Variety / genotype", "Sowing date", "Male–female sowing difference (days)", "Observation date", "Male plants assessed", "Male shedding (%)", "Pollen intensity (0-5)", "Male plant height (cm)", "Female plants assessed", "Female silking (%)", "Female receptive silks (%)", "Female plant height (cm)", "Crop stress score (0-5)", "Detasselling complete", "Notes"]
    if identity.empty:
        frame = pd.DataFrame(columns=columns)
    else:
        frame = identity.copy()
        frame["Observation date"] = str(observation_date)
        frame["Male plants assessed"] = 20
        frame["Male shedding (%)"] = np.nan
        frame["Pollen intensity (0-5)"] = np.nan
        frame["Male plant height (cm)"] = np.nan
        frame["Female plants assessed"] = 20
        frame["Female silking (%)"] = np.nan
        frame["Female receptive silks (%)"] = np.nan
        frame["Female plant height (cm)"] = np.nan
        frame["Crop stress score (0-5)"] = np.nan
        frame["Detasselling complete"] = False
        frame["Notes"] = ""
        frame = frame[columns]
    return frame.to_csv(index=False).encode("utf-8")


def phenology_event_template(plots: pd.DataFrame) -> bytes:
    identity = _template_identity(plots)
    columns = ["Plot", "Treatment unit", "Experiment plot", "Treatment", "Female parent", "Male parent", "Parent combination", "Sowing density (plants/ha)", "Variety / genotype", "Sowing date", "Male–female sowing difference (days)", "Male flowering initiation date", "Male flowering date", "Female flowering initiation date", "Female flowering date", "Notes"]
    if identity.empty:
        frame = pd.DataFrame(columns=columns)
    else:
        frame = identity.copy()
        for column in ["Male flowering initiation date", "Male flowering date", "Female flowering initiation date", "Female flowering date", "Notes"]:
            frame[column] = ""
        frame = frame[columns]
    return frame.to_csv(index=False).encode("utf-8")


def harvest_template(plots: pd.DataFrame) -> bytes:
    identity = _template_identity(plots)
    columns = ["Plot", "Treatment unit", "Experiment plot", "Treatment", "Female parent", "Male parent", "Parent combination", "Sowing density (plants/ha)", "Variety / genotype", "Sowing date", "Male–female sowing difference (days)", "Harvest date", "Ears harvested", "Kernels per ear", "Kernel rows per ear", "Filled kernels", "Unfilled kernels", "Seed set (%)", "Seed yield (kg/plot)", "Seed yield (t/ha)", "1000-kernel weight (g)", "Germination (%)", "Genetic purity (%)", "Pure seed (%)", "Notes"]
    if identity.empty:
        frame = pd.DataFrame(columns=columns)
    else:
        frame = identity.copy()
        for column in columns:
            if column not in frame:
                frame[column] = "" if column in {"Harvest date", "Notes"} else np.nan
        frame = frame[columns]
    return frame.to_csv(index=False).encode("utf-8")


def leaf_development_template(plots: pd.DataFrame, observation_date: date | None = None) -> bytes:
    """Template for the repeated four-tagged-plant protocol in Laurent et al."""
    observation_date = observation_date or date.today()
    identity = _template_identity(plots)
    rows: list[dict[str, Any]] = []
    for record in identity.to_dict("records"):
        for role, prefix in (("Female", "F"), ("Male", "M")):
            for number in range(1, 5):
                rows.append({
                    **record,
                    "Observation date": observation_date.isoformat(),
                    "Plant tag": f"{prefix}-P{number}",
                    "Parent role": role,
                    "Collared leaf number": np.nan,
                    "Final total leaf number": np.nan,
                    "Ear biomass (g)": np.nan,
                    "Ear length (mm)": np.nan,
                    "Developmental stage": "",
                    "Notes": "",
                })
    columns = [
        "Plot", "Treatment unit", "Experiment plot", "Treatment", "Female parent", "Male parent",
        "Parent combination", "Sowing density (plants/ha)", "Variety / genotype", "Sowing date",
        "Male–female sowing difference (days)", "Observation date", "Plant tag", "Parent role",
        "Collared leaf number", "Final total leaf number", "Ear biomass (g)", "Ear length (mm)",
        "Developmental stage", "Notes",
    ]
    return pd.DataFrame(rows, columns=columns).to_csv(index=False).encode("utf-8")


def parent_physiology_template(parent_lines: Sequence[str] | None = None) -> bytes:
    rows = []
    for name in list(parent_lines or ["F01", "M01"]):
        role = "Male" if str(name).strip().casefold().startswith("m") else "Female"
        rows.append({
            "Parent line": name, "Role": role,
            "tln": DEFAULT_PHYSIOLOGY.tln, "coblf": DEFAULT_PHYSIOLOGY.coblf,
            "eb_r1_g": DEFAULT_PHYSIOLOGY.eb_r1_g,
            "tln_sd": DEFAULT_PHYSIOLOGY.tln_sd, "coblf_sd": DEFAULT_PHYSIOLOGY.coblf_sd,
            "eb_r1_sd": DEFAULT_PHYSIOLOGY.eb_r1_sd,
            "Method": "User-entered informative prior", "Source": "", "Sample size": "", "Notes": "",
        })
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")


def snp_marker_template(parent_lines: Sequence[str] | None = None) -> bytes:
    names = list(parent_lines or ["F01", "M01"])
    rows = []
    for index, name in enumerate(names):
        rows.append({"Parent line": name, "SNP_0001": index % 3, "SNP_0002": (index + 1) % 3, "SNP_0003": (index + 2) % 3})
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")


def _parse_number_levels(text: str, *, integer: bool = False) -> list[float | int]:
    values: list[float | int] = []
    for token in str(text or "").replace(";", ",").replace("\n", ",").split(","):
        token = token.strip()
        if not token:
            continue
        value = float(token)
        values.append(int(round(value)) if integer else float(value))
    return list(dict.fromkeys(values))


def _parse_text_levels(text: str | Sequence[str]) -> list[str]:
    if isinstance(text, Sequence) and not isinstance(text, (str, bytes)):
        tokens = [str(value).strip() for value in text]
    else:
        tokens = [token.strip() for token in str(text or "").replace(";", ",").replace("\n", ",").split(",")]
    return list(dict.fromkeys(token for token in tokens if token))


PARENT_PAIRING_MODES = [
    "All female × male combinations",
    "Match lines by position",
    "Explicit selected pairings",
]


def parse_parent_pairings_text(text: str) -> list[dict[str, str]]:
    """Parse one explicit female|male pairing per line."""
    rows: list[dict[str, str]] = []
    for raw in str(text or "").replace(";", "\n").splitlines():
        token = raw.strip()
        if not token:
            continue
        if "|" in token:
            female, male = token.split("|", 1)
        elif "×" in token:
            female, male = token.split("×", 1)
        else:
            raise PollinationLabError(
                f"Invalid parent pairing: {token}. Use one pair per line as Female line | Male line."
            )
        female = female.strip()
        male = male.strip()
        if not female or not male:
            raise PollinationLabError(f"Both parent names are required in pairing: {token}")
        rows.append({
            "female_parent": female,
            "male_parent": male,
            "parent_combination": f"{female} × {male}",
        })
    unique: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (row["female_parent"], row["male_parent"])
        if key not in seen:
            seen.add(key)
            unique.append(row)
    return unique


def build_parent_combinations(
    female_lines: Sequence[str],
    male_lines: Sequence[str],
    *,
    pairing_mode: str = "All female × male combinations",
    explicit_pairings: Sequence[Mapping[str, Any]] | str | None = None,
) -> list[dict[str, str]]:
    """Create the genotype factor levels from multiple female and male parent lines."""
    females = _parse_text_levels(female_lines)
    males = _parse_text_levels(male_lines)
    if not females or not males:
        raise PollinationLabError("Enter at least one female parent line and one male parent line.")
    mode = str(pairing_mode or PARENT_PAIRING_MODES[0]).strip()
    if mode == "Explicit selected pairings":
        if isinstance(explicit_pairings, str) or explicit_pairings is None:
            rows = parse_parent_pairings_text(str(explicit_pairings or ""))
        else:
            rows = []
            for item in explicit_pairings:
                female = str(item.get("female_parent") or item.get("female") or "").strip()
                male = str(item.get("male_parent") or item.get("male") or "").strip()
                if female and male:
                    rows.append({
                        "female_parent": female,
                        "male_parent": male,
                        "parent_combination": str(item.get("parent_combination") or f"{female} × {male}"),
                    })
        if not rows:
            raise PollinationLabError("Enter at least one explicit parent pairing.")
        unknown = [
            row for row in rows
            if row["female_parent"] not in females or row["male_parent"] not in males
        ]
        if unknown:
            first = unknown[0]
            raise PollinationLabError(
                "Every explicit pairing must use a line listed above. "
                f"Unknown pairing: {first['female_parent']} × {first['male_parent']}"
            )
        return rows
    if mode == "Match lines by position":
        count = max(len(females), len(males))
        if len(females) not in {1, count} or len(males) not in {1, count}:
            raise PollinationLabError(
                "Match-by-position requires equal list lengths, or one side containing a single line to reuse across all pairings."
            )
        return [
            {
                "female_parent": females[0] if len(females) == 1 else females[index],
                "male_parent": males[0] if len(males) == 1 else males[index],
                "parent_combination": f"{females[0] if len(females) == 1 else females[index]} × {males[0] if len(males) == 1 else males[index]}",
            }
            for index in range(count)
        ]
    return [
        {
            "female_parent": female,
            "male_parent": male,
            "parent_combination": f"{female} × {male}",
        }
        for female, male in product(females, males)
    ]


def _parse_date_levels(text: str, fallback: date | str) -> list[str]:
    tokens = [token.strip() for token in str(text or "").replace(";", ",").replace("\n", ",").split(",") if token.strip()]
    if not tokens:
        tokens = [str(fallback)]
    parsed: list[str] = []
    for token in tokens:
        value = pd.to_datetime(token, errors="coerce")
        if pd.isna(value):
            raise PollinationLabError(f"Invalid sowing date level: {token}. Use YYYY-MM-DD.")
        parsed.append(value.date().isoformat())
    return list(dict.fromkeys(parsed))


def factorial_treatment_combinations(
    *,
    densities: Sequence[float],
    sowing_dates: Sequence[str],
    offsets_days: Sequence[int],
    parent_combinations: Sequence[Mapping[str, Any]] | None = None,
    varieties: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    """Build the full factorial design while preserving separate female and male identities."""
    densities = list(densities) or [np.nan]
    sowing_dates = list(sowing_dates)
    offsets_days = [int(value) for value in offsets_days]
    if not sowing_dates or not offsets_days:
        raise PollinationLabError("At least one sowing date and one male–female sowing-date difference are required.")
    genotype_levels: list[dict[str, str]] = []
    if parent_combinations:
        for item in parent_combinations:
            female = str(item.get("female_parent") or item.get("female") or "").strip()
            male = str(item.get("male_parent") or item.get("male") or "").strip()
            combination = str(item.get("parent_combination") or item.get("variety_genotype") or "").strip()
            if not combination:
                combination = f"{female} × {male}".strip(" ×")
            genotype_levels.append({
                "female_parent": female,
                "male_parent": male,
                "parent_combination": combination,
            })
    else:
        genotype_levels = [
            {"female_parent": "", "male_parent": "", "parent_combination": str(value or "")}
            for value in (list(varieties or []) or [""])
        ]
    rows: list[dict[str, Any]] = []
    for index, (density, genotype, sowing_date, offset) in enumerate(
        product(densities, genotype_levels, sowing_dates, offsets_days), start=1
    ):
        sign = f"+{offset}" if offset > 0 else str(offset)
        density_label = f"{float(density):,.0f}/ha" if pd.notna(density) else "density NA"
        genotype_label = str(genotype.get("parent_combination") or "genotype NA")
        label = f"T{index:03d} · {genotype_label} · {density_label} · {sowing_date} · Δ{sign} d"
        rows.append({
            "treatment_code": f"T{index:03d}",
            "treatment_label": label,
            "sowing_density_plants_ha": None if pd.isna(density) else float(density),
            "female_parent": str(genotype.get("female_parent") or ""),
            "male_parent": str(genotype.get("male_parent") or ""),
            "parent_combination": genotype_label,
            "variety_genotype": genotype_label,
            "sowing_date": str(sowing_date),
            "male_sowing_offset_days": int(offset),
        })
    return rows


def _spatial_sort_geometries(geometries: Sequence[Mapping[str, Any]], row_tolerance_factor: float = 0.45) -> list[dict[str, Any]]:
    valid = [validate_aoi_geometry(item) for item in geometries]
    if len(valid) < 2:
        return valid
    centres = [(geometry_centroid(item)[0], geometry_centroid(item)[1], item) for item in valid]
    latitudes = sorted(value[0] for value in centres)
    diffs = [abs(b-a) for a,b in zip(latitudes[:-1], latitudes[1:]) if abs(b-a) > 0]
    tolerance = (float(np.median(diffs)) * row_tolerance_factor) if diffs else 1e-7
    rows: list[list[tuple[float,float,dict[str,Any]]]] = []
    for lat, lon, geom in sorted(centres, key=lambda value: (-value[0], value[1])):
        if not rows or abs(lat - float(np.mean([item[0] for item in rows[-1]]))) > tolerance:
            rows.append([(lat, lon, geom)])
        else:
            rows[-1].append((lat, lon, geom))
    ordered: list[dict[str, Any]] = []
    for row in rows:
        ordered.extend(item[2] for item in sorted(row, key=lambda value: value[1]))
    return ordered


def experiment_plot_geometries(plots: pd.DataFrame) -> list[dict[str, Any]]:
    if plots is None or plots.empty or "Geometry" not in plots:
        return []
    group_col = "Experiment plot" if "Experiment plot" in plots else "Block"
    features: list[dict[str, Any]] = []
    for label, group in plots.groupby(group_col, sort=False):
        geometries = [item for item in group["Geometry"].tolist() if isinstance(item, Mapping)]
        if not geometries:
            continue
        parent_geometry = geometry_union(geometries)
        if shape is not None and mapping is not None:
            try:
                parent_geometry = validate_aoi_geometry(mapping(shape(parent_geometry).convex_hull))
            except Exception:
                pass
        features.append({"label": str(label), "geometry": parent_geometry, "units": int(len(group))})
    return features


def validate_treatment_unit_geometries(
    geometries: Sequence[Mapping[str, Any]],
    *,
    field_geometry: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Validate treatment-unit geometry integrity without allowing spatial overlap.

    Shared borders are valid. Any positive-area overlap or exact duplicate is rejected because
    independent experimental units must not occupy the same physical area.
    """
    validated = [validate_aoi_geometry(item) for item in geometries]
    if field_geometry is not None:
        outside = [index + 1 for index, geometry in enumerate(validated) if not plot_is_inside_field(geometry, field_geometry)]
        if outside:
            raise PollinationLabError(
                "These treatment units extend outside the experiment field: " + ", ".join(map(str, outside))
            )
    if shape is None:
        raise PollinationLabError("Shapely is required to verify treatment-unit overlap safely.")
    shaped = [shape(item) for item in validated]
    conflicts: list[str] = []
    for left in range(len(shaped)):
        for right in range(left + 1, len(shaped)):
            intersection = shaped[left].intersection(shaped[right])
            if intersection.is_empty:
                continue
            # Touching boundaries have zero area and are valid. Positive area means the same
            # physical ground has been assigned to two experimental units.
            if float(intersection.area) > 1e-12:
                conflicts.append(f"{left + 1}↔{right + 1}")
                if len(conflicts) >= 12:
                    break
        if len(conflicts) >= 12:
            break
    if conflicts:
        suffix = " (first 12 shown)" if len(conflicts) >= 12 else ""
        raise PollinationLabError(
            "Treatment-unit polygons overlap. Shared borders are allowed, but positive-area overlaps are not. "
            + "Conflicting units: " + ", ".join(conflicts) + suffix
        )
    return validated


def randomised_plot_assignments(
    *,
    geometries: Sequence[Mapping[str, Any]],
    treatments: Sequence[Mapping[str, Any]] | None = None,
    offsets_days: Sequence[int] | None = None,
    blocks: int,
    replicates_per_treatment: int,
    female_sowing_date: date | str,
    seed: int,
    field_geometry: Mapping[str, Any] | None = None,
    preserve_geometry_order: bool = False,
    minimise_adjacent_identical: bool = False,
    randomisation_attempts: int = 1,
) -> list[dict[str, Any]]:
    if treatments is None:
        offsets = [int(value) for value in (offsets_days or [])]
        treatments = factorial_treatment_combinations(
            densities=[np.nan], varieties=[""],
            sowing_dates=[str(pd.Timestamp(female_sowing_date).date())], offsets_days=offsets
        )
    treatment_levels = [dict(item) for item in treatments]
    if not treatment_levels:
        raise PollinationLabError("At least one treatment combination is required.")
    block_count = int(blocks)
    repeats = int(replicates_per_treatment)
    units_per_block = len(treatment_levels) * repeats
    expected = block_count * units_per_block
    if len(geometries) != expected:
        raise PollinationLabError(f"Create exactly {expected} treatment-unit polygons; {len(geometries)} geometries are currently captured.")
    ordered_geometries = list(geometries) if preserve_geometry_order else _spatial_sort_geometries(geometries)
    valid_geometries = validate_treatment_unit_geometries(ordered_geometries, field_geometry=field_geometry)
    rng = np.random.default_rng(int(seed))
    rows: list[dict[str, Any]] = []
    global_index = 0
    attempts = max(1, min(int(randomisation_attempts), 500))
    for block in range(1, block_count + 1):
        base_assignments: list[dict[str, Any]] = []
        for replicate in range(1, repeats + 1):
            for treatment in treatment_levels:
                base_assignments.append({**treatment, "replicate": replicate})

        block_start = (block - 1) * units_per_block
        block_geometries = valid_geometries[block_start:block_start + units_per_block]
        adjacency_pairs: list[tuple[int, int]] = []
        if minimise_adjacent_identical and shape is not None:
            shaped = [shape(item) for item in block_geometries]
            for left in range(len(shaped)):
                for right in range(left + 1, len(shaped)):
                    try:
                        if shaped[left].touches(shaped[right]):
                            adjacency_pairs.append((left, right))
                    except Exception:
                        continue

        best_assignments = None
        best_score = None
        for _attempt in range(attempts if minimise_adjacent_identical else 1):
            candidate = [base_assignments[int(index)] for index in rng.permutation(len(base_assignments))]
            if not adjacency_pairs:
                best_assignments = candidate
                break
            score = 0
            for left, right in adjacency_pairs:
                left_label = str(candidate[left].get("treatment_label") or candidate[left].get("treatment_code") or "")
                right_label = str(candidate[right].get("treatment_label") or candidate[right].get("treatment_code") or "")
                if left_label == right_label:
                    score += 1
            if best_score is None or score < best_score:
                best_score = score
                best_assignments = candidate
                if score == 0:
                    break
        assignments = best_assignments or [base_assignments[int(index)] for index in rng.permutation(len(base_assignments))]
        for unit_index, treatment in enumerate(assignments, start=1):
            global_index += 1
            sowing = pd.Timestamp(treatment.get("sowing_date") or female_sowing_date).date()
            offset = int(treatment.get("male_sowing_offset_days", 0))
            male_date = sowing + pd.Timedelta(days=offset)
            unit_label = f"B{block:02d}-U{unit_index:03d}"
            female_parent = str(treatment.get("female_parent") or "")
            male_parent = str(treatment.get("male_parent") or "")
            parent_combination = str(
                treatment.get("parent_combination")
                or treatment.get("variety_genotype")
                or f"{female_parent} × {male_parent}".strip(" ×")
            )
            factors = {
                "Female parent": female_parent,
                "Male parent": male_parent,
                "Parent combination": parent_combination,
                "Sowing density (plants/ha)": treatment.get("sowing_density_plants_ha"),
                "Variety / genotype": parent_combination,
                "Sowing date": sowing.isoformat(),
                "Male–female sowing difference (days)": offset,
            }
            rows.append({
                "plot_label": unit_label, "experiment_plot_label": f"B{block:02d}",
                "treatment_unit_label": unit_label, "block": block,
                "replicate": int(treatment.get("replicate", 1)),
                "treatment_label": str(treatment.get("treatment_label") or treatment.get("treatment_code") or unit_label),
                "male_sowing_offset_days": offset,
                "sowing_density_plants_ha": treatment.get("sowing_density_plants_ha"),
                "female_parent": female_parent, "male_parent": male_parent,
                "parent_combination": parent_combination,
                "variety_genotype": parent_combination,
                "sowing_date": sowing.isoformat(), "factor_levels": factors,
                "female_sowing_date": sowing.isoformat(),
                "male_sowing_date": pd.Timestamp(male_date).date().isoformat(),
                "geometry": valid_geometries[global_index - 1],
            })
    return rows


def _summarise_weather_window(subset: pd.DataFrame, prefix: str) -> dict[str, float]:
    if subset is None or subset.empty:
        return {}
    tmax = pd.to_numeric(subset["Tmax (°C)"], errors="coerce")
    return {
        f"{prefix} weather days": float(subset["Date"].nunique()),
        f"{prefix} GDD": float(pd.to_numeric(subset["GDD daily"], errors="coerce").sum(min_count=1)),
        f"{prefix} rainfall (mm)": float(pd.to_numeric(subset["Rainfall (mm)"], errors="coerce").sum(min_count=1)),
        f"{prefix} mean temperature (°C)": float(pd.to_numeric(subset["Tmean (°C)"], errors="coerce").mean()),
        f"{prefix} maximum temperature (°C)": float(tmax.max()),
        f"{prefix} heat days ≥35°C": float((tmax >= 35).sum()),
        f"{prefix} reference ET (mm)": float(pd.to_numeric(subset["Reference ET (mm)"], errors="coerce").sum(min_count=1)),
        f"{prefix} solar radiation": float(pd.to_numeric(subset["Solar radiation (MJ/m²/day)"], errors="coerce").sum(min_count=1)),
    }


def _weather_features(weather: pd.DataFrame, female_sowing: Any, male_sowing: Any, analysis_end: Any) -> dict[str, float]:
    if weather is None or weather.empty:
        return {}
    dates = pd.to_datetime(weather["Date"], errors="coerce").dt.normalize()
    start = min(pd.Timestamp(female_sowing), pd.Timestamp(male_sowing)).normalize()
    fixed_30_end = start + pd.Timedelta(days=29)
    fixed_60_start = start + pd.Timedelta(days=30)
    fixed_60_end = start + pd.Timedelta(days=59)
    first_30 = weather.loc[dates.between(start, fixed_30_end)].copy()
    days_31_60 = weather.loc[dates.between(fixed_60_start, fixed_60_end)].copy()
    features = {}
    features.update(_summarise_weather_window(first_30, "First 30d"))
    features.update(_summarise_weather_window(days_31_60, "Days 31–60"))
    end = pd.to_datetime(analysis_end, errors="coerce")
    if pd.notna(end):
        event = pd.Timestamp(end).normalize()
        retrospective = weather.loc[dates.between(start, event)].copy()
        features.update(_summarise_weather_window(retrospective, "Through observed female50"))
        preflower = weather.loc[dates.between(event - pd.Timedelta(days=13), event)].copy()
        flowering_window = weather.loc[dates.between(event - pd.Timedelta(days=7), event + pd.Timedelta(days=7))].copy()
        features.update(_summarise_weather_window(preflower, "14d before observed female50"))
        features.update(_summarise_weather_window(flowering_window, "Retrospective flowering ±7d"))
    return features


def _root_zone_features(root_zone: pd.DataFrame | None, start: Any, female50: Any) -> dict[str, float]:
    if not isinstance(root_zone, pd.DataFrame) or root_zone.empty:
        return {}
    date_column = "Date" if "Date" in root_zone.columns else "DATE" if "DATE" in root_zone.columns else None
    if date_column is None:
        return {}
    frame = root_zone.copy()
    frame["_date"] = pd.to_datetime(frame[date_column], errors="coerce").dt.normalize()
    start_date = pd.Timestamp(start).normalize()

    def summarise(subset: pd.DataFrame, prefix: str) -> dict[str, float]:
        if subset.empty:
            return {}
        ks = pd.to_numeric(subset.get("Ks"), errors="coerce")
        depletion = pd.to_numeric(subset.get("Relative depletion"), errors="coerce")
        stress = pd.Series(subset.get("Stress day", False), index=subset.index).fillna(False).astype(bool)
        return {
            f"{prefix} mean Ks": float(ks.mean()),
            f"{prefix} minimum Ks": float(ks.min()),
            f"{prefix} stress days": float(stress.sum()),
            f"{prefix} maximum relative depletion": float(depletion.max()),
            f"{prefix} actual ETc (mm)": float(pd.to_numeric(subset.get("Actual ETc (mm)"), errors="coerce").sum(min_count=1)),
        }

    features = {}
    features.update(summarise(frame.loc[frame["_date"].between(start_date, start_date + pd.Timedelta(days=29))], "First 30d root-zone"))
    features.update(summarise(frame.loc[frame["_date"].between(start_date + pd.Timedelta(days=30), start_date + pd.Timedelta(days=59))], "Days 31–60 root-zone"))
    event = pd.to_datetime(female50, errors="coerce")
    if pd.notna(event):
        event_date = pd.Timestamp(event).normalize()
        features.update(summarise(frame.loc[frame["_date"].between(event_date - pd.Timedelta(days=13), event_date)], "14d before female50 root-zone"))
    return features

def satellite_feature_table(links: pd.DataFrame) -> pd.DataFrame:
    if links is None or links.empty:
        return pd.DataFrame()
    rows = []
    for _, link in links.iterrows():
        records = _loads(link.get("Time series"), [])
        frame = pd.DataFrame(records)
        if frame.empty:
            continue
        if "Date" in frame.columns:
            frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
        usable = frame.loc[frame.get("Status", "Usable").astype(str).eq("Usable")].copy() if "Status" in frame.columns else frame
        features: dict[str, Any] = {
            "Satellite target": link.get("Target"),
            "Satellite observations": int(len(usable)),
            "Latest satellite date": usable["Date"].max() if "Date" in usable.columns and not usable.empty else pd.NaT,
        }
        for index_name in ["NDVI", "EVI", "NDMI", "NDRE"]:
            column = next((candidate for candidate in [f"{index_name} Mean", index_name] if candidate in usable.columns), None)
            if column:
                series = pd.to_numeric(usable[column], errors="coerce")
                features[f"Mean {index_name}"] = series.mean()
                features[f"Maximum {index_name}"] = series.max()
                features[f"Latest {index_name}"] = series.dropna().iloc[-1] if series.notna().any() else np.nan
        for plot_id in _loads(link.get("Plot IDs"), []):
            rows.append({"Plot ID": plot_id, **features})
    return pd.DataFrame(rows)


def build_model_table(
    *,
    trial: Mapping[str, Any],
    plots: pd.DataFrame,
    plot_metrics: pd.DataFrame,
    phenology_events: pd.DataFrame | None,
    harvest: pd.DataFrame,
    weather: pd.DataFrame,
    satellite_links_frame: pd.DataFrame,
    root_zone: pd.DataFrame | None = None,
) -> pd.DataFrame:
    if plots is None or plots.empty:
        return pd.DataFrame()
    base_columns = ["Plot ID", "Plot", "Treatment unit", "Experiment plot", "Block", "Replicate", "Treatment", "Female parent", "Male parent", "Parent combination", "Sowing density (plants/ha)", "Variety / genotype", "Sowing date", "Male–female sowing difference (days)", "Male offset (days)", "Female sowing", "Male sowing", "Area (ha)"]
    table = plots[[column for column in base_columns if column in plots.columns]].copy()
    if isinstance(plot_metrics, pd.DataFrame) and not plot_metrics.empty:
        table = table.merge(plot_metrics.drop(columns=["Plot", "Block", "Treatment", "Male offset (days)"], errors="ignore"), on="Plot ID", how="left")
    if isinstance(phenology_events, pd.DataFrame) and not phenology_events.empty:
        table = table.merge(phenology_events.drop(columns=["Plot", "Block", "Treatment", "Male offset (days)"], errors="ignore"), on="Plot ID", how="left")
    if isinstance(harvest, pd.DataFrame) and not harvest.empty:
        table = table.merge(harvest.drop(columns=["Plot", "Block", "Treatment", "Male offset (days)"], errors="ignore"), on="Plot ID", how="left")
    for label, sowing_column in [
        ("Male flowering initiation date", "Male sowing"),
        ("Male flowering date", "Male sowing"),
        ("Female flowering initiation date", "Female sowing"),
        ("Female flowering date", "Female sowing"),
    ]:
        if label in table.columns:
            prefix = label.replace(" date", "")
            table[f"Days from sowing to {prefix.casefold()}"] = (pd.to_datetime(table[label], errors="coerce") - pd.to_datetime(table[sowing_column], errors="coerce")).dt.total_seconds() / 86400.0
    if "Female parent" not in table:
        table["Female parent"] = trial.get("female_parent")
    if "Male parent" not in table:
        table["Male parent"] = trial.get("male_parent")
    if "Parent combination" not in table:
        table["Parent combination"] = table["Female parent"].astype(str) + " × " + table["Male parent"].astype(str)
    table["Site"] = trial.get("site_name")
    table["Season year"] = trial.get("season_year")
    table["Planting density (plants/ha)"] = trial.get("planting_density_plants_ha")
    table["Row ratio"] = trial.get("row_ratio")
    weather_rows = []
    for _, row in table.iterrows():
        analysis_end = row.get("Female 50% silking date")
        if pd.isna(pd.to_datetime(analysis_end, errors="coerce")):
            analysis_end = pd.to_datetime(weather["Date"], errors="coerce").max() if isinstance(weather, pd.DataFrame) and not weather.empty else row.get("Female sowing")
        earliest_sowing = min(pd.Timestamp(row.get("Female sowing")), pd.Timestamp(row.get("Male sowing")))
        combined_features = _weather_features(weather, row.get("Female sowing"), row.get("Male sowing"), analysis_end)
        combined_features.update(_root_zone_features(root_zone, earliest_sowing, analysis_end))
        weather_rows.append(combined_features)
    if weather_rows:
        table = pd.concat([table.reset_index(drop=True), pd.DataFrame(weather_rows)], axis=1)
    satellite = satellite_feature_table(satellite_links_frame)
    if not satellite.empty:
        table = table.merge(satellite, on="Plot ID", how="left")
    return table


@dataclass
class ModelFitResult:
    metrics: pd.DataFrame
    predictions: pd.DataFrame
    models: dict[str, Pipeline]
    feature_columns: list[str]
    categorical_columns: list[str]
    numerical_columns: list[str]
    training_frame: pd.DataFrame
    target: str


def fit_predictive_models(
    frame: pd.DataFrame,
    *,
    target: str,
    group_column: str | None,
    feature_columns: Sequence[str],
    folds: int = 5,
    random_state: int = 42,
) -> ModelFitResult:
    if frame is None or frame.empty or target not in frame.columns:
        raise PollinationLabError("The selected model target is unavailable.")
    selected = [column for column in feature_columns if column in frame.columns and column != target]
    if not selected:
        raise PollinationLabError("Select at least one predictor.")
    data = frame[selected + [target] + ([group_column] if group_column and group_column in frame.columns and group_column not in selected else [])].copy()
    data[target] = pd.to_numeric(data[target], errors="coerce")
    data = data.dropna(subset=[target]).reset_index(drop=True)
    if len(data) < 8:
        raise PollinationLabError("At least eight complete target observations are required for model comparison.")
    categorical = [column for column in selected if not pd.api.types.is_numeric_dtype(data[column])]
    numerical = [column for column in selected if column not in categorical]
    numeric_pipeline = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
    categorical_pipeline = Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))])
    preprocessor = ColumnTransformer([("numeric", numeric_pipeline, numerical), ("categorical", categorical_pipeline, categorical)])
    candidates = {
        "Ridge": Ridge(alpha=1.0),
        "Random forest": RandomForestRegressor(n_estimators=400, min_samples_leaf=2, random_state=random_state, n_jobs=-1),
    }
    if group_column and group_column in data.columns and data[group_column].nunique() >= 3:
        groups = data[group_column].astype(str).to_numpy()
        splitter = GroupKFold(n_splits=min(int(folds), data[group_column].nunique()))
        split_list = list(splitter.split(data, groups=groups))
        validation_design = f"Grouped CV by {group_column}"
    else:
        splitter = KFold(n_splits=min(max(2, int(folds)), len(data)), shuffle=True, random_state=random_state)
        split_list = list(splitter.split(data))
        validation_design = "K-fold CV"
    prediction_rows = []
    metric_rows = []
    fitted_models: dict[str, Pipeline] = {}
    X = data[selected]
    y = data[target].to_numpy(float)
    for model_name, estimator in candidates.items():
        predictions = np.full(len(data), np.nan)
        for train_index, test_index in split_list:
            pipeline = Pipeline([("preprocess", preprocessor), ("model", estimator)])
            pipeline.fit(X.iloc[train_index], y[train_index])
            predictions[test_index] = pipeline.predict(X.iloc[test_index])
        complete = np.isfinite(predictions) & np.isfinite(y)
        mae = mean_absolute_error(y[complete], predictions[complete])
        rmse = math.sqrt(mean_squared_error(y[complete], predictions[complete]))
        r2 = r2_score(y[complete], predictions[complete]) if complete.sum() >= 3 and np.std(y[complete]) > 0 else np.nan
        metric_rows.append({"Model": model_name, "N": int(complete.sum()), "MAE": mae, "RMSE": rmse, "R²": r2, "Validation design": validation_design})
        result = data.copy()
        result["Observed"] = y
        result["Prediction"] = predictions
        result["Residual"] = predictions - y
        result["Model"] = model_name
        prediction_rows.append(result)
        final_pipeline = Pipeline([("preprocess", preprocessor), ("model", estimator)])
        final_pipeline.fit(X, y)
        fitted_models[model_name] = final_pipeline
    return ModelFitResult(
        metrics=pd.DataFrame(metric_rows).sort_values("RMSE"),
        predictions=pd.concat(prediction_rows, ignore_index=True),
        models=fitted_models,
        feature_columns=list(selected),
        categorical_columns=categorical,
        numerical_columns=numerical,
        training_frame=data,
        target=target,
    )


def optimise_sowing_offset(
    fit: ModelFitResult,
    *,
    model_name: str,
    offset_column: str = "Male offset (days)",
    minimum_offset: int = -10,
    maximum_offset: int = 10,
    scenario_values: Mapping[str, Any] | None = None,
    maximise: bool | None = None,
    objective: str | None = None,
) -> pd.DataFrame:
    if model_name not in fit.models:
        raise PollinationLabError("Selected model is unavailable.")
    if offset_column not in fit.feature_columns:
        raise PollinationLabError("The sowing-offset predictor was not included in the fitted model.")
    scenario_values = dict(scenario_values or {})
    base: dict[str, Any] = {}
    for column in fit.feature_columns:
        if column in scenario_values:
            base[column] = scenario_values[column]
        elif column in fit.numerical_columns:
            base[column] = pd.to_numeric(fit.training_frame[column], errors="coerce").median()
        else:
            modes = fit.training_frame[column].dropna().astype(str).mode()
            base[column] = modes.iloc[0] if not modes.empty else "Unknown"
    rows = []
    for offset in range(int(minimum_offset), int(maximum_offset) + 1):
        row = dict(base)
        row[offset_column] = offset
        rows.append(row)
    candidates = pd.DataFrame(rows)
    candidates["Predicted outcome"] = fit.models[model_name].predict(candidates[fit.feature_columns])
    candidates["Male offset (days)"] = candidates[offset_column]
    if objective is None:
        objective = "maximise" if maximise is not False else "minimise"
    objective = str(objective).strip().casefold()
    if objective == "closest to zero":
        candidates["Optimisation score"] = -candidates["Predicted outcome"].abs()
    elif objective == "minimise":
        candidates["Optimisation score"] = -candidates["Predicted outcome"]
    else:
        candidates["Optimisation score"] = candidates["Predicted outcome"]
    candidates["Recommended"] = False
    best_index = candidates["Optimisation score"].idxmax()
    candidates.loc[best_index, "Recommended"] = True
    candidates["Objective"] = objective
    return candidates


def thermal_time_forecast(
    *,
    weather: pd.DataFrame,
    sowing_date: Any,
    target_gdd: float,
    as_of: Any | None = None,
    recent_days: int = 7,
) -> dict[str, Any]:
    if weather is None or weather.empty:
        raise PollinationLabError("Stored trial weather is required for the thermal-time forecast.")
    as_of = pd.Timestamp(as_of or pd.to_datetime(weather["Date"]).max()).normalize()
    sowing = pd.Timestamp(sowing_date).normalize()
    subset = weather.loc[pd.to_datetime(weather["Date"]).dt.normalize().between(sowing, as_of)].copy()
    accumulated = float(pd.to_numeric(subset["GDD daily"], errors="coerce").sum(min_count=1)) if not subset.empty else 0.0
    remaining = max(0.0, float(target_gdd) - accumulated)
    recent = weather.loc[pd.to_datetime(weather["Date"]).dt.normalize().le(as_of)].tail(max(3, int(recent_days)))
    recent_rate = float(pd.to_numeric(recent["GDD daily"], errors="coerce").mean()) if not recent.empty else np.nan
    days_remaining = remaining / recent_rate if np.isfinite(recent_rate) and recent_rate > 0 else np.nan
    predicted = as_of + pd.Timedelta(days=float(days_remaining)) if np.isfinite(days_remaining) else pd.NaT
    return {
        "Sowing date": sowing.date().isoformat(),
        "As of": as_of.date().isoformat(),
        "Target GDD": float(target_gdd),
        "Accumulated GDD": accumulated,
        "Remaining GDD": remaining,
        "Recent mean GDD/day": recent_rate,
        "Estimated days remaining": days_remaining,
        "Estimated event date": predicted.date().isoformat() if pd.notna(predicted) else None,
        "Method": f"Recent {max(3, int(recent_days))}-day mean thermal-time rate; not a weather forecast",
    }


# -----------------------------------------------------------------------------
# Streamlit UI
# -----------------------------------------------------------------------------


def _state_default(key: str, value: Any) -> None:
    if key not in st.session_state:
        st.session_state[key] = value


def initialise_ui_state() -> None:
    defaults = {
        "pollination_active_trial_id": None,
        "pollination_field_geometry": None,
        "pollination_pending_plot_geometries": [],
        "pollination_model_fit": None,
        "pollination_model_table": None,
        "pollination_plot_metrics": None,
        "pollination_daily_curves": None,
        "pollination_optimizer": None,
        "pollination_satellite_target": None,
    }
    for key, value in defaults.items():
        _state_default(key, value)


def _activate_trial_state(trial_id: str) -> None:
    previous = st.session_state.get("pollination_active_trial_id")
    if previous != trial_id:
        for key, value in {
            "pollination_model_fit": None,
            "pollination_model_table": None,
            "pollination_plot_metrics": None,
            "pollination_daily_curves": None,
            "pollination_optimizer": None,
            "pollination_satellite_target": None,
            "pollination_satellite_plots": [],
            "pollination_pending_plot_geometries": [],
        }.items():
            st.session_state[key] = value
    st.session_state.pollination_active_trial_id = trial_id


def _active_trial(db: PollinationDatabase) -> dict[str, Any] | None:
    trial_id = st.session_state.get("pollination_active_trial_id")
    if not trial_id:
        return None
    try:
        return db.get_trial(trial_id)
    except Exception:
        st.session_state.pollination_active_trial_id = None
        return None


def _trial_selector(db: PollinationDatabase, key: str) -> dict[str, Any] | None:
    trials = db.list_trials()
    if trials.empty:
        st.info("No pollination trial has been created yet.")
        return None
    labels = {_trial_display_label(row): row["Trial ID"] for _, row in trials.iterrows()}
    current_id = st.session_state.get("pollination_active_trial_id")
    options = list(labels)
    index = next((i for i, label in enumerate(options) if labels[label] == current_id), 0)
    selected = st.selectbox("Active pollination trial", options, index=index, key=key)
    trial_id = labels[selected]
    _activate_trial_state(trial_id)
    return db.get_trial(trial_id)


def _parse_geojson_upload(uploaded) -> dict[str, Any] | None:
    if uploaded is None:
        return None
    try:
        payload = json.loads(uploaded.getvalue().decode("utf-8"))
        return validate_aoi_geometry(payload)
    except Exception as error:
        raise PollinationLabError(f"GeoJSON could not be read: {error}") from error



def _field_library(field_db) -> pd.DataFrame:
    if field_db is None:
        return pd.DataFrame()
    try:
        fields = field_db.fields()
    except Exception:
        return pd.DataFrame()
    return fields if isinstance(fields, pd.DataFrame) else pd.DataFrame()


def _field_label(row: Mapping[str, Any]) -> str:
    farm = str(row.get("farm_name") or "Farm")
    name = str(row.get("name") or row.get("field_id") or "Field")
    area = pd.to_numeric(pd.Series([row.get("area_ha")]), errors="coerce").iloc[0]
    area_text = f" · {float(area):,.3f} ha" if pd.notna(area) else ""
    code = str(row.get("code") or "").strip()
    code_text = f" [{code}]" if code else ""
    return f"{farm} · {name}{code_text}{area_text}"


def _select_mapped_field(field_db, *, key: str, label: str = "Mapped field") -> dict[str, Any] | None:
    fields = _field_library(field_db)
    if fields.empty:
        st.warning("No mapped fields exist yet. Create one under Fields & Operations → Fields & Maps.")
        return None
    labels = {_field_label(row): str(row["field_id"]) for _, row in fields.iterrows()}
    selected_label = st.selectbox(label, list(labels), key=key, help="The exact saved polygon, area, centroid and geometry fingerprint are inherited from this field.")
    return field_db.field(labels[selected_label])


def _spatial_comparison_map(trial_geometry: Mapping[str, Any] | None, field_geometry: Mapping[str, Any] | None, *, key: str) -> None:
    geometry = field_geometry or trial_geometry
    if not geometry:
        return
    lat, lon = geometry_centroid(geometry)
    map_object = folium.Map(location=[lat, lon], zoom_start=16, tiles=None, control_scale=True)
    _add_base_layers(map_object, satellite_default=True, collapsed=False)
    _add_distance_measurement(map_object)
    if field_geometry:
        folium.GeoJson(field_geometry, name="Mapped field", style_function=lambda _: {"color": "#0f766e", "weight": 4, "fillOpacity": 0.05}).add_to(map_object)
    if trial_geometry:
        folium.GeoJson(trial_geometry, name="Trial boundary", style_function=lambda _: {"color": "#dc2626", "weight": 3, "dashArray": "7 5", "fillOpacity": 0.04}).add_to(map_object)
    folium.LayerControl(collapsed=False).add_to(map_object)
    st_folium(map_object, height=430, use_container_width=True, key=key, returned_objects=[])


def generate_measured_plot_grid(
    *,
    field_geometry: Mapping[str, Any],
    plot_count: int,
    columns: int,
    plot_width_m: float,
    plot_length_m: float,
    column_gap_m: float,
    row_gap_m: float,
    orientation_deg_from_north: float,
    offset_east_m: float = 0.0,
    offset_north_m: float = 0.0,
) -> list[dict[str, Any]]:
    """Generate dimension-controlled rectangular trial plots centred in a mapped field."""
    if any(item is None for item in [shape, mapping, transform, affinity, box]):
        raise PollinationLabError("Measured plot generation requires Shapely. Run INSTALL_SATELLITE_DEPENDENCIES.bat.")
    field_geojson = validate_aoi_geometry(field_geometry)
    field_shape = shape(field_geojson)
    if field_shape.is_empty:
        raise PollinationLabError("The mapped field boundary is empty.")
    count = int(plot_count)
    cols = max(1, min(int(columns), count))
    rows = int(math.ceil(count / cols))
    width = float(plot_width_m)
    length = float(plot_length_m)
    gap_x = max(0.0, float(column_gap_m))
    gap_y = max(0.0, float(row_gap_m))
    if count < 1 or width <= 0 or length <= 0:
        raise PollinationLabError("Plot count, width and length must be positive.")
    centre_lat, centre_lon = geometry_centroid(field_geojson)
    metres_per_lat = 111_320.0
    metres_per_lon = max(1.0, 111_320.0 * math.cos(math.radians(centre_lat)))

    def to_local(x, y, z=None):
        return ((x - centre_lon) * metres_per_lon, (y - centre_lat) * metres_per_lat)

    def to_geo(x, y, z=None):
        return (centre_lon + x / metres_per_lon, centre_lat + y / metres_per_lat)

    local_field = transform(to_local, field_shape)
    total_width = cols * width + max(0, cols - 1) * gap_x
    total_height = rows * length + max(0, rows - 1) * gap_y
    start_x = -total_width / 2.0
    start_y = total_height / 2.0
    angle = 90.0 - float(orientation_deg_from_north)
    output: list[dict[str, Any]] = []
    outside: list[int] = []
    for index in range(count):
        row = index // cols
        col = index % cols
        x0 = start_x + col * (width + gap_x)
        y1 = start_y - row * (length + gap_y)
        rectangle = box(x0, y1 - length, x0 + width, y1)
        rectangle = affinity.rotate(rectangle, angle, origin=(0.0, 0.0), use_radians=False)
        rectangle = affinity.translate(rectangle, xoff=float(offset_east_m), yoff=float(offset_north_m))
        if not local_field.covers(rectangle):
            outside.append(index + 1)
        output.append(validate_aoi_geometry(mapping(transform(to_geo, rectangle))))
    if outside:
        raise PollinationLabError(
            "The measured grid does not fit inside the selected field. Adjust plot dimensions, gaps, columns, orientation or offsets. "
            + "Outside plots: " + ", ".join(map(str, outside[:20]))
        )
    return output


def generate_hierarchical_treatment_unit_grid(
    *,
    field_geometry: Mapping[str, Any],
    blocks: int,
    units_per_block: int,
    block_columns: int,
    units_per_row: int,
    unit_width_m: float,
    unit_length_m: float,
    unit_column_gap_m: float,
    unit_row_gap_m: float,
    block_column_gap_m: float,
    block_row_gap_m: float,
    orientation_deg_from_north: float,
    offset_east_m: float = 0.0,
    offset_north_m: float = 0.0,
) -> list[dict[str, Any]]:
    """Generate treatment units nested visibly inside separate experiment plots/blocks."""
    if any(item is None for item in [shape, mapping, transform, affinity, box]):
        raise PollinationLabError("Hierarchical measured-grid generation requires Shapely.")
    field_geojson = validate_aoi_geometry(field_geometry)
    field_shape = shape(field_geojson)
    block_count = int(blocks)
    units_count = int(units_per_block)
    if block_count < 1 or units_count < 1:
        raise PollinationLabError("Blocks and treatment units per experiment plot must be positive.")
    bcols = max(1, min(int(block_columns), block_count))
    brows = int(math.ceil(block_count / bcols))
    ucols = max(1, min(int(units_per_row), units_count))
    urows = int(math.ceil(units_count / ucols))
    width = float(unit_width_m)
    length = float(unit_length_m)
    if width <= 0 or length <= 0:
        raise PollinationLabError("Treatment-unit width and length must be positive.")
    ugx = max(0.0, float(unit_column_gap_m))
    ugy = max(0.0, float(unit_row_gap_m))
    bgx = max(0.0, float(block_column_gap_m))
    bgy = max(0.0, float(block_row_gap_m))
    block_width = ucols * width + max(0, ucols - 1) * ugx
    block_height = urows * length + max(0, urows - 1) * ugy
    total_width = bcols * block_width + max(0, bcols - 1) * bgx
    total_height = brows * block_height + max(0, brows - 1) * bgy
    centre_lat, centre_lon = geometry_centroid(field_geojson)
    metres_per_lat = 111_320.0
    metres_per_lon = max(1.0, 111_320.0 * math.cos(math.radians(centre_lat)))

    def to_local(x, y, z=None):
        return ((x - centre_lon) * metres_per_lon, (y - centre_lat) * metres_per_lat)

    def to_geo(x, y, z=None):
        return (centre_lon + x / metres_per_lon, centre_lat + y / metres_per_lat)

    local_field = transform(to_local, field_shape)
    start_x = -total_width / 2.0
    start_y = total_height / 2.0
    angle = 90.0 - float(orientation_deg_from_north)
    output: list[dict[str, Any]] = []
    outside: list[str] = []
    for block_index in range(block_count):
        block_row = block_index // bcols
        block_col = block_index % bcols
        block_x = start_x + block_col * (block_width + bgx)
        block_y = start_y - block_row * (block_height + bgy)
        for unit_index in range(units_count):
            unit_row = unit_index // ucols
            unit_col = unit_index % ucols
            x0 = block_x + unit_col * (width + ugx)
            y1 = block_y - unit_row * (length + ugy)
            rectangle = box(x0, y1 - length, x0 + width, y1)
            rectangle = affinity.rotate(rectangle, angle, origin=(0.0, 0.0), use_radians=False)
            rectangle = affinity.translate(rectangle, xoff=float(offset_east_m), yoff=float(offset_north_m))
            label = f"B{block_index + 1:02d}-U{unit_index + 1:03d}"
            if not local_field.buffer(1e-8).covers(rectangle):
                outside.append(label)
            output.append(validate_aoi_geometry(mapping(transform(to_geo, rectangle))))
    if outside:
        raise PollinationLabError(
            "The hierarchical grid does not fit inside the selected trial boundary. Adjust unit dimensions, "
            "units per row, experiment plots per row, gaps, orientation or offsets. Outside units: "
            + ", ".join(outside[:20])
        )
    return output


def _preview_pending_plots(
    field_geometry: Mapping[str, Any],
    geometries: Sequence[Mapping[str, Any]],
    *,
    key: str,
    blocks: int | None = None,
    units_per_block: int | None = None,
) -> None:
    lat, lon = geometry_centroid(field_geometry)
    map_object = folium.Map(location=[lat, lon], zoom_start=17, tiles=None, control_scale=True)
    _add_base_layers(map_object, satellite_default=True, collapsed=False)
    _add_distance_measurement(map_object)
    folium.GeoJson(
        field_geometry, name="Exact experiment boundary",
        style_function=lambda _: {"color": "#0f766e", "weight": 4, "fillOpacity": 0.03},
    ).add_to(map_object)
    block_count = int(blocks or 0)
    units_count = int(units_per_block or 0)
    if block_count > 0 and units_count > 0:
        for block in range(1, block_count + 1):
            subset = list(geometries[(block - 1) * units_count:block * units_count])
            if not subset:
                continue
            try:
                parent = geometry_union(subset)
                if shape is not None and mapping is not None:
                    parent = validate_aoi_geometry(mapping(shape(parent).convex_hull))
                folium.GeoJson(
                    parent, name=f"Experiment plot B{block:02d}",
                    tooltip=f"Experiment plot B{block:02d} · {len(subset)} treatment units",
                    style_function=lambda _: {"color": "#111827", "weight": 4, "dashArray": "9 5", "fillOpacity": 0.01},
                ).add_to(map_object)
            except Exception:
                pass
    preview_rows = []
    for index, geometry in enumerate(geometries, start=1):
        block = ((index - 1) // units_count + 1) if units_count else None
        unit_index = ((index - 1) % units_count + 1) if units_count else index
        label = f"B{block:02d}-U{unit_index:03d}" if block else f"U{index:03d}"
        colour = _factor_colour(block or 1, "Experiment plot")
        folium.GeoJson(
            geometry, name=f"Treatment unit {label}", tooltip=f"Treatment unit {label}",
            style_function=lambda _, c=colour: {"color": c, "weight": 2, "fillColor": c, "fillOpacity": 0.24},
        ).add_to(map_object)
        preview_rows.append({"Experiment plot": f"B{block:02d}" if block else "Pending", "Treatment unit": label})
    if preview_rows:
        _add_factor_legend(map_object, pd.DataFrame(preview_rows), "Experiment plot")
    _fit_map_to_geometries(map_object, [field_geometry] + list(geometries))
    _render_folium_view(map_object, height=560, key=key)


def _field_geometry_selector(
    project: Mapping[str, Any] | None,
    *,
    key_prefix: str,
    field_db=None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    mapped_fields = _field_library(field_db)
    sources = []
    if not mapped_fields.empty:
        sources.extend(["Use exact mapped field", "Use subsection of mapped field"])
    sources.extend(["Draw independent experiment field", "Use active project field", "Use current Satellite field", "Upload GeoJSON"])
    source = st.radio(
        "Experiment-field source",
        sources,
        horizontal=False,
        key=f"{key_prefix}_field_source",
        help="Use an existing mapped field whenever the trial occupies a saved field. AgroLattice then inherits the exact polygon instead of asking you to redraw it.",
    )
    geometry = None
    metadata: dict[str, Any] = {"Source": source, "Boundary mode": "Independent boundary"}
    project_geometry = ((project or {}).get("location") or {}).get("field_geometry")
    satellite_geometry = st.session_state.get("satellite_aoi_geometry")

    if source == "Use exact mapped field":
        selected_field = _select_mapped_field(field_db, key=f"{key_prefix}_exact_field")
        if selected_field:
            geometry = selected_field.get("geometry")
            metadata.update({
                "Source field ID": selected_field.get("field_id"),
                "Source field name": selected_field.get("name"),
                "Source farm": selected_field.get("farm_name"),
                "Source field geometry hash": geometry_hash(geometry),
                "Source field snapshot": geometry,
                "Boundary mode": "Exact mapped field",
                "Location": selected_field.get("name"),
            })
            st.success("The trial will inherit the exact saved field polygon, dimensions, centroid and geometry fingerprint.")
            _spatial_comparison_map(None, geometry, key=f"{key_prefix}_exact_field_preview")
    elif source == "Use subsection of mapped field":
        selected_field = _select_mapped_field(field_db, key=f"{key_prefix}_parent_field", label="Parent mapped field")
        if selected_field:
            parent_geometry = selected_field.get("geometry")
            centre_lat, centre_lon = geometry_centroid(parent_geometry)
            stored_key = f"{key_prefix}_subsection_geometry"
            candidate_geometry = render_boundary_editor(
                key=f"{key_prefix}_subsection_map", center=(centre_lat, centre_lon),
                initial_geometry=st.session_state.get(stored_key),
                reference_geometries=[{"geometry": parent_geometry, "label": "Locked parent field", "color": "#0f766e", "weight": 4}],
                zoom=17, height=520, satellite_default=True,
            )
            if candidate_geometry:
                geometry = validate_aoi_geometry(candidate_geometry)
                st.session_state[stored_key] = geometry
            else:
                geometry = st.session_state.get(stored_key)
            if geometry:
                if shape is not None and not shape(parent_geometry).covers(shape(geometry)):
                    st.error("The trial subsection extends outside the selected mapped field. Edit or redraw it entirely inside the green parent boundary.")
                    geometry = None
                else:
                    metadata.update({
                        "Source field ID": selected_field.get("field_id"),
                        "Source field name": selected_field.get("name"),
                        "Source farm": selected_field.get("farm_name"),
                        "Source field geometry hash": geometry_hash(parent_geometry),
                        "Source field snapshot": parent_geometry,
                        "Boundary mode": "Field subsection",
                        "Location": selected_field.get("name"),
                    })
                    st.success("The subsection is contained inside the exact mapped-field boundary. Both geometries will remain linked.")
            else:
                st.info("Draw only the experimental subsection. The green mapped-field boundary is locked as the spatial parent.")
    elif source == "Use active project field":
        geometry = project_geometry
        if geometry is None:
            st.warning("The active project does not contain a field geometry.")
    elif source == "Use current Satellite field":
        geometry = satellite_geometry
        if geometry is None:
            st.warning("No field geometry is currently loaded in Satellite crop monitoring.")
    elif source == "Upload GeoJSON":
        upload = st.file_uploader("Upload experiment-field Polygon or MultiPolygon", type=["json", "geojson"], key=f"{key_prefix}_field_upload")
        if upload is not None:
            geometry = _parse_geojson_upload(upload)
    else:
        existing = st.session_state.get("pollination_field_geometry") or project_geometry or satellite_geometry
        if existing:
            centre_lat, centre_lon = geometry_centroid(existing)
        else:
            centre_lat, centre_lon = st.session_state.get("agrolattice_active_country_map_centre", (19.45, -98.90))
        candidate_geometry = render_boundary_editor(
            key=f"{key_prefix}_field_map", center=(centre_lat, centre_lon),
            initial_geometry=existing, zoom=15, height=520, satellite_default=True,
        )
        if candidate_geometry:
            geometry = validate_aoi_geometry(candidate_geometry)
            st.session_state.pollination_field_geometry = geometry
        elif existing:
            geometry = existing
        else:
            st.info("Draw the outer boundary of the experiment field.")
    if geometry:
        geometry = validate_aoi_geometry(geometry)
        area = geometry_area_hectares(geometry)
        lat, lon = geometry_centroid(geometry)
        st.session_state.pollination_field_geometry = geometry
        metadata.update({"Area (ha)": area, "Centroid latitude": lat, "Centroid longitude": lon})
        cards = st.columns(3)
        cards[0].metric("Experiment-field area", f"{area:,.3f} ha")
        cards[1].metric("Centroid", f"{lat:.5f}, {lon:.5f}")
        cards[2].metric("Geometry hash", geometry_hash(geometry)[:10])
    return geometry, metadata

def _fit_map_to_geometries(map_object: folium.Map, geometries: Sequence[Mapping[str, Any]]) -> None:
    valid = [item for item in geometries if isinstance(item, Mapping)]
    if not valid or shape is None or unary_union is None:
        return
    try:
        minx, miny, maxx, maxy = unary_union([shape(validate_aoi_geometry(item)) for item in valid]).bounds
        map_object.fit_bounds([[miny, minx], [maxy, maxx]], padding=(28, 28))
    except Exception:
        pass


def _render_folium_view(map_object: folium.Map, *, height: int, key: str) -> None:
    """Render a saved/view-only Folium map without relying on st_folium state exchange.

    Some streamlit-folium versions can leave a blank component for view-only maps.
    Direct Folium HTML is more reliable for saved layouts while drawing maps still use
    st_folium so geometries can be returned to Python.
    """
    try:
        from streamlit.components.v1 import html as components_html
        rendered = map_object.get_root().render()
        components_html(rendered, height=int(height), scrolling=False)
    except Exception:
        st_folium(map_object, height=int(height), use_container_width=True, key=key)


def _add_factor_legend(map_object: folium.Map, frame: pd.DataFrame, factor: str) -> None:
    if frame is None or frame.empty or factor not in frame.columns:
        return
    values: list[str] = []
    for value in frame[factor].tolist():
        label = "Missing" if value is None or (isinstance(value, float) and pd.isna(value)) else str(value)
        if label not in values:
            values.append(label)
    if not values:
        return
    rows = "".join(
        f'<div style="display:flex;align-items:center;gap:6px;margin:2px 0;">'
        f'<span style="width:12px;height:12px;border-radius:2px;background:{_factor_colour(value, factor)};display:inline-block;"></span>'
        f'<span>{value}</span></div>'
        for value in values[:16]
    )
    if len(values) > 16:
        rows += f'<div style="margin-top:4px;">+ {len(values)-16} more levels</div>'
    legend = (
        '<div style="position:fixed;bottom:24px;left:24px;z-index:9999;background:white;'
        'border:1px solid #cbd5e1;border-radius:8px;padding:9px 11px;max-width:280px;'
        'max-height:260px;overflow:auto;font-size:12px;box-shadow:0 1px 4px rgba(0,0,0,.2);">'
        f'<div style="font-weight:700;margin-bottom:5px;">{factor}</div>{rows}</div>'
    )
    map_object.get_root().html.add_child(Element(legend))


def _factor_colour(value: Any, factor: str) -> str:
    palette = ["#2563eb", "#7c3aed", "#c2410c", "#15803d", "#be123c", "#0f766e", "#a16207", "#475569"]
    digest = hashlib.sha256(f"{factor}|{value}".encode("utf-8")).hexdigest()
    return palette[int(digest[:8], 16) % len(palette)]


def _plot_tooltip(plot: Mapping[str, Any]) -> str:
    fields = [
        ("Treatment unit", plot.get("Treatment unit") or plot.get("Plot")),
        ("Experiment plot", plot.get("Experiment plot") or f"B{plot.get('Block')}"),
        ("Treatment", plot.get("Treatment")),
        ("Female parent", plot.get("Female parent")),
        ("Male parent", plot.get("Male parent")),
        ("Parent combination", plot.get("Parent combination") or plot.get("Variety / genotype")),
        ("Density", plot.get("Sowing density (plants/ha)")),
        ("Sowing date", plot.get("Sowing date")),
        ("Male–female difference", plot.get("Male–female sowing difference (days)")),
    ]
    return "<br>".join(f"<b>{label}:</b> {value}" for label, value in fields if value not in (None, "") and not (isinstance(value, float) and pd.isna(value)))


def _plots_map(trial: Mapping[str, Any], saved_plots: pd.DataFrame, *, draw: bool, key: str, colour_by: str = "Variety / genotype") -> tuple[folium.Map, dict[str, Any] | None]:
    field = trial.get("field_geometry")
    if field:
        lat, lon = geometry_centroid(field)
    elif not saved_plots.empty:
        lat, lon = float(saved_plots["Latitude"].mean()), float(saved_plots["Longitude"].mean())
    else:
        lat, lon = st.session_state.get("agrolattice_active_country_map_centre", (19.45, -98.90))
    map_object = folium.Map(location=[lat, lon], zoom_start=17, tiles=None, control_scale=True)
    _add_base_layers(map_object, satellite_default=True, collapsed=False)
    _add_distance_measurement(map_object)
    _add_live_draw_distance(map_object)
    Fullscreen().add_to(map_object)
    if field:
        folium.GeoJson(field, name="Experiment field", style_function=lambda _: {"color": "#0f766e", "weight": 4, "fillOpacity": 0.03}).add_to(map_object)
    if not saved_plots.empty:
        for parent in experiment_plot_geometries(saved_plots):
            folium.GeoJson(
                parent["geometry"], name=f"Experiment plot {parent['label']}",
                tooltip=f"Experiment plot {parent['label']} · {parent['units']} treatment units",
                style_function=lambda _: {"color": "#111827", "weight": 4, "dashArray": "8 5", "fillOpacity": 0.01},
            ).add_to(map_object)
        for _, plot in saved_plots.iterrows():
            value = plot.get(colour_by) if colour_by in saved_plots.columns else plot.get("Treatment")
            colour = _factor_colour(value, colour_by)
            folium.GeoJson(
                plot["Geometry"], tooltip=_plot_tooltip(plot), popup=_plot_tooltip(plot),
                style_function=lambda _, c=colour: {"color": c, "weight": 2, "fillColor": c, "fillOpacity": 0.35},
            ).add_to(map_object)
    map_geometries = ([field] if field else []) + (saved_plots["Geometry"].tolist() if not saved_plots.empty and "Geometry" in saved_plots else [])
    _fit_map_to_geometries(map_object, map_geometries)
    if not saved_plots.empty:
        _add_factor_legend(map_object, saved_plots, colour_by)
    if draw:
        Draw(export=False, draw_options=_draw_options(), edit_options={"edit": True, "remove": True}).add_to(map_object)
        result = st_folium(
            map_object, height=600, use_container_width=True, key=key,
            returned_objects=["all_drawings", "last_active_drawing"],
        )
        return map_object, result
    _render_folium_view(map_object, height=620, key=key)
    return map_object, None


def _clickable_plot_selector(trial: Mapping[str, Any], plots: pd.DataFrame, *, key: str) -> str | None:
    field = trial.get("field_geometry")
    if field:
        lat, lon = geometry_centroid(field)
    else:
        lat, lon = float(plots["Latitude"].mean()), float(plots["Longitude"].mean())
    map_object = folium.Map(location=[lat, lon], zoom_start=17, tiles=None, control_scale=True)
    _add_base_layers(map_object, satellite_default=True, collapsed=False)
    _add_distance_measurement(map_object)
    _add_live_draw_distance(map_object)
    Fullscreen().add_to(map_object)
    if field:
        folium.GeoJson(field, name="Experiment field", style_function=lambda _: {"color": "#0f766e", "weight": 3, "fillOpacity": 0.03}).add_to(map_object)
    selected = set(st.session_state.get("pollination_satellite_plots") or [])
    for _, plot in plots.iterrows():
        is_selected = str(plot["Plot"]) in selected
        folium.GeoJson(
            plot["Geometry"],
            tooltip=str(plot["Plot"]),
            popup=f"{plot['Plot']} · {plot['Treatment']} · Block {plot['Block']}",
            style_function=lambda _, chosen=is_selected: {
                "color": "#dc2626" if chosen else "#2563eb",
                "weight": 4 if chosen else 2,
                "fillOpacity": 0.30 if chosen else 0.12,
            },
        ).add_to(map_object)
    result = st_folium(
        map_object,
        height=560,
        use_container_width=True,
        key=key,
        returned_objects=["last_object_clicked_tooltip"],
    )
    clicked = (result or {}).get("last_object_clicked_tooltip")
    return str(clicked) if clicked in set(plots["Plot"].astype(str)) else None


def _trial_display_label(row: Mapping[str, Any]) -> str:
    female = str(row.get("Female parent") or "Female line")
    male = str(row.get("Male parent") or "Male line")
    combinations = row.get("Parent combinations")
    suffix = ""
    try:
        count = int(combinations)
        if count > 1:
            suffix = f" · {count} parent combinations"
    except Exception:
        pass
    return f"{row.get('Trial')} · {female} × {male}{suffix} · {row.get('Year')}"


def _current_weather_candidate() -> tuple[pd.DataFrame | None, str]:
    for key, label in [
        ("live_monitor_weather", "Current-season monitor"),
        ("soil_water_raw_weather", "Soil-water balance"),
        ("daily_weather_derived", "Daily weather & phenology"),
        ("daily_weather_raw", "Daily weather & phenology raw"),
        ("aquacrop_weather", "AquaCrop weather"),
    ]:
        candidate = st.session_state.get(key)
        if isinstance(candidate, pd.DataFrame) and not candidate.empty:
            return candidate.copy(), label
    return None, "Unavailable"


def render_trial_designer_page(*, db: PollinationDatabase, project: Mapping[str, Any] | None, locations: pd.DataFrame | None = None, field_db=None) -> None:
    initialise_ui_state()
    st.title("🌽 Advanced trial design & field-data workbench")
    st.caption("Design a male–female flowering synchrony experiment, map treatment units, randomise agronomic factors, and collect flowering, tagged-plant leaf development, ear development and harvest data for the Mechanistic Maize Twin.")
    st.warning("The treatment range, isolation, row ratio, detasselling and field protocol must be approved by the maize-seed-production specialists supervising the trial.")
    library_tab, setup_tab, plot_tab, observations_tab, leaf_tab, phenology_tab, harvest_tab, satellite_tab, export_tab = st.tabs(["Trial library", "Trial setup", "Plot map & randomisation", "Daily flowering data", "Leaf & ear development", "Flowering dates", "Harvest & seed quality", "Satellite linkage", "Export & methods"])

    with library_tab:
        trials = db.list_trials()
        if not trials.empty:
            st.dataframe(trials, hide_index=True, width="stretch")
            labels = {_trial_display_label(row): row["Trial ID"] for _, row in trials.iterrows()}
            selected = st.selectbox("Trial", list(labels), key="pollination_library_trial")
            action = st.columns(2)
            if action[0].button("Activate trial", type="primary", width="stretch", key="pollination_activate_trial"):
                _activate_trial_state(labels[selected])
                st.success("Trial activated.")
            action[1].download_button("Export trial", db.export_trial_package(labels[selected]), file_name=f"{slugify(selected)}.zip", mime="application/zip", width="stretch", key="pollination_library_export")
            selected_trial_id = labels[selected]
            selected_trial = db.get_trial(selected_trial_id)
            current_status_row = trials.loc[trials["Trial ID"].astype(str).eq(str(selected_trial_id)), "Status"]
            current_status = str(current_status_row.iloc[0]) if not current_status_row.empty else "Active"
            status_cols = st.columns([2, 1])
            status_options = ["Draft", "Designed", "Randomised", "Field-Ready", "Data Collection", "Completed", "Analysed", "Archived", "Planned", "Active"]
            status_value = status_cols[0].selectbox("Trial status", status_options, index=status_options.index(current_status) if current_status in status_options else 0, key="pollination_library_status")
            if status_cols[1].button("Save status", width="stretch", key="pollination_save_status"):
                db.update_trial_status(selected_trial_id, status_value)
                st.success("Trial status updated.")
                st.rerun()
            try:
                twin_links = db._twin_link_count(selected_trial_id)
                twin_check_error = None
            except PollinationLabError as error:
                twin_links = 0
                twin_check_error = str(error)
            if twin_check_error:
                st.warning(twin_check_error)
            elif twin_links:
                st.warning(f"Hard deletion blocked: this trial is linked to {twin_links} Persistent Twin(s). Archive it or remove/reassign those Twin links first.")

            with st.expander("Archive or permanently delete this trial", expanded=False):
                st.info("Archiving is the recommended way to retire a trial because it preserves plots, observations, outcomes, provenance and Twin compatibility.")
                archive_col, _ = st.columns([1, 2])
                if archive_col.button("Archive trial", disabled=current_status == "Archived", width="stretch", key="pollination_archive_trial"):
                    db.update_trial_status(selected_trial_id, "Archived")
                    st.success("Trial archived; all research records were preserved.")
                    st.rerun()
                try:
                    delete_counts = db.trial_deletion_counts(selected_trial_id)
                except Exception as error:
                    delete_counts = {}
                    st.warning(f"Could not inspect deletion impact safely: {error}")
                if delete_counts:
                    impact = pd.DataFrame(
                        [{"Record class": label, "Rows that would be deleted": int(value)} for label, value in delete_counts.items()]
                    )
                    st.dataframe(impact, hide_index=True, width="stretch")
                    st.caption(f"Permanent deletion would remove {sum(delete_counts.values()):,} trial-scoped row(s), plus the trial record itself. This cannot be undone from the app.")
                exact_name = str(selected_trial.get("name") or "")
                typed_name = st.text_input(
                    f'Type the exact trial name to enable hard deletion: {exact_name}',
                    key="pollination_delete_trial_name",
                )
                destructive_ack = st.checkbox(
                    "I understand that hard deletion cascades through the records listed above",
                    key="pollination_delete_trial_ack",
                )
                delete_enabled = (
                    typed_name.strip() == exact_name.strip()
                    and destructive_ack
                    and not bool(twin_links)
                    and not bool(twin_check_error)
                    and bool(delete_counts)
                )
                if st.button(
                    "Permanently delete trial and listed records",
                    type="secondary",
                    disabled=not delete_enabled,
                    width="stretch",
                    key="pollination_delete_trial",
                ):
                    try:
                        db.delete_trial(
                            selected_trial_id,
                            confirmation_name=typed_name,
                            allow_cascade=True,
                        )
                        if st.session_state.get("pollination_active_trial_id") == selected_trial_id:
                            st.session_state.pollination_active_trial_id = None
                        st.success("Trial permanently deleted.")
                        st.rerun()
                    except Exception as error:
                        st.error(str(error))
        else:
            st.info("Create the first trial in Trial setup.")

    with setup_tab:
        st.markdown("### 1. Define the experiment field")
        geometry, field_metadata = _field_geometry_selector(project, key_prefix="pollination_create", field_db=field_db)
        st.markdown("### 2. Define parent lines and experimental factors")
        st.caption(
            "A trial may contain several female lines and several male lines. AgroLattice treats each selected "
            "female × male pairing as the **variety/genotype factor**, then combines it with density, sowing date "
            "and male–female sowing-date difference."
        )
        trial_columns = st.columns(3)
        name = trial_columns[0].text_input(
            "Trial name", value="2027 maize flowering synchrony trial", key="pollination_trial_name"
        )
        site_name = trial_columns[1].text_input(
            "Site",
            value=str(field_metadata.get("Location") or ((project or {}).get("location") or {}).get("name") or ""),
            key="pollination_site",
        )
        season_year = int(
            trial_columns[2].number_input(
                "Season year", 2000, 2100, date.today().year + 1, 1, key="pollination_year"
            )
        )
        parent_columns = st.columns(2)
        female_lines_text = parent_columns[0].text_area(
            "Female parent lines",
            value="F01",
            height=120,
            key="pollination_female_parent_lines",
            help="Enter one line per row or separate names with commas.",
        )
        male_lines_text = parent_columns[1].text_area(
            "Male parent lines",
            value="M01",
            height=120,
            key="pollination_male_parent_lines",
            help="Enter one line per row or separate names with commas.",
        )
        pairing_mode = st.radio(
            "Which female–male combinations belong in the experiment?",
            PARENT_PAIRING_MODES,
            horizontal=True,
            key="pollination_parent_pairing_mode",
            help=(
                "All combinations creates every female × male cross. Match-by-position pairs the first female with "
                "the first male and so on. Explicit mode accepts one Female | Male pair per line."
            ),
        )
        explicit_pairings_text = ""
        if pairing_mode == "Explicit selected pairings":
            explicit_pairings_text = st.text_area(
                "Explicit parent pairings",
                value="F01 | M01",
                height=110,
                key="pollination_explicit_parent_pairings",
                help="One pair per line, written as Female line | Male line.",
            )
        factor_columns = st.columns(3)
        density_levels_text = factor_columns[0].text_input(
            "Sowing-density levels (plants/ha)",
            value="65000",
            key="pollination_setup_density_levels",
            help="Comma-separated values, for example 55000,65000,75000.",
        )
        sowing_date_levels_text = factor_columns[1].text_input(
            "Female sowing-date levels",
            value=f"{date.today().year + 1}-05-01",
            key="pollination_setup_sowing_dates",
            help="Comma-separated YYYY-MM-DD dates.",
        )
        offset_levels_text = factor_columns[2].text_input(
            "Male–female sowing differences (days)",
            value="-6,-4,-2,0,2,4,6",
            key="pollination_setup_offsets",
            help="Negative values sow the male before the female; positive values sow it after the female.",
        )
        factor_error = None
        female_lines: list[str] = []
        male_lines: list[str] = []
        parent_pairings: list[dict[str, str]] = []
        density_levels: list[float] = []
        sowing_date_levels: list[str] = []
        offset_levels: list[int] = []
        setup_treatments: list[dict[str, Any]] = []
        try:
            female_lines = _parse_text_levels(female_lines_text)
            male_lines = _parse_text_levels(male_lines_text)
            parent_pairings = build_parent_combinations(
                female_lines,
                male_lines,
                pairing_mode=pairing_mode,
                explicit_pairings=explicit_pairings_text if pairing_mode == "Explicit selected pairings" else None,
            )
            density_levels = [float(value) for value in _parse_number_levels(density_levels_text)]
            sowing_date_levels = _parse_date_levels(
                sowing_date_levels_text, f"{season_year}-05-01"
            )
            offset_levels = [int(value) for value in _parse_number_levels(offset_levels_text, integer=True)]
            setup_treatments = factorial_treatment_combinations(
                densities=density_levels,
                parent_combinations=parent_pairings,
                sowing_dates=sowing_date_levels,
                offsets_days=offset_levels,
            )
        except Exception as error:
            factor_error = str(error)
            st.error(factor_error)
        design_columns = st.columns(4)
        blocks = int(design_columns[0].number_input("Experiment plots / blocks", 1, 20, 3, 1, key="pollination_blocks"))
        replicates = int(design_columns[1].number_input("Replicates per treatment per block", 1, 10, 1, 1, key="pollination_replicates"))
        row_ratio = design_columns[2].text_input("Female:male row ratio", value="4:2", key="pollination_row_ratio")
        trial_status = design_columns[3].selectbox(
            "Trial status", ["Planned", "Active", "Completed", "Archived"], index=1, key="pollination_trial_status"
        )
        if setup_treatments:
            cards = st.columns(5)
            cards[0].metric("Female lines", len(female_lines))
            cards[1].metric("Male lines", len(male_lines))
            cards[2].metric("Parent combinations", len(parent_pairings))
            cards[3].metric("Factor combinations", len(setup_treatments))
            cards[4].metric("Treatment units required", len(setup_treatments) * blocks * replicates)
            preview = pd.DataFrame(setup_treatments).rename(columns={
                "treatment_code": "Code",
                "female_parent": "Female parent",
                "male_parent": "Male parent",
                "parent_combination": "Parent combination",
                "sowing_density_plants_ha": "Sowing density (plants/ha)",
                "sowing_date": "Female sowing date",
                "male_sowing_offset_days": "Male–female difference (days)",
            })
            with st.expander("Preview the complete treatment design", expanded=len(preview) <= 24):
                st.dataframe(
                    preview[[column for column in [
                        "Code", "Female parent", "Male parent", "Parent combination",
                        "Sowing density (plants/ha)", "Female sowing date", "Male–female difference (days)",
                    ] if column in preview]],
                    hide_index=True,
                    width="stretch",
                )
            if len(setup_treatments) * blocks * replicates > 1000:
                st.warning(
                    "This design requires more than 1,000 treatment units. Confirm that every factor is intended "
                    "to be fully crossed before generating the spatial layout."
                )
        outcome = st.selectbox(
            "Primary outcome",
            ["Seed-set percentage", "Seed yield (t/ha)", "Kernels per ear", "Kernel rows per ear", "Pure seed (%)", "Germination (%)", "Genetic purity (%)", "Flowering overlap score"],
            key="pollination_primary_outcome",
        )
        thermal = st.columns(2)
        base_temp = float(thermal[0].number_input("GDD base temperature (°C)", -5.0, 20.0, 10.0, 0.5, key="pollination_base_temp"))
        upper_temp = float(thermal[1].number_input("GDD upper cap (°C)", 20.0, 45.0, 30.0, 0.5, key="pollination_upper_temp"))
        notes = st.text_area("Protocol notes", key="pollination_trial_notes")
        submitted = st.button(
            "Create and activate trial",
            type="primary",
            width="stretch",
            key="pollination_create_trial",
            disabled=bool(factor_error) or not bool(setup_treatments),
        )
        if submitted:
            try:
                if geometry is None:
                    raise PollinationLabError("Select or draw the experiment field before creating the trial.")
                trial_id = db.create_trial({
                    "name": name,
                    "project_id": (project or {}).get("project_id"),
                    "site_name": site_name,
                    "season_year": season_year,
                    "female_parent_levels": female_lines,
                    "male_parent_levels": male_lines,
                    "parent_pairings": parent_pairings,
                    "parent_pairing_mode": pairing_mode,
                    "sowing_density_levels": density_levels,
                    "sowing_date_levels": sowing_date_levels,
                    "sowing_offset_levels": offset_levels,
                    "female_sowing_date": sowing_date_levels[0],
                    "design_type": "Randomised complete block",
                    "blocks": blocks,
                    "replicates_per_treatment": replicates,
                    "row_ratio": row_ratio,
                    "planting_density_plants_ha": density_levels[0] if density_levels else None,
                    "primary_outcome": outcome,
                    "base_temperature_c": base_temp,
                    "upper_temperature_c": upper_temp,
                    "status": trial_status,
                    "field_geometry": geometry,
                    "source_field_id": field_metadata.get("Source field ID"),
                    "source_field_geometry_hash": field_metadata.get("Source field geometry hash"),
                    "source_field_snapshot": field_metadata.get("Source field snapshot"),
                    "boundary_mode": field_metadata.get("Boundary mode", "Independent boundary"),
                    "notes": notes,
                })
                _activate_trial_state(trial_id)
                st.success("Trial created with the full multi-parent factorial design. Continue to Plot map & randomisation.")
            except Exception as error:
                st.error(f"{type(error).__name__}: {error}")


        st.markdown("### 3. Link or synchronise an existing trial")
        with st.expander("Spatial linkage for an existing trial", expanded=False):
            existing_trial = _trial_selector(db, "pollination_spatial_trial_selector")
            if existing_trial is not None:
                linked_field = None
                if existing_trial.get("source_field_id") and field_db is not None:
                    linked_field = field_db.field(str(existing_trial.get("source_field_id")))
                if linked_field:
                    status = db.spatial_link_status(existing_trial["trial_id"], linked_field)
                    status_cols = st.columns(4)
                    status_cols[0].metric("Boundary mode", status["boundary_mode"])
                    status_cols[1].metric("Exact geometry", "Yes" if status["exact_match"] else "No")
                    status_cols[2].metric("Source field changed", "Yes" if status["source_changed"] else "No")
                    status_cols[3].metric("Trial inside field", "Yes" if status["trial_inside_field"] else "No" if status["trial_inside_field"] is False else "Unknown")
                    if status["source_changed"]:
                        st.warning("The mapped-field boundary changed after this trial was linked. Synchronise it below before collecting new spatial data.")
                    _spatial_comparison_map(existing_trial.get("field_geometry"), linked_field.get("geometry"), key="pollination_existing_link_map")
                replacement_field = _select_mapped_field(field_db, key="pollination_existing_link_field", label="Mapped field to use as spatial parent") if field_db is not None else None
                if replacement_field:
                    comparison = db.spatial_link_status(existing_trial["trial_id"], replacement_field)
                    trial_area = geometry_area_hectares(existing_trial["field_geometry"]) if existing_trial.get("field_geometry") else float("nan")
                    field_area = float(replacement_field.get("area_ha") or geometry_area_hectares(replacement_field["geometry"]))
                    metrics = st.columns(4)
                    metrics[0].metric("Current trial area", f"{trial_area:,.3f} ha" if pd.notna(trial_area) else "—")
                    metrics[1].metric("Mapped-field area", f"{field_area:,.3f} ha")
                    metrics[2].metric("Trial hash", str(comparison.get("trial_geometry_hash") or "")[:10] or "—")
                    metrics[3].metric("Field hash", str(comparison.get("current_field_geometry_hash") or "")[:10] or "—")
                    action = st.radio(
                        "Spatial-link action",
                        ["Replace trial boundary with exact mapped-field boundary", "Keep current trial boundary as a field subsection"],
                        key="pollination_existing_link_action",
                        help="Replacing the boundary preserves plot and observation records. Subsection mode keeps the trial polygon but verifies that it is fully contained in the mapped field.",
                    )
                    preserve_ack = st.checkbox("I understand that the outer trial boundary will be updated but existing internal plot records will be preserved", key="pollination_existing_link_ack")
                    if st.button("Apply exact spatial linkage", type="primary", disabled=not preserve_ack, key="pollination_existing_link_apply", width="stretch"):
                        try:
                            if action.startswith("Replace"):
                                db.update_trial_spatial_link(
                                    existing_trial["trial_id"],
                                    source_field_id=str(replacement_field["field_id"]),
                                    source_field_geometry=replacement_field["geometry"],
                                    boundary_mode="Exact mapped field",
                                    trial_geometry=replacement_field["geometry"],
                                )
                            else:
                                db.update_trial_spatial_link(
                                    existing_trial["trial_id"],
                                    source_field_id=str(replacement_field["field_id"]),
                                    source_field_geometry=replacement_field["geometry"],
                                    boundary_mode="Field subsection",
                                    trial_geometry=existing_trial.get("field_geometry"),
                                )
                            st.success("Trial spatial linkage updated. All existing treatment units were verified inside the new trial boundary before commit; no plots, observations or harvest outcomes were deleted.")
                            st.rerun()
                        except Exception as error:
                            st.error(f"{type(error).__name__}: {error}")

    with plot_tab:
        trial = _trial_selector(db, "pollination_plot_trial_selector")
        if trial:
            saved_plots = db.list_plots(trial["trial_id"])
            st.markdown("### Factorial treatment design")
            st.caption("An **experiment plot** is the block-level spatial container. A **treatment unit** is the smaller mapped subplot that receives one randomised factor combination and is the unit used for observations and harvest outcomes.")
            stored_females = trial.get("female_parent_levels") or [trial.get("female_parent")]
            stored_males = trial.get("male_parent_levels") or [trial.get("male_parent")]
            stored_pairings = trial.get("parent_pairings") or build_parent_combinations(
                stored_females, stored_males, pairing_mode="Match lines by position"
            )
            stored_mode = str(trial.get("parent_pairing_mode") or "Legacy single pairing")
            if stored_mode not in PARENT_PAIRING_MODES:
                stored_mode = "Match lines by position"
            parent_editor = st.expander("Parent-line and factor levels", expanded=True)
            with parent_editor:
                parent_cols = st.columns(2)
                female_levels_text = parent_cols[0].text_area(
                    "Female parent lines",
                    value="\n".join(str(value) for value in stored_females if value),
                    height=105,
                    key="pollination_plot_female_lines",
                )
                male_levels_text = parent_cols[1].text_area(
                    "Male parent lines",
                    value="\n".join(str(value) for value in stored_males if value),
                    height=105,
                    key="pollination_plot_male_lines",
                )
                plot_pairing_mode = st.radio(
                    "Parent-combination rule",
                    PARENT_PAIRING_MODES,
                    index=PARENT_PAIRING_MODES.index(stored_mode),
                    horizontal=True,
                    key="pollination_plot_pairing_mode",
                )
                stored_explicit_text = "\n".join(
                    f"{item.get('female_parent','')} | {item.get('male_parent','')}" for item in stored_pairings
                )
                plot_explicit_text = ""
                if plot_pairing_mode == "Explicit selected pairings":
                    plot_explicit_text = st.text_area(
                        "Explicit parent pairings",
                        value=stored_explicit_text,
                        height=100,
                        key="pollination_plot_explicit_pairings",
                    )
                factor_cols = st.columns(3)
                density_default = ",".join(
                    f"{float(value):.0f}" for value in (trial.get("sowing_density_levels") or [trial.get("planting_density_plants_ha") or 65000])
                    if value is not None
                )
                density_text = factor_cols[0].text_input(
                    "Sowing-density levels (plants/ha)",
                    value=density_default or "65000",
                    help="Comma-separated levels, for example 55000,65000,75000.",
                    key="pollination_density_levels",
                )
                sowing_default = ",".join(
                    str(value) for value in (trial.get("sowing_date_levels") or [trial.get("female_sowing_date")]) if value
                )
                sowing_dates_text = factor_cols[1].text_input(
                    "Female sowing-date levels",
                    value=sowing_default,
                    help="Comma-separated YYYY-MM-DD dates.",
                    key="pollination_sowing_date_levels",
                )
                offsets_default = ",".join(
                    str(int(value)) for value in (trial.get("sowing_offset_levels") or [-6, -4, -2, 0, 2, 4, 6])
                )
                offsets_text = factor_cols[2].text_input(
                    "Male–female sowing-date differences (days)",
                    value=offsets_default,
                    help="Negative values sow the male before the female; positive values sow it after the female.",
                    key="pollination_offsets",
                )
            try:
                female_levels = _parse_text_levels(female_levels_text)
                male_levels = _parse_text_levels(male_levels_text)
                parent_combinations = build_parent_combinations(
                    female_levels,
                    male_levels,
                    pairing_mode=plot_pairing_mode,
                    explicit_pairings=plot_explicit_text if plot_pairing_mode == "Explicit selected pairings" else None,
                )
                densities = [float(value) for value in _parse_number_levels(density_text)]
                sowing_dates = _parse_date_levels(sowing_dates_text, trial["female_sowing_date"])
                offsets = [int(value) for value in _parse_number_levels(offsets_text, integer=True)]
                treatments = factorial_treatment_combinations(
                    densities=densities,
                    parent_combinations=parent_combinations,
                    sowing_dates=sowing_dates,
                    offsets_days=offsets,
                )
            except Exception as error:
                female_levels, male_levels, parent_combinations = [], [], []
                densities, sowing_dates, offsets, treatments = [], [], [], []
                st.error(str(error))
            factor_actions = st.columns([3, 1])
            factor_actions[0].caption(
                "These levels define the trial design. Each treatment unit receives one complete factor combination."
            )
            if factor_actions[1].button(
                "Save factor design",
                key="pollination_save_factor_design",
                width="stretch",
                disabled=not bool(treatments),
            ):
                try:
                    db.update_trial_factor_design(
                        trial["trial_id"],
                        female_parent_levels=female_levels,
                        male_parent_levels=male_levels,
                        parent_pairings=parent_combinations,
                        parent_pairing_mode=plot_pairing_mode,
                        sowing_density_levels=densities,
                        sowing_date_levels=sowing_dates,
                        sowing_offset_levels=offsets,
                    )
                    st.success("Multi-parent factor design saved to the trial.")
                    st.rerun()
                except Exception as error:
                    st.error(f"{type(error).__name__}: {error}")
            treatment_table = pd.DataFrame(treatments).rename(columns={
                "treatment_code": "Code", "treatment_label": "Treatment",
                "female_parent": "Female parent", "male_parent": "Male parent",
                "parent_combination": "Parent combination",
                "sowing_density_plants_ha": "Sowing density (plants/ha)",
                "variety_genotype": "Variety / genotype", "sowing_date": "Sowing date",
                "male_sowing_offset_days": "Male–female difference (days)",
            })
            if not treatment_table.empty:
                with st.expander("Preview factor combinations", expanded=len(treatment_table) <= 30):
                    st.dataframe(treatment_table, hide_index=True, width="stretch")
            required_plots = int(trial["blocks"]) * int(trial["replicates_per_treatment"]) * len(treatments)
            cards = st.columns(5)
            cards[0].metric("Factor combinations", len(treatments))
            cards[1].metric("Experiment plots / blocks", trial["blocks"])
            cards[2].metric("Units per block", len(treatments) * int(trial["replicates_per_treatment"]))
            cards[3].metric("Required treatment units", required_plots)
            cards[4].metric("Saved treatment units", len(saved_plots))
            geometry_method = st.radio(
                "Treatment-unit geometry method",
                ["Generate measured treatment-unit grid", "Draw treatment units manually"],
                horizontal=True,
                key="pollination_plot_geometry_method",
                help="Measured-grid mode creates exact plot dimensions mathematically. Manual mode remains available for irregular layouts.",
            )
            units_per_block = len(treatments) * int(trial["replicates_per_treatment"])
            if geometry_method == "Generate measured treatment-unit grid":
                st.info(
                    "AgroLattice now generates a **hierarchical layout**: separate experiment plots/blocks, "
                    "each containing the complete set of smaller treatment units."
                )
                hierarchy = st.columns(4)
                default_block_columns = min(int(trial["blocks"]), 2 if int(trial["blocks"]) > 1 else 1)
                block_columns = int(hierarchy[0].number_input(
                    "Experiment plots per row", 1, max(1, int(trial["blocks"])),
                    default_block_columns, 1, key="pollination_grid_block_columns"
                ))
                default_units_per_row = min(max(1, int(math.ceil(math.sqrt(max(1, units_per_block))))), max(1, units_per_block))
                units_per_row = int(hierarchy[1].number_input(
                    "Treatment units per row inside each plot", 1, max(1, units_per_block),
                    default_units_per_row, 1, key="pollination_grid_units_per_row"
                ))
                plot_width = float(hierarchy[2].number_input(
                    "Treatment-unit width (m)", 0.1, 1000.0, 4.0, 0.1, key="pollination_grid_plot_width"
                ))
                plot_length = float(hierarchy[3].number_input(
                    "Treatment-unit length (m)", 0.1, 2000.0, 8.0, 0.1, key="pollination_grid_plot_length"
                ))
                gaps = st.columns(4)
                column_gap = float(gaps[0].number_input(
                    "Gap between treatment-unit columns (m)", 0.0, 100.0, 1.0, 0.1, key="pollination_grid_col_gap"
                ))
                row_gap = float(gaps[1].number_input(
                    "Gap between treatment-unit rows (m)", 0.0, 100.0, 1.0, 0.1, key="pollination_grid_row_gap"
                ))
                block_column_gap = float(gaps[2].number_input(
                    "Gap between experiment plots horizontally (m)", 0.0, 500.0, 3.0, 0.5, key="pollination_grid_block_col_gap"
                ))
                block_row_gap = float(gaps[3].number_input(
                    "Gap between experiment plots vertically (m)", 0.0, 500.0, 3.0, 0.5, key="pollination_grid_block_row_gap"
                ))
                placement = st.columns(3)
                orientation = float(placement[0].number_input(
                    "Row direction (° clockwise from north)", 0.0, 359.9, 0.0, 1.0, key="pollination_grid_orientation"
                ))
                east_offset = float(placement[1].number_input(
                    "Whole-layout offset east/west (m)", -10000.0, 10000.0, 0.0, 0.5, key="pollination_grid_east_offset"
                ))
                north_offset = float(placement[2].number_input(
                    "Whole-layout offset north/south (m)", -10000.0, 10000.0, 0.0, 0.5, key="pollination_grid_north_offset"
                ))
                if st.button(
                    "Generate or refresh hierarchical experiment layout",
                    type="secondary", width="stretch", key="pollination_generate_grid"
                ):
                    try:
                        generated = generate_hierarchical_treatment_unit_grid(
                            field_geometry=trial.get("field_geometry"),
                            blocks=int(trial["blocks"]),
                            units_per_block=units_per_block,
                            block_columns=block_columns,
                            units_per_row=units_per_row,
                            unit_width_m=plot_width,
                            unit_length_m=plot_length,
                            unit_column_gap_m=column_gap,
                            unit_row_gap_m=row_gap,
                            block_column_gap_m=block_column_gap,
                            block_row_gap_m=block_row_gap,
                            orientation_deg_from_north=orientation,
                            offset_east_m=east_offset,
                            offset_north_m=north_offset,
                        )
                        st.session_state.pollination_pending_plot_geometries = generated
                        st.session_state.pollination_pending_geometry_order = "hierarchical"
                        st.session_state.pollination_pending_plot_dimensions = {
                            "unit_width_m": plot_width,
                            "unit_length_m": plot_length,
                            "units_per_row": units_per_row,
                            "experiment_plots_per_row": block_columns,
                            "unit_column_gap_m": column_gap,
                            "unit_row_gap_m": row_gap,
                            "experiment_plot_column_gap_m": block_column_gap,
                            "experiment_plot_row_gap_m": block_row_gap,
                            "orientation_deg_from_north": orientation,
                            "offset_east_m": east_offset,
                            "offset_north_m": north_offset,
                        }
                        st.success(
                            f"Generated {int(trial['blocks'])} experiment plots containing "
                            f"{len(generated)} exact treatment-unit polygons."
                        )
                    except Exception as error:
                        st.error(f"{type(error).__name__}: {error}")
                pending = st.session_state.get("pollination_pending_plot_geometries") or []
                if pending and trial.get("field_geometry"):
                    _preview_pending_plots(
                        trial["field_geometry"], pending,
                        key="pollination_generated_grid_preview",
                        blocks=int(trial["blocks"]), units_per_block=units_per_block,
                    )
            else:
                st.info(
                    f"Draw exactly {required_plots} **treatment-unit** polygons or rectangles inside the trial boundary. "
                    f"After saving, AgroLattice spatially orders them and groups every {units_per_block} units into one "
                    "experiment plot/block. Use the satellite layer and ruler to verify placement and dimensions."
                )
                _, result = _plots_map(trial, saved_plots, draw=True, key="pollination_plot_draw_map")
                drawings = (result or {}).get("all_drawings") or []
                drawn_geometries = [validate_aoi_geometry(item) for item in drawings if item and item.get("geometry")]
                if drawn_geometries:
                    st.session_state.pollination_pending_plot_geometries = drawn_geometries
                    st.session_state.pollination_pending_geometry_order = "spatial"
                pending = st.session_state.get("pollination_pending_plot_geometries") or []
                if pending and trial.get("field_geometry"):
                    st.markdown("#### Captured manual treatment-unit preview")
                    _preview_pending_plots(
                        trial["field_geometry"], pending,
                        key="pollination_manual_grid_preview",
                        blocks=int(trial["blocks"]) if len(pending) == required_plots else None,
                        units_per_block=units_per_block if len(pending) == required_plots else None,
                    )
            st.caption(f"Captured/generated treatment-unit geometries: {len(pending)} of {required_plots}")
            existing_design_dependencies = db.trial_plot_dependency_counts(trial["trial_id"])
            locked_dependencies = {key: value for key, value in existing_design_dependencies.items() if value}
            if locked_dependencies:
                st.warning(
                    "This mapped design is locked because plot-linked research data already exist: "
                    + ", ".join(f"{key}={value}" for key, value in locked_dependencies.items())
                    + ". Create a new trial/design version to re-randomise without relabelling or deleting collected data."
                )
            constraint_cols = st.columns(2)
            minimise_adjacent = constraint_cols[0].checkbox(
                "Prefer spatial separation of identical treatments", value=True, key="pollination_minimise_adjacent",
                help="AGROLATTICE tests repeated randomisations and selects the allocation with the fewest shared borders between identical treatment labels. The random seed and search settings are saved for reproducibility."
            )
            randomisation_attempts = int(constraint_cols[1].slider(
                "Constrained randomisation attempts", 1, 200, 50, key="pollination_randomisation_attempts",
                disabled=not minimise_adjacent,
            ))
            seed = int(st.number_input("Randomisation seed", 0, 2_147_483_647, 2027, 1, key="pollination_random_seed"))
            if st.button("Randomise treatments and save plot map", type="primary", width="stretch", disabled=not treatments, key="pollination_save_plots"):
                try:
                    rows = randomised_plot_assignments(
                        geometries=pending, treatments=treatments, blocks=int(trial["blocks"]),
                        replicates_per_treatment=int(trial["replicates_per_treatment"]),
                        female_sowing_date=sowing_dates[0], seed=seed,
                        field_geometry=trial.get("field_geometry"),
                        preserve_geometry_order=(st.session_state.get("pollination_pending_geometry_order") == "hierarchical"),
                        minimise_adjacent_identical=minimise_adjacent,
                        randomisation_attempts=randomisation_attempts,
                    )
                    db.save_factor_design_and_plots(
                        trial["trial_id"], rows,
                        female_parent_levels=female_levels, male_parent_levels=male_levels,
                        parent_pairings=parent_combinations, parent_pairing_mode=plot_pairing_mode,
                        sowing_density_levels=densities, sowing_date_levels=sowing_dates,
                        sowing_offset_levels=offsets,
                    )
                    db.save_design_version(
                        trial["trial_id"], random_seed=seed, algorithm="Blocked factorial randomisation",
                        constraints={
                            "preserve_geometry_order": st.session_state.get("pollination_pending_geometry_order") == "hierarchical",
                            "blocks": int(trial["blocks"]),
                            "replicates_per_treatment": int(trial["replicates_per_treatment"]),
                            "minimise_adjacent_identical": bool(minimise_adjacent),
                            "randomisation_attempts": int(randomisation_attempts),
                        },
                        factor_matrix=treatments, allocation_manifest=rows, status="Randomised",
                    )
                    db.update_trial_status(trial["trial_id"], "Randomised")
                    st.session_state.pollination_pending_plot_geometries = []
                    st.session_state.pollination_pending_geometry_order = None
                    st.success("Experiment plots, treatment-unit map and factorial randomisation saved.")
                    st.rerun()
                except Exception as error:
                    st.error(f"{type(error).__name__}: {error}")
            if not saved_plots.empty:
                st.markdown("### Saved experiment plots and treatment units")
                factor_options = [column for column in ["Parent combination", "Female parent", "Male parent", "Sowing density (plants/ha)", "Sowing date", "Male–female sowing difference (days)", "Treatment"] if column in saved_plots.columns]
                colour_by = st.selectbox("Colour treatment units by", factor_options, key="pollination_saved_map_colour")
                _plots_map(trial, saved_plots, draw=False, key="pollination_saved_treatment_unit_map", colour_by=colour_by)
                parent_summary = pd.DataFrame([{"Experiment plot": item["label"], "Treatment units": item["units"], "Area (ha)": geometry_area_hectares(item["geometry"])} for item in experiment_plot_geometries(saved_plots)])
                if not parent_summary.empty:
                    st.dataframe(parent_summary, hide_index=True, width="stretch")
                st.dataframe(saved_plots.drop(columns=["Geometry", "Factor levels"], errors="ignore"), hide_index=True, width="stretch")

    with observations_tab:
        trial = _trial_selector(db, "pollination_obs_trial_selector")
        if trial:
            plots = db.list_plots(trial["trial_id"])
            if plots.empty:
                st.warning("Save the plot map before entering observations.")
            else:
                st.download_button("Download daily flowering sheet", observation_template(plots), file_name="daily_flowering_observations.csv", mime="text/csv", width="stretch", key="pollination_download_observation_template")
                uploaded = st.file_uploader("Upload completed daily flowering CSV", type=["csv"], key="pollination_observation_upload")
                if uploaded is not None:
                    preview = pd.read_csv(uploaded)
                    st.dataframe(preview.head(200), hide_index=True, width="stretch")
                    if st.button("Import or update flowering observations", type="primary", width="stretch", key="pollination_import_observations"):
                        inserted, issues = db.upsert_observations(trial["trial_id"], preview)
                        st.success(f"Imported or updated {inserted} observations.")
                        for issue in issues[:20]:
                            st.warning(issue)
                st.markdown("### Quick single-plot entry")
                with st.form("pollination_quick_observation_form"):
                    header = st.columns(2)
                    plot_label = header[0].selectbox("Plot", plots["Plot"].tolist(), key="pollination_quick_plot")
                    observation_date = header[1].date_input("Observation date", value=date.today(), key="pollination_quick_date")
                    row1 = st.columns(5)
                    male_n = int(row1[0].number_input("Male plants assessed", 0, 10000, 20, 1, key="pollination_quick_male_n"))
                    male_pct = float(row1[1].number_input("Male shedding (%)", 0.0, 100.0, 0.0, 1.0, key="pollination_quick_male_pct"))
                    pollen_intensity = float(row1[2].number_input("Pollen intensity (0–5)", 0.0, 5.0, 0.0, 0.5, key="pollination_quick_pollen"))
                    male_height = float(row1[3].number_input("Male height (cm)", 0.0, 500.0, 0.0, 1.0, key="pollination_quick_male_height"))
                    stress_score = float(row1[4].number_input("Crop stress (0–5)", 0.0, 5.0, 0.0, 0.5, key="pollination_quick_stress"))
                    row2 = st.columns(5)
                    female_n = int(row2[0].number_input("Female plants assessed", 0, 10000, 20, 1, key="pollination_quick_female_n"))
                    female_silking = float(row2[1].number_input("Female silking (%)", 0.0, 100.0, 0.0, 1.0, key="pollination_quick_silking"))
                    female_receptive = float(row2[2].number_input("Receptive silks (%)", 0.0, 100.0, 0.0, 1.0, key="pollination_quick_receptive"))
                    female_height = float(row2[3].number_input("Female height (cm)", 0.0, 500.0, 0.0, 1.0, key="pollination_quick_female_height"))
                    detasselling = row2[4].checkbox("Detasselling complete", key="pollination_quick_detasselling")
                    notes = st.text_input("Notes", key="pollination_quick_notes")
                    quick_submit = st.form_submit_button("Save observation", type="primary", width="stretch")
                if quick_submit:
                    frame = pd.DataFrame([{"Plot": plot_label, "Observation date": observation_date, "Male plants assessed": male_n, "Male shedding (%)": male_pct, "Pollen intensity (0-5)": pollen_intensity, "Male plant height (cm)": male_height or np.nan, "Female plants assessed": female_n, "Female silking (%)": female_silking, "Female receptive silks (%)": female_receptive, "Female plant height (cm)": female_height or np.nan, "Crop stress score (0-5)": stress_score, "Detasselling complete": detasselling, "Notes": notes}])
                    inserted, issues = db.upsert_observations(trial["trial_id"], frame)
                    if inserted:
                        st.success("Observation saved.")
                    for issue in issues:
                        st.warning(issue)
                observations = db.observations(trial["trial_id"])
                if not observations.empty:
                    st.dataframe(observations.tail(500), hide_index=True, width="stretch")

    with leaf_tab:
        trial = _trial_selector(db, "pollination_leaf_trial_selector")
        if trial:
            plots = db.list_plots(trial["trial_id"])
            if plots.empty:
                st.warning("Save the treatment-unit map before recording leaf development.")
            else:
                st.caption(
                    "Tag four representative plants per treatment unit at approximately V4. Count collared leaves "
                    "on the same plants about every 10 days, marking the uppermost counted leaf. Record final total "
                    "leaf number when known. Ear biomass is optional and requires a documented destructive-sampling protocol."
                )
                st.download_button(
                    "Download four-plant leaf-development sheet",
                    leaf_development_template(plots),
                    file_name="maize_leaf_and_ear_development.csv",
                    mime="text/csv", width="stretch", key="pollination_download_leaf_template",
                )
                upload = st.file_uploader("Upload completed leaf-development CSV", type=["csv"], key="pollination_leaf_upload")
                if upload is not None:
                    preview = pd.read_csv(upload)
                    st.dataframe(preview.head(300), hide_index=True, width="stretch")
                    if st.button("Import or update leaf observations", type="primary", width="stretch", key="pollination_import_leaf"):
                        inserted, issues = db.upsert_leaf_observations(trial["trial_id"], preview)
                        st.success(f"Imported or updated {inserted} tagged-plant observations.")
                        for issue in issues[:30]:
                            st.warning(issue)
                st.markdown("### Quick tagged-plant entry")
                with st.form("pollination_quick_leaf_form"):
                    header = st.columns(4)
                    plot_label = header[0].selectbox("Treatment unit", plots["Plot"].tolist(), key="pollination_quick_leaf_plot")
                    observed_date = header[1].date_input("Observation date", value=date.today(), key="pollination_quick_leaf_date")
                    parent_role = header[2].selectbox("Parent role", ["Female", "Male"], key="pollination_quick_leaf_role")
                    plant_tag = header[3].text_input("Plant tag", value="F-P1", key="pollination_quick_leaf_tag")
                    measures = st.columns(5)
                    collared = float(measures[0].number_input("Collared leaves", 0.0, 40.0, 4.0, 0.5, key="pollination_quick_leaf_count"))
                    final_tln = float(measures[1].number_input("Final total leaves", 0.0, 40.0, 0.0, 0.5, key="pollination_quick_final_tln"))
                    ear_biomass = float(measures[2].number_input("Ear biomass (g)", 0.0, 20.0, 0.0, 0.01, key="pollination_quick_ear_biomass"))
                    ear_length = float(measures[3].number_input("Ear length (mm)", 0.0, 1000.0, 0.0, 1.0, key="pollination_quick_ear_length"))
                    stage = measures[4].text_input("Stage", value="V4", key="pollination_quick_leaf_stage")
                    notes = st.text_input("Leaf / sampling notes", key="pollination_quick_leaf_notes")
                    submit_leaf = st.form_submit_button("Save tagged-plant observation", type="primary", width="stretch")
                if submit_leaf:
                    row = pd.DataFrame([{
                        "Plot": plot_label, "Observation date": observed_date, "Plant tag": plant_tag, "Parent role": parent_role,
                        "Collared leaf number": collared,
                        "Final total leaf number": final_tln if final_tln > 0 else np.nan,
                        "Ear biomass (g)": ear_biomass if ear_biomass > 0 else np.nan,
                        "Ear length (mm)": ear_length if ear_length > 0 else np.nan,
                        "Developmental stage": stage, "Notes": notes,
                    }])
                    inserted, issues = db.upsert_leaf_observations(trial["trial_id"], row)
                    if inserted:
                        st.success("Tagged-plant observation saved.")
                    for issue in issues:
                        st.warning(issue)
                leaf_records = db.leaf_observations(trial["trial_id"])
                if not leaf_records.empty:
                    cards = st.columns(4)
                    cards[0].metric("Tagged-plant records", len(leaf_records))
                    cards[1].metric("Treatment units", leaf_records["Plot ID"].nunique())
                    cards[2].metric("Plant tags", leaf_records["Plant tag"].nunique())
                    cards[3].metric("Observation dates", leaf_records["Observation date"].nunique())
                    st.dataframe(leaf_records.tail(600), hide_index=True, width="stretch")

    with phenology_tab:
        trial = _trial_selector(db, "pollination_phenology_trial_selector")
        if trial:
            plots = db.list_plots(trial["trial_id"])
            if plots.empty:
                st.warning("Save the plot map first.")
            else:
                st.caption("Record the date flowering first begins and the protocol-defined flowering date separately for male and female parents. Define the flowering-date criterion in the protocol, for example 50% of plants flowering.")
                st.download_button("Download flowering-date sheet", phenology_event_template(plots), file_name="plot_flowering_dates.csv", mime="text/csv", width="stretch", key="pollination_download_phenology_template")
                upload = st.file_uploader("Upload completed flowering-date CSV", type=["csv"], key="pollination_phenology_upload")
                if upload is not None:
                    preview = pd.read_csv(upload)
                    st.dataframe(preview.head(200), hide_index=True, width="stretch")
                    if st.button("Import or update flowering dates", type="primary", width="stretch", key="pollination_import_phenology"):
                        inserted, issues = db.upsert_phenology_events(trial["trial_id"], preview)
                        st.success(f"Imported or updated {inserted} plot flowering-date records.")
                        for issue in issues[:20]:
                            st.warning(issue)
                st.markdown("### Quick flowering-date entry")
                with st.form("pollination_quick_phenology_form"):
                    plot_label = st.selectbox("Plot", plots["Plot"].tolist(), key="pollination_quick_phenology_plot")
                    cols = st.columns(4)
                    male_init = cols[0].date_input("Male initiation date", value=None, key="pollination_male_init_date")
                    male_flowering = cols[1].date_input("Male flowering date", value=None, key="pollination_male_flowering_date")
                    female_init = cols[2].date_input("Female initiation date", value=None, key="pollination_female_init_date")
                    female_flowering = cols[3].date_input("Female flowering date", value=None, key="pollination_female_flowering_date")
                    notes = st.text_input("Definition / notes", key="pollination_phenology_notes")
                    submit_dates = st.form_submit_button("Save flowering dates", type="primary", width="stretch")
                if submit_dates:
                    frame = pd.DataFrame([{
                        "Plot": plot_label,
                        "Male flowering initiation date": male_init,
                        "Male flowering date": male_flowering,
                        "Female flowering initiation date": female_init,
                        "Female flowering date": female_flowering,
                        "Notes": notes,
                    }])
                    inserted, issues = db.upsert_phenology_events(trial["trial_id"], frame)
                    if inserted:
                        st.success("Flowering dates saved.")
                    for issue in issues:
                        st.warning(issue)
                events = db.phenology_events(trial["trial_id"])
                st.session_state.pollination_phenology_events = events
                if not events.empty:
                    st.dataframe(events, hide_index=True, width="stretch")

    with harvest_tab:
        trial = _trial_selector(db, "pollination_harvest_trial_selector")
        if trial:
            plots = db.list_plots(trial["trial_id"])
            if plots.empty:
                st.warning("Save the plot map first.")
            else:
                st.caption("Kernel rows per ear (sometimes called lines per ear) is recorded separately from total kernels per ear. Pure seed (%) is also separate from genetic purity (%); use the laboratory's formal definitions and method for each.")
                st.download_button("Download harvest sheet", harvest_template(plots), file_name="pollination_harvest_outcomes.csv", mime="text/csv", width="stretch", key="pollination_download_harvest_template")
                upload = st.file_uploader("Upload completed harvest CSV", type=["csv"], key="pollination_harvest_upload")
                if upload is not None:
                    preview = pd.read_csv(upload)
                    st.dataframe(preview.head(200), hide_index=True, width="stretch")
                    if st.button("Import or update harvest outcomes", type="primary", width="stretch", key="pollination_import_harvest"):
                        inserted, issues = db.upsert_harvest(trial["trial_id"], preview)
                        st.success(f"Imported or updated {inserted} harvest rows.")
                        for issue in issues[:20]:
                            st.warning(issue)
                st.markdown("### Quick single-plot harvest and seed-quality entry")
                with st.form("pollination_quick_harvest_form"):
                    header = st.columns(3)
                    plot_label = header[0].selectbox("Plot", plots["Plot"].tolist(), key="pollination_quick_harvest_plot")
                    harvest_date_value = header[1].date_input("Harvest date", value=date.today(), key="pollination_quick_harvest_date")
                    ears = float(header[2].number_input("Ears harvested", 0.0, 100000.0, 0.0, 1.0, key="pollination_quick_ears"))
                    row1 = st.columns(5)
                    kernels_per_ear = float(row1[0].number_input("Kernels per ear", 0.0, 5000.0, 0.0, 1.0, key="pollination_quick_kernels_per_ear"))
                    kernel_rows = float(row1[1].number_input("Kernel rows per ear", 0.0, 100.0, 0.0, 1.0, key="pollination_quick_kernel_rows"))
                    filled = float(row1[2].number_input("Filled kernels", 0.0, 1000000.0, 0.0, 1.0, key="pollination_quick_filled"))
                    unfilled = float(row1[3].number_input("Unfilled kernels", 0.0, 1000000.0, 0.0, 1.0, key="pollination_quick_unfilled"))
                    seed_yield_plot = float(row1[4].number_input("Seed yield (kg/plot)", 0.0, 100000.0, 0.0, 0.1, key="pollination_quick_seed_yield_plot"))
                    row2 = st.columns(5)
                    seed_yield_ha = float(row2[0].number_input("Seed yield (t/ha)", 0.0, 100.0, 0.0, 0.1, key="pollination_quick_seed_yield_ha"))
                    tkw = float(row2[1].number_input("1000-kernel weight (g)", 0.0, 2000.0, 0.0, 1.0, key="pollination_quick_tkw"))
                    germination = float(row2[2].number_input("Germination (%)", 0.0, 100.0, 0.0, 0.1, key="pollination_quick_germination"))
                    genetic_purity = float(row2[3].number_input("Genetic purity (%)", 0.0, 100.0, 0.0, 0.1, key="pollination_quick_genetic_purity"))
                    pure_seed = float(row2[4].number_input("Pure seed (%)", 0.0, 100.0, 0.0, 0.1, key="pollination_quick_pure_seed"))
                    notes = st.text_input("Harvest / laboratory notes", key="pollination_quick_harvest_notes")
                    submit_harvest = st.form_submit_button("Save harvest outcome", type="primary", width="stretch")
                if submit_harvest:
                    frame = pd.DataFrame([{
                        "Plot": plot_label, "Harvest date": harvest_date_value,
                        "Ears harvested": ears or np.nan, "Kernels per ear": kernels_per_ear or np.nan,
                        "Kernel rows per ear": kernel_rows or np.nan, "Filled kernels": filled or np.nan,
                        "Unfilled kernels": unfilled or np.nan, "Seed yield (kg/plot)": seed_yield_plot or np.nan,
                        "Seed yield (t/ha)": seed_yield_ha or np.nan, "1000-kernel weight (g)": tkw or np.nan,
                        "Germination (%)": germination or np.nan, "Genetic purity (%)": genetic_purity or np.nan,
                        "Pure seed (%)": pure_seed or np.nan, "Notes": notes,
                    }])
                    inserted, issues = db.upsert_harvest(trial["trial_id"], frame)
                    if inserted:
                        st.success("Harvest and seed-quality outcome saved.")
                    for issue in issues:
                        st.warning(issue)
                harvest = db.harvest(trial["trial_id"])
                st.session_state.pollination_harvest_outcomes = harvest
                if not harvest.empty:
                    st.dataframe(harvest, hide_index=True, width="stretch")

    with satellite_tab:
        trial = _trial_selector(db, "pollination_satellite_trial_selector")
        if trial:
            plots = db.list_plots(trial["trial_id"])
            if plots.empty:
                st.warning("Save plots before linking satellite data.")
            else:
                labels = plots["Plot"].tolist()
                current_plot_selection = [label for label in (st.session_state.get("pollination_satellite_plots") or []) if label in labels]
                st.session_state.pollination_satellite_plots = current_plot_selection or labels[:1]
                st.caption("Click a plot on the map to add it to the selection. Selected plots are outlined in red. Use the control below to remove plots or select several at once.")
                clicked_plot = _clickable_plot_selector(trial, plots, key="pollination_clickable_plot_selector")
                if clicked_plot and clicked_plot not in st.session_state.get("pollination_satellite_plots", []):
                    st.session_state.pollination_satellite_plots = list(st.session_state.get("pollination_satellite_plots", [])) + [clicked_plot]
                    st.rerun()
                selected_labels = st.multiselect("Selected mapped plot(s)", labels, key="pollination_satellite_plots")
                selected_rows = plots.loc[plots["Plot"].isin(selected_labels)]
                if not selected_rows.empty:
                    selected_geometry = geometry_union(selected_rows["Geometry"].tolist())
                    _, _ = _plots_map(trial, selected_rows, draw=False, key="pollination_selected_plot_map")
                    cards = st.columns(3)
                    cards[0].metric("Selected plots", len(selected_rows))
                    cards[1].metric("Selected area", f"{geometry_area_hectares(selected_geometry):,.3f} ha")
                    cards[2].metric("AOI hash", geometry_hash(selected_geometry)[:10])
                    if st.button("Send selected plot(s) to Satellite crop monitoring", type="primary", width="stretch", key="pollination_send_satellite"):
                        lat, lon = geometry_centroid(selected_geometry)
                        metadata = {"Area source": "Maize Flowering Synchrony Lab", "Trial": trial["name"], "Plots": selected_labels, "Area (ha)": geometry_area_hectares(selected_geometry), "Centroid latitude": lat, "Centroid longitude": lon}
                        st.session_state.satellite_aoi_geometry = selected_geometry
                        st.session_state.satellite_aoi_metadata = metadata
                        st.session_state.pollination_satellite_target = {"trial_id": trial["trial_id"], "plot_ids": selected_rows["Plot ID"].tolist(), "plot_labels": selected_labels, "geometry": selected_geometry, "geometry_hash": geometry_hash(selected_geometry)}
                        st.success("The selected mapped plot area is now the active Satellite crop monitoring AOI. Open that page, process Sentinel-2 scenes, then return here to attach the results.")
                    target = st.session_state.get("pollination_satellite_target")
                    time_series = st.session_state.get("satellite_time_series")
                    current_geometry = st.session_state.get("satellite_aoi_geometry")
                    matching = bool(target and current_geometry and target.get("geometry_hash") == geometry_hash(current_geometry))
                    st.caption(f"Satellite result ready: {isinstance(time_series, pd.DataFrame) and not time_series.empty}; AOI match: {matching}")
                    if st.button("Attach current satellite time series to selected plot(s)", width="stretch", disabled=not (matching and isinstance(time_series, pd.DataFrame) and not time_series.empty), key="pollination_attach_satellite"):
                        db.add_satellite_link(trial["trial_id"], target_label=", ".join(selected_labels), plot_ids=selected_rows["Plot ID"].tolist(), geometry=selected_geometry, time_series=time_series, processing_metadata=st.session_state.get("satellite_processing_config"))
                        st.success("Satellite time series linked to the exact selected plot geometry.")
                links = db.satellite_links(trial["trial_id"])
                if not links.empty:
                    st.dataframe(links.drop(columns=["Time series"], errors="ignore"), hide_index=True, width="stretch")

    with export_tab:
        trial = _trial_selector(db, "pollination_export_trial_selector")
        if trial:
            st.download_button("Download complete trial package", db.export_trial_package(trial["trial_id"]), file_name=f"{slugify(trial['name'])}_pollination_trial.zip", mime="application/zip", width="stretch", key="pollination_export_trial_package")
            st.markdown("### Recommended daily field protocol")
            st.write("Observe every plot daily from before first pollen shed until female silk receptivity and male pollen activity have both declined. Use the same assessment time, plant sample size and definitions each day.")
            st.markdown("### Scientific limitations")
            st.write("The map stores spatial support and enables Sentinel-2 integration, but Sentinel-2 cannot directly measure pollen release or silk receptivity. Flowering observations remain the primary data source.")


def render_synchrony_prediction_page(*, db: PollinationDatabase, project: Mapping[str, Any] | None) -> None:
    initialise_ui_state()
    st.title("📈 Advanced maize synchrony, modelling & optimisation workbench")
    st.caption("Quantify flowering overlap, calibrate genotype physiology, simulate daily development, compare empirical models, optimise one or two male sowing dates, and track in-season thermal time.")
    trial = _trial_selector(db, "pollination_analysis_trial_selector")
    if not trial:
        return
    plots = db.list_plots(trial["trial_id"])
    observations = db.observations(trial["trial_id"])
    leaf_observations = db.leaf_observations(trial["trial_id"])
    phenology_events = db.phenology_events(trial["trial_id"])
    harvest = db.harvest(trial["trial_id"])
    st.session_state.pollination_phenology_events = phenology_events
    st.session_state.pollination_harvest_outcomes = harvest
    stored_weather = db.weather(trial["trial_id"])
    links = db.satellite_links(trial["trial_id"])
    analysis_tab, weather_tab, features_tab, model_tab, optimiser_tab, physiology_tab, mechanistic_tab, strategy_tab, genomic_tab, forecast_tab, export_tab = st.tabs([
        "Synchrony curves", "Weather & GDD", "Model table", "Predictive models", "Empirical optimiser",
        "Parent physiology", "Mechanistic simulator", "Sowing strategy", "Genomics (optional)",
        "In-season forecast", "Export & methods",
    ])

    with weather_tab:
        current, source = _current_weather_candidate()
        st.caption(f"Current app weather source: {source}")
        upload = st.file_uploader("Or upload daily weather CSV", type=["csv"], key="pollination_weather_upload")
        candidate = pd.read_csv(upload) if upload is not None else current
        if isinstance(candidate, pd.DataFrame) and not candidate.empty:
            try:
                prepared = prepare_weather(candidate, base_temperature_c=float(trial["base_temperature_c"]), upper_temperature_c=float(trial["upper_temperature_c"]))
                st.dataframe(prepared.head(300), hide_index=True, width="stretch")
                if st.button("Store this weather with the trial", type="primary", width="stretch", key="pollination_store_weather"):
                    count = db.replace_weather(trial["trial_id"], prepared, source="Uploaded CSV" if upload is not None else source)
                    st.success(f"Stored {count:,} daily weather rows.")
                    st.rerun()
            except Exception as error:
                st.error(f"{type(error).__name__}: {error}")
        if not stored_weather.empty:
            cards = st.columns(4)
            cards[0].metric("Stored weather days", len(stored_weather))
            cards[1].metric("Start", str(stored_weather["Date"].min().date()))
            cards[2].metric("End", str(stored_weather["Date"].max().date()))
            cards[3].metric("Accumulated GDD", f"{stored_weather['GDD daily'].sum():,.0f}")

    plot_metrics, daily_curves = compute_plot_synchrony_metrics(observations, stored_weather)
    st.session_state.pollination_plot_metrics = plot_metrics
    st.session_state.pollination_daily_curves = daily_curves

    with analysis_tab:
        if observations.empty:
            st.info("Import daily flowering observations before calculating synchrony.")
        else:
            treatment = treatment_summary(plot_metrics, harvest)
            cards = st.columns(5)
            cards[0].metric("Plots observed", plot_metrics["Plot ID"].nunique() if not plot_metrics.empty else 0)
            cards[1].metric("Observation records", len(observations))
            cards[2].metric("Median absolute gap", f"{plot_metrics['Absolute synchrony gap (days)'].median():.2f} d" if not plot_metrics.empty else "—")
            cards[3].metric("Median overlap", f"{plot_metrics['Overlap area (equivalent full-overlap days)'].median():.2f} d" if not plot_metrics.empty else "—")
            cards[4].metric("Harvested plots", len(harvest))
            selected_treatments = st.multiselect("Treatments", sorted(daily_curves["Treatment"].dropna().unique()), default=sorted(daily_curves["Treatment"].dropna().unique()), key="pollination_curve_treatments")
            curve = daily_curves.loc[daily_curves["Treatment"].isin(selected_treatments)].groupby(["Treatment", "Date"], as_index=False)[["Male activity (%)", "Female silking (%)", "Female receptive (%)", "Daily overlap (%)"]].mean()
            long = curve.melt(id_vars=["Treatment", "Date"], var_name="Flowering measure", value_name="Percent")
            figure = px.line(long, x="Date", y="Percent", color="Flowering measure", facet_row="Treatment", markers=True, title="Male pollen activity and female silking/receptivity")
            figure.update_yaxes(range=[0, 105])
            st.plotly_chart(figure, width="stretch")
            st.markdown("### Plot-level synchrony metrics")
            st.dataframe(plot_metrics, hide_index=True, width="stretch")
            st.markdown("### Treatment summary")
            st.dataframe(treatment, hide_index=True, width="stretch")
            if not treatment.empty:
                outcome = "Mean seed set (%)" if "Mean seed set (%)" in treatment.columns else "Mean receptivity covered (%)"
                chart = px.scatter(treatment, x="Male offset (days)", y=outcome, size="Plots", hover_name="Treatment", title=f"Sowing offset versus {outcome.lower()}")
                st.plotly_chart(chart, width="stretch")

    with features_tab:
        model_table = build_model_table(
            trial=trial, plots=plots, plot_metrics=plot_metrics, phenology_events=phenology_events, harvest=harvest,
            weather=stored_weather, satellite_links_frame=links,
            root_zone=st.session_state.get("soil_water_balance_results"),
        )
        st.session_state.pollination_model_table = model_table
        if model_table.empty:
            st.info("Create plots and observations before building the model table.")
        else:
            st.dataframe(model_table, hide_index=True, width="stretch")
            st.download_button("Download modelling table", model_table.to_csv(index=False).encode("utf-8"), file_name="maize_pollination_model_table.csv", mime="text/csv", width="stretch", key="pollination_download_model_table")
            st.caption("Satellite features appear only after a plot AOI has been processed in Satellite crop monitoring and linked back to this trial.")

    with model_tab:
        model_table = st.session_state.get("pollination_model_table")
        if not isinstance(model_table, pd.DataFrame) or model_table.empty:
            st.info("Build the model table first.")
        else:
            target_options = [column for column in ["Days from male sowing to male 50%", "Days from female sowing to female 50%", "Days from sowing to male flowering initiation", "Days from sowing to male flowering", "Days from sowing to female flowering initiation", "Days from sowing to female flowering", "Synchrony gap (days; male50 - female50)", "Absolute synchrony gap (days)", "Overlap area (equivalent full-overlap days)", "Female receptivity covered by pollen (%)", "Maximum male plant height (cm)", "Maximum female plant height (cm)", "Seed set (%)", "Kernel rows per ear", "Seed yield (t/ha)", "Pure seed (%)", "Germination (%)", "Genetic purity (%)"] if column in model_table.columns and pd.to_numeric(model_table[column], errors="coerce").notna().sum() >= 3]
            if not target_options:
                st.warning("No target has enough observed values yet.")
            else:
                target = st.selectbox("Prediction target", target_options, key="pollination_model_target")
                forbidden = {"Plot ID", "Plot", target, "Treatment", "Male 10% date", "Male 50% date", "Male 90% date", "Female 10% silking date", "Female 50% silking date", "Female 90% silking date", "Harvest date", "Notes"}
                feature_options = [column for column in model_table.columns if column not in forbidden]
                flowering_target = any(token in target.casefold() for token in ["days from", "gdd to", "synchrony gap", "absolute synchrony"])
                if flowering_target:
                    preferred = [
                        "Male offset (days)", "Female parent", "Male parent", "Site", "Season year", "Block",
                        "Planting density (plants/ha)", "First 30d GDD", "First 30d rainfall (mm)",
                        "First 30d mean temperature (°C)", "First 30d heat days ≥35°C",
                        "Days 31–60 GDD", "Days 31–60 rainfall (mm)",
                        "First 30d root-zone mean Ks", "First 30d root-zone stress days",
                    ]
                else:
                    preferred = [
                        "Male offset (days)", "Female parent", "Male parent", "Site", "Season year", "Block",
                        "Planting density (plants/ha)", "Synchrony gap (days; male50 - female50)",
                        "Overlap area (equivalent full-overlap days)", "Female receptivity covered by pollen (%)",
                        "14d before female50 root-zone minimum Ks", "14d before female50 root-zone stress days",
                        "Through observed female50 heat days ≥35°C", "Mean NDVI", "Mean NDMI",
                    ]
                defaults = [column for column in preferred if column in feature_options]
                features = st.multiselect("Predictors", feature_options, default=defaults, key="pollination_model_features")
                group_options = ["None"] + [column for column in ["Block", "Site", "Season year", "Female parent", "Male parent"] if column in model_table.columns]
                grouping = st.selectbox("Independent validation group", group_options, key="pollination_model_group")
                folds = int(st.slider("Validation folds", 2, 10, 5, key="pollination_model_folds"))
                if st.button("Fit and cross-validate models", type="primary", width="stretch", disabled=not features, key="pollination_fit_models"):
                    try:
                        fit = fit_predictive_models(model_table, target=target, group_column=None if grouping == "None" else grouping, feature_columns=features, folds=folds)
                        st.session_state.pollination_model_fit = fit
                        db.save_model_run(trial["trial_id"], target, grouping, {"features": features, "folds": folds}, fit.metrics, fit.predictions)
                        st.success("Models fitted and evaluated.")
                    except Exception as error:
                        st.error(f"{type(error).__name__}: {error}")
                fit = st.session_state.get("pollination_model_fit")
                if isinstance(fit, ModelFitResult):
                    st.dataframe(fit.metrics, hide_index=True, width="stretch")
                    chart = px.scatter(fit.predictions, x="Observed", y="Prediction", color="Model", hover_data=["Residual"], title="Cross-validated observed versus predicted")
                    values = pd.concat([fit.predictions["Observed"], fit.predictions["Prediction"]]).dropna()
                    if not values.empty:
                        chart.add_shape(type="line", x0=values.min(), y0=values.min(), x1=values.max(), y1=values.max(), line=dict(dash="dash"))
                    st.plotly_chart(chart, width="stretch")
                    st.warning("With one site-year or few independent groups, performance estimates are preliminary and should not be described as externally validated.")

    with optimiser_tab:
        fit = st.session_state.get("pollination_model_fit")
        if not isinstance(fit, ModelFitResult):
            st.info("Fit a model that includes Male offset (days) before using the optimiser.")
        elif "Male offset (days)" not in fit.feature_columns:
            st.warning("Refit the model with Male offset (days) included as a predictor.")
        else:
            model_name = st.selectbox("Model", list(fit.models), key="pollination_optimizer_model")
            range_columns = st.columns(2)
            minimum = int(range_columns[0].number_input("Minimum offset", -30, 30, -10, 1, key="pollination_optimizer_min"))
            maximum = int(range_columns[1].number_input("Maximum offset", -30, 30, 10, 1, key="pollination_optimizer_max"))
            target_key = fit.target.casefold()
            if "synchrony gap" in target_key and "absolute" not in target_key:
                objective = "closest to zero"
            elif any(token in target_key for token in ["absolute gap", "error", "loss"]):
                objective = "minimise"
            elif any(token in target_key for token in ["overlap", "receptivity", "seed", "yield", "purity", "germination"]):
                objective = "maximise"
            else:
                objective = st.selectbox(
                    "Optimisation objective for this target",
                    ["minimise", "maximise", "closest to zero"],
                    key="pollination_empirical_objective",
                    help="For targets without an inherent optimum, choose the scientifically justified direction before generating a recommendation.",
                )
            st.info(f"Objective for **{fit.target}**: **{objective}**. A signed synchrony gap is never maximised; it is brought as close to zero as possible.")
            scenario_values: dict[str, Any] = {}
            with st.expander("Define the exact recommendation scenario", expanded=True):
                st.caption("These values replace the old generic median/mode scenario. Any predictor not shown still uses a clearly reported training median or mode.")
                scenario_columns = st.columns(3)
                known = [
                    ("Female parent", 0), ("Male parent", 1), ("Site", 2),
                    ("Sowing density (plants/ha)", 0), ("Planting density (plants/ha)", 0),
                    ("Season year", 1), ("Sowing date", 2),
                ]
                rendered: set[str] = set()
                for column, position in known:
                    if column not in fit.feature_columns or column in rendered:
                        continue
                    rendered.add(column)
                    series = fit.training_frame[column].dropna()
                    if column in fit.numerical_columns:
                        default = float(pd.to_numeric(series, errors="coerce").median()) if not series.empty else 0.0
                        scenario_values[column] = float(scenario_columns[position].number_input(column, value=default, key=f"pollination_empirical_scenario_{slugify(column)}"))
                    else:
                        options = list(dict.fromkeys(series.astype(str).tolist())) or ["Unknown"]
                        scenario_values[column] = scenario_columns[position].selectbox(column, options, key=f"pollination_empirical_scenario_{slugify(column)}")
            if st.button("Optimise sowing offset", type="primary", width="stretch", key="pollination_run_optimizer"):
                try:
                    result = optimise_sowing_offset(
                        fit, model_name=model_name, minimum_offset=minimum, maximum_offset=maximum,
                        scenario_values=scenario_values, objective=objective,
                    )
                    st.session_state.pollination_optimizer = result
                    st.session_state.pollination_optimizer_scenario = scenario_values
                except Exception as error:
                    st.error(f"{type(error).__name__}: {error}")
            result = st.session_state.get("pollination_optimizer")
            if isinstance(result, pd.DataFrame) and not result.empty:
                best = result.loc[result["Recommended"]].iloc[0]
                st.metric("Exploratory recommended male offset", f"{int(best['Male offset (days)']):+d} days", delta=f"Predicted {fit.target}: {best['Predicted outcome']:.3f}")
                chart = px.line(result, x="Male offset (days)", y="Predicted outcome", markers=True, title=f"Predicted {fit.target} across candidate offsets")
                st.plotly_chart(chart, width="stretch")
                st.dataframe(result, hide_index=True, width="stretch")
                st.caption("Scenario used: " + json.dumps(st.session_state.get("pollination_optimizer_scenario") or {}, ensure_ascii=False, default=str))
                observed_offsets = pd.to_numeric(fit.training_frame["Male offset (days)"], errors="coerce").dropna()
                if not observed_offsets.empty and (minimum < observed_offsets.min() or maximum > observed_offsets.max()):
                    st.warning("Part of the optimisation range extrapolates beyond tested sowing offsets. Treat those predictions as unsupported.")

    female_names = list(dict.fromkeys((plots.get("Female parent", pd.Series(dtype=str)).dropna().astype(str).tolist())))
    male_names = list(dict.fromkeys((plots.get("Male parent", pd.Series(dtype=str)).dropna().astype(str).tolist())))
    if not female_names:
        female_names = [str(value) for value in (trial.get("female_parent_levels") or [trial.get("female_parent")]) if value]
    if not male_names:
        male_names = [str(value) for value in (trial.get("male_parent_levels") or [trial.get("male_parent")]) if value]

    with physiology_tab:
        st.markdown("### Genotype-specific physiological parameters")
        st.caption(
            "The MFS model uses total leaf number (tln), coefficient of leaf appearance (coblf), and ear biomass "
            "at 50% silking (ebR1). Defaults are informative publication priors, not measured values for your lines."
        )
        parent_roles = [(name, "Female") for name in female_names] + [(name, "Male") for name in male_names]
        stored = db.parent_physiology([name for name, _ in parent_roles])
        lookup = {(str(row["Parent line"]), str(row["Role"])): row for _, row in stored.iterrows()} if not stored.empty else {}
        rows = []
        for name, role in parent_roles:
            existing = lookup.get((name, role))
            params = physiology_from_mapping(existing.to_dict() if existing is not None else None)
            rows.append({
                "Parent line": name, "Role": role, **params.to_record(),
                "Method": str(existing.get("Method")) if existing is not None else "Publication informative prior",
                "Source": str(existing.get("Source") or "") if existing is not None else "Laurent et al. (2025) prior",
                "Sample size": existing.get("Sample size") if existing is not None else np.nan,
                "Notes": str(existing.get("Notes") or "") if existing is not None else "",
            })
        physiology_editor = st.data_editor(
            pd.DataFrame(rows), hide_index=True, width="stretch", num_rows="fixed",
            disabled=["Parent line", "Role"], key="pollination_physiology_editor",
        )
        save_cols = st.columns(3)
        if save_cols[0].button("Save physiology parameters", type="primary", width="stretch", key="pollination_save_physiology"):
            saved_count = 0
            try:
                for row in physiology_editor.to_dict("records"):
                    db.upsert_parent_physiology(
                        row["Parent line"], row["Role"], physiology_from_mapping(row),
                        method=row.get("Method") or "User-entered", source=row.get("Source") or "",
                        sample_size=row.get("Sample size"), notes=row.get("Notes") or "",
                    )
                    saved_count += 1
                st.success(f"Saved physiological parameters for {saved_count} parent-role records.")
                st.rerun()
            except Exception as error:
                st.error(f"{type(error).__name__}: {error}")
        save_cols[1].download_button(
            "Download physiology CSV", parent_physiology_template([name for name, _ in parent_roles]),
            file_name="maize_parent_physiology.csv", mime="text/csv", width="stretch",
            key="pollination_physiology_template",
        )
        physiology_upload = save_cols[2].file_uploader("Import physiology CSV", type=["csv"], key="pollination_physiology_upload", label_visibility="collapsed")
        if physiology_upload is not None:
            imported_physiology = pd.read_csv(physiology_upload)
            st.dataframe(imported_physiology, hide_index=True, width="stretch")
            if st.button("Validate and import physiology file", width="stretch", key="pollination_import_physiology"):
                try:
                    for row in imported_physiology.to_dict("records"):
                        db.upsert_parent_physiology(
                            row.get("Parent line"), row.get("Role"), physiology_from_mapping(row),
                            method=row.get("Method") or "Imported", source=row.get("Source") or "",
                            sample_size=row.get("Sample size"), notes=row.get("Notes") or "",
                        )
                    st.success(f"Imported {len(imported_physiology)} physiology records.")
                    st.rerun()
                except Exception as error:
                    st.error(f"{type(error).__name__}: {error}")

        st.markdown("### Prior-regularised calibration from this trial")
        if stored_weather.empty:
            st.info("Store daily weather before calibrating parent physiology.")
        else:
            calibration_controls = st.columns(3)
            calibration_role = calibration_controls[0].selectbox("Parent role", ["Female", "Male"], key="pollination_calibration_role")
            available_names = female_names if calibration_role == "Female" else male_names
            calibration_parent = calibration_controls[1].selectbox("Parent line", available_names, key="pollination_calibration_parent") if available_names else None
            calibration_source = calibration_controls[2].text_input("Calibration source label", value=f"{trial['name']} field observations", key="pollination_calibration_source")
            prior = db.physiology_for_parent(calibration_parent, calibration_role) if calibration_parent else DEFAULT_PHYSIOLOGY
            if st.button("Calibrate selected parent", type="primary", width="stretch", disabled=not calibration_parent, key="pollination_calibrate_parent"):
                try:
                    plot_subset = plots.loc[plots[f"{calibration_role} parent"].astype(str).eq(str(calibration_parent))]
                    plot_ids = set(plot_subset["Plot ID"].astype(str))
                    event_column = f"{calibration_role} flowering date"
                    sowing_column = f"{calibration_role} sowing"
                    event_rows = phenology_events.loc[phenology_events["Plot ID"].astype(str).isin(plot_ids)].merge(
                        plot_subset[["Plot ID", sowing_column]], on="Plot ID", how="left"
                    ) if not phenology_events.empty and event_column in phenology_events else pd.DataFrame()
                    event_input = pd.DataFrame({
                        "Sowing date": event_rows.get(sowing_column, pd.Series(dtype=str)),
                        "Event date": event_rows.get(event_column, pd.Series(dtype=str)),
                    })
                    leaf_rows = leaf_observations.loc[
                        leaf_observations["Plot ID"].astype(str).isin(plot_ids)
                        & leaf_observations["Parent role"].astype(str).eq(calibration_role)
                    ].copy() if not leaf_observations.empty else pd.DataFrame()
                    if not leaf_rows.empty:
                        leaf_rows["Sowing date"] = leaf_rows[f"{calibration_role} sowing"]
                    calibration = calibrate_parent_physiology(
                        stored_weather, role=calibration_role,
                        event_observations=event_input, leaf_observations=leaf_rows, prior=prior,
                    )
                    st.session_state.pollination_physiology_calibration = {
                        "parent": calibration_parent, "role": calibration_role,
                        "source": calibration_source, "result": calibration,
                    }
                except Exception as error:
                    st.error(f"{type(error).__name__}: {error}")
            calibration_state = st.session_state.get("pollination_physiology_calibration")
            if isinstance(calibration_state, Mapping):
                result = calibration_state["result"]
                params = result["parameters"]
                cards = st.columns(6)
                for card, (label, value) in zip(cards, [
                    ("tln", params.tln), ("tln SD", params.tln_sd), ("coblf", params.coblf),
                    ("coblf SD", params.coblf_sd), ("ebR1 (g)", params.eb_r1_g), ("ebR1 SD", params.eb_r1_sd),
                ]):
                    card.metric(label, f"{value:.6g}")
                for warning in result.get("warnings", []):
                    st.warning(warning)
                if st.button("Accept and save calibrated parameters", type="primary", width="stretch", key="pollination_accept_calibration"):
                    db.upsert_parent_physiology(
                        calibration_state["parent"], calibration_state["role"], params,
                        method=result["method"], source=calibration_state["source"],
                        sample_size=result["event_records"] + result["leaf_records"],
                        notes="; ".join(result.get("warnings", [])),
                    )
                    st.success("Calibrated physiology saved.")
                    st.rerun()

    with mechanistic_tab:
        st.markdown("### Daily MFS mechanistic simulation")
        st.caption("Daily thermal time drives leaf appearance and ear biomass. Male anthesis and female silking are simulated separately for the selected parent lines and sowing dates.")
        if stored_weather.empty or not female_names or not male_names:
            st.info("Stored trial weather plus at least one female and one male parent are required.")
        else:
            controls = st.columns(4)
            mechanism_female = controls[0].selectbox("Female parent", female_names, key="pollination_mechanistic_female")
            mechanism_male = controls[1].selectbox("Male parent", male_names, key="pollination_mechanistic_male")
            default_sowing = pd.Timestamp(trial.get("female_sowing_date") or date.today()).date()
            female_sowing = controls[2].date_input("Female sowing", value=default_sowing, key="pollination_mechanistic_female_sowing")
            male_offset = int(controls[3].number_input("Male sowing difference (days)", -30, 30, 0, 1, key="pollination_mechanistic_offset"))
            uncertainty_draws = int(st.select_slider("Uncertainty draws", [100, 250, 500, 1000, 2500], value=500, key="pollination_mechanistic_draws"))
            if st.button("Run mechanistic twin", type="primary", width="stretch", key="pollination_run_mechanistic"):
                try:
                    female_parameters = db.physiology_for_parent(mechanism_female, "Female")
                    male_parameters = db.physiology_for_parent(mechanism_male, "Male")
                    male_sowing = pd.Timestamp(female_sowing) + pd.Timedelta(days=male_offset)
                    female_curve, female_summary = simulate_mfs(stored_weather, female_sowing, female_parameters)
                    male_curve, male_summary = simulate_mfs(stored_weather, male_sowing, male_parameters)
                    _, female_uncertainty = simulate_event_uncertainty(stored_weather, female_sowing, female_parameters, "Female", draws=uncertainty_draws, random_state=42)
                    _, male_uncertainty = simulate_event_uncertainty(stored_weather, male_sowing, male_parameters, "Male", draws=uncertainty_draws, random_state=43)
                    gap = (pd.Timestamp(male_summary["Anthesis date"]) - pd.Timestamp(female_summary["Silking date"])).days
                    st.session_state.pollination_mechanistic_result = {
                        "female_curve": female_curve, "male_curve": male_curve,
                        "female_summary": female_summary, "male_summary": male_summary,
                        "female_uncertainty": female_uncertainty, "male_uncertainty": male_uncertainty,
                        "gap": gap, "female_parent": mechanism_female, "male_parent": mechanism_male,
                    }
                except Exception as error:
                    st.error(f"{type(error).__name__}: {error}")
            mechanism_result = st.session_state.get("pollination_mechanistic_result")
            if isinstance(mechanism_result, Mapping):
                cards = st.columns(5)
                cards[0].metric("Female silking", mechanism_result["female_summary"]["Silking date"] or "—")
                cards[1].metric("Male anthesis", mechanism_result["male_summary"]["Anthesis date"] or "—")
                cards[2].metric("Signed gap", f"{mechanism_result['gap']:+d} d")
                cards[3].metric("Female 90% interval", f"{mechanism_result['female_uncertainty']['P05 event date']} → {mechanism_result['female_uncertainty']['P95 event date']}")
                cards[4].metric("Male 90% interval", f"{mechanism_result['male_uncertainty']['P05 event date']} → {mechanism_result['male_uncertainty']['P95 event date']}")
                female_curve = mechanism_result["female_curve"]
                male_curve = mechanism_result["male_curve"]
                leaf_long = pd.concat([
                    female_curve[["Date", "Predicted collared leaf number"]].assign(Parent=f"Female · {mechanism_result['female_parent']}"),
                    male_curve[["Date", "Predicted collared leaf number"]].assign(Parent=f"Male · {mechanism_result['male_parent']}"),
                ], ignore_index=True)
                st.plotly_chart(px.line(leaf_long, x="Date", y="Predicted collared leaf number", color="Parent", title="Mechanistic leaf appearance"), width="stretch")
                ear = female_curve[["Date", "Predicted ear biomass (g)"]].copy()
                st.plotly_chart(px.line(ear, x="Date", y="Predicted ear biomass (g)", title="Female ear-biomass trajectory and silking threshold"), width="stretch")
                with st.expander("Mechanistic parameters and thermal targets"):
                    st.json({"Female": mechanism_result["female_summary"], "Male": mechanism_result["male_summary"]})

    with strategy_tab:
        st.markdown("### Single or staggered male-sowing strategy")
        st.caption("The optimiser evaluates uncertainty and targets male pollen-shed timing about two days before and two days after female silking. It predicts timing, not pollen quantity.")
        if stored_weather.empty or not female_names or not male_names:
            st.info("Store weather and define both parent roles first.")
        else:
            controls = st.columns(4)
            strategy_female = controls[0].selectbox("Female parent", female_names, key="pollination_strategy_female")
            strategy_male = controls[1].selectbox("Male parent", male_names, key="pollination_strategy_male")
            strategy_sowing = controls[2].date_input("Female sowing date", value=pd.Timestamp(trial.get("female_sowing_date") or date.today()).date(), key="pollination_strategy_sowing")
            strategy_type = controls[3].selectbox("Strategy", ["Compare single and two-date strategies", "One male sowing date", "Two staggered male sowing dates"], key="pollination_strategy_type")
            ranges = st.columns(5)
            min_offset = int(ranges[0].number_input("Minimum offset", -30, 30, -10, 1, key="pollination_strategy_min"))
            max_offset = int(ranges[1].number_input("Maximum offset", -30, 30, 14, 1, key="pollination_strategy_max"))
            min_spacing = int(ranges[2].number_input("Minimum pair spacing", 1, 20, 2, 1, key="pollination_strategy_min_spacing"))
            max_spacing = int(ranges[3].number_input("Maximum pair spacing", 1, 30, 10, 1, key="pollination_strategy_max_spacing"))
            strategy_draws = int(ranges[4].selectbox("Uncertainty draws", [100, 250, 500, 1000, 2500], index=2, key="pollination_strategy_draws"))
            if st.button("Optimise sowing strategy", type="primary", width="stretch", key="pollination_run_strategy"):
                try:
                    strategies = optimise_male_sowing_strategy(
                        stored_weather, strategy_sowing,
                        db.physiology_for_parent(strategy_female, "Female"),
                        db.physiology_for_parent(strategy_male, "Male"),
                        minimum_offset=min_offset, maximum_offset=max_offset, strategy=strategy_type,
                        minimum_pair_spacing=min_spacing, maximum_pair_spacing=max_spacing,
                        draws=strategy_draws, random_state=42,
                    )
                    st.session_state.pollination_mechanistic_strategy = strategies
                except Exception as error:
                    st.error(f"{type(error).__name__}: {error}")
            strategies = st.session_state.get("pollination_mechanistic_strategy")
            if isinstance(strategies, pd.DataFrame) and not strategies.empty:
                recommended = strategies.loc[strategies["Recommended"]]
                for _, row in recommended.iterrows():
                    second = f" and {row['Male sowing 2']} ({int(row['Offset 2 (days)']):+d} d)" if pd.notna(row["Offset 2 (days)"]) else ""
                    st.success(
                        f"**{row['Strategy']}**: sow male on {row['Male sowing 1']} ({int(row['Offset 1 (days)']):+d} d){second}. "
                        f"Timing score {row['Objective score']:.3f}; probability any median-shed target is within ±2 days {row['P(any shed within ±2 d)']:.1%}."
                    )
                display = strategies.head(250)
                st.dataframe(display, hide_index=True, width="stretch")
                chart_data = strategies.loc[strategies["Strategy"].eq("One male sowing date")]
                if not chart_data.empty:
                    st.plotly_chart(px.line(chart_data, x="Offset 1 (days)", y="Objective score", markers=True, title="Single-date timing score across male sowing offsets"), width="stretch")
                st.download_button("Download all sowing strategies", strategies.to_csv(index=False).encode("utf-8"), file_name="mechanistic_male_sowing_strategies.csv", mime="text/csv", width="stretch", key="pollination_download_strategy")

    with genomic_tab:
        st.markdown("### Optional SNP marker → physiology bridge")
        st.warning("This is a transparent genomic-ridge approximation. It is not the paper's unavailable Bayesian C++ CGM-WGP sampler and must not be reported as a replication of it.")
        physiology_frame = db.parent_physiology()
        all_parent_names = list(dict.fromkeys(female_names + male_names))
        templates = st.columns(2)
        templates[0].download_button("Download SNP-marker template", snp_marker_template(all_parent_names), file_name="maize_snp_markers.csv", mime="text/csv", width="stretch", key="pollination_snp_template")
        templates[1].download_button("Download calibrated physiology", physiology_frame.to_csv(index=False).encode("utf-8"), file_name="calibrated_parent_physiology.csv", mime="text/csv", width="stretch", key="pollination_download_calibrated_physiology")
        marker_upload = st.file_uploader("Upload wide SNP-marker CSV (Parent line plus 0/1/2 marker columns)", type=["csv"], key="pollination_marker_upload")
        if marker_upload is not None:
            marker_frame = pd.read_csv(marker_upload)
            st.dataframe(marker_frame.head(100), hide_index=True, width="stretch")
            alpha = float(st.number_input("Genomic ridge penalty", 0.001, 100000.0, 10.0, step=1.0, format="%.3f", key="pollination_genomic_alpha"))
            if st.button("Fit parent-level genomic bridge", type="primary", width="stretch", key="pollination_fit_genomic"):
                try:
                    predictions, metrics = genomic_physiology_bridge(marker_frame, physiology_frame, alpha=alpha)
                    st.session_state.pollination_genomic_predictions = predictions
                    st.session_state.pollination_genomic_metrics = metrics
                except Exception as error:
                    st.error(f"{type(error).__name__}: {error}")
        genomic_predictions = st.session_state.get("pollination_genomic_predictions")
        genomic_metrics = st.session_state.get("pollination_genomic_metrics")
        if isinstance(genomic_metrics, pd.DataFrame):
            st.dataframe(genomic_metrics, hide_index=True, width="stretch")
        if isinstance(genomic_predictions, pd.DataFrame):
            st.dataframe(genomic_predictions, hide_index=True, width="stretch")
            st.download_button("Download genomic physiology predictions", genomic_predictions.to_csv(index=False).encode("utf-8"), file_name="genomic_parent_physiology_predictions.csv", mime="text/csv", width="stretch", key="pollination_download_genomic_predictions")
            save_predictions = st.checkbox("Confirm saving predictions for parents without observed physiology", key="pollination_confirm_genomic_save")
            if st.button("Save missing-parent genomic predictions", disabled=not save_predictions, width="stretch", key="pollination_save_genomic_predictions"):
                saved = 0
                for row in genomic_predictions.to_dict("records"):
                    if all(pd.notna(row.get(f"Observed {parameter}")) for parameter in ("tln", "coblf", "eb_r1_g")):
                        continue
                    name = str(row["Parent line"])
                    roles = [role for parent, role in parent_roles if parent == name] or ["Female"]
                    for role in roles:
                        db.upsert_parent_physiology(
                            name, role,
                            PhysiologyParameters(
                                tln=float(row["Predicted tln"]), coblf=float(row["Predicted coblf"]), eb_r1_g=float(row["Predicted eb_r1_g"]),
                                tln_sd=DEFAULT_PHYSIOLOGY.tln_sd, coblf_sd=DEFAULT_PHYSIOLOGY.coblf_sd, eb_r1_sd=DEFAULT_PHYSIOLOGY.eb_r1_sd,
                            ),
                            method="Genomic ridge approximation", source="Uploaded SNP marker matrix",
                            notes="Prediction uncertainty retains conservative publication-prior SDs.",
                        )
                        saved += 1
                st.success(f"Saved {saved} predicted parent-role physiology records.")
                st.rerun()

    with forecast_tab:
        if plot_metrics.empty or stored_weather.empty:
            st.info("The in-season forecast requires stored weather and observed flowering GDD targets from prior plots or trials.")
        else:
            parent_role = st.radio("Forecast event", ["Male 50% pollen shed", "Female 50% silking"], horizontal=True, key="pollination_forecast_role")
            if parent_role.startswith("Male"):
                target_values = pd.to_numeric(plot_metrics.get("Male GDD to 50%"), errors="coerce").dropna()
                sowing_column = "Male sowing"
            else:
                target_values = pd.to_numeric(plot_metrics.get("Female GDD to 50%"), errors="coerce").dropna()
                sowing_column = "Female sowing"
            if target_values.empty:
                st.warning("No observed thermal-time target is available for this event.")
            else:
                target_gdd = float(st.number_input("Target GDD", min_value=1.0, value=float(target_values.median()), step=5.0, key="pollination_forecast_target_gdd"))
                plot_label = st.selectbox("Plot", plots["Plot"].tolist(), key="pollination_forecast_plot")
                selected = plots.loc[plots["Plot"].eq(plot_label)].iloc[0]
                forecast = thermal_time_forecast(weather=stored_weather, sowing_date=selected[sowing_column], target_gdd=target_gdd)
                cards = st.columns(5)
                cards[0].metric("Target GDD", f"{forecast['Target GDD']:.0f}")
                cards[1].metric("Accumulated", f"{forecast['Accumulated GDD']:.0f}")
                cards[2].metric("Remaining", f"{forecast['Remaining GDD']:.0f}")
                cards[3].metric("Days remaining", f"{forecast['Estimated days remaining']:.1f}" if forecast["Estimated days remaining"] is not None and np.isfinite(forecast["Estimated days remaining"]) else "—")
                cards[4].metric("Estimated event", forecast["Estimated event date"] or "—")
                st.json(forecast)
                st.warning("This estimate extends the recent thermal-time rate; it is not a meteorological forecast and should update whenever new weather or field observations arrive.")

    with export_tab:
        model_table = st.session_state.get("pollination_model_table")
        treatment = treatment_summary(plot_metrics, harvest)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("plot_synchrony_metrics.csv", plot_metrics.to_csv(index=False))
            archive.writestr("daily_flowering_curves.csv", daily_curves.to_csv(index=False))
            archive.writestr("treatment_summary.csv", treatment.to_csv(index=False))
            archive.writestr("leaf_development_observations.csv", leaf_observations.to_csv(index=False))
            archive.writestr("parent_physiology.csv", db.parent_physiology(female_names + male_names).to_csv(index=False))
            archive.writestr("mechanistic_method_manifest.json", json.dumps(mechanistic_method_manifest(), indent=2))
            if isinstance(model_table, pd.DataFrame):
                archive.writestr("pollination_model_table.csv", model_table.to_csv(index=False))
            fit = st.session_state.get("pollination_model_fit")
            if isinstance(fit, ModelFitResult):
                archive.writestr("model_metrics.csv", fit.metrics.to_csv(index=False))
                archive.writestr("cross_validated_predictions.csv", fit.predictions.to_csv(index=False))
            optimiser = st.session_state.get("pollination_optimizer")
            if isinstance(optimiser, pd.DataFrame):
                archive.writestr("sowing_offset_optimisation.csv", optimiser.to_csv(index=False))
            strategy = st.session_state.get("pollination_mechanistic_strategy")
            if isinstance(strategy, pd.DataFrame):
                archive.writestr("mechanistic_male_sowing_strategies.csv", strategy.to_csv(index=False))
            mechanism = st.session_state.get("pollination_mechanistic_result")
            if isinstance(mechanism, Mapping):
                archive.writestr("mechanistic_female_daily.csv", mechanism["female_curve"].to_csv(index=False))
                archive.writestr("mechanistic_male_daily.csv", mechanism["male_curve"].to_csv(index=False))
                archive.writestr("mechanistic_simulation_summary.json", json.dumps({
                    "female": mechanism["female_summary"], "male": mechanism["male_summary"],
                    "female_uncertainty": mechanism["female_uncertainty"], "male_uncertainty": mechanism["male_uncertainty"],
                    "signed_gap_days": mechanism["gap"],
                }, indent=2, default=str))
            genomic_predictions = st.session_state.get("pollination_genomic_predictions")
            genomic_metrics = st.session_state.get("pollination_genomic_metrics")
            if isinstance(genomic_predictions, pd.DataFrame):
                archive.writestr("genomic_bridge_predictions.csv", genomic_predictions.to_csv(index=False))
            if isinstance(genomic_metrics, pd.DataFrame):
                archive.writestr("genomic_bridge_cross_validation.csv", genomic_metrics.to_csv(index=False))
            archive.writestr("README.txt", "AGROLATTICE 11.15 Experiment Command Centre outputs. Synchrony metrics and model outputs are research estimates. Validate recommendations in independent site-years and parent combinations. The optional genomic-ridge bridge is not a replication of Laurent et al.'s unavailable Bayesian C++ CGM-WGP sampler.\n")
        st.download_button("Download synchrony and prediction package", buffer.getvalue(), file_name=f"{slugify(trial['name'])}_synchrony_analysis.zip", mime="application/zip", width="stretch", key="pollination_download_analysis")
        st.markdown("### Interpretation rules")
        st.write("A synchrony gap near zero indicates alignment of the two 50% events, but the overlap-area and receptivity-covered metrics retain more information about flowering duration. A high cross-validation score does not establish transferability to new parents, sites or years.")
        st.write("Mechanistic uncertainty intervals propagate uncertainty in tln, coblf and ebR1. They do not include all weather-forecast, water-stress, disease, pollen-quantity or operational uncertainty.")
