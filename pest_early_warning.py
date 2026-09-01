"""Environmental pest early-warning methods for AGROLATTICE 11.4.

This is an independent, leakage-safer adaptation of Wadhwa & Malik (2024),
Computers and Electronics in Agriculture 227, 109472.  Their environmental
feature engineering, CatBoost emphasis and SHAP interpretation are retained as
research inspiration, while AGROLATTICE defaults to site/year/forward validation
when such columns are available.  Pest risk is not a disease diagnosis.
"""
from __future__ import annotations

import importlib
import math
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin, clone
from sklearn.ensemble import AdaBoostClassifier, GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import f1_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline as SkPipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from agricultural_validation import (
    AgriculturalValidationError,
    aggregate_fold_metrics,
    applicability_profile,
    build_protocol_folds,
    evaluate_estimator,
    leakage_guard_manifest,
)

MODULE_VERSION = "1.0.0"
SOURCE_DOI = "10.1016/j.compag.2024.109472"
SOURCE_METHOD = "Wadhwa & Malik (2024) environmental pest early-warning adaptation"

PAPER_FEATURE_ALIASES = {
    "MaxT": ("MaxT", "Tmax", "TMAX", "Maximum temperature", "T2M_MAX"),
    "MinT": ("MinT", "Tmin", "TMIN", "Minimum temperature", "T2M_MIN"),
    "RH1": ("RH1(%)", "RH1", "RH morning", "Morning RH", "RH_MAX"),
    "RH2": ("RH2(%)", "RH2", "RH evening", "Evening RH", "RH_MIN"),
    "Rainfall": ("RF(mm)", "RF", "Rainfall", "Precipitation", "PRECTOTCORR"),
    "Wind": ("WS(kmph)", "WS", "Wind speed", "WS2M"),
    "Sunshine": ("SSH(hrs)", "SSH", "Sunshine hours", "Sunshine duration"),
    "Evaporation": ("EVP(mm)", "EVP", "Evaporation", "EVAPORATION_LAND"),
}

PEST_DISEASE_REFERENCE = {
    "Green Leafhopper": {
        "associated_risk": "Tungro virus disease",
        "note": "Association reported in the source paper; a predicted vector does not confirm disease presence.",
    },
    "Yellow Stem Borer": {
        "associated_risk": "Deadhearts / whiteheads",
        "note": "Damage association reported in the source paper; field confirmation remains required.",
    },
}




class EncodedClassifier(BaseEstimator, ClassifierMixin):
    """Wrap classifiers that require integer-coded labels and decode outputs."""
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


class PestEarlyWarningError(RuntimeError):
    pass


def _resolve_column(frame: pd.DataFrame, aliases: Sequence[str]) -> str | None:
    exact = {str(column).casefold(): column for column in frame.columns}
    for alias in aliases:
        if alias.casefold() in exact:
            return exact[alias.casefold()]
    return None


def resolve_paper_columns(frame: pd.DataFrame) -> dict[str, str]:
    return {canonical: column for canonical, aliases in PAPER_FEATURE_ALIASES.items() if (column := _resolve_column(frame, aliases)) is not None}


