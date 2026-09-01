"""AGROLATTICE Experiment Command Centre (introduced in Release 11.13; current Release 11.15).

A researcher-facing layer over the persistent Maize Synchrony experiment store.
The module deliberately keeps trial design, spatial assignment, field observations,
mechanistic development, outcomes, statistical analysis and provenance connected
without forcing every expensive workbench to execute on each Streamlit rerun.
"""
from __future__ import annotations

import io
import json
import math
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

try:
    import statsmodels.formula.api as smf
except Exception:  # pragma: no cover
    smf = None

try:
    from shapely.geometry import shape
except Exception:  # pragma: no cover
    shape = None

from maize_pollination_lab import (
    PollinationDatabase,
    PollinationLabError,
    _plots_map,
    build_model_table,
    compute_plot_synchrony_metrics,
    treatment_summary,
)

MODULE_VERSION = "1.0.0"

LIFECYCLE = [
    "Draft", "Designed", "Randomised", "Field-Ready", "Data Collection",
    "Completed", "Analysed", "Archived",
]


def _now() -> pd.Timestamp:
    return pd.Timestamp.now(tz="UTC")


def _safe_frame(func: Callable[[], pd.DataFrame]) -> pd.DataFrame:
    try:
        frame = func()
        return frame if isinstance(frame, pd.DataFrame) else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def _active_trial(db: PollinationDatabase) -> tuple[str | None, dict[str, Any] | None]:
    trials = db.list_trials()
    if trials.empty:
        return None, None
    ids = trials["Trial ID"].astype(str).tolist()
    active = str(st.session_state.get("pollination_active_trial_id") or "")
    if active not in ids:
        active = ids[0]
        st.session_state.pollination_active_trial_id = active
    try:
        return active, db.get_trial(active)
    except Exception:
        return None, None


def _trial_selector(db: PollinationDatabase) -> str | None:
    trials = db.list_trials()
    if trials.empty:
        st.info("No experiments are stored yet. Open Design to create the first mapped trial.")
        return None
    labels: dict[str, str] = {}
    for _, row in trials.iterrows():
        label = f"{row.get('Trial','Trial')} · {row.get('Site','')} · {row.get('Year','')}"
        labels[label] = str(row.get("Trial ID"))
    active = str(st.session_state.get("pollination_active_trial_id") or "")
    current_label = next((label for label, identifier in labels.items() if identifier == active), next(iter(labels)))
    chosen = st.selectbox("Active experiment", list(labels), index=list(labels).index(current_label), key="experiment_cc_trial_selector")
    selected = labels[chosen]
    if selected != active:
        st.session_state.pollination_active_trial_id = selected
        st.rerun()
    return selected


def _context_line(trial: Mapping[str, Any], field_db=None) -> str:
    field = None
    if field_db is not None and trial.get("source_field_id"):
        try:
            field = field_db.field(str(trial.get("source_field_id")))
        except Exception:
            field = None
    parts = [
        str((field or {}).get("farm_name") or trial.get("site_name") or "Research site"),
        str((field or {}).get("name") or "Mapped field"),
        str(trial.get("season_year") or "Season not set"),
        str(trial.get("name") or "Experiment"),
    ]
    return "  →  ".join(parts)


def _snapshot(db: PollinationDatabase, trial_id: str) -> dict[str, Any]:
    trial = db.get_trial(trial_id)
    plots = _safe_frame(lambda: db.list_plots(trial_id))
    obs = _safe_frame(lambda: db.observations(trial_id))
    leaf = _safe_frame(lambda: db.leaf_observations(trial_id))
    phenology = _safe_frame(lambda: db.phenology_events(trial_id))
    harvest = _safe_frame(lambda: db.harvest(trial_id))
    weather = _safe_frame(lambda: db.weather(trial_id))
    satellite = _safe_frame(lambda: db.satellite_links(trial_id))
    protocol = db.experiment_protocol(trial_id)
    protocol_versions = _safe_frame(lambda: db.protocol_versions(trial_id))
    factors = _safe_frame(lambda: db.factor_definitions(trial_id))
    requirements = _safe_frame(lambda: db.measurement_requirements(trial_id))
    completeness = _safe_frame(lambda: db.data_completeness_matrix(trial_id))
    audit = _safe_frame(lambda: db.trial_audit(trial_id))
    designs = _safe_frame(lambda: db.design_versions(trial_id))
    return {
        "trial": trial, "plots": plots, "obs": obs, "leaf": leaf,
        "phenology": phenology, "harvest": harvest, "weather": weather,
        "satellite": satellite, "protocol": protocol, "protocol_versions": protocol_versions, "factors": factors,
        "requirements": requirements, "completeness": completeness,
        "audit": audit, "designs": designs,
    }


def _observation_latest(snapshot: Mapping[str, Any]) -> pd.Timestamp | None:
    values: list[pd.Timestamp] = []
    for key, column in (("obs", "Date"), ("leaf", "Observation date"), ("phenology", "Female flowering date"), ("harvest", "Harvest date")):
        frame = snapshot.get(key)
        if not isinstance(frame, pd.DataFrame) or frame.empty or column not in frame:
            continue
        parsed = pd.to_datetime(frame[column], errors="coerce", utc=True).dropna()
        if not parsed.empty:
            values.append(parsed.max())
    return max(values) if values else None


def _required_unit_count(trial: Mapping[str, Any]) -> int:
    densities = list(trial.get("sowing_density_levels") or []) or [trial.get("planting_density_plants_ha")]
    dates = list(trial.get("sowing_date_levels") or []) or [trial.get("female_sowing_date")]
    offsets = list(trial.get("sowing_offset_levels") or [0])
    pairings = list(trial.get("parent_pairings") or []) or [{}]
    treatment_count = max(1, len(densities)) * max(1, len(dates)) * max(1, len(offsets)) * max(1, len(pairings))
    return int(trial.get("blocks") or 0) * int(trial.get("replicates_per_treatment") or 0) * treatment_count


def _default_factor_rows(trial: Mapping[str, Any]) -> pd.DataFrame:
    rows = [
        {"Factor": "Female genotype", "Type": "Categorical", "Role": "Treatment", "Levels": ", ".join(map(str, trial.get("female_parent_levels") or [])), "Unit": "", "Notes": "Parent identity"},
        {"Factor": "Male genotype", "Type": "Categorical", "Role": "Treatment", "Levels": ", ".join(map(str, trial.get("male_parent_levels") or [])), "Unit": "", "Notes": "Parent identity"},
        {"Factor": "Sowing density", "Type": "Quantitative", "Role": "Treatment", "Levels": ", ".join(map(str, trial.get("sowing_density_levels") or [])), "Unit": "plants/ha", "Notes": ""},
        {"Factor": "Female sowing date", "Type": "Date", "Role": "Treatment", "Levels": ", ".join(map(str, trial.get("sowing_date_levels") or [])), "Unit": "date", "Notes": ""},
        {"Factor": "Male–female sowing difference", "Type": "Quantitative", "Role": "Treatment", "Levels": ", ".join(map(str, trial.get("sowing_offset_levels") or [])), "Unit": "days", "Notes": "Positive means male later"},
        {"Factor": "Block", "Type": "Categorical", "Role": "Blocking", "Levels": ", ".join(str(v) for v in range(1, int(trial.get("blocks") or 0)+1)), "Unit": "", "Notes": "Design stratum"},
    ]
    return pd.DataFrame(rows)


