# AGROLATTICE 11.8 — Technical basis: Field Command Centre

## Design objective
Release 11.8 treats the mapped field as the persistent operational and research
context. The UI is intentionally structured around one active field instead of
independent page-level field selectors.

## Performance
The Overview path uses lightweight SQLite aggregation plus small metadata reads
from the Research Evidence and Persistent Twin stores. It does not fetch NASA
POWER data, query STAC, process satellite rasters, build crop models or train ML.
The full Folium spatial workspace is only created when the Map view is selected.
Portfolio Attention is one aggregate SQL query rather than several count queries
for every field.

## Schema strategy
Release 11.8 uses additive extension tables. Existing Release 11.7 core tables are
left structurally unchanged, preserving old insert/export/import paths and user
records. Extension tables are linked by stable IDs with foreign keys and ON DELETE
behaviour consistent with the parent record.

New extensions cover:
- field seasons;
- task research links/completion detail;
- observation protocols and quantitative measurements;
- operation spatial/provenance detail;
- sensor lifecycle/calibration;
- structured nutrient/sample metadata;
- alert rule persistence/cooldown and incident detail;
- persistent sampling points.

## Alert state
Alert persistence is no longer only metadata. `alert_rule_state` stores consecutive
trigger count, last value, last evaluation and last alert time per field/rule.
`evaluate_alert_rules` requires the configured number of consecutive triggered
evaluations and enforces the configured cooldown before creating another incident.
This remains rule-based screening, not a probabilistic pest/disease diagnosis.

## Spatial semantics
Field geometry remains authoritative. Scouting and sampling locations are point
supports. Custom operation polygons record treated spatial support and must be
contained by the field geometry. Trial/experimental-unit geometry remains owned by
the experiment system and is displayed as linked overlays.

## Precision semantics
Stored nutrient samples can feed multi-variable exploratory clustering. Variables
are standardised; PCA is optional; K-means is deterministic under a saved seed;
silhouette is displayed as an internal clustering diagnostic. No interpolation is
silently invented, and sample clusters are not promoted to continuous management
zones without appropriate spatial modelling and validation.

## Backward compatibility
The packaged Release 11.7 Field Operations database is preserved as
`field_operations/backups/pre_11_8_field_operations.sqlite`. Build verification
checks exact core-table row equivalence before/after migration. Pollination Lab,
Persistent Twin, Research Evidence and Mechanistic Maize files are carried forward
byte-for-byte.
