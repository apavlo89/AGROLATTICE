# AGROLATTICE 11.17 — Technical Basis: Help, Onboarding & UX Consistency

## Scope
Release 11.17 adds a metadata-driven researcher-guidance layer without changing scientific databases or crop-model equations.

## Architecture
- `researcher_guidance.py` contains pure, testable workspace guidance, evidence vocabulary, requirement definitions, workflows, troubleshooting and glossary metadata.
- `help_command_centre.py` renders the Help command centre and collects only small persisted readiness summaries from existing service APIs.
- `agrolattice.py` exposes the same `What do I need here?` panel across the nine primary research/data workspaces and routes Help actions to existing workspaces/tools.
- `ui_release10_4_help.py` retains the contextual hover-help engine and is updated to version 10.4.4.

## Performance boundary
Guidance collection must not:
- read/rebuild the large historical climate table;
- call NASA POWER or STAC;
- execute crop models;
- train/validate ML models;
- recompute a Persistent Twin.
It may issue small SQLite/DataFrame summary queries through existing databases/registries.

## Evidence vocabulary
The guidance layer standardises the labels Observed, Recorded, Retrieved, Derived, Mechanistic, ML prediction, Forecast, Scenario, Recommendation, Actual operation, Outcome and Causal estimate. These labels are interpretive metadata and do not alter historical records.

## Readiness semantics
`Ready` means the relevant persistent record/evidence exists. It does not certify validity, QC, adequacy, model promotion status or experimental design quality. `Partial` is reserved for cases where a future implementation supplies intermediate/stale status; otherwise missing prerequisites are reported as `Missing`.

## Database changes
None. Existing user data and schema versions are preserved.

## Scientific boundary
This release introduces no new paper-derived model and no scientific method change. It improves how existing methods, evidence types and limitations are explained and connected in the user interface.
