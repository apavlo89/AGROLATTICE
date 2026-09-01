"""Hybrid mechanistic + ML residual correction for AGROLATTICE 11.4."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np
import pandas as pd
from sklearn.base import clone

from agricultural_validation import build_protocol_folds, evaluate_estimator, regression_metrics
from research_models import make_estimator

MODULE_VERSION = "1.0.0"
METHOD_LABEL = "Mechanistic/base prediction + leakage-safe ML residual correction"


class HybridResidualError(RuntimeError):
    pass


@dataclass
class HybridResidualModel:
    residual_model: Any
    base_prediction_column: str
    feature_columns: list[str]
    validation: pd.DataFrame
    improvement: dict[str, float]
    accepted: bool
    base_model_name: str


def fit_hybrid_residual(
    frame: pd.DataFrame,
    *,
    observed_column: str,
    base_prediction_column: str,
    feature_columns: Sequence[str],
    protocol: str,
    group_column: str | None = None,
    year_column: str | None = None,
    region_column: str | None = None,
    date_column: str | None = None,
    residual_model_name: str = "Random forest",
    n_splits: int = 5,
    random_state: int = 42,
) -> HybridResidualModel:
    features = [str(c) for c in feature_columns if c in frame and c not in {observed_column, base_prediction_column}]
    if not features:
        raise HybridResidualError("Select at least one residual-correction feature.")
    context = [c for c in (group_column, year_column, region_column, date_column) if c and c in frame]
    needed = list(dict.fromkeys([observed_column, base_prediction_column] + features + context))
    work = frame[needed].copy()
    work[observed_column] = pd.to_numeric(work[observed_column], errors="coerce")
    work[base_prediction_column] = pd.to_numeric(work[base_prediction_column], errors="coerce")
    work = work.dropna(subset=[observed_column, base_prediction_column]).reset_index(drop=True)
    if len(work) < 12:
        raise HybridResidualError("At least 12 paired observed/base predictions are required.")
    work["__residual_target__"] = work[observed_column] - work[base_prediction_column]
    folds = build_protocol_folds(
        work, protocol=protocol, target_column="__residual_target__", task_type="regression",
        group_column=group_column, year_column=year_column, region_column=region_column,
        date_column=date_column, n_splits=n_splits,
    )
    estimator = make_estimator(
        residual_model_name, task_type="regression", frame=work[features],
        feature_columns=features, random_state=random_state,
    )
    fold_metrics, oof = evaluate_estimator(estimator, work[features], work["__residual_target__"], folds, task_type="regression")
    # evaluate_estimator preserves row indices from X in the OOF table.
    row_ids = pd.to_numeric(oof["Row"], errors="coerce").astype(int).to_numpy()
    aligned = work.iloc[row_ids].copy().reset_index(drop=True)
    residual_prediction = pd.to_numeric(oof["Predicted"], errors="coerce").to_numpy()
    observed = aligned[observed_column].to_numpy(float)
    base = aligned[base_prediction_column].to_numpy(float)
    corrected = base + residual_prediction
    base_metrics = regression_metrics(observed, base)
    corrected_metrics = regression_metrics(observed, corrected)
    improvement = {
        "RMSE improvement (%)": float((base_metrics["RMSE"] - corrected_metrics["RMSE"]) / base_metrics["RMSE"] * 100) if base_metrics.get("RMSE") else np.nan,
        "MAE improvement (%)": float((base_metrics["MAE"] - corrected_metrics["MAE"]) / base_metrics["MAE"] * 100) if base_metrics.get("MAE") else np.nan,
    }
    accepted = bool(np.isfinite(improvement["RMSE improvement (%)"]) and improvement["RMSE improvement (%)"] > 0)
    validation = pd.DataFrame([
        {"Model": "Mechanistic/base prediction", **base_metrics},
        {"Model": "Hybrid corrected prediction", **corrected_metrics},
    ])
    estimator.fit(work[features], work["__residual_target__"])
    return HybridResidualModel(
        residual_model=estimator,
        base_prediction_column=base_prediction_column,
        feature_columns=features,
        validation=validation,
        improvement=improvement,
        accepted=accepted,
        base_model_name=residual_model_name,
    )


def predict_hybrid(model: HybridResidualModel, frame: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in [model.base_prediction_column] + model.feature_columns if c not in frame]
    if missing:
        raise HybridResidualError("Missing hybrid-model columns: " + ", ".join(missing))
    out = frame.copy()
    base = pd.to_numeric(out[model.base_prediction_column], errors="coerce")
    residual = model.residual_model.predict(out[model.feature_columns])
    out["Base mechanistic/model prediction"] = base
    out["Predicted residual correction"] = residual
    out["Hybrid corrected prediction"] = base + residual
    out["Hybrid accepted by held-out RMSE"] = bool(model.accepted)
    return out


def hybrid_manifest(model: HybridResidualModel) -> dict:
    return {
        "method": METHOD_LABEL,
        "base_prediction_column": model.base_prediction_column,
        "residual_model": model.base_model_name,
        "feature_columns": model.feature_columns,
        "held_out_metrics": model.validation.to_dict(orient="records"),
        "improvement": model.improvement,
        "promotion_guard": "The hybrid correction is considered useful only when it improves held-out RMSE under the selected agricultural validation protocol.",
        "accepted": model.accepted,
    }
