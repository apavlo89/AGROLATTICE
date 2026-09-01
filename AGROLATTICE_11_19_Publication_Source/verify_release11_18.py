from __future__ import annotations

import ast
import hashlib
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent

EXPECTED_HASHES = {
    "field_operations/field_operations.sqlite": "fbf5ab2de711830a50bed5acfae84a86ec58efc45448d18ea7b88e04b4ff69b5",
    "pollination_lab/maize_flowering_trials.sqlite": "87511c0a9921e731f8bd8b3111118e452b9aa6d6ee32905fee3b7af73a258819",
    "agrolattice_twin/agrolattice_twin.sqlite": "ea5746651e6fb6c3de409ec8cf64d6e68409b40c0a7853f33982b2fb3f006bb4",
    "models_evidence/research_evidence.sqlite": "7e80e599285753c026ff47e86127ad3df42b4cfdb7ff662fb6cd1011b1052a25",
    "models_evidence/crop_profiles.sqlite": "84da237e7a8f20b3c84da7c9c423d0aa5a2dab130608c1eebfc2b06885c9e3a6",
    "reports/reporting.sqlite": "f1e3cd3dfce0a91e65db13f282d940245d5f42716551c276a6cef5af3d5e81d4",
    "maize_mechanistic_twin.py": "a62679f3aef1db8dfa4b459db8701cbf8502e7955b88daa520135b905e9400e8",
}

