AGROLATTICE 11.2 - SPATIAL & UPGRADE INTEGRITY UPDATE
=====================================================

This is the complete AGROLATTICE 11.2 application and supersedes Release 11.1.
It preserves the Mechanistic Maize Twin and Research Integrity safeguards while
fixing the remaining upgrade and trial-spatial-lifecycle defects found in the
second Release 11.1 audit.

WHAT 11.2 FIXES
---------------
1. Existing-trial spatial-link status now returns exact_match, removing the linked-trial UI crash.
2. Spatial re-linking is pre-commit safe. Existing treatment units are checked against
   the proposed trial boundary; the update rolls back if any unit would lie outside.
3. Exact mapped-field mode is explicitly tied to authoritative mapped-field geometry.
4. Trial retirement is safer. Archive is the recommended action. Hard deletion displays
   affected trial-scoped record counts, requires the exact trial name and an explicit
   cascade acknowledgement; the database layer independently enforces this for data-bearing trials.
5. The 11.1 migration flaw is fixed. The working app folder selected by the user becomes
   the research-database source of truth after explicit confirmation. Packaged/current
   destination DBs and source DBs are backed up first.
6. Research DB migration uses SQLite's online backup API to include committed WAL state,
   validates integrity/foreign keys, verifies table row counts before/after replacement,
   rolls research databases back if activation fails, removes stale WAL/SHM files and writes a migration report.
7. Current help wording/user guide now describe the 11.2 workflows. The old Release 10.3
   PDF is retained only as clearly-labelled legacy documentation.

SCIENTIFIC MODEL
----------------
The Release 11.0 Mechanistic Maize Twin is unchanged. Laurent et al. (2025)-inspired
assumptions, calibration, uncertainty and the approximate genomic bridge remain as
previously documented. Priors are not local measurements; predictions require field validation.

DATABASES
---------
No schema change is required from 11.1 to 11.2. The protected Field Operations,
Pollination Lab and Persistent Twin SQLite schema versions are unchanged.

UPGRADE FROM A WORKING OLDER VERSION
------------------------------------
Close the older app, extract 11.2, then run MIGRATE_USER_DATA_FROM_EXISTING_APP.bat.
Choose the ROOT folder of the working installation that contains your real research data.
After you type MIGRATE, 11.2 creates timestamped source/destination snapshots before
activating verified copies of the selected source databases. A migration_report.json is
written in the backup folder. Then launch RUN_APP.bat.

APPLICATION VERSION
-------------------
20.2-release11.2-spatial-upgrade-integrity

DEPENDENCIES
------------
Streamlit >=1.48.0 remains required. RUN_APP.bat checks it before launch.

CURRENT GUIDE
-------------
See USER_GUIDE_RELEASE_11_2.txt. The legacy Release 10.3 PDF is historical only.

VERIFICATION COMPLETED FOR THIS BUILD
-------------------------------------
- Full Python compilation: passed.
- Release 11.0 mechanistic regression suite: passed.
- Release 11.1 research-integrity regression suite: passed.
- Release 11.2 spatial/upgrade-integrity regression suite: passed.
- Packaged Field Operations SQLite integrity/foreign-key checks: passed.
- Packaged Pollination Lab SQLite integrity/foreign-key checks: passed.
- Packaged Persistent Twin SQLite integrity/foreign-key checks: passed.

LIMITATIONS
-----------
- Browser-level Streamlit rendering was not executed in the Linux build container because
  Streamlit is not installed there; non-UI modules were tested headlessly and RUN_APP.bat
  performs dependency/version checks in the user's environment.
- Cross-database reference guards assume the standard AGROLATTICE folder layout.
- Mechanistic flowering timing remains a research estimate, not a guarantee of pollen
  quantity, genetic purity, seed set or commercial performance.
