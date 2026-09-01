"""Persistent reporting, publication and claim-evidence registry for AGROLATTICE.

Release 11.15 adds a reporting database rather than overloading the scientific
source databases. Report records reference Field/Trial/Twin/Model identifiers
but never alter those authoritative stores.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

MODULE_VERSION = "1.0.0"
DB_SCHEMA_VERSION = "1.0.0"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, pd.Timestamp, Path)):
        return str(value)
    if isinstance(value, Mapping):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(v) for v in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return str(value)


def stable_json(value: Any) -> str:
    return json.dumps(json_safe(value), sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ReportingRegistry:
    def __init__(self, path: str | Path, asset_root: str | Path | None = None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.asset_root = Path(asset_root) if asset_root else self.path.parent / "report_assets"
        self.asset_root.mkdir(parents=True, exist_ok=True)
        self._initialise()
        self._seed_citations()

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _initialise(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS studies (
            study_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            short_title TEXT,
            report_type TEXT NOT NULL,
            scope_json TEXT NOT NULL DEFAULT '{}',
            manuscript_json TEXT NOT NULL DEFAULT '{}',
            authors_json TEXT NOT NULL DEFAULT '[]',
            affiliations_json TEXT NOT NULL DEFAULT '[]',
            corresponding_author TEXT,
            corresponding_orcid TEXT,
            target_journal TEXT,
            manuscript_status TEXT NOT NULL DEFAULT 'Draft',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS evidence_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            study_id TEXT NOT NULL,
            label TEXT,
            scope_json TEXT NOT NULL DEFAULT '{}',
            manifest_json TEXT NOT NULL,
            manifest_sha256 TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(study_id) REFERENCES studies(study_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS report_versions (
            version_id TEXT PRIMARY KEY,
            study_id TEXT NOT NULL,
            version_number INTEGER NOT NULL,
            label TEXT,
            manuscript_status TEXT NOT NULL DEFAULT 'Draft',
            evidence_snapshot_id TEXT,
            manuscript_json TEXT NOT NULL DEFAULT '{}',
            notes TEXT,
            author TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(study_id, version_number),
            FOREIGN KEY(study_id) REFERENCES studies(study_id) ON DELETE CASCADE,
            FOREIGN KEY(evidence_snapshot_id) REFERENCES evidence_snapshots(snapshot_id)
        );
        CREATE TABLE IF NOT EXISTS report_artifacts (
            artifact_id TEXT PRIMARY KEY,
            study_id TEXT NOT NULL,
            snapshot_id TEXT,
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            caption TEXT,
            source_json TEXT NOT NULL DEFAULT '{}',
            settings_json TEXT NOT NULL DEFAULT '{}',
            file_path TEXT,
            sha256 TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(study_id) REFERENCES studies(study_id) ON DELETE CASCADE,
            FOREIGN KEY(snapshot_id) REFERENCES evidence_snapshots(snapshot_id)
        );
        CREATE TABLE IF NOT EXISTS claims (
            claim_id TEXT PRIMARY KEY,
            study_id TEXT NOT NULL,
            version_id TEXT,
            claim_text TEXT NOT NULL,
            evidence_type TEXT,
            source_reference TEXT,
            statistic TEXT,
            status TEXT NOT NULL DEFAULT 'Draft',
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(study_id) REFERENCES studies(study_id) ON DELETE CASCADE,
            FOREIGN KEY(version_id) REFERENCES report_versions(version_id)
        );
        CREATE TABLE IF NOT EXISTS citations (
            citation_id TEXT PRIMARY KEY,
            doi TEXT,
            authors TEXT,
            year INTEGER,
            title TEXT NOT NULL,
            journal TEXT,
            bibtex TEXT,
            ris TEXT,
            notes TEXT,
            source TEXT,
            created_at TEXT NOT NULL
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_citations_doi ON citations(doi) WHERE doi IS NOT NULL AND doi <> '';
        CREATE TABLE IF NOT EXISTS study_citations (
            study_id TEXT NOT NULL,
            citation_id TEXT NOT NULL,
            purpose TEXT,
            PRIMARY KEY(study_id, citation_id),
            FOREIGN KEY(study_id) REFERENCES studies(study_id) ON DELETE CASCADE,
            FOREIGN KEY(citation_id) REFERENCES citations(citation_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS export_packages (
            export_id TEXT PRIMARY KEY,
            study_id TEXT NOT NULL,
            version_id TEXT,
            package_type TEXT NOT NULL,
            privacy_profile TEXT NOT NULL,
            file_path TEXT,
            sha256 TEXT,
            manifest_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            FOREIGN KEY(study_id) REFERENCES studies(study_id) ON DELETE CASCADE,
            FOREIGN KEY(version_id) REFERENCES report_versions(version_id)
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            audit_id TEXT PRIMARY KEY,
            study_id TEXT,
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id TEXT,
            actor TEXT,
            details_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            FOREIGN KEY(study_id) REFERENCES studies(study_id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_reports_updated ON studies(updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_snapshots_study ON evidence_snapshots(study_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_versions_study ON report_versions(study_id, version_number DESC);
        CREATE INDEX IF NOT EXISTS idx_artifacts_study ON report_artifacts(study_id, kind, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_claims_study ON claims(study_id, status);
        """
        with self.connection() as conn:
            conn.executescript(schema)
            conn.execute("INSERT OR REPLACE INTO metadata(key,value) VALUES('schema_version',?)", (DB_SCHEMA_VERSION,))
            conn.execute("INSERT OR REPLACE INTO metadata(key,value) VALUES('module_version',?)", (MODULE_VERSION,))

    def _seed_citations(self) -> None:
        seeds = [
            {
                "doi": "10.1002/csc2.21453",
                "authors": "Laurent et al.",
                "year": 2025,
                "title": "Predicting inbred parent synchrony at flowering for maize hybrid seed production",
                "journal": "Crop Science",
                "notes": "Source method for the AGROLATTICE Mechanistic Maize Twin adaptation; local data and the original proprietary Bayesian sampler are not reproduced.",
                "source": "Built-in AGROLATTICE method citation",
            },
            {
                "doi": "10.1016/j.compag.2024.109472",
                "authors": "Daisy Wadhwa; Kamal Malik",
                "year": 2024,
                "title": "A generalizable and interpretable model for early warning of pest-induced crop diseases using environmental data",
                "journal": "Computers and Electronics in Agriculture",
                "notes": "Source for environmental pest-risk feature engineering and interpretable classification adaptations.",
                "source": "Built-in AGROLATTICE method citation",
            },
            {
                "doi": "10.1016/j.eswa.2024.124137",
                "authors": "Jiale Wang; Dong Zhang",
                "year": 2024,
                "title": "Intelligent pest forecasting with meteorological data: An explainable deep learning approach",
                "journal": "Expert Systems with Applications",
                "notes": "Source for the ALIC pest-forecasting research method; only cite as implemented when the corresponding model is actually used.",
                "source": "Built-in AGROLATTICE method citation",
            },
            {
                "doi": "10.1088/1748-9326/acf50e",
                "authors": "Dilli Paudel et al.",
                "year": 2023,
                "title": "A weakly supervised framework for high-resolution crop yield forecasts",
                "journal": "Environmental Research Letters",
                "notes": "Source for weakly supervised aggregate-consistency yield modelling adaptation.",
                "source": "Built-in AGROLATTICE method citation",
            },
            {
                "doi": "10.1145/3637528.3671536",
                "authors": "Fudong Lin et al.",
                "year": 2024,
                "title": "An Open and Large-Scale Dataset for Multi-Modal Climate Change-aware Crop Yield Predictions",
                "journal": "KDD 2024",
                "notes": "CropNet dataset/method reference used for benchmark provenance.",
                "source": "Built-in AGROLATTICE method citation",
            },
            {
                "doi": "10.5194/essd-15-5491-2023",
                "authors": "Van Tricht et al.",
                "year": 2023,
                "title": "WorldCereal: a dynamic open-source system for global-scale, seasonal, and reproducible crop and irrigation mapping",
                "journal": "Earth System Science Data",
                "notes": "WorldCereal reference used for EO benchmark/provenance.",
                "source": "Built-in AGROLATTICE method citation",
            },
            {
                "doi": "10.1016/j.isprsjprs.2023.09.025",
                "authors": "Chishan Zhang; Chunyuan Diao",
                "year": 2023,
                "title": "A Phenology-guided Bayesian-CNN (PB-CNN) framework for soybean yield estimation and uncertainty analysis",
                "journal": "ISPRS Journal of Photogrammetry and Remote Sensing",
                "notes": "Uncertainty/phenology research reference; do not claim exact implementation unless the specific method is used.",
                "source": "Built-in AGROLATTICE method citation",
            },
        ]
        for seed in seeds:
            self.add_citation(seed, ignore_existing=True)

    def integrity_check(self) -> dict[str, Any]:
        with self.connection() as conn:
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            fk = conn.execute("PRAGMA foreign_key_check").fetchall()
        return {"integrity_check": integrity, "foreign_key_violations": len(fk), "schema_version": DB_SCHEMA_VERSION}

    def summary(self) -> dict[str, int]:
        with self.connection() as conn:
            names = ["studies", "report_versions", "evidence_snapshots", "report_artifacts", "claims", "citations", "export_packages"]
            return {name: int(conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]) for name in names}

    def save_study(self, record: Mapping[str, Any]) -> str:
        now = utc_now_iso()
        study_id = str(record.get("study_id") or uuid.uuid4())
        with self.connection() as conn:
            existing = conn.execute("SELECT created_at FROM studies WHERE study_id=?", (study_id,)).fetchone()
            created = existing[0] if existing else now
            conn.execute(
                """INSERT OR REPLACE INTO studies(
                    study_id,title,short_title,report_type,scope_json,manuscript_json,authors_json,affiliations_json,
                    corresponding_author,corresponding_orcid,target_journal,manuscript_status,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    study_id,
                    str(record.get("title") or "Untitled research report"),
                    str(record.get("short_title") or str(record.get("title") or "Research report")[:80]),
                    str(record.get("report_type") or "Full scientific manuscript"),
                    stable_json(record.get("scope") or {}),
                    stable_json(record.get("manuscript") or {}),
                    stable_json(record.get("authors") or []),
                    stable_json(record.get("affiliations") or []),
                    record.get("corresponding_author"),
                    record.get("corresponding_orcid"),
                    record.get("target_journal"),
                    str(record.get("manuscript_status") or "Draft"),
                    created,
                    now,
                ),
            )
        self.audit(study_id, "save_study", "study", study_id, details={"report_type": record.get("report_type")})
        return study_id

    @staticmethod
    def _decode_study(row: sqlite3.Row | Mapping[str, Any]) -> dict[str, Any]:
        out = dict(row)
        for key, target in [("scope_json", "scope"), ("manuscript_json", "manuscript"), ("authors_json", "authors"), ("affiliations_json", "affiliations")]:
            try:
                out[target] = json.loads(out.pop(key) or "{}" if key in ("scope_json", "manuscript_json") else out.pop(key) or "[]")
            except Exception:
                out[target] = {} if key in ("scope_json", "manuscript_json") else []
        return out

    def study(self, study_id: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM studies WHERE study_id=?", (study_id,)).fetchone()
        return self._decode_study(row) if row else None

    def studies(self) -> pd.DataFrame:
        with self.connection() as conn:
            return pd.read_sql_query("SELECT study_id,title,short_title,report_type,target_journal,manuscript_status,created_at,updated_at FROM studies ORDER BY updated_at DESC", conn)

    def save_snapshot(self, study_id: str, *, label: str, scope: Mapping[str, Any], manifest: Mapping[str, Any]) -> str:
        snapshot_id = str(uuid.uuid4())
        manifest_text = stable_json(manifest)
        with self.connection() as conn:
            conn.execute(
                "INSERT INTO evidence_snapshots(snapshot_id,study_id,label,scope_json,manifest_json,manifest_sha256,created_at) VALUES(?,?,?,?,?,?,?)",
                (snapshot_id, study_id, label, stable_json(scope), manifest_text, hashlib.sha256(manifest_text.encode("utf-8")).hexdigest(), utc_now_iso()),
            )
        self.audit(study_id, "freeze_evidence", "evidence_snapshot", snapshot_id, details={"label": label})
        return snapshot_id

    def snapshots(self, study_id: str | None = None) -> pd.DataFrame:
        sql = "SELECT * FROM evidence_snapshots"
        params: tuple[Any, ...] = ()
        if study_id:
            sql += " WHERE study_id=?"
            params = (study_id,)
        sql += " ORDER BY created_at DESC"
        with self.connection() as conn:
            return pd.read_sql_query(sql, conn, params=params)

    def snapshot(self, snapshot_id: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM evidence_snapshots WHERE snapshot_id=?", (snapshot_id,)).fetchone()
        if not row:
            return None
        out = dict(row)
        for key in ("scope_json", "manifest_json"):
            try:
                out[key[:-5]] = json.loads(out[key])
            except Exception:
                out[key[:-5]] = {}
        return out

    def create_version(self, study_id: str, *, manuscript: Mapping[str, Any], snapshot_id: str | None, label: str = "", status: str = "Draft", notes: str = "", author: str = "") -> str:
        with self.connection() as conn:
            number = int(conn.execute("SELECT COALESCE(MAX(version_number),0)+1 FROM report_versions WHERE study_id=?", (study_id,)).fetchone()[0])
            version_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO report_versions(version_id,study_id,version_number,label,manuscript_status,evidence_snapshot_id,manuscript_json,notes,author,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (version_id, study_id, number, label or f"v{number}", status, snapshot_id, stable_json(manuscript), notes, author, utc_now_iso()),
            )
        self.audit(study_id, "create_report_version", "report_version", version_id, actor=author, details={"version_number": number, "status": status})
        return version_id

    def versions(self, study_id: str) -> pd.DataFrame:
        with self.connection() as conn:
            return pd.read_sql_query("SELECT * FROM report_versions WHERE study_id=? ORDER BY version_number DESC", conn, params=(study_id,))

    def latest_version(self, study_id: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM report_versions WHERE study_id=? ORDER BY version_number DESC LIMIT 1", (study_id,)).fetchone()
        if not row:
            return None
        out = dict(row)
        try:
            out["manuscript"] = json.loads(out.get("manuscript_json") or "{}")
        except Exception:
            out["manuscript"] = {}
        return out

    def save_artifact(self, study_id: str, *, kind: str, title: str, caption: str = "", source: Mapping[str, Any] | None = None, settings: Mapping[str, Any] | None = None, data: bytes | None = None, suffix: str = ".bin", snapshot_id: str | None = None) -> str:
        artifact_id = str(uuid.uuid4())
        file_path = None
        digest = None
        if data is not None:
            folder = self.asset_root / study_id / f"{kind}s"
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / f"{artifact_id}{suffix}"
            path.write_bytes(data)
            file_path = str(path)
            digest = sha256_bytes(data)
        with self.connection() as conn:
            conn.execute(
                "INSERT INTO report_artifacts(artifact_id,study_id,snapshot_id,kind,title,caption,source_json,settings_json,file_path,sha256,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (artifact_id, study_id, snapshot_id, kind, title, caption, stable_json(source or {}), stable_json(settings or {}), file_path, digest, utc_now_iso()),
            )
        self.audit(study_id, "save_artifact", kind, artifact_id, details={"title": title, "sha256": digest})
        return artifact_id

    def artifacts(self, study_id: str, kind: str | None = None) -> pd.DataFrame:
        sql = "SELECT * FROM report_artifacts WHERE study_id=?"
        params: list[Any] = [study_id]
        if kind:
            sql += " AND kind=?"
            params.append(kind)
        sql += " ORDER BY created_at DESC"
        with self.connection() as conn:
            return pd.read_sql_query(sql, conn, params=tuple(params))

    def delete_artifact(self, artifact_id: str) -> None:
        with self.connection() as conn:
            row = conn.execute("SELECT study_id,file_path FROM report_artifacts WHERE artifact_id=?", (artifact_id,)).fetchone()
            if not row:
                return
            conn.execute("DELETE FROM report_artifacts WHERE artifact_id=?", (artifact_id,))
        if row[1]:
            try:
                Path(row[1]).unlink(missing_ok=True)
            except Exception:
                pass
        self.audit(row[0], "delete_artifact", "artifact", artifact_id)

    def save_claim(self, study_id: str, *, text: str, evidence_type: str = "", source_reference: str = "", statistic: str = "", status: str = "Draft", notes: str = "", version_id: str | None = None, claim_id: str | None = None) -> str:
        claim_id = str(claim_id or uuid.uuid4())
        now = utc_now_iso()
        with self.connection() as conn:
            existing = conn.execute("SELECT created_at FROM claims WHERE claim_id=?", (claim_id,)).fetchone()
            created = existing[0] if existing else now
            conn.execute(
                "INSERT OR REPLACE INTO claims(claim_id,study_id,version_id,claim_text,evidence_type,source_reference,statistic,status,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (claim_id, study_id, version_id, text, evidence_type, source_reference, statistic, status, notes, created, now),
            )
        self.audit(study_id, "save_claim", "claim", claim_id, details={"status": status, "evidence_type": evidence_type})
        return claim_id

    def claims(self, study_id: str) -> pd.DataFrame:
        with self.connection() as conn:
            return pd.read_sql_query("SELECT * FROM claims WHERE study_id=? ORDER BY updated_at DESC", conn, params=(study_id,))

    def add_citation(self, record: Mapping[str, Any], *, ignore_existing: bool = False) -> str:
        doi = str(record.get("doi") or "").strip() or None
        with self.connection() as conn:
            if doi:
                existing = conn.execute("SELECT citation_id FROM citations WHERE doi=?", (doi,)).fetchone()
                if existing:
                    if ignore_existing:
                        return str(existing[0])
                    citation_id = str(existing[0])
                else:
                    citation_id = str(record.get("citation_id") or uuid.uuid4())
            else:
                citation_id = str(record.get("citation_id") or uuid.uuid4())
            conn.execute(
                "INSERT OR REPLACE INTO citations(citation_id,doi,authors,year,title,journal,bibtex,ris,notes,source,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,COALESCE((SELECT created_at FROM citations WHERE citation_id=?),?))",
                (citation_id, doi, record.get("authors"), record.get("year"), record.get("title"), record.get("journal"), record.get("bibtex"), record.get("ris"), record.get("notes"), record.get("source"), citation_id, utc_now_iso()),
            )
        return citation_id

    def citations(self) -> pd.DataFrame:
        with self.connection() as conn:
            return pd.read_sql_query("SELECT * FROM citations ORDER BY COALESCE(year,0) DESC, title", conn)

    def link_citation(self, study_id: str, citation_id: str, purpose: str = "") -> None:
        with self.connection() as conn:
            conn.execute("INSERT OR REPLACE INTO study_citations(study_id,citation_id,purpose) VALUES(?,?,?)", (study_id, citation_id, purpose))
        self.audit(study_id, "link_citation", "citation", citation_id, details={"purpose": purpose})

    def study_citations(self, study_id: str) -> pd.DataFrame:
        with self.connection() as conn:
            return pd.read_sql_query(
                "SELECT c.*, sc.purpose FROM study_citations sc JOIN citations c ON c.citation_id=sc.citation_id WHERE sc.study_id=? ORDER BY COALESCE(c.year,0), c.authors",
                conn,
                params=(study_id,),
            )

    def save_export(self, study_id: str, *, package_type: str, privacy_profile: str, data: bytes, manifest: Mapping[str, Any], version_id: str | None = None, suffix: str = ".zip") -> str:
        export_id = str(uuid.uuid4())
        folder = self.asset_root / study_id / "exports"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{export_id}{suffix}"
        path.write_bytes(data)
        digest = sha256_bytes(data)
        with self.connection() as conn:
            conn.execute(
                "INSERT INTO export_packages(export_id,study_id,version_id,package_type,privacy_profile,file_path,sha256,manifest_json,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (export_id, study_id, version_id, package_type, privacy_profile, str(path), digest, stable_json(manifest), utc_now_iso()),
            )
        self.audit(study_id, "save_export", "export", export_id, details={"package_type": package_type, "privacy_profile": privacy_profile, "sha256": digest})
        return export_id

    def exports(self, study_id: str) -> pd.DataFrame:
        with self.connection() as conn:
            return pd.read_sql_query("SELECT * FROM export_packages WHERE study_id=? ORDER BY created_at DESC", conn, params=(study_id,))

    def audit(self, study_id: str | None, action: str, entity_type: str = "", entity_id: str | None = None, *, actor: str = "", details: Mapping[str, Any] | None = None) -> str:
        audit_id = str(uuid.uuid4())
        with self.connection() as conn:
            conn.execute(
                "INSERT INTO audit_log(audit_id,study_id,action,entity_type,entity_id,actor,details_json,created_at) VALUES(?,?,?,?,?,?,?,?)",
                (audit_id, study_id, action, entity_type, entity_id, actor, stable_json(details or {}), utc_now_iso()),
            )
        return audit_id

    def audit_log(self, study_id: str | None = None, limit: int = 2000) -> pd.DataFrame:
        sql = "SELECT * FROM audit_log"
        params: list[Any] = []
        if study_id:
            sql += " WHERE study_id=?"
            params.append(study_id)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(int(limit))
        with self.connection() as conn:
            return pd.read_sql_query(sql, conn, params=tuple(params))

    def import_legacy_studies(self, legacy_root: str | Path) -> dict[str, int]:
        root = Path(legacy_root)
        result = {"found": 0, "imported": 0, "skipped": 0, "failed": 0}
        if not root.exists():
            return result
        for path in root.glob("*.json"):
            result["found"] += 1
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                old_id = str(payload.get("study_id") or path.stem)
                if self.study(old_id):
                    result["skipped"] += 1
                    continue
                manuscript = {k: payload.get(k, "") for k in (
                    "abstract_background", "abstract_methods", "abstract_results", "abstract_conclusion",
                    "introduction", "discussion", "limitations", "conclusion", "data_availability",
                )}
                self.save_study({
                    "study_id": old_id,
                    "title": payload.get("title") or "Imported legacy study",
                    "short_title": payload.get("short_title"),
                    "report_type": "Full scientific manuscript",
                    "scope": {"legacy_project_id": payload.get("project_id")},
                    "manuscript": manuscript,
                    "authors": payload.get("authors") or [],
                    "corresponding_author": payload.get("corresponding_author"),
                    "target_journal": payload.get("journal"),
                })
                result["imported"] += 1
            except Exception:
                result["failed"] += 1
        return result
