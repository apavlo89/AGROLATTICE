# Validated agronomic parameter library for the Mexico Agroclimate Research Tool
**Review date:** 24 July 2026
## Executive conclusion
The crop module should be rebuilt around two separate layers: (1) broad ecological screening from crop-specific temperature and rainfall envelopes, and (2) water adequacy and yield response from the FAO crop-coefficient framework. The present app's fixed stage precipitation totals and fixed water-deficit values in millimetres should not be treated as validated biological thresholds.
The recommended equations are:
```text
ETc = Kc × ETo
1 − Ya/Ym = Ky × (1 − ETa/ETm)
```
Planting periods should be selected from Mexican state-, crop-, agricultural-cycle- and water-regime data rather than one national month sequence. The SIAP agricultural calendar is the appropriate official starting point.
## Implementation-ready crop defaults
| Crop/profile | Temperature absolute–optimal–absolute (°C) | Rainfall envelope (mm) | Crop water need | Evidence | Status |
|---|---:|---:|---:|---|---|
| Maize — Grain maize – broad screening | 10 / 18–33 / 47 | 400 / 600–1200 / 1800 | 500–800 mm (Medium-maturity crop cycle) | A/B | Ready |
| Coffee — Productive Arabica – unshaded screening | 10 / 14–28 / 34 | 750 / 1400–2300 / 4200 | Not established | B | Ready with canopy/age warning |
| Wheat — Bread wheat – Mexico screening | 5 / 15–23 / 27 | 300 / 750–900 / 1600 | 450–650 mm (Crop cycle) | A | Ready |
| Beans — Dry common bean | 7 / 16–25 / 32 | 300 / 500–2000 / 4300 | 300–500 mm (60–120 day crop) | A/B | Ready |
| Sorghum — Grain sorghum | 8 / 22–35 / 40 | 300 / 400–600 / 700 | 450–650 mm (110–130 day crop) | A/B | Ready |
| Avocado — Hass-like Mexican × Guatemalan composite | 10 / 14–24 / 30 | 660 / 1000–1400 / 1800 | 713–1028 mm (Seasonal orchard ET observed at California Hass sites) | B | Ready as labelled composite |
| Avocado — Mexican race | 10 / 14–22 / 28 | 660 / 1000–1400 / 1800 | Not established | B | Ready |
| Avocado — Guatemalan race | 12 / 15–24 / 30 | 660 / 1000–1400 / 1800 | Not established | B | Ready |
| Avocado — West Indian race | 12 / 15–26 / 34 | 660 / 1000–1400 / 1800 | Not established | B | Ready |
| Agave — Blue agave – Mexico observational screening | NA / 23–25 / NA | 500 / 600–1000 / 1200 | Not established | B/C | Do not use four-point temperature trapezoid |
| Tomato — Field tomato | 7 / 18–25 / 35 | 400 / 600–1300 / 1800 | 400–600 mm (90–120 days after transplanting) | A/B | Ready |
| Sugarcane — Commercial sugarcane | 15 / 22–30 / 41 | 1000 / 1500–2000 / 5000 | 1500–2500 mm (Growing season) | A/B | Ready |
| Barley — Grain barley | 2 / 15–20 / 40 | 200 / 500–1000 / 2000 | 450–650 mm (Crop cycle; FAO groups barley/oats/wheat) | B/C | Ready with proxy warning |
| Citrus — Mature sweet orange orchard | 13 / 20–30 / 38 | 450 / 1200–2000 / 2700 | 900–1200 mm (Year) | A/B | Ready |

