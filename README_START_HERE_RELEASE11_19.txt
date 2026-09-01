AGROLATTICE 11.19 — PUBLICATION REFERENCE RELEASE
================================================

REFERENCE IDENTIFIER
--------------------
AGROLATTICE-11.19-PRR-2026-08-12

PURPOSE
-------
11.19 freezes the integrated 11.x platform as the software/reference release for the AGROLATTICE platform manuscript. It is deliberately not a new scientific-model release.

The paper can now describe one stable version while AGROLATTICE 12.x develops separately.

WHAT IS NEW
-----------
• Stable publication-reference identifier visible in the app and bundled as PUBLICATION_REFERENCE_ID.txt.
• Publication Reference page under Help with architecture/workflow figures, citation metadata and a downloadable synthetic demo project.
• Deterministic synthetic demonstration project (seed 1119) with 24 experimental units, 4 blocks, 6 treatments and all 19 canonical environmental variable columns.
• Four reproducible reference figures in 300-dpi PNG and SVG.
• Example output tables plus a manuscript-safe demonstration results summary.
• CITATION.cff, codemeta.json and archive-ready .zenodo.json metadata.
• Restrictive proprietary portfolio-evaluation licence for original AGROLATTICE source plus a third-party/data/method notice.
• Publication-reference dependency lock and a Windows helper to freeze the exact target environment actually used for the paper.
• Reproducibility workflow, screenshot/figure checklist and manuscript starter scaffold.
• Source-file SHA-256 manifest and protected-artifact verification in the 11.19 verifier.
• Publication-safe source-archive builder excluding user SQLite databases, installed country datasets, caches and attachments while retaining schema-only SQL exports.
• Packaged runtime caches are cleaned from the publication reference archive; user caches can still migrate/rebuild normally.

SCIENTIFIC METHODS
------------------
11.19 changes no crop, climate, EO, statistical, ML, causal, irrigation, nutrient, crop-model or mechanistic maize scientific method.

The Laurent-derived Mechanistic Maize Twin is byte-for-byte unchanged.

DATABASES
---------
No database schema migration.

• Field Operations: 8.0.0
• Experiments: 3.0.0
• Persistent Twin: 3.0.0
• Research Evidence: 2.0.0
• Crop Profiles: 1.0.0
• Reporting: 1.0.0

The six protected SQLite databases remain byte-for-byte unchanged from 11.18.

SYNTHETIC DEMO BOUNDARY
-----------------------
The bundled publication_reference/demo_project data are synthetic.
They are not:
• field measurements;
• NASA POWER retrievals;
• Sentinel observations;
• sensor records;
• evidence that an AGROLATTICE model is agronomically accurate;
• evidence that a recommendation causes an outcome.

They exist solely so software plumbing, figures, tables, manifests and reproducibility workflows can be regenerated without private research data.

REPRODUCE THE DEMO
------------------
Run RUN_PUBLICATION_REFERENCE_DEMO.bat or:

python publication_reference.py --output publication_reference

The script regenerates and verifies the deterministic demo bundle, figures and example outputs.

FREEZE THE ACTUAL PAPER ENVIRONMENT
-----------------------------------
After RUN_APP.bat works in the Windows/Anaconda environment used for manuscript analyses, run:

FREEZE_PUBLICATION_ENV.bat

This records the exact Python runtime and pip freeze into publication_reference/environment/.

ARCHIVE / DOI
-------------
11.19 contains a stable internal reference identifier but cannot mint a DOI itself. Deposit the exact final 11.19 ZIP and checksum in a DOI-granting archive, then record the DOI in the manuscript and public repository metadata.

Do not replace the frozen 11.19 manuscript reference with 12.x functionality unless the manuscript itself is intentionally revised to describe a new reference release.

PCA / K-MEANS
-------------
The k=2–20 climate clustering/PCA exploration remains available. High-k exploration is diagnostic and does not define official agroecological zones.
