"""Verification for AGROLATTICE 11.19 adaptive-clustering build AC3."""
from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from agroclimatic_selection_ac3 import MODULE_VERSION, benchmark_clustering_algorithms_ac3


ROOT = Path(__file__).resolve().parent
EXPECTED_DATABASE_HASHES = {
    "field_operations/field_operations.sqlite": "fbf5ab2de711830a50bed5acfae84a86ec58efc45448d18ea7b88e04b4ff69b5",
    "pollination_lab/maize_flowering_trials.sqlite": "87511c0a9921e731f8bd8b3111118e452b9aa6d6ee32905fee3b7af73a258819",
    "agrolattice_twin/agrolattice_twin.sqlite": "ea5746651e6fb6c3de409ec8cf64d6e68409b40c0a7853f33982b2fb3f006bb4",
    "models_evidence/research_evidence.sqlite": "7e80e599285753c026ff47e86127ad3df42b4cfdb7ff662fb6cd1011b1052a25",
    "models_evidence/crop_profiles.sqlite": "84da237e7a8f20b3c84da7c9c423d0aa5a2dab130608c1eebfc2b06885c9e3a6",
    "reports/reporting.sqlite": "f1e3cd3dfce0a91e65db13f282d940245d5f42716551c276a6cef5af3d5e81d4",
}
EXPECTED_MEXICO_DATASET_HASH = "653690a345d298056b780edc0588a56d879ba52f76a8a21834a83476de1f8687"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _synthetic_result():
    rng = np.random.default_rng(1119)
    data = np.vstack([
        rng.normal((-5.0, -5.0, 0.0), 0.45, (90, 3)),
        rng.normal((0.0, 5.0, 0.0), 0.45, (90, 3)),
        rng.normal((5.0, -3.0, 1.0), 0.45, (90, 3)),
    ])
    return benchmark_clustering_algorithms_ac3(
        pd.DataFrame(data),
        algorithm_families=[
            "K-means", "Bisecting K-means", "Gaussian mixture", "BIRCH",
            "Ward hierarchy", "Average-cosine hierarchy",
        ],
        maximum_k=6,
        search_repeats=3,
        audit_repeats=5,
        include_hdbscan_diagnostic=True,
        random_seed=1119,
    )


def verify_synthetic_benchmark() -> None:
    first = _synthetic_result()
    second = _synthetic_result()
    assert MODULE_VERSION == "3.0.0"
    assert first.selected_configuration.family == "K-means"
    assert first.selected_configuration.k == 3
    assert first.selected_configuration == second.selected_configuration
    assert np.array_equal(first.final_labels, second.final_labels)
    assert first.selected_audit_evaluation.mean_holdout_silhouette > 0.60
    assert first.selected_audit_evaluation.mean_stability_ari > 0.99
    assert set(first.algorithm_agreement.index) == {
        "K-means", "Bisecting K-means", "Gaussian mixture", "BIRCH",
        "Ward hierarchy", "Average-cosine hierarchy",
    }
    assert not first.density_diagnostics.empty
    assert first.consensus_matrix.shape == (270, 270)


def verify_integration() -> None:
    app = (ROOT / "agrolattice.py").read_text(encoding="utf-8")
    ac3_engine = (ROOT / "agroclimatic_selection_ac3.py").read_text(encoding="utf-8")
    launcher = (ROOT / "RUN_APP.bat").read_text(encoding="utf-8", errors="replace")
    for fragment in (
        'APP_VERSION = "20.19-release11.19-publication-reference-adaptive-clustering-ac3"',
        "run_agroclimatic_clustering_ac3",
        "benchmark_clustering_algorithms_ac3",
        "Climate-zone discovery",
        "Robust multi-method analysis (recommended)",
        "Focused K-means analysis",
        "Automatically choose a compact variable set",
        "Climate-space map",
        "Method comparison",
        "Assignment confidence",
        "How methods differ",
        "How location assignments change across family winners",
        "Download analysis and reproducibility package",
        "The active Mexico climate table is incomplete",
        "Location coverage audit",
        '"Eligible cluster sizes": eligible_cluster_sizes',
        "max_value=50",
        'polar={"radialaxis": {"visible": True, "showgrid": True}}',
    ):
        assert fragment in app, fragment
    assert "Oaxaca retained" not in app
    assert "· Oaxaca:" not in app
    assert 'polar={"radialaxis": {"visible": True, "zeroline": True}}' not in app
    assert "min(50, len(raw) - 1)" in ac3_engine
    for fragment in (
        "agroclimatic_selection_ac3.py",
        "verify_release11_19_ac3.py",
        "adaptive-clustering build AC3 preflight passed",
    ):
        assert fragment in launcher, fragment
    for name in (
        "ADAPTIVE_CLUSTERING_BUILD_ID_AC3.txt",
        "README_START_HERE_RELEASE11_19_AC3.txt",
        "CHANGELOG_RELEASE_11_19_AC3.txt",
        "RESEARCH_METHODS_MANIFEST_11_19_AC3.json",
        "RELEASE_MANIFEST_11_19_AC3.json",
        "VERIFICATION_REPORT_11_19_AC3.txt",
        "FILE_MANIFEST_11_19_AC3.sha256",
        "MEXICO_DATASET_COVERAGE_AC3.txt",
    ):
        assert (ROOT / name).exists(), name
    publication_id = (ROOT / "PUBLICATION_REFERENCE_ID.txt").read_text(encoding="utf-8")
    assert "AGROLATTICE-11.19-PRR-2026-08-12" in publication_id


def verify_database_preservation() -> None:
    for relative, expected_hash in EXPECTED_DATABASE_HASHES.items():
        path = ROOT / relative
        assert _sha256(path) == expected_hash, relative
        with sqlite3.connect(path) as connection:
            assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok", relative
            assert connection.execute("PRAGMA foreign_key_check").fetchall() == [], relative


def verify_frozen_mexico_dataset() -> None:
    """Prevent an interrupted country update from entering the frozen release."""
    path = ROOT / "Datasets/countries/mexico/agroclimate_longformat.csv"
    assert _sha256(path) == EXPECTED_MEXICO_DATASET_HASH
    location_keys: set[tuple[str, str]] = set()
    for chunk in pd.read_csv(path, usecols=["CITY", "STATE"], chunksize=500_000):
        location_keys.update(
            chunk.drop_duplicates().itertuples(index=False, name=None)
        )
    assert len(location_keys) == 1_012
    assert sum(state == "Oaxaca" for _, state in location_keys) == 80
    assert len({state for _, state in location_keys}) == 32


def main() -> None:
    verify_synthetic_benchmark()
    verify_integration()
    verify_database_preservation()
    verify_frozen_mexico_dataset()
    print("AGROLATTICE 11.19 adaptive-clustering build AC3 verification passed")


if __name__ == "__main__":
    main()
