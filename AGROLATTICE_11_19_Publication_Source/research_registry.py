"""Research model, evidence, observation, prediction and recommendation registry.

AGROLATTICE 11.3 introduced this additive database; later releases added data-acquisition, decision, state-assimilation and causal-audit records. Release 11.14 adds immutable dataset/model versioning, persistent validation evidence, auditable model-status history, prediction-outcome links and model-health evidence without modifying the protected Field Operations, Pollination Lab or Persistent Twin schemas.

The registry records provenance and scientific status for research models and their outputs. It does not promote a prediction to an agronomic recommendation by itself.
"""
from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd

MODULE_VERSION = "2.0.0"
DB_SCHEMA_VERSION = "2.0.0"
MODEL_STATUSES = (
    "Prototype",
    "Internally validated",
    "Externally validated",
    "Operationally eligible",
    "Retired",
)
EVIDENCE_TYPES = (
    "Measured",
    "Derived",
    "Assumption",
    "Prior",
    "Forecast",
    "Model output",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_text(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True, default=str)


def json_value(value: Any, default: Any = None) -> Any:
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list, tuple, int, float, bool)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class RegistrySummary:
    datasets: int
    observations: int
    models: int
    predictions: int
    recommendations: int
    treatment_outcomes: int
    benchmark_runs: int
    data_acquisitions: int = 0
    decision_runs: int = 0
    state_assimilations: int = 0
    causal_analyses: int = 0


class ResearchRegistryError(RuntimeError):
    """Raised when registry operations would be invalid or unsafe."""


