"""AgroLattice Release 10.4 contextual help system.

Adds native Streamlit help icons to input widgets, compact hover help for tabs,
charts, maps and tables, and a user-selectable help density. The implementation
is deliberately centralised so all existing workspaces and imported modules gain
help without rewriting hundreds of controls one by one.
"""

from __future__ import annotations

import html
import inspect
import re
import sys
from collections.abc import Callable, Iterable, Sequence
from typing import Any

MODULE_VERSION = "10.4.4"

_ST: Any | None = None
_PATCHED = False
_ORIGINALS: dict[tuple[str, str], Any] = {}

TERM_DEFINITIONS = {
    "AOI": "Area of interest: the exact point buffer or polygon analysed on a map or by satellite.",
    "Anthesis": "The flowering stage when anthers release pollen. In maize this is commonly represented by active pollen shed from the male parent.",
    "Silking": "Emergence of silks from the female maize ear. Silks must be receptive while viable pollen is available.",
    "Detasselling": "Removal of tassels from female maize rows before pollen release to prevent self-pollination in hybrid seed production.",
    "Seed set": "The percentage of potential kernel sites that become filled kernels after successful fertilisation and development.",
    "Pure seed": "The proportion of a sample that meets the programme's physical or varietal definition of pure seed. Document the exact test used.",
    "Genetic purity": "The proportion of seed that genetically matches the intended hybrid or parentage, measured with an accepted purity method.",
    "Kernel rows per ear": "The number of longitudinal rows of kernels around a maize ear; a yield-component and ear-trait measurement.",
    "GDD": "Growing degree days: accumulated thermal time above a base temperature, usually capped at an upper temperature.",
    "Phenology": "The timing of crop development stages such as emergence, flowering and maturity.",
    "ET0": "Reference evapotranspiration: atmospheric evaporative demand from a standard reference surface.",
    "ETc": "Crop evapotranspiration: estimated crop water use, commonly calculated as crop coefficient Kc multiplied by ET0.",
    "Kc": "Crop coefficient: a stage-dependent multiplier that converts ET0 into crop evapotranspiration.",
    "TAW": "Total available water: root-zone water held between field capacity and permanent wilting point.",
    "RAW": "Readily available water: the fraction of TAW that can be depleted before crop water stress is expected.",
    "Ks": "Water-stress coefficient: a value near 1 indicates little water limitation; lower values reduce estimated crop evapotranspiration.",
    "Field capacity": "The water content remaining after excess gravitational water has drained from the soil.",
    "Permanent wilting point": "The soil water content below which plants generally cannot recover turgor.",
    "Root-zone depletion": "The amount of plant-available water removed from the effective rooting depth relative to field capacity.",
    "Deep percolation": "Water that drains below the simulated root zone and is no longer available to the crop in the model.",
    "Capillary rise": "Upward movement of groundwater into the root zone; use only when supported by local evidence.",
    "Curve number": "An NRCS runoff parameter representing rainfall-runoff potential; higher values generally imply more runoff.",
    "NDVI": "Normalised Difference Vegetation Index, commonly used as a canopy greenness or vigour indicator.",
    "EVI": "Enhanced Vegetation Index, designed to improve canopy sensitivity and reduce some background and atmospheric effects.",
    "NDMI": "Normalised Difference Moisture Index, sensitive to canopy water content and moisture-related change.",
    "NDRE": "Normalised Difference Red Edge Index, often sensitive to chlorophyll and canopy status in developed crops.",
    "SCL": "Sentinel-2 Scene Classification Layer, used to mask clouds, shadows, snow and other unwanted pixel classes.",
    "PCA": "Principal component analysis: a dimension-reduction method that summarises correlated variables into orthogonal axes.",
    "K-means": "A clustering algorithm that partitions observations around cluster centres in feature space.",
    "Silhouette score": "A cluster-quality measure comparing within-cluster cohesion with separation from other clusters.",
    "MAE": "Mean absolute error: the average absolute difference between prediction and observation.",
    "RMSE": "Root mean squared error: an error metric that gives greater weight to large errors.",
    "R-squared": "The proportion of observed variance explained by predictions; it can be negative on validation data.",
    "Calibration": "Agreement between predicted and observed levels across the prediction range.",
    "Experimental unit": "The smallest independently treated or randomised unit in an experiment; AGROLATTICE may display it as a subplot in friendlier UI text.",
    "Applicability": "Whether a new prediction lies within the model's training and validation support. An out-of-domain prediction requires extra caution.",
    "Forecast": "A future estimate based on forecast inputs and/or predictive models; it should remain visually distinct from observations.",
    "Mechanistic model": "A process-based model with explicit biological or physical assumptions. Mechanistic does not mean automatically locally valid.",
    "Grouped cross-validation": "Validation that keeps related observations, such as the same field or year, together to reduce leakage.",
    "NASA POWER": "A global gridded meteorological and solar-data service used for point-based climate and daily weather acquisition.",
    "Sentinel-2": "A European optical Earth-observation satellite mission providing multispectral imagery, including 10 m and 20 m bands.",
    "AquaCrop": "FAO's crop-water productivity model, represented here through AquaCrop-OSPy when installed.",
    "DSSAT": "Decision Support System for Agrotechnology Transfer, an external process-based crop-modelling system.",
    "APSIM": "Agricultural Production Systems sIMulator, an external process-based modelling framework.",
}