def engineer_environmental_pest_features(
    frame: pd.DataFrame,
    *,
    column_map: Mapping[str, str] | None = None,
    keep_original_columns: bool = True,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Create the four engineered variables described by Wadhwa & Malik.

    VPD follows the paper's mean-temperature/mean-RH Magnus calculation.  No
    missing values are imputed here; imputation belongs inside model folds.
    """
    mapping = dict(column_map or resolve_paper_columns(frame))
    required = ["MaxT", "MinT", "RH1", "RH2"]
    missing = [name for name in required if name not in mapping]
    if missing:
        raise PestEarlyWarningError("Feature engineering requires: " + ", ".join(missing))
    output = frame.copy() if keep_original_columns else pd.DataFrame(index=frame.index)
    max_t = pd.to_numeric(frame[mapping["MaxT"]], errors="coerce")
    min_t = pd.to_numeric(frame[mapping["MinT"]], errors="coerce")
    rh1 = pd.to_numeric(frame[mapping["RH1"]], errors="coerce")
    rh2 = pd.to_numeric(frame[mapping["RH2"]], errors="coerce")
    output["Temp_Diff"] = max_t - min_t
    output["Hum_Diff"] = rh1 - rh2
    output["Avg_Hum"] = (rh1 + rh2) / 2.0
    mean_t = (max_t + min_t) / 2.0
    es = 0.6108 * np.exp((17.27 * mean_t) / (mean_t + 237.3))
    ea = (output["Avg_Hum"].clip(0, 100) / 100.0) * es
    output["VPD"] = (es - ea).clip(lower=0)
    metadata = {
        "source_method": SOURCE_METHOD,
        "source_doi": SOURCE_DOI,
        "resolved_columns": mapping,
        "engineered_features": {
            "Temp_Diff": "MaxT - MinT",
            "Hum_Diff": "RH1 - RH2",
            "Avg_Hum": "(RH1 + RH2) / 2",
            "VPD": "es(Tmean) - ea(RHmean), Magnus form used in source paper",
        },
    }
    return output, metadata


def recommended_feature_columns(frame: pd.DataFrame, mapping: Mapping[str, str] | None = None) -> list[str]:
    mapping = dict(mapping or resolve_paper_columns(frame))
    originals = [mapping[name] for name in ("MaxT", "MinT", "RH1", "RH2", "Rainfall", "Wind", "Sunshine", "Evaporation") if name in mapping]
    engineered = [name for name in ("Temp_Diff", "Hum_Diff", "Avg_Hum", "VPD") if name in frame]
    return originals + engineered


def dependency_status() -> dict[str, bool]:
    output = {}
    for module in ("catboost", "xgboost", "lightgbm", "imblearn", "optuna", "shap"):
        try:
            importlib.import_module(module); output[module] = True
        except Exception:
            output[module] = False
    return output


def available_baselines() -> list[str]:
    names = ["SVM", "kNN", "Decision tree", "MLP", "Random forest", "Gradient boosting", "AdaBoost"]
    status = dependency_status()
    if status["imblearn"]:
        names += ["Balanced random forest", "Easy ensemble"]
    if status["xgboost"]:
        names.append("XGBoost")
    if status["catboost"]:
        names.append("CatBoost")
    if status["lightgbm"]:
        names.append("LightGBM")
    return names


def _classifier(name: str, *, random_state: int = 42):
    key = name.casefold()
    if key == "svm":
        return SVC(C=1.0, kernel="rbf", probability=True, class_weight="balanced", random_state=random_state)
    if key == "knn":
        return KNeighborsClassifier(n_neighbors=7, weights="distance")
    if key == "decision tree":
        return DecisionTreeClassifier(max_depth=None, class_weight="balanced", random_state=random_state)
    if key == "mlp":
        return EncodedClassifier(MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=1200, random_state=random_state, early_stopping=True))
    if key == "random forest":
        return RandomForestClassifier(n_estimators=400, min_samples_leaf=2, class_weight="balanced", n_jobs=-1, random_state=random_state)
    if key == "gradient boosting":
        return GradientBoostingClassifier(n_estimators=250, learning_rate=0.04, random_state=random_state)
    if key == "adaboost":
        return AdaBoostClassifier(n_estimators=250, learning_rate=0.05, random_state=random_state)
    if key == "balanced random forest":
        from imblearn.ensemble import BalancedRandomForestClassifier
        return BalancedRandomForestClassifier(n_estimators=400, min_samples_leaf=2, random_state=random_state, n_jobs=-1, sampling_strategy="all", replacement=True, bootstrap=False)
    if key == "easy ensemble":
        from imblearn.ensemble import EasyEnsembleClassifier
        return EasyEnsembleClassifier(n_estimators=20, random_state=random_state, n_jobs=-1)
    if key == "xgboost":
        from xgboost import XGBClassifier
        return EncodedClassifier(XGBClassifier(n_estimators=350, max_depth=7, learning_rate=0.04, subsample=0.9, colsample_bytree=0.9, eval_metric="mlogloss", random_state=random_state, n_jobs=-1))
    if key == "catboost":
        from catboost import CatBoostClassifier
        return EncodedClassifier(CatBoostClassifier(iterations=350, depth=7, learning_rate=0.04, verbose=False, random_seed=random_state, auto_class_weights="Balanced"))
    if key == "lightgbm":
        from lightgbm import LGBMClassifier
        return EncodedClassifier(LGBMClassifier(n_estimators=350, learning_rate=0.04, class_weight="balanced", random_state=random_state, verbosity=-1, n_jobs=-1))
    raise PestEarlyWarningError(f"Unknown classifier: {name}")


def make_classifier_pipeline(
    name: str,
    *,
    resampling: str = "Class weights / model balancing",
    random_state: int = 42,
):
    classifier = _classifier(name, random_state=random_state)
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    if resampling.casefold().startswith("smote"):
        try:
            from imblearn.combine import SMOTEENN
            from imblearn.pipeline import Pipeline
        except Exception as error:
            raise PestEarlyWarningError("SMOTE-ENN requires imbalanced-learn.") from error
        return Pipeline([
            ("imputer", imputer),
            ("scaler", scaler),
            ("resample", SMOTEENN(random_state=random_state)),
            ("model", classifier),
        ])
    return SkPipeline([("imputer", imputer), ("scaler", scaler), ("model", classifier)])


def compare_pest_models(
    frame: pd.DataFrame,
    *,
    target_column: str,
    feature_columns: Sequence[str],
    model_names: Sequence[str],
    protocol: str,
    group_column: str | None = None,
    year_column: str | None = None,
    region_column: str | None = None,
    date_column: str | None = None,
    resampling: str = "Class weights / model balancing",
    n_splits: int = 5,
    random_state: int = 42,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame], dict[str, Any]]:
    needed = [target_column] + list(feature_columns) + [c for c in (group_column, year_column, region_column, date_column) if c]
    needed = list(dict.fromkeys([c for c in needed if c in frame.columns]))
    working = frame[needed].loc[frame[target_column].notna()].reset_index(drop=True)
    if len(working) < 20 or working[target_column].nunique() < 2:
        raise PestEarlyWarningError("Pest classification needs at least 20 labelled rows and two classes.")
    folds = build_protocol_folds(
        working, protocol=protocol, target_column=target_column, task_type="classification",
        group_column=group_column, year_column=year_column, region_column=region_column,
        date_column=date_column, n_splits=n_splits,
    )
    X, y = working[list(feature_columns)], working[target_column]
    summary_rows, predictions = [], {}
    for name in model_names:
        estimator = make_classifier_pipeline(name, resampling=resampling, random_state=random_state)
        fold_metrics, oof = evaluate_estimator(estimator, X, y, folds, task_type="classification")
        predictions[name] = oof
        summary_rows.append({"Model": name, **aggregate_fold_metrics(fold_metrics)})
    manifest = {
        "source_method": SOURCE_METHOD,
        "source_doi": SOURCE_DOI,
        "protocol": protocol,
        "features": list(feature_columns),
        "target": target_column,
        "resampling": resampling,
        "leakage_guards": leakage_guard_manifest(protocol, resampling=resampling if resampling.casefold().startswith("smote") else None),
        "folds": [{"fold": f.fold, "label": f.label, "train_n": len(f.train_index), "test_n": len(f.test_index)} for f in folds],
        "adaptation_note": "Source-paper feature engineering and model families are adapted, but AGROLATTICE does not treat random 80/20 performance as proof of geographic generalisability.",
    }
    return pd.DataFrame(summary_rows), predictions, manifest


def tune_catboost(
    frame: pd.DataFrame,
    *,
    target_column: str,
    feature_columns: Sequence[str],
    protocol: str,
    group_column: str | None = None,
    year_column: str | None = None,
    region_column: str | None = None,
    date_column: str | None = None,
    n_trials: int = 20,
    random_state: int = 42,
) -> tuple[dict[str, Any], pd.DataFrame]:
    try:
        import optuna
        from catboost import CatBoostClassifier
    except Exception as error:
        raise PestEarlyWarningError("CatBoost tuning requires catboost and optuna.") from error
    needed = [target_column] + list(feature_columns) + [c for c in (group_column, year_column, region_column, date_column) if c]
    needed = list(dict.fromkeys([c for c in needed if c in frame.columns]))
    working = frame[needed].loc[frame[target_column].notna()].reset_index(drop=True)
    folds = build_protocol_folds(
        working, protocol=protocol, target_column=target_column, task_type="classification",
        group_column=group_column, year_column=year_column, region_column=region_column,
        date_column=date_column, n_splits=5,
    )
    X = working[list(feature_columns)].apply(pd.to_numeric, errors="coerce")
    y = working[target_column].astype(str)
    records = []

    def objective(trial):
        params = {
            "iterations": trial.suggest_int("iterations", 120, 450),
            "depth": trial.suggest_int("depth", 4, 10),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1e-5, 10.0, log=True),
            "random_strength": trial.suggest_float("random_strength", 1e-6, 3.0, log=True),
            "bagging_temperature": trial.suggest_float("bagging_temperature", 0.0, 1.0),
            "border_count": trial.suggest_int("border_count", 32, 255),
        }
        scores = []
        for fold in folds:
            train_x, test_x = X.iloc[fold.train_index].copy(), X.iloc[fold.test_index].copy()
            medians = train_x.median()
            train_x, test_x = train_x.fillna(medians), test_x.fillna(medians)
            train_y, test_y = y.iloc[fold.train_index], y.iloc[fold.test_index]
            model = CatBoostClassifier(**params, loss_function="MultiClass", verbose=False, random_seed=random_state, auto_class_weights="Balanced")
            model.fit(train_x, train_y)
            pred = model.predict(test_x).reshape(-1)
            scores.append(f1_score(test_y, pred, average="macro", zero_division=0))
        score = float(np.mean(scores))
        records.append({"Trial": trial.number, "Macro F1": score, **params})
        return score

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=random_state))
    study.optimize(objective, n_trials=max(3, int(n_trials)), show_progress_bar=False)
    return {**study.best_params, "best_macro_f1": float(study.best_value), "n_trials": len(study.trials)}, pd.DataFrame(records).sort_values("Macro F1", ascending=False)


def fit_pest_model(
    frame: pd.DataFrame,
    *,
    target_column: str,
    feature_columns: Sequence[str],
    model_name: str = "CatBoost",
    resampling: str = "Class weights / model balancing",
    random_state: int = 42,
):
    working = frame.loc[frame[target_column].notna()].copy()
    X = working[list(feature_columns)]
    y = working[target_column]
    model = make_classifier_pipeline(model_name, resampling=resampling, random_state=random_state)
    model.fit(X, y)
    return model, applicability_profile(working, feature_columns)


def shap_feature_importance(model, X: pd.DataFrame, *, max_rows: int = 500, random_state: int = 42) -> pd.DataFrame:
    """Return mean absolute SHAP importance when the fitted backend supports it.

    Explanation values are model explanations, not causal effects.
    """
    try:
        import shap
    except Exception as error:
        raise PestEarlyWarningError("SHAP is not installed.") from error
    if len(X) > max_rows:
        X = X.sample(max_rows, random_state=random_state)
    if not hasattr(model, "named_steps"):
        raise PestEarlyWarningError("Expected a fitted pipeline.")
    preprocess_steps = [name for name in ("imputer", "scaler") if name in model.named_steps]
    transformed = X.copy()
    for name in preprocess_steps:
        transformed = model.named_steps[name].transform(transformed)
    estimator = model.named_steps["model"]
    # Compatibility/label wrappers intentionally remain the final sklearn
    # pipeline step; SHAP needs the fitted third-party tree estimator itself.
    if hasattr(estimator, "estimator_"):
        estimator = estimator.estimator_
    try:
        explainer = shap.TreeExplainer(estimator)
        values = explainer.shap_values(transformed)
    except Exception as error:
        raise PestEarlyWarningError(f"SHAP TreeExplainer is not available for this fitted model: {error}") from error
    if isinstance(values, list):
        matrix = np.mean([np.abs(np.asarray(item)) for item in values], axis=0)
    else:
        array = np.asarray(values)
        if array.ndim == 3:
            matrix = np.mean(np.abs(array), axis=2)
        else:
            matrix = np.abs(array)
    importance = np.mean(matrix, axis=0)
    if len(importance) != X.shape[1]:
        raise PestEarlyWarningError("Could not align SHAP values to input features.")
    return pd.DataFrame({"Feature": X.columns, "Mean |SHAP|": importance}).sort_values("Mean |SHAP|", ascending=False).reset_index(drop=True)


def disease_risk_note(predicted_pest: str) -> dict[str, str] | None:
    return PEST_DISEASE_REFERENCE.get(str(predicted_pest))
