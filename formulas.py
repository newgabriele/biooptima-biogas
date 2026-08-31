"""
formulas.py - Kinetische rekenengine, proceschemie, H2S/NH3-inhibitie,
DM-Verdunningsbalans, Gesynchroniseerde Validatie, H2S-Gasvalorisatie, 
Actieve Kool Standtijd, WKK/CHP Olie-exploitatie, Benchmarkvergelijking, 
Wobbe-Index, PCI/PCS Thermodynamica & Least-Cost Optimalisatie.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
from scipy.optimize import linprog
import numpy as np
import pandas as pd

# ============================================================================
# 1. CONSTANTEN & CHEMISCHE PARAMETERS
# ============================================================================

M_S = 32.065
M_FE = 55.845
M_FE2O3 = 159.69   # ~70.0% Fe
M_FEO = 71.844     # ~77.7% Fe

FRAC_FE2O3 = 0.35
FRAC_FEO = 0.35

FE_PER_KG_PRODUCT = (FRAC_FE2O3 * (2 * M_FE / M_FE2O3)) + (FRAC_FEO * (M_FE / M_FEO))
FE_TO_S_RATIO = M_FE / M_S  # 1.7418 kg Fe nodig per 1.0 kg S

# ============================================================================
# 2. DATASTRUCTUUR VOOR INSTALLATIES
# ============================================================================

@dataclass
class PlantProfile:
    name: str = "Standaard Installatie"
    inst_type: str = "agro"  # "agro", "covergisting", "industrieel"
    volume_m3: float = 2500.0
    biogas_flow_m3_h: float = 500.0
    ph_nominal: float = 7.65
    ph_crit_low: float = 7.30
    temp_c: float = 38.5
    target_h2s_ppm: float = 100.0
    alarm_h2s_ppm: float = 200.0
    target_depot_buffer_kg: float = 100.0
    initial_fe_depot_kg: float = 120.0
    safety_margin: float = 1.25
    max_vfa_shock_risk: float = 2.5
    initial_tan_mg_l: float = 2200.0
    hrt_days: float = 50.0
    biogas_price_per_m3: float = 0.68
    fe_product_price_per_kg: float = 1.20

# ============================================================================
# 3. FYSISCH-CHEMISCHE EVENWICHTEN & DM BALANS
# ============================================================================

def calculate_h2s_gas_fraction(ph: float, temp_c: float = 38.5) -> float:
    pka1 = 7.05 - 0.013 * (temp_c - 25.0)
    alpha_h2s = 1.0 / (1.0 + 10 ** (ph - pka1))
    return float(np.clip(alpha_h2s, 0.01, 0.99))


def calculate_fe_dissolution_rate(ph: float) -> float:
    eta = 1.0 + (7.5 - ph) * 0.35
    return float(np.clip(eta, 0.4, 1.6))


def calculate_free_ammonia_nh3(tan_mg_l: float, ph: float, temp_c: float) -> float:
    t_k = temp_c + 273.15
    pka_nh4 = 0.09018 + (2729.92 / t_k)
    f_nh3 = 1.0 / (1.0 + 10 ** (pka_nh4 - ph))
    return float(tan_mg_l * f_nh3)


def calculate_reactor_dm_balance(schedule_df, results_df, plant_data, substrates_db, active_cols):
    vol_m3 = float(plant_data.get("volume_m3", 2500.0))
    initial_dm = float(plant_data.get("initial_dm_pct", 8.5))
    hrt_days = float(plant_data.get("hrt_days", 50.0))
    recirc_type = plant_data.get("recirculation_type", "Eigen Digestaat-Circulaat (Dunne fractie)")
    recirc_ts_pct = 0.040 if "Eigen" in recirc_type else 0.000
    current_ts_mass = (vol_m3 * 1.0) * (initial_dm / 100.0)
    total_reactor_mass = vol_m3 * 1.0
    dm_series = []
    
    for idx, row in schedule_df.iterrows():
        daily_inflow_ts = 0.0
        daily_inflow_vol = 0.0
        for sub in active_cols:
            tons = float(row.get(sub, 0.0))
            if tons > 0 and sub in substrates_db:
                daily_inflow_ts += tons * float(substrates_db[sub]["ts_pct"])
                daily_inflow_vol += tons

        recirc_m3 = float(row.get("recirc_m3_day", 0.0))
        daily_inflow_ts += recirc_m3 * recirc_ts_pct
        daily_inflow_vol += recirc_m3

        res_row = results_df.iloc[idx]
        gas_m3 = float(res_row.get("biogas_m3_day", 0.0))
        ts_destroyed_ton = (gas_m3 * 1.15) / 1000.0
        outflow_ton = max(daily_inflow_vol, vol_m3 / hrt_days)
        current_dm_fraction = current_ts_mass / max(100.0, total_reactor_mass)
        ts_outflow_ton = outflow_ton * current_dm_fraction
        
        current_ts_mass = max(10.0, current_ts_mass + daily_inflow_ts - ts_destroyed_ton - ts_outflow_ton)
        dm_series.append(round((current_ts_mass / total_reactor_mass) * 100.0, 2))
    return np.array(dm_series)


def calculate_required_recirculation_for_dm(
    diet: Dict[str, float],
    substrates_db: Dict[str, Any],
    target_dm_pct: float = 8.5,
    recirc_ts_pct: float = 0.04
) -> float:
    target_frac = target_dm_pct / 100.0
    tot_ts_substrates = 0.0
    tot_mass_substrates = 0.0

    for sub, tons in diet.items():
        if sub in substrates_db and tons > 0:
            ts = float(substrates_db[sub].get("ts_pct", 0.2))
            tot_ts_substrates += tons * ts
            tot_mass_substrates += tons

    denom = target_frac - recirc_ts_pct
    if denom <= 0.001:
        denom = 0.01

    needed_recirc = (tot_ts_substrates - (target_frac * tot_mass_substrates)) / denom
    return float(max(5.0, min(80.0, round(needed_recirc, 1))))

# ============================================================================
# 4. KINETISCHE REKENENGINE OVER DE VOLLEDIGE HORIZON
# ============================================================================

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
        
        s_rel_fast = pool_fast * (1.0 - np.exp(-2.2))
        s_rel_med = pool_med * (1.0 - np.exp(-0.35))
        s_rel_slow = pool_slow * (1.0 - np.exp(-0.06))
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
            src_text = f" ({', '.join(dominant_vfa_sources)})" if dominant_vfa_sources else ""
            vfa_causes.append(f"Snelle koolhydraten{src_text}")
        if olr_val > 11.5:
            alerts.append("📈Hoge OLR")
            vfa_causes.append(f"Overbelasting ({olr_val:.2f} kg ODM/m³/d)")
        if nh3_free_mg_l > 500:
            alerts.append(f"☠️NH₃ Alarm ({nh3_free_mg_l:.0f} mg/L)")
            n_src = f" ({', '.join(dominant_n_sources)})" if dominant_n_sources else ""
            vfa_causes.append(f"Ernstige NH3-inhibitie{n_src}")
        elif nh3_free_mg_l > 250:
            alerts.append(f"⚠️NH₃ Hoog ({nh3_free_mg_l:.0f} mg/L)")
            vfa_causes.append(f"Matige NH3-inhibitie")
        if predicted_h2s_ppm > plant.alarm_h2s_ppm:
            alerts.append(f"🔴H₂S ALARM (>{plant.alarm_h2s_ppm:.0f}ppm)")
        elif predicted_h2s_ppm > plant.target_h2s_ppm:
            alerts.append(f"🟠H₂S Boven Doel")

        alert_str = " | ".join(alerts) if alerts else "✅ In Balans"
        cause_str = " | ".join(vfa_causes) if vfa_causes else "Geen biologische inhibitie"

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
            "vfa_causes": cause_str,
            "Alerts": alert_str,
            "biogas_m3_day": round(day_biogas_produced_m3, 0),
            "gas_revenue_eur": round(gas_revenue_eur, 2),
            "substrate_cost_eur": round(day_substrate_cost_eur, 2),
            "fe_cost_eur": round(fe_cost_eur, 2),
            "ideal_fe_cost_eur": round(ideal_fe_cost_eur, 2),
            "net_profit_eur": round(net_profit_eur, 2)
        })
        
    return pd.DataFrame(results)

# ============================================================================
# 5. VALIDATIE & PLAFONDS
# ============================================================================

def calculate_max_allowed_inputs(
    schedule_df: pd.DataFrame,
    plant: PlantProfile,
    substrates_db: Dict[str, Any],
    active_substrates: List[str],
    max_dm_limit: float = 10.5
) -> pd.DataFrame:
    max_records = []
    max_total_odm_kg = plant.volume_m3 * 11.5
    
    for idx, row in schedule_df.iterrows():
        day_lbl = str(row.get("Dag", f"t{idx}"))
        rec = {"Dag": day_lbl}
        
        for sub in active_substrates:
            if sub in substrates_db:
                sub_meta = substrates_db[sub]
                ts = float(sub_meta.get("ts_pct", 0.2))
                vs = float(sub_meta.get("vs_pct", 0.85))
                odm_factor = max(0.01, ts * vs * 1000.0)
                single_sub_cap = min(80.0, round(max_total_odm_kg / odm_factor, 1))
                rec[f"Max {sub.replace('_', ' ').title()} (t)"] = single_sub_cap

        rec["Max Circulaat (m³)"] = 100.0
        max_records.append(rec)

    return pd.DataFrame(max_records)


def validate_plan_safety(
    schedule_df: pd.DataFrame,
    results_df: pd.DataFrame,
    max_dm_limit: float = 10.5,
    plant_volume_m3: float = 2500.0,
    nominal_flow_m3_h: float = 500.0
) -> Tuple[bool, List[str]]:
    errors = []
    is_safe = True
    max_allowed_olr = 11.5
    max_allowed_vfa = 60.0

    for idx, row in results_df.iterrows():
        dag = str(row.get("Tijdstap", f"t{idx}"))
        olr = float(row.get("olr", 0.0))
        vfa = float(row.get("vfa_risk_index", 0.0))
        dm = float(row.get("dm_pct_reactor", 0.0))
        ph = float(row.get("ph", 7.6))

        if olr > max_allowed_olr:
            is_safe = False
            errors.append(f"❌ **{dag}:** Organische belasting te hoog (OLR = **{olr:.2f}** > max {max_allowed_olr:.2f} kg ODM/m³·d).")
        if vfa > max_allowed_vfa:
            is_safe = False
            errors.append(f"❌ **{dag}:** Acuut verzuringsrisico (VZV-Index = **{vfa:.1f}** > max {max_allowed_vfa:.1f}).")
        if dm > (max_dm_limit + 2.0):
            is_safe = False
            errors.append(f"❌ **{dag}:** Drogestoflimiet overschreden (**{dm:.1f}%** DM > max {max_dm_limit:.1f}%).")
        if ph < 7.00:
            is_safe = False
            errors.append(f"❌ **{dag}:** Kritieke pH-daling (**{ph:.2f}** < 7.00).")

    return is_safe, errors

# ============================================================================
# 6. H2S VALORISATIE & THEORETISCHE GASOPBRENGSTVERHOGING
# ============================================================================

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
    
    if inst_type == "agro":
        default_diet_boost = 2.0
        ammonia_stress_factor = 1.0
    elif inst_type == "covergisting":
        default_diet_boost = 3.0
        ammonia_stress_factor = 1.2
    elif inst_type == "industrieel":
        default_diet_boost = 3.5
        ammonia_stress_factor = 1.4
    else:
        default_diet_boost = 2.5
        ammonia_stress_factor = 1.0

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
    srb_redirection_pct = min(1.0, (raw_h2s_ppm - target_h2s_ppm) / 5000.0 * 1.0)
    
    total_yield_gain_pct = toxicity_relief_pct + diet_gain_pct + srb_redirection_pct
    
    extra_daily_gas_m3 = base_daily_gas_m3 * (total_yield_gain_pct / 100.0)
    extra_annual_gas_m3 = extra_daily_gas_m3 * 365.0
    new_daily_gas_m3 = base_daily_gas_m3 + extra_daily_gas_m3
    new_flow_m3_h = new_daily_gas_m3 / 24.0
    
    chp_gain_point = 1.2 if inst_type in ["covergisting", "industrieel"] and diet_boost_enabled else (1.0 if diet_boost_enabled else 0.3)
    new_ch4_pct = min(68.0, base_ch4_pct + chp_gain_point)
    
    base_kwh_per_m3 = (base_ch4_pct / 100.0) * 9.94
    new_kwh_per_m3 = (new_ch4_pct / 100.0) * 9.94
    
    base_annual_kwh = base_annual_gas_m3 * base_kwh_per_m3
    new_annual_kwh = new_daily_gas_m3 * 365.0 * new_kwh_per_m3
    extra_annual_kwh = max(0.0, new_annual_kwh - base_annual_kwh)
    
    extra_revenue_volume_yr = extra_annual_gas_m3 * biogas_price_per_m3
    net_extra_cashflow_yr = extra_revenue_volume_yr - fe_cost_yr
    roi_pct = (net_extra_cashflow_yr / fe_cost_yr * 100.0) if fe_cost_yr > 0 else 0.0

    return {
        "inst_type": inst_type,
        "base_flow_m3_h": round(nominal_flow_m3_h, 1),
        "new_flow_m3_h": round(new_flow_m3_h, 1),
        "base_daily_gas_m3": round(base_daily_gas_m3, 0),
        "new_daily_gas_m3": round(new_daily_gas_m3, 0),
        "extra_daily_gas_m3": round(extra_daily_gas_m3, 0),
        "extra_annual_gas_m3": round(extra_annual_gas_m3, 0),
        "h2s_reduction_pct": round(h2s_reduction_pct, 1),
        "s_removed_day_kg": round(s_removed_day_kg, 1),
        "toxicity_relief_pct": round(toxicity_relief_pct, 2),
        "diet_gain_pct": round(diet_gain_pct, 2),
        "srb_redirection_pct": round(srb_redirection_pct, 2),
        "total_yield_gain_pct": round(total_yield_gain_pct, 2),
        "base_ch4_pct": round(base_ch4_pct, 1),
        "new_ch4_pct": round(new_ch4_pct, 1),
        "base_kwh_per_m3": round(base_kwh_per_m3, 2),
        "new_kwh_per_m3": round(new_kwh_per_m3, 2),
        "extra_annual_kwh": round(extra_annual_kwh, 0),
        "fe_needed_day_kg": round(fe_needed_day_kg, 1),
        "fe_bags_day": fe_bags_day,
        "fe_cost_yr": round(fe_cost_yr, 2),
        "extra_revenue_volume_yr": round(extra_revenue_volume_yr, 2),
        "net_extra_cashflow_yr": round(net_extra_cashflow_yr, 2),
        "roi_pct": round(roi_pct, 1)
    }

# ============================================================================
# 7. ACTIEVE KOOLFILTER STANDTIJD & EXPLOITATIE BENCHMARK
# ============================================================================

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
    s_conv_factor = 1.33e-6
    
    if "KI" in carbon_type:
        s_cap_wt_pct = 0.12
    elif "NaOH" in carbon_type or "KOH" in carbon_type:
        s_cap_wt_pct = 0.08
    else:
        s_cap_wt_pct = 0.04
        
    bed_s_capacity_kg = float(carbon_bed_kg * s_cap_wt_pct)
    s_inflow_raw_day = float(daily_gas_m3 * raw_h2s_ppm * s_conv_factor)
    s_inflow_target_day = float(daily_gas_m3 * target_h2s_ppm * s_conv_factor)
    
    lifespan_days_without = max(0.1, bed_s_capacity_kg / max(0.001, s_inflow_raw_day))
    lifespan_days_with = max(0.1, bed_s_capacity_kg / max(0.001, s_inflow_target_day))
    lifespan_factor = lifespan_days_with / lifespan_days_without
    
    changes_yr_without = 365.0 / lifespan_days_without
    changes_yr_with = 365.0 / lifespan_days_with
    cost_per_change = (carbon_bed_kg / 1000.0) * carbon_price_per_ton + replacement_service_fee
    
    annual_cost_without = changes_yr_without * cost_per_change
    annual_cost_with = changes_yr_with * cost_per_change
    annual_savings = max(0.0, annual_cost_without - annual_cost_with)
    
    return {
        "carbon_type": carbon_type,
        "s_cap_wt_pct": round(s_cap_wt_pct * 100.0, 1),
        "bed_s_capacity_kg": round(bed_s_capacity_kg, 1),
        "s_inflow_raw_day": round(s_inflow_raw_day, 2),
        "s_inflow_target_day": round(s_inflow_target_day, 2),
        "lifespan_days_without": round(lifespan_days_without, 1),
        "lifespan_months_without": round(lifespan_days_without / 30.416, 1),
        "lifespan_days_with": round(lifespan_days_with, 1),
        "lifespan_months_with": round(lifespan_days_with / 30.416, 1),
        "lifespan_factor": round(lifespan_factor, 1),
        "changes_yr_without": round(changes_yr_without, 1),
        "changes_yr_with": round(changes_yr_with, 2),
        "cost_per_change": round(cost_per_change, 2),
        "annual_cost_without": round(annual_cost_without, 2),
        "annual_cost_with": round(annual_cost_with, 2),
        "annual_savings": round(annual_savings, 2)
    }

# ============================================================================
# 8. WKK / CHP MOTORSTANDTIJD, OLIEWISSELS & FILTERELIMINATIE
# ============================================================================

def calculate_chp_and_filter_elimination_benchmark(
    nominal_flow_m3_h: float = 500.0,
    raw_h2s_ppm: float = 2500.0,
    target_h2s_ppm: float = 80.0,
    chp_annual_operating_hours: float = 8200.0,
    oil_interval_raw_hours: float = 400.0,
    oil_interval_low_h2s_hours: float = 1400.0,
    oil_service_cost_eur: float = 850.0,
    engine_maint_wear_savings_yr: float = 4500.0,
    eliminate_carbon_filter: bool = True,
    carbon_bed_kg: float = 2000.0,
    carbon_price_per_ton: float = 3800.0,
    carbon_replacement_fee: float = 1200.0
) -> Dict[str, Any]:
    oil_changes_raw_yr = chp_annual_operating_hours / max(100.0, oil_interval_raw_hours)
    oil_changes_treated_yr = chp_annual_operating_hours / max(100.0, oil_interval_low_h2s_hours)
    
    oil_cost_raw_yr = oil_changes_raw_yr * oil_service_cost_eur
    oil_cost_treated_yr = oil_changes_treated_yr * oil_service_cost_eur
    oil_cost_savings_yr = max(0.0, oil_cost_raw_yr - oil_cost_treated_yr)
    
    total_chp_savings_yr = oil_cost_savings_yr + engine_maint_wear_savings_yr
    oil_interval_factor = oil_interval_low_h2s_hours / max(1.0, oil_interval_raw_hours)
    
    daily_gas_m3 = float(nominal_flow_m3_h * 24.0)
    s_conv = 1.33e-6
    s_raw_day = daily_gas_m3 * raw_h2s_ppm * s_conv
    bed_cap_s = carbon_bed_kg * 0.12
    cost_per_carbon_change = (carbon_bed_kg / 1000.0) * carbon_price_per_ton + carbon_replacement_fee
    
    carbon_changes_raw_yr = 365.0 / max(0.1, (bed_cap_s / max(0.001, s_raw_day)))
    carbon_cost_raw_yr = carbon_changes_raw_yr * cost_per_carbon_change
    
    if eliminate_carbon_filter:
        carbon_cost_treated_yr = 0.0
        carbon_savings_yr = carbon_cost_raw_yr
        carbon_status = "100% Geëlimineerd / Direct naar WKK (<100 ppm)"
    else:
        s_target_day = daily_gas_m3 * target_h2s_ppm * s_conv
        carbon_changes_treated_yr = 365.0 / max(0.1, (bed_cap_s / max(0.001, s_target_day)))
        carbon_cost_treated_yr = carbon_changes_treated_yr * cost_per_carbon_change
        carbon_savings_yr = max(0.0, carbon_cost_raw_yr - carbon_cost_treated_yr)
        carbon_status = "Polishing Bed Actief"

    total_combined_savings_yr = total_chp_savings_yr + carbon_savings_yr
    
    return {
        "oil_interval_raw_hours": round(oil_interval_raw_hours, 0),
        "oil_interval_low_h2s_hours": round(oil_interval_low_h2s_hours, 0),
        "oil_interval_factor": round(oil_interval_factor, 1),
        "oil_changes_raw_yr": round(oil_changes_raw_yr, 1),
        "oil_changes_treated_yr": round(oil_changes_treated_yr, 1),
        "oil_cost_raw_yr": round(oil_cost_raw_yr, 2),
        "oil_cost_treated_yr": round(oil_cost_treated_yr, 2),
        "oil_cost_savings_yr": round(oil_cost_savings_yr, 2),
        "engine_maint_wear_savings_yr": round(engine_maint_wear_savings_yr, 2),
        "total_chp_savings_yr": round(total_chp_savings_yr, 2),
        "carbon_cost_raw_yr": round(carbon_cost_raw_yr, 2),
        "carbon_cost_treated_yr": round(carbon_cost_treated_yr, 2),
        "carbon_savings_yr": round(carbon_savings_yr, 2),
        "carbon_status": carbon_status,
        "total_combined_savings_yr": round(total_combined_savings_yr, 2)
    }

# ============================================================================
# 9. INTEGRALE BENCHMARKVERGELIJKING
# ============================================================================

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
    meas_co2_pct = float(measured_data.get("CO2", 46.42))
    meas_o2_pct = float(measured_data.get("O2", 0.17))
    meas_pci = float(measured_data.get("PCI", 14.8))
    meas_pcs = float(measured_data.get("PCS", 21.3))
    meas_flow_h = meas_gas_m3_day / 24.0
    
    val_res = calculate_h2s_valorisation_and_yield_gain(
        nominal_flow_m3_h=meas_flow_h,
        raw_h2s_ppm=meas_h2s_ppm,
        target_h2s_ppm=target_h2s_ppm,
        base_ch4_pct=meas_ch4_pct,
        biogas_price_per_m3=plant.biogas_price_per_m3,
        fe_price_per_kg=fe_price_per_kg,
        safety_margin=plant.safety_margin,
        diet_boost_enabled=True,
        inst_type=plant.inst_type
    )
    
    chp_res = calculate_chp_and_filter_elimination_benchmark(
        nominal_flow_m3_h=meas_flow_h,
        raw_h2s_ppm=meas_h2s_ppm,
        target_h2s_ppm=target_h2s_ppm,
        chp_annual_operating_hours=8200.0,
        oil_interval_raw_hours=500.0 if meas_h2s_ppm <= 400.0 else 400.0,
        oil_interval_low_h2s_hours=1400.0,
        oil_service_cost_eur=850.0,
        engine_maint_wear_savings_yr=4500.0,
        eliminate_carbon_filter=True,
        carbon_bed_kg=carbon_bed_kg,
        carbon_price_per_ton=carbon_price_per_ton,
        carbon_replacement_fee=1200.0
    )
    
    delta_gas_m3_day = val_res["new_daily_gas_m3"] - meas_gas_m3_day
    delta_gas_pct = (delta_gas_m3_day / max(1.0, meas_gas_m3_day)) * 100.0
    delta_h2s_ppm = meas_h2s_ppm - target_h2s_ppm
    delta_ch4_pct = val_res["new_ch4_pct"] - meas_ch4_pct
    
    pot_pci = meas_pci * (val_res["new_ch4_pct"] / max(1.0, meas_ch4_pct))
    pot_pcs = meas_pcs * (val_res["new_ch4_pct"] / max(1.0, meas_ch4_pct))
    
    wobbe_meas = calculate_wobbe_index(
        ch4_pct=meas_ch4_pct, co2_pct=meas_co2_pct, o2_pct=meas_o2_pct, pcs_mj_m3=meas_pcs, pci_mj_m3=meas_pci
    )
    wobbe_pot = calculate_wobbe_index(
        ch4_pct=val_res["new_ch4_pct"], co2_pct=max(0.0, meas_co2_pct - delta_ch4_pct), o2_pct=meas_o2_pct, pcs_mj_m3=pot_pcs, pci_mj_m3=pot_pci
    )
    
    total_gross_gain_yr = val_res["extra_revenue_volume_yr"] + chp_res["total_combined_savings_yr"]
    fe_cost_yr = val_res["fe_cost_yr"]
    total_net_gain_yr = total_gross_gain_yr - fe_cost_yr
    
    return {
        "meas_flow_h": round(meas_flow_h, 1),
        "meas_gas_m3_day": round(meas_gas_m3_day, 0),
        "meas_h2s_ppm": round(meas_h2s_ppm, 0),
        "meas_ch4_pct": round(meas_ch4_pct, 1),
        "meas_pci": round(meas_pci, 2),
        "meas_pcs": round(meas_pcs, 2),
        "meas_kwh_m3": round(meas_pci * 0.277778, 2),
        "meas_wobbe_ws_mj": wobbe_meas["wobbe_upper_mj_m3"],
        "meas_wobbe_ws_kwh": wobbe_meas["wobbe_upper_kwh_m3"],
        "meas_wobbe_class": wobbe_meas["gas_class"],
        "meas_density_d": wobbe_meas["relative_density_d"],
        "pot_flow_h": val_res["new_flow_m3_h"],
        "pot_gas_m3_day": val_res["new_daily_gas_m3"],
        "pot_h2s_ppm": target_h2s_ppm,
        "pot_ch4_pct": val_res["new_ch4_pct"],
        "pot_pci": round(pot_pci, 2),
        "pot_pcs": round(pot_pcs, 2),
        "pot_kwh_m3": round(pot_pci * 0.277778, 2),
        "pot_wobbe_ws_mj": wobbe_pot["wobbe_upper_mj_m3"],
        "pot_wobbe_ws_kwh": wobbe_pot["wobbe_upper_kwh_m3"],
        "pot_wobbe_class": wobbe_pot["gas_class"],
        "pot_density_d": wobbe_pot["relative_density_d"],
        "delta_gas_m3_day": round(delta_gas_m3_day, 0),
        "delta_gas_pct": round(delta_gas_pct, 2),
        "delta_h2s_ppm": round(delta_h2s_ppm, 0),
        "delta_ch4_pct": round(delta_ch4_pct, 1),
        "delta_wobbe_ws_mj": round(wobbe_pot["wobbe_upper_mj_m3"] - wobbe_meas["wobbe_upper_mj_m3"], 2),
        "extra_revenue_gas_yr": val_res["extra_revenue_volume_yr"],
        "chp_oil_savings_yr": chp_res["total_chp_savings_yr"],
        "carbon_filter_savings_yr": chp_res["carbon_savings_yr"],
        "fe_cost_yr": fe_cost_yr,
        "fe_bags_day": val_res["fe_bags_day"],
        "total_net_gain_yr": round(total_net_gain_yr, 2),
        "roi_pct": round((total_net_gain_yr / fe_cost_yr * 100.0) if fe_cost_yr > 0 else 0.0, 1)
    }

# ============================================================================
# 10. WOBBE-INDEX & GASKWALITEITS-CLASSIFICATIE
# ============================================================================

def calculate_wobbe_index(
    ch4_pct: float = 53.6,
    co2_pct: float = 46.42,
    o2_pct: float = 0.17,
    n2_pct: float = 0.0,
    pcs_mj_m3: float = None,
    pci_mj_m3: float = None
) -> Dict[str, Any]:
    y_ch4 = max(0.01, min(1.0, ch4_pct / 100.0))
    y_co2 = max(0.0, min(1.0, (co2_pct if co2_pct is not None else (100.0 - ch4_pct - o2_pct - n2_pct)) / 100.0))
    y_o2 = max(0.0, min(0.1, o2_pct / 100.0))
    y_n2 = max(0.0, min(0.2, n2_pct / 100.0))
    
    m_ch4 = 16.043
    m_co2 = 44.010
    m_o2 = 31.999
    m_n2 = 28.013
    m_air = 28.964
    
    m_gas = (y_ch4 * m_ch4) + (y_co2 * m_co2) + (y_o2 * m_o2) + (y_n2 * m_n2)
    rel_density = m_gas / m_air
    
    calc_pcs = pcs_mj_m3 if pcs_mj_m3 is not None and pcs_mj_m3 > 0 else (y_ch4 * 39.82)
    calc_pci = pci_mj_m3 if pci_mj_m3 is not None and pci_mj_m3 > 0 else (y_ch4 * 35.88)
    
    sqrt_d = np.sqrt(max(0.1, rel_density))
    wobbe_upper_mj = calc_pcs / sqrt_d
    wobbe_upper_kwh = wobbe_upper_mj * 0.277778
    
    wobbe_lower_mj = calc_pci / sqrt_d
    wobbe_lower_kwh = wobbe_lower_mj * 0.277778
    
    if wobbe_upper_mj < 26.0:
        gas_class = "Ruw Biogas (Geschikt voor Biogas-WKK)"
        grid_compliance = "❌ Niet conform openbaar net (Biogas-kwaliteit)"
        badge_color = "orange"
    elif 26.0 <= wobbe_upper_mj < 43.5:
        gas_class = "Verrijkt Biogas / Tussenkwaliteit"
        grid_compliance = "⚠️ Tussenkwaliteit (Vereist verdere opwerking)"
        badge_color = "yellow"
    elif 43.5 <= wobbe_upper_mj <= 44.4:
        gas_class = "G-gas Kwaliteit (NL Laagcalorisch Net / Groningen)"
        grid_compliance = "🟢 Conform G-gas Distributienet (Nederland)"
        badge_color = "green"
    elif 49.0 <= wobbe_upper_mj <= 55.7:
        gas_class = "H-gas Kwaliteit (Hoogcalorisch Transportnet IT / DE / NL)"
        grid_compliance = "🟢 Conform H-gas Transportnet (Italië / Duitsland / NL)"
        badge_color = "green"
    elif 44.4 < wobbe_upper_mj < 49.0:
        gas_class = "Sub-H Kwaliteit (Overgangsgebied G- en H-gas)"
        grid_compliance = "🟡 Lichte conditionering vereist"
        badge_color = "blue"
    else:
        gas_class = "Buiten standaardspecificatie"
        grid_compliance = "🔴 Buiten tolerantiegrenzen"
        badge_color = "red"
        
    return {
        "ch4_pct": round(ch4_pct, 2),
        "co2_pct": round(y_co2 * 100.0, 2),
        "o2_pct": round(y_o2 * 100.0, 2),
        "m_gas": round(m_gas, 2),
        "relative_density_d": round(rel_density, 3),
        "pcs_mj_m3": round(calc_pcs, 2),
        "pci_mj_m3": round(calc_pci, 2),
        "pci_kwh_m3": round(calc_pci * 0.277778, 2),
        "wobbe_upper_mj_m3": round(wobbe_upper_mj, 2),
        "wobbe_upper_kwh_m3": round(wobbe_upper_kwh, 2),
        "wobbe_lower_mj_m3": round(wobbe_lower_mj, 2),
        "wobbe_lower_kwh_m3": round(wobbe_lower_kwh, 2),
        "gas_class": gas_class,
        "grid_compliance": grid_compliance,
        "badge_color": badge_color
    }

# ============================================================================
# 11. PCI / PCS THERMODYNAMICA, VOCHTBALANS & ROOKGASCONDENSATIE
# ============================================================================

def calculate_pci_pcs_moisture_balance(
    ch4_pct: float = 53.6,
    co2_pct: float = 46.42,
    temp_c: float = 38.5,
    gas_dewpoint_c: float = 4.0,
    chp_condensing_efficiency: float = 0.90
) -> Dict[str, Any]:
    p_sat_raw = 0.61078 * np.exp((17.27 * temp_c) / (temp_c + 237.3))
    x_h2o_raw = min(0.25, max(0.01, p_sat_raw / 101.325))
    h2o_g_per_nm3_raw = float((x_h2o_raw * 18.015) / 0.022414)
    
    p_sat_cooled = 0.61078 * np.exp((17.27 * gas_dewpoint_c) / (gas_dewpoint_c + 237.3))
    x_h2o_cooled = min(0.25, max(0.001, p_sat_cooled / 101.325))
    h2o_g_per_nm3_cooled = float((x_h2o_cooled * 18.015) / 0.022414)
    
    condensate_removed_g_m3 = max(0.0, h2o_g_per_nm3_raw - h2o_g_per_nm3_cooled)
    
    y_ch4_dry = max(0.01, min(1.0, ch4_pct / 100.0))
    pcs_dry_mj = y_ch4_dry * 39.82
    pci_dry_mj = y_ch4_dry * 35.89
    
    pcs_wet_raw_mj = pcs_dry_mj * (1.0 - x_h2o_raw)
    pci_wet_raw_mj = pci_dry_mj * (1.0 - x_h2o_raw)
    
    pcs_cooled_mj = pcs_dry_mj * (1.0 - x_h2o_cooled)
    pci_cooled_mj = pci_dry_mj * (1.0 - x_h2o_cooled)
    
    combustion_water_latent_mj = pcs_dry_mj - pci_dry_mj
    flue_gas_condensing_gain_kwh_m3 = (combustion_water_latent_mj * chp_condensing_efficiency) * 0.277778
    
    return {
        "temp_c": round(temp_c, 1),
        "gas_dewpoint_c": round(gas_dewpoint_c, 1),
        "x_h2o_raw_pct": round(x_h2o_raw * 100.0, 2),
        "h2o_g_per_nm3_raw": round(h2o_g_per_nm3_raw, 1),
        "x_h2o_cooled_pct": round(x_h2o_cooled * 100.0, 2),
        "h2o_g_per_nm3_cooled": round(h2o_g_per_nm3_cooled, 1),
        "condensate_removed_g_m3": round(condensate_removed_g_m3, 1),
        "pcs_dry_mj": round(pcs_dry_mj, 2),
        "pci_dry_mj": round(pci_dry_mj, 2),
        "pci_dry_kwh": round(pci_dry_mj * 0.277778, 2),
        "pcs_wet_raw_mj": round(pcs_wet_raw_mj, 2),
        "pci_wet_raw_mj": round(pci_wet_raw_mj, 2),
        "pci_wet_raw_kwh": round(pci_wet_raw_mj * 0.277778, 2),
        "pcs_cooled_mj": round(pcs_cooled_mj, 2),
        "pci_cooled_mj": round(pci_cooled_mj, 2),
        "pci_cooled_kwh": round(pci_cooled_mj * 0.277778, 2),
        "combustion_water_latent_mj": round(combustion_water_latent_mj, 2),
        "latent_heat_diff_pct": round(((pcs_dry_mj - pci_dry_mj) / max(0.1, pci_dry_mj)) * 100.0, 1),
        "flue_gas_condensing_gain_kwh_m3": round(flue_gas_condensing_gain_kwh_m3, 2)
    }

# ============================================================================
# 12. SUBSTRAAT & RECEPTOPTIMALISATIE (LEAST-COST FEED - LINEAR PROGRAMMING)
# ============================================================================

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
        if is_manure:
            bounds.append((min_manure_tons, 100.0))
        else:
            bounds.append((0.0, 60.0))
            
    # 1. Biogas opbrengst constraint
    gas_row = []
    for name in sub_names:
        sub = substrates_db[name]
        vs_pct = sub.get("vs_pct", 0.85)
        gas_yield = sub.get("biogas_m3_per_ton_odm", 450.0)
        m3_per_ton = (sub["ts_pct"] * 1000.0 * vs_pct / 1000.0) * gas_yield
        gas_row.append(-m3_per_ton)
    A_ub.append(gas_row)
    b_ub.append(-target_daily_biogas_m3)
    
    # 2. Maximale OLR constraint
    olr_row = []
    for name in sub_names:
        sub = substrates_db[name]
        vs_pct = sub.get("vs_pct", 0.85)
        kg_odm_per_ton = sub["ts_pct"] * 1000.0 * vs_pct
        olr_row.append(kg_odm_per_ton)
    A_ub.append(olr_row)
    b_ub.append(reactor_volume_m3 * max_olr)
    
    # 3. Stikstof & TAN Inhibitie Constraint
    max_allowed_n_inflow_kg = (max_tan_mg_l * reactor_volume_m3) / (max(10.0, hrt_days) * 1000.0)
    n_row = []
    for name in sub_names:
        sub = substrates_db[name]
        ts_pct = sub.get("ts_pct", 0.2)
        n_g_kg_ts = sub.get("n_g_per_kg_ts", 10.0)
        n_row.append(ts_pct * n_g_kg_ts)
    A_ub.append(n_row)
    b_ub.append(max_allowed_n_inflow_kg)
    
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
    
    optimal_diet = {}
    total_substrate_cost = 0.0
    total_gas = 0.0
    total_odm = 0.0
    total_n_kg = 0.0
    total_s_kg = 0.0
    
    if res.success:
        for i, name in enumerate(sub_names):
            tons = round(float(res.x[i]), 2)
            optimal_diet[name] = tons
            sub = substrates_db[name]
            price = substrate_prices.get(name, sub.get("price_per_ton", 0.0))
            total_substrate_cost += tons * price
            
            vs_pct = sub.get("vs_pct", 0.85)
            odm = tons * sub["ts_pct"] * vs_pct
            total_odm += odm
            total_gas += odm * sub.get("biogas_m3_per_ton_odm", 450.0)
            
            ts_pct = sub.get("ts_pct", 0.2)
            total_n_kg += tons * ts_pct * sub.get("n_g_per_kg_ts", 10.0)
            total_s_kg += tons * 1000.0 * ts_pct * (sub.get("s_g_per_kg_ts", 4.0) / 1000.0)
    else:
        for name in sub_names:
            optimal_diet[name] = 10.0 if "mest" in name.lower() else 5.0
            
    # Automatische IJzerdosering & Kostenberekening
    effective_fe_per_kg = FE_PER_KG_PRODUCT  # uit formulas.py constanten
    fe_needed_kg = (total_s_kg * FE_TO_S_RATIO * safety_margin) / effective_fe_per_kg if effective_fe_per_kg > 0 else 0.0
    fe_bags_day = int(np.ceil(fe_needed_kg / 20.0))
    fe_cost_day = fe_needed_kg * fe_product_price_per_kg
    total_combined_cost = total_substrate_cost + fe_cost_day
    estimated_tan = (total_n_kg * hrt_days) / reactor_volume_m3 * 1000.0 if reactor_volume_m3 > 0 else 0.0
            
    return {
        "success": res.success,
        "message": res.message if hasattr(res, "message") else "Geoptimaliseerd",
        "optimal_diet": optimal_diet,
        "total_substrate_cost_eur": round(total_substrate_cost, 2),
        "fe_needed_kg": round(fe_needed_kg, 1),
        "fe_bags_day": fe_bags_day,
        "fe_cost_eur": round(fe_cost_day, 2),
        "total_cost_eur": round(total_combined_cost, 2),
        "total_biogas_m3": round(total_gas, 0),
        "total_odm_kg": round(total_odm * 1000.0, 0),
        "calculated_olr": round((total_odm * 1000.0) / max(1.0, reactor_volume_m3), 2),
        "estimated_tan_mg_l": round(estimated_tan, 0),
        "total_s_kg": round(total_s_kg, 1)
    }

# ============================================================================
# 13. RED II / ISCC EU DUURZAAMHEIDS- EN EMISSIEBALANS (GHG REDUCTIE)
# ============================================================================

def calculate_red_ii_ghg_balance(
    manure_share_pct: float = 60.0,
    maize_share_pct: float = 30.0,
    industrial_waste_share_pct: float = 10.0,
    transport_distance_km: float = 25.0,
    methane_leakage_pct: float = 1.0,
    upgrade_type: str = "Membraanfiltratie"
) -> Dict[str, Any]:
    """
    Berekent de broeikasgasemissies (GHG) en reductiepercentage volgens de Europese 
    RED II richtlijn (EU 2018/2001) ten opzichte van de fossiele referentie (94.0 gCO2eq/MJ).
    """
    fossil_comparator = 94.0  # gCO2eq/MJ voor fossiele referentie
    
    ep_maize = (maize_share_pct / 100.0) * 22.5
    ep_manure = (manure_share_pct / 100.0) * -45.0  # Mestverwerking geeft vermeden emissies
    ep_waste = (industrial_waste_share_pct / 100.0) * 1.0
    ep_total = ep_maize + ep_manure + ep_waste
    
    upgrade_penalties = {
        "Membraanfiltratie": 8.5,
        "Wassiging (Water Scrubbing)": 11.0,
        "Amine-was": 9.5,
        "Geen (Alleen WKK)": 4.0
    }
    eprocess = upgrade_penalties.get(upgrade_type, 8.5)
    emethane_leak = methane_leakage_pct * 14.2
    etd = (transport_distance_km / 50.0) * 3.2
    
    total_ghg_emissions = max(1.0, ep_total + eprocess + emethane_leak + etd)
    ghg_saving_pct = ((fossil_comparator - total_ghg_emissions) / fossil_comparator) * 100.0
    is_compliant = ghg_saving_pct >= 80.0
    
    return {
        "fossil_comparator": fossil_comparator,
        "total_ghg_emissions": round(total_ghg_emissions, 2),
        "ghg_saving_pct": round(ghg_saving_pct, 1),
        "ep_total": round(ep_total, 2),
        "eprocess": round(eprocess, 2),
        "emethane_leak": round(emethane_leak, 2),
        "etd": round(etd, 2),
        "is_compliant": is_compliant,
        "compliance_status": "🟢 Voldoet aan RED II norm (>= 80% reductie)" if is_compliant else "🔴 Voldoet niet aan strenge RED II drempel"
    }
# ============================================================================
# 14. MULTI-DAY HORIZON OPTIMALISATIE (MODEL PREDICTIVE CONTROL - MPC)
# ============================================================================

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
            
    A_ub = []
    b_ub = []
    bounds = []
    
    for _ in range(horizon_days):
        for name in sub_names:
            is_manure = "mest" in name.lower() or "drijfmest" in name.lower()
            if is_manure:
                bounds.append((min_manure_tons, 100.0))
            else:
                bounds.append((0.0, 60.0))
                
    max_allowed_n_inflow_kg = (max_tan_mg_l * reactor_volume_m3) / (max(10.0, hrt_days) * 1000.0)
                
    for d in range(horizon_days):
        gas_row = [0.0] * total_vars
        for i, name in enumerate(sub_names):
            sub = substrates_db[name]
            vs_pct = sub.get("vs_pct", 0.85)
            gas_yield = sub.get("biogas_m3_per_ton_odm", 450.0)
            m3_per_ton = (sub["ts_pct"] * 1000.0 * vs_pct / 1000.0) * gas_yield
            gas_row[d * n_subs + i] = -m3_per_ton
        A_ub.append(gas_row)
        b_ub.append(-target_daily_biogas_m3)
        
        olr_row = [0.0] * total_vars
        for i, name in enumerate(sub_names):
            sub = substrates_db[name]
            vs_pct = sub.get("vs_pct", 0.85)
            kg_odm_per_ton = sub["ts_pct"] * 1000.0 * vs_pct
            olr_row[d * n_subs + i] = kg_odm_per_ton
        A_ub.append(olr_row)
        b_ub.append(reactor_volume_m3 * max_olr)
        
        n_row = [0.0] * total_vars
        for i, name in enumerate(sub_names):
            sub = substrates_db[name]
            ts_pct = sub.get("ts_pct", 0.2)
            n_row[d * n_subs + i] = ts_pct * sub.get("n_g_per_kg_ts", 10.0)
        A_ub.append(n_row)
        b_ub.append(max_allowed_n_inflow_kg)
        
        if d > 0:
            for i, name in enumerate(sub_names):
                sub = substrates_db[name]
                if sub.get("vfa_risk", 0.0) > 2.0:
                    smooth_row = [0.0] * total_vars
                    smooth_row[d * n_subs + i] = 1.0
                    smooth_row[(d - 1) * n_subs + i] = -1.0
                    A_ub.append(smooth_row)
                    b_ub.append(10.0)

    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
    
    schedule_results = []
    total_horizon_cost = 0.0
    total_horizon_substrate_cost = 0.0
    total_horizon_fe_cost = 0.0
    total_horizon_gas = 0.0
    
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
                price = substrate_prices.get(name, sub.get("price_per_ton", 0.0))
                day_sub_cost += tons * price
                
                vs_pct = sub.get("vs_pct", 0.85)
                ts_pct = sub.get("ts_pct", 0.2)
                odm = tons * ts_pct * vs_pct
                day_odm += odm
                day_gas += odm * sub.get("biogas_m3_per_ton_odm", 450.0)
                day_n += tons * ts_pct * sub.get("n_g_per_kg_ts", 10.0)
                day_s += tons * 1000.0 * ts_pct * (sub.get("s_g_per_kg_ts", 4.0) / 1000.0)
                
            fe_needed_d = (day_s * FE_TO_S_RATIO * safety_margin) / FE_PER_KG_PRODUCT
            fe_bags_d = int(np.ceil(fe_needed_d / 20.0))
            fe_cost_d = fe_needed_d * fe_product_price_per_kg
            day_total_cost = day_sub_cost + fe_cost_d
            
            total_horizon_substrate_cost += day_sub_cost
            total_horizon_fe_cost += fe_cost_d
            total_horizon_cost += day_total_cost
            total_horizon_gas += day_gas
            est_tan = (day_n * hrt_days) / reactor_volume_m3 * 1000.0
            
            schedule_results.append({
                "dag": f"Dag t+{d}" if d > 0 else "Dag t0 (Vandaag)",
                "diet": day_diet,
                "dag_sub_cost_eur": round(day_sub_cost, 2),
                "fe_bags": fe_bags_d,
                "fe_cost_eur": round(fe_cost_d, 2),
                "dag_totaal_kosten_eur": round(day_total_cost, 2),
                "dag_biogas_m3": round(day_gas, 0),
                "dag_olr": round((day_odm * 1000.0) / max(1.0, reactor_volume_m3), 2),
                "est_tan_mg_l": round(est_tan, 0),
                "dag_s_kg": round(day_s, 1)
            })
            
    return {
        "success": res.success,
        "message": res.message if hasattr(res, "message") else "MPC Geoptimaliseerd",
        "horizon_days": horizon_days,
        "total_substrate_cost_eur": round(total_horizon_substrate_cost, 2),
        "total_fe_cost_eur": round(total_horizon_fe_cost, 2),
        "total_cost_eur": round(total_horizon_cost, 2),
        "avg_daily_cost_eur": round(total_horizon_cost / horizon_days, 2),
        "total_biogas_m3": round(total_horizon_gas, 0),
        "schedule": schedule_results
    }
# ============================================================================
# 15. GEVOELIGHEIDSANALYSE & PRIJSVOLATILITEIT (SCENARIO-ANALYSE)
# ============================================================================

def calculate_substrate_sensitivity_analysis(
    substrates_db: Dict[str, Any],
    base_substrate_prices: Dict[str, float],
    target_daily_biogas_m3: float = 12000.0,
    reactor_volume_m3: float = 2500.0,
    max_olr: float = 11.5,
    target_substrate: str = "maissilage",
    price_variation_pct_range: List[float] = [-50.0, -25.0, 0.0, 25.0, 50.0, 100.0]
) -> pd.DataFrame:
    """
    Berekent de gevoeligheid van de totale dagkosten en de optimale receptuur 
    bij prijsschommelingen van een specifiek substraat (scenario-analyse).
    """
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
            diet = opt_res["optimal_diet"]
            tonnage = diet.get(target_substrate, 0.0)
            results.append({
                "Prijsvariatie (%)": pct,
                "Substraatijs (€/ton)": round(new_price, 2),
                "Ingezet Tonage (t/dag)": round(tonnage, 1),
                "Totale Dagkosten (€/dag)": opt_res["total_cost_eur"],
                "Totale Biogas (m³)": opt_res["total_biogas_m3"],
                "Berekende OLR": opt_res["calculated_olr"]
            })
            
    return pd.DataFrame(results)
def process_imported_plant_data(df: pd.DataFrame) -> dict:
    """
    Verwerkt en analyseert geüploadde plantdata (CSV/Excel).
    Retourneert een gestructureerd dictionary met KPI's en opgeschoonde data
    voor gebruik in alle andere tabbladen.
    """
    if df is None or df.empty:
        return {"status": "empty"}
    
    # Standaardiseer kolomnamen naar lowercase zonder spaties voor betrouwbare herkenning
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    summary = {
        "status": "success",
        "total_rows": len(df),
        "columns": list(df.columns),
        "raw_data": df
    }
    
    # Automatische detectie van veelvoorkomende biogas-parameters indien aanwezig in de kolommen
    for col in df.columns:
        if "h2s" in col or "sulfide" in col:
            summary["avg_h2s"] = float(df[col].mean(skipna=True))
        if "flow" in col or "debiet" in col or "gas" in col:
            summary["avg_flow"] = float(df[col].mean(skipna=True))
        if "temp" in col or "temperatuur" in col:
            summary["avg_temp"] = float(df[col].mean(skipna=True))
        if "ph" in col:
            summary["avg_ph"] = float(df[col].mean(skipna=True))
            
    return summary
def calculate_recipe_totals(df):
    """
    Berekent de totale tonnages, gewogen drogestof (DS), organische drogestof (oDS) 
    en de totale verwachte biogasproductie (m³/dag) uit het substraatrecept.
    """
    if df.empty or "Tonnage (ton/dag)" not in df.columns:
        return 0.0, 0.0, 0.0, 0.0

    total_tonnage = df["Tonnage (ton/dag)"].sum()
    if total_tonnage <= 0:
        return 0.0, 0.0, 0.0, 0.0
    
    weighted_ds = (df["Tonnage (ton/dag)"] * df["DS (%)"]).sum() / total_tonnage
    weighted_ods = (df["Tonnage (ton/dag)"] * df["oDS (% oDS)"]).sum() / total_tonnage
    total_biogas = (df["Tonnage (ton/dag)"] * df["Biogaspotentieel (m³/ton)"]).sum()
    
    return total_tonnage, weighted_ds, weighted_ods, total_biogas

def calculate_organic_loading_rate(total_tonnage, ds_pct, ods_pct, volume_m3):
    """
    Berekent de organische belasting in kg oDS / m³·dag.
    """
    if volume_m3 <= 0 or total_tonnage <= 0:
        return 0.0
    
    kg_ods_day = total_tonnage * (ds_pct / 100.0) * (ods_pct / 100.0) * 1000.0
    return kg_ods_day / volume_m3

def calculate_h2s_dosages(flow_m3_h, h2s_raw_ppm, temp_c, fe_ratio, sbg_product):
    """
    Berekent de H2S vracht, benodigd actief Fe en de SBG additiefdosering.
    """
    product_factors = {"SBG agro": 1.0, "SBG energo": 0.90, "SBG industrial": 0.80}
    active_factor = product_factors.get(sbg_product, 1.0)

    daily_biogas = flow_m3_h * 24.0
    molar_volume_t = 0.0224 * ((temp_c + 273.15) / 273.15)
    mol_h2s = (daily_biogas * (h2s_raw_ppm / 1_000_000.0)) / molar_volume_t
    
    mass_h2s_kg = mol_h2s * 34.08 / 1000.0
    mass_fe_needed = mol_h2s * fe_ratio * 55.845 / 1000.0
    total_dose = mass_fe_needed * active_factor * 2.5

    return mass_h2s_kg, mass_fe_needed, total_dose