"""Adaptive modality-aware fusion for AGROLATTICE 11.4.

Release 11.3 provided validation-weighted late fusion. Release 11.4 retains that
scientifically transparent baseline and adds an adaptive reliability gate: each
modality is first evaluated out-of-fold, then a separate error model learns
which input conditions are associated with larger/smaller held-out errors.
At prediction time inverse predicted error produces sample-specific modality
weights, renormalised across the modalities that are actually available.

This is an independent CPU-friendly AGROLATTICE adaptation inspired by gated
multimodal crop-yield work. It is not an exact reproduction of Mena et al.'s
neural architecture, and learned gate weights are predictive reliabilities, not
causal importance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

from agricultural_validation import build_protocol_folds, evaluate_estimator, regression_metrics
from research_models import make_estimator

MODULE_VERSION = "2.0.0"
METHOD_LABEL = "Adaptive reliability-gated multimodal fusion (AGROLATTICE adaptation)"
LEGACY_METHOD_LABEL = "Validation-weighted modality-aware late fusion (AGROLATTICE adaptation)"


class MultimodalFusionError(RuntimeError):
    pass


@dataclass
class FittedFusion:
    models: dict[str, Any]
    feature_groups: dict[str, list[str]]
    weights: dict[str, float]
    validation_metrics: pd.DataFrame
    method: str = METHOD_LABEL
    reliability_models: dict[str, Any] = field(default_factory=dict)
    gating_mode: str = "Adaptive reliability gating"
    gate_floor: float = 1e-3


def validate_feature_groups(frame: pd.DataFrame, feature_groups: Mapping[str, Sequence[str]]) -> dict[str, list[str]]:
    resolved: dict[str, list[str]] = {}
    used: set[str] = set()
    for modality, columns in feature_groups.items():
        valid = [str(column) for column in columns if str(column) in frame.columns]
        if not valid:
            continue
        overlap = used.intersection(valid)
        if overlap:
            raise MultimodalFusionError(f"Features cannot belong to more than one modality: {sorted(overlap)}")
        used.update(valid)
        resolved[str(modality)] = valid
    if len(resolved) < 2:
        raise MultimodalFusionError("At least two non-empty modality feature groups are required.")
    return resolved


def _inverse_rmse_weights(metrics: pd.DataFrame) -> dict[str, float]:
    if metrics.empty:
        raise MultimodalFusionError("No modality validation metrics are available.")
    rmse = pd.to_numeric(metrics["RMSE"], errors="coerce")
    valid = rmse.notna() & rmse.gt(0)
    if not valid.any():
        return {str(row["Modality"]): 1.0 / len(metrics) for _, row in metrics.iterrows()}
    raw = 1.0 / np.maximum(rmse[valid].to_numpy(float), 1e-9)
    raw /= raw.sum()
    return dict(zip(metrics.loc[valid, "Modality"].astype(str), raw))


def _fit_reliability_model(X: pd.DataFrame, absolute_error: pd.Series, random_state: int) -> Any | None:
    target = pd.to_numeric(absolute_error, errors="coerce")
    valid = target.notna()
    if valid.sum() < 10 or target[valid].nunique() < 2:
        return None
    # Numeric-only reliability gate is deliberate: modality encoders can still
    # contain mixed/categorical features through research_models, while the gate
    # uses robust numeric environmental context without inventing ordinal coding.
    numeric = X.apply(pd.to_numeric, errors="coerce")
    if numeric.notna().sum().sum() == 0:
        return None
    pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("model", RandomForestRegressor(n_estimators=240, min_samples_leaf=3, random_state=random_state, n_jobs=-1)),
    ])
    pipe.fit(numeric.loc[valid], target.loc[valid])
    return pipe


def fit_fusion(
    frame: pd.DataFrame,
    *,
    target_column: str,
    feature_groups: Mapping[str, Sequence[str]],
    protocol: str,
    group_column: str | None = None,
    year_column: str | None = None,
    region_column: str | None = None,
    date_column: str | None = None,
    base_model: str = "Random forest",
    n_splits: int = 5,
    random_state: int = 42,
    gating_mode: str = "Adaptive reliability gating",
) -> FittedFusion:
    groups = validate_feature_groups(frame, feature_groups)
    context_columns = [c for c in (group_column, year_column, region_column, date_column) if c and c in frame.columns]
    all_features = list(dict.fromkeys([c for cols in groups.values() for c in cols]))
    working = frame[[target_column] + all_features + context_columns].loc[frame[target_column].notna()].reset_index(drop=True)
    if len(working) < 12:
        raise MultimodalFusionError("At least 12 rows with observed outcomes are required for multimodal fusion.")
    folds = build_protocol_folds(
        working, protocol=protocol, target_column=target_column, task_type="regression",
        group_column=group_column, year_column=year_column, region_column=region_column,
        date_column=date_column, n_splits=n_splits,
    )
    validation_rows = []
    fitted: dict[str, Any] = {}
    reliability: dict[str, Any] = {}
    for index, (modality, columns) in enumerate(groups.items()):
        estimator = make_estimator(base_model, task_type="regression", frame=working[columns], feature_columns=columns, random_state=random_state)
        fold_metrics, oof = evaluate_estimator(estimator, working[columns], working[target_column], folds, task_type="regression")
        pooled = regression_metrics(oof["Observed"], oof["Predicted"])
        validation_rows.append({"Modality": modality, **pooled})
        if str(gating_mode).casefold().startswith("adaptive"):
            row_ids = pd.to_numeric(oof["Row"], errors="coerce").dropna().astype(int)
            aligned = working.loc[row_ids, columns].copy()
            errors = (pd.to_numeric(oof.loc[row_ids.index, "Observed"], errors="coerce").reset_index(drop=True) - pd.to_numeric(oof.loc[row_ids.index, "Predicted"], errors="coerce").reset_index(drop=True)).abs()
            aligned = aligned.reset_index(drop=True)
            gate = _fit_reliability_model(aligned, errors, random_state + index)
            if gate is not None:
                reliability[modality] = gate
        estimator.fit(working[columns], working[target_column])
        fitted[modality] = estimator
    validation = pd.DataFrame(validation_rows)
    weights = _inverse_rmse_weights(validation)
    for modality in groups:
        weights.setdefault(modality, 0.0)
    total = sum(weights.values())
    weights = ({modality: 1.0 / len(groups) for modality in groups} if total <= 0 else {modality: value / total for modality, value in weights.items()})
    adaptive = str(gating_mode).casefold().startswith("adaptive") and bool(reliability)
    return FittedFusion(
        models=fitted, feature_groups=groups, weights=weights, validation_metrics=validation,
        method=METHOD_LABEL if adaptive else LEGACY_METHOD_LABEL,
        reliability_models=reliability,
        gating_mode="Adaptive reliability gating" if adaptive else "Global held-out inverse-RMSE weights",
    )


def _adaptive_row_weights(fitted: FittedFusion, frame: pd.DataFrame, finite: np.ndarray) -> np.ndarray:
    modalities = list(fitted.models)
    base_weights = np.array([fitted.weights.get(m, 0.0) for m in modalities], dtype=float)
    row_weights = np.tile(base_weights, (len(frame), 1))
    if fitted.reliability_models:
        for j, modality in enumerate(modalities):
            gate = fitted.reliability_models.get(modality)
            if gate is None:
                continue
            columns = fitted.feature_groups[modality]
            numeric = frame[columns].apply(pd.to_numeric, errors="coerce")
            try:
                predicted_error = np.asarray(gate.predict(numeric), dtype=float)
                predicted_error = np.maximum(predicted_error, fitted.gate_floor)
                row_weights[:, j] = 1.0 / predicted_error
            except Exception:
                # Fall back to global evidence weight for this modality only.
                row_weights[:, j] = base_weights[j]
    row_weights = np.where(finite, row_weights, 0.0)
    denominator = row_weights.sum(axis=1, keepdims=True)
    return np.divide(row_weights, denominator, out=np.zeros_like(row_weights), where=denominator > 0)


def predict_fusion(fitted: FittedFusion, frame: pd.DataFrame) -> pd.DataFrame:
    output = pd.DataFrame(index=frame.index)
    prediction_columns = []
    modalities = list(fitted.models)
    for modality, model in fitted.models.items():
        columns = fitted.feature_groups[modality]
        missing_columns = [c for c in columns if c not in frame]
        if missing_columns:
            values = np.full(len(frame), np.nan)
            available = pd.Series(False, index=frame.index)
        else:
            available = frame[columns].notna().any(axis=1)
            values = np.full(len(frame), np.nan)
            if available.any():
                values[available.to_numpy()] = model.predict(frame.loc[available, columns])
        column = f"{modality} prediction"
        output[column] = values
        output[f"{modality} available"] = available.to_numpy()
        prediction_columns.append(column)

    matrix = output[prediction_columns].to_numpy(float)
    finite = np.isfinite(matrix)
    row_weights = _adaptive_row_weights(fitted, frame, finite)
    denominator = row_weights.sum(axis=1)
    output["Fused prediction"] = np.divide(
        np.nansum(matrix * row_weights, axis=1), denominator,
        out=np.full(len(frame), np.nan), where=denominator > 0,
    )
    for j, modality in enumerate(modalities):
        output[f"{modality} fusion weight"] = row_weights[:, j]
    output["Modalities available"] = finite.sum(axis=1)
    output["Inter-modality SD"] = np.nanstd(matrix, axis=1, ddof=0)
    output["Relative disagreement (%)"] = np.where(
        np.abs(output["Fused prediction"]) > 1e-12,
        output["Inter-modality SD"] / np.abs(output["Fused prediction"]) * 100,
        np.nan,
    )
    output["Fusion method"] = fitted.method
    return output


def fusion_manifest(fitted: FittedFusion) -> dict[str, Any]:
    return {
        "method": fitted.method,
        "module_version": MODULE_VERSION,
        "implementation_type": "Independent AGROLATTICE CPU adaptation; not an exact reproduction of the cited neural gated-fusion paper.",
        "feature_groups": fitted.feature_groups,
        "global_validation_error_weights": fitted.weights,
        "gating_mode": fitted.gating_mode,
        "adaptive_gate_modalities": sorted(fitted.reliability_models),
        "gate_training": "Per-modality random-forest prediction of absolute out-of-fold error; inverse predicted error is renormalised per sample across available modalities.",
        "interpretation_guardrail": "Fusion weights indicate model reliability under learned predictive conditions; they are not causal variable or modality effects.",
        "uncertainty_note": "Inter-modality spread is model disagreement, not a calibrated probabilistic confidence interval.",
    }