def _priority_actions(snapshot: Mapping[str, Any]) -> list[dict[str, str]]:
    trial = snapshot["trial"]
    plots = snapshot["plots"]
    obs = snapshot["obs"]
    leaf = snapshot["leaf"]
    harvest = snapshot["harvest"]
    weather = snapshot["weather"]
    protocol = snapshot["protocol"]
    required = _required_unit_count(trial)
    actions: list[dict[str, str]] = []
    if not protocol:
        actions.append({"title": "Write and lock the experimental protocol", "detail": "Objective, hypotheses, outcomes and planned analysis are not yet versioned.", "view": "Design"})
    if required and len(plots) != required:
        actions.append({"title": "Complete the mapped randomisation", "detail": f"{len(plots)} of {required} required experimental units are stored.", "view": "Spatial layout"})
    if plots.empty:
        actions.append({"title": "Create experimental-unit geometry", "detail": "No independently treated units are mapped yet.", "view": "Spatial layout"})
    elif obs.empty:
        actions.append({"title": "Start flowering observations", "detail": "No male-shedding/female-silking records are stored for this experiment.", "view": "Data collection"})
    if weather.empty:
        actions.append({"title": "Link or retrieve field weather", "detail": "Stage-specific G×E×M exposure and mechanistic development need approved weather evidence.", "view": "Development & synchrony"})
    if not plots.empty and not obs.empty:
        observed_units = obs.get("Plot ID", pd.Series(dtype=str)).astype(str).nunique() if "Plot ID" in obs else 0
        if observed_units < len(plots):
            actions.append({"title": "Fill observation gaps", "detail": f"Flowering data cover {observed_units} of {len(plots)} experimental units.", "view": "Data collection"})
    if not plots.empty and harvest.empty and str(trial.get("status") or "").casefold() in {"completed", "analysed", "archived"}:
        actions.append({"title": "Record harvest outcomes", "detail": "The trial is marked complete but no plot-level harvest outcomes are stored.", "view": "Outcomes"})
    if leaf.empty and not obs.empty:
        actions.append({"title": "Add tagged-plant development observations", "detail": "Leaf counts strengthen mechanistic parent calibration and development checks.", "view": "Data collection"})
    return actions[:6]


def _route_button(label: str, destination: str, *, key: str) -> None:
    if st.button(label, key=key, width="stretch"):
        st.session_state["experiment_cc_requested_view"] = destination
        st.rerun()


def _consume_requested_view(options: Sequence[str]) -> str:
    requested = st.session_state.pop("experiment_cc_requested_view", None)
    current = str(st.session_state.get("experiment_cc_view") or options[0])
    if requested in options:
        current = str(requested)
        st.session_state["experiment_cc_view"] = current
    if current not in options:
        current = options[0]
        st.session_state["experiment_cc_view"] = current
    return current


def _status_badge(label: str, value: str) -> str:
    return f"**{label}:** {value}"


def _render_overview(db: PollinationDatabase, snapshot: Mapping[str, Any], field_db=None) -> None:
    trial = snapshot["trial"]
    plots, obs, leaf, harvest, weather = snapshot["plots"], snapshot["obs"], snapshot["leaf"], snapshot["harvest"], snapshot["weather"]
    required = _required_unit_count(trial)
    latest = _observation_latest(snapshot)
    plots_observed = obs.get("Plot ID", pd.Series(dtype=str)).astype(str).nunique() if not obs.empty and "Plot ID" in obs else 0
    completion_pct = 100.0 * plots_observed / len(plots) if len(plots) else 0.0
    metrics, curves = compute_plot_synchrony_metrics(obs, weather)
    median_gap = pd.to_numeric(metrics.get("Absolute synchrony gap (days)"), errors="coerce").median() if not metrics.empty else np.nan

    cards = st.columns(4)
    cards[0].metric("Design status", str(trial.get("status") or "Draft"), help="Experiment lifecycle state; not a scientific evidence grade.")
    cards[1].metric("Experimental units", f"{len(plots):,}" + (f" / {required:,}" if required else ""))
    cards[2].metric("Flowering coverage", f"{completion_pct:.0f}%", help="Share of mapped experimental units with at least one flowering observation.")
    cards[3].metric("Median synchrony gap", f"{median_gap:.2f} d" if pd.notna(median_gap) else "—", help="Absolute male50–female50 gap among units with estimable curves.")

    st.markdown("### Experiment Pulse")
    pulse = st.columns(4)
    pulse[0].markdown(_status_badge("Parents", f"{len(trial.get('female_parent_levels') or [])} female × {len(trial.get('male_parent_levels') or [])} male"))
    pulse[0].caption(f"{len(trial.get('parent_pairings') or [])} configured parent combination(s)")
    pulse[1].markdown(_status_badge("Development evidence", f"{len(obs):,} flowering · {len(leaf):,} tagged-plant records"))
    pulse[1].caption(f"Latest field record: {latest.date().isoformat() if latest is not None else 'none'}")
    pulse[2].markdown(_status_badge("Environment", f"{len(weather):,} approved weather day(s)"))
    pulse[2].caption(f"EO links: {len(snapshot['satellite']):,} · Field link: {'yes' if trial.get('source_field_id') else 'no'}")
    pulse[3].markdown(_status_badge("Outcomes", f"{len(harvest):,} harvest unit(s)"))
    pulse[3].caption(f"Model runs saved: {_model_run_count(db, trial['trial_id'])}")

    actions = _priority_actions(snapshot)
    left, right = st.columns([3, 2])
    with left:
        st.markdown("### Priority actions & evidence gaps")
        if not actions:
            st.success("No obvious structural evidence gap is currently flagged. Review data quality and planned analyses before drawing conclusions.")
        for index, action in enumerate(actions, start=1):
            row = st.columns([5, 2])
            row[0].markdown(f"**{index}. {action['title']}**")
            row[0].caption(action["detail"])
            with row[1]:
                _route_button(f"Open {action['view']}", action["view"], key=f"experiment_cc_action_{index}")
            st.divider()
    with right:
        st.markdown("### Design & data readiness")
        readiness = [
            ("Protocol", bool(snapshot["protocol"]), "Versioned / locked" if snapshot["protocol"] and snapshot["protocol"].get("locked_at") else "Not locked"),
            ("Randomisation", bool(len(plots) and (not required or len(plots)==required)), f"{len(plots)}/{required or '—'} units"),
            ("Weather", not weather.empty, f"{len(weather)} rows"),
            ("Flowering", not obs.empty, f"{plots_observed}/{len(plots) or 0} units"),
            ("Tagged plants", not leaf.empty, f"{len(leaf)} rows"),
            ("Harvest", not harvest.empty, f"{len(harvest)} units"),
        ]
        for name, ready, detail in readiness:
            st.markdown(("✅" if ready else "⚠️") + f" **{name}** — {detail}")
        st.caption("Readiness describes data availability, not validity or causal evidence.")

    st.markdown("### Parent-pair overview")
    if plots.empty:
        st.info("Map and randomise experimental units to populate the parent-pair overview.")
    else:
        cols = [c for c in ["Female parent", "Male parent", "Parent combination", "Male offset (days)", "Sowing density (plants/ha)", "Block"] if c in plots]
        pair_table = plots.groupby([c for c in ["Female parent","Male parent","Parent combination"] if c in plots], dropna=False).agg(
            **{"Experimental units": ("Plot ID", "count"), "Blocks": ("Block", "nunique")}
        ).reset_index()
        st.dataframe(pair_table, hide_index=True, width="stretch")

    if not snapshot["audit"].empty:
        st.markdown("### Recent experiment activity")
        audit = snapshot["audit"].head(8).copy()
        display_cols = [c for c in ["created_at","event_type","entity_type","user_name"] if c in audit]
        st.dataframe(audit[display_cols], hide_index=True, width="stretch")