## Critical changes to the current application
- **CROP_SEASONAL_WINDOWS fixed national months — Replace:** Require planting date or state/cycle/irrigation-mode calendar; derive stages from day lengths Rationale: Mexico has spring–summer and autumn–winter cycles, irrigated and rainfed systems. One national month sequence is not defensible.
- **Stage-specific precipitation trapezoids — Replace:** Use broad rainfall envelope only for ecological screening; use ETc = Kc × ETo for water adequacy Rationale: Rainfall totals are not equivalent to crop water supply and should not be universal stage thresholds.
- **water_deficit_abs / water_deficit_opt fixed mm values — Remove:** Use actual/maximum ET ratio and Ky: 1 − Ya/Ym = Ky(1 − ETa/ETm) Rationale: A fixed deficit in mm has different biological meaning across climate, crop duration, soil and stage.
- **Single crop-wide Kc in irrigation estimator — Replace:** Use stage-specific Kc curve; adjust Kc ini for wetting frequency and local climate Rationale: Kc changes across development and with canopy/ground cover.
- **Generic avocado profile — Replace:** Offer Hass-like composite plus Mexican, Guatemalan and West Indian race profiles Rationale: Avocado races have materially different temperature envelopes.
- **Agave four-point trapezoid and Kc — Disable by default:** Display observed cultivated-site climate ranges; no precise irrigation score until local Kc/calibration exists Rationale: Available evidence supports observational zoning, not universal physiological limits or Kc.
- **Coffee fixed Kc — Replace:** Expose age/canopy/shade/pruning selector; default productive full-sun Kc ≈0.95 with warning Rationale: Published Kc spans roughly 0.44–1.50 depending on system.
- **Perennial crop 'full growing season' precipitation sums — Replace:** Use annual climate envelope and annual/monthly orchard Kc Rationale: Perennials transpire year-round and do not follow one annual crop cycle.
- **Maize/coffee fixed potential yield ceilings — Disable as scientific default:** Require user value or fit against observed yield data; label any fallback as illustrative Rationale: Potential yield is cultivar-, environment- and management-specific.
- **Reliability score weights — Retain with relabelling:** Label as application-defined index and expose weights/sensitivity Rationale: Validated crop inputs do not validate a custom composite score.
- **Portfolio/substitution scores — Retain with relabelling:** Label as exploratory application-defined rankings; show component values Rationale: Do not imply agronomic or economic recommendation.
- **Suitability class cut-offs 20/40/60/80 — Retain only as UI categories:** Label as conventional app categories, not published crop standards Rationale: Scores are continuous model outputs; categorical labels are convenience thresholds.
- **Temperature thresholds copied identically to every stage — Use cautiously:** Apply broad crop envelope by default; use stage-specific temperature rules only where directly supported Rationale: Stage-specific thresholds are often cultivar- and context-dependent.
- **Source provenance absent from UI — Add:** Display source title, URL, evidence grade, parameter basis and last review date beside defaults Rationale: Allows peer review, audit and future updating.
- **No distinction between ecological rainfall and crop water use — Add explicit distinction:** Store `rainfall_envelope_mm` separately from `crop_water_requirement_mm` Rationale: These quantities answer different questions and must not share the same field.

## Evidence limitations
- **Agave tequilana (High priority):** Universal Kc, Ky, absolute temperature limits and stage-specific ET demand. Do not generate irrigation/yield-loss defaults. Obtain INIFAP or field-calibrated parameters for target denomination-of-origin zones.
- **Coffee (Medium priority):** Universal stage-specific Kc and water-deficit threshold. Use age/canopy/shade-specific options; validate in Mexican coffee regions.
- **Avocado (Medium priority):** Mexico-specific Hass Kc and crop-water requirement across production regions. Use 0.55–0.85 as a research prior; calibrate with Mexican orchard ET or irrigation records.
- **Barley (Medium priority):** Barley-specific Kc/Ky in the reviewed official sources. Use transparent small-grain proxy and flag it in the interface.
- **All annual crops (High priority):** National fixed planting months. Import SIAP calendars by state, cycle and irrigation regime; permit local user overrides.
- **All crops (High priority):** Cultivar-specific heat thresholds and phenology. Add optional cultivar profiles and growing-degree-day phenology when reliable sources are available.
- **All crops (High priority):** Soil-water storage, rooting depth, runoff and effective rainfall. Add a soil-water balance layer before calling irrigation estimates operational.
- **Yield module (High priority):** Validated potential yield and response calibration. Train/calibrate against SIAP or experimental observed yields; remove universal ceilings.

