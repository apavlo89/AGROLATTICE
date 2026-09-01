# AGROLATTICE 11.19 — Technical Basis: Publication Reference Release

## Scope

Release 11.19 is a freeze/archival release built from 11.18. It does not introduce a new agronomic, statistical, ML, causal, EO, irrigation, nutrient, crop-model or mechanistic-maize method. Its technical purpose is to make the platform paper reproducible against one immutable software reference.

## Reference identity

The release defines:

`AGROLATTICE-11.19-PRR-2026-08-12`

This is an internal persistent identifier stored in source and metadata. It is intentionally distinct from an external DOI, which can only be minted after depositing the finished archive in an external repository.

## Deterministic synthetic demonstration

`publication_reference.py` creates a fixed synthetic demonstration from seed 1119. It generates:

- 24 experimental units (4 blocks × 6 treatments);
- explicit male/female parent labels, sowing offsets, densities and irrigation-treatment labels;
- field-like synthetic geometry;
- 145 daily synthetic environmental records containing all 19 canonical AGROLATTICE environmental variables;
- flowering/synchrony observations and a synthetic predicted-vs-observed table;
- deterministic summary metrics.

The demo is a software test/illustration. It is not a biological simulator and its apparent model performance must not be interpreted as empirical validation.

## Publication figures

Four figures are regenerated from the fixed demo/reference metadata and stored as 300-dpi PNG and SVG. They are deterministic publication diagrams, not screenshots of a running Streamlit browser session.

## Environment reproducibility

The release contains:

- the normal application requirement files;
- an exact publication-reference dependency lock;
- a packaging-environment manifest;
- `FREEZE_PUBLICATION_ENV.bat`, which records Python/runtime plus `pip freeze --all` from the actual target Windows/Anaconda environment used for paper analyses.

The target-environment snapshot should be archived with final manuscript materials because the Linux packaging environment lacks several UI packages and is not the authoritative interactive runtime.

## Source/archive integrity

The release verifier checks protected database/model hashes against 11.18, validates the deterministic demo manifest, checks citation/archive metadata, validates all six SQLite databases, confirms k≤20 clustering remains present, and verifies that the scientific-method manifest reports no scientific-method changes.

`SOURCE_FILE_MANIFEST_11_19.sha256` records file-level hashes for the frozen release tree, excluding itself and transient Python cache files.

## Publication-safe source archive

`build_public_archive.py` constructs a supplementary source-only archive that excludes user SQLite files, installed country datasets, caches, attachments and run outputs while retaining source, documentation, citation metadata, deterministic synthetic demo assets and schema-only SQL exports. This is intended for public deposition; the full working release remains the researcher's migration-compatible application package.

## Data safety

No schema migration is introduced. Safe migration remains source-authoritative only after explicit confirmation, snapshots all available scientific/reporting databases first, and verifies SQLite integrity/row counts.

Packaged reproducible network caches are cleaned from the publication archive to reduce volatile third-party content and make the reference archive cleaner. This does not delete user scientific databases, installed datasets, reports or model artifacts.

## Scientific boundary

The publication freeze establishes software identity and reproducibility. It does not establish:

- agronomic correctness;
- external validity;
- causal efficacy of recommendations;
- model calibration;
- sensor accuracy;
- transferability to unseen genotype/site/season;
- agronomic equivalence of climate analogues.

Those claims must be supported by the actual empirical evidence/validation stored in AGROLATTICE and frozen into the relevant report.
