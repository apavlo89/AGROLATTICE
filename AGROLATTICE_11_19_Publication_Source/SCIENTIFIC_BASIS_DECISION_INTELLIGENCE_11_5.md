# AGROLATTICE 11.5 — Scientific basis: Decision Intelligence & Research Optimisation

Release 11.5 operationalises the principle that **forecasting and decision-making are different scientific tasks**. A crop-state or yield model can be accurate yet still imply a poor action under costs, constraints, uncertainty or competing objectives. AGROLATTICE therefore stores the full chain **evidence -> model/scenario -> decision alternatives -> recommendation -> actual action -> measured outcome -> effectiveness audit**.

## 1. Irrigation: prediction/state model separate from policy

The reviewed 2026 work *Optimizing irrigation decisions with Seq2Seq modeling and deep reinforcement learning* (Computers and Electronics in Agriculture 245, 111448; DOI `10.1016/j.compag.2026.111448`) motivates separation of a soil-moisture/state forecast from a decision policy. Release 11.5 does **not** claim an exact Seq2Seq or deep-RL reproduction. Instead it uses the established AGROLATTICE FAO-style daily root-zone water-balance engine to compare explicit policies under identical crop, soil and weather assumptions.

Candidate policies include rainfed, RAW-triggered refill, deficit refill and fixed intervals, with optional comparison against a recorded soil-moisture sensor threshold. The sensor pathway uses existing Field Operations readings but sends no hardware command. NASA POWER can be retrieved directly for mapped fields and is recorded as gridded environmental evidence. Future weather must be supplied as a forecast/scenario and is labelled accordingly.

Where a whole-season yield-response factor (`Ky`) exists, relative-yield response is presented as a **water-stress proxy**. It is not silently converted into a field-calibrated yield forecast.

## 2. Multi-objective nutrient decisions and Pareto fronts

The reviewed paper *Multiobjective spatial optimization of fertilizer rates enables sustainable crop production in southwest China* (npj Sustainable Agriculture 4, 22, 2026; DOI `10.1038/s44264-026-00127-y`) motivates exposing competing nutrient objectives rather than hiding them in one score. Release 11.5 independently adapts the multi-objective concept with a transparent second-order empirical N/P/K response surface, regularisation, group-aware validation, a bounded candidate grid and non-dominated/Pareto screening.

This is **not** the paper's exact NSGA-II implementation. The simpler grid is intentional at this stage: it is auditable, CPU-friendly and keeps candidate rates visibly inside researcher-defined/observed support. Model quality is reported before optimisation. Without measured outcome and actual N/P/K rate variation, the tool does not generate a valid response surface.

## 3. State assimilation

The reviewed rice work *Developing remote sensing- and crop model-based methods to optimize nitrogen management in rice fields* (Computers and Electronics in Agriculture 220, 108899; DOI `10.1016/j.compag.2024.108899`) demonstrates the value of updating crop-model states with observations before a later management decision. Release 11.5 adds a general uncertainty-weighted scalar Gaussian update as infrastructure for this direction. For evolving states, it can update each time point independently against its own model prior; recursive posterior carry-forward is reserved for repeated measurements of a static/calibration state unless a process model supplies the next prior:

\[
K = \frac{\sigma_p^2}{\sigma_p^2 + \sigma_o^2},\qquad
\mu_{post}=\mu_p + K(y-\mu_p)
\]

\[
\sigma_{post}^2=(1-K)\sigma_p^2
\]

where the prior and observation must represent the same state and units (or use a separately validated observation operator). Release 11.5 does **not** define universal transforms from NDVI or another EO index to LAI, biomass, N status or soil water, and it does not claim the exact crop-specific N assimilation/optimisation workflow from the paper.

## 4. Recommendation effectiveness and observational causal inference

Tsoumas et al., *Evaluating Digital Tools for Sustainable Agriculture using Causal Inference* (arXiv:2211.03195), motivates evaluating whether following a digital recommendation is associated with improved field outcomes under explicit causal assumptions. Release 11.5 adds recommendation/outcome records and independent implementations of standard observational estimators: inverse-probability weighting, separate outcome models/T-learner and a doubly robust AIPW-style estimator.

Numeric and categorical pre-treatment confounders are supported; categorical factors are reference-coded and their encoded levels are retained in balance diagnostics. Nuisance models are cross-fitted to reduce same-sample overfitting; grouped cross-fitting is available for field/site/season/trial clusters. The interface reports overlap/positivity diagnostics, weighting effective sample size, standardised covariate balance and a treatment-shuffle placebo/refutation diagnostic. Bootstrap intervals resample the already cross-fitted effect scores (clustered when requested); nuisance models are not refit on each bootstrap replicate, so the interval is a fast research diagnostic rather than a full nested-bootstrap uncertainty analysis.

A causal interpretation additionally requires defensible assumptions including:

- consistency/well-defined treatment,
- conditional exchangeability given the selected **pre-treatment** covariates,
- positivity/overlap,
- no relevant interference between units,
- acceptable measurement and nuisance-model specification.


AGROLATTICE also stores the selected treated/intervention level, effect direction, selected adjustment variables, grouped cross-fitting choice and an optional researcher-authored adjustment rationale. This makes the identification assumptions reviewable rather than leaving only an estimator output. Categorical pre-treatment covariates are reference-coded internally and surfaced in diagnostics.

Unmeasured confounding cannot be ruled out by SHAP, propensity scores, weighting, balance tables or confidence intervals. AGROLATTICE therefore labels these outputs observational causal **audits/estimates**, not causal proof.

## 5. Scientific data separation

Release 11.5 deliberately distinguishes:

- **retrieved environmental evidence** (e.g. NASA POWER),
- **measured field observations**,
- **model/state estimates**,
- **decision alternatives**,
- **research recommendations**,
- **accepted/rejected recommendations**,
- **recorded applied operations**, and
- **measured outcomes**.

Recommendation status transitions are stored as separate audit-history events, including the previous status, new status, timestamp and optional researcher note. This preserves decision provenance without rewriting the history of what was proposed or reviewed.

This separation is essential for later effectiveness analysis. A recommendation being saved or converted to a task does not mean it was applied. An operation being recorded does not prove compliance with a prior recommendation. An observational association does not establish causality.

## 6. Researcher-centred design choices

Release 11.5 exposes alternatives, validation residuals, search ranges, assumptions and diagnostics rather than providing only a single answer. Automatic retrieval is used when AGROLATTICE already holds a defensible source (mapped fields, NASA POWER, sensors, trial/twin records); CSV upload remains a fallback for external experiments and future scenarios. The aim is to reduce provenance loss and repetitive data wrangling while preserving researcher control over variables, units, validation groups and decision objectives.
