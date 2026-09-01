-- AGROLATTICE 11.19 schema export: experiments
-- Schema version: 3.0.0
-- No user rows are included.
PRAGMA foreign_keys=ON;

CREATE TABLE design_versions (
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

CREATE TABLE experiment_protocol_versions (
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

CREATE TABLE experiment_protocols (
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

CREATE TABLE flowering_observations (
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
    detasselling_complete INTEGER,
    notes TEXT,
    created_at TEXT NOT NULL, male_plant_height_cm REAL, female_plant_height_cm REAL,
    UNIQUE(plot_id, observation_date)
);

CREATE TABLE harvest_outcomes (
    harvest_id TEXT PRIMARY KEY,
    trial_id TEXT NOT NULL REFERENCES trials(trial_id) ON DELETE CASCADE,
    plot_id TEXT NOT NULL REFERENCES plots(plot_id) ON DELETE CASCADE,
    harvest_date TEXT,
    ears_harvested REAL,
    kernels_per_ear REAL,
    filled_kernels REAL,
    unfilled_kernels REAL,
    seed_set_percent REAL,
    seed_yield_kg_plot REAL,
    seed_yield_t_ha REAL,
    thousand_kernel_weight_g REAL,
    germination_percent REAL,
    genetic_purity_percent REAL,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL, kernel_rows_per_ear REAL, pure_seed_percent REAL,
    UNIQUE(plot_id)
);

CREATE TABLE leaf_development_observations (
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

CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE model_runs (
    run_id TEXT PRIMARY KEY,
    trial_id TEXT NOT NULL REFERENCES trials(trial_id) ON DELETE CASCADE,
    target TEXT NOT NULL,
    grouping TEXT,
    settings_json TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    predictions_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE parent_lines (
    parent_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL,
    maturity_notes TEXT,
    source TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE parent_physiology (
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

CREATE TABLE plot_phenology_events (
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

CREATE TABLE plots (
    plot_id TEXT PRIMARY KEY,
    trial_id TEXT NOT NULL REFERENCES trials(trial_id) ON DELETE CASCADE,
    plot_label TEXT NOT NULL,
    block INTEGER NOT NULL,
    replicate INTEGER NOT NULL,
    treatment_label TEXT NOT NULL,
    male_sowing_offset_days INTEGER NOT NULL,
    female_sowing_date TEXT NOT NULL,
    male_sowing_date TEXT NOT NULL,
    geometry_json TEXT NOT NULL,
    area_ha REAL,
    centroid_lat REAL,
    centroid_lon REAL,
    created_at TEXT NOT NULL, experiment_plot_label TEXT, treatment_unit_label TEXT, sowing_density_plants_ha REAL, variety_genotype TEXT, sowing_date TEXT, factor_levels_json TEXT, female_parent TEXT, male_parent TEXT, parent_combination TEXT,
    UNIQUE(trial_id, plot_label)
);

CREATE TABLE satellite_links (
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

CREATE TABLE trial_audit_log (
    audit_id TEXT PRIMARY KEY,
    trial_id TEXT REFERENCES trials(trial_id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    user_name TEXT,
    details_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE trial_factor_definitions (
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

CREATE TABLE trial_measurement_requirements (
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

CREATE TABLE trials (
    trial_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    project_id TEXT,
    site_name TEXT,
    season_year INTEGER,
    female_parent TEXT NOT NULL,
    male_parent TEXT NOT NULL,
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
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
, source_field_id TEXT, source_field_geometry_hash TEXT, source_field_snapshot_json TEXT, boundary_mode TEXT, status TEXT NOT NULL DEFAULT 'Active', female_parent_levels_json TEXT, male_parent_levels_json TEXT, parent_pairings_json TEXT, parent_pairing_mode TEXT, sowing_density_levels_json TEXT, sowing_date_levels_json TEXT, sowing_offset_levels_json TEXT);

CREATE TABLE weather_daily (
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

CREATE INDEX idx_design_version_trial ON design_versions(trial_id, version_number);

CREATE INDEX idx_factor_trial ON trial_factor_definitions(trial_id);

CREATE INDEX idx_harvest_trial ON harvest_outcomes(trial_id);

CREATE INDEX idx_leaf_trial_date ON leaf_development_observations(trial_id, observation_date);

CREATE INDEX idx_measurement_requirement_trial ON trial_measurement_requirements(trial_id);

CREATE INDEX idx_obs_trial_date ON flowering_observations(trial_id, observation_date);

CREATE INDEX idx_parent_physiology_name ON parent_physiology(parent_name, role);

CREATE INDEX idx_phenology_trial ON plot_phenology_events(trial_id);

CREATE INDEX idx_plots_trial ON plots(trial_id);

CREATE INDEX idx_protocol_trial ON experiment_protocols(trial_id);

CREATE INDEX idx_protocol_versions_trial ON experiment_protocol_versions(trial_id, version_number);

CREATE INDEX idx_satellite_trial ON satellite_links(trial_id);

CREATE INDEX idx_trial_audit ON trial_audit_log(trial_id, created_at);
