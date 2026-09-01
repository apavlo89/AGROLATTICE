"""AGROLATTICE 11.19 Data & Settings Command Centre.

The module deliberately treats scientific databases/datasets as user-owned data.
Backup operations use SQLite's online backup API, restores are integrity checked,
and cache deletion is restricted to known reproducible cache folders.
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

import pandas as pd
import streamlit as st

from navigation_state import consume_view_request, queue_view_request

MODULE_VERSION = "1.1.0"
BACKUP_MANIFEST_VERSION = "1.0.0"


def _human_bytes(value: int | float) -> str:
    size = float(value or 0)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size) < 1024 or unit == "TB":
            return f"{size:,.1f} {unit}" if unit != "B" else f"{int(size):,} B"
        size /= 1024
    return f"{size:,.1f} TB"


def _folder_size(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except OSError:
                pass
    return total


def _sha256(path: Path, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def _sqlite_connect_ro(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True, timeout=30)


def _sqlite_info(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path), "exists": path.exists(), "size": path.stat().st_size if path.exists() else 0,
        "integrity": "missing", "foreign_keys": None, "schema_version": "Unknown", "tables": 0, "rows": 0,
        "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if path.exists() else None,
    }
    if not path.exists():
        return result
    try:
        with _sqlite_connect_ro(path) as conn:
            row = conn.execute("PRAGMA integrity_check").fetchone()
            result["integrity"] = str(row[0]) if row else "unknown"
            result["foreign_keys"] = len(conn.execute("PRAGMA foreign_key_check").fetchall())
            tables = [str(r[0]) for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()]
            result["tables"] = len(tables)
            total_rows = 0
            for table in tables:
                safe = table.replace('"', '""')
                try:
                    total_rows += int(conn.execute(f'SELECT COUNT(*) FROM "{safe}"').fetchone()[0])
                except sqlite3.Error:
                    pass
            result["rows"] = total_rows
            if "metadata" in tables:
                try:
                    hit = conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
                    if hit:
                        result["schema_version"] = str(hit[0])
                except sqlite3.Error:
                    pass
    except Exception as exc:
        result["integrity"] = f"ERROR: {type(exc).__name__}: {exc}"
    return result


def _sqlite_snapshot(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.unlink(missing_ok=True)
    with _sqlite_connect_ro(source) as src, sqlite3.connect(destination, timeout=30) as dst:
        src.backup(dst)
    info = _sqlite_info(destination)
    if str(info["integrity"]).casefold() != "ok" or int(info.get("foreign_keys") or 0) != 0:
        raise RuntimeError(f"Snapshot verification failed for {source.name}: {info}")


def _safe_extract_zip(blob: bytes, destination: Path) -> list[Path]:
    destination.mkdir(parents=True, exist_ok=True)
    extracted: list[Path] = []
    with zipfile.ZipFile(io.BytesIO(blob), "r") as zf:
        for member in zf.infolist():
            name = member.filename.replace("\\", "/")
            if not name or name.endswith("/"):
                continue
            rel = Path(name)
            if rel.is_absolute() or ".." in rel.parts:
                raise ValueError(f"Unsafe archive path: {name}")
            target = (destination / rel).resolve()
            if destination.resolve() not in target.parents:
                raise ValueError(f"Unsafe archive path: {name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member, "r") as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            extracted.append(target)
    return extracted


def _copy_tree_into_zip(zf: zipfile.ZipFile, source: Path, arc_root: str, manifest_files: list[dict[str, Any]]) -> None:
    if not source.exists():
        return
    for root, _, files in os.walk(source):
        for filename in files:
            path = Path(root) / filename
            if path.name.endswith(("-wal", "-shm")):
                continue
            rel = Path(arc_root) / path.relative_to(source)
            zf.write(path, rel.as_posix())
            manifest_files.append({"path": rel.as_posix(), "size": path.stat().st_size, "sha256": _sha256(path), "kind": "file"})


def create_backup_package(
    *,
    app_root: Path,
    app_version: str,
    database_paths: Mapping[str, Path],
    include_projects: bool = True,
    include_attachments: bool = True,
    include_report_assets: bool = True,
    include_climate: bool = False,
) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup_root = app_root / "system_backups"
    backup_root.mkdir(parents=True, exist_ok=True)
    destination = backup_root / f"AGROLATTICE_user_backup_{stamp}.zip"
    with tempfile.TemporaryDirectory(prefix="agrolattice_backup_") as td:
        stage = Path(td)
        manifest_files: list[dict[str, Any]] = []
        db_info: dict[str, Any] = {}
        for label, source in database_paths.items():
            source = Path(source)
            if not source.exists():
                continue
            target_rel = Path("databases") / source.relative_to(app_root)
            target = stage / target_rel
            _sqlite_snapshot(source, target)
            info = _sqlite_info(target)
            db_info[label] = {"relative_path": str(source.relative_to(app_root)).replace("\\", "/"), **info}
        manifest = {
            "manifest_version": BACKUP_MANIFEST_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "app_version": app_version,
            "backup_type": "AGROLATTICE user-data backup",
            "scientific_databases": db_info,
            "files": manifest_files,
            "includes": {
                "projects": include_projects,
                "attachments": include_attachments,
                "report_assets": include_report_assets,
                "climate_datasets": include_climate,
                "caches": False,
            },
        }
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for label, source in database_paths.items():
                source = Path(source)
                if not source.exists():
                    continue
                rel = Path("databases") / source.relative_to(app_root)
                staged = stage / rel
                zf.write(staged, rel.as_posix())
                manifest_files.append({"path": rel.as_posix(), "size": staged.stat().st_size, "sha256": _sha256(staged), "kind": "sqlite_snapshot", "label": label})
            for cfg in ("global_country_settings.json", "platform_settings.json", "analysis_presets.json", "analysis_history.json", "custom_crop_profiles.json"):
                p = app_root / cfg
                if p.exists():
                    zf.write(p, (Path("configuration") / cfg).as_posix())
                    manifest_files.append({"path": (Path("configuration") / cfg).as_posix(), "size": p.stat().st_size, "sha256": _sha256(p), "kind": "configuration"})
            if include_projects:
                _copy_tree_into_zip(zf, app_root / "project_store", "project_store", manifest_files)
                _copy_tree_into_zip(zf, app_root / "study_store", "study_store", manifest_files)
            if include_attachments:
                _copy_tree_into_zip(zf, app_root / "field_operations" / "attachments", "field_operations/attachments", manifest_files)
            if include_report_assets:
                _copy_tree_into_zip(zf, app_root / "reports" / "assets", "reports/assets", manifest_files)
            if include_climate:
                _copy_tree_into_zip(zf, app_root / "Datasets" / "countries", "Datasets/countries", manifest_files)
            zf.writestr("BACKUP_MANIFEST.json", json.dumps(manifest, indent=2, ensure_ascii=False))
    return destination


def validate_backup_package(blob: bytes, *, expected_databases: Mapping[str, Path], app_root: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="agrolattice_restore_validate_") as td:
        stage = Path(td)
        _safe_extract_zip(blob, stage)
        manifest_path = stage / "BACKUP_MANIFEST.json"
        if not manifest_path.exists():
            raise ValueError("This ZIP does not contain an AGROLATTICE BACKUP_MANIFEST.json.")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        files = manifest.get("files") or []
        failures: list[str] = []
        for item in files:
            rel = str(item.get("path") or "")
            path = stage / rel
            if not path.exists():
                failures.append(f"Missing {rel}")
                continue
            expected = str(item.get("sha256") or "")
            if expected and _sha256(path) != expected:
                failures.append(f"SHA-256 mismatch: {rel}")
        databases: list[dict[str, Any]] = []
        for label, live in expected_databases.items():
            rel = Path("databases") / Path(live).relative_to(app_root)
            source = stage / rel
            if source.exists():
                info = _sqlite_info(source)
                databases.append({"label": label, "archive_path": rel.as_posix(), **info})
                if str(info.get("integrity")).casefold() != "ok" or int(info.get("foreign_keys") or 0) != 0:
                    failures.append(f"SQLite validation failed: {label}")
        if not databases:
            failures.append("No recognised AGROLATTICE scientific databases were found in the backup.")
        return {"manifest": manifest, "databases": databases, "failures": failures}


def restore_databases_from_package(
    blob: bytes,
    *,
    app_root: Path,
    database_paths: Mapping[str, Path],
    app_version: str,
) -> Path:
    validation = validate_backup_package(blob, expected_databases=database_paths, app_root=app_root)
    if validation["failures"]:
        raise ValueError("Backup validation failed: " + "; ".join(validation["failures"]))
    # Independent pre-restore recovery package with current databases.
    recovery = create_backup_package(app_root=app_root, app_version=app_version, database_paths=database_paths, include_projects=False, include_attachments=False, include_report_assets=False, include_climate=False)
    with tempfile.TemporaryDirectory(prefix="agrolattice_restore_") as td:
        stage = Path(td)
        _safe_extract_zip(blob, stage)
        for label, live in database_paths.items():
            rel = Path("databases") / Path(live).relative_to(app_root)
            source = stage / rel
            if not source.exists():
                continue
            temp = Path(live).with_suffix(Path(live).suffix + ".restore")
            _sqlite_snapshot(source, temp)
            os.replace(temp, live)
            Path(str(live) + "-wal").unlink(missing_ok=True)
            Path(str(live) + "-shm").unlink(missing_ok=True)
            final = _sqlite_info(Path(live))
            if str(final["integrity"]).casefold() != "ok" or int(final.get("foreign_keys") or 0) != 0:
                raise RuntimeError(f"Post-restore verification failed for {label}.")
    return recovery


def _data_library_rows(app_root: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    climate_root = app_root / "Datasets" / "countries"
    if climate_root.exists():
        for file in sorted(climate_root.glob("*/agroclimate_longformat.csv")):
            rows.append({"Type": "Historical climate", "Name": file.parent.name, "Path": str(file.relative_to(app_root)), "Size": _human_bytes(file.stat().st_size), "Modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat(timespec="seconds")})
    for kind, rel in [
        ("NASA daily cache", "cache/nasa_power_daily"),
        ("Sentinel-2 cache", "cache/sentinel2_crop_monitoring"),
        ("Dataset update cache", "cache/nasa_power_dataset_updates"),
        ("Model artifacts", "models_evidence/artifacts"),
        ("Report assets", "reports/assets"),
        ("Field attachments", "field_operations/attachments"),
        ("External model runs", "external_model_runs"),
    ]:
        p = app_root / rel
        rows.append({"Type": kind, "Name": p.name, "Path": rel, "Size": _human_bytes(_folder_size(p)), "Modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds") if p.exists() else "—"})
    return pd.DataFrame(rows)


def _optional_packages() -> pd.DataFrame:
    packages = ["xgboost", "lightgbm", "catboost", "optuna", "shap", "torch", "tabpfn", "aquacrop", "rasterio", "pystac_client"]
    return pd.DataFrame([{"Package": p, "Installed": bool(importlib.util.find_spec(p))} for p in packages])


def render_data_settings_command_centre(
    *,
    app_root: str | Path,
    app_version: str,
    active_country: str,
    climate_file: str | Path,
    database_paths: Mapping[str, str | Path],
    settings_store: Any,
    performance_summary: Mapping[str, Any],
    stac_providers: Mapping[str, str] | None,
    nasa_endpoint: str,
    callbacks: Mapping[str, Callable[[], None]],
    clear_runtime_callback: Callable[[], None] | None = None,
    executable_status_callback: Callable[[str, str], Mapping[str, Any]] | None = None,
    runtime_profile_callback: Callable[[], pd.DataFrame] | None = None,
    runtime_clear_callback: Callable[[], None] | None = None,
    integration_audit_callback: Callable[[], pd.DataFrame] | None = None,
    workflow_chain_callback: Callable[[], pd.DataFrame] | None = None,
) -> None:
    app_root = Path(app_root)
    climate_file = Path(climate_file)
    db_paths = {str(k): Path(v) for k, v in database_paths.items()}
    views = ["Overview", "Data sources", "Data library", "Country climate", "Connections", "Databases & backups", "Performance & storage", "Integration & reliability", "Preferences", "Diagnostics", "Updates & migration"]
    consume_view_request(
        st.session_state,
        request_key="release11_16_settings_view_request",
        widget_key="release11_16_settings_view",
        options=views,
        default="Overview",
    )
    selected = st.selectbox("Data & Settings", views, key="release11_16_settings_view")
    st.divider()

    db_infos = {label: _sqlite_info(path) for label, path in db_paths.items()}
    healthy = sum(str(info.get("integrity")).casefold() == "ok" and int(info.get("foreign_keys") or 0) == 0 for info in db_infos.values())
    cache_root = app_root / "cache"

    if selected == "Overview":
        st.markdown("### Platform control centre")
        st.caption("Inspect the data and infrastructure AGROLATTICE is actually using. Scientific data are never deleted or replaced merely by opening this page.")
        cols = st.columns(5)
        cols[0].metric("Country", active_country)
        cols[1].metric("Historical climate", _human_bytes(climate_file.stat().st_size) if climate_file.exists() else "Not installed")
        cols[2].metric("Databases healthy", f"{healthy}/{len(db_infos)}")
        cols[3].metric("Cache storage", _human_bytes(_folder_size(cache_root)))
        cols[4].metric("System backups", len(list((app_root / "system_backups").glob("*.zip"))) if (app_root / "system_backups").exists() else 0)
        st.markdown("#### Attention")
        issues = []
        if not climate_file.exists() or climate_file.stat().st_size == 0:
            issues.append(f"No installed historical climate dataset for {active_country}.")
        for label, info in db_infos.items():
            if str(info.get("integrity")).casefold() != "ok" or int(info.get("foreign_keys") or 0) != 0:
                issues.append(f"{label}: database integrity needs review.")
        if not issues:
            st.success("Core persistent data stores pass lightweight health checks.")
        else:
            for issue in issues:
                st.warning(issue)
        st.markdown("#### Quick actions")
        q = st.columns(4)
        if q[0].button("Open Research Data Hub", width="stretch", key="r1116_ds_hub") and callbacks.get("data_hub"):
            callbacks["data_hub"]()
        if q[1].button("Update country climate", width="stretch", key="r1116_ds_update") and callbacks.get("dataset_updater"):
            callbacks["dataset_updater"]()
        if q[2].button("System diagnostics", width="stretch", key="r1116_ds_diag"):
            queue_view_request(st.session_state, request_key="release11_16_settings_view_request", target="Diagnostics")
            st.rerun()
        if q[3].button("Create backup", width="stretch", key="r1116_ds_backup"):
            queue_view_request(st.session_state, request_key="release11_16_settings_view_request", target="Databases & backups")
            st.rerun()
        return

    if selected == "Data sources":
        st.markdown("### Data sources")
        rows = [
            {"Source": "Installed historical agroclimate", "Status": "Ready" if climate_file.exists() and climate_file.stat().st_size else "Missing", "Scope": active_country, "Storage": _human_bytes(climate_file.stat().st_size) if climate_file.exists() else "—", "Type": "Retrieved/gridded monthly"},
            {"Source": "NASA POWER daily", "Status": "Available on explicit retrieval", "Scope": "Global point/field-centroid", "Storage": _human_bytes(_folder_size(app_root / 'cache/nasa_power_daily')), "Type": "Retrieved gridded daily"},
            {"Source": "Sentinel-2 Earth observation", "Status": "Available when optional EO dependencies/network are ready", "Scope": "Mapped field/AOI", "Storage": _human_bytes(_folder_size(app_root / 'cache/sentinel2_crop_monitoring')), "Type": "Retrieved EO"},
            {"Source": "Field Operations", "Status": "Ready" if db_paths.get('Field Operations', Path('x')).exists() else "Missing", "Scope": "Fields/seasons", "Storage": _human_bytes(db_infos.get('Field Operations', {}).get('size', 0)), "Type": "Measured/recorded"},
            {"Source": "Experiments", "Status": "Ready" if db_paths.get('Experiments', Path('x')).exists() else "Missing", "Scope": "Trial/EU/plant", "Storage": _human_bytes(db_infos.get('Experiments', {}).get('size', 0)), "Type": "Measured/derived"},
            {"Source": "Persistent Twin", "Status": "Ready" if db_paths.get('Persistent Twin', Path('x')).exists() else "Missing", "Scope": "Field/season/Twin", "Storage": _human_bytes(db_infos.get('Persistent Twin', {}).get('size', 0)), "Type": "Observed/modelled"},
            {"Source": "Research Evidence", "Status": "Ready" if db_paths.get('Research Evidence', Path('x')).exists() else "Missing", "Scope": "Datasets/models/predictions", "Storage": _human_bytes(db_infos.get('Research Evidence', {}).get('size', 0)), "Type": "Evidence/provenance"},
        ]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        st.info("AGROLATTICE keeps measured, retrieved, derived, modelled and forecast information distinguishable. Data availability does not imply equivalent spatial or temporal resolution.")
        return

    if selected == "Data library":
        st.markdown("### Data library")
        frame = _data_library_rows(app_root)
        query = st.text_input("Search library", placeholder="climate, Sentinel, model, attachment…", key="r1116_library_search")
        if query.strip():
            mask = frame.astype(str).apply(lambda c: c.str.contains(query, case=False, regex=False)).any(axis=1)
            frame = frame[mask]
        st.dataframe(frame, width="stretch", hide_index=True)
        st.caption("This inventory is metadata-only. It does not load the large climate CSVs or model artifacts into memory.")
        return

    if selected == "Country climate":
        st.markdown("### Country climate workspaces")
        rows = []
        root = app_root / "Datasets/countries"
        for file in sorted(root.glob("*/agroclimate_longformat.csv")) if root.exists() else []:
            rows.append({"Country workspace": file.parent.name, "Installed": file.stat().st_size > 0, "Size": _human_bytes(file.stat().st_size), "Active": file.resolve() == climate_file.resolve()})
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        st.caption("All countries use the same canonical country-scoped storage layout; global functions must not assume Mexico.")
        cols = st.columns(2)
        if cols[0].button("Open country workspace", width="stretch", key="r1116_country_ws") and callbacks.get("country_workspace"):
            callbacks["country_workspace"]()
        if cols[1].button("Open dataset updater", width="stretch", key="r1116_country_update") and callbacks.get("dataset_updater"):
            callbacks["dataset_updater"]()
        return

    if selected == "Connections":
        st.markdown("### Connections & optional backends")
        st.caption("Network services are contacted only when you explicitly run a retrieval/test. Merely opening Data & Settings does not make external requests.")
        st.markdown("#### Environmental data")
        st.code(nasa_endpoint, language="text")
        if stac_providers:
            st.dataframe(pd.DataFrame([{"Provider": k, "Endpoint": v} for k, v in stac_providers.items()]), width="stretch", hide_index=True)
        st.markdown("#### Optional Python research stack")
        st.dataframe(_optional_packages(), width="stretch", hide_index=True)
        prefs = settings_store.load()
        conn = prefs.get("connections", {})
        st.markdown("#### External crop-model executables")
        c = st.columns(2)
        dssat_path = c[0].text_input("DSSAT executable", value=str(conn.get("dssat_executable") or ""), key="r1116_dssat_path")
        apsim_path = c[1].text_input("APSIM executable", value=str(conn.get("apsim_executable") or ""), key="r1116_apsim_path")
        if st.button("Save executable paths", type="primary", key="r1116_save_exec"):
            settings_store.update_section("connections", {"dssat_executable": dssat_path.strip(), "apsim_executable": apsim_path.strip()})
            st.success("Connection preferences saved. No external model was executed.")
        if executable_status_callback:
            rows = []
            for model, path in (("DSSAT", dssat_path), ("APSIM", apsim_path)):
                try:
                    status = dict(executable_status_callback(path, model)) if path.strip() else {"exists": False}
                except Exception as exc:
                    status = {"exists": False, "error": str(exc)}
                rows.append({"Model": model, "Configured": bool(path.strip()), "Available": bool(status.get("exists") or status.get("ready") or status.get("available")), "Path": path or "—", "Detail": status.get("error") or status.get("message") or ""})
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        return

    if selected == "Databases & backups":
        st.markdown("### Databases & backups")
        st.caption("Scientific SQLite databases are user data. Backups use SQLite snapshots so committed WAL content is included and verified.")
        db_frame = pd.DataFrame([{"Database": label, "Schema": info.get("schema_version"), "Integrity": info.get("integrity"), "FK issues": info.get("foreign_keys"), "Tables": info.get("tables"), "Rows": info.get("rows"), "Size": _human_bytes(info.get("size", 0)), "Modified": info.get("modified")} for label, info in db_infos.items()])
        st.dataframe(db_frame, width="stretch", hide_index=True)
        st.markdown("#### Create backup")
        opts = st.columns(4)
        inc_projects = opts[0].checkbox("Projects/studies", value=True, key="r1116_bk_projects")
        inc_attach = opts[1].checkbox("Attachments", value=True, key="r1116_bk_attach")
        inc_reports = opts[2].checkbox("Report assets", value=True, key="r1116_bk_reports")
        inc_climate = opts[3].checkbox("Climate datasets", value=False, key="r1116_bk_climate", help="Can make the backup hundreds of MB or larger. Climate data can normally be retrieved again.")
        if inc_climate:
            st.warning("Climate datasets are large. Mexico alone may add hundreds of MB. Reproducible caches are still excluded.")
        if st.button("Create verified backup package", type="primary", key="r1116_create_backup"):
            with st.spinner("Creating SQLite-consistent backup…"):
                path = create_backup_package(app_root=app_root, app_version=app_version, database_paths=db_paths, include_projects=inc_projects, include_attachments=inc_attach, include_report_assets=inc_reports, include_climate=inc_climate)
            st.session_state.r1116_last_backup = str(path)
            st.success(f"Backup created: {path.name}")
        last = st.session_state.get("r1116_last_backup")
        if last and Path(last).exists():
            p = Path(last)
            st.download_button("Download latest backup", data=p.read_bytes(), file_name=p.name, mime="application/zip", key="r1116_download_backup")
        st.markdown("#### Restore scientific databases")
        st.warning("Restore replaces only recognised scientific SQLite databases. AGROLATTICE first creates a recovery backup of the current databases. Climate datasets, attachments and caches are not overwritten by this restore tool.")
        uploaded = st.file_uploader("AGROLATTICE backup ZIP", type=["zip"], key="r1116_restore_upload")
        if uploaded is not None:
            blob = uploaded.getvalue()
            try:
                validation = validate_backup_package(blob, expected_databases=db_paths, app_root=app_root)
                backup_version = str(validation.get("manifest", {}).get("app_version") or "")
                version_mismatch = bool(backup_version and backup_version != app_version)
                if validation["failures"]:
                    st.error("Backup cannot be restored: " + "; ".join(validation["failures"]))
                elif version_mismatch:
                    st.error(f"This backup was created by {backup_version}. The in-app restore control only restores same-release database snapshots. Use MIGRATE_USER_DATA_FROM_EXISTING_APP.bat for cross-release migration.")
                else:
                    st.success("Backup hashes and SQLite integrity checks passed.")
                    st.dataframe(pd.DataFrame(validation["databases"])[["label", "schema_version", "tables", "rows", "size", "integrity", "foreign_keys"]], width="stretch", hide_index=True)
                    confirmation = st.text_input("Type RESTORE to confirm database replacement", key="r1116_restore_confirm")
                    if st.button("Restore databases", disabled=confirmation != "RESTORE", type="primary", key="r1116_restore_go"):
                        recovery = restore_databases_from_package(blob, app_root=app_root, database_paths=db_paths, app_version=app_version)
                        if clear_runtime_callback:
                            clear_runtime_callback()
                        st.success(f"Restore completed. Pre-restore recovery backup: {recovery.name}. The app will rerun using restored stores.")
                        st.rerun()
            except Exception as exc:
                st.error(f"Backup validation failed: {type(exc).__name__}: {exc}")
        return

    if selected == "Performance & storage":
        st.markdown("### Performance & storage")
        cols = st.columns(5)
        cols[0].metric("Active climate source", _human_bytes(int(performance_summary.get("source_size_mb", 0) * 1024 * 1024)))
        cols[1].metric("Climate rows", f"{int(performance_summary.get('rows', 0)):,}")
        cols[2].metric("Mapped rows", f"{int(performance_summary.get('matched_rows', 0)):,}")
        cols[3].metric("Variables", f"{int(performance_summary.get('variables', 0)):,}")
        cols[4].metric("Cache storage", _human_bytes(_folder_size(cache_root)))
        cache_rows = []
        for name, rel in [("NASA daily weather", "cache/nasa_power_daily"), ("Sentinel-2", "cache/sentinel2_crop_monitoring"), ("Dataset updater downloads", "cache/nasa_power_dataset_updates")]:
            p = app_root / rel
            cache_rows.append({"Cache": name, "Path": rel, "Size": _human_bytes(_folder_size(p)), "Files": sum(len(files) for _, _, files in os.walk(p)) if p.exists() else 0})
        cache_rows.append({"Cache": "Similarity/derived cache root", "Path": "cache", "Size": _human_bytes(_folder_size(cache_root)), "Files": sum(len(files) for _, _, files in os.walk(cache_root)) if cache_root.exists() else 0})
        st.dataframe(pd.DataFrame(cache_rows), width="stretch", hide_index=True)
        st.markdown("#### Session page-performance profile")
        st.caption("Release 11.19 times top-level workspace renders in this browser session. These timings are diagnostic observations, not benchmark guarantees; network/model actions can dominate a page when you explicitly run them.")
        profile = runtime_profile_callback() if runtime_profile_callback else pd.DataFrame()
        if isinstance(profile, pd.DataFrame) and not profile.empty:
            st.dataframe(profile, width="stretch", hide_index=True)
            slow = profile.loc[pd.to_numeric(profile.get("P95 ms"), errors="coerce").ge(2000)] if "P95 ms" in profile else pd.DataFrame()
            if not slow.empty:
                st.warning(f"{len(slow)} page(s) have session P95 render time ≥2 s. Review whether the delay came from page entry or an explicit heavy action before optimising.")
        else:
            st.info("No page timings have been recorded yet in this session. Navigate through several workspaces and return here.")
        if runtime_clear_callback and st.button("Clear session performance history", key="r1118_clear_profile"):
            runtime_clear_callback()
            st.success("Session performance history cleared. Scientific data were not touched.")
            st.rerun()
        st.markdown("#### Safe cache cleanup")
        st.caption("Only reproducible cache files are eligible here. Scientific databases, field attachments, model artifacts and installed historical climate datasets are never included.")
        clear_daily = st.checkbox("NASA daily cache", value=False, key="r1116_clear_daily")
        clear_sat = st.checkbox("Sentinel-2 cache", value=False, key="r1116_clear_sat")
        clear_update = st.checkbox("Dataset updater download cache", value=False, key="r1116_clear_update")
        confirm = st.text_input("Type CLEAR CACHE to enable deletion", key="r1116_clear_confirm")
        if st.button("Clear selected caches", disabled=confirm != "CLEAR CACHE" or not any((clear_daily, clear_sat, clear_update)), key="r1116_clear_cache"):
            for chosen, rel in ((clear_daily, "cache/nasa_power_daily"), (clear_sat, "cache/sentinel2_crop_monitoring"), (clear_update, "cache/nasa_power_dataset_updates")):
                if chosen:
                    p = app_root / rel
                    if p.exists():
                        shutil.rmtree(p)
                    p.mkdir(parents=True, exist_ok=True)
            if clear_runtime_callback:
                clear_runtime_callback()
            st.success("Selected reproducible caches cleared. Scientific records were not touched.")
            st.rerun()
        return

    if selected == "Integration & reliability":
        st.markdown("### Integration & reliability")
        st.caption("Audit the persistent hand-offs between Fields → Experiments → Twin → Models/Evidence → Reports. These checks validate references and workflow continuity; they do not certify scientific validity or model performance.")
        st.markdown("#### Active workflow chain")
        chain = workflow_chain_callback() if workflow_chain_callback else pd.DataFrame()
        if isinstance(chain, pd.DataFrame) and not chain.empty:
            st.dataframe(chain, width="stretch", hide_index=True)
            ready = int(chain.get("Status", pd.Series(dtype=str)).astype(str).eq("Ready").sum()) if "Status" in chain else 0
            st.caption(f"{ready}/{len(chain)} persisted workflow stages currently have linked evidence in the active context. Missing stages can be scientifically legitimate depending on study phase.")
        else:
            st.info("Select an active field and/or experiment to inspect the end-to-end evidence chain.")
        st.markdown("#### Cross-workspace reference audit")
        st.caption("Run this after upgrades, restores, geometry edits or when a cross-tab link appears inconsistent. It reads database metadata/references only and does not modify records.")
        if st.button("Run integration audit", type="primary", key="r1118_run_integration_audit"):
            try:
                result = integration_audit_callback() if integration_audit_callback else pd.DataFrame()
                st.session_state["r1118_integration_audit"] = result
            except Exception as exc:
                st.error(f"Integration audit failed: {type(exc).__name__}: {exc}")
        audit = st.session_state.get("r1118_integration_audit")
        if isinstance(audit, pd.DataFrame) and not audit.empty:
            st.dataframe(audit, width="stretch", hide_index=True)
            failures = audit["Status"].astype(str).isin(["FAIL", "WARN"]).sum() if "Status" in audit else 0
            if failures:
                st.warning(f"Audit found {int(failures)} warning/failure row(s). Review the details before assuming a cross-workspace result is complete.")
            else:
                st.success("Cross-workspace reference checks passed.")
        with st.expander("What this audit does and does not prove", expanded=False):
            st.markdown("""- Checks SQLite integrity and foreign keys.
