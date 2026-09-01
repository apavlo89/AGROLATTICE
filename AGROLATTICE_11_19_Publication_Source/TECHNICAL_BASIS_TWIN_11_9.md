# AGROLATTICE 11.9 — Persistent Twin technical basis

## Purpose

Release 11.9 unifies the persistent spatial/observational Twin with the existing
Mechanistic Maize Twin implementation. The aim is not to replace field evidence
with a crop model; it is to make biological state, observations, EO, water,
management, uncertainty and provenance inspectable in one long-lived field/season
object.

## Mechanistic maize timing

AGROLATTICE retains the disclosed concepts already implemented from Laurent et al.
(2025), Crop Science 65, DOI `10.1002/csc2.21453`:

- 30.6 GDD planting → emergence.
- Post-emergence collared leaf number: `2.5 * exp(GDD * coblf)`, capped at `tln`.
- Ear growth starts at `Vn = 0.67 * tln`.
- Ear biomass starts at 0.01 g.
- Female 50% silking occurs at `ebR1`.
- Male anthesis occurs 40 GDD after final-leaf expansion.
- Genotype parameters: `tln`, `coblf`, `ebR1`.

Publication priors remain approximately `N(19,2)`, `N(0.0019,0.00036)` and
`N(2,0.5)` respectively. These are priors, not local-line measurements.

The original proprietary data and original C++ Bayesian sampler are unavailable.
The AGROLATTICE implementation therefore remains an approximation/reimplementation
of disclosed mechanics and must not be called an exact reproduction.

## Persistent Twin integration

For a maize Twin with a linked trial, sowing dates and usable daily weather:

1. Resolve male/female physiology from the Maize Synchrony parent registry.
2. Fall back to the publication prior when local physiology is absent.
3. Compute mechanistic planting-GDD targets for anthesis/silking.
4. Reconstruct accumulated GDD at the requested Twin date.
5. If the event is already reached in available data, use the mechanistic event
   date; otherwise project remaining thermal time using the recent GDD rate.
6. Compare mechanistic timing with the pre-existing transparent target-GDD path
   to quantify model disagreement.
7. Retain legacy 650/670-GDD behaviour only as an explicitly labelled fallback.

## Time-travel leakage protection

When the Twin is reconstructed at a historical `as_of` date, mechanistic event
search and parameter-uncertainty simulation receive only weather through that
selected date. Later observed weather is not used to identify a past event.

The fallback point forecast may project remaining thermal time from the recent
GDD rate available by the selected date. This is an approximation, not a weather
forecast.

## Calibration

The Calibration Assistant calls the existing `calibrate_parent_physiology`
implementation using trial-linked flowering-event and leaf-count observations.
The fitted record is stored only after explicit researcher confirmation and is
saved with method/source/sample-size provenance in the Maize Synchrony parent
registry and a calibration audit record in the Twin DB.

## Uncertainty semantics

11.9 distinguishes:

- **Data completeness/quality** — freshness/availability of observation streams.
- **Parameter uncertainty** — prior-driven versus locally informed physiology.
- **Predictive timing interval** — generated only when weather coverage permits
  simulated event dates.
- **Model disagreement** — mechanistic timing versus the legacy/observed-target
  timing pathway.

The older scalar uncertainty score remains a compatibility alias and is labelled
as a data-uncertainty proxy rather than a formal posterior predictive interval.

## Scenarios

The maize sowing-strategy explorer uses the mechanistic uncertainty-aware
optimizer from `maize_mechanistic_twin.py`. Environmental/management scenario
responses from the older Twin simulator are retained separately and explicitly
labelled exploratory/heuristic.

## Spatial and evidence model

Field geometry stays authoritative. Trial/experimental-unit geometry is linked to
it and can be overlaid with sensors, scouting observations and operation polygons.
The Twin does not rewrite authoritative field geometry.

Evidence is shown as observed/retrieved/derived/modelled/forecast/heuristic where
applicable. Twin recommendations can be transferred to the Research Evidence
Recommendation → Action → Outcome ledger but are not treated as completed field
operations.

## Database migration

Twin DB schema 3.0.0 adds only:

- `twin_events`
- `calibration_runs`
- `analogue_seasons`

All legacy Twin tables are retained. A pre-11.9 backup is bundled and the release
verifier compares every legacy table row before/after migration.

## Performance

The Command Centre uses persisted summaries on entry. Maps, NASA retrieval,
Sentinel/STAC processing, calibration and scenario optimisation are only executed
inside their respective views/actions. This preserves the fast-navigation design
introduced in release 11.6.
