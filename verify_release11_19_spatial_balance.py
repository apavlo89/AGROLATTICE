"""Targeted verification for AGROLATTICE 11.19 spatially balanced clustering."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from spatial_clustering_balance import (
    RAW_LOCATION_MODE,
    SPATIALLY_BALANCED_MODE,
    build_spatial_support,
    expand_support_results,
)


ROOT = Path(__file__).resolve().parent


def main() -> None:
    climate_path = ROOT / "Datasets/countries/mexico/agroclimate_longformat.csv"
    catalogue_path = ROOT / "Datasets/worldcities.csv"

    climate_locations = pd.read_csv(
        climate_path, usecols=["CITY", "STATE"]
    ).drop_duplicates(["CITY", "STATE"])
    assert len(climate_locations) == 1_012
    assert climate_locations["STATE"].nunique() == 32
    assert int(climate_locations["STATE"].eq("Oaxaca").sum()) == 80

    catalogue = pd.read_csv(catalogue_path)
    mexico = (
        catalogue.loc[catalogue["country"].eq("Mexico"), ["city_ascii", "admin_name", "lat", "lng"]]
        .rename(columns={"city_ascii": "CITY", "admin_name": "STATE"})
        .drop_duplicates(["CITY", "STATE"], keep="first")
        .reset_index(drop=True)
    )
    assert len(mexico) == 1_012

    locations = climate_locations.merge(
        mexico[["CITY", "STATE"]], on=["CITY", "STATE"], how="inner", validate="one_to_one"
    ).sort_values(["CITY", "STATE"]).reset_index(drop=True)
    assert len(locations) == 1_012
    locations["Location"] = locations["CITY"] + " (" + locations["STATE"] + ")"
    locations["Data completeness (%)"] = 100.0
    features = pd.DataFrame({
        "TEMPERATURE_JANUARY": np.linspace(-1.0, 1.0, len(locations)),
        "PRECIPITATION_AVG_JANUARY": np.cos(np.linspace(0.0, 5.0, len(locations))),
    })

    balanced = build_spatial_support(
        locations, features, mexico, SPATIALLY_BALANCED_MODE, 50.0
    )
    support_count = len(balanced.analysis_locations)
    assert 250 < support_count < 600
    assert len(balanced.expanded_locations) == 1_012
    assert np.isclose(
        balanced.expanded_locations["Spatial analysis weight"].sum(), support_count
    )
    assert np.allclose(balanced.support_table["Total spatial weight"], 1.0)
    assert int(balanced.support_table["Locations in support cell"].max()) > 1

    support_results = balanced.analysis_locations.copy()
    support_results["Cluster"] = np.where(
        np.arange(support_count) % 2 == 0, 1, 2
    )
    expanded = expand_support_results(
        balanced.expanded_locations, support_results, ["Cluster"]
    )
    assert len(expanded) == 1_012
    assert expanded["Cluster"].notna().all()

    raw = build_spatial_support(
        locations, features, mexico, RAW_LOCATION_MODE, 50.0
    )
    assert len(raw.analysis_locations) == 1_012
    assert np.allclose(raw.expanded_locations["Spatial analysis weight"], 1.0)

    app_text = (ROOT / "agrolattice.py").read_text(encoding="utf-8")
    for fragment in (
        "How unequal location density is corrected",
        "Spatial sampling correction",
        "Effective support units",
        "spatial_sampling_audit.csv",
        "Spatial analysis weight",
    ):
        assert fragment in app_text, fragment

    print(
        "AGROLATTICE 11.19 spatial-balance verification passed: "
        f"1,012 locations -> {support_count} equal-weight 50 km support units."
    )


if __name__ == "__main__":
    main()
