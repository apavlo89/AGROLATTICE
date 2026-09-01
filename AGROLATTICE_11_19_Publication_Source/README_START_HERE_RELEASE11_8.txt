AGROLATTICE 11.8 — Field Command Centre & Operations Polish
============================================================

Release 11.8 is built directly on AGROLATTICE 11.7 and preserves the 11.6
performance optimisations, 11.7 Research Command Centre, the Release 11.5
decision-intelligence stack, the Release 11.4 research-data/multimodal stack,
and the Release 11.0 Mechanistic Maize Twin.

The focus of 11.8 is Fields & Operations. The workspace is reorganised around
one persistent active mapped field instead of a collection of disconnected
forms.

Highlights
----------
* Field Command Centre with one active field across Overview, Map, Work &
  scouting, Operations, Sensors & samples, Crop health, Precision, History and
  Administration.
* Lightweight Field Pulse, data freshness, recent activity and Portfolio
  Attention without automatically fetching NASA/Sentinel data or running models.
* One authoritative spatial workspace combining field geometry, experiment
  overlays, experimental units, scouting points, sensors, nutrient samples,
  sampling designs and saved prescriptions.
* Geometry QA and GeoJSON export while keeping boundary editing inside the safer
  Administration section.
* Structured field seasons for cross-season research context.
* Editable tasks plus genuine recurrence generation on completion.
* Reusable observation protocols and quantitative scouting measurements linked
  to trial / experimental unit / tagged plant identifiers where available.
* Map-click scouting coordinates with field-boundary validation.
* Planned-vs-actual structured operation records, recommendation linkage and
  optional custom treated geometry.
* Sensor dashboard, lifecycle states and calibration history without deleting
  historical readings.
* Structured soil/tissue/water sample metadata: depth, growth stage, tissue,
  laboratory, analytical method, units and detection limits.
* Persistent field-health evidence reading from the Research Evidence Registry
  and Persistent Twin instead of depending only on Streamlit session state.
* Alert templates, metric-safe selectors, consecutive-trigger persistence and
  cooldown control; incident acknowledgement, false-positive marking, snoozing,
  resolution notes and scouting-task creation.
* Portfolio Attention replaces the old leaderboard and uses one batch SQL
  summary rather than repeated per-field count queries.
* Precision sampling now supports systematic, random and stratified-random
  designs and can persist sample points.
* Management-zone exploration can use already stored nutrient samples, multiple
  variables, optional PCA, K-means and silhouette diagnostics. K-means outputs
  are explicitly labelled exploratory point clusters rather than validated
  continuous agronomic zones.
* Field history now includes structured seasons, samples, alerts and sampling
  designs in addition to tasks, scouting and operations.

Installation / start
--------------------
1. Extract the complete Release 11.8 folder.
2. If your real working databases live in an older AGROLATTICE folder, run
   MIGRATE_USER_DATA_FROM_EXISTING_APP.bat first.
3. Run RUN_APP.bat.

Database migration
------------------
Field Operations changes from the Release 11.7 core schema to the additive
Release 11.8 schema. The legacy 11.7 tables are NOT rewritten. Release 11.8
creates extension tables for structured seasons, research observation details,
operation spatial/provenance details, sensor lifecycle/calibration, structured
sample metadata, alert persistence/incidents and persistent sampling points.

The packaged 11.7 Field Operations database was backed up before migration at:
  field_operations/backups/pre_11_8_field_operations.sqlite

The build verification confirmed that every row in every legacy Field Operations
table is identical before and after migration. The Pollination Lab, Persistent
Twin and Research Evidence databases are byte-for-byte unchanged from 11.7.

Scientific boundaries
---------------------
* Recorded, retrieved, derived, modelled, forecast and recommended information
  remain distinct concepts.
* Alert thresholds are screening/decision-support rules, not disease diagnoses.
* K-means point clusters are not automatically valid continuous management zones.
* A partial-field operation polygon records spatial support; it does not prove
  treatment efficacy.
* Sensor broad-range QC does not replace calibration or installation QA.
* No automatic irrigation hardware control is added.
* The Mechanistic Maize Twin model implementation is unchanged.

See CHANGELOG_RELEASE_11_8.txt, USER_GUIDE_RELEASE_11_8.txt,
TECHNICAL_BASIS_FIELDS_11_8.md and BUILD_VERIFICATION_11_8.txt.
