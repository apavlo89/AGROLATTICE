# Public source archive exclusions

AGROLATTICE 11.19 is distributed to the working researcher as a complete application release, including protected local scientific databases and installed datasets carried forward from the user's working installation.

Those materials should **not automatically be published** with the source code.

The public-source archive builder therefore excludes:

- all SQLite databases, WAL/SHM files and SQLite backups;
- Field Operations attachments;
- installed country climate datasets and `worldcities.csv`;
- project/study stores;
- caches and dataset-update working directories;
- satellite exports;
- external model run outputs/artifacts that may be licensed or user-specific;
- transient Python caches.

The public archive keeps source code, documentation, templates, branding, deterministic synthetic publication-reference data/figures, citation metadata and schema-only SQL exports.

This exclusion policy protects user data and avoids implying redistribution rights for third-party datasets or external model artifacts. It does not guarantee that every future file added to AGROLATTICE is safe for public release; researchers should review the generated archive before deposition.
