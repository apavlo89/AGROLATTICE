# AGROLATTICE 11.19 publication-reference workflow

Reference identifier: `AGROLATTICE-11.19-PRR-2026-08-12`

## Purpose

AGROLATTICE 11.19 is a frozen paper/reference release. It intentionally avoids introducing a new scientific model or changing protected scientific databases. Its purpose is to give the manuscript, reviewers and future users one stable software object that can be cited and reproduced while AGROLATTICE 12.x develops separately.

## Reproduce the bundled demonstration

1. Extract the 11.19 archive into a new folder.
2. Run `RUN_PUBLICATION_REFERENCE_DEMO.bat`, or run `python publication_reference.py --output publication_reference` from an environment containing NumPy, pandas and matplotlib.
3. The script regenerates the fixed synthetic demonstration project from seed `1119`.
4. It regenerates four publication-reference figures in PNG (300 dpi) and SVG.
5. It regenerates the example tables/results summary.
6. It verifies the SHA-256 of every fixed demo data file against `DEMO_DATA_MANIFEST.json`.

The demo contains 24 synthetic experimental units in 4 blocks and all 19 canonical AGROLATTICE environmental variable columns. No demo value should be reported as empirical agricultural evidence.

## Freeze the exact target runtime used for manuscript analyses

Run `FREEZE_PUBLICATION_ENV.bat` inside the Windows/Anaconda environment actually used to run AGROLATTICE for the paper. This writes the exact Python runtime and `pip freeze --all` output into `publication_reference/environment/`.

The bundled `requirements_publication_reference_lock.txt` is the release reference lock. The generated target-environment snapshot is stronger evidence for the final manuscript because it records the exact environment actually used.

## Manuscript-use rule

The paper should identify the software as **AGROLATTICE 11.19 Publication Reference Release**, give the internal reference identifier, and cite the DOI of the exact archived 11.19 ZIP once a DOI has been minted externally.

Do not rewrite the manuscript to describe later 12.x functionality unless a new manuscript version explicitly changes its reference release.

## Archive/DOI step

This package cannot mint its own DOI. Deposit the exact final 11.19 ZIP and checksum in a DOI-granting software/data archive. After deposition, record the returned DOI in the manuscript and update the public archive metadata/CITATION file in the repository copy without changing the scientific contents of the archived ZIP.
