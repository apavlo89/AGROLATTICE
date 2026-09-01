-- AGROLATTICE 11.19 schema export: research_evidence
-- Schema version: 2.0.0
-- No user rows are included.
PRAGMA foreign_keys=ON;

CREATE TABLE benchmark_runs (
                    benchmark_run_id TEXT PRIMARY KEY,
                    benchmark_name TEXT NOT NULL,
                    model_id TEXT,
                    dataset_id TEXT,
                    protocol TEXT NOT NULL,
                    settings_json TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    applicability_json TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT NOT NULL,
                    notes TEXT,
                    FOREIGN KEY(model_id) REFERENCES models(model_id) ON DELETE SET NULL,
                    FOREIGN KEY(dataset_id) REFERENCES datasets(dataset_id) ON DELETE SET NULL
                );

CREATE TABLE causal_analyses (
                    analysis_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    dataset_id TEXT,
                    field_id TEXT,
                    trial_id TEXT,
                    treatment TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    covariates_json TEXT NOT NULL,
                    group_column TEXT,
                    method TEXT NOT NULL,
                    assumptions_json TEXT NOT NULL,
                    diagnostics_json TEXT NOT NULL,
                    estimates_json TEXT NOT NULL,
                    provenance_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(dataset_id) REFERENCES datasets(dataset_id) ON DELETE SET NULL
                );

CREATE TABLE data_acquisitions (
                    acquisition_id TEXT PRIMARY KEY,
                    dataset_id TEXT,
                    source TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    field_id TEXT,
                    trial_id TEXT,
                    latitude REAL,
                    longitude REAL,
                    period_start TEXT,
                    period_end TEXT,
                    temporal_resolution TEXT,
                    variables_json TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    provenance_json TEXT NOT NULL,
                    row_count INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(dataset_id) REFERENCES datasets(dataset_id) ON DELETE SET NULL
                );

CREATE TABLE dataset_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    dataset_id TEXT,
                    parent_snapshot_id TEXT,
                    name TEXT NOT NULL,
                    row_count INTEGER,
                    entity_count INTEGER,
                    manifest_json TEXT NOT NULL,
                    local_path TEXT,
                    sha256 TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(dataset_id) REFERENCES datasets(dataset_id) ON DELETE SET NULL,
                    FOREIGN KEY(parent_snapshot_id) REFERENCES dataset_snapshots(snapshot_id) ON DELETE SET NULL
                );

