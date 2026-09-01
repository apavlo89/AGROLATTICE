
"""Model ensemble and disagreement analysis for AgroLattice."""
from __future__ import annotations

import io
import json
import math
import zipfile
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
from scipy import stats

MODULE_VERSION = "1.0.0"


class EnsembleAnalysisError(RuntimeError):
    """Raised when an ensemble cannot be calculated."""


def inverse_error_weights(
    metrics: pd.DataFrame,
    *,
    model_column: str = "Model",
    error_column: str = "RMSE",
    minimum_weight: float = 1e-6,
) -> dict[str, float]:
    if metrics.empty or model_column not in metrics.columns or error_column not in metrics.columns:
        raise EnsembleAnalysisError("Validation metrics do not contain model and error columns.")
    errors = pd.to_numeric(metrics[error_column], errors="coerce")
    models = metrics[model_column].astype(str)
    valid = errors.notna() & (errors >= 0)
    if not valid.any():
        raise EnsembleAnalysisError("No valid model errors are available for inverse-error weighting.")
    raw = 1.0 / np.maximum(errors[valid].to_numpy(float), minimum_weight)
    raw = raw / raw.sum()
    return dict(zip(models[valid], raw))


def normalise_weights(model_columns: Sequence[str], weights: Mapping[str, float] | None = None) -> dict[str, float]:
    columns = [str(column) for column in model_columns]
    if not columns:
        raise EnsembleAnalysisError("Select at least one model column.")
    if weights is None:
        return {column: 1 / len(columns) for column in columns}
    raw = np.array([max(0.0, float(weights.get(column, 0.0))) for column in columns], dtype=float)
    if raw.sum() <= 0:
        raise EnsembleAnalysisError("At least one ensemble weight must be positive.")
    raw = raw / raw.sum()
    return dict(zip(columns, raw))