EXACT_CONTROL: dict[str, tuple[str, str]] = {
    "Country": ("Select the active country workspace. It controls the country climate dataset, location catalogue, updater folders, backups and similarity cache.", "Mexico"),
    "Country to download or update": ("Select the country whose NASA POWER dataset will be created or refreshed. This can differ from the currently viewed country.", "Cyprus"),
    "Workspace preset": ("Changes recommended shortcuts and terminology emphasis without hiding or removing tools.", "Researcher"),
    "Workspace view": ("Choose the functional view inside the current consolidated workspace. Your active country, project, field and trial remain unchanged.", "Live state"),
    "Analysis": ("Choose the analysis view inside the current studio. The selection changes what is displayed, not the underlying data.", "Clusters"),
    "Search": ("Enter part of a tool, field, trial or concept name to find it quickly.", "maize"),
    "Search tools": ("Search all original analytical tools by name, workspace or purpose.", "similarity"),
    "Matching tools": ("Select one tool returned by the sidebar search.", "Maize flowering trials & field data"),
    "Project": ("Select the persistent project whose crop, location and season context should be active.", "2027 maize trial"),
    "Field": ("Select the mapped field used by operations, satellite, sensor or Twin workflows.", "Field 3"),
    "Plot": ("Select the experimental plot whose observations, geometry or predictions should be used.", "Block 2 - Plot 4"),
    "Trial": ("Select the experimental trial whose design, plots, observations and outcomes should be active.", "2027 maize flowering synchrony trial"),
    "Active pollination trial": ("Select the maize trial whose plots, observations and outcomes should be used.", "2027 maize flowering synchrony trial"),
    "Location source": ("Choose a location from the country catalogue or enter exact custom coordinates.", "App city"),
    "Location": ("Select the city, mapped location or project location used by the current analysis.", "Montecillo (México)"),
    "Site": ("Enter or select the physical research location. Use a stable site name across seasons.", "Montecillo Research Station"),
    "Latitude": ("North-south coordinate in decimal degrees. Positive values are north of the equator.", "19.46"),
    "Longitude": ("East-west coordinate in decimal degrees. Verify the sign and map position before downloading weather or satellite data.", "-98.90"),
    "Crop": ("Select the crop whose validated parameters or custom profile should be used.", "Maize"),
    "Crop profile": ("Select a validated or custom set of crop thresholds, stage durations and water-response parameters.", "Validated maize profile"),
    "Primary outcome": ("Choose the main response the experiment is designed to optimise or explain.", "Seed-set percentage"),
    "Protocol notes": ("Document design details, sampling rules, measurement definitions, exclusions and deviations from protocol.", "Assess 20 male and 20 female plants per plot each morning."),
    "Male sowing offsets relative to female (days)": ("Enter male planting offsets relative to the female sowing date. Negative values mean male earlier; positive values mean male later.", "-6,-4,-2,0,2,4,6"),
    "Randomisation seed": ("A fixed number that makes treatment randomisation reproducible. The same design and seed produce the same assignment.", "2027"),
    "Random seed": ("A fixed number that makes clustering or model fitting reproducible.", "42"),
    "Prediction target": ("Select the outcome the machine-learning models should predict.", "Seed-set percentage"),
    "Predictors": ("Select explanatory variables supplied to the model. Avoid variables measured after the outcome or derived from the target.", "Sowing offset, GDD and pre-flowering water stress"),
    "Independent validation group": ("Choose the grouping variable that defines independent validation units and prevents data leakage.", "Year or field"),
    "Validation folds": ("Set the number of cross-validation partitions. It cannot exceed the available independent groups.", "5"),
    "Target GDD": ("Enter the thermal-time requirement for the selected flowering or development event.", "650 GDD"),
    "GDD base temperature (°C)": ("Lower developmental threshold. Temperatures below this value contribute no thermal time in the capped method.", "10 °C"),
    "GDD upper cap (°C)": ("Upper temperature used in capped GDD. Higher temperatures receive no additional developmental credit.", "30 °C"),
    "GDD base temperature": ("Lower developmental threshold. Temperatures below this value contribute no thermal time.", "10 °C"),
    "GDD upper cap": ("Upper temperature used in capped GDD. Higher temperatures receive no additional developmental credit.", "30 °C"),
    "Area source": ("Choose where satellite geometry comes from: a city buffer, uploaded polygon, project, mapped field, trial plot or current session field.", "Mapped field"),
    "Buffer radius (m)": ("Set the radius around a point when an exact polygon boundary is unavailable.", "500 m"),
    "Maximum scene cloud (%)": ("Filter catalogue scenes using scene-level cloud metadata before pixel-level masking.", "30%"),
    "Minimum clear field pixels (%)": ("Reject scenes when too little of the field remains after cloud and quality masking.", "60%"),
    "Analysis resolution": ("Set output pixel size. Finer resolution preserves detail but increases processing cost.", "10 m"),
    "Indices": ("Select vegetation and moisture indices calculated from each accepted satellite scene.", "NDVI, EVI, NDMI and NDRE"),
    "Catalogue provider": ("Select the STAC catalogue used to find Sentinel-2 scenes. Automatic failover tries another provider when needed.", "Automatic failover"),
    "Planting or season start date": ("Set day 1 for weather, phenology and crop-water calculations.", "1 May 2027"),
    "Planting or simulation start date": ("Set the date from which stage durations or GDD are accumulated.", "1 May 2027"),
    "Stage-prediction method": ("Choose calendar-duration ranges or cumulative GDD targets for predicting crop stages.", "User-defined cumulative GDD targets"),
    "Time standard": ("Choose local solar time or UTC for NASA POWER daily output.", "LST"),
    "First historical year": ("First year included in the historical comparison.", "1991"),
    "Last historical year": ("Last year included in the historical comparison.", "2025"),
    "Target season year": ("Season compared with historical years or a baseline.", "2025"),
    "Season length (days)": ("Number of days included after the planting or season-start date.", "150 days"),
    "Minimum monthly daily coverage": ("Minimum percentage of expected daily values required before a monthly aggregate is accepted.", "90%"),
    "Deduplicate locations by approximate NASA meteorological grid cell": ("Download one NASA point for cities resolving to the same approximate grid cell, then assign the shared profile to each city.", "Enabled"),
    "Request legacy optional NASA parameters": ("Request variables used by older datasets. Leave off unless backward compatibility is required.", "Disabled"),
    "Delay between grid requests (seconds)": ("Pause between public NASA requests to reduce rate-limiting risk.", "1.5 seconds"),
    "Create mixed-format export": ("Create an optional legacy-style export. The current app uses long-format country datasets, so this can normally remain off.", "Disabled"),
    "Create legacy very-wide export": ("Create a large very-wide legacy file. It is not required by the current app.", "Disabled"),
    "Ignore local NASA cache": ("Force a new request instead of reusing a compatible locally cached response.", "Disabled"),
    "Ignore local cache and download again": ("Force a fresh daily-weather request rather than using cached data.", "Disabled"),
    "Application efficiency": ("Fraction of gross irrigation that reaches and is stored in the root zone.", "0.75"),
    "Initial depletion (% of TAW)": ("Set how dry the root zone is at the simulation start, expressed as a percentage of total available water.", "25%"),
    "Runoff method": ("Choose how rainfall runoff is estimated: none, fixed fraction or NRCS curve-number method.", "NRCS curve number"),
    "Map metric": ("Select the variable used to colour mapped fields or plots.", "Inspection priority"),
    "Farm to delete": ("Select the farm that will be permanently removed together with every field and dependent operations record inside it.", "Montecillo Research Station"),
    "Field to delete": ("Select the mapped field that will be permanently removed together with its dependent field-operation records.", "Field 3"),
    "Twin to delete": ("Select the AgroLattice Twin link that will be permanently removed together with saved Twin outputs. The underlying field and trial are retained.", "2027 maize Twin"),
    "Stored outputs to clear": ("Choose old Twin snapshots, scenarios, recommendations or registered models to remove while keeping the Twin link and calibration.", "Saved snapshots and scenarios"),
    "Twin state date": ("Set the date on which the field state is reconstructed.", "Latest available date"),
    "Plant height (cm)": ("Record plant height using the trial's documented method, for example soil surface to the uppermost leaf collar or tassel tip.", "180 cm"),
    "Male plant height (cm)": ("Record male-parent plant height in centimetres using the same method and timing across plots.", "185 cm"),
    "Female plant height (cm)": ("Record female-parent plant height in centimetres using the same method and timing across plots.", "170 cm"),
    "Male flowering-initiation date": ("Record the first date male flowering or pollen-shed activity is observed according to the protocol.", "15 July 2027"),
    "Female flowering-initiation date": ("Record the first date female silks emerge according to the protocol.", "17 July 2027"),
    "Male flowering date": ("Record the protocol-defined male flowering date, commonly 50% active pollen shed.", "19 July 2027"),
    "Female flowering date": ("Record the protocol-defined female flowering date, commonly 50% silking.", "20 July 2027"),
    "Kernel rows per ear": ("Record the number of longitudinal kernel rows around each sampled ear.", "14 rows"),
    "Pure seed (%)": ("Record physical or varietal pure-seed percentage using the breeding programme's documented test.", "98.5%"),
    "Genetic purity (%)": ("Record the percentage confirmed to match intended parentage or hybrid identity using an accepted method.", "99.0%"),
    "Seed-set percentage": ("Record filled kernels as a percentage of filled plus unfilled kernel sites.", "88%"),
    "Farm to edit": ("Select an existing farm or research station whose metadata should be changed.", "Montecillo Research Station"),
    "Field to edit": ("Select an existing mapped field whose metadata, parent farm or boundary should be changed.", "Farm A · Field 3"),
    "Boundary update": ("Keep the current polygon or replace it with a newly supplied geometry.", "Keep existing boundary"),
    "Field status": ("Describe whether the field is active, planned, fallow, completed or archived.", "Active"),
}

