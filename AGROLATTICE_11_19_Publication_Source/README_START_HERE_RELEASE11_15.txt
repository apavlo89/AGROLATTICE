AGROLATTICE 11.15 — Research Reporting & Publication Command Centre
====================================================================

WHAT THIS RELEASE DOES
----------------------
Release 11.15 replaces Reports' old Release-3/session-state-first publication experience with a persistent research-reporting system that reads Field Operations, Experiments, Persistent Twin and Research Evidence directly.

Main Reports navigation:
  Overview | Report Builder | Publications | Tables & Figures | Evidence & Claims | Reproducibility | Report Library

Highlights:
- Persistent report registry and immutable report versions.
- Field/Trial/Twin/Model-aware reporting context.
- Purpose-built report types (experiment, synchrony, Twin season, field season, climate/EO, crop decision, model validation, recommendation/outcome, G×E×M, manuscript, supplement).
- Report readiness and evidence-gap checks.
- Frozen evidence snapshots with per-table SHA-256.
- Publication tables and a much broader scientific figure builder.
- Claim-evidence ledger and automated scientific-wording audit.
- Built-in/manual citation library.
- Method inventory from actual stored evidence plus explicit implementation relationship.
- Internal/public reproducibility packages with transparent redaction rules.
- Improved DOCX/Markdown/HTML manuscript export and 300/600-dpi figures.
- Legacy Release-3 studies remain importable; original JSON files are not deleted.

DATA SAFETY
-----------
11.15 does not alter the schemas of Field Operations, Pollination, Persistent Twin, Research Evidence or Crop Profile databases.

A new additive reporting database is introduced:
  reports/reporting.sqlite
  schema 1.0.0

The reporting database references scientific source IDs and stores reporting metadata, snapshots, artifacts, claims, citations, versions and export history. It does not replace or overwrite the authoritative source databases.

UPGRADING EXISTING USER DATA
----------------------------
Use MIGRATE_USER_DATA_FROM_EXISTING_APP.bat and select the root of the existing working AGROLATTICE folder. The migration remains backup-first and will also migrate an existing reports/reporting.sqlite if a future/current source already contains one. If the source predates 11.15, the clean packaged reporting database is preserved.

SCIENTIFIC BOUNDARIES
---------------------
- Report generation does not validate a model or causal claim.
- Frozen evidence makes the report traceable; it does not make incomplete evidence complete.
- AI-assisted report auditing is optional and must not invent measurements, significance or references.
- Public-package redaction is a convenience aid, not a guarantee of full de-identification; researchers must inspect the final package.
- Journal-specific formatting must be checked against the target journal's current instructions.

STARTING
--------
Run RUN_APP.bat in the normal Windows/Anaconda environment.
