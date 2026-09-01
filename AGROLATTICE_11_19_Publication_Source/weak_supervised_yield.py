"""Weakly supervised fine-resolution yield estimation for AGROLATTICE 11.4.

This is a transparent aggregate-consistency baseline inspired by the weakly
supervised yield-forecasting literature.  It trains on group-level aggregate
labels using group means of fine-resolution covariates, then projects the fitted
response surface back to fine rows. Fine-scale values are estimates and are not
claimed to be independently validated merely because aggregate validation is
strong.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

MODULE_VERSION = "1.0.0"
METHOD_LABEL = "Aggregate-consistency weak supervision (AGROLATTICE ridge baseline)"


class WeakSupervisionError(RuntimeError):
    pass


@dataclass
class WeakYieldModel:
    estimator: Any
    group_column: str
    target_column: str
    feature_columns: list[str]
    group_training_table: pd.DataFrame
    validation_table: pd.DataFrame


def _group_table(frame: pd.DataFrame, group_column: str, target_column: str, features: Sequence[str]) -> pd.DataFrame:
    work = frame[[group_column, target_column] + list(features)].copy()
    work[target_column] = pd.to_numeric(work[target_column], errors="coerce")
    for c in features:
        work[c] = pd.to_numeric(work[c], errors="coerce")
    # The coarse target must be constant within a supervision group. Allow tiny
    # floating noise but reject materially conflicting labels.
    variation = work.groupby(group_column, dropna=False)[target_column].agg(lambda x: np.nanmax(x) - np.nanmin(x) if x.notna().any() else np.nan)
    bad = variation[variation.fillna(0).gt(1e-8)]
    if not bad.empty:
        raise WeakSupervisionError("Aggregate target varies within one or more supervision groups. Supply one authoritative coarse yield label per group.")
    agg = work.groupby(group_column, as_index=False).agg({target_column: "first", **{c: "mean" for c in features}})
    return agg.dropna(subset=[target_column]).reset_index(drop=True)


def fit_weak_yield_model(
    frame: pd.DataFrame,
    *,
    group_column: str,
    aggregate_target_column: str,
    feature_columns: Sequence[str],
    alpha: float = 1.0,
) -> WeakYieldModel:
    features = [str(c) for c in feature_columns if c in frame and c not in {group_column, aggregate_target_column}]
    if not features:
        raise WeakSupervisionError("Select at least one fine-resolution covariate.")
    groups = _group_table(frame, group_column, aggregate_target_column, features)
    if len(groups) < 4:
        raise WeakSupervisionError("At least four independently labelled aggregate groups are required.")
    estimator = Pipeline([
        ("prep", ColumnTransformer([("numeric", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), features)], remainder="drop")),
        ("model", Ridge(alpha=float(alpha))),
    ])
    # Leave-one-group-out at the coarse label level.
    records = []
    predictions = []
    for i in range(len(groups)):
        train = groups.drop(index=i)
        test = groups.iloc[[i]]
        candidate = clone(estimator)
        candidate.fit(train[features], train[aggregate_target_column])
        pred = float(candidate.predict(test[features])[0])
        obs = float(test[aggregate_target_column].iloc[0])
        predictions.append((obs, pred))
        records.append({"Held-out group": str(test[group_column].iloc[0]), "Observed aggregate": obs, "Predicted aggregate": pred, "Error": pred - obs})
    observed = np.asarray([x[0] for x in predictions], dtype=float)
    predicted = np.asarray([x[1] for x in predictions], dtype=float)
    summary = {
        "MAE": float(mean_absolute_error(observed, predicted)),
        "RMSE": float(np.sqrt(mean_squared_error(observed, predicted))),
        "R2": float(r2_score(observed, predicted)) if len(observed) > 1 else np.nan,
    }
    validation = pd.DataFrame(records)
    for key, value in summary.items():
        validation.attrs[key] = value
    estimator.fit(groups[features], groups[aggregate_target_column])
    return WeakYieldModel(estimator, group_column, aggregate_target_column, features, groups, validation)


def predict_fine_resolution(model: WeakYieldModel, frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    missing = [c for c in model.feature_columns if c not in frame]
    if missing:
        raise WeakSupervisionError("Missing fine-resolution covariates: " + ", ".join(missing))
    out = frame.copy()
    out["Weakly supervised fine-scale yield estimate"] = model.estimator.predict(out[model.feature_columns])
    if model.group_column in out:
        aggregated = out.groupby(model.group_column, as_index=False)["Weakly supervised fine-scale yield estimate"].mean()
        aggregated = aggregated.rename(columns={"Weakly supervised fine-scale yield estimate": "Predicted aggregate from fine estimates"})
        if model.target_column in out:
            observed = out.groupby(model.group_column, as_index=False)[model.target_column].first()
            aggregated = aggregated.merge(observed, on=model.group_column, how="left")
    else:
        aggregated = pd.DataFrame()
    return out, aggregated


def weak_supervision_manifest(model: WeakYieldModel) -> dict:
    return {
        "method": METHOD_LABEL,
        "supervision_group": model.group_column,
        "aggregate_target": model.target_column,
        "fine_covariates": model.feature_columns,
        "group_count": int(len(model.group_training_table)),
        "leave_one_group_out": {k: v for k, v in model.validation_table.attrs.items()},
        "scientific_guardrail": "Fine-scale outputs are model estimates learned from aggregate labels. Aggregate agreement does not constitute independent validation at the fine spatial scale.",
    }