DB_REL = {
    "Field Operations": Path("field_operations/field_operations.sqlite"),
    "Experiments": Path("pollination_lab/maize_flowering_trials.sqlite"),
    "Persistent Twin": Path("agrolattice_twin/agrolattice_twin.sqlite"),
    "Research Evidence": Path("models_evidence/research_evidence.sqlite"),
    "Crop Profiles": Path("models_evidence/crop_profiles.sqlite"),
    "Reporting": Path("reports/reporting.sqlite"),
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sqlite_integrity(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok", path
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == [], path


def copy_dbs(root: Path) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for label, rel in DB_REL.items():
        src = ROOT / rel
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        paths[label] = dst
    return paths


def build_synthetic_chain(paths: dict[str, Path]) -> tuple[str, str]:
    now = "2026-08-12T08:00:00+00:00"
    farm = "qa-farm"
    field = "qa-field"
    trial = "qa-trial"
    plot = "qa-eu-001"
    twin = "qa-twin"
    model = "qa-model"
    pred = "qa-pred"
    rec = "qa-rec"
    outcome = "qa-outcome"
    study = "qa-study"
    geom = json.dumps({"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]})

    with sqlite3.connect(paths["Field Operations"]) as c:
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("INSERT INTO farms(farm_id,name,country,created_at,updated_at,entity_type) VALUES(?,?,?,?,?,?)", (farm, "QA Farm", "Cyprus", now, now, "Farm"))
        c.execute(
            "INSERT INTO fields(field_id,farm_id,name,geometry_json,geometry_hash,centroid_lat,centroid_lon,area_ha,crop,season_year,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (field, farm, "QA Field", geom, "qa-geometry-hash", 0.5, 0.5, 100.0, "Maize", 2026, "Active", now, now),
        )
        c.execute("INSERT INTO field_seasons(season_id,field_id,season_year,crop,sowing_date,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)", ("qa-season", field, 2026, "Maize", "2026-04-01", "Active", now, now))
        c.execute("INSERT INTO observations(observation_id,field_id,observed_at,category,notes,created_at) VALUES(?,?,?,?,?,?)", ("qa-field-obs", field, "2026-06-01", "Crop", "QA", now))
        c.execute("INSERT INTO operations(operation_id,field_id,operation_date,category,water_mm,created_at) VALUES(?,?,?,?,?,?)", ("qa-operation", field, "2026-05-01", "Irrigation", 20.0, now))

    with sqlite3.connect(paths["Experiments"]) as c:
        c.execute("PRAGMA foreign_keys=ON")
        c.execute(
            """INSERT INTO trials(trial_id,name,site_name,season_year,female_parent,male_parent,female_sowing_date,design_type,blocks,replicates_per_treatment,base_temperature_c,upper_temperature_c,field_geometry_json,field_area_ha,centroid_lat,centroid_lon,created_at,updated_at,source_field_id,source_field_geometry_hash,status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (trial, "QA Trial", "QA Field", 2026, "F1", "M1", "2026-04-01", "RCBD", 1, 1, 8.0, 30.0, geom, 100.0, 0.5, 0.5, now, now, field, "qa-geometry-hash", "Data Collection"),
        )
        c.execute(
            """INSERT INTO plots(plot_id,trial_id,plot_label,block,replicate,treatment_label,male_sowing_offset_days,female_sowing_date,male_sowing_date,geometry_json,area_ha,created_at,female_parent,male_parent,parent_combination) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (plot, trial, "EU-001", 1, 1, "T1", 0, "2026-04-01", "2026-04-01", geom, 1.0, now, "F1", "M1", "F1 × M1"),
        )
        c.execute(
            """INSERT INTO flowering_observations(observation_id,trial_id,plot_id,observation_date,male_plants_assessed,male_shedding_percent,female_plants_assessed,female_silking_percent,created_at) VALUES(?,?,?,?,?,?,?,?,?)""",
            ("qa-flowering", trial, plot, "2026-06-15", 10, 50.0, 10, 50.0, now),
        )
        c.execute("INSERT INTO harvest_outcomes(harvest_id,trial_id,plot_id,harvest_date,seed_yield_t_ha,created_at,updated_at) VALUES(?,?,?,?,?,?,?)", ("qa-harvest", trial, plot, "2026-09-01", 8.0, now, now))

    with sqlite3.connect(paths["Persistent Twin"]) as c:
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("INSERT INTO twin_links(link_id,name,field_id,trial_id,active,created_at,updated_at) VALUES(?,?,?,?,?,?,?)", (twin, "QA Twin", field, trial, 1, now, now))
        c.execute(
            "INSERT INTO twin_weather(link_id,latitude,longitude,start_date,end_date,time_standard,parameters_json,data_json,source,fetched_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (twin, 0.5, 0.5, "2026-04-01", "2026-06-01", "LST", "[]", "[]", "QA synthetic verification", now, now),
        )
        c.execute("INSERT INTO snapshots(snapshot_id,link_id,as_of,state_json,created_at) VALUES(?,?,?,?,?)", ("qa-snapshot", twin, "2026-06-15", "{}", now))

    with sqlite3.connect(paths["Research Evidence"]) as c:
        c.execute("PRAGMA foreign_keys=ON")
        j, a = "{}", "[]"
        c.execute(
            """INSERT INTO models(model_id,name,family,target,task_type,status,implementation_type,training_scope_json,required_modalities_json,feature_names_json,preprocessing_json,validation_protocol_json,metrics_json,calibration_json,applicability_json,limitations_json,dependency_versions_json,code_version,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (model, "QA model", "Regression", "yield", "Regression", "Prototype", "Native AGROLATTICE", j, a, a, j, j, j, j, j, a, j, "11.18", now, now),
        )
        c.execute(
            """INSERT INTO validation_runs(validation_id,model_id,validation_type,evidence_level,primary_metric,metrics_json,fold_metrics_json,predictions_json,split_manifest_json,calibration_json,uncertainty_json,applicability_json,leakage_guards_json,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            ("qa-validation", model, "Leave-one-trial-out", "Internal", "RMSE", '{"RMSE":1.0}', a, a, j, j, j, j, j, "Completed", now),
        )
        c.execute(
            """INSERT INTO predictions(prediction_id,model_id,entity_type,entity_id,field_id,trial_id,season_year,target,prediction,input_snapshot_json,provenance_json,generated_at,class_probabilities_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (pred, model, "Experimental unit", plot, field, trial, 2026, "yield", 7.5, j, j, now, j),
        )
        c.execute(
            """INSERT INTO recommendations(recommendation_id,model_id,prediction_id,field_id,trial_id,experimental_unit_id,action_type,action_text,constraints_json,status,provenance_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (rec, model, pred, field, trial, plot, "Irrigation", "Apply 20 mm", j, "Applied", j, now, now),
        )
        c.execute(
            """INSERT INTO treatment_outcomes(outcome_id,recommendation_id,field_id,trial_id,experimental_unit_id,recommendation_followed,actual_action_text,outcome_variable,outcome_value,outcome_unit,measured_at,covariates_json,provenance_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (outcome, rec, field, trial, plot, 1, "20 mm applied", "yield", 8.0, "t/ha", "2026-09-01", j, j, now),
        )

    with sqlite3.connect(paths["Reporting"]) as c:
        c.execute("PRAGMA foreign_keys=ON")
        c.execute(
            """INSERT INTO studies(study_id,title,short_title,report_type,scope_json,manuscript_json,authors_json,affiliations_json,manuscript_status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (study, "QA E2E report", "QA", "Experiment report", json.dumps({"field_id": field, "trial_id": trial}), "{}", "[]", "[]", "Draft", now, now),
        )
    return field, trial


def main() -> None:
    app = (ROOT / "agrolattice.py").read_text(encoding="utf-8")
    assert 'APP_VERSION = "20.18-release11.18-end-to-end-reliability-performance-integration-qa"' in app
    assert "AGROLATTICE Release 11.18 · Platform Control Centre" in app
    assert "USER_GUIDE_RELEASE_11_18.txt" in app
    assert "reliability_cross_workspace_integrity" in app
    assert "RELEASE11_18_PAGE_CALLABLES" in app
    assert 'request_key="field_command_section_request"' in app
    assert 'request_key="model_evidence_view_request_11_14"' in app
    assert 'request_key="crop_decision_command_view_request"' in app

    required = [
        "integration_reliability.py",
        "README_START_HERE_RELEASE11_18.txt",
        "USER_GUIDE_RELEASE_11_18.txt",
        "CHANGELOG_RELEASE_11_18.txt",
        "TECHNICAL_BASIS_RELIABILITY_INTEGRATION_11_18.md",
        "RESEARCH_METHODS_MANIFEST_11_18.json",
        "RELEASE_MANIFEST_11_18.json",
    ]
    for rel in required:
        assert (ROOT / rel).exists(), rel

    # Syntax across all top-level Python modules.
    for py in ROOT.glob("*.py"):
        ast.parse(py.read_text(encoding="utf-8"), filename=str(py))

    # Protected scientific artifacts are byte-for-byte unchanged from 11.17.
    for rel, expected in EXPECTED_HASHES.items():
        path = ROOT / rel
        assert path.exists(), rel
        assert sha(path) == expected, f"Protected artifact changed: {rel}"
        if path.suffix == ".sqlite":
            sqlite_integrity(path)

    from integration_reliability import (
        MODULE_VERSION,
        append_runtime_event,
        clear_runtime_profile,
        cross_workspace_integrity,
        profile_call,
        runtime_events_frame,
        runtime_profile_summary,
        workflow_chain_status,
    )
    assert MODULE_VERSION == "1.0.0"

    # Runtime profiler is bounded, summarises correctly, and is clearable.
    state: dict[str, object] = {}
    for i in range(300):
        append_runtime_event(state, page="Home" if i % 2 == 0 else "Fields", elapsed_seconds=0.001 + i / 1_000_000)
    events = runtime_events_frame(state)
    assert len(events) == 250
    summary = runtime_profile_summary(events)
    assert set(summary["Page"]) == {"Home", "Fields"}
    assert summary["Runs"].sum() == 250
    assert profile_call(state, "QA callable", lambda: 42) == 42
    assert "QA callable" in set(runtime_events_frame(state)["page"])

    # Streamlit rerun/stop control-flow exceptions are timing events, not reliability errors.
    class RerunException(BaseException):
        pass
    try:
        profile_call(state, "QA rerun", lambda: (_ for _ in ()).throw(RerunException("rerun")))
    except RerunException:
        pass
    rerun_event = runtime_events_frame(state).loc[lambda df: df["page"].eq("QA rerun")].iloc[-1]
    assert rerun_event["status"] == "control"
    assert int(runtime_profile_summary(runtime_events_frame(state))["Errors"].sum()) == 0

    clear_runtime_profile(state)
    assert runtime_events_frame(state).empty

    db_paths = {label: ROOT / rel for label, rel in DB_REL.items()}
    audit = cross_workspace_integrity(db_paths)
    assert not audit.empty
    assert (audit["Status"] == "PASS").all(), audit[audit["Status"] != "PASS"].to_dict("records")

    # Complete end-to-end workflow on temporary copies only.
    with tempfile.TemporaryDirectory(prefix="agrolattice_1118_e2e_") as td:
        temp_root = Path(td)
        temp_paths = copy_dbs(temp_root)
        field_id, trial_id = build_synthetic_chain(temp_paths)
        chain = workflow_chain_status(temp_paths, active_field_id=field_id, active_trial_id=trial_id)
        assert len(chain) >= 14
        assert (chain["Status"] == "Ready").all(), chain.to_dict("records")
        audit2 = cross_workspace_integrity(temp_paths)
        assert (audit2["Status"] == "PASS").all(), audit2[audit2["Status"] != "PASS"].to_dict("records")

        # Authoritative field geometry changed after trial mapping: must warn, never silently rewrite.
        with sqlite3.connect(temp_paths["Field Operations"]) as c:
            c.execute("UPDATE fields SET geometry_hash='changed-after-randomisation' WHERE field_id=?", (field_id,))
        stale = cross_workspace_integrity(temp_paths)
        stale_row = stale.loc[stale["Check"].eq("Trial field-geometry snapshot matches authoritative field")]
        assert not stale_row.empty and stale_row.iloc[0]["Status"] == "WARN"

        # Cross-database evidence references cannot be enforced by SQLite; the audit must catch them.
        with sqlite3.connect(temp_paths["Research Evidence"]) as c:
            c.execute("UPDATE predictions SET field_id='missing-field-reference' WHERE prediction_id='qa-pred'")
        broken = cross_workspace_integrity(temp_paths)
        hit = broken.loc[broken["Check"].eq("predictions field references resolve")]
        assert not hit.empty and hit.iloc[0]["Status"] == "WARN" and int(hit.iloc[0]["Count"]) >= 1

    # Field command centre now supports safe pre-widget routing.
    field_code = (ROOT / "field_command_centre.py").read_text(encoding="utf-8")
    assert 'MODULE_VERSION = "1.0.1"' in field_code
    assert 'request_key="field_command_section_request"' in field_code
    assert "consume_view_request" in field_code

    settings_code = (ROOT / "data_settings_command_centre.py").read_text(encoding="utf-8")
    assert 'MODULE_VERSION = "1.1.0"' in settings_code
    assert '"Integration & reliability"' in settings_code
    assert "runtime_profile_callback" in settings_code
    assert "workflow_chain_callback" in settings_code
    assert "Run integration audit" in settings_code

    # Climate cluster exploration up to 20 remains preserved.
    assert "max_value=20" in app or "2, 20" in app

    manifest = json.loads((ROOT / "RELEASE_MANIFEST_11_18.json").read_text(encoding="utf-8"))
    assert manifest["release"] == "AGROLATTICE 11.18"
    assert manifest["database_schema_changes"] is False
    assert manifest["mechanistic_maize_model_changed"] is False
    methods = json.loads((ROOT / "RESEARCH_METHODS_MANIFEST_11_18.json").read_text(encoding="utf-8"))
    assert methods["scientific_methods_changed"] is False
    assert methods["mechanistic_maize_changed"] is False

    migration = (ROOT / "safe_data_migration.py").read_text(encoding="utf-8")
    assert 'RELEASE = "AGROLATTICE 11.18"' in migration
    assert "before_11_18_" in migration
    for rel in DB_REL.values():
        assert str(rel).replace("\\", "/") in migration

    run_bat = (ROOT / "RUN_APP.bat").read_text(encoding="utf-8")
    assert "AGROLATTICE 11.18" in run_bat
    assert "integration_reliability" in run_bat
    assert "field_command_centre.MODULE_VERSION == '1.0.1'" in run_bat
    assert "data_settings_command_centre.MODULE_VERSION == '1.1.0'" in run_bat

    print("AGROLATTICE 11.18 verification passed")


if __name__ == "__main__":
    main()
