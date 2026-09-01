"""Global country workspaces, standardised storage and map search support.

Release 10.2 stores every country—including Mexico—under the same canonical
layout: ``Datasets/countries/<country>/agroclimate_longformat.csv``.  A safe
one-time migration recognises the historic Mexico filename and moves it into
the canonical country folder without changing its contents.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

MODULE_VERSION = "10.3.0"
DEFAULT_COUNTRY = "Mexico"
COUNTRY_DATA_DIRNAME = "countries"
COUNTRY_DATA_FILENAME = "agroclimate_longformat.csv"
CANONICAL_COLUMNS = ["CITY", "STATE", "Year", "Month", "Variable", "Value"]
LEGACY_MEXICO_DATA_FILENAME = "mexico_climatology_1985_2024_longformat.csv"

_MAP_SEARCH_STATE: dict[str, Any] = {
    "enabled": True,
    "restrict_country": True,
    "country_code": "mx",
    "placeholder": "Search a place…",
}
_MAP_PATCHED = False
_ORIGINAL_FOLIUM_MAP_INIT = None


def country_slug(country: str) -> str:
    text = unicodedata.normalize("NFKD", str(country)).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "country"


def settings_path(data_dir: Path) -> Path:
    return Path(data_dir) / "global_country_settings.json"


def load_settings(data_dir: Path) -> dict[str, Any]:
    defaults = {
        "active_country": DEFAULT_COUNTRY,
        "restrict_map_search_to_country": True,
        "map_search_enabled": True,
    }
    path = settings_path(data_dir)
    if not path.exists():
        return defaults
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, Mapping):
            defaults.update({key: payload[key] for key in defaults if key in payload})
    except Exception:
        pass
    return defaults


def save_settings(data_dir: Path, settings: Mapping[str, Any]) -> Path:
    path = settings_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "active_country": str(settings.get("active_country") or DEFAULT_COUNTRY),
        "restrict_map_search_to_country": bool(settings.get("restrict_map_search_to_country", True)),
        "map_search_enabled": bool(settings.get("map_search_enabled", True)),
    }
    # Streamlit reruns the app for normal navigation. Avoid rewriting this
    # settings file when the logical values have not changed; this reduces
    # needless filesystem work and preserves a meaningful modification time.
    if path.exists():
        try:
            current = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(current, Mapping) and all(current.get(key) == value for key, value in payload.items()):
                return path
        except Exception:
            pass
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)
    return path


def available_countries(cities: pd.DataFrame) -> list[str]:
    if "country" not in cities.columns:
        return [DEFAULT_COUNTRY]
    values = sorted({str(value).strip() for value in cities["country"].dropna() if str(value).strip()}, key=str.casefold)
    if DEFAULT_COUNTRY in values:
        values.remove(DEFAULT_COUNTRY)
        values.insert(0, DEFAULT_COUNTRY)
    return values or [DEFAULT_COUNTRY]


def country_iso2(cities: pd.DataFrame, country: str) -> str | None:
    if not {"country", "iso2"}.issubset(cities.columns):
        return None
    rows = cities.loc[cities["country"].astype(str).str.casefold().eq(str(country).casefold()), "iso2"].dropna()
    if rows.empty:
        return None
    value = str(rows.iloc[0]).strip().lower()
    return value if len(value) == 2 else None


def country_locations(cities: pd.DataFrame, country: str) -> pd.DataFrame:
    required = {"country", "city_ascii", "admin_name", "lat", "lng"}
    missing = required.difference(cities.columns)
    if missing:
        raise ValueError(f"worldcities.csv is missing columns: {sorted(missing)}")
    result = (
        cities.loc[
            cities["country"].astype(str).str.casefold().eq(str(country).casefold()),
            [column for column in ["city_ascii", "admin_name", "lat", "lng", "iso2", "iso3"] if column in cities.columns],
        ]
        .rename(columns={"city_ascii": "CITY", "admin_name": "STATE"})
        .dropna(subset=["CITY", "lat", "lng"])
        .assign(
            CITY=lambda frame: frame["CITY"].astype(str).str.strip(),
            STATE=lambda frame: frame["STATE"].fillna(str(country)).astype(str).str.strip().replace("", str(country)),
            lat=lambda frame: pd.to_numeric(frame["lat"], errors="coerce"),
            lng=lambda frame: pd.to_numeric(frame["lng"], errors="coerce"),
        )
        .dropna(subset=["lat", "lng"])
        .drop_duplicates(["CITY", "STATE"], keep="first")
        .reset_index(drop=True)
    )
    return result


def country_dataset_directory(data_dir: Path, country: str) -> Path:
    return Path(data_dir) / "Datasets" / COUNTRY_DATA_DIRNAME / country_slug(country)


def resolve_climate_file(data_dir: Path, country: str) -> Path:
    """Return the canonical climate file for any country, including Mexico."""
    return country_dataset_directory(Path(data_dir), country) / COUNTRY_DATA_FILENAME


def legacy_mexico_climate_file(data_dir: Path) -> Path:
    """Return the pre-10.2 Mexico dataset path used by older releases."""
    return Path(data_dir) / "Datasets" / LEGACY_MEXICO_DATA_FILENAME


def country_update_directory(data_dir: Path, country: str) -> Path:
    """Return the standard country-specific dataset-updater workspace."""
    return Path(data_dir) / "dataset_updates" / country_slug(country)


def country_update_cache_directory(data_dir: Path, country: str) -> Path:
    """Return the standard country-specific NASA updater cache."""
    return Path(data_dir) / "cache" / "nasa_power_dataset_updates" / country_slug(country)


def _sha256(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _move_file_verified(source: Path, target: Path) -> str:
    """Move a file, falling back to a checksum-verified copy across volumes."""
    source = Path(source)
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        source.replace(target)
        return "moved"
    except OSError:
        temporary = target.with_name(target.name + ".migration.tmp")
        if temporary.exists():
            temporary.unlink()
        shutil.copy2(source, temporary)
        if source.stat().st_size != temporary.stat().st_size or _sha256(source) != _sha256(temporary):
            temporary.unlink(missing_ok=True)
            raise IOError(f"Checksum verification failed while migrating {source}")
        os.replace(temporary, target)
        source.unlink()
        return "copied-and-verified"


def _merge_directory(source: Path, target: Path, actions: list[str], warnings: list[str]) -> None:
    """Merge a legacy directory into its country folder without overwriting data."""
    source = Path(source)
    target = Path(target)
    if not source.exists():
        return
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
        actions.append(f"Moved {source} -> {target}")
        return

    target.mkdir(parents=True, exist_ok=True)
    for item in list(source.iterdir()):
        destination = target / item.name
        if not destination.exists():
            shutil.move(str(item), str(destination))
            actions.append(f"Moved {item} -> {destination}")
            continue
        if item.is_file() and destination.is_file():
            try:
                if item.stat().st_size == destination.stat().st_size and _sha256(item) == _sha256(destination):
                    item.unlink()
                    actions.append(f"Removed duplicate legacy file {item}")
                    continue
            except OSError:
                pass
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        conflict = target / f"{item.stem}_legacy_{timestamp}{item.suffix}"
        shutil.move(str(item), str(conflict))
        warnings.append(f"A conflicting legacy item was preserved as {conflict}")
    try:
        source.rmdir()
    except OSError:
        pass


def migrate_legacy_mexico_storage(data_dir: Path) -> dict[str, Any]:
    """Standardise an existing Mexico installation into country-scoped storage.

    The function is idempotent. It preserves the CSV byte-for-byte, so rows
    added through 2025 and corrected locations such as Valtierrilla are not
    transformed or re-aggregated. It also moves the legacy Mexico updater job,
    backups and root-level NASA updater cache into Mexico-specific folders.
    """
    root = Path(data_dir).resolve()
    legacy_dataset = legacy_mexico_climate_file(root)
    target_dataset = resolve_climate_file(root, DEFAULT_COUNTRY)
    actions: list[str] = []
    warnings: list[str] = []

    if legacy_dataset.exists():
        if not target_dataset.exists():
            method = _move_file_verified(legacy_dataset, target_dataset)
            actions.append(f"{method}: {legacy_dataset} -> {target_dataset}")
        else:
            try:
                identical = (
                    legacy_dataset.stat().st_size == target_dataset.stat().st_size
                    and _sha256(legacy_dataset) == _sha256(target_dataset)
                )
            except OSError:
                identical = False
            if identical:
                legacy_dataset.unlink()
                actions.append(f"Removed duplicate legacy Mexico dataset {legacy_dataset}")
            else:
                warnings.append(
                    "Both the legacy and canonical Mexico datasets exist and differ. "
                    "The canonical country file was left active and the legacy file was not deleted."
                )

    legacy_update_root = root / "dataset_updates"
    mexico_update_root = country_update_directory(root, DEFAULT_COUNTRY)
    _merge_directory(legacy_update_root / "active_job", mexico_update_root / "active_job", actions, warnings)
    _merge_directory(legacy_update_root / "backups", mexico_update_root / "backups", actions, warnings)

    legacy_cache_root = root / "cache" / "nasa_power_dataset_updates"
    mexico_cache_root = country_update_cache_directory(root, DEFAULT_COUNTRY)
    if legacy_cache_root.exists():
        mexico_cache_root.mkdir(parents=True, exist_ok=True)
        for item in list(legacy_cache_root.iterdir()):
            # Existing subfolders are country workspaces and must stay in place.
            if item.is_dir():
                continue
            destination = mexico_cache_root / item.name
            if not destination.exists():
                shutil.move(str(item), str(destination))
                actions.append(f"Moved {item} -> {destination}")
            else:
                try:
                    if item.stat().st_size == destination.stat().st_size and _sha256(item) == _sha256(destination):
                        item.unlink()
                        actions.append(f"Removed duplicate legacy cache file {item}")
                    else:
                        warnings.append(f"Conflicting cache file retained at {item}")
                except OSError as error:
                    warnings.append(f"Could not compare cache file {item}: {error}")

    target_dataset.parent.mkdir(parents=True, exist_ok=True)
    marker = target_dataset.parent / ".storage_standardisation.json"
    payload = {
        "schema": "country-storage-v1",
        "country": DEFAULT_COUNTRY,
        "canonical_dataset": str(target_dataset),
        "legacy_dataset": str(legacy_dataset),
        "dataset_exists": target_dataset.exists(),
        "actions": actions,
        "warnings": warnings,
        "completed_utc": datetime.now(timezone.utc).isoformat(),
    }
    temporary = marker.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, marker)
    return payload


def ensure_empty_country_dataset(data_dir: Path, country: str) -> Path:
    path = resolve_climate_file(data_dir, country)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=CANONICAL_COLUMNS).to_csv(path, index=False)
    return path


def read_country_dataset(data_dir: Path, country: str) -> tuple[Path, pd.DataFrame]:
    path = resolve_climate_file(data_dir, country)
    if not path.exists():
        return path, pd.DataFrame(columns=CANONICAL_COLUMNS)
    try:
        frame = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        frame = pd.DataFrame(columns=CANONICAL_COLUMNS)
    for column in CANONICAL_COLUMNS:
        if column not in frame.columns:
            frame[column] = pd.Series(dtype="float64" if column in {"Year", "Value"} else "object")
    return path, frame[CANONICAL_COLUMNS].copy()


def country_dataset_status(data_dir: Path, country: str) -> dict[str, Any]:
    path, frame = read_country_dataset(data_dir, country)
    return {
        "country": country,
        "path": str(path),
        "exists": path.exists(),
        "rows": int(len(frame)),
        "locations": int(frame[["CITY", "STATE"]].drop_duplicates().shape[0]) if not frame.empty else 0,
        "years": sorted(pd.to_numeric(frame.get("Year"), errors="coerce").dropna().astype(int).unique().tolist()) if not frame.empty else [],
    }


def configure_map_search(*, enabled: bool, restrict_country: bool, country_code: str | None) -> None:
    _MAP_SEARCH_STATE.update(
        {
            "enabled": bool(enabled),
            "restrict_country": bool(restrict_country),
            "country_code": str(country_code or "").lower() or None,
        }
    )


def install_folium_map_search() -> None:
    """Add an OpenStreetMap/Nominatim search control to every Folium map.

    The patch is intentionally applied once and only affects maps created after
    installation. It avoids having to duplicate search-control code across the
    application's many independent mapping modules.
    """
    global _MAP_PATCHED, _ORIGINAL_FOLIUM_MAP_INIT
    if _MAP_PATCHED:
        return
    import folium
    from folium.plugins import Geocoder

    _ORIGINAL_FOLIUM_MAP_INIT = folium.Map.__init__

    def patched_init(self, *args, **kwargs):
        _ORIGINAL_FOLIUM_MAP_INIT(self, *args, **kwargs)
        if not _MAP_SEARCH_STATE.get("enabled", True):
            return
        provider_options: dict[str, Any] = {
            "geocodingQueryParams": {"accept-language": "en"},
        }
        code = _MAP_SEARCH_STATE.get("country_code")
        if _MAP_SEARCH_STATE.get("restrict_country", True) and code:
            provider_options["geocodingQueryParams"]["countrycodes"] = code
        try:
            Geocoder(
                collapsed=False,
                position="topright",
                add_marker=True,
                zoom=14,
                provider="nominatim",
                provider_options=provider_options,
                placeholder=str(_MAP_SEARCH_STATE.get("placeholder") or "Search a place…"),
            ).add_to(self)
        except Exception:
            # A map must remain usable even if the optional control cannot load.
            pass

    folium.Map.__init__ = patched_init
    _MAP_PATCHED = True


def country_summary(cities: pd.DataFrame, country: str) -> dict[str, Any]:
    locations = country_locations(cities, country)
    if locations.empty:
        return {"country": country, "locations": 0, "states": 0, "centre_lat": 0.0, "centre_lon": 0.0}
    return {
        "country": country,
        "locations": int(len(locations)),
        "states": int(locations["STATE"].nunique()),
        "centre_lat": float(locations["lat"].median()),
        "centre_lon": float(locations["lng"].median()),
    }
