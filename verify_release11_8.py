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

ROOT = Path(__file__).resolve().parent
SOURCE_ZIP = Path('/mnt/data/AGROLATTICE_Release_11_7_Research_Command_Centre_Home_Polish.zip')
SOURCE_ROOT = 'AGROLATTICE_Release_11_7_Research_Command_Centre/'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_sha(relative: str) -> str | None:
    if not SOURCE_ZIP.exists():
        return None
    with zipfile.ZipFile(SOURCE_ZIP) as zf:
        return hashlib.sha256(zf.read(SOURCE_ROOT + relative)).hexdigest()


def canonical_table(path: Path, table: str) -> str:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    rows = [dict(row) for row in con.execute(f'SELECT * FROM {table} ORDER BY rowid').fetchall()]
    con.close()
    return hashlib.sha256(json.dumps(rows, sort_keys=True, default=str).encode()).hexdigest()


def assert_sqlite(path: Path) -> None:
    con = sqlite3.connect(path)
    assert con.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', path
    assert con.execute('PRAGMA foreign_key_check').fetchall() == [], path
    con.close()


def stub_streamlit() -> None:
    st = types.ModuleType('streamlit')
    st.session_state = {}
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


def core_workflow_test() -> None:
    stub_streamlit()
    from field_operations_suite import FieldOperationsDatabase, evaluate_alert_rules
    from shapely.geometry import Polygon, mapping
    import pandas as pd

    tmp = Path(tempfile.mkdtemp())
    db = FieldOperationsDatabase(tmp / 'ops.sqlite')
    farm = db.create_farm('Research centre', 'Cyprus', entity_type='Agricultural research centre', geometry=mapping(Polygon([(33,35),(34,35),(34,36),(33,36)])))
    field = db.create_field(farm, 'Field A', mapping(Polygon([(33.1,35.1),(33.2,35.1),(33.2,35.2),(33.1,35.2)])), crop='Maize', variety='G1', season_year=2026, status='Active')
    db.save_season(field, 2026, 'Maize', genotype='G1', status='Active')
    task = db.create_task(field, 'Scout flowering', category='Phenology', due_date='2026-08-10', recurrence='Weekly')
    db.update_task_status(task, 'Completed', 'tester', 'complete')
    assert len(db.tasks(field)) == 2
    protocol = db.save_observation_protocol('Flowering', [{'name':'silking_pct','label':'Silking','unit':'%'}], category='Phenology')
    obs = db.create_observation(field, category='Phenology', latitude=35.15, longitude=33.15, created_by='tester')
    db.save_observation_details(obs, protocol_id=protocol, plant_tag='P1', measurements={'silking_pct': 50})
    assert db.detailed_observations(field).iloc[0]['plant_tag'] == 'P1'
    op = db.create_operation(field, operation_date='2026-08-10', category='Irrigation', water_mm=15)
    db.save_operation_details(op, record_type='Actual', purpose='Water', geometry=db.field(field)['geometry'])
    assert db.detailed_operations(field).iloc[0]['record_type'] == 'Actual'
    sensor = db.create_sensor(field, 'SM30', 'Soil moisture', depth_cm=30, latitude=35.15, longitude=33.15)
    db.save_sensor_details(sensor, installed_at='2026-08-01')
    db.add_sensor_calibration(sensor, '2026-08-05', method='reference', result='ok')
    assert len(db.sensor_calibrations(sensor)) == 1
    sample = db.add_nutrient_sample(field, sample_type='Soil', latitude=35.15, longitude=33.15, nitrogen=10)
    db.save_nutrient_sample_details(sample, external_sample_id='S1', depth_from_cm=0, depth_to_cm=30, laboratory='Lab')
    assert db.detailed_nutrient_samples(field).iloc[0]['external_sample_id'] == 'S1'
    points = pd.DataFrame([{'sample_id':'A','latitude':35.12,'longitude':33.12},{'sample_id':'B','latitude':35.18,'longitude':33.18}])
    assert db.save_sampling_points(field, points, 'Design', 'Random') == 2
    # isolate alert persistence test from default rules
    db.execute('UPDATE alert_rules SET enabled=0')
    rule = db.save_rule(name='Heat persistence', source='weather', metric='Tmax', operator='>=', threshold=35, severity='High', window_days=1, enabled=True, notes='')
    db.save_alert_rule_details(rule, persistence_count=2, cooldown_hours=24)
    assert evaluate_alert_rules(db, field, {'Tmax':36.0})['generated'] == 0
    assert evaluate_alert_rules(db, field, {'Tmax':36.0})['generated'] == 1
    assert evaluate_alert_rules(db, field, {'Tmax':36.0})['generated'] == 0
    assert_sqlite(tmp / 'ops.sqlite')


