"""End-to-end verification for AGROLATTICE 11.0."""
from __future__ import annotations

import io
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from local_boundary_editor import COMPONENT_DIRECTORY
from maize_mechanistic_twin import (
    DEFAULT_PHYSIOLOGY,
    PhysiologyParameters,
    calibrate_parent_physiology,
    event_date,
    genomic_physiology_bridge,
    optimise_male_sowing_strategy,
    simulate_event_uncertainty,
    simulate_mfs,
)
from maize_pollination_lab import ModelFitResult, PollinationDatabase, optimise_sowing_offset


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def synthetic_weather() -> pd.DataFrame:
    dates = pd.date_range("2027-03-01", periods=260, freq="D")
    seasonal = 11.0 + 2.5 * np.sin(np.linspace(0, 4 * np.pi, len(dates)))
    return pd.DataFrame({
        "Date": dates,
        "GDD daily": np.clip(seasonal, 4, None),
        "Tmin (°C)": 12.0,
        "Tmax (°C)": 30.0,
        "Tmean (°C)": 21.0,
        "Rainfall (mm)": 0.0,
        "Solar radiation (MJ/m²/day)": 20.0,
        "Reference ET (mm)": 4.0,
    })


def verify_mechanistic_engine() -> None:
    weather = synthetic_weather()
    curve, summary = simulate_mfs(weather, "2027-04-01", DEFAULT_PHYSIOLOGY)
    require(len(curve) > 100, "Daily mechanistic curve is unexpectedly short.")
    require(summary["Anthesis date"] and summary["Silking date"], "MFS event dates were not reached.")
    require(curve["Predicted collared leaf number"].max() <= DEFAULT_PHYSIOLOGY.tln + 1e-9, "Leaf number exceeded tln.")
    require(curve["Predicted ear biomass (g)"].max() <= 5.0 + 1e-9, "Ear biomass exceeded its model cap.")
    _, uncertainty = simulate_event_uncertainty(weather, "2027-04-01", DEFAULT_PHYSIOLOGY, "Female", draws=250)
    require(uncertainty["Complete draws"] >= 200, "Too many uncertainty draws were incomplete.")
    strategies = optimise_male_sowing_strategy(
        weather, "2027-04-01", DEFAULT_PHYSIOLOGY, DEFAULT_PHYSIOLOGY,
        minimum_offset=-10, maximum_offset=12, draws=250,
    )
    require(set(strategies["Strategy"]) == {"One male sowing date", "Two staggered male sowing dates"}, "Both strategy classes were not evaluated.")
    require(strategies.groupby("Strategy")["Recommended"].sum().eq(1).all(), "Each strategy class must have one recommendation.")


def verify_calibration_and_genomics() -> None:
    weather = synthetic_weather()
    true_parameters = PhysiologyParameters(tln=18.2, coblf=0.00205, eb_r1_g=1.85, tln_sd=0.3, coblf_sd=0.00008, eb_r1_sd=0.12)
    event_rows = []
    leaf_rows = []
    for offset in (0, 4, 8, 12):
        sowing = pd.Timestamp("2027-04-01") + pd.Timedelta(days=offset)
        observed_event = event_date(weather, sowing, true_parameters, "Female")
        event_rows.append({"Sowing date": sowing, "Event date": observed_event})
        curve, _ = simulate_mfs(weather, sowing, true_parameters)
        for observed_date in pd.date_range(sowing + pd.Timedelta(days=25), periods=5, freq="10D"):
            nearest = curve.iloc[(curve["Date"] - observed_date).abs().argsort()[:1]]
            leaf_rows.append({
                "Sowing date": sowing, "Observation date": observed_date,
                "Collared leaf number": float(nearest["Predicted collared leaf number"].iloc[0]),
            })
    calibration = calibrate_parent_physiology(
        weather, role="Female", event_observations=pd.DataFrame(event_rows),
        leaf_observations=pd.DataFrame(leaf_rows), prior=DEFAULT_PHYSIOLOGY,
    )
    require(calibration["success"], "Prior-regularised calibration failed.")
    require(abs(calibration["parameters"].coblf - true_parameters.coblf) < 0.0004, "Calibration did not recover a plausible coblf.")

    rng = np.random.default_rng(7)
    marker_values = rng.integers(0, 3, size=(14, 24))
    marker_frame = pd.DataFrame(marker_values, columns=[f"SNP_{index:04d}" for index in range(24)])
    marker_frame.insert(0, "Parent line", [f"P{index:02d}" for index in range(14)])
    physiology = pd.DataFrame({
        "Parent line": marker_frame["Parent line"],
        "tln": 17.0 + marker_values[:, 0] * 0.8 + marker_values[:, 1] * 0.25,
        "coblf": 0.0016 + marker_values[:, 2] * 0.00015 + marker_values[:, 3] * 0.00004,
        "eb_r1_g": 1.4 + marker_values[:, 4] * 0.3 + marker_values[:, 5] * 0.08,
    })
    predictions, metrics = genomic_physiology_bridge(marker_frame, physiology, alpha=2.0)
    require(len(predictions) == 14 and len(metrics) == 3, "Genomic bridge output dimensions are incorrect.")
    require(predictions.filter(like="Predicted").notna().all().all(), "Genomic bridge returned missing predictions.")


