"""Searchable AGROLATTICE tool catalogue for Release 11.19."""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Mapping

import streamlit as st

MODULE_VERSION = "1.0.0"

PRIMARY_WORKSPACES = {
    "Home", "Fields & Operations", "AgroLattice Twin", "Climate & Earth Observation",
    "Crop Decisions", "Experiments", "Models & Evidence", "Reports", "Data & Settings", "Help",
}


def _maturity(name: str, category: str) -> str:
    text = f"{name} {category}".casefold()
    if "legacy" in text or name in {"Study & publication builder", "Workflow & reporting"}:
        return "Legacy"
    if any(token in text for token in ("toolbox", "laboratory", "ensemble", "robustness", "interoperability", "advanced")):
        return "Advanced"
    return "Primary"


def _requirements(name: str) -> str:
    n = name.casefold()
    if "satellite" in n or "earth" in n:
        return "Mapped AOI/field; internet for new Sentinel retrieval"
    if "weather" in n or "climate" in n or "drought" in n or "risk" in n or "similarity" in n:
        return "Installed climate data or field coordinates for NASA retrieval"
    if "maize" in n or "gx" in n or "experiment" in n:
        return "Mapped trial/experimental units and experiment records"
    if "model" in n or "validation" in n or "evidence" in n:
        return "Registered dataset/model or analysis-ready table"
    if "field" in n or "scouting" in n or "sensor" in n:
        return "Mapped field and relevant field records"
    if "report" in n or "publication" in n:
        return "Persistent AGROLATTICE evidence or a legacy saved study"
    return "Depends on the selected workflow"


