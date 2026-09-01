"""Regression verification for AGROLATTICE 11.1 research-integrity safeguards."""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pandas as pd

from field_operations_suite import FieldOperationsDatabase
from maize_pollination_lab import (
    PollinationDatabase,
    PollinationLabError,
    compute_plot_synchrony_metrics,
    randomised_plot_assignments,
    validate_treatment_unit_geometries,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def square(x0: float, y0: float, size: float = 0.001) -> dict:
    return {
        "type": "Polygon",
        "coordinates": [[
            [x0, y0], [x0 + size, y0], [x0 + size, y0 + size],
            [x0, y0 + size], [x0, y0],
        ]],
    }


def create_trial(db: PollinationDatabase, geometry: dict, *, source_field_id: str | None = None) -> str:
    return db.create_trial({
        "name": "AGROLATTICE 11.1 safeguard test", "site_name": "Test site", "season_year": 2027,
        "female_parent_levels": ["F01"], "male_parent_levels": ["M01"],
        "parent_pairing_mode": "All female × male combinations",
        "sowing_density_levels": [65000], "sowing_date_levels": ["2027-04-01"],
        "sowing_offset_levels": [0], "female_sowing_date": "2027-04-01",
        "design_type": "Randomised complete block", "blocks": 1, "replicates_per_treatment": 1,
        "row_ratio": "4:2", "primary_outcome": "Flowering overlap score",
        "base_temperature_c": 10, "upper_temperature_c": 30, "field_geometry": geometry,
        "source_field_id": source_field_id, "status": "Active",
    })


def plot_row(geometry: dict, *, treatment: str = "T001") -> dict:
    return {
        "plot_label": "B01-U001", "experiment_plot_label": "B01", "treatment_unit_label": "B01-U001",
        "block": 1, "replicate": 1, "treatment_label": treatment, "male_sowing_offset_days": 0,
        "sowing_density_plants_ha": 65000, "female_parent": "F01", "male_parent": "M01",
        "parent_combination": "F01 × M01", "sowing_date": "2027-04-01",
        "female_sowing_date": "2027-04-01", "male_sowing_date": "2027-04-01", "geometry": geometry,
    }


def verify_overlap_guard() -> None:
    g = square(-98.90, 19.45)
    try:
        validate_treatment_unit_geometries([g, g], field_geometry=g)
    except PollinationLabError:
        pass
    else:
        raise AssertionError("Duplicate/overlapping treatment-unit polygons were accepted.")

    adjacent = square(-98.899, 19.45)
    validate_treatment_unit_geometries([g, adjacent])


def verify_non_destructive_randomisation_and_atomicity() -> None:
    field = square(-98.90, 19.45, 0.004)
    unit = square(-98.8995, 19.4505, 0.001)
    with tempfile.TemporaryDirectory(prefix="agrolattice11_1-") as temporary:
        root = Path(temporary)
        db = PollinationDatabase(root / "pollination_lab" / "maize_flowering_trials.sqlite")
        trial_id = create_trial(db, field)
        db.replace_plots(trial_id, [plot_row(unit)])
        original_plot_id = str(db.list_plots(trial_id).iloc[0]["Plot ID"])

        # Before data collection, a same-labelled re-save preserves the stable experimental-unit ID.
        db.replace_plots(trial_id, [plot_row(square(-98.8994, 19.4506, 0.001), treatment="T001-resaved")])
        require(str(db.list_plots(trial_id).iloc[0]["Plot ID"]) == original_plot_id,
                "Plot ID changed during a safe pre-observation map update.")

        inserted, issues = db.upsert_leaf_observations(trial_id, pd.DataFrame([{
            "Plot": "B01-U001", "Observation date": "2027-04-25", "Plant tag": "F-P1",
            "Parent role": "Female", "Collared leaf number": 4,
        }]))
        require(inserted == 1 and not issues, "Could not create safeguard observation.")
        try:
            db.replace_plots(trial_id, [plot_row(unit, treatment="T999")])
        except PollinationLabError:
            pass
        else:
            raise AssertionError("Re-randomisation was allowed after plot-linked data collection.")
        require(len(db.leaf_observations(trial_id)) == 1, "Collected leaf data were lost after blocked re-randomisation.")

        # Factor design cannot be changed separately once a plot map exists.
        try:
            db.update_trial_factor_design(
                trial_id,
                female_parent_levels=["F01"], male_parent_levels=["M01"],
                parent_pairings=[{"female_parent": "F01", "male_parent": "M01"}],
                parent_pairing_mode="All female × male combinations",
                sowing_density_levels=[70000], sowing_date_levels=["2027-04-01"], sowing_offset_levels=[0],
            )
        except PollinationLabError:
            pass
        else:
            raise AssertionError("Factor metadata changed independently of an existing mapped design.")

        # Atomic save: malformed spatial data must leave factor metadata unchanged.
        trial_before = db.get_trial(trial_id)
        try:
            db.save_factor_design_and_plots(
                trial_id, [plot_row(unit)],
                female_parent_levels=["F01"], male_parent_levels=["M01"],
                parent_pairings=[{"female_parent": "F01", "male_parent": "M01"}],
                parent_pairing_mode="All female × male combinations",
                sowing_density_levels=[72000], sowing_date_levels=["2027-04-01"], sowing_offset_levels=[0],
            )
        except PollinationLabError:
            # Expected because scientific data lock the design before any write.
            pass
        require(db.get_trial(trial_id)["sowing_density_levels"] == trial_before["sowing_density_levels"],
                "Factor metadata changed despite a blocked atomic design save.")


def verify_cross_database_delete_guards() -> None:
    field_geom = square(-98.90, 19.45, 0.004)
    with tempfile.TemporaryDirectory(prefix="agrolattice11_1-links-") as temporary:
        root = Path(temporary)
        field_db = FieldOperationsDatabase(root / "field_operations" / "field_operations.sqlite")
        farm_id = field_db.create_farm("Research centre", country="Mexico", entity_type="Agricultural research centre")
        field_id = field_db.create_field(farm_id, "Trial field", field_geom)

        pollination_db = PollinationDatabase(root / "pollination_lab" / "maize_flowering_trials.sqlite")
        trial_id = create_trial(pollination_db, field_geom, source_field_id=field_id)

        twin_path = root / "agrolattice_twin" / "agrolattice_twin.sqlite"
        twin_path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(twin_path)
        con.execute("CREATE TABLE twin_links(link_id TEXT PRIMARY KEY, name TEXT, field_id TEXT, trial_id TEXT)")
        con.execute("INSERT INTO twin_links VALUES('L1','Twin 1',?,?)", (field_id, trial_id))
        con.commit(); con.close()

        require(field_db.external_field_dependency_counts(field_id)["Linked maize trials"] == 1,
                "Linked trial was not detected by field deletion guard.")
        require(field_db.external_field_dependency_counts(field_id)["Persistent Twin links"] == 1,
                "Persistent Twin field link was not detected.")
        try:
            field_db.delete_field(field_id)
        except ValueError:
            pass
        else:
            raise AssertionError("Field deletion was allowed despite Trial/Twin references.")
        require(field_db.field(field_id) is not None, "Blocked field deletion nevertheless removed the field.")

        try:
            pollination_db.delete_trial(trial_id)
        except PollinationLabError:
            pass
        else:
            raise AssertionError("Trial deletion was allowed despite a Persistent Twin reference.")
        require(pollination_db.get_trial(trial_id)["trial_id"] == trial_id, "Blocked trial deletion removed the trial.")


def verify_synchrony_gap_diagnostics() -> None:
    obs = pd.DataFrame({
        "Plot ID": ["P1", "P1", "P1"], "Plot": ["B01-U001"] * 3, "Block": [1] * 3,
        "Treatment": ["T1"] * 3, "Male offset (days)": [0] * 3,
        "Date": pd.to_datetime(["2027-06-01", "2027-06-02", "2027-06-05"]),
        "Male shedding (%)": [10, 50, 90], "Pollen intensity (0-5)": [1, 3, 5],
        "Female silking (%)": [5, 40, 90], "Female receptive silks (%)": [5, 45, 95],
        "Crop stress score (0-5)": [0, 0, 0], "Male plant height (cm)": [100, 120, 140],
        "Female plant height (cm)": [90, 110, 130],
        "Female sowing": ["2027-04-01"] * 3, "Male sowing": ["2027-04-01"] * 3,
    })
    metrics, _ = compute_plot_synchrony_metrics(obs)
    row = metrics.iloc[0]
    require(int(row["Observation window days"]) == 5, "Observation window was not calculated correctly.")
    require(int(row["Missing observation days"]) == 2, "Missing observation dates were not reported.")
    require(float(row["Largest observation gap (days)"]) == 3.0, "Largest observation gap was not reported.")
    require(abs(float(row["Observation completeness (%)"]) - 60.0) < 1e-9,
            "Observation completeness was not calculated correctly.")


def main() -> None:
    verify_overlap_guard()
    verify_non_destructive_randomisation_and_atomicity()
    verify_cross_database_delete_guards()
    verify_synchrony_gap_diagnostics()
    print("AGROLATTICE 11.1 research-integrity verification passed")


if __name__ == "__main__":
    main()
