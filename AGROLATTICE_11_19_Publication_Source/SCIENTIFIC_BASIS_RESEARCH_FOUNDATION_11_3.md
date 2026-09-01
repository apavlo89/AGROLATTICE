# AGROLATTICE 11.3 — Scientific basis of the Research Foundation

## Design principle

Release 11.3 converts the reviewed agricultural-informatics literature into a reusable scientific infrastructure rather than adding one page per paper. The target chain remains **field geometry → environment/soil/crop state → management/experiment → EO/sensors → model → uncertainty/applicability → recommendation → measured outcome → validation**.

A publication is evidence that a method merits evaluation; it is not evidence that the method is already valid for a new AGROLATTICE crop, field, genotype, country or season.

## 1. Canonical evidence and provenance

The new Research Evidence Registry stores datasets, long-form observations, models, runs, predictions, recommendations and outcomes. Every observation can be explicitly typed as **Measured, Derived, Assumption, Prior, Forecast or Model output**. Spatial support and temporal resolution are retained so field averages, experimental units, pixels, sensors and coarse gridded climate values are not silently treated as equivalent measurements.

The design is informed by multimodal benchmark/data-system work including CropNet, YieldSAT and WorldCereal. Release 11.3 provides metadata/adapters for these resources but does not redistribute their large source datasets.

## 2. Validation under agricultural distribution shift

YieldSAT and the wider reviewed literature motivate evaluation that matches deployment. AGROLATTICE 11.3 therefore provides grouped CV, leave-one-group-out, leave-one-year-out, leave-one-region-out and forward/walk-forward validation. Random CV remains available only as a diagnostic.

All estimator preprocessing is encapsulated in fold-fitted pipelines. Class resampling such as SMOTE-ENN is also placed inside training folds. This is intentionally stricter than reproducing leakage-prone or random-only protocols from individual source papers.

## 3. Applicability rather than false confidence

The release adds a robust marginal support diagnostic using training medians, IQR/scale and observed ranges. It flags rows that are outside the empirical training range and returns a similarity/support score. This score is **not a calibrated probability that the prediction is correct** and must not be presented as one.

## 4. Phenology as a shared biological axis

PhenoYieldNet and PB-CNN reinforce the value of representing crop development rather than relying only on calendar date. AGROLATTICE 11.3 therefore introduces a central Phenology Service with generic thermal-time staging and direct integration with the existing Mechanistic Maize Twin.

The mechanistic maize implementation is unchanged in this release. It retains the disclosed Laurent et al. (2025)-inspired assumptions already present in AGROLATTICE: 30.6 GDD planting→emergence; leaf number `2.5*exp(post-emergence GDD*coblf)` capped at `tln`; ear-growth onset at `0.67*tln`; ear biomass initiation at 0.01 g; female 50% silking at `ebR1`; male anthesis 40 GDD after final-leaf expansion. Genotype parameters remain `tln`, `coblf`, `ebR1` and publication priors remain priors rather than measurements of local lines.

Mechanistic timing does not guarantee pollen quantity, seed set or seed purity.

## 5. Environmental pest early warning

The lower-data pest workflow is an independent adaptation of Wadhwa & Malik (2024), *Computers and Electronics in Agriculture* 227, 109472, DOI `10.1016/j.compag.2024.109472`.

Source-derived engineered variables implemented in 11.3 are:

- `Temp_Diff = MaxT - MinT`
- `Hum_Diff = RH1 - RH2`
- `Avg_Hum = (RH1 + RH2)/2`
- `es = 0.6108 * exp(17.27*Tmean/(Tmean+237.3))`
- `ea = (RHmean/100)*es`
- `VPD = es - ea`

The source paper compared multiple classical/ensemble models, handled imbalance with SMOTE-ENN, tuned shortlisted models with Optuna and used SHAP. AGROLATTICE supports the same broad families where dependencies are available, but deliberately prefers grouped/year/region/forward validation over treating the paper's random 80/20 result as proof of geographic generalization. Resampling is performed inside training folds.

Pest-disease mappings are warning context only: pest prediction is not a confirmed disease diagnosis.

## 6. Temporal pest forecasting (ALIC) — reviewed, not yet reproduced

Wang & Zhang (2024), DOI `10.1016/j.eswa.2024.124137`, uses feature attention, separate LSTM representations for meteorology and historical pest series, an Interaction CNN for intra/inter-modal interactions, and walk-forward evaluation. The full method has been reviewed. Exact ALIC is intentionally deferred until AGROLATTICE has sufficient historical pest time-series data and the common registry/validation interfaces are established. Release 11.3's forward validation and pest data contract are preparatory infrastructure, not an ALIC reproduction.

## 7. Multimodal fusion

The release includes a practical CPU baseline inspired by adaptive multimodal crop-yield fusion work. Each modality is modeled separately and evaluated on the same agricultural held-out folds. Inverse held-out RMSE determines baseline modality weights. Weights are renormalized per prediction when an entire modality is missing.

This is **not** an exact implementation of a neural gated-fusion architecture. The stored method name explicitly labels it an AGROLATTICE adaptation. Inter-modality standard deviation is disagreement among modality models, not calibrated aleatoric/epistemic uncertainty.

## 8. Uncertainty schema

PB-CNN motivates explicit distinction between aleatoric and epistemic uncertainty. Release 11.3's Prediction Registry can store total, aleatoric and epistemic components plus the named uncertainty method. The baseline Model Lab may use held-out residual/conformal-style intervals where appropriate, but these are not relabeled as Bayesian uncertainty.

## 9. Small-data baseline strategy

The model laboratory emphasizes strong simple baselines before deep networks. Core models include linear/logistic, random forest, extra trees and histogram gradient boosting. XGBoost, LightGBM and CatBoost are supported. TabPFN is a runtime-discovered optional backend motivated by recent small-data crop-yield work; it is not a required startup dependency.

## 10. Recommendation and outcome persistence before causal claims

Research on causal evaluation of digital agricultural tools motivates a durable record of recommendation, compliance/application and later outcome. Release 11.3 implements this data contract. It does **not** yet implement treatment-effect estimators. Future causal analysis must state DAG/identification assumptions, overlap, estimator, uncertainty and sensitivity/refutation checks.

## 11. Methods intentionally deferred

The following are not claimed as implemented in Release 11.3: exact MMST-ViT, exact PhenoYieldNet, exact PB-CNN, exact ALIC, weakly supervised fine-resolution yield loss, SCM-GAT, causal treatment-effect estimators, EO/crop-model N optimization, DRL irrigation control, NSGA-II fertilizer optimization, production agricultural-price GNN/transformers and federated learning.

They are documented in `RESEARCH_METHODS_MANIFEST_11_3.json` so later releases can integrate them into the same evidence/validation system rather than creating isolated prototypes.
