"""Offline/package verifier for AGROLATTICE Release 11.11.

This verifier intentionally avoids importing Streamlit/agrolattice.py so it can
run in the packaging environment. RUN_APP.bat performs the full runtime import
preflight in the user's Windows/Anaconda environment.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import sqlite3
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def source(path: str) -> str:
    p = ROOT / path
    require(p.exists(), f"Missing required file: {path}")
    return p.read_text(encoding="utf-8", errors="replace")


def load_module(name: str, relpath: str):
    path = ROOT / relpath
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"Cannot import {relpath}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sqlite_check(relpath: str) -> tuple[str, int]:
    path = ROOT / relpath
    require(path.exists(), f"Missing database: {relpath}")
    con = sqlite3.connect(path)
    try:
        integrity = str(con.execute("PRAGMA integrity_check").fetchone()[0])
        foreign = len(con.execute("PRAGMA foreign_key_check").fetchall())
    finally:
        con.close()
    require(integrity.lower() == "ok", f"SQLite integrity failed: {relpath}: {integrity}")
    require(foreign == 0, f"SQLite foreign-key violations: {relpath}: {foreign}")
    return integrity, foreign


def main() -> None:
    print("AGROLATTICE 11.11 offline/package verification")

    app = source("agrolattice.py")
    require('APP_VERSION = "20.11-release11.11-crop-decision-command-centre"' in app, "11.11 APP_VERSION missing")
    require("AGROLATTICE Release 11.11 · Crop Decision Command Centre" in app, "11.11 Crop Decisions header missing")
    require("USER_GUIDE_RELEASE_11_11.txt" in app, "Help is not pointing at 11.11 user guide")
    require("CropProfileRegistry" in app and "crop_profiles.sqlite" in app, "Crop Profile Registry is not wired into application")
    require("render_crop_decision_command_centre" in app, "Crop Decision Command Centre is not wired into application")

    cmd = source("crop_decision_command_centre.py")
    for token in (
        'MODULE_VERSION = "1.0.0"',
        '"Overview", "Crop & planting", "Water & irrigation", "Nutrition", "Pest & crop health"',
        '"Yield & economics", "Crop models", "Recommendations & outcomes"',
        "Daily sowing-date climate risk explorer",
        "Operationally eligible",
        "risk prediction",
        "Recommendation → action → outcome",
        "Data readiness",
        "Which model should I use?",
    ):
        require(token.casefold() in cmd.casefold(), f"Missing Crop Decisions implementation hook: {token}")
    require("fetch_canonical_nasa_weather" in cmd, "Canonical NASA retrieval not available to Crop Decisions")
    require("nasa_pest_covariates" in cmd, "NASA-compatible pest covariates not wired")
    require("applicability_score" in cmd, "Pest applicability check not wired")

    # Syntax parse the integration-heavy modules without requiring Streamlit.
    for rel in (
        "agrolattice.py",
        "crop_decision_command_centre.py",
        "crop_profile_registry.py",
        "aquacrop_integration.py",
        "dssat_apsim_interop.py",
        "decision_intelligence_ui.py",
    ):
        ast.parse(source(rel), filename=rel)
    print("  source syntax / integration hooks: OK")

    profiles_mod = load_module("crop_profile_registry_verify", "crop_profile_registry.py")
    require(profiles_mod.MODULE_VERSION == "1.0.0", "Crop Profile Registry module version mismatch")
    require(profiles_mod.DB_SCHEMA_VERSION == "1.0.0", "Crop Profile Registry schema version mismatch")

    # Regression: version history must survive an update and cloning must produce a separate profile.
    with tempfile.TemporaryDirectory(prefix="agrolattice_11_11_profiles_") as td:
        reg = profiles_mod.CropProfileRegistry(Path(td) / "profiles.sqlite")
        pid = reg.save_profile(
            {"name": "Verification maize", "crop": "Maize", "country": "Test", "author": "Verifier"},
            parameters={"base_temp": 10.0}, change_note="v1",
        )
        reg.save_profile(
            {"profile_id": pid, "name": "Verification maize", "crop": "Maize", "country": "Test", "author": "Verifier"},
            parameters={"base_temp": 10.5}, change_note="v2",
        )
        versions = reg.versions(pid)
        require(len(versions) == 2, f"Crop profile version history regression: expected 2, got {len(versions)}")
        require(sorted(versions["version_number"].astype(int).tolist()) == [1, 2], "Crop profile version numbering failed")
        clone = reg.clone_profile(pid, name="Verification maize clone", author="Verifier")
        require(clone != pid, "Crop profile clone reused source id")
        require(reg.profile(clone) is not None, "Cloned crop profile missing")
        require(reg.integrity_check() == ("ok", 0), "Temporary Crop Profile Registry integrity failed")
    print("  crop-profile version history / clone regression: OK")

    # Installed empty registry schema/integrity.
    crop_profile_db = ROOT / "models_evidence" / "crop_profiles.sqlite"
    require(crop_profile_db.exists(), "Packaged crop profile database missing")
    sqlite_check("models_evidence/crop_profiles.sqlite")
    con = sqlite3.connect(crop_profile_db)
    try:
        schema = con.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
        require(schema and schema[0] == "1.0.0", "Packaged crop profile DB schema metadata mismatch")
    finally:
        con.close()
    print("  crop-profile packaged database: OK")

    for rel in (
        "field_operations/field_operations.sqlite",
        "pollination_lab/maize_flowering_trials.sqlite",
        "agrolattice_twin/agrolattice_twin.sqlite",
        "models_evidence/research_evidence.sqlite",
    ):
        sqlite_check(rel)
        print(f"  {rel}: integrity OK / foreign keys OK")

    aqua = source("aquacrop_integration.py")
    for token in ("TEMPERATURE_MIN", "TEMPERATURE_MAX", "PRECIPITATION_AVG", "EVAPOTRANSPIRATION"):
        require(token in aqua, f"AquaCrop canonical weather alias missing: {token}")
    external = source("dssat_apsim_interop.py")
    for token in ("TEMPERATURE_MIN", "TEMPERATURE_MAX", "PRECIPITATION_AVG", "SOLAR_RADIATION"):
        require(token in external, f"DSSAT/APSIM canonical weather alias missing: {token}")
    print("  canonical crop-model weather aliases: OK")

    run = source("RUN_APP.bat")
    for token in (
        "AGROLATTICE 11.11 - Crop Decision Command Centre & Agronomic Planning",
        "crop_decision_command_centre.py",
        "crop_profile_registry.py",
        "crop_decision_command_centre.MODULE_VERSION == '1.0.0'",
        "crop_profile_registry.DB_SCHEMA_VERSION == '1.0.0'",
    ):
        require(token in run, f"RUN_APP 11.11 preflight hook missing: {token}")
    print("  RUN_APP.bat 11.11 preflight: OK")

    migration = source("safe_data_migration.py")
    require('RELEASE = "AGROLATTICE 11.11"' in migration, "Safe data migration release version not updated")
    require('Path("models_evidence/crop_profiles.sqlite")' in migration, "Safe data migration does not protect/migrate crop profile registry")
    require("before_11_11_" in migration, "11.11 migration backup naming missing")
    print("  backup-first user-data migration 11.11 hooks: OK")

    manifest = json.loads(source("RELEASE_MANIFEST_11_11.json"))
    require(manifest.get("release") == "AGROLATTICE 11.11", "Release manifest mismatch")
    for rel in (
        "README_START_HERE_RELEASE11_11.txt",
        "USER_GUIDE_RELEASE_11_11.txt",
        "CHANGELOG_RELEASE_11_11.txt",
        "TECHNICAL_BASIS_CROP_DECISIONS_11_11.md",
        "RESEARCH_METHODS_MANIFEST_11_11.json",
    ):
        require((ROOT / rel).exists(), f"Missing release documentation: {rel}")
    print("  release documentation / manifest: OK")

    # Make sure the mechanistic maize model itself was not relabelled/reworked by this release.
    maize = source("maize_mechanistic_twin.py")
    require('MODULE_VERSION = "1.0.0"' in maize, "Mechanistic Maize Twin version unexpectedly changed")

    print("PASS: AGROLATTICE 11.11 offline/package verification completed.")


if __name__ == "__main__":
    main()
