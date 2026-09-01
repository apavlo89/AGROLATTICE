from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import sqlite3
import sys
import tempfile
import types
from pathlib import Path

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


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def integrity(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok", path
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == [], path


def dummy_streamlit() -> None:
    if "streamlit" not in sys.modules:
        sys.modules["streamlit"] = types.ModuleType("streamlit")


def import_file(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def make_db(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS records(id INTEGER PRIMARY KEY, value TEXT)")
        conn.execute("INSERT OR REPLACE INTO metadata(key,value) VALUES('schema_version','test-1')")
        conn.execute("DELETE FROM records")
        conn.execute("INSERT INTO records(value) VALUES(?)", (value,))
        conn.commit()


def main() -> None:
    # Version/files and static syntax.
    app = (ROOT / "agrolattice.py").read_text(encoding="utf-8")
    assert 'APP_VERSION = "20.16-release11.16-platform-control-centre-data-settings-tool-catalogue"' in app
    assert "render_data_settings_command_centre" in app
    assert "render_tool_catalogue" in app
    assert '"Current 11.16 guide"' in app
    for required in [
        "platform_settings.py", "data_settings_command_centre.py", "tool_catalogue.py",
        "RELEASE_MANIFEST_11_16.json", "CHANGELOG_RELEASE_11_16.txt",
        "README_START_HERE_RELEASE11_16.txt", "USER_GUIDE_RELEASE_11_16.txt",
        "TECHNICAL_BASIS_PLATFORM_CONTROL_11_16.md", "RESEARCH_METHODS_MANIFEST_11_16.json",
    ]:
        assert (ROOT / required).exists(), required
    for py in ROOT.glob("*.py"):
        ast.parse(py.read_text(encoding="utf-8"), filename=str(py))

    # Protected scientific artifacts remain byte-for-byte unchanged from supplied 11.15.
    for rel, expected in EXPECTED_HASHES.items():
        path = ROOT / rel
        assert path.exists(), rel
        assert sha(path) == expected, f"Protected artifact changed: {rel}"
        if path.suffix == ".sqlite":
            integrity(path)

    # Platform settings persistence/favourites/recent tools.
    settings_mod = import_file("platform_settings_test", "platform_settings.py")
    assert settings_mod.MODULE_VERSION == "1.0.0"
    with tempfile.TemporaryDirectory() as td:
        store = settings_mod.PlatformSettingsStore(td)
        data = store.load()
        assert data["workspace"]["default_role"] == "Researcher"
        store.update_section("workspace", {"default_role": "Agronomist"})
        store.toggle_favourite("PCA")
        store.record_recent_tool("PCA")
        loaded = store.load()
        assert loaded["workspace"]["default_role"] == "Agronomist"
        assert "PCA" in loaded["tool_catalogue"]["favourites"]
        assert loaded["tool_catalogue"]["recent"][0] == "PCA"

    # Import UI helper with a harmless Streamlit stub and regression-test backup/restore primitives.
    dummy_streamlit()
    ds = import_file("data_settings_command_centre_test", "data_settings_command_centre.py")
    assert ds.MODULE_VERSION == "1.0.0"
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        db1 = root / "field_operations" / "field_operations.sqlite"
        db2 = root / "models_evidence" / "research_evidence.sqlite"
        make_db(db1, "before-A")
        make_db(db2, "before-B")
        package = ds.create_backup_package(
            app_root=root,
            app_version="test-release",
            database_paths={"Field Operations": db1, "Research Evidence": db2},
            include_projects=False,
            include_attachments=False,
            include_report_assets=False,
            include_climate=False,
        )
        blob = package.read_bytes()
        check = ds.validate_backup_package(blob, expected_databases={"Field Operations": db1, "Research Evidence": db2}, app_root=root)
        assert not check["failures"], check
        make_db(db1, "changed-A")
        make_db(db2, "changed-B")
        recovery = ds.restore_databases_from_package(blob, app_root=root, database_paths={"Field Operations": db1, "Research Evidence": db2}, app_version="test-release")
        assert recovery.exists()
        with sqlite3.connect(db1) as conn:
            assert conn.execute("SELECT value FROM records").fetchone()[0] == "before-A"
        with sqlite3.connect(db2) as conn:
            assert conn.execute("SELECT value FROM records").fetchone()[0] == "before-B"
        integrity(db1); integrity(db2)

    tc = import_file("tool_catalogue_test", "tool_catalogue.py")
    assert tc.MODULE_VERSION == "1.0.0"
    assert tc._maturity("Workflow & reporting", "All Tools / Legacy") == "Legacy"
    assert tc._maturity("Climate similarity", "Climate & Earth Observation") == "Primary"

    # Preserve the requested k<=20 climate/PCA exploration.
    assert 'max_value=20' in app or ', 20,' in app or '2, 20' in app

    manifest = json.loads((ROOT / "RELEASE_MANIFEST_11_16.json").read_text(encoding="utf-8"))
    assert manifest["release"] == "AGROLATTICE 11.16"
    assert manifest["database_schema_changes"] is False
    print("AGROLATTICE 11.16 verification passed")


if __name__ == "__main__":
    main()
