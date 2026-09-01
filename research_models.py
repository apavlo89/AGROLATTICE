"""Leakage-safe baseline model laboratory for AGROLATTICE 11.15.

The purpose is to establish strong, reproducible baselines before advanced
paper-derived architectures are promoted. Optional XGBoost, LightGBM, CatBoost
and TabPFN backends are discovered at runtime and never prevent the core app
from starting.
"""
from __future__ import annotations

import importlib
import json
import math
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin, RegressorMixin, clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier, ExtraTreesRegressor, HistGradientBoostingClassifier, HistGradientBoostingRegressor, RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler

from agricultural_validation import (
    AgriculturalValidationError,
    aggregate_fold_metrics,
    applicability_profile,
    build_protocol_folds,
    evaluate_estimator,
    leakage_guard_manifest,
)

MODULE_VERSION = "1.1.0"




class EncodedClassifier(BaseEstimator, ClassifierMixin):
    """Wrap classifiers that require integer class labels and decode predictions."""
    def __init__(self, base_estimator):
        self.base_estimator = base_estimator

    def fit(self, X, y):
        self.label_encoder_ = LabelEncoder().fit(pd.Series(y).astype(str))
        encoded = self.label_encoder_.transform(pd.Series(y).astype(str))
        self.estimator_ = clone(self.base_estimator)
        self.estimator_.fit(X, encoded)
        self.classes_ = self.label_encoder_.classes_
        return self

    def predict(self, X):
        encoded = np.asarray(self.estimator_.predict(X)).astype(int).reshape(-1)
        return self.label_encoder_.inverse_transform(encoded)

    def predict_proba(self, X):
        return self.estimator_.predict_proba(X)


class CompatibleRegressor(BaseEstimator, RegressorMixin):
    """Expose a stable scikit-learn estimator interface for optional regressors.

    Some third-party estimators (notably particular CatBoost releases) do not
    expose the modern ``__sklearn_tags__`` API expected by recent sklearn
    Pipelines. Wrapping them prevents a runtime failure without changing the
    underlying fit/predict behaviour.
    """
    def __init__(self, base_estimator):
        self.base_estimator = base_estimator

    def fit(self, X, y):
        self.estimator_ = clone(self.base_estimator)
        self.estimator_.fit(X, y)
        return self

    def predict(self, X):
        return np.asarray(self.estimator_.predict(X)).reshape(-1)


@dataclass(frozen=True)
class DependencyStatus:
    available: bool
    version: str | None
    detail: str


def dependency_status() -> dict[str, DependencyStatus]:
    result: dict[str, DependencyStatus] = {}
    for module in ("xgboost", "lightgbm", "catboost", "optuna", "imblearn", "shap", "tabpfn"):
        try:
            imported = importlib.import_module(module)
            result[module] = DependencyStatus(True, getattr(imported, "__version__", None), "Available")
        except Exception as error:
            result[module] = DependencyStatus(False, None, f"Optional dependency unavailable: {error}")
    return result


def infer_feature_types(frame: pd.DataFrame, features: Sequence[str]) -> tuple[list[str], list[str]]:
    numeric, categorical = [], []
    for column in features:
        if column not in frame:
            continue
        series = frame[column]
        converted = pd.to_numeric(series, errors="coerce")
        if pd.api.types.is_numeric_dtype(series) or converted.notna().mean() >= 0.95:
            numeric.append(column)
        else:
            categorical.append(column)
    return numeric, categorical


def preprocessing_pipeline(frame: pd.DataFrame, feature_columns: Sequence[str], *, scale_numeric: bool = False) -> ColumnTransformer:
    numeric, categorical = infer_feature_types(frame, feature_columns)
    if not numeric and not categorical:
        raise AgriculturalValidationError("No usable feature columns were selected.")
    transformers = []
    if numeric:
        steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
        if scale_numeric:
            steps.append(("scaler", StandardScaler()))
        transformers.append(("numeric", Pipeline(steps), numeric))
    if categorical:
        transformers.append((
            "categorical",
            Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ]),
            categorical,
        ))
    return ColumnTransformer(transformers, remainder="drop", verbose_feature_names_out=False)


