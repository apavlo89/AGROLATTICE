AGROLATTICE 11.14 — Model Evidence Command Centre & Scientific Validation
========================================================================

START
1. Activate the same Anaconda/Python environment you used for AGROLATTICE 11.13.
2. Double-click RUN_APP.bat.
3. Open Models & Evidence.

WHAT IS NEW
- Model Evidence Command Centre with lazy navigation.
- Persistent training runs for every candidate model attempt.
- Immutable model versions with artifact SHA-256, environment and feature contract.
- Auditable evidence-gated model promotion.
- Registry-aware validation against measured outcomes, with split preview, repeated grouped holdouts and model-ranking stability.
- Uncertainty/calibration and applicability review.
- Predictive explainability tools with causal-language safeguards.
- Registry-native model disagreement comparison with paired bootstrap model-difference uncertainty.
- Local benchmark execution with explicit reproduction status.
- Automatic training dataset snapshot manifests and one-click reproducibility packages.
- Season/spatial-context-aware prediction -> measured outcome linking and model-health/drift evidence.

RESEARCH EVIDENCE MIGRATION
The first 11.14 startup upgrades models_evidence/research_evidence.sqlite from schema 1.3.0 to 2.0.0 additively. A byte-for-byte 11.13 predecessor copy is included at:
models_evidence/backups/pre_11_14_research_evidence.sqlite

IMPORTANT
- Do not delete your existing field, pollination, Twin or model databases before upgrading.
- Copy your real user-data directories into the new release as you normally do, or use the existing safe migration workflow.
- A model marked Prototype remains a research candidate.
- Operational eligibility is evidence-gated and auditable.
- No model, benchmark or explainability computation runs merely because you open Models & Evidence.
