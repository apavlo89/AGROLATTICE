# AGROLATTICE 11.18 — Technical Basis: Reliability, Performance and Integration QA

## Scope

Release 11.18 is an integration/reliability release. It does not alter crop biology, climate derivations, pest models, causal estimators, crop-model equations, model-validation metrics or the Laurent-derived mechanistic maize implementation.

## Runtime profiling

`integration_reliability.py` records bounded in-session events containing page/tool name, elapsed milliseconds, completion/error status and a short diagnostic detail. The profile is intentionally session-local and is not written to scientific databases.

Top-level Streamlit pages are wrapped once at the navigation boundary. Advanced embedded tools are also profiled through the existing safe embedded-render wrapper. Summary statistics use median, empirical 95th percentile and maximum observed render time. These values are diagnostic observations under the current hardware/session workload rather than reproducible performance benchmarks.

## Cross-workspace integrity audit

The audit opens scientific SQLite stores read-only and checks local SQLite integrity/foreign keys plus selected cross-database identifiers that SQLite itself cannot enforce because they reside in separate files.

Checks include:

1. Trial `source_field_id` resolves to Field Operations.
2. Trial `source_field_geometry_hash` is compared with the authoritative current Field geometry hash. A mismatch is a warning, not an automatic geometry rewrite.
3. Persistent Twin field/trial links resolve.
4. Research Evidence field/trial/experimental-unit IDs resolve where context columns are populated.
5. Explicit reporting scope Field/Trial IDs resolve.

Cross-database legacy/external evidence may intentionally reference entities not stored in the current Field/Trial databases; therefore Research Evidence and reporting context mismatches are warnings rather than destructive automatic repairs.

## Workflow-chain readiness

The active chain is a persistence/readiness view, not a validity score. It counts linked records through Field → Season → Experiment → Experimental Unit → Observation/Outcome → Twin → Model/Validation → Prediction → Recommendation → Outcome → Report. Missing records can be correct for an early-stage study.

## Navigation reliability

Programmatic routes use `navigation_state.queue_view_request` and destination command centres consume those requests before their Streamlit widgets are instantiated. Release 11.18 extends this contract to the Fields & Operations section selector and replaces remaining Home shortcuts that still wrote obsolete release10 mirror keys.

## Scientific boundary

None of these checks establish:

- causal effects;
- external validity;
- model calibration;
- treatment efficacy;
- sensor measurement accuracy;
- agronomic equivalence of climate analogues;
- crop-model parameter validity.

Those questions remain the responsibility of the relevant Experiment, Models & Evidence, Twin and Reports workflows.
