"""
formulas/optimization.py - LP Least-Cost optimalisatie, 7-daagse MPC en prijsgevoeligheid.
"""

from typing import Any, Dict, List
from scipy.optimize import linprog
import numpy as np
import pandas as pd
from .core import FE_TO_S_RATIO, FE_PER_KG_PRODUCT

def optimize_least_cost_recipe(
    substrates_db: Dict[str, Any],
    substrate_prices: Dict[str, float],
    target_daily_biogas_m3: float = 12000.0,
    reactor_volume_m3: float = 2500.0,
    max_olr: float = 11.5,
    min_manure_tons: float = 30.0,
    max_tan_mg_l: float = 3000.0,
    hrt_days: float = 50.0,
    fe_product_price_per_kg: float = 1.20,
    safety_margin: float = 1.25
) -> Dict[str, Any]:
    sub_names = list(substrates_db.keys())
    c = [substrate_prices.get(name, substrates_db[name].get("price_per_ton", 0.0)) for name in sub_names]
    
    A_ub = []
    b_ub = []
    bounds = []
    
    for name in sub_names:
        is_manure = "mest" in name.lower() or "drijfmest" in name.lower()
        bounds.append((min_manure_tons, 100.0) if is_manure else (0.0, 60.0))
            
    gas_row = []
    for name in sub_names:
        sub = substrates_db[name]
        vs_pct = sub.get("vs_pct", 0.85)
        m3_per_ton = (sub["ts_pct"] * 1000.0 * vs_pct / 1000.0) * sub.get("biogas_m3_per_ton_odm", 450.0)
        gas_row.append(-m3_per_ton)
    A_ub.append(gas_row)
    b_ub.append(-target_daily_biogas_m3)
    
    olr_row = []
    for name in sub_names:
        sub = substrates_db[name]
        olr_row.append(sub["ts_pct"] * 1000.0 * sub.get("vs_pct", 0.85))
    A_ub.append(olr_row)
    b_ub.append(reactor_volume_m3 * max_olr)
    
    max_allowed_n = (max_tan_mg_l * reactor_volume_m3) / (max(10.0, hrt_days) * 1000.0)
    n_row = []
    for name in sub_names:
        sub = substrates_db[name]
        n_row.append(sub["ts_pct"] * sub.get("n_g_per_kg_ts", 10.0))
    A_ub.append(n_row)
    b_ub.append(max_allowed_n)
    
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
    
    optimal_diet = {}
    tot_sub_cost = 0.0
    tot_gas = 0.0
    tot_odm = 0.0
    tot_n = 0.0
    tot_s = 0.0
    
    if res.success:
        for i, name in enumerate(sub_names):
            tons = round(float(res.x[i]), 2)
            optimal_diet[name] = tons
            sub = substrates_db[name]
            price = substrate_prices.get(name, sub.get("price_per_ton", 0.0))
            tot_sub_cost += tons * price
            odm = tons * sub["ts_pct"] * sub.get("vs_pct", 0.85)
            tot_odm += odm
            tot_gas += odm * sub.get("biogas_m3_per_ton_odm", 450.0)
            tot_n += tons * sub["ts_pct"] * sub.get("n_g_per_kg_ts", 10.0)
            tot_s += tons * 1000.0 * sub["ts_pct"] * (sub.get("s_g_per_kg_ts", 4.0) / 1000.0)
    else:
        for name in sub_names:
            optimal_diet[name] = 10.0 if "mest" in name.lower() else 5.0
            
    fe_needed = (tot_s * FE_TO_S_RATIO * safety_margin) / FE_PER_KG_PRODUCT
    fe_bags = int(np.ceil(fe_needed / 20.0))
    fe_cost = fe_needed * fe_product_price_per_kg
    
    return {
        "success": res.success,
        "message": res.message if hasattr(res, "message") else "Geoptimaliseerd",
        "optimal_diet": optimal_diet,
        "total_substrate_cost_eur": round(tot_sub_cost, 2),
        "fe_needed_kg": round(fe_needed, 1),
        "fe_bags_day": fe_bags,
        "fe_cost_eur": round(fe_cost, 2),
        "total_cost_eur": round(tot_sub_cost + fe_cost, 2),
        "total_biogas_m3": round(tot_gas, 0),
        "total_odm_kg": round(tot_odm * 1000.0, 0),
        "calculated_olr": round((tot_odm * 1000.0) / max(1.0, reactor_volume_m3), 2),
        "estimated_tan_mg_l": round((tot_n * hrt_days) / reactor_volume_m3 * 1000.0, 0),
        "total_s_kg": round(tot_s, 1)
    }

