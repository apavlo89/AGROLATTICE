# AGROLATTICE platform paper starter — reference release 11.19

**Software reference:** AGROLATTICE 11.19 Publication Reference Release (`AGROLATTICE-11.19-PRR-2026-08-12`).

This is a manuscript scaffold, not a completed paper. Bracketed items require author input or evidence from the frozen report/evidence system. No empirical performance result is supplied by this template.

## Candidate title

**AGROLATTICE: a spatially explicit agricultural digital-twin platform integrating field experiments, environmental data, crop models, Earth observation and scientific evidence**

## Abstract structure

**Background:** [Agricultural research problem and fragmentation of field, environmental, experimental and modelling evidence.]

**Methods/platform:** Describe the persistent spatial hierarchy, Field/Twin/Experiment/Model evidence spine, the 19-variable environmental data layer, EO/sensor links, mechanistic maize synchrony, decision tracking, validation governance and reproducible reporting.

**Results/platform demonstration:** Report software capabilities and a real case-study/evaluation only where supported by frozen empirical evidence. The bundled synthetic demonstration may be used to show reproducibility plumbing but must not be reported as agronomic validation.

**Conclusions:** State what integration/provenance problem AGROLATTICE addresses and the boundaries of evidence. Do not claim that mechanistic or ML components are universally valid merely because they are implemented.

## 1. Introduction

- Need for integration of genotype × environment × management evidence.
- Fragmentation across GIS, field operations, crop models, EO, sensor systems, experiments and predictive analytics.
- Difference between a persistent field digital twin and a one-off analysis.
- Contribution and intended users.

## 2. Software architecture

Suggested figure: `publication_reference/figures/figure_01_platform_architecture.svg`.

Describe the workspaces and persistent spatial hierarchy:

Country → research centre/farm → field → trial → experimental unit → plant/observation.

Explain that field geometry is authoritative and persistent evidence links Field → Trial → Experimental Unit → Twin → Model → Recommendation → Outcome → Report.

## 3. Environmental and spatial data

Describe the established 19-variable NASA-derived agroclimate dataset and global country support. Distinguish retrieved environmental estimates from local measurements. Describe Sentinel/EO linkage and spatial support limitations.

## 4. Persistent agricultural Twins

Describe the persistent state chain: environment → soil/root zone → crop development → phenology/stress → management → EO/sensors → treatments → phenotype → outcome.

Explain scenario, calibration, uncertainty and cross-season evidence concepts without claiming cross-season adaptive learning that belongs to future 12.x work unless implemented/validated in the frozen reference release.

## 5. Experiments and mechanistic maize synchrony

Describe experimental-unit mapping, factors, randomisation/protocol provenance, observation completeness and outcomes. For maize, distinguish female and male genotype, density, sowing dates/offset, block/replication, irrigation/management treatment and spatial assignment.

Document Laurent et al.-derived mechanistic assumptions accurately and state that proprietary data/original C++ Bayesian code are unavailable and exact reproduction is not claimed.

## 6. Models, validation and uncertainty

Describe model/training/version registries, grouped/site/season-aware validation, applicability/OOD, calibration/uncertainty and prediction→outcome linkage. Make clear that evidence status depends on actual saved validation and that random row splitting may be inappropriate for agricultural deployment questions.

## 7. Crop decisions and outcome tracking

Explain separation of retrieved/derived/model evidence, recommendations, actual operations and observed outcomes. Avoid causal claims from chronological association unless a causal design/estimator and assumptions support them.

## 8. Research reporting and reproducibility

Describe frozen evidence snapshots, report versions, claims, methods/citations, figures/tables and reproducibility packages. Suggested figure: `publication_reference/figures/figure_02_evidence_workflow.svg`.

## 9. Demonstration / case study

Two distinct options:

1. **Software reproducibility demonstration:** use the bundled deterministic synthetic project. State explicitly that it is synthetic and demonstrates plumbing only.
2. **Empirical agricultural case study:** use a frozen real dataset/report and report only supported measurements/validation results.

## 10. Discussion

Discuss integration advantages, researcher workflow, interoperability, interpretability, provenance and limitations. Include limits of gridded environmental data, EO spatial/temporal resolution, mechanistic parameter calibration, site/season transferability, optional external crop-model dependencies and observational causal inference.

## 11. Availability and reproducibility

State the exact AGROLATTICE 11.19 archive DOI/checksum once archived. Include `CITATION.cff`, release SHA-256, the source-file manifest, environment snapshot, demo-data manifest and reproducibility instructions. For public code deposition, prefer the publication-safe source archive and schema-only SQL exports rather than publishing local user databases.

## 12. Limitations and future work

Separate 11.19 capabilities from planned AGROLATTICE 12.x cross-season adaptive G×E×M learning. Future capability must not be written as current functionality.
