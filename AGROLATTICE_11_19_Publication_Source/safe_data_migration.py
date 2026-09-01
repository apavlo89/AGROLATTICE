"""Backup-first user-data migration for AGROLATTICE 11.19.

The user explicitly selects an older/current working AGROLATTICE folder as the
source of truth. Research SQLite databases are copied using SQLite's online
backup API (so committed WAL content is included), verified before replacement,
and the packaged destination databases are backed up first.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable

RELEASE = "AGROLATTICE 11.19"
RESEARCH_DATABASES = (
    Path("field_operations/field_operations.sqlite"),
    Path("pollination_lab/maize_flowering_trials.sqlite"),
    Path("agrolattice_twin/agrolattice_twin.sqlite"),
    Path("models_evidence/research_evidence.sqlite"),
    Path("models_evidence/crop_profiles.sqlite"),
    Path("reports/reporting.sqlite"),
)
MERGE_DIRECTORIES = (
    "Datasets",
    "project_store",
    "study_store",
    "reports/assets",
    "cache",
    "dataset_updates",
    "external_model_runs",
    "satellite_exports",
    "system_backups",
)
SPECIAL_DIRECTORIES = ("pollination_lab", "field_operations", "agrolattice_twin", "models_evidence", "reports")
CONFIG_FILES = (
    "analysis_history.json",
    "custom_crop_profiles.json",
    "analysis_presets.json",
    "global_country_settings.json",
    "platform_settings.json",
)


class MigrationError(RuntimeError):
    pass


def _connect_ro(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True, timeout=30)


def integrity_check(path: Path) -> None:
    try:
        with _connect_ro(path) as conn:
            result = conn.execute("PRAGMA integrity_check").fetchone()
            if not result or str(result[0]).lower() != "ok":
                raise MigrationError(f"SQLite integrity_check failed for {path}: {result}")
            fk = conn.execute("PRAGMA foreign_key_check").fetchall()
            if fk:
                raise MigrationError(f"SQLite foreign_key_check found {len(fk)} issue(s) in {path}.")
    except sqlite3.Error as exc:
        raise MigrationError(f"Could not validate SQLite database {path}: {exc}") from exc


def table_counts(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    with _connect_ro(path) as conn:
        tables = [
            str(row[0])
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
        ]
        for table in tables:
            safe = table.replace('"', '""')
            counts[table] = int(conn.execute(f'SELECT COUNT(*) FROM "{safe}"').fetchone()[0])
    return counts


def sqlite_snapshot(source: Path, destination: Path) -> None:
    """Create a consistent database snapshot, including committed WAL content."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    try:
        with _connect_ro(source) as src, sqlite3.connect(destination, timeout=30) as dst:
            src.backup(dst)
    except sqlite3.Error as exc:
        raise MigrationError(f"Could not snapshot {source}: {exc}") from exc
    integrity_check(destination)


def copy_tree(source: Path, destination: Path, *, exclude_sqlite: bool = False) -> None:
    if not source.exists():
        return
    destination.mkdir(parents=True, exist_ok=True)
    for root, dirs, files in os.walk(source):
        root_path = Path(root)
        relative = root_path.relative_to(source)
        target_root = destination / relative
        target_root.mkdir(parents=True, exist_ok=True)
        for filename in files:
            lower = filename.lower()
            if exclude_sqlite and (lower.endswith(".sqlite") or lower.endswith(".sqlite-wal") or lower.endswith(".sqlite-shm")):
                continue
            src = root_path / filename
            dst = target_root / filename
            shutil.copy2(src, dst)


def backup_regular_file(path: Path, backup_root: Path, relative: Path) -> None:
    if not path.exists():
        return
    target = backup_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)


