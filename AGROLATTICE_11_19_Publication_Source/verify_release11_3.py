"""Regression verification for AGROLATTICE 11.3 Research Foundation.

The tests deliberately focus on release invariants: additive evidence storage,
leakage-safe validation, source-paper pest feature equations, model
applicability, multimodal missingness, unchanged mechanistic maize constants,
and source-authoritative user-data migration.
"""
from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

import agricultural_validation
import ast
import maize_mechanistic_twin
from agricultural_validation import applicability_profile, applicability_score, leave_one_year_out_folds
from multimodal_fusion import fit_fusion, predict_fusion
from pest_early_warning import engineer_environmental_pest_features, make_classifier_pipeline
from research_registry import DB_SCHEMA_VERSION, EVIDENCE_TYPES, ResearchEvidenceRegistry, ResearchRegistryError
from safe_data_migration import migrate


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify_registry_roundtrip() -> None:
    with tempfile.TemporaryDirectory(prefix="agrolattice11_3-registry-") as temporary:
        registry = ResearchEvidenceRegistry(Path(temporary) / "models_evidence" / "research_evidence.sqlite")
        require(DB_SCHEMA_VERSION == "1.1.0", "Unexpected Research Evidence DB schema version.")
        dataset_id = registry.register_dataset({
            "name": "Verification dataset", "dataset_type": "field trial", "source": "synthetic verification",
            "crop_scope": "maize", "geography_scope": "test", "provenance": {"purpose": "release verification"},
        })
        added = registry.add_observations([{
            "dataset_id": dataset_id, "entity_type": "field", "entity_id": "FIELD-TEST", "field_id": "FIELD-TEST",
            "observed_at": "2027-06-01", "variable": "yield", "value_numeric": 8.2, "unit": "t/ha",
            "evidence_type": "Measured", "spatial_support": "field polygon", "source": "verification",
            "provenance": {"synthetic": True},
        }])
        require(added == 1, "Observation was not registered.")
        model_id = registry.register_model({
            "name": "Verification baseline", "family": "Random forest", "target": "yield", "task_type": "regression",
            "status": "Prototype", "implementation_type": "Independent AGROLATTICE baseline",
            "training_dataset_id": dataset_id, "training_scope": {"years": [2025, 2026]},
            "required_modalities": ["weather"], "feature_names": ["temperature"],
            "preprocessing": {"fit_scope": "training fold only"}, "validation_protocol": {"name": "LOYO"},
            "metrics": {"RMSE": 0.5}, "calibration": {}, "uncertainty_method": "OOF residual interval",
            "applicability": {"method": "robust marginal support"}, "limitations": ["Synthetic verification only"],
            "dependency_versions": {}, "code_version": "11.3",
        })
        prediction_id = registry.save_prediction({
            "model_id": model_id, "entity_type": "field", "entity_id": "FIELD-TEST", "field_id": "FIELD-TEST",
            "season_year": 2027, "target": "yield", "prediction": 8.0, "lower_bound": 7.2, "upper_bound": 8.8,
            "uncertainty_total": 0.8, "uncertainty_method": "OOF residual interval",
            "applicability_status": "Within support", "applicability_score": 82.0,
            "input_snapshot": {"synthetic": True}, "provenance": {"verification": True},
        })
        classifier_id = registry.register_model({
            "name": "Verification classifier", "family": "Logistic regression", "target": "pest", "task_type": "classification",
            "status": "Prototype", "implementation_type": "Independent AGROLATTICE baseline", "feature_names": ["temperature"],
            "training_scope": {}, "required_modalities": ["weather"], "preprocessing": {}, "validation_protocol": {"name": "LOYO"},
            "metrics": {"Macro F1": 0.8}, "calibration": {}, "applicability": {}, "limitations": ["Synthetic verification only"],
            "dependency_versions": {}, "code_version": "11.3",
        })
        registry.save_prediction({
            "model_id": classifier_id, "entity_type": "field", "entity_id": "FIELD-TEST", "field_id": "FIELD-TEST",
            "season_year": 2027, "target": "pest", "prediction_text": "No Pest",
            "class_probabilities": {"No Pest": 0.8, "Green Leafhopper": 0.2},
            "uncertainty_method": "Class probabilities; calibration must be checked",
            "applicability_status": "Within support", "applicability_score": 85.0,
            "input_snapshot": {"temperature": 24.0}, "provenance": {"verification": True},
        })

        recommendation_id = registry.save_recommendation({
            "model_id": model_id, "prediction_id": prediction_id, "field_id": "FIELD-TEST",
            "action_type": "measurement", "action_text": "Collect an independent yield observation before model promotion.",
            "objective": "validation", "constraints": {"human_review": True}, "status": "Proposed",
            "provenance": {"verification": True},
        })
        registry.save_treatment_outcome({
            "recommendation_id": recommendation_id, "field_id": "FIELD-TEST", "recommendation_followed": True,
            "actual_action_text": "Verification measurement", "outcome_variable": "yield", "outcome_value": 8.1,
            "outcome_unit": "t/ha", "measured_at": "2027-10-01", "covariates": {}, "provenance": {"verification": True},
        })
        registry.save_benchmark_run({
            "benchmark_name": "Verification benchmark", "model_id": model_id, "dataset_id": dataset_id,
            "protocol": "LOYO", "settings": {}, "metrics": {"RMSE": 0.5}, "applicability": {},
        })
        summary = registry.summary()
        require(summary.datasets == 1 and summary.observations == 1 and summary.models == 2, "Registry core counts are wrong.")
        require(summary.predictions == 2 and summary.recommendations == 1 and summary.treatment_outcomes == 1, "Evidence roundtrip failed.")
        integrity = registry.integrity_check()
        require(integrity["integrity_check"] == "ok" and not integrity["foreign_key_issues"], "Research registry integrity failed.")
        card = registry.export_model_card(model_id)
        require(card["status"] == "Prototype" and card["predictions_recorded"] == 1, "Model-card export is incomplete.")
        class_rows = registry.predictions(model_id=classifier_id)
        require(class_rows.iloc[0]["prediction_text"] == "No Pest", "Classification prediction text was not stored.")
        require("No Pest" in class_rows.iloc[0]["class_probabilities_json"], "Classification probability provenance was not stored.")
        try:
            registry.add_observations([{"entity_type": "field", "variable": "x", "evidence_type": "Invented"}])
        except ResearchRegistryError:
            pass
        else:
            raise AssertionError("Registry accepted an unsupported evidence type.")
        require("Measured" in EVIDENCE_TYPES and "Model output" in EVIDENCE_TYPES, "Scientific evidence vocabulary changed unexpectedly.")


