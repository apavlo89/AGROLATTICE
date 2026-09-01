"""Pure researcher-guidance metadata for AGROLATTICE 11.19.

This module intentionally has no Streamlit/database dependency so the guidance,
readiness rules and workflow logic can be regression tested independently.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

MODULE_VERSION = "1.0.0"

EVIDENCE_TERMS: dict[str, dict[str, str]] = {
    "Observed": {"definition": "Direct local measurement or observation recorded by a researcher, instrument or field protocol.", "caution": "Observation quality still depends on the protocol, instrument, spatial support and QC."},
    "Recorded": {"definition": "A user-recorded management, identity, geometry or administrative fact such as sowing date or irrigation applied.", "caution": "Recorded does not mean independently verified."},
    "Retrieved": {"definition": "Data acquired from an external service or catalogue, such as NASA POWER or Sentinel-2.", "caution": "Retrieved gridded or remotely sensed data are not automatically equivalent to local measurements."},
    "Derived": {"definition": "A deterministic value calculated from recorded/retrieved inputs, such as GDD, VPD or a summary statistic.", "caution": "Its validity inherits assumptions and limitations of the source inputs and formula."},
    "Mechanistic": {"definition": "Output from a process-based or physiological model with explicit biological/physical assumptions.", "caution": "Mechanistic does not mean automatically correct or locally calibrated."},
    "ML prediction": {"definition": "Output from a statistical or machine-learning model trained on historical data.", "caution": "Interpret within the model's validation and applicability scope; predictive importance is not causality."},
    "Forecast": {"definition": "A future estimate that depends on forecast inputs and/or predictive models.", "caution": "Future weather and crop states should remain distinguishable from observations."},
    "Scenario": {"definition": "A hypothetical alternative used for exploration, sensitivity analysis or decision comparison.", "caution": "A scenario is not evidence that the hypothetical action will occur or succeed."},
    "Recommendation": {"definition": "A proposed management or research action produced from evidence, constraints and assumptions.", "caution": "Recommendation is separate from acceptance and from the operation actually applied."},
    "Actual operation": {"definition": "A management action recorded as actually applied in the field.", "caution": "Record timing, amount, spatial support and deviations from the recommendation where possible."},
    "Outcome": {"definition": "A measured result observed after field management or an experiment, such as yield, seed purity or flowering date.", "caution": "Temporal order alone does not prove that the preceding action caused the outcome."},
    "Causal estimate": {"definition": "An estimated treatment effect under explicit causal assumptions and an identified analysis design.", "caution": "Report assumptions, overlap/positivity, uncertainty and sensitivity; observational estimates are not experimental proof."},
}

WORKSPACE_ORDER = [
    "Home", "Fields & Operations", "AgroLattice Twin", "Climate & Earth Observation",
    "Crop Decisions", "Experiments", "Models & Evidence", "Reports", "Data & Settings", "Help",
]

WORKSPACE_GUIDES: dict[str, dict[str, Any]] = {
    "Home": {
        "purpose": "Resume the active research context, see what changed, identify stale/missing evidence and choose the next useful action.",
        "questions": ["What is happening now?", "What needs attention?", "What should I do next?"],
        "requirements": ["country_dataset", "research_context"],
        "outputs": ["Twin/field pulse", "Priority actions", "Data freshness", "Upcoming work"],
        "cautions": ["Home is a lightweight summary; it does not automatically retrieve data or run models."],
    },
    "Fields & Operations": {
        "purpose": "Maintain authoritative research-centre/field geometry and the spatial record of work, scouting, sensors, samples and seasons.",
        "questions": ["Where exactly is the research field?", "What has been done and observed?", "What field work is due?"],
        "requirements": ["mapped_field"],
        "outputs": ["Field geometry", "Operations", "Observations", "Sensors/samples", "Field timeline"],
        "cautions": ["Field geometry is authoritative; partial-field operations and observations should retain spatial support."],
    },
    "AgroLattice Twin": {
        "purpose": "Maintain a persistent field/season digital twin linking environment, root zone, crop development, observations, EO, scenarios and outcomes.",
        "questions": ["What is the crop state?", "What is uncertain?", "Which measurement would improve the Twin?"],
        "requirements": ["mapped_field", "season", "twin"],
        "outputs": ["Twin state", "Mechanistic phenology", "Water/EO trajectories", "Scenarios", "Calibration evidence"],
        "cautions": ["Publication priors are not local genotype measurements; flowering timing does not guarantee pollen quantity or seed purity."],
    },
    "Climate & Earth Observation": {
        "purpose": "Explore the 19-variable climate dataset, retrieve field weather/EO, compare environments and quantify climate/EO context.",
        "questions": ["What environmental conditions occurred?", "How unusual were they?", "How transferable is this environment?"],
        "requirements": ["country_dataset"],
        "outputs": ["Climate summaries", "NASA field weather", "Sentinel-2 evidence", "Similarity/transferability", "Risk context"],
        "cautions": ["Climate similarity does not prove agronomic equivalence; gridded weather is not a local station measurement."],
    },
    "Crop Decisions": {
        "purpose": "Compare transparent crop-management options using field, season, Twin, environmental and model evidence while keeping recommendations separate from operations.",
        "questions": ["What options are feasible?", "What evidence supports them?", "What should be measured before acting?"],
        "requirements": ["mapped_field", "season"],
        "outputs": ["Planting/water/nutrient/pest/yield decision evidence", "Recommendations", "Outcome follow-up"],
        "cautions": ["A prediction is not a management action; recommendations require review, constraints and field validation."],
    },
    "Experiments": {
        "purpose": "Design, randomise, map, measure and analyse spatial experiments while preserving trial/block/replicate/experimental-unit structure.",
        "questions": ["Is the design reproducible?", "Which measurements are missing?", "What can be inferred from the design?"],
        "requirements": ["mapped_field", "trial"],
        "outputs": ["Protocol", "Randomisation manifest", "Experimental-unit map", "Longitudinal observations", "Outcomes"],
        "cautions": ["Respect the declared design/error strata; repeated observations from one EU/plant are not independent replicates."],
    },
    "Models & Evidence": {
        "purpose": "Govern datasets, training runs, model versions, validation, calibration, applicability, prediction outcomes and reproducibility.",
        "questions": ["How was this model trained?", "Where was it validated?", "Is this prediction in-domain and calibrated?"],
        "requirements": ["analysis_data"],
        "outputs": ["Training/validation runs", "Model cards", "Applicability", "Uncertainty/calibration", "Prediction-outcome evidence"],
        "cautions": ["Prefer grouped/site/season-aware validation over leakage-prone random splits; predictive explanations are not causal effects."],
    },
    "Reports": {
        "purpose": "Build versioned, traceable scientific reports and publications from frozen persistent AGROLATTICE evidence.",
        "questions": ["Is the evidence complete?", "Can each claim be traced?", "Can this result be reproduced?"],
        "requirements": ["report_evidence"],
        "outputs": ["Reports/manuscripts", "Tables/figures", "Claim ledger", "Reproducibility package"],
        "cautions": ["Freeze evidence before final reporting; do not promote model or observational claims beyond their validation/causal support."],
    },
    "Data & Settings": {
        "purpose": "Manage country climate workspaces, data sources, connections, protected scientific databases, backups, performance and migrations.",
        "questions": ["Are my data safe?", "Which sources/backends are available?", "Is the installation healthy?"],
        "requirements": [],
        "outputs": ["Verified backups", "Data/source inventory", "Diagnostics", "Storage/cache controls"],
        "cautions": ["Use verified backups before migrations or destructive recovery actions; cache clearing must never target scientific data."],
    },
    "Help": {
        "purpose": "Learn AGROLATTICE workflows, data requirements, terminology, scientific labels and troubleshooting without leaving the app.",
        "questions": ["What should I do first?", "What data does this workflow need?", "What does this label/term mean?"],
        "requirements": [],
        "outputs": ["Guided workflows", "Workspace guides", "Readiness checks", "Troubleshooting"],
        "cautions": ["Help explains the software and scientific boundaries; it does not replace local protocols, agronomic expertise or validation."],
    },
}

REQUIREMENTS: dict[str, dict[str, str]] = {
    "country_dataset": {"label": "Country climate workspace", "why": "Needed for historical 19-variable climate analysis; field NASA retrieval can still work from coordinates when the historical dataset is absent.", "workspace": "Data & Settings", "tool": "Dataset updater"},
    "research_context": {"label": "Active research context", "why": "Selecting a field/trial/season makes summaries and cross-workspace links context aware.", "workspace": "Fields & Operations", "tool": "Farm portfolio & mapped fields"},
    "mapped_field": {"label": "Mapped field", "why": "Authoritative field geometry links weather, EO, Twin, trial, scouting and operations to the real spatial unit.", "workspace": "Fields & Operations", "tool": "Farm portfolio & mapped fields"},
    "season": {"label": "Field season", "why": "Crop/genotype/sowing/harvest context prevents analyses from mixing different seasons.", "workspace": "Fields & Operations", "tool": "Farm portfolio & mapped fields"},
    "trial": {"label": "Mapped experiment", "why": "A trial and its experimental units are required for design-aware observations and G×E×M analysis.", "workspace": "Experiments", "tool": "Maize flowering trials & field data"},
    "trial_geometry": {"label": "Experimental-unit geometry", "why": "Spatial experimental units allow mapped treatment assignment, observations and EO extraction where resolution permits.", "workspace": "Experiments", "tool": "Maize flowering trials & field data"},
    "observations": {"label": "Field/experiment observations", "why": "Measured phenology/outcome observations are required to calibrate and validate models.", "workspace": "Experiments", "tool": "Maize flowering trials & field data"},
    "twin": {"label": "Persistent Twin", "why": "Links field/season state, environment, crop development, water, EO, scenarios and calibration over time.", "workspace": "AgroLattice Twin", "tool": "AgroLattice twin configuration"},
    "weather": {"label": "Daily weather evidence", "why": "Phenology, root-zone and many decision workflows need date-aligned daily weather.", "workspace": "Climate & Earth Observation", "tool": "Daily weather & phenology"},
    "eo": {"label": "Earth-observation evidence", "why": "Satellite observations add canopy/spatial evidence but are optional for many workflows.", "workspace": "Climate & Earth Observation", "tool": "Satellite crop monitoring"},
    "root_zone": {"label": "Root-zone state", "why": "Needed for water-stress interpretation and irrigation decision support.", "workspace": "Crop Decisions", "tool": "Soil-water balance"},
    "analysis_data": {"label": "Analysis-ready data", "why": "Training/validation requires a target, predictors and preserved grouping/site/season identifiers.", "workspace": "Models & Evidence", "tool": "Research Data Hub"},
    "model": {"label": "Registered model", "why": "Model governance starts from an immutable registered model/version and its training run.", "workspace": "Models & Evidence", "tool": "Research Model & Evidence Registry"},
    "validation": {"label": "Held-out validation evidence", "why": "Operational use requires validation appropriate to the deployment question, not training performance.", "workspace": "Models & Evidence", "tool": "Validation Centre"},
    "outcomes": {"label": "Measured outcomes", "why": "Prediction and recommendation quality can only be evaluated when real outcomes are linked later.", "workspace": "Experiments", "tool": "Maize flowering trials & field data"},
    "report_evidence": {"label": "Persistent report evidence", "why": "Reports should use traceable Field/Twin/Experiment/Model evidence rather than transient session tables.", "workspace": "Reports", "tool": "Study & publication builder"},
}

WORKFLOWS: dict[str, dict[str, Any]] = {
    "first_field": {
        "title": "Create my first mapped field & season",
        "goal": "Establish the spatial and seasonal context that every later AGROLATTICE workflow can reuse.",
        "steps": [
            ("country_dataset", "Prepare the country climate workspace", "Install or verify the country's historical 19-variable climate dataset."),
            ("mapped_field", "Map the research centre and field", "Draw/import the authoritative field polygon and verify it persists after rerun."),
            ("season", "Create the field season", "Record crop/genotype and real sowing/harvest dates when known."),
        ],
    },
    "first_trial": {
        "title": "Create my first mapped experiment",
        "goal": "Create a reproducible field experiment whose treatments, randomisation and measurements stay linked to geometry.",
        "steps": [
            ("mapped_field", "Select a mapped field", "Experiments should link to authoritative field geometry."),
            ("trial", "Create the experiment protocol", "Define objective, outcomes, design family, factors, blocks/replication and randomisation seed."),
            ("trial_geometry", "Map/randomise experimental units", "Verify treatment allocation and spatial balance before field deployment."),
            ("observations", "Collect protocol-driven observations", "Use trial/EU/plant identifiers and preserve repeated measurements."),
            ("outcomes", "Record harvest/outcome data", "Close the experiment with measured outcomes linked to the same EUs."),
        ],
    },
    "maize_synchrony": {
        "title": "Build a maize synchrony experiment",
        "goal": "Study male × female flowering synchrony as genotype × environment × management rather than a fixed sowing offset.",
        "steps": [
            ("mapped_field", "Map the seed-production field", "Use the real field polygon and season context."),
            ("trial", "Define parent-pair and management factors", "Include male/female genotypes, density, sowing dates/difference, block/replication and irrigation/management treatment."),
            ("weather", "Attach daily weather", "Use persisted field/Twin weather or retrieve NASA weather explicitly."),
            ("observations", "Collect flowering and leaf observations", "Record anthesis/silking and tagged-plant leaf development for calibration."),
            ("twin", "Link a Persistent Twin", "Use the mechanistic maize engine with parent-specific physiology and uncertainty."),
            ("outcomes", "Record seed-production outcomes", "Synchrony timing alone does not establish pollen quantity, seed set or purity."),
        ],
    },
    "persistent_twin": {
        "title": "Create & calibrate a Persistent Twin",
        "goal": "Build a long-lived field/season representation that can be revisited, calibrated and compared across seasons.",
        "steps": [
            ("mapped_field", "Choose the authoritative field", "The Twin should reference a real mapped field."),
            ("season", "Confirm crop and season", "Use explicit season/sowing context rather than generic calendar assumptions."),
            ("twin", "Create/link the Twin", "Link field and experiment where relevant."),
            ("weather", "Attach daily weather", "Retrieve/approve weather; preserve source and date coverage."),
            ("root_zone", "Establish root-zone state", "Use measured soil inputs where available and label assumptions."),
            ("observations", "Add calibration observations", "Flowering/leaf/sensor observations improve local calibration and uncertainty."),
            ("eo", "Attach EO when useful", "Use field polygon and preserve scene/quality provenance."),
        ],
    },
    "model_validation": {
        "title": "Train & validate a model",
        "goal": "Create a reproducible model whose validation design matches the intended deployment setting.",
        "steps": [
            ("analysis_data", "Build an analysis-ready dataset", "Preserve trial/field/site/season/group identifiers and prevent future/target leakage."),
            ("model", "Train and register a model version", "Persist the training run, split definition, seed, preprocessing, hyperparameters and artifact hash."),
            ("validation", "Run deployment-relevant validation", "Prefer leave-site/year/trial/genotype/parent-pair or forward validation where appropriate."),
            ("outcomes", "Link future measured outcomes", "Use later field outcomes to evaluate drift/calibration and real-world error."),
        ],
    },
    "decision_outcome": {
        "title": "Take a crop decision through to outcome",
        "goal": "Keep prediction, recommendation, applied operation and outcome distinct so decisions can later be evaluated.",
        "steps": [
            ("mapped_field", "Select the active field/season", "Decision evidence must be tied to the real management unit."),
            ("weather", "Update relevant environment evidence", "Use current persisted weather and field observations before running the decision workflow."),
            ("model", "Use an eligible model/mechanistic decision engine", "Check applicability, uncertainty and validation scope."),
            ("outcomes", "Record the actual operation and measured outcome", "Do not treat a recommendation as if it was applied."),
        ],
    },
    "publication": {
        "title": "Produce a reproducible scientific report",
        "goal": "Freeze the exact evidence, figures, methods and model versions supporting a report or manuscript.",
        "steps": [
            ("report_evidence", "Choose persistent evidence", "Use Field/Twin/Experiment/Model evidence rather than transient session-state tables."),
            ("validation", "Confirm model/statistical evidence", "Claims about model performance should point to saved held-out validation."),
            ("outcomes", "Check outcome completeness", "Mark incomplete/preliminary outcomes explicitly."),
        ],
    },
}

TROUBLESHOOTING: dict[str, dict[str, Any]] = {
    "Map is blank or disappears": {"symptoms": "Field/research-centre map is blank, flashes briefly, or saved geometry seems missing.", "steps": ["Open Data & Settings → Diagnostics and confirm the app/module preflight passes.", "Return to Fields & Operations → Map and use the saved-boundary/zoom controls before redrawing.", "Verify the field still exists in the Field Operations database; do not delete/recreate it just to refresh the map.", "If a browser-specific rendering issue persists, reload the page after confirming the database is intact."], "avoid": "Do not overwrite or delete a valid saved polygon merely because the map component failed to render."},
    "A shortcut/button appears to do nothing": {"symptoms": "A command-centre action seems to return to the same page after clicking.", "steps": ["Try the same destination from the workspace navigation to confirm whether the issue is routing or the target page.", "Check Data & Settings → Diagnostics for the current navigation/module version.", "If reproducible, record the source workspace, button label and expected destination for a navigation regression."], "avoid": "Do not repeatedly click a destructive or run-model action when the UI state is uncertain."},
    "NASA weather retrieval fails": {"symptoms": "NASA POWER request times out, returns no rows or reports an HTTP/service error.", "steps": ["Confirm the mapped field has valid centroid coordinates.", "Retry later if NASA POWER is unavailable; existing persisted weather remains usable within its coverage.", "Check the requested dates and whether the source supports them.", "Do not substitute fabricated weather values; upload an external measured dataset only when you have a real source."], "avoid": "Do not silently fill missing weather with climate normals when the workflow expects observed/retrieved daily weather."},
    "Sentinel/STAC retrieval fails": {"symptoms": "Scene search returns provider/server errors or no usable clear scenes.", "steps": ["Use provider failover/advanced EO controls and inspect the requested date window and AOI.", "Check cloud/usable-pixel criteria before assuming imagery is missing.", "Retry provider access later if a STAC endpoint is unavailable."], "avoid": "Do not report an EO metric when no acceptable scene/pixels were processed."},
    "The app feels slow": {"symptoms": "Workspace navigation or a specific analysis takes longer than expected.", "steps": ["Distinguish first-load cost from repeated navigation; the large country climate dataset is process-cached after initial preparation.", "Open Data & Settings → Performance & Storage to inspect cache/storage state.", "Avoid triggering NASA/STAC/model runs unless needed; modern command-centre landing pages should remain lightweight."], "avoid": "Do not delete scientific databases or installed climate datasets to 'speed up' the app."},
    "Optional ML/crop-model feature is unavailable": {"symptoms": "TabPFN/PyTorch/AquaCrop/DSSAT/APSIM or another optional backend is reported missing.", "steps": ["Open Data & Settings → Connections and verify the optional package/executable.", "Use the bundled optional-dependency installer where applicable.", "For DSSAT/APSIM, configure the executable path once and verify its version/health before a run."], "avoid": "A missing optional backend should not prevent the core application from starting."},
    "Database/schema problem": {"symptoms": "Startup preflight or a workspace reports an integrity/schema error.", "steps": ["Do not keep writing to the affected database.", "Open Data & Settings → Databases & Backups and run integrity checks.", "Create/verify a backup before any recovery action.", "Use the release migration/restore workflow rather than manually editing SQLite tables."], "avoid": "Never replace protected databases with empty files or run ad-hoc destructive SQL during recovery."},
    "A model looks excellent but may be leaking": {"symptoms": "Validation is unexpectedly high or random CV greatly exceeds site/year/field holdout performance.", "steps": ["Inspect the validation split before training and confirm repeated rows from one field/EU/plant stay together.", "Fit imputation/scaling/SMOTE/feature selection inside training folds only.", "Use leave-site/year/trial/genotype/parent-pair or forward validation that matches deployment."], "avoid": "Do not promote a model based on training metrics or leakage-prone random row splits."},
}

GLOSSARY: dict[str, str] = {
    "Experimental unit": "The smallest independently treated/randomised unit. It may be displayed as a subplot in friendlier UI text.",
    "G×E×M": "Genotype × Environment × Management: the interacting biological, environmental and management context AGROLATTICE is designed to learn.",
    "Persistent Twin": "A long-lived digital representation of a real field/season linking state, observations, scenarios, calibration, uncertainty and outcomes.",
    "Applicability / OOD": "Whether a new prediction lies within the model's training support; out-of-domain predictions require extra caution even if a point prediction is available.",
    "LOYO": "Leave-one-year-out validation, useful for testing transfer to an unseen season/year.",
    "LORO": "Leave-one-region-out validation, useful for testing geographic transfer.",
    "Leave-one-parent-pair-out": "Validation in maize synchrony where all rows from one male×female parent combination are held out together.",
    "Aleatoric uncertainty": "Uncertainty associated with irreducible/data noise under the modelling assumptions.",
    "Epistemic uncertainty": "Uncertainty associated with limited model/parameter knowledge that may reduce with better data/model information.",
    "Conformal interval": "A prediction interval calibrated from held-out residuals under assumptions appropriate to the chosen conformal method.",
    "Weak supervision": "Learning from coarse or aggregate labels while predicting at a finer support; fine-scale predictions still require independent validation.",
    "Climate analogue": "A historical/location environment that is similar under a defined metric/variables; similarity does not prove agronomic equivalence.",
    "RAW": "Readily available water: the fraction of total available root-zone water that can be depleted before water stress is expected.",
    "Ks": "Water-stress coefficient; values near 1 imply little water limitation in the root-zone model, lower values reduce crop water use." ,
    "tln": "Total leaf number parameter used by the mechanistic maize model; publication priors are not measurements of local lines.",
    "coblf": "Maize leaf-appearance parameter in the mechanistic model; should be calibrated with local leaf observations when possible.",
    "ebR1": "Female ear-biomass threshold parameter associated with 50% silking in the mechanistic maize model.",
}


def requirement_status(key: str, state: Mapping[str, Any]) -> str:
    """Return Ready / Partial / Missing for a requirement from a derived app-state mapping."""
    value = state.get(key)
    if isinstance(value, str):
        norm = value.strip().casefold()
        if norm in {"ready", "complete", "current", "yes", "true"}:
            return "Ready"
        if norm in {"partial", "review", "stale", "limited"}:
            return "Partial"
        if norm in {"missing", "no", "false", ""}:
            return "Missing"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return "Ready" if value > 0 else "Missing"
    if value is True:
        return "Ready"
    if value is False or value is None:
        return "Missing"
    return "Ready"


def readiness_rows(workspace: str, state: Mapping[str, Any]) -> list[dict[str, str]]:
    guide = WORKSPACE_GUIDES.get(workspace, {})
    rows: list[dict[str, str]] = []
    for key in guide.get("requirements", []):
        meta = REQUIREMENTS[key]
        rows.append({"key": key, "label": meta["label"], "status": requirement_status(key, state), "why": meta["why"], "workspace": meta["workspace"], "tool": meta["tool"]})
    return rows


def workflow_progress(workflow_id: str, state: Mapping[str, Any]) -> dict[str, Any]:
    flow = WORKFLOWS[workflow_id]
    steps = []
    ready = 0
    for key, title, detail in flow["steps"]:
        status = requirement_status(key, state)
        ready += int(status == "Ready")
        meta = REQUIREMENTS[key]
        steps.append({"key": key, "title": title, "detail": detail, "status": status, "workspace": meta["workspace"], "tool": meta["tool"]})
    total = len(steps)
    return {"id": workflow_id, "title": flow["title"], "goal": flow["goal"], "steps": steps, "ready": ready, "total": total, "progress": (ready / total if total else 1.0)}


def search_guidance(query: str) -> list[dict[str, str]]:
    q = str(query or "").strip().casefold()
    if not q:
        return []
    tokens = q.split()
    hits: list[dict[str, str]] = []
    for workspace, guide in WORKSPACE_GUIDES.items():
        text = " ".join([workspace, guide.get("purpose", ""), *guide.get("questions", []), *guide.get("outputs", []), *guide.get("cautions", [])]).casefold()
        if all(t in text for t in tokens):
            hits.append({"kind": "Workspace", "title": workspace, "detail": guide.get("purpose", "")})
    for term, definition in GLOSSARY.items():
        text = f"{term} {definition}".casefold()
        if all(t in text for t in tokens):
            hits.append({"kind": "Glossary", "title": term, "detail": definition})
    for title, item in TROUBLESHOOTING.items():
        text = " ".join([title, item.get("symptoms", ""), *item.get("steps", []), item.get("avoid", "")]).casefold()
        if all(t in text for t in tokens):
            hits.append({"kind": "Troubleshooting", "title": title, "detail": item.get("symptoms", "")})
    for key, flow in WORKFLOWS.items():
        text = " ".join([flow["title"], flow["goal"], *(s[1] + " " + s[2] for s in flow["steps"])]).casefold()
        if all(t in text for t in tokens):
            hits.append({"kind": "Guided workflow", "title": flow["title"], "detail": flow["goal"]})
    return hits
