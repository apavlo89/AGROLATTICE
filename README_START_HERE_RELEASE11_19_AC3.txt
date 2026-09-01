AGROLATTICE 11.19 — ADAPTIVE CLUSTERING BUILD AC3
=================================================

Build identifier: AGROLATTICE-11.19-AC3-2026-08-13

STATUS AND LINEAGE
------------------
AC3 is a separately packaged derivative of the frozen AGROLATTICE 11.19
Publication Reference Release. The visible release name remains 11.19. The
AC3 build identifier and archive checksum distinguish this executable build.
The original 11.19 and AC2 archives are retained separately and are not
overwritten. The AC2 and original manual workflows remain available in AC3.

PURPOSE
-------
AC3 adds a reproducible benchmark across alternative clustering geometries
instead of assuming that K-means is appropriate. It keeps variable-subset
selection, clustering model selection and PCA dimensionality as distinct,
reported decisions.

AC3 WORKFLOW
------------
1. Build a location by variable-month matrix. Each value is a climatological
   mean over the selected years for a selected calendar month. The clustering
   interface does not cluster raw daily records.
2. Either freeze a researcher-defined variable set or run the retained AC2
   forward-selection/backward-removal procedure and freeze its selected set.
3. Screen k and method-specific settings for K-means, bisecting K-means,
   diagonal/tied Gaussian mixtures, BIRCH, Ward hierarchy and average-linkage
   hierarchy under cosine distance.
4. Shortlist the two strongest eligible configurations per family using
   full-data silhouette only as a computational screen.
5. Evaluate shortlisted configurations using common repeated 80/20 splits.
   Scaling and fitting use training locations only. Championship silhouette is
   Euclidean for every method on the same standardised held-out locations.
6. Measure stability using pairwise adjusted Rand agreement among predictions
   from resampled fits. Penalise resamples containing a cluster below 2% of
   locations.
7. Select the simplest searched configuration within a one-sided 0.02
   operational non-inferiority margin of the strongest repeated-resampling
   quality. This is not a population-level equivalence test.
8. Audit the strongest searched configuration from each family on untouched
   splits. The champion selected during search is not changed using audit data.
9. Fit each family winner to all locations, report assignment confidence,
   compare partitions, and create a selected-method co-clustering consensus
   matrix from independent audit predictions.
10. Optionally run HDBSCAN as a noise-aware full-data density diagnostic. It is
    not eligible to win the inductive championship because its transductive
    coverage and noise semantics are not directly comparable.
11. Select PCA dimensionality independently as the smallest component count
    reaching the chosen cumulative-variance threshold.

HIERARCHICAL PREDICTION DISCLOSURE
----------------------------------
Scikit-learn agglomerative methods do not natively predict unseen samples.
AC3 fits the hierarchy on training locations and assigns held-out locations to
the nearest training-cluster centroid. Ward uses Euclidean distance;
average-cosine uses cosine distance. This disclosed surrogate permits held-out
evaluation but is not identical to refitting a full transductive dendrogram.

VISUAL ANALYTICS
----------------
AC3 includes a family leaderboard, confidence-scaled PCA plot and geographic
map, within-cluster silhouette distributions, confidence-separation plot,
co-clustering consensus heatmap, family agreement matrix, Sankey assignment
flows, standardised fingerprint heatmap and radar profiles. All underlying
tables and reproducibility metadata can be exported as a ZIP package.

MEXICO REFERENCE BENCHMARK
--------------------------
The publication setting was verified on the bundled Mexico data: 1,012
locations, 1985–2025, all 12 calendar months and 19 candidate variables. AC2
selected SURFACE_PRESSURE and TEMPERATURE_MIN. AC3 selected K-means with k=2.
The independent audit produced mean held-out silhouette 0.6081 (SE 0.0061),
stability ARI 0.9727, mean assignment confidence 0.6926 and zero tiny-cluster
resamples. Bisecting K-means was nearly indistinguishable, but ordinary
K-means was retained by the declared parsimony rule. These results describe
this run and are not official Mexican agroecological zones.

RUN
---
Double-click RUN_APP.bat and open:
Climate & Earth Observation > Climate Zones & Transferability > Climate-zone discovery

The interface uses task-oriented names. Select "Robust multi-method analysis
(recommended)" for the full benchmark or "Focused K-means analysis" for a
simpler prespecified workflow. AC2 and AC3 remain technical engine identifiers
in reproducibility records rather than user-facing workflow names.

The climate-zone workflows can screen candidate k through 50. Automatic
selection applies a 2% minimum-zone-size safeguard; all tested k remain visible
for diagnosis. The page blocks incomplete frozen Mexico inventories and reports
source, eligible, mapped and excluded location counts after every run.

VERIFICATION
------------
python verify_release11_19_ac3.py

SCIENTIFIC BOUNDARY
-------------------
AC3 optimises an empirical partition within the supplied period, variables,
locations, algorithms and scoring rule. It does not discover causal climate
drivers, establish an official classification, validate crop response or
guarantee G×E×M transferability.