## Source register
- **FAO_MAIZE — FAO Crop Water Information: Maize**. https://www.fao.org/land-water/databases-and-software/crop-information/maize/ar/
- **FAO_BEAN — FAO Crop Water Information: Bean**. https://www.fao.org/land-water/databases-and-software/crop-information/bean/en/
- **FAO_SORGHUM — FAO Crop Water Information: Sorghum**. https://www.fao.org/land-water/databases-and-software/crop-information/sorghum/es/
- **FAO_WHEAT — FAO Crop Water Information: Wheat**. https://www.fao.org/land-water/databases-and-software/crop-information/wheat/zh/
- **FAO_TOMATO — FAO Crop Water Information: Tomato**. https://www.fao.org/land-water/databases-and-software/crop-information/tomato/ar/
- **FAO_SUGARCANE — FAO Crop Water Information: Sugarcane**. https://www.fao.org/land-water/databases-and-software/crop-information/sugarcane/en/
- **FAO_CITRUS — FAO Crop Water Information: Citrus**. https://www.fao.org/land-water/databases-and-software/crop-information/citrus/en/
- **FAO56 — Allen et al. FAO Irrigation and Drainage Paper 56**. https://www.fao.org/4/x0490e/x0490e0b.htm
- **FAO_KY — Steduto et al. Crop yield response to water, FAO Irrigation and Drainage Paper 66**. https://www.fao.org/4/i2800e/i2800e.pdf
- **ECO_MAIZE — FAO Ecocrop: Zea mays ssp. mays**. https://ecocrop.apps.fao.org/ecocrop/srv/en/dataSheet?id=238663
- **ECO_BEAN — FAO Ecocrop: Phaseolus vulgaris**. https://ecocrop.apps.fao.org/ecocrop/srv/en/dataSheet?id=1668
- **ECO_SORGHUM — FAO Ecocrop: Sorghum bicolor**. https://ecocrop.apps.fao.org/ecocrop/srv/en/dataSheet?id=48747
- **INIFAP_WHEAT — INIFAP agroclimatic wheat requirements table using Ecocrop**. https://cienciasagricolas.inifap.gob.mx/index.php/agricolas/es/article/download/1391/1482/4911?inline=1
- **ECO_BARLEY — FAO Ecocrop: Hordeum vulgare**. https://ecocrop.apps.fao.org/ecocrop/srv/en/dataSheet?id=1232
- **ECO_TOMATO — FAO Ecocrop: Lycopersicon esculentum / Solanum lycopersicum**. https://ecocrop.apps.fao.org/ecocrop/srv/en/dataSheet?id=1379
- **ECO_SUGARCANE — FAO Ecocrop: Saccharum officinarum**. https://ecocrop.apps.fao.org/ecocrop/srv/en/dataSheet?id=1884
- **ECO_COFFEE — FAO Ecocrop: Coffea arabica**. https://ecocrop.apps.fao.org/ecocrop/srv/en/dataSheet?id=749
- **COFFEE_COLOMBIA_KC — Castaño-Marín et al. Evapotranspiration and crop coefficients for coffee production systems in Colombia**. https://acsess.onlinelibrary.wiley.com/doi/10.1002/agj2.20960
- **COFFEE_BRAZIL_KC — Oliveira et al. Coffee evapotranspiration and crop coefficient**. https://revistas.fca.unesp.br/index.php/irriga/article/view/3142
- **ECO_AVOCADO_MEX — FAO Ecocrop: Mexican avocado race**. https://ecocrop.apps.fao.org/ecocrop/srv/en/dataSheet?id=17644
- **ECO_AVOCADO_GUA — FAO Ecocrop: Guatemalan avocado race**. https://ecocrop.apps.fao.org/ecocrop/srv/en/dataSheet?id=17645
- **ECO_AVOCADO_WI — FAO Ecocrop: West Indian avocado race**. https://ecocrop.apps.fao.org/ecocrop/srv/en/dataSheet?id=17646
- **AVOCADO_KC_2025 — California Hass avocado ET and crop coefficients**. https://www.sciencedirect.com/science/article/pii/S0378377425001957
- **UCR_AVOCADO_KC — University of California avocado monthly crop coefficients**. https://avocado.ucr.edu/crop-coefficients-avocados
- **INIFAP_AGAVE — Agroclimatic characterization of Agave tequilana in the Santiago River ravine**. https://www.scielo.org.mx/scielo.php?pid=S2007-09342023000300375&script=sci_arttext&tlng=en
- **ECO_CITRUS_ORANGE — FAO Ecocrop: Citrus sinensis**. https://ecocrop.apps.fao.org/ecocrop/srv/en/dataSheet?id=720
- **SIAP_CALENDAR — Mexican agricultural calendar**. https://nube.agricultura.gob.mx/calendario_agricola/