def migrate(source_root: Path, destination_root: Path) -> Path:
    source_root = source_root.expanduser().resolve()
    destination_root = destination_root.expanduser().resolve()
    if not source_root.is_dir():
        raise MigrationError(f"Source folder does not exist: {source_root}")
    if source_root == destination_root:
        raise MigrationError("Source and destination are the same folder; nothing was changed.")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = destination_root / "migration_backups" / f"before_11_19_{stamp}"
    backup_root.mkdir(parents=True, exist_ok=False)
    report: dict[str, object] = {
        "release": RELEASE,
        "source": str(source_root),
        "destination": str(destination_root),
        "backup": str(backup_root),
        "research_databases": [],
        "merged_directories": [],
        "config_files": [],
    }

    # Validate all available source research databases before changing the destination.
    available_sources: list[Path] = []
    for relative in RESEARCH_DATABASES:
        src = source_root / relative
        if src.exists():
            integrity_check(src)
            available_sources.append(relative)
    if not available_sources:
        raise MigrationError(
            "No AGROLATTICE research SQLite databases were found in the selected source. "
            "Check that you selected the root of the working app folder."
        )

    # Back up current destination state first. SQLite snapshots include committed WAL data.
    for relative in RESEARCH_DATABASES:
        dst = destination_root / relative
        if dst.exists():
            sqlite_snapshot(dst, backup_root / "destination_before" / relative)
    for filename in CONFIG_FILES:
        backup_regular_file(destination_root / filename, backup_root, Path("destination_before") / filename)

    # Keep an independent source snapshot as migration evidence/recovery material and
    # stage *all* database replacements before changing any active destination DB.
    source_counts_by_relative: dict[Path, dict[str, int]] = {}
    for relative in available_sources:
        src = source_root / relative
        snapshot = backup_root / "source_snapshot" / relative
        source_counts = table_counts(src)
        sqlite_snapshot(src, snapshot)
        if table_counts(snapshot) != source_counts:
            raise MigrationError(f"Row-count verification failed while staging {relative}.")
        source_counts_by_relative[relative] = source_counts

    replaced: list[Path] = []
    try:
        for relative in available_sources:
            dst = destination_root / relative
            staged = backup_root / "source_snapshot" / relative
            dst.parent.mkdir(parents=True, exist_ok=True)
            temp = dst.with_suffix(dst.suffix + ".migrating")
            shutil.copy2(staged, temp)
            integrity_check(temp)
            os.replace(temp, dst)
            replaced.append(relative)
            for suffix in ("-wal", "-shm"):
                Path(str(dst) + suffix).unlink(missing_ok=True)
            integrity_check(dst)
            final_counts = table_counts(dst)
            source_counts = source_counts_by_relative[relative]
            if final_counts != source_counts:
                raise MigrationError(f"Post-replacement row-count verification failed for {relative}.")
            report["research_databases"].append({
                "path": str(relative),
                "tables": source_counts,
                "status": "migrated_from_selected_source",
            })
    except Exception as replacement_error:
        rollback_errors: list[str] = []
        for relative in reversed(replaced):
            dst = destination_root / relative
            previous = backup_root / "destination_before" / relative
            try:
                if previous.exists():
                    rollback_temp = dst.with_suffix(dst.suffix + ".rollback")
                    shutil.copy2(previous, rollback_temp)
                    integrity_check(rollback_temp)
                    os.replace(rollback_temp, dst)
                else:
                    dst.unlink(missing_ok=True)
                for suffix in ("-wal", "-shm"):
                    Path(str(dst) + suffix).unlink(missing_ok=True)
            except Exception as rollback_error:
                rollback_errors.append(f"{relative}: {rollback_error}")
        detail = f" Research-database rollback issues: {'; '.join(rollback_errors)}" if rollback_errors else " Research databases were rolled back to their pre-migration state."
        raise MigrationError(f"Research database activation failed: {replacement_error}.{detail}") from replacement_error

    # Merge user-owned data folders. Source files win because the user explicitly selected it as the working app.
    for dirname in MERGE_DIRECTORIES:
        src = source_root / dirname
        if src.exists():
            copy_tree(src, destination_root / dirname)
            report["merged_directories"].append(dirname)
    for dirname in SPECIAL_DIRECTORIES:
        src = source_root / dirname
        if src.exists():
            copy_tree(src, destination_root / dirname, exclude_sqlite=True)
            report["merged_directories"].append(f"{dirname} (non-SQLite files)")

    for filename in CONFIG_FILES:
        src = source_root / filename
        if src.exists():
            shutil.copy2(src, destination_root / filename)
            report["config_files"].append(filename)

    report_path = backup_root / "migration_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return backup_root


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"{RELEASE} safe user-data migration")
    parser.add_argument("source", type=Path, help="Existing working AGROLATTICE app folder")
    parser.add_argument("--destination", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--confirmed", action="store_true", help="Acknowledge source-authoritative migration")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if not args.confirmed:
        print("ERROR: migration requires explicit confirmation (--confirmed).", file=sys.stderr)
        return 2
    try:
        backup = migrate(args.source, args.destination)
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"Migration completed successfully. Safety backup: {backup}")
    print("Selected source research databases are now active in AGROLATTICE 11.19 and passed integrity/row-count verification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