def optimize_multiday_least_cost_recipe(
    substrates_db: Dict[str, Any],
    substrate_prices: Dict[str, float],
    target_daily_biogas_m3: float = 12000.0,
    reactor_volume_m3: float = 2500.0,
    max_olr: float = 11.5,
    min_manure_tons: float = 30.0,
    max_tan_mg_l: float = 3000.0,
    hrt_days: float = 50.0,
    fe_product_price_per_kg: float = 1.20,
    safety_margin: float = 1.25,
    horizon_days: int = 7
) -> Dict[str, Any]:
    sub_names = list(substrates_db.keys())
    n_subs = len(sub_names)
    total_vars = n_subs * horizon_days
    
    c = []
    for _ in range(horizon_days):
        for name in sub_names:
            c.append(substrate_prices.get(name, substrates_db[name].get("price_per_ton", 0.0)))
            
    A_ub, b_ub, bounds = [], [], []
    for _ in range(horizon_days):
        for name in sub_names:
            bounds.append((min_manure_tons, 100.0) if "mest" in name.lower() else (0.0, 60.0))
                
    max_allowed_n = (max_tan_mg_l * reactor_volume_m3) / (max(10.0, hrt_days) * 1000.0)
                
    for d in range(horizon_days):
        gas_row = [0.0] * total_vars
        for i, name in enumerate(sub_names):
            sub = substrates_db[name]
            m3_per_ton = (sub["ts_pct"] * 1000.0 * sub.get("vs_pct", 0.85) / 1000.0) * sub.get("biogas_m3_per_ton_odm", 450.0)
            gas_row[d * n_subs + i] = -m3_per_ton
        A_ub.append(gas_row)
        b_ub.append(-target_daily_biogas_m3)
        
        olr_row = [0.0] * total_vars
        for i, name in enumerate(sub_names):
            sub = substrates_db[name]
            olr_row[d * n_subs + i] = sub["ts_pct"] * 1000.0 * sub.get("vs_pct", 0.85)
        A_ub.append(olr_row)
        b_ub.append(reactor_volume_m3 * max_olr)
        
        n_row = [0.0] * total_vars
        for i, name in enumerate(sub_names):
            sub = substrates_db[name]
            n_row[d * n_subs + i] = sub["ts_pct"] * sub.get("n_g_per_kg_ts", 10.0)
        A_ub.append(n_row)
        b_ub.append(max_allowed_n)
        
        if d > 0:
            for i, name in enumerate(sub_names):
                if substrates_db[name].get("vfa_risk", 0.0) > 2.0:
                    smooth_row = [0.0] * total_vars
                    smooth_row[d * n_subs + i] = 1.0
                    smooth_row[(d - 1) * n_subs + i] = -1.0
                    A_ub.append(smooth_row)
                    b_ub.append(10.0)

    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
    
    schedule_results = []
    tot_horizon_sub_cost = 0.0
    tot_horizon_fe_cost = 0.0
    tot_horizon_cost = 0.0
    tot_horizon_gas = 0.0
    
    if res.success:
        for d in range(horizon_days):
            day_diet = {}
            day_sub_cost = 0.0
            day_gas = 0.0
            day_odm = 0.0
            day_n = 0.0
            day_s = 0.0
            
            for i, name in enumerate(sub_names):
                tons = round(float(res.x[d * n_subs + i]), 2)
                day_diet[name] = tons
                sub = substrates_db[name]
                day_sub_cost += tons * substrate_prices.get(name, sub.get("price_per_ton", 0.0))
                odm = tons * sub["ts_pct"] * sub.get("vs_pct", 0.85)
                day_odm += odm
                day_gas += odm * sub.get("biogas_m3_per_ton_odm", 450.0)
                day_n += tons * sub["ts_pct"] * sub.get("n_g_per_kg_ts", 10.0)
                day_s += tons * 1000.0 * sub["ts_pct"] * (sub.get("s_g_per_kg_ts", 4.0) / 1000.0)
                
            fe_needed_d = (day_s * FE_TO_S_RATIO * safety_margin) / FE_PER_KG_PRODUCT
            fe_bags_d = int(np.ceil(fe_needed_d / 20.0))
            fe_cost_d = fe_needed_d * fe_product_price_per_kg
            day_total = day_sub_cost + fe_cost_d
            
            tot_horizon_sub_cost += day_sub_cost
            tot_horizon_fe_cost += fe_cost_d
            tot_horizon_cost += day_total
            tot_horizon_gas += day_gas
            
            schedule_results.append({
                "dag": f"Dag t+{d}" if d > 0 else "Dag t0 (Vandaag)",
                "diet": day_diet,
                "dag_sub_cost_eur": round(day_sub_cost, 2),
                "fe_bags": fe_bags_d,
                "fe_cost_eur": round(fe_cost_d, 2),
                "dag_totaal_kosten_eur": round(day_total, 2),
                "dag_biogas_m3": round(day_gas, 0),
                "dag_olr": round((day_odm * 1000.0) / max(1.0, reactor_volume_m3), 2),
                "est_tan_mg_l": round((day_n * hrt_days) / reactor_volume_m3 * 1000.0, 0),
                "dag_s_kg": round(day_s, 1)
            })
            
    return {
        "success": res.success,
        "message": res.message if hasattr(res, "message") else "MPC Geoptimaliseerd",
        "horizon_days": horizon_days,
        "total_substrate_cost_eur": round(tot_horizon_sub_cost, 2),
        "total_fe_cost_eur": round(tot_horizon_fe_cost, 2),
        "total_cost_eur": round(tot_horizon_cost, 2),
        "avg_daily_cost_eur": round(tot_horizon_cost / horizon_days, 2),
        "total_biogas_m3": round(tot_horizon_gas, 0),
        "schedule": schedule_results
    }

