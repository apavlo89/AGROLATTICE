"""Regression verification for AGROLATTICE 11.4 Multimodal/Hybrid release.

The suite exercises the new non-UI research/data paths while preserving the
scientific and data-integrity invariants inherited from 11.3/11.2.
"""
from __future__ import annotations

import ast
import json
import sqlite3
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

import maize_mechanistic_twin
from agricultural_validation import applicability_profile, applicability_score, leave_one_year_out_folds
from gxem_data_builder import build_maize_gxem_table
from hybrid_residual import fit_hybrid_residual, predict_hybrid
from multimodal_fusion import fit_fusion, predict_fusion
from pest_early_warning import engineer_environmental_pest_features, make_classifier_pipeline
from phenology_service import generic_gdd_stage_estimate, mechanistic_maize_estimate
from research_data_hub import (
    TWIN_CANONICAL_WEATHER_VARIABLES,
    _canonicalise_weather,
    aggregate_daily_weather,
    installed_monthly_climate,
    merge_weather_with_labels,
    nasa_pest_covariates,
)
from research_registry import DB_SCHEMA_VERSION, ResearchEvidenceRegistry
from safe_data_migration import migrate
from weak_supervised_yield import fit_weak_yield_model, predict_fine_resolution


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def synthetic_nasa(n: int = 160) -> pd.DataFrame:
    rng = np.random.default_rng(114)
    return pd.DataFrame({
        "DATE": pd.date_range("2025-04-01", periods=n, freq="D"),
        "T2M": 24 + rng.normal(0, 1.5, n),
        "T2M_MAX": 31 + rng.normal(0, 1.5, n),
        "T2M_MIN": 17 + rng.normal(0, 1.5, n),
        "RH2M": 62 + rng.normal(0, 5, n),
        "PRECTOTCORR": rng.gamma(1.0, 2.0, n),
        "WS2M": 2 + rng.random(n),
        "ALLSKY_SFC_SW_DWN": 19 + rng.normal(0, 1, n),
        "ALLSKY_SFC_LW_DWN": 30 + rng.normal(0, 1, n),
        "PS": 95 + rng.normal(0, .5, n),
        "ALLSKY_KT": .55 + rng.normal(0, .03, n),
        "TSOIL1": 24 + rng.normal(0, 1, n),
        "TSOIL2": 23 + rng.normal(0, 1, n),
    })


def verify_registry_and_acquisition() -> None:
    with tempfile.TemporaryDirectory(prefix="agrolattice11_4-registry-") as td:
        registry = ResearchEvidenceRegistry(Path(td) / "models_evidence" / "research_evidence.sqlite")
        require(DB_SCHEMA_VERSION == "1.2.0", "Unexpected Research Evidence schema.")
        dataset_id = registry.register_dataset({"name": "retrieved weather", "source": "NASA POWER", "provenance": {"verification": True}})
        acquisition_id = registry.save_data_acquisition({
            "dataset_id": dataset_id, "source": "NASA POWER", "source_type": "API",
            "field_id": "FIELD-A", "latitude": 19.4, "longitude": -99.1,
            "period_start": "2025-04-01", "period_end": "2025-05-01",
            "temporal_resolution": "daily", "variables": ["T2M", "RH2M"],
            "request": {"time_standard": "LST"}, "provenance": {"verification": True},
            "row_count": 31, "status": "Completed",
        })
        require(bool(acquisition_id), "Acquisition ID was not created.")
        require(registry.summary().data_acquisitions == 1, "Data acquisition was not persisted.")
        require(registry.integrity_check()["schema_version"] == "1.2.0", "Registry schema version was not persisted.")


