"""Spatial sampling correction for AGROLATTICE climate-zone discovery.

City catalogues are convenient display and retrieval indexes, but their spatial
density follows settlement patterns rather than equal geographic support.  This
module converts eligible city profiles into occupied equal-area support cells
before PCA, model selection and clustering.  Each occupied cell contributes one
analysis unit; every original city is retained for mapping and export.

The projection is a spherical Lambert cylindrical equal-area projection.  It is
implemented directly to keep the publication-reference release independent of
optional GIS packages.  Cell width and height are expressed in projected
kilometres, so every cell has the same projected area.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


EARTH_RADIUS_KM = 6371.0088
SPATIALLY_BALANCED_MODE = "Equal-area support cells (recommended)"
RAW_LOCATION_MODE = "Raw location counts (diagnostic only)"


@dataclass(frozen=True)
class SpatialSupport:
    """Frames and diagnostics required by downstream clustering engines."""

    analysis_locations: pd.DataFrame
    analysis_features: pd.DataFrame
    expanded_locations: pd.DataFrame
    support_table: pd.DataFrame
    diagnostics: dict


def _equal_area_cell_ids(
    latitude: pd.Series,
    longitude: pd.Series,
    cell_size_km: float,
) -> pd.Series:
    """Return stable Lambert cylindrical equal-area square-cell identifiers."""
    size = float(cell_size_km)
    if not np.isfinite(size) or size <= 0:
        raise ValueError("Spatial support-cell size must be a positive number of kilometres.")
    lat_radians = np.radians(pd.to_numeric(latitude, errors="coerce").to_numpy(dtype=float))
    lon_radians = np.radians(pd.to_numeric(longitude, errors="coerce").to_numpy(dtype=float))
    projected_x = EARTH_RADIUS_KM * lon_radians
    projected_y = EARTH_RADIUS_KM * np.sin(lat_radians)
    cell_x = np.floor(projected_x / size).astype(np.int64)
    cell_y = np.floor(projected_y / size).astype(np.int64)
    prefix = f"EA{size:g}KM"
    return pd.Series(
        [f"{prefix}_X{x:+05d}_Y{y:+05d}" for x, y in zip(cell_x, cell_y)],
        index=latitude.index,
        dtype="object",
    )


def build_spatial_support(
    locations: pd.DataFrame,
    raw_features: pd.DataFrame,
    coordinate_catalogue: pd.DataFrame,
    mode: str = SPATIALLY_BALANCED_MODE,
    cell_size_km: float = 50.0,
) -> SpatialSupport:
    """Create equal-weight spatial units and preserve city-level membership.

    In the recommended mode, feature values are averaged within occupied
    equal-area cells.  In diagnostic raw-location mode, every city remains a
    separate unit.  The latter is retained only to reproduce or investigate
    the effect of settlement-density weighting.
    """
    if len(locations) != len(raw_features):
        raise ValueError("Location and feature rows are not aligned.")
    required_location_columns = {"CITY", "STATE", "Location", "Data completeness (%)"}
    missing_locations = required_location_columns.difference(locations.columns)
    if missing_locations:
        raise ValueError(f"Locations are missing required columns: {sorted(missing_locations)}")
    required_coordinates = {"CITY", "STATE", "lat", "lng"}
    missing_coordinates = required_coordinates.difference(coordinate_catalogue.columns)
    if missing_coordinates:
        raise ValueError(f"Coordinate catalogue is missing columns: {sorted(missing_coordinates)}")

    coordinates = (
        coordinate_catalogue[["CITY", "STATE", "lat", "lng"]]
        .drop_duplicates(["CITY", "STATE"], keep="first")
    )
    expanded = locations.reset_index(drop=True).merge(
        coordinates,
        on=["CITY", "STATE"],
        how="left",
        validate="one_to_one",
    )
    expanded["lat"] = pd.to_numeric(expanded["lat"], errors="coerce")
    expanded["lng"] = pd.to_numeric(expanded["lng"], errors="coerce")
    missing_geography = expanded[["lat", "lng"]].isna().any(axis=1)
    if bool(missing_geography.any()):
        examples = ", ".join(expanded.loc[missing_geography, "Location"].head(5).astype(str))
        raise ValueError(
            f"Spatial balancing requires coordinates for every eligible location; "
            f"{int(missing_geography.sum())} are unmatched (for example: {examples})."
        )

    balanced = str(mode).startswith("Equal-area")
    if balanced:
        expanded["Spatial support cell"] = _equal_area_cell_ids(
            expanded["lat"], expanded["lng"], float(cell_size_km)
        )
    else:
        expanded["Spatial support cell"] = [
            f"RAW_LOCATION_{index + 1:06d}" for index in range(len(expanded))
        ]

    expanded["Locations in support cell"] = (
        expanded.groupby("Spatial support cell")["Spatial support cell"].transform("size").astype(int)
    )
    expanded["Spatial analysis weight"] = 1.0 / expanded["Locations in support cell"]
    expanded["Spatial weighting method"] = (
        f"Equal weight per occupied {float(cell_size_km):g} km × {float(cell_size_km):g} km "
        "Lambert cylindrical equal-area support cell"
        if balanced
        else "One equal vote per raw catalogue location"
    )

    feature_frame = raw_features.reset_index(drop=True).copy()
    feature_frame.insert(0, "Spatial support cell", expanded["Spatial support cell"].to_numpy())
    analysis_features = (
        feature_frame.groupby("Spatial support cell", sort=True)[list(raw_features.columns)]
        .mean()
    )

    ordered = expanded.sort_values(
        ["Spatial support cell", "Location"], kind="mergesort"
    )
    representatives = ordered.groupby("Spatial support cell", sort=True).first()
    support_table = (
        expanded.groupby("Spatial support cell", sort=True)
        .agg(
            **{
                "Locations in support cell": ("Location", "size"),
                "Cell centroid latitude": ("lat", "mean"),
                "Cell centroid longitude": ("lng", "mean"),
                "Mean completeness (%)": ("Data completeness (%)", "mean"),
            }
        )
    )
    support_table["Representative location"] = representatives["Location"]
    support_table["Representative city"] = representatives["CITY"]
    support_table["Representative state"] = representatives["STATE"]
    support_table["Total spatial weight"] = expanded.groupby(
        "Spatial support cell", sort=True
    )["Spatial analysis weight"].sum()
    support_table = support_table.reset_index()

    analysis_locations = pd.DataFrame({
        "Spatial support cell": support_table["Spatial support cell"],
        "CITY": support_table["Representative city"],
        "STATE": support_table["Representative state"],
        "Location": support_table["Representative location"],
        "Data completeness (%)": support_table["Mean completeness (%)"],
        "lat": support_table["Cell centroid latitude"],
        "lng": support_table["Cell centroid longitude"],
        "Locations in support cell": support_table["Locations in support cell"].astype(int),
    })

    counts = support_table["Locations in support cell"].astype(int)
    diagnostics = {
        "Spatial balancing enabled": bool(balanced),
        "Method": (
            "Equal-weight occupied cells in a spherical Lambert cylindrical equal-area grid"
            if balanced else "Uncorrected raw catalogue-location weighting"
        ),
        "Support-cell width (km)": float(cell_size_km) if balanced else None,
        "Support-cell nominal area (km²)": float(cell_size_km) ** 2 if balanced else None,
        "Eligible catalogue locations": int(len(expanded)),
        "Georeferenced locations": int(len(expanded)),
        "Occupied spatial support units": int(len(support_table)),
        "Effective spatial sample size": float(expanded["Spatial analysis weight"].sum()),
        "Mean locations per support unit": float(counts.mean()),
        "Median locations per support unit": float(counts.median()),
        "Maximum locations in one support unit": int(counts.max()),
        "Singleton support units": int((counts == 1).sum()),
        "Singleton support units (%)": float(100.0 * (counts == 1).mean()),
        "Interpretation": (
            "PCA, model selection, silhouette, stability and minimum-cluster safeguards use occupied support cells; "
            "all catalogue locations inherit their cell assignment for mapping and export."
            if balanced else
            "PCA and clustering use raw catalogue locations, so densely catalogued regions contribute more weight."
        ),
    }
    return SpatialSupport(
        analysis_locations=analysis_locations.reset_index(drop=True),
        analysis_features=analysis_features.reset_index(drop=True),
        expanded_locations=expanded.reset_index(drop=True),
        support_table=support_table.reset_index(drop=True),
        diagnostics=diagnostics,
    )


def expand_support_results(
    expanded_locations: pd.DataFrame,
    support_results: pd.DataFrame,
    result_columns: list[str],
) -> pd.DataFrame:
    """Attach support-cell cluster results to every original catalogue location."""
    available = [column for column in result_columns if column in support_results.columns]
    lookup = support_results[["Spatial support cell"] + available].copy()
    if lookup["Spatial support cell"].duplicated().any():
        raise ValueError("Support-cell result keys are not unique.")
    return expanded_locations.merge(
        lookup,
        on="Spatial support cell",
        how="left",
        validate="many_to_one",
    )
