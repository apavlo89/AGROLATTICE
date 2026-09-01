AGROLATTICE 11.19 — ADAPTIVE CLUSTERING BUILD AC2
=================================================

Build identifier
----------------
AGROLATTICE-11.19-AC2-2026-08-12

Status
------
This is a separately packaged derivative of the frozen AGROLATTICE 11.19
Publication Reference Release. The visible release name remains 11.19, while
AC2 and its archive checksum distinguish the executable analysis build. The
original 11.19 archive is retained separately and is not overwritten.

Purpose
-------
AC2 adds a performance-oriented, auditable search for the environmental
variable subset and number of K-means clusters. The original 11.19 manual
variable workflow remains available in the same page.

AC2 algorithm
-------------
1. Build location-level variable-by-month climatological features for the
   selected years and months.
2. Use deterministic forward variable-block selection followed by backward
   removal. At least two variables are required so the result remains
   multivariate.
3. For every proposed subset, screen every feasible k from 2 to 20 on the full
   data. Full-data silhouette is used only for computational screening.
4. Evaluate the three strongest eligible k values using repeated 80/20
   train/test splits. Standardisation and K-means fitting occur on training
   locations only; silhouette is calculated on held-out locations.
5. Measure stability as pairwise adjusted Rand agreement between the full set
   of location assignments predicted by independently resampled fits.
6. Penalise each additional variable by 0.005 and each resample producing a
   cluster below 2% of locations by 0.10.
7. Select the simplest searched subset whose one-sided upper confidence bound
   for quality loss is no greater than the pre-specified 0.02 operational
   non-inferiority margin relative to the best searched subset.
8. Audit the selected subset and k on new random splits not used during search.
9. Fit the final descriptive K-means solution to all retained locations.
10. Select PCA dimensionality separately as the smallest number of components
    reaching the researcher-selected cumulative-variance threshold.

Interpretation boundary
-----------------------
AC2 finds the simplest supplied variable subset producing a clear, repeatable
empirical partition. It does not determine causal climate drivers, guarantee
coverage of every agronomically important process, establish official
agroecological zones, or prove transferability to another period, country,
crop or management question. Candidate variables remain a researcher decision.

Runtime
-------
The publication setting uses five search splits and ten independent audit
splits. On the bundled Mexico dataset with 1,012 locations and 19 candidates,
the reference run required about three minutes in the verification container.
The preview option uses three search and five audit splits.

Run
---
Double-click RUN_APP.bat and open:
Climate & Earth Observation > Spatial & Transferability > Agroclimatic clusters

Verification
------------
python verify_release11_19_ac2.py

The retained verify_release11_19.py and SOURCE_FILE_MANIFEST_11_19.sha256 apply
to the original frozen source tree. They are preserved for provenance and will
correctly detect that AC2 is a derivative.
