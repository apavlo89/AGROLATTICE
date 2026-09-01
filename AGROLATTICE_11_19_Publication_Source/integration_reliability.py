"""AGROLATTICE 11.19 integration reliability and runtime profiling helpers.

The module is intentionally independent of Streamlit and the scientific model stack.
It performs lightweight SQLite metadata/reference checks and keeps bounded in-session
runtime events. It never writes scientific databases and never runs models, remote
retrievals, EO processing, or large climate-table scans.
"""
from __future__ import annotations

import json
import math
import sqlite3
import time
from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import Any, Callable

import pandas as pd

MODULE_VERSION = "1.0.0"
PROFILE_EVENT_LIMIT = 250


def utc_timestamp() -> str:
    return pd.Timestamp.now(tz="UTC").isoformat()


def append_runtime_event(
    state: MutableMapping[str, Any],
    *,
    page: str,
    elapsed_seconds: float,
    status: str = "ok",
    detail: str = "",
    key: str = "release11_18_runtime_events",
    limit: int = PROFILE_EVENT_LIMIT,
) -> None:
    events = list(state.get(key) or [])
    events.append({
        "timestamp": utc_timestamp(),
        "page": str(page),
        "elapsed_ms": round(max(0.0, float(elapsed_seconds)) * 1000.0, 3),
        "status": str(status),
        "detail": str(detail or "")[:600],
    })
    state[key] = events[-max(10, int(limit)):]


def profile_call(state: MutableMapping[str, Any], page: str, function: Callable[[], Any]) -> Any:
    start = time.perf_counter()
    status = "ok"
    detail = ""
    try:
        return function()
    except BaseException as exc:
        exc_name = type(exc).__name__
        # Streamlit uses exceptions for normal control flow (rerun/stop). Record them
        # without inflating the reliability error count, while still re-raising exactly
        # as Streamlit expects. This module deliberately avoids importing Streamlit.
        if exc_name in {"RerunException", "StopException"} or "Rerun" in exc_name:
            status = "control"
        else:
            status = "error"
        detail = f"{exc_name}: {exc}"
        raise
    finally:
        append_runtime_event(
            state,
            page=page,
            elapsed_seconds=time.perf_counter() - start,
            status=status,
            detail=detail,
        )


def runtime_events_frame(state: Mapping[str, Any], key: str = "release11_18_runtime_events") -> pd.DataFrame:
    frame = pd.DataFrame(list(state.get(key) or []))
    if frame.empty:
        return pd.DataFrame(columns=["timestamp", "page", "elapsed_ms", "status", "detail"])
    frame["elapsed_ms"] = pd.to_numeric(frame.get("elapsed_ms"), errors="coerce")
    return frame


def runtime_profile_summary(events: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(events, pd.DataFrame) or events.empty:
        return pd.DataFrame(columns=["Page", "Runs", "Median ms", "P95 ms", "Max ms", "Errors", "Last run"])
    rows: list[dict[str, Any]] = []
    for page, group in events.groupby(events["page"].astype(str), dropna=False):
        vals = pd.to_numeric(group["elapsed_ms"], errors="coerce").dropna()
        rows.append({
            "Page": str(page),
            "Runs": int(len(group)),
            "Median ms": round(float(vals.median()), 1) if not vals.empty else math.nan,
            "P95 ms": round(float(vals.quantile(0.95)), 1) if not vals.empty else math.nan,
            "Max ms": round(float(vals.max()), 1) if not vals.empty else math.nan,
            "Errors": int(group["status"].astype(str).str.casefold().eq("error").sum()),
            "Last run": str(group.iloc[-1].get("timestamp") or ""),
        })
    return pd.DataFrame(rows).sort_values(["P95 ms", "Page"], ascending=[False, True], na_position="last").reset_index(drop=True)


def clear_runtime_profile(state: MutableMapping[str, Any], key: str = "release11_18_runtime_events") -> None:
    state.pop(key, None)


def _connect_ro(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True, timeout=30)


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (str(table),)).fetchone() is not None


