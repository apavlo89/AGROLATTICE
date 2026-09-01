# AGROLATTICE 11.7 — Technical basis: Research Command Centre

## Design objective
Home must answer **what is happening, what needs attention, and what should be
done next** without becoming an expensive analytical workspace itself.

## Lightweight data contract
`_release11_7_home_snapshot()` reads only small persistent summaries from:
- ProjectStore metadata;
- Field Operations tasks/alerts/timeline and a SQL MAX sensor timestamp;
- Maize Synchrony trial metadata and repeated-observation dates;
- Persistent Twin link metadata, attached-data metadata and latest saved snapshot;
- Research Evidence acquisition/prediction/recommendation/model metadata.

It does not invoke the heavy climate table, NASA POWER network retrieval, STAC,
raster processing, model training, the Twin state builder or an optimizer.

## Persistent freshness
11.6 Home used Streamlit session-state presence for daily weather/satellite
notices. 11.7 checks persistent field/Twin/registry metadata. This prevents a
simple app restart from making valid saved evidence appear absent.

For completed/historical seasons, freshness status becomes `Historical` when a
record exists. This avoids the scientifically misleading statement that a 2024
trial dataset is "stale" merely because the current calendar year is later.

## Priority actions
`home_command_centre.py` contains deterministic rules with explicit priorities.
Rules use only stored state: tasks, alerts, data freshness, trial-observation
recency, model status, applicability, recommendation/outcome closure and saved
Twin uncertainty. They are workflow prompts and do not make causal/agronomic
claims.

## Next measurement
The measurement suggestion is deliberately conservative and transparent. It can
prefer direct phenology or soil-water evidence when the Twin is uncertain or
critical data are missing. It is not presented as Bayesian expected information
gain and does not alter the trial design automatically.

## No schema change
11.7 adds one Python module and UI logic only. All research database schemas are
unchanged.
