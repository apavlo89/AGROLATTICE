AGROLATTICE 11.18 — END-TO-END RELIABILITY, PERFORMANCE & INTEGRATION QA
=======================================================================

This release is built on AGROLATTICE 11.17 and focuses on making the complete research workflow more reliable before the planned AGROLATTICE 12.0 modelling milestone.

WHAT IS NEW
-----------
• Data & Settings now contains an Integration & reliability workspace.
• AGROLATTICE can audit persistent hand-offs across Fields → Experiments → Persistent Twin → Models/Evidence → Reports without modifying scientific records.
• Cross-workspace checks detect broken Field/Trial/Twin references, stale Trial field-boundary snapshots, unresolved Research Evidence context IDs and explicit report scopes that no longer resolve.
• An Active workflow chain shows which persisted stages currently exist for the selected Field/Trial, from mapped field and experiment through Twin evidence, prediction, recommendation, measured outcome and traceable report.
• Top-level workspace renders and embedded advanced tools are profiled in-session. Data & Settings → Performance & storage shows median, P95, maximum render time and errors by page/tool.
• Page profiling is bounded to the current browser session and can be cleared without touching scientific data.
• Home and cross-workspace shortcuts now use the safe two-stage navigation contracts introduced in 11.12 instead of older direct widget-state mutations.
• Fields & Operations now supports queued programmatic routing to the correct command-centre section.
• The 11.18 verifier exercises a complete synthetic persisted workflow using temporary database copies: Field → Season → Experiment → Experimental Unit → observations/outcome → Twin → Model/Validation → Prediction → Recommendation → measured outcome → Report.

STARTING THE APP
----------------
1. Keep your existing AGROLATTICE user data in place or use the bundled migration tool when moving from an older release folder.
2. Run RUN_APP.bat.
3. The 11.18 preflight checks current modules and the unchanged scientific database schemas before Streamlit starts.
4. Use Data & Settings → Integration & reliability if an upgrade, restore, geometry edit or cross-tab hand-off appears inconsistent.
5. Use Data & Settings → Performance & storage after navigating through several workspaces to inspect session render timings.

RELIABILITY WORKFLOW
--------------------
A typical complete evidence chain is:

Mapped Field → Structured Season → Experiment → Experimental Units → Field/Trial observations → Persistent Twin → weather/root-zone/state → registered model + validation → prediction → recommendation → actual action/outcome → frozen report evidence.

AGROLATTICE 11.18 reports which of these stages are currently linked. Missing stages are not automatically errors: a newly designed trial, for example, should not yet have harvest outcomes.

WHAT THE INTEGRATION AUDIT DOES NOT PROVE
-----------------------------------------
Passing the integration audit does not prove:
• agronomic correctness;
• sensor accuracy;
• model calibration or external validity;
• causal effects;
• treatment efficacy;
• crop-model parameter correctness;
• that climate analogues are agronomically equivalent.

It verifies persistence, database health and cross-workspace references only.

PERFORMANCE INTERPRETATION
--------------------------
The session profiler measures observed render time in the current Streamlit session. It is intended to locate slow workspaces and accidental rerun costs. It is not a hardware-independent benchmark. Explicit NASA/Sentinel retrieval, model training, crop-model execution or other heavy actions can legitimately dominate an individual render.

DATA SAFETY
-----------
11.18 introduces no scientific database schema migration. The following remain on their 11.17 schemas:
• Field Operations 8.0.0
• Maize Experiments 3.0.0
• Persistent Twin 3.0.0
• Research Evidence 2.0.0
• Crop Profiles 1.0.0
• Reporting 1.0.0

The Mechanistic Maize Twin equations and publication-derived assumptions are unchanged.

PCA / K-MEANS
-------------
The k=2–20 climate clustering/PCA exploration introduced in 11.13 remains available. High-k exploration is diagnostic and does not create official agroecological zones.
