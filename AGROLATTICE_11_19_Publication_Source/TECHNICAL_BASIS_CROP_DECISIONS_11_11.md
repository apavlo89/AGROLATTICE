# AGROLATTICE 11.11 — Technical Basis: Crop Decision Command Centre

## Objective

Release 11.11 makes Crop Decisions the agronomic decision layer that consumes
persisted Field, Twin, environmental, experiment, model and outcome evidence. It
does **not** replace the underlying scientific engines. Instead it standardises
context, readiness, provenance and the path from evidence to recommendation and
then to observed outcome.

## Architectural principles

1. **Field geometry and recorded season are authoritative context.** A mapped
   field is preferred over asking the user for duplicate city/coordinate inputs.
2. **Reuse saved evidence before retrieving again.** Persisted Twin/field weather
   is exposed as a first-class source. Remote retrieval remains explicit.
3. **Do not invent missing agronomic facts.** Missing sowing date, cultivar,
   nutrient rate or predictor remains missing.
4. **Prediction is not intervention.** Prediction, recommendation, planned/actual
   operation and measured outcome remain separate objects/workflows.
5. **Operational eligibility is explicit.** Prototype models are not promoted to
   field inference merely because they can produce a number.
6. **Country-specific assumptions remain scoped.** Mexico-specific agronomic
   calendar guidance is not presented as a global default.

## New modules

### `crop_decision_command_centre.py` — module 1.0.0

Provides the integrated Crop Decisions navigation and field-aware decision
workflows. Overview is designed to use lightweight database summaries and does
not perform remote retrieval/model execution on entry.

### `crop_profile_registry.py` — module 1.0.0 / DB schema 1.0.0

Adds a separate additive SQLite registry for researcher-defined crop/cultivar
profiles and immutable version history. The four protected operational/research
databases are not schema-migrated for this release.

A profile parent row stores identity/context; every parameter change is stored in
`crop_profile_versions`. Existing parents are updated with SQL `UPDATE`, not
SQLite `REPLACE`, so foreign-key cascade semantics cannot erase version history.

## Daily sowing-date climate exposure

The new explorer retrieves the canonical daily NASA weather bundle for the active
field only after explicit user action. Candidate sowing dates are evaluated over
historical years with an explicit season horizon and sensitive period.

Reported quantities include:
- precipitation and ETo-derived water balance where ETo exists;
- heat-day counts above an explicit Tmax threshold;
- maximum temperature in the sensitive period;
- longest dry spell;
- accumulated GDD using user-visible base and upper-cap assumptions;
- coverage/sample counts.

The output intentionally remains a **climate-exposure comparison**. It does not
claim cultivar-specific phenological timing or yield response unless a separate
validated model supplies those relationships.

## Pest operational inference

The main decision page filters the Research Model Registry to models whose status
is exactly `Operationally eligible`. A registered joblib artifact is loaded only
on researcher request. Predictors are built from the canonical weather data only
where definitions can be reproduced.

The implementation does not fabricate morning/evening relative humidity from a
single mean-RH product. If an eligible model requires predictors that cannot be
constructed, the workflow refuses the inference and explains the missing fields.

Where model support metadata are available, input applicability is evaluated and
reported. The registered output remains a model prediction; it is not converted
into a pest observation, disease diagnosis or treatment operation.

## Nutrient readiness

The command centre checks whether the field has structured samples, recorded
nutrient operations, meaningful variation in application rates and observed
outcomes. These are readiness indicators, not a formal proof that a response
surface is identifiable. Optimisation remains disabled/inappropriate when the
research data cannot support it.

## Yield evidence

Field-linked registered predictions and observed harvest outcomes are displayed
side-by-side. They are not averaged across model families. Differences between
models are treated as disagreement requiring review of assumptions, validation,
uncertainty and applicability.

## AquaCrop integration

AquaCrop can receive context from the active field and structured field season.
Weather preparation supports the canonical names:
`TEMPERATURE_MIN`, `TEMPERATURE_MAX`, `PRECIPITATION_AVG`, and
`EVAPOTRANSPIRATION` in addition to established aliases.

The readiness panel distinguishes recorded/field-specific information from
review-required/generic parameterisation. A successful run is not labelled as a
locally calibrated prediction without calibration evidence.

## DSSAT / APSIM interoperability

External model weather preparation also accepts canonical AGROLATTICE weather
aliases. Runs may be linked to the active mapped field when a legacy Project is
not active. Run status (including failure), executable/backend, exact command and
outputs/errors are retained as research provenance where the user saves the run.

Execution success does not certify equivalence of cultivar, soil, nitrogen or
management configuration between model backends.

## Performance

The Crop Decision Overview must remain lightweight. Remote NASA retrieval,
optimisation, pest inference, AquaCrop, DSSAT/APSIM and other expensive analyses
are explicit actions. The large country climate dataset remains managed by the
process-level performance cache introduced in Release 11.6.

## Validation / limitations

- The sowing-date explorer is not a crop-yield optimiser.
- Registered `Operationally eligible` status is a governance gate; researchers
  should still inspect model scope, validation and applicability.
- Economic values populated from Field Operations may omit unrecorded fixed or
  variable costs.
- Full interactive Streamlit widget/browser testing requires the target runtime;
  the build container does not contain Streamlit.
