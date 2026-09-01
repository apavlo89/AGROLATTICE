"""External agricultural benchmark metadata and local adapters.

Large public datasets are never bundled into AGROLATTICE.  This module records
where CropNet/YieldSAT-style data came from and prepares local tables for the
same distribution-shift protocols used by AGROLATTICE's Validation Centre.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

MODULE_VERSION = "1.0.0"

BENCHMARKS: dict[str, dict[str, Any]] = {
    "CropNet": {
        "citation": "Lin et al., KDD 2024, An Open and Large-Scale Dataset for Multi-Modal Climate Change-aware Crop Yield Predictions",
        "doi": "10.1145/3637528.3671536",
        "project_url": "https://github.com/fudong03/CropNet",
        "paper_url": "https://arxiv.org/abs/2406.06081",
        "modalities": ["Sentinel-2", "weather", "crop/yield records"],
        "recommended_protocols": ["Leave-one-year-out", "Leave-one-region/site-out", "Forward time"],
        "notes": "External benchmark adapter only. Verify the current repository/dataset licence before download or redistribution.",
    },
    "YieldSAT": {
        "citation": "Lorenz et al., CVPR 2026, YieldSAT: A Multimodal Benchmark Dataset for High-Resolution Crop Yield Prediction",
        "doi": None,
        "project_url": "https://yieldsat.github.io/",
        "paper_url": "https://arxiv.org/abs/2604.00940",
        "modalities": ["satellite", "weather", "field/subfield yield"],
        "recommended_protocols": ["Leave-one-year-out", "Leave-one-region-out"],
        "notes": "Use official benchmark split definitions when supplied. A 10-m weak/subfield prediction is not considered spatially validated without independent high-resolution ground truth.",
    },
    "WorldCereal": {
        "citation": "Van Tricht et al., Earth System Science Data 15 (2023) 5491-5515",
        "doi": "10.5194/essd-15-5491-2023",
        "project_url": "https://esa-worldcereal.org/",
        "paper_url": "https://essd.copernicus.org/articles/15/5491/2023/",
        "modalities": ["Sentinel-1", "Sentinel-2", "reference data", "crop calendars"],
        "recommended_protocols": ["Geographic holdout", "Season holdout"],
        "notes": "EO classifications should be stored as predictions with confidence and must not overwrite recorded crop/irrigation observations.",
    },
}


class BenchmarkAdapterError(RuntimeError):
    pass


def benchmark_catalog() -> pd.DataFrame:
    rows = []
    for name, record in BENCHMARKS.items():
        rows.append({
            "Benchmark": name,
            "Citation": record.get("citation"),
            "DOI": record.get("doi"),
            "Modalities": ", ".join(record.get("modalities", [])),
            "Recommended validation": ", ".join(record.get("recommended_protocols", [])),
            "Project": record.get("project_url"),
            "Paper": record.get("paper_url"),
            "Notes": record.get("notes"),
        })
    return pd.DataFrame(rows)


def inspect_local_table(frame: pd.DataFrame) -> dict[str, Any]:
    if frame is None or frame.empty:
        raise BenchmarkAdapterError("Benchmark table is empty.")
    likely = {
        "year": next((c for c in frame.columns if str(c).casefold() in {"year", "season_year", "harvest_year"}), None),
        "region": next((c for c in frame.columns if any(token in str(c).casefold() for token in ("region", "state", "site", "country"))), None),
        "field": next((c for c in frame.columns if str(c).casefold() in {"field", "field_id", "fieldid"}), None),
        "yield": next((c for c in frame.columns if "yield" in str(c).casefold()), None),
        "date": next((c for c in frame.columns if "date" in str(c).casefold() or "time" in str(c).casefold()), None),
    }
    return {
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "likely_columns": likely,
        "missing_percent": {str(c): float(frame[c].isna().mean() * 100) for c in frame.columns},
    }


def prepare_benchmark_table(
    frame: pd.DataFrame,
    *,
    target_column: str,
    year_column: str | None = None,
    region_column: str | None = None,
    field_column: str | None = None,
) -> pd.DataFrame:
    if target_column not in frame:
        raise BenchmarkAdapterError("Selected target column is missing.")
    output = frame.copy()
    output["__agrolattice_target__"] = pd.to_numeric(output[target_column], errors="coerce")
    if year_column and year_column in output:
        output["__agrolattice_year__"] = pd.to_numeric(output[year_column], errors="coerce")
    if region_column and region_column in output:
        output["__agrolattice_region__"] = output[region_column].astype("string")
    if field_column and field_column in output:
        output["__agrolattice_field__"] = output[field_column].astype("string")
    return output


def read_local_benchmark(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise BenchmarkAdapterError(f"Benchmark file does not exist: {path}")
    suffix = path.suffix.casefold()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise BenchmarkAdapterError("Supported local benchmark tables are CSV, Parquet or Excel.")
