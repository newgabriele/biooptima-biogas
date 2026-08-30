def calculate_red_ii_ghg_balance(
    manure_share_pct,
    maize_share_pct,
    industrial_waste_share_pct,
    transport_distance_km,
    methane_leakage_pct,
    upgrade_type
):
    fossil_comparator = 94.0 # g CO2eq / MJ
    
    # Teelt- en grondstofemissies
    ep_total = (maize_share_pct * 18.5 + manure_share_pct * (-4.5) + industrial_waste_share_pct * 2.0) / 100.0
    
    # Energiebelasting per opwerkingstechnologie
    upgrade_penalties = {
        "Membraanfiltratie": 8.5,
        "Wassiging (Water Scrubbing)": 11.0,
        "Amine-was": 14.0,
        "Geen (Alleen WKK)": 5.0
    }
    eprocess = upgrade_penalties.get(upgrade_type, 9.0)
    
    # Methaanlek-emissies
    emethane_leak = methane_leakage_pct * 28.0 * 0.35
    
    # Transport logistiek (etd)
    etd = transport_distance_km * 0.12
    
    total_ghg_emissions = ep_total + eprocess + emethane_leak + etd
    ghg_saving_pct = max(0.0, ((fossil_comparator - total_ghg_emissions) / fossil_comparator) * 100.0)
    
    if ghg_saving_pct >= 80.0:
        compliance_status = "✅ **Volledige naleving RED III / ISCC EU:** De installatie behaalt een broeikasgasreductie van **≥ 80%**."
    elif ghg_saving_pct >= 65.0:
        compliance_status = "⚠️ **Naleving RED II:** De installatie behaalt een reductie van **≥ 65%**, maar haalt de strengere RED III norm van 80% nog niet."
    else:
        compliance_status = "❌ **Niet conform:** De reductie blijft onder de minimale drempelwaarde van 65%."
        
    return {
        "total_ghg_emissions": round(total_ghg_emissions, 2),
        "fossil_comparator": fossil_comparator,
        "ghg_saving_pct": round(ghg_saving_pct, 1),
        "eprocess": round(eprocess, 2),
        "ep_total": round(ep_total, 2),
        "emethane_leak": round(emethane_leak, 2),
        "etd": round(etd, 2),
        "compliance_status": compliance_status
    }