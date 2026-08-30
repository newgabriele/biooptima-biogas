# formulas/optimization.py

def optimize_dosage_cost(biogas_flow_m3_h, h2s_in=1500, h2s_target=150):
    """Optimaliseert de doseringskosten en producthoeveelheid voor ijzeroxide additieven."""
    daily_flow = biogas_flow_m3_h * 24
    s_load_kg = daily_flow * (h2s_in / 1e6) * 1.34
    product_kg = s_load_kg * 2.5
    cost_per_kg = 1.20
    daily_cost = product_kg * cost_per_kg
    return {
        "daily_product_kg": round(product_kg, 2),
        "daily_cost_eur": round(daily_cost, 2),
        "residual_h2s": h2s_target
    }

def calculate_economic_return(biogas_flow_m3_h, biogas_price_per_m3=0.68, dosage_cost_eur=50.0):
    """Berekent het netto rendement op basis van biogasopbrengst en doseringskosten."""
    monthly_gas_volume = biogas_flow_m3_h * 24 * 30.5
    gross_revenue = monthly_gas_volume * biogas_price_per_m3
    monthly_dosage_cost = dosage_cost_eur * 30.5
    net_return = gross_revenue - monthly_dosage_cost
    return {
        "monthly_gas_volume_m3": round(monthly_gas_volume, 2),
        "gross_revenue_eur": round(gross_revenue, 2),
        "monthly_dosage_cost_eur": round(monthly_dosage_cost, 2),
        "net_return_eur": round(net_return, 2)
    }