def _model_run_count(db: PollinationDatabase, trial_id: str) -> int:
    try:
        with db.connect() as con:
            return int(con.execute("SELECT COUNT(*) FROM model_runs WHERE trial_id=?", (trial_id,)).fetchone()[0])
    except Exception:
        return 0


def _safe_reyear(value: Any, year: int) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return date(int(year), 1, 1).isoformat()
    month, day = int(parsed.month), int(parsed.day)
    # Feb 29 cannot be copied into a non-leap year; preserve month and use Feb 28.
    try:
        return date(int(year), month, day).isoformat()
    except ValueError:
        return date(int(year), month, min(day, 28)).isoformat()


def _render_design(db: PollinationDatabase, snapshot: Mapping[str, Any], field_db=None, callbacks: Mapping[str, Callable] | None = None) -> None:
    trial = snapshot["trial"]
    trial_id = str(trial["trial_id"])
    st.markdown("### Experiment lifecycle")
    status_cols = st.columns([3, 1])
    current_status = str(trial.get("status") or "Draft")
    lifecycle_options = LIFECYCLE + [value for value in ["Planned", "Active"] if value not in LIFECYCLE]
    chosen_status = status_cols[0].selectbox("Lifecycle state", lifecycle_options, index=lifecycle_options.index(current_status) if current_status in lifecycle_options else 0, key="experiment_cc_lifecycle")
    if status_cols[1].button("Save state", key="experiment_cc_save_lifecycle", width="stretch"):
        db.update_trial_status(trial_id, chosen_status)
        db.audit_trial(trial_id, "lifecycle_changed", "trial", trial_id, details={"from": current_status, "to": chosen_status})
        st.success("Experiment lifecycle updated.")
        st.rerun()
    st.caption("Once field deployment/data collection begins, change the protocol or randomisation only through explicit versioned amendments rather than silently relabelling existing units.")

    st.markdown("### Design family & replication")
    design_families = ["Completely randomised", "Randomised complete block", "Factorial RCBD", "Split-plot", "Strip-plot", "Incomplete block / lattice", "Custom"]
    current_design = str(trial.get("design_type") or "Randomised complete block")
    if current_design not in design_families:
        design_families = [current_design] + design_families
    dcols = st.columns(3)
    design_family = dcols[0].selectbox("Design family", design_families, index=design_families.index(current_design), key="experiment_cc_design_family")
    design_blocks = int(dcols[1].number_input("Blocks / whole plots", 1, 100, int(trial.get("blocks") or 1), 1, key="experiment_cc_design_blocks"))
    design_reps = int(dcols[2].number_input("Replicates per treatment / block", 1, 50, int(trial.get("replicates_per_treatment") or 1), 1, key="experiment_cc_design_reps"))
    if design_family in {"Split-plot", "Strip-plot", "Incomplete block / lattice", "Custom"}:
        st.warning("This design family can be documented and mapped, but the current automatic factorial allocator is not a general split-plot/strip-plot/incomplete-block design generator. Define whole-plot/subplot or incomplete-block strata explicitly in the protocol and use an allocation compatible with the intended error structure.")
    if st.button("Save declared design settings", key="experiment_cc_save_design_settings", width="stretch"):
        try:
            db.update_trial_design_settings(trial_id, design_type=design_family, blocks=design_blocks, replicates_per_treatment=design_reps)
            st.success("Declared design settings saved and audit-logged.")
            st.rerun()
        except PollinationLabError as error:
            st.error(str(error))

    st.markdown("### Experimental protocol")
    protocol = snapshot["protocol"] or {}
    locked = bool(protocol.get("locked_at"))
    if locked:
        st.info(f"Protocol locked at {protocol.get('locked_at')}. Edits are saved as a new protocol version and retained in the audit trail.")
    with st.form("experiment_cc_protocol_form"):
        objective = st.text_area("Objective", value=str(protocol.get("objective") or ""), height=80)
        hypotheses = st.text_area("Hypotheses", value=str(protocol.get("hypotheses") or ""), height=100)
        primary = st.text_input("Primary outcome", value=str(protocol.get("primary_outcome") or trial.get("primary_outcome") or ""))
        secondary = st.text_input("Secondary outcomes (comma separated)", value=", ".join(protocol.get("secondary_outcomes") or []))
        planned = st.text_area("Planned analysis", value=str(protocol.get("planned_analysis") or ""), height=100, help="Record the intended analysis before examining final outcomes where possible.")
        design_notes = st.text_area("Design / field-protocol notes", value=str(protocol.get("design_notes") or ""), height=80)
        lock_protocol = st.checkbox("Lock protocol for field deployment", value=locked, disabled=locked)
        save_protocol = st.form_submit_button("Save protocol version", type="primary", width="stretch")
    if save_protocol:
        db.upsert_experiment_protocol(trial_id, objective=objective, hypotheses=hypotheses, primary_outcome=primary,
                                      secondary_outcomes=[x.strip() for x in secondary.split(",") if x.strip()],
                                      planned_analysis=planned, design_notes=design_notes, lock=lock_protocol)
        st.success("Experimental protocol version saved.")
        st.rerun()
    versions = snapshot.get("protocol_versions")
    if isinstance(versions, pd.DataFrame) and not versions.empty:
        st.caption(f"{len(versions)} immutable protocol snapshot(s) retained. Current protocol is version {int(versions.iloc[0]['version_number'])}.")
        with st.expander("Protocol version history", expanded=False):
            st.dataframe(versions[[c for c in ["version_number","created_at","locked_at","objective","hypotheses","primary_outcome","planned_analysis","design_notes"] if c in versions]], hide_index=True, width="stretch")

    st.markdown("### Factor structure")
    factors = snapshot["factors"]
    if factors.empty:
        editor = _default_factor_rows(trial)
    else:
        editor = pd.DataFrame({
            "Factor": factors["factor_name"], "Type": factors["factor_type"], "Role": factors["role"],
            "Levels": factors["levels"].map(lambda v: ", ".join(map(str, v or []))), "Unit": factors["unit"], "Notes": factors["notes"],
        })
    edited = st.data_editor(editor, num_rows="dynamic", hide_index=True, width="stretch", key="experiment_cc_factor_editor")
    if st.button("Save factor definitions", key="experiment_cc_save_factors", width="stretch"):
        rows = []
        for _, row in edited.iterrows():
            name = str(row.get("Factor") or "").strip()
            if not name:
                continue
            rows.append({"factor_name": name, "factor_type": str(row.get("Type") or "Categorical"), "role": str(row.get("Role") or "Treatment"),
                         "levels": [v.strip() for v in str(row.get("Levels") or "").split(",") if v.strip()], "unit": str(row.get("Unit") or ""), "notes": str(row.get("Notes") or "")})
        db.save_factor_definitions(trial_id, rows)
        st.success("Factor definitions saved with the experiment.")
        st.rerun()

    st.markdown("### Treatment matrix & design readiness")
    pairings = trial.get("parent_pairings") or []
    densities = trial.get("sowing_density_levels") or [trial.get("planting_density_plants_ha")]
    sow_dates = trial.get("sowing_date_levels") or [trial.get("female_sowing_date")]
    offsets = trial.get("sowing_offset_levels") or [0]
    combinations = max(1, len(pairings)) * max(1, len(densities)) * max(1, len(sow_dates)) * max(1, len(offsets))
    required = _required_unit_count(trial)
    rcols = st.columns(5)
    rcols[0].metric("Treatment combinations", combinations)
    rcols[1].metric("Blocks", int(trial.get("blocks") or 0))
    rcols[2].metric("Replicates / treatment / block", int(trial.get("replicates_per_treatment") or 0))
    rcols[3].metric("Units required", required)
    rcols[4].metric("Units mapped", len(snapshot["plots"]))
    if pairings:
        matrix = []
        for pairing in pairings:
            for density in densities:
                for sow in sow_dates:
                    for offset in offsets:
                        matrix.append({"Female": pairing.get("female_parent"), "Male": pairing.get("male_parent"), "Parent combination": pairing.get("parent_combination"),
                                       "Density (plants/ha)": density, "Female sowing": sow, "Male–female difference (d)": offset})
        st.dataframe(pd.DataFrame(matrix), hide_index=True, width="stretch", height=min(420, 45 + len(matrix)*30))
    if required > 1000:
        st.warning("This factorial design exceeds 1,000 experimental units. Verify feasibility, field capacity and measurement labour before randomisation.")
    if snapshot["plots"].empty:
        st.warning("No randomisation is saved yet.")
    elif len(snapshot["plots"]) != required:
        st.error(f"Stored map has {len(snapshot['plots'])} units but the declared factor structure requires {required}. Do not collect additional data until the design mismatch is resolved.")
    else:
        st.success("Mapped experimental-unit count matches the declared factorial design.")

    st.markdown("### Sample-size / power planning")
    pcols = st.columns(4)
    alpha = float(pcols[0].number_input("Alpha", 0.001, 0.20, 0.05, 0.005, key="experiment_cc_power_alpha"))
    power = float(pcols[1].number_input("Desired power", 0.50, 0.99, 0.80, 0.05, key="experiment_cc_power_power"))
    effect = float(pcols[2].number_input("Standardised effect (Cohen d)", 0.05, 5.0, 0.5, 0.05, key="experiment_cc_power_effect"))
    design_effect = float(pcols[3].number_input("Design-effect multiplier", 1.0, 5.0, 1.0, 0.1, key="experiment_cc_power_deff", help="Use >1 only when justified by clustering/repeated-measure assumptions."))
    z_alpha = stats.norm.ppf(1-alpha/2)
    z_power = stats.norm.ppf(power)
    n_per_group = math.ceil(2 * ((z_alpha + z_power) / effect) ** 2 * design_effect)
    st.info(f"Approximate two-group planning requirement: **{n_per_group} independent experimental units per group** under the stated assumptions. This is a planning approximation, not a substitute for design-specific power simulation.")

    st.markdown("### Randomisation provenance")
    designs = snapshot["designs"]
    if designs.empty:
        st.caption("No explicit design-version record is stored yet. Existing randomisations remain valid, but save future randomisations with seed/algorithm/constraints for full reproducibility.")
    else:
        st.dataframe(designs[[c for c in ["version_number","random_seed","algorithm","status","created_at"] if c in designs]], hide_index=True, width="stretch")

    with st.expander("Clone this experiment skeleton", expanded=False):
        clone_name = st.text_input("New experiment name", value=f"{trial.get('name','Experiment')} · clone")
        clone_year = int(st.number_input("New season year", 1900, 2200, int(trial.get("season_year") or date.today().year)+1, key="experiment_cc_clone_year"))
        field_options = {"Keep current mapped field": trial.get("source_field_id")}
        if field_db is not None:
            fields = _safe_frame(lambda: field_db.fields())
            for _, row in fields.iterrows():
                field_options[f"{row.get('farm_name')} · {row.get('name')}"] = str(row.get("field_id"))
        field_label = st.selectbox("Mapped field", list(field_options), key="experiment_cc_clone_field")
        if st.button("Create clean experiment clone", key="experiment_cc_clone_button", width="stretch"):
            source_field_id = field_options[field_label]
            field = field_db.field(str(source_field_id)) if field_db is not None and source_field_id else None
            payload = {
                "name": clone_name, "project_id": trial.get("project_id"), "site_name": (field or {}).get("farm_name") or trial.get("site_name"), "season_year": clone_year,
                "female_parent_levels": trial.get("female_parent_levels"), "male_parent_levels": trial.get("male_parent_levels"), "parent_pairings": trial.get("parent_pairings"), "parent_pairing_mode": trial.get("parent_pairing_mode"),
                "sowing_density_levels": trial.get("sowing_density_levels"), "sowing_date_levels": trial.get("sowing_date_levels"), "sowing_offset_levels": trial.get("sowing_offset_levels"),
                "female_sowing_date": _safe_reyear(trial.get("female_sowing_date"), clone_year),
                "design_type": trial.get("design_type"), "blocks": trial.get("blocks"), "replicates_per_treatment": trial.get("replicates_per_treatment"), "row_ratio": trial.get("row_ratio"),
                "planting_density_plants_ha": trial.get("planting_density_plants_ha"), "primary_outcome": trial.get("primary_outcome"), "base_temperature_c": trial.get("base_temperature_c"), "upper_temperature_c": trial.get("upper_temperature_c"),
                "field_geometry": (field or {}).get("geometry") or trial.get("field_geometry"), "source_field_id": source_field_id, "source_field_snapshot": (field or {}).get("geometry") or trial.get("source_field_snapshot"), "boundary_mode": "Cloned design skeleton", "status": "Draft",
                "notes": f"Cloned from {trial.get('name')} ({trial_id}); observations/outcomes were not copied.",
            }
            new_id = db.create_trial(payload)
            if snapshot["protocol"]:
                pr = snapshot["protocol"]
                db.upsert_experiment_protocol(new_id, objective=pr.get("objective") or "", hypotheses=pr.get("hypotheses") or "", primary_outcome=pr.get("primary_outcome") or "", secondary_outcomes=pr.get("secondary_outcomes") or [], planned_analysis=pr.get("planned_analysis") or "", design_notes=f"Cloned protocol from {trial_id}; review before locking.")
            if not snapshot["factors"].empty:
                db.save_factor_definitions(new_id, [{"factor_name": r["factor_name"], "factor_type": r["factor_type"], "role": r["role"], "levels": r["levels"], "unit": r["unit"], "notes": r["notes"]} for _,r in snapshot["factors"].iterrows()])
            st.session_state.pollination_active_trial_id = new_id
            st.success("Experiment skeleton cloned without copying observations, outcomes or randomisation.")
            st.rerun()

    if callbacks and callbacks.get("trial_workbench"):
        st.markdown("### Advanced design workbench")
        st.caption("The full geometry/randomisation workbench is intentionally lazy because it contains large maps and legacy multi-section tools.")
        if st.toggle("Load advanced mapped trial design workbench", value=False, key="experiment_cc_load_trial_workbench_design"):
            callbacks["trial_workbench"]()