def verify_11_3_to_11_4_registry_migration() -> None:
    with tempfile.TemporaryDirectory(prefix="agrolattice11_4-schema-") as td:
        path = Path(td) / "registry.sqlite"
        registry = ResearchEvidenceRegistry(path)
        dataset = registry.register_dataset({"name": "keep me", "provenance": {"sentinel": True}})
        # Emulate the immediately previous metadata version; tables/records remain.
        with sqlite3.connect(path) as conn:
            conn.execute("DROP TABLE data_acquisitions")
            conn.execute("UPDATE metadata SET value='1.1.0' WHERE key='schema_version'")
            conn.commit()
        migrated = ResearchEvidenceRegistry(path)
        require((migrated.datasets()["dataset_id"] == dataset).any(), "Existing registry record was lost during 1.1 -> 1.2 migration.")
        require(migrated.integrity_check()["schema_version"] == "1.2.0", "Registry did not migrate to 1.2.0.")
        require(migrated.data_acquisitions().empty, "Migration invented acquisition records.")


def verify_research_data_hub_and_phenology() -> None:
    canonical, provenance = _canonicalise_weather(synthetic_nasa(), 19.43)
    require(all(c in canonical.columns for c in TWIN_CANONICAL_WEATHER_VARIABLES), "The full 19-variable canonical weather profile was not created.")
    require(canonical["EVAPOTRANSPIRATION"].notna().any(), "FAO-56 ETo was not derived when drivers were present.")
    require(set(canonical["SOIL_HEAT_FLUX"].dropna().unique()) == {0.0}, "Daily FAO-56 G=0 assumption changed.")
    require("note" in provenance["SOIL_HEAT_FLUX"], "Soil-heat-flux assumption lost provenance.")
    weekly = aggregate_daily_weather(canonical, "Weekly")
    require(0 < len(weekly) < len(canonical), "Weather aggregation did not reduce temporal rows.")

    pest, meta = nasa_pest_covariates(canonical)
    require({"NASA_Tmax", "NASA_Tmin", "NASA_RHmean", "Temp_Diff", "Avg_Hum", "VPD"}.issubset(pest.columns), "NASA pest covariates are incomplete.")
    require("RH1" not in pest.columns and "RH2" not in pest.columns, "NASA mean RH was incorrectly fabricated as morning/evening RH.")
    require("does not reproduce" in meta["compatibility_note"], "Pest source-compatibility warning is missing.")

    labels = pd.DataFrame({"observed_at": [canonical["DATE"].iloc[5], canonical["DATE"].iloc[20]], "pest": ["A", "B"]})
    joined = merge_weather_with_labels(labels, pest, label_date_column="observed_at", tolerance_days=1)
    require(joined["pest"].tolist() == ["A", "B"], "Measured scouting labels were not preserved during weather enrichment.")

    generic = generic_gdd_stage_estimate(canonical, "2025-04-01", {"Emergence": 100, "Flowering": 900}, base_temperature_c=10, upper_temperature_c=30)
    require(generic.accumulated_gdd is not None and generic.accumulated_gdd > 0, "Canonical NASA weather did not feed the GDD service.")
    maize, simulation, _ = mechanistic_maize_estimate(canonical, "2025-04-01", role="Female", uncertainty_draws=100)
    require(not simulation.empty and maize.source == "Mechanistic Maize Twin", "Canonical NASA weather did not feed mechanistic maize phenology.")

    installed = pd.DataFrame([
        {"CITY": "X", "STATE": "Y", "Year": y, "Month": m, "lat": 1.0, "lng": 2.0, "Variable": var, "Value": float(1 if m == "January" else 2)}
        for y in [2024, 2025] for m in ["January", "February"] for var in ["TEMPERATURE", "PRECIPITATION_AVG"]
    ])
    acquired = installed_monthly_climate(installed, city="X", state="Y", start_year=2024, end_year=2025)
    require({"TEMPERATURE", "PRECIPITATION_AVG", "DATE"}.issubset(acquired.frame.columns), "Installed country climate pivot failed.")


