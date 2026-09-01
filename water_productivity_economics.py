
"""Water productivity and economic scenario analysis for AgroLattice."""
from __future__ import annotations

import io
import json
import math
import zipfile
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

MODULE_VERSION = "1.0.0"


class EconomicsAnalysisError(RuntimeError):
    """Raised when an economic or water-productivity analysis is invalid."""


def _safe_divide(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if np.isfinite(denominator) and abs(denominator) > 1e-12 else float("nan")


def calculate_scenario(
    *,
    scenario_name: str,
    yield_t_ha: float,
    crop_price_per_t: float,
    area_ha: float,
    seasonal_etc_mm: float,
    irrigation_mm: float,
    effective_rainfall_mm: float = 0.0,
    non_water_variable_cost_per_ha: float = 0.0,
    fixed_cost_per_ha: float = 0.0,
    water_price_per_m3: float = 0.0,
    pumping_energy_kwh_per_m3: float = 0.0,
    electricity_price_per_kwh: float = 0.0,
    irrigation_labour_cost_per_ha: float = 0.0,
    other_irrigation_cost_per_ha: float = 0.0,
) -> dict[str, float | str]:
    values = {
        "yield_t_ha": yield_t_ha,
        "crop_price_per_t": crop_price_per_t,
        "area_ha": area_ha,
        "seasonal_etc_mm": seasonal_etc_mm,
        "irrigation_mm": irrigation_mm,
    }
    if any(not np.isfinite(float(value)) for value in values.values()):
        raise EconomicsAnalysisError("Yield, price, area, ETc and irrigation must be finite numbers.")
    if area_ha <= 0 or yield_t_ha < 0 or seasonal_etc_mm < 0 or irrigation_mm < 0:
        raise EconomicsAnalysisError("Area must be positive and biophysical quantities cannot be negative.")

    irrigation_m3_ha = irrigation_mm * 10.0
    irrigation_m3_total = irrigation_m3_ha * area_ha
    yield_total_t = yield_t_ha * area_ha
    gross_revenue_ha = yield_t_ha * crop_price_per_t
    water_purchase_cost_ha = irrigation_m3_ha * water_price_per_m3
    pumping_energy_kwh_ha = irrigation_m3_ha * pumping_energy_kwh_per_m3
    pumping_energy_cost_ha = pumping_energy_kwh_ha * electricity_price_per_kwh
    irrigation_cost_ha = (
        water_purchase_cost_ha
        + pumping_energy_cost_ha
        + irrigation_labour_cost_per_ha
        + other_irrigation_cost_per_ha
    )
    total_cost_ha = non_water_variable_cost_per_ha + fixed_cost_per_ha + irrigation_cost_ha
    gross_margin_ha = gross_revenue_ha - total_cost_ha
    break_even_yield = _safe_divide(total_cost_ha, crop_price_per_t)
    break_even_price = _safe_divide(total_cost_ha, yield_t_ha)
    crop_water_productivity = _safe_divide(yield_t_ha * 1000.0, seasonal_etc_mm * 10.0)
    irrigation_water_productivity = _safe_divide(yield_t_ha * 1000.0, irrigation_m3_ha)
    economic_water_productivity = _safe_divide(gross_margin_ha, irrigation_m3_ha)
    rainfall_share = _safe_divide(effective_rainfall_mm, max(seasonal_etc_mm, 1e-12)) * 100

    return {
        "Scenario": str(scenario_name),
        "Area (ha)": float(area_ha),
        "Yield (t/ha)": float(yield_t_ha),
        "Total production (t)": float(yield_total_t),
        "Crop price (currency/t)": float(crop_price_per_t),
        "Gross revenue (currency/ha)": float(gross_revenue_ha),
        "Non-water variable cost (currency/ha)": float(non_water_variable_cost_per_ha),
        "Fixed cost (currency/ha)": float(fixed_cost_per_ha),
        "Water purchase cost (currency/ha)": float(water_purchase_cost_ha),
        "Pumping energy (kWh/ha)": float(pumping_energy_kwh_ha),
        "Pumping energy cost (currency/ha)": float(pumping_energy_cost_ha),
        "Irrigation labour and other cost (currency/ha)": float(irrigation_labour_cost_per_ha + other_irrigation_cost_per_ha),
        "Total irrigation cost (currency/ha)": float(irrigation_cost_ha),
        "Total cost (currency/ha)": float(total_cost_ha),
        "Gross margin (currency/ha)": float(gross_margin_ha),
        "Gross margin total (currency)": float(gross_margin_ha * area_ha),
        "Break-even yield (t/ha)": float(break_even_yield),
        "Break-even crop price (currency/t)": float(break_even_price),
        "Seasonal ETc (mm)": float(seasonal_etc_mm),
        "Effective rainfall (mm)": float(effective_rainfall_mm),
        "Irrigation (mm)": float(irrigation_mm),
        "Irrigation (m³/ha)": float(irrigation_m3_ha),
        "Total irrigation (m³)": float(irrigation_m3_total),
        "Crop water productivity (kg/m³ ETc)": float(crop_water_productivity),
        "Irrigation water productivity (kg/m³ irrigation)": float(irrigation_water_productivity),
        "Economic irrigation-water productivity (currency/m³)": float(economic_water_productivity),
        "Effective rainfall share of ETc (%)": float(rainfall_share),
        "Profitable": bool(gross_margin_ha >= 0),
    }


def compare_scenarios(rows: Sequence[Mapping[str, Any]], baseline_name: str | None = None) -> pd.DataFrame:
    frame = pd.DataFrame(list(rows))
    if frame.empty:
        return frame
    baseline = baseline_name if baseline_name in frame["Scenario"].astype(str).tolist() else str(frame.iloc[0]["Scenario"])
    baseline_row = frame.loc[frame["Scenario"].astype(str).eq(baseline)].iloc[0]
    for metric in [
        "Yield (t/ha)",
        "Irrigation (mm)",
        "Gross margin (currency/ha)",
        "Crop water productivity (kg/m³ ETc)",
        "Irrigation water productivity (kg/m³ irrigation)",
    ]:
        frame[f"Δ {metric} vs baseline"] = pd.to_numeric(frame[metric], errors="coerce") - float(baseline_row[metric])
    frame["Baseline scenario"] = baseline
    return frame


def monte_carlo_economics(
    *,
    base_inputs: Mapping[str, Any],
    iterations: int = 5000,
    seed: int = 42,
    yield_cv_percent: float = 15.0,
    price_cv_percent: float = 10.0,
    cost_cv_percent: float = 10.0,
    irrigation_cv_percent: float = 10.0,
) -> tuple[pd.DataFrame, dict[str, float]]:
    rng = np.random.default_rng(seed)
    n = max(500, int(iterations))
    def lognormal_samples(mean: float, cv_percent: float, nonnegative: bool = True) -> np.ndarray:
        mean = float(mean)
        cv = max(0.0, float(cv_percent) / 100.0)
        if cv == 0 or mean == 0:
            return np.full(n, max(0.0, mean) if nonnegative else mean)
        sigma2 = math.log(1 + cv ** 2)
        mu = math.log(max(mean, 1e-9)) - sigma2 / 2
        values = rng.lognormal(mu, math.sqrt(sigma2), size=n)
        return values if nonnegative else values

    yield_samples = lognormal_samples(float(base_inputs["yield_t_ha"]), yield_cv_percent)
    price_samples = lognormal_samples(float(base_inputs["crop_price_per_t"]), price_cv_percent)
    irrigation_samples = lognormal_samples(float(base_inputs["irrigation_mm"]), irrigation_cv_percent)
    variable_cost_samples = lognormal_samples(float(base_inputs.get("non_water_variable_cost_per_ha", 0)), cost_cv_percent)
    fixed_cost_samples = lognormal_samples(float(base_inputs.get("fixed_cost_per_ha", 0)), cost_cv_percent)

    records = []
    for index in range(n):
        scenario = calculate_scenario(
            scenario_name="Monte Carlo",
            yield_t_ha=float(yield_samples[index]),
            crop_price_per_t=float(price_samples[index]),
            area_ha=float(base_inputs["area_ha"]),
            seasonal_etc_mm=float(base_inputs["seasonal_etc_mm"]),
            irrigation_mm=float(irrigation_samples[index]),
            effective_rainfall_mm=float(base_inputs.get("effective_rainfall_mm", 0)),
            non_water_variable_cost_per_ha=float(variable_cost_samples[index]),
            fixed_cost_per_ha=float(fixed_cost_samples[index]),
            water_price_per_m3=float(base_inputs.get("water_price_per_m3", 0)),
            pumping_energy_kwh_per_m3=float(base_inputs.get("pumping_energy_kwh_per_m3", 0)),
            electricity_price_per_kwh=float(base_inputs.get("electricity_price_per_kwh", 0)),
            irrigation_labour_cost_per_ha=float(base_inputs.get("irrigation_labour_cost_per_ha", 0)),
            other_irrigation_cost_per_ha=float(base_inputs.get("other_irrigation_cost_per_ha", 0)),
        )
        records.append({
            "Iteration": index + 1,
            "Yield (t/ha)": scenario["Yield (t/ha)"],
            "Crop price (currency/t)": scenario["Crop price (currency/t)"],
            "Irrigation (mm)": scenario["Irrigation (mm)"],
            "Gross margin (currency/ha)": scenario["Gross margin (currency/ha)"],
            "Irrigation water productivity (kg/m³ irrigation)": scenario["Irrigation water productivity (kg/m³ irrigation)"],
        })
    frame = pd.DataFrame(records)
    margin = frame["Gross margin (currency/ha)"]
    summary = {
        "Iterations": int(n),
        "Probability of profit (%)": float((margin >= 0).mean() * 100),
        "Expected gross margin (currency/ha)": float(margin.mean()),
        "Median gross margin (currency/ha)": float(margin.median()),
        "Gross margin P05": float(margin.quantile(0.05)),
        "Gross margin P95": float(margin.quantile(0.95)),
        "Value at risk P05 (loss magnitude)": float(max(0.0, -margin.quantile(0.05))),
    }
    return frame, summary


def economics_export_package(
    *,
    assumptions: Mapping[str, Any],
    scenarios: pd.DataFrame,
    monte_carlo_results: pd.DataFrame | None = None,
    monte_carlo_summary: Mapping[str, Any] | None = None,
) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("economic_assumptions.json", json.dumps(dict(assumptions), indent=2, default=str))
        archive.writestr("water_productivity_economic_scenarios.csv", scenarios.to_csv(index=False))
        if monte_carlo_results is not None and not monte_carlo_results.empty:
            archive.writestr("monte_carlo_economic_results.csv", monte_carlo_results.to_csv(index=False))
        if monte_carlo_summary:
            archive.writestr("monte_carlo_summary.json", json.dumps(dict(monte_carlo_summary), indent=2, default=str))
        archive.writestr(
            "README.txt",
            "Economic results depend on user-supplied prices and costs. Currency units are intentionally generic unless the user specifies a currency.\n",
        )
    return buffer.getvalue()
