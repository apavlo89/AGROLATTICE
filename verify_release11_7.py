"""Regression verification for AGROLATTICE 11.7 Research Command Centre."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pandas as pd

import home_command_centre
import maize_mechanistic_twin
import verify_release11_6 as v116

ROOT = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def literal(filename: str, name: str):
    tree = ast.parse((ROOT / filename).read_text(encoding="utf-8"), filename=filename)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"Could not find {name} in {filename}")


def function_source(filename: str, function_name: str) -> str:
    source = (ROOT / filename).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=filename)
    lines = source.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            return "\n".join(lines[node.lineno - 1 : node.end_lineno])
    raise AssertionError(f"Could not find function {function_name}")


def verify_home_logic() -> None:
    now = "2026-08-10T10:00:00Z"
    tasks = pd.DataFrame([
        {"status": "Planned", "due_date": "2026-08-09", "title": "Flowering observation", "category": "Phenology"},
        {"status": "Completed", "due_date": "2026-08-08", "title": "Done", "category": "Other"},
        {"status": "Planned", "due_date": "2026-08-14", "title": "Scouting", "category": "Scouting"},
    ])
    alerts = pd.DataFrame([{"status": "Open"}])
    summary = home_command_centre.open_task_summary(tasks, now=now)
    require(summary == {"open": 2, "overdue": 1, "due_soon": 1}, f"Task summary changed: {summary}")
    require(home_command_centre.open_alert_count(alerts) == 1, "Open alert count failed.")

    freshness = [
        home_command_centre.freshness_status("Weather", "2026-08-01", fresh_days=1, warn_days=3, now=now),
        home_command_centre.freshness_status("Satellite", None, fresh_days=7, warn_days=16, now=now),
        home_command_centre.freshness_status("Root zone", None, fresh_days=1, warn_days=3, now=now),
        home_command_centre.freshness_status("Sensors", None, fresh_days=1, warn_days=3, now=now),
    ]
    actions = home_command_centre.build_priority_actions(
        dataset_ready=True,
        has_context=True,
        field_name="Field A",
        tasks=tasks,
        alerts=alerts,
        freshness=freshness,
        trial_status="Active",
        trial_observations=pd.DataFrame(),
        latest_model={"name": "Yield model", "status": "Prototype"},
        latest_prediction={"applicability_status": "Outside training support"},
        recommendations=pd.DataFrame(),
        treatment_outcomes=pd.DataFrame(),
        twin_state={"Uncertainty (%)": 75, "Field observations": 1},
        now=now,
        limit=6,
    )
    titles = [row["title"] for row in actions]
    require(titles[0].startswith("Review 1 overdue"), "Overdue work must be high priority.")
    require(any("weather" in title.casefold() for title in titles), "Stale weather did not trigger a retrieval action.")
    require(any("applicability" in title.casefold() for title in titles), "Out-of-scope prediction did not trigger evidence review.")
    require(any(row.get("tool") == "Research Data Hub" for row in actions), "Weather action does not deep-link to the Data Hub.")

    measurement = home_command_centre.next_best_measurement(
        twin_state={"Uncertainty (%)": 70, "Field observations": 1, "Male progress (%)": 88, "Female progress (%)": 82},
        freshness=freshness,
        trial_active=True,
    )
    require(measurement and "silking" in measurement["title"].casefold(), "Near-flowering measurement recommendation failed.")

    timeline = home_command_centre.build_upcoming_timeline(
        tasks=tasks,
        twin_state={"Predicted male 50% flowering": "2026-08-12"},
        trial=None,
        now=now,
    )
    require(len(timeline) == 2, "Upcoming timeline should contain the modelled event and due task.")
    require(set(timeline["type"]) == {"Modelled", "Task"}, "Timeline lost evidence-type distinction.")


def verify_home_source_guards() -> None:
    source = (ROOT / "agrolattice.py").read_text(encoding="utf-8")
    home_source = function_source("agrolattice.py", "page_release10_home")
    snapshot_source = function_source("agrolattice.py", "_release11_7_home_snapshot")
    require(literal("agrolattice.py", "APP_VERSION") == "20.7-release11.7-research-command-centre", "Application version is not 11.7.")
    require(home_command_centre.MODULE_VERSION == "1.0.0", "Unexpected Home command-centre module version.")
    require("Detailed system readiness" not in home_source and "page_home()" not in home_source, "Legacy nested command centre returned to Home.")
    require("daily_weather_derived" not in home_source and "satellite_time_series" not in home_source, "Home reverted to session-only data readiness.")
    for expensive in ("fetch_nasa_power_daily", "search_sentinel2_scenes", "process_scene_collection", "build_twin_state", "run_aquacrop_ospy"):
        require(expensive not in home_source and expensive not in snapshot_source, f"Home performs expensive work automatically: {expensive}")
    require("merged_df_long" not in home_source and "merged_df_long" not in snapshot_source, "Home directly traverses the large climate runtime table.")
    for marker in ("Twin Pulse", "Priority actions", "Data freshness & completeness", "Model & evidence status", "Next 14 days", "What changed recently", "Recent research projects"):
        require(marker in home_source, f"Home section missing: {marker}")
    require("Historical" in snapshot_source, "Historical-season freshness safeguard is missing.")
    require("Research Data Hub" in source and "_release11_7_open_destination" in source, "Home deep-link routing is missing.")


def verify_release_files() -> None:
    required = [
        "RELEASE_MANIFEST_11_7.json",
        "RESEARCH_METHODS_MANIFEST_11_7.json",
        "CHANGELOG_RELEASE_11_7.txt",
        "README_START_HERE_RELEASE11_7.txt",
        "USER_GUIDE_RELEASE_11_7.txt",
        "TECHNICAL_BASIS_HOME_11_7.md",
        "home_command_centre.py",
    ]
    for filename in required:
        require((ROOT / filename).exists(), f"Required 11.7 file missing: {filename}")
    manifest = json.loads((ROOT / "RELEASE_MANIFEST_11_7.json").read_text(encoding="utf-8"))
    require(manifest["release"] == "AGROLATTICE 11.7", "11.7 manifest has wrong release.")
    require(manifest["database_schema_changes"] is False and manifest["protected_database_schema_changes"] is False, "11.7 must not claim a DB schema change.")
    require(manifest["mechanistic_maize_model_changed"] is False, "11.7 must not claim Mechanistic Maize changes.")
    run_app = (ROOT / "RUN_APP.bat").read_text(encoding="utf-8")
    require("home_command_centre.py" in run_app and "home_command_centre.MODULE_VERSION == '1.0.0'" in run_app, "RUN_APP does not preflight the 11.7 Home module.")
    require("AGROLATTICE 11.7" in run_app, "RUN_APP title/preflight is not current.")


def verify_protected_files() -> None:
    expected = {
        "field_operations/field_operations.sqlite": "e1b2c1e4efe8a846a3fb6563262abcbd59d7ad2e057e70adb3bad3d03041f525",
        "pollination_lab/maize_flowering_trials.sqlite": "6dec74ccdb70bcffb9530bf08c6e36eba9827cef0790af0552e8ae4db0c1cd30",
        "agrolattice_twin/agrolattice_twin.sqlite": "2c36a232474b494f2dcef8cf1f4561cc4c94b291ae85752db3f54f1f3c131d2a",
        "models_evidence/research_evidence.sqlite": "516b3361c1bca07b76da4f033dcd4ec693324d41d1924120fded88353600f58b",
        "maize_mechanistic_twin.py": "a62679f3aef1db8dfa4b459db8701cbf8502e7955b88daa520135b905e9400e8",
    }
    for relative, digest in expected.items():
        require(sha256(ROOT / relative) == digest, f"Protected 11.6 source/data changed unexpectedly: {relative}")
    require(maize_mechanistic_twin.EMERGENCE_GDD == 30.6, "Mechanistic maize emergence GDD changed.")


def main() -> None:
    # Carry forward the full 11.5 scientific/decision suite exposed in verify_release11_6.
    for check in (
        v116.verify_registry_and_acquisition,
        v116.verify_11_4_to_11_5_registry_migration,
        v116.verify_research_data_hub_and_phenology,
        v116.verify_pest_paper_equations_and_fold_resampling,
        v116.verify_adaptive_fusion,
        v116.verify_hybrid_residual,
        v116.verify_weak_supervision,
        v116.verify_gxem_builder,
        v116.verify_loyo_and_applicability,
        v116.verify_decision_registry_records,
        v116.verify_pareto_and_state_assimilation,
        v116.verify_irrigation_policy_studio_engine,
        v116.verify_nutrient_response_engine,
        v116.verify_causal_audit_categorical_and_grouped,
        v116.verify_source_authoritative_migration,
        v116.verify_runtime_equivalence_and_signatures,
        v116.verify_settings_write_optimisation,
        v116.verify_brand_assets,
    ):
        check()
    verify_home_logic()
    verify_home_source_guards()
    verify_release_files()
    verify_protected_files()
    print("AGROLATTICE 11.7 Research Command Centre verification passed")


if __name__ == "__main__":
    main()