def _spatial_diagnostics(trial: Mapping[str, Any], plots: pd.DataFrame) -> pd.DataFrame:
    if plots.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    block_counts = plots.groupby("Block").size() if "Block" in plots else pd.Series(dtype=int)
    treatment_counts = plots.groupby("Treatment").size() if "Treatment" in plots else pd.Series(dtype=int)
    area = pd.to_numeric(plots.get("Area (ha)"), errors="coerce") if "Area (ha)" in plots else pd.Series(dtype=float)
    field_area = pd.to_numeric(pd.Series([trial.get("field_area_ha")]), errors="coerce").iloc[0]
    rows.append({"Diagnostic": "Block size balance", "Value": f"{block_counts.min()}–{block_counts.max()} units" if not block_counts.empty else "—", "Interpretation": "Equal counts are expected for a balanced complete-block design."})
    rows.append({"Diagnostic": "Treatment replication balance", "Value": f"{treatment_counts.min()}–{treatment_counts.max()} units" if not treatment_counts.empty else "—", "Interpretation": "Large differences require explanation or design correction."})
    if not area.empty and area.notna().any():
        cv = 100*float(area.std(ddof=1)/area.mean()) if area.mean() else np.nan
        rows.append({"Diagnostic": "Experimental-unit area CV", "Value": f"{cv:.1f}%" if pd.notna(cv) else "—", "Interpretation": "Unequal unit area can affect exposure and harvest scaling."})
        if pd.notna(field_area) and field_area > 0:
            rows.append({"Diagnostic": "Mapped unit area / field area", "Value": f"{100*area.sum()/field_area:.1f}%", "Interpretation": "Excludes alleys, borders and unused field area."})
    if shape is not None and "Geometry" in plots and "Treatment" in plots:
        adjacency_same = 0; adjacency_total = 0
        geoms = [(shape(g), str(t)) for g,t in zip(plots["Geometry"], plots["Treatment"]) if isinstance(g, Mapping)]
        for i in range(len(geoms)):
            for j in range(i+1, len(geoms)):
                try:
                    if geoms[i][0].touches(geoms[j][0]):
                        adjacency_total += 1
                        adjacency_same += int(geoms[i][1] == geoms[j][1])
                except Exception:
                    pass
        if adjacency_total:
            rows.append({"Diagnostic": "Same-treatment shared borders", "Value": f"{adjacency_same}/{adjacency_total}", "Interpretation": "A diagnostic of spatial clustering; not by itself a validity test."})
    return pd.DataFrame(rows)