def available_model_names(task_type: str) -> list[str]:
    classification = task_type.casefold().startswith("class")
    names = [
        "Logistic regression" if classification else "Ridge",
        "Random forest",
        "Extra trees",
        "Histogram gradient boosting",
    ]
    status = dependency_status()
    if status["xgboost"].available:
        names.append("XGBoost")
    if status["lightgbm"].available:
        names.append("LightGBM")
    if status["catboost"].available:
        names.append("CatBoost")
    if status["tabpfn"].available:
        names.append("TabPFN")
    return names


def make_estimator(
    name: str,
    *,
    task_type: str,
    frame: pd.DataFrame,
    feature_columns: Sequence[str],
    random_state: int = 42,
    class_weight: str | None = "balanced",
):
    classification = task_type.casefold().startswith("class")
    key = name.strip().casefold()
    scale = key in {"ridge", "logistic regression", "tabpfn"}
    preprocess = preprocessing_pipeline(frame, feature_columns, scale_numeric=scale)

    if key == "ridge":
        estimator = Ridge(alpha=1.0)
    elif key == "logistic regression":
        estimator = LogisticRegression(max_iter=4000, class_weight=class_weight, random_state=random_state)
    elif key == "random forest":
        estimator = RandomForestClassifier(n_estimators=400, min_samples_leaf=2, class_weight=class_weight, n_jobs=-1, random_state=random_state) if classification else RandomForestRegressor(n_estimators=400, min_samples_leaf=2, n_jobs=-1, random_state=random_state)
    elif key == "extra trees":
        estimator = ExtraTreesClassifier(n_estimators=400, min_samples_leaf=2, class_weight=class_weight, n_jobs=-1, random_state=random_state) if classification else ExtraTreesRegressor(n_estimators=400, min_samples_leaf=2, n_jobs=-1, random_state=random_state)
    elif key == "histogram gradient boosting":
        estimator = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.05, random_state=random_state) if classification else HistGradientBoostingRegressor(max_iter=250, learning_rate=0.05, random_state=random_state)
    elif key == "xgboost":
        if classification:
            from xgboost import XGBClassifier
            estimator = EncodedClassifier(XGBClassifier(n_estimators=350, max_depth=6, learning_rate=0.04, subsample=0.85, colsample_bytree=0.85, eval_metric="mlogloss", random_state=random_state, n_jobs=-1))
        else:
            from xgboost import XGBRegressor
            estimator = XGBRegressor(n_estimators=350, max_depth=6, learning_rate=0.04, subsample=0.85, colsample_bytree=0.85, objective="reg:squarederror", random_state=random_state, n_jobs=-1)
    elif key == "lightgbm":
        if classification:
            from lightgbm import LGBMClassifier
            estimator = EncodedClassifier(LGBMClassifier(n_estimators=350, learning_rate=0.04, class_weight=class_weight, random_state=random_state, verbosity=-1))
        else:
            from lightgbm import LGBMRegressor
            estimator = LGBMRegressor(n_estimators=350, learning_rate=0.04, random_state=random_state, verbosity=-1)
    elif key == "catboost":
        if classification:
            from catboost import CatBoostClassifier
            estimator = EncodedClassifier(CatBoostClassifier(iterations=350, depth=7, learning_rate=0.04, verbose=False, random_seed=random_state, auto_class_weights="Balanced" if class_weight else None))
        else:
            from catboost import CatBoostRegressor
            estimator = CompatibleRegressor(CatBoostRegressor(iterations=350, depth=7, learning_rate=0.04, verbose=False, random_seed=random_state, loss_function="RMSE"))
    elif key == "tabpfn":
        try:
            from tabpfn import TabPFNClassifier, TabPFNRegressor
            estimator = TabPFNClassifier() if classification else TabPFNRegressor()
        except Exception as error:
            raise AgriculturalValidationError(f"TabPFN is not usable in this environment: {error}") from error
    else:
        raise AgriculturalValidationError(f"Unknown model: {name}")
    return Pipeline([("preprocess", preprocess), ("model", estimator)])


