"""Verification for AGROLATTICE 11.19 adaptive-clustering build AC2."""
from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from agroclimatic_selection_ac2 import MODULE_VERSION, select_variables_and_clusters_ac2


ROOT = Path(__file__).resolve().parent
EXPECTED_DATABASE_HASHES = {
    "field_operations/field_operations.sqlite": "fbf5ab2de711830a50bed5acfae84a86ec58efc45448d18ea7b88e04b4ff69b5",
    "pollination_lab/maize_flowering_trials.sqlite": "87511c0a9921e731f8bd8b3111118e452b9aa6d6ee32905fee3b7af73a258819",
    "agrolattice_twin/agrolattice_twin.sqlite": "ea5746651e6fb6c3de409ec8cf64d6e68409b40c0a7853f33982b2fb3f006bb4",
    "models_evidence/research_evidence.sqlite": "7e80e599285753c026ff47e86127ad3df42b4cfdb7ff662fb6cd1011b1052a25",
    "models_evidence/crop_profiles.sqlite": "84da237e7a8f20b3c84da7c9c423d0aa5a2dab130608c1eebfc2b06885c9e3a6",
    "reports/reporting.sqlite": "f1e3cd3dfce0a91e65db13f282d940245d5f42716551c276a6cef5af3d5e81d4",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_synthetic_selection() -> None:
    rng = np.random.default_rng(1119)
    n = 240
    known = np.repeat(np.arange(3), n // 3)
    thermal = np.array([-4.0, 0.0, 4.0])[known]
    water = np.array([0.0, 4.0, 0.0])[known]
    months = ("JANUARY", "MARCH", "MAY", "JULY", "SEPTEMBER", "NOVEMBER")
    data: dict[str, np.ndarray] = {}
    for month_index, month in enumerate(months):
        data[f"TEMPERATURE_{month}"] = thermal + 0.2 * month_index + rng.normal(0, 0.7, n)
        data[f"PRECIPITATION_AVG_{month}"] = water - 0.1 * month_index + rng.normal(0, 0.7, n)
        data[f"TEMPERATURE_MAX_{month}"] = thermal + rng.normal(0, 0.9, n)
        data[f"SOLAR_RADIATION_{month}"] = rng.normal(0, 2.0, n)
        data[f"WIND_SPEED_{month}"] = rng.normal(0, 2.0, n)
    raw = pd.DataFrame(data)
    candidates = (
        "TEMPERATURE", "PRECIPITATION_AVG", "TEMPERATURE_MAX",
        "SOLAR_RADIATION", "WIND_SPEED",
    )
    first = select_variables_and_clusters_ac2(
        raw, list(raw.columns), candidates,
        minimum_variables=2, maximum_variables=4,
        minimum_k=2, maximum_k=5,
        search_repeats=3, audit_repeats=4,
        random_seed=1119,
    )
    second = select_variables_and_clusters_ac2(
        raw, list(raw.columns), candidates,
        minimum_variables=2, maximum_variables=4,
        minimum_k=2, maximum_k=5,
        search_repeats=3, audit_repeats=4,
        random_seed=1119,
    )
    assert MODULE_VERSION == "2.0.0"
    assert first.selected_variables == ("PRECIPITATION_AVG", "TEMPERATURE")
    assert first.selected_k == 3
    assert first.selected_variables == second.selected_variables
    assert first.selected_k == second.selected_k
    assert np.array_equal(first.labels, second.labels)
    assert float(first.audit_diagnostics["Independent mean held-out silhouette"]) > 0.70
    assert float(first.audit_diagnostics["Independent mean stability ARI"]) > 0.95


def verify_integration() -> None:
    app = (ROOT / "agrolattice.py").read_text(encoding="utf-8")
    launcher = (ROOT / "RUN_APP.bat").read_text(encoding="utf-8", errors="replace")
    for fragment in (
        'APP_VERSION = "20.19-release11.19-publication-reference-adaptive-clustering-ac2"',
        "AC2 automatic subset and cluster search",
        "run_agroclimatic_clustering_ac2",
        "select_variables_and_clusters_ac2",
        "PCA cumulative-variance threshold",
        "Independent mean held-out silhouette",
        "Download Complete Clustering Reproducibility Package",
        "Manual variables / original 11.19 clustering",
    ):
        assert fragment in app, fragment
    assert "agroclimatic_selection_ac2.py" in launcher
    for name in (
        "ADAPTIVE_CLUSTERING_BUILD_ID_AC2.txt",
        "README_START_HERE_RELEASE11_19_AC2.txt",
        "CHANGELOG_RELEASE_11_19_AC2.txt",
        "RESEARCH_METHODS_MANIFEST_11_19_AC2.json",
        "RELEASE_MANIFEST_11_19_AC2.json",
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


def main() -> None:
    verify_synthetic_selection()
    verify_integration()
    verify_database_preservation()
    print("AGROLATTICE 11.19 adaptive-clustering build AC2 verification passed")


if __name__ == "__main__":
    main()