def verify_loyo_and_applicability() -> None:
    years = pd.Series([2021] * 4 + [2022] * 4 + [2023] * 4)
    folds = leave_one_year_out_folds(years)
    require(len(folds) == 3, "LOYO did not create one fold per year.")
    for fold in folds:
        train_years = set(years.iloc[fold.train_index].tolist())
        test_years = set(years.iloc[fold.test_index].tolist())
        require(train_years.isdisjoint(test_years), "LOYO leaked a held-out year into training.")

    train = pd.DataFrame({"temperature": [20, 21, 22, 23, 24], "rainfall": [1, 2, 3, 4, 5]})
    profile = applicability_profile(train, ["temperature", "rainfall"])
    scores = applicability_score(pd.DataFrame({"temperature": [22, 100], "rainfall": [3, 200]}), profile)
    require(scores.iloc[0]["Applicability status"] != "Outside training range", "In-range case was incorrectly flagged outside support.")
    require(scores.iloc[1]["Applicability status"] == "Outside training range", "Out-of-range case was not flagged.")
    guards = agricultural_validation.leakage_guard_manifest("LOYO", resampling="SMOTE-ENN")
    require(guards["preprocessing_fit_scope"] == "Training fold only", "Preprocessing leakage guard is missing.")
    require(guards["class_resampling_fit_scope"] == "Training fold only", "Resampling leakage guard is missing.")


