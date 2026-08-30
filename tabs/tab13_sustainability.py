# tabs/tab13_sustainability.py
import streamlit as st
import pandas as pd
from formulas import calculate_red_ii_ghg_balance

def render():
    st.subheader("🇪🇺 RED II / ISCC EU Duurzaamheids- & Emissiebalans (ESG)")
    
    # Duidelijk aangeven voor welke actieve installatie de berekening geldt
    if "active_plant" in st.session_state and st.session_state.active_plant:
        plant = st.session_state.active_plant
        st.info(f"📍 **Actieve Installatie voor deze emissiebalans:** `{plant.name}` (Type: {plant.inst_type}, Debiet: {plant.biogas_flow_m3_h} m³/h, Volume: {plant.volume_m3} m³)")
    else:
        st.warning("⚠️ Geen specifieke installatie geselecteerd via het Motherboard. De berekening gebruikt de standaard referentiewaarden.")

    st.markdown("Bereken de broeikasgasreductie (GHG) en controleer de naleving van de Europese duurzaamheidscriteria voor biomethaan.")

    col1, col2 = st.columns(2)
    with col1:
        manure_pct = st.slider("Aandeel Drijfmest / Reststromen (%)", 0.0, 100.0, 60.0, 5.0, key="red_manure_share")
        maize_pct = st.slider("Aandeel Maïs / Teeltgewassen (%)", 0.0, 100.0, 30.0, 5.0, key="red_maize_share")
        waste_pct = st.slider("Aandeel Industrieel Afval (%)", 0.0, 100.0, 10.0, 5.0, key="red_waste_share")
    with col2:
        transport_km = st.number_input("Gemiddelde Transportafstand Substraat (km)", 5.0, 200.0, 25.0, 5.0, key="red_transport_dist")
        methane_leak = st.slider("Methaanverlekkingspercentage (%)", 0.1, 5.0, 1.0, 0.1, key="red_methane_leak")
        upgrade_tech = st.selectbox("Opwerkingstechnologie", ["Membraanfiltratie", "Wassiging (Water Scrubbing)", "Amine-was", "Geen (Alleen WKK)"], key="red_upgrade_tech")

    if st.button("📊 Bereken RED II Emissiebalans", key="calc_red_btn"):
        res = calculate_red_ii_ghg_balance(
            manure_share_pct=manure_pct,
            maize_share_pct=maize_pct,
            industrial_waste_share_pct=waste_pct,
            transport_distance_km=transport_km,
            methane_leakage_pct=methane_leak,
            upgrade_type=upgrade_tech
        )

        st.markdown("---")
        if "active_plant" in st.session_state and st.session_state.active_plant:
            st.markdown(f"**Validatierapport voor installatie:** `{st.session_state.active_plant.name}`")
        
        st.markdown(res["compliance_status"])

        m1, m2, m3 = st.columns(3)
        m1.metric("Totale Ketenemissie", f"{res['total_ghg_emissions']:.1f} gCO₂eq/MJ", f"Fossiel: {res['fossil_comparator']} g")
        m2.metric("GHG Reductiepercentage", f"{res['ghg_saving_pct']:.1f}%", "Norm: ≥ 80%")
        m3.metric("Proces- & Opwerkingsbelasting", f"{res['eprocess']:.1f} gCO₂eq/MJ")

        st.markdown("### 📋 Emissie-opbouw per Categorie")
        breakdown_df = pd.DataFrame([
            {"Emissiebron": "Teelt & Grondstofkrediet (ep)", "Waarde (gCO₂eq/MJ)": res["ep_total"]},
            {"Emissiebron": "Opwerking & Energiegebruik", "Waarde (gCO₂eq/MJ)": res["eprocess"]},
            {"Emissiebron": "Methaanlek-emissies", "Waarde (gCO₂eq/MJ)": res["emethane_leak"]},
            {"Emissiebron": "Transport logistiek (etd)", "Waarde (gCO₂eq/MJ)": res["etd"]}
        ])
        st.dataframe(breakdown_df, use_container_width=True, hide_index=True)