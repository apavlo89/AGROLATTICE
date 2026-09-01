"""AGROLATTICE 11.19 publication-reference utilities.

This module is deliberately independent of Streamlit. It defines the frozen
publication-reference identifier, deterministic synthetic demonstration data,
reference figures, reproducibility manifests and source-integrity helpers used
for the AGROLATTICE 11.19 paper/reference release.

The bundled demonstration data are synthetic and must never be described as
field measurements, NASA retrievals, Sentinel observations or validation of an
agronomic recommendation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np
import pandas as pd

MODULE_VERSION = "1.0.0"
REFERENCE_RELEASE = "AGROLATTICE 11.19"
REFERENCE_ID = "AGROLATTICE-11.19-PRR-2026-08-12"
REFERENCE_DATE = "2026-08-12"
REFERENCE_TITLE = "Publication Reference Release"
DEMO_SEED = 1119

CANONICAL_WEATHER_VARIABLES = [
    "CLEARNESS_INDEX",
    "CLOUD_AMOUNT_DAY",
    "EVAPORATION_LAND",
    "EVAPOTRANSPIRATION",
    "EVAPOTRANSPIRATION_ENERGY_FLUX",
    "LONGWAVE_RADIATION",
    "PRECIPITATION_AVG",
    "PRECIPITATION_MAX",
    "PRECIPITATION_MIN",
    "RELATIVE_HUMIDITY",
    "SOIL_HEAT_FLUX",
    "SOIL_TEMP_LAYER1",
    "SOIL_TEMP_LAYER2",
    "SOLAR_RADIATION",
    "SURFACE_PRESSURE",
    "TEMPERATURE",
    "TEMPERATURE_MAX",
    "TEMPERATURE_MIN",
    "WIND_SPEED",
]

PROTECTED_ARTIFACTS = {
    "Field Operations": "field_operations/field_operations.sqlite",
    "Experiments": "pollination_lab/maize_flowering_trials.sqlite",
    "Persistent Twin": "agrolattice_twin/agrolattice_twin.sqlite",
    "Research Evidence": "models_evidence/research_evidence.sqlite",
    "Crop Profiles": "models_evidence/crop_profiles.sqlite",
    "Reporting": "reports/reporting.sqlite",
    "Mechanistic Maize Twin": "maize_mechanistic_twin.py",
}

SCHEMA_VERSIONS = {
    "Field Operations": "8.0.0",
    "Experiments": "3.0.0",
    "Persistent Twin": "3.0.0",
    "Research Evidence": "2.0.0",
    "Crop Profiles": "1.0.0",
    "Reporting": "1.0.0",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _treatment_table() -> pd.DataFrame:
    offsets = [-6, -3, 0, 3, 6, 9]
    return pd.DataFrame(
        {
            "treatment_id": [f"T{i+1:02d}" for i in range(len(offsets))],
            "female_parent": ["DEMO-F"] * len(offsets),
            "male_parent": ["DEMO-M"] * len(offsets),
            "female_sowing_date": ["2026-04-01"] * len(offsets),
            "male_sowing_offset_days": offsets,
            "sowing_density_plants_ha": [72000, 72000, 76000, 76000, 80000, 80000],
            "irrigation_treatment": ["Reference", "Reference", "Reference", "Sensor-triggered", "Sensor-triggered", "Sensor-triggered"],
        }
    )


def demo_trial_design() -> pd.DataFrame:
    """Return deterministic synthetic experimental-unit assignments."""
    treatments = _treatment_table()
    rows: list[dict[str, Any]] = []
    # 4 blocks × 6 treatments = 24 independently treated EUs.
    permutations = [
        [0, 3, 1, 5, 2, 4],
        [4, 1, 5, 0, 3, 2],
        [2, 5, 3, 1, 4, 0],
        [1, 4, 0, 2, 5, 3],
    ]
    origin_lon, origin_lat = 33.0000, 35.0000
    cell_lon, cell_lat = 0.00045, 0.00030
    for block in range(1, 5):
        for col, treatment_index in enumerate(permutations[block - 1]):
            t = treatments.iloc[treatment_index]
            eu = f"EU-{block:02d}-{col+1:02d}"
            x0 = origin_lon + col * cell_lon
            y0 = origin_lat + (block - 1) * cell_lat
            rows.append(
                {
                    "experimental_unit_id": eu,
                    "plot_label": eu,
                    "block": block,
                    "replicate": block,
                    "treatment_id": t["treatment_id"],
                    "female_parent": t["female_parent"],
                    "male_parent": t["male_parent"],
                    "female_sowing_date": t["female_sowing_date"],
                    "male_sowing_offset_days": int(t["male_sowing_offset_days"]),
                    "sowing_density_plants_ha": int(t["sowing_density_plants_ha"]),
                    "irrigation_treatment": t["irrigation_treatment"],
                    "centroid_lon": x0 + cell_lon / 2,
                    "centroid_lat": y0 + cell_lat / 2,
                    "geometry_wkt": (
                        f"POLYGON(({x0:.6f} {y0:.6f}, {(x0+cell_lon):.6f} {y0:.6f}, "
                        f"{(x0+cell_lon):.6f} {(y0+cell_lat):.6f}, {x0:.6f} {(y0+cell_lat):.6f}, {x0:.6f} {y0:.6f}))"
                    ),
                }
            )
    return pd.DataFrame(rows)


def demo_field_geojson() -> dict[str, Any]:
    design = demo_trial_design()
    min_lon = float(design["centroid_lon"].min() - 0.000225)
    max_lon = float(design["centroid_lon"].max() + 0.000225)
    min_lat = float(design["centroid_lat"].min() - 0.000150)
    max_lat = float(design["centroid_lat"].max() + 0.000150)
    coords = [[
        [min_lon, min_lat], [max_lon, min_lat], [max_lon, max_lat],
        [min_lon, max_lat], [min_lon, min_lat],
    ]]
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "field_id": "PUBREF-DEMO-FIELD",
                    "name": "AGROLATTICE Synthetic Publication Demo Field",
                    "country": "Synthetic / demonstration only",
                    "season_year": 2026,
                    "crop": "Maize",
                    "evidence_type": "Synthetic demonstration",
                },
                "geometry": {"type": "Polygon", "coordinates": coords},
            }
        ],
    }


def demo_weather() -> pd.DataFrame:
    """Synthetic 19-variable daily weather-like data for workflow demonstration."""
    rng = np.random.default_rng(DEMO_SEED)
    start = date(2026, 3, 20)
    n = 145
    rows: list[dict[str, Any]] = []
    for i in range(n):
        d = start + timedelta(days=i)
        seasonal = math.sin((i - 20) / 145 * math.pi)
        tmean = 18.0 + 9.0 * seasonal + rng.normal(0, 1.2)
        tmin = tmean - (6.5 + rng.normal(0, 0.8))
        tmax = tmean + (7.5 + rng.normal(0, 0.8))
        rain = float(max(0.0, rng.gamma(1.1, 4.0) - 2.5)) if rng.random() < 0.28 else 0.0
        rh = float(np.clip(68 - 0.7 * (tmean - 20) + rng.normal(0, 5), 25, 96))
        solar = float(max(5.0, 17 + 6 * seasonal + rng.normal(0, 1.8)))
        wind = float(max(0.2, rng.normal(2.6, 0.8)))
        eto = float(max(0.5, 0.15 * (tmax - tmin) + 0.12 * solar + rng.normal(0, 0.25)))
        cloud = float(np.clip(100 - solar * 3.2 + rng.normal(0, 8), 0, 100))
        clear = float(np.clip(1 - cloud / 120, 0.05, 0.95))
        soil1 = tmean + rng.normal(1.2, 0.7)
        soil2 = tmean + rng.normal(0.3, 0.5)
        rows.append(
            {
                "date": d.isoformat(),
                "CLEARNESS_INDEX": clear,
                "CLOUD_AMOUNT_DAY": cloud,
                "EVAPORATION_LAND": max(0.0, eto * 0.82 + rng.normal(0, 0.2)),
                "EVAPOTRANSPIRATION": eto,
                "EVAPOTRANSPIRATION_ENERGY_FLUX": eto * 28.4,
                "LONGWAVE_RADIATION": 310 + 2.2 * tmean + rng.normal(0, 6),
                "PRECIPITATION_AVG": rain,
                "PRECIPITATION_MAX": rain * 1.15,
                "PRECIPITATION_MIN": max(0.0, rain * 0.85),
                "RELATIVE_HUMIDITY": rh,
                "SOIL_HEAT_FLUX": rng.normal(1.8, 2.5),
                "SOIL_TEMP_LAYER1": soil1,
                "SOIL_TEMP_LAYER2": soil2,
                "SOLAR_RADIATION": solar,
                "SURFACE_PRESSURE": 96.5 + rng.normal(0, 0.6),
                "TEMPERATURE": tmean,
                "TEMPERATURE_MAX": tmax,
                "TEMPERATURE_MIN": tmin,
                "WIND_SPEED": wind,
                "source": "Synthetic deterministic publication-reference demo; not NASA POWER",
            }
        )
    frame = pd.DataFrame(rows)
    assert [c for c in CANONICAL_WEATHER_VARIABLES if c not in frame.columns] == []
    return frame


def demo_flowering_and_model() -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(DEMO_SEED + 1)
    design = demo_trial_design()
    flowering: list[dict[str, Any]] = []
    validation: list[dict[str, Any]] = []
    base_female = 72.0
    base_male = 69.5
    for _, row in design.iterrows():
        block_effect = (int(row["block"]) - 2.5) * 0.35
        density_effect = (float(row["sowing_density_plants_ha"]) - 76000) / 20000
        irrigation_effect = -0.5 if row["irrigation_treatment"] == "Sensor-triggered" else 0.0
        female = base_female + block_effect + 0.25 * density_effect + irrigation_effect + rng.normal(0, 0.55)
        male = base_male + float(row["male_sowing_offset_days"]) * 0.82 + block_effect + rng.normal(0, 0.55)
        observed_gap = female - male
        predicted_female = base_female + block_effect + 0.20 * density_effect + irrigation_effect + rng.normal(0, 0.35)
        predicted_male = base_male + float(row["male_sowing_offset_days"]) * 0.80 + block_effect + rng.normal(0, 0.35)
        predicted_gap = predicted_female - predicted_male
        flowering.append(
            {
                "experimental_unit_id": row["experimental_unit_id"],
                "block": int(row["block"]),
                "treatment_id": row["treatment_id"],
                "male_sowing_offset_days": int(row["male_sowing_offset_days"]),
                "observed_female_50pct_silking_das": round(float(female), 2),
                "observed_male_50pct_anthesis_das": round(float(male), 2),
                "observed_synchrony_gap_days": round(float(observed_gap), 2),
                "evidence_type": "Synthetic demonstration",
            }
        )
        validation.append(
            {
                "experimental_unit_id": row["experimental_unit_id"],
                "observed_synchrony_gap_days": round(float(observed_gap), 2),
                "predicted_synchrony_gap_days": round(float(predicted_gap), 2),
                "residual_days": round(float(observed_gap - predicted_gap), 2),
                "model_label": "Synthetic demonstration model",
                "validation_scope": "Demonstration only; not agronomic validation",
            }
        )
    return pd.DataFrame(flowering), pd.DataFrame(validation)


def demo_summary() -> dict[str, Any]:
    design = demo_trial_design()
    flowering, validation = demo_flowering_and_model()
    rmse = float(np.sqrt(np.mean(np.square(validation["residual_days"].astype(float)))))
    mae = float(np.mean(np.abs(validation["residual_days"].astype(float))))
    return {
        "reference_id": REFERENCE_ID,
        "synthetic": True,
        "experimental_units": int(len(design)),
        "blocks": int(design["block"].nunique()),
        "treatments": int(design["treatment_id"].nunique()),
        "weather_days": int(len(demo_weather())),
        "weather_variables": len(CANONICAL_WEATHER_VARIABLES),
        "demo_rmse_days": round(rmse, 3),
        "demo_mae_days": round(mae, 3),
        "scientific_boundary": "These metrics demonstrate the software workflow only and are not evidence of agronomic predictive performance.",
    }


def write_demo_bundle(output_dir: Path) -> dict[str, str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    design = demo_trial_design()
    flowering, validation = demo_flowering_and_model()
    weather = demo_weather()
    files: dict[str, Path] = {
        "trial_design": output_dir / "demo_trial_design.csv",
        "flowering_observations": output_dir / "demo_flowering_observations.csv",
        "model_validation": output_dir / "demo_model_validation.csv",
        "weather": output_dir / "demo_weather_19_variables.csv",
        "field": output_dir / "demo_field.geojson",
        "summary": output_dir / "demo_summary.json",
    }
    design.to_csv(files["trial_design"], index=False)
    flowering.to_csv(files["flowering_observations"], index=False)
    validation.to_csv(files["model_validation"], index=False)
    weather.to_csv(files["weather"], index=False)
    files["field"].write_text(json.dumps(demo_field_geojson(), indent=2), encoding="utf-8")
    files["summary"].write_text(json.dumps(demo_summary(), indent=2), encoding="utf-8")
    manifest = {
        "reference_id": REFERENCE_ID,
        "dataset_name": "AGROLATTICE 11.19 deterministic synthetic publication-reference project",
        "seed": DEMO_SEED,
        "synthetic": True,
        "not_field_data": True,
        "not_nasa_or_sentinel": True,
        "purpose": "Reproduce the software demonstration figures/tables without using private research data.",
        "files": {name: {"path": path.name, "sha256": sha256_file(path)} for name, path in files.items()},
        "scientific_boundary": "The example project verifies software plumbing and reproducible rendering only; it must not be used as empirical validation of AGROLATTICE models or recommendations.",
    }
    manifest_path = output_dir / "DEMO_DATA_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    readme = output_dir / "README_DEMO_PROJECT.md"
    readme.write_text(
        "# AGROLATTICE 11.19 synthetic publication-reference project\n\n"
        "This fixed dataset is generated deterministically from seed 1119. It is **synthetic**. "
        "It is not a field trial, NASA POWER retrieval, Sentinel observation, sensor stream, or agronomic validation dataset.\n\n"
        "It exists so reviewers/readers can reproduce the software workflow, figures, tables, provenance and report packaging without access to private research data.\n\n"
        "The weather table contains all 19 canonical AGROLATTICE weather variables solely to exercise the same data contracts as the production application.\n",
        encoding="utf-8",
    )
    return {name: str(path) for name, path in files.items()} | {"manifest": str(manifest_path), "readme": str(readme)}



def _save_figure(fig: plt.Figure, output_base: Path) -> list[Path]:
    """Save publication-reference figures as high-resolution PNG and vector SVG."""
    png = output_base.with_suffix(".png")
    svg = output_base.with_suffix(".svg")
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.16)
    fig.savefig(svg, bbox_inches="tight", pad_inches=0.16)
    plt.close(fig)
    return [png, svg]


def _diagram_box(
    ax,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    subtitle: str | None = None,
    linewidth: float = 1.4,
    title_size: float = 10.0,
    subtitle_size: float = 8.2,
) -> None:
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.04,rounding_size=0.07",
        fill=False,
        linewidth=linewidth,
    )
    ax.add_patch(box)
    if subtitle:
        ax.text(
            x + w / 2, y + h * 0.62, title,
            ha="center", va="center",
            fontsize=title_size, fontweight="bold",
        )
        ax.text(
            x + w / 2, y + h * 0.30, subtitle,
            ha="center", va="center",
            fontsize=subtitle_size,
        )
    else:
        ax.text(
            x + w / 2, y + h / 2, title,
            ha="center", va="center",
            fontsize=title_size, fontweight="bold",
        )



def figure_architecture(output_dir: Path) -> list[Path]:
    """Compact publication-ready architecture figure."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12.8, 7.2))
    ax.set_xlim(0, 12.8)
    ax.set_ylim(0, 7.2)
    ax.axis("off")

    ax.text(
        6.4, 6.90,
        "AGROLATTICE 11.19 — integrated research architecture",
        ha="center", va="center",
        fontsize=18, fontweight="bold",
    )
    ax.text(
        6.4, 6.55,
        "Spatial identity links field evidence, persistent Twins, experiments, models and decisions.",
        ha="center", va="center",
        fontsize=10.4,
    )

    # Section headings are centred over their own columns to prevent collisions.
    ax.text(
        1.675, 5.92, "SPATIAL & DATA FOUNDATION",
        ha="center", fontsize=8.5, fontweight="bold",
    )
    ax.text(
        7.68, 5.92, "INTEGRATED PLATFORM CORE",
        ha="center", fontsize=8.5, fontweight="bold",
    )

    _diagram_box(
        ax, 0.55, 4.70, 2.25, 0.92,
        "Mapped field hierarchy", "Country → Farm → Field",
        title_size=8.7, subtitle_size=7.6,
    )
    _diagram_box(
        ax, 0.55, 3.47, 2.25, 0.92,
        "Experimental identity", "Trial → Unit → Observation",
        title_size=8.7, subtitle_size=7.6,
    )
    _diagram_box(
        ax, 0.55, 2.24, 2.25, 0.92,
        "Environmental evidence", "Climate • Soil • EO • Sensors",
        title_size=8.5, subtitle_size=7.2,
    )

    core = [
        ("Fields & Operations", "geometry • management"),
        ("AgroLattice Twin", "state • timeline • scenarios"),
        ("Climate & EO", "climate • satellite • risk"),
        ("Crop Decisions", "phenology • water • planning"),
        ("Experiments", "design • treatments • G×E×M"),
        ("Models & Evidence", "validation • ensembles • UQ"),
        ("Reports", "provenance • figures • export"),
        ("Data & Settings", "datasets • diagnostics • control"),
    ]
    positions = [
        (3.25, 4.70), (5.55, 4.70), (7.85, 4.70), (10.15, 4.70),
        (3.25, 3.47), (5.55, 3.47), (7.85, 3.47), (10.15, 3.47),
    ]
    for (title, subtitle), (x, y) in zip(core, positions):
        _diagram_box(
            ax, x, y, 1.95, 0.92, title, subtitle,
            title_size=8.15, subtitle_size=6.65,
        )

    # Foundation enters the integrated platform.
    for y in (5.16, 3.93, 2.70):
        ax.annotate(
            "", xy=(3.10, y), xytext=(2.82, y),
            arrowprops=dict(arrowstyle="->", linewidth=1.15),
        )

    spine = FancyBboxPatch(
        (3.25, 2.05), 8.85, 0.88,
        boxstyle="round,pad=0.04,rounding_size=0.07",
        fill=False, linewidth=1.8,
    )
    ax.add_patch(spine)
    ax.text(
        7.68, 2.60, "Persistent evidence spine",
        ha="center", va="center",
        fontsize=11.0, fontweight="bold",
    )
    ax.text(
        7.68, 2.29,
        "Field → Trial → Experimental unit → Twin → Model → Recommendation → Outcome → Report",
        ha="center", va="center",
        fontsize=8.6,
    )

    for x in (4.23, 6.53, 8.83, 11.13):
        ax.annotate(
            "", xy=(x, 2.95), xytext=(x, 3.43),
            arrowprops=dict(arrowstyle="->", linewidth=1.0),
        )

    ax.text(0.55, 1.62, "SCIENTIFIC GUARDRAILS", fontsize=8.8, fontweight="bold")
    ax.text(
        0.55, 1.18,
        "Measured ≠ retrieved   •   Mechanistic ≠ validated   •   Prediction ≠ causality\n"
        "Recommendation ≠ actual operation   •   Climate similarity ≠ agronomic equivalence",
        fontsize=8.8, va="top", linespacing=1.55,
    )
    ax.text(
        6.4, 0.42,
        "Spatial identity, provenance, uncertainty and validation remain attached to the evidence chain.",
        ha="center", va="center",
        fontsize=9.3,
    )
    return _save_figure(fig, output_dir / "figure_01_platform_architecture")


