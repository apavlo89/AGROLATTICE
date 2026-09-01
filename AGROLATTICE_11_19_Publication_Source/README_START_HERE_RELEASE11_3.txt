AGROLATTICE 11.3 — START HERE
============================
Research Foundation & Predictive Evidence Update

This package is a complete upgrade from AGROLATTICE 11.2. It preserves the
11.2 spatial-integrity fixes and adds the research/model foundation needed to
integrate the agricultural-informatics literature without turning AGROLATTICE
into a collection of disconnected AI demos.

START
-----
1. Keep a copy of your currently working AGROLATTICE folder.
2. If upgrading an existing working installation, run:
      MIGRATE_USER_DATA_FROM_EXISTING_APP.bat
   and select the root of your previous AGROLATTICE folder.
   The migration is backup-first and source-authoritative for available user DBs.
3. Activate the ML_AGRICULTURE conda environment if you normally use it.
4. Run INSTALL_DEPENDENCIES.bat if the 11.3 research packages have not been installed.
5. Optional: run INSTALL_OPTIONAL_RESEARCH_MODELS.bat only if you want TabPFN.
6. Start with RUN_APP.bat.

NEW RESEARCH WORKFLOWS
----------------------
Models & Evidence
  • Research registry — datasets, model cards, predictions, recommendations,
    benchmark runs and evidence provenance.
  • Research model lab — leakage-safe agricultural model comparison and model fitting.
  • Multimodal fusion — validation-weighted modality-aware prediction baseline.
  • External benchmarks — CropNet, YieldSAT and WorldCereal metadata/adapters.

Crop Decisions
  • Phenology service — generic thermal time plus unchanged mechanistic maize phenology.
  • Pest early warning — environmental pest-risk models with interpretable features.

AgroLattice Twin
  • Research evidence — registered model predictions/recommendations linked to the
    currently selected field/trial where identifiers are available.

DATA SAFETY
-----------
Release 11.3 adds one new database only:
  models_evidence/research_evidence.sqlite

The Field Operations, Maize Pollination Lab and AgroLattice Twin DB schemas were
not changed. The migration utility backs up active destination DBs, creates an
independent snapshot of source DBs, verifies SQLite integrity/row counts, then
activates source-authoritative copies. A Release 11.2 source without the new
Research Evidence DB remains valid.

SCIENTIFIC SAFETY
-----------------
• Use grouped, site/season/year/region or forward validation for deployment claims.
• Random CV is a diagnostic, not proof of transfer to new environments.
• Preprocessing/resampling must stay inside training folds.
• New models are Prototype until evidence supports promotion.
• Applicability flags describe similarity to the training support, not certainty.
• A pest forecast is not a laboratory/field disease diagnosis.
• Inter-modality disagreement is not a calibrated uncertainty interval.
• Recorded management remains distinct from recommended management.

METHOD STATUS
-------------
11.3 implements the common foundation and selected high-value adaptations.
It does NOT claim that all reviewed papers have been reproduced. See:
  RESEARCH_METHODS_MANIFEST_11_3.json
  SCIENTIFIC_BASIS_RESEARCH_FOUNDATION_11_3.md

VERIFY
------
For a development/build check run:
  python verify_release11_3.py

The packaged BUILD_VERIFICATION_11_3.txt records the checks performed before
this release archive was generated.
