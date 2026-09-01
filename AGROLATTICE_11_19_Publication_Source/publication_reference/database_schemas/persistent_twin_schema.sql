-- AGROLATTICE 11.19 schema export: persistent_twin
-- Schema version: 3.0.0
-- No user rows are included.
PRAGMA foreign_keys=ON;

CREATE TABLE analogue_seasons (
    analogue_id TEXT PRIMARY KEY,
    link_id TEXT NOT NULL,
    name TEXT NOT NULL,
    source TEXT,
    settings_json TEXT NOT NULL DEFAULT '{}',
    data_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    FOREIGN KEY(link_id) REFERENCES twin_links(link_id) ON DELETE CASCADE
);

CREATE TABLE calibration_runs (
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

CREATE TABLE metadata (
            key TEXT PRIMARY KEY, value TEXT NOT NULL
        );

CREATE TABLE model_registry (
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

CREATE TABLE recommendations (
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

CREATE TABLE scenarios (
            scenario_id TEXT PRIMARY KEY,
            link_id TEXT NOT NULL,
            name TEXT NOT NULL,
            settings_json TEXT NOT NULL,
            results_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(link_id) REFERENCES twin_links(link_id) ON DELETE CASCADE
        );

CREATE TABLE snapshots (
            snapshot_id TEXT PRIMARY KEY,
            link_id TEXT NOT NULL,
            as_of TEXT NOT NULL,
            state_json TEXT NOT NULL,
            plot_states_json TEXT,
            input_manifest_json TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(link_id) REFERENCES twin_links(link_id) ON DELETE CASCADE
        );

CREATE TABLE twin_events (
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

CREATE TABLE twin_links (
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

CREATE TABLE twin_root_zone (
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

CREATE TABLE twin_satellite (
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

CREATE TABLE twin_settings (
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

CREATE TABLE twin_weather (
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

CREATE INDEX idx_twin_events_link_time ON twin_events(link_id,event_time);