def verify_pest_paper_equations_and_fold_resampling() -> None:
    source = pd.DataFrame({"MaxT": [30.0], "MinT": [20.0], "RH1(%)": [80.0], "RH2(%)": [60.0], "RF(mm)": [5.0], "WS(kmph)": [4.0], "SSH(hrs)": [7.0], "EVP(mm)": [3.0]})
    engineered, _ = engineer_environmental_pest_features(source)
    require(abs(float(engineered.loc[0, "Temp_Diff"]) - 10.0) < 1e-12, "Wadhwa/Malik Temp_Diff changed.")
    require(abs(float(engineered.loc[0, "Hum_Diff"]) - 20.0) < 1e-12, "Wadhwa/Malik Hum_Diff changed.")
    pipeline = make_classifier_pipeline("Random forest", resampling="SMOTE-ENN")
    require("resample" in pipeline.named_steps and list(pipeline.named_steps).index("resample") < list(pipeline.named_steps).index("model"), "SMOTE-ENN is not inside the fitted training pipeline.")


def verify_adaptive_fusion() -> None:
    rng = np.random.default_rng(14); n = 90
    frame = pd.DataFrame({
        "w1": rng.normal(size=n), "w2": rng.normal(size=n), "eo1": rng.normal(size=n),
        "year": np.repeat([2022, 2023, 2024], 30),
    })
    frame["yield"] = 3 * frame["w1"] - frame["w2"] + .5 * frame["eo1"] + rng.normal(0, .2, n)
    fitted = fit_fusion(frame, target_column="yield", feature_groups={"weather": ["w1", "w2"], "EO": ["eo1"]}, protocol="LOYO", year_column="year", base_model="Random forest", n_splits=3, gating_mode="Adaptive reliability gating")
    predicted = predict_fusion(fitted, frame.iloc[:4].copy())
    weight_cols = ["weather fusion weight", "EO fusion weight"]
    require(np.allclose(predicted[weight_cols].sum(axis=1), 1.0), "Adaptive modality weights do not normalise by row.")
    missing = frame.iloc[:2].copy(); missing.loc[missing.index[1], "eo1"] = np.nan
    result = predict_fusion(fitted, missing)
    require(int(result.iloc[1]["Modalities available"]) == 1 and np.isfinite(result.iloc[1]["Fused prediction"]), "Missing-modality fallback failed.")


def verify_hybrid_residual() -> None:
    rng = np.random.default_rng(140); n = 120
    x1 = rng.normal(size=n); x2 = rng.normal(size=n); group = np.repeat(np.arange(12), 10)
    observed = 4 * x1 - 2 * x2 + rng.normal(0, .2, n)
    base = 2 * x1 - .5 * x2
    frame = pd.DataFrame({"x1": x1, "x2": x2, "group": group, "observed": observed, "mechanistic": base})
    fitted = fit_hybrid_residual(frame, observed_column="observed", base_prediction_column="mechanistic", feature_columns=["x1", "x2"], protocol="Grouped CV", group_column="group", residual_model_name="Random forest")
    require(fitted.accepted, "Synthetic residual correction that clearly improves held-out RMSE did not pass the promotion guard.")
    predicted = predict_hybrid(fitted, frame.iloc[:5])
    require("Hybrid corrected prediction" in predicted, "Hybrid corrected predictions were not produced.")


def verify_weak_supervision() -> None:
    rng = np.random.default_rng(1140); rows = []
    for group in range(16):
        for _ in range(6): rows.append((group, rng.normal(group / 10, 1), rng.normal()))
    frame = pd.DataFrame(rows, columns=["zone", "a", "b"])
    means = frame.groupby("zone")[["a", "b"]].mean()
    target = 3 * means["a"] - 1.5 * means["b"] + 5
    frame["aggregate_yield"] = frame["zone"].map(target)
    fitted = fit_weak_yield_model(frame, group_column="zone", aggregate_target_column="aggregate_yield", feature_columns=["a", "b"])
    fine, aggregated = predict_fine_resolution(fitted, frame)
    require("Weakly supervised fine-scale yield estimate" in fine, "Fine weak-supervision output is missing.")
    require(len(aggregated) == 16, "Fine estimates did not reaggregate by supervision group.")
    require("RMSE" in fitted.validation_table.attrs, "Leave-one-aggregate-group-out validation summary is missing.")