def calculate_ensemble(
    frame: pd.DataFrame,
    *,
    model_columns: Sequence[str],
    method: str = "Mean",
    weights: Mapping[str, float] | None = None,
    trim_fraction: float = 0.1,
    observed_column: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise EnsembleAnalysisError("Ensemble input data are empty.")
    columns = [column for column in model_columns if column in frame.columns]
    if not columns:
        raise EnsembleAnalysisError("None of the selected model columns exist.")
    output = frame.copy()
    matrix = output[columns].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    available = np.isfinite(matrix)
    model_count = available.sum(axis=1)

    if method in {"Weighted mean", "Inverse-error weighted"}:
        resolved_weights = normalise_weights(columns, weights)
        weight_array = np.array([resolved_weights[column] for column in columns], dtype=float)
        row_weights = np.where(available, weight_array, 0.0)
        denominator = row_weights.sum(axis=1)
        ensemble = np.divide(
            np.nansum(matrix * row_weights, axis=1),
            denominator,
            out=np.full(len(output), np.nan),
            where=denominator > 0,
        )
    elif method == "Median":
        resolved_weights = normalise_weights(columns)
        ensemble = np.nanmedian(matrix, axis=1)
    elif method == "Trimmed mean":
        resolved_weights = normalise_weights(columns)
        ensemble_values = []
        for row in matrix:
            values = row[np.isfinite(row)]
            if values.size == 0:
                ensemble_values.append(np.nan)
            elif values.size < 3:
                ensemble_values.append(float(np.mean(values)))
            else:
                ensemble_values.append(float(stats.trim_mean(values, proportiontocut=max(0, min(0.4, trim_fraction)))))
        ensemble = np.asarray(ensemble_values)
    else:
        resolved_weights = normalise_weights(columns)
        ensemble = np.nanmean(matrix, axis=1)

    output["Ensemble prediction"] = ensemble
    output["Models available"] = model_count
    output["Model mean"] = np.nanmean(matrix, axis=1)
    output["Model median"] = np.nanmedian(matrix, axis=1)
    output["Model SD"] = np.nanstd(matrix, axis=1, ddof=0)
    output["Model minimum"] = np.nanmin(matrix, axis=1)
    output["Model maximum"] = np.nanmax(matrix, axis=1)
    output["Model range"] = output["Model maximum"] - output["Model minimum"]
    output["Relative disagreement (%)"] = np.where(
        np.abs(output["Ensemble prediction"]) > 1e-12,
        output["Model SD"] / np.abs(output["Ensemble prediction"]) * 100,
        np.nan,
    )
    output["Model P10"] = np.nanquantile(matrix, 0.10, axis=1)
    output["Model P90"] = np.nanquantile(matrix, 0.90, axis=1)
    output["All models above ensemble"] = np.all(np.where(available, matrix >= ensemble[:, None], True), axis=1)
    output["All models below ensemble"] = np.all(np.where(available, matrix <= ensemble[:, None], True), axis=1)

    weight_table = pd.DataFrame({
        "Model": columns,
        "Weight": [resolved_weights[column] for column in columns],
        "Method": method,
    })
    if observed_column and observed_column in output.columns:
        observed = pd.to_numeric(output[observed_column], errors="coerce")
        output["Ensemble residual"] = output["Ensemble prediction"] - observed
        output["Ensemble absolute error"] = output["Ensemble residual"].abs()
    return output, weight_table


def model_pairwise_agreement(frame: pd.DataFrame, model_columns: Sequence[str]) -> pd.DataFrame:
    data = frame[list(model_columns)].apply(pd.to_numeric, errors="coerce")
    rows = []
    for index, model_a in enumerate(model_columns):
        for model_b in model_columns[index + 1:]:
            paired = data[[model_a, model_b]].dropna()
            if len(paired) < 3:
                pearson = spearman = rmse_difference = float("nan")
            else:
                pearson = float(stats.pearsonr(paired[model_a], paired[model_b]).statistic) if paired[model_a].std() > 0 and paired[model_b].std() > 0 else float("nan")
                spearman = float(stats.spearmanr(paired[model_a], paired[model_b]).statistic)
                rmse_difference = float(np.sqrt(np.mean((paired[model_a] - paired[model_b]) ** 2)))
            rows.append({
                "Model A": model_a,
                "Model B": model_b,
                "N paired": int(len(paired)),
                "Pearson r": pearson,
                "Spearman rho": spearman,
                "RMSE between models": rmse_difference,
            })
    return pd.DataFrame(rows)


def ranking_disagreement(
    frame: pd.DataFrame,
    *,
    model_columns: Sequence[str],
    id_column: str | None = None,
    higher_is_better: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    data = frame.copy()
    ranks = pd.DataFrame(index=data.index)
    for model in model_columns:
        values = pd.to_numeric(data[model], errors="coerce")
        ranks[model] = values.rank(ascending=not higher_is_better, method="average")
    output = pd.DataFrame(index=data.index)
    if id_column and id_column in data.columns:
        output[id_column] = data[id_column]
    output["Mean model rank"] = ranks.mean(axis=1)
    output["Rank SD"] = ranks.std(axis=1, ddof=0)
    output["Best rank"] = ranks.min(axis=1)
    output["Worst rank"] = ranks.max(axis=1)
    output["Rank range"] = output["Worst rank"] - output["Best rank"]
    correlations = ranks.corr(method="spearman")
    return output.reset_index(drop=True), correlations


def consensus_classification(
    frame: pd.DataFrame,
    *,
    model_columns: Sequence[str],
    threshold: float,
    direction: str = "Above",
) -> pd.DataFrame:
    matrix = frame[list(model_columns)].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    available = np.isfinite(matrix)
    if direction == "Below":
        votes = matrix <= threshold
    else:
        votes = matrix >= threshold
    votes = np.where(available, votes, False)
    denominator = available.sum(axis=1)
    support = np.divide(votes.sum(axis=1), denominator, out=np.full(len(frame), np.nan), where=denominator > 0)
    return pd.DataFrame({
        "Models available": denominator,
        "Models supporting condition": votes.sum(axis=1),
        "Consensus probability (%)": support * 100,
        "Unanimous": (support == 1.0) & (denominator > 0),
        "Majority": (support >= 0.5) & (denominator > 0),
    })


def ensemble_export_package(
    *,
    settings: Mapping[str, Any],
    ensemble_results: pd.DataFrame,
    weights: pd.DataFrame,
    pairwise_agreement: pd.DataFrame,
    ranking_results: pd.DataFrame | None = None,
    ranking_correlations: pd.DataFrame | None = None,
) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("ensemble_settings.json", json.dumps(dict(settings), indent=2, default=str))
        archive.writestr("ensemble_predictions_and_disagreement.csv", ensemble_results.to_csv(index=False))
        archive.writestr("ensemble_weights.csv", weights.to_csv(index=False))
        archive.writestr("model_pairwise_agreement.csv", pairwise_agreement.to_csv(index=False))
        if ranking_results is not None and not ranking_results.empty:
            archive.writestr("ranking_disagreement.csv", ranking_results.to_csv(index=False))
        if ranking_correlations is not None and not ranking_correlations.empty:
            archive.writestr("ranking_spearman_correlations.csv", ranking_correlations.to_csv())
        archive.writestr(
            "README.txt",
            "Ensemble estimates summarise selected model outputs. Their uncertainty range is inter-model spread, not a calibrated probabilistic confidence interval unless independently validated.\n",
        )
    return buffer.getvalue()