def _count(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> int:
    row = conn.execute(sql, params).fetchone()
    return int(row[0] or 0) if row else 0


def _read_ids(conn: sqlite3.Connection, table: str, column: str) -> set[str]:
    if not _table_exists(conn, table):
        return set()
    return {str(r[0]) for r in conn.execute(f'SELECT "{column}" FROM "{table}" WHERE "{column}" IS NOT NULL').fetchall()}


def _status_row(check: str, status: str, severity: str, count: int, detail: str, scope: str) -> dict[str, Any]:
    return {"Scope": scope, "Check": check, "Status": status, "Severity": severity, "Count": int(count), "Detail": detail}


def cross_workspace_integrity(database_paths: Mapping[str, str | Path]) -> pd.DataFrame:
    """Audit cross-database references without modifying user data.

    This is deliberately a referential/integration audit, not a scientific validity audit.
    """
    paths = {str(k): Path(v) for k, v in database_paths.items()}
    rows: list[dict[str, Any]] = []

    # Database-local integrity first.
    for label, path in paths.items():
        if not path.exists():
            rows.append(_status_row("SQLite database present", "FAIL", "Critical", 1, f"Missing: {path}", label))
            continue
        try:
            with _connect_ro(path) as conn:
                integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
                fk = len(conn.execute("PRAGMA foreign_key_check").fetchall())
            ok = integrity.casefold() == "ok" and fk == 0
            rows.append(_status_row("SQLite integrity & foreign keys", "PASS" if ok else "FAIL", "Critical" if not ok else "Info", fk, f"integrity={integrity}; foreign_key_issues={fk}", label))
        except Exception as exc:
            rows.append(_status_row("SQLite integrity & foreign keys", "FAIL", "Critical", 1, f"{type(exc).__name__}: {exc}", label))

    field_path = paths.get("Field Operations")
    trial_path = paths.get("Experiments")
    twin_path = paths.get("Persistent Twin")
    evidence_path = paths.get("Research Evidence")
    report_path = paths.get("Reporting")
    if not all(p and p.exists() for p in (field_path, trial_path, twin_path, evidence_path)):
        return pd.DataFrame(rows)

    with _connect_ro(field_path) as fc, _connect_ro(trial_path) as tc, _connect_ro(twin_path) as twc, _connect_ro(evidence_path) as ec:
        fields = _read_ids(fc, "fields", "field_id")
        trials = _read_ids(tc, "trials", "trial_id")
        plots = _read_ids(tc, "plots", "plot_id")

        # Trial -> authoritative field.
        trial_refs = tc.execute("SELECT trial_id, source_field_id, source_field_geometry_hash FROM trials WHERE source_field_id IS NOT NULL AND TRIM(source_field_id)<>''").fetchall()
        missing = [(tid, fid) for tid, fid, _ in trial_refs if str(fid) not in fields]
        rows.append(_status_row("Trials reference existing authoritative fields", "PASS" if not missing else "FAIL", "Critical" if missing else "Info", len(missing), "All mapped trials resolve to a Field Operations field." if not missing else f"Missing field references: {missing[:5]}", "Experiments → Fields"))

        # Detect field geometry changes after trial mapping.
        field_hash = {str(r[0]): str(r[1] or "") for r in fc.execute("SELECT field_id, geometry_hash FROM fields").fetchall()}
        stale = [(str(tid), str(fid)) for tid, fid, saved_hash in trial_refs if str(fid) in field_hash and str(saved_hash or "") and field_hash[str(fid)] and str(saved_hash) != field_hash[str(fid)]]
        rows.append(_status_row("Trial field-geometry snapshot matches authoritative field", "PASS" if not stale else "WARN", "Warning" if stale else "Info", len(stale), "No mapped trial has a stale field-boundary snapshot." if not stale else f"Field geometry changed after trial linkage for {len(stale)} trial(s). Review spatial layout before field work.", "Experiments → Fields"))

        # Twin link -> field/trial.
        twin_refs = twc.execute("SELECT link_id, field_id, trial_id FROM twin_links").fetchall() if _table_exists(twc, "twin_links") else []
        bad_field = [(lid, fid) for lid, fid, _ in twin_refs if fid not in (None, "") and str(fid) not in fields]
        bad_trial = [(lid, tid) for lid, _, tid in twin_refs if tid not in (None, "") and str(tid) not in trials]
        rows.append(_status_row("Twin links resolve to fields", "PASS" if not bad_field else "FAIL", "Critical" if bad_field else "Info", len(bad_field), "All Twin field links resolve." if not bad_field else f"Broken Twin field links: {bad_field[:5]}", "Twin → Fields"))
        rows.append(_status_row("Twin links resolve to trials", "PASS" if not bad_trial else "FAIL", "Critical" if bad_trial else "Info", len(bad_trial), "All Twin trial links resolve." if not bad_trial else f"Broken Twin trial links: {bad_trial[:5]}", "Twin → Experiments"))

        # Research evidence context references.
        for table in ("observations", "predictions", "recommendations", "treatment_outcomes"):
            if not _table_exists(ec, table):
                continue
            cols = {str(r[1]) for r in ec.execute(f'PRAGMA table_info("{table}")').fetchall()}
            if "field_id" in cols:
                refs = [str(r[0]) for r in ec.execute(f'SELECT DISTINCT field_id FROM "{table}" WHERE field_id IS NOT NULL AND TRIM(field_id)<>\'\'').fetchall()]
                bad = [value for value in refs if value not in fields]
                rows.append(_status_row(f"{table} field references resolve", "PASS" if not bad else "WARN", "Warning" if bad else "Info", len(bad), "All field references resolve." if not bad else f"Unresolved field IDs: {bad[:5]}", f"Evidence/{table}"))
            if "trial_id" in cols:
                refs = [str(r[0]) for r in ec.execute(f'SELECT DISTINCT trial_id FROM "{table}" WHERE trial_id IS NOT NULL AND TRIM(trial_id)<>\'\'').fetchall()]
                bad = [value for value in refs if value not in trials]
                rows.append(_status_row(f"{table} trial references resolve", "PASS" if not bad else "WARN", "Warning" if bad else "Info", len(bad), "All trial references resolve." if not bad else f"Unresolved trial IDs: {bad[:5]}", f"Evidence/{table}"))
            if "experimental_unit_id" in cols:
                refs = [str(r[0]) for r in ec.execute(f'SELECT DISTINCT experimental_unit_id FROM "{table}" WHERE experimental_unit_id IS NOT NULL AND TRIM(experimental_unit_id)<>\'\'').fetchall()]
                bad = [value for value in refs if value not in plots]
                rows.append(_status_row(f"{table} experimental-unit references resolve", "PASS" if not bad else "WARN", "Warning" if bad else "Info", len(bad), "All experimental-unit references resolve." if not bad else f"Unresolved experimental-unit IDs: {bad[:5]}", f"Evidence/{table}"))

    # Reporting scope JSON references are warnings, because reports may intentionally cover external/legacy data.
    if report_path and report_path.exists():
        try:
            with _connect_ro(report_path) as rc, _connect_ro(field_path) as fc, _connect_ro(trial_path) as tc:
                fields = _read_ids(fc, "fields", "field_id")
                trials = _read_ids(tc, "trials", "trial_id")
                unresolved: list[str] = []
                if _table_exists(rc, "studies"):
                    for sid, scope_json in rc.execute("SELECT study_id, scope_json FROM studies").fetchall():
                        try:
                            scope = json.loads(scope_json or "{}") if isinstance(scope_json, str) else {}
                        except Exception:
                            continue
                        fid = scope.get("field_id") or scope.get("Field ID")
                        tid = scope.get("trial_id") or scope.get("Trial ID")
                        if fid and str(fid) not in fields:
                            unresolved.append(f"{sid}:field={fid}")
                        if tid and str(tid) not in trials:
                            unresolved.append(f"{sid}:trial={tid}")
                rows.append(_status_row("Report scopes resolve to current Field/Trial records", "PASS" if not unresolved else "WARN", "Warning" if unresolved else "Info", len(unresolved), "All explicit report field/trial scopes resolve." if not unresolved else f"Unresolved report scopes: {unresolved[:5]}", "Reports → Evidence"))
        except Exception as exc:
            rows.append(_status_row("Report scope audit", "WARN", "Warning", 1, f"Could not inspect reporting scope: {type(exc).__name__}: {exc}", "Reports → Evidence"))

    return pd.DataFrame(rows)


def workflow_chain_status(
    database_paths: Mapping[str, str | Path],
    *,
    active_field_id: str | None = None,
    active_trial_id: str | None = None,
) -> pd.DataFrame:
    """Return a lightweight persisted-evidence chain for the active context."""
    paths = {str(k): Path(v) for k, v in database_paths.items()}
    rows: list[dict[str, Any]] = []

    def add(stage: str, ready: bool, detail: str, evidence: str) -> None:
        rows.append({"Stage": stage, "Status": "Ready" if ready else "Missing / not yet linked", "Evidence type": evidence, "Detail": detail})

    field_id = str(active_field_id or "").strip() or None
    trial_id = str(active_trial_id or "").strip() or None
    # A mapped experiment can supply the authoritative field when the researcher
    # selected the trial without separately selecting the field in the context bar.
    tp_for_context = paths.get("Experiments")
    if trial_id and not field_id and tp_for_context and tp_for_context.exists():
        try:
            with _connect_ro(tp_for_context) as c:
                hit = c.execute("SELECT source_field_id FROM trials WHERE trial_id=?", (trial_id,)).fetchone()
                if hit and hit[0]:
                    field_id = str(hit[0])
        except Exception:
            pass
    field_exists = False
    trial_exists = False
    plot_count = 0

    fp = paths.get("Field Operations")
    if fp and fp.exists() and field_id:
        with _connect_ro(fp) as c:
            field_exists = _count(c, "SELECT COUNT(*) FROM fields WHERE field_id=?", (field_id,)) > 0
            season_count = _count(c, "SELECT COUNT(*) FROM field_seasons WHERE field_id=?", (field_id,)) if _table_exists(c, "field_seasons") else 0
            ops_count = _count(c, "SELECT COUNT(*) FROM operations WHERE field_id=?", (field_id,)) if _table_exists(c, "operations") else 0
            obs_count = _count(c, "SELECT COUNT(*) FROM observations WHERE field_id=?", (field_id,)) if _table_exists(c, "observations") else 0
        add("Mapped field", field_exists, f"Active field ID {field_id}" if field_exists else "Select an existing mapped field.", "Recorded spatial")
        add("Structured season", season_count > 0, f"{season_count} season record(s).", "Recorded")
        add("Field observations / operations", (ops_count + obs_count) > 0, f"{obs_count} observation(s), {ops_count} operation(s).", "Observed / recorded")
    else:
        add("Mapped field", False, "No active field selected.", "Recorded spatial")
        add("Structured season", False, "Requires an active mapped field.", "Recorded")
        add("Field observations / operations", False, "Requires an active mapped field.", "Observed / recorded")

    tp = paths.get("Experiments")
    if tp and tp.exists() and trial_id:
        with _connect_ro(tp) as c:
            trial_exists = _count(c, "SELECT COUNT(*) FROM trials WHERE trial_id=?", (trial_id,)) > 0
            plot_count = _count(c, "SELECT COUNT(*) FROM plots WHERE trial_id=?", (trial_id,)) if _table_exists(c, "plots") else 0
            obs = _count(c, "SELECT COUNT(*) FROM flowering_observations WHERE trial_id=?", (trial_id,)) if _table_exists(c, "flowering_observations") else 0
            if obs == 0 and _table_exists(c, "observations"):
                obs = _count(c, "SELECT COUNT(*) FROM observations WHERE trial_id=?", (trial_id,))
            harvest = _count(c, "SELECT COUNT(*) FROM harvest_outcomes WHERE trial_id=?", (trial_id,)) if _table_exists(c, "harvest_outcomes") else 0
            if harvest == 0 and _table_exists(c, "harvest"):
                harvest = _count(c, "SELECT COUNT(*) FROM harvest WHERE trial_id=?", (trial_id,))
        add("Experiment", trial_exists, f"Active trial ID {trial_id}" if trial_exists else "Selected trial does not exist in the experiment database.", "Recorded design")
        add("Experimental units", plot_count > 0, f"{plot_count} mapped/saved experimental unit(s).", "Recorded spatial design")
        add("Experimental observations", obs > 0, f"{obs} flowering/observation record(s).", "Observed")
        add("Harvest / trial outcome", harvest > 0, f"{harvest} harvest record(s).", "Observed outcome")
    else:
        add("Experiment", False, "No active trial selected.", "Recorded design")
        add("Experimental units", False, "Requires an active experiment.", "Recorded spatial design")
        add("Experimental observations", False, "Requires an active experiment.", "Observed")
        add("Harvest / trial outcome", False, "Requires an active experiment.", "Observed outcome")

    twinp = paths.get("Persistent Twin")
    link_ids: list[str] = []
    if twinp and twinp.exists():
        with _connect_ro(twinp) as c:
            if _table_exists(c, "twin_links"):
                clauses = []
                params: list[str] = []
                if field_id:
                    clauses.append("field_id=?")
                    params.append(field_id)
                if trial_id:
                    clauses.append("trial_id=?")
                    params.append(trial_id)
                if clauses:
                    link_ids = [str(r[0]) for r in c.execute(f"SELECT link_id FROM twin_links WHERE {' OR '.join(clauses)}", tuple(params)).fetchall()]
            weather = snapshots = root = 0
            if link_ids:
                placeholders = ",".join("?" for _ in link_ids)
                weather = _count(c, f"SELECT COUNT(*) FROM twin_weather WHERE link_id IN ({placeholders})", tuple(link_ids)) if _table_exists(c, "twin_weather") else 0
                snapshots = _count(c, f"SELECT COUNT(*) FROM snapshots WHERE link_id IN ({placeholders})", tuple(link_ids)) if _table_exists(c, "snapshots") else 0
                root = _count(c, f"SELECT COUNT(*) FROM twin_root_zone WHERE link_id IN ({placeholders})", tuple(link_ids)) if _table_exists(c, "twin_root_zone") else 0
        add("Persistent Twin link", bool(link_ids), f"{len(link_ids)} Twin link(s) match the active field/trial.", "Persistent digital-twin linkage")
        add("Twin environmental/state evidence", (weather + snapshots + root) > 0, f"weather={weather}; snapshots={snapshots}; root-zone records={root}.", "Retrieved / derived / mechanistic")
    else:
        add("Persistent Twin link", False, "Persistent Twin database unavailable.", "Persistent digital-twin linkage")
        add("Twin environmental/state evidence", False, "Requires a linked Twin.", "Retrieved / derived / mechanistic")

    ep = paths.get("Research Evidence")
    if ep and ep.exists():
        with _connect_ro(ep) as c:
            where_parts = []
            params: list[str] = []
            if field_id:
                where_parts.append("field_id=?")
                params.append(field_id)
            if trial_id:
                where_parts.append("trial_id=?")
                params.append(trial_id)
            where = (" WHERE " + " OR ".join(where_parts)) if where_parts else ""
            pred = _count(c, "SELECT COUNT(*) FROM predictions" + where, tuple(params)) if _table_exists(c, "predictions") else 0
            rec = _count(c, "SELECT COUNT(*) FROM recommendations" + where, tuple(params)) if _table_exists(c, "recommendations") else 0
            out = _count(c, "SELECT COUNT(*) FROM treatment_outcomes" + where, tuple(params)) if _table_exists(c, "treatment_outcomes") else 0
            models = _count(c, "SELECT COUNT(*) FROM models") if _table_exists(c, "models") else 0
            validations = _count(c, "SELECT COUNT(*) FROM validation_runs") if _table_exists(c, "validation_runs") else 0
        add("Registered models / validation", models > 0, f"{models} registered model(s); {validations} saved validation run(s).", "Predictive evidence")
        add("Context-linked prediction", pred > 0, f"{pred} prediction(s) linked to the active field/trial.", "ML / mechanistic prediction")
        add("Recommendation", rec > 0, f"{rec} recommendation(s) linked to the active field/trial.", "Recommendation")
        add("Measured decision outcome", out > 0, f"{out} treatment/decision outcome(s) linked to the active field/trial.", "Observed outcome")

    rp = paths.get("Reporting")
    report_count = 0
    if rp and rp.exists():
        with _connect_ro(rp) as c:
            if _table_exists(c, "studies"):
                # JSON matching is deliberately conservative and used only as a readiness hint.
                for _, scope_json in c.execute("SELECT study_id, scope_json FROM studies").fetchall():
                    try:
                        scope = json.loads(scope_json or "{}")
                    except Exception:
                        continue
                    if field_id and str(scope.get("field_id") or scope.get("Field ID") or "") == field_id:
                        report_count += 1
                    elif trial_id and str(scope.get("trial_id") or scope.get("Trial ID") or "") == trial_id:
                        report_count += 1
        add("Traceable report/publication", report_count > 0, f"{report_count} report study/studies explicitly scoped to the active context.", "Frozen report evidence")

    return pd.DataFrame(rows)
