AGROLATTICE 11.17 — HELP, ONBOARDING & RESEARCHER GUIDANCE
==========================================================

This release is built on AGROLATTICE 11.16 and focuses on making the now-large platform easier to learn and safer to use consistently.

WHAT IS NEW
-----------
• Help is now a real command centre rather than a collection of static guides.
• Start Here shows context-aware onboarding progress from persisted AGROLATTICE records.
• Guided workflows walk through mapped field/season setup, experiments, maize synchrony, Persistent Twins, model validation, decision-to-outcome and reporting.
• Every primary research workspace contains a lightweight "What do I need here?" panel showing prerequisites, why they matter and where to create/retrieve missing evidence.
• Scientific evidence labels are standardised across the guidance layer: Observed, Recorded, Retrieved, Derived, Mechanistic, ML prediction, Forecast, Scenario, Recommendation, Actual operation, Outcome and Causal estimate.
• Searchable terminology and troubleshooting are available directly in Help.
• The existing contextual ? help remains available and has been updated for 11.17.

STARTING THE APP
----------------
1. Keep your existing AGROLATTICE user data in place or use the bundled migration tool when moving from an older release folder.
2. Run RUN_APP.bat from this release.
3. The preflight checks the current 11.17 modules and the unchanged protected database schemas before Streamlit starts.
4. Open Help → Start Here if you are creating a new research workflow.

RECOMMENDED FIRST WORKFLOW
--------------------------
1. Data & Settings: verify the country climate workspace.
2. Fields & Operations: map the research centre/field and create the season.
3. Experiments: create and map a trial if the work is experimental.
4. Climate & Earth Observation: attach/retrieve field weather and EO when needed.
5. AgroLattice Twin: create/link the persistent field/season Twin.
6. Crop Decisions: compare management options while keeping recommendations separate from recorded operations.
7. Models & Evidence: train/validate models with grouped/site/season-aware designs.
8. Reports: freeze evidence and build the report/manuscript from persistent records.

IMPORTANT SCIENTIFIC BOUNDARIES
-------------------------------
• Gridded NASA weather is retrieved environmental evidence, not a local weather-station measurement.
• Sentinel indices are EO-derived observations at their actual spatial support/resolution.
• Mechanistic means explicit biological/physical assumptions, not automatically correct.
• ML prediction and feature importance are predictive evidence, not causal proof.
• Climate similarity does not prove agronomic equivalence.
• A recommendation is not an actual operation until the applied action is recorded.
• Observed outcomes do not establish causality merely because they occurred after a recommendation/operation.
• Laurent et al. maize physiology priors are not measurements of local lines.

DATA SAFETY
-----------
11.17 makes no scientific database schema change. The Field Operations, Experiment, Persistent Twin, Research Evidence, Crop Profile and Reporting databases remain on their existing schemas. The Mechanistic Maize Twin equations are unchanged.

PERFORMANCE
-----------
Help and readiness panels use small metadata queries only. They do not automatically fetch NASA/Sentinel data, run models, execute crop-model backends or load/reprocess the large country climate table.
