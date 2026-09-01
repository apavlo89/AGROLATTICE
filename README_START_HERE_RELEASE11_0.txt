AGROLATTICE 11.0 - MECHANISTIC MAIZE TWIN
=========================================

This is the complete AGROLATTICE 11.0 application, superseding the 10.12 Field
Command Centre release while preserving its datasets, Persistent Twins, field
operations, mapped research centres, trials and satellite workflows.

START
-----
1. Extract the complete ZIP to a new folder.
2. To bring data from an older installation, run
   MIGRATE_USER_DATA_FROM_EXISTING_APP.bat and select the old AGROLATTICE folder.
3. Run INSTALL_DEPENDENCIES.bat if this environment has not been prepared.
4. Start with RUN_APP.bat.

WHAT IS NEW
-----------
* Daily MFS mechanistic maize simulation from tln, coblf and ebR1.
* Parent-specific physiology registry with informative priors and uncertainty.
* Repeated four-tagged-plant leaf-count and optional ear-development protocol.
* Prior-regularised calibration from local flowering and leaf observations.
* Selected-parent, selected-sowing-date, daily-weather scenario simulation.
* Correct empirical optimisation of signed synchrony gap toward zero.
* One-date versus two-date staggered male-sowing optimisation.
* Monte Carlo event-date intervals and timing-success probabilities.
* Optional SNP-marker genomic-ridge bridge for unmeasured parent physiology.
* Explicit scientific manifests and analysis-ready exports.
* Locally bundled boundary editor for research centres, fields and trial areas.

SCIENTIFIC BOUNDARY
-------------------
The MFS equations disclosed by Laurent et al. (2025), DOI
10.1002/csc2.21453, are implemented. Their commercial data and original C++
Bayesian CGM-WGP sampler are not public and are not reproduced. The optional
genomic-ridge bridge is clearly labelled as an approximation.

DATA SAFETY
-----------
The pollination database migrates in place without deleting old tables or
records. New tables store parent physiology and tagged-plant leaf development.
The complete package contains the data present in the supplied 10.12 base.
Keep the old installation until you have verified your migrated records.

RELEASE IDENTIFIERS
-------------------
Application: 20.0-release11.0-mechanistic-maize-twin
Maize lab: 2.0.0
Mechanistic engine: 1.0.0
Pollination database schema: 2.0.0
Fields & operations: 7.0.0
Local boundary editor: 1.0.0