- Checks Trial → authoritative Field links and detects changed field-geometry snapshots.
- Checks Twin → Field/Trial references.
- Checks Research Evidence field/trial/experimental-unit references.
- Checks explicit report scope references.
- **Does not** prove causal validity, agronomic correctness, sensor accuracy, model calibration or external generalisation.""")
        return

    if selected == "Preferences":
        st.markdown("### Preferences")
        prefs = settings_store.load()
        workspace = prefs.get("workspace", {})
        role_options = ["Agronomist", "Researcher", "Field technician", "Administrator", "All tools"]
        default_role = st.selectbox("Default workspace preset", role_options, index=role_options.index(workspace.get("default_role", "Researcher")) if workspace.get("default_role", "Researcher") in role_options else 1, key="r1116_pref_role")
        show_advanced = st.checkbox("Show advanced tools by default in the catalogue", value=bool(workspace.get("show_advanced_tools", False)), key="r1116_pref_advanced")
        if st.button("Save preferences", type="primary", key="r1116_save_prefs"):
            settings_store.update_section("workspace", {"default_role": default_role, "show_advanced_tools": show_advanced})
            st.session_state.release10_workspace_preset = default_role
            st.success("Preferences saved and applied to this session.")
        st.caption("Preferences change navigation emphasis only. They never hide scientific data or remove tools.")
        return

    if selected == "Diagnostics":
        st.markdown("### Diagnostics")
        st.caption("Full technical diagnostics remain available here rather than being repeated across scientific workspaces.")
        if callbacks.get("diagnostics"):
            callbacks["diagnostics"]()
        return

    if selected == "Updates & migration":
        st.markdown("### Updates & migration")
        st.info("AGROLATTICE upgrades should be backup-first. A newer release must preserve existing user data and migrate schemas explicitly when required.")
        rows = [{"Database": label, "Schema": info.get("schema_version"), "Integrity": info.get("integrity"), "Path": str(Path(path).relative_to(app_root))} for (label, path), info in zip(db_paths.items(), db_infos.values())]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        migration = app_root / "MIGRATE_USER_DATA_FROM_EXISTING_APP.bat"
        st.markdown("#### Existing-installation migration")
        st.caption("Use the bundled migration tool when moving user data from another AGROLATTICE installation into this release. It validates source databases, snapshots destination databases, stages replacements, verifies row counts, and rolls back database replacements if activation fails.")
        st.code(str(migration.name), language="text")
        cols = st.columns(2)
        if cols[0].button("Open Dataset updater", width="stretch", key="r1116_update_data") and callbacks.get("dataset_updater"):
            callbacks["dataset_updater"]()
        if cols[1].button("Open release notes", width="stretch", key="r1116_release_notes") and callbacks.get("release_notes"):
            callbacks["release_notes"]()
        return