def _render_spatial(snapshot: Mapping[str, Any], callbacks: Mapping[str, Callable] | None = None) -> None:
    trial, plots = snapshot["trial"], snapshot["plots"]
    if plots.empty:
        st.warning("No experimental-unit geometry is saved yet.")
        if callbacks and callbacks.get("trial_workbench"):
            if st.button("Open advanced trial creation workbench", key="experiment_cc_open_first_trial"):
                st.session_state["experiment_cc_create_first_trial"] = True
                st.rerun()
            if st.session_state.get("experiment_cc_create_first_trial"):
                callbacks["trial_workbench"]()
        return
    st.markdown("### Spatial experiment layout")
    options = [c for c in ["Parent combination","Female parent","Male parent","Sowing density (plants/ha)","Sowing date","Male–female sowing difference (days)","Treatment","Block"] if c in plots]
    colour_by = st.selectbox("Colour experimental units by", options or ["Treatment"], key="experiment_cc_colour_by")
    _plots_map(trial, plots, draw=False, key="experiment_cc_spatial_map", colour_by=colour_by)
    st.caption("Field geometry is authoritative. Experimental-unit polygons are independently treated spatial supports; touching borders are permitted but positive-area overlap is not.")
    diagnostics = _spatial_diagnostics(trial, plots)
    if not diagnostics.empty:
        st.markdown("### Spatial design diagnostics")
        st.dataframe(diagnostics, hide_index=True, width="stretch")
    st.markdown("### Experimental-unit register")
    show = [c for c in ["Treatment unit","Experiment plot","Block","Replicate","Female parent","Male parent","Parent combination","Sowing density (plants/ha)","Sowing date","Male–female sowing difference (days)","Area (ha)"] if c in plots]
    st.dataframe(plots[show], hide_index=True, width="stretch")
    st.download_button("Download field-label register", plots[show].to_csv(index=False).encode("utf-8"), file_name="experimental_unit_label_register.csv", mime="text/csv", width="stretch")

    st.markdown("### Experimental-unit data card")
    labels = {str(row.get("Treatment unit") or row.get("Plot")): str(row.get("Plot ID")) for _, row in plots.iterrows()}
    selected_label = st.selectbox("Inspect experimental unit", list(labels), key="experiment_cc_unit_card")
    selected_id = labels[selected_label]
    unit_row = plots.loc[plots["Plot ID"].astype(str).eq(selected_id)].iloc[0]
    cols = st.columns(4)
    cols[0].metric("Block / replicate", f"{unit_row.get('Block','—')} / {unit_row.get('Replicate','—')}")
    cols[1].metric("Female parent", str(unit_row.get("Female parent") or "—"))
    cols[2].metric("Male parent", str(unit_row.get("Male parent") or "—"))
    cols[3].metric("Sowing offset", f"{unit_row.get('Male–female sowing difference (days)')} d" if pd.notna(unit_row.get('Male–female sowing difference (days)')) else "—")
    st.caption(f"Treatment: {unit_row.get('Treatment') or '—'} · Density: {unit_row.get('Sowing density (plants/ha)') or '—'} plants/ha · Female sowing: {unit_row.get('Female sowing') or '—'}")
    related = []
    for key, label, id_col in (("obs", "Flowering", "Plot ID"), ("leaf", "Tagged plant", "Plot ID"), ("phenology", "Phenology", "Plot ID"), ("harvest", "Harvest", "Plot ID")):
        frame = snapshot.get(key)
        if isinstance(frame, pd.DataFrame) and not frame.empty and id_col in frame:
            part = frame.loc[frame[id_col].astype(str).eq(selected_id)].copy()
            if not part.empty:
                part.insert(0, "Evidence type", label)
                related.append(part)
    if related:
        st.dataframe(pd.concat(related, ignore_index=True, sort=False), hide_index=True, width="stretch", height=300)
    else:
        st.info("No measured observations or outcomes are linked to this experimental unit yet.")


