-- AGROLATTICE 11.19 schema export: field_operations
-- Schema version: 8.0.0
-- No user rows are included.
PRAGMA foreign_keys=ON;

CREATE TABLE alert_details (
    alert_id TEXT PRIMARY KEY, acknowledged_at TEXT, snoozed_until TEXT, resolution_notes TEXT,
    false_positive INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL,
    FOREIGN KEY(alert_id) REFERENCES alerts(alert_id) ON DELETE CASCADE
);

CREATE TABLE alert_rule_details (
    rule_id TEXT PRIMARY KEY, persistence_count INTEGER NOT NULL DEFAULT 1, cooldown_hours INTEGER NOT NULL DEFAULT 24,
    crop_stage TEXT, updated_at TEXT NOT NULL,
    FOREIGN KEY(rule_id) REFERENCES alert_rules(rule_id) ON DELETE CASCADE
);

CREATE TABLE alert_rule_state (
 field_id TEXT NOT NULL, rule_id TEXT NOT NULL, consecutive_count INTEGER NOT NULL DEFAULT 0,
 last_value REAL, last_evaluated_at TEXT, last_alert_at TEXT,
 PRIMARY KEY(field_id, rule_id), FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE,
 FOREIGN KEY(rule_id) REFERENCES alert_rules(rule_id) ON DELETE CASCADE
);

CREATE TABLE alert_rules (
            rule_id TEXT PRIMARY KEY, name TEXT NOT NULL, source TEXT NOT NULL, metric TEXT NOT NULL,
            operator TEXT NOT NULL, threshold REAL NOT NULL, severity TEXT NOT NULL,
            window_days INTEGER, enabled INTEGER NOT NULL DEFAULT 1, notes TEXT, created_at TEXT NOT NULL
        );

CREATE TABLE alerts (
            alert_id TEXT PRIMARY KEY, field_id TEXT NOT NULL, rule_id TEXT, source TEXT,
            alert_type TEXT, severity TEXT, message TEXT, metric TEXT, value REAL, threshold REAL,
            status TEXT, fingerprint TEXT UNIQUE, created_at TEXT NOT NULL, resolved_at TEXT,
            FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE,
            FOREIGN KEY(rule_id) REFERENCES alert_rules(rule_id) ON DELETE SET NULL
        );

CREATE TABLE audit_log (
            audit_id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, entity_type TEXT,
            entity_id TEXT, user_name TEXT, details_json TEXT, created_at TEXT NOT NULL
        );

CREATE TABLE crop_history (
            history_id TEXT PRIMARY KEY, field_id TEXT NOT NULL, season_year INTEGER NOT NULL,
            crop TEXT NOT NULL, variety TEXT, sowing_date TEXT, harvest_date TEXT, yield_t_ha REAL,
            notes TEXT, created_at TEXT NOT NULL,
            FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE
        );

CREATE TABLE farms (
            farm_id TEXT PRIMARY KEY, name TEXT NOT NULL, country TEXT, admin_area TEXT,
            manager TEXT, notes TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        , entity_type TEXT NOT NULL DEFAULT 'Farm', geometry_json TEXT, geometry_hash TEXT, centroid_lat REAL, centroid_lon REAL, area_ha REAL);

CREATE TABLE field_access (
            user_id TEXT NOT NULL, field_id TEXT NOT NULL, permission TEXT NOT NULL,
            PRIMARY KEY(user_id, field_id),
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE
        );

CREATE TABLE field_seasons (
    season_id TEXT PRIMARY KEY, field_id TEXT NOT NULL, season_year INTEGER NOT NULL,
    crop TEXT NOT NULL, genotype TEXT, sowing_date TEXT, harvest_date TEXT, status TEXT,
    irrigation_system TEXT, notes TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
    UNIQUE(field_id, season_year, crop, genotype), FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE
);

CREATE TABLE fields (
            field_id TEXT PRIMARY KEY, farm_id TEXT NOT NULL, name TEXT NOT NULL, code TEXT,
            geometry_json TEXT NOT NULL, geometry_hash TEXT NOT NULL, centroid_lat REAL, centroid_lon REAL,
            area_ha REAL, crop TEXT, variety TEXT, season_year INTEGER, irrigation_system TEXT,
            soil_type TEXT, status TEXT, notes TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            FOREIGN KEY(farm_id) REFERENCES farms(farm_id) ON DELETE CASCADE
        );

CREATE TABLE nutrient_sample_details (
    sample_id TEXT PRIMARY KEY, external_sample_id TEXT, depth_from_cm REAL, depth_to_cm REAL,
    tissue_part TEXT, growth_stage TEXT, laboratory TEXT, analytical_method TEXT, units_json TEXT,
    detection_limit TEXT, updated_at TEXT NOT NULL,
    FOREIGN KEY(sample_id) REFERENCES nutrient_samples(sample_id) ON DELETE CASCADE
);

CREATE TABLE nutrient_samples (
            sample_id TEXT PRIMARY KEY, field_id TEXT NOT NULL, sample_date TEXT NOT NULL, sample_type TEXT,
            latitude REAL, longitude REAL, nitrogen REAL, phosphorus REAL, potassium REAL, ph REAL,
            ec REAL, organic_matter REAL, notes TEXT, created_at TEXT NOT NULL,
            FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE
        );

