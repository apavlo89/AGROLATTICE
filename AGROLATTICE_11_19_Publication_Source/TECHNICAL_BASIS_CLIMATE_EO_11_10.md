# AGROLATTICE 11.10 — Technical Basis: Climate & Earth Observation

## Purpose

Release 11.10 is an orchestration, usability, provenance and performance release
for environmental intelligence. It does not replace the established climate,
risk, spatial or Sentinel-2 scientific methods. It connects them around mapped
field/season context and makes acquisition/evidence workflows persistent.

## Canonical climate data

The established country dataset remains authoritative and retains the complete
19-variable set:

`CLEARNESS_INDEX`, `CLOUD_AMOUNT_DAY`, `EVAPORATION_LAND`,
`EVAPOTRANSPIRATION`, `EVAPOTRANSPIRATION_ENERGY_FLUX`, `LONGWAVE_RADIATION`,
`PRECIPITATION_AVG`, `PRECIPITATION_MAX`, `PRECIPITATION_MIN`,
`RELATIVE_HUMIDITY`, `SOIL_HEAT_FLUX`, `SOIL_TEMP_LAYER1`, `SOIL_TEMP_LAYER2`,
`SOLAR_RADIATION`, `SURFACE_PRESSURE`, `TEMPERATURE`, `TEMPERATURE_MAX`,
`TEMPERATURE_MIN`, `WIND_SPEED`.

No Mexico-specific assumption is introduced into global retrieval or display
logic.

## Active-field climate reference

A mapped field may be used as the analysis context. For the installed monthly
climate dataset, the field centroid is compared with the small catalogue of
installed climate locations using haversine distance, and the nearest available
location is offered as the default reference. The UI explicitly labels this as a
spatial proxy. It is not converted into an on-field measurement.

## Direct NASA weather retrieval

The command centre reuses `research_data_hub.fetch_canonical_nasa_weather` and
its canonical 19-variable mapping. Retrieval is an explicit researcher action.
The field's authoritative centroid is used. Date-window precedence is:

1. structured field-season sowing/harvest dates when present;
2. recorded season year;
3. rolling 12 months.

No phenological date is invented. Acquisition provenance is sent to the Research
Evidence registry. When a compatible Persistent Twin link exists, retrieved
weather is also saved to the Twin using its existing persistence API.

## Sentinel-2 quick update

The quick EO action reuses the existing Sentinel-2 L2A/STAC processing system:
provider failover, catalogue cloud filtering, SCL masking, field polygon support
and the existing vegetation/moisture indices. Scene selection favours lower-cloud
observations per month and caps processing to protect interactivity. Advanced
manual processing remains available.

EO results are observational/derived evidence. They do not overwrite recorded
crop, irrigation or management data. Small experimental units may contain too few
pure pixels for defensible unit-level inference.

## Evidence persistence

Research Evidence schema 1.3.0 is reused; no schema migration is required.
Field-linked acquisition records preserve source, temporal support, variables,
request/provenance and row counts. User-approved session analyses may be written
as JSON artifacts and registered as evidence snapshots. This is provenance, not
a validation/promotion mechanism.

## Performance architecture

`CountryRuntimeData` now exposes a `climate_locations` table built once while the
active-country runtime is prepared. This prevents repeated `drop_duplicates`
operations over the full climate table for common selectors. The full climate
frame remains process-cached and the Field Climate page caches only the chosen
location subset keyed by the climate file's modification signature.

The Climate & EO landing view performs no NASA request, STAC query, raster
processing, similarity computation, PCA/clustering or crop-model execution.

## Scientific interpretation constraints

- Climate similarity depends on selected variables, temporal window, scaling and
  weights; it does not prove agronomic equivalence.
- PCA/cluster/embedding patterns are descriptive/predictive structures, not
  causal mechanisms.
- Hazard exposure is not automatically crop loss.
- NASA/gridded weather and local station/sensor measurements must remain
  distinguishable.
- EO indices are sensitive to usable pixels, cloud/shadow masking, acquisition
  frequency, spatial resolution and mixed pixels.
- Persisted analysis output is not automatically externally validated evidence.

## Database status

No database schema changes are introduced in 11.10. The four protected SQLite
files should remain byte-for-byte unchanged from the supplied 11.9 baseline.
