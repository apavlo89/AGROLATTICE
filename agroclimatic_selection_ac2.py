"""Nested, stability-aware variable-subset selection for agroclimatic clustering.

AC2 treats each canonical environmental variable as a block of calendar-month
features.  It uses a deterministic forward search followed by backward removal.
Every proposed subset is screened across the feasible k range on the complete
data; the strongest feasible k candidates are then evaluated on the same
repeated train/test splits.  Scaling and K-means fitting occur on the training
locations only, and silhouette is calculated on held-out locations.

The selected subset is the simplest searched subset that satisfies a
pre-specified repeated-holdout non-inferiority rule relative to the best
searched subset.  An independent set of splits is reserved for the final audit.

This remains exploratory unsupervised model selection.  It does not establish
agronomic causality, an official agroecological classification, or external
transferability.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler


MODULE_VERSION = "2.0.0"

MONTH_NAMES = (
    "JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE",
    "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER",
)


@dataclass
class SubsetEvaluation:
    variables: tuple[str, ...]
    selected_k: int
    mean_holdout_silhouette: float
    holdout_silhouette_se: float
    mean_stability_ari: float
    tiny_cluster_rate: float
    mean_resampling_quality: float
    complexity_penalty: float
    penalised_score: float
    repeat_quality: np.ndarray
    k_diagnostics: pd.DataFrame


@dataclass
class AC2SelectionResult:
    selected_variables: tuple[str, ...]
    selected_k: int
    search_evaluation: SubsetEvaluation
    audit_diagnostics: dict[str, float | int]
    search_history: pd.DataFrame
    subset_diagnostics: pd.DataFrame
    k_diagnostics: pd.DataFrame
    final_model: KMeans
    labels: np.ndarray
    standardised: pd.DataFrame
    selected_feature_columns: tuple[str, ...]
    method: str


def variable_from_feature(feature: str) -> str:
    """Return the canonical variable name from a VARIABLE_MONTH feature."""
    text = str(feature)
    upper = text.upper()
    for month in MONTH_NAMES:
        suffix = f"_{month}"
        if upper.endswith(suffix):
            return text[: -len(suffix)]
    return text.rsplit("_", 1)[0] if "_" in text else text


def feature_columns_for_variables(
    feature_columns: Sequence[str],
    variables: Iterable[str],
) -> list[str]:
    selected = {str(variable) for variable in variables}
    return [
        str(feature) for feature in feature_columns
        if variable_from_feature(str(feature)) in selected
    ]


def _make_splits(
    n_rows: int,
    repeats: int,
    test_fraction: float,
    random_seed: int,
) -> list[tuple[np.ndarray, np.ndarray]]:
    if n_rows < 10:
        raise ValueError("AC2 requires at least ten locations for repeated holdout evaluation.")
    test_size = int(np.clip(round(float(test_fraction) * n_rows), 3, n_rows - 3))
    rng = np.random.default_rng(int(random_seed))
    splits: list[tuple[np.ndarray, np.ndarray]] = []
    for _ in range(int(repeats)):
        order = rng.permutation(n_rows)
        test = np.sort(order[:test_size])
        train = np.sort(order[test_size:])
        splits.append((train, test))
    return splits


def _harmonic_quality(silhouette: float, stability: float) -> float:
    separation = max(0.0, float(silhouette))
    reproducibility = max(0.0, float(stability))
    if separation + reproducibility <= 0:
        return 0.0
    return float(2.0 * separation * reproducibility / (separation + reproducibility))


def _standard_error(values: Sequence[float]) -> float:
    array = np.asarray(values, dtype=float)
    if array.size < 2:
        return 0.0
    return float(np.std(array, ddof=1) / math.sqrt(array.size))


def _pairwise_repeat_stability(predictions: Sequence[np.ndarray]) -> tuple[float, np.ndarray]:
    count = len(predictions)
    if count < 2:
        return 0.0, np.zeros(count, dtype=float)
    matrix = np.eye(count, dtype=float)
    for left in range(count):
        for right in range(left + 1, count):
            score = float(adjusted_rand_score(predictions[left], predictions[right]))
            matrix[left, right] = score
            matrix[right, left] = score
    per_repeat = (matrix.sum(axis=1) - 1.0) / float(count - 1)
    pair_values = matrix[np.triu_indices(count, k=1)]
    return float(np.mean(pair_values)), per_repeat.astype(float)


def _evaluate_k_on_splits(
    raw: np.ndarray,
    k: int,
    splits: Sequence[tuple[np.ndarray, np.ndarray]],
    *,
    random_seed: int,
    n_init: int,
    minimum_cluster_fraction: float,
    tiny_cluster_penalty: float,
) -> dict[str, object]:
    holdout_silhouettes: list[float] = []
    predictions: list[np.ndarray] = []
    tiny_flags: list[float] = []
    n_rows = raw.shape[0]
    minimum_full_size = max(3, int(math.ceil(minimum_cluster_fraction * n_rows)))

    for repeat, (train_indices, test_indices) in enumerate(splits):
        scaler = StandardScaler().fit(raw[train_indices])
        train = scaler.transform(raw[train_indices])
        test = scaler.transform(raw[test_indices])
        all_rows = scaler.transform(raw)
        model = KMeans(
            n_clusters=int(k),
            n_init=int(n_init),
            random_state=int(random_seed) + 1009 * int(k) + repeat,
        ).fit(train)
        test_labels = model.predict(test)
        all_labels = model.predict(all_rows)
        unique_test = np.unique(test_labels)
        if 2 <= unique_test.size < len(test_labels):
            holdout = float(silhouette_score(test, test_labels))
        else:
            holdout = -1.0
        counts = np.bincount(all_labels, minlength=int(k))
        tiny = float(counts.size < int(k) or int(counts.min()) < minimum_full_size)
        holdout_silhouettes.append(holdout)
        predictions.append(all_labels.astype(int))
        tiny_flags.append(tiny)

    stability, per_repeat_stability = _pairwise_repeat_stability(predictions)
    silhouettes = np.asarray(holdout_silhouettes, dtype=float)
    tiny_array = np.asarray(tiny_flags, dtype=float)
    repeat_quality = np.asarray([
        _harmonic_quality(silhouettes[index], per_repeat_stability[index])
        - float(tiny_cluster_penalty) * tiny_array[index]
        for index in range(len(silhouettes))
    ])
    return {
        "holdout_silhouettes": silhouettes,
        "mean_holdout_silhouette": float(np.mean(silhouettes)),
        "holdout_silhouette_se": _standard_error(silhouettes),
        "mean_stability_ari": stability,
        "tiny_cluster_rate": float(np.mean(tiny_array)),
        "repeat_quality": repeat_quality,
        "mean_resampling_quality": float(np.mean(repeat_quality)),
    }


def evaluate_subset(
    raw_features: pd.DataFrame,
    feature_columns: Sequence[str],
    variables: Sequence[str],
    splits: Sequence[tuple[np.ndarray, np.ndarray]],
    *,
    minimum_k: int = 2,
    maximum_k: int = 20,
    shortlist_k: int = 3,
    random_seed: int = 42,
    screening_n_init: int = 3,
    holdout_n_init: int = 5,
    minimum_cluster_fraction: float = 0.02,
    complexity_penalty_per_extra_variable: float = 0.005,
    tiny_cluster_penalty: float = 0.10,
) -> SubsetEvaluation:
    """Evaluate one variable subset across k, then resample the best candidates."""
    subset = tuple(sorted({str(variable) for variable in variables}))
    columns = feature_columns_for_variables(feature_columns, subset)
    if not columns:
        raise ValueError("The proposed variable subset has no usable feature columns.")
    raw = raw_features.loc[:, columns].to_numpy(dtype=float)
    if not np.isfinite(raw).all():
        raise ValueError("The proposed variable subset contains non-finite values.")

    full_scaler = StandardScaler().fit(raw)
    full = full_scaler.transform(raw)
    unique_profiles = int(np.unique(np.round(full, decimals=10), axis=0).shape[0])
    upper = min(int(maximum_k), full.shape[0] - 1, unique_profiles)
    if upper < int(minimum_k):
        raise ValueError("Too few distinct profiles are available for clustering.")
    minimum_full_size = max(3, int(math.ceil(minimum_cluster_fraction * full.shape[0])))

    screening_rows: list[dict[str, float | int | bool]] = []
    for k in range(int(minimum_k), upper + 1):
        model = KMeans(
            n_clusters=k,
            n_init=int(screening_n_init),
            random_state=int(random_seed) + k,
        ).fit(full)
        labels = model.labels_.astype(int)
        counts = np.bincount(labels, minlength=k)
        populated = np.unique(labels).size
        if 2 <= populated < full.shape[0]:
            apparent_silhouette = float(silhouette_score(full, labels))
        else:
            apparent_silhouette = -1.0
        eligible = bool(populated == k and int(counts.min()) >= minimum_full_size)
        screening_rows.append({
            "Clusters": int(k),
            "Full-data silhouette (screening only)": apparent_silhouette,
            "K-means inertia": float(model.inertia_),
            "Smallest full-data cluster": int(counts.min()) if counts.size else 0,
            "Largest full-data cluster": int(counts.max()) if counts.size else 0,
            "Eligible full-data cluster sizes": eligible,
        })

    diagnostics = pd.DataFrame(screening_rows)
    eligible_rows = diagnostics.loc[diagnostics["Eligible full-data cluster sizes"]].copy()
    if eligible_rows.empty:
        eligible_rows = diagnostics.copy()
    shortlisted = (
        eligible_rows.sort_values(
            ["Full-data silhouette (screening only)", "Clusters"],
            ascending=[False, True],
        )
        .head(max(1, int(shortlist_k)))
        ["Clusters"]
        .astype(int)
        .tolist()
    )

    resampled_by_k: dict[int, dict[str, object]] = {}
    for k in shortlisted:
        resampled_by_k[k] = _evaluate_k_on_splits(
            raw,
            k,
            splits,
            random_seed=int(random_seed),
            n_init=int(holdout_n_init),
            minimum_cluster_fraction=float(minimum_cluster_fraction),
            tiny_cluster_penalty=float(tiny_cluster_penalty),
        )

    for column in (
        "Mean held-out silhouette", "Held-out silhouette SE",
        "Mean resampling stability (ARI)", "Tiny-cluster resample rate",
        "Mean resampling quality",
    ):
        diagnostics[column] = np.nan
    diagnostics["Repeated-holdout shortlisted"] = diagnostics["Clusters"].isin(shortlisted)
    for k, result in resampled_by_k.items():
        mask = diagnostics["Clusters"].eq(k)
        diagnostics.loc[mask, "Mean held-out silhouette"] = result["mean_holdout_silhouette"]
        diagnostics.loc[mask, "Held-out silhouette SE"] = result["holdout_silhouette_se"]
        diagnostics.loc[mask, "Mean resampling stability (ARI)"] = result["mean_stability_ari"]
        diagnostics.loc[mask, "Tiny-cluster resample rate"] = result["tiny_cluster_rate"]
        diagnostics.loc[mask, "Mean resampling quality"] = result["mean_resampling_quality"]

    ranked_k = sorted(
        shortlisted,
        key=lambda k: (
            -float(resampled_by_k[k]["mean_resampling_quality"]),
            -float(resampled_by_k[k]["mean_holdout_silhouette"]),
            int(k),
        ),
    )
    selected_k = int(ranked_k[0])
    selected = resampled_by_k[selected_k]
    complexity_penalty = float(complexity_penalty_per_extra_variable) * max(0, len(subset) - 1)
    penalised_score = float(selected["mean_resampling_quality"]) - complexity_penalty
    diagnostics["Selected k for subset"] = diagnostics["Clusters"].eq(selected_k)
    diagnostics["Variable subset"] = ", ".join(subset)
    diagnostics["Variables in subset"] = len(subset)

    return SubsetEvaluation(
        variables=subset,
        selected_k=selected_k,
        mean_holdout_silhouette=float(selected["mean_holdout_silhouette"]),
        holdout_silhouette_se=float(selected["holdout_silhouette_se"]),
        mean_stability_ari=float(selected["mean_stability_ari"]),
        tiny_cluster_rate=float(selected["tiny_cluster_rate"]),
        mean_resampling_quality=float(selected["mean_resampling_quality"]),
        complexity_penalty=complexity_penalty,
        penalised_score=penalised_score,
        repeat_quality=np.asarray(selected["repeat_quality"], dtype=float),
        k_diagnostics=diagnostics,
    )


def _noninferiority_upper_bound(
    best: SubsetEvaluation,
    candidate: SubsetEvaluation,
) -> float:
    differences = np.asarray(best.repeat_quality) - np.asarray(candidate.repeat_quality)
    if differences.size < 2:
        return float(np.mean(differences))
    # One-sided normal approximation. This is an operational resampling rule,
    # not a claim of population-level statistical equivalence.
    return float(np.mean(differences) + 1.645 * np.std(differences, ddof=1) / math.sqrt(differences.size))


def _evaluation_row(
    evaluation: SubsetEvaluation,
    *,
    stage: str,
    step: int,
) -> dict[str, object]:
    return {
        "Stage": stage,
        "Step": int(step),
        "Variables": ", ".join(evaluation.variables),
        "Variable count": len(evaluation.variables),
        "Selected k": int(evaluation.selected_k),
        "Mean held-out silhouette": evaluation.mean_holdout_silhouette,
        "Held-out silhouette SE": evaluation.holdout_silhouette_se,
        "Mean resampling stability (ARI)": evaluation.mean_stability_ari,
        "Tiny-cluster resample rate": evaluation.tiny_cluster_rate,
        "Mean resampling quality": evaluation.mean_resampling_quality,
        "Complexity penalty": evaluation.complexity_penalty,
        "Penalised selection score": evaluation.penalised_score,
    }


def select_variables_and_clusters_ac2(
    raw_features: pd.DataFrame,
    feature_columns: Sequence[str],
    candidate_variables: Sequence[str],
    *,
    minimum_variables: int = 2,
    maximum_variables: int = 8,
    minimum_k: int = 2,
    maximum_k: int = 20,
    search_repeats: int = 5,
    audit_repeats: int = 10,
    test_fraction: float = 0.20,
    random_seed: int = 42,
    noninferiority_margin: float = 0.02,
    minimum_forward_gain: float = 0.002,
    forward_patience: int = 0,
    minimum_cluster_fraction: float = 0.02,
    complexity_penalty_per_extra_variable: float = 0.005,
    tiny_cluster_penalty: float = 0.10,
) -> AC2SelectionResult:
    """Run AC2 forward selection, backward removal and independent audit."""
    candidates = tuple(sorted({str(variable) for variable in candidate_variables}))
    if len(candidates) < int(minimum_variables):
        raise ValueError(f"At least {minimum_variables} candidate variables are required.")
    maximum_variables = int(np.clip(maximum_variables, minimum_variables, len(candidates)))
    search_splits = _make_splits(
        len(raw_features), int(search_repeats), float(test_fraction), int(random_seed)
    )
    audit_splits = _make_splits(
        len(raw_features), int(audit_repeats), float(test_fraction), int(random_seed) + 500_003
    )

    cache: dict[tuple[str, ...], SubsetEvaluation] = {}
    history_stage: dict[tuple[str, ...], tuple[str, int]] = {}

    def evaluate(subset: Sequence[str], stage: str, step: int) -> SubsetEvaluation:
        key = tuple(sorted(set(subset)))
        if key not in cache:
            cache[key] = evaluate_subset(
                raw_features,
                feature_columns,
                key,
                search_splits,
                minimum_k=int(minimum_k),
                maximum_k=int(maximum_k),
                random_seed=int(random_seed),
                minimum_cluster_fraction=float(minimum_cluster_fraction),
                complexity_penalty_per_extra_variable=float(complexity_penalty_per_extra_variable),
                tiny_cluster_penalty=float(tiny_cluster_penalty),
            )
            history_stage[key] = (stage, int(step))
        return cache[key]

    # Forward phase: choose the strongest one-block seed, then add the block
    # giving the largest penalised repeated-holdout score at each step.
    seed_evaluations = [evaluate((variable,), "Forward seed", 1) for variable in candidates]
    current = max(seed_evaluations, key=lambda item: (item.penalised_score, -len(item.variables)))
    best_forward = current
    non_improving_steps = 0
    step = 1
    while len(current.variables) < maximum_variables:
        step += 1
        remaining = [variable for variable in candidates if variable not in current.variables]
        additions = [
            evaluate((*current.variables, variable), "Forward addition", step)
            for variable in remaining
        ]
        if not additions:
            break
        proposal = max(additions, key=lambda item: (item.penalised_score, -len(item.variables)))
        gain = proposal.penalised_score - current.penalised_score
        forced_to_minimum = len(current.variables) < int(minimum_variables)
        if forced_to_minimum or gain >= float(minimum_forward_gain):
            current = proposal
            non_improving_steps = 0
        elif non_improving_steps < int(forward_patience):
            current = proposal
            non_improving_steps += 1
        else:
            break
        if current.penalised_score > best_forward.penalised_score:
            best_forward = current

    # Backward phase starts from the best forward point and removes blocks when
    # the simpler proposal improves the score or meets the non-inferiority rule.
    current = best_forward
    backward_step = 0
    while len(current.variables) > int(minimum_variables):
        backward_step += 1
        removals = [
            evaluate(
                tuple(variable for variable in current.variables if variable != removed),
                "Backward removal",
                backward_step,
            )
            for removed in current.variables
        ]
        proposal = max(removals, key=lambda item: (item.penalised_score, -len(item.variables)))
        upper = _noninferiority_upper_bound(current, proposal)
        if proposal.penalised_score >= current.penalised_score or upper <= float(noninferiority_margin):
            current = proposal
        else:
            break

    eligible = [item for item in cache.values() if len(item.variables) >= int(minimum_variables)]
    best = max(eligible, key=lambda item: item.mean_resampling_quality)
    near_equivalent = [
        item for item in eligible
        if _noninferiority_upper_bound(best, item) <= float(noninferiority_margin)
    ]
    if not near_equivalent:
        near_equivalent = [best]
    selected = sorted(
        near_equivalent,
        key=lambda item: (
            len(item.variables),
            -item.penalised_score,
            -item.mean_holdout_silhouette,
            item.variables,
        ),
    )[0]

    selected_columns = feature_columns_for_variables(feature_columns, selected.variables)
    selected_raw = raw_features.loc[:, selected_columns].to_numpy(dtype=float)
    audit = _evaluate_k_on_splits(
        selected_raw,
        selected.selected_k,
        audit_splits,
        random_seed=int(random_seed) + 500_003,
        n_init=20,
        minimum_cluster_fraction=float(minimum_cluster_fraction),
        tiny_cluster_penalty=float(tiny_cluster_penalty),
    )
    scaler = StandardScaler().fit(selected_raw)
    standardised_array = scaler.transform(selected_raw)
    final_model = KMeans(
        n_clusters=int(selected.selected_k),
        n_init=50,
        random_state=int(random_seed),
    ).fit(standardised_array)
    final_labels = final_model.labels_.astype(int)
    full_silhouette = float(silhouette_score(standardised_array, final_labels))
    counts = np.bincount(final_labels, minlength=int(selected.selected_k))

    subset_rows = []
    for key, evaluation in cache.items():
        stage, stage_step = history_stage[key]
        row = _evaluation_row(evaluation, stage=stage, step=stage_step)
        row["Non-inferiority upper bound vs best"] = _noninferiority_upper_bound(best, evaluation)
        row["Within AC2 non-inferiority margin"] = bool(
            row["Non-inferiority upper bound vs best"] <= float(noninferiority_margin)
        )
        row["Selected subset"] = bool(evaluation.variables == selected.variables)
        subset_rows.append(row)
    subset_diagnostics = pd.DataFrame(subset_rows).sort_values(
        ["Variable count", "Penalised selection score"], ascending=[True, False]
    )

    audit_diagnostics: dict[str, float | int] = {
        "Independent audit repeats": int(audit_repeats),
        "Independent mean held-out silhouette": float(audit["mean_holdout_silhouette"]),
        "Independent held-out silhouette SE": float(audit["holdout_silhouette_se"]),
        "Independent mean stability ARI": float(audit["mean_stability_ari"]),
        "Independent tiny-cluster rate": float(audit["tiny_cluster_rate"]),
        "Independent mean quality": float(audit["mean_resampling_quality"]),
        "Full-data silhouette": full_silhouette,
        "Smallest full-data cluster": int(counts.min()),
        "Largest full-data cluster": int(counts.max()),
    }

    search_history = subset_diagnostics[
        [
            "Stage", "Step", "Variables", "Variable count", "Selected k",
            "Mean held-out silhouette", "Mean resampling stability (ARI)",
            "Tiny-cluster resample rate", "Penalised selection score",
            "Within AC2 non-inferiority margin", "Selected subset",
        ]
    ].copy()
    k_diagnostics = selected.k_diagnostics.copy()
    k_diagnostics["Selected subset"] = ", ".join(selected.variables)

    return AC2SelectionResult(
        selected_variables=selected.variables,
        selected_k=int(selected.selected_k),
        search_evaluation=selected,
        audit_diagnostics=audit_diagnostics,
        search_history=search_history,
        subset_diagnostics=subset_diagnostics,
        k_diagnostics=k_diagnostics,
        final_model=final_model,
        labels=final_labels,
        standardised=pd.DataFrame(standardised_array, columns=selected_columns),
        selected_feature_columns=tuple(selected_columns),
        method=(
            "AC2 forward selection plus backward removal; all feasible k screened for each subset, "
            "top three k evaluated by repeated 80/20 holdout; held-out silhouette and pairwise "
            "resampling ARI combined; variable-count and tiny-cluster penalties; simplest subset "
            "within a one-sided 0.02 resampling non-inferiority margin; independent final audit"
        ),
    )
