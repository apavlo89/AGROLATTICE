from __future__ import annotations

import ast
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASELINE = {
    "field_operations/field_operations.sqlite": "fbf5ab2de711830a50bed5acfae84a86ec58efc45448d18ea7b88e04b4ff69b5",
    "agrolattice_twin/agrolattice_twin.sqlite": "ea5746651e6fb6c3de409ec8cf64d6e68409b40c0a7853f33982b2fb3f006bb4",
    "models_evidence/research_evidence.sqlite": "516b3361c1bca07b76da4f033dcd4ec693324d41d1924120fded88353600f58b",
    "models_evidence/crop_profiles.sqlite": "84da237e7a8f20b3c84da7c9c423d0aa5a2dab130608c1eebfc2b06885c9e3a6",
    "maize_mechanistic_twin.py": "a62679f3aef1db8dfa4b459db8701cbf8502e7955b88daa520135b905e9400e8",
}
OLD_POLLINATION_SHA = "6dec74ccdb70bcffb9530bf08c6e36eba9827cef0790af0552e8ae4db0c1cd30"


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
                # schema_version is intentionally upgraded; all other predecessor metadata must remain identical.
                old_rows = [r for r in old_rows if not r or str(r[0]) != "schema_version"]
                new_rows = [r for r in new_rows if not r or str(r[0]) != "schema_version"]
            assert old_rows == new_rows, f"Legacy rows changed in {table}"


def main() -> int:
    required = [
        "experiment_command_centre.py", "maize_pollination_lab.py", "agrolattice.py",
        "README_START_HERE_RELEASE11_13.txt", "USER_GUIDE_RELEASE_11_13.txt",
        "CHANGELOG_RELEASE_11_13.txt", "TECHNICAL_BASIS_EXPERIMENTS_11_13.md",
        "RELEASE_MANIFEST_11_13.json", "RESEARCH_METHODS_MANIFEST_11_13.json",
        "RUN_APP.bat", "safe_data_migration.py",
    ]
    for item in required:
        assert (ROOT / item).exists(), item

    assert const_from_source(ROOT / "agrolattice.py", "APP_VERSION") == "20.13-release11.13-experiment-command-centre"
    assert const_from_source(ROOT / "experiment_command_centre.py", "MODULE_VERSION") == "1.0.0"
    assert const_from_source(ROOT / "maize_pollination_lab.py", "MODULE_VERSION") == "3.0.0"
    assert const_from_source(ROOT / "maize_pollination_lab.py", "DB_SCHEMA_VERSION") == "3.0.0"

    cc = (ROOT / "experiment_command_centre.py").read_text(encoding="utf-8")
    maize = (ROOT / "maize_pollination_lab.py").read_text(encoding="utf-8")
    app = (ROOT / "agrolattice.py").read_text(encoding="utf-8")
    assert "st.tabs(" not in cc, "Experiment Command Centre must keep true lazy top-level rendering"
    for token in ["Experiment Pulse", "Experimental protocol", "Factor structure", "Design family & replication", "Experimental-unit data card", "Data completeness", "Analysis-ready G×E×M table", "Experiment audit trail"]:
        assert token in cc, token
    for token in ["experiment_protocols", "experiment_protocol_versions", "trial_factor_definitions", "design_versions", "trial_measurement_requirements", "trial_audit_log", "minimise_adjacent_identical", "randomisation_attempts", "update_trial_design_settings", "protocol_versions"]:
        assert token in maize, token
    assert 'max_value=20' in app and 'maximum_k = min(20, n_samples - 1, unique_profile_count)' in app
    assert 'st.slider("Colour by K-means clusters", 2, 20, 5' in app
    assert '"#636363"' in app, "20-category palette not found"
    assert "render_experiment_command_centre" in app and "page_release10_experiments" in app

    pollination = ROOT / "pollination_lab/maize_flowering_trials.sqlite"
    predecessor = ROOT / "pollination_lab/backups/pre_11_13_maize_flowering_trials.sqlite"
    assert pollination.exists() and predecessor.exists()
    assert sha(predecessor) == OLD_POLLINATION_SHA
    db_health(pollination)
    db_health(predecessor)
    with sqlite3.connect(pollination) as conn:
        schema = conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0]
        assert schema == "3.0.0"
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table in ["experiment_protocols", "experiment_protocol_versions", "trial_factor_definitions", "design_versions", "trial_measurement_requirements", "trial_audit_log"]:
            assert table in tables
            assert conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] == 0, f"Synthetic records packaged in {table}"
    compare_predecessor_projection(predecessor, pollination)

    for relative, expected in BASELINE.items():
        path = ROOT / relative
        assert path.exists(), relative
        assert sha(path) == expected, f"Protected artifact changed unexpectedly: {relative}"
        if path.suffix == ".sqlite":
            db_health(path)

    migration = (ROOT / "safe_data_migration.py").read_text(encoding="utf-8")
    assert 'RELEASE = "AGROLATTICE 11.13"' in migration
    run = (ROOT / "RUN_APP.bat").read_text(encoding="utf-8")
    for token in ["AGROLATTICE 11.13", "experiment_command_centre.py", "experiment_command_centre", "maize_pollination_lab.MODULE_VERSION == '3.0.0'", "maize_pollination_lab.DB_SCHEMA_VERSION == '3.0.0'"]:
        assert token in run, token

    manifest = json.loads((ROOT / "RELEASE_MANIFEST_11_13.json").read_text(encoding="utf-8"))
    assert manifest["release"] == "AGROLATTICE 11.13"
    assert manifest["database_schema_changes"] is True
    assert manifest["mechanistic_maize_model_changed"] is False

    print("AGROLATTICE 11.13 verification passed")
    print("- Experiment Command Centre static architecture checks passed")
    print("- Pollination DB 3.0.0 additive migration and predecessor row preservation passed")
    print("- Protected DB/source hashes match the supplied 11.12 baseline")
    print("- k=2..20 climate clustering controls and diagnostics detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