def _qc_flags(snapshot: Mapping[str, Any]) -> pd.DataFrame:
    flags: list[dict[str, Any]] = []
    obs, leaf, harvest, trial = snapshot["obs"], snapshot["leaf"], snapshot["harvest"], snapshot["trial"]
    sow = pd.to_datetime(trial.get("female_sowing_date"), errors="coerce")
    if not obs.empty:
        if "Date" in obs and pd.notna(sow):
            bad = pd.to_datetime(obs["Date"], errors="coerce") < sow
            for _, row in obs.loc[bad].head(50).iterrows(): flags.append({"Severity":"Error","Record":"Flowering","Unit":row.get("Plot"),"Issue":"Observation predates female sowing","Value":row.get("Date")})
        for col in ["Male shedding (%)","Female silking (%)","Female receptive silks (%)"]:
            if col in obs:
                vals = pd.to_numeric(obs[col], errors="coerce"); bad=(vals<0)|(vals>100)
                for _,row in obs.loc[bad].head(50).iterrows(): flags.append({"Severity":"Error","Record":"Flowering","Unit":row.get("Plot"),"Issue":f"{col} outside 0–100%","Value":row.get(col)})
        if "Crop stress score (0-5)" in obs:
            vals=pd.to_numeric(obs["Crop stress score (0-5)"],errors="coerce"); bad=(vals<0)|(vals>5)
            for _,row in obs.loc[bad].head(50).iterrows(): flags.append({"Severity":"Warning","Record":"Flowering","Unit":row.get("Plot"),"Issue":"Stress score outside 0–5","Value":row.get("Crop stress score (0-5)")})
    if not leaf.empty:
        if "Collared leaf number" in leaf:
            vals=pd.to_numeric(leaf["Collared leaf number"],errors="coerce"); bad=(vals<0)|(vals>40)
            for _,row in leaf.loc[bad].head(50).iterrows(): flags.append({"Severity":"Warning","Record":"Tagged plant","Unit":row.get("Plot"),"Issue":"Collared leaf number outside broad maize QA range","Value":row.get("Collared leaf number")})
    if not harvest.empty:
        for col in ["Seed set (%)","Germination (%)","Genetic purity (%)","Pure seed (%)"]:
            if col in harvest:
                vals=pd.to_numeric(harvest[col],errors="coerce"); bad=(vals<0)|(vals>100)
                for _,row in harvest.loc[bad].head(50).iterrows(): flags.append({"Severity":"Error","Record":"Harvest","Unit":row.get("Plot"),"Issue":f"{col} outside 0–100%","Value":row.get(col)})
    return pd.DataFrame(flags)


def _render_collection(db: PollinationDatabase, snapshot: Mapping[str, Any], field_db=None, callbacks: Mapping[str, Callable] | None = None) -> None:
    trial, plots = snapshot["trial"], snapshot["plots"]
    st.markdown("### Data completeness")
    completeness = snapshot["completeness"]
    if completeness.empty:
        st.info("No experimental units are available yet.")
    else:
        st.dataframe(completeness, hide_index=True, width="stretch")
        st.download_button("Download completeness matrix", completeness.to_csv(index=False).encode("utf-8"), file_name="experiment_data_completeness.csv", mime="text/csv", width="stretch")

    st.markdown("### Field-data quality checks")
    flags = _qc_flags(snapshot)
    if flags.empty:
        st.success("No broad structural/range QA flags were detected. This does not establish measurement validity.")
    else:
        st.dataframe(flags, hide_index=True, width="stretch")

    st.markdown("### Measurement plan")
    requirements = snapshot["requirements"]
    if not requirements.empty:
        st.dataframe(requirements[[c for c in ["measurement_name","timing_label","due_date","scope","required","notes"] if c in requirements]], hide_index=True, width="stretch")
    protocol_options = {"None": None}
    if field_db is not None:
        try:
            protocols = field_db.observation_protocols()
            for _, row in protocols.iterrows(): protocol_options[str(row.get("name"))] = str(row.get("protocol_id"))
        except Exception:
            protocols = pd.DataFrame()
    with st.form("experiment_cc_requirement_form"):
        name = st.text_input("Expected measurement", placeholder="e.g. Female silking %, male pollen shed, tagged-plant leaf number")
        cols=st.columns(4)
        timing=cols[0].text_input("Timing / stage", placeholder="Daily around flowering")
        has_due=cols[1].checkbox("Set due date", value=False)
        due=cols[1].date_input("Due date", value=date.today(), disabled=not has_due)
        scope=cols[2].selectbox("Scope", ["Experimental unit","Tagged plant","Block","Field"])
        protocol_name=cols[3].selectbox("Observation protocol", list(protocol_options))
        notes=st.text_input("Notes")
        save=st.form_submit_button("Add measurement requirement", width="stretch")
    if save and name.strip():
        db.save_measurement_requirement(str(trial["trial_id"]), name.strip(), protocol_id=protocol_options[protocol_name], timing_label=timing, due_date=str(due) if has_due else None, scope=scope, notes=notes)
        st.success("Measurement requirement saved.")
        st.rerun()

    if field_db is not None and trial.get("source_field_id"):
        st.markdown("### Create field-work task")
        field_id=str(trial.get("source_field_id"))
        protocol_options2 = protocol_options
        c=st.columns(3)
        task_title=c[0].text_input("Task", value=f"Collect observations · {trial.get('name')}")
        task_due=c[1].date_input("Task due", value=date.today(), key="experiment_cc_task_due")
        task_protocol=c[2].selectbox("Protocol", list(protocol_options2), key="experiment_cc_task_protocol")
        unit_options={"Whole trial":None}
        if not plots.empty:
            for _,row in plots.iterrows(): unit_options[str(row.get("Treatment unit") or row.get("Plot"))]=str(row.get("Plot ID"))
        unit_label=st.selectbox("Experimental unit", list(unit_options), key="experiment_cc_task_unit")
        if st.button("Create linked Field Operations task", key="experiment_cc_create_task", width="stretch"):
            task_id=field_db.create_task(field_id, task_title, category="Experiment observation", due_date=str(task_due), priority="High", source="Experiment Command Centre", description="Collect protocol-driven research observations; do not infer missing measurements.")
            field_db.save_task_details(task_id, trial_id=str(trial["trial_id"]), experimental_unit_id=unit_options[unit_label], protocol_id=protocol_options2[task_protocol])
            db.audit_trial(str(trial["trial_id"]), "field_task_created", "field_task", task_id, details={"experimental_unit_id":unit_options[unit_label],"protocol_id":protocol_options2[task_protocol]})
            st.success("Field task created and linked to this experiment.")

    if callbacks and callbacks.get("trial_workbench"):
        if st.toggle("Load advanced observation-entry workbench", value=False, key="experiment_cc_load_trial_workbench_collection"):
            callbacks["trial_workbench"]()


