from __future__ import annotations

import ast
import hashlib
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path

import pandas as pd
import yaml

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
    """Insert a complete temporary cross-database workflow for integration/migration regression."""
    now = "2026-08-12T08:00:00+00:00"
    farm, field, trial, plot, twin = "qa-farm", "qa-field", "qa-trial", "qa-eu-001", "qa-twin"
    model, pred, rec, outcome, study = "qa-model", "qa-pred", "qa-rec", "qa-outcome", "qa-study"
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
            (model, "QA model", "Regression", "yield", "Regression", "Prototype", "Native AGROLATTICE", j, a, a, j, j, j, j, j, a, j, "11.19", now, now),
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
    assert (
        'APP_VERSION = "20.19-release11.19-publication-reference-release"' in app
        or 'APP_VERSION = "20.19-release11.19-publication-reference-adaptive-clustering-ac3"' in app
    )
    assert "AGROLATTICE Release 11.19 · Platform Control Centre" in app
    assert "AGROLATTICE Release 11.19 · Research Reporting & Publication Command Centre" in app
    assert "USER_GUIDE_RELEASE_11_19.txt" in app
    assert "PUBLICATION_REFERENCE_ID" in app and "page_publication_reference" in app
    assert 'request_key="field_command_section_request"' in app
    assert 'request_key="model_evidence_view_request_11_14"' in app
    assert 'request_key="crop_decision_command_view_request"' in app
    assert "max_value=20" in app or "2, 20" in app

    required = [
        "publication_reference.py",
        "README_START_HERE_RELEASE11_19.txt",
        "USER_GUIDE_RELEASE_11_19.txt",
        "CHANGELOG_RELEASE_11_19.txt",
        "TECHNICAL_BASIS_PUBLICATION_REFERENCE_11_19.md",
        "RESEARCH_METHODS_MANIFEST_11_19.json",
        "RELEASE_MANIFEST_11_19.json",
        "PUBLICATION_REFERENCE_ID.txt",
        "PUBLICATION_REFERENCE_WORKFLOW.md",
        "PAPER_STARTER_AGROLATTICE_11_19.md",
        "SCREENSHOT_AND_FIGURE_CAPTURE_CHECKLIST.md",
        "requirements_publication_reference_lock.txt",
        "FREEZE_PUBLICATION_ENV.bat",
        "RUN_PUBLICATION_REFERENCE_DEMO.bat",
        "build_public_archive.py",
        "PUBLIC_ARCHIVE_EXCLUSIONS.md",
        "publication_reference/database_schemas/DATABASE_SCHEMA_MANIFEST.json",
        "CITATION.cff",
        "codemeta.json",
        ".zenodo.json",
        "LICENSE",
        "THIRD_PARTY_NOTICE.md",
        "SOURCE_FILE_MANIFEST_11_19.sha256",
    ]
    for rel in required:
        assert (ROOT / rel).exists(), rel

    # Syntax across all top-level Python modules without importing Streamlit.
    for py in ROOT.glob("*.py"):
        ast.parse(py.read_text(encoding="utf-8"), filename=str(py))

    # Protected research artifacts remain byte-for-byte identical to 11.18.
    for rel, expected in EXPECTED_HASHES.items():
        path = ROOT / rel
        assert path.exists(), rel
        assert sha(path) == expected, f"Protected artifact changed: {rel}"
        if path.suffix == ".sqlite":
            sqlite_integrity(path)

    from publication_reference import (
        MODULE_VERSION as PUB_MODULE_VERSION,
        REFERENCE_ID,
        CANONICAL_WEATHER_VARIABLES,
        demo_summary,
        verify_demo_bundle,
        write_demo_bundle,
    )
    assert PUB_MODULE_VERSION == "1.0.0"
    assert REFERENCE_ID == "AGROLATTICE-11.19-PRR-2026-08-12"
    assert len(CANONICAL_WEATHER_VARIABLES) == 19
    verify_demo_bundle(ROOT / "publication_reference/demo_project")
    summary = demo_summary()
    assert summary["synthetic"] is True
    assert summary["experimental_units"] == 24 and summary["blocks"] == 4 and summary["treatments"] == 6
    assert summary["weather_variables"] == 19

    # Rebuilding the fixed demo reproduces identical source tables/manifests.
    with tempfile.TemporaryDirectory(prefix="agrolattice_1119_demo_") as td:
        out = Path(td)
        write_demo_bundle(out)
        verify_demo_bundle(out)
        for name in [
            "demo_trial_design.csv", "demo_flowering_observations.csv", "demo_model_validation.csv",
            "demo_weather_19_variables.csv", "demo_field.geojson", "demo_summary.json", "DEMO_DATA_MANIFEST.json",
        ]:
            assert sha(out / name) == sha(ROOT / "publication_reference/demo_project" / name), name

    # Publication figures and example outputs are present and non-trivial.
    figures = ROOT / "publication_reference/figures"
    for stem in [
        "figure_01_platform_architecture", "figure_02_evidence_workflow",
        "figure_03_demo_trial_layout", "figure_04_demo_observed_vs_predicted",
    ]:
        assert (figures / f"{stem}.png").stat().st_size > 50_000
        assert (figures / f"{stem}.svg").stat().st_size > 10_000
    example = ROOT / "publication_reference/example_outputs"
    assert (example / "table_01_treatment_summary.csv").exists()
    assert (example / "example_results_summary.md").exists()
    assert "not model-validation evidence" in (example / "example_results_summary.md").read_text(encoding="utf-8").casefold()


    # Schema-only exports and the publication-safe source-archive builder exclude user data.
    schema_manifest = json.loads((ROOT / "publication_reference/database_schemas/DATABASE_SCHEMA_MANIFEST.json").read_text(encoding="utf-8"))
    assert schema_manifest["contains_user_rows"] is False
    assert set(schema_manifest["schemas"]) == {"field_operations", "experiments", "persistent_twin", "research_evidence", "crop_profiles", "reporting"}
    from build_public_archive import build as build_public_archive
    with tempfile.TemporaryDirectory(prefix="agrolattice_1119_public_source_") as td:
        archive_path = Path(td) / "source.zip"
        result = build_public_archive(ROOT, archive_path)
        assert result["file_count"] > 50 and archive_path.exists()
        import zipfile
        with zipfile.ZipFile(archive_path) as z:
            names = z.namelist()
            assert not any(name.lower().endswith(".sqlite") or "/datasets/" in name.casefold() for name in names)
            assert any(name.endswith("publication_reference/demo_project/DEMO_DATA_MANIFEST.json") for name in names)
            assert any(name.endswith("publication_reference/database_schemas/research_evidence_schema.sql") for name in names)

    # Citation/archive metadata are syntactically readable and do not claim a DOI.
    citation = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
    assert citation["version"] == "11.19" and citation["license"] == "MIT"
    assert citation["title"].startswith("AGROLATTICE")
    assert "doi" not in citation
    zenodo = json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    assert zenodo["version"] == "11.19" and zenodo["license"] == "MIT"
    codemeta = json.loads((ROOT / "codemeta.json").read_text(encoding="utf-8"))
    assert codemeta["version"] == "11.19"

    # The reference lock is exact (no ranges) for all active dependency lines.
    lock_lines = [x.strip() for x in (ROOT / "requirements_publication_reference_lock.txt").read_text(encoding="utf-8").splitlines() if x.strip() and not x.lstrip().startswith("#")]
    assert len(lock_lines) >= 20
    assert all("==" in x and all(op not in x.replace("==", "") for op in (">=", "<=", "~=", ">", "<")) for x in lock_lines)

    manifest = json.loads((ROOT / "RELEASE_MANIFEST_11_19.json").read_text(encoding="utf-8"))
    assert manifest["release"] == "AGROLATTICE 11.19"
    assert manifest["publication_reference_id"] == REFERENCE_ID
    assert manifest["database_schema_changes"] is False
    assert manifest["mechanistic_maize_model_changed"] is False
    methods = json.loads((ROOT / "RESEARCH_METHODS_MANIFEST_11_19.json").read_text(encoding="utf-8"))
    assert methods["scientific_methods_changed"] is False
    assert methods["mechanistic_maize_changed"] is False

    # Existing 11.18 integration QA still passes on the unchanged core infrastructure.
    from integration_reliability import cross_workspace_integrity, workflow_chain_status
    db_paths = {label: ROOT / rel for label, rel in DB_REL.items()}
    audit = cross_workspace_integrity(db_paths)
    assert not audit.empty and (audit["Status"] == "PASS").all(), audit[audit["Status"] != "PASS"].to_dict("records")
    with tempfile.TemporaryDirectory(prefix="agrolattice_1119_e2e_") as td:
        temp_paths = copy_dbs(Path(td))
        field_id, trial_id = build_synthetic_chain(temp_paths)
        chain = workflow_chain_status(temp_paths, active_field_id=field_id, active_trial_id=trial_id)
        assert len(chain) >= 14 and (chain["Status"] == "Ready").all(), chain.to_dict("records")
        audit2 = cross_workspace_integrity(temp_paths)
        assert (audit2["Status"] == "PASS").all(), audit2[audit2["Status"] != "PASS"].to_dict("records")

    # Backup-first migration still protects all six user-owned databases and is regression-tested on temp copies.
    migration = (ROOT / "safe_data_migration.py").read_text(encoding="utf-8")
    assert 'RELEASE = "AGROLATTICE 11.19"' in migration
    assert "before_11_19_" in migration
    for rel in DB_REL.values():
        assert str(rel).replace("\\", "/") in migration
    from safe_data_migration import migrate, table_counts
    with tempfile.TemporaryDirectory(prefix="agrolattice_1119_migrate_") as td:
        base = Path(td)
        src_root, dst_root = base / "source", base / "dest"
        src_paths, dst_paths = copy_dbs(src_root), copy_dbs(dst_root)
        build_synthetic_chain(src_paths)
        backup = migrate(src_root, dst_root)
        assert backup.exists() and "before_11_19_" in backup.name
        for label, rel in DB_REL.items():
            sqlite_integrity(dst_root / rel)
            assert table_counts(dst_root / rel) == table_counts(src_root / rel), label

    run_bat = (ROOT / "RUN_APP.bat").read_text(encoding="utf-8")
    assert "AGROLATTICE 11.19" in run_bat
    assert "publication_reference.py" in run_bat and "verify_release11_19.py" in run_bat
    assert "AGROLATTICE-11.19-PRR-2026-08-12" in run_bat

    # Source manifest covers the major immutable/publication files and each recorded digest matches.
    source_manifest = ROOT / "SOURCE_FILE_MANIFEST_11_19.sha256"
    rows = [line.split("  ", 1) for line in source_manifest.read_text(encoding="utf-8").splitlines() if "  " in line]
    entries = {path: digest for digest, path in rows}
    for rel in ["agrolattice.py", "publication_reference.py", "CITATION.cff", "LICENSE", "maize_mechanistic_twin.py"]:
        assert rel in entries, rel
        assert entries[rel] == sha(ROOT / rel), rel

    # Publication archive intentionally contains no packaged network cache files.
    cache_root = ROOT / "cache"
    if cache_root.exists():
        assert not any(p.is_file() for p in cache_root.rglob("*")), "Publication archive contains volatile cache files"

    print("AGROLATTICE 11.19 publication-reference verification passed")


if __name__ == "__main__":
    main()
