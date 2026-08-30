# tabs/tab6_substrates.py
import streamlit as st
import pandas as pd
from formulas import optimize_least_cost_recipe

def render():
    st.subheader("🌾 Substraat- en Recepturenoptimalisatie (Least-Cost Feed)")
    st.markdown("Bereken automatisch de meest kostenefficiënte dagelijkse voermix op basis van marktprijzen en procesgrenzen.")

    if "substrates_db" not in st.session_state:
        st.session_state.substrates_db = {
            "runderdrijfmest": {"ts_pct": 0.09, "vs_pct": 0.75, "s_g_per_kg_ts": 4.0, "biogas_m3_per_ton_odm": 350.0, "price_per_ton": -5.0, "f_fast": 0.2, "f_med": 0.5, "f_slow": 0.3, "vfa_risk": 0.5},
            "maissilage": {"ts_pct": 0.33, "vs_pct": 0.95, "s_g_per_kg_ts": 1.5, "biogas_m3_per_ton_odm": 620.0, "price_per_ton": 48.0, "f_fast": 0.5, "f_med": 0.4, "f_slow": 0.1, "vfa_risk": 2.5},
            "kippenmest": {"ts_pct": 0.55, "vs_pct": 0.80, "s_g_per_kg_ts": 12.0, "biogas_m3_per_ton_odm": 480.0, "price_per_ton": 12.0, "f_fast": 0.6, "f_med": 0.3, "f_slow": 0.1, "vfa_risk": 4.0},
            "melasse": {"ts_pct": 0.75, "vs_pct": 0.98, "s_g_per_kg_ts": 0.8, "biogas_m3_per_ton_odm": 750.0, "price_per_ton": 120.0, "f_fast": 0.9, "f_med": 0.1, "f_slow": 0.0, "vfa_risk": 6.0}
        }

    st.markdown("### 💶 Actuele Marktprijzen & Substraatbeheer")
    prices_col1, prices_col2 = st.columns(2)
    
    updated_prices = {}
    items = list(st.session_state.substrates_db.items())
    with prices_col1:
        for sub, meta in items[:2]:
            updated_prices[sub] = st.number_input(f"Prijs {sub.replace('_', ' ').title()} (€/ton)", -50.0, 200.0, float(meta.get("price_per_ton", 0.0)), 1.0, key=f"price_{sub}")
    with prices_col2:
        for sub, meta in items[2:]:
            updated_prices[sub] = st.number_input(f"Prijs {sub.replace('_', ' ').title()} (€/ton)", -50.0, 200.0, float(meta.get("price_per_ton", 0.0)), 1.0, key=f"price_{sub}")

    st.markdown("---")
    st.markdown("### ⚙️ Optimalisatie Parameters")
    opt_col1, opt_col2 = st.columns(2)
    with opt_col1:
        target_gas = st.number_input("Doel Biogasproductie (m³/dag)", 5000.0, 30000.0, 12000.0, 500.0, key="opt_target_gas")
    with opt_col2:
        max_olr_limit = st.number_input("Maximale OLR (kg ODM/m³·d)", 5.0, 15.0, 11.5, 0.5, key="opt_max_olr")

    if st.button("🚀 Bereken Meest Kostenefficiënte Receptuur", key="btn_calc_recipe"):
        result = optimize_least_cost_recipe(
            substrates_db=st.session_state.substrates_db,
            substrate_prices=updated_prices,
            target_daily_biogas_m3=target_gas,
            reactor_volume_m3=2500.0,
            max_olr=max_olr_limit
        )

        if result["success"]:
            st.success("✅ Optimale voermix succesvol berekend via Linear Programming!")
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Totale Substraatkosten", f"€ {result['total_cost_eur']:,.2f} / dag")
            m2.metric("Geproduceerd Biogas", f"{result['total_biogas_m3']:,.0f} m³/dag")
            m3.metric("Organische Belasting (OLR)", f"{result['calculated_olr']:.2f} kg ODM/m³·d")
            m4.metric("Totale ODM Vracht", f"{result['total_odm_kg']:,.0f} kg ODM/dag")

            st.markdown("### 📋 Optimale Dagelijkse Receptuur")
            opt_df = pd.DataFrame([
                {"Substraat": k.replace("_", " ").title(), "Optimale Tonage (ton/dag)": v, "Marktprijs (€/ton)": updated_prices[k], "Dagkosten (€)": round(v * updated_prices[k], 2)}
                for k, v in result["optimal_diet"].items()
            ])
            st.dataframe(opt_df, use_container_width=True, hide_index=True)
        else:
            st.error("⚠️ Geen sluitende oplossing gevonden binnen de huidige grenswaarden. Pas de marktprijzen of de OLR-limiet aan.")