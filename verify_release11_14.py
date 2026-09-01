from __future__ import annotations

import ast
import hashlib
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent

UNCHANGED_BASELINE = {
    "field_operations/field_operations.sqlite": "fbf5ab2de711830a50bed5acfae84a86ec58efc45448d18ea7b88e04b4ff69b5",
    "pollination_lab/maize_flowering_trials.sqlite": "87511c0a9921e731f8bd8b3111118e452b9aa6d6ee32905fee3b7af73a258819",
    "agrolattice_twin/agrolattice_twin.sqlite": "ea5746651e6fb6c3de409ec8cf64d6e68409b40c0a7853f33982b2fb3f006bb4",
    "models_evidence/crop_profiles.sqlite": "84da237e7a8f20b3c84da7c9c423d0aa5a2dab130608c1eebfc2b06885c9e3a6",
    "maize_mechanistic_twin.py": "a62679f3aef1db8dfa4b459db8701cbf8502e7955b88daa520135b905e9400e8",
}
PRE_11_14_RESEARCH_SHA = "516b3361c1bca07b76da4f033dcd4ec693324d41d1924120fded88353600f58b"
EXPECTED_MIGRATED_RESEARCH_SHA = "7e80e599285753c026ff47e86127ad3df42b4cfdb7ff662fb6cd1011b1052a25"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def const_from_source(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"{name} not found in {path.name}")


def db_health(path: Path):
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0].lower() == "ok", path
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == [], path


