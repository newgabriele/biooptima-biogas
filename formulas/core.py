"""
formulas/core.py - Constanten, fysisch-chemische evenwichten, DM-balans,
Wobbe-Index, PCI/PCS Thermodynamica, RED II en FOS/TAC Soft-Sensor.
"""

from dataclasses import dataclass
from typing import Any, Dict
import numpy as np

M_S = 32.065
M_FE = 55.845
M_FE2O3 = 159.69
M_FEO = 71.844

FRAC_FE2O3 = 0.35
FRAC_FEO = 0.35

FE_PER_KG_PRODUCT = (FRAC_FE2O3 * (2 * M_FE / M_FE2O3)) + (FRAC_FEO * (M_FE / M_FEO))
FE_TO_S_RATIO = M_FE / M_S

@dataclass
class PlantProfile:
    name: str = "Standaard Installatie"
    inst_type: str = "agro"
    temp_regime: str = "Mesofiel"  # "Mesofiel" of "Thermofiel"
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

def calculate_fos_tac_soft_sensor(
    vfa_risk_load: float,
    olr: float,
    tan_mg_l: float,
    ph: float,
    base_fos: float = 2000.0
) -> Dict[str, Any]:
    tac = max(1500.0, (tan_mg_l * 1.8) + 1500.0)
    fos = max(500.0, base_fos + (vfa_risk_load * 250.0) + (max(0.0, olr - 3.0) * 150.0))
    
    if ph < 7.4:
        tac *= max(0.6, (ph / 7.4))
        fos *= (1.0 + (7.4 - ph) * 0.5)

    fos_tac_ratio = fos / tac
    if fos_tac_ratio < 0.30:
        status = "🟢 Stabiel biologisch evenwicht (FOS/TAC < 0.30)"
        level = "stable"
    elif 0.30 <= fos_tac_ratio <= 0.45:
        status = "⚠️ Waarschuwing: Lichte verzuringsdruk (0.30 - 0.45)"
        level = "warning"
    else:
        status = "🛑 Kritiek: Ernstige verzuringsdreiging (FOS/TAC > 0.45)"
        level = "critical"

    return {
        "fos_mg_l": round(fos, 0),
        "tac_mg_l": round(tac, 0),
        "fos_tac_ratio": round(fos_tac_ratio, 2),
        "status_text": status,
        "level": level
    }

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
    
    m_gas = (y_ch4 * 16.043) + (y_co2 * 44.010) + (y_o2 * 31.999) + (y_n2 * 28.013)
    rel_density = m_gas / 28.964
    
    calc_pcs = pcs_mj_m3 if pcs_mj_m3 is not None and pcs_mj_m3 > 0 else (y_ch4 * 39.82)
    calc_pci = pci_mj_m3 if pci_mj_m3 is not None and pci_mj_m3 > 0 else (y_ch4 * 35.88)
    
    sqrt_d = np.sqrt(max(0.1, rel_density))
    wobbe_upper_mj = calc_pcs / sqrt_d
    wobbe_upper_kwh = wobbe_upper_mj * 0.277778
    wobbe_lower_mj = calc_pci / sqrt_d
    wobbe_lower_kwh = wobbe_lower_mj * 0.277778
    
    if wobbe_upper_mj < 26.0:
        gas_class = "Ruw Biogas (Geschikt voor Biogas-WKK)"
        grid_compliance = "❌ Niet conform openbaar net"
        badge_color = "orange"
    elif 26.0 <= wobbe_upper_mj < 43.5:
        gas_class = "Verrijkt Biogas / Tussenkwaliteit"
        grid_compliance = "⚠️ Tussenkwaliteit"
        badge_color = "yellow"
    elif 43.5 <= wobbe_upper_mj <= 44.4:
        gas_class = "G-gas Kwaliteit (NL Laagcalorisch Net)"
        grid_compliance = "🟢 Conform G-gas Distributienet"
        badge_color = "green"
    elif 49.0 <= wobbe_upper_mj <= 55.7:
        gas_class = "H-gas Kwaliteit (Transportnet IT/DE/NL)"
        grid_compliance = "🟢 Conform H-gas Transportnet"
        badge_color = "green"
    else:
        gas_class = "Sub-H Kwaliteit"
        grid_compliance = "🟡 Lichte conditionering vereist"
        badge_color = "blue"
        
    return {
        "ch4_pct": round(ch4_pct, 2),
        "co2_pct": round(y_co2 * 100.0, 2),
        "o2_pct": round(y_o2 * 100.0, 2),
        "m_gas": round(m_gas, 2),
        "relative_density_d": round(rel_density, 3),
        "pcs_mj_m3": round(calc_pcs, 2),
        "pci_mj_m3": round(calc_pci, 2),
        "wobbe_upper_mj_m3": round(wobbe_upper_mj, 2),
        "wobbe_upper_kwh_m3": round(wobbe_upper_kwh, 2),
        "gas_class": gas_class,
        "grid_compliance": grid_compliance,
        "badge_color": badge_color
    }

def calculate_red_ii_ghg_balance(
    manure_share_pct: float = 60.0,
    maize_share_pct: float = 30.0,
    industrial_waste_share_pct: float = 10.0,
    transport_distance_km: float = 25.0,
    methane_leakage_pct: float = 1.0,
    upgrade_type: str = "Membraanfiltratie"
) -> Dict[str, Any]:
    fossil_comparator = 94.0
    ep_maize = (maize_share_pct / 100.0) * 22.5
    ep_manure = (manure_share_pct / 100.0) * -45.0
    ep_waste = (industrial_waste_share_pct / 100.0) * 1.0
    ep_total = ep_maize + ep_manure + ep_waste
    
    upgrade_penalties = {"Membraanfiltratie": 8.5, "Wassiging (Water Scrubbing)": 11.0, "Amine-was": 9.5, "Geen (Alleen WKK)": 4.0}
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
        "is_compliant": is_compliant,
        "compliance_status": "🟢 Voldoet aan RED II norm (>= 80% reductie)" if is_compliant else "🔴 Voldoet niet aan RED II drempel"
    }