CREATE TABLE datasets (
                    dataset_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    dataset_type TEXT,
                    source TEXT,
                    source_version TEXT,
                    licence TEXT,
                    local_path TEXT,
                    sha256 TEXT,
                    crop_scope TEXT,
                    geography_scope TEXT,
                    spatial_resolution TEXT,
                    temporal_resolution TEXT,
                    provenance_json TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

CREATE TABLE decision_runs (
                    decision_run_id TEXT PRIMARY KEY,
                    decision_type TEXT NOT NULL,
                    field_id TEXT,
                    trial_id TEXT,
                    dataset_id TEXT,
                    objective TEXT NOT NULL,
                    status TEXT NOT NULL,
                    input_snapshot_json TEXT NOT NULL,
                    alternatives_json TEXT NOT NULL,
                    selected_alternative_json TEXT NOT NULL,
                    constraints_json TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    provenance_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(dataset_id) REFERENCES datasets(dataset_id) ON DELETE SET NULL
                );

CREATE TABLE metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

CREATE TABLE model_health_events (
                    health_event_id TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL,
                    health_status TEXT NOT NULL,
                    metric_name TEXT,
                    metric_value REAL,
                    threshold REAL,
                    evidence_json TEXT NOT NULL,
                    note TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(model_id) REFERENCES models(model_id) ON DELETE CASCADE
                );

CREATE TABLE model_status_history (
                    event_id TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL,
                    old_status TEXT,
                    new_status TEXT NOT NULL,
                    rationale TEXT,
                    evidence_json TEXT NOT NULL,
                    override_used INTEGER NOT NULL DEFAULT 0,
                    changed_at TEXT NOT NULL,
                    FOREIGN KEY(model_id) REFERENCES models(model_id) ON DELETE CASCADE
                );

CREATE TABLE model_versions (
                    version_id TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL,
                    version_number INTEGER NOT NULL,
                    parent_version_id TEXT,
                    dataset_snapshot_id TEXT,
                    artifact_path TEXT,
                    artifact_sha256 TEXT,
                    environment_json TEXT NOT NULL,
                    feature_contract_json TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(model_id) REFERENCES models(model_id) ON DELETE CASCADE,
                    FOREIGN KEY(parent_version_id) REFERENCES model_versions(version_id) ON DELETE SET NULL,
                    FOREIGN KEY(dataset_snapshot_id) REFERENCES dataset_snapshots(snapshot_id) ON DELETE SET NULL,
                    UNIQUE(model_id, version_number)
                );

CREATE TABLE models (
                    model_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    family TEXT NOT NULL,
                    target TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    source_method TEXT,
                    source_citation TEXT,
                    implementation_type TEXT NOT NULL,
                    training_dataset_id TEXT,
                    training_scope_json TEXT NOT NULL,
                    required_modalities_json TEXT NOT NULL,
                    feature_names_json TEXT NOT NULL,
                    preprocessing_json TEXT NOT NULL,
                    validation_protocol_json TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    calibration_json TEXT NOT NULL,
                    uncertainty_method TEXT,
                    applicability_json TEXT NOT NULL,
                    limitations_json TEXT NOT NULL,
                    artifact_path TEXT,
                    dependency_versions_json TEXT NOT NULL,
                    code_version TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(training_dataset_id) REFERENCES datasets(dataset_id) ON DELETE SET NULL
                );

CREATE TABLE observations (
                    observation_id TEXT PRIMARY KEY,
                    dataset_id TEXT,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT,
                    field_id TEXT,
                    trial_id TEXT,
                    experimental_unit_id TEXT,
                    observed_at TEXT,
                    period_start TEXT,
                    period_end TEXT,
                    variable TEXT NOT NULL,
                    value_numeric REAL,
                    value_text TEXT,
                    unit TEXT,
                    evidence_type TEXT NOT NULL,
                    geometry_json TEXT,
                    spatial_support TEXT,
                    spatial_resolution_m REAL,
                    temporal_resolution TEXT,
                    quality_flag TEXT,
                    source TEXT,
                    provenance_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(dataset_id) REFERENCES datasets(dataset_id) ON DELETE SET NULL
                );

CREATE TABLE prediction_outcome_links (
                    match_id TEXT PRIMARY KEY,
                    prediction_id TEXT NOT NULL,
                    observation_id TEXT,
                    treatment_outcome_id TEXT,
                    observed_value REAL,
                    observed_text TEXT,
                    unit TEXT,
                    matching_basis TEXT NOT NULL,
                    provenance_json TEXT NOT NULL,
                    matched_at TEXT NOT NULL,
                    FOREIGN KEY(prediction_id) REFERENCES predictions(prediction_id) ON DELETE CASCADE,
                    FOREIGN KEY(observation_id) REFERENCES observations(observation_id) ON DELETE SET NULL,
                    FOREIGN KEY(treatment_outcome_id) REFERENCES treatment_outcomes(outcome_id) ON DELETE SET NULL
                );

CREATE TABLE predictions (
                    prediction_id TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT,
                    field_id TEXT,
                    trial_id TEXT,
                    season_year INTEGER,
                    target TEXT NOT NULL,
                    horizon TEXT,
                    prediction REAL,
                    lower_bound REAL,
                    upper_bound REAL,
                    uncertainty_total REAL,
                    uncertainty_aleatoric REAL,
                    uncertainty_epistemic REAL,
                    uncertainty_method TEXT,
                    applicability_status TEXT,
                    applicability_score REAL,
                    input_snapshot_json TEXT NOT NULL,
                    provenance_json TEXT NOT NULL,
                    generated_at TEXT NOT NULL, prediction_text TEXT, class_probabilities_json TEXT NOT NULL DEFAULT '{}',
                    FOREIGN KEY(model_id) REFERENCES models(model_id) ON DELETE RESTRICT
                );

CREATE TABLE recommendation_status_history (
                    event_id TEXT PRIMARY KEY,
                    recommendation_id TEXT NOT NULL,
                    old_status TEXT,
                    new_status TEXT NOT NULL,
                    note TEXT,
                    changed_at TEXT NOT NULL,
                    FOREIGN KEY(recommendation_id) REFERENCES recommendations(recommendation_id) ON DELETE CASCADE
                );

CREATE TABLE recommendations (
                    recommendation_id TEXT PRIMARY KEY,
                    model_id TEXT,
                    prediction_id TEXT,
                    field_id TEXT,
                    trial_id TEXT,
                    experimental_unit_id TEXT,
                    action_type TEXT NOT NULL,
                    action_text TEXT NOT NULL,
                    proposed_time TEXT,
                    amount REAL,
                    unit TEXT,
                    expected_effect REAL,
                    lower_bound REAL,
                    upper_bound REAL,
                    objective TEXT,
                    constraints_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    provenance_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(model_id) REFERENCES models(model_id) ON DELETE SET NULL,
                    FOREIGN KEY(prediction_id) REFERENCES predictions(prediction_id) ON DELETE SET NULL
                );

CREATE TABLE state_assimilations (
                    assimilation_id TEXT PRIMARY KEY,
                    field_id TEXT,
                    trial_id TEXT,
                    state_variable TEXT NOT NULL,
                    prior_mean REAL NOT NULL,
                    prior_sd REAL NOT NULL,
                    observation REAL NOT NULL,
                    observation_sd REAL NOT NULL,
                    posterior_mean REAL NOT NULL,
                    posterior_sd REAL NOT NULL,
                    method TEXT NOT NULL,
                    provenance_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                , sequence_json TEXT NOT NULL DEFAULT '[]');

CREATE TABLE training_runs (
                    run_id TEXT PRIMARY KEY,
                    model_id TEXT,
                    dataset_id TEXT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    status TEXT NOT NULL,
                    settings_json TEXT NOT NULL,
                    split_summary_json TEXT NOT NULL,
                    leakage_guards_json TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    artifact_path TEXT,
                    notes TEXT,
                    FOREIGN KEY(model_id) REFERENCES models(model_id) ON DELETE SET NULL,
                    FOREIGN KEY(dataset_id) REFERENCES datasets(dataset_id) ON DELETE SET NULL
                );

CREATE TABLE treatment_outcomes (
                    outcome_id TEXT PRIMARY KEY,
                    recommendation_id TEXT,
                    field_id TEXT,
                    trial_id TEXT,
                    experimental_unit_id TEXT,
                    recommendation_followed INTEGER,
                    actual_action_text TEXT,
                    action_time TEXT,
                    outcome_variable TEXT NOT NULL,
                    outcome_value REAL,
                    outcome_unit TEXT,
                    measured_at TEXT,
                    covariates_json TEXT NOT NULL,
                    provenance_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(recommendation_id) REFERENCES recommendations(recommendation_id) ON DELETE SET NULL
                );

CREATE TABLE validation_runs (
                    validation_id TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL,
                    dataset_id TEXT,
                    validation_type TEXT NOT NULL,
                    evidence_level TEXT NOT NULL,
                    primary_metric TEXT,
                    metrics_json TEXT NOT NULL,
                    fold_metrics_json TEXT NOT NULL,
                    predictions_json TEXT NOT NULL,
                    split_manifest_json TEXT NOT NULL,
                    calibration_json TEXT NOT NULL,
                    uncertainty_json TEXT NOT NULL,
                    applicability_json TEXT NOT NULL,
                    leakage_guards_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(model_id) REFERENCES models(model_id) ON DELETE CASCADE,
                    FOREIGN KEY(dataset_id) REFERENCES datasets(dataset_id) ON DELETE SET NULL
                );

CREATE INDEX idx_causal_analyses_field ON causal_analyses(field_id, created_at);

CREATE INDEX idx_data_acquisitions_field ON data_acquisitions(field_id, created_at);

CREATE INDEX idx_decision_runs_field ON decision_runs(field_id, created_at);

CREATE INDEX idx_model_health_model ON model_health_events(model_id, created_at);

CREATE INDEX idx_model_status_history_model ON model_status_history(model_id, changed_at);

CREATE INDEX idx_model_versions_model ON model_versions(model_id, version_number);

CREATE INDEX idx_models_status ON models(status, task_type);

CREATE INDEX idx_observations_field ON observations(field_id, observed_at);

CREATE INDEX idx_observations_trial ON observations(trial_id, observed_at);

CREATE INDEX idx_prediction_outcomes_prediction ON prediction_outcome_links(prediction_id, matched_at);

CREATE INDEX idx_predictions_field ON predictions(field_id, generated_at);

CREATE INDEX idx_predictions_trial ON predictions(trial_id, generated_at);

CREATE INDEX idx_recommendation_status_history_rec ON recommendation_status_history(recommendation_id, changed_at);

CREATE INDEX idx_recommendations_field ON recommendations(field_id, created_at);

CREATE INDEX idx_state_assimilations_field ON state_assimilations(field_id, created_at);

CREATE INDEX idx_validation_runs_model ON validation_runs(model_id, created_at);
