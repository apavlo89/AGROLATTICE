"""AgroLattice Release 10 UX and compatibility helpers.

This module deliberately has no Streamlit dependency so that launchers can verify
critical compatibility before the dashboard starts.
"""

from __future__ import annotations

import inspect
import re
from collections.abc import Callable, Sequence
from typing import Any

import pandas as pd

MODULE_VERSION = "10.2.0"


def safe_key(value: Any) -> str:
    """Return a stable lowercase identifier suitable for Streamlit widget keys."""
    text = re.sub(r"[^a-zA-Z0-9]+", "_", str(value).strip()).strip("_").lower()
    return text or "item"


def _fallback_normalise_locations(
    climate_frame: pd.DataFrame,
    cities_frame: pd.DataFrame,
    *,
    scope: str = "existing",
    selected_states: Sequence[str] | None = None,
    selected_locations: Sequence[str] | None = None,
    country: str = "Mexico",
) -> pd.DataFrame:
    """Country-aware implementation used when an older updater is present.

    Release 9 introduced a ``country`` keyword to ``dataset_updater.normalise_locations``.
    Some users had an older updater module beside the new main application, which caused
    ``TypeError: unexpected keyword argument 'country'``. This fallback preserves global
    country support even in that mixed-file situation.
    """
    required = {"country", "city_ascii", "lat", "lng", "admin_name"}
    missing = required.difference(cities_frame.columns)
    if missing:
        raise ValueError(f"worldcities.csv is missing columns: {sorted(missing)}")

    selected_country = str(country or "Mexico").strip() or "Mexico"
    cities = (
        cities_frame.loc[
            cities_frame["country"].astype(str).str.casefold().eq(selected_country.casefold()),
            ["city_ascii", "admin_name", "lat", "lng"],
        ]
        .rename(columns={"city_ascii": "CITY", "admin_name": "STATE"})
        .dropna(subset=["CITY", "lat", "lng"])
        .assign(
            CITY=lambda frame: frame["CITY"].astype(str).str.strip(),
            STATE=lambda frame: (
                frame["STATE"]
                .fillna(selected_country)
                .astype(str)
                .str.strip()
                .replace("", selected_country)
            ),
            lat=lambda frame: pd.to_numeric(frame["lat"], errors="coerce"),
            lng=lambda frame: pd.to_numeric(frame["lng"], errors="coerce"),
        )
        .dropna(subset=["lat", "lng"])
        .drop_duplicates(["CITY", "STATE"], keep="first")
    )

    scope_key = str(scope).strip().casefold()
    if scope_key in {"all_country", "all_mexico"}:
        locations = cities.copy()
    else:
        required_climate = {"CITY", "STATE"}
        if not required_climate.issubset(climate_frame.columns):
            existing = pd.DataFrame(columns=["CITY", "STATE"])
        else:
            existing = climate_frame[["CITY", "STATE"]].drop_duplicates().copy()
            existing["CITY"] = existing["CITY"].astype(str).str.strip()
            existing["STATE"] = existing["STATE"].astype(str).str.strip()
        locations = existing.merge(cities, on=["CITY", "STATE"], how="inner")

    if selected_states:
        state_set = {str(value).strip() for value in selected_states}
        locations = locations[locations["STATE"].isin(state_set)]

    locations = locations.copy()
    locations["Location"] = locations["CITY"] + " (" + locations["STATE"] + ")"
    if selected_locations:
        selected_set = {str(value) for value in selected_locations}
        locations = locations[locations["Location"].isin(selected_set)]

    return locations.sort_values(["STATE", "CITY"]).reset_index(drop=True)


def normalise_locations_compat(
    normaliser: Callable[..., pd.DataFrame],
    climate_frame: pd.DataFrame,
    cities_frame: pd.DataFrame,
    *,
    scope: str = "existing",
    selected_states: Sequence[str] | None = None,
    selected_locations: Sequence[str] | None = None,
    country: str = "Mexico",
) -> pd.DataFrame:
    """Call a current updater normaliser or transparently support an older one."""
    kwargs = {
        "scope": scope,
        "selected_states": selected_states,
        "selected_locations": selected_locations,
    }
    try:
        parameters = inspect.signature(normaliser).parameters
    except (TypeError, ValueError):
        parameters = {}

    if "country" in parameters:
        return normaliser(
            climate_frame,
            cities_frame,
            country=country,
            **kwargs,
        )

    # Do not call an old Mexico-hardcoded function for a non-Mexico workspace.
    # The local fallback is deterministic and supports both old and new scopes.
    return _fallback_normalise_locations(
        climate_frame,
        cities_frame,
        country=country,
        **kwargs,
    )


def install_candidate_compat(
    installer: Callable[..., dict],
    job_dir: Any,
    target_dataset_path: Any,
    *,
    backup_dir: Any,
    similarity_cache_path: Any | None = None,
) -> dict:
    """Install a candidate with either the current or legacy cache keyword.

    Release 9 accidentally called ``install_candidate`` with
    ``target_similarity_cache_path`` while the updater API uses
    ``similarity_cache_path``. Mixed-version folders therefore failed only at the
    final installation step. This adapter introspects the installed updater and
    supplies whichever keyword it accepts.
    """
    try:
        parameters = inspect.signature(installer).parameters
    except (TypeError, ValueError):
        parameters = {}

    kwargs = {"backup_dir": backup_dir}
    if "similarity_cache_path" in parameters:
        kwargs["similarity_cache_path"] = similarity_cache_path
    elif "target_similarity_cache_path" in parameters:
        kwargs["target_similarity_cache_path"] = similarity_cache_path
    elif similarity_cache_path is not None:
        # Very old installers may not expose a cache argument. Installation can
        # still proceed safely; clear the cache after the verified replacement.
        result = installer(job_dir, target_dataset_path, **kwargs)
        try:
            from pathlib import Path as _Path
            _Path(similarity_cache_path).unlink(missing_ok=True)
        except Exception:
            pass
        return result

    return installer(job_dir, target_dataset_path, **kwargs)
