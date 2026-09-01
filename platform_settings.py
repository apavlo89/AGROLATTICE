"""Persistent user/platform preferences for AGROLATTICE 11.16.

Small JSON settings only. Scientific databases remain authoritative and are never
stored here. Writes are atomic so a crash cannot truncate the active settings.
"""
from __future__ import annotations

import json
import os
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

MODULE_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"

DEFAULT_SETTINGS: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "workspace": {
        "default_role": "Researcher",
        "show_advanced_tools": False,
    },
    "tool_catalogue": {
        "favourites": [],
        "recent": [],
    },
    "connections": {
        "dssat_executable": "",
        "apsim_executable": "",
    },
}


class PlatformSettingsStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.path = self.root / "platform_settings.json"

    def load(self) -> dict[str, Any]:
        data = deepcopy(DEFAULT_SETTINGS)
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(raw, Mapping):
                    self._deep_update(data, raw)
            except Exception:
                # A corrupt preference file must never prevent scientific work.
                pass
        data["schema_version"] = SCHEMA_VERSION
        return data

    def save(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        data = deepcopy(DEFAULT_SETTINGS)
        self._deep_update(data, payload)
        data["schema_version"] = SCHEMA_VERSION
        self.root.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix="platform_settings_", suffix=".json", dir=str(self.root))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, ensure_ascii=False, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
        finally:
            try:
                Path(temp_name).unlink(missing_ok=True)
            except Exception:
                pass
        return data

    def update_section(self, section: str, values: Mapping[str, Any]) -> dict[str, Any]:
        data = self.load()
        current = data.setdefault(section, {})
        if not isinstance(current, dict):
            current = {}
            data[section] = current
        current.update(dict(values))
        return self.save(data)

    def toggle_favourite(self, tool_name: str) -> dict[str, Any]:
        data = self.load()
        catalogue = data.setdefault("tool_catalogue", {})
        favourites = [str(x) for x in catalogue.get("favourites", [])]
        if tool_name in favourites:
            favourites.remove(tool_name)
        else:
            favourites.append(tool_name)
        catalogue["favourites"] = favourites
        return self.save(data)

    def record_recent_tool(self, tool_name: str, limit: int = 12) -> dict[str, Any]:
        data = self.load()
        catalogue = data.setdefault("tool_catalogue", {})
        recent = [str(x) for x in catalogue.get("recent", []) if str(x) != tool_name]
        recent.insert(0, str(tool_name))
        catalogue["recent"] = recent[: max(1, int(limit))]
        return self.save(data)

    @staticmethod
    def _deep_update(target: dict[str, Any], source: Mapping[str, Any]) -> None:
        for key, value in source.items():
            if isinstance(value, Mapping) and isinstance(target.get(key), dict):
                PlatformSettingsStore._deep_update(target[key], value)
            else:
                target[key] = deepcopy(value)
