"""Regression and performance verification for AGROLATTICE 11.6."""
from __future__ import annotations

import ast
import hashlib
import json
import tempfile
import time
from pathlib import Path

import pandas as pd
from PIL import Image

import global_country_support
import maize_mechanistic_twin
from performance_runtime import MODULE_VERSION as PERFORMANCE_MODULE_VERSION, build_country_runtime, file_signature
from verify_release11_5 import (
    verify_registry_and_acquisition,
    verify_11_4_to_11_5_registry_migration,
    verify_research_data_hub_and_phenology,
    verify_pest_paper_equations_and_fold_resampling,
    verify_adaptive_fusion,
    verify_hybrid_residual,
    verify_weak_supervision,
    verify_gxem_builder,
    verify_loyo_and_applicability,
    verify_decision_registry_records,
    verify_pareto_and_state_assimilation,
    verify_irrigation_policy_studio_engine,
    verify_nutrient_response_engine,
    verify_causal_audit_categorical_and_grouped,
    verify_source_authoritative_migration,
)


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
    root = Path(__file__).resolve().parent
    tree = ast.parse((root / filename).read_text(encoding="utf-8"), filename=filename)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"Could not find {name} in {filename}")


def verify_runtime_equivalence_and_signatures() -> None:
    with tempfile.TemporaryDirectory(prefix="agrolattice11_6-runtime-") as td:
        root = Path(td)
        cities = pd.DataFrame([
            {"city": "One", "city_ascii": "One", "lat": 10.0, "lng": 20.0, "country": "Testland", "iso2": "TL", "iso3": "TST", "admin_name": "North", "capital": "", "population": 1, "id": 1},
            {"city": "Two", "city_ascii": "Two", "lat": 11.0, "lng": 21.0, "country": "Testland", "iso2": "TL", "iso3": "TST", "admin_name": "South", "capital": "", "population": 1, "id": 2},
        ])
        climate = pd.DataFrame([
            {"CITY": " One ", "STATE": "North", "Year": "2025", "Month": "january", "Variable": "temperature", "Value": "20.5"},
            {"CITY": "Two", "STATE": "South", "Year": 2025, "Month": "JANUARY", "Variable": "PRECIPITATION_AVG", "Value": 4.25},
        ])
        city_path = root / "worldcities.csv"; climate_path = root / "agroclimate_longformat.csv"
        cities.to_csv(city_path, index=False); climate.to_csv(climate_path, index=False)
        before = file_signature(climate_path)
        runtime = build_country_runtime(city_path, climate_path, "Testland")
        require(runtime.climate is runtime.merged, "Fully matched standard data should not duplicate the entire climate frame.")
        require(runtime.status["rows"] == 2 and runtime.status["locations"] == 2, "Runtime status is inconsistent.")
        require(runtime.variables == ["PRECIPITATION_AVG", "TEMPERATURE"], "Variable normalisation changed.")
        require(runtime.climate["CITY"].tolist() == ["One", "Two"], "CITY cleaning changed.")
        require(runtime.climate["Month"].tolist() == ["JANUARY", "JANUARY"], "Month cleaning changed.")
        require(runtime.climate["lat"].tolist() == [10.0, 11.0], "Coordinate attachment failed.")
        time.sleep(0.002)
        with climate_path.open("a", encoding="utf-8") as handle:
            handle.write("\n")
        after = file_signature(climate_path)
        require((before.size_bytes, before.mtime_ns) != (after.size_bytes, after.mtime_ns), "File signature did not detect a source change.")


def verify_settings_write_optimisation() -> None:
    with tempfile.TemporaryDirectory(prefix="agrolattice11_6-settings-") as td:
        root = Path(td)
        payload = {"active_country": "Mexico", "restrict_map_search_to_country": True, "map_search_enabled": True}
        path = global_country_support.save_settings(root, payload)
        first = path.stat().st_mtime_ns
        time.sleep(0.01)
        global_country_support.save_settings(root, payload)
        second = path.stat().st_mtime_ns
        require(first == second, "Unchanged country settings were rewritten to disk.")
        changed = dict(payload); changed["map_search_enabled"] = False
        time.sleep(0.01)
        global_country_support.save_settings(root, changed)
        require(path.stat().st_mtime_ns != second, "Changed country settings were not persisted.")
        require(global_country_support.MODULE_VERSION == "10.3.0", "Global country module version was not advanced.")


def verify_brand_assets() -> None:
    root = Path(__file__).resolve().parent
    logo = root / "assets" / "brand" / "agrolattice_logo.png"
    icon = root / "assets" / "brand" / "agrolattice_icon.png"
    source = root / "assets" / "brand" / "agrolattice_logo_source.png"
    for path in (logo, icon, source):
        require(path.exists() and path.stat().st_size > 1000, f"Brand asset missing/empty: {path}")
        with Image.open(path) as image:
            image.verify()
    with Image.open(logo) as image:
        require(image.width > image.height and image.mode == "RGBA", "Horizontal transparent logo is malformed.")
    with Image.open(icon) as image:
        require(image.size == (512, 512) and image.mode == "RGBA", "Compact icon is malformed.")


