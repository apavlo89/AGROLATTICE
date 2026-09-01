"""Persistent crop-profile registry for AGROLATTICE Crop Decisions.

Release 11.11 introduces this additive registry so researcher-defined crop and
cultivar profiles are versioned, attributable, region-aware and auditable rather
than existing only as an unstructured JSON sidecar.  Validated library records
remain immutable source material; this registry stores user/research adaptations.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

MODULE_VERSION = "1.0.0"
DB_SCHEMA_VERSION = "1.0.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True, default=str)


def _loads(value: Any, default: Any = None) -> Any:
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list, tuple, int, float, bool)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


class CropProfileRegistry:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialise()

    @contextmanager
    def connection(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialise(self) -> None:
        with self.connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata(
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS crop_profiles(
                    profile_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    crop TEXT NOT NULL,
                    cultivar TEXT,
                    country TEXT,
                    region TEXT,
                    source_profile TEXT,
                    evidence_grade TEXT,
                    status TEXT NOT NULL,
                    author TEXT,
                    notes TEXT,
                    current_version INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS crop_profile_versions(
                    version_id TEXT PRIMARY KEY,
                    profile_id TEXT NOT NULL,
                    version_number INTEGER NOT NULL,
                    parameters_json TEXT NOT NULL,
                    source_citation TEXT,
                    change_note TEXT,
                    created_by TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(profile_id) REFERENCES crop_profiles(profile_id) ON DELETE CASCADE,
                    UNIQUE(profile_id, version_number)
                );
                CREATE INDEX IF NOT EXISTS idx_crop_profiles_crop ON crop_profiles(crop);
                CREATE INDEX IF NOT EXISTS idx_crop_profiles_country ON crop_profiles(country);
                """
            )
            connection.execute("INSERT OR REPLACE INTO metadata(key,value) VALUES('schema_version',?)", (DB_SCHEMA_VERSION,))
            connection.execute("INSERT OR REPLACE INTO metadata(key,value) VALUES('module_version',?)", (MODULE_VERSION,))

    def save_profile(self, record: Mapping[str, Any], *, parameters: Mapping[str, Any], change_note: str = "Created") -> str:
        crop = str(record.get("crop") or "").strip()
        name = str(record.get("name") or "").strip()
        if not crop or not name:
            raise ValueError("Crop profile requires crop and name.")
        profile_id = str(record.get("profile_id") or uuid.uuid4())
        now = utc_now()
        with self.connection() as connection:
            existing = connection.execute("SELECT current_version,created_at FROM crop_profiles WHERE profile_id=?", (profile_id,)).fetchone()
            version = int(existing["current_version"]) + 1 if existing else 1
            created_at = str(existing["created_at"]) if existing else now
            values = (
                name, crop, record.get("cultivar"), record.get("country"), record.get("region"),
                record.get("source_profile"), record.get("evidence_grade") or "Researcher supplied",
                record.get("status") or "Research", record.get("author"), record.get("notes"),
                version, now,
            )
            if existing:
                # UPDATE rather than SQLite REPLACE: REPLACE deletes and reinserts the parent
                # row, which would cascade-delete version history through the foreign key.
                connection.execute(
                    """UPDATE crop_profiles SET
                        name=?,crop=?,cultivar=?,country=?,region=?,source_profile=?,evidence_grade=?,status=?,
                        author=?,notes=?,current_version=?,updated_at=? WHERE profile_id=?""",
                    values + (profile_id,),
                )
            else:
                connection.execute(
                    """INSERT INTO crop_profiles(
                        profile_id,name,crop,cultivar,country,region,source_profile,evidence_grade,status,
                        author,notes,current_version,created_at,updated_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (profile_id,) + values[:-1] + (created_at, values[-1]),
                )
            connection.execute(
                """INSERT INTO crop_profile_versions(
                    version_id,profile_id,version_number,parameters_json,source_citation,change_note,created_by,created_at
                ) VALUES(?,?,?,?,?,?,?,?)""",
                (
                    str(uuid.uuid4()), profile_id, version, _json(dict(parameters)), record.get("source_citation"),
                    change_note, record.get("author"), now,
                ),
            )
        return profile_id

    def clone_profile(self, profile_id: str, *, name: str, author: str | None = None, country: str | None = None, region: str | None = None) -> str:
        source = self.profile(profile_id)
        if not source:
            raise ValueError("Source crop profile not found.")
        record = {
            "name": name,
            "crop": source["crop"],
            "cultivar": source.get("cultivar"),
            "country": country if country is not None else source.get("country"),
            "region": region if region is not None else source.get("region"),
            "source_profile": f"Cloned from {source.get('name')} ({profile_id[:8]})",
            "evidence_grade": source.get("evidence_grade"),
            "status": "Research",
            "author": author,
            "notes": source.get("notes"),
            "source_citation": source.get("source_citation"),
        }
        return self.save_profile(record, parameters=source.get("parameters") or {}, change_note=f"Cloned from {profile_id}")

    def profiles(self, *, crop: str | None = None) -> pd.DataFrame:
        query = "SELECT * FROM crop_profiles"
        params: list[Any] = []
        if crop:
            query += " WHERE crop=?"; params.append(crop)
        query += " ORDER BY updated_at DESC"
        with self.connection() as connection:
            return pd.read_sql_query(query, connection, params=params)

    def profile(self, profile_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM crop_profiles WHERE profile_id=?", (profile_id,)).fetchone()
            if not row:
                return None
            result = dict(row)
            version = connection.execute(
                "SELECT * FROM crop_profile_versions WHERE profile_id=? ORDER BY version_number DESC LIMIT 1", (profile_id,)
            ).fetchone()
        if version:
            result["parameters"] = _loads(version["parameters_json"], {})
            result["source_citation"] = version["source_citation"]
            result["change_note"] = version["change_note"]
            result["version_created_at"] = version["created_at"]
        else:
            result["parameters"] = {}
        return result

    def versions(self, profile_id: str) -> pd.DataFrame:
        with self.connection() as connection:
            return pd.read_sql_query(
                "SELECT version_id,profile_id,version_number,source_citation,change_note,created_by,created_at,parameters_json FROM crop_profile_versions WHERE profile_id=? ORDER BY version_number DESC",
                connection, params=[profile_id],
            )

    def integrity_check(self) -> tuple[str, int]:
        with self.connection() as connection:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            foreign = connection.execute("PRAGMA foreign_key_check").fetchall()
        return str(integrity), len(foreign)

    def import_legacy_profiles(self, profiles: Mapping[str, Any], *, country: str | None = None) -> int:
        """Import legacy custom_crop_profiles.json once, without deleting the source file."""
        if not isinstance(profiles, Mapping) or not profiles:
            return 0
        existing = self.profiles()
        existing_names = set(existing["name"].astype(str)) if not existing.empty else set()
        imported = 0
        for crop, payload in profiles.items():
            name = f"Legacy custom · {crop}"
            if name in existing_names:
                continue
            self.save_profile(
                {
                    "name": name,
                    "crop": crop,
                    "country": country,
                    "source_profile": "custom_crop_profiles.json",
                    "evidence_grade": "Legacy researcher supplied",
                    "status": "Research",
                    "notes": (payload or {}).get("notes") if isinstance(payload, Mapping) else None,
                },
                parameters=dict(payload) if isinstance(payload, Mapping) else {"legacy_value": payload},
                change_note="Imported from legacy custom_crop_profiles.json; original file retained unchanged.",
            )
            imported += 1
        return imported
