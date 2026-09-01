# AGROLATTICE 11.16 — Platform Control Centre technical basis

## Scope
Release 11.16 modernises Data & Settings and All Tools without altering the scientific models or protected database schemas.

## Backup design
Scientific SQLite stores may use WAL mode; raw file copying while the app is active can therefore miss committed WAL content. The 11.16 backup centre uses `sqlite3.Connection.backup()` to produce consistent snapshots, then runs `PRAGMA integrity_check` and `PRAGMA foreign_key_check`. File SHA-256 hashes are stored in `BACKUP_MANIFEST.json`.

Restore is deliberately narrower than full-version migration. Only recognised scientific SQLite databases are restored. Before replacement, AGROLATTICE creates a current-state recovery backup. Uploaded archives are path-sanitised, hashes are checked, staged SQLite files are integrity checked, and typed confirmation is required.

## Cache boundary
The safe cache cleaner only targets reproducible cache directories:
- `cache/nasa_power_daily`
- `cache/sentinel2_crop_monitoring`
- `cache/nasa_power_dataset_updates`

It never targets installed climate datasets, field attachments, model artifacts, reports or scientific SQLite stores.

## Data-library performance
The library is filesystem-metadata based. It reports file/folder sizes and modification times without parsing large historical climate CSVs or loading model artifacts.

## Tool catalogue
The catalogue retains all existing tools. Search uses name, workspace, description, maturity and data-requirement text. Primary/Advanced/Legacy are navigation labels only; they do not alter scientific behaviour. Favourites/recent tools are stored in the small `platform_settings.json` preference file.

## Scientific integrity
No evidence type is changed by this release. Retrieved climate/EO, measured field observations, model outputs and recommendations remain distinct. No network retrieval occurs merely because Data & Settings opens.
