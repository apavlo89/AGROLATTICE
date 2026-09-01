"""Agricultural validation protocols for AGROLATTICE 11.15.

The module favours deployment-relevant splits (field/site/year/genotype and
forward-time) over random splits.  Preprocessing is fitted inside each training
fold through scikit-learn pipelines; callers should not pre-scale or pre-SMOTE
data before using these helpers.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    log_loss,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, KFold, StratifiedKFold

MODULE_VERSION = "1.1.0"


class AgriculturalValidationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Fold:
    fold: int
    train_index: np.ndarray
    test_index: np.ndarray
    label: str


def _non_missing_indices(values: pd.Series) -> np.ndarray:
    return np.flatnonzero(values.notna().to_numpy())


def grouped_folds(groups: Sequence[Any], n_splits: int = 5, label: str = "Grouped CV") -> list[Fold]:
    series = pd.Series(groups).astype("string")
    usable = series.notna()
    unique = series[usable].nunique()
    if unique < 2:
        raise AgriculturalValidationError("Grouped validation requires at least two distinct groups.")
    splits = min(max(2, int(n_splits)), int(unique))
    indices = np.arange(len(series))
    result = []
    splitter = GroupKFold(n_splits=splits)
    for fold_id, (train, test) in enumerate(splitter.split(indices, groups=series.fillna("__MISSING__")), 1):
        result.append(Fold(fold_id, train, test, f"{label} · fold {fold_id}"))
    return result


def leave_one_group_out_folds(groups: Sequence[Any], label: str = "Leave-one-group-out") -> list[Fold]:
    series = pd.Series(groups)
    values = [value for value in pd.unique(series.dropna())]
    if len(values) < 2:
        raise AgriculturalValidationError("Leave-one-group-out validation requires at least two groups.")
    folds: list[Fold] = []
    for fold_id, value in enumerate(values, 1):
        test = np.flatnonzero(series.eq(value).to_numpy())
        train = np.flatnonzero((series.notna() & series.ne(value)).to_numpy())
        if train.size and test.size:
            folds.append(Fold(fold_id, train, test, f"{label}: {value}"))
    return folds




def repeated_group_holdout_folds(
    groups: Sequence[Any],
    *,
    n_repeats: int = 5,
    test_fraction: float = 0.20,
    random_state: int = 42,
    label: str = "Repeated grouped holdout",
) -> list[Fold]:
    """Repeated group-isolated holdouts for ranking/stability diagnostics.

    A group is never split between train and test within a repeat. Repeated
    holdouts are complementary to deterministic GroupKFold/leave-one-group-out;
    they do not create independent external validation.
    """
    series = pd.Series(groups).astype("string")
    if series.notna().sum() < 4 or series.dropna().nunique() < 3:
        raise AgriculturalValidationError("Repeated grouped holdout requires at least three distinct groups and four observations.")
    fraction = float(np.clip(test_fraction, 0.10, 0.50))
    repeats = max(2, min(20, int(n_repeats)))
    indices = np.arange(len(series))
    splitter = GroupShuffleSplit(n_splits=repeats, test_size=fraction, random_state=int(random_state))
    result: list[Fold] = []
    for fold_id, (train, test) in enumerate(splitter.split(indices, groups=series.fillna("__MISSING__")), 1):
        if train.size and test.size:
            result.append(Fold(fold_id, train, test, f"{label} · repeat {fold_id}"))
    if not result:
        raise AgriculturalValidationError("Could not form repeated grouped holdouts.")
    return result



def frozen_group_holdout_folds(groups: Sequence[Any], holdout_value: Any, label: str = "Frozen holdout") -> list[Fold]:
    series = pd.Series(groups)
    test = np.flatnonzero(series.astype(str).eq(str(holdout_value)).to_numpy())
    train = np.flatnonzero((series.notna() & ~series.astype(str).eq(str(holdout_value))).to_numpy())
    if train.size < 2 or test.size < 1:
        raise AgriculturalValidationError("Frozen holdout requires at least two training rows and one held-out row.")
    return [Fold(1, train, test, f"{label}: {holdout_value}")]

def leave_one_year_out_folds(years: Sequence[Any]) -> list[Fold]:
    return leave_one_group_out_folds(years, "LOYO")


def leave_one_region_out_folds(regions: Sequence[Any]) -> list[Fold]:
    return leave_one_group_out_folds(regions, "LORO")


def forward_time_folds(
    dates: Sequence[Any],
    *,
    n_splits: int = 4,
    minimum_train_fraction: float = 0.45,
) -> list[Fold]:
    parsed = pd.to_datetime(pd.Series(dates), errors="coerce")
    valid = parsed.notna()
    if valid.sum() < 8:
        raise AgriculturalValidationError("Forward validation requires at least eight dated observations.")
    order = np.flatnonzero(valid.to_numpy())[np.argsort(parsed[valid].to_numpy())]
    n = len(order)
    requested = max(1, int(n_splits))
    first_test = max(2, int(math.ceil(n * float(minimum_train_fraction))))
    remaining = n - first_test
    if remaining < requested:
        requested = max(1, remaining)
    boundaries = np.linspace(first_test, n, requested + 1, dtype=int)
    folds: list[Fold] = []
    for fold_id in range(requested):
        start, stop = int(boundaries[fold_id]), int(boundaries[fold_id + 1])
        train = order[:start]
        test = order[start:stop]
        if train.size and test.size:
            start_date = parsed.iloc[test].min().date().isoformat()
            end_date = parsed.iloc[test].max().date().isoformat()
            folds.append(Fold(fold_id + 1, train, test, f"Forward {start_date} to {end_date}"))
    if not folds:
        raise AgriculturalValidationError("Could not form forward-time validation folds.")
    return folds


def random_folds(y: Sequence[Any], *, task_type: str, n_splits: int = 5, random_state: int = 42) -> list[Fold]:
    y_series = pd.Series(y)
    splits = min(max(2, int(n_splits)), max(2, len(y_series) // 2))
    indices = np.arange(len(y_series))
    if task_type.casefold().startswith("class") and y_series.nunique(dropna=True) > 1:
        minimum_class = int(y_series.value_counts().min())
        splits = min(splits, minimum_class)
        if splits < 2:
            raise AgriculturalValidationError("Stratified CV needs at least two samples in every class.")
        splitter = StratifiedKFold(n_splits=splits, shuffle=True, random_state=random_state)
        raw = splitter.split(indices, y_series)
    else:
        splitter = KFold(n_splits=splits, shuffle=True, random_state=random_state)
        raw = splitter.split(indices)
    return [Fold(i, train, test, f"Random diagnostic fold {i}") for i, (train, test) in enumerate(raw, 1)]


def build_protocol_folds(
    frame: pd.DataFrame,
    *,
    protocol: str,
    target_column: str,
    group_column: str | None = None,
    year_column: str | None = None,
    region_column: str | None = None,
    date_column: str | None = None,
    holdout_value: Any | None = None,
    task_type: str = "regression",
    n_splits: int = 5,
    random_state: int = 42,
    test_fraction: float = 0.20,
) -> list[Fold]:
    key = str(protocol).strip().casefold()
    if key in {"grouped", "grouped cv", "field grouped", "site grouped"}:
        if not group_column or group_column not in frame:
            raise AgriculturalValidationError("Grouped validation requires a group column.")
        return grouped_folds(frame[group_column], n_splits=n_splits)
    if key in {"repeated grouped holdout", "repeated group holdout", "group shuffle", "repeated group shuffle"}:
        if not group_column or group_column not in frame:
            raise AgriculturalValidationError("Repeated grouped holdout requires a grouping column.")
        return repeated_group_holdout_folds(frame[group_column], n_repeats=n_splits, test_fraction=test_fraction, random_state=random_state)
    if key in {"leave-one-group-out", "leave one group out", "logo", "leave-one-trial-out", "leave-one-field-out", "leave-one-genotype-out", "leave-one-parent-pair-out", "spatial group holdout"}:
        if not group_column or group_column not in frame:
            raise AgriculturalValidationError("Leave-one-group-out validation requires a grouping column.")
        return leave_one_group_out_folds(frame[group_column], str(protocol))
    if key in {"frozen group holdout", "frozen holdout", "reserved holdout"}:
        if not group_column or group_column not in frame:
            raise AgriculturalValidationError("Frozen holdout requires a grouping column.")
        if holdout_value is None:
            raise AgriculturalValidationError("Frozen holdout requires the reserved group value.")
        return frozen_group_holdout_folds(frame[group_column], holdout_value, "Frozen deployment-like holdout")
    if key in {"loyo", "leave-one-year-out", "leave one year out"}:
        if not year_column or year_column not in frame:
            raise AgriculturalValidationError("LOYO requires a year column.")
        return leave_one_year_out_folds(frame[year_column])
    if key in {"loro", "leave-one-region-out", "leave one region out"}:
        if not region_column or region_column not in frame:
            raise AgriculturalValidationError("LORO requires a region/site column.")
        return leave_one_region_out_folds(frame[region_column])
    if key in {"forward", "forward time", "walk-forward", "walk forward", "rolling origin"}:
        if not date_column or date_column not in frame:
            raise AgriculturalValidationError("Forward validation requires a date column.")
        return forward_time_folds(frame[date_column], n_splits=n_splits)
    if target_column not in frame:
        raise AgriculturalValidationError("Target column is missing.")
    return random_folds(frame[target_column], task_type=task_type, n_splits=n_splits, random_state=random_state)


def regression_metrics(y_true: Sequence[float], y_pred: Sequence[float]) -> dict[str, float]:
    true = pd.to_numeric(pd.Series(y_true).reset_index(drop=True), errors="coerce")
    pred = pd.to_numeric(pd.Series(y_pred).reset_index(drop=True), errors="coerce")
    valid = true.notna() & pred.notna()
    true, pred = true[valid].to_numpy(float), pred[valid].to_numpy(float)
    if len(true) == 0:
        return {"N": 0, "MAE": np.nan, "RMSE": np.nan, "Bias": np.nan, "R2": np.nan, "CCC": np.nan}
    mean_true, mean_pred = np.mean(true), np.mean(pred)
    var_true, var_pred = np.var(true), np.var(pred)
    covariance = np.mean((true - mean_true) * (pred - mean_pred))
    denominator = var_true + var_pred + (mean_true - mean_pred) ** 2
    ccc = 2 * covariance / denominator if denominator > 0 else np.nan
    return {
        "N": int(len(true)),
        "MAE": float(mean_absolute_error(true, pred)),
        "RMSE": float(np.sqrt(mean_squared_error(true, pred))),
        "Bias": float(np.mean(pred - true)),
        "R2": float(r2_score(true, pred)) if len(true) >= 2 else np.nan,
        "CCC": float(ccc),
    }


def classification_metrics(y_true: Sequence[Any], y_pred: Sequence[Any], probabilities: np.ndarray | None = None, classes: Sequence[Any] | None = None) -> dict[str, float]:
    true, pred = pd.Series(y_true).reset_index(drop=True), pd.Series(y_pred).reset_index(drop=True)
    valid = true.notna() & pred.notna()
    true, pred = true[valid].to_numpy(), pred[valid].to_numpy()
    output: dict[str, float] = {
        "N": int(len(true)),
        "Balanced accuracy": float(balanced_accuracy_score(true, pred)) if len(true) else np.nan,
        "Macro F1": float(f1_score(true, pred, average="macro", zero_division=0)) if len(true) else np.nan,
        "Weighted F1": float(f1_score(true, pred, average="weighted", zero_division=0)) if len(true) else np.nan,
        "Macro precision": float(precision_score(true, pred, average="macro", zero_division=0)) if len(true) else np.nan,
        "Macro recall": float(recall_score(true, pred, average="macro", zero_division=0)) if len(true) else np.nan,
    }
    if len(true):
        for cls in pd.unique(pd.Series(true)):
            safe = str(cls).replace(" ", "_")[:40]
            output[f"Recall[{safe}]"] = float(recall_score(true, pred, labels=[cls], average="macro", zero_division=0))
            output[f"Precision[{safe}]"] = float(precision_score(true, pred, labels=[cls], average="macro", zero_division=0))
    if probabilities is not None and len(true):
        probs = np.asarray(probabilities)[valid.to_numpy()]
        resolved_classes = np.asarray(classes if classes is not None else pd.unique(true))
        try:
            if probs.ndim == 2 and probs.shape[1] == 2 and len(resolved_classes) == 2:
                positive = resolved_classes[1]
                binary = (true == positive).astype(int)
                output["ROC AUC"] = float(roc_auc_score(binary, probs[:, 1]))
                output["PR AUC"] = float(average_precision_score(binary, probs[:, 1]))
                output["Brier"] = float(brier_score_loss(binary, probs[:, 1]))
                output["Log loss"] = float(log_loss(true, probs, labels=resolved_classes))
            elif probs.ndim == 2 and probs.shape[1] > 2 and probs.shape[1] == len(resolved_classes):
                output["ROC AUC OvR weighted"] = float(roc_auc_score(true, probs, labels=resolved_classes, multi_class="ovr", average="weighted"))
                onehot = np.column_stack([(true == cls).astype(float) for cls in resolved_classes])
                output["Multiclass Brier"] = float(np.mean(np.sum((onehot - probs) ** 2, axis=1)))
                output["Log loss"] = float(log_loss(true, probs, labels=resolved_classes))
        except Exception:
            pass
    return output



def evaluate_estimator(
    estimator,
    X: pd.DataFrame,
    y: pd.Series,
    folds: Sequence[Fold],
    *,
    task_type: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Evaluate an estimator with fold-contained fitting and preprocessing.

    The estimator may be a Pipeline.  It is cloned for each fold so scalers,
    imputers, feature selection and resampling wrappers are never fitted on the
    held-out observations.
    """
    X = X.reset_index(drop=True)
    y = y.reset_index(drop=True)
    predictions: list[dict[str, Any]] = []
    metrics_rows: list[dict[str, Any]] = []
    is_classification = task_type.casefold().startswith("class")
    for fold in folds:
        model = clone(estimator)
        X_train, X_test = X.iloc[fold.train_index], X.iloc[fold.test_index]
        y_train, y_test = y.iloc[fold.train_index], y.iloc[fold.test_index]
        if y_train.nunique(dropna=True) < 2 and is_classification:
            continue
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        probabilities = None
        classes = None
        if is_classification and hasattr(model, "predict_proba"):
            try:
                probabilities = model.predict_proba(X_test)
                classes = getattr(model, "classes_", None)
            except Exception:
                probabilities = None
        fold_metrics = classification_metrics(y_test, pred, probabilities, classes) if is_classification else regression_metrics(y_test, pred)
        fold_metrics.update({"Fold": fold.fold, "Split": fold.label, "Train N": int(len(X_train)), "Test N": int(len(X_test))})
        metrics_rows.append(fold_metrics)
        for position, (index, observed, predicted) in enumerate(zip(fold.test_index, y_test, pred)):
            row = {"Row": int(index), "Fold": fold.fold, "Split": fold.label, "Observed": observed, "Predicted": predicted}
            if probabilities is not None:
                row["Probabilities"] = {str(cls): float(probabilities[position, j]) for j, cls in enumerate(classes)}
            predictions.append(row)
    if not metrics_rows:
        raise AgriculturalValidationError("No valid folds could be evaluated.")
    return pd.DataFrame(metrics_rows), pd.DataFrame(predictions)


