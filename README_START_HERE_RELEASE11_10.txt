AGROLATTICE 11.10 — START HERE
=============================

Release title
-------------
Climate & Earth Observation Command Centre

What is new
-----------
Climate & Earth Observation is now organised around the active mapped field and
one environmental research workflow instead of four loosely connected tool
families. Existing climate comparison, spatial/risk analyses and Sentinel-2
methods remain available, but field context, 19-variable exploration, data
freshness, direct retrieval and provenance are much easier to use.

Main Climate & EO views
-----------------------
Overview
  Lightweight Environmental Pulse showing saved weather, EO, root-zone and
  sensor freshness plus direct research actions.

Field Climate
  Explore all 19 canonical agroclimate variables by location, year, climatology,
  annual trend and year × month pattern. A mapped field defaults to its nearest
  installed climate reference and the UI clearly labels this as gridded/location
  evidence rather than an on-field measurement.

Climate Comparison
  Existing similarity, pairwise, analogue, explanation and robustness tools,
  now with active-field reference support.

Spatial & Transferability
  Existing climate-space and transferability analyses with clearer interpretation
  guidance for PCA and nonlinear embeddings.

Climate Risk
  Existing climate-risk tools shown in active crop/season context. Hazard
  exposure remains separate from any unvalidated claim about crop consequence.

Earth Observation
  Existing Sentinel-2 workflow under researcher-facing names, with active-field
  geometry preloading and an explicit quick-update option.

Evidence & Data
  Field-linked environmental provenance, Twin attachments and explicit saving of
  current climate/EO analysis snapshots to the Research Evidence registry.

Direct retrieval — no CSV required for data AGROLATTICE can obtain
------------------------------------------------------------------
For a mapped field, "Update NASA weather" retrieves the canonical daily weather
bundle from the existing Research Data Hub pathway. "Quick update EO" uses the
existing Sentinel-2 L2A pipeline. These are deliberate button actions: they do
not run just because you enter the page.

AGROLATTICE never silently treats NASA/gridded values as local weather-station
measurements, and it does not invent sowing dates when a structured field-season
record does not provide one.

Performance
-----------
The 11.6 process-level climate cache is preserved. Release 11.10 also prepares a
small climate-location catalogue once, so selectors do not repeatedly de-duplicate
the very large country climate table. Opening Climate & EO itself remains light.

Starting the app
----------------
Use RUN_APP.bat from the AGROLATTICE folder in the same Windows/Anaconda setup
used for previous releases. The preflight verifies the 11.10 Climate & Earth
Observation Command Centre before Streamlit launches.

Data safety
-----------
Release 11.10 requires no database schema migration and adds no new mandatory
package. Keep your normal backups; the included migration utility remains the
safe way to bring real working data from an older AGROLATTICE folder.