PATTERN_RULES: list[tuple[str, str, str]] = [
    (r"country", "Select the country context or country-specific dataset.", "Mexico"),
    (r"administrative region|state|province|district", "Select a first-level administrative area used to filter locations.", "Guanajuato"),
    (r"(^|\s)(city|location|site|field)(\s|$)", "Select the geographic or experimental unit used by the analysis.", "A mapped research field or catalogue city"),
    (r"year$", "Select a calendar or season year included in the analysis.", "2025"),
    (r"(start|end).*date|date$", "Set a temporal boundary or recorded field date. Use the actual field record when available.", "1 May 2027"),
    (r"period", "Define the years or dates included in the calculation.", "1991-2025"),
    (r"months?$", "Select the months included in a crop window or climate summary.", "May-September"),
    (r"stage", "Select a crop-development phase such as establishment, flowering or maturity.", "Flowering"),
    (r"variety|cultivar|parent line", "Identify the genetic material being studied. Use the official breeding or cultivar code.", "CML-XXX"),
    (r"plant height", "Record plant height in centimetres using a consistent documented measurement method.", "180 cm"),
    (r"flowering initiation", "Record the first date flowering activity is observed according to the protocol.", "15 July 2027"),
    (r"flowering date", "Record the protocol-defined flowering date, such as 50% flowering.", "19 July 2027"),
    (r"kernel rows|lines per ear", "Record the number of longitudinal kernel rows around each ear.", "14 rows"),
    (r"pure seed", "Record physical or varietal pure-seed percentage using the documented test.", "98.5%"),
    (r"genetic purity", "Record the percentage confirmed to match intended parentage or hybrid identity.", "99.0%"),
    (r"germination", "Record the percentage of tested seeds that germinate under the specified method.", "95%"),
    (r"seed.?set", "Record or predict the percentage of potential kernel sites that produce filled kernels.", "88%"),
    (r"sowing offset", "Difference between male and female sowing dates. Negative means male earlier; positive means male later.", "-2 days"),
    (r"blocks?", "Number or identity of spatial blocks used to control field heterogeneity.", "3 blocks"),
    (r"replicates?", "Number of independent repetitions of each treatment.", "1 per treatment per block"),
    (r"row ratio", "Arrangement of female to male rows in hybrid seed production.", "4:2"),
    (r"planting density", "Target plant population per hectare. Document whether this includes both male and female plants.", "65,000 plants/ha"),
    (r"random.*seed", "Fixed value used to reproduce randomisation, clustering or model fitting.", "42"),
    (r"number of clusters|clusters$", "Set the requested number of groups. Do not exceed the number of distinct usable climate profiles.", "3 clusters"),
    (r"principal components|components$", "Set how many PCA axes are retained or displayed.", "2 components"),
    (r"folds", "Set the number of cross-validation partitions.", "5 folds"),
    (r"target", "Select the response variable or event the analysis predicts or evaluates.", "Seed-set percentage"),
    (r"predictor|feature", "Select explanatory variables supplied to a model. Avoid target leakage.", "GDD, water stress and sowing offset"),
    (r"validation group", "Define independent groups that must not be split across training and validation.", "Year"),
    (r"metric", "Select the result variable used in a chart, ranking or comparison.", "RMSE"),
    (r"aggregation", "Define how multiple components are combined, for example limiting factor or arithmetic mean.", "Limiting factor"),
    (r"weight", "Control the relative influence of a variable or component in a combined score.", "Temperature weight = 1.5"),
    (r"threshold", "Set the value at which a condition, alert or classification changes.", "Ks below 0.6"),
    (r"minimum|maximum", "Set a lower or upper screening, processing or validation limit.", "Use a locally justified value"),
    (r"cloud", "Control satellite cloud filtering or masking.", "30% maximum scene cloud"),
    (r"resolution", "Control spatial or temporal detail and computational cost.", "10 m satellite pixels"),
    (r"baseline", "Define the reference period or scenario against which change is measured.", "1985-2014"),
    (r"scenario", "Select or define an alternative assumption set for comparison with the baseline.", "Add 25 mm irrigation"),
    (r"irrigation", "Configure irrigation timing, amount, efficiency or scenario assumptions.", "Trigger at RAW with 75% efficiency"),
    (r"precipitation|rainfall", "Control or select rainfall-related inputs or outputs, usually in millimetres.", "500 mm seasonal rainfall"),
    (r"temperature", "Control or select a temperature threshold, range or variable in degrees Celsius.", "30 °C"),
    (r"water deficit", "Represent precipitation or available water falling below atmospheric or crop demand.", "-150 mm"),
    (r"root depth", "Define the depth of soil explored by roots and therefore the size of the simulated water reservoir.", "1.2 m"),
    (r"efficiency", "Fraction of an applied resource that reaches its intended target.", "0.75"),
    (r"notes|description|source", "Store contextual information, methods, data provenance or interpretation notes.", "Include instrument, sampling method and citation."),
]

