"""Release 4 shared UI/UX system for the AgroLattice Research Tool.

This module is intentionally independent of the analytical engines. It reads
application state and metadata supplied by the main Streamlit script, then
renders a coherent project-based shell without changing scientific results.
"""
from __future__ import annotations

import html
import importlib.util
import json
import os
import platform
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd
import streamlit as st

UI_RELEASE_VERSION = "4.3.0"

_STATUS_META = {
    "ready": ("READY", "good"),
    "complete": ("COMPLETED", "good"),
    "saved": ("SAVED", "good"),
    "warning": ("ATTENTION", "warn"),
    "stale": ("DATA STALE", "warn"),
    "required": ("RUN REQUIRED", "warn"),
    "missing": ("NOT CONFIGURED", "neutral"),
    "optional": ("OPTIONAL", "neutral"),
    "failed": ("FAILED", "bad"),
    "unvalidated": ("UNVALIDATED", "bad"),
    "info": ("INFO", "info"),
}

GLOSSARY_ROWS = [
    ("TAW", "Total available water in the modelled root zone."),
    ("RAW", "Readily available water before crop water stress is expected."),
    ("Ks", "Water-stress coefficient; values below 1 indicate modelled stress."),
    ("Kc", "Crop coefficient used to relate reference ET to crop ET."),
    ("GDD", "Growing degree days accumulated above a selected base temperature."),
    ("ETo", "FAO-56 reference evapotranspiration."),
    ("NDVI", "Normalised Difference Vegetation Index derived from red and near-infrared reflectance."),
    ("NDMI", "Normalised Difference Moisture Index derived from near-infrared and shortwave-infrared reflectance."),
    ("NDRE", "Normalised Difference Red Edge Index."),
    ("STAC", "SpatioTemporal Asset Catalog used to discover satellite scenes."),
    ("RMSE", "Root mean squared error between observed and predicted values."),
    ("CCC", "Concordance correlation coefficient, combining precision and agreement."),
    ("NSE", "Nash–Sutcliffe efficiency."),
    ("Sen's slope", "Median monotonic change per time unit."),
    ("AquaCrop-OSPy", "Independent Python implementation based on AquaCrop-OS; not the official FAO executable."),
    ("DSSAT", "Decision Support System for Agrotechnology Transfer crop-model suite."),
    ("APSIM", "Agricultural Production Systems sIMulator."),
    ("Flowering synchrony gap", "Male 50% pollen-shed date minus female 50% silking date; positive values mean the male event occurred later."),
    ("Flowering overlap", "Daily overlap between male pollen activity and female silk receptivity, summarised as equivalent full-overlap days or receptivity coverage."),
    ("Male sowing offset", "Male sowing date relative to female sowing; negative values mean the male is sown earlier."),
]

WORKFLOW_STEPS = [
    ("Project", "active_project_id", "Create or activate a field-season project."),
    ("Daily weather", "daily_weather_derived", "Download and derive daily weather."),
    ("Phenology", "phenology_schedule", "Build a stage schedule for the crop season."),
    ("Soil water", "soil_water_balance_results", "Run the root-zone water balance."),
    ("Satellite", "satellite_time_series", "Process a usable Sentinel-2 time series."),
    ("Pollination trial", "pollination_active_trial_id", "Create a mapped maize flowering trial and randomise sowing-offset treatments."),
    ("Crop model", "aquacrop_run", "Run AquaCrop or import an external crop-model result."),
    ("Validation", "release2_validation_metrics", "Compare model predictions with independent observations."),
    ("Economics", "release2_economic_comparison", "Compare water productivity and economic scenarios."),
    ("Publication", "release3_publication_package", "Build a reproducible study package."),
]


