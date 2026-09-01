"""Sentinel-2 satellite crop monitoring for the AgroLattice app.

The module uses resilient STAC catalogue discovery for Sentinel-2 Level-2A,
trying Element 84 Earth Search first and Microsoft Planetary Computer as an
automatic fallback. It reads only the required raster windows from cloud-hosted
Cloud-Optimized GeoTIFF assets. It supports field polygons or point buffers, SCL-based cloud
masking, vegetation-index time series, image previews, historical anomalies,
and comparison with the app's daily phenology and root-zone water-balance
outputs.

Scientific scope
----------------
* Optical vegetation indices are observational indicators, not direct yield or
  causal stress measurements.
* Sentinel-2 pixels and the selected field geometry define the spatial support.
* Pixel-level quality is assessed from the Level-2A Scene Classification Layer
  where available; scene cloud percentage is only a search filter.
* Public STAC services are best-effort; automatic provider failover is used when one catalogue is unavailable.
"""

from __future__ import annotations

import hashlib
import io
import json
import math
import os
import shutil
import time
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence
from urllib.parse import parse_qs, unquote, urlparse

import numpy as np
import pandas as pd
import requests

try:
    from PIL import Image
except Exception:  # pragma: no cover - optional dependency check
    Image = None

try:
    from shapely.geometry import Point, mapping, shape
    from shapely.ops import transform as shapely_transform, unary_union
    from shapely.validation import make_valid
except Exception:  # pragma: no cover
    Point = mapping = shape = shapely_transform = unary_union = make_valid = None

try:
    from pyproj import CRS, Geod, Transformer
except Exception:  # pragma: no cover
    CRS = Geod = Transformer = None

try:
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.features import geometry_mask
    from rasterio.transform import array_bounds, from_origin
    from rasterio.warp import reproject, transform_bounds, transform_geom
except Exception:  # pragma: no cover
    rasterio = None
    Resampling = geometry_mask = array_bounds = from_origin = None
    reproject = transform_bounds = transform_geom = None

try:
    import matplotlib
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover
    matplotlib = plt = None


EARTH_SEARCH_STAC_URL = "https://earth-search.aws.element84.com/v1"
EARTH_SEARCH_SEARCH_URL = f"{EARTH_SEARCH_STAC_URL}/search"
PLANETARY_COMPUTER_STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
PLANETARY_COMPUTER_SEARCH_URL = f"{PLANETARY_COMPUTER_STAC_URL}/search"
PLANETARY_COMPUTER_SAS_TOKEN_URL = (
    "https://planetarycomputer.microsoft.com/api/sas/v1/token/sentinel-2-l2a"
)
SENTINEL_COLLECTIONS = ["sentinel-2-c1-l2a", "sentinel-2-l2a"]
PLANETARY_COMPUTER_COLLECTIONS = ["sentinel-2-l2a"]
STAC_PROVIDERS = {
    "Earth Search": {
        "catalog": EARTH_SEARCH_STAC_URL,
        "search": EARTH_SEARCH_SEARCH_URL,
        "collections": SENTINEL_COLLECTIONS,
    },
    "Planetary Computer": {
        "catalog": PLANETARY_COMPUTER_STAC_URL,
        "search": PLANETARY_COMPUTER_SEARCH_URL,
        "collections": PLANETARY_COMPUTER_COLLECTIONS,
    },
}
MODULE_VERSION = "1.1.0"

_PC_SAS_CACHE: dict[str, Any] = {"token": None, "expires_at": 0.0}

SCL_CLASSES = {
    0: "No data",
    1: "Saturated or defective",
    2: "Cast shadow / dark feature",
    3: "Cloud shadow",
    4: "Vegetation",
    5: "Not vegetated",
    6: "Water",
    7: "Unclassified",
    8: "Cloud, medium probability",
    9: "Cloud, high probability",
    10: "Thin cirrus",
    11: "Snow or ice",
}
DEFAULT_EXCLUDED_SCL = {0, 1, 2, 3, 6, 8, 9, 10, 11}

INDEX_REGISTRY: dict[str, dict[str, Any]] = {
    "NDVI": {
        "label": "Normalised Difference Vegetation Index",
        "bands": ["nir", "red"],
        "formula": "(NIR - Red) / (NIR + Red)",
        "range": (-1.0, 1.0),
        "interpretation": "General canopy greenness and photosynthetically active vegetation.",
    },
    "EVI": {
        "label": "Enhanced Vegetation Index",
        "bands": ["nir", "red", "blue"],
        "formula": "2.5 × (NIR - Red) / (NIR + 6 Red - 7.5 Blue + 1)",
        "range": (-1.0, 1.0),
        "interpretation": "Vegetation activity with reduced soil and dense-canopy saturation effects.",
    },
    "NDMI": {
        "label": "Normalised Difference Moisture Index",
        "bands": ["nir", "swir16"],
        "formula": "(NIR - SWIR1) / (NIR + SWIR1)",
        "range": (-1.0, 1.0),
        "interpretation": "Canopy and vegetation moisture condition; not direct root-zone soil moisture.",
    },
    "NDRE": {
        "label": "Normalised Difference Red Edge Index",
        "bands": ["nir_narrow", "rededge1"],
        "formula": "(Narrow NIR - Red edge 1) / (Narrow NIR + Red edge 1)",
        "range": (-1.0, 1.0),
        "interpretation": "Red-edge chlorophyll and crop-condition indicator.",
    },
}

ASSET_ALIASES: dict[str, tuple[str, ...]] = {
    "blue": ("blue", "b02", "band02", "coastal_blue"),
    "green": ("green", "b03", "band03"),
    "red": ("red", "b04", "band04"),
    "rededge1": ("rededge1", "rededge", "b05", "band05"),
    "nir": ("nir", "nir08", "b08", "band08"),
    "nir_narrow": ("nir09", "nir08a", "narrow_nir", "b8a", "band8a"),
    "swir16": ("swir16", "swir1", "b11", "band11"),
    "scl": ("scl", "scene_classification", "scene-classification"),
    "visual": ("visual", "true_color", "tci"),
}

COMMON_NAME_TO_ROLE = {
    "blue": "blue",
    "green": "green",
    "red": "red",
    "nir": "nir",
    "nir08": "nir",
    "nir09": "nir_narrow",
    "rededge": "rededge1",
    "swir16": "swir16",
}


class SatelliteMonitoringError(RuntimeError):
    """Raised when a satellite search or raster analysis cannot be completed."""


@dataclass(frozen=True)
class SatelliteSearchConfig:
    start_date: str
    end_date: str
    maximum_scene_cloud_percent: float = 40.0
    maximum_items: int = 250
    collections: tuple[str, ...] = tuple(SENTINEL_COLLECTIONS)
    provider_preference: str = "Automatic"


@dataclass(frozen=True)
class RasterGrid:
    crs: Any
    transform: Any
    width: int
    height: int
    geometry_projected: dict[str, Any]
    polygon_mask: np.ndarray
    bounds_wgs84: tuple[float, float, float, float]
    resolution_m: float


