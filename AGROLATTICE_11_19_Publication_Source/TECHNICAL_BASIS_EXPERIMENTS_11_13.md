# AGROLATTICE 11.13 — Technical basis: Experiments

## Design principle
The experiment is a persistent spatial scientific object: **field → trial → block/experiment plot → experimental unit → plant/observation**. Experimental-unit geometry remains tied to an authoritative mapped field.

## Database extension
Pollination schema 3.0.0 adds protocol, factors, design versions, measurement requirements and audit events without rewriting the established flowering, leaf-development, phenology, harvest, weather, satellite, physiology or model-run tables.

## Randomisation
The existing factorial block allocator is preserved. Random seed and full allocation manifest are persisted. Optional constrained search evaluates multiple reproducible candidate permutations within the block structure and selects the candidate with the fewest identical-treatment shared borders where geometry/Shapely permit. This is a spatial-balance heuristic, not proof of optimal design.

## Analysis integrity
11.13 keeps block/replicate/treatment/parent identifiers in the analysis-ready dataset. Random row splitting is not promoted as the primary validation strategy. The lightweight mixed model uses block as a random intercept only when the data support it; the UI warns that actual error strata must match the design.

## Mechanistic maize
`maize_mechanistic_twin.py` is not modified. Experiments continue to expose the established Laurent-derived mechanistic pathway and local calibration through the existing advanced synchrony workbench. Publication priors remain priors, not local measurements.

## Climate clustering k up to 20
K-means candidate search is bounded by `min(20, n_samples-1, distinct_profile_count)`. Automatic selection uses silhouette score over feasible k. Diagnostics also expose inertia and cluster sizes. PCA is a representation of the full standardized climate feature matrix; K-means is not interpreted as an official agroecological classification.

## Performance
The command centre uses a radio-based top-level state machine and executes only the selected branch. Legacy heavy workbenches are called only after an explicit toggle. No climate retrieval, satellite processing, model training or mechanistic optimisation executes merely because the Experiments workspace opens.
