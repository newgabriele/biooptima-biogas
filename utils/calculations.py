# utils/calculations.py
import pandas as pd

TARGET_BIOGAS_FLOW = 500.0  # m3/h

def calculate_process_metrics(active_recipe_df, reactor_vol, gas_stripping_factor, temp_regime="Mesofiel (~38°C)"):
    
    if "Thermofiel" in temp_regime:
        odm_efficiency_factor = 1.05  
        max_safe_olr = 5.2            
        min_safe_hrt = 15.0           
    else:
        odm_efficiency_factor = 1.00  
        max_safe_olr = 4.5
        min_safe_hrt = 22.0           
        
    total_substraat = 0.0
    total_odm_load = 0.0
    total_s_load_kg = 0.0
    total_dry_mass_kg = 0.0
    
    for _, row in active_recipe_df.iterrows():
        ton = row["ton/d"]
        dm_pct = row["DM %"]
        dm = dm_pct / 100.0
        odm = row["ODM %"] / 100.0
        s_pct = row["S %"] / 100.0
        recirc_pct = row["Recirc. %"]  # Percentage (bijv. 40.0)
        recirc_frac = recirc_pct / 100.0
        
        # Effectieve DM na correctie van het recirculatiepercentage
        eff_dm = dm * (1.0 - 0.35 * recirc_frac)
        
        ton_odm_per_day = ton * 1000.0 * eff_dm * odm
        sulfur_from_sub = (ton * 1000.0) * eff_dm * s_pct
        dry_mass_sub = (ton * 1000.0) * eff_dm
        
        total_substraat += ton
        total_odm_load += ton_odm_per_day
        total_s_load_kg += sulfur_from_sub
        total_dry_mass_kg += dry_mass_sub

    current_olr = total_odm_load / reactor_vol if reactor_vol > 0 else 0.0
    
    daily_liquid_flow = total_substraat if total_substraat > 0 else 1.0
    current_hrt = reactor_vol / daily_liquid_flow
    
    base_biogas_m3_day = total_odm_load * 0.6 * odm_efficiency_factor * gas_stripping_factor
    calc_biogas = base_biogas_m3_day / 24.0
    
    avg_dm = (total_dry_mass_kg / (total_substraat * 1000.0) * 100.0) if total_substraat > 0 else 0.0
    current_vzv = (current_olr / max_safe_olr) * 35.0

    product_needed_kg = max(5.0, total_s_load_kg * 0.35 * (1.0 / gas_stripping_factor))
    bags_needed_day = product_needed_kg / 25.0

    return {
        "current_olr": current_olr,
        "current_vzv": current_vzv,
        "avg_dm": avg_dm,
        "calc_biogas": calc_biogas,
        "total_substraat": total_substraat,
        "product_needed": product_needed_kg,
        "bags_needed": bags_needed_day,
        "max_safe_olr": max_safe_olr,
        "current_hrt": current_hrt,
        "min_safe_hrt": min_safe_hrt
    }