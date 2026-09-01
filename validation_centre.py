
"""Validation Centre for the AgroLattice Research Tool.

The module evaluates already-generated predictions against observations and can
optionally cross-validate a simple linear calibration. It does not manufacture
observations or silently impute missing outcomes.
"""
from __future__ import annotations

import io
import json
import math
import zipfile
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold, KFold

MODULE_VERSION = "1.0.0"


class ValidationCentreError(RuntimeError):
    """Raised when a validation workflow cannot be completed safely."""


def json_safe_dataframe(value: Any) -> pd.DataFrame | None:
    if isinstance(value, pd.DataFrame):
        return value.copy()
    if isinstance(value, Mapping) and value.get("__type__") == "dataframe":
        return pd.DataFrame(value.get("records", []), columns=value.get("columns"))
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        try:
            frame = pd.DataFrame(value)
            return frame if not frame.empty else None
        except Exception:
            return None
    return None


def clean_validation_frame(
    frame: pd.DataFrame,
    *,
    observed_column: str,
    prediction_columns: Sequence[str],
    group_column: str | None = None,
    date_column: str | None = None,
) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise ValidationCentreError("Validation data are empty.")
    required = [observed_column, *prediction_columns]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValidationCentreError("Missing validation columns: " + ", ".join(missing))
    output = frame.copy()
    output[observed_column] = pd.to_numeric(output[observed_column], errors="coerce")
    for column in prediction_columns:
        output[column] = pd.to_numeric(output[column], errors="coerce")
    if date_column and date_column in output.columns:
        output[date_column] = pd.to_datetime(output[date_column], errors="coerce")
    if group_column and group_column in output.columns:
        output[group_column] = output[group_column].astype("string")
    output = output.dropna(subset=[observed_column])
    if output.empty:
        raise ValidationCentreError("No valid observed values remain.")
    return output