def compare_predecessor_projection(old: Path, new: Path):
    """Verify that every predecessor table/column/row is retained exactly.

    Only metadata.schema_version may differ. New additive tables/columns are ignored.
    """
    with sqlite3.connect(old) as a, sqlite3.connect(new) as b:
        old_tables = [r[0] for r in a.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        new_tables = {r[0] for r in b.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        for table in old_tables:
            assert table in new_tables, f"Legacy table missing after migration: {table}"
            columns = [r[1] for r in a.execute(f'PRAGMA table_info("{table}")')]
            quoted = ", ".join('"' + c.replace('"', '""') + '"' for c in columns)
            old_rows = a.execute(f'SELECT {quoted} FROM "{table}"').fetchall()
            new_rows = b.execute(f'SELECT {quoted} FROM "{table}"').fetchall()
            if table == "metadata":
                old_rows = [r for r in old_rows if not r or str(r[0]) != "schema_version"]
                new_rows = [r for r in new_rows if not r or str(r[0]) != "schema_version"]
            assert old_rows == new_rows, f"Legacy rows changed in {table}"


def functional_registry_regression() -> None:
    from research_registry import ResearchEvidenceRegistry, ResearchRegistryError, sha256_file
    from agricultural_validation import build_protocol_folds

    with tempfile.TemporaryDirectory(prefix="agrolattice_11_14_verify_") as td:
        root = Path(td)
        registry = ResearchEvidenceRegistry(root / "research.sqlite")
        assert registry.integrity_check()["schema_version"] == "2.0.0"

        dataset_id = registry.register_dataset({
            "name": "Verification field trial",
            "dataset_type": "Experimental-unit table",
            "source": "11.14 verifier",
            "crop_scope": "Maize",
            "geography_scope": "Synthetic temporary test only",
            "provenance": {"purpose": "release verification"},
        })
        snapshot_id = registry.save_dataset_snapshot({
            "dataset_id": dataset_id,
            "name": "Frozen verification snapshot",
            "row_count": 6,
            "entity_count": 3,
            "manifest": {"columns": ["Group", "x", "y"]},
        })

        artifact = root / "model.bin"
        artifact.write_bytes(b"AGROLATTICE 11.14 verifier artifact")
        model_id = registry.register_model({
            "name": "Verification regression model",
            "family": "Linear test",
            "target": "Yield",
            "task_type": "regression",
            "status": "Prototype",
            "training_dataset_id": dataset_id,
            "feature_names": ["x"],
            "training_scope": {"crop": "Maize"},
            "preprocessing": {"fit_inside_fold": True},
            "validation_protocol": {"planned": "Grouped CV"},
            "metrics": {},
            "calibration": {},
            "uncertainty_method": None,
            "applicability": {},
            "limitations": [],
            "artifact_path": str(artifact),
            "dependency_versions": {"python": sys.version.split()[0]},
            "code_version": "AGROLATTICE 11.14",
        })

        # Upsert attempts cannot silently promote evidence status.
        registry.register_model({
            "model_id": model_id, "name": "Verification regression model", "family": "Linear test", "target": "Yield",
            "task_type": "regression", "status": "Operationally eligible", "training_dataset_id": dataset_id,
            "feature_names": ["x"], "training_scope": {}, "preprocessing": {}, "validation_protocol": {}, "metrics": {},
            "calibration": {}, "applicability": {}, "limitations": [], "dependency_versions": {},
        })
        assert registry.model(model_id)["status"] == "Prototype"

        failed_run = registry.save_training_run({
            "model_id": model_id, "dataset_id": dataset_id, "status": "Failed",
            "settings": {"candidate": "deliberately failed verifier candidate"},
            "split_summary": {"protocol": "Grouped CV"},
            "leakage_guards": {"preprocessing_inside_fold": True},
            "metrics": {}, "notes": "Failure persistence regression",
        })
        completed_run = registry.save_training_run({
            "model_id": model_id, "dataset_id": dataset_id, "status": "Completed",
            "settings": {"candidate": "verification model", "seed": 42},
            "split_summary": {"protocol": "Grouped CV", "folds": 3},
            "leakage_guards": {"preprocessing_inside_fold": True, "group_isolation": True},
            "metrics": {"RMSE": 1.2},
        })
        runs = registry.training_runs(model_id=model_id)
        assert {"Failed", "Completed"}.issubset(set(runs["status"].astype(str)))
        assert failed_run and completed_run

        validation_id = registry.save_validation_run({
            "model_id": model_id,
            "dataset_id": dataset_id,
            "validation_type": "Grouped CV",
            "evidence_level": "Internal CV",
            "primary_metric": "RMSE",
            "metrics": {"RMSE": 1.2, "MAE": 0.9},
            "fold_metrics": [{"fold": 1, "RMSE": 1.1}, {"fold": 2, "RMSE": 1.3}],
            "predictions": [{"Row": 0, "Observed": 8.0, "Predicted": 7.8}],
            "split_manifest": {"group_column": "Field"},
            "calibration": {},
            "uncertainty": {},
            "applicability": {},
            "leakage_guards": {"group_isolation": True},
            "status": "Completed",
        })
        assert validation_id

        # Evidence gating: internal promotion succeeds; external promotion remains blocked.
        registry.change_model_status(model_id, "Internally validated", rationale="Verifier internal evidence exists.")
        try:
            registry.change_model_status(model_id, "Externally validated", rationale="Should be blocked in verifier.")
        except ResearchRegistryError:
            pass
        else:
            raise AssertionError("External promotion was not blocked without independent/cross-site/cross-season evidence")

        version_id = registry.register_model_version({
            "model_id": model_id,
            "dataset_snapshot_id": snapshot_id,
            "artifact_path": str(artifact),
            "environment": {"python": sys.version.split()[0], "agrolattice": "11.14"},
            "feature_contract": {"x": {"dtype": "numeric", "unit": "unitless", "missing": "not allowed"}},
            "notes": "Immutable verifier model version",
        })
        latest = registry.latest_model_version(model_id)
        assert latest and latest["version_id"] == version_id
        assert latest["artifact_sha256"] == sha256_file(artifact)

        prediction_id = registry.save_prediction({
            "model_id": model_id, "entity_type": "Field", "entity_id": "F1", "field_id": "F1",
            "season_year": 2026, "target": "Yield", "prediction": 7.8,
            "lower_bound": 7.0, "upper_bound": 8.6, "uncertainty_method": "Verification interval",
            "applicability_status": "Within training support", "applicability_score": 1.0,
            "input_snapshot": {"version_id": version_id}, "provenance": {"verification": True},
        })
        observation_id = "obs-verify-1"
        assert registry.add_observations([{
            "observation_id": observation_id, "dataset_id": dataset_id, "entity_type": "Field", "entity_id": "F1",
            "field_id": "F1", "observed_at": "2026-08-01", "variable": "Yield", "value_numeric": 8.1,
            "unit": "t/ha", "evidence_type": "Measured", "source": "Verification measurement",
            "provenance": {"verification": True},
        }]) == 1
        match_id = registry.save_prediction_outcome_link({
            "prediction_id": prediction_id, "observation_id": observation_id, "observed_value": 8.1,
            "unit": "t/ha", "matching_basis": "Exact field-season-target verifier match",
            "provenance": {"researcher_review_required": True},
        })
        assert match_id and len(registry.prediction_outcome_links(model_id=model_id)) == 1

        health_id = registry.save_model_health_event({
            "model_id": model_id, "health_status": "Monitoring", "metric_name": "RMSE", "metric_value": 1.2,
            "threshold": 2.0, "evidence": {"validation_id": validation_id}, "note": "Verifier health event",
        })
        assert health_id and len(registry.model_health_events(model_id)) == 1
        assert len(registry.model_status_history(model_id)) == 1
        assert registry.integrity_check()["foreign_key_issues"] == []

        # Validation protocol regression, including the new frozen deployment-like holdout.
        frame = pd.DataFrame({"Group": ["A", "A", "B", "B", "C", "C"], "x": [1,2,3,4,5,6], "y": [2,3,4,5,6,7]})
        folds = build_protocol_folds(frame, protocol="Frozen group holdout", target_column="y", group_column="Group", holdout_value="C")
        assert len(folds) == 1
        assert set(frame.iloc[folds[0].test_index]["Group"]) == {"C"}
        assert "C" not in set(frame.iloc[folds[0].train_index]["Group"])
        repeated = build_protocol_folds(frame, protocol="Repeated grouped holdout", target_column="y", group_column="Group", n_splits=3, random_state=42, test_fraction=0.34)
        assert len(repeated) == 3
        for fold in repeated:
            train_groups=set(frame.iloc[fold.train_index]["Group"]); test_groups=set(frame.iloc[fold.test_index]["Group"])
            assert not (train_groups & test_groups)


def main() -> int:
    required = [
        "model_evidence_command_centre.py", "research_registry.py", "research_evidence_ui.py",
        "research_models.py", "agricultural_validation.py", "agrolattice.py",
        "README_START_HERE_RELEASE11_14.txt", "USER_GUIDE_RELEASE_11_14.txt",
        "CHANGELOG_RELEASE_11_14.txt", "TECHNICAL_BASIS_MODELS_EVIDENCE_11_14.md",
        "RELEASE_MANIFEST_11_14.json", "RESEARCH_METHODS_MANIFEST_11_14.json",
        "RUN_APP.bat", "safe_data_migration.py",
    ]
    for item in required:
        assert (ROOT / item).exists(), item

    # Release/module version checks.
    assert const_from_source(ROOT / "agrolattice.py", "APP_VERSION") == "20.14-release11.14-model-evidence-command-centre"
    assert const_from_source(ROOT / "model_evidence_command_centre.py", "MODULE_VERSION") == "1.0.0"
    assert const_from_source(ROOT / "research_registry.py", "MODULE_VERSION") == "2.0.0"
    assert const_from_source(ROOT / "research_registry.py", "DB_SCHEMA_VERSION") == "2.0.0"
    assert const_from_source(ROOT / "research_evidence_ui.py", "MODULE_VERSION") == "3.0.0"
    assert const_from_source(ROOT / "research_models.py", "MODULE_VERSION") == "1.1.0"
    assert const_from_source(ROOT / "agricultural_validation.py", "MODULE_VERSION") == "1.1.0"
    assert const_from_source(ROOT / "experiment_command_centre.py", "MODULE_VERSION") == "1.0.0"
    assert const_from_source(ROOT / "maize_pollination_lab.py", "MODULE_VERSION") == "3.0.0"
    assert const_from_source(ROOT / "maize_pollination_lab.py", "DB_SCHEMA_VERSION") == "3.0.0"

    command = (ROOT / "model_evidence_command_centre.py").read_text(encoding="utf-8")
    registry_ui = (ROOT / "research_evidence_ui.py").read_text(encoding="utf-8")
    registry_src = (ROOT / "research_registry.py").read_text(encoding="utf-8")
    models_src = (ROOT / "research_models.py").read_text(encoding="utf-8")
    validation_src = (ROOT / "agricultural_validation.py").read_text(encoding="utf-8")
    app = (ROOT / "agrolattice.py").read_text(encoding="utf-8")

    # Lazy command-centre architecture and major scientific workflows.
    assert "st.tabs(" not in command, "Models & Evidence Command Centre must use true lazy top-level navigation"
    for token in [
        "Priority evidence gaps", "Models", "Training", "Validation", "Uncertainty & calibration",
        "Explainability", "Comparison & ensembles", "Benchmarks & transferability", "Evidence & reproducibility",
        "Evidence graph", "Reproducibility package", "Status & health", "Datasets & snapshots",
    ]:
        assert token in command, token
    for token in [
        "model_versions", "model_status_history", "validation_runs", "dataset_snapshots",
        "prediction_outcome_links", "model_health_events", "promotion_requirements", "change_model_status",
    ]:
        assert token in registry_src, token
    for token in [
        "Primary metric declared before comparison", "save_training_run", "save_validation_run", "register_model_version",
        "Leave-one-parent-pair-out", "Spatial block holdout", "Frozen group holdout",
    ]:
        assert token in registry_ui, token
    for token in ["failures", "fold_metrics_by_model", "holdout_value"]:
        assert token in models_src, token
    for token in ["frozen_group_holdout_folds", "repeated_group_holdout_folds", "leave-one-parent-pair-out", "spatial group holdout", "PR AUC", "Log loss"]:
        assert token in validation_src, token
    assert "render_model_evidence_command_centre" in app and "page_release10_models_evidence" in app

    # Retain Release 11.13's requested k<=20 PCA/K-means exploration.
    assert "max_value=20" in app and "maximum_k = min(20, n_samples - 1, unique_profile_count)" in app
    assert 'st.slider("Colour by K-means clusters", 2, 20, 5' in app

    # Research Evidence 1.3 -> 2.0 additive migration with exact predecessor copy.
    research = ROOT / "models_evidence/research_evidence.sqlite"
    predecessor = ROOT / "models_evidence/backups/pre_11_14_research_evidence.sqlite"
    assert research.exists() and predecessor.exists()
    assert sha(predecessor) == PRE_11_14_RESEARCH_SHA
    assert sha(research) == EXPECTED_MIGRATED_RESEARCH_SHA, "Packaged Research Evidence DB differs from verified clean migration"
    db_health(research); db_health(predecessor)
    with sqlite3.connect(research) as conn:
        schema = conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0]
        assert schema == "2.0.0"
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        new_tables = ["dataset_snapshots", "model_versions", "model_status_history", "validation_runs", "prediction_outcome_links", "model_health_events"]
        for table in new_tables:
            assert table in tables
            assert conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] == 0, f"Synthetic records packaged in {table}"
    compare_predecessor_projection(predecessor, research)

    # All other protected research/field databases and mechanistic maize source are unchanged from 11.13.
    for relative, expected in UNCHANGED_BASELINE.items():
        path = ROOT / relative
        assert path.exists(), relative
        assert sha(path) == expected, f"Protected artifact changed unexpectedly: {relative}"
        if path.suffix == ".sqlite":
            db_health(path)

    # Runtime/migration/version integration.
    migration = (ROOT / "safe_data_migration.py").read_text(encoding="utf-8")
    assert 'RELEASE = "AGROLATTICE 11.14"' in migration
    run = (ROOT / "RUN_APP.bat").read_text(encoding="utf-8")
    for token in [
        "AGROLATTICE 11.14", "model_evidence_command_centre.py", "model_evidence_command_centre",
        "research_registry.MODULE_VERSION == '2.0.0'", "research_registry.DB_SCHEMA_VERSION == '2.0.0'",
        "research_evidence_ui.MODULE_VERSION == '3.0.0'", "research_models.MODULE_VERSION == '1.1.0'",
        "agricultural_validation.MODULE_VERSION == '1.1.0'",
    ]:
        assert token in run, token

    manifest = json.loads((ROOT / "RELEASE_MANIFEST_11_14.json").read_text(encoding="utf-8"))
    assert manifest["release"] == "AGROLATTICE 11.14"
    assert manifest["application_version"] == "20.14-release11.14-model-evidence-command-centre"
    assert manifest["database_schema_changes"] is True
    assert manifest["research_evidence_schema"] == "2.0.0"
    assert manifest["mechanistic_maize_model_changed"] is False
    assert manifest["new_dependencies"] == []

    functional_registry_regression()

    print("AGROLATTICE 11.14 verification passed")
    print("- Lazy Model & Evidence Command Centre architecture detected")
    print("- Persistent successful/failed training runs, immutable model versions and evidence-gated status history tested")
    print("- Registry-aware validation, prediction-outcome linkage, model health and frozen holdout tested")
    print("- Research Evidence DB additive 1.3.0 -> 2.0.0 migration preserves all predecessor rows")
    print("- Field Ops, Pollination, Persistent Twin, Crop Profile DBs and mechanistic maize source match 11.13 hashes")
    print("- k=2..20 climate/PCA exploration remains available")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