class FakePollinationDB:
    def list_trials(self):
        return pd.DataFrame([{"Trial ID": "T1", "Trial": "Synchrony", "Site": "Test", "Year": 2025, "Source field ID": "F1", "Status": "Active"}])
    def get_trial(self, _):
        return {"irrigation_method": "sensor", "irrigation_treatment": "A", "management_notes": "test", "base_temperature_c": 10, "upper_temperature_c": 30}
    def list_plots(self, _):
        return pd.DataFrame([{"Plot ID": "P1", "Plot": "1", "Female parent": "F", "Male parent": "M", "Block": "B1", "Replicate": 1, "Female sowing date": "2025-04-01", "Male sowing date": "2025-04-04", "Sowing density": 7.5}])
    def observations(self, _): return pd.DataFrame([{"Plot ID": "P1", "Plant height": 100.0}])
    def leaf_observations(self, _): return pd.DataFrame([{"Plot ID": "P1", "Leaf count": 13}])
    def phenology_events(self, _): return pd.DataFrame([{"Plot ID": "P1", "Male flowering date": "2025-06-20", "Female flowering date": "2025-06-21"}])
    def harvest(self, _): return pd.DataFrame([{"Plot ID": "P1", "Yield": 5.2, "Seed purity": 98.0}])
    def weather(self, _): return pd.DataFrame([{"Tmean (°C)": 23, "Tmax (°C)": 30, "Tmin (°C)": 16, "Rainfall (mm)": 4, "Solar radiation (MJ/m²/day)": 20, "Reference ET (mm)": 3.5, "GDD daily": 13}])


def verify_gxem_builder() -> None:
    frame, meta = build_maize_gxem_table(FakePollinationDB())
    require(len(frame) == 1, "G×E×M builder lost the experimental unit.")
    require({"Trial ID", "Source field ID", "Block", "Replicate", "Female parent", "Male parent", "Yield"}.issubset(frame.columns), "G×E×M identifiers/outcomes are incomplete.")
    require(meta["trials"] == 1 and meta["experimental_units"] == 1, "G×E×M metadata is inconsistent.")


def verify_loyo_and_applicability() -> None:
    years = pd.Series([2021] * 4 + [2022] * 4 + [2023] * 4)
    folds = leave_one_year_out_folds(years)
    require(len(folds) == 3, "LOYO split count changed.")
    for fold in folds:
        require(set(years.iloc[fold.train_index]).isdisjoint(set(years.iloc[fold.test_index])), "LOYO leaked a year.")
    profile = applicability_profile(pd.DataFrame({"x": [0, 1, 2, 3]}), ["x"])
    scored = applicability_score(pd.DataFrame({"x": [1, 100]}), profile)
    require(scored.iloc[1]["Applicability status"] == "Outside training range", "Out-of-support case was not flagged.")


def verify_mechanistic_and_protected_schema_invariants() -> None:
    require(maize_mechanistic_twin.EMERGENCE_GDD == 30.6, "Emergence GDD changed.")
    require(maize_mechanistic_twin.EAR_GROWTH_LEAF_FRACTION == 0.67, "Ear-growth fraction changed.")
    require(maize_mechanistic_twin.ANTHESIS_AFTER_FINAL_LEAF_GDD == 40.0, "Anthesis offset changed.")
    root = Path(__file__).resolve().parent
    def literal(filename: str, name: str):
        tree = ast.parse((root / filename).read_text(encoding="utf-8"), filename=filename)
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == name:
                        return ast.literal_eval(node.value)
        raise AssertionError(f"Could not find {name} in {filename}")
    require(literal("maize_pollination_lab.py", "DB_SCHEMA_VERSION") == "2.0.0", "Pollination DB schema changed.")
    require(literal("agrolattice_twin.py", "DB_SCHEMA_VERSION") == "2.3.0", "Twin DB schema changed.")
    require(literal("field_operations_suite.py", "MODULE_VERSION") == "7.1.0", "Field Operations module invariant changed.")
    require(literal("agrolattice.py", "APP_VERSION") == "20.4-release11.4-multimodal-hybrid", "Application version string is not 11.4.")


