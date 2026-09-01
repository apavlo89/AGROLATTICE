"""G×E×M research-table assembly for AGROLATTICE 11.4.

The builder reads existing Maize Synchrony Lab records and creates analysis
views without altering the protected pollination database. Experimental-unit
(plot/treatment-unit) identity, trial, block and replicate remain explicit so
validation can be grouped rather than leakage-prone random splitting.
"""
from __future__ import annotations

from typing import Any, Sequence
import numpy as np
import pandas as pd

MODULE_VERSION = "1.0.0"


class GXEMBuilderError(RuntimeError):
    pass


def _numeric_summary_by_plot(frame: pd.DataFrame, *, prefix: str) -> pd.DataFrame:
    if frame is None or frame.empty or "Plot ID" not in frame:
        return pd.DataFrame(columns=["Plot ID"])
    work = frame.copy()
    ignore = {"Plot ID", "Observation ID", "Plot", "Treatment", "Female sowing", "Male sowing", "Date", "Notes"}
    numeric_cols = []
    for c in work.columns:
        if c in ignore:
            continue
        converted = pd.to_numeric(work[c], errors="coerce")
        if converted.notna().any():
            work[c] = converted
            numeric_cols.append(c)
    if not numeric_cols:
        return work[["Plot ID"]].drop_duplicates()
    agg = work.groupby("Plot ID", as_index=False)[numeric_cols].agg(["mean", "max", "min"])
    # pandas produces a multi-index after groupby/agg; flatten it.
    agg.columns = ["Plot ID" if col[0] == "Plot ID" else f"{prefix}{col[0]} [{col[1]}]" for col in agg.columns]
    return agg


def _weather_summary(weather: pd.DataFrame) -> dict[str, float]:
    if weather is None or weather.empty:
        return {}
    out: dict[str, float] = {}
    mappings = {
        "Environment mean temperature (°C)": ("Tmean (°C)", "mean"),
        "Environment max temperature (°C)": ("Tmax (°C)", "max"),
        "Environment min temperature (°C)": ("Tmin (°C)", "min"),
        "Environment rainfall total (mm)": ("Rainfall (mm)", "sum"),
        "Environment solar radiation mean (MJ/m²/day)": ("Solar radiation (MJ/m²/day)", "mean"),
        "Environment reference ET total (mm)": ("Reference ET (mm)", "sum"),
        "Environment GDD total": ("GDD daily", "sum"),
    }
    for label, (column, how) in mappings.items():
        if column not in weather:
            continue
        values = pd.to_numeric(weather[column], errors="coerce")
        if values.notna().any():
            out[label] = float(values.sum() if how == "sum" else values.max() if how == "max" else values.min() if how == "min" else values.mean())
    return out


def build_maize_gxem_table(pollination_db: Any, trial_ids: Sequence[str] | None = None) -> tuple[pd.DataFrame, dict]:
    trials = pollination_db.list_trials()
    if trials.empty:
        raise GXEMBuilderError("No Maize Synchrony Lab trials are stored.")
    if trial_ids:
        wanted = {str(x) for x in trial_ids}
        trials = trials.loc[trials["Trial ID"].astype(str).isin(wanted)]
    if trials.empty:
        raise GXEMBuilderError("No selected trials were found.")

    rows: list[pd.DataFrame] = []
    issues: list[str] = []
    for trial_row in trials.to_dict("records"):
        trial_id = str(trial_row["Trial ID"])
        try:
            trial = pollination_db.get_trial(trial_id)
            plots = pollination_db.list_plots(trial_id)
        except Exception as error:
            issues.append(f"{trial_id}: {error}")
            continue
        if plots.empty:
            issues.append(f"{trial_id}: no experimental units")
            continue
        base = plots.copy()
        base["Trial ID"] = trial_id
        base["Trial"] = trial_row.get("Trial")
        base["Site"] = trial_row.get("Site")
        base["Season year"] = trial_row.get("Year")
        base["Source field ID"] = trial_row.get("Source field ID")
        base["Trial status"] = trial_row.get("Status")
        base["Management irrigation method"] = trial.get("irrigation_method")
        base["Management irrigation treatment"] = trial.get("irrigation_treatment")
        base["Management notes"] = trial.get("management_notes")
        base["Base temperature (°C)"] = trial.get("base_temperature_c")
        base["Upper temperature (°C)"] = trial.get("upper_temperature_c")

        for getter, prefix in ((pollination_db.observations, "Flowering obs · "), (pollination_db.leaf_observations, "Leaf obs · ")):
            try:
                summary = _numeric_summary_by_plot(getter(trial_id), prefix=prefix)
                if not summary.empty:
                    base = base.merge(summary, on="Plot ID", how="left")
            except Exception as error:
                issues.append(f"{trial_id} {prefix.strip()}: {error}")

        try:
            phen = pollination_db.phenology_events(trial_id)
            if not phen.empty:
                date_cols = [c for c in phen.columns if c.endswith("date")]
                keep = ["Plot ID"] + date_cols
                p = phen[keep].copy()
                for c in date_cols:
                    p[c] = pd.to_datetime(p[c], errors="coerce")
                if {"Male flowering date", "Female flowering date"}.issubset(p.columns):
                    p["Observed male–female flowering difference (days)"] = (p["Male flowering date"] - p["Female flowering date"]).dt.days
                base = base.merge(p, on="Plot ID", how="left")
        except Exception as error:
            issues.append(f"{trial_id} phenology: {error}")

        try:
            harvest = pollination_db.harvest(trial_id)
            if not harvest.empty:
                duplicate = [c for c in harvest.columns if c in base.columns and c != "Plot ID"]
                base = base.merge(harvest.drop(columns=duplicate, errors="ignore"), on="Plot ID", how="left")
        except Exception as error:
            issues.append(f"{trial_id} harvest: {error}")

        try:
            weather_summary = _weather_summary(pollination_db.weather(trial_id))
            for key, value in weather_summary.items():
                base[key] = value
        except Exception as error:
            issues.append(f"{trial_id} weather: {error}")
        rows.append(base)

    if not rows:
        raise GXEMBuilderError("No plot-level G×E×M rows could be assembled.")
    combined = pd.concat(rows, ignore_index=True, sort=False)
    meta = {
        "trials": int(combined["Trial ID"].nunique()),
        "experimental_units": int(len(combined)),
        "fields": int(combined["Source field ID"].dropna().astype(str).nunique()) if "Source field ID" in combined else 0,
        "genotype_columns": [c for c in ("Female parent", "Male parent", "Parent combination", "Variety / genotype") if c in combined],
        "management_columns": [c for c in combined.columns if c.startswith("Management ") or "Sowing" in c or "density" in c.casefold()],
        "environment_columns": [c for c in combined.columns if c.startswith("Environment ")],
        "validation_guardrail": "Keep Trial ID, Source field ID, Season year, Block and Replicate in the table. Use grouped/LOYO validation rather than random rows when estimating transfer performance.",
        "issues": issues,
    }
    return combined, meta
