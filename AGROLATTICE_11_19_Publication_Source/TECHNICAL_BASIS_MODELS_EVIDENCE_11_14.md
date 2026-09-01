# AGROLATTICE 11.14 — Technical Basis: Models & Evidence

## Architecture
11.14 makes Research Evidence the persistent governance layer around predictive models. The canonical chain is:

`Dataset / snapshot -> Training run -> Model version -> Validation run -> Prediction -> Recommendation -> Operation / measured outcome`

The workspace is lazy-rendered by `model_evidence_command_centre.py` so inactive sections do not execute expensive code.

## Research Evidence schema 2.0.0
Additive tables:
- `dataset_snapshots`
- `model_versions`
- `model_status_history`
- `validation_runs`
- `prediction_outcome_links`
- `model_health_events`

Existing schema-1.3 tables are preserved. `ResearchEvidenceRegistry` performs a SQLite backup before upgrading an older schema and verifies integrity, foreign keys and predecessor row counts after initialisation.

## Training-run persistence
`Research Model Lab` writes one `training_runs` record for every attempted candidate, including failed candidates. The settings include analysis goal, target, feature list, validation protocol, grouping columns, random seed and primary metric. Split manifests and leakage guards are stored separately from summary metrics.

## Validation design
Supported Model Lab presets include grouped CV, leave-one-group variants, LOYO, LORO, frozen group holdout and forward-time evaluation. Random row CV is retained only as a diagnostic option. Scalers/imputers/encoders remain inside sklearn pipelines fitted within training folds.

## Immutable model versions
The first Model Lab registration writes a `model_versions` record with:
- monotonically increasing version number
- artifact path and SHA-256
- software environment
- feature contract
- optional dataset snapshot relation

Legacy registered models without model-version rows remain readable.

## Evidence-gated promotion
`promotion_requirements()` inspects persistent validation evidence, applicability, calibration/uncertainty and limitations. `change_model_status()` blocks unsupported promotion unless a written governance override is explicitly used. Every status event is append-only.

## Validation runs
A validation run stores summary metrics, fold metrics, row-level predictions, split manifest, leakage guards, uncertainty/calibration/applicability context and evidence level. This permits later model comparison without reconstructing transient Streamlit state.

## Explainability
11.14 provides model-agnostic permutation importance and partial dependence where a compatible local artifact and evaluation table are available. Artifact hash mismatch blocks explanation. Existing model-specific SHAP workflows remain available. No feature-importance output is labelled causal.

## Ensembles
Registry-native comparison requires the same target, registered validation dataset and common held-out rows. Equal-weight aggregation is displayed only as a diagnostic. Learned weights and stacking are not labelled validated without an independent/nested meta-learning design.

## External benchmarks
Large benchmark resources are not silently downloaded. Local benchmark execution records benchmark family, reproduction status, model, features, target, metrics and dataset provenance. “Official split reproduced” is a researcher-declared status that should only be selected when true.

## Reproducibility
A downloadable ZIP can contain model card, training runs, validation runs, model versions, status history and prediction-outcome links. Inclusion of the model artifact is explicit. Raw source datasets are not silently redistributed.

## Limitations
- 11.14 does not implement a universal nested-stacking trainer; unsafe learned ensemble weights are intentionally not automated.
- Official benchmark dataset retrieval remains explicit/manual because size, licence and upstream formats vary.
- Full SHAP support is model/backend dependent.
- Automated prediction-outcome matching uses explicit target and field/trial context and should be reviewed by the researcher.
- External validity still depends on genuinely independent data, not the name assigned to a split.

## Split preview, repeated-group stability and paired differences
Model Lab can materialise the proposed fold manifest before fitting and verify group isolation. `Repeated grouped holdout` uses group-isolated repeated holdouts with a reproducible random seed for stability diagnostics. Per-fold metrics are retained so candidate ranking stability can be displayed. Registry-native comparison can bootstrap paired ΔRMSE on common held-out rows; it does not learn ensemble weights from the evaluation data.

## Classification probability evidence
`classification_metrics()` now reports class-specific precision/recall and, when genuine held-out probability matrices are available, ROC-AUC, PR-AUC, Brier score and log loss. Probability metrics are omitted when probabilities are not available. Validation UI also exposes a confusion matrix.

## Prediction/outcome matching guardrails
Automatic canonical matching prioritises experimental-unit context, then trial/field context, and uses the prediction season when timestamped observations permit. Prediction/observation chronology is retained and surfaced because retrospective model-evaluation records must not be interpreted as prospective deployment forecasts.

## Applicability and monitoring
The model detail page exposes OOD/extrapolation flags and outcome-linked error monitoring. Recent-versus-earlier error changes are descriptive drift diagnostics. A model-health event is an auditable scientific interpretation, not an automatic causal explanation for degradation.

## Registration and promotion governance
`register_model()` cannot silently promote a model: new models enter as Prototype and existing model upserts retain their status. All status changes flow through `change_model_status()`. Non-diagnostic held-out validation plus leakage/split documentation is required for internal validation. External/operational promotion requires explicitly recorded independent external, cross-site, cross-season or benchmark evidence. Generic leave-one-group-out evidence is not automatically relabelled external.
