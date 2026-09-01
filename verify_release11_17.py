from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import sqlite3
import sys
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
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def integrity(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok", path
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == [], path


def import_file(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def dummy_streamlit() -> None:
    if "streamlit" not in sys.modules:
        sys.modules["streamlit"] = types.ModuleType("streamlit")


def main() -> None:
    app = (ROOT / "agrolattice.py").read_text(encoding="utf-8")
    assert 'APP_VERSION = "20.17-release11.17-help-onboarding-ux-consistency"' in app
    assert 'AGROLATTICE Release 11.17 · Help, Onboarding & Researcher Guidance' in app
    assert 'USER_GUIDE_RELEASE_11_17.txt' in app
    assert 'render_help_command_centre' in app
    assert 'render_workspace_requirements_panel' in app
    for workspace in ["Home", "Fields & Operations", "AgroLattice Twin", "Climate & Earth Observation", "Crop Decisions", "Experiments", "Models & Evidence", "Reports", "Data & Settings"]:
        assert f'_release11_17_workspace_help("{workspace}")' in app, workspace

    required = [
        "researcher_guidance.py", "help_command_centre.py", "RELEASE_MANIFEST_11_17.json",
        "CHANGELOG_RELEASE_11_17.txt", "README_START_HERE_RELEASE11_17.txt",
        "USER_GUIDE_RELEASE_11_17.txt", "TECHNICAL_BASIS_HELP_ONBOARDING_11_17.md",
        "RESEARCH_METHODS_MANIFEST_11_17.json",
    ]
    for rel in required:
        assert (ROOT / rel).exists(), rel

    # Static syntax across all top-level Python modules.
    for py in ROOT.glob("*.py"):
        ast.parse(py.read_text(encoding="utf-8"), filename=str(py))

    # Protected scientific artifacts stay byte-for-byte identical to supplied 11.16.
    for rel, expected in EXPECTED_HASHES.items():
        path = ROOT / rel
        assert path.exists(), rel
        assert sha(path) == expected, f"Protected artifact changed: {rel}"
        if path.suffix == ".sqlite":
            integrity(path)

    guidance = import_file("researcher_guidance_test", "researcher_guidance.py")
    assert guidance.MODULE_VERSION == "1.0.0"
    assert len(guidance.EVIDENCE_TERMS) >= 11
    assert "Actual operation" in guidance.EVIDENCE_TERMS
    assert "Causal estimate" in guidance.EVIDENCE_TERMS
    assert "maize_synchrony" in guidance.WORKFLOWS
    assert "model_validation" in guidance.WORKFLOWS
    assert set(guidance.WORKSPACE_ORDER) >= {"Fields & Operations", "AgroLattice Twin", "Models & Evidence", "Reports"}

    blank = {key: False for key in guidance.REQUIREMENTS}
    flow = guidance.workflow_progress("maize_synchrony", blank)
    assert flow["total"] >= 5 and flow["ready"] == 0
    ready = dict(blank)
    for key, *_ in guidance.WORKFLOWS["maize_synchrony"]["steps"]:
        ready[key] = True
    flow_ready = guidance.workflow_progress("maize_synchrony", ready)
    assert flow_ready["ready"] == flow_ready["total"]
    rows = guidance.readiness_rows("Experiments", {"mapped_field": True, "trial": False})
    statuses = {row["key"]: row["status"] for row in rows}
    assert statuses["mapped_field"] == "Ready"
    assert statuses["trial"] == "Missing"
    hits = guidance.search_guidance("model leakage")
    assert any(hit["kind"] == "Troubleshooting" for hit in hits)
    assert any("experimental unit" in key.casefold() for key in guidance.GLOSSARY)

    dummy_streamlit()
    help_ui = import_file("help_command_centre_test", "help_command_centre.py")
    assert help_ui.MODULE_VERSION == "1.0.0"
    assert callable(help_ui.collect_guidance_state)
    assert callable(help_ui.render_workspace_requirements_panel)

    help_engine = import_file("ui_release10_4_help_test", "ui_release10_4_help.py")
    assert help_engine.MODULE_VERSION == "10.4.4"
    assert "Experimental unit" in help_engine.TERM_DEFINITIONS
    assert "Applicability" in help_engine.TERM_DEFINITIONS

    # Requested climate cluster exploration remains k <= 20.
    assert 'max_value=20' in app or ', 20,' in app or '2, 20' in app

    manifest = json.loads((ROOT / "RELEASE_MANIFEST_11_17.json").read_text(encoding="utf-8"))
    assert manifest["release"] == "AGROLATTICE 11.17"
    assert manifest["database_schema_changes"] is False
    methods = json.loads((ROOT / "RESEARCH_METHODS_MANIFEST_11_17.json").read_text(encoding="utf-8"))
    assert methods["scientific_methods_changed"] is False
    assert methods["mechanistic_maize_changed"] is False

    run_bat = (ROOT / "RUN_APP.bat").read_text(encoding="utf-8")
    assert "researcher_guidance.py" in run_bat and "help_command_centre.py" in run_bat
    assert "AGROLATTICE 11.17" in run_bat
    assert "ui_release10_4_help.MODULE_VERSION == '10.4.4'" in run_bat

    print("AGROLATTICE 11.17 verification passed")


if __name__ == "__main__":
    main()