def _render_development(db: PollinationDatabase, snapshot: Mapping[str, Any], callbacks: Mapping[str, Callable] | None = None) -> None:
    trial, obs, weather, harvest = snapshot["trial"], snapshot["obs"], snapshot["weather"], snapshot["harvest"]
    metrics, curves = compute_plot_synchrony_metrics(obs, weather)
    if weather.empty:
        st.warning("No approved daily weather is stored with this experiment. Use field-linked Climate & Earth Observation data where available rather than re-uploading the same weather as a detached CSV.")
        if callbacks and callbacks.get("climate") and st.button("Open Climate & Earth Observation to retrieve / review field weather", key="experiment_cc_open_climate_weather", width="stretch"):
            callbacks["climate"]()
    else:
        source_text = ""
        if "Source" in weather:
            source_text = ", ".join(sorted(set(weather["Source"].dropna().astype(str))))
        st.caption(f"Using {len(weather):,} persisted experiment-weather day(s){' · '+source_text if source_text else ''}. Reuse approved field evidence; update only when coverage is stale or incomplete.")
    st.markdown("### Flowering & synchrony state")
    if metrics.empty:
        st.info("Daily flowering observations are insufficient to estimate plot-level synchrony curves.")
    else:
        c=st.columns(4)
        c[0].metric("Units with synchrony estimates", metrics["Plot ID"].nunique() if "Plot ID" in metrics else len(metrics))
        c[1].metric("Median absolute gap", f"{pd.to_numeric(metrics['Absolute synchrony gap (days)'],errors='coerce').median():.2f} d" if "Absolute synchrony gap (days)" in metrics else "—")
        c[2].metric("Median receptivity covered", f"{pd.to_numeric(metrics['Female receptivity covered by pollen (%)'],errors='coerce').median():.1f}%" if "Female receptivity covered by pollen (%)" in metrics else "—")
        c[3].metric("Weather coverage", f"{len(weather):,} d")
        if not curves.empty:
            treatment_values=sorted(curves["Treatment"].dropna().astype(str).unique())
            selected=st.multiselect("Treatments shown", treatment_values, default=treatment_values[:min(8,len(treatment_values))], key="experiment_cc_curve_treatments")
            curve=curves.loc[curves["Treatment"].astype(str).isin(selected)].groupby(["Treatment","Date"],as_index=False)[[c for c in ["Male activity (%)","Female silking (%)","Female receptive (%)","Daily overlap (%)"] if c in curves]].mean()
            long=curve.melt(id_vars=["Treatment","Date"],var_name="Measure",value_name="Percent")
            fig=px.line(long,x="Date",y="Percent",color="Measure",facet_row="Treatment",markers=True,title="Observed male/female flowering trajectories")
            fig.update_yaxes(range=[0,105]); st.plotly_chart(fig,width="stretch")
        st.dataframe(metrics, hide_index=True, width="stretch")
        summary=treatment_summary(metrics,harvest)
        if not summary.empty:
            st.markdown("### Treatment / parent-pair summary")
            st.dataframe(summary,hide_index=True,width="stretch")

    st.markdown("### Parent physiology provenance")
    parents=list(dict.fromkeys(list(trial.get("female_parent_levels") or [])+list(trial.get("male_parent_levels") or [])))
    phys=db.parent_physiology(parents) if parents else pd.DataFrame()
    if phys.empty:
        st.warning("No local parent physiology records are stored. Mechanistic calculations therefore use publication-informed priors until local calibration is approved.")
    else:
        st.dataframe(phys,hide_index=True,width="stretch")
    st.caption("Flowering timing overlap does not guarantee pollen quantity, fertilisation, seed purity or yield.")
    if callbacks and callbacks.get("synchrony_workbench"):
        if st.toggle("Load advanced mechanistic synchrony, calibration & strategy workbench", value=False, key="experiment_cc_load_sync_development"):
            callbacks["synchrony_workbench"]()


def _render_outcomes(snapshot: Mapping[str, Any]) -> None:
    harvest=snapshot["harvest"]
    plots=snapshot["plots"]
    st.markdown("### Harvest & reproductive outcomes")
    if harvest.empty:
        st.info("No plot-level harvest outcome has been recorded yet.")
        return
    merged=harvest.copy()
    outcome_cols=[c for c in ["Seed set (%)","Seed yield (t/ha)","Pure seed (%)","Genetic purity (%)","Germination (%)","Kernel rows per ear","Thousand kernel weight (g)"] if c in merged]
    cards=st.columns(min(4,max(1,len(outcome_cols))))
    for idx,col in enumerate(outcome_cols[:4]):
        vals=pd.to_numeric(merged[col],errors="coerce")
        cards[idx].metric(col, f"{vals.mean():.2f}" if vals.notna().any() else "—")
    st.dataframe(merged,hide_index=True,width="stretch")
    if "Treatment" in merged and outcome_cols:
        target=st.selectbox("Outcome to compare", outcome_cols, key="experiment_cc_outcome_target")
        vals=pd.to_numeric(merged[target],errors="coerce")
        plot=merged.assign(_y=vals).dropna(subset=["_y"])
        if not plot.empty:
            fig=px.box(plot,x="Treatment",y="_y",points="all",title=f"{target} by treatment")
            fig.update_yaxes(title=target); st.plotly_chart(fig,width="stretch")
    coverage=100*len(harvest)/len(plots) if len(plots) else 0
    st.caption(f"Harvest outcomes are stored for {len(harvest)} of {len(plots)} mapped experimental units ({coverage:.0f}%).")


def _analysis_table(snapshot: Mapping[str, Any]) -> pd.DataFrame:
    trial=snapshot["trial"]
    return build_model_table(trial=trial, plots=snapshot["plots"], plot_metrics=compute_plot_synchrony_metrics(snapshot["obs"],snapshot["weather"])[0],
                             phenology_events=snapshot["phenology"], harvest=snapshot["harvest"], weather=snapshot["weather"],
                             satellite_links_frame=snapshot["satellite"], root_zone=None)


def _render_analysis(db: PollinationDatabase, snapshot: Mapping[str, Any], callbacks: Mapping[str, Callable] | None = None) -> None:
    st.markdown("### Analysis-ready G×E×M table")
    table=_analysis_table(snapshot)
    if table.empty:
        st.info("More mapped units and/or observations are required before an analysis-ready table can be assembled.")
    else:
        st.dataframe(table,hide_index=True,width="stretch",height=420)
        st.download_button("Download analysis-ready table",table.to_csv(index=False).encode("utf-8"),file_name="experiment_gxem_analysis_table.csv",mime="text/csv",width="stretch")
        st.caption("Trial, block, replicate, parent and spatial identifiers are retained. Validation should respect these grouped structures rather than use leakage-prone random row splits.")
        if any(str(c).startswith("Retrospective flowering") or str(c).startswith("Through observed female50") for c in table.columns):
            st.warning("Some environment columns are explicitly retrospective (for example weather through/around observed female 50% silking). Use them to explain later outcomes such as harvest, not as predictors of an event that had not yet occurred at decision time.")

        targets=[c for c in ["Absolute synchrony gap (days)","Synchrony gap (days; male50 - female50)","Female receptivity covered by pollen (%)","Seed set (%)","Seed yield (t/ha)","Pure seed (%)","Germination (%)","Genetic purity (%)"] if c in table and pd.to_numeric(table[c],errors="coerce").notna().sum()>=4]
        if targets:
            st.markdown("### Designed-experiment summary")
            target=st.selectbox("Outcome",targets,key="experiment_cc_analysis_target")
            group_col="Treatment" if "Treatment" in table else ("Parent combination" if "Parent combination" in table else None)
            if group_col:
                data=table[[group_col,target]+(["Block"] if "Block" in table else [])].copy()
                data[target]=pd.to_numeric(data[target],errors="coerce"); data=data.dropna(subset=[target])
                summary=data.groupby(group_col)[target].agg(["count","mean","std"]).reset_index()
                summary["se"]=summary["std"]/np.sqrt(summary["count"].clip(lower=1))
                summary["95% CI low"]=summary["mean"]-1.96*summary["se"]; summary["95% CI high"]=summary["mean"]+1.96*summary["se"]
                st.dataframe(summary,hide_index=True,width="stretch")
                fig=px.scatter(summary,x=group_col,y="mean",error_y=1.96*summary["se"],title=f"{target}: treatment means ± approximate 95% CI")
                st.plotly_chart(fig,width="stretch")
                if smf is not None and "Block" in data and data["Block"].nunique()>=2 and data[group_col].nunique()>=2 and len(data)>=8:
                    if st.button("Fit block-aware mixed model",key="experiment_cc_mixed_model",width="stretch"):
                        safe=data.rename(columns={target:"outcome",group_col:"treatment", "Block":"block"})
                        try:
                            fit=smf.mixedlm("outcome ~ C(treatment)",safe,groups=safe["block"]).fit(reml=True,method="lbfgs")
                            st.text(fit.summary().as_text())
                            st.caption("Random-intercept block model. Confirm that this model matches the actual randomisation/error strata before using it for inference.")
                        except Exception as error:
                            st.warning(f"Mixed model could not be fitted reliably: {error}")
            st.warning("Treatment summaries and mixed models support designed-experiment analysis, but they do not turn observational covariates into causal treatment effects automatically.")

    if callbacks and callbacks.get("gxem"):
        if st.toggle("Load cross-trial G×E×M builder", value=False, key="experiment_cc_load_gxem"):
            callbacks["gxem"]()
    if callbacks and callbacks.get("synchrony_workbench"):
        if st.toggle("Load advanced prediction & optimisation workbench", value=False, key="experiment_cc_load_sync_analysis"):
            callbacks["synchrony_workbench"]()


