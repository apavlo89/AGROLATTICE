AGROLATTICE 11.5 — Decision Intelligence & Research Optimisation
================================================================

Release 11.5 builds on 11.4's multimodal/hybrid research foundation and adds a complete
researcher workflow for comparing agronomic decisions, recording recommendations and actual
outcomes, and evaluating whether recommendations appear to have helped under explicit
assumptions.

START
-----
1. Extract the complete Release 11.5 folder.
2. If your live research data are in an older AGROLATTICE folder, run
   MIGRATE_USER_DATA_FROM_EXISTING_APP.bat first. It uses backup-first SQLite migration,
   integrity checks, row-count verification and rollback protection.
3. Run RUN_APP.bat.
4. Open Crop Decisions -> Decision intelligence & optimisation.

WHAT TO TRY FIRST
-----------------
Irrigation policy studio
  - Pick a mapped field.
  - Retrieve NASA POWER weather directly or reuse Research Data Hub weather.
  - Pick crop, crop-water profile and soil profile.
  - Compare rainfed, RAW-trigger, deficit and fixed strategies; optionally include a recorded
    soil-moisture sensor strategy and simple economics.
  - Inspect Pareto alternatives before saving any research recommendation.

Nutrient optimisation
  - Reuse a G×E×M/trial table from the Research Data Hub or load a study table.
  - Select measured outcome, N/P/K rate columns, validation group and optional covariates.
  - Fit the response model, inspect held-out residuals, then explore the Pareto front.
  - Search defaults stay inside observed N/P/K support.

Recommendation trials
  - Save a recommendation separately from what was actually applied.
  - Later record whether it was followed, actual action, measured outcome and context.
  - A research recommendation becomes a Field Operations task only after explicit acknowledgement.

Causal audit
  - Analyse saved recommendation/outcome pairs directly, or another observational study table.
  - Select a binary treatment (numeric or categorical), outcome and pre-treatment covariates.
  - Prefer field/site/season/trial grouping when observations are clustered.
  - Inspect overlap, effective sample size and covariate balance before interpreting an effect.

STATE & DATA SAFETY
-------------------
Release 11.5 does not change the schemas of the three protected research databases:
  field_operations/field_operations.sqlite
  pollination_lab/maize_flowering_trials.sqlite
  agrolattice_twin/agrolattice_twin.sqlite

The separate additive Research Evidence database advances to schema 1.3.0 and stores decision
runs, state-assimilation evidence, causal audits and recommendation-status audit history. Existing research-registry records are
preserved through backup-first additive migration.

INTERPRETATION
--------------
Predicted != observed.
Recommendation != applied operation.
Pareto-efficient != agronomically validated.
Association-adjusted causal estimate != causal proof.
NASA POWER != local station measurement or future forecast.
A model/recommendation remains bounded by its recorded validation and applicability scope.

See CHANGELOG_RELEASE_11_5.txt, USER_GUIDE_RELEASE_11_5.txt and
SCIENTIFIC_BASIS_DECISION_INTELLIGENCE_11_5.md.
