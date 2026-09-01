# Spatial sampling correction for climate-zone discovery

AGROLATTICE climate-zone discovery uses a city catalogue to retrieve and display
environmental profiles. City catalogues are spatially uneven: several nearby
locations may occur in densely populated regions while large sparsely populated
areas may contain few catalogue entries. Treating every city as an independent,
equally weighted sample can therefore cause settlement density to influence PCA,
cluster centroids, silhouette scores and the selected number of zones.

## Default method

The default **Equal-area support cells** option applies the following procedure:

1. Eligible, georeferenced locations are projected using a spherical Lambert
   cylindrical equal-area projection.
2. Locations are assigned to equal-area square support cells. The default cell
   width and height are 50 km, corresponding to a nominal area of 2,500 km².
3. Environmental feature values are averaged among locations occupying the same
   support cell.
4. Each occupied support cell contributes one equal analysis unit to variable
   selection, PCA, cluster-number selection, clustering, silhouette calculation,
   stability analysis and minimum-cluster safeguards.
5. Every original catalogue location inherits the final assignment of its support
   cell and remains present in maps and exports.

For a cell containing `n` catalogue locations, every exported location receives a
spatial analysis weight of `1/n`; weights sum to one within every occupied cell.
Adding an additional city inside an already occupied cell therefore does not give
that region more total influence. A location in a previously empty cell adds a new
spatial support unit.

## User controls and reporting

The support-cell width can be changed from 25 to 100 km. The selected width, raw
location count, effective support-unit count, mean and maximum locations per cell,
singleton-cell fraction, cell-membership table and location weights are displayed
after every analysis and included in the reproducibility download.

The **Raw location counts** option is retained only for sensitivity analysis and
reproduction of uncorrected workflows. The interface warns that this option allows
densely catalogued regions to contribute more influence.

## Interpretation

Cluster counts based on support cells describe represented geographic support;
city counts remain secondary display statistics. They are not estimates of land
area, cropland area or population. The resulting groups remain exploratory climate
clusters rather than official agroecological zones.