def verify_source_level_performance_guards() -> None:
    root = Path(__file__).resolve().parent
    source = (root / "agrolattice.py").read_text(encoding="utf-8")
    require("country_dataset_status(data_dir, selected_country)" not in source, "Top-level full CSV status reread returned.")
    require("@st.cache_resource" in source and "_load_country_runtime_resource" in source, "Active-country resource cache is missing.")
    for name in ("_pollination_db_resource", "_field_operations_db_resource", "_twin_db_resource", "_research_registry_resource"):
        require(name in source, f"Database service cache missing: {name}")
    require("PERFORMANCE_RUNTIME_SUMMARY" in source and "Performance & navigation cache" in source, "Performance diagnostics are missing.")
    require("st.logo" in source and "agrolattice_logo.png" in source, "App logo integration is missing.")
    require(literal("agrolattice.py", "APP_VERSION") == "20.6-release11.6-performance-branding", "Application version is not 11.6.")
    require(PERFORMANCE_MODULE_VERSION == "1.0.0", "Unexpected performance-runtime module version.")


def verify_protected_invariants() -> None:
    root = Path(__file__).resolve().parent
    expected = {
        "field_operations/field_operations.sqlite": "e1b2c1e4efe8a846a3fb6563262abcbd59d7ad2e057e70adb3bad3d03041f525",
        "pollination_lab/maize_flowering_trials.sqlite": "6dec74ccdb70bcffb9530bf08c6e36eba9827cef0790af0552e8ae4db0c1cd30",
        "agrolattice_twin/agrolattice_twin.sqlite": "2c36a232474b494f2dcef8cf1f4561cc4c94b291ae85752db3f54f1f3c131d2a",
        "models_evidence/research_evidence.sqlite": "516b3361c1bca07b76da4f033dcd4ec693324d41d1924120fded88353600f58b",
        "maize_mechanistic_twin.py": "a62679f3aef1db8dfa4b459db8701cbf8502e7955b88daa520135b905e9400e8",
    }
    for relative, digest in expected.items():
        require(sha256(root / relative) == digest, f"11.5 invariant changed unexpectedly: {relative}")
    require(maize_mechanistic_twin.EMERGENCE_GDD == 30.6, "Emergence GDD changed.")
    require(maize_mechanistic_twin.EAR_GROWTH_LEAF_FRACTION == 0.67, "Ear-growth fraction changed.")
    require(maize_mechanistic_twin.ANTHESIS_AFTER_FINAL_LEAF_GDD == 40.0, "Anthesis offset changed.")
    require(literal("maize_pollination_lab.py", "DB_SCHEMA_VERSION") == "2.0.0", "Pollination DB schema changed.")
    require(literal("agrolattice_twin.py", "DB_SCHEMA_VERSION") == "2.3.0", "Twin DB schema changed.")


def verify_release_files() -> None:
    root = Path(__file__).resolve().parent
    required = [
        "RELEASE_MANIFEST_11_6.json", "RESEARCH_METHODS_MANIFEST_11_6.json", "CHANGELOG_RELEASE_11_6.txt",
        "README_START_HERE_RELEASE11_6.txt", "USER_GUIDE_RELEASE_11_6.txt", "TECHNICAL_BASIS_PERFORMANCE_11_6.md",
        "performance_runtime.py", "assets/brand/agrolattice_logo.png", "assets/brand/agrolattice_icon.png",
    ]
    for filename in required:
        require((root / filename).exists(), f"Required 11.6 file missing: {filename}")
    manifest = json.loads((root / "RELEASE_MANIFEST_11_6.json").read_text(encoding="utf-8"))
    require(manifest["release"] == "AGROLATTICE 11.6", "Release manifest has wrong version.")
    require(manifest["protected_database_schema_changes"] is False and manifest["database_schema_changes"] is False, "11.6 must not claim a DB schema change.")
    require(manifest["mechanistic_maize_model_changed"] is False, "11.6 must not claim a Mechanistic Maize change.")
    run_app = (root / "RUN_APP.bat").read_text(encoding="utf-8")
    require("performance_runtime.py" in run_app and "agrolattice_logo.png" in run_app, "RUN_APP preflight omits performance/brand assets.")
    require("global_country_support.MODULE_VERSION == '10.3.0'" in run_app, "RUN_APP expects wrong country-support version.")


def main() -> None:
    # Carry forward the complete scientific/decision regression suite from 11.5.
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
    verify_source_authoritative_migration()

    verify_runtime_equivalence_and_signatures()
    verify_settings_write_optimisation()
    verify_brand_assets()
    verify_source_level_performance_guards()
    verify_protected_invariants()
    verify_release_files()
    print("AGROLATTICE 11.6 Performance & Branding verification passed")


if __name__ == "__main__":
    main()
