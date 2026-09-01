# AGROLATTICE 11.15 — Technical basis for research reporting

## Architecture

Reports now reads persisted evidence directly from the four operational/research stores plus crop/model metadata. It does not require source evidence to be exported to CSV and re-uploaded.

The new independent `reports/reporting.sqlite` database is intentionally additive. It stores reporting objects and references to scientific source IDs without modifying Field Operations, Experiment, Twin or Research Evidence schemas.

## Evidence snapshots

A frozen report snapshot stores a scope, readiness state and SHA-256 of each selected persisted table encoded as deterministic CSV. Snapshot-table files are then saved under the reporting asset tree. This makes later database changes detectable rather than silently changing the evidence behind an older report.

## Report versions

Report versions are append-only rows containing version number, manuscript state, linked evidence snapshot, status, author and revision note. Draft editing updates the current study, while formal versions preserve prior states.

## Claim ledger

Important manuscript claims can be linked to evidence type, source reference and statistic/effect estimate. Automated wording checks flag terms that commonly overstate evidence (e.g. causal, optimal, validated, significant, generalizable). The audit is advisory and never creates evidence.

## Methods and citations

Method text is inferred from actual artifact/model evidence where possible. Every method carries an implementation relationship such as native AGROLATTICE, independent paper-derived adaptation, external backend or legacy alias. Paper citations are linked only where bibliographic information is known; no reference is fabricated.

## Privacy

Public exports can redact columns whose names identify coordinates, private field names, genotype identifiers or researcher names. The package includes the exact redaction rules/columns. This is not guaranteed anonymisation of arbitrary narrative text.

## Performance

The Reports landing page performs no remote NASA/STAC access, model execution, climate-space calculation or large-dataset scan. It queries field/trial/Twin-scoped persisted tables. Full climate SHA-256 computation is opt-in at package-build time because country datasets may be hundreds of megabytes.