def _render_evidence(db: PollinationDatabase, snapshot: Mapping[str, Any], callbacks: Mapping[str, Callable] | None = None) -> None:
    trial=snapshot["trial"]; trial_id=str(trial["trial_id"])
    st.markdown("### Evidence status")
    rows=[
        {"Evidence component":"Experimental protocol","Status":"Locked" if snapshot["protocol"] and snapshot["protocol"].get("locked_at") else ("Versioned" if snapshot["protocol"] else "Missing"),"Rows / versions":snapshot["protocol"].get("protocol_version") if snapshot["protocol"] else 0},
        {"Evidence component":"Mapped experimental units","Status":"Available" if not snapshot["plots"].empty else "Missing","Rows / versions":len(snapshot["plots"])},
        {"Evidence component":"Flowering observations","Status":"Measured" if not snapshot["obs"].empty else "Missing","Rows / versions":len(snapshot["obs"])},
        {"Evidence component":"Tagged-plant observations","Status":"Measured" if not snapshot["leaf"].empty else "Missing","Rows / versions":len(snapshot["leaf"])},
        {"Evidence component":"Daily weather","Status":"Retrieved / approved" if not snapshot["weather"].empty else "Missing","Rows / versions":len(snapshot["weather"])},
        {"Evidence component":"EO links","Status":"EO-derived" if not snapshot["satellite"].empty else "Missing","Rows / versions":len(snapshot["satellite"])},
        {"Evidence component":"Harvest outcomes","Status":"Measured" if not snapshot["harvest"].empty else "Missing","Rows / versions":len(snapshot["harvest"])},
        {"Evidence component":"Model runs","Status":"Research estimates" if _model_run_count(db,trial_id) else "None","Rows / versions":_model_run_count(db,trial_id)},
    ]
    st.dataframe(pd.DataFrame(rows),hide_index=True,width="stretch")

    st.markdown("### Experiment audit trail")
    audit=snapshot["audit"]
    if audit.empty: st.caption("No experiment audit events have been recorded yet.")
    else: st.dataframe(audit[[c for c in ["created_at","event_type","entity_type","entity_id","user_name","details"] if c in audit]],hide_index=True,width="stretch")

    st.markdown("### Reproducible export")
    package=db.export_trial_package(trial_id)
    st.download_button("Download complete experiment package",package,file_name=f"experiment_{trial_id[:8]}.zip",mime="application/zip",width="stretch")
    analysis=_analysis_table(snapshot)
    if not analysis.empty:
        completeness=snapshot["completeness"]
        protocol=snapshot["protocol"] or {}
        buffer=io.BytesIO()
        with zipfile.ZipFile(buffer,"w",zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("analysis_ready.csv",analysis.to_csv(index=False))
            archive.writestr("data_completeness.csv",completeness.to_csv(index=False) if not completeness.empty else "")
            archive.writestr("experiment_protocol.json",json.dumps(protocol,indent=2,default=str))
            protocol_versions = snapshot.get("protocol_versions")
            archive.writestr("experiment_protocol_versions.csv", protocol_versions.to_csv(index=False) if isinstance(protocol_versions, pd.DataFrame) and not protocol_versions.empty else "")
            archive.writestr("factor_definitions.csv",snapshot["factors"].to_csv(index=False) if not snapshot["factors"].empty else "")
            archive.writestr("audit_log.csv",audit.to_csv(index=False) if not audit.empty else "")
            archive.writestr("METHODS_NOTE.txt","AGROLATTICE 11.15 export. Preserve trial/block/replicate structure in validation. Mechanistic maize timing does not guarantee pollen quantity, genetic purity or yield. Any causal interpretation requires the randomisation/error structure and planned contrasts to be respected.\n")
        st.download_button("Download publication/evidence bundle",buffer.getvalue(),file_name=f"experiment_evidence_{trial_id[:8]}.zip",mime="application/zip",width="stretch")
    if callbacks and callbacks.get("projects"):
        if st.toggle("Load legacy research project library", value=False, key="experiment_cc_load_projects"):
            callbacks["projects"]()


def render_experiment_command_centre(*, db: PollinationDatabase, field_db=None, callbacks: Mapping[str, Callable] | None = None, app_version: str = "11.15") -> None:
    st.markdown(f"## 🧪 Experiments")
    st.caption("Design spatial experiments, collect protocol-driven field data, analyse genotype × environment × management responses, and preserve the randomisation/evidence chain from treatment assignment to outcome.")
    selected=_trial_selector(db)
    if selected is None:
        if callbacks and callbacks.get("trial_workbench"):
            callbacks["trial_workbench"]()
        return
    snapshot=_snapshot(db,selected)
    trial=snapshot["trial"]
    st.markdown(f"**{_context_line(trial,field_db)}**")
    st.caption(f"Experiment ID {selected[:8]} · Pollination DB schema 3.0 · AGROLATTICE {app_version}")

    options=["Overview","Design","Spatial layout","Data collection","Development & synchrony","Outcomes","Analysis","Evidence & export"]
    default=_consume_requested_view(options)
    # True lazy navigation: only the selected branch below is executed.
    view=st.radio("Experiment workspace",options,index=options.index(default),horizontal=True,key="experiment_cc_view")
    st.divider()
    # Refresh after selector/status writes only; not on every widget interaction.
    snapshot=_snapshot(db,selected)
    if view=="Overview": _render_overview(db,snapshot,field_db)
    elif view=="Design": _render_design(db,snapshot,field_db,callbacks)
    elif view=="Spatial layout": _render_spatial(snapshot,callbacks)
    elif view=="Data collection": _render_collection(db,snapshot,field_db,callbacks)
    elif view=="Development & synchrony": _render_development(db,snapshot,callbacks)
    elif view=="Outcomes": _render_outcomes(snapshot)
    elif view=="Analysis": _render_analysis(db,snapshot,callbacks)
    elif view=="Evidence & export": _render_evidence(db,snapshot,callbacks)
