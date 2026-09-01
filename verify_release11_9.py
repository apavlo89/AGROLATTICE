from __future__ import annotations

import hashlib
import json
import py_compile
import sqlite3
import sys
import tempfile
import types
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent

EXPECTED_UNCHANGED = {
    'field_operations/field_operations.sqlite': 'fbf5ab2de711830a50bed5acfae84a86ec58efc45448d18ea7b88e04b4ff69b5',
    'pollination_lab/maize_flowering_trials.sqlite': '6dec74ccdb70bcffb9530bf08c6e36eba9827cef0790af0552e8ae4db0c1cd30',
    'models_evidence/research_evidence.sqlite': '516b3361c1bca07b76da4f033dcd4ec693324d41d1924120fded88353600f58b',
    'maize_mechanistic_twin.py': 'a62679f3aef1db8dfa4b459db8701cbf8502e7955b88daa520135b905e9400e8',
}
EXPECTED_PRE_11_9_TWIN = '2c36a232474b494f2dcef8cf1f4561cc4c94b291ae85752db3f54f1f3c131d2a'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_sqlite(path: Path) -> None:
    con = sqlite3.connect(path)
    assert con.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', path
    assert con.execute('PRAGMA foreign_key_check').fetchall() == [], path
    con.close()


def rows(path: Path, table: str) -> list[dict]:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    result = [dict(row) for row in con.execute(f'SELECT * FROM {table} ORDER BY rowid').fetchall()]
    con.close()
    return result


def stub_streamlit() -> None:
    class SessionState(dict):
        def __getattr__(self, name):
            try:
                return self[name]
            except KeyError as exc:
                raise AttributeError(name) from exc
        def __setattr__(self, name, value):
            self[name] = value

    st = types.ModuleType('streamlit')
    st.session_state = SessionState()
    comp_pkg = types.ModuleType('streamlit.components')
    comp_v1 = types.ModuleType('streamlit.components.v1')
    comp_v1.declare_component = lambda *a, **k: (lambda **kwargs: None)
    comp_pkg.v1 = comp_v1
    sys.modules['streamlit'] = st
    sys.modules['streamlit.components'] = comp_pkg
    sys.modules['streamlit.components.v1'] = comp_v1
    sf = types.ModuleType('streamlit_folium')
    sf.st_folium = lambda *a, **k: {}
    sys.modules['streamlit_folium'] = sf


def mechanistic_integration_test() -> None:
    stub_streamlit()
    from agrolattice_twin import build_twin_state
    import twin_command_centre as twin_cc
    assert twin_cc.MODULE_VERSION == '1.0.0'
    from maize_mechanistic_twin import DEFAULT_PHYSIOLOGY, parameter_thermal_targets

    weather = pd.DataFrame({
        'Date': pd.date_range('2026-04-01', periods=180, freq='D'),
        'T2M_MIN': np.full(180, 15.0),
        'T2M_MAX': np.full(180, 25.0),
        'PRECTOTCORR': np.zeros(180),
    })
    trial = {
        'name': 'Synthetic synchrony trial',
        'female_sowing_date': '2026-04-01',
        'male_parent': 'M1', 'female_parent': 'F1',
        'base_temperature_c': 10.0, 'upper_temperature_c': 30.0,
    }
    plots = pd.DataFrame({'Male sowing': ['2026-04-03', '2026-04-03']})
    kwargs = dict(
        context={}, field={'name': 'Field A', 'crop': 'Maize'}, trial=trial,
        plots=plots, observations=pd.DataFrame(), harvest=pd.DataFrame(),
        trial_weather=weather, twin_weather=None, root_zone=pd.DataFrame(),
        satellite=pd.DataFrame(), sensors=pd.DataFrame(), sensor_readings=pd.DataFrame(),
        tasks=pd.DataFrame(), alerts=pd.DataFrame(), settings={}, as_of='2026-06-10',
        male_physiology=DEFAULT_PHYSIOLOGY, female_physiology=DEFAULT_PHYSIOLOGY,
        male_physiology_source='Publication prior', female_physiology_source='Publication prior',
    )
    state, _, manifest = build_twin_state(**kwargs)
    targets = parameter_thermal_targets(DEFAULT_PHYSIOLOGY)
    assert state['Phenology model'] == 'Mechanistic maize'
    assert abs(float(state['Male target GDD']) - targets['Planting GDD to anthesis']) < 1e-9
    assert abs(float(state['Female target GDD']) - targets['Planting GDD to silking']) < 1e-9
    assert state['Predicted male 50% flowering'] and state['Predicted female 50% silking']
    assert state['Mechanistic maize DOI'] == '10.1002/csc2.21453'
    assert manifest['phenology_model'] == 'Mechanistic maize'
    assert abs(float(state['Rain last 7 days (mm)'])) < 1e-12
    assert np.isfinite(float(state['Mean temperature last 7 days (°C)']))

    fallback, _, _ = build_twin_state(
        context={}, field={'name': 'Field B', 'crop': 'Wheat'}, trial=None,
        plots=pd.DataFrame(), observations=pd.DataFrame(), harvest=pd.DataFrame(),
        trial_weather=weather, twin_weather=None, root_zone=pd.DataFrame(), satellite=pd.DataFrame(),
        sensors=pd.DataFrame(), sensor_readings=pd.DataFrame(), tasks=pd.DataFrame(), alerts=pd.DataFrame(),
        settings={}, as_of='2026-06-10',
    )
    assert fallback['Phenology model'] == 'Legacy transparent GDD target'
    assert float(fallback['Male target GDD']) == 650.0
    assert float(fallback['Female target GDD']) == 670.0


