AGROLATTICE 11.6 — Performance & Branding Update
================================================

Release 11.6 is a focused optimisation release built on AGROLATTICE 11.5.
It preserves the Decision Intelligence, multimodal research, Persistent Twin,
Field Operations, Maize Synchrony and scientific-integrity capabilities while
making normal workspace navigation substantially lighter.

WHAT CHANGED
------------
1. The new AGROLATTICE logo is included under assets/brand and is displayed by
   the Streamlit application where the installed Streamlit version supports
   st.logo. A compact icon is included for collapsed navigation.
2. The active country's historical climate table is now a process-local,
   zero-copy Streamlit resource rather than an st.cache_data object. This avoids
   serialising/copying a very large DataFrame during normal reruns.
3. Dataset status is computed from the already loaded table. Release 11.5 could
   reread the complete country CSV only to count rows/locations/years. For the
   bundled Mexico file this meant another ~579 MB CSV read on navigation.
4. Country coordinates are attached without duplicating the entire climate
   table when every dataset location has a catalogue match (the normal case).
5. Field Operations, Pollination Lab, Persistent Twin, Research Evidence,
   ProjectStore and StudyStore service objects are initialised once per process
   and then reused. Their methods still open fresh SQLite connections when
   needed; no long-lived database connection is cached.
6. Country settings are no longer rewritten to disk when values have not
   changed.
7. System Diagnostics now includes a Performance & navigation cache panel with
   explicit reload controls for externally replaced datasets or service schema
   re-checks.
8. Dataset-updater changes remain safe: file size and modification-time tokens
   automatically invalidate the active-country runtime cache.

INSTALL / RUN
-------------
1. Extract the complete Release 11.6 folder.
2. If your real research databases/data live in a previous AGROLATTICE folder,
   run MIGRATE_USER_DATA_FROM_EXISTING_APP.bat before starting work.
3. Activate your normal ML_AGRICULTURE Anaconda environment if needed.
4. Double-click RUN_APP.bat.
5. On the first opening of a very large country dataset, AGROLATTICE still has
   to parse and prepare the authoritative CSV once for that Python process.
   Subsequent workspace/page reruns reuse the prepared runtime object.

DATA SAFETY
-----------
Release 11.6 makes NO schema change to:
- field_operations/field_operations.sqlite
- pollination_lab/maize_flowering_trials.sqlite
- agrolattice_twin/agrolattice_twin.sqlite
- models_evidence/research_evidence.sqlite

The Mechanistic Maize Twin equations/parameters are unchanged from Release 11.0.
The optimisation changes application loading/runtime behaviour only; they do not
alter stored climate values, model equations, experimental records or maps.

PERFORMANCE EXPECTATION
-----------------------
The most important improvement is navigation after the first active-country
load. Exact speed depends on CPU, RAM, storage and dataset size. The bundled
Mexico dataset is hundreds of MB, so initial loading can still take noticeable
time. Release 11.6 is designed to stop paying that cost again merely because a
researcher moved to another workspace or changed a normal Streamlit control.

See CHANGELOG_RELEASE_11_6.txt and USER_GUIDE_RELEASE_11_6.txt for details.
