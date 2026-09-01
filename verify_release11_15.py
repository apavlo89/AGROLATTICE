from __future__ import annotations

import ast
import hashlib
import io
import json
import shutil
import sqlite3
import tempfile
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
PROTECTED_HASHES = {
    "field_operations/field_operations.sqlite": "fbf5ab2de711830a50bed5acfae84a86ec58efc45448d18ea7b88e04b4ff69b5",
    "pollination_lab/maize_flowering_trials.sqlite": "87511c0a9921e731f8bd8b3111118e452b9aa6d6ee32905fee3b7af73a258819",
    "agrolattice_twin/agrolattice_twin.sqlite": "ea5746651e6fb6c3de409ec8cf64d6e68409b40c0a7853f33982b2fb3f006bb4",
    "models_evidence/research_evidence.sqlite": "7e80e599285753c026ff47e86127ad3df42b4cfdb7ff662fb6cd1011b1052a25",
    "models_evidence/crop_profiles.sqlite": "84da237e7a8f20b3c84da7c9c423d0aa5a2dab130608c1eebfc2b06885c9e3a6",
    "maize_mechanistic_twin.py": "a62679f3aef1db8dfa4b459db8701cbf8502e7955b88daa520135b905e9400e8",
}


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


def db_health(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0].lower() == "ok", path
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == [], path


def functional_reporting_regression() -> None:
    from reporting_registry import ReportingRegistry
    from publication_builder import build_publication_package, figure_png, figure_svg, new_study_template, report_audit

    with tempfile.TemporaryDirectory(prefix="agrolattice_11_15_reporting_") as td:
        root = Path(td)
        registry = ReportingRegistry(root / "reporting.sqlite", root / "assets")
        assert registry.integrity_check()["schema_version"] == "1.0.0"
        assert len(registry.citations()) >= 7
        template = new_study_template(title="Verification report", report_type="Model validation report")
        manuscript = {
            "abstract_background": "Verification background.",
            "abstract_methods": "Verification methods.",
            "abstract_results": "Verification results.",
            "abstract_conclusion": "Verification conclusion.",
            "introduction": "Verification introduction.",
            "study_design": "Grouped verification design.",
            "results": "Verification results narrative.",
            "discussion": "Verification discussion.",
            "limitations": "Synthetic temporary verification only.",
            "conclusion": "Verification conclusion.",
            "data_availability": "Synthetic temporary data.",
            "code_availability": "Release verifier only.",
        }
        sid = registry.save_study({**template, "scope": {"field_id": "F1"}, "manuscript": manuscript})
        snapshot_manifest = {"artifacts": {"verification": {"sha256_csv": "abc"}}, "readiness": {"Validation": {"status": "Complete"}}}
        snap = registry.save_snapshot(sid, label="Verification freeze", scope={"field_id": "F1"}, manifest=snapshot_manifest)
        version = registry.create_version(sid, manuscript=manuscript, snapshot_id=snap, label="Verification v1", author="Verifier")
        assert version
        frame = pd.DataFrame({"Observed": [1.0, 2.0, 3.0], "Predicted": [1.1, 1.9, 2.8]})
        table_id = registry.save_artifact(sid, kind="table", title="Observed/predicted", caption="Verification table", source={"artifact": "verification"}, settings={"columns": list(frame)}, data=frame.to_csv(index=False).encode(), suffix=".csv", snapshot_id=snap)
        fig = figure_png(frame, chart_type="Observed vs predicted", x_column="Observed", y_columns=["Predicted"], title="Observed vs predicted")
        fig_svg = figure_svg(frame, chart_type="Observed vs predicted", x_column="Observed", y_columns=["Predicted"], title="Observed vs predicted")
        assert fig_svg.lstrip().startswith(b"<?xml") or b"<svg" in fig_svg[:500]
        figure_id = registry.save_artifact(sid, kind="figure", title="Observed vs predicted", caption="Verification figure", source={"artifact": "verification"}, settings={"chart_type": "Observed vs predicted"}, data=fig, suffix=".png", snapshot_id=snap)
        assert table_id and figure_id
        claim_id = registry.save_claim(sid, text="The model caused yield improvement", evidence_type="Predictive", source_reference="verification table", statistic="RMSE=0.2")
        assert claim_id
        warnings = report_audit({**template, **manuscript}, claims=registry.claims(sid).to_dict("records"), figure_count=1, table_count=1, citation_count=1, snapshot_present=True, evidence_manifest=snapshot_manifest)
        assert any(row["category"] == "Claim" for row in warnings)
        citation = registry.citations().iloc[0].to_dict()
        registry.link_citation(sid, citation["citation_id"], "Verification method")
        tables = [{"title": "Observed/predicted", "caption": "Verification table", "frame": frame, "source": {"artifact": "verification"}, "settings": {}}]
        figures = [{"title": "Observed vs predicted", "caption": "Verification figure", "png": fig, "svg": fig_svg, "source": {"artifact": "verification"}, "settings": {}}]
        pkg = build_publication_package(
            study={**template, **manuscript, "authors": ["Verifier"], "affiliations": ["AGROLATTICE QA"]},
            selected_methods=["Agricultural grouped validation"],
            selected_tables=tables,
            figures=figures,
            reproducibility={"evidence_snapshot_id": snap, "app_version": "11.15 verifier"},
            citations=registry.study_citations(sid).to_dict("records"),
            claims=registry.claims(sid).to_dict("records"),
            privacy_profile="Public package",
            redaction_options={"coordinates": True, "field_names": True, "genotypes": False, "researcher_names": True},
        )
        with zipfile.ZipFile(io.BytesIO(pkg)) as archive:
            names = set(archive.namelist())
            for required in [
                "manuscript/manuscript.md", "manuscript/manuscript.docx", "manuscript/manuscript.html",
                "reproducibility/reproducibility_manifest.json", "reproducibility/report_audit.csv",
                "reproducibility/redaction_report.json", "evidence/claim_ledger.csv", "README.txt",
            ]:
                assert required in names, required
            assert any(name.startswith("figures/figure_01_") and name.endswith(".svg") for name in names), "SVG figure missing from package"
            # DOCX is a valid OOXML ZIP container.
            with zipfile.ZipFile(io.BytesIO(archive.read("manuscript/manuscript.docx"))) as docx:
                assert "word/document.xml" in docx.namelist()
        registry.save_export(sid, package_type="Verification", privacy_profile="Public package", data=pkg, manifest={"verification": True}, version_id=version)
        assert len(registry.exports(sid)) == 1
        assert registry.integrity_check()["foreign_key_violations"] == 0


