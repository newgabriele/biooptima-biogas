"""
formulas/economics.py - H2S gasvalorisatie, actieve kool, WKK-onderhoud en veldbenchmarks.
"""

from typing import Any, Dict
import numpy as np
from .core import PlantProfile, calculate_wobbe_index, FE_TO_S_RATIO, FE_PER_KG_PRODUCT

def calculate_h2s_valorisation_and_yield_gain(
    nominal_flow_m3_h: float = 500.0,
    raw_h2s_ppm: float = 2500.0,
    target_h2s_ppm: float = 100.0,
    base_ch4_pct: float = 53.5,
    biogas_price_per_m3: float = 0.68,
    fe_price_per_kg: float = 1.20,
    safety_margin: float = 1.25,
    diet_boost_enabled: bool = True,
    inst_type: str = "agro"
) -> Dict[str, Any]:
    base_daily_gas_m3 = float(nominal_flow_m3_h * 24.0)
    base_annual_gas_m3 = float(base_daily_gas_m3 * 365.0)
    
    default_diet_boost = 2.0 if inst_type == "agro" else (3.0 if inst_type == "covergisting" else 3.5)
    ammonia_stress_factor = 1.0 if inst_type == "agro" else (1.2 if inst_type == "covergisting" else 1.4)

    h2s_reduction_pct = max(0.0, (1.0 - (target_h2s_ppm / max(1.0, raw_h2s_ppm))) * 100.0)
    s_conv_factor = 1.33e-6
    s_raw_day_kg = base_daily_gas_m3 * raw_h2s_ppm * s_conv_factor
    s_target_day_kg = base_daily_gas_m3 * target_h2s_ppm * s_conv_factor
    s_removed_day_kg = max(0.0, s_raw_day_kg - s_target_day_kg)
    
    bag_weight_kg = 20.0
    fe_needed_day_kg = (s_removed_day_kg * FE_TO_S_RATIO * safety_margin * ammonia_stress_factor) / FE_PER_KG_PRODUCT
    fe_bags_day = int(np.ceil(fe_needed_day_kg / bag_weight_kg))
    fe_cost_day = fe_bags_day * bag_weight_kg * fe_price_per_kg
    fe_cost_yr = fe_cost_day * 365.0
    
    toxicity_relief_pct = min(5.0, max(0.5, (raw_h2s_ppm - target_h2s_ppm) / 1000.0 * 1.5))
    diet_gain_pct = default_diet_boost if diet_boost_enabled else 0.0
    total_yield_gain_pct = toxicity_relief_pct + diet_gain_pct
    
    extra_daily_gas_m3 = base_daily_gas_m3 * (total_yield_gain_pct / 100.0)
    extra_annual_gas_m3 = extra_daily_gas_m3 * 365.0
    new_daily_gas_m3 = base_daily_gas_m3 + extra_daily_gas_m3
    new_flow_m3_h = new_daily_gas_m3 / 24.0
    
    new_ch4_pct = min(68.0, base_ch4_pct + (1.2 if diet_boost_enabled else 0.3))
    new_kwh_per_m3 = (new_ch4_pct / 100.0) * 9.94
    new_annual_kwh = new_daily_gas_m3 * 365.0 * new_kwh_per_m3
    extra_revenue_volume_yr = extra_annual_gas_m3 * biogas_price_per_m3
    net_extra_cashflow_yr = extra_revenue_volume_yr - fe_cost_yr

    return {
        "base_flow_m3_h": round(nominal_flow_m3_h, 1),
        "new_flow_m3_h": round(new_flow_m3_h, 1),
        "base_daily_gas_m3": round(base_daily_gas_m3, 0),
        "new_daily_gas_m3": round(new_daily_gas_m3, 0),
        "extra_daily_gas_m3": round(extra_daily_gas_m3, 0),
        "extra_annual_gas_m3": round(extra_annual_gas_m3, 0),
        "h2s_reduction_pct": round(h2s_reduction_pct, 1),
        "s_removed_day_kg": round(s_removed_day_kg, 1),
        "total_yield_gain_pct": round(total_yield_gain_pct, 2),
        "new_ch4_pct": round(new_ch4_pct, 1),
        "fe_needed_day_kg": round(fe_needed_day_kg, 1),
        "fe_bags_day": fe_bags_day,
        "fe_cost_yr": round(fe_cost_yr, 2),
        "extra_revenue_volume_yr": round(extra_revenue_volume_yr, 2),
        "net_extra_cashflow_yr": round(net_extra_cashflow_yr, 2),
        "roi_pct": round((net_extra_cashflow_yr / fe_cost_yr * 100.0) if fe_cost_yr > 0 else 0.0, 1)
    }

def calculate_activated_carbon_benchmark(
    nominal_flow_m3_h: float = 500.0,
    raw_h2s_ppm: float = 2500.0,
    target_h2s_ppm: float = 100.0,
    carbon_bed_kg: float = 2000.0,
    carbon_type: str = "KI-Geïmpregneerd (12 wt% S)",
    carbon_price_per_ton: float = 3800.0,
    replacement_service_fee: float = 1200.0
) -> Dict[str, Any]:
    daily_gas_m3 = float(nominal_flow_m3_h * 24.0)
    s_conv = 1.33e-6
    s_cap = carbon_bed_kg * 0.12
    s_in_raw = daily_gas_m3 * raw_h2s_ppm * s_conv
    s_in_target = daily_gas_m3 * target_h2s_ppm * s_conv
    
    days_wo = max(0.1, s_cap / max(0.001, s_in_raw))
    days_w = max(0.1, s_cap / max(0.001, s_in_target))
    cost_per_change = (carbon_bed_kg / 1000.0) * carbon_price_per_ton + replacement_service_fee
    
    annual_cost_wo = (365.0 / days_wo) * cost_per_change
    annual_cost_w = (365.0 / days_w) * cost_per_change
    
    return {
        "lifespan_days_without": round(days_wo, 1),
        "lifespan_days_with": round(days_w, 1),
        "annual_savings": round(max(0.0, annual_cost_wo - annual_cost_w), 2)
    }

def calculate_field_vs_potential_benchmark(
    measured_data: Dict[str, float],
    plant: PlantProfile,
    target_h2s_ppm: float = 80.0,
    fe_price_per_kg: float = 1.20,
    carbon_bed_kg: float = 2000.0,
    carbon_price_per_ton: float = 3800.0
) -> Dict[str, Any]:
    meas_gas_m3_day = float(measured_data.get("measured_biogas_m3", plant.biogas_flow_m3_h * 24.0))
    meas_h2s_ppm = float(measured_data.get("measured_h2s_ppm", 400.0))
    meas_ch4_pct = float(measured_data.get("CH4", 53.6))
    meas_flow_h = meas_gas_m3_day / 24.0
    
    val_res = calculate_h2s_valorisation_and_yield_gain(
        nominal_flow_m3_h=meas_flow_h, raw_h2s_ppm=meas_h2s_ppm, target_h2s_ppm=target_h2s_ppm, base_ch4_pct=meas_ch4_pct
    )
    
    total_net_gain_yr = val_res["net_extra_cashflow_yr"]
    return {
        "meas_gas_m3_day": round(meas_gas_m3_day, 0),
        "pot_gas_m3_day": val_res["new_daily_gas_m3"],
        "delta_gas_m3_day": val_res["extra_daily_gas_m3"],
        "total_net_gain_yr": round(total_net_gain_yr, 2),
        "roi_pct": val_res["roi_pct"]
    }