"""Offline/package verifier for AGROLATTICE Release 11.12.

This verifier avoids importing Streamlit/agrolattice.py so it can run in the
packaging environment. RUN_APP.bat performs the full runtime import preflight in
the user's Windows/Anaconda environment.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import sqlite3
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
    print("AGROLATTICE 11.12 offline/package verification")

    app = source("agrolattice.py")
    require('APP_VERSION = "20.12-release11.12-navigation-reliability"' in app, "11.12 APP_VERSION missing")
    require("AGROLATTICE Release 11.12 · Crop Decision Command Centre" in app, "11.12 Crop Decisions header missing")
    require("USER_GUIDE_RELEASE_11_12.txt" in app, "Help is not pointing at 11.12 user guide")

    crop = source("crop_decision_command_centre.py")
    twin = source("twin_command_centre.py")
    climate = source("climate_earth_command_centre.py")
    nav = source("navigation_state.py")
    require('MODULE_VERSION = "1.0.1"' in crop, "Crop Decisions module version mismatch")
    require('MODULE_VERSION = "1.0.1"' in twin, "Twin Command Centre module version mismatch")
    require('MODULE_VERSION = "1.0.1"' in climate, "Climate/EO Command Centre module version mismatch")
    require('MODULE_VERSION = "1.0.0"' in nav, "Navigation helper module version mismatch")
    for token in (
        "crop_decision_command_view_request",
        "crop_decision_command_view_radio",
        "consume_view_request",
        "Opened from priority action",
    ):
        require(token in crop, f"Crop Decisions navigation fix missing: {token}")
    for token in ("twin_cc_view_request", "twin_cc_view_radio", "consume_view_request"):
        require(token in twin, f"Twin navigation hardening missing: {token}")
    for token in ("release11_10_climate_command_view_request", "queue_view_request", "consume_view_request"):
        require(token in climate, f"Climate/EO navigation hardening missing: {token}")

    # Syntax parse current integration modules without requiring Streamlit.
    for rel in (
        "agrolattice.py",
        "navigation_state.py",
        "crop_decision_command_centre.py",
        "twin_command_centre.py",
        "climate_earth_command_centre.py",
        "safe_data_migration.py",
    ):
        ast.parse(source(rel), filename=rel)
    print("  source syntax / navigation hooks: OK")

    # Pure state-machine regression: stale widget state must no longer cancel a button route.
    navmod = load_module("navigation_state_verify", "navigation_state.py")
    require(navmod.MODULE_VERSION == "1.0.0", "navigation_state module version mismatch")
    options = ["Overview", "Crop & planting", "Nutrition", "Pest & crop health"]
    state = {
        "crop_decision_command_view": "Overview",
        "crop_decision_command_view_radio": "Overview",
    }
    navmod.queue_view_request(
        state,
        request_key="crop_decision_command_view_request",
        target="Nutrition",
        notice_key="crop_decision_navigation_notice",
        notice={"area": "Nutrition", "title": "Check nutrient evidence readiness"},
    )
    require(state["crop_decision_command_view_radio"] == "Overview", "Queue mutated widget state too early")
    resolved = navmod.consume_view_request(
        state,
        request_key="crop_decision_command_view_request",
        widget_key="crop_decision_command_view_radio",
        mirror_key="crop_decision_command_view",
        options=options,
        default="Overview",
    )
    require(resolved == "Nutrition", f"Queued route was not resolved: {resolved}")
    require(state["crop_decision_command_view_radio"] == "Nutrition", "Widget state was not synchronized before render")
    require(state["crop_decision_command_view"] == "Nutrition", "Mirror state was not synchronized")
    require("crop_decision_command_view_request" not in state, "Navigation request was not consumed")

    # Invalid requests must not corrupt a valid current view.
    state["crop_decision_command_view_request"] = "Not a real view"
    resolved = navmod.consume_view_request(
        state,
        request_key="crop_decision_command_view_request",
        widget_key="crop_decision_command_view_radio",
        mirror_key="crop_decision_command_view",
        options=options,
        default="Overview",
    )
    require(resolved == "Nutrition", "Invalid route corrupted current navigation state")
    print("  queued navigation state-machine regression: OK")

    # Databases must remain valid; 11.12 has no schema migration.
    for rel in (
        "field_operations/field_operations.sqlite",
        "pollination_lab/maize_flowering_trials.sqlite",
        "agrolattice_twin/agrolattice_twin.sqlite",
        "models_evidence/research_evidence.sqlite",
        "models_evidence/crop_profiles.sqlite",
    ):
        sqlite_check(rel)
        print(f"  {rel}: integrity OK / foreign keys OK")

    run = source("RUN_APP.bat")
    for token in (
        "AGROLATTICE 11.12 - Navigation Reliability & Interaction Fix",
        "navigation_state.py",
        "navigation_state.MODULE_VERSION == '1.0.0'",
        "crop_decision_command_centre.MODULE_VERSION == '1.0.1'",
        "twin_command_centre.MODULE_VERSION == '1.0.1'",
        "climate_earth_command_centre.MODULE_VERSION == '1.0.1'",
    ):
        require(token in run, f"RUN_APP 11.12 preflight hook missing: {token}")
    print("  RUN_APP.bat 11.12 preflight: OK")

    migration = source("safe_data_migration.py")
    require('RELEASE = "AGROLATTICE 11.12"' in migration, "Safe data migration release version not updated")
    require("before_11_12_" in migration, "11.12 migration backup naming missing")
    require('Path("models_evidence/crop_profiles.sqlite")' in migration, "Crop profile registry is not protected by migration utility")
    print("  backup-first migration target labelling: OK")

    manifest = json.loads(source("RELEASE_MANIFEST_11_12.json"))
    require(manifest.get("release") == "AGROLATTICE 11.12", "Release manifest mismatch")
    require(manifest.get("database_schema_changes") is False, "11.12 should not claim a database schema change")
    require(manifest.get("new_dependencies") == [], "11.12 should not add a third-party dependency")
    for rel in (
        "README_START_HERE_RELEASE11_12.txt",
        "USER_GUIDE_RELEASE_11_12.txt",
        "CHANGELOG_RELEASE_11_12.txt",
        "TECHNICAL_BASIS_NAVIGATION_RELIABILITY_11_12.md",
        "RESEARCH_METHODS_MANIFEST_11_12.json",
    ):
        require((ROOT / rel).exists(), f"Missing release documentation: {rel}")
    print("  release documentation / manifest: OK")

    # Scientific model was not touched.
    maize = source("maize_mechanistic_twin.py")
    require('MODULE_VERSION = "1.0.0"' in maize, "Mechanistic Maize Twin version unexpectedly changed")

    print("PASS: AGROLATTICE 11.12 offline/package verification completed.")


if __name__ == "__main__":
    main()
