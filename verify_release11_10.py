from __future__ import annotations

import hashlib
import json
import py_compile
import sqlite3
import sys
import tempfile
import types
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent

EXPECTED_UNCHANGED = {
    "field_operations/field_operations.sqlite": "fbf5ab2de711830a50bed5acfae84a86ec58efc45448d18ea7b88e04b4ff69b5",
    "pollination_lab/maize_flowering_trials.sqlite": "6dec74ccdb70bcffb9530bf08c6e36eba9827cef0790af0552e8ae4db0c1cd30",
    "agrolattice_twin/agrolattice_twin.sqlite": "ea5746651e6fb6c3de409ec8cf64d6e68409b40c0a7853f33982b2fb3f006bb4",
    "models_evidence/research_evidence.sqlite": "516b3361c1bca07b76da4f033dcd4ec693324d41d1924120fded88353600f58b",
    "maize_mechanistic_twin.py": "a62679f3aef1db8dfa4b459db8701cbf8502e7955b88daa520135b905e9400e8",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_sqlite(path: Path) -> None:
    con = sqlite3.connect(path)
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok", path
    assert con.execute("PRAGMA foreign_key_check").fetchall() == [], path
    con.close()


def stub_streamlit() -> types.ModuleType:
    class SessionState(dict):
        def __getattr__(self, name):
            try:
                return self[name]
            except KeyError as exc:
                raise AttributeError(name) from exc

        def __setattr__(self, name, value):
            self[name] = value

    st = types.ModuleType("streamlit")
    st.session_state = SessionState()
    sys.modules["streamlit"] = st
    return st


def climate_command_module_test() -> None:
    st = stub_streamlit()
    import climate_earth_command_centre as cc

    assert cc.MODULE_VERSION == "1.0.0"
    all_variables = [v for values in cc.VARIABLE_GROUPS.values() for v in values]
    assert len(all_variables) == 19
    assert len(set(all_variables)) == 19
    assert set(all_variables) == set(cc.VARIABLE_LABELS)

    locations = pd.DataFrame(
        {
            "CITY": ["Alpha", "Beta"],
            "STATE": ["North", "South"],
            "lat": [10.0, 20.0],
            "lng": [-70.0, -80.0],
            "Location": ["Alpha (North)", "Beta (South)"],
        }
    )
    field = {"centroid_lat": 10.01, "centroid_lon": -70.02, "field_id": "f1", "name": "Field A"}
    nearest = cc._nearest_location(field, locations)
    assert nearest and nearest["CITY"] == "Alpha"
    assert 0 <= float(nearest["distance_km"]) < 5

    climate = pd.DataFrame(
        {
            "CITY": ["Alpha", "Alpha", "Beta"],
            "STATE": ["North", "North", "South"],
            "Year": [2025, 2026, 2026],
            "Month": ["JANUARY", "FEBRUARY", "JANUARY"],
            "Variable": ["TEMPERATURE", "TEMPERATURE", "TEMPERATURE"],
            "Value": [20.0, 21.0, 25.0],
        }
    )
    subset1 = cc._location_subset(climate, "Alpha", "North", "Testland", 123)
    subset2 = cc._location_subset(climate, "Alpha", "North", "Testland", 123)
    assert len(subset1) == 2
    assert subset1 is subset2  # session-level location cache reused

    class FakeRegistry:
        def __init__(self):
            self.dataset = None
            self.acquisition = None

        def register_dataset(self, record):
            self.dataset = record
            return "dataset-1"

        def save_data_acquisition(self, record):
            self.acquisition = record
            return "acq-1"

    st.session_state["similarity_results"] = pd.DataFrame({"Location": ["B"], "Similarity": [0.91]})
    tempdir = Path(tempfile.mkdtemp())
    registry = FakeRegistry()
    saved = cc._save_session_analysis_bundle(
        registry=registry,
        artifact_dir=tempdir,
        field={"field_id": "f1", "name": "Field A", "crop": "Maize", "centroid_lat": 10.0, "centroid_lon": -70.0},
        country="Testland",
    )
    assert saved is not None
    dataset_id, path = saved
    assert dataset_id == "dataset-1" and path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert "climate_similarity" in payload["analyses"]
    assert registry.dataset["dataset_type"] == "Climate / Earth observation evidence snapshot"
    assert registry.acquisition["field_id"] == "f1"


def performance_runtime_test() -> None:
    from performance_runtime import build_country_runtime, dataset_status_from_frame

    tempdir = Path(tempfile.mkdtemp())
    cities = tempdir / "cities.csv"
    climate = tempdir / "climate.csv"
    pd.DataFrame(
        {
            "city_ascii": ["Alpha", "Beta", "Gamma"],
            "lat": [10.0, 20.0, 0.0],
            "lng": [-70.0, -80.0, 0.0],
            "country": ["Testland", "Testland", "Other"],
            "admin_name": ["North", "South", "Elsewhere"],
            "iso2": ["TL", "TL", "OT"],
            "iso3": ["TST", "TST", "OTH"],
        }
    ).to_csv(cities, index=False)
    pd.DataFrame(
        {
            "CITY": ["Alpha", "Alpha", "Beta", "Beta"],
            "STATE": ["North", "North", "South", "South"],
            "Year": [2025, 2026, 2025, 2026],
            "Month": ["JANUARY", "FEBRUARY", "JANUARY", "FEBRUARY"],
            "Variable": ["TEMPERATURE", "TEMPERATURE", "PRECIPITATION_AVG", "PRECIPITATION_AVG"],
            "Value": [20.0, 21.0, 3.0, 4.0],
        }
    ).to_csv(climate, index=False)
    runtime = build_country_runtime(cities, climate, "Testland")
    assert len(runtime.climate) == 4
    assert len(runtime.climate_locations) == 2
    assert runtime.status["locations"] == 2
    assert set(runtime.climate_locations["Location"]) == {"Alpha (North)", "Beta (South)"}
    status = dataset_status_from_frame(runtime.climate, path=climate, country="Testland", location_count=2)
    assert status["rows"] == 4 and status["locations"] == 2


def document_test() -> None:
    required = [
        "CHANGELOG_RELEASE_11_10.txt",
        "README_START_HERE_RELEASE11_10.txt",
        "USER_GUIDE_RELEASE_11_10.txt",
        "TECHNICAL_BASIS_CLIMATE_EO_11_10.md",
        "RELEASE_MANIFEST_11_10.json",
        "RESEARCH_METHODS_MANIFEST_11_10.json",
    ]
    for name in required:
        assert (ROOT / name).exists(), name
    manifest = json.loads((ROOT / "RELEASE_MANIFEST_11_10.json").read_text(encoding="utf-8"))
    assert manifest["release"] == "AGROLATTICE 11.10"
    assert manifest["database_schema_changes"] is False
    assert manifest["application_version"] == "20.10-release11.10-climate-earth-observation-command-centre"
    methods = json.loads((ROOT / "RESEARCH_METHODS_MANIFEST_11_10.json").read_text(encoding="utf-8"))
    assert methods["scientific_method_change"] is False


def main() -> None:
    ag = (ROOT / "agrolattice.py").read_text(encoding="utf-8")
    cc = (ROOT / "climate_earth_command_centre.py").read_text(encoding="utf-8")
    runtime = (ROOT / "performance_runtime.py").read_text(encoding="utf-8")
    run = (ROOT / "RUN_APP.bat").read_text(encoding="utf-8")

    assert '20.10-release11.10-climate-earth-observation-command-centre' in ag
    assert "render_climate_earth_command_centre" in ag
    assert "fetch_canonical_nasa_weather" in ag
    assert "_release11_10_quick_update_field_weather" in ag
    assert "_release11_10_quick_update_field_eo" in ag
    assert 'guide = data_dir / "USER_GUIDE_RELEASE_11_10.txt"' in ag
    assert "_release_artifact_version_key" in ag
    assert "climate_locations = _country_runtime.climate_locations" in ag
    assert 'MODULE_VERSION = "1.0.0"' in cc
    assert "climate_locations: pd.DataFrame" in runtime
    for view in ["Overview", "Field Climate", "Climate Comparison", "Spatial & Transferability", "Climate Risk", "Earth Observation", "Evidence & Data"]:
        assert view in cc, view
    for phrase in ["19-variable Field Climate Explorer", "gridded/location climate evidence", "Save current climate / EO evidence snapshot"]:
        assert phrase in cc, phrase
    assert "AGROLATTICE 11.10 - Climate & Earth Observation Command Centre" in run
    assert "climate_earth_command_centre.MODULE_VERSION == '1.0.0'" in run
    assert "'climate_locations' in performance_runtime.CountryRuntimeData.__dataclass_fields__" in run

    py_files = sorted(ROOT.glob("*.py"))
    for path in py_files:
        py_compile.compile(str(path), doraise=True)

    for relative, expected in EXPECTED_UNCHANGED.items():
        path = ROOT / relative
        assert sha(path) == expected, f"Protected artifact changed unexpectedly: {relative}"
        if relative.endswith(".sqlite"):
            assert_sqlite(path)

    document_test()
    climate_command_module_test()
    performance_runtime_test()

    print(f"PASS: AGROLATTICE 11.10 verification succeeded; {len(py_files)} top-level Python files compiled; protected databases unchanged.")


if __name__ == "__main__":
    main()