def render_tool_catalogue(
    *,
    tools: Mapping[str, Callable[[], None]],
    categories: Mapping[str, str],
    descriptions: Mapping[str, str],
    settings_store: Any,
    safe_key: Callable[[str], str],
    render_embedded: Callable[[Callable[[], None]], None],
    active_context: Mapping[str, str] | None = None,
) -> None:
    settings = settings_store.load()
    favourites = set(str(x) for x in settings.get("tool_catalogue", {}).get("favourites", []))
    recent = [str(x) for x in settings.get("tool_catalogue", {}).get("recent", [])]

    selected = st.session_state.get("release11_16_selected_tool") or st.session_state.get("release10_selected_tool")
    if selected in tools:
        cols = st.columns([1.1, 4.7, 1.2])
        if cols[0].button("← Catalogue", width="stretch", key="r1116_tool_back"):
            st.session_state.release11_16_selected_tool = None
            st.session_state.release10_selected_tool = None
            st.rerun()
        cols[1].markdown(f"### {selected}")
        category = categories.get(selected, "Other")
        maturity = _maturity(selected, category)
        cols[1].caption(f"{category} · {maturity} · {_requirements(selected)}")
        fav_label = "★ Favourite" if selected in favourites else "☆ Favourite"
        if cols[2].button(fav_label, width="stretch", key=f"r1116_fav_open_{safe_key(selected)}"):
            settings_store.toggle_favourite(selected)
            st.rerun()
        st.info(descriptions.get(selected, "Open the complete AGROLATTICE analytical workflow."))
        settings_store.record_recent_tool(selected)
        st.divider()
        render_embedded(tools[selected])
        return

    st.markdown("### Tool catalogue")
    st.caption("Find an AGROLATTICE capability by scientific task, workspace, maturity or data requirement. Legacy tools remain available but are clearly identified.")

    quick = st.columns(3)
    quick[0].metric("Tools", len(tools))
    quick[1].metric("Favourites", len([x for x in favourites if x in tools]))
    quick[2].metric("Legacy", sum(_maturity(n, categories.get(n, "Other")) == "Legacy" for n in tools))

    controls = st.columns([3.2, 1.8, 1.8, 1.2])
    query = controls[0].text_input("Search", placeholder="e.g. silking, PCA, SHAP, irrigation, Sentinel", key="r1116_tool_search")
    workspace_options = ["All"] + sorted(set(categories.get(n, "Other") for n in tools))
    workspace = controls[1].selectbox("Workspace", workspace_options, key="r1116_tool_workspace")
    visibility_options = ["Primary only", "Primary + Advanced", "All including Legacy"]
    default_visibility = "Primary + Advanced" if bool(settings.get("workspace", {}).get("show_advanced_tools", False)) else "Primary only"
    visibility = controls[2].selectbox("Visibility", visibility_options, index=visibility_options.index(default_visibility), key="r1116_tool_visibility")
    only_fav = controls[3].checkbox("Favourites", value=False, key="r1116_tool_only_fav")

    q = query.strip().casefold()
    matches: list[str] = []
    for name in tools:
        category = categories.get(name, "Other")
        mat = _maturity(name, category)
        if workspace != "All" and category != workspace:
            continue
        # Explicit search spans the entire catalogue so an advanced/legacy tool is never
        # made undiscoverable by the default visibility preference.
        if not q:
            if visibility == "Primary only" and mat != "Primary":
                continue
            if visibility == "Primary + Advanced" and mat == "Legacy":
                continue
        if only_fav and name not in favourites:
            continue
        hay = " ".join([name, category, descriptions.get(name, ""), _requirements(name), mat]).casefold()
        if q and not all(token in hay for token in q.split()):
            continue
        matches.append(name)

    context = dict(active_context or {})
    if not query and not only_fav:
        st.markdown("#### Suggested for current context")
        suggestions: list[str] = []
        if context.get("Trial") and context.get("Trial") != "Not selected":
            suggestions += ["Maize flowering trials & field data", "Maize synchrony analysis & prediction", "G×E×M research dataset builder"]
        if context.get("Field") and context.get("Field") != "Not selected":
            suggestions += ["AgroLattice live twin", "Satellite crop monitoring", "Tasks, scouting & operations"]
        if context.get("Crop") and context.get("Crop") != "Not selected":
            suggestions += ["Daily weather & phenology", "Soil-water balance", "Decision Intelligence & Research Optimisation"]
        seen = set()
        suggestions = [s for s in suggestions if s in tools and not (s in seen or seen.add(s))][:6]
        if suggestions:
            scols = st.columns(min(3, len(suggestions)))
            for i, name in enumerate(suggestions):
                with scols[i % len(scols)]:
                    st.markdown(f"**{name}**")
                    st.caption(descriptions.get(name, ""))
                    if st.button("Open", key=f"r1116_suggest_{i}_{safe_key(name)}", width="stretch"):
                        st.session_state.release11_16_selected_tool = name
                        st.rerun()
        if favourites:
            st.markdown("#### Favourites")
            favs = [x for x in favourites if x in tools][:8]
            if favs:
                st.caption(" · ".join(favs))
        if recent:
            st.markdown("#### Recently used")
            rec = [x for x in recent if x in tools][:8]
            if rec:
                st.caption(" · ".join(rec))

    st.markdown(f"#### Results ({len(matches)})")
    for index, name in enumerate(sorted(matches, key=lambda x: (categories.get(x, "Other"), x))):
        category = categories.get(name, "Other")
        mat = _maturity(name, category)
        cols = st.columns([0.35, 5.1, 1.0])
        fav = name in favourites
        if cols[0].button("★" if fav else "☆", key=f"r1116_fav_{index}_{safe_key(name)}", help="Add/remove favourite"):
            settings_store.toggle_favourite(name)
            st.rerun()
        cols[1].markdown(f"**{name}**  ·  `{mat}`")
        cols[1].caption(f"{category} · {descriptions.get(name, 'AGROLATTICE analytical tool.')} · Requires: {_requirements(name)}")
        if cols[2].button("Open", key=f"r1116_open_{index}_{safe_key(name)}", width="stretch"):
            st.session_state.release11_16_selected_tool = name
            st.rerun()
        st.divider()