TERM_KEYWORDS = {
    "gdd": "GDD", "growing degree": "GDD", "phenology": "Phenology", "anthesis": "Anthesis",
    "pollen": "Anthesis", "silking": "Silking", "detass": "Detasselling", "seed set": "Seed set",
    "pure seed": "Pure seed", "genetic purity": "Genetic purity", "kernel rows": "Kernel rows per ear",
    "et0": "ET0", "etc": "ETc", "crop coefficient": "Kc", " kc": "Kc", "taw": "TAW", "raw": "RAW",
    " ks": "Ks", "field capacity": "Field capacity", "wilting": "Permanent wilting point",
    "depletion": "Root-zone depletion", "deep percolation": "Deep percolation", "capillary rise": "Capillary rise",
    "curve number": "Curve number", "ndvi": "NDVI", "evi": "EVI", "ndmi": "NDMI", "ndre": "NDRE",
    "scl": "SCL", "pca": "PCA", "silhouette": "Silhouette score", "aquacrop": "AquaCrop",
    "dssat": "DSSAT", "apsim": "APSIM", "nasa power": "NASA POWER", "sentinel": "Sentinel-2",
    "mae": "MAE", "rmse": "RMSE", "r-squared": "R-squared", "calibration": "Calibration",
}

INPUT_WIDGETS = (
    "selectbox", "multiselect", "radio", "segmented_control", "pills", "checkbox", "toggle",
    "slider", "select_slider", "number_input", "date_input", "time_input", "text_input",
    "text_area", "file_uploader", "color_picker", "camera_input", "chat_input",
)
ACTION_WIDGETS = ("button", "form_submit_button", "download_button")
OUTPUT_WIDGETS = (
    "plotly_chart", "altair_chart", "pyplot", "line_chart", "bar_chart", "area_chart",
    "scatter_chart", "map", "dataframe", "data_editor", "metric",
)


