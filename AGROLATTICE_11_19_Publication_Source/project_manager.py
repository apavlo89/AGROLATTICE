"""Persistent local project management for the AgroLattice Research Tool.

Projects are portable JSON documents. The store uses unique temporary files and
retrying replacements to reduce collisions with Windows Defender and OneDrive.
"""
from __future__ import annotations

import io
import json
import os
import re
import shutil
import time
import uuid
import zipfile
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

SCHEMA_VERSION = "1.0.0"


class ProjectError(RuntimeError):
    """Raised when a project cannot be read, validated, or saved safely."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def json_safe(value: Any) -> Any:
    """Convert common scientific objects to JSON-safe values."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (date, datetime, pd.Timestamp)):
        return pd.Timestamp(value).isoformat()
    if isinstance(value, pd.DataFrame):
        return {
            "__type__": "dataframe",
            "columns": [str(c) for c in value.columns],
            "records": [json_safe(record) for record in value.to_dict(orient="records")],
        }
    if isinstance(value, pd.Series):
        return {
            "__type__": "series",
            "name": str(value.name) if value.name is not None else None,
            "values": json_safe(value.to_dict()),
        }
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    if isinstance(value, Mapping):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(v) for v in value]
    return str(value)


def dataframe_from_json_safe(value: Any) -> pd.DataFrame | None:
    if isinstance(value, Mapping) and value.get("__type__") == "dataframe":
        return pd.DataFrame(value.get("records", []), columns=value.get("columns"))
    return None


def slugify(value: str, fallback: str = "project") -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:70] or fallback


def _unique_temp(target: Path) -> Path:
    return target.with_name(f"{target.name}.{os.getpid()}.{time.time_ns()}.tmp")


def _replace_with_retries(source: Path, target: Path, attempts: int = 10) -> None:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            os.replace(source, target)
            return
        except (PermissionError, OSError) as error:
            last_error = error
            time.sleep(0.12 * (attempt + 1))
    raise ProjectError(
        f"Could not update {target}. Close programs using the file or pause OneDrive "
        f"synchronisation, then retry. Original error: {last_error}"
    )


