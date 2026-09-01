AGROLATTICE 11.13 — EXPERIMENT COMMAND CENTRE & TRIAL INTELLIGENCE
==================================================================

Baseline
--------
Built from AGROLATTICE 11.12 Navigation Reliability & Interaction Fix.

What this release changes
-------------------------
11.13 polishes the Experiments workspace into a persistent, spatial research command centre. It keeps the existing Maize Synchrony/Mechanistic Maize capabilities but places design, spatial assignment, protocol-driven field collection, outcomes, analysis, evidence and export in one trial context.

Main researcher workflow
------------------------
1. Choose the active mapped experiment once.
2. Review Experiment Pulse and priority evidence gaps.
3. Version the experimental protocol and factor definitions.
4. Confirm design family, replication, treatment matrix and randomisation provenance.
5. Inspect the authoritative field/experimental-unit layout.
6. Collect protocol-linked observations and field tasks.
7. Review flowering/synchrony and parent physiology.
8. Record harvest/reproductive outcomes.
9. Build an analysis-ready G×E×M table and perform design-aware summaries.
10. Export the complete randomisation/evidence package.

Performance
-----------
The modern Experiment Command Centre uses true lazy top-level navigation. Only the selected experiment view is rendered. The old advanced workbenches remain available behind explicit load toggles because their maps, tables and modelling interfaces are intentionally heavier.

Climate clustering
------------------
Agroclimatic K-means exploration and the Climate Space K-means display now support k=2 through k=20 where the sample size and number of distinct climate profiles permit. Silhouette, inertia and cluster-size diagnostics are shown. High-k results remain exploratory and are not labelled official agroecological zones.

Database migration
------------------
The Maize Pollination Lab database is upgraded additively to schema 3.0.0. A pre-11.13 backup is included under pollination_lab/backups/. Existing scientific tables and rows are preserved. New additive tables store protocol snapshots/versions, factor definitions, design versions, measurement requirements and the trial audit trail.

Safety
------
Do not overwrite your working research databases casually. Use safe_data_migration.py with explicit confirmation when carrying data from an older installation.

Start
-----
Run RUN_APP.bat from the AGROLATTICE folder in the normal ML_AGRICULTURE Anaconda environment.
