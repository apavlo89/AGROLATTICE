"""Fast immutable runtime data preparation for AGROLATTICE.

Release 11.6 removes repeated parsing and preparation of the large country
climate table during Streamlit reruns.  The functions in this module are pure
Python/Pandas helpers; Streamlit owns the process-local resource cache in
``agrolattice.py``.

The source CSV remains authoritative.  No row values are altered beyond the
same whitespace/case/numeric normalisation already used by the application.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from global_country_support import country_locations

MODULE_VERSION = "1.0.0"
CANONICAL_CLIMATE_COLUMNS = ["CITY", "STATE", "Year", "Month", "Variable", "Value"]


@dataclass(frozen=True)
class FileSignature:
    path: str
    exists: bool
    size_bytes: int
    mtime_ns: int


@dataclass
class CountryRuntimeData:
    cities: pd.DataFrame
    country_cities: pd.DataFrame
    climate: pd.DataFrame
    merged: pd.DataFrame
    climate_locations: pd.DataFrame
    status: dict[str, Any]
    years: list[int]
    variables: list[str]
    map_centre: tuple[float, float]
    climate_signature: FileSignature


def file_signature(path: str | Path) -> FileSignature:
    target = Path(path)
    try:
        stat = target.stat()
        return FileSignature(str(target.resolve()), True, int(stat.st_size), int(stat.st_mtime_ns))
    except FileNotFoundError:
        return FileSignature(str(target.resolve()), False, 0, 0)


def read_city_catalogue(path: str | Path) -> pd.DataFrame:
    """Read the global city catalogue once for process-local reuse."""
    return pd.read_csv(Path(path))


def _empty_climate() -> pd.DataFrame:
    return pd.DataFrame(columns=CANONICAL_CLIMATE_COLUMNS)


def read_and_clean_climate(path: str | Path) -> pd.DataFrame:
    """Read and normalise the authoritative monthly climate CSV.

    This intentionally mirrors the Release 11.5 cleaning rules so performance
    optimisation does not change scientific values or inclusion criteria.
    """
    target = Path(path)
    if not target.exists():
        return _empty_climate()
    try:
        frame = pd.read_csv(target)
    except pd.errors.EmptyDataError:
        return _empty_climate()

    missing = set(CANONICAL_CLIMATE_COLUMNS).difference(frame.columns)
    if missing:
        raise ValueError(f"The climate dataset is missing columns: {sorted(missing)}")

    frame = frame[CANONICAL_CLIMATE_COLUMNS].copy()
    frame["CITY"] = frame["CITY"].astype(str).str.strip()
    frame["STATE"] = frame["STATE"].astype(str).str.strip()
    frame["Month"] = frame["Month"].astype(str).str.upper().str.strip()
    frame["Variable"] = frame["Variable"].astype(str).str.upper().str.strip()
    frame["Year"] = pd.to_numeric(frame["Year"], errors="coerce")
    frame["Value"] = pd.to_numeric(frame["Value"], errors="coerce")
    frame = frame.dropna(subset=CANONICAL_CLIMATE_COLUMNS).reset_index(drop=True)
    if not frame.empty:
        frame["Year"] = frame["Year"].astype(int)
    return frame


def dataset_status_from_frame(frame: pd.DataFrame, *, path: str | Path, country: str, location_count: int | None = None) -> dict[str, Any]:
    """Calculate status from an already-loaded frame, never rereading the CSV."""
    target = Path(path)
    if frame is None or frame.empty:
        return {
            "country": country,
            "path": str(target),
            "exists": target.exists(),
            "rows": 0,
            "locations": 0,
            "years": [],
        }
    return {
        "country": country,
        "path": str(target),
        "exists": target.exists(),
        "rows": int(len(frame)),
        "locations": int(location_count) if location_count is not None else int(frame[["CITY", "STATE"]].drop_duplicates().shape[0]),
        "years": sorted(pd.to_numeric(frame["Year"], errors="coerce").dropna().astype(int).unique().tolist()),
    }


def build_country_runtime(
    cities_path: str | Path,
    climate_path: str | Path,
    country: str,
) -> CountryRuntimeData:
    """Load and prepare the complete active-country runtime dataset once.

    The returned frames are intended to be treated as read-only process-local
    resources by Streamlit.  This avoids the large serialisation/copy cost of
    ``st.cache_data`` for the Mexico table and prevents a second full CSV read
    merely to calculate dataset status.
    """
    cities = read_city_catalogue(cities_path)
    climate = read_and_clean_climate(climate_path)
    locations = country_locations(cities, country)

    if locations.empty:
        centre = (19.4326, -99.1332)
    else:
        centre = (float(locations["lat"].median()), float(locations["lng"].median()))

    if climate.empty or locations.empty:
        for column in ("lat", "lng"):
            if column not in climate.columns:
                climate[column] = pd.Series(dtype="float64")
        merged = climate
    else:
        # Release 11.5 used a full many-to-one DataFrame merge here. On the
        # Mexico dataset that duplicated ~8.8 million climate rows merely to
        # attach two coordinates. Instead, align the small coordinate lookup
        # to the existing row keys and add just two numeric arrays in place.
        # Standard country datasets originate from this same catalogue, so
        # all rows normally match and ``merged`` can safely alias ``climate``
        # without a multi-gigabyte duplicate. Any exceptional unmatched rows
        # retain the historical inner-merge semantics via a filtered copy.
        coordinate_lookup = locations.set_index(["CITY", "STATE"])[["lat", "lng"]]
        if not coordinate_lookup.index.is_unique:
            raise ValueError("Country location catalogue contains duplicate CITY/STATE keys.")
        row_keys = pd.MultiIndex.from_arrays(
            [climate["CITY"].to_numpy(copy=False), climate["STATE"].to_numpy(copy=False)],
            names=["CITY", "STATE"],
        )
        aligned = coordinate_lookup.reindex(row_keys)
        climate["lat"] = aligned["lat"].to_numpy(copy=False)
        climate["lng"] = aligned["lng"].to_numpy(copy=False)
        matched = climate["lat"].notna() & climate["lng"].notna()
        merged = climate if bool(matched.all()) else climate.loc[matched].reset_index(drop=True)

    if merged.empty:
        climate_locations = pd.DataFrame(columns=["CITY", "STATE", "lat", "lng", "Location"])
    else:
        climate_locations = (
            merged[["CITY", "STATE", "lat", "lng"]]
            .dropna(subset=["CITY", "STATE", "lat", "lng"])
            .drop_duplicates(["CITY", "STATE"], keep="first")
            .sort_values(["CITY", "STATE"])
            .reset_index(drop=True)
        )
        climate_locations["Location"] = climate_locations["CITY"].astype(str) + " (" + climate_locations["STATE"].astype(str) + ")"

    status = dataset_status_from_frame(climate, path=climate_path, country=country, location_count=len(climate_locations))
    years = sorted(int(year) for year in merged["Year"].unique()) if not merged.empty else []
    variables = sorted(str(value) for value in merged["Variable"].dropna().unique()) if not merged.empty else []
    return CountryRuntimeData(
        cities=cities,
        country_cities=locations,
        climate=climate,
        merged=merged,
        climate_locations=climate_locations,
        status=status,
        years=years,
        variables=variables,
        map_centre=centre,
        climate_signature=file_signature(climate_path),
    )


def runtime_summary(runtime: CountryRuntimeData) -> dict[str, Any]:
    """Small diagnostic summary safe to render in the UI."""
    sig = runtime.climate_signature
    return {
        "rows": int(len(runtime.climate)),
        "matched_rows": int(len(runtime.merged)),
        "locations": int(runtime.status.get("locations", 0)),
        "years": len(runtime.years),
        "variables": len(runtime.variables),
        "source_size_mb": round(sig.size_bytes / (1024 * 1024), 1),
        "source_mtime_ns": sig.mtime_ns,
        "cache_strategy": "process-local zero-copy resource",
    }