def main() -> None:
    ag = (ROOT / 'agrolattice.py').read_text(encoding='utf-8')
    fos = (ROOT / 'field_operations_suite.py').read_text(encoding='utf-8')
    fcc = (ROOT / 'field_command_centre.py').read_text(encoding='utf-8')
    run = (ROOT / 'RUN_APP.bat').read_text(encoding='utf-8')
    assert '20.8-release11.8-field-command-centre' in ag
    assert 'AGROLATTICE Release 11.8 · Field Command Centre' in ag
    assert 'render_field_command_centre' in ag
    assert 'MODULE_VERSION = "8.0.0"' in fos and 'DB_SCHEMA_VERSION = "8.0.0"' in fos
    assert 'MODULE_VERSION = "1.0.0"' in fcc
    for label in ['Overview','Map','Work & scouting','Operations','Sensors & samples','Crop health','Precision','History','Administration']:
        assert label in fcc
    for phrase in ['alert_rule_state','persistence_count','cooldown_hours','observation_protocols','sampling_points','record_type']:
        assert phrase in fos
    assert "field_operations_suite.MODULE_VERSION == '8.0.0'" in run
    assert "field_command_centre.MODULE_VERSION == '1.0.0'" in run

    py_files = sorted(ROOT.glob('*.py'))
    for path in py_files:
        py_compile.compile(str(path), doraise=True)

    field_db = ROOT / 'field_operations/field_operations.sqlite'
    backup = ROOT / 'field_operations/backups/pre_11_8_field_operations.sqlite'
    assert field_db.exists() and backup.exists()
    assert_sqlite(field_db)
    assert_sqlite(backup)
    core = ['farms','fields','crop_history','users','field_access','tasks','observations','operations','sensors','sensor_readings','nutrient_samples','alert_rules','alerts','prescriptions','audit_log']
    for table in core:
        assert canonical_table(field_db, table) == canonical_table(backup, table), table
    con = sqlite3.connect(field_db)
    ext = ['field_seasons','task_details','observation_protocols','observation_details','operation_details','sensor_details','sensor_calibrations','nutrient_sample_details','alert_rule_details','alert_details','alert_rule_state','sampling_points']
    for table in ext:
        assert con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone(), table
        assert con.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] == 0, table
    con.close()

    unchanged = {
        'pollination_lab/maize_flowering_trials.sqlite': ROOT / 'pollination_lab/maize_flowering_trials.sqlite',
        'agrolattice_twin/agrolattice_twin.sqlite': ROOT / 'agrolattice_twin/agrolattice_twin.sqlite',
        'models_evidence/research_evidence.sqlite': ROOT / 'models_evidence/research_evidence.sqlite',
        'maize_mechanistic_twin.py': ROOT / 'maize_mechanistic_twin.py',
    }
    for relative, local in unchanged.items():
        src = source_sha(relative)
        if src is not None:
            assert src == sha(local), relative
    src_field = source_sha('field_operations/field_operations.sqlite')
    if src_field is not None:
        assert src_field == sha(backup)

    for db_path in [ROOT/'pollination_lab/maize_flowering_trials.sqlite', ROOT/'agrolattice_twin/agrolattice_twin.sqlite', ROOT/'models_evidence/research_evidence.sqlite']:
        assert_sqlite(db_path)

    core_workflow_test()
    print(f'PASS: AGROLATTICE 11.8 verification succeeded; {len(py_files)} top-level Python files compiled.')


if __name__ == '__main__':
    main()
