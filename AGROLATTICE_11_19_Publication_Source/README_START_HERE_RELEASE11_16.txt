AGROLATTICE 11.16 — Platform Control Centre, Data Settings & Tool Catalogue

START HERE
==========

1. Keep your previous AGROLATTICE folder intact until you verify this release locally.
2. If you are moving existing user data into this folder, use MIGRATE_USER_DATA_FROM_EXISTING_APP.bat and point it to your working older installation.
3. Start with RUN_APP.bat.
4. Open Data & Settings to inspect database health, country climate data, storage, optional backends and backups.
5. Create a verified backup before major data updates or future version changes.

WHAT IS NEW
===========
- Data & Settings is now a dedicated Platform Control Centre.
- All Tools is now a searchable scientific-tool catalogue rather than a long undifferentiated directory.
- Safe verified backup and scientific-database restore are built into the interface.
- Storage/cache controls explicitly protect scientific data and only delete reproducible caches.
- Optional research/model backends and DSSAT/APSIM executable paths are visible in one place.
- The current country climate workspaces and core database schemas/health can be inspected without loading huge tables into memory.

NO SCIENTIFIC DATABASE MIGRATION
================================
All protected scientific database schemas are unchanged from 11.15.
The Mechanistic Maize Twin is unchanged.

PERFORMANCE
===========
The 11.6 process-local climate/runtime caching is preserved. Data & Settings uses metadata and small SQLite queries; it does not load the 579-MB Mexico climate dataset again merely to render its dashboard.

BACKUP SAFETY
=============
The Backup Centre uses SQLite snapshots and verifies every included scientific database. Restore creates a recovery backup first and requires typed confirmation.

If something fails, use Data & Settings → Diagnostics and preserve the previous working release until the issue is understood.