def compare_models(
    frame: pd.DataFrame,
    *,
    target_column: str,
    feature_columns: Sequence[str],
    task_type: str,
    model_names: Sequence[str],
    protocol: str,
    group_column: str | None = None,
    year_column: str | None = None,
    region_column: str | None = None,
    date_column: str | None = None,
    holdout_value: Any | None = None,
    n_splits: int = 5,
    random_state: int = 42,
    test_fraction: float = 0.20,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame], dict[str, Any]]:
    required = [target_column] + [column for column in feature_columns if column in frame]
    working = frame[required + [c for c in (group_column, year_column, region_column, date_column) if c and c in frame and c not in required]].copy()
    working = working.loc[working[target_column].notna()].reset_index(drop=True)
    if len(working) < 8:
        raise AgriculturalValidationError("At least eight rows with observed outcomes are required.")
    folds = build_protocol_folds(
        working,
        protocol=protocol,
        target_column=target_column,
        group_column=group_column,
        year_column=year_column,
        region_column=region_column,
        date_column=date_column,
        holdout_value=holdout_value,
        task_type=task_type,
        n_splits=n_splits,
        random_state=random_state,
        test_fraction=test_fraction,
    )
    X = working[list(feature_columns)].copy()
    y = working[target_column].copy()
    rows, detail = [], {}
    failures: dict[str, str] = {}
    fold_metrics_by_model: dict[str, list[dict[str, Any]]] = {}
    for model_name in model_names:
        try:
            estimator = make_estimator(model_name, task_type=task_type, frame=X, feature_columns=feature_columns, random_state=random_state)
            fold_metrics, predictions = evaluate_estimator(estimator, X, y, folds, task_type=task_type)
            detail[model_name] = predictions
            fold_metrics_by_model[model_name] = fold_metrics.to_dict(orient="records")
            aggregate = aggregate_fold_metrics(fold_metrics)
            rows.append({"Model": model_name, "Status": "Completed", **aggregate})
        except Exception as error:
            failures[model_name] = str(error)
            detail[model_name] = pd.DataFrame()
            fold_metrics_by_model[model_name] = []
            rows.append({"Model": model_name, "Status": "Failed", "Failure": str(error)})
    summary = pd.DataFrame(rows)
    manifest = {
        "protocol": protocol,
        "folds": [{"fold": fold.fold, "label": fold.label, "train_n": int(len(fold.train_index)), "test_n": int(len(fold.test_index))} for fold in folds],
        "features": list(feature_columns),
        "target": target_column,
        "task_type": task_type,
        "leakage_guards": leakage_guard_manifest(protocol),
        "random_state": int(random_state),
        "holdout_value": holdout_value,
        "test_fraction": float(test_fraction),
        "fold_metrics_by_model": fold_metrics_by_model,
        "failures": failures,
    }
    return summary, detail, manifest


def fit_final_model(
    frame: pd.DataFrame,
    *,
    target_column: str,
    feature_columns: Sequence[str],
    task_type: str,
    model_name: str,
    random_state: int = 42,
):
    working = frame.loc[frame[target_column].notna()].copy()
    estimator = make_estimator(model_name, task_type=task_type, frame=working, feature_columns=feature_columns, random_state=random_state)
    estimator.fit(working[list(feature_columns)], working[target_column])
    profile = applicability_profile(working, feature_columns)
    return estimator, profile


def conformal_half_width_from_oof(predictions: pd.DataFrame, *, coverage: float = 0.90) -> float | None:
    if predictions.empty or "Observed" not in predictions or "Predicted" not in predictions:
        return None
    observed = pd.to_numeric(predictions["Observed"], errors="coerce")
    predicted = pd.to_numeric(predictions["Predicted"], errors="coerce")
    residuals = (observed - predicted).abs().dropna().to_numpy(float)
    if len(residuals) < 10:
        return None
    coverage = float(np.clip(coverage, 0.5, 0.99))
    n = len(residuals)
    quantile = min(1.0, math.ceil((n + 1) * coverage) / n)
    return float(np.quantile(residuals, quantile, method="higher"))