def twin_db_test() -> None:
    from agrolattice_twin import AgroLatticeTwinDatabase
    tmp = Path(tempfile.mkdtemp()) / 'twin.sqlite'
    db = AgroLatticeTwinDatabase(tmp)
    link = db.save_link(name='Test Twin', field_id='field-1', trial_id='trial-1', notes='test')
    eid = db.log_event(link, event_type='Observation', title='Observed flowering', event_time='2026-08-10', details={'x': 1})
    assert eid and len(db.events(link)) == 1
    cid = db.save_calibration_run(link, parent_name='M1', role='Male', prior={'tln':19}, fitted={'tln':18.5}, diagnostics={'rmse':1.2})
    assert cid and len(db.calibration_runs(link)) == 1
    aid = db.save_analogue_season(link, name='Analogue A', source='test', data={'site':'X','year':2020})
    assert aid and len(db.analogue_seasons(link)) == 1
    package = db.export_package(link)
    with zipfile.ZipFile(__import__('io').BytesIO(package)) as zf:
        names = set(zf.namelist())
        for expected in ['twin_events.csv','calibration_runs.csv','analogue_seasons.csv']:
            assert expected in names, expected
    assert_sqlite(tmp)


def pollination_clean_schema_test() -> None:
    from maize_pollination_lab import PollinationDatabase
    tmp = Path(tempfile.mkdtemp()) / 'pollination.sqlite'
    db = PollinationDatabase(tmp)
    con = sqlite3.connect(tmp)
    names = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    con.close()
    for expected in ['parent_physiology','leaf_development_observations','plot_phenology_events']:
        assert expected in names, expected


def main() -> None:
    ag = (ROOT / 'agrolattice.py').read_text(encoding='utf-8')
    twin = (ROOT / 'agrolattice_twin.py').read_text(encoding='utf-8')
    cc = (ROOT / 'twin_command_centre.py').read_text(encoding='utf-8')
    run = (ROOT / 'RUN_APP.bat').read_text(encoding='utf-8')
    assert '20.9-release11.9-persistent-twin-command-centre' in ag
    assert 'render_twin_command_centre' in ag
    assert 'MODULE_VERSION = "3.0.0"' in twin and 'DB_SCHEMA_VERSION = "3.0.0"' in twin
    assert 'MODULE_VERSION = "1.0.0"' in cc
    for label in ['Overview','Spatial Twin','Development & water','Timeline','Scenarios','Measurements & copilot','Evidence & validation','Setup']:
        assert label in cc, label
    for phrase in ['Mechanistic maize','Model disagreement','Calibration Assistant' if False else 'Fit prior-regularised local physiology','Recommendation → Action → Outcome','Persistent Twin state chain']:
        assert phrase in (cc + twin), phrase
    assert "agrolattice_twin.MODULE_VERSION == '3.0.0'" in run
    assert "twin_command_centre.MODULE_VERSION == '1.0.0'" in run

    py_files = sorted(ROOT.glob('*.py'))
    for path in py_files:
        py_compile.compile(str(path), doraise=True)

    # Protected databases and disclosed mechanistic biology remain byte-for-byte unchanged.
    for relative, expected in EXPECTED_UNCHANGED.items():
        assert sha(ROOT / relative) == expected, relative
        if relative.endswith('.sqlite'):
            assert_sqlite(ROOT / relative)

    twin_db = ROOT / 'agrolattice_twin/agrolattice_twin.sqlite'
    backup = ROOT / 'agrolattice_twin/backups/pre_11_9_agrolattice_twin.sqlite'
    assert sha(backup) == EXPECTED_PRE_11_9_TWIN
    assert_sqlite(twin_db)
    assert_sqlite(backup)

    legacy_tables = ['model_registry','recommendations','scenarios','snapshots','twin_links','twin_root_zone','twin_satellite','twin_settings','twin_weather']
    for table in legacy_tables:
        assert rows(twin_db, table) == rows(backup, table), table
    old_meta = {r['key']:r['value'] for r in rows(backup,'metadata')}
    new_meta = {r['key']:r['value'] for r in rows(twin_db,'metadata')}
    for key, value in old_meta.items():
        if key != 'schema_version':
            assert new_meta.get(key) == value, key
    assert new_meta.get('schema_version') == '3.0.0'
    con = sqlite3.connect(twin_db)
    for table in ['twin_events','calibration_runs','analogue_seasons']:
        assert con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone(), table
        assert con.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] == 0, table
    con.close()

    mechanistic_integration_test()
    twin_db_test()
    pollination_clean_schema_test()
    print(f'PASS: AGROLATTICE 11.9 verification succeeded; {len(py_files)} top-level Python files compiled.')


if __name__ == '__main__':
    main()
