"""Small Streamlit harness used by verify_release11_0_ui.py."""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

from maize_pollination_lab import PollinationDatabase, render_synchrony_prediction_page


database_path = Path(os.environ.get("AGROLATTICE_UI_TEST_DB", "/tmp/agrolattice_release11_ui.sqlite"))
database = PollinationDatabase(database_path)
if database.list_trials().empty:
    geometry = {
        "type": "Polygon",
        "coordinates": [[[-98.90, 19.45], [-98.899, 19.45], [-98.899, 19.451], [-98.90, 19.451], [-98.90, 19.45]]],
    }
    trial_id = database.create_trial({
        "name": "UI verification trial", "site_name": "Montecillo", "season_year": 2027,
        "female_parent_levels": ["F01"], "male_parent_levels": ["M01"],
        "parent_pairing_mode": "All female × male combinations",
        "sowing_density_levels": [65000], "sowing_date_levels": ["2027-04-01"],
        "sowing_offset_levels": [0], "female_sowing_date": "2027-04-01",
        "design_type": "Randomised complete block", "blocks": 1, "replicates_per_treatment": 1,
        "row_ratio": "4:2", "primary_outcome": "Flowering overlap score",
        "base_temperature_c": 10, "upper_temperature_c": 30,
        "field_geometry": geometry, "status": "Active",
    })
    database.replace_plots(trial_id, [{
        "plot_label": "B01-U001", "block": 1, "replicate": 1, "treatment_label": "T001",
        "male_sowing_offset_days": 0, "sowing_density_plants_ha": 65000,
        "female_parent": "F01", "male_parent": "M01", "parent_combination": "F01 × M01",
        "female_sowing_date": "2027-04-01", "male_sowing_date": "2027-04-01", "geometry": geometry,
    }])
    dates = pd.date_range("2027-03-01", periods=260)
    weather = pd.DataFrame({
        "Date": dates, "Tmin (°C)": 12.0, "Tmax (°C)": 30.0, "Tmean (°C)": 21.0,
        "Rainfall (mm)": 0.0, "Solar radiation (MJ/m²/day)": 20.0,
        "Reference ET (mm)": 4.0, "GDD daily": 11.0 + np.sin(np.linspace(0, 8, len(dates))),
    })
    database.replace_weather(trial_id, weather, source="UI verification")

render_synchrony_prediction_page(db=database, project=None)
