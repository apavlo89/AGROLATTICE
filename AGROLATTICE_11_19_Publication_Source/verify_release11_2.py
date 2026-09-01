"""Regression verification for AGROLATTICE 11.2 spatial and upgrade integrity."""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pandas as pd

from maize_pollination_lab import PollinationDatabase, PollinationLabError
from safe_data_migration import migrate


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def square(x0: float, y0: float, size: float = 0.001) -> dict:
    return {
        "type": "Polygon",
        "coordinates": [[[x0, y0], [x0 + size, y0], [x0 + size, y0 + size], [x0, y0 + size], [x0, y0]]],
    }


def create_trial(db: PollinationDatabase, geometry: dict, *, name: str = "AGROLATTICE 11.2 safeguard test") -> str:
    return db.create_trial({
        "name": name, "site_name": "Test site", "season_year": 2027,
        "female_parent_levels": ["F01"], "male_parent_levels": ["M01"],
        "parent_pairing_mode": "All female × male combinations",
        "sowing_density_levels": [65000], "sowing_date_levels": ["2027-04-01"],
        "sowing_offset_levels": [0], "female_sowing_date": "2027-04-01",
        "design_type": "Randomised complete block", "blocks": 1, "replicates_per_treatment": 1,
        "row_ratio": "4:2", "primary_outcome": "Flowering overlap score",
        "base_temperature_c": 10, "upper_temperature_c": 30, "field_geometry": geometry,
        "status": "Active",
    })


def plot_row(geometry: dict) -> dict:
    return {
        "plot_label": "B01-U001", "experiment_plot_label": "B01", "treatment_unit_label": "B01-U001",
        "block": 1, "replicate": 1, "treatment_label": "T001", "male_sowing_offset_days": 0,
        "sowing_density_plants_ha": 65000, "female_parent": "F01", "male_parent": "M01",
        "parent_combination": "F01 × M01", "sowing_date": "2027-04-01",
        "female_sowing_date": "2027-04-01", "male_sowing_date": "2027-04-01", "geometry": geometry,
    }


def verify_exact_match_and_relink_guard() -> None:
    with tempfile.TemporaryDirectory(prefix="agrolattice11_2-spatial-") as temporary:
        db = PollinationDatabase(Path(temporary) / "pollination_lab" / "maize_flowering_trials.sqlite")
        outer = square(-98.90, 19.45, 0.004)
        trial_id = create_trial(db, outer)
        db.update_trial_spatial_link(
            trial_id, source_field_id="FIELD-A", source_field_geometry=outer,
            boundary_mode="Exact mapped field", trial_geometry=outer,
        )
        status = db.spatial_link_status(trial_id, {"geometry": outer})
        require("exact_match" in status and status["exact_match"] is True, "Exact geometry status is missing or wrong.")

        unit = square(-98.899, 19.451, 0.001)
        db.replace_plots(trial_id, [plot_row(unit)])
        before = db.get_trial(trial_id)
        too_small = square(-98.90, 19.45, 0.0005)
        try:
            db.update_trial_spatial_link(
                trial_id, source_field_id="FIELD-B", source_field_geometry=too_small,
                boundary_mode="Exact mapped field", trial_geometry=too_small,
            )
        except PollinationLabError:
            pass
        else:
            raise AssertionError("Spatial re-link was allowed even though saved treatment units would fall outside.")
        after = db.get_trial(trial_id)
        require(after.get("source_field_id") == before.get("source_field_id"), "Blocked spatial re-link changed source field.")
        require(after.get("field_geometry") == before.get("field_geometry"), "Blocked spatial re-link changed trial geometry.")


def verify_protected_trial_delete() -> None:
    with tempfile.TemporaryDirectory(prefix="agrolattice11_2-delete-") as temporary:
        db = PollinationDatabase(Path(temporary) / "pollination_lab" / "maize_flowering_trials.sqlite")
        outer = square(-98.90, 19.45, 0.004)
        trial_name = "Deletion protection trial"
        trial_id = create_trial(db, outer, name=trial_name)
        db.replace_plots(trial_id, [plot_row(square(-98.899, 19.451, 0.001))])
        inserted, issues = db.upsert_leaf_observations(trial_id, pd.DataFrame([{
            "Plot": "B01-U001", "Observation date": "2027-04-25", "Plant tag": "F-P1",
            "Parent role": "Female", "Collared leaf number": 4,
        }]))
        require(inserted == 1 and not issues, "Could not create deletion-protection observation.")
        counts = db.trial_deletion_counts(trial_id)
        require(counts["Treatment units"] == 1 and counts["Leaf/ear observations"] == 1, "Deletion impact counts are wrong.")
        try:
            db.delete_trial(trial_id)
        except PollinationLabError:
            pass
        else:
            raise AssertionError("Data-bearing trial was hard-deleted without explicit cascade confirmation.")
        db.update_trial_status(trial_id, "Archived")
        require(db.get_trial(trial_id)["status"] == "Archived", "Archive status did not persist.")
        try:
            db.delete_trial(trial_id, confirmation_name="wrong", allow_cascade=True)
        except PollinationLabError:
            pass
        else:
            raise AssertionError("Hard delete accepted the wrong typed trial name.")
        db.delete_trial(trial_id, confirmation_name=trial_name, allow_cascade=True)
        try:
            db.get_trial(trial_id)
        except PollinationLabError:
            pass
        else:
            raise AssertionError("Explicitly confirmed hard delete did not remove the trial.")


def make_simple_db(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE records(id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("INSERT INTO records(value) VALUES(?)", (value,))
        conn.commit()


def read_value(path: Path) -> str:
    with sqlite3.connect(path) as conn:
        return str(conn.execute("SELECT value FROM records ORDER BY id LIMIT 1").fetchone()[0])


def verify_source_authoritative_migration() -> None:
    with tempfile.TemporaryDirectory(prefix="agrolattice11_2-migrate-") as temporary:
        root = Path(temporary)
        source = root / "source"
        destination = root / "destination"
        for relative in (
            Path("field_operations/field_operations.sqlite"),
            Path("pollination_lab/maize_flowering_trials.sqlite"),
            Path("agrolattice_twin/agrolattice_twin.sqlite"),
        ):
            make_simple_db(source / relative, "LIVE-SOURCE")
            make_simple_db(destination / relative, "PACKAGED-DESTINATION")
        (source / "analysis_history.json").write_text('{"source": true}', encoding="utf-8")
        backup = migrate(source, destination)
        require(backup.exists(), "Migration backup folder was not created.")
        for relative in (
            Path("field_operations/field_operations.sqlite"),
            Path("pollination_lab/maize_flowering_trials.sqlite"),
            Path("agrolattice_twin/agrolattice_twin.sqlite"),
        ):
            require(read_value(destination / relative) == "LIVE-SOURCE", f"Source DB did not replace packaged DB: {relative}")
            require(read_value(backup / "destination_before" / relative) == "PACKAGED-DESTINATION", f"Destination backup missing: {relative}")
            require(read_value(backup / "source_snapshot" / relative) == "LIVE-SOURCE", f"Source snapshot missing: {relative}")
        require((backup / "migration_report.json").exists(), "Migration report was not written.")
        require((destination / "analysis_history.json").read_text(encoding="utf-8") == '{"source": true}', "User config was not migrated.")


def main() -> None:
    verify_exact_match_and_relink_guard()
    verify_protected_trial_delete()
    verify_source_authoritative_migration()
    print("AGROLATTICE 11.2 spatial and upgrade integrity verification passed")


if __name__ == "__main__":
    main()