# -----------------------------------------------------------------------------
# Dependency and geometry helpers
# -----------------------------------------------------------------------------


def dependency_status() -> dict[str, bool]:
    return {
        "requests": requests is not None,
        "Pillow": Image is not None,
        "shapely": shape is not None,
        "pyproj": Transformer is not None,
        "rasterio": rasterio is not None,
        "matplotlib": plt is not None,
    }


def require_satellite_stack() -> None:
    missing = [name for name, available in dependency_status().items() if not available]
    if missing:
        raise SatelliteMonitoringError(
            "Satellite monitoring requires additional geospatial packages: "
            + ", ".join(missing)
            + ". Run INSTALL_DEPENDENCIES.bat or install requirements_ml_agriculture.txt."
        )


def _normalise_geojson_object(value: Mapping[str, Any]) -> dict[str, Any]:
    require_satellite_stack()
    obj_type = str(value.get("type", ""))
    if obj_type == "Feature":
        geometry = value.get("geometry")
        if not geometry:
            raise SatelliteMonitoringError("The GeoJSON feature has no geometry.")
        return dict(geometry)
    if obj_type == "FeatureCollection":
        geometries = [feature.get("geometry") for feature in value.get("features", []) if feature.get("geometry")]
        if not geometries:
            raise SatelliteMonitoringError("The GeoJSON feature collection contains no geometries.")
        combined = unary_union([shape(geometry) for geometry in geometries])
        if combined.geom_type not in {"Polygon", "MultiPolygon"}:
            combined = combined.convex_hull
        return mapping(combined)
    if obj_type in {"Polygon", "MultiPolygon"}:
        return dict(value)
    raise SatelliteMonitoringError("Use a Polygon, MultiPolygon, Feature, or FeatureCollection GeoJSON object.")


def validate_aoi_geometry(value: Mapping[str, Any]) -> dict[str, Any]:
    geometry = _normalise_geojson_object(value)
    geom = shape(geometry)
    if geom.is_empty:
        raise SatelliteMonitoringError("The selected area is empty.")
    if not geom.is_valid:
        geom = make_valid(geom)
    if geom.geom_type not in {"Polygon", "MultiPolygon"}:
        geom = geom.convex_hull
    minx, miny, maxx, maxy = geom.bounds
    if not (-180 <= minx <= 180 and -180 <= maxx <= 180 and -90 <= miny <= 90 and -90 <= maxy <= 90):
        raise SatelliteMonitoringError("The area must use WGS84 longitude/latitude coordinates.")
    return mapping(geom)


def geometry_from_point_buffer(latitude: float, longitude: float, radius_m: float) -> dict[str, Any]:
    require_satellite_stack()
    latitude = float(latitude)
    longitude = float(longitude)
    radius_m = float(radius_m)
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise SatelliteMonitoringError("Invalid point coordinates.")
    if radius_m <= 0:
        raise SatelliteMonitoringError("Buffer radius must be positive.")
    zone = int(math.floor((longitude + 180.0) / 6.0) + 1)
    epsg = 32600 + zone if latitude >= 0 else 32700 + zone
    to_projected = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
    to_wgs84 = Transformer.from_crs(f"EPSG:{epsg}", "EPSG:4326", always_xy=True)
    point_projected = shapely_transform(to_projected.transform, Point(longitude, latitude))
    buffered = point_projected.buffer(radius_m, resolution=48)
    return mapping(shapely_transform(to_wgs84.transform, buffered))


def geometry_area_hectares(geometry: Mapping[str, Any]) -> float:
    require_satellite_stack()
    geom = shape(validate_aoi_geometry(geometry))
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)
    projected = shapely_transform(transformer.transform, geom)
    return float(projected.area / 10000.0)


def geometry_centroid(geometry: Mapping[str, Any]) -> tuple[float, float]:
    geom = shape(validate_aoi_geometry(geometry))
    centroid = geom.centroid
    return float(centroid.y), float(centroid.x)