def atomic_json_write(path: str | Path, payload: Mapping[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = _unique_temp(target)
    try:
        temporary.write_text(
            json.dumps(json_safe(payload), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        _replace_with_retries(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def new_project_template(
    *,
    name: str,
    location_name: str,
    latitude: float,
    longitude: float,
    crop: str,
    planting_date: str,
    expected_harvest_date: str | None = None,
    description: str = "",
) -> dict[str, Any]:
    now = utc_now_iso()
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": str(uuid.uuid4()),
        "name": str(name).strip() or "Untitled project",
        "description": str(description),
        "created_at": now,
        "updated_at": now,
        "status": "Active",
        "tags": [],
        "location": {
            "name": str(location_name),
            "latitude": float(latitude),
            "longitude": float(longitude),
            "state": None,
            "municipality": None,
            "elevation_m": None,
            "field_geometry": None,
            "field_area_ha": None,
        },
        "season": {
            "crop": str(crop),
            "cultivar": None,
            "planting_date": str(planting_date),
            "expected_harvest_date": expected_harvest_date,
            "phenology_method": "Validated stage durations",
            "base_temperature_c": None,
            "upper_temperature_c": None,
            "gdd_targets": [],
        },
        "soil": {
            "source": "Generic screening preset",
            "preset": "Silt",
            "field_capacity": 0.32,
            "wilting_point": 0.15,
            "initial_depletion_fraction": 0.25,
            "rooting_depth_m": None,
            "notes": "",
        },
        "irrigation": {
            "strategy": "Rainfed",
            "application_efficiency_percent": 75.0,
            "trigger_fraction_taw": 1.0,
            "refill_fraction": 1.0,
            "maximum_event_mm": 40.0,
            "fixed_interval_days": 7,
            "fixed_depth_mm": 25.0,
            "schedule": [],
        },
        "satellite": {
            "provider_preference": "Automatic failover",
            "buffer_radius_m": 500.0,
            "maximum_scene_cloud_percent": 50.0,
            "minimum_field_clear_percent": 30.0,
            "indices": ["NDVI", "EVI", "NDMI", "NDRE"],
        },
        "aquacrop": {
            "backend": "AquaCrop-OSPy",
            "crop_name": None,
            "soil_type": "SiltLoam",
            "initial_water_content": "FC",
            "irrigation_method": "Rainfed",
            "soil_moisture_targets": [70, 70, 70, 70],
            "maximum_daily_irrigation_mm": 25.0,
        },
        "observations": {
            "observed_yield_t_ha": None,
            "observed_harvest_date": None,
            "notes": "",
        },
        "workspace_snapshots": [],
        "model_runs": [],
        "audit_log": [
            {
                "timestamp": now,
                "action": "Project created",
                "details": "Initial project record created.",
            }
        ],
    }


def validate_project(project: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    if not str(project.get("project_id", "")).strip():
        issues.append("Missing project_id")
    if not str(project.get("name", "")).strip():
        issues.append("Missing project name")
    location = project.get("location", {}) or {}
    try:
        latitude = float(location.get("latitude"))
        longitude = float(location.get("longitude"))
        if not -90 <= latitude <= 90:
            issues.append("Latitude is outside -90 to 90")
        if not -180 <= longitude <= 180:
            issues.append("Longitude is outside -180 to 180")
    except Exception:
        issues.append("Latitude or longitude is missing or invalid")
    season = project.get("season", {}) or {}
    if not str(season.get("crop", "")).strip():
        issues.append("Crop is missing")
    if pd.isna(pd.to_datetime(season.get("planting_date"), errors="coerce")):
        issues.append("Planting date is invalid")
    return issues


@dataclass
class ProjectStore:
    root: Path

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.trash_dir.mkdir(parents=True, exist_ok=True)

    @property
    def projects_dir(self) -> Path:
        return self.root / "projects"

    @property
    def trash_dir(self) -> Path:
        return self.root / "trash"

    def path_for(self, project_id: str) -> Path:
        return self.projects_dir / f"{str(project_id)}.json"

    def save(self, project: Mapping[str, Any], action: str | None = None) -> dict[str, Any]:
        payload = deepcopy(dict(project))
        payload.setdefault("schema_version", SCHEMA_VERSION)
        payload.setdefault("project_id", str(uuid.uuid4()))
        payload.setdefault("created_at", utc_now_iso())
        payload["updated_at"] = utc_now_iso()
        payload.setdefault("audit_log", [])
        if action:
            payload["audit_log"].append(
                {"timestamp": utc_now_iso(), "action": action, "details": ""}
            )
        issues = validate_project(payload)
        if issues:
            raise ProjectError("Project validation failed: " + "; ".join(issues))
        atomic_json_write(self.path_for(payload["project_id"]), payload)
        return payload

    def load(self, project_id: str) -> dict[str, Any]:
        path = self.path_for(project_id)
        if not path.exists():
            raise ProjectError(f"Project not found: {project_id}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:
            raise ProjectError(f"Could not read {path.name}: {error}") from error
        issues = validate_project(payload)
        if issues:
            raise ProjectError("Stored project is invalid: " + "; ".join(issues))
        return payload

    def list_projects(self) -> pd.DataFrame:
        records: list[dict[str, Any]] = []
        for path in sorted(self.projects_dir.glob("*.json")):
            try:
                project = json.loads(path.read_text(encoding="utf-8"))
                location = project.get("location", {}) or {}
                season = project.get("season", {}) or {}
                records.append(
                    {
                        "Project ID": project.get("project_id"),
                        "Name": project.get("name"),
                        "Status": project.get("status", "Active"),
                        "Location": location.get("name"),
                        "Crop": season.get("crop"),
                        "Planting date": season.get("planting_date"),
                        "Updated": project.get("updated_at"),
                        "Model runs": len(project.get("model_runs", [])),
                        "Snapshots": len(project.get("workspace_snapshots", [])),
                    }
                )
            except Exception as error:
                records.append(
                    {
                        "Project ID": path.stem,
                        "Name": f"Unreadable: {path.name}",
                        "Status": "Error",
                        "Location": None,
                        "Crop": None,
                        "Planting date": None,
                        "Updated": None,
                        "Model runs": 0,
                        "Snapshots": 0,
                        "Error": str(error),
                    }
                )
        return pd.DataFrame(records)

    def delete(self, project_id: str) -> Path:
        source = self.path_for(project_id)
        if not source.exists():
            raise ProjectError("Project file does not exist.")
        destination = self.trash_dir / f"{source.stem}_{int(time.time())}.json"
        shutil.move(str(source), str(destination))
        return destination

    def duplicate(self, project_id: str, new_name: str | None = None) -> dict[str, Any]:
        project = self.load(project_id)
        project["project_id"] = str(uuid.uuid4())
        project["name"] = new_name or f"{project.get('name', 'Project')} copy"
        project["created_at"] = utc_now_iso()
        project["model_runs"] = []
        project["workspace_snapshots"] = []
        project["audit_log"] = [
            {
                "timestamp": utc_now_iso(),
                "action": "Project duplicated",
                "details": f"Copied from {project_id}",
            }
        ]
        return self.save(project)

    def import_json(self, uploaded_bytes: bytes) -> dict[str, Any]:
        try:
            payload = json.loads(uploaded_bytes.decode("utf-8"))
        except Exception as error:
            raise ProjectError(f"Uploaded JSON could not be read: {error}") from error
        if "project" in payload and isinstance(payload["project"], Mapping):
            payload = payload["project"]
        payload = deepcopy(dict(payload))
        payload["project_id"] = str(uuid.uuid4())
        payload["name"] = f"{payload.get('name', 'Imported project')} (imported)"
        payload["created_at"] = utc_now_iso()
        payload.setdefault("audit_log", []).append(
            {"timestamp": utc_now_iso(), "action": "Project imported", "details": ""}
        )
        return self.save(payload)

    def bundle_bytes(self, project_id: str) -> bytes:
        project = self.load(project_id)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                f"{slugify(project.get('name', 'project'))}.json",
                json.dumps(json_safe(project), indent=2, ensure_ascii=False),
            )
            archive.writestr(
                "README.txt",
                "Portable AgroLattice project bundle. API keys and source climate datasets are not included.\n",
            )
            for run in project.get("model_runs", []):
                run_id = str(run.get("run_id", "run"))
                archive.writestr(
                    f"model_runs/{run_id}.json",
                    json.dumps(json_safe(run), indent=2, ensure_ascii=False),
                )
            for index, snapshot in enumerate(project.get("workspace_snapshots", []), start=1):
                archive.writestr(
                    f"snapshots/snapshot_{index:03d}.json",
                    json.dumps(json_safe(snapshot), indent=2, ensure_ascii=False),
                )
        return buffer.getvalue()


def append_model_run(project: Mapping[str, Any], run: Mapping[str, Any]) -> dict[str, Any]:
    payload = deepcopy(dict(project))
    payload.setdefault("model_runs", []).append(json_safe(run))
    payload.setdefault("audit_log", []).append(
        {
            "timestamp": utc_now_iso(),
            "action": "Model run added",
            "details": str(run.get("run_id", "")),
        }
    )
    return payload


def append_workspace_snapshot(
    project: Mapping[str, Any],
    *,
    label: str,
    modules: Mapping[str, Any],
) -> dict[str, Any]:
    payload = deepcopy(dict(project))
    payload.setdefault("workspace_snapshots", []).append(
        {
            "snapshot_id": str(uuid.uuid4()),
            "timestamp": utc_now_iso(),
            "label": label,
            "modules": json_safe(modules),
        }
    )
    payload.setdefault("audit_log", []).append(
        {"timestamp": utc_now_iso(), "action": "Workspace snapshot saved", "details": label}
    )
    return payload
