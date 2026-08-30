"""
formulas/kinetics.py - Kinetische rekenengine over horizon en validatie.
"""

from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from .core import PlantProfile, calculate_h2s_gas_fraction, calculate_fe_dissolution_rate, calculate_free_ammonia_nh3, calculate_fos_tac_soft_sensor, FE_TO_S_RATIO, FE_PER_KG_PRODUCT

def run_kinetics_calculation(
    feeding_schedule: List[Dict[str, Any]],
    plant: PlantProfile,
    substrates_db: Dict[str, Any],
    substrate_prices: Dict[str, float] = None
) -> pd.DataFrame:
    if substrate_prices is None:
        substrate_prices = {k: v.get("price_per_ton", 0.0) for k, v in substrates_db.items()}

    results = []
    first_entry = feeding_schedule[0]["substrates"] if feeding_schedule else {}
    init_s_day = 0.0
    
    for name, tons in first_entry.items():
        if name in substrates_db:
            sub = substrates_db[name]
            init_s_day += tons * 1000.0 * sub["ts_pct"] * (sub["s_g_per_kg_ts"] / 1000.0)
            
    pool_fast = init_s_day * 0.2
    pool_med = init_s_day * 1.5
    pool_slow = init_s_day * 4.0
    
    active_fe_depot = float(plant.initial_fe_depot_kg)
    simulated_ideal_depot = float(plant.initial_fe_depot_kg)
    current_tan_mg_l = float(plant.initial_tan_mg_l)
    
    daily_biogas_m3_nominal = plant.biogas_flow_m3_h * 24.0
    kg_s_to_ppm_factor = 1.0 / (daily_biogas_m3_nominal * 1.33e-6) if daily_biogas_m3_nominal > 0 else 0.0

    # Thermisch regime factoren
    is_thermophilic = (str(plant.temp_regime).lower() == "thermofiel" or plant.temp_c > 45.0)
    nh3_critical_limit = 180.0 if is_thermophilic else 350.0
    hydrolysis_multiplier = 1.45 if is_thermophilic else 1.0

    daily_fast_s_inputs = []
    for entry in feeding_schedule:
        day_fast = 0.0
        for name, tons in entry.get("substrates", {}).items():
            if name in substrates_db:
                sub = substrates_db[name]
                kg_ts = tons * 1000.0 * sub["ts_pct"]
                day_fast += (kg_ts * (sub["s_g_per_kg_ts"] / 1000.0)) * sub["f_fast"]
        daily_fast_s_inputs.append(day_fast)

    for i, entry in enumerate(feeding_schedule):
        day = entry["day"]
        substrates = entry.get("substrates", {})
        manual_fe_dosed_kg = float(entry.get("fe_product_dosed_kg", 0.0))
        
        day_s_fast_in = 0.0
        day_s_med_in = 0.0
        day_s_slow_in = 0.0
        day_n_in_kg = 0.0
        vfa_shock_load = 0.0
        total_odm_kg = 0.0
        day_biogas_produced_m3 = 0.0
        day_substrate_cost_eur = 0.0
        dominant_vfa_sources = []
        dominant_n_sources = []
        
        for name, tons in substrates.items():
            if name in substrates_db and tons > 0:
                sub = substrates_db[name]
                kg_ts = tons * 1000.0 * sub["ts_pct"]
                vs_pct = sub.get("vs_pct", 0.85)
                odm_ton = (kg_ts * vs_pct) / 1000.0
                total_odm_kg += odm_ton * 1000.0
                
                gas_yield_odm = sub.get("biogas_m3_per_ton_odm", 450.0)
                day_biogas_produced_m3 += odm_ton * gas_yield_odm
                
                sub_price = substrate_prices.get(name, sub.get("price_per_ton", 0.0))
                day_substrate_cost_eur += tons * sub_price
                
                kg_s_total = kg_ts * (sub["s_g_per_kg_ts"] / 1000.0)
                day_s_fast_in += kg_s_total * sub["f_fast"]
                day_s_med_in += kg_s_total * sub["f_med"]
                day_s_slow_in += kg_s_total * sub["f_slow"]
                
                n_g_kg_ts = sub.get("n_g_per_kg_ts", 4.0)
                sub_n_kg = kg_ts * (n_g_kg_ts / 1000.0)
                day_n_in_kg += sub_n_kg
                if sub_n_kg > 20.0:
                    dominant_n_sources.append(name.replace("_", " ").title())
                
                sub_vfa_risk = tons * sub.get("vfa_risk", 0.0)
                vfa_shock_load += sub_vfa_risk
                if sub_vfa_risk >= 1.0:
                    dominant_vfa_sources.append(name.replace("_", " ").title())
        
        daily_tan_increase_mg_l = (day_n_in_kg * 1000.0) / plant.volume_m3 if plant.volume_m3 > 0 else 0.0
        washout_rate = 1.0 / max(10.0, plant.hrt_days)
        current_tan_mg_l = current_tan_mg_l * (1.0 - washout_rate) + daily_tan_increase_mg_l
        
        olr_val = (total_odm_kg / plant.volume_m3) if plant.volume_m3 > 0 else 0.0
        
        pool_fast += day_s_fast_in
        pool_med += day_s_med_in
        pool_slow += day_s_slow_in
        
        s_rel_fast = pool_fast * (1.0 - np.exp(-2.2 * hydrolysis_multiplier))
        s_rel_med = pool_med * (1.0 - np.exp(-0.35 * hydrolysis_multiplier))
        s_rel_slow = pool_slow * (1.0 - np.exp(-0.06 * hydrolysis_multiplier))
        s_total_released_kg = s_rel_fast + s_rel_med + s_rel_slow
        
        pool_fast = max(0.0, pool_fast - s_rel_fast)
        pool_med = max(0.0, pool_med - s_rel_med)
        pool_slow = max(0.0, pool_slow - s_rel_slow)
        
        delta_ph = -0.015 * (vfa_shock_load / 10.0) if vfa_shock_load > 0 else 0.0
        current_ph = plant.ph_nominal + delta_ph
        
        nh3_free_mg_l = calculate_free_ammonia_nh3(current_tan_mg_l, current_ph, plant.temp_c)
        alpha_gas = calculate_h2s_gas_fraction(current_ph, plant.temp_c)
        dissolution_eta = calculate_fe_dissolution_rate(current_ph)
        
        unmitigated_gas_s_kg = s_total_released_kg * alpha_gas
        raw_h2s_ppm = unmitigated_gas_s_kg * kg_s_to_ppm_factor
        
        upcoming_fast_peak = 0.0
        if i + 1 < len(daily_fast_s_inputs):
            upcoming_fast_peak += daily_fast_s_inputs[i + 1] * 0.70
        if i + 2 < len(daily_fast_s_inputs):
            upcoming_fast_peak += daily_fast_s_inputs[i + 2] * 0.35
            
        fe_stoich_today_kg = s_total_released_kg * FE_TO_S_RATIO * plant.safety_margin
        depot_deficit_kg = max(0.0, plant.target_depot_buffer_kg - simulated_ideal_depot)
        anticipation_fe_kg = upcoming_fast_peak * FE_TO_S_RATIO
        
        total_ideal_fe_kg = fe_stoich_today_kg + (depot_deficit_kg * 0.6) + anticipation_fe_kg
        effective_fe_per_kg = FE_PER_KG_PRODUCT * dissolution_eta
        ideal_fe_product_kg = total_ideal_fe_kg / effective_fe_per_kg if effective_fe_per_kg > 0 else 0.0
        
        simulated_ideal_depot += (ideal_fe_product_kg * FE_PER_KG_PRODUCT * dissolution_eta) - (s_total_released_kg * FE_TO_S_RATIO)
        fe_inflow_active_kg = manual_fe_dosed_kg * FE_PER_KG_PRODUCT * dissolution_eta
        active_fe_depot += fe_inflow_active_kg
        
        max_s_bindable_kg = active_fe_depot / FE_TO_S_RATIO
        
        if max_s_bindable_kg >= s_total_released_kg:
            s_bound_kg = s_total_released_kg
            fe_consumed_kg = s_bound_kg * FE_TO_S_RATIO
            active_fe_depot -= fe_consumed_kg
            depot_ratio = active_fe_depot / max(1.0, plant.target_depot_buffer_kg)
            equilibrium_factor = float(np.exp(-0.75 * depot_ratio))
            base_ppm = max(15.0, plant.target_h2s_ppm * 0.25)
            predicted_h2s_ppm = int(min(raw_h2s_ppm, base_ppm + (plant.target_h2s_ppm - base_ppm) * equilibrium_factor))
        else:
            s_bound_kg = max_s_bindable_kg
            fe_consumed_kg = active_fe_depot
            active_fe_depot = 0.0
            unbound_s_kg = s_total_released_kg - s_bound_kg
            breakthrough_ppm = (unbound_s_kg * alpha_gas) * kg_s_to_ppm_factor
            predicted_h2s_ppm = int(min(raw_h2s_ppm, plant.target_h2s_ppm + breakthrough_ppm))

        fos_tac_res = calculate_fos_tac_soft_sensor(
            vfa_risk_load=vfa_shock_load,
            olr=olr_val,
            tan_mg_l=current_tan_mg_l,
            ph=current_ph
        )

        gas_revenue_eur = day_biogas_produced_m3 * plant.biogas_price_per_m3
        fe_cost_eur = manual_fe_dosed_kg * plant.fe_product_price_per_kg
        ideal_fe_cost_eur = ideal_fe_product_kg * plant.fe_product_price_per_kg
        net_profit_eur = gas_revenue_eur - day_substrate_cost_eur - fe_cost_eur

        alerts = []
        vfa_causes = []

        if day_s_fast_in > 5.0:
            alerts.append("⚡Acute Fast-S Piek")
        if current_ph < plant.ph_crit_low:
            alerts.append(f"🛑pH Alarm (<{plant.ph_crit_low:.2f})")
            vfa_causes.append("Bufferuitputting")
        if vfa_shock_load > 60.0:
            alerts.append("⚠️VZV Risico")
            vfa_causes.append("Snelle koolhydraten")
        if olr_val > 11.5:
            alerts.append("📈Hoge OLR")
            vfa_causes.append(f"Overbelasting ({olr_val:.2f})")
        if nh3_free_mg_l > nh3_critical_limit:
            regime_label = "Thermofiel" if is_thermophilic else "Mesofiel"
            alerts.append(f"☠️NH₃ Alarm ({nh3_free_mg_l:.0f} mg/L)")
            vfa_causes.append(f"{regime_label} NH3-inhibitie")
        if predicted_h2s_ppm > plant.alarm_h2s_ppm:
            alerts.append(f"🔴H₂S ALARM (>{plant.alarm_h2s_ppm:.0f}ppm)")

        results.append({
            "day": day,
            "ph": round(current_ph, 2),
            "olr": round(olr_val, 2),
            "tan_mg_l": round(current_tan_mg_l, 0),
            "nh3_mg_l": round(nh3_free_mg_l, 1),
            "s_fast_in_kg": round(day_s_fast_in, 2),
            "s_released_today_kg": round(s_total_released_kg, 2),
            "raw_h2s_ppm": int(raw_h2s_ppm),
            "predicted_h2s_ppm": int(predicted_h2s_ppm),
            "ideal_fe_product_kg": float(np.round(max(0.0, ideal_fe_product_kg), 1)),
            "manual_fe_dosed_kg": round(manual_fe_dosed_kg, 1),
            "active_fe_depot_kg": round(active_fe_depot, 1),
            "vfa_risk_index": round(vfa_shock_load, 1),
            "fos_mg_l": fos_tac_res["fos_mg_l"],
            "tac_mg_l": fos_tac_res["tac_mg_l"],
            "fos_tac_ratio": fos_tac_res["fos_tac_ratio"],
            "fos_tac_status": fos_tac_res["status_text"],
            "vfa_causes": " | ".join(vfa_causes) if vfa_causes else "Geen biologische inhibitie",
            "Alerts": " | ".join(alerts) if alerts else "✅ In Balans",
            "biogas_m3_day": round(day_biogas_produced_m3, 0),
            "gas_revenue_eur": round(gas_revenue_eur, 2),
            "substrate_cost_eur": round(day_substrate_cost_eur, 2),
            "fe_cost_eur": round(fe_cost_eur, 2),
            "ideal_fe_cost_eur": round(ideal_fe_cost_eur, 2),
            "net_profit_eur": round(net_profit_eur, 2)
        })
        
    return pd.DataFrame(results)

def validate_plan_safety(
    schedule_df: pd.DataFrame,
    results_df: pd.DataFrame,
    max_dm_limit: float = 10.5,
    plant_volume_m3: float = 2500.0,
    nominal_flow_m3_h: float = 500.0
) -> Tuple[bool, List[str]]:
    errors = []
    is_safe = True
    for idx, row in results_df.iterrows():
        dag = str(row.get("Tijdstap", f"t{idx}"))
        olr = float(row.get("olr", 0.0))
        vfa = float(row.get("vfa_risk_index", 0.0))
        ph = float(row.get("ph", 7.6))

        if olr > 11.5:
            is_safe = False
            errors.append(f"❌ **{dag}:** Organische belasting te hoog (OLR = **{olr:.2f}**).")
        if vfa > 60.0:
            is_safe = False
            errors.append(f"❌ **{dag}:** Acuut verzuringsrisico (VZV = **{vfa:.1f}**).")
        if ph < 7.00:
            is_safe = False
            errors.append(f"❌ **{dag}:** Kritieke pH-daling (**{ph:.2f}**).")
    return is_safe, errors