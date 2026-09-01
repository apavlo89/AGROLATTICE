"""Locally bundled boundary editor for AGROLATTICE Streamlit workflows."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

import streamlit as st
import streamlit.components.v1 as components


MODULE_VERSION = "1.0.0"
COMPONENT_DIRECTORY = Path(__file__).resolve().parent / "components" / "agrolattice_boundary_editor"
_component = components.declare_component("agrolattice_boundary_editor", path=str(COMPONENT_DIRECTORY))


def render_boundary_editor(
    *,
    key: str,
    center: tuple[float, float] | Sequence[float],
    initial_geometry: Mapping[str, Any] | None = None,
    reference_geometries: Sequence[Mapping[str, Any]] | None = None,
    zoom: int = 16,
    height: int = 520,
    satellite_default: bool = True,
    drawing_enabled: bool = True,
) -> dict[str, Any] | None:
    """Render a CDN-independent map canvas and return its editable geometry."""
    state_key = f"_agrolattice_local_boundary_{key}"
    deleted_key = f"{state_key}_deleted"
    current = st.session_state.get(state_key)
    if current is None and initial_geometry is not None and not st.session_state.get(deleted_key, False):
        current = dict(initial_geometry)
        st.session_state[state_key] = current
    result = _component(
        key=key,
        center=[float(center[0]), float(center[1])],
        zoom=int(zoom),
        height=int(height),
        initial_geometry=current,
        reference_geometries=list(reference_geometries or []),
        satellite_default=bool(satellite_default),
        drawing_enabled=bool(drawing_enabled),
        default=None,
    )
    if isinstance(result, Mapping):
        action = str(result.get("action") or "")
        geometry = result.get("geometry")
        if action == "deleted" or geometry is None:
            st.session_state.pop(state_key, None)
            st.session_state[deleted_key] = True
            return None
        if isinstance(geometry, Mapping):
            st.session_state[state_key] = dict(geometry)
            st.session_state[deleted_key] = False
            return dict(geometry)
    stored = st.session_state.get(state_key)
    return dict(stored) if isinstance(stored, Mapping) else None


def clear_boundary_editor(key: str) -> None:
    state_key = f"_agrolattice_local_boundary_{key}"
    st.session_state.pop(state_key, None)
    st.session_state.pop(f"{state_key}_deleted", None)
