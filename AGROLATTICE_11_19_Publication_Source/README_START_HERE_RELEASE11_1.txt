AGROLATTICE 11.1 - RESEARCH INTEGRITY UPDATE
=============================================

This is the complete AGROLATTICE 11.1 application, superseding Release 11.0.
It retains the Mechanistic Maize Twin and Field Command Centre while hardening
experimental-data safety, spatial integrity and release compatibility.

KEY FIXES
---------
1. Plot re-randomisation is blocked once plot-linked observations, phenology,
   harvest, leaf/ear, satellite-link or model-run data exist. Collected data are
   no longer cascade-deleted by a routine randomisation save.
2. Factor-design metadata and plot randomisation are saved atomically. If any
   validation/write fails, neither side of the design is committed.
3. Treatment-unit polygons are rejected when they have positive-area overlaps;
   shared boundaries remain valid.
4. Field/farm/trial deletion now checks cross-database Persistent Twin and
   maize-trial links and blocks operations that would orphan research objects.
5. Streamlit >=1.48 is now required and checked by RUN_APP.bat because the app
   uses the current width="stretch" widget API.
6. Help -> Release notes resolves the current README from the latest manifest.
7. The data-migration BAT preserves existing Release 11.1 SQLite databases and
   creates a timestamped safety backup before migration.
8. Synchrony outputs report observation completeness, missing dates and largest
   gaps; overlap is explicitly an observed-day metric with no silent gap fill.

SCIENTIFIC MODEL
----------------
The Release 11.0 mechanistic maize assumptions are retained unchanged: 30.6 GDD
planting->emergence; leaf number 2.5*exp(post-emergence GDD*coblf) capped at tln;
ear-growth onset Vn=0.67*tln; ear biomass starts at 0.01 g; female 50% silking
at ebR1; male anthesis 40 GDD after final-leaf expansion. Local calibration and
uncertainty remain required; priors are not measurements of local lines.

DATABASE MIGRATION
------------------
No schema migration is required from Release 11.0 to 11.1. Existing Field
Operations, Pollination Lab and Persistent Twin SQLite schemas remain compatible.
The release adds application-level cross-database guards and safer transactions.

APPLICATION VERSION
-------------------
20.1-release11.1-research-integrity

START
-----
Run RUN_APP.bat from your normal ML_AGRICULTURE environment.

DEPENDENCIES
------------
The main environment now requires Streamlit >=1.48.0. RUN_APP.bat checks this
before launch. Other dependency pins/requirements remain in
requirements_ml_agriculture.txt.

VERIFICATION COMPLETED FOR THIS BUILD
-------------------------------------
- Full Python compile/AST check: passed.
- Release 11.0 mechanistic regression suite: passed.
- Release 11.1 research-integrity regression suite: passed.
- Field Operations SQLite integrity_check: passed.
- Pollination Lab SQLite integrity_check: passed.
- Persistent Twin SQLite integrity_check: passed.
- Packaged 11.0 user databases were byte-for-byte preserved during the upgrade.

LIMITATIONS
-----------
- A genuine Streamlit browser/AppTest session was not executed in the build
  container because Streamlit is not installed there; RUN_APP.bat now verifies
  the required installed version on the user's machine. Source compilation and
  non-UI regression tests were completed.
- Cross-database delete guards assume the standard AGROLATTICE folder layout.
  If a dependency database exists but cannot be read, deletion is safety-blocked.
- Synchrony overlap remains based on observed daily records; missing dates are
  reported and are not silently interpolated.
- Mechanistic timing predictions remain research estimates and do not guarantee
  pollen quantity, seed purity or field performance.
