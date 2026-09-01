"""Multi-algorithm agroclimatic clustering benchmark for AGROLATTICE AC3.

AC3 compares inductive clustering configurations on common repeated train/test
splits.  Scaling and model fitting use training locations only; silhouette is
calculated on held-out locations, and stability is the pairwise adjusted Rand
agreement among full-location predictions made by the resampled fits.

K-means, bisecting K-means, diagonal/tied Gaussian mixtures and BIRCH have
native prediction for unseen locations.  Agglomerative methods are evaluated
with a disclosed nearest-training-centroid induction rule because scikit-learn
agglomerative clustering is transductive.  HDBSCAN is reported as a separate
full-data density diagnostic and is not eligible to win the inductive audit.

The benchmark selects the simplest configuration within a repeated-resampling
non-inferiority margin of the best searched configuration.  This is an
operational model-selection rule, not a population-level equivalence test.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import (
    AgglomerativeClustering,
    Birch,
    BisectingKMeans,
    HDBSCAN,
    KMeans,
)
from sklearn.metrics import (
    adjusted_rand_score,
    pairwise_distances,
    silhouette_samples,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler


MODULE_VERSION = "3.0.0"


@dataclass(frozen=True)
class AlgorithmConfiguration:
    key: str
    family: str
    label: str
    k: int
    parameters: tuple[tuple[str, object], ...]
    complexity_rank: int
    induction_rule: str

    def parameter_dict(self) -> dict[str, object]:
        return dict(self.parameters)


@dataclass
class ConfigurationEvaluation:
    configuration: AlgorithmConfiguration
    mean_holdout_silhouette: float
    holdout_silhouette_se: float
    mean_stability_ari: float
    tiny_cluster_rate: float
    mean_quality: float
    repeat_quality: np.ndarray
    repeat_predictions: tuple[np.ndarray, ...]
    mean_confidence: float


@dataclass
class AC3BenchmarkResult:
    selected_configuration: AlgorithmConfiguration
    selected_search_evaluation: ConfigurationEvaluation
    selected_audit_evaluation: ConfigurationEvaluation
    screening_diagnostics: pd.DataFrame
    leaderboard: pd.DataFrame
    density_diagnostics: pd.DataFrame
    final_labels: np.ndarray
    final_confidence: np.ndarray
    final_silhouette_samples: np.ndarray
    family_labels: pd.DataFrame
    family_confidence: pd.DataFrame
    algorithm_agreement: pd.DataFrame
    consensus_matrix: np.ndarray
    method: str


def _make_splits(
    n_rows: int,
    repeats: int,
    test_fraction: float,
    random_seed: int,
) -> list[tuple[np.ndarray, np.ndarray]]:
    if n_rows < 10:
        raise ValueError("AC3 requires at least ten locations.")
    test_size = int(np.clip(round(float(test_fraction) * n_rows), 3, n_rows - 3))
    rng = np.random.default_rng(int(random_seed))
    splits = []
    for _ in range(int(repeats)):
        order = rng.permutation(n_rows)
        splits.append((np.sort(order[test_size:]), np.sort(order[:test_size])))
    return splits


def _standard_error(values: Sequence[float]) -> float:
    array = np.asarray(values, dtype=float)
    if array.size < 2:
        return 0.0
    return float(np.std(array, ddof=1) / math.sqrt(array.size))


def _harmonic_quality(silhouette: float, stability: float) -> float:
    separation = max(0.0, float(silhouette))
    reproducibility = max(0.0, float(stability))
    if separation + reproducibility <= 0:
        return 0.0
    return float(2.0 * separation * reproducibility / (separation + reproducibility))


def _pairwise_stability(predictions: Sequence[np.ndarray]) -> tuple[float, np.ndarray]:
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
    return float(np.mean(matrix[np.triu_indices(count, 1)])), per_repeat


def _centroids(data: np.ndarray, labels: np.ndarray, k: int) -> np.ndarray:
    return np.vstack([data[labels == cluster].mean(axis=0) for cluster in range(k)])


def _distance_confidence(
    data: np.ndarray,
    centres: np.ndarray,
    metric: str = "euclidean",
) -> np.ndarray:
    distances = pairwise_distances(data, centres, metric=metric)
    if distances.shape[1] < 2:
        return np.ones(len(data), dtype=float)
    ordered = np.sort(distances, axis=1)
    margin = 1.0 - ordered[:, 0] / np.maximum(ordered[:, 1], 1e-12)
    return np.clip(margin, 0.0, 1.0)


def _fit_predict_configuration(
    configuration: AlgorithmConfiguration,
    train: np.ndarray,
    all_rows: np.ndarray,
    test: np.ndarray,
    random_seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, object, float | None]:
    """Return all labels, test labels, all confidence, model and optional BIC."""
    k = int(configuration.k)
    params = configuration.parameter_dict()
    family = configuration.family
    bic: float | None = None

    if family == "K-means":
        model = KMeans(n_clusters=k, n_init=20, random_state=int(random_seed)).fit(train)
        all_labels = model.predict(all_rows)
        test_labels = model.predict(test)
        confidence = _distance_confidence(all_rows, model.cluster_centers_)
    elif family == "Bisecting K-means":
        model = BisectingKMeans(
            n_clusters=k,
            random_state=int(random_seed),
            bisecting_strategy=str(params.get("bisecting_strategy", "biggest_inertia")),
        ).fit(train)
        all_labels = model.predict(all_rows)
        test_labels = model.predict(test)
        confidence = _distance_confidence(all_rows, model.cluster_centers_)
    elif family == "Gaussian mixture":
        model = GaussianMixture(
            n_components=k,
            covariance_type=str(params.get("covariance_type", "diag")),
            reg_covar=1e-5,
            n_init=3,
            max_iter=300,
            random_state=int(random_seed),
        ).fit(train)
        all_labels = model.predict(all_rows)
        test_labels = model.predict(test)
        confidence = model.predict_proba(all_rows).max(axis=1)
        bic = float(model.bic(train))
    elif family == "BIRCH":
        model = Birch(
            n_clusters=k,
            threshold=float(params.get("threshold", 0.5)),
            branching_factor=50,
        ).fit(train)
        all_labels = model.predict(all_rows)
        test_labels = model.predict(test)
        train_labels = model.predict(train)
        populated = np.unique(train_labels)
        if populated.size == k:
            centres = _centroids(train, train_labels, k)
            confidence = _distance_confidence(all_rows, centres)
        else:
            confidence = np.zeros(len(all_rows), dtype=float)
    elif family in {"Ward hierarchy", "Average-cosine hierarchy"}:
        if family == "Ward hierarchy":
            model = AgglomerativeClustering(n_clusters=k, linkage="ward")
            metric = "euclidean"
        else:
            model = AgglomerativeClustering(n_clusters=k, linkage="average", metric="cosine")
            metric = "cosine"
        train_labels = model.fit_predict(train).astype(int)
        centres = _centroids(train, train_labels, k)
        all_distances = pairwise_distances(all_rows, centres, metric=metric)
        test_distances = pairwise_distances(test, centres, metric=metric)
        all_labels = np.argmin(all_distances, axis=1)
        test_labels = np.argmin(test_distances, axis=1)
        confidence = _distance_confidence(all_rows, centres, metric=metric)
    else:
        raise ValueError(f"Unsupported AC3 algorithm family: {family}")

    return (
        np.asarray(all_labels, dtype=int),
        np.asarray(test_labels, dtype=int),
        np.asarray(confidence, dtype=float),
        model,
        bic,
    )


def _configurations(
    algorithm_families: Sequence[str],
    minimum_k: int,
    maximum_k: int,
) -> list[AlgorithmConfiguration]:
    requested = set(algorithm_families)
    configurations: list[AlgorithmConfiguration] = []
    for k in range(int(minimum_k), int(maximum_k) + 1):
        if "K-means" in requested:
            configurations.append(AlgorithmConfiguration(
                f"kmeans-k{k}", "K-means", f"K-means (k={k})", k, (), 1,
                "Native nearest-centroid prediction",
            ))
        if "Bisecting K-means" in requested:
            configurations.append(AlgorithmConfiguration(
                f"bisect-k{k}", "Bisecting K-means", f"Bisecting K-means (k={k})", k,
                (("bisecting_strategy", "biggest_inertia"),), 2,
                "Native hierarchical-centroid prediction",
            ))
        if "Gaussian mixture" in requested:
            for covariance, rank in (("diag", 4), ("tied", 5)):
                configurations.append(AlgorithmConfiguration(
                    f"gmm-{covariance}-k{k}", "Gaussian mixture",
                    f"Gaussian mixture {covariance} (k={k})", k,
                    (("covariance_type", covariance),), rank,
                    "Native maximum-posterior prediction",
                ))
        if "BIRCH" in requested:
            for threshold in (0.5, 1.0):
                configurations.append(AlgorithmConfiguration(
                    f"birch-t{threshold}-k{k}", "BIRCH",
                    f"BIRCH threshold={threshold:g} (k={k})", k,
                    (("threshold", threshold),), 2,
                    "Native subcluster-centroid prediction",
                ))
        if "Ward hierarchy" in requested:
            configurations.append(AlgorithmConfiguration(
                f"ward-k{k}", "Ward hierarchy", f"Ward hierarchy (k={k})", k, (), 3,
                "Nearest training-cluster centroid surrogate",
            ))
        if "Average-cosine hierarchy" in requested:
            configurations.append(AlgorithmConfiguration(
                f"average-cosine-k{k}", "Average-cosine hierarchy",
                f"Average-cosine hierarchy (k={k})", k, (), 3,
                "Nearest training-cluster centroid under cosine distance",
            ))
    return configurations


def _evaluate_configuration(
    raw: np.ndarray,
    configuration: AlgorithmConfiguration,
    splits: Sequence[tuple[np.ndarray, np.ndarray]],
    *,
    random_seed: int,
    minimum_cluster_fraction: float,
    tiny_cluster_penalty: float,
) -> ConfigurationEvaluation:
    predictions: list[np.ndarray] = []
    silhouettes: list[float] = []
    tiny_flags: list[float] = []
    confidences: list[float] = []
    minimum_size = max(3, int(math.ceil(minimum_cluster_fraction * len(raw))))
    for repeat, (train_indices, test_indices) in enumerate(splits):
        scaler = StandardScaler().fit(raw[train_indices])
        train = scaler.transform(raw[train_indices])
        test = scaler.transform(raw[test_indices])
        all_rows = scaler.transform(raw)
        try:
            all_labels, test_labels, confidence, _, _ = _fit_predict_configuration(
                configuration,
                train,
                all_rows,
                test,
                int(random_seed) + repeat * 1009 + configuration.k * 37,
            )
            counts = np.bincount(all_labels, minlength=configuration.k)
            tiny = float(
                np.unique(all_labels).size != configuration.k
                or counts.size < configuration.k
                or int(counts.min()) < minimum_size
            )
            unique_test = np.unique(test_labels)
            if 2 <= unique_test.size < len(test_labels):
                # Keep the evaluation geometry common across families. The
                # algorithm may fit with cosine distance, but championship
                # silhouette is always Euclidean in the same scaled feature
                # space so metric choice cannot change the scoring scale.
                score = float(silhouette_score(test, test_labels, metric="euclidean"))
            else:
                score = -1.0
        except Exception:
            all_labels = np.zeros(len(raw), dtype=int)
            confidence = np.zeros(len(raw), dtype=float)
            tiny = 1.0
            score = -1.0
        predictions.append(all_labels)
        silhouettes.append(score)
        tiny_flags.append(tiny)
        confidences.append(float(np.mean(confidence)))

    stability, per_repeat_stability = _pairwise_stability(predictions)
    silhouettes_array = np.asarray(silhouettes, dtype=float)
    tiny_array = np.asarray(tiny_flags, dtype=float)
    repeat_quality = np.asarray([
        _harmonic_quality(silhouettes_array[index], per_repeat_stability[index])
        - tiny_cluster_penalty * tiny_array[index]
        for index in range(len(silhouettes_array))
    ])
    return ConfigurationEvaluation(
        configuration=configuration,
        mean_holdout_silhouette=float(np.mean(silhouettes_array)),
        holdout_silhouette_se=_standard_error(silhouettes_array),
        mean_stability_ari=float(stability),
        tiny_cluster_rate=float(np.mean(tiny_array)),
        mean_quality=float(np.mean(repeat_quality)),
        repeat_quality=repeat_quality,
        repeat_predictions=tuple(predictions),
        mean_confidence=float(np.mean(confidences)),
    )


def _noninferiority_upper_bound(
    best: ConfigurationEvaluation,
    candidate: ConfigurationEvaluation,
) -> float:
    difference = np.asarray(best.repeat_quality) - np.asarray(candidate.repeat_quality)
    if difference.size < 2:
        return float(np.mean(difference))
    return float(
        np.mean(difference)
        + 1.645 * np.std(difference, ddof=1) / math.sqrt(difference.size)
    )


def _evaluation_row(
    evaluation: ConfigurationEvaluation,
    phase: str,
) -> dict[str, object]:
    configuration = evaluation.configuration
    return {
        "Phase": phase,
        "Configuration key": configuration.key,
        "Algorithm": configuration.family,
        "Configuration": configuration.label,
        "Clusters": configuration.k,
        "Parameters": "; ".join(f"{key}={value}" for key, value in configuration.parameters),
        "Induction rule": configuration.induction_rule,
        "Complexity rank": configuration.complexity_rank,
        "Mean held-out silhouette": evaluation.mean_holdout_silhouette,
        "Held-out silhouette SE": evaluation.holdout_silhouette_se,
        "Mean resampling stability ARI": evaluation.mean_stability_ari,
        "Tiny-cluster resample rate": evaluation.tiny_cluster_rate,
        "Mean assignment confidence": evaluation.mean_confidence,
        "Mean resampling quality": evaluation.mean_quality,
    }


def _align_labels(reference: np.ndarray, candidate: np.ndarray) -> np.ndarray:
    reference_values = np.unique(reference)
    candidate_values = np.unique(candidate)
    contingency = np.zeros((len(reference_values), len(candidate_values)), dtype=int)
    for row, ref_value in enumerate(reference_values):
        for column, candidate_value in enumerate(candidate_values):
            contingency[row, column] = int(
                np.sum((reference == ref_value) & (candidate == candidate_value))
            )
    rows, columns = linear_sum_assignment(-contingency)
    mapping = {
        candidate_values[column]: reference_values[row]
        for row, column in zip(rows, columns)
    }
    next_label = int(reference_values.max()) + 1 if reference_values.size else 0
    aligned = []
    for value in candidate:
        if value not in mapping:
            mapping[value] = next_label
            next_label += 1
        aligned.append(mapping[value])
    return np.asarray(aligned, dtype=int)


def _fit_full(
    raw: np.ndarray,
    configuration: AlgorithmConfiguration,
    random_seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    scaler = StandardScaler().fit(raw)
    full = scaler.transform(raw)
    labels, _, confidence, _, _ = _fit_predict_configuration(
        configuration,
        full,
        full,
        full,
        int(random_seed),
    )
    return labels, confidence


def _density_diagnostic(
    standardised: np.ndarray,
    random_seed: int,
) -> tuple[pd.DataFrame, np.ndarray | None, np.ndarray | None]:
    del random_seed  # HDBSCAN is deterministic for these settings.
    rows: list[dict[str, object]] = []
    fitted_results: list[tuple[float, np.ndarray, np.ndarray]] = []
    for fraction in (0.02, 0.05, 0.10):
        minimum_cluster_size = max(5, int(math.ceil(fraction * len(standardised))))
        for minimum_samples in (5, 10, 20):
            model = HDBSCAN(
                min_cluster_size=minimum_cluster_size,
                min_samples=minimum_samples,
                cluster_selection_method="eom",
                allow_single_cluster=False,
                copy=True,
            ).fit(standardised)
            labels = np.asarray(model.labels_, dtype=int)
            assigned = labels >= 0
            clusters = int(np.unique(labels[assigned]).size) if assigned.any() else 0
            coverage = float(np.mean(assigned))
            if clusters >= 2 and int(assigned.sum()) > clusters:
                density_silhouette = float(silhouette_score(standardised[assigned], labels[assigned]))
            else:
                density_silhouette = -1.0
            quality = max(0.0, density_silhouette) * coverage - 0.10 * (1.0 - coverage)
            probabilities = np.asarray(
                getattr(model, "probabilities_", np.where(assigned, 1.0, 0.0)),
                dtype=float,
            )
            rows.append({
                "Algorithm": "HDBSCAN (exploratory; not championship eligible)",
                "Minimum cluster size": minimum_cluster_size,
                "Minimum samples": minimum_samples,
                "Clusters excluding noise": clusters,
                "Assigned coverage": coverage,
                "Noise fraction": 1.0 - coverage,
                "Assigned-point silhouette": density_silhouette,
                "Coverage-adjusted diagnostic": quality,
            })
            fitted_results.append((quality, labels, probabilities))
    diagnostics = pd.DataFrame(rows).sort_values(
        "Coverage-adjusted diagnostic", ascending=False
    )
    if not fitted_results:
        return diagnostics, None, None
    _, labels, probabilities = max(fitted_results, key=lambda item: item[0])
    return diagnostics, labels, probabilities


def benchmark_clustering_algorithms_ac3(
    raw_features: pd.DataFrame | np.ndarray,
    *,
    algorithm_families: Sequence[str],
    minimum_k: int = 2,
    maximum_k: int = 12,
    search_repeats: int = 5,
    audit_repeats: int = 10,
    test_fraction: float = 0.20,
    shortlist_per_family: int = 2,
    minimum_cluster_fraction: float = 0.02,
    tiny_cluster_penalty: float = 0.10,
    noninferiority_margin: float = 0.02,
    random_seed: int = 42,
    include_hdbscan_diagnostic: bool = True,
) -> AC3BenchmarkResult:
    """Screen, resample, independently audit and compare clustering algorithms."""
    raw = np.asarray(raw_features, dtype=float)
    if raw.ndim != 2 or raw.shape[0] < 10 or raw.shape[1] < 1:
        raise ValueError("AC3 requires at least ten rows and one feature.")
    if not np.isfinite(raw).all():
        raise ValueError("AC3 input contains non-finite values.")
    families = tuple(dict.fromkeys(str(family) for family in algorithm_families))
    if not families:
        raise ValueError("Select at least one clustering algorithm family.")
    maximum_k = int(np.clip(maximum_k, minimum_k, min(50, len(raw) - 1)))
    configurations = _configurations(families, minimum_k, maximum_k)
    if not configurations:
        raise ValueError("No eligible AC3 algorithm configurations were generated.")

    full_scaler = StandardScaler().fit(raw)
    full = full_scaler.transform(raw)
    minimum_size = max(3, int(math.ceil(minimum_cluster_fraction * len(raw))))
    screening_rows: list[dict[str, object]] = []
    for index, configuration in enumerate(configurations):
        try:
            labels, _, confidence, _, bic = _fit_predict_configuration(
                configuration,
                full,
                full,
                full,
                int(random_seed) + index,
            )
            counts = np.bincount(labels, minlength=configuration.k)
            populated = np.unique(labels).size
            score = (
                float(silhouette_score(full, labels, metric="euclidean"))
                if 2 <= populated < len(full) else -1.0
            )
            eligible = bool(
                populated == configuration.k
                and counts.size >= configuration.k
                and int(counts.min()) >= minimum_size
            )
            error = ""
        except Exception as exc:
            counts = np.array([], dtype=int)
            score = -1.0
            eligible = False
            confidence = np.zeros(len(full), dtype=float)
            bic = None
            error = str(exc)
        screening_rows.append({
            "Configuration key": configuration.key,
            "Algorithm": configuration.family,
            "Configuration": configuration.label,
            "Clusters": configuration.k,
            "Parameters": "; ".join(f"{key}={value}" for key, value in configuration.parameters),
            "Induction rule": configuration.induction_rule,
            "Complexity rank": configuration.complexity_rank,
            "Full-data silhouette (screening only)": score,
            "Smallest full-data cluster": int(counts.min()) if counts.size else 0,
            "Largest full-data cluster": int(counts.max()) if counts.size else 0,
            "Mean full-data confidence": float(np.mean(confidence)),
            "Gaussian-mixture BIC (within-family only)": bic,
            "Eligible full-data cluster sizes": eligible,
            "Screening error": error,
        })
    screening = pd.DataFrame(screening_rows)

    shortlisted_keys: list[str] = []
    for family in families:
        family_rows = screening.loc[
            screening["Algorithm"].eq(family)
            & screening["Eligible full-data cluster sizes"]
        ]
        if family_rows.empty:
            continue
        shortlisted_keys.extend(
            family_rows.sort_values(
                ["Full-data silhouette (screening only)", "Complexity rank", "Clusters"],
                ascending=[False, True, True],
            ).head(max(1, int(shortlist_per_family)))["Configuration key"].tolist()
        )
    lookup = {configuration.key: configuration for configuration in configurations}
    shortlisted = [lookup[key] for key in shortlisted_keys]
    if not shortlisted:
        raise ValueError("No AC3 configuration satisfied the minimum cluster-size safeguard.")

    search_splits = _make_splits(len(raw), search_repeats, test_fraction, random_seed)
    search_evaluations = [
        _evaluate_configuration(
            raw,
            configuration,
            search_splits,
            random_seed=int(random_seed),
            minimum_cluster_fraction=minimum_cluster_fraction,
            tiny_cluster_penalty=tiny_cluster_penalty,
        )
        for configuration in shortlisted
    ]
    best_search = max(search_evaluations, key=lambda evaluation: evaluation.mean_quality)
    noninferior = [
        evaluation for evaluation in search_evaluations
        if _noninferiority_upper_bound(best_search, evaluation) <= noninferiority_margin
    ] or [best_search]
    selected_search = sorted(
        noninferior,
        key=lambda evaluation: (
            evaluation.configuration.complexity_rank,
            evaluation.configuration.k,
            -evaluation.mean_quality,
            evaluation.configuration.key,
        ),
    )[0]

    # Audit the best searched configuration in every family on untouched splits.
    search_family_winners: dict[str, ConfigurationEvaluation] = {}
    for evaluation in search_evaluations:
        current = search_family_winners.get(evaluation.configuration.family)
        if current is None or evaluation.mean_quality > current.mean_quality:
            search_family_winners[evaluation.configuration.family] = evaluation
    audit_splits = _make_splits(
        len(raw), audit_repeats, test_fraction, int(random_seed) + 700_001
    )
    audit_evaluations: list[ConfigurationEvaluation] = []
    for family in families:
        if family not in search_family_winners:
            continue
        audit_evaluations.append(_evaluate_configuration(
            raw,
            search_family_winners[family].configuration,
            audit_splits,
            random_seed=int(random_seed) + 700_001,
            minimum_cluster_fraction=minimum_cluster_fraction,
            tiny_cluster_penalty=tiny_cluster_penalty,
        ))
    audit_by_key = {
        evaluation.configuration.key: evaluation for evaluation in audit_evaluations
    }
    selected_audit = audit_by_key.get(selected_search.configuration.key)
    if selected_audit is None:
        selected_audit = _evaluate_configuration(
            raw,
            selected_search.configuration,
            audit_splits,
            random_seed=int(random_seed) + 700_001,
            minimum_cluster_fraction=minimum_cluster_fraction,
            tiny_cluster_penalty=tiny_cluster_penalty,
        )

    leaderboard_rows = []
    for family in families:
        search = search_family_winners.get(family)
        if search is None:
            continue
        audit = audit_by_key.get(search.configuration.key)
        row = _evaluation_row(search, "Search")
        if audit is not None:
            row.update({
                "Independent audit held-out silhouette": audit.mean_holdout_silhouette,
                "Independent audit silhouette SE": audit.holdout_silhouette_se,
                "Independent audit stability ARI": audit.mean_stability_ari,
                "Independent audit tiny-cluster rate": audit.tiny_cluster_rate,
                "Independent audit assignment confidence": audit.mean_confidence,
                "Independent audit quality": audit.mean_quality,
            })
        row["Selected AC3 champion"] = bool(
            search.configuration.key == selected_search.configuration.key
        )
        row["Search non-inferiority upper bound vs best"] = _noninferiority_upper_bound(
            best_search, search
        )
        leaderboard_rows.append(row)
    leaderboard = pd.DataFrame(leaderboard_rows).sort_values(
        ["Selected AC3 champion", "Independent audit quality"],
        ascending=[False, False],
    )

    final_labels_by_family: dict[str, np.ndarray] = {}
    final_confidence_by_family: dict[str, np.ndarray] = {}
    for family, search in search_family_winners.items():
        labels, confidence = _fit_full(raw, search.configuration, random_seed)
        final_labels_by_family[family] = labels
        final_confidence_by_family[family] = confidence
    selected_labels = final_labels_by_family[selected_search.configuration.family]
    selected_confidence = final_confidence_by_family[selected_search.configuration.family]

    aligned_labels: dict[str, np.ndarray] = {}
    for family, labels in final_labels_by_family.items():
        aligned_labels[family] = (
            labels if family == selected_search.configuration.family
            else _align_labels(selected_labels, labels)
        )
    family_labels = pd.DataFrame(aligned_labels)
    family_confidence = pd.DataFrame(final_confidence_by_family)
    agreement = pd.DataFrame(index=list(final_labels_by_family), columns=list(final_labels_by_family), dtype=float)
    for left in agreement.index:
        for right in agreement.columns:
            agreement.loc[left, right] = adjusted_rand_score(
                final_labels_by_family[left], final_labels_by_family[right]
            )

    consensus = np.zeros((len(raw), len(raw)), dtype=np.float32)
    for prediction in selected_audit.repeat_predictions:
        consensus += (prediction[:, None] == prediction[None, :]).astype(np.float32)
    consensus /= float(len(selected_audit.repeat_predictions))

    full_standardised = StandardScaler().fit_transform(raw)
    selected_silhouette_samples = silhouette_samples(
        full_standardised,
        selected_labels,
        metric="euclidean",
    )
    if include_hdbscan_diagnostic:
        density_diagnostics, density_labels, density_confidence = _density_diagnostic(
            full_standardised, random_seed
        )
        if density_labels is not None:
            family_labels["HDBSCAN exploratory"] = density_labels
            family_confidence["HDBSCAN exploratory"] = density_confidence
    else:
        density_diagnostics = pd.DataFrame()

    screening["Repeated-holdout shortlisted"] = screening["Configuration key"].isin(shortlisted_keys)
    screening["Selected AC3 champion"] = screening["Configuration key"].eq(
        selected_search.configuration.key
    )

    return AC3BenchmarkResult(
        selected_configuration=selected_search.configuration,
        selected_search_evaluation=selected_search,
        selected_audit_evaluation=selected_audit,
        screening_diagnostics=screening,
        leaderboard=leaderboard,
        density_diagnostics=density_diagnostics,
        final_labels=selected_labels,
        final_confidence=selected_confidence,
        final_silhouette_samples=selected_silhouette_samples,
        family_labels=family_labels,
        family_confidence=family_confidence,
        algorithm_agreement=agreement,
        consensus_matrix=consensus,
        method=(
            "AC3 multi-algorithm benchmark: full-data screening; common repeated 80/20 "
            "train/test search; held-out silhouette; pairwise resampling ARI; 2% minimum "
            "cluster safeguard; simplest configuration within a one-sided 0.02 operational "
            "non-inferiority margin; independent family-wise audit; HDBSCAN density diagnostic "
            "reported separately because it is transductive"
        ),
    )
