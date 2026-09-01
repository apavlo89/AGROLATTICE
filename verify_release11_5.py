"""Regression verification for AGROLATTICE 11.5 Decision Intelligence release.

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
from decision_intelligence import (
    build_crop_daily_drivers, causal_treatment_audit, evaluate_irrigation_policies,
    fit_nutrient_response_model, generate_irrigation_strategies, nutrient_candidate_grid,
    paired_state_assimilation, pareto_mask, scalar_state_assimilation, sequential_state_assimilation,
)
from soil_water_balance import soil_profile_from_preset


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
    with tempfile.TemporaryDirectory(prefix="agrolattice11_5-registry-") as td:
        registry = ResearchEvidenceRegistry(Path(td) / "models_evidence" / "research_evidence.sqlite")
        require(DB_SCHEMA_VERSION == "1.3.0", "Unexpected Research Evidence schema.")
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
        require(registry.integrity_check()["schema_version"] == "1.3.0", "Registry schema version was not persisted.")


def verify_11_4_to_11_5_registry_migration() -> None:
    with tempfile.TemporaryDirectory(prefix="agrolattice11_5-schema-") as td:
        path = Path(td) / "registry.sqlite"
        registry = ResearchEvidenceRegistry(path)
        dataset = registry.register_dataset({"name": "keep me", "provenance": {"sentinel": True}})
        # Emulate the immediately previous 1.2 schema while retaining existing data/acquisition records.
        registry.save_data_acquisition({"source": "NASA POWER", "source_type": "API", "variables": ["T2M"], "row_count": 1})
        with sqlite3.connect(path) as conn:
            for table in ("recommendation_status_history", "decision_runs", "state_assimilations", "causal_analyses"):
                conn.execute(f"DROP TABLE {table}")
            conn.execute("UPDATE metadata SET value='1.2.0' WHERE key='schema_version'")
            conn.commit()
        migrated = ResearchEvidenceRegistry(path)
        require((migrated.datasets()["dataset_id"] == dataset).any(), "Existing registry record was lost during 1.2 -> 1.3 migration.")
        require(migrated.integrity_check()["schema_version"] == "1.3.0", "Registry did not migrate to 1.3.0.")
        require(len(migrated.data_acquisitions()) == 1, "Existing data-acquisition provenance was lost during migration.")
        require(migrated.decision_runs().empty and migrated.state_assimilations().empty and migrated.causal_analyses().empty, "Migration invented decision evidence records.")


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


def verify_decision_registry_records() -> None:
    with tempfile.TemporaryDirectory(prefix="agrolattice11_5-decision-registry-") as td:
        registry = ResearchEvidenceRegistry(Path(td) / "evidence.sqlite")
        run_id = registry.save_decision_run({"decision_type": "Irrigation policy comparison", "objective": "Balanced", "alternatives": [{"Policy": "Rainfed"}]})
        assimilation_id = registry.save_state_assimilation({"state_variable": "soil_water", "prior_mean": 20, "prior_sd": 4, "observation": 23, "observation_sd": 2, "posterior_mean": 22.4, "posterior_sd": 1.79, "sequence": [{"time": "2026-08-01", "posterior_mean": 22.4, "posterior_sd": 1.79}]})
        causal_id = registry.save_causal_analysis({"name": "test", "treatment": "followed", "outcome": "yield", "method": "AIPW", "assumptions": ["exchangeability"], "diagnostics": {}, "estimates": {"ate": 1.0}})
        recommendation_id = registry.save_recommendation({"action_type": "Irrigation", "action_text": "Apply test irrigation", "status": "Proposed"})
        registry.update_recommendation_status(recommendation_id, "Accepted", "Reviewed by researcher")
        history = registry.recommendation_status_history(recommendation_id)
        require(bool(run_id and assimilation_id and causal_id and recommendation_id), "Decision evidence IDs were not created.")
        require(len(history) == 2 and ((history["new_status"] == "Accepted") & (history["note"] == "Reviewed by researcher")).any(), "Recommendation status audit history was not preserved.")
        assimilations = registry.state_assimilations()
        require('2026-08-01' in str(assimilations.iloc[0].get("sequence_json", "")), "State-assimilation sequence JSON was not persisted.")
        summary = registry.summary()
        require(summary.decision_runs == 1 and summary.state_assimilations == 1 and summary.causal_analyses == 1, "Decision evidence summary counts are inconsistent.")
        require(registry.integrity_check()["integrity_check"] == "ok", "Decision Evidence registry failed SQLite integrity.")


def verify_pareto_and_state_assimilation() -> None:
    frame = pd.DataFrame({"yield": [9.0, 10.0, 9.5], "water": [100.0, 180.0, 120.0]})
    mask = pareto_mask(frame, [("yield", "max"), ("water", "min")])
    require(mask.tolist() == [True, True, True], "Pareto mixed-direction screening changed unexpectedly.")
    update = scalar_state_assimilation(20.0, 4.0, 24.0, 2.0)
    require(20.0 < update["posterior_mean"] < 24.0 and update["posterior_sd"] < 2.0, "Scalar assimilation does not shrink uncertainty correctly.")
    seq = sequential_state_assimilation(20.0, 4.0, pd.DataFrame({"date": ["2026-01-01", "2026-01-02"], "obs": [24.0, 23.0], "sd": [2.0, 2.0]}), value_column="obs", sd_column="sd", time_column="date")
    require(len(seq) == 2 and seq["posterior_sd"].iloc[-1] < 2.0, "Sequential assimilation trajectory failed.")
    dynamic = paired_state_assimilation(pd.DataFrame({"time": [1, 2], "prior": [2.0, 3.0], "prior_sd": [.5, .6], "obs": [2.4, 2.8], "obs_sd": [.25, .3]}), prior_mean_column="prior", prior_sd_column="prior_sd", observation_column="obs", observation_sd_column="obs_sd", time_column="time")
    require(len(dynamic) == 2 and np.all((dynamic["posterior_mean"] >= np.minimum(dynamic["prior_mean"], dynamic["observation"])) & (dynamic["posterior_mean"] <= np.maximum(dynamic["prior_mean"], dynamic["observation"]))), "Time-varying paired assimilation failed.")


def verify_irrigation_policy_studio_engine() -> None:
    root = Path(__file__).resolve().parent
    crop_library = json.loads((root / "validated_crop_defaults_mexico.json").read_text(encoding="utf-8"))
    drivers, schedule, meta = build_crop_daily_drivers(
        synthetic_nasa(150), latitude=19.4, crop_library=crop_library, crop="Maize", profile="Grain maize", planting_date="2025-04-01"
    )
    strategies = generate_irrigation_strategies(trigger_values=[0.8, 1.0], refill_values=[0.5, 0.8], fixed_intervals=[7], fixed_depths_mm=[25])
    result = evaluate_irrigation_policies(drivers, soil_profile_from_preset("Silt — FAO screening"), strategies, seasonal_ky=meta.get("whole_season_ky"), potential_yield_t_ha=8.0, crop_price_per_t=250.0, water_cost_per_m3=0.05, seasonal_water_limit_mm=400.0, maximum_irrigation_events=40)
    require(len(result.table) >= 5, "Irrigation policy candidate evaluation returned too few alternatives.")
    require({"Feasible", "Constraint note", "Pareto", "Gross irrigation (mm)", "ET satisfaction (%)", "Stress days"}.issubset(result.table.columns), "Irrigation decision metrics/constraint fields are incomplete.")
    require(result.table["Pareto"].any(), "Irrigation comparison has no Pareto-efficient alternative.")


def verify_nutrient_response_engine() -> None:
    rng = np.random.default_rng(115); rows = []
    for group in range(12):
        for _ in range(8):
            n = rng.uniform(40, 220); p = rng.uniform(10, 90); k = rng.uniform(10, 120)
            y = 4 + 0.035*n - 0.00008*n*n + 0.012*p + 0.008*k + rng.normal(0, 0.18)
            rows.append((group, n, p, k, y))
    frame = pd.DataFrame(rows, columns=["trial", "N", "P", "K", "yield"])
    fitted = fit_nutrient_response_model(frame, target_column="yield", n_column="N", p_column="P", k_column="K", group_column="trial")
    require(np.isfinite(fitted.metrics["rmse"]) and fitted.metrics["rmse"] < 1.0, "Synthetic nutrient response validation failed unexpectedly.")
    grid = nutrient_candidate_grid(fitted, n_range=(40, 220), p_range=(10, 90), k_range=(10, 120), steps=6, crop_price_per_output_unit=250, n_cost_per_unit=1.2, p_cost_per_unit=1.0, k_cost_per_unit=.8)
    require(len(grid) == 216 and grid["Pareto"].any(), "Nutrient candidate/Pareto grid failed.")


def verify_causal_audit_categorical_and_grouped() -> None:
    rng = np.random.default_rng(1155); rows = []
    for group in range(20):
        for i in range(6):
            x = rng.normal(); p = 1/(1+np.exp(-0.7*x))
            treated = rng.random() < p
            y = 2.0 * treated + 0.8*x + rng.normal(0, .5)
            siteclass = "Highland" if group % 2 else "Lowland"
            rows.append((f"trial-{group}", "Followed" if treated else "Not followed", x, siteclass, y))
    frame = pd.DataFrame(rows, columns=["trial", "treatment", "baseline", "siteclass", "yield"])
    result = causal_treatment_audit(frame, treatment_column="treatment", outcome_column="yield", covariates=["baseline", "siteclass"], method="Doubly robust AIPW", group_column="trial", treated_value="Followed", bootstrap_iterations=25, placebo_iterations=25)
    require(np.isfinite(result.estimate) and 0.5 < result.estimate < 3.5, "Categorical/grouped causal audit produced an implausible synthetic effect.")
    require("crossfit_protocol" in result.diagnostics and "Group" in result.diagnostics["crossfit_protocol"], "Grouped cross-fitting was not recorded.")
    require(result.balance is not None and not result.balance.empty, "Causal covariate-balance diagnostics are missing.")
    require(any("siteclass" in str(name) for name in result.diagnostics.get("expanded_design_features", [])), "Categorical pre-treatment covariate was not encoded for causal adjustment.")


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
    require(literal("agrolattice.py", "APP_VERSION") == "20.5-release11.5-decision-intelligence", "Application version string is not 11.5.")


def make_simple_db(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE records(id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("INSERT INTO records(value) VALUES(?)", (value,)); conn.commit()


def read_value(path: Path) -> str:
    with sqlite3.connect(path) as conn: return str(conn.execute("SELECT value FROM records LIMIT 1").fetchone()[0])


def verify_source_authoritative_migration() -> None:
    relatives = (Path("field_operations/field_operations.sqlite"), Path("pollination_lab/maize_flowering_trials.sqlite"), Path("agrolattice_twin/agrolattice_twin.sqlite"), Path("models_evidence/research_evidence.sqlite"))
    with tempfile.TemporaryDirectory(prefix="agrolattice11_5-migrate-") as td:
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
        "RELEASE_MANIFEST_11_5.json", "CHANGELOG_RELEASE_11_5.txt", "README_START_HERE_RELEASE11_5.txt",
        "USER_GUIDE_RELEASE_11_5.txt", "SCIENTIFIC_BASIS_DECISION_INTELLIGENCE_11_5.md", "RESEARCH_METHODS_MANIFEST_11_5.json",
        "research_data_hub.py", "hybrid_residual.py", "weak_supervised_yield.py", "gxem_data_builder.py",
        "multimodal_fusion.py", "research_registry.py", "research_evidence_ui.py",
        "decision_intelligence.py", "decision_intelligence_ui.py",
    ]
    for filename in required:
        require((root / filename).exists(), f"Required 11.5 file missing: {filename}")
    manifest = json.loads((root / "RELEASE_MANIFEST_11_5.json").read_text(encoding="utf-8"))
    require(manifest["release"] == "AGROLATTICE 11.5" and manifest["protected_database_schema_changes"] is False, "Release manifest invariants are wrong.")
    require(manifest["mechanistic_maize_model_changed"] is False, "Manifest incorrectly claims a Mechanistic Maize change.")
    run_app = (root / "RUN_APP.bat").read_text(encoding="utf-8")
    for module in ("research_data_hub", "hybrid_residual", "weak_supervised_yield", "gxem_data_builder", "decision_intelligence", "decision_intelligence_ui"):
        require(module in run_app, f"RUN_APP preflight does not include {module}.")
    require("research_registry.DB_SCHEMA_VERSION == '1.3.0'" in run_app, "RUN_APP preflight expects the wrong Research Evidence schema.")
    require("Decision intelligence & optimisation" in (root / "agrolattice.py").read_text(encoding="utf-8"), "Decision workspace is not routed in agrolattice.py.")


def main() -> None:
    verify_registry_and_acquisition()
    verify_11_4_to_11_5_registry_migration()
    verify_research_data_hub_and_phenology()
    verify_pest_paper_equations_and_fold_resampling()
    verify_adaptive_fusion()
    verify_hybrid_residual()
    verify_weak_supervision()
    verify_gxem_builder()
    verify_loyo_and_applicability()
    verify_decision_registry_records()
    verify_pareto_and_state_assimilation()
    verify_irrigation_policy_studio_engine()
    verify_nutrient_response_engine()
    verify_causal_audit_categorical_and_grouped()
    verify_mechanistic_and_protected_schema_invariants()
    verify_source_authoritative_migration()
    verify_release_files()
    print("AGROLATTICE 11.5 Decision Intelligence & Research Optimisation verification passed")


if __name__ == "__main__":
    main()