CREATE TABLE observation_details (
    observation_id TEXT PRIMARY KEY, trial_id TEXT, experimental_unit_id TEXT, plant_tag TEXT,
    protocol_id TEXT, measurement_json TEXT, updated_at TEXT NOT NULL,
    FOREIGN KEY(observation_id) REFERENCES observations(observation_id) ON DELETE CASCADE,
    FOREIGN KEY(protocol_id) REFERENCES observation_protocols(protocol_id) ON DELETE SET NULL
);

CREATE TABLE observation_protocols (
    protocol_id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT, description TEXT,
    fields_json TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);

CREATE TABLE observations (
            observation_id TEXT PRIMARY KEY, field_id TEXT NOT NULL, task_id TEXT, observed_at TEXT NOT NULL,
            category TEXT, severity INTEGER, latitude REAL, longitude REAL, notes TEXT,
            recommendation TEXT, photo_path TEXT, status TEXT, created_by TEXT, created_at TEXT NOT NULL,
            FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE,
            FOREIGN KEY(task_id) REFERENCES tasks(task_id) ON DELETE SET NULL
        );

CREATE TABLE operation_details (
    operation_id TEXT PRIMARY KEY, start_time TEXT, end_time TEXT, purpose TEXT, equipment TEXT,
    method TEXT, active_ingredient TEXT, batch_lot TEXT, recommendation_id TEXT,
    record_type TEXT NOT NULL DEFAULT 'Actual', geometry_json TEXT, weather_json TEXT, updated_at TEXT NOT NULL,
    FOREIGN KEY(operation_id) REFERENCES operations(operation_id) ON DELETE CASCADE
);

CREATE TABLE operations (
            operation_id TEXT PRIMARY KEY, field_id TEXT NOT NULL, operation_date TEXT NOT NULL,
            category TEXT, product TEXT, rate REAL, rate_unit TEXT, treated_area_ha REAL,
            water_mm REAL, cost REAL, operator TEXT, notes TEXT, created_at TEXT NOT NULL,
            FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE
        );

CREATE TABLE prescriptions (
            prescription_id TEXT PRIMARY KEY, field_id TEXT NOT NULL, name TEXT NOT NULL,
            variable TEXT, rate_unit TEXT, zone_label TEXT, rate REAL, geometry_json TEXT,
            source_metric TEXT, created_at TEXT NOT NULL,
            FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE
        );

CREATE TABLE sampling_points (
    sampling_point_id TEXT PRIMARY KEY, field_id TEXT NOT NULL, design_name TEXT, design_type TEXT,
    latitude REAL NOT NULL, longitude REAL NOT NULL, stratum TEXT, status TEXT NOT NULL DEFAULT 'Planned',
    sampled_at TEXT, notes TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
    FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE
);

CREATE TABLE sensor_calibrations (
    calibration_id TEXT PRIMARY KEY, sensor_id TEXT NOT NULL, calibration_date TEXT NOT NULL,
    method TEXT, reference TEXT, result TEXT, notes TEXT, created_at TEXT NOT NULL,
    FOREIGN KEY(sensor_id) REFERENCES sensors(sensor_id) ON DELETE CASCADE
);

CREATE TABLE sensor_details (
    sensor_id TEXT PRIMARY KEY, installed_at TEXT, retired_at TEXT, updated_at TEXT NOT NULL,
    FOREIGN KEY(sensor_id) REFERENCES sensors(sensor_id) ON DELETE CASCADE
);

CREATE TABLE sensor_readings (
            reading_id TEXT PRIMARY KEY, sensor_id TEXT NOT NULL, timestamp TEXT NOT NULL, value REAL,
            quality_flag TEXT, source TEXT, created_at TEXT NOT NULL,
            UNIQUE(sensor_id, timestamp),
            FOREIGN KEY(sensor_id) REFERENCES sensors(sensor_id) ON DELETE CASCADE
        );

CREATE TABLE sensors (
            sensor_id TEXT PRIMARY KEY, field_id TEXT NOT NULL, name TEXT NOT NULL, sensor_type TEXT NOT NULL,
            unit TEXT, depth_cm REAL, latitude REAL, longitude REAL, source TEXT, status TEXT,
            calibration_note TEXT, created_at TEXT NOT NULL,
            FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE
        );

CREATE TABLE task_details (
    task_id TEXT PRIMARY KEY, completion_notes TEXT, parent_task_id TEXT, trial_id TEXT,
    experimental_unit_id TEXT, protocol_id TEXT, updated_at TEXT NOT NULL,
    FOREIGN KEY(task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
);

CREATE TABLE tasks (
            task_id TEXT PRIMARY KEY, field_id TEXT NOT NULL, title TEXT NOT NULL, category TEXT,
            assigned_to TEXT, due_date TEXT, priority TEXT, status TEXT, description TEXT,
            recurrence TEXT, source TEXT, created_at TEXT NOT NULL, completed_at TEXT,
            FOREIGN KEY(field_id) REFERENCES fields(field_id) ON DELETE CASCADE
        );

CREATE TABLE users (
            user_id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT, role TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL
        );

CREATE INDEX idx_field_seasons_field_year ON field_seasons(field_id, season_year);

CREATE INDEX idx_observation_details_protocol ON observation_details(protocol_id);

CREATE INDEX idx_sampling_points_field ON sampling_points(field_id);

CREATE INDEX idx_sensor_calibrations_sensor ON sensor_calibrations(sensor_id, calibration_date);