class ResearchEvidenceRegistry:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._upgrade_backup: Path | None = None
        self._pre_upgrade_counts: dict[str, int] = {}
        self._backup_before_schema_upgrade()
        self._initialise()
        self._verify_schema_upgrade()

    def _backup_before_schema_upgrade(self) -> None:
        """Snapshot an existing older registry before any Research Evidence schema change.

        SQLite's online backup API includes committed WAL content. A backup is
        created only when an existing metadata schema version differs from the
        current version, so ordinary startup does not generate repeated copies.
        """
        if not self.path.exists() or self.path.stat().st_size == 0:
            return
        try:
            with sqlite3.connect(self.path) as source:
                table_names = {str(row[0]) for row in source.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
                if "metadata" not in table_names:
                    return
                row = source.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
                existing_version = str(row[0]) if row and row[0] is not None else None
                if not existing_version or existing_version == DB_SCHEMA_VERSION:
                    return
                for table in sorted(table_names):
                    if table.startswith("sqlite_"):
                        continue
                    safe = table.replace('"', '""')
                    self._pre_upgrade_counts[table] = int(source.execute(f'SELECT COUNT(*) FROM "{safe}"').fetchone()[0])
                backup_dir = self.path.parent / "backups"
                backup_dir.mkdir(parents=True, exist_ok=True)
                stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                clean_version = ''.join(ch if ch.isalnum() or ch in '._-' else '_' for ch in existing_version)
                backup_path = backup_dir / f"research_evidence_pre_{clean_version}_to_{DB_SCHEMA_VERSION}_{stamp}.sqlite"
                with sqlite3.connect(backup_path) as destination:
                    source.backup(destination)
                with sqlite3.connect(backup_path) as check:
                    integrity = check.execute("PRAGMA integrity_check").fetchone()
                    if not integrity or str(integrity[0]).casefold() != "ok":
                        backup_path.unlink(missing_ok=True)
                        raise ResearchRegistryError(f"Pre-upgrade Research Evidence backup failed integrity_check: {integrity}")
                self._upgrade_backup = backup_path
        except ResearchRegistryError:
            raise
        except sqlite3.Error as error:
            raise ResearchRegistryError(f"Could not create pre-upgrade Research Evidence backup: {error}") from error

    def _verify_schema_upgrade(self) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            integrity = connection.execute("PRAGMA integrity_check").fetchone()
            if not integrity or str(integrity[0]).casefold() != "ok":
                raise ResearchRegistryError(f"Research Evidence integrity_check failed after schema initialisation: {integrity}")
            foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
            if foreign_keys:
                raise ResearchRegistryError(f"Research Evidence foreign_key_check found {len(foreign_keys)} issue(s) after schema initialisation.")
            for table, before in self._pre_upgrade_counts.items():
                exists = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
                if not exists:
                    raise ResearchRegistryError(f"Schema upgrade removed existing table {table!r}.")
                safe = table.replace('"', '""')
                after = int(connection.execute(f'SELECT COUNT(*) FROM "{safe}"').fetchone()[0])
                if after < before:
                    raise ResearchRegistryError(f"Schema upgrade reduced row count in {table!r}: {before} -> {after}.")

    @contextmanager
    def connection(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialise(self) -> None:
        with self.connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS datasets (
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

                CREATE TABLE IF NOT EXISTS observations (
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

                CREATE TABLE IF NOT EXISTS models (
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

                CREATE TABLE IF NOT EXISTS training_runs (
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

                CREATE TABLE IF NOT EXISTS predictions (
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
                    prediction_text TEXT,
                    class_probabilities_json TEXT NOT NULL DEFAULT '{}',
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
                    generated_at TEXT NOT NULL,
                    FOREIGN KEY(model_id) REFERENCES models(model_id) ON DELETE RESTRICT
                );

                CREATE TABLE IF NOT EXISTS recommendations (
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

                CREATE TABLE IF NOT EXISTS recommendation_status_history (
                    event_id TEXT PRIMARY KEY,
                    recommendation_id TEXT NOT NULL,
                    old_status TEXT,
                    new_status TEXT NOT NULL,
                    note TEXT,
                    changed_at TEXT NOT NULL,
                    FOREIGN KEY(recommendation_id) REFERENCES recommendations(recommendation_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS treatment_outcomes (
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

                CREATE TABLE IF NOT EXISTS benchmark_runs (
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

                CREATE TABLE IF NOT EXISTS data_acquisitions (
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

                CREATE TABLE IF NOT EXISTS decision_runs (
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

                CREATE TABLE IF NOT EXISTS state_assimilations (
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
                    sequence_json TEXT NOT NULL DEFAULT '[]',
                    provenance_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS causal_analyses (
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



                CREATE TABLE IF NOT EXISTS dataset_snapshots (
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

                CREATE TABLE IF NOT EXISTS model_versions (
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

                CREATE TABLE IF NOT EXISTS model_status_history (
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

                CREATE TABLE IF NOT EXISTS validation_runs (
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

                CREATE TABLE IF NOT EXISTS prediction_outcome_links (
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

                CREATE TABLE IF NOT EXISTS model_health_events (
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

                CREATE INDEX IF NOT EXISTS idx_observations_field ON observations(field_id, observed_at);
                CREATE INDEX IF NOT EXISTS idx_observations_trial ON observations(trial_id, observed_at);
                CREATE INDEX IF NOT EXISTS idx_predictions_field ON predictions(field_id, generated_at);
                CREATE INDEX IF NOT EXISTS idx_predictions_trial ON predictions(trial_id, generated_at);
                CREATE INDEX IF NOT EXISTS idx_models_status ON models(status, task_type);
                CREATE INDEX IF NOT EXISTS idx_recommendations_field ON recommendations(field_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_recommendation_status_history_rec ON recommendation_status_history(recommendation_id, changed_at);
                CREATE INDEX IF NOT EXISTS idx_data_acquisitions_field ON data_acquisitions(field_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_decision_runs_field ON decision_runs(field_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_state_assimilations_field ON state_assimilations(field_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_causal_analyses_field ON causal_analyses(field_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_model_versions_model ON model_versions(model_id, version_number);
                CREATE INDEX IF NOT EXISTS idx_model_status_history_model ON model_status_history(model_id, changed_at);
                CREATE INDEX IF NOT EXISTS idx_validation_runs_model ON validation_runs(model_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_prediction_outcomes_prediction ON prediction_outcome_links(prediction_id, matched_at);
                CREATE INDEX IF NOT EXISTS idx_model_health_model ON model_health_events(model_id, created_at);
                """
            )
            # Additive schema migration for early Release 11.3 development databases.
            # Explicit-column INSERTs below keep column order irrelevant.
            state_columns = {row[1] for row in connection.execute("PRAGMA table_info(state_assimilations)").fetchall()}
            if "sequence_json" not in state_columns:
                connection.execute("ALTER TABLE state_assimilations ADD COLUMN sequence_json TEXT NOT NULL DEFAULT '[]'")

            prediction_columns = {row[1] for row in connection.execute("PRAGMA table_info(predictions)").fetchall()}
            if "prediction_text" not in prediction_columns:
                connection.execute("ALTER TABLE predictions ADD COLUMN prediction_text TEXT")
            if "class_probabilities_json" not in prediction_columns:
                connection.execute("ALTER TABLE predictions ADD COLUMN class_probabilities_json TEXT NOT NULL DEFAULT '{}' ")

            connection.execute(
                "INSERT INTO metadata(key,value) VALUES('schema_version',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (DB_SCHEMA_VERSION,),
            )

    def integrity_check(self) -> dict[str, Any]:
        with self.connection() as connection:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            foreign_keys = [dict(row) for row in connection.execute("PRAGMA foreign_key_check")]
            version = connection.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
        return {
            "integrity_check": integrity,
            "foreign_key_issues": foreign_keys,
            "schema_version": version[0] if version else None,
        }

    def summary(self) -> RegistrySummary:
        tables = ["datasets", "observations", "models", "predictions", "recommendations", "treatment_outcomes", "benchmark_runs", "data_acquisitions", "decision_runs", "state_assimilations", "causal_analyses"]
        with self.connection() as connection:
            counts = {table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]) for table in tables}
        return RegistrySummary(
            datasets=counts["datasets"],
            observations=counts["observations"],
            models=counts["models"],
            predictions=counts["predictions"],
            recommendations=counts["recommendations"],
            treatment_outcomes=counts["treatment_outcomes"],
            benchmark_runs=counts["benchmark_runs"],
            data_acquisitions=counts["data_acquisitions"],
            decision_runs=counts["decision_runs"],
            state_assimilations=counts["state_assimilations"],
            causal_analyses=counts["causal_analyses"],
        )

    def register_dataset(self, record: Mapping[str, Any]) -> str:
        dataset_id = str(record.get("dataset_id") or uuid.uuid4())
        name = str(record.get("name") or "").strip()
        if not name:
            raise ResearchRegistryError("Dataset name is required.")
        local_path = str(record.get("local_path") or "").strip() or None
        file_hash = str(record.get("sha256") or "").strip() or None
        if local_path and not file_hash and Path(local_path).is_file():
            file_hash = sha256_file(local_path)
        now = utc_now()
        values = (
            dataset_id, name, record.get("dataset_type"), record.get("source"), record.get("source_version"),
            record.get("licence"), local_path, file_hash, record.get("crop_scope"), record.get("geography_scope"),
            record.get("spatial_resolution"), record.get("temporal_resolution"), json_text(record.get("provenance")),
            record.get("notes"), now, now,
        )
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO datasets VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(dataset_id) DO UPDATE SET
                    name=excluded.name,dataset_type=excluded.dataset_type,source=excluded.source,
                    source_version=excluded.source_version,licence=excluded.licence,local_path=excluded.local_path,
                    sha256=excluded.sha256,crop_scope=excluded.crop_scope,geography_scope=excluded.geography_scope,
                    spatial_resolution=excluded.spatial_resolution,temporal_resolution=excluded.temporal_resolution,
                    provenance_json=excluded.provenance_json,notes=excluded.notes,updated_at=excluded.updated_at
                """,
                values,
            )
        return dataset_id

    def datasets(self) -> pd.DataFrame:
        with self.connection() as connection:
            return pd.read_sql_query("SELECT * FROM datasets ORDER BY updated_at DESC", connection)

    def add_observations(self, rows: Sequence[Mapping[str, Any]]) -> int:
        if not rows:
            return 0
        payload = []
        for row in rows:
            evidence_type = str(row.get("evidence_type") or "Measured")
            if evidence_type not in EVIDENCE_TYPES:
                raise ResearchRegistryError(f"Unsupported evidence type: {evidence_type}")
            variable = str(row.get("variable") or "").strip()
            entity_type = str(row.get("entity_type") or "").strip()
            if not variable or not entity_type:
                raise ResearchRegistryError("Each observation requires entity_type and variable.")
            payload.append((
                str(row.get("observation_id") or uuid.uuid4()), row.get("dataset_id"), entity_type, row.get("entity_id"),
                row.get("field_id"), row.get("trial_id"), row.get("experimental_unit_id"), row.get("observed_at"),
                row.get("period_start"), row.get("period_end"), variable, row.get("value_numeric"), row.get("value_text"),
                row.get("unit"), evidence_type, json_text(row.get("geometry")) if row.get("geometry") is not None else None,
                row.get("spatial_support"), row.get("spatial_resolution_m"), row.get("temporal_resolution"),
                row.get("quality_flag"), row.get("source"), json_text(row.get("provenance")), utc_now(),
            ))
        with self.connection() as connection:
            connection.executemany(
                "INSERT INTO observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                payload,
            )
        return len(payload)

    def observations(self, *, field_id: str | None = None, trial_id: str | None = None, limit: int = 5000) -> pd.DataFrame:
        where, params = [], []
        if field_id:
            where.append("field_id=?"); params.append(field_id)
        if trial_id:
            where.append("trial_id=?"); params.append(trial_id)
        clause = " WHERE " + " AND ".join(where) if where else ""
        with self.connection() as connection:
            return pd.read_sql_query(
                f"SELECT * FROM observations{clause} ORDER BY observed_at DESC, created_at DESC LIMIT ?",
                connection, params=params + [int(limit)],
            )

    def register_model(self, record: Mapping[str, Any]) -> str:
        model_id = str(record.get("model_id") or uuid.uuid4())
        name = str(record.get("name") or "").strip()
        family = str(record.get("family") or "").strip()
        target = str(record.get("target") or "").strip()
        task_type = str(record.get("task_type") or "").strip()
        if not all((name, family, target, task_type)):
            raise ResearchRegistryError("Model name, family, target and task_type are required.")
        requested_status = str(record.get("status") or "Prototype")
        if requested_status not in MODEL_STATUSES:
            raise ResearchRegistryError(f"Unsupported model status: {requested_status}")
        existing_model = self.model(model_id)
        # Scientific-governance rule: evidence status is never promoted by an
        # upsert. New registrations begin as Prototype; existing registrations
        # retain their current status. Use change_model_status() for every
        # auditable promotion/demotion/retirement decision.
        status = str(existing_model.get("status")) if existing_model else "Prototype"
        implementation_type = str(record.get("implementation_type") or "Independent adaptation")
        now = utc_now()
        values = (
            model_id, name, family, target, task_type, status, record.get("source_method"), record.get("source_citation"),
            implementation_type, record.get("training_dataset_id"), json_text(record.get("training_scope")),
            json_text(record.get("required_modalities", [])), json_text(record.get("feature_names", [])),
            json_text(record.get("preprocessing")), json_text(record.get("validation_protocol")),
            json_text(record.get("metrics")), json_text(record.get("calibration")), record.get("uncertainty_method"),
            json_text(record.get("applicability")), json_text(record.get("limitations", [])), record.get("artifact_path"),
            json_text(record.get("dependency_versions")), record.get("code_version"), now, now,
        )
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO models VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(model_id) DO UPDATE SET
                    name=excluded.name,family=excluded.family,target=excluded.target,task_type=excluded.task_type,
                    status=excluded.status,source_method=excluded.source_method,source_citation=excluded.source_citation,
                    implementation_type=excluded.implementation_type,training_dataset_id=excluded.training_dataset_id,
                    training_scope_json=excluded.training_scope_json,required_modalities_json=excluded.required_modalities_json,
                    feature_names_json=excluded.feature_names_json,preprocessing_json=excluded.preprocessing_json,
                    validation_protocol_json=excluded.validation_protocol_json,metrics_json=excluded.metrics_json,
                    calibration_json=excluded.calibration_json,uncertainty_method=excluded.uncertainty_method,
                    applicability_json=excluded.applicability_json,limitations_json=excluded.limitations_json,
                    artifact_path=excluded.artifact_path,dependency_versions_json=excluded.dependency_versions_json,
                    code_version=excluded.code_version,updated_at=excluded.updated_at
                """,
                values,
            )
        return model_id

    def models(self, *, status: str | None = None) -> pd.DataFrame:
        query = "SELECT * FROM models"
        params: list[Any] = []
        if status:
            query += " WHERE status=?"; params.append(status)
        query += " ORDER BY updated_at DESC"
        with self.connection() as connection:
            return pd.read_sql_query(query, connection, params=params)

    def model(self, model_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM models WHERE model_id=?", (model_id,)).fetchone()
        return dict(row) if row else None

    def save_training_run(self, record: Mapping[str, Any]) -> str:
        run_id = str(record.get("run_id") or uuid.uuid4())
        with self.connection() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO training_runs VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    run_id, record.get("model_id"), record.get("dataset_id"), record.get("started_at") or utc_now(),
                    record.get("completed_at"), record.get("status") or "Completed", json_text(record.get("settings")),
                    json_text(record.get("split_summary")), json_text(record.get("leakage_guards")),
                    json_text(record.get("metrics")), record.get("artifact_path"), record.get("notes"),
                ),
            )
        return run_id

    def training_runs(self, *, model_id: str | None = None) -> pd.DataFrame:
        query, params = "SELECT * FROM training_runs", []
        if model_id:
            query += " WHERE model_id=?"; params.append(model_id)
        query += " ORDER BY started_at DESC"
        with self.connection() as connection:
            return pd.read_sql_query(query, connection, params=params)

    def save_prediction(self, record: Mapping[str, Any]) -> str:
        prediction_id = str(record.get("prediction_id") or uuid.uuid4())
        model_id = str(record.get("model_id") or "").strip()
        if not model_id:
            raise ResearchRegistryError("Prediction requires model_id.")
        target = str(record.get("target") or "").strip()
        entity_type = str(record.get("entity_type") or "").strip()
        if not target or not entity_type:
            raise ResearchRegistryError("Prediction requires target and entity_type.")
        prediction_numeric = record.get("prediction")
        prediction_text = record.get("prediction_text")
        if prediction_numeric is not None:
            try:
                prediction_numeric = float(prediction_numeric)
            except Exception as error:
                raise ResearchRegistryError("Numeric prediction must be a finite number or omitted in favour of prediction_text.") from error
            if not math.isfinite(prediction_numeric):
                raise ResearchRegistryError("Numeric prediction must be finite.")
        if prediction_text is not None:
            prediction_text = str(prediction_text)
        if prediction_numeric is None and not prediction_text:
            raise ResearchRegistryError("Prediction requires either a numeric prediction or prediction_text.")
        probabilities = record.get("class_probabilities") or {}
        if probabilities and not isinstance(probabilities, Mapping):
            raise ResearchRegistryError("class_probabilities must be a mapping of class label to probability.")
        probability_payload: dict[str, float] = {}
        for label, value in dict(probabilities).items():
            try:
                probability = float(value)
            except Exception as error:
                raise ResearchRegistryError(f"Invalid probability for class {label!r}.") from error
            if not math.isfinite(probability) or probability < 0 or probability > 1:
                raise ResearchRegistryError(f"Class probability for {label!r} must be between 0 and 1.")
            probability_payload[str(label)] = probability
        lower, upper = record.get("lower_bound"), record.get("upper_bound")
        if lower is not None:
            lower = float(lower)
        if upper is not None:
            upper = float(upper)
        if lower is not None and upper is not None and lower > upper:
            raise ResearchRegistryError("Prediction lower_bound cannot exceed upper_bound.")
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO predictions(
                    prediction_id,model_id,entity_type,entity_id,field_id,trial_id,season_year,target,horizon,
                    prediction,prediction_text,class_probabilities_json,lower_bound,upper_bound,
                    uncertainty_total,uncertainty_aleatoric,uncertainty_epistemic,uncertainty_method,
                    applicability_status,applicability_score,input_snapshot_json,provenance_json,generated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    prediction_id, model_id, entity_type, record.get("entity_id"), record.get("field_id"), record.get("trial_id"),
                    record.get("season_year"), target, record.get("horizon"), prediction_numeric, prediction_text,
                    json_text(probability_payload), lower, upper, record.get("uncertainty_total"),
                    record.get("uncertainty_aleatoric"), record.get("uncertainty_epistemic"), record.get("uncertainty_method"),
                    record.get("applicability_status"), record.get("applicability_score"), json_text(record.get("input_snapshot")),
                    json_text(record.get("provenance")), record.get("generated_at") or utc_now(),
                ),
            )
        return prediction_id

    def predictions(self, *, field_id: str | None = None, trial_id: str | None = None, model_id: str | None = None, limit: int = 2000) -> pd.DataFrame:
        where, params = [], []
        for column, value in (("field_id", field_id), ("trial_id", trial_id), ("model_id", model_id)):
            if value:
                where.append(f"p.{column}=?"); params.append(value)
        clause = " WHERE " + " AND ".join(where) if where else ""
        query = (
            "SELECT p.*,m.name AS model_name,m.family AS model_family,m.status AS model_status "
            "FROM predictions p JOIN models m ON p.model_id=m.model_id" + clause +
            " ORDER BY p.generated_at DESC LIMIT ?"
        )
        with self.connection() as connection:
            return pd.read_sql_query(query, connection, params=params + [int(limit)])

    def save_recommendation(self, record: Mapping[str, Any]) -> str:
        recommendation_id = str(record.get("recommendation_id") or uuid.uuid4())
        action_type = str(record.get("action_type") or "").strip()
        action_text = str(record.get("action_text") or "").strip()
        if not action_type or not action_text:
            raise ResearchRegistryError("Recommendation requires action_type and action_text.")
        status = str(record.get("status") or "Proposed")
        now = utc_now()
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO recommendations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    recommendation_id, record.get("model_id"), record.get("prediction_id"), record.get("field_id"),
                    record.get("trial_id"), record.get("experimental_unit_id"), action_type, action_text,
                    record.get("proposed_time"), record.get("amount"), record.get("unit"), record.get("expected_effect"),
                    record.get("lower_bound"), record.get("upper_bound"), record.get("objective"),
                    json_text(record.get("constraints")), status, json_text(record.get("provenance")), now, now,
                ),
            )
            connection.execute(
                "INSERT INTO recommendation_status_history(event_id,recommendation_id,old_status,new_status,note,changed_at) VALUES(?,?,?,?,?,?)",
                (str(uuid.uuid4()), recommendation_id, None, status, str(record.get("status_note") or "Created"), now),
            )
        return recommendation_id

    def recommendations(self, *, field_id: str | None = None, trial_id: str | None = None) -> pd.DataFrame:
        where, params = [], []
        if field_id:
            where.append("field_id=?"); params.append(field_id)
        if trial_id:
            where.append("trial_id=?"); params.append(trial_id)
        clause = " WHERE " + " AND ".join(where) if where else ""
        with self.connection() as connection:
            return pd.read_sql_query(f"SELECT * FROM recommendations{clause} ORDER BY created_at DESC", connection, params=params)

    def update_recommendation_status(self, recommendation_id: str, status: str, note: str | None = None) -> None:
        changed_at = utc_now()
        with self.connection() as connection:
            existing = connection.execute("SELECT status FROM recommendations WHERE recommendation_id=?", (recommendation_id,)).fetchone()
            if existing is None:
                raise ResearchRegistryError("Recommendation was not found.")
            old_status = existing[0]
            connection.execute(
                "UPDATE recommendations SET status=?,updated_at=? WHERE recommendation_id=?",
                (status, changed_at, recommendation_id),
            )
            connection.execute(
                "INSERT INTO recommendation_status_history(event_id,recommendation_id,old_status,new_status,note,changed_at) VALUES(?,?,?,?,?,?)",
                (str(uuid.uuid4()), recommendation_id, old_status, status, note, changed_at),
            )

    def recommendation_status_history(self, recommendation_id: str | None = None, limit: int = 5000) -> pd.DataFrame:
        query = "SELECT * FROM recommendation_status_history"
        params: list[Any] = []
        if recommendation_id:
            query += " WHERE recommendation_id=?"
            params.append(recommendation_id)
        query += " ORDER BY changed_at DESC LIMIT ?"
        params.append(int(limit))
        with self.connection() as connection:
            return pd.read_sql_query(query, connection, params=params)

    def save_treatment_outcome(self, record: Mapping[str, Any]) -> str:
        outcome_id = str(record.get("outcome_id") or uuid.uuid4())
        variable = str(record.get("outcome_variable") or "").strip()
        if not variable:
            raise ResearchRegistryError("Treatment outcome requires outcome_variable.")
        followed = record.get("recommendation_followed")
        followed_value = None if followed is None else int(bool(followed))
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO treatment_outcomes VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    outcome_id, record.get("recommendation_id"), record.get("field_id"), record.get("trial_id"),
                    record.get("experimental_unit_id"), followed_value, record.get("actual_action_text"),
                    record.get("action_time"), variable, record.get("outcome_value"), record.get("outcome_unit"),
                    record.get("measured_at"), json_text(record.get("covariates")), json_text(record.get("provenance")), utc_now(),
                ),
            )
        return outcome_id

    def treatment_outcomes(self, *, recommendation_id: str | None = None, field_id: str | None = None, trial_id: str | None = None) -> pd.DataFrame:
        where, params = [], []
        for column, value in (("recommendation_id", recommendation_id), ("field_id", field_id), ("trial_id", trial_id)):
            if value:
                where.append(f"{column}=?"); params.append(value)
        clause = " WHERE " + " AND ".join(where) if where else ""
        with self.connection() as connection:
            return pd.read_sql_query(
                f"SELECT * FROM treatment_outcomes{clause} ORDER BY measured_at DESC, created_at DESC",
                connection, params=params,
            )

    def save_benchmark_run(self, record: Mapping[str, Any]) -> str:
        run_id = str(record.get("benchmark_run_id") or uuid.uuid4())
        benchmark = str(record.get("benchmark_name") or "").strip()
        protocol = str(record.get("protocol") or "").strip()
        if not benchmark or not protocol:
            raise ResearchRegistryError("Benchmark run requires benchmark_name and protocol.")
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO benchmark_runs VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (
                    run_id, benchmark, record.get("model_id"), record.get("dataset_id"), protocol,
                    json_text(record.get("settings")), json_text(record.get("metrics")), json_text(record.get("applicability")),
                    record.get("started_at"), record.get("completed_at") or utc_now(), record.get("notes"),
                ),
            )
        return run_id

    def benchmark_runs(self) -> pd.DataFrame:
        with self.connection() as connection:
            return pd.read_sql_query("SELECT * FROM benchmark_runs ORDER BY completed_at DESC", connection)

    def save_data_acquisition(self, record: Mapping[str, Any]) -> str:
        acquisition_id = str(record.get("acquisition_id") or uuid.uuid4())
        source = str(record.get("source") or "").strip()
        source_type = str(record.get("source_type") or "").strip()
        if not source or not source_type:
            raise ResearchRegistryError("Data acquisition source and source_type are required.")
        with self.connection() as connection:
            connection.execute(
                """INSERT INTO data_acquisitions(
                    acquisition_id,dataset_id,source,source_type,field_id,trial_id,latitude,longitude,
                    period_start,period_end,temporal_resolution,variables_json,request_json,provenance_json,
                    row_count,status,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    acquisition_id, record.get("dataset_id"), source, source_type, record.get("field_id"),
                    record.get("trial_id"), record.get("latitude"), record.get("longitude"),
                    record.get("period_start"), record.get("period_end"), record.get("temporal_resolution"),
                    json_text(record.get("variables") or []), json_text(record.get("request") or {}),
                    json_text(record.get("provenance") or {}), int(record.get("row_count") or 0),
                    str(record.get("status") or "Completed"), utc_now(),
                ),
            )
        return acquisition_id

    def data_acquisitions(self, *, field_id: str | None = None, limit: int = 1000) -> pd.DataFrame:
        query = "SELECT * FROM data_acquisitions"
        params: list[Any] = []
        if field_id:
            query += " WHERE field_id=?"
            params.append(field_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(int(limit))
        with self.connection() as connection:
            return pd.read_sql_query(query, connection, params=tuple(params))

    def save_decision_run(self, record: Mapping[str, Any]) -> str:
        run_id = str(record.get("decision_run_id") or uuid.uuid4())
        decision_type = str(record.get("decision_type") or "").strip()
        objective = str(record.get("objective") or "").strip()
        if not decision_type or not objective:
            raise ResearchRegistryError("Decision run requires decision_type and objective.")
        with self.connection() as connection:
            connection.execute(
                """INSERT INTO decision_runs(
                    decision_run_id,decision_type,field_id,trial_id,dataset_id,objective,status,
                    input_snapshot_json,alternatives_json,selected_alternative_json,constraints_json,
                    metrics_json,provenance_json,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    run_id, decision_type, record.get("field_id"), record.get("trial_id"), record.get("dataset_id"),
                    objective, str(record.get("status") or "Research scenario"),
                    json_text(record.get("input_snapshot") or {}), json_text(record.get("alternatives") or []),
                    json_text(record.get("selected_alternative") or {}), json_text(record.get("constraints") or {}),
                    json_text(record.get("metrics") or {}), json_text(record.get("provenance") or {}), utc_now(),
                ),
            )
        return run_id

    def decision_runs(self, *, field_id: str | None = None, decision_type: str | None = None, limit: int = 1000) -> pd.DataFrame:
        where, params = [], []
        if field_id:
            where.append("field_id=?"); params.append(field_id)
        if decision_type:
            where.append("decision_type=?"); params.append(decision_type)
        clause = " WHERE " + " AND ".join(where) if where else ""
        with self.connection() as connection:
            return pd.read_sql_query(
                f"SELECT * FROM decision_runs{clause} ORDER BY created_at DESC LIMIT ?",
                connection, params=params + [int(limit)],
            )

    def save_state_assimilation(self, record: Mapping[str, Any]) -> str:
        assimilation_id = str(record.get("assimilation_id") or uuid.uuid4())
        variable = str(record.get("state_variable") or "").strip()
        if not variable:
            raise ResearchRegistryError("State assimilation requires state_variable.")
        numeric_names = ["prior_mean", "prior_sd", "observation", "observation_sd", "posterior_mean", "posterior_sd"]
        values = {}
        for name in numeric_names:
            value = pd.to_numeric(record.get(name), errors="coerce")
            if pd.isna(value):
                raise ResearchRegistryError(f"State assimilation requires numeric {name}.")
            values[name] = float(value)
        if values["prior_sd"] <= 0 or values["observation_sd"] <= 0 or values["posterior_sd"] < 0:
            raise ResearchRegistryError("State-assimilation uncertainty values are invalid.")
        with self.connection() as connection:
            connection.execute(
                """INSERT INTO state_assimilations(
                    assimilation_id,field_id,trial_id,state_variable,prior_mean,prior_sd,observation,
                    observation_sd,posterior_mean,posterior_sd,method,sequence_json,provenance_json,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    assimilation_id, record.get("field_id"), record.get("trial_id"), variable,
                    values["prior_mean"], values["prior_sd"], values["observation"], values["observation_sd"],
                    values["posterior_mean"], values["posterior_sd"], str(record.get("method") or "Independent Gaussian update"),
                    json_text(record.get("sequence") or []), json_text(record.get("provenance") or {}), utc_now(),
                ),
            )
        return assimilation_id

    def state_assimilations(self, *, field_id: str | None = None, limit: int = 1000) -> pd.DataFrame:
        query = "SELECT * FROM state_assimilations"
        params: list[Any] = []
        if field_id:
            query += " WHERE field_id=?"; params.append(field_id)
        query += " ORDER BY created_at DESC LIMIT ?"; params.append(int(limit))
        with self.connection() as connection:
            return pd.read_sql_query(query, connection, params=params)

    def save_causal_analysis(self, record: Mapping[str, Any]) -> str:
        analysis_id = str(record.get("analysis_id") or uuid.uuid4())
        name = str(record.get("name") or "").strip()
        treatment = str(record.get("treatment") or "").strip()
        outcome = str(record.get("outcome") or "").strip()
        method = str(record.get("method") or "").strip()
        if not all((name, treatment, outcome, method)):
            raise ResearchRegistryError("Causal analysis requires name, treatment, outcome and method.")
        with self.connection() as connection:
            connection.execute(
                """INSERT INTO causal_analyses(
                    analysis_id,name,dataset_id,field_id,trial_id,treatment,outcome,covariates_json,
                    group_column,method,assumptions_json,diagnostics_json,estimates_json,provenance_json,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    analysis_id, name, record.get("dataset_id"), record.get("field_id"), record.get("trial_id"),
                    treatment, outcome, json_text(record.get("covariates") or []), record.get("group_column"), method,
                    json_text(record.get("assumptions") or []), json_text(record.get("diagnostics") or {}),
                    json_text(record.get("estimates") or {}), json_text(record.get("provenance") or {}), utc_now(),
                ),
            )
        return analysis_id

    def causal_analyses(self, *, field_id: str | None = None, limit: int = 1000) -> pd.DataFrame:
        query = "SELECT * FROM causal_analyses"
        params: list[Any] = []
        if field_id:
            query += " WHERE field_id=?"; params.append(field_id)
        query += " ORDER BY created_at DESC LIMIT ?"; params.append(int(limit))
        with self.connection() as connection:
            return pd.read_sql_query(query, connection, params=params)


    def save_dataset_snapshot(self, record: Mapping[str, Any]) -> str:
        snapshot_id = str(record.get("snapshot_id") or uuid.uuid4())
        name = str(record.get("name") or "Dataset snapshot").strip()
        local_path = str(record.get("local_path") or "").strip() or None
        file_hash = str(record.get("sha256") or "").strip() or None
        if local_path and not file_hash and Path(local_path).is_file():
            file_hash = sha256_file(local_path)
        with self.connection() as connection:
            connection.execute(
                """INSERT INTO dataset_snapshots(snapshot_id,dataset_id,parent_snapshot_id,name,row_count,entity_count,manifest_json,local_path,sha256,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (snapshot_id, record.get("dataset_id"), record.get("parent_snapshot_id"), name,
                 record.get("row_count"), record.get("entity_count"), json_text(record.get("manifest")),
                 local_path, file_hash, utc_now()),
            )
        return snapshot_id

    def dataset_snapshots(self, *, dataset_id: str | None = None, limit: int = 1000) -> pd.DataFrame:
        query, params = "SELECT * FROM dataset_snapshots", []
        if dataset_id:
            query += " WHERE dataset_id=?"; params.append(dataset_id)
        query += " ORDER BY created_at DESC LIMIT ?"; params.append(int(limit))
        with self.connection() as connection:
            return pd.read_sql_query(query, connection, params=params)

    def register_model_version(self, record: Mapping[str, Any]) -> str:
        model_id = str(record.get("model_id") or "").strip()
        if not self.model(model_id):
            raise ResearchRegistryError("Model version requires an existing model_id.")
        version_id = str(record.get("version_id") or uuid.uuid4())
        artifact_path = str(record.get("artifact_path") or "").strip() or None
        artifact_sha256 = str(record.get("artifact_sha256") or "").strip() or None
        resolved = Path(artifact_path) if artifact_path else None
        if resolved and resolved.is_file() and not artifact_sha256:
            artifact_sha256 = sha256_file(resolved)
        with self.connection() as connection:
            row = connection.execute("SELECT COALESCE(MAX(version_number),0)+1 FROM model_versions WHERE model_id=?", (model_id,)).fetchone()
            version_number = int(record.get("version_number") or row[0])
            connection.execute(
                """INSERT INTO model_versions(version_id,model_id,version_number,parent_version_id,dataset_snapshot_id,artifact_path,artifact_sha256,environment_json,feature_contract_json,notes,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (version_id, model_id, version_number, record.get("parent_version_id"), record.get("dataset_snapshot_id"),
                 artifact_path, artifact_sha256, json_text(record.get("environment")), json_text(record.get("feature_contract")),
                 record.get("notes"), utc_now()),
            )
        return version_id

    def model_versions(self, model_id: str | None = None) -> pd.DataFrame:
        query, params = "SELECT * FROM model_versions", []
        if model_id:
            query += " WHERE model_id=?"; params.append(model_id)
        query += " ORDER BY model_id, version_number DESC"
        with self.connection() as connection:
            return pd.read_sql_query(query, connection, params=params)

    def latest_model_version(self, model_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM model_versions WHERE model_id=? ORDER BY version_number DESC LIMIT 1", (model_id,)).fetchone()
        return dict(row) if row else None

    def save_validation_run(self, record: Mapping[str, Any]) -> str:
        model_id = str(record.get("model_id") or "").strip()
        if not self.model(model_id):
            raise ResearchRegistryError("Validation run requires an existing model.")
        validation_id = str(record.get("validation_id") or uuid.uuid4())
        validation_type = str(record.get("validation_type") or "Unspecified validation").strip()
        evidence_level = str(record.get("evidence_level") or "Internal").strip()
        with self.connection() as connection:
            connection.execute(
                """INSERT INTO validation_runs(validation_id,model_id,dataset_id,validation_type,evidence_level,primary_metric,metrics_json,fold_metrics_json,predictions_json,split_manifest_json,calibration_json,uncertainty_json,applicability_json,leakage_guards_json,status,notes,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (validation_id, model_id, record.get("dataset_id"), validation_type, evidence_level, record.get("primary_metric"),
                 json_text(record.get("metrics")), json_text(record.get("fold_metrics")), json_text(record.get("predictions")),
                 json_text(record.get("split_manifest")), json_text(record.get("calibration")), json_text(record.get("uncertainty")),
                 json_text(record.get("applicability")), json_text(record.get("leakage_guards")), str(record.get("status") or "Completed"),
                 record.get("notes"), utc_now()),
            )
        return validation_id

    def validation_runs(self, *, model_id: str | None = None, evidence_level: str | None = None, limit: int = 2000) -> pd.DataFrame:
        where, params = [], []
        if model_id: where.append("model_id=?"); params.append(model_id)
        if evidence_level: where.append("evidence_level=?"); params.append(evidence_level)
        clause = " WHERE " + " AND ".join(where) if where else ""
        with self.connection() as connection:
            return pd.read_sql_query(f"SELECT * FROM validation_runs{clause} ORDER BY created_at DESC LIMIT ?", connection, params=params+[int(limit)])

    def model_status_history(self, model_id: str | None = None, limit: int = 2000) -> pd.DataFrame:
        query, params = "SELECT * FROM model_status_history", []
        if model_id:
            query += " WHERE model_id=?"; params.append(model_id)
        query += " ORDER BY changed_at DESC LIMIT ?"; params.append(int(limit))
        with self.connection() as connection:
            return pd.read_sql_query(query, connection, params=params)

    def promotion_requirements(self, model_id: str, target_status: str) -> dict[str, Any]:
        model = self.model(model_id)
        if not model:
            raise ResearchRegistryError("Model was not found.")
        if target_status not in MODEL_STATUSES:
            raise ResearchRegistryError(f"Unsupported model status: {target_status}")
        validations = self.validation_runs(model_id=model_id, limit=10000)
        limitations = json_value(model.get("limitations_json"), []) or []
        model_applicability = json_value(model.get("applicability_json"), {}) or {}
        model_calibration = json_value(model.get("calibration_json"), {}) or {}
        model_uncertainty = str(model.get("uncertainty_method") or "").strip()

        completed = validations.loc[validations["status"].astype(str).str.casefold().eq("completed")].copy() if not validations.empty else validations
        if not completed.empty:
            diagnostic = completed["evidence_level"].astype(str).str.casefold().str.contains("diagnostic") | completed["validation_type"].astype(str).str.casefold().str.contains("random diagnostic")
            held_out = completed.loc[~diagnostic].copy()
        else:
            held_out = completed
        internal = not held_out.empty

        leakage_documented = False
        external = False
        validation_applicability = False
        validation_uncertainty = False
        for _, row in held_out.iterrows() if not held_out.empty else []:
            leakage_documented = leakage_documented or bool(json_value(row.get("leakage_guards_json"), {}) or {})
            validation_applicability = validation_applicability or bool(json_value(row.get("applicability_json"), {}) or {})
            validation_uncertainty = validation_uncertainty or bool(json_value(row.get("uncertainty_json"), {}) or {}) or bool(json_value(row.get("calibration_json"), {}) or {})
            level = str(row.get("evidence_level") or "").casefold()
            # Externally validated is intentionally stricter than generic leave-one-group-out.
            # Parent-pair/trial/field holdouts remain important transfer evidence, but do not
            # by themselves establish external site/season/dataset validity.
            if any(token in level for token in ("independent external", "external", "cross-site", "cross-season", "benchmark")):
                external = True

        applicability_ok = bool(model_applicability) or validation_applicability
        uncertainty_ok = bool(model_uncertainty or model_calibration) or validation_uncertainty
        requirements = []
        if target_status in {"Internally validated", "Externally validated", "Operationally eligible"}:
            requirements.append(("At least one completed non-diagnostic held-out validation run", internal))
            requirements.append(("Leakage/split safeguards documented for held-out validation", leakage_documented))
        if target_status in {"Externally validated", "Operationally eligible"}:
            requirements.append(("Independent external, cross-site, cross-season or benchmark evidence", external))
        if target_status == "Operationally eligible":
            requirements.append(("Applicability profile documented", applicability_ok))
            requirements.append(("Uncertainty/calibration assessment documented", uncertainty_ok))
            requirements.append(("At least one documented limitation", bool(limitations)))
        return {
            "target_status": target_status,
            "requirements": [{"requirement": a, "met": bool(b)} for a, b in requirements],
            "passed": all(b for _, b in requirements) if requirements else True,
        }

    def change_model_status(self, model_id: str, new_status: str, *, rationale: str, override: bool = False, evidence: Mapping[str, Any] | None = None) -> dict[str, Any]:
        model = self.model(model_id)
        if not model:
            raise ResearchRegistryError("Model was not found.")
        if new_status not in MODEL_STATUSES:
            raise ResearchRegistryError(f"Unsupported model status: {new_status}")
        rationale = str(rationale or "").strip()
        if not rationale:
            raise ResearchRegistryError("A written rationale is required for every model-status change.")
        check = self.promotion_requirements(model_id, new_status)
        if not check["passed"] and not override:
            missing = [r["requirement"] for r in check["requirements"] if not r["met"]]
            raise ResearchRegistryError("Promotion blocked; missing evidence: " + "; ".join(missing))
        now = utc_now(); old = str(model.get("status") or "Prototype")
        with self.connection() as connection:
            connection.execute("UPDATE models SET status=?,updated_at=? WHERE model_id=?", (new_status, now, model_id))
            connection.execute(
                "INSERT INTO model_status_history(event_id,model_id,old_status,new_status,rationale,evidence_json,override_used,changed_at) VALUES(?,?,?,?,?,?,?,?)",
                (str(uuid.uuid4()), model_id, old, new_status, rationale, json_text({"gate": check, **dict(evidence or {})}), int(bool(override)), now),
            )
        return check

    def save_prediction_outcome_link(self, record: Mapping[str, Any]) -> str:
        match_id = str(record.get("match_id") or uuid.uuid4())
        prediction_id = str(record.get("prediction_id") or "").strip()
        if not prediction_id:
            raise ResearchRegistryError("Prediction-outcome link requires prediction_id.")
        with self.connection() as connection:
            connection.execute(
                """INSERT INTO prediction_outcome_links(match_id,prediction_id,observation_id,treatment_outcome_id,observed_value,observed_text,unit,matching_basis,provenance_json,matched_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (match_id, prediction_id, record.get("observation_id"), record.get("treatment_outcome_id"), record.get("observed_value"),
                 record.get("observed_text"), record.get("unit"), str(record.get("matching_basis") or "Manual match"), json_text(record.get("provenance")), utc_now()),
            )
        return match_id

    def prediction_outcome_links(self, *, model_id: str | None = None, limit: int = 5000) -> pd.DataFrame:
        query = "SELECT l.*,p.model_id,p.field_id,p.trial_id,p.target,p.prediction,p.prediction_text,p.generated_at FROM prediction_outcome_links l JOIN predictions p ON p.prediction_id=l.prediction_id"
        params=[]
        if model_id:
            query += " WHERE p.model_id=?"; params.append(model_id)
        query += " ORDER BY l.matched_at DESC LIMIT ?"; params.append(int(limit))
        with self.connection() as connection:
            return pd.read_sql_query(query, connection, params=params)

    def save_model_health_event(self, record: Mapping[str, Any]) -> str:
        event_id = str(record.get("health_event_id") or uuid.uuid4())
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO model_health_events VALUES(?,?,?,?,?,?,?,?,?)",
                (event_id, record.get("model_id"), str(record.get("health_status") or "Monitoring"), record.get("metric_name"), record.get("metric_value"), record.get("threshold"), json_text(record.get("evidence")), record.get("note"), utc_now())
            )
        return event_id

    def model_health_events(self, model_id: str | None = None, limit: int = 2000) -> pd.DataFrame:
        query, params = "SELECT * FROM model_health_events", []
        if model_id:
            query += " WHERE model_id=?"; params.append(model_id)
        query += " ORDER BY created_at DESC LIMIT ?"; params.append(int(limit))
        with self.connection() as connection:
            return pd.read_sql_query(query, connection, params=params)

    def export_model_card(self, model_id: str) -> dict[str, Any]:
        record = self.model(model_id)
        if not record:
            raise ResearchRegistryError("Model was not found.")
        parsed = dict(record)
        for key in (
            "training_scope_json", "required_modalities_json", "feature_names_json", "preprocessing_json",
            "validation_protocol_json", "metrics_json", "calibration_json", "applicability_json",
            "limitations_json", "dependency_versions_json",
        ):
            parsed[key.removesuffix("_json")] = json_value(parsed.pop(key), {})
        parsed["predictions_recorded"] = int(len(self.predictions(model_id=model_id, limit=1000000)))
        parsed["training_runs"] = self.training_runs(model_id=model_id).to_dict(orient="records")
        parsed["validation_runs"] = self.validation_runs(model_id=model_id).to_dict(orient="records")
        parsed["versions"] = self.model_versions(model_id).to_dict(orient="records")
        parsed["status_history"] = self.model_status_history(model_id).to_dict(orient="records")
        parsed["health_events"] = self.model_health_events(model_id).to_dict(orient="records")
        return parsed


def observations_from_dataframe(
    frame: pd.DataFrame,
    *,
    dataset_id: str | None,
    entity_type: str,
    variable_columns: Sequence[str],
    unit_map: Mapping[str, str] | None = None,
    date_column: str | None = None,
    entity_id_column: str | None = None,
    field_id_column: str | None = None,
    trial_id_column: str | None = None,
    experimental_unit_column: str | None = None,
    evidence_type: str = "Measured",
    source: str | None = None,
) -> list[dict[str, Any]]:
    """Convert a wide dataframe into explicit long-form canonical observations.

    No values are imputed. Missing values are skipped, preserving the distinction
    between a missing measurement and a measured zero.
    """
    if evidence_type not in EVIDENCE_TYPES:
        raise ResearchRegistryError(f"Unsupported evidence type: {evidence_type}")
    units = dict(unit_map or {})
    rows: list[dict[str, Any]] = []
    for _, record in frame.iterrows():
        observed_at = None
        if date_column and date_column in frame.columns and pd.notna(record.get(date_column)):
            observed_at = pd.to_datetime(record.get(date_column), errors="coerce")
            observed_at = observed_at.isoformat() if pd.notna(observed_at) else None
        for variable in variable_columns:
            if variable not in frame.columns or pd.isna(record.get(variable)):
                continue
            value = record.get(variable)
            numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
            rows.append({
                "dataset_id": dataset_id,
                "entity_type": entity_type,
                "entity_id": record.get(entity_id_column) if entity_id_column else None,
                "field_id": record.get(field_id_column) if field_id_column else None,
                "trial_id": record.get(trial_id_column) if trial_id_column else None,
                "experimental_unit_id": record.get(experimental_unit_column) if experimental_unit_column else None,
                "observed_at": observed_at,
                "variable": variable,
                "value_numeric": None if pd.isna(numeric) else float(numeric),
                "value_text": None if pd.notna(numeric) else str(value),
                "unit": units.get(variable),
                "evidence_type": evidence_type,
                "source": source,
                "provenance": {"source_column": variable},
            })
    return rows