def calculate_substrate_sensitivity_analysis(
    substrates_db: Dict[str, Any],
    base_substrate_prices: Dict[str, float],
    target_daily_biogas_m3: float = 12000.0,
    reactor_volume_m3: float = 2500.0,
    max_olr: float = 11.5,
    target_substrate: str = "maissilage",
    price_variation_pct_range: List[float] = [-50.0, -25.0, 0.0, 25.0, 50.0, 100.0]
) -> pd.DataFrame:
    results = []
    base_price = base_substrate_prices.get(target_substrate, 0.0)
    for pct in price_variation_pct_range:
        current_prices = base_substrate_prices.copy()
        new_price = base_price * (1.0 + (pct / 100.0))
        current_prices[target_substrate] = new_price
        
        opt_res = optimize_least_cost_recipe(
            substrates_db=substrates_db,
            substrate_prices=current_prices,
            target_daily_biogas_m3=target_daily_biogas_m3,
            reactor_volume_m3=reactor_volume_m3,
            max_olr=max_olr
        )
        if opt_res["success"]:
            results.append({
                "Prijsvariatie (%)": pct,
                "Substraatijs (€/ton)": round(new_price, 2),
                "Ingezet Tonage (t/dag)": round(opt_res["optimal_diet"].get(target_substrate, 0.0), 1),
                "Totale Dagkosten (€/dag)": opt_res["total_cost_eur"],
                "Totale Biogas (m³)": opt_res["total_biogas_m3"],
                "Berekende OLR": opt_res["calculated_olr"]
            })
    return pd.DataFrame(results)