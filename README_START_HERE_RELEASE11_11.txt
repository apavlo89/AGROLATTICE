AGROLATTICE 11.11 — CROP DECISION COMMAND CENTRE & AGRONOMIC PLANNING
=====================================================================

WHAT THIS RELEASE IS
--------------------
Release 11.11 reorganises Crop Decisions around the active mapped field, crop
season, trial and Persistent Twin. It is primarily an integration, workflow and
scientific-polish release: existing phenology, water, pest, nutrient, economics,
AquaCrop and DSSAT/APSIM capabilities are brought into one field-aware decision
workspace instead of behaving like independent development-era modules.

The release also adds a versioned research crop-profile registry and strengthens
the boundary between prediction, recommendation, actual operation and measured
outcome.

STARTING THE APPLICATION
------------------------
Windows / Anaconda:
  1. Extract the complete release directory.
  2. Keep the directory structure intact.
  3. Run RUN_APP.bat.

RUN_APP.bat checks the required modules, Streamlit version, database schema
versions and the new Crop Decision Command Centre / Crop Profile Registry before
starting Streamlit.

CROP DECISIONS IN 11.11
-----------------------
The workspace is organised as:
  Overview | Crop & planting | Water & irrigation | Nutrition |
  Pest & crop health | Yield & economics | Crop models |
  Recommendations & outcomes

When a mapped field is selected, AGROLATTICE carries its field/season/crop/Twin
context through the workspace. Manual/custom analysis remains available where
field data are missing or where the researcher intentionally studies another
location.

IMPORTANT NEW WORKFLOWS
-----------------------
- Lightweight Decision Pulse and Decision Inbox from persisted evidence.
- Field-aware daily weather / phenology that can reuse saved field/Twin weather
  rather than always downloading the same NASA data again.
- Historical daily sowing-date climate exposure explorer across candidate dates
  and years. This is climate-risk screening, not an official sowing calendar or
  cultivar-specific yield optimiser.
- Versioned Crop Profile Manager with author/region/evidence/version history.
- Water & irrigation view linking persisted root-zone evidence, recorded
  operations and the existing Irrigation Policy Studio.
- Nutrient data-readiness checks using structured samples, recorded nutrient
  operations, treatment-rate variation and observed outcomes.
- Operational pest-risk inference only from registered models explicitly marked
  Operationally eligible. Prototype model building remains an Advanced research
  workflow.
- Yield Evidence view that compares available model predictions with observed
  harvest outcomes without silently averaging incompatible models.
- Economics can start from recorded operation costs / irrigation totals while
  leaving all economic assumptions editable and explicit.
- AquaCrop and DSSAT/APSIM workflows now accept mapped-field evidence more
  naturally and preserve external-model execution status, including failures.
- Recommendation → Action → Outcome lifecycle is visible from Crop Decisions.
- A Crop Decision Timeline synthesises persisted operations, observations, model
  predictions, recommendations and measured outcomes without implying causality.

DATA AND SCIENTIFIC BOUNDARIES
------------------------------
- Existing field/Twin/environmental evidence is reused where possible. Retrieval
  remains explicit when evidence is missing or stale.
- NASA/gridded weather is not represented as a local station measurement.
- Pest risk is not pest confirmation and is not disease diagnosis.
- A model prediction is not a recommendation; a recommendation is not an actual
  operation; an operation is not proof of benefit.
- Climate-exposure sowing analysis does not replace local official calendars,
  extension guidance, field experiments or validated crop-response models.
- Mexico-specific calendar/agronomic guidance is displayed only for Mexico.
- Validated crop defaults and researcher profiles retain provenance; local
  assumptions are not silently promoted to global defaults.

DATABASES
---------
Release 11.11 does not migrate the four protected operational/research SQLite
schemas. It adds one independent additive registry:

  models_evidence/crop_profiles.sqlite

Crop Profile Registry schema: 1.0.0

The legacy custom_crop_profiles.json pathway is retained for compatibility and
may be imported into the new registry without deleting or overwriting the source.

PERFORMANCE
-----------
Opening Crop Decisions does not automatically call NASA/STAC, train pest models,
run optimisers, execute AquaCrop/DSSAT/APSIM or run root-zone simulations.
Overview uses lightweight saved summaries. Expensive retrieval/model work remains
an explicit researcher action.

TESTING LIMITATION
------------------
The build environment can compile and regression-test the source and databases,
but it does not contain Streamlit for a complete interactive browser session.
RUN_APP.bat performs the runtime dependency/module/schema preflight in the target
Windows/Anaconda installation.