def concordance_correlation_coefficient(observed: Sequence[float], predicted: Sequence[float]) -> float:
    x = np.asarray(observed, dtype=float)
    y = np.asarray(predicted, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    if x.size < 2:
        return float("nan")
    covariance = np.mean((x - x.mean()) * (y - y.mean()))
    denominator = x.var(ddof=0) + y.var(ddof=0) + (x.mean() - y.mean()) ** 2
    return float(2 * covariance / denominator) if denominator > 0 else float("nan")


def regression_metrics(observed: Sequence[float], predicted: Sequence[float]) -> dict[str, float]:
    x = np.asarray(observed, dtype=float)
    y = np.asarray(predicted, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    if x.size == 0:
        return {name: float("nan") for name in [
            "N", "Bias", "MAE", "RMSE", "R²", "Pearson r", "Spearman rho",
            "CCC", "Calibration slope", "Calibration intercept", "NSE", "MAPE (%)"
        ]}
    bias = float(np.mean(y - x))
    mae = float(mean_absolute_error(x, y))
    rmse = float(math.sqrt(mean_squared_error(x, y)))
    r2 = float(r2_score(x, y)) if x.size >= 2 and np.nanstd(x) > 0 else float("nan")
    pearson = float(stats.pearsonr(x, y).statistic) if x.size >= 3 and np.std(x) > 0 and np.std(y) > 0 else float("nan")
    spearman = float(stats.spearmanr(x, y).statistic) if x.size >= 3 else float("nan")
    if x.size >= 2 and np.std(y) > 0:
        calibration = stats.linregress(y, x)
        slope = float(calibration.slope)
        intercept = float(calibration.intercept)
    else:
        slope = intercept = float("nan")
    denominator = float(np.sum((x - np.mean(x)) ** 2))
    nse = float(1 - np.sum((x - y) ** 2) / denominator) if denominator > 0 else float("nan")
    nonzero = np.abs(x) > 1e-12
    mape = float(np.mean(np.abs((y[nonzero] - x[nonzero]) / x[nonzero])) * 100) if nonzero.any() else float("nan")
    return {
        "N": int(x.size),
        "Bias": bias,
        "MAE": mae,
        "RMSE": rmse,
        "R²": r2,
        "Pearson r": pearson,
        "Spearman rho": spearman,
        "CCC": concordance_correlation_coefficient(x, y),
        "Calibration slope": slope,
        "Calibration intercept": intercept,
        "NSE": nse,
        "MAPE (%)": mape,
    }


def binary_metrics(
    observed: Sequence[float],
    score: Sequence[float],
    *,
    threshold: float = 0.5,
) -> dict[str, float]:
    truth = np.asarray(observed, dtype=float)
    probability = np.asarray(score, dtype=float)
    mask = np.isfinite(truth) & np.isfinite(probability)
    truth = truth[mask].astype(int)
    probability = np.clip(probability[mask], 0, 1)
    prediction = (probability >= threshold).astype(int)
    if truth.size == 0:
        raise ValidationCentreError("No complete binary validation rows remain.")
    matrix = confusion_matrix(truth, prediction, labels=[0, 1])
    tn, fp, fn, tp = matrix.ravel()
    specificity = tn / (tn + fp) if tn + fp else float("nan")
    auc = roc_auc_score(truth, probability) if len(np.unique(truth)) == 2 else float("nan")
    return {
        "N": int(truth.size),
        "Threshold": float(threshold),
        "Accuracy": float(accuracy_score(truth, prediction)),
        "Balanced accuracy": float(balanced_accuracy_score(truth, prediction)),
        "Sensitivity / recall": float(recall_score(truth, prediction, zero_division=0)),
        "Specificity": float(specificity),
        "Precision": float(precision_score(truth, prediction, zero_division=0)),
        "F1": float(f1_score(truth, prediction, zero_division=0)),
        "ROC AUC": float(auc),
        "Brier score": float(brier_score_loss(truth, probability)),
        "True negatives": int(tn),
        "False positives": int(fp),
        "False negatives": int(fn),
        "True positives": int(tp),
    }


def _linear_calibrate(train_observed: np.ndarray, train_predicted: np.ndarray, test_predicted: np.ndarray) -> np.ndarray:
    mask = np.isfinite(train_observed) & np.isfinite(train_predicted)
    if mask.sum() < 3 or np.std(train_predicted[mask]) <= 0:
        return test_predicted.astype(float)
    model = LinearRegression()
    model.fit(train_predicted[mask].reshape(-1, 1), train_observed[mask])
    return model.predict(test_predicted.reshape(-1, 1))


def cross_validated_calibration(
    frame: pd.DataFrame,
    *,
    observed_column: str,
    prediction_column: str,
    strategy: str = "None",
    group_column: str | None = None,
    date_column: str | None = None,
    folds: int = 5,
    temporal_train_fraction: float = 0.7,
) -> pd.DataFrame:
    data = frame[[observed_column, prediction_column] + [
        column for column in [group_column, date_column] if column and column in frame.columns
    ]].copy()
    data[observed_column] = pd.to_numeric(data[observed_column], errors="coerce")
    data[prediction_column] = pd.to_numeric(data[prediction_column], errors="coerce")
    data = data.dropna(subset=[observed_column, prediction_column])
    if data.empty:
        raise ValidationCentreError("No complete rows remain for calibration.")
    data["Calibrated prediction"] = np.nan
    data["Validation split"] = ""

    if strategy == "None":
        data["Calibrated prediction"] = data[prediction_column]
        data["Validation split"] = "Direct evaluation"
        return data

    if strategy == "Temporal holdout":
        if not date_column or date_column not in data.columns:
            raise ValidationCentreError("Temporal holdout requires a date or year column.")
        data = data.sort_values(date_column).reset_index(drop=True)
        split = max(2, min(len(data) - 1, int(round(len(data) * temporal_train_fraction))))
        train_index = np.arange(split)
        test_index = np.arange(split, len(data))
        data.loc[test_index, "Calibrated prediction"] = _linear_calibrate(
            data.loc[train_index, observed_column].to_numpy(float),
            data.loc[train_index, prediction_column].to_numpy(float),
            data.loc[test_index, prediction_column].to_numpy(float),
        )
        data.loc[test_index, "Validation split"] = "Temporal test"
        return data.loc[test_index].copy()

    if strategy == "Grouped cross-validation":
        if not group_column or group_column not in data.columns:
            raise ValidationCentreError("Grouped cross-validation requires a grouping column.")
        groups = data[group_column].astype(str).to_numpy()
        unique_groups = np.unique(groups)
        if unique_groups.size < 3:
            raise ValidationCentreError("Grouped calibration requires at least three independent groups.")
        splitter = GroupKFold(n_splits=min(max(2, folds), unique_groups.size))
        split_iterator = splitter.split(data, groups=groups)
    elif strategy == "K-fold cross-validation":
        if len(data) < 6:
            raise ValidationCentreError("K-fold calibration requires at least six complete rows.")
        splitter = KFold(n_splits=min(max(2, folds), len(data)), shuffle=True, random_state=42)
        split_iterator = splitter.split(data)
    else:
        raise ValidationCentreError(f"Unknown calibration strategy: {strategy}")

    for fold, (train_index, test_index) in enumerate(split_iterator, start=1):
        calibrated = _linear_calibrate(
            data.iloc[train_index][observed_column].to_numpy(float),
            data.iloc[train_index][prediction_column].to_numpy(float),
            data.iloc[test_index][prediction_column].to_numpy(float),
        )
        data.iloc[test_index, data.columns.get_loc("Calibrated prediction")] = calibrated
        data.iloc[test_index, data.columns.get_loc("Validation split")] = f"Fold {fold}"
    return data


def evaluate_regression_models(
    frame: pd.DataFrame,
    *,
    observed_column: str,
    prediction_columns: Sequence[str],
    calibration_strategy: str = "None",
    group_column: str | None = None,
    date_column: str | None = None,
    folds: int = 5,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    cleaned = clean_validation_frame(
        frame,
        observed_column=observed_column,
        prediction_columns=prediction_columns,
        group_column=group_column,
        date_column=date_column,
    )
    metric_rows: list[dict[str, Any]] = []
    prediction_rows: list[pd.DataFrame] = []
    for model_name in prediction_columns:
        calibrated = cross_validated_calibration(
            cleaned,
            observed_column=observed_column,
            prediction_column=model_name,
            strategy=calibration_strategy,
            group_column=group_column,
            date_column=date_column,
            folds=folds,
        )
        evaluated_column = "Calibrated prediction"
        metrics = regression_metrics(calibrated[observed_column], calibrated[evaluated_column])
        metric_rows.append({
            "Model": model_name,
            "Evaluation": "Raw" if calibration_strategy == "None" else f"Linear calibration · {calibration_strategy}",
            **metrics,
        })
        result = calibrated.copy()
        result["Model"] = model_name
        result["Observed"] = result[observed_column]
        result["Raw prediction"] = result[model_name]
        result["Prediction"] = result[evaluated_column]
        result["Residual"] = result["Prediction"] - result["Observed"]
        result["Absolute error"] = result["Residual"].abs()
        prediction_rows.append(result)
    return pd.DataFrame(metric_rows), pd.concat(prediction_rows, ignore_index=True)


def grouped_regression_metrics(
    predictions_long: pd.DataFrame,
    *,
    group_column: str,
) -> pd.DataFrame:
    if group_column not in predictions_long.columns:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for (model, group), subset in predictions_long.groupby(["Model", group_column], dropna=False):
        rows.append({"Model": model, group_column: group, **regression_metrics(subset["Observed"], subset["Prediction"])})
    return pd.DataFrame(rows)


def bootstrap_metric_intervals(
    observed: Sequence[float],
    predicted: Sequence[float],
    *,
    iterations: int = 1000,
    confidence: float = 0.95,
    seed: int = 42,
) -> pd.DataFrame:
    x = np.asarray(observed, dtype=float)
    y = np.asarray(predicted, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    if x.size < 3:
        return pd.DataFrame()
    rng = np.random.default_rng(seed)
    records: list[dict[str, float]] = []
    for _ in range(max(100, int(iterations))):
        index = rng.integers(0, x.size, size=x.size)
        metrics = regression_metrics(x[index], y[index])
        records.append({key: value for key, value in metrics.items() if key in {"Bias", "MAE", "RMSE", "R²", "CCC"}})
    frame = pd.DataFrame(records)
    alpha = (1 - confidence) / 2
    rows = []
    point = regression_metrics(x, y)
    for metric in frame.columns:
        rows.append({
            "Metric": metric,
            "Estimate": point.get(metric),
            "Lower": frame[metric].quantile(alpha),
            "Upper": frame[metric].quantile(1 - alpha),
            "Confidence": confidence,
        })
    return pd.DataFrame(rows)


def bland_altman_table(observed: Sequence[float], predicted: Sequence[float]) -> tuple[pd.DataFrame, dict[str, float]]:
    x = np.asarray(observed, dtype=float)
    y = np.asarray(predicted, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    differences = y - x
    means = (x + y) / 2
    bias = float(np.mean(differences)) if differences.size else float("nan")
    sd = float(np.std(differences, ddof=1)) if differences.size > 1 else float("nan")
    summary = {
        "Bias": bias,
        "Lower agreement limit": bias - 1.96 * sd if np.isfinite(sd) else float("nan"),
        "Upper agreement limit": bias + 1.96 * sd if np.isfinite(sd) else float("nan"),
    }
    return pd.DataFrame({"Mean of observed and predicted": means, "Difference (predicted - observed)": differences}), summary


def validation_export_package(
    *,
    settings: Mapping[str, Any],
    metrics: pd.DataFrame,
    predictions: pd.DataFrame,
    grouped_metrics: pd.DataFrame | None = None,
    bootstrap_intervals: pd.DataFrame | None = None,
    binary_metrics_frame: pd.DataFrame | None = None,
) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("validation_settings.json", json.dumps(dict(settings), indent=2, default=str))
        archive.writestr("validation_metrics.csv", metrics.to_csv(index=False))
        archive.writestr("validation_predictions.csv", predictions.to_csv(index=False))
        if grouped_metrics is not None and not grouped_metrics.empty:
            archive.writestr("validation_metrics_by_group.csv", grouped_metrics.to_csv(index=False))
        if bootstrap_intervals is not None and not bootstrap_intervals.empty:
            archive.writestr("bootstrap_metric_intervals.csv", bootstrap_intervals.to_csv(index=False))
        if binary_metrics_frame is not None and not binary_metrics_frame.empty:
            archive.writestr("binary_validation_metrics.csv", binary_metrics_frame.to_csv(index=False))
        archive.writestr(
            "README.txt",
            "Release 2 Validation Centre export. Predictions remain model outputs; validation quality depends on independent, correctly matched observations.\n",
        )
    return buffer.getvalue()