def _escape(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def _truthy_artifact(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, pd.DataFrame):
        return not value.empty
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return bool(value)


def status_badge(status: str, label: str | None = None) -> str:
    """Return legacy badge HTML for decorative components outside diagnostics."""
    default_label, css = _STATUS_META.get(status, (status.upper(), "neutral"))
    resolved = label or default_label
    return f'<span class="r4-badge r4-badge-{css}">{_escape(resolved)}</span>'


def native_status_text(status: str, label: str | None = None) -> str:
    """Return an HTML-free status label for native Streamlit rows."""
    default_label, _ = _STATUS_META.get(status, (str(status).upper(), "neutral"))
    resolved = str(label or default_label)
    icon = {
        "ready": "🟢",
        "complete": "🟢",
        "saved": "🟢",
        "warning": "🟠",
        "stale": "🟠",
        "required": "🟠",
        "missing": "⚪",
        "optional": "⚪",
        "failed": "🔴",
        "unvalidated": "🔴",
        "info": "🔵",
    }.get(str(status), "⚪")
    return f"{icon} **{resolved}**"


def install_design_system() -> None:
    """Install global Release 4 CSS and accessibility refinements."""
    st.markdown(
        """
        <style>
        :root {
            --r4-border: color-mix(in srgb, var(--text-color) 14%, transparent);
            --r4-border-strong: color-mix(in srgb, var(--text-color) 23%, transparent);
            --r4-panel: color-mix(in srgb, var(--secondary-background-color) 92%, transparent);
            --r4-panel-soft: color-mix(in srgb, var(--secondary-background-color) 62%, transparent);
            --r4-primary: #176B52;
            --r4-primary-dark: #0D4F3C;
            --r4-blue: #1D69A6;
            --r4-amber: #A35A00;
            --r4-red: #A52A2A;
            --r4-purple: #6650A4;
            --r4-radius: 0.9rem;
            --r4-shadow: 0 8px 28px rgba(0,0,0,0.055);
        }
        html {scroll-behavior: smooth;}
        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 4rem;
            max-width: 1480px;
        }
        [data-testid="stSidebar"] {
            border-right: 1px solid var(--r4-border);
        }
        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1rem;
        }
        [data-testid="stSidebarNav"] span {
            line-height: 1.25;
        }
        [data-testid="stMetric"] {
            background: var(--r4-panel);
            border: 1px solid var(--r4-border);
            border-radius: var(--r4-radius);
            padding: 0.85rem 1rem;
            box-shadow: none;
            min-height: 104px;
        }
        [data-testid="stMetricLabel"] {font-weight: 650;}
        [data-testid="stMetricValue"] {letter-spacing: -0.025em;}
        div[data-testid="stForm"] {
            border: 1px solid var(--r4-border);
            border-radius: var(--r4-radius);
            padding: 1.05rem 1.05rem 0.45rem 1.05rem;
            background: var(--r4-panel-soft);
        }
        div[data-testid="stExpander"] {
            border: 1px solid var(--r4-border);
            border-radius: 0.75rem;
            overflow: hidden;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--r4-border);
            border-radius: 0.75rem;
            overflow: hidden;
        }
        div[data-baseweb="tab-list"] {
            gap: 0.25rem;
            border-bottom: 1px solid var(--r4-border);
        }
        button[data-baseweb="tab"] {
            border-radius: 0.6rem 0.6rem 0 0;
            padding-left: 0.9rem;
            padding-right: 0.9rem;
        }
        .stButton > button[kind="primary"],
        .stDownloadButton > button[kind="primary"] {
            background: var(--r4-primary);
            border-color: var(--r4-primary);
        }
        .stButton > button[kind="primary"]:hover,
        .stDownloadButton > button[kind="primary"]:hover {
            background: var(--r4-primary-dark);
            border-color: var(--r4-primary-dark);
        }
        .stButton > button, .stDownloadButton > button {
            border-radius: 0.7rem;
            min-height: 2.65rem;
            font-weight: 650;
        }
        input:focus, textarea:focus, [data-baseweb="select"]:focus-within {
            outline: 2px solid color-mix(in srgb, var(--r4-primary) 55%, transparent) !important;
            outline-offset: 1px;
        }
        .r4-page-shell {margin-bottom: 0.9rem;}
        .r4-page-kicker {
            font-size: 0.75rem;
            font-weight: 750;
            letter-spacing: 0.095em;
            text-transform: uppercase;
            opacity: 0.68;
        }
        .r4-page-title {
            font-size: clamp(1.8rem, 3vw, 2.45rem);
            font-weight: 780;
            line-height: 1.11;
            letter-spacing: -0.035em;
            margin: 0.12rem 0 0.38rem 0;
        }
        .r4-page-subtitle {
            font-size: 1.02rem;
            line-height: 1.55;
            opacity: 0.78;
            max-width: 980px;
        }
        .r4-context {
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 0;
            margin: 0.9rem 0 1.25rem 0;
            border: 1px solid var(--r4-border);
            border-radius: var(--r4-radius);
            background: var(--r4-panel-soft);
            overflow: hidden;
        }
        .r4-context-item {
            padding: 0.72rem 0.82rem;
            min-width: 0;
            border-right: 1px solid var(--r4-border);
        }
        .r4-context-item:last-child {border-right: none;}
        .r4-label {
            font-size: 0.66rem;
            font-weight: 750;
            letter-spacing: 0.075em;
            text-transform: uppercase;
            opacity: 0.58;
            margin-bottom: 0.18rem;
        }
        .r4-value {
            font-size: 0.88rem;
            font-weight: 650;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .r4-grid {
            display: grid;
            grid-template-columns: repeat(12, minmax(0, 1fr));
            gap: 0.85rem;
        }
        .r4-card {
            border: 1px solid var(--r4-border);
            background: var(--r4-panel);
            border-radius: var(--r4-radius);
            padding: 1rem 1.05rem;
            box-shadow: none;
            height: 100%;
        }
        .r4-card-emphasis {
            background: linear-gradient(135deg, color-mix(in srgb, var(--r4-primary) 11%, var(--secondary-background-color)), var(--secondary-background-color));
            border-color: color-mix(in srgb, var(--r4-primary) 28%, transparent);
        }
        .r4-card h3, .r4-card h4 {margin: 0 0 0.38rem 0;}
        .r4-card p {margin: 0.2rem 0; line-height: 1.48;}
        .r4-muted {opacity: 0.7;}
        .r4-badge {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.16rem 0.52rem;
            font-size: 0.64rem;
            line-height: 1.35;
            font-weight: 800;
            letter-spacing: 0.05em;
            white-space: nowrap;
            border: 1px solid transparent;
        }
        .r4-badge-good {background: rgba(23,107,82,0.13); color: #176B52; border-color: rgba(23,107,82,0.25);}
        .r4-badge-warn {background: rgba(214,126,0,0.14); color: #8A4B00; border-color: rgba(214,126,0,0.28);}
        .r4-badge-bad {background: rgba(172,45,45,0.12); color: #992D2D; border-color: rgba(172,45,45,0.25);}
        .r4-badge-info {background: rgba(29,105,166,0.12); color: #1D69A6; border-color: rgba(29,105,166,0.25);}
        .r4-badge-neutral {background: rgba(100,100,100,0.10); color: inherit; border-color: var(--r4-border);}
        .r4-status-row {
            display: grid;
            grid-template-columns: minmax(130px, 0.9fr) auto minmax(180px, 1.4fr);
            gap: 0.75rem;
            align-items: center;
            padding: 0.63rem 0;
            border-bottom: 1px solid var(--r4-border);
        }
        .r4-status-row:last-child {border-bottom: none;}
        .r4-status-name {font-weight: 680;}
        .r4-status-detail {font-size: 0.84rem; opacity: 0.7;}
        .r4-step {
            display: grid;
            grid-template-columns: 28px 1fr auto;
            gap: 0.65rem;
            align-items: start;
            padding: 0.58rem 0;
            border-bottom: 1px solid var(--r4-border);
        }
        .r4-step:last-child {border-bottom: 0;}
        .r4-step-dot {
            width: 22px; height: 22px; border-radius: 999px;
            display:flex; align-items:center; justify-content:center;
            font-size: 0.72rem; font-weight:800;
            background: rgba(100,100,100,0.12);
        }
        .r4-step-dot.done {background: rgba(23,107,82,0.16); color:#176B52;}
        .r4-step-title {font-weight: 680;}
        .r4-step-help {font-size: 0.81rem; opacity: 0.67; margin-top: 0.12rem;}
        .r4-sidebar-card {
            border: 1px solid var(--r4-border);
            border-radius: 0.75rem;
            padding: 0.75rem 0.8rem;
            background: var(--r4-panel-soft);
            margin: 0.5rem 0 0.8rem 0;
        }
        .r4-sidebar-title {font-weight:750; margin-bottom:0.2rem;}
        .r4-sidebar-meta {font-size:0.78rem; opacity:0.72; line-height:1.45;}
        .r4-error-panel {
            border: 1px solid rgba(172,45,45,0.3);
            background: rgba(172,45,45,0.07);
            border-radius: var(--r4-radius);
            padding: 1rem 1.05rem;
        }
        @media (max-width: 1000px) {
            .r4-context {grid-template-columns: repeat(3, minmax(0,1fr));}
            .r4-context-item:nth-child(3n) {border-right:none;}
            .r4-context-item {border-bottom:1px solid var(--r4-border);}
        }
        @media (max-width: 650px) {
            .block-container {padding-left: 0.8rem; padding-right:0.8rem;}
            .r4-context {grid-template-columns: 1fr 1fr;}
            .r4-context-item:nth-child(3n) {border-right:1px solid var(--r4-border);}
            .r4-context-item:nth-child(2n) {border-right:none;}
            .r4-status-row {grid-template-columns: 1fr auto;}
            .r4-status-detail {grid-column:1 / -1;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(
    kicker: str,
    title: str,
    subtitle: str,
    *,
    active_project: Mapping[str, Any] | None = None,
    show_context: bool = True,
) -> None:
    st.markdown(
        f"""
        <div class="r4-page-shell">
          <div class="r4-page-kicker">{_escape(kicker)}</div>
          <div class="r4-page-title">{_escape(title)}</div>
          <div class="r4-page-subtitle">{_escape(subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if show_context and active_project:
        render_project_context(active_project)


def render_project_context(project: Mapping[str, Any]) -> None:
    location = project.get("location", {}) or {}
    season = project.get("season", {}) or {}
    area = location.get("field_area_ha")
    area_text = f"{float(area):,.2f} ha" if area not in (None, "") else "Not defined"
    updated = str(project.get("updated_at") or "")
    if "T" in updated:
        updated = updated.split("T", 1)[0]
    fields = [
        ("Project", project.get("name") or "Untitled"),
        ("Location", location.get("name") or "Not defined"),
        ("Crop", season.get("crop") or "Not defined"),
        ("Planting", season.get("planting_date") or "Not defined"),
        ("Field", area_text),
        ("Project state", f"{project.get('status', 'Active')} · {updated or 'unsaved'}"),
    ]
    items = "".join(
        f'<div class="r4-context-item"><div class="r4-label">{_escape(label)}</div><div class="r4-value" title="{_escape(value)}">{_escape(value)}</div></div>'
        for label, value in fields
    )
    st.markdown(f'<div class="r4-context">{items}</div>', unsafe_allow_html=True)


def render_sidebar_summary(
    *,
    app_version: str,
    years: Sequence[int],
    variable_count: int,
    active_project: Mapping[str, Any] | None,
) -> None:
    st.markdown("## AgroLattice")
    st.caption("Global agricultural intelligence platform")
    if active_project:
        season = active_project.get("season", {}) or {}
        location = active_project.get("location", {}) or {}
        st.markdown(
            f"""
            <div class="r4-sidebar-card">
              <div class="r4-sidebar-title">{_escape(active_project.get('name') or 'Active project')}</div>
              <div class="r4-sidebar-meta">{_escape(season.get('crop') or 'Crop not set')} · {_escape(season.get('planting_date') or 'Planting not set')}<br>{_escape(location.get('name') or 'Location not set')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="r4-sidebar-card"><div class="r4-sidebar-title">No active project</div><div class="r4-sidebar-meta">Create or activate a project to connect analyses across pages.</div></div>',
            unsafe_allow_html=True,
        )
    if years:
        st.caption(f"Data {min(years)}–{max(years)} · {variable_count} variables")
    st.caption(f"App {app_version} · UI {UI_RELEASE_VERSION}")


def _readiness_rows(context: Mapping[str, Any]) -> list[dict[str, str]]:
    state = context.get("state", {}) or {}
    active_project = context.get("active_project")
    dataset_exists = bool(context.get("dataset_exists"))
    dataset_detail = str(context.get("dataset_detail") or "Historical dataset unavailable")
    aquacrop = context.get("aquacrop_status", {}) or {}
    satellite = context.get("satellite_status", {}) or {}
    openai_status = str(state.get("openai_key_status") or "Not tested")
    field_operations = context.get("field_operations_status", {}) or {}
    twin = context.get("agrolattice_twin_status", {}) or {}
    return [
        {
            "name": "Active project",
            "status": "ready" if active_project else "required",
            "detail": active_project.get("name") if active_project else "Create or activate a field-season project.",
        },
        {
            "name": "Historical climate",
            "status": "ready" if dataset_exists else "failed",
            "detail": dataset_detail,
        },
        {
            "name": "Field operations",
            "status": "ready" if int(field_operations.get("fields", 0) or 0) > 0 else "optional",
            "detail": (
                f"{int(field_operations.get('farms', 0) or 0)} farms, {int(field_operations.get('fields', 0) or 0)} mapped fields, "
                f"{int(field_operations.get('open_tasks', 0) or 0)} open tasks and {int(field_operations.get('open_alerts', 0) or 0)} active alerts."
                if not field_operations.get("error") else f"Status check failed: {field_operations.get('error')}"
            ),
        },
        {
            "name": "AgroLattice Twin",
            "status": "ready" if twin.get("ready") else "optional",
            "detail": (
                f"{int(twin.get('twins', 0) or 0)} configured twin(s) and {int(twin.get('snapshots', 0) or 0)} saved state snapshot(s)."
                if not twin.get("error") else f"Status check failed: {twin.get('error')}"
            ),
        },
        {
            "name": "Daily weather",
            "status": "ready" if _truthy_artifact(state.get("daily_weather_derived")) else "required",
            "detail": "Daily NASA POWER data are in memory." if _truthy_artifact(state.get("daily_weather_derived")) else "Run Daily weather & phenology.",
        },
        {
            "name": "Root-zone model",
            "status": "ready" if _truthy_artifact(state.get("soil_water_balance_results")) else "required",
            "detail": "Module B result is available." if _truthy_artifact(state.get("soil_water_balance_results")) else "Run Soil-water balance after weather and phenology.",
        },
        {
            "name": "Satellite monitoring",
            "status": "ready" if _truthy_artifact(state.get("satellite_time_series")) else ("ready" if satellite.get("ready") else "optional"),
            "detail": "Processed field time series available." if _truthy_artifact(state.get("satellite_time_series")) else satellite.get("message", "Optional Sentinel-2 layer not yet processed."),
        },
        {
            "name": "AquaCrop-OSPy",
            "status": "ready" if aquacrop.get("installed") else "missing",
            "detail": aquacrop.get("message", "Optional backend not installed."),
        },
        {
            "name": "OpenAI interpretation",
            "status": "ready" if bool(state.get("openai_key_valid")) else "optional",
            "detail": openai_status,
        },
        {
            "name": "External validation",
            "status": "complete" if _truthy_artifact(state.get("release2_validation_metrics")) else "unvalidated",
            "detail": "Validation metrics available." if _truthy_artifact(state.get("release2_validation_metrics")) else "No independent validation result is currently loaded.",
        },
    ]


def render_readiness(rows: Sequence[Mapping[str, Any]]) -> None:
    """Render readiness with native Streamlit elements only."""
    with st.container(border=True):
        for index, row in enumerate(rows):
            name_column, status_column, detail_column = st.columns(
                [1.10, 0.92, 2.30], gap="small", vertical_alignment="center"
            )
            with name_column:
                st.write(f"**{str(row.get('name') or '')}**")
            with status_column:
                st.markdown(native_status_text(str(row.get('status') or 'info')))
            with detail_column:
                st.caption(str(row.get('detail') or ''))
            if index < len(rows) - 1:
                st.divider()


def _workflow_progress(state: Mapping[str, Any]) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    complete = 0
    for title, key, help_text in WORKFLOW_STEPS:
        done = bool(state.get(key)) if key == "active_project_id" else _truthy_artifact(state.get(key))
        complete += int(done)
        rows.append({"title": title, "key": key, "done": done, "help": help_text})
    return rows, complete


def render_workflow(state: Mapping[str, Any]) -> None:
    """Render workflow progress with native Streamlit elements only."""
    rows, complete = _workflow_progress(state)
    st.progress(
        complete / max(1, len(rows)),
        text=f"{complete} of {len(rows)} workflow layers ready",
    )
    next_found = False
    with st.container(border=True):
        for index, row in enumerate(rows, start=1):
            done = bool(row["done"])
            is_next = not done and not next_found
            if is_next:
                next_found = True
            marker_column, description_column, status_column = st.columns(
                [0.38, 2.50, 0.92], gap="small", vertical_alignment="center"
            )
            with marker_column:
                st.markdown(f"### {'✓' if done else index}")
            with description_column:
                st.write(f"**{row['title']}**")
                st.caption(str(row['help']))
            with status_column:
                state_name = "complete" if done else ("required" if is_next else "missing")
                state_label = "DONE" if done else ("NEXT" if is_next else "PENDING")
                st.markdown(native_status_text(state_name, state_label))
            if index < len(rows):
                st.divider()


def render_command_centre(context: Mapping[str, Any]) -> None:
    """Render the project-based Release 4 home command centre."""
    active_project = context.get("active_project")
    render_page_header(
        "AgroLattice",
        "Research command centre",
        "Connect climate, crop, water, satellite, field operations and digital-twin intelligence in one defensible workflow.",
        active_project=active_project,
        show_context=bool(active_project),
    )

    state = context.get("state", {}) or {}
    coverage = context.get("coverage", {}) or {}
    metrics = st.columns(4)
    metrics[0].metric("Matched locations", f"{int(coverage.get('locations', 0)):,}")
    metrics[1].metric("Climate coverage", str(coverage.get("period", "Unavailable")))
    metrics[2].metric("Variables", f"{int(coverage.get('variables', 0)):,}")
    metrics[3].metric("Usable values", f"{float(coverage.get('usable_percent', 0.0)):.1f}%")

    if not state.get("release4_onboarding_dismissed"):
        st.markdown("### First-run readiness")
        st.info(
            "Start by confirming the datasets, activating a project, and checking optional model connections. "
            "The diagnostics page can be reopened at any time."
        )
        onboarding_cols = st.columns(2)
        if onboarding_cols[0].button("Mark onboarding as reviewed", type="primary", width="stretch", key="release4_dismiss_onboarding"):
            st.session_state.release4_onboarding_dismissed = True
            st.rerun()
        onboarding_cols[1].caption("Open **System diagnostics** from Data & setup for the full check.")

    left, right = st.columns([1.05, 0.95], gap="large")
    with left:
        st.markdown("### Workflow progress")
        render_workflow(state)
    with right:
        st.markdown("### System readiness")
        render_readiness(_readiness_rows(context))

    st.markdown("### Continue your research")
    cards = st.columns(4)
    card_data = [
        ("1", "Build the field-season record", "Projects", "Define the crop, location, dates, soil, irrigation and field geometry once."),
        ("2", "Connect climate to crop stage", "Daily weather & phenology", "Retrieve daily weather and establish the crop-stage timeline."),
        ("3", "Test water and vegetation response", "Soil-water + satellite", "Compare root-zone stress with remotely sensed vegetation dynamics."),
        ("4", "Validate and publish", "Validation + study builder", "Quantify performance, disagreement and provenance before reporting results."),
    ]
    for column, (number, title, destination, description) in zip(cards, card_data):
        with column:
            st.markdown(
                f"""
                <div class="r4-card {'r4-card-emphasis' if number == '1' and not active_project else ''}">
                  <div class="r4-label">STEP {number} · {destination}</div>
                  <h4>{_escape(title)}</h4>
                  <p class="r4-muted">{_escape(description)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    recent_projects = context.get("project_library")
    recent_runs = context.get("recent_runs")
    project_col, run_col = st.columns(2, gap="large")
    with project_col:
        st.markdown("### Recent projects")
        if isinstance(recent_projects, pd.DataFrame) and not recent_projects.empty:
            visible = [column for column in ["Name", "Crop", "Location", "Planting date", "Updated", "Model runs"] if column in recent_projects.columns]
            st.dataframe(recent_projects.head(8)[visible], hide_index=True, width="stretch")
        else:
            st.info("No saved projects yet. Create the first field-season project from **Workspace → Projects**.")
    with run_col:
        st.markdown("### Recent model and analysis records")
        if isinstance(recent_runs, pd.DataFrame) and not recent_runs.empty:
            st.dataframe(recent_runs.head(8), hide_index=True, width="stretch")
        else:
            st.info("No project model runs are recorded yet.")

    with st.expander("Dataset and scientific-use notes"):
        st.write(
            "The platform integrates historical climate, daily weather, crop screening, soil-water modelling, satellite observations, "
            "process-based crop models, validation and publication tools. Model outputs remain conditional on the selected inputs and require independent validation."
        )
        variables = context.get("available_variables") or []
        if variables:
            st.dataframe(pd.DataFrame({"Available variable": variables}), hide_index=True, width="stretch")


def dependency_row(module_name: str, friendly_name: str | None = None, optional: bool = False) -> dict[str, Any]:
    available = importlib.util.find_spec(module_name) is not None
    return {
        "Component": friendly_name or module_name,
        "Status": "Available" if available else ("Optional missing" if optional else "Missing"),
        "Required": "No" if optional else "Yes",
    }


def diagnostic_report(context: Mapping[str, Any]) -> dict[str, Any]:
    paths = context.get("paths", {}) or {}
    files = []
    for label, raw_path in paths.items():
        path = Path(raw_path) if raw_path else None
        files.append(
            {
                "label": label,
                "path": str(path) if path else None,
                "exists": bool(path and path.exists()),
                "size_bytes": int(path.stat().st_size) if path and path.exists() and path.is_file() else None,
                "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if path and path.exists() else None,
            }
        )
    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "app_version": context.get("app_version"),
        "ui_version": UI_RELEASE_VERSION,
        "python": sys.version,
        "platform": platform.platform(),
        "working_directory": os.getcwd(),
        "files": files,
        "readiness": _readiness_rows(context),
        "session_artifacts": {
            key: _truthy_artifact(value)
            for key, value in (context.get("state", {}) or {}).items()
            if key in {item[1] for item in WORKFLOW_STEPS}
        },
    }


def render_system_diagnostics(context: Mapping[str, Any]) -> None:
    render_page_header(
        "Data & setup",
        "System diagnostics",
        "Verify datasets, analytical engines, optional model backends and saved-workspace paths before running a study.",
        active_project=context.get("active_project"),
    )
    overview_tab, files_tab, packages_tab, report_tab = st.tabs(["Readiness", "Files & storage", "Python packages", "Diagnostic report"])
    with overview_tab:
        render_readiness(_readiness_rows(context))
        st.markdown("### Workflow layers currently available")
        render_workflow(context.get("state", {}) or {})
    with files_tab:
        report = diagnostic_report(context)
        file_frame = pd.DataFrame(report["files"])
        if file_frame.empty:
            st.info("No file paths were supplied to the diagnostic engine.")
        else:
            st.dataframe(file_frame, hide_index=True, width="stretch")
        cache_paths = [Path(value) for key, value in (context.get("paths", {}) or {}).items() if value and "cache" in key.casefold()]
        cache_size = 0
        cache_files = 0
        for path in cache_paths:
            if path.exists() and path.is_dir():
                for item in path.rglob("*"):
                    if item.is_file():
                        cache_files += 1
                        try:
                            cache_size += item.stat().st_size
                        except OSError:
                            pass
        st.metric("Cache footprint", f"{cache_size / (1024 ** 2):,.1f} MB", f"{cache_files:,} files")
    with packages_tab:
        dependencies = [
            dependency_row("streamlit", "Streamlit"),
            dependency_row("pandas", "pandas"),
            dependency_row("numpy", "NumPy"),
            dependency_row("plotly", "Plotly"),
            dependency_row("folium", "Folium"),
            dependency_row("streamlit_folium", "streamlit-folium"),
            dependency_row("statsmodels", "statsmodels"),
            dependency_row("sklearn", "scikit-learn"),
            dependency_row("rasterio", "rasterio", optional=True),
            dependency_row("shapely", "Shapely", optional=True),
            dependency_row("aquacrop", "AquaCrop-OSPy", optional=True),
            dependency_row("docx", "python-docx", optional=True),
            dependency_row("openai", "OpenAI Python SDK", optional=True),
        ]
        st.dataframe(pd.DataFrame(dependencies), hide_index=True, width="stretch")
        st.caption("DSSAT and APSIM are external executables and are checked from their dedicated interoperability page.")
    with report_tab:
        report = diagnostic_report(context)
        st.json(report, expanded=False)
        st.download_button(
            "Download diagnostic report",
            json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8"),
            file_name="mexico_agroclimate_diagnostic_report.json",
            mime="application/json",
            width="stretch",
            key="release4_download_diagnostic_report",
        )


def render_user_guide(context: Mapping[str, Any]) -> None:
    render_page_header(
        "Help",
        "Quick guide & glossary",
        "Use the intended project workflow, understand the main analytical layers, and resolve common setup mistakes.",
        active_project=context.get("active_project"),
    )
    start_tab, workflow_tab, glossary_tab, troubleshooting_tab = st.tabs(["Getting started", "Recommended workflow", "Glossary", "Troubleshooting"])
    with start_tab:
        st.markdown("### Five-minute start")
        steps = [
            "Open **Projects** and create or activate a field-season research record.",
            "Open **Farm portfolio & mapped fields** to register the farm, exact field boundary, crop season and team workflow.",
            "Run **Daily weather & phenology** for the project location and crop season.",
            "Run **Soil-water balance** using a defensible soil profile and irrigation strategy.",
            "Process the field in **Satellite crop monitoring** when a geometry is available.",
            "For hybrid-maize seed research, create mapped plots in **Maize flowering research**, collect daily flowering observations, and link the exact plot AOI to Sentinel-2.",
            "Use a crop model, then upload independent observations in the **Validation Centre** before treating predictions as validated.",
        ]
        for index, text in enumerate(steps, start=1):
            st.markdown(f"**{index}.** {text}")
        st.info("Advanced pages remain available in Full research interface mode from the sidebar.")
    with workflow_tab:
        workflow = pd.DataFrame(
            [
                ("Project", "Field-season identity and shared assumptions", "Projects"),
                ("Field operations", "Mapped fields, tasks, scouting, sensors, alerts and field diary", "Field operations & precision agriculture"),
                ("Weather", "Daily observed/reanalysis forcing and derived metrics", "Daily weather & phenology"),
                ("Phenology", "Stage timing and weather exposure", "Daily weather & phenology"),
                ("Water", "Root-zone depletion, stress and irrigation scenarios", "Soil-water balance"),
                ("Remote sensing", "Sentinel-2 vegetation and moisture indices", "Satellite crop monitoring"),
                ("Maize flowering", "Mapped plots, pollen-shed/silking overlap, GDD and sowing-offset models", "Maize flowering research"),
                ("Crop models", "AquaCrop, DSSAT or APSIM simulation", "Crop models"),
                ("Validation", "Observed-versus-predicted performance", "Validation Centre"),
                ("Decision analysis", "Water productivity, economics and model ensembles", "Crop & water / Validation"),
                ("Reporting", "Reproducible manuscript and supplement package", "Study & publication builder"),
            ],
            columns=["Layer", "Purpose", "Where to go"],
        )
        st.dataframe(workflow, hide_index=True, width="stretch")
    with glossary_tab:
        st.dataframe(pd.DataFrame(GLOSSARY_ROWS, columns=["Term", "Meaning"]), hide_index=True, width="stretch")
    with troubleshooting_tab:
        issues = {
            "The app starts but datasets are missing": "Place worldcities.csv in Datasets and the Mexico climate file at Datasets/countries/mexico/agroclimate_longformat.csv. Release 10.2 automatically migrates the older Mexico filename.",
            "A result disappeared after changing an input": "Many pages invalidate stale results when inputs change. Re-run the analysis using the primary action button.",
            "NASA or STAC requests fail": "Retry later, use the cache when appropriate, or select an alternative satellite provider. Public services can be temporarily unavailable.",
            "AquaCrop is unavailable": "Run the optional AquaCrop installer in the same Python environment that launches Streamlit.",
            "DSSAT or APSIM cannot run": "Install the external program separately and point the interoperability page to the correct executable.",
            "ChatGPT interpretation is unavailable": "Configure and test an OpenAI API key in ChatGPT settings. Analytical results do not depend on the AI feature.",
            "OneDrive blocks a file update": "Close programs using the file, retry, or move the working folder outside a synchronised directory.",
        }
        for title, answer in issues.items():
            with st.expander(title):
                st.write(answer)


def render_friendly_exception(error: BaseException) -> None:
    st.markdown(
        f"""
        <div class="r4-error-panel">
          <div class="r4-label">ANALYSIS COULD NOT COMPLETE</div>
          <h3>{_escape(type(error).__name__)}</h3>
          <p>{_escape(str(error) or 'An unexpected error occurred.')}</p>
          <p class="r4-muted">Review the input state, retry the action, or download a diagnostic report from System diagnostics.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("Show technical details"):
        st.code("".join(traceback.format_exception(type(error), error, error.__traceback__)))