def geometry_hash(geometry: Mapping[str, Any]) -> str:
    normalised = json.dumps(validate_aoi_geometry(geometry), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()[:20]


def geometry_geojson_bytes(geometry: Mapping[str, Any], properties: Mapping[str, Any] | None = None) -> bytes:
    feature = {
        "type": "Feature",
        "properties": dict(properties or {}),
        "geometry": validate_aoi_geometry(geometry),
    }
    return json.dumps(feature, indent=2, ensure_ascii=False).encode("utf-8")


# -----------------------------------------------------------------------------
# STAC discovery and scene selection
# -----------------------------------------------------------------------------


def _request_with_retries(
    method: str,
    url: str,
    *,
    json_payload: Mapping[str, Any] | None = None,
    timeout_seconds: int = 60,
    attempts: int = 4,
) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(max(1, attempts)):
        try:
            response = requests.request(
                method,
                url,
                json=json_payload,
                timeout=timeout_seconds,
                headers={"User-Agent": f"MexicoAgroclimateSatellite/{MODULE_VERSION}"},
            )
            if response.status_code in {429, 500, 502, 503, 504} and attempt < attempts - 1:
                time.sleep(min(20.0, 1.5 * (2**attempt)))
                continue
            response.raise_for_status()
            return response
        except Exception as error:
            last_error = error
            if attempt < attempts - 1:
                time.sleep(min(20.0, 1.5 * (2**attempt)))
    raise SatelliteMonitoringError(f"STAC request failed after {attempts} attempts: {last_error}")


def _normalise_provider_preference(value: str | None) -> str:
    token = str(value or "Automatic").strip().casefold()
    if "planet" in token or "microsoft" in token:
        return "Planetary Computer"
    if "earth" in token or "element" in token:
        return "Earth Search"
    return "Automatic"


def _provider_order(preference: str | None) -> list[str]:
    resolved = _normalise_provider_preference(preference)
    if resolved == "Earth Search":
        return ["Earth Search"]
    if resolved == "Planetary Computer":
        return ["Planetary Computer"]
    return ["Earth Search", "Planetary Computer"]


def scene_provider(item: Mapping[str, Any]) -> str:
    provider = item.get("_agroclimate_provider")
    if provider:
        return str(provider)
    links = item.get("links", [])
    for link in links if isinstance(links, list) else []:
        href = str(link.get("href", "")).casefold()
        if "planetarycomputer.microsoft.com" in href:
            return "Planetary Computer"
        if "earth-search.aws.element84.com" in href:
            return "Earth Search"
    for asset in (item.get("assets", {}) or {}).values():
        href = str(asset.get("href", "")).casefold()
        if "blob.core.windows.net" in href or "planetarycomputer.microsoft.com" in href:
            return "Planetary Computer"
        if "amazonaws.com" in href:
            return "Earth Search"
    return "Unknown"


def scene_catalog_url(item: Mapping[str, Any]) -> str:
    provider = scene_provider(item)
    return str(STAC_PROVIDERS.get(provider, {}).get("catalog", ""))


def _annotate_provider(
    features: Sequence[Mapping[str, Any]],
    provider: str,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for feature in features:
        candidate = dict(feature)
        candidate["_agroclimate_provider"] = provider
        candidate["_agroclimate_catalog"] = STAC_PROVIDERS[provider]["catalog"]
        output.append(candidate)
    return output


def _search_provider(
    provider: str,
    geometry: Mapping[str, Any],
    start: pd.Timestamp,
    end: pd.Timestamp,
    config: SatelliteSearchConfig,
) -> list[dict[str, Any]]:
    provider_info = STAC_PROVIDERS[provider]
    collections = (
        list(config.collections)
        if provider == "Earth Search"
        else list(provider_info["collections"])
    )
    payload: dict[str, Any] = {
        "collections": collections,
        "intersects": geometry,
        "datetime": (
            f"{start.strftime('%Y-%m-%dT00:00:00Z')}/"
            f"{end.strftime('%Y-%m-%dT23:59:59Z')}"
        ),
        "limit": min(1000, max(1, int(config.maximum_items))),
        "query": {
            "eo:cloud_cover": {
                "lte": float(config.maximum_scene_cloud_percent)
            }
        },
    }
    # Earth Search supports server-side sorting. Omitting it for Planetary
    # Computer maximises compatibility; results are sorted client-side.
    if provider == "Earth Search":
        payload["sortby"] = [
            {"field": "properties.datetime", "direction": "asc"}
        ]

    response = _request_with_retries(
        "POST",
        str(provider_info["search"]),
        json_payload=payload,
        timeout_seconds=75,
        attempts=4,
    )
    data = response.json()
    features = data.get("features", [])
    if not isinstance(features, list):
        raise SatelliteMonitoringError(
            f"{provider} returned a STAC response without a feature list."
        )
    return _annotate_provider(features, provider)


def search_sentinel2_scenes(
    geometry: Mapping[str, Any],
    config: SatelliteSearchConfig,
) -> list[dict[str, Any]]:
    geometry = validate_aoi_geometry(geometry)
    start = pd.Timestamp(config.start_date)
    end = pd.Timestamp(config.end_date)
    if pd.isna(start) or pd.isna(end) or start > end:
        raise SatelliteMonitoringError("The satellite-search date range is invalid.")

    errors: list[str] = []
    for provider in _provider_order(config.provider_preference):
        try:
            features = _search_provider(provider, geometry, start, end, config)
            return deduplicate_scenes(features)
        except Exception as error:
            errors.append(f"{provider}: {type(error).__name__}: {error}")

    raise SatelliteMonitoringError(
        "All configured Sentinel-2 STAC catalogues failed. "
        + " | ".join(errors)
        + ". This is normally a temporary catalogue-service problem. "
          "Retry later or select a specific provider in the search controls."
    )


def _scene_datetime(item: Mapping[str, Any]) -> pd.Timestamp:
    value = item.get("properties", {}).get("datetime") or item.get("properties", {}).get("start_datetime")
    return pd.to_datetime(value, utc=True, errors="coerce")


def _scene_tile(item: Mapping[str, Any]) -> str:
    props = item.get("properties", {})
    return str(props.get("grid:code") or props.get("s2:mgrs_tile") or props.get("mgrs:utm_zone") or "unknown")


def _scene_cloud(item: Mapping[str, Any]) -> float:
    return float(pd.to_numeric(item.get("properties", {}).get("eo:cloud_cover"), errors="coerce"))


def deduplicate_scenes(items: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Prefer Collection-1 scenes when duplicate acquisition/tile records exist."""
    candidates: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in items:
        timestamp = _scene_datetime(item)
        if pd.isna(timestamp):
            continue
        key = (timestamp.strftime("%Y-%m-%dT%H:%M"), _scene_tile(item), str(item.get("properties", {}).get("platform", "")))
        current = candidates.get(key)
        if current is None:
            candidates[key] = dict(item)
            continue
        current_collection = str(current.get("collection", ""))
        new_collection = str(item.get("collection", ""))
        if new_collection == "sentinel-2-c1-l2a" and current_collection != "sentinel-2-c1-l2a":
            candidates[key] = dict(item)
        elif _scene_cloud(item) < _scene_cloud(current):
            candidates[key] = dict(item)
    return sorted(candidates.values(), key=lambda item: (_scene_datetime(item), _scene_cloud(item)))


def scene_catalog_table(items: Sequence[Mapping[str, Any]]) -> pd.DataFrame:
    rows = []
    for item in items:
        props = item.get("properties", {})
        timestamp = _scene_datetime(item)
        rows.append(
            {
                "Scene ID": item.get("id"),
                "Date": timestamp.date() if not pd.isna(timestamp) else pd.NaT,
                "Acquisition UTC": timestamp.isoformat() if not pd.isna(timestamp) else None,
                "Provider": scene_provider(item),
                "Collection": item.get("collection"),
                "Platform": props.get("platform"),
                "Tile": _scene_tile(item),
                "Scene cloud (%)": pd.to_numeric(props.get("eo:cloud_cover"), errors="coerce"),
                "No-data pixels (%)": pd.to_numeric(props.get("s2:nodata_pixel_percentage"), errors="coerce"),
                "Processing baseline": props.get("s2:processing_baseline"),
            }
        )
    return pd.DataFrame(rows).sort_values(["Date", "Scene cloud (%)"], na_position="last").reset_index(drop=True) if rows else pd.DataFrame()


def select_scene_subset(
    items: Sequence[Mapping[str, Any]],
    method: str,
    maximum_scenes: int,
) -> list[dict[str, Any]]:
    scenes = list(items)
    maximum_scenes = max(1, int(maximum_scenes))
    if not scenes:
        return []
    method_key = method.casefold()
    if "month" in method_key:
        frame = scene_catalog_table(scenes)
        frame["Month"] = pd.to_datetime(frame["Date"]).dt.to_period("M")
        selected_ids = (
            frame.sort_values(["Month", "Scene cloud (%)", "Date"])
            .groupby("Month", as_index=False)
            .head(1)["Scene ID"]
            .tolist()
        )
        selected = [dict(item) for item in scenes if item.get("id") in selected_ids]
    elif "lowest" in method_key:
        selected = sorted(scenes, key=_scene_cloud)[:maximum_scenes]
        selected = sorted(selected, key=_scene_datetime)
    elif len(scenes) > maximum_scenes:
        positions = np.linspace(0, len(scenes) - 1, maximum_scenes).round().astype(int)
        selected = [dict(scenes[position]) for position in sorted(set(positions.tolist()))]
    else:
        selected = [dict(item) for item in scenes]
    if len(selected) > maximum_scenes:
        selected = selected[:maximum_scenes]
    return selected


# -----------------------------------------------------------------------------
# STAC asset resolution and raster processing
# -----------------------------------------------------------------------------


def _normalised_token(value: Any) -> str:
    return str(value or "").casefold().replace("-", "_").replace(" ", "_")


def _planetary_computer_token(force_refresh: bool = False) -> str:
    now = time.time()
    cached_token = _PC_SAS_CACHE.get("token")
    cached_expiry = float(_PC_SAS_CACHE.get("expires_at") or 0.0)
    if cached_token and not force_refresh and now < cached_expiry - 120:
        return str(cached_token)

    response = _request_with_retries(
        "GET",
        PLANETARY_COMPUTER_SAS_TOKEN_URL,
        timeout_seconds=45,
        attempts=4,
    )
    payload = response.json()
    token = str(payload.get("token") or "").lstrip("?")
    if not token:
        raise SatelliteMonitoringError(
            "Planetary Computer returned no Sentinel-2 data-access token."
        )

    # Tokens normally carry an expiry timestamp. Use it when available, with
    # a conservative one-hour fallback cache.
    expires_at = now + 3600
    expiry_text = payload.get("msft:expiry")
    if expiry_text:
        expiry = pd.to_datetime(expiry_text, utc=True, errors="coerce")
        if not pd.isna(expiry):
            expires_at = float(expiry.timestamp())
    else:
        parsed = parse_qs(token)
        expiry_values = parsed.get("se")
        if expiry_values:
            expiry = pd.to_datetime(
                unquote(expiry_values[0]), utc=True, errors="coerce"
            )
            if not pd.isna(expiry):
                expires_at = float(expiry.timestamp())

    _PC_SAS_CACHE["token"] = token
    _PC_SAS_CACHE["expires_at"] = expires_at
    return token


def _sign_planetary_computer_href(href: str) -> str:
    value = str(href)
    if "blob.core.windows.net" not in value.casefold():
        return value
    query = parse_qs(urlparse(value).query)
    if "sig" in query:
        return value
    token = _planetary_computer_token()
    separator = "&" if "?" in value else "?"
    return f"{value}{separator}{token}"


def resolve_scene_assets(item: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    assets = item.get("assets", {})
    resolved: dict[str, dict[str, Any]] = {}

    # First pass: metadata common names and exact aliases.
    for key, asset in assets.items():
        href = str(asset.get("href", ""))
        if not href.startswith(("https://", "http://")):
            continue
        key_token = _normalised_token(key)
        title_token = _normalised_token(asset.get("title"))
        role_tokens = {_normalised_token(role) for role in asset.get("roles", [])}
        band_entries = asset.get("eo:bands") or []
        band_tokens: set[str] = set()
        for band in band_entries:
            band_tokens.update({_normalised_token(band.get("name")), _normalised_token(band.get("common_name"))})
        tokens = {key_token, title_token, *role_tokens, *band_tokens}

        for role, aliases in ASSET_ALIASES.items():
            alias_tokens = {_normalised_token(alias) for alias in aliases}
            if tokens.intersection(alias_tokens):
                existing = resolved.get(role)
                # Prefer GeoTIFF/COG assets and shorter, exact key matches.
                score = 0
                asset_type = str(asset.get("type", "")).casefold()
                if "geotiff" in asset_type or href.casefold().endswith((".tif", ".tiff")):
                    score += 4
                if key_token in alias_tokens:
                    score += 3
                if href.startswith("https://"):
                    score += 1
                candidate = dict(asset)
                candidate["_key"] = key
                candidate["_score"] = score
                if existing is None or score > existing.get("_score", -1):
                    resolved[role] = candidate

    # Second pass: looser key/title matching for SCL and specific bands.
    for key, asset in assets.items():
        href = str(asset.get("href", ""))
        if not href.startswith(("https://", "http://")):
            continue
        combined = " ".join([_normalised_token(key), _normalised_token(asset.get("title")), href.casefold()])
        guesses = {
            "scl": ["scl", "scene_classification"],
            "nir_narrow": ["b8a", "nir09", "nir_09"],
            "rededge1": ["b05", "rededge1", "red_edge_1"],
            "swir16": ["b11", "swir16", "swir_16"],
        }
        for role, needles in guesses.items():
            if role not in resolved and any(needle in combined for needle in needles):
                candidate = dict(asset)
                candidate["_key"] = key
                candidate["_score"] = 1
                resolved[role] = candidate

    if scene_provider(item) == "Planetary Computer":
        signed: dict[str, dict[str, Any]] = {}
        for role, asset in resolved.items():
            candidate = dict(asset)
            candidate["href"] = _sign_planetary_computer_href(
                str(candidate.get("href", ""))
            )
            signed[role] = candidate
        resolved = signed

    return resolved


def _asset_scale_offset(asset: Mapping[str, Any]) -> tuple[float, float]:
    bands = asset.get("raster:bands") or []
    if bands and isinstance(bands[0], Mapping):
        scale = pd.to_numeric(bands[0].get("scale", 1.0), errors="coerce")
        offset = pd.to_numeric(bands[0].get("offset", 0.0), errors="coerce")
        return (float(scale) if np.isfinite(scale) else 1.0, float(offset) if np.isfinite(offset) else 0.0)
    return 1.0, 0.0


def _raster_env():
    if rasterio is None:
        raise SatelliteMonitoringError("rasterio is not installed.")
    return rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.TIF,.tiff,.TIFF",
        GDAL_HTTP_MULTIRANGE="YES",
        GDAL_HTTP_MERGE_CONSECUTIVE_RANGES="YES",
        VSI_CACHE="TRUE",
        VSI_CACHE_SIZE="50000000",
        AWS_NO_SIGN_REQUEST="YES",
        GDAL_HTTP_TIMEOUT="60",
        GDAL_HTTP_MAX_RETRY="3",
        GDAL_HTTP_RETRY_DELAY="2",
    )


def _build_reference_grid(
    reference_asset: Mapping[str, Any],
    geometry: Mapping[str, Any],
    resolution_m: float,
    maximum_pixels: int,
) -> RasterGrid:
    href = str(reference_asset.get("href"))
    with _raster_env(), rasterio.open(href) as src:
        if src.crs is None:
            raise SatelliteMonitoringError("The Sentinel-2 asset has no coordinate reference system.")
        projected_geometry = transform_geom("EPSG:4326", src.crs, validate_aoi_geometry(geometry), precision=7)
        projected_shape = shape(projected_geometry)
        intersection = projected_shape.intersection(shape({
            "type": "Polygon",
            "coordinates": [[
                [src.bounds.left, src.bounds.bottom],
                [src.bounds.right, src.bounds.bottom],
                [src.bounds.right, src.bounds.top],
                [src.bounds.left, src.bounds.top],
                [src.bounds.left, src.bounds.bottom],
            ]],
        }))
        if intersection.is_empty:
            raise SatelliteMonitoringError("The scene does not overlap the selected area after reprojection.")
        left, bottom, right, top = intersection.bounds
        resolution = float(max(10.0, resolution_m))
        left = math.floor(left / resolution) * resolution
        bottom = math.floor(bottom / resolution) * resolution
        right = math.ceil(right / resolution) * resolution
        top = math.ceil(top / resolution) * resolution
        width = max(1, int(math.ceil((right - left) / resolution)))
        height = max(1, int(math.ceil((top - bottom) / resolution)))
        if width * height > int(maximum_pixels):
            raise SatelliteMonitoringError(
                f"The requested area would require {width * height:,} pixels at {resolution:.0f} m resolution. "
                "Use a smaller polygon, a smaller point buffer, or a coarser analysis resolution."
            )
        transform = from_origin(left, top, resolution, resolution)
        polygon_mask = geometry_mask(
            [projected_geometry],
            out_shape=(height, width),
            transform=transform,
            invert=True,
            all_touched=False,
        )
        bounds = array_bounds(height, width, transform)
        west, south, east, north = transform_bounds(src.crs, "EPSG:4326", *bounds, densify_pts=21)
        return RasterGrid(
            crs=src.crs,
            transform=transform,
            width=width,
            height=height,
            geometry_projected=projected_geometry,
            polygon_mask=polygon_mask,
            bounds_wgs84=(west, south, east, north),
            resolution_m=resolution,
        )


def _read_asset_to_grid(
    asset: Mapping[str, Any],
    grid: RasterGrid,
    *,
    categorical: bool = False,
) -> np.ndarray:
    href = str(asset.get("href"))
    destination = np.full((grid.height, grid.width), np.nan, dtype="float32")
    with _raster_env(), rasterio.open(href) as src:
        reproject(
            source=rasterio.band(src, 1),
            destination=destination,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=src.nodata,
            dst_transform=grid.transform,
            dst_crs=grid.crs,
            dst_nodata=np.nan,
            resampling=Resampling.nearest if categorical else Resampling.bilinear,
            num_threads=2,
        )
    if not categorical:
        scale, offset = _asset_scale_offset(asset)
        destination = destination.astype("float32") * scale + offset
        finite = destination[np.isfinite(destination)]
        if finite.size and np.nanpercentile(np.abs(finite), 95) > 2.0 and scale == 1.0 and offset == 0.0:
            destination = destination / 10000.0
    destination[~grid.polygon_mask] = np.nan
    return destination


def _safe_index(numerator: np.ndarray, denominator: np.ndarray, low: float = -1.0, high: float = 1.0) -> np.ndarray:
    result = np.full(numerator.shape, np.nan, dtype="float32")
    valid = np.isfinite(numerator) & np.isfinite(denominator) & (np.abs(denominator) > 1e-8)
    result[valid] = numerator[valid] / denominator[valid]
    result[(result < low) | (result > high)] = np.nan
    return result


def calculate_indices(bands: Mapping[str, np.ndarray], index_names: Sequence[str]) -> dict[str, np.ndarray]:
    output: dict[str, np.ndarray] = {}
    for name in index_names:
        if name == "NDVI":
            output[name] = _safe_index(bands["nir"] - bands["red"], bands["nir"] + bands["red"])
        elif name == "EVI":
            numerator = 2.5 * (bands["nir"] - bands["red"])
            denominator = bands["nir"] + 6.0 * bands["red"] - 7.5 * bands["blue"] + 1.0
            output[name] = _safe_index(numerator, denominator, low=-2.0, high=2.0)
        elif name == "NDMI":
            output[name] = _safe_index(bands["nir"] - bands["swir16"], bands["nir"] + bands["swir16"])
        elif name == "NDRE":
            output[name] = _safe_index(
                bands["nir_narrow"] - bands["rededge1"],
                bands["nir_narrow"] + bands["rededge1"],
            )
        else:
            raise SatelliteMonitoringError(f"Unsupported vegetation index: {name}")
    return output


def _clear_pixel_mask(
    grid: RasterGrid,
    bands: Mapping[str, np.ndarray],
    scl: np.ndarray | None,
    excluded_scl_classes: set[int],
) -> tuple[np.ndarray, dict[str, float]]:
    valid = grid.polygon_mask.copy()
    for band in bands.values():
        valid &= np.isfinite(band)
        valid &= band > -0.2
        valid &= band < 1.6
    scl_percentages: dict[str, float] = {}
    polygon_count = int(np.count_nonzero(grid.polygon_mask))
    if scl is not None:
        scl_rounded = np.where(np.isfinite(scl), np.rint(scl), -999).astype("int16", copy=False)
        for class_id, class_name in SCL_CLASSES.items():
            count = int(np.count_nonzero(grid.polygon_mask & (scl_rounded == class_id)))
            scl_percentages[f"SCL {class_id}: {class_name} (%)"] = 100.0 * count / polygon_count if polygon_count else np.nan
        valid &= ~np.isin(scl_rounded, list(excluded_scl_classes))
    return valid, scl_percentages


def _numeric_statistics(values: np.ndarray) -> dict[str, float]:
    data = values[np.isfinite(values)]
    if data.size == 0:
        return {"Mean": np.nan, "Median": np.nan, "Std": np.nan, "P10": np.nan, "P90": np.nan}
    return {
        "Mean": float(np.nanmean(data)),
        "Median": float(np.nanmedian(data)),
        "Std": float(np.nanstd(data, ddof=1)) if data.size > 1 else 0.0,
        "P10": float(np.nanpercentile(data, 10)),
        "P90": float(np.nanpercentile(data, 90)),
    }


def _scene_cache_key(
    item: Mapping[str, Any],
    geometry: Mapping[str, Any],
    indices: Sequence[str],
    resolution_m: float,
    excluded_scl_classes: Iterable[int],
) -> str:
    payload = {
        "scene": item.get("id"),
        "provider": scene_provider(item),
        "collection": item.get("collection"),
        "geometry": geometry_hash(geometry),
        "indices": sorted(indices),
        "resolution_m": float(resolution_m),
        "excluded_scl": sorted(int(value) for value in excluded_scl_classes),
        "version": MODULE_VERSION,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if value is pd.NA:
        return None
    return value


def process_scene(
    item: Mapping[str, Any],
    geometry: Mapping[str, Any],
    index_names: Sequence[str],
    cache_dir: str | Path,
    *,
    resolution_m: float = 20.0,
    minimum_usable_pixel_percent: float = 20.0,
    excluded_scl_classes: set[int] | None = None,
    maximum_pixels: int = 2_000_000,
    force_refresh: bool = False,
) -> dict[str, Any]:
    require_satellite_stack()
    geometry = validate_aoi_geometry(geometry)
    index_names = [name for name in index_names if name in INDEX_REGISTRY]
    if not index_names:
        raise SatelliteMonitoringError("Select at least one vegetation index.")
    excluded = set(DEFAULT_EXCLUDED_SCL if excluded_scl_classes is None else excluded_scl_classes)
    cache_root = Path(cache_dir)
    cache_root.mkdir(parents=True, exist_ok=True)
    cache_key = _scene_cache_key(item, geometry, index_names, resolution_m, excluded)
    cache_path = cache_root / f"{cache_key}.json"
    if cache_path.exists() and not force_refresh:
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            cached["Loaded from cache"] = True
            return cached
        except Exception:
            cache_path.unlink(missing_ok=True)

    assets = resolve_scene_assets(item)
    required_roles = sorted({role for name in index_names for role in INDEX_REGISTRY[name]["bands"]})
    missing = [role for role in required_roles if role not in assets]
    if missing:
        raise SatelliteMonitoringError(
            f"Scene {item.get('id')} lacks required assets: {', '.join(missing)}. "
            f"Available resolved assets: {', '.join(sorted(assets)) or 'none'}."
        )

    reference_role = "red" if "red" in assets else required_roles[0]
    grid = _build_reference_grid(assets[reference_role], geometry, resolution_m, maximum_pixels)
    band_arrays = {role: _read_asset_to_grid(assets[role], grid) for role in required_roles}
    scl_array = _read_asset_to_grid(assets["scl"], grid, categorical=True) if "scl" in assets else None
    clear_mask, scl_percentages = _clear_pixel_mask(grid, band_arrays, scl_array, excluded)
    polygon_pixels = int(np.count_nonzero(grid.polygon_mask))
    usable_pixels = int(np.count_nonzero(clear_mask))
    usable_percent = 100.0 * usable_pixels / polygon_pixels if polygon_pixels else 0.0

    indices = calculate_indices(band_arrays, index_names)
    result: dict[str, Any] = {
        "Scene ID": item.get("id"),
        "Collection": item.get("collection"),
        "Acquisition UTC": _scene_datetime(item).isoformat(),
        "Date": _scene_datetime(item).date().isoformat(),
        "Platform": item.get("properties", {}).get("platform"),
        "Tile": _scene_tile(item),
        "Scene cloud (%)": _scene_cloud(item),
        "Field usable pixels (%)": usable_percent,
        "Field polygon pixels": polygon_pixels,
        "Field usable pixels": usable_pixels,
        "Analysis resolution (m)": float(grid.resolution_m),
        "SCL available": scl_array is not None,
        "Raster bounds WGS84": list(grid.bounds_wgs84),
        "Status": "Usable" if usable_percent >= minimum_usable_pixel_percent else "Insufficient clear pixels",
        "Loaded from cache": False,
        "Resolved asset keys": {role: assets[role].get("_key") for role in sorted(assets)},
    }
    result.update(scl_percentages)

    for name, array in indices.items():
        masked = np.where(clear_mask, array, np.nan)
        stats = _numeric_statistics(masked)
        for statistic, value in stats.items():
            result[f"{name} {statistic}"] = value
        result[f"{name} vegetation pixels > 0.2 (%)"] = (
            100.0 * np.count_nonzero(np.isfinite(masked) & (masked > 0.2)) / usable_pixels if usable_pixels else np.nan
        )

    cache_path.write_text(json.dumps(_json_safe(result), indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def process_scene_collection(
    items: Sequence[Mapping[str, Any]],
    geometry: Mapping[str, Any],
    index_names: Sequence[str],
    cache_dir: str | Path,
    *,
    resolution_m: float = 20.0,
    minimum_usable_pixel_percent: float = 20.0,
    excluded_scl_classes: set[int] | None = None,
    maximum_pixels: int = 2_000_000,
    force_refresh: bool = False,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    total = len(items)
    for index, item in enumerate(items, start=1):
        scene_id = str(item.get("id"))
        if progress_callback:
            progress_callback(index, total, scene_id)
        try:
            row = process_scene(
                item,
                geometry,
                index_names,
                cache_dir,
                resolution_m=resolution_m,
                minimum_usable_pixel_percent=minimum_usable_pixel_percent,
                excluded_scl_classes=excluded_scl_classes,
                maximum_pixels=maximum_pixels,
                force_refresh=force_refresh,
            )
        except Exception as error:
            timestamp = _scene_datetime(item)
            row = {
                "Scene ID": scene_id,
                "Collection": item.get("collection"),
                "Date": timestamp.date().isoformat() if not pd.isna(timestamp) else None,
                "Acquisition UTC": timestamp.isoformat() if not pd.isna(timestamp) else None,
                "Scene cloud (%)": _scene_cloud(item),
                "Status": "Processing failed",
                "Error": f"{type(error).__name__}: {error}",
            }
        rows.append(row)
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
        frame = frame.sort_values(["Date", "Scene cloud (%)"], na_position="last").reset_index(drop=True)
    return frame


# -----------------------------------------------------------------------------
# Preview generation
# -----------------------------------------------------------------------------


def _stretch_rgb(red: np.ndarray, green: np.ndarray, blue: np.ndarray, mask: np.ndarray) -> np.ndarray:
    channels = []
    for array in [red, green, blue]:
        data = array[mask & np.isfinite(array)]
        if data.size:
            low, high = np.nanpercentile(data, [2, 98])
            if high <= low:
                low, high = float(np.nanmin(data)), float(np.nanmax(data) + 1e-6)
        else:
            low, high = 0.0, 0.3
        scaled = np.clip((array - low) / max(high - low, 1e-6), 0.0, 1.0)
        channels.append(scaled)
    rgb = np.dstack(channels)
    rgb[~mask] = 1.0
    return (rgb * 255).astype("uint8")


def _index_rgba(index_array: np.ndarray, mask: np.ndarray, index_name: str) -> np.ndarray:
    if matplotlib is None:
        raise SatelliteMonitoringError("matplotlib is required for index previews.")
    cmap_name = "RdYlGn" if index_name in {"NDVI", "EVI", "NDRE"} else "BrBG"
    cmap = matplotlib.colormaps.get_cmap(cmap_name)
    normalised = np.clip((index_array + 1.0) / 2.0, 0.0, 1.0)
    rgba = (cmap(normalised) * 255).astype("uint8")
    rgba[..., 3] = np.where(mask & np.isfinite(index_array), 220, 0).astype("uint8")
    return rgba


def _png_bytes(array: np.ndarray) -> bytes:
    if Image is None:
        raise SatelliteMonitoringError("Pillow is required for image previews.")
    image = Image.fromarray(array)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def generate_scene_preview(
    item: Mapping[str, Any],
    geometry: Mapping[str, Any],
    index_name: str,
    *,
    resolution_m: float = 20.0,
    excluded_scl_classes: set[int] | None = None,
    maximum_pixels: int = 2_000_000,
) -> dict[str, Any]:
    require_satellite_stack()
    if index_name not in INDEX_REGISTRY:
        raise SatelliteMonitoringError(f"Unsupported preview index: {index_name}")
    geometry = validate_aoi_geometry(geometry)
    excluded = set(DEFAULT_EXCLUDED_SCL if excluded_scl_classes is None else excluded_scl_classes)
    assets = resolve_scene_assets(item)
    required = set(INDEX_REGISTRY[index_name]["bands"]) | {"red", "green", "blue"}
    missing = [role for role in sorted(required) if role not in assets]
    if missing:
        raise SatelliteMonitoringError(f"The selected scene lacks preview assets: {', '.join(missing)}")
    grid = _build_reference_grid(assets["red"], geometry, resolution_m, maximum_pixels)
    band_arrays = {role: _read_asset_to_grid(assets[role], grid) for role in required}
    scl = _read_asset_to_grid(assets["scl"], grid, categorical=True) if "scl" in assets else None
    clear_mask, scl_percentages = _clear_pixel_mask(grid, band_arrays, scl, excluded)
    index_array = calculate_indices(band_arrays, [index_name])[index_name]
    true_colour = _stretch_rgb(band_arrays["red"], band_arrays["green"], band_arrays["blue"], clear_mask)
    index_rgba = _index_rgba(index_array, clear_mask, index_name)
    west, south, east, north = grid.bounds_wgs84
    return {
        "true_colour_png": _png_bytes(true_colour),
        "index_png": _png_bytes(index_rgba),
        "true_colour_array": true_colour,
        "index_rgba_array": index_rgba,
        "bounds": [[south, west], [north, east]],
        "index_name": index_name,
        "scl_percentages": scl_percentages,
        "usable_pixel_percent": 100.0 * np.count_nonzero(clear_mask) / max(1, np.count_nonzero(grid.polygon_mask)),
        "scene_id": item.get("id"),
        "date": _scene_datetime(item).date().isoformat(),
    }


# -----------------------------------------------------------------------------
# Historical anomalies and integration with Modules A/B
# -----------------------------------------------------------------------------


def add_crop_season_coordinates(
    time_series: pd.DataFrame,
    planting_month: int,
    planting_day: int,
    season_length_days: int,
) -> pd.DataFrame:
    frame = time_series.copy()
    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
    frame = frame.dropna(subset=["Date"])
    records = []
    for _, row in frame.iterrows():
        observation = pd.Timestamp(row["Date"])
        anchors = []
        for candidate_year in [observation.year - 1, observation.year]:
            try:
                anchor = pd.Timestamp(year=candidate_year, month=int(planting_month), day=int(planting_day))
            except ValueError:
                anchor = pd.Timestamp(year=candidate_year, month=int(planting_month), day=28)
            anchors.append(anchor)
        valid = [(observation - anchor).days for anchor in anchors if 0 <= (observation - anchor).days <= season_length_days]
        if not valid:
            continue
        dap = min(valid)
        season_year = observation.year if observation.month > planting_month or (observation.month == planting_month and observation.day >= planting_day) else observation.year - 1
        record = row.to_dict()
        record["Season year"] = int(season_year)
        record["Days after planting"] = int(dap)
        records.append(record)
    return pd.DataFrame(records)


def historical_index_anomaly(
    time_series: pd.DataFrame,
    index_name: str,
    target_year: int,
    planting_month: int,
    planting_day: int,
    season_length_days: int,
    bin_width_days: int = 15,
    baseline_years: Sequence[int] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    value_column = f"{index_name} Mean"
    if value_column not in time_series.columns:
        raise SatelliteMonitoringError(f"The processed time series does not contain {value_column}.")
    seasonal = add_crop_season_coordinates(time_series, planting_month, planting_day, season_length_days)
    seasonal[value_column] = pd.to_numeric(seasonal[value_column], errors="coerce")
    seasonal = seasonal.dropna(subset=[value_column])
    seasonal["DAP bin"] = (seasonal["Days after planting"] // int(bin_width_days)) * int(bin_width_days)
    if baseline_years is None:
        baseline = seasonal[seasonal["Season year"] != int(target_year)].copy()
    else:
        baseline = seasonal[seasonal["Season year"].isin([int(year) for year in baseline_years])].copy()
    target = seasonal[seasonal["Season year"] == int(target_year)].copy()
    if baseline.empty:
        raise SatelliteMonitoringError("No baseline-season observations are available for the selected settings.")
    if target.empty:
        raise SatelliteMonitoringError("No target-season observations are available.")

    baseline_summary = (
        baseline.groupby("DAP bin")[value_column]
        .agg(
            **{
                "Baseline median": "median",
                "Baseline mean": "mean",
                "Baseline observations": "count",
                "Baseline years": lambda values: baseline.loc[values.index, "Season year"].nunique(),
                "Baseline P10": lambda values: values.quantile(0.10),
                "Baseline P90": lambda values: values.quantile(0.90),
            }
        )
        .reset_index()
    )
    target_summary = (
        target.groupby("DAP bin")
        .agg(
            **{
                "Target value": (value_column, "mean"),
                "Target observations": (value_column, "count"),
                "Target first date": ("Date", "min"),
                "Target last date": ("Date", "max"),
            }
        )
        .reset_index()
    )
    comparison = target_summary.merge(baseline_summary, on="DAP bin", how="left")
    comparison["Absolute anomaly"] = comparison["Target value"] - comparison["Baseline median"]
    comparison["Percent anomaly"] = np.where(
        np.abs(comparison["Baseline median"]) > 1e-8,
        comparison["Absolute anomaly"] / np.abs(comparison["Baseline median"]) * 100.0,
        np.nan,
    )

    percentiles = []
    for _, row in comparison.iterrows():
        values = baseline.loc[baseline["DAP bin"].eq(row["DAP bin"]), value_column].dropna().to_numpy(float)
        if values.size:
            percentile = 100.0 * (np.count_nonzero(values < row["Target value"]) + 0.5 * np.count_nonzero(values == row["Target value"])) / values.size
        else:
            percentile = np.nan
        percentiles.append(percentile)
    comparison["Target historical percentile"] = percentiles
    return seasonal.reset_index(drop=True), comparison.reset_index(drop=True)


def assign_stage_to_observations(time_series: pd.DataFrame, schedule: pd.DataFrame | None) -> pd.DataFrame:
    frame = time_series.copy()
    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
    frame["Crop stage"] = pd.NA
    if schedule is None or not isinstance(schedule, pd.DataFrame) or schedule.empty:
        return frame
    stage_column = next((column for column in ["Stage", "Crop stage"] if column in schedule.columns), None)
    start_column = next((column for column in ["Start date", "Start", "Stage start"] if column in schedule.columns), None)
    end_column = next((column for column in ["End date", "End", "Stage end"] if column in schedule.columns), None)
    if not all([stage_column, start_column, end_column]):
        return frame
    for _, row in schedule.iterrows():
        start = pd.to_datetime(row[start_column], errors="coerce")
        end = pd.to_datetime(row[end_column], errors="coerce")
        if pd.isna(start) or pd.isna(end):
            continue
        frame.loc[frame["Date"].between(start, end), "Crop stage"] = str(row[stage_column])
    return frame


def compare_with_root_zone_model(
    time_series: pd.DataFrame,
    root_zone_daily: pd.DataFrame,
    index_name: str,
    antecedent_window_days: int = 14,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    value_column = f"{index_name} Mean"
    if value_column not in time_series.columns:
        raise SatelliteMonitoringError(f"Missing {value_column} from satellite time series.")
    if root_zone_daily is None or root_zone_daily.empty or "Date" not in root_zone_daily.columns:
        raise SatelliteMonitoringError("No compatible Module B daily root-zone result is available.")
    satellite = time_series.copy()
    satellite["Date"] = pd.to_datetime(satellite["Date"], errors="coerce").dt.normalize()
    satellite[value_column] = pd.to_numeric(satellite[value_column], errors="coerce")
    satellite = satellite.dropna(subset=["Date", value_column])
    soil = root_zone_daily.copy()
    soil["Date"] = pd.to_datetime(soil["Date"], errors="coerce").dt.normalize()
    soil = soil.dropna(subset=["Date"]).sort_values("Date")
    window_days = max(1, int(antecedent_window_days))
    rows = []
    for _, scene in satellite.iterrows():
        end = scene["Date"]
        start = end - pd.Timedelta(days=window_days - 1)
        window = soil.loc[soil["Date"].between(start, end)]
        if window.empty:
            continue
        rows.append(
            {
                "Satellite date": end,
                "Index": index_name,
                "Index value": scene[value_column],
                "Mean Ks": pd.to_numeric(window.get("Ks"), errors="coerce").mean(),
                "Minimum Ks": pd.to_numeric(window.get("Ks"), errors="coerce").min(),
                "Maximum relative depletion": pd.to_numeric(window.get("Relative depletion"), errors="coerce").max(),
                "Stress days": pd.Series(window.get("Stress day", False)).fillna(False).astype(bool).sum(),
                "Severe stress days": pd.Series(window.get("Severe stress day", False)).fillna(False).astype(bool).sum(),
                "Mean actual ETc (mm)": pd.to_numeric(window.get("Actual ETc (mm)"), errors="coerce").mean(),
                "Mean potential ETc (mm)": pd.to_numeric(window.get("Potential ETc (mm)"), errors="coerce").mean(),
                "Antecedent window (days)": window_days,
            }
        )
    paired = pd.DataFrame(rows)
    if paired.empty:
        return paired, pd.DataFrame()
    metrics = ["Mean Ks", "Minimum Ks", "Maximum relative depletion", "Stress days", "Severe stress days"]
    correlations = []
    for metric in metrics:
        subset = paired[["Index value", metric]].dropna()
        if len(subset) < 3 or subset[metric].nunique() < 2 or subset["Index value"].nunique() < 2:
            pearson = spearman = p_pearson = p_spearman = np.nan
        else:
            from scipy import stats

            pearson, p_pearson = stats.pearsonr(subset["Index value"], subset[metric])
            spearman, p_spearman = stats.spearmanr(subset["Index value"], subset[metric])
        correlations.append(
            {
                "Model metric": metric,
                "Paired observations": len(subset),
                "Pearson r": pearson,
                "Pearson p": p_pearson,
                "Spearman rho": spearman,
                "Spearman p": p_spearman,
            }
        )
    return paired, pd.DataFrame(correlations)


def stage_index_summary(time_series: pd.DataFrame, schedule: pd.DataFrame, index_names: Sequence[str]) -> pd.DataFrame:
    assigned = assign_stage_to_observations(time_series, schedule)
    if assigned["Crop stage"].isna().all():
        return pd.DataFrame()
    value_columns = [f"{name} Mean" for name in index_names if f"{name} Mean" in assigned.columns]
    if not value_columns:
        return pd.DataFrame()
    aggregations: dict[str, Any] = {
        "First observation": ("Date", "min"),
        "Last observation": ("Date", "max"),
        "Observations": ("Date", "count"),
        "Mean field usable pixels (%)": ("Field usable pixels (%)", "mean"),
    }
    for column in value_columns:
        aggregations[f"Mean {column.replace(' Mean', '')}"] = (column, "mean")
        aggregations[f"Minimum {column.replace(' Mean', '')}"] = (column, "min")
        aggregations[f"Maximum {column.replace(' Mean', '')}"] = (column, "max")
    return assigned.dropna(subset=["Crop stage"]).groupby("Crop stage", sort=False).agg(**aggregations).reset_index()


# -----------------------------------------------------------------------------
# Cache and exports
# -----------------------------------------------------------------------------


def cache_inventory(cache_dir: str | Path) -> pd.DataFrame:
    root = Path(cache_dir)
    rows = []
    if not root.exists():
        return pd.DataFrame()
    for path in root.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            rows.append(
                {
                    "Cache file": path.name,
                    "Scene ID": data.get("Scene ID"),
                    "Date": data.get("Date"),
                    "Status": data.get("Status"),
                    "Size (KB)": path.stat().st_size / 1024.0,
                    "Modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
                }
            )
        except Exception:
            rows.append({"Cache file": path.name, "Status": "Unreadable"})
    return pd.DataFrame(rows).sort_values("Date", na_position="last").reset_index(drop=True) if rows else pd.DataFrame()


def clear_cache(cache_dir: str | Path) -> int:
    root = Path(cache_dir)
    if not root.exists():
        return 0
    removed = 0
    for path in root.iterdir():
        if path.is_file():
            path.unlink(missing_ok=True)
            removed += 1
        elif path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
            removed += 1
    return removed


def build_satellite_export_package(
    output_path: str | Path,
    *,
    geometry: Mapping[str, Any],
    search_catalog: pd.DataFrame | None,
    time_series: pd.DataFrame | None,
    metadata: Mapping[str, Any],
    anomaly_table: pd.DataFrame | None = None,
    model_pairs: pd.DataFrame | None = None,
    model_correlations: pd.DataFrame | None = None,
) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f"{destination.name}.{time.time_ns()}.tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("field_aoi.geojson", geometry_geojson_bytes(geometry, metadata).decode("utf-8"))
        archive.writestr("analysis_metadata.json", json.dumps(_json_safe(metadata), indent=2, ensure_ascii=False))
        if search_catalog is not None and not search_catalog.empty:
            archive.writestr("sentinel2_scene_catalog.csv", search_catalog.to_csv(index=False))
        if time_series is not None and not time_series.empty:
            archive.writestr("satellite_index_time_series.csv", time_series.to_csv(index=False))
        if anomaly_table is not None and not anomaly_table.empty:
            archive.writestr("historical_satellite_anomalies.csv", anomaly_table.to_csv(index=False))
        if model_pairs is not None and not model_pairs.empty:
            archive.writestr("satellite_root_zone_pairs.csv", model_pairs.to_csv(index=False))
        if model_correlations is not None and not model_correlations.empty:
            archive.writestr("satellite_root_zone_correlations.csv", model_correlations.to_csv(index=False))
    os.replace(temporary, destination)
    return destination


def module_metadata() -> dict[str, Any]:
    return {
        "module": "Satellite crop monitoring",
        "version": MODULE_VERSION,
        "catalogues": {
            provider: details["catalog"]
            for provider, details in STAC_PROVIDERS.items()
        },
        "default_provider_order": ["Earth Search", "Planetary Computer"],
        "collections": {
            "Earth Search": SENTINEL_COLLECTIONS,
            "Planetary Computer": PLANETARY_COMPUTER_COLLECTIONS,
        },
        "indices": INDEX_REGISTRY,
        "default_excluded_scl_classes": sorted(DEFAULT_EXCLUDED_SCL),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "limitations": [
            "Vegetation indices are not direct yield measurements.",
            "Clouds, cloud shadows, haze, mixed pixels, field boundaries, and crop identity affect interpretation.",
            "NDMI is a canopy moisture indicator and not a direct root-zone soil-moisture observation.",
            "A temporal association with modelled stress does not establish causation.",
            "Public STAC catalogues are best-effort; provider failover does not guarantee continuous availability.",
        ],
    }