def verify_pest_feature_engineering_and_pipeline() -> None:
    source = pd.DataFrame({
        "MaxT": [30.0], "MinT": [20.0], "RH1(%)": [80.0], "RH2(%)": [60.0],
        "RF(mm)": [5.0], "WS(kmph)": [4.0], "SSH(hrs)": [7.0], "EVP(mm)": [3.0],
    })
    engineered, metadata = engineer_environmental_pest_features(source)
    require(abs(float(engineered.loc[0, "Temp_Diff"]) - 10.0) < 1e-12, "Temperature-difference equation changed.")
    require(abs(float(engineered.loc[0, "Hum_Diff"]) - 20.0) < 1e-12, "Humidity-difference equation changed.")
    require(abs(float(engineered.loc[0, "Avg_Hum"]) - 70.0) < 1e-12, "Average-humidity equation changed.")
    mean_t = 25.0
    es = 0.6108 * np.exp((17.27 * mean_t) / (mean_t + 237.3))
    expected_vpd = es - 0.70 * es
    require(abs(float(engineered.loc[0, "VPD"]) - expected_vpd) < 1e-10, "VPD Magnus calculation changed.")
    require("10.1016/j.compag.2024.109472" in metadata["source_doi"], "Pest source provenance is missing.")
    try:
        pipeline = make_classifier_pipeline("Random forest", resampling="SMOTE-ENN")
        require("resample" in pipeline.named_steps, "SMOTE-ENN is not inside the training pipeline.")
        require(list(pipeline.named_steps).index("resample") < list(pipeline.named_steps).index("model"), "SMOTE-ENN is not upstream of model fit.")
    except Exception as error:
        # imbalanced-learn is a declared Release 11.3 dependency; fail with a clear build message.
        raise AssertionError(f"SMOTE-ENN pipeline could not be constructed: {error}") from error


def verify_multimodal_fusion_missingness() -> None:
    rng = np.random.default_rng(11)
    n = 36
    frame = pd.DataFrame({
        "weather_temp": rng.normal(25, 2, n), "weather_rain": rng.normal(4, 1, n),
        "eo_ndvi": rng.normal(0.65, 0.08, n), "eo_evi": rng.normal(0.42, 0.06, n),
        "year": np.repeat([2021, 2022, 2023], 12),
    })
    frame["yield"] = 0.12 * frame["weather_temp"] + 3.0 * frame["eo_ndvi"] + rng.normal(0, 0.15, n)
    fitted = fit_fusion(
        frame, target_column="yield",
        feature_groups={"weather": ["weather_temp", "weather_rain"], "EO": ["eo_ndvi", "eo_evi"]},
        protocol="LOYO", year_column="year", base_model="Random forest", n_splits=3,
    )
    require(abs(sum(fitted.weights.values()) - 1.0) < 1e-8, "Fusion validation weights do not sum to one.")
    new = frame.iloc[:2].copy()
    new.loc[new.index[1], ["eo_ndvi", "eo_evi"]] = np.nan
    predicted = predict_fusion(fitted, new)
    require(np.isfinite(predicted.iloc[0]["Fused prediction"]), "Fusion failed with all modalities available.")
    require(int(predicted.iloc[1]["Modalities available"]) == 1, "Missing modality was not detected.")
    require(np.isfinite(predicted.iloc[1]["Fused prediction"]), "Fusion did not renormalise over the remaining modality.")


def verify_mechanistic_maize_unchanged() -> None:
    require(maize_mechanistic_twin.EMERGENCE_GDD == 30.6, "Mechanistic maize emergence GDD changed.")
    require(maize_mechanistic_twin.EAR_GROWTH_LEAF_FRACTION == 0.67, "Mechanistic maize ear-growth fraction changed.")
    require(maize_mechanistic_twin.ANTHESIS_AFTER_FINAL_LEAF_GDD == 40.0, "Mechanistic maize anthesis offset changed.")
    priors = maize_mechanistic_twin.DEFAULT_PHYSIOLOGY.to_record()
    require(abs(float(priors["tln"]) - 19.0) < 1e-12, "Default tln prior centre changed.")
    require(abs(float(priors["coblf"]) - 0.0019) < 1e-12, "Default coblf prior centre changed.")
    require(abs(float(priors["eb_r1_g"]) - 2.0) < 1e-12, "Default ebR1 prior centre changed.")
    root = Path(__file__).resolve().parent
    def literal_constant(filename: str, name: str):
        tree = ast.parse((root / filename).read_text(encoding="utf-8"), filename=filename)
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == name:
                        return ast.literal_eval(node.value)
        raise AssertionError(f"Could not find {name} in {filename}.")
    require(literal_constant("maize_pollination_lab.py", "DB_SCHEMA_VERSION") == "2.0.0", "Pollination DB schema changed unexpectedly.")
    require(literal_constant("agrolattice_twin.py", "DB_SCHEMA_VERSION") == "2.3.0", "Twin DB schema changed unexpectedly.")
    require(literal_constant("field_operations_suite.py", "MODULE_VERSION") == "7.1.0", "Field Operations module version changed unexpectedly.")