def aggregate_fold_metrics(metrics: pd.DataFrame) -> dict[str, float]:
    output: dict[str, float] = {"Folds": int(len(metrics))}
    for column in metrics.columns:
        if column in {"Fold", "Split", "Train N", "Test N"}:
            continue
        numeric = pd.to_numeric(metrics[column], errors="coerce")
        if numeric.notna().any():
            output[f"Mean {column}"] = float(numeric.mean())
            output[f"SD {column}"] = float(numeric.std(ddof=0))
    return output


def calibration_table_binary(y_true: Sequence[Any], probability: Sequence[float], *, positive_label: Any = 1, bins: int = 10) -> pd.DataFrame:
    true = (pd.Series(y_true) == positive_label).astype(int)
    prob = pd.to_numeric(pd.Series(probability), errors="coerce")
    valid = prob.notna()
    if valid.sum() < 5:
        return pd.DataFrame()
    observed, predicted = calibration_curve(true[valid], prob[valid], n_bins=max(3, int(bins)), strategy="quantile")
    return pd.DataFrame({"Mean predicted probability": predicted, "Observed frequency": observed})


def applicability_profile(training: pd.DataFrame, feature_columns: Sequence[str]) -> dict[str, Any]:
    """Build a transparent training-support profile for mixed tabular data.

    Numeric features use robust marginal ranges/distances. Categorical features
    retain their observed levels so an unseen level can be flagged. The result is
    a deployment-support diagnostic, not a calibrated probability of accuracy.
    """
    selected = [str(column) for column in feature_columns if str(column) in training.columns]
    numeric_features: list[str] = []
    categorical_features: list[str] = []
    numeric_data: dict[str, pd.Series] = {}
    categorical_levels: dict[str, list[str]] = {}
    for feature in selected:
        source = training[feature]
        converted = pd.to_numeric(source, errors="coerce")
        if pd.api.types.is_numeric_dtype(source) or converted.notna().mean() >= 0.80:
            numeric_features.append(feature)
            numeric_data[feature] = converted
        else:
            categorical_features.append(feature)
            levels = source.dropna().astype(str).drop_duplicates().tolist()
            categorical_levels[feature] = levels[:1000]

    numeric = pd.DataFrame(numeric_data, index=training.index)
    medians = numeric.median() if not numeric.empty else pd.Series(dtype=float)
    scales = (numeric.quantile(0.75) - numeric.quantile(0.25)).replace(0, np.nan) if not numeric.empty else pd.Series(dtype=float)
    if not numeric.empty:
        scales = scales.fillna(numeric.std(ddof=0).replace(0, np.nan)).fillna(1.0)
    return {
        "features": selected,
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "categorical_levels": categorical_levels,
        "median": {key: float(value) for key, value in medians.items() if pd.notna(value)},
        "scale": {key: float(value) for key, value in scales.items() if pd.notna(value)},
        "minimum": {key: float(value) for key, value in numeric.min().items() if pd.notna(value)} if not numeric.empty else {},
        "maximum": {key: float(value) for key, value in numeric.max().items() if pd.notna(value)} if not numeric.empty else {},
        "method": "Robust marginal numeric support plus seen categorical levels; not a calibrated probability.",
    }