class _SignedGapModel:
    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        return pd.to_numeric(frame["Male offset (days)"], errors="coerce").to_numpy(float) + 3.0


def verify_empirical_objective() -> None:
    training = pd.DataFrame({"Male offset (days)": [-6, -3, 0, 3], "Target": [-3, 0, 3, 6]})
    fit = ModelFitResult(
        metrics=pd.DataFrame(), predictions=pd.DataFrame(), models={"Test": _SignedGapModel()},
        feature_columns=["Male offset (days)"], categorical_columns=[],
        numerical_columns=["Male offset (days)"], training_frame=training, target="Synchrony gap (days; male50 - female50)",
    )
    result = optimise_sowing_offset(fit, model_name="Test", minimum_offset=-8, maximum_offset=8, objective="closest to zero")
    recommended = result.loc[result["Recommended"]].iloc[0]
    require(int(recommended["Male offset (days)"]) == -3, "Signed synchrony gap was not optimised toward zero.")


def verify_database_and_export() -> None:
    geometry = {
        "type": "Polygon",
        "coordinates": [[[-98.90, 19.45], [-98.899, 19.45], [-98.899, 19.451], [-98.90, 19.451], [-98.90, 19.45]]],
    }
    with tempfile.TemporaryDirectory(prefix="agrolattice11-") as temporary:
        database = PollinationDatabase(Path(temporary) / "pollination.sqlite")
        trial_id = database.create_trial({
            "name": "Release 11 verification", "site_name": "Montecillo", "season_year": 2027,
            "female_parent_levels": ["F01"], "male_parent_levels": ["M01"],
            "parent_pairing_mode": "All female × male combinations",
            "sowing_density_levels": [65000], "sowing_date_levels": ["2027-04-01"],
            "sowing_offset_levels": [0], "female_sowing_date": "2027-04-01",
            "design_type": "Randomised complete block", "blocks": 1,
            "replicates_per_treatment": 1, "row_ratio": "4:2",
            "primary_outcome": "Flowering overlap score", "base_temperature_c": 10,
            "upper_temperature_c": 30, "field_geometry": geometry, "status": "Active",
        })
        database.replace_plots(trial_id, [{
            "plot_label": "B01-U001", "experiment_plot_label": "B01", "treatment_unit_label": "B01-U001",
            "block": 1, "replicate": 1, "treatment_label": "T001", "male_sowing_offset_days": 0,
            "sowing_density_plants_ha": 65000, "female_parent": "F01", "male_parent": "M01",
            "parent_combination": "F01 × M01", "sowing_date": "2027-04-01",
            "female_sowing_date": "2027-04-01", "male_sowing_date": "2027-04-01",
            "geometry": geometry,
        }])
        database.initialise()
        database.initialise()
        inserted, issues = database.upsert_leaf_observations(trial_id, pd.DataFrame([
            {"Plot": "B01-U001", "Observation date": "2027-04-25", "Plant tag": "F-P1", "Parent role": "Female", "Collared leaf number": 4},
            {"Plot": "B01-U001", "Observation date": "2027-04-25", "Plant tag": "M-P1", "Parent role": "Male", "Collared leaf number": 4},
        ]))
        require(inserted == 2 and not issues, "Tagged-plant leaf observations were not imported.")
        database.upsert_parent_physiology("F01", "Female", DEFAULT_PHYSIOLOGY)
        database.upsert_parent_physiology("M01", "Male", DEFAULT_PHYSIOLOGY)
        package = database.export_trial_package(trial_id)
        with zipfile.ZipFile(io.BytesIO(package)) as archive:
            names = set(archive.namelist())
        require("trial/leaf_development_observations.csv" in names, "Leaf observations are missing from the trial export.")
        require("trial/parent_physiology.csv" in names, "Parent physiology is missing from the trial export.")
        require("trial/mechanistic_method_manifest.json" in names, "Mechanistic manifest is missing from the trial export.")


def verify_local_component() -> None:
    required = {"index.html", "main.js", "main.css", "spritesheet.svg"}
    names = {path.name for path in COMPONENT_DIRECTORY.iterdir()}
    require(required <= names, "Locally bundled boundary-editor assets are incomplete.")
    index = (COMPONENT_DIRECTORY / "index.html").read_text(encoding="utf-8")
    require("./main.js" in index and "./main.css" in index, "Boundary editor does not reference local assets.")
    require("unpkg.com" not in index and "cdn.jsdelivr.net" not in index, "Boundary editor still depends on a public script CDN.")


def main() -> None:
    verify_mechanistic_engine()
    verify_calibration_and_genomics()
    verify_empirical_objective()
    verify_database_and_export()
    verify_local_component()
    print("AGROLATTICE 11.0 verification passed")


if __name__ == "__main__":
    main()
