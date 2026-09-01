AGROLATTICE RELEASE 10.8
EXACT MAPPED-FIELD TRIAL LINKAGE AND MEASURED PLOT GEOMETRY

WHAT CHANGED

Release 10.8 removes the need to redraw an existing mapped field when creating a
maize flowering synchrony trial.

In Maize Synchrony Lab -> Trial setup, choose:

  Use exact mapped field

Then select the farm and field already stored under Fields & Operations. The
trial inherits the exact saved polygon, area, centroid and geometry fingerprint.
The trial also stores the source field ID and a geometry snapshot for
reproducibility.

If the experiment occupies only part of a larger field, choose:

  Use subsection of mapped field

The parent field is shown as a locked reference layer. The trial subsection must
remain completely inside it.

TWIN LINKING

When a trial has an exact mapped-field link, Twin configuration automatically
inherits that same field. The user cannot accidentally pair the trial with a
similarly named or slightly different field. For subsection trials, the Twin
inherits the parent mapped field while keeping the smaller trial geometry.

MEASURED INTERNAL PLOTS

Under Plot map & randomisation, choose:

  Generate measured plot grid

Enter plot width, plot length, number of plots per row, row/column gaps, row
direction and optional east/north offsets. AgroLattice generates exact polygons,
checks that every plot fits inside the trial boundary, previews them on the map,
then randomises treatments without requiring mouse-drawn plot rectangles.

EXISTING TRIALS

Trial setup now contains Spatial linkage for an existing trial. Use it to:

  - replace a manually drawn trial boundary with the exact mapped-field boundary;
  - retain the current trial as a validated subsection of a mapped field;
  - detect when a mapped field was edited after linkage;
  - resynchronise the trial while preserving internal plots, observations and
    harvest outcomes.

DATA SAFETY

The updater adds nullable columns to the existing maize-trial database. It does
not delete or rebuild farms, fields, trials, plots, observations, Twins, weather,
root-zone or Sentinel-2 records. Existing independent trials continue to work.

VERSION

App: 19.0-release10.8-exact-trial-field-linkage
Maize Flowering Synchrony Lab: 1.2.0
AgroLattice Twin: 2.5.0