def applicability_score(rows: pd.DataFrame, profile: Mapping[str, Any]) -> pd.DataFrame:
    all_features = [f for f in profile.get("features", []) if f in rows.columns]
    if not all_features:
        raise AgriculturalValidationError("Applicability profile has no matching features.")
    numeric_features = [f for f in profile.get("numeric_features", []) if f in rows.columns]
    categorical_features = [f for f in profile.get("categorical_features", []) if f in rows.columns]

    numeric_outside = pd.Series(0, index=rows.index, dtype=int)
    if numeric_features:
        median = pd.Series(profile.get("median", {}), dtype=float).reindex(numeric_features)
        scale = pd.Series(profile.get("scale", {}), dtype=float).reindex(numeric_features).replace(0, 1.0).fillna(1.0)
        minimum = pd.Series(profile.get("minimum", {}), dtype=float)
        maximum = pd.Series(profile.get("maximum", {}), dtype=float)
        data = rows[numeric_features].apply(pd.to_numeric, errors="coerce")
        z = (data - median) / scale
        array = z.to_numpy(float)
        with np.errstate(invalid="ignore"):
            robust_distance = np.sqrt(np.nanmean(np.square(array), axis=1))
        robust_distance = np.where(np.isfinite(robust_distance), robust_distance, 0.0)
        numeric_outside = pd.DataFrame({
            f: (data[f] < minimum.get(f, -np.inf)) | (data[f] > maximum.get(f, np.inf))
            for f in numeric_features
        }, index=rows.index).sum(axis=1).astype(int)
    else:
        robust_distance = np.zeros(len(rows), dtype=float)

    categorical_unseen = pd.Series(0, index=rows.index, dtype=int)
    levels_by_feature = profile.get("categorical_levels", {}) or {}
    for feature in categorical_features:
        allowed = set(str(value) for value in levels_by_feature.get(feature, []))
        values = rows[feature]
        unseen = values.notna() & ~values.astype(str).isin(allowed)
        categorical_unseen = categorical_unseen + unseen.astype(int)

    outside = numeric_outside + categorical_unseen
    support = np.exp(-0.5 * np.square(np.clip(robust_distance, 0, 8))) * 100
    # Penalise unseen categories without pretending this creates a probability.
    support = support * np.power(0.5, categorical_unseen.to_numpy(float))
    status = np.where(outside.to_numpy() > 0, "Outside training range", np.where(support >= 60, "Within support", np.where(support >= 30, "Limited support", "Low support")))
    return pd.DataFrame({
        "Applicability score (%)": np.clip(support, 0, 100),
        "Features outside training range": outside.astype(int),
        "Unseen categorical levels": categorical_unseen.astype(int),
        "Applicability status": status,
        "Robust distance": robust_distance,
    }, index=rows.index)


def leakage_guard_manifest(protocol: str, *, resampling: str | None = None) -> dict[str, Any]:
    return {
        "protocol": protocol,
        "preprocessing_fit_scope": "Training fold only",
        "imputation_fit_scope": "Training fold only",
        "scaling_fit_scope": "Training fold only",
        "feature_selection_fit_scope": "Training fold only if used",
        "class_resampling_fit_scope": "Training fold only" if resampling else "Not used",
        "class_resampling_method": resampling,
        "held_out_outcomes_used_for_training": False,
        "scientific_note": "Random CV is diagnostic only when deployment involves new sites, seasons, fields, genotypes or future time periods.",
    }
