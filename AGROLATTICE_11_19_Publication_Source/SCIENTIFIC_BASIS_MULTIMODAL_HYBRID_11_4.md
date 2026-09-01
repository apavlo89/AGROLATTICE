# AGROLATTICE 11.4 — Scientific basis: multimodal crop intelligence and hybrid Twin learning

Release 11.4 implements selected high-value research directions on top of the Release 11.3 model/evidence infrastructure. It does **not** treat every reviewed paper as a separate application page. The design remains: **authoritative field/trial geometry → measured/retrieved environment and management → crop/phenology state → prediction with provenance → agricultural validation → Twin evidence**.

## Direct environmental acquisition

Many reviewed methods require weather, EO or crop-state covariates. Requiring users to export existing AGROLATTICE data and re-upload CSV would create avoidable duplication and provenance loss. Release 11.4 therefore adds a Research Data Hub that reuses the established NASA POWER client, installed country climate datasets, Field Operations records and current application outputs. NASA POWER values remain labelled gridded estimates. Retrieval does not create agronomic outcomes.

The full established 19-variable canonical climate profile remains available. Where NASA POWER optional fields fail, they stay missing and the retrieval warning is retained. Daily FAO-56 ETo is derived only when the required drivers exist; daily soil heat flux uses the transparent FAO-56 G=0 assumption and is not relabelled as a NASA observation.

## Phenology

PhenoYieldNet and PB-CNN reinforce the importance of biological/phenological time. Release 11.4 makes the central Phenology Service acquire mapped-field daily weather directly. The existing Laurent et al. (2025)-inspired Mechanistic Maize Twin remains the biological model; it is not replaced by a learned phenology network. Weekly/monthly climatology is rejected as daily GDD input.

## Pest early warning

Wadhwa & Malik (2024), DOI `10.1016/j.compag.2024.109472`, use MaxT, MinT, morning/evening RH, rainfall, wind, sunshine and evaporation plus engineered temperature difference, humidity difference, average humidity and VPD, followed by model comparison, imbalance handling, tuning and SHAP. Release 11.4 retains the independent AGROLATTICE implementation while adding direct NASA retrieval. NASA POWER's daily mean RH is **not** silently duplicated into RH1 and RH2. A NASA-compatible reduced feature set is used instead, and models trained on unavailable source-specific variables are declared incompatible rather than coerced.

Wang & Zhang (2024), DOI `10.1016/j.eswa.2024.124137`, motivate future temporal pest forecasting using attention, LSTM and Interaction CNN with historical pest counts. Exact ALIC is not claimed in 11.4 because adequate longitudinal pest-count data and a dedicated time-series backend are prerequisites.

## Adaptive multimodal fusion

The adaptive fusion literature motivates modality-specific encoders and sample-dependent fusion rather than unconditional concatenation. Release 11.4 implements a CPU reliability-gated adaptation: each modality model is evaluated out of fold, an error model predicts absolute error from that modality's numeric context, and inverse predicted error is normalised across available modalities per sample. This is an AGROLATTICE adaptation, not an exact neural reproduction of Mena et al. Gate weights are predictive reliability signals; they do not identify causal agronomic drivers.

## Hybrid mechanistic + ML residual learning

AGROLATTICE's preferred direction is mechanistic crop biology plus observations/EO/statistical correction, not black-box replacement. Release 11.4 therefore adds residual learning:

`hybrid prediction = mechanistic/base prediction + predicted residual`.

The residual model is evaluated using the same held-out agricultural folds as the base comparison. The correction is marked PASS only when held-out RMSE improves. This does not validate the underlying mechanistic model and does not justify external deployment without independent site/season evidence.

## Weakly supervised spatial yield

Paudel et al. (2023), DOI `10.1088/1748-9326/acf50e`, demonstrate the value of learning fine spatial patterns when labels exist only at coarse support. Release 11.4 introduces a transparent aggregate-consistency Ridge baseline rather than claiming reproduction of the paper's full neural framework. It trains on independently labelled aggregate groups and applies the learned response surface to fine covariate rows. Agreement at aggregate support is **not** independent validation of fine-scale yield.

## G×E×M research-table assembly

The Maize Synchrony Lab already stores parent/genotype, sowing strategy, density, blocks/replicates, management, observations and outcomes. Release 11.4 exposes these as a read-only experimental-unit research view so modelling can use existing app data without export/re-upload. Trial, field, season, block and replicate identifiers are preserved specifically to enable group-aware validation and avoid leakage.

## Deferred methods

Release 11.4 does not claim exact implementations of MMST-ViT, PhenoYieldNet, PB-CNN, ALIC, SCM-GAT, causal treatment-effect estimation, EO/crop-model N optimisation, DRL irrigation control, NSGA-II fertiliser optimisation, production market GNN/transformers or federated learning. Their reviewed methods remain roadmap inputs and should enter AGROLATTICE only when the data contract, validation scope and operational safeguards are appropriate.
