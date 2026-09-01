AGROLATTICE 11.7 — Research Command Centre & Home Polish
========================================================

Release 11.7 is built directly on the fast AGROLATTICE 11.6 baseline. It keeps
all 11.6 performance improvements and turns Home into a research command centre
rather than a generic launcher.

WHAT YOU WILL NOTICE FIRST
--------------------------
When Home opens, it now answers five questions without running heavy analyses:
1. What field/project/trial am I working on?
2. What is happening in the latest saved Twin/evidence state?
3. Which data are current, historical, stale or missing?
4. What requires attention next?
5. What measurement or workflow is most useful now?

The Home page now includes:
- Continue current work / Resume Twin
- Twin Pulse
- dynamic Priority actions
- Data freshness & completeness
- Model & evidence status
- Next 14 days
- What changed recently
- Recent research projects

IMPORTANT PERFORMANCE DESIGN
----------------------------
Home deliberately does not fetch NASA data, search Sentinel-2, process rasters,
run the Twin, train ML models or run optimization on entry. It reads small
persisted summaries and gives explicit buttons for expensive work. This protects
the speed gains introduced in 11.6.

INSTALL / RUN
-------------
1. Extract the complete Release 11.7 folder.
2. If your real research databases/data live in another AGROLATTICE folder, run
   MIGRATE_USER_DATA_FROM_EXISTING_APP.bat before starting work.
3. Activate your ML_AGRICULTURE Anaconda environment if required.
4. Double-click RUN_APP.bat.
5. Select the desired project/field/trial using Change context on Home.

DATA SAFETY
-----------
Release 11.7 makes no database schema change. The packaged Field Operations,
Pollination Lab, Persistent Twin and Research Evidence databases are carried
forward byte-for-byte from the supplied 11.6 package. The Mechanistic Maize Twin
source is unchanged.

SCIENTIFIC INTERPRETATION
-------------------------
Twin Pulse may show retrieved data, derived values and model outputs together,
but each is labelled. A modelled flowering date is not an observation. Priority
actions and next-measurement prompts are transparent workflow heuristics, not
proof of agronomic benefit or autonomous control instructions.

See CHANGELOG_RELEASE_11_7.txt, USER_GUIDE_RELEASE_11_7.txt and
TECHNICAL_BASIS_HOME_11_7.md for details.