def figure_workflow(output_dir: Path) -> list[Path]:
    """Readable persistent evidence-chain figure."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12.8, 4.3))
    ax.set_xlim(0, 12.8)
    ax.set_ylim(0, 4.3)
    ax.axis("off")

    ax.text(
        6.4, 4.02,
        "Persistent research workflow and evidence chain",
        ha="center", va="center",
        fontsize=17.5, fontweight="bold",
    )
    ax.text(
        6.4, 3.66,
        "A result remains traceable to the mapped unit, observations, model state and frozen report.",
        ha="center", va="center",
        fontsize=10.0,
    )

    labels = [
        ("Mapped field", "spatial identity"),
        ("Experiment", "treatments"),
        ("Twin state", "saved evidence"),
        ("Model + validation", "prediction + UQ"),
        ("Decision", "recommendation"),
        ("Measured outcome", "field evidence"),
        ("Frozen report", "reproducible record"),
    ]

    start_x = 0.35
    width = 1.47
    gap = 0.30
    y = 2.05
    h = 0.92

    for i, (title, subtitle) in enumerate(labels):
        x = start_x + i * (width + gap)
        _diagram_box(
            ax, x, y, width, h, title, subtitle,
            title_size=8.6 if len(title) < 16 else 7.9,
            subtitle_size=7.0,
        )
        if i < len(labels) - 1:
            ax.annotate(
                "",
                xy=(x + width + gap - 0.05, y + h / 2),
                xytext=(x + width + 0.05, y + h / 2),
                arrowprops=dict(arrowstyle="->", linewidth=1.15),
            )

    provenance = FancyBboxPatch(
        (1.10, 0.82), 10.60, 0.62,
        boxstyle="round,pad=0.04,rounding_size=0.06",
        fill=False, linewidth=1.4,
    )
    ax.add_patch(provenance)
    ax.text(
        6.4, 1.13,
        "Identity + provenance + uncertainty + validation are retained at every hand-off",
        ha="center", va="center",
        fontsize=9.5, fontweight="bold",
    )
    ax.text(
        6.4, 0.34,
        "Missing stages remain explicit rather than silently inferred. "
        "The publication-reference release freezes an immutable software state.",
        ha="center", va="center",
        fontsize=9.0,
    )
    return _save_figure(fig, output_dir / "figure_02_evidence_workflow")



def figure_demo_layout(output_dir: Path) -> list[Path]:
    """Synthetic 4×6 experimental layout without scientific-notation map axes."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    design = demo_trial_design().copy()

    lon_order = {v: i + 1 for i, v in enumerate(sorted(design["centroid_lon"].unique()))}
    lat_order = {v: i + 1 for i, v in enumerate(sorted(design["centroid_lat"].unique()))}
    design["plot_col"] = design["centroid_lon"].map(lon_order)
    design["plot_row"] = design["centroid_lat"].map(lat_order)

    fig, ax = plt.subplots(figsize=(10.8, 6.6))
    fig.subplots_adjust(top=0.82, bottom=0.16, left=0.10, right=0.98)

    fig.suptitle(
        "Synthetic publication-reference trial layout",
        fontsize=15.5, fontweight="bold", y=0.975,
    )
    fig.text(
        0.5, 0.915,
        "4 blocks × 6 treatments • cell labels show treatment ID and male sowing offset",
        ha="center", va="center",
        fontsize=9.6,
    )

    hatches = ["", "//", "\\\\", "xx", "..", "++"]
    treatments = sorted(design["treatment_id"].unique())
    treatment_hatch = {t: hatches[i % len(hatches)] for i, t in enumerate(treatments)}

    for _, row in design.iterrows():
        x = float(row["plot_col"])
        y = float(row["plot_row"])
        rect = Rectangle(
            (x - 0.48, y - 0.43),
            0.96, 0.86,
            fill=False,
            linewidth=1.15,
            hatch=treatment_hatch[row["treatment_id"]],
        )
        ax.add_patch(rect)
        ax.text(
            x, y + 0.08, str(row["treatment_id"]),
            ha="center", va="center",
            fontsize=9.6, fontweight="bold",
        )
        ax.text(
            x, y - 0.14,
            f"{int(row['male_sowing_offset_days']):+d} d",
            ha="center", va="center",
            fontsize=8.4,
        )

    ax.set_xlim(0.35, 6.65)
    ax.set_ylim(0.35, 4.65)
    ax.set_xticks(range(1, 7))
    ax.set_yticks(range(1, 5))
    ax.set_xlabel("Plot position (west → east)")
    ax.set_ylabel("Block")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(False)

    fig.text(
        0.5, 0.045,
        "Synthetic layout for software demonstration only — not a real field or randomisation recommendation.",
        ha="center", va="center",
        fontsize=8.8,
    )

    return _save_figure(fig, output_dir / "figure_03_demo_trial_layout")


