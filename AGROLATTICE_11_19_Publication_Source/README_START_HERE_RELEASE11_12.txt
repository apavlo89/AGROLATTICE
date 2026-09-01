AGROLATTICE 11.12 — NAVIGATION RELIABILITY & INTERACTION FIX
=============================================================

WHAT THIS RELEASE IS
--------------------
Release 11.12 is a focused reliability release built from AGROLATTICE 11.11.
It fixes programmatic navigation in command-centre interfaces after a real user
reported that the Priority decisions & evidence gaps buttons in Crop Decisions
appeared to do nothing.

ROOT CAUSE
----------
The Crop Decisions command centre maintained both a logical navigation state and
an explicit Streamlit radio-widget state. Priority buttons updated the logical
state, but on rerun the already-persisted radio widget restored its old value and
overrode the requested destination. Updating the widget key directly after the
radio had already been created would also be unsafe in Streamlit.

11.12 introduces a two-phase navigation request:
  1. a button queues the requested destination in a non-widget session key;
  2. the next rerun consumes that request BEFORE the navigation widget is
     created and safely updates the widget state.

The same latent interaction pattern was audited and corrected in the Persistent
Twin and Climate & Earth Observation command centres.

CROP DECISIONS FIX
------------------
Priority-decision buttons now reliably open their target areas:
  - Crop & planting
  - Water & irrigation
  - Nutrition
  - Pest & crop health
  - Yield & economics / other configured priority destination
  - Recommendations & outcomes when generated

After a priority action opens its destination, AGROLATTICE displays a short
context note explaining which priority action sent the researcher there.

OTHER NAVIGATION HARDENING
--------------------------
- Persistent Twin buttons such as Open Measurements & copilot, Open Setup,
  Open Spatial Twin and Open Evidence & validation use the same safe route
  request pattern.
- Climate & EO's Update field EO shortcut now safely routes to Earth Observation
  without mutating an already-instantiated segmented-control key.
- Manual navigation using the radio/segmented controls is unchanged.

STARTING THE APPLICATION
------------------------
Windows / Anaconda:
  1. Extract the complete release directory.
  2. Keep the directory structure intact.
  3. Run RUN_APP.bat.

DATABASES / MIGRATION
---------------------
No database schema changes are introduced in Release 11.12.
All existing Field Operations, Maize Pollination, Persistent Twin, Research
Evidence and Crop Profile Registry databases remain compatible with 11.11.
The backup-first migration utility is updated only to identify the target release
as 11.12; it does not rewrite unchanged schemas.

DEPENDENCIES
------------
No new third-party dependency is required. navigation_state.py is an internal,
pure-Python helper.

SCIENTIFIC MODEL STATUS
-----------------------
This release changes navigation behaviour only. It does not change crop models,
climate algorithms, field geometry, pest models, irrigation/nutrient logic,
Persistent Twin equations, or the Laurent-derived Mechanistic Maize Twin.

TESTING LIMITATION
------------------
The packaging environment does not contain Streamlit for a complete interactive
browser session. Release verification therefore includes an offline regression
of the navigation state machine, syntax checks, package integrity checks and
SQLite integrity checks. RUN_APP.bat performs the runtime Streamlit/module
preflight in the target Windows/Anaconda environment.
