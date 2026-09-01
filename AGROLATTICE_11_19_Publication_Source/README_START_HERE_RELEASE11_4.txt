AGROLATTICE 11.4 — Multimodal Crop Intelligence & Hybrid Twin Learning
======================================================================

This release builds on 11.3's Research Model & Evidence foundation and makes the
new research tools use AGROLATTICE data directly instead of assuming every workflow
starts with a CSV upload.

START
-----
1. Extract the complete release folder.
2. If your real data live in another AGROLATTICE folder, run
   MIGRATE_USER_DATA_FROM_EXISTING_APP.bat first. It performs backup-first SQLite
   copying and verification.
3. Run RUN_APP.bat.
4. Use Data & Settings -> Research Data Hub to retrieve/reuse data for research tools.

WHAT TO TRY FIRST
-----------------
Research Data Hub
  - Retrieve daily/weekly/monthly NASA POWER weather for a mapped field.
  - Load the selected country's installed 19-variable climate history.
  - Reuse Field Operations observations, operations, sensors and nutrients.
  - Reuse current Daily Weather, Sentinel-2 and root-zone results.
  - Register acquisition provenance when a retrieved table becomes a research dataset.

Crop Decisions -> Phenology service
  - Select a mapped field and retrieve daily NASA weather directly.
  - Run generic GDD or the unchanged Mechanistic Maize Twin.

Crop Decisions -> Pest early warning
  - Train with measured pest/absence labels plus environmental covariates.
  - Forecast from newly retrieved NASA weather for a mapped field.
  - AGROLATTICE will not invent RH1/RH2 or pest labels to make incompatible data fit.

Models & Evidence
  - Adaptive multimodal fusion: separate weather/soil/EO/management/sensor/phenology
    feature groups and inspect per-row reliability weights.
  - Hybrid Twin learning: learn residual corrections around mechanistic/base predictions
    and require held-out RMSE improvement.
  - Weakly supervised spatial yield: explore aggregate-supervised fine estimates with
    explicit spatial-validation warnings.

Experiments -> G×E×M dataset builder
  - Build plot/experimental-unit modelling data directly from the Maize Synchrony Lab.
  - Keep Trial, Field, Season, Block and Replicate identifiers for grouped validation.

PROTECTED DATA
--------------
Release 11.4 does not alter the schemas of the three protected research databases:
  field_operations/field_operations.sqlite
  pollination_lab/maize_flowering_trials.sqlite
  agrolattice_twin/agrolattice_twin.sqlite

The separate additive models_evidence/research_evidence.sqlite database advances to
schema 1.2.0 by adding retrieval/acquisition provenance.

SCIENTIFIC INTERPRETATION
-------------------------
Retrieved != measured locally. Predicted != observed. Recommendation != applied action.
Weakly supervised fine output != measured subfield yield. Predictive importance !=
causality. A model remains a Prototype until its recorded validation scope supports a
higher status.

See CHANGELOG_RELEASE_11_4.txt and SCIENTIFIC_BASIS_MULTIMODAL_HYBRID_11_4.md.