def migration_regression() -> None:
    from safe_data_migration import migrate
    with tempfile.TemporaryDirectory(prefix="agrolattice_11_15_migration_") as td:
        temp = Path(td)
        source = temp / "old_app"
        destination = temp / "new_app"
        source.mkdir(); destination.mkdir()
        # Source simulates 11.14: no reporting database.
        for rel in PROTECTED_HASHES:
            if not rel.endswith(".sqlite"):
                continue
            src = ROOT / rel
            target = source / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
            dest = destination / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
        report_src = ROOT / "reports/reporting.sqlite"
        report_dest = destination / "reports/reporting.sqlite"
        report_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(report_src, report_dest)
        before = sha(report_dest)
        migrate(source, destination)
        assert sha(report_dest) == before, "Migration from a pre-11.15 app must preserve the clean packaged reporting DB"
        db_health(report_dest)


def main() -> int:
    required = [
        "report_command_centre.py", "reporting_registry.py", "publication_builder.py", "agrolattice.py",
        "README_START_HERE_RELEASE11_15.txt", "USER_GUIDE_RELEASE_11_15.txt", "CHANGELOG_RELEASE_11_15.txt",
        "TECHNICAL_BASIS_REPORTING_11_15.md", "RELEASE_MANIFEST_11_15.json", "RESEARCH_METHODS_MANIFEST_11_15.json",
        "RUN_APP.bat", "safe_data_migration.py", "reports/reporting.sqlite",
    ]
    for item in required:
        assert (ROOT / item).exists(), item
    assert const_from_source(ROOT / "agrolattice.py", "APP_VERSION") == "20.15-release11.15-research-reporting-publication-command-centre"
    assert const_from_source(ROOT / "report_command_centre.py", "MODULE_VERSION") == "1.0.0"
    assert const_from_source(ROOT / "reporting_registry.py", "MODULE_VERSION") == "1.0.0"
    assert const_from_source(ROOT / "reporting_registry.py", "DB_SCHEMA_VERSION") == "1.0.0"
    assert const_from_source(ROOT / "publication_builder.py", "MODULE_VERSION") == "2.0.0"

    command = (ROOT / "report_command_centre.py").read_text(encoding="utf-8")
    app = (ROOT / "agrolattice.py").read_text(encoding="utf-8")
    for token in [
        "Report Builder", "Publications", "Tables & Figures", "Evidence & Claims", "Reproducibility", "Report Library",
        "Freeze current evidence", "Claim ledger", "Citation Library", "Build complete reproducibility package",
        "Internal research package", "Public package", "Report readiness", "Priority reporting issues",
    ]:
        assert token in command, token
    assert "st.tabs(" not in command, "11.15 Reports must use lazy top-level navigation, not eager Streamlit tabs"
    assert "render_report_command_centre" in app and "page_release10_reports" in app
    assert '"Study & publication builder": "All Tools / Legacy"' in app
    assert '"Statistics toolbox": "Climate & Earth Observation"' in app

    reporting = ROOT / "reports/reporting.sqlite"
    db_health(reporting)
    with sqlite3.connect(reporting) as conn:
        schema = conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0]
        assert schema == "1.0.0"
        for table in ["studies", "report_versions", "evidence_snapshots", "report_artifacts", "claims", "export_packages", "audit_log"]:
            assert conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] == 0, f"Synthetic records packaged in {table}"
        assert conn.execute("SELECT COUNT(*) FROM citations").fetchone()[0] >= 7, "Built-in method citations were not seeded"

    for rel, expected in PROTECTED_HASHES.items():
        path = ROOT / rel
        assert path.exists(), rel
        assert sha(path) == expected, f"Protected source changed unexpectedly: {rel}"
        if path.suffix == ".sqlite":
            db_health(path)

    run = (ROOT / "RUN_APP.bat").read_text(encoding="utf-8")
    for token in ["AGROLATTICE 11.15", "report_command_centre.py", "reporting_registry.py", "reports\\reporting.sqlite", "publication_builder.MODULE_VERSION == '2.0.0'", "reporting_registry.DB_SCHEMA_VERSION == '1.0.0'"]:
        assert token in run, token
    migration = (ROOT / "safe_data_migration.py").read_text(encoding="utf-8")
    assert 'RELEASE = "AGROLATTICE 11.15"' in migration
    assert 'Path("reports/reporting.sqlite")' in migration
    manifest = json.loads((ROOT / "RELEASE_MANIFEST_11_15.json").read_text(encoding="utf-8"))
    assert manifest["release"] == "AGROLATTICE 11.15"
    assert manifest["application_version"] == "20.15-release11.15-research-reporting-publication-command-centre"
    assert manifest["reporting_schema"].startswith("1.0.0")
    assert manifest["new_dependencies"] == []
    assert manifest["mechanistic_maize_model_changed"] is False

    # Requested k<=20 climate/PCA exploration remains present.
    assert "max_value=20" in app and "maximum_k = min(20, n_samples - 1, unique_profile_count)" in app
    assert 'st.slider("Colour by K-means clusters", 2, 20, 5' in app

    functional_reporting_regression()
    migration_regression()
    print("AGROLATTICE 11.15 verification passed")
    print("- Reporting registry 1.0.0 initialises cleanly with built-in citations and no synthetic reports")
    print("- Immutable report versions, evidence snapshots, artifacts, claims, citations and exports tested")
    print("- Publication ZIP and embedded DOCX OOXML validated")
    print("- Migration from pre-11.15 source preserves the packaged reporting DB")
    print("- All protected scientific databases and mechanistic maize source match 11.14 hashes")
    print("- k=2..20 climate/PCA exploration remains available")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