def figure_demo_validation(output_dir: Path) -> list[Path]:
    """Balanced observed-vs-predicted synthetic demonstration plot."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    _, validation = demo_flowering_and_model()
    obs = validation["observed_synchrony_gap_days"].astype(float)
    pred = validation["predicted_synchrony_gap_days"].astype(float)

    lo = float(min(obs.min(), pred.min()) - 0.5)
    hi = float(max(obs.max(), pred.max()) + 0.5)
    summary = demo_summary()

    fig, ax = plt.subplots(figsize=(7.6, 7.0))
    ax.scatter(obs, pred, s=48, zorder=3)
    ax.plot([lo, hi], [lo, hi], linestyle="--", linewidth=1.4, zorder=2)

    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Synthetic observed synchrony gap (days)")
    ax.set_ylabel("Synthetic predicted synchrony gap (days)")
    ax.set_title(
        "Synthetic demo: observed vs predicted synchrony",
        fontsize=15.0, fontweight="bold", pad=14,
    )
    ax.text(
        0.04, 0.96,
        f"n = {len(validation)}\n"
        f"RMSE = {summary['demo_rmse_days']:.3f} d\n"
        f"MAE = {summary['demo_mae_days']:.3f} d",
        transform=ax.transAxes,
        va="top", ha="left",
        fontsize=9.8,
        bbox=dict(boxstyle="round,pad=0.35", fill=False, linewidth=1.0),
    )
    ax.text(
        0.96, 0.04,
        "Dashed line: 1:1 agreement",
        transform=ax.transAxes,
        ha="right", va="bottom",
        fontsize=8.8,
    )
    ax.text(
        0.5, -0.13,
        "Demonstration metric only — not evidence of field predictive performance.",
        transform=ax.transAxes,
        ha="center",
        fontsize=9.0,
    )
    ax.grid(True, linewidth=0.5, alpha=0.25)
    return _save_figure(fig, output_dir / "figure_04_demo_observed_vs_predicted")

def build_reference_figures(output_dir: Path) -> list[str]:
    paths: list[Path] = []
    paths += figure_architecture(output_dir)
    paths += figure_workflow(output_dir)
    paths += figure_demo_layout(output_dir)
    paths += figure_demo_validation(output_dir)
    return [str(p) for p in paths]


def build_example_outputs(output_dir: Path) -> dict[str, str]:
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    design = demo_trial_design(); flowering, validation = demo_flowering_and_model(); summary = demo_summary()
    treatment_summary = flowering.groupby(["treatment_id", "male_sowing_offset_days"], as_index=False).agg(
        n=("experimental_unit_id", "count"),
        mean_observed_gap_days=("observed_synchrony_gap_days", "mean"),
        sd_observed_gap_days=("observed_synchrony_gap_days", "std"),
    )
    treatment_summary.to_csv(output_dir / "table_01_treatment_summary.csv", index=False)
    validation.to_csv(output_dir / "table_02_demo_validation_records.csv", index=False)
    design.to_csv(output_dir / "table_03_randomisation_manifest.csv", index=False)
    (output_dir / "example_results_summary.md").write_text(
        "# AGROLATTICE 11.19 example outputs\n\n"
        f"Reference identifier: `{REFERENCE_ID}`\n\n"
        "These outputs are generated from the deterministic synthetic demonstration project. They verify the reproducibility pathway and must not be reported as empirical agricultural results.\n\n"
        f"- Experimental units: {summary['experimental_units']}\n"
        f"- Blocks: {summary['blocks']}\n"
        f"- Treatments: {summary['treatments']}\n"
        f"- Synthetic daily weather records: {summary['weather_days']} using all {summary['weather_variables']} canonical variables\n"
        f"- Demonstration RMSE: {summary['demo_rmse_days']} days\n"
        f"- Demonstration MAE: {summary['demo_mae_days']} days\n\n"
        "**Scientific boundary:** these metrics are not model-validation evidence.\n",
        encoding="utf-8",
    )
    return {p.name: str(p) for p in output_dir.iterdir() if p.is_file()}


def build_environment_manifest(root: Path) -> dict[str, Any]:
    import importlib.metadata as metadata
    packages = [
        "folium", "joblib", "matplotlib", "numpy", "pandas", "plotly", "seaborn",
        "scipy", "statsmodels", "scikit-learn", "openpyxl", "requests", "rasterio",
        "shapely", "pyproj", "Pillow", "python-docx", "xgboost", "lightgbm",
        "catboost", "optuna", "imbalanced-learn", "shap", "packaging",
        "streamlit", "streamlit-folium", "umap-learn", "openai", "tabpfn",
    ]
    versions: dict[str, str | None] = {}
    for package in packages:
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = None
    return {
        "reference_id": REFERENCE_ID,
        "generated_in_packaging_environment": True,
        "python": sys.version,
        "platform": platform.platform(),
        "package_versions": versions,
        "target_runtime_note": "RUN_APP.bat remains the authoritative Windows/Anaconda runtime preflight. Missing packages in this Linux packaging environment are not evidence that the Windows target environment lacks them.",
        "declared_requirement_files": ["requirements_ml_agriculture.txt", "requirements_research_optional.txt", "requirements_aquacrop.txt"],
        "protected_schemas": SCHEMA_VERSIONS,
    }


def verify_demo_bundle(root: Path) -> None:
    root = Path(root)
    design = pd.read_csv(root / "demo_trial_design.csv")
    flowering = pd.read_csv(root / "demo_flowering_observations.csv")
    validation = pd.read_csv(root / "demo_model_validation.csv")
    weather = pd.read_csv(root / "demo_weather_19_variables.csv")
    assert len(design) == 24 and design["block"].nunique() == 4 and design["treatment_id"].nunique() == 6
    assert len(flowering) == 24 and len(validation) == 24
    assert len(weather) == 145
    assert all(name in weather.columns for name in CANONICAL_WEATHER_VARIABLES)
    manifest = json.loads((root / "DEMO_DATA_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["synthetic"] is True and manifest["not_field_data"] is True
    for item in manifest["files"].values():
        assert sha256_file(root / item["path"]) == item["sha256"]


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build/verify AGROLATTICE 11.19 publication-reference assets")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "publication_reference")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    demo_dir = args.output / "demo_project"
    if not args.verify_only:
        write_demo_bundle(demo_dir)
        build_reference_figures(args.output / "figures")
        build_example_outputs(args.output / "example_outputs")
        (args.output / "ENVIRONMENT_REFERENCE_11_19.json").write_text(json.dumps(build_environment_manifest(Path(__file__).resolve().parent), indent=2), encoding="utf-8")
    verify_demo_bundle(demo_dir)
    print(f"{REFERENCE_ID} publication-reference assets verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