def make_simple_db(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE records(id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("INSERT INTO records(value) VALUES(?)", (value,)); conn.commit()


def read_value(path: Path) -> str:
    with sqlite3.connect(path) as conn: return str(conn.execute("SELECT value FROM records LIMIT 1").fetchone()[0])


def verify_source_authoritative_migration() -> None:
    relatives = (Path("field_operations/field_operations.sqlite"), Path("pollination_lab/maize_flowering_trials.sqlite"), Path("agrolattice_twin/agrolattice_twin.sqlite"), Path("models_evidence/research_evidence.sqlite"))
    with tempfile.TemporaryDirectory(prefix="agrolattice11_4-migrate-") as td:
        source = Path(td) / "source"; destination = Path(td) / "destination"
        for rel in relatives:
            make_simple_db(source / rel, "LIVE-SOURCE"); make_simple_db(destination / rel, "PACKAGED")
        backup = migrate(source, destination)
        for rel in relatives:
            require(read_value(destination / rel) == "LIVE-SOURCE", f"Source DB did not replace destination: {rel}")
            require(read_value(backup / "destination_before" / rel) == "PACKAGED", f"Destination backup missing: {rel}")
        report = json.loads((backup / "migration_report.json").read_text(encoding="utf-8"))
        require(len(report["research_databases"]) == 4, "Migration report omitted a research database.")


def verify_release_files() -> None:
    root = Path(__file__).resolve().parent
    required = [
        "RELEASE_MANIFEST_11_4.json", "CHANGELOG_RELEASE_11_4.txt", "README_START_HERE_RELEASE11_4.txt",
        "USER_GUIDE_RELEASE_11_4.txt", "SCIENTIFIC_BASIS_MULTIMODAL_HYBRID_11_4.md", "RESEARCH_METHODS_MANIFEST_11_4.json",
        "research_data_hub.py", "hybrid_residual.py", "weak_supervised_yield.py", "gxem_data_builder.py",
        "multimodal_fusion.py", "research_registry.py", "research_evidence_ui.py",
    ]
    for filename in required: require((root / filename).exists(), f"Required 11.4 file missing: {filename}")
    manifest = json.loads((root / "RELEASE_MANIFEST_11_4.json").read_text(encoding="utf-8"))
    require(manifest["release"] == "AGROLATTICE 11.4" and manifest["protected_database_schema_changes"] is False, "Release manifest invariants are wrong.")
    run_app = (root / "RUN_APP.bat").read_text(encoding="utf-8")
    for module in ("research_data_hub", "hybrid_residual", "weak_supervised_yield", "gxem_data_builder"):
        require(module in run_app, f"RUN_APP preflight does not include {module}.")
    require("research_registry.DB_SCHEMA_VERSION == '1.2.0'" in run_app, "RUN_APP preflight expects the wrong Research Evidence schema.")


def main() -> None:
    verify_registry_and_acquisition()
    verify_11_3_to_11_4_registry_migration()
    verify_research_data_hub_and_phenology()
    verify_pest_paper_equations_and_fold_resampling()
    verify_adaptive_fusion()
    verify_hybrid_residual()
    verify_weak_supervision()
    verify_gxem_builder()
    verify_loyo_and_applicability()
    verify_mechanistic_and_protected_schema_invariants()
    verify_source_authoritative_migration()
    verify_release_files()
    print("AGROLATTICE 11.4 Multimodal Crop Intelligence verification passed")


if __name__ == "__main__":
    main()