def make_simple_db(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE records(id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        connection.execute("INSERT INTO records(value) VALUES(?)", (value,))
        connection.commit()


def read_value(path: Path) -> str:
    with sqlite3.connect(path) as connection:
        return str(connection.execute("SELECT value FROM records ORDER BY id LIMIT 1").fetchone()[0])


def verify_source_authoritative_migration() -> None:
    relatives = (
        Path("field_operations/field_operations.sqlite"),
        Path("pollination_lab/maize_flowering_trials.sqlite"),
        Path("agrolattice_twin/agrolattice_twin.sqlite"),
        Path("models_evidence/research_evidence.sqlite"),
    )
    with tempfile.TemporaryDirectory(prefix="agrolattice11_3-migrate-") as temporary:
        root = Path(temporary); source = root / "source"; destination = root / "destination"
        for relative in relatives:
            make_simple_db(source / relative, "LIVE-SOURCE")
            make_simple_db(destination / relative, "PACKAGED-DESTINATION")
        (source / "models_evidence" / "model_artifact.bin").write_bytes(b"source-artifact")
        backup = migrate(source, destination)
        for relative in relatives:
            require(read_value(destination / relative) == "LIVE-SOURCE", f"Source DB did not replace destination: {relative}")
            require(read_value(backup / "destination_before" / relative) == "PACKAGED-DESTINATION", f"Destination backup missing: {relative}")
            require(read_value(backup / "source_snapshot" / relative) == "LIVE-SOURCE", f"Source snapshot missing: {relative}")
        require((destination / "models_evidence" / "model_artifact.bin").read_bytes() == b"source-artifact", "Research model artifact was not migrated.")
        report = json.loads((backup / "migration_report.json").read_text(encoding="utf-8"))
        require(len(report["research_databases"]) == 4, "Research Evidence DB was not included in migration report.")

    # A Release 11.2 source has no Research Evidence DB; migration must still work.
    with tempfile.TemporaryDirectory(prefix="agrolattice11_3-migrate-legacy-") as temporary:
        root = Path(temporary); source = root / "source"; destination = root / "destination"
        for relative in relatives[:3]:
            make_simple_db(source / relative, "LEGACY-11.2")
            make_simple_db(destination / relative, "PACKAGED")
        make_simple_db(destination / relatives[3], "NEW-11.3")
        migrate(source, destination)
        for relative in relatives[:3]:
            require(read_value(destination / relative) == "LEGACY-11.2", f"Legacy source DB was not migrated: {relative}")
        require(read_value(destination / relatives[3]) == "NEW-11.3", "11.3 Research Evidence DB was overwritten by a legacy source that did not contain it.")


def verify_release_files() -> None:
    root = Path(__file__).resolve().parent
    for filename in (
        "RELEASE_MANIFEST_11_3.json", "CHANGELOG_RELEASE_11_3.txt", "README_START_HERE_RELEASE11_3.txt",
        "USER_GUIDE_RELEASE_11_3.txt", "SCIENTIFIC_BASIS_RESEARCH_FOUNDATION_11_3.md",
        "RESEARCH_METHODS_MANIFEST_11_3.json", "research_registry.py", "agricultural_validation.py",
        "research_models.py", "pest_early_warning.py", "phenology_service.py", "research_benchmarks.py",
        "multimodal_fusion.py", "research_evidence_ui.py",
    ):
        require((root / filename).exists(), f"Required Release 11.3 file is missing: {filename}")


def main() -> None:
    verify_registry_roundtrip()
    verify_loyo_and_applicability()
    verify_pest_feature_engineering_and_pipeline()
    verify_multimodal_fusion_missingness()
    verify_mechanistic_maize_unchanged()
    verify_source_authoritative_migration()
    verify_release_files()
    print("AGROLATTICE 11.3 Research Foundation verification passed")


if __name__ == "__main__":
    main()