def _clean_label(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = re.sub(r"\s*[:?]\s*$", "", text)
    return text


def _mode() -> str:
    if _ST is None:
        return "Detailed"
    try:
        return str(_ST.session_state.get("agrolattice_help_mode", "Detailed"))
    except Exception:
        return "Detailed"


def _specific_help(label: str) -> tuple[str, str] | None:
    clean = _clean_label(label)
    if clean in EXACT_CONTROL:
        return EXACT_CONTROL[clean]
    lower = clean.casefold()
    for pattern, explanation, example in PATTERN_RULES:
        if re.search(pattern, lower):
            return explanation, example
    return None


def _term_notes(text: str, *, limit: int = 3) -> list[str]:
    lower = f" {str(text).casefold()} "
    terms: list[str] = []
    for keyword, term in TERM_KEYWORDS.items():
        if keyword in lower and term not in terms:
            terms.append(term)
        if len(terms) >= limit:
            break
    return [f"{term}: {TERM_DEFINITIONS[term]}" for term in terms if term in TERM_DEFINITIONS]


def explain_control(label: Any, widget_type: str = "control") -> str | None:
    """Return concise field help suitable for Streamlit's native ``help`` tooltip."""
    clean = _clean_label(label)
    if not clean or clean.casefold() in {"none", "<none>"}:
        return None
    mode = _mode()
    if mode == "Off":
        return None
    specific = _specific_help(clean)
    if specific:
        explanation, example = specific
    elif mode == "Essential":
        return None
    elif widget_type in {"checkbox", "toggle"}:
        explanation = f"Enable or disable '{clean}'. Leave the default unchanged unless the alternative is intentional."
        example = "Toggle only when the workflow or protocol requires it."
    elif widget_type in {"selectbox", "radio", "segmented_control", "pills"}:
        explanation = f"Select one option for '{clean}'. Available choices may depend on the active country, dataset, project or earlier selection."
        example = "Choose the option that matches the research question."
    elif widget_type == "multiselect":
        explanation = f"Select one or more entries for '{clean}'. More entries broaden the analysis and may increase processing time."
        example = "Select only variables, locations or treatments required for the analysis."
    elif widget_type in {"slider", "select_slider", "number_input"}:
        explanation = f"Enter or adjust '{clean}'. Use the displayed units and a scientifically justified value."
        example = "Start with the documented default, then test sensitivity where appropriate."
    elif widget_type in {"date_input", "time_input"}:
        explanation = f"Set the date or time for '{clean}'. Confirm that it matches local field records and the crop season."
        example = "Use the recorded field date rather than an estimate when available."
    elif widget_type in {"text_input", "text_area", "chat_input"}:
        explanation = f"Enter the requested information for '{clean}'. Use consistent identifiers and document methods or sources where relevant."
        example = "Use a clear name that remains meaningful in exports."
    elif widget_type in {"file_uploader", "camera_input"}:
        explanation = f"Provide the file or image required for '{clean}'. Check the displayed template, accepted type and required columns before import."
        example = "Use the matching AgroLattice template when one is provided."
    elif widget_type in ACTION_WIDGETS:
        action = clean.casefold()
        if any(word in action for word in ("delete", "reset", "clear", "install", "replace")):
            explanation = f"Runs '{clean}'. This may clear, replace or permanently alter stored data, so verify the active country, field or trial first."
            example = "Keep a backup and review confirmation controls before continuing."
        elif widget_type == "download_button":
            explanation = f"Downloads '{clean}' using the current analysis results and context."
            example = "Save the file with country, project and analysis date in its filename."
        else:
            explanation = f"Runs '{clean}' using the current selections."
            example = "Review inputs and warnings before starting the action."
    else:
        explanation = f"Configures '{clean}' for the current tool."
        example = "Use the value appropriate to the active analysis."
    pieces = [explanation, f"Example: {example}"]
    pieces.extend(_term_notes(clean + " " + explanation, limit=2))
    return "\n\n".join(pieces)[:1800]


def explain_tab(label: Any) -> str:
    clean = _clean_label(label)
    specific = _specific_help(clean)
    if specific:
        explanation, example = specific
        return f"{clean}: {explanation} Example: {example}"
    lower = clean.casefold()
    tab_rules = [
        (("overview", "summary", "dashboard", "live state"), "Shows the main status, key metrics and highest-priority results."),
        (("setup", "configuration", "settings", "design"), "Defines assumptions, identifiers, geometry or parameters used by later calculations."),
        (("map", "field", "plots", "geometry"), "Displays or edits spatial boundaries and mapped experimental units."),
        (("weather", "climate"), "Displays weather inputs, climate summaries or derived environmental indicators."),
        (("gdd", "phenology", "flowering"), "Shows crop-development timing and thermal-time calculations."),
        (("water", "irrigation", "soil"), "Shows root-zone water status, crop water demand and irrigation assumptions."),
        (("satellite", "remote sensing"), "Shows Sentinel-2 scenes, vegetation or moisture indices and spatial crop patterns."),
        (("observations", "field data", "measurements"), "Captures or reviews repeated field measurements and quality-control notes."),
        (("harvest", "outcomes", "seed quality"), "Captures or analyses final yield, seed-set and seed-quality outcomes."),
        (("model", "prediction", "validation"), "Fits, evaluates or compares predictive models using the selected target and features."),
        (("scenario", "what-if"), "Compares alternative assumptions with the current or baseline state."),
        (("report", "export", "publication"), "Builds downloadable tables, figures, records or publication packages."),
        (("audit", "provenance", "history"), "Reviews data sources, saved runs, changes and reproducibility records."),
    ]
    for keywords, text in tab_rules:
        if any(keyword in lower for keyword in keywords):
            return f"{clean}: {text}"
    return f"{clean}: Opens this view while preserving the active country, project, field, season and trial context."


def _escape_title(text: str) -> str:
    return html.escape(re.sub(r"\s+", " ", str(text)).strip(), quote=True)


def _render_hover(container: Any, label: str, tooltip: str, *, kind: str = "help") -> None:
    if _mode() == "Off" or not tooltip:
        return
    safe_label = html.escape(str(label))
    safe_tooltip = _escape_title(tooltip)
    markup = (
        f'<div class="agl-context-help agl-context-help-{html.escape(kind)}">'
        f'<span class="agl-context-help-label">{safe_label}</span>'
        f'<span class="agl-help-dot" role="img" aria-label="{safe_tooltip}" title="{safe_tooltip}">?</span>'
        f'</div>'
    )
    try:
        container.markdown(markup, unsafe_allow_html=True)
    except Exception:
        try:
            _ST.markdown(markup, unsafe_allow_html=True)
        except Exception:
            pass


def _inject_css(st_module: Any) -> None:
    css = """
<style>
.agl-context-help { display:flex; align-items:center; justify-content:flex-end; gap:.32rem; min-height:.9rem; margin:.05rem 0 .18rem 0; color:rgba(49,51,63,.70); font-size:.72rem; line-height:1; }
.agl-context-help-tabs { justify-content:flex-start; margin:.05rem 0 .15rem 0; }
.agl-context-help-label { font-weight:500; }
.agl-help-dot { display:inline-flex; width:1.02rem; height:1.02rem; align-items:center; justify-content:center; border:1px solid rgba(49,51,63,.30); border-radius:999px; font-weight:700; font-size:.72rem; cursor:help; background:rgba(255,255,255,.50); color:rgba(49,51,63,.82); }
.agl-help-dot:hover { border-color:var(--primary-color, #2e7d32); color:var(--primary-color, #2e7d32); background:rgba(46,125,50,.08); }
@media (prefers-color-scheme: dark) {
  .agl-context-help { color:rgba(250,250,250,.68); }
  .agl-help-dot { color:rgba(250,250,250,.86); border-color:rgba(250,250,250,.35); background:rgba(0,0,0,.18); }
}
</style>
"""
    try:
        st_module.markdown(css, unsafe_allow_html=True)
    except Exception:
        pass


def _supports_parameter(callable_obj: Any, parameter: str) -> bool:
    try:
        signature = inspect.signature(callable_obj)
    except (TypeError, ValueError):
        return False
    if parameter in signature.parameters:
        return True
    return any(item.kind == inspect.Parameter.VAR_KEYWORD for item in signature.parameters.values())


def _wrap_input(original: Callable[..., Any], widget_type: str, *, method: bool) -> Callable[..., Any]:
    supports_help = _supports_parameter(original, "help")

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        offset = 1 if method else 0
        label = args[offset] if len(args) > offset else kwargs.get("label", "")
        text = explain_control(label, widget_type)
        if text and not kwargs.get("help"):
            if supports_help:
                kwargs["help"] = text
            else:
                container = args[0] if method and args else _ST
                _render_hover(container, "Field help", text, kind="field")
        return original(*args, **kwargs)

    wrapper.__name__ = getattr(original, "__name__", widget_type)
    wrapper.__doc__ = getattr(original, "__doc__", None)
    setattr(wrapper, "_agrolattice_help_wrapper", True)
    return wrapper


def _wrap_action(original: Callable[..., Any], widget_type: str, *, method: bool) -> Callable[..., Any]:
    supports_help = _supports_parameter(original, "help")

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        offset = 1 if method else 0
        label = args[offset] if len(args) > offset else kwargs.get("label", "")
        clean = _clean_label(label).casefold()
        important = any(word in clean for word in ("run", "create", "install", "delete", "reset", "clear", "download", "save", "import", "export", "finalise", "process", "fetch"))
        if important:
            text = explain_control(label, widget_type)
            if text and not kwargs.get("help"):
                if supports_help:
                    kwargs["help"] = text
                else:
                    container = args[0] if method and args else _ST
                    _render_hover(container, "Action help", text, kind="field")
        return original(*args, **kwargs)

    wrapper.__name__ = getattr(original, "__name__", widget_type)
    setattr(wrapper, "_agrolattice_help_wrapper", True)
    return wrapper


def _plotly_metadata(figure: Any) -> tuple[str, str, str, list[str]]:
    title = ""
    x_title = ""
    y_title = ""
    trace_types: list[str] = []
    try:
        title = str(getattr(getattr(figure, "layout", None), "title", None).text or "")
    except Exception:
        pass
    try:
        x_title = str(getattr(getattr(figure.layout, "xaxis", None), "title", None).text or "")
    except Exception:
        pass
    try:
        y_title = str(getattr(getattr(figure.layout, "yaxis", None), "title", None).text or "")
    except Exception:
        pass
    try:
        trace_types = [str(getattr(trace, "type", "")).casefold() for trace in figure.data]
    except Exception:
        pass
    return title, x_title, y_title, trace_types


def explain_chart(chart_obj: Any, chart_kind: str) -> str:
    title = ""
    x_title = ""
    y_title = ""
    trace_types: list[str] = []
    if chart_kind == "plotly_chart":
        title, x_title, y_title, trace_types = _plotly_metadata(chart_obj)
    elif chart_kind == "pyplot":
        try:
            axes = chart_obj.axes
            if axes:
                title = axes[0].get_title() or ""
                x_title = axes[0].get_xlabel() or ""
                y_title = axes[0].get_ylabel() or ""
        except Exception:
            pass
    combined = " ".join([title, x_title, y_title, " ".join(trace_types)]).casefold()
    if "pca" in combined or "principal component" in combined:
        base = "Each point is a location or observation projected onto principal-component axes. Nearby points have similar multivariable profiles. Axis percentages, when shown, are the variance explained; PCA axes are combinations of original variables rather than direct agricultural measurements."
    elif "cluster" in combined or "kmeans" in combined:
        base = "Colours or symbols identify model-assigned clusters. Compare separation, overlap and cluster size; clusters describe similarity in the selected features and are not automatically agronomic zones."
    elif "observed" in combined and "predicted" in combined:
        base = "Each point compares an observed value with a model prediction. Points close to the 1:1 line indicate agreement; systematic offsets, curvature or widening spread suggest bias or changing error variance."
    elif "residual" in combined:
        base = "Residuals are observed minus predicted values. A random cloud around zero is desirable; patterns, funnels or extreme points can indicate bias, heteroscedasticity or influential observations."
    elif "ndvi" in combined or "evi" in combined or "ndmi" in combined or "ndre" in combined:
        base = "The chart shows satellite-index change through time or space. Interpret values relative to crop stage, cloud masking and field conditions; an index change is a screening signal, not a diagnosis by itself."
    elif "gdd" in combined or "phenolog" in combined or "flower" in combined or "silk" in combined or "pollen" in combined:
        base = "The chart shows crop-development timing, thermal accumulation or male-female flowering progress. Look for the timing and duration of pollen-shed and silk-receptivity overlap, not only a single date."
    elif "soil" in combined or "depletion" in combined or "taw" in combined or "raw" in combined or "irrig" in combined:
        base = "The chart shows root-zone water, depletion, stress or irrigation over time. Compare depletion with RAW/TAW thresholds and interpret results using the selected soil, root-depth and efficiency assumptions."
    elif "yield" in combined or "seed set" in combined or "econom" in combined:
        base = "The chart compares crop or economic outcomes across treatments, scenarios or years. Check units, uncertainty and whether differences are observed, simulated or predicted."
    elif any(t in trace_types for t in ("scatter", "scattergl")) or chart_kind == "scatter_chart":
        base = "Each point is an observation. Read its horizontal and vertical values from the axes, then inspect trend, spread, groups and unusual points. Association does not by itself prove causation."
    elif any(t in trace_types for t in ("bar", "histogram")) or chart_kind == "bar_chart":
        base = "Compare bar lengths or heights using the displayed units. Check whether values are totals, means, percentages or counts before interpreting differences."
    elif any(t in trace_types for t in ("box", "violin")):
        base = "The centre line usually represents the median, the box the middle 50% of observations, and points beyond whiskers possible outliers. Compare both centre and spread."
    elif any(t in trace_types for t in ("heatmap", "contour")):
        base = "Colour represents the value shown in the legend. Use the scale, units and missing-data pattern before comparing cells or areas."
    else:
        base = "Use the axis labels, units, legend and caption to identify what is being compared. Look for trends, differences, uncertainty and missing data before drawing a conclusion."
    if title:
        base = f"Chart: {title}. {base}"
    axes = []
    if x_title:
        axes.append(f"X-axis: {x_title}")
    if y_title:
        axes.append(f"Y-axis: {y_title}")
    if axes:
        base += " " + "; ".join(axes) + "."
    notes = _term_notes(combined, limit=3)
    if notes:
        base += " " + " ".join(notes)
    return base[:2600]


def explain_table(data: Any, *, editable: bool = False) -> str:
    rows = None
    columns: list[str] = []
    try:
        rows = len(data)
    except Exception:
        pass
    try:
        columns = [str(item) for item in list(data.columns)[:10]]
    except Exception:
        pass
    if editable:
        base = "This is an editable table. Enter or paste values without changing column meanings or units, then use the page's save or import action. Empty required cells may prevent processing."
    else:
        base = "This table contains the detailed records behind the summary. Sort or inspect columns, check units and missing values, and use the page download when a reproducible copy is needed."
    if rows is not None:
        base += f" Rows currently displayed: {rows}."
    if columns:
        base += " Key columns: " + ", ".join(columns) + "."
    notes = _term_notes(" ".join(columns), limit=3)
    if notes:
        base += " " + " ".join(notes)
    return base[:2400]


def _wrap_output(original: Callable[..., Any], output_type: str, *, method: bool) -> Callable[..., Any]:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        offset = 1 if method else 0
        if len(args) > offset:
            obj = args[offset]
        elif "figure_or_data" in kwargs:
            obj = kwargs.get("figure_or_data")
        else:
            obj = kwargs.get("data")
        container = args[0] if method and args else _ST
        mode = _mode()
        if mode != "Off":
            if output_type in {"plotly_chart", "altair_chart", "pyplot", "line_chart", "bar_chart", "area_chart", "scatter_chart"}:
                _render_hover(container, "Chart guide", explain_chart(obj, output_type), kind="chart")
            elif output_type == "map":
                _render_hover(container, "Map guide", "Use the layer control to switch Roads, Satellite or Light map. Pan and zoom to inspect context. Markers, colours and polygons represent the active fields, plots or results; use the map legend and page caption for their meaning.", kind="map")
            elif output_type == "dataframe" and mode == "Detailed":
                _render_hover(container, "Table guide", explain_table(obj), kind="table")
            elif output_type == "data_editor":
                _render_hover(container, "Editable table guide", explain_table(obj, editable=True), kind="table")
            elif output_type == "metric":
                # st.metric supports native help in current Streamlit. Inject there when possible.
                label = args[offset] if len(args) > offset else kwargs.get("label", "Metric")
                text = explain_control(label, "metric") or f"Summary value for {_clean_label(label)}. Check the unit and active context."
                if not kwargs.get("help"):
                    if _supports_parameter(original, "help"):
                        kwargs["help"] = text
                    else:
                        _render_hover(container, "Metric guide", text, kind="chart")
        return original(*args, **kwargs)

    wrapper.__name__ = getattr(original, "__name__", output_type)
    setattr(wrapper, "_agrolattice_help_wrapper", True)
    return wrapper


def _wrap_tabs(original: Callable[..., Any], *, method: bool) -> Callable[..., Any]:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        offset = 1 if method else 0
        labels = args[offset] if len(args) > offset else kwargs.get("tabs", kwargs.get("labels", []))
        container = args[0] if method and args else _ST
        if _mode() != "Off" and isinstance(labels, Sequence) and not isinstance(labels, (str, bytes)):
            descriptions = [explain_tab(item) for item in labels]
            tooltip = " | ".join(descriptions)
            _render_hover(container, "Tab guide", tooltip, kind="tabs")
        return original(*args, **kwargs)

    wrapper.__name__ = getattr(original, "__name__", "tabs")
    setattr(wrapper, "_agrolattice_help_wrapper", True)
    return wrapper


def _patch_attribute(target: Any, target_name: str, attribute: str, wrapper_factory: Callable[[Any], Any]) -> None:
    try:
        original = getattr(target, attribute)
    except Exception:
        return
    if getattr(original, "_agrolattice_help_wrapper", False):
        return
    _ORIGINALS[(target_name, attribute)] = original
    try:
        setattr(target, attribute, wrapper_factory(original))
    except Exception:
        pass


def install_contextual_help(st_module: Any) -> None:
    """Install help wrappers once per Python process."""
    global _ST, _PATCHED
    _ST = st_module
    # Streamlit rebuilds the document on every rerun, so emit the small CSS block
    # every time even though function monkey-patching is process-global.
    _inject_css(st_module)
    if _PATCHED or getattr(st_module, "_agrolattice_context_help_installed", False):
        return

    for name in INPUT_WIDGETS:
        _patch_attribute(st_module, "streamlit", name, lambda original, n=name: _wrap_input(original, n, method=False))
    for name in ACTION_WIDGETS:
        _patch_attribute(st_module, "streamlit", name, lambda original, n=name: _wrap_action(original, n, method=False))
    for name in OUTPUT_WIDGETS:
        _patch_attribute(st_module, "streamlit", name, lambda original, n=name: _wrap_output(original, n, method=False))
    _patch_attribute(st_module, "streamlit", "tabs", lambda original: _wrap_tabs(original, method=False))

    try:
        from streamlit.delta_generator import DeltaGenerator
    except Exception:
        DeltaGenerator = None
    if DeltaGenerator is not None:
        for name in INPUT_WIDGETS:
            _patch_attribute(DeltaGenerator, "DeltaGenerator", name, lambda original, n=name: _wrap_input(original, n, method=True))
        for name in ACTION_WIDGETS:
            _patch_attribute(DeltaGenerator, "DeltaGenerator", name, lambda original, n=name: _wrap_action(original, n, method=True))
        for name in OUTPUT_WIDGETS:
            _patch_attribute(DeltaGenerator, "DeltaGenerator", name, lambda original, n=name: _wrap_output(original, n, method=True))
        _patch_attribute(DeltaGenerator, "DeltaGenerator", "tabs", lambda original: _wrap_tabs(original, method=True))

    try:
        setattr(st_module, "_agrolattice_context_help_installed", True)
    except Exception:
        pass
    _PATCHED = True


def wrap_st_folium(original: Callable[..., Any], st_module: Any | None = None) -> Callable[..., Any]:
    """Wrap a ``st_folium`` alias with a compact map hover guide."""
    if getattr(original, "_agrolattice_help_wrapper", False):
        return original
    local_st = st_module or _ST

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if _mode() != "Off" and local_st is not None:
            tooltip = (
                "Use the layer control to switch between Roads & places, Satellite imagery and Light map where available. "
                "Use the search box to locate a place, the ruler to measure distance or area, and drawing tools to create or edit field and plot boundaries. "
                "Verify that the geometry is inside the correct country and field before saving or sending it to satellite processing."
            )
            _render_hover(local_st, "Interactive map guide", tooltip, kind="map")
        return original(*args, **kwargs)

    wrapper.__name__ = getattr(original, "__name__", "st_folium")
    setattr(wrapper, "_agrolattice_help_wrapper", True)
    return wrapper


def patch_loaded_map_aliases(st_module: Any | None = None) -> None:
    """Patch st_folium aliases imported by AgroLattice feature modules."""
    for module_name in ("maize_pollination_lab", "field_operations_suite", "agrolattice_twin"):
        module = sys.modules.get(module_name)
        if module is None:
            continue
        alias = getattr(module, "st_folium", None)
        if callable(alias) and not getattr(alias, "_agrolattice_help_wrapper", False):
            try:
                setattr(module, "st_folium", wrap_st_folium(alias, st_module or _ST))
            except Exception:
                pass


def render_help_settings(st_module: Any) -> None:
    """Render compact sidebar controls for contextual-help density."""
    options = ["Detailed", "Essential", "Off"]
    current = str(st_module.session_state.get("agrolattice_help_mode", "Detailed"))
    if current not in options:
        current = "Detailed"
    selected = st_module.selectbox(
        "Contextual help",
        options,
        index=options.index(current),
        key="agrolattice_help_mode",
        help=(
            "Detailed adds hover explanations to most fields, charts, maps, tabs and tables. "
            "Essential limits field explanations to recognised scientific or workflow settings. "
            "Off hides automatically added help while preserving help written directly into a page."
        ),
    )
    if selected != "Off":
        _render_hover(
            st_module,
            "Hover help is active",
            "Move the pointer over a small ? icon beside a field, chart, map, tab guide or table guide. No click is required.",
            kind="tabs",
        )


def render_contextual_help_guide(st_module: Any) -> None:
    """Render the user-facing guide shown in the Help workspace."""
    st_module.markdown("### Contextual ? help")
    st_module.write(
        "Contextual hover help is maintained in AGROLATTICE 11.19 alongside the current spatial, Twin and experimental-data safeguards. Move the pointer over a small **?** icon to see what a field, selection, tab, chart, map or table means."
    )
    columns = st_module.columns(3)
    columns[0].markdown("**Detailed**")
    columns[0].caption("Explains nearly every input plus charts, maps, tabs and tables. Best for new users.")
    columns[1].markdown("**Essential**")
    columns[1].caption("Explains recognised scientific, agricultural and workflow controls plus all visual outputs.")
    columns[2].markdown("**Off**")
    columns[2].caption("Hides automatically generated help. Page-specific help written by the developer remains available.")
    st_module.info(
        "A tooltip explains how to use or interpret a control; it does not replace the scientific protocol. Local crop parameters, laboratory definitions and experimental decisions should still be documented."
    )
    st_module.markdown("#### What the different guides explain")
    st_module.markdown(
        "- **Field help:** expected input, units, effect on the analysis and a practical example.\n"
        "- **Tab guide:** purpose of each view in the current workspace.\n"
        "- **Chart guide:** axes, marks and interpretation cautions, including domain-specific notes for PCA, clusters, flowering, water and satellite indices.\n"
        "- **Map guide:** base layers, search, measuring and boundary-drawing tools.\n"
        "- **Table guide:** whether the table is editable, how to inspect it and why units and missing values matter."
    )
    st_module.markdown("#### Example")
    st_module.code(
        "GDD base temperature (°C)\n"
        "Lower developmental threshold. Temperatures below this value contribute no thermal time.\n"
        "Example: 10 °C",
        language="text",
    )
    st_module.caption(f"Contextual help engine version {MODULE_VERSION}")


def coverage_summary() -> dict[str, Any]:
    return {
        "module_version": MODULE_VERSION,
        "exact_control_definitions": len(EXACT_CONTROL),
        "pattern_rules": len(PATTERN_RULES),
        "term_definitions": len(TERM_DEFINITIONS),
        "input_widget_types": len(INPUT_WIDGETS),
        "output_widget_types": len(OUTPUT_WIDGETS),
        "map_alias_modules": 3,
    }
