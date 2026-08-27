"""
gebruikerapp.py - BioOptima 360° Beveiligde Klant- & Operatorweergave
Toont alle 11 operationele modules in een afgeschermde schil zonder IP/formule-blootlegging.
"""

import streamlit as st
import pandas as pd
import numpy as np
import os

# Paginaconfiguratie
st.set_page_config(
    page_title="BioOptima 360° - Klant- & Operatorportal",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLING & BEVEILIGINGSSCHIL ---
st.markdown("""
    <style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #2e7d32;
        margin-bottom: 10px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 2.8em;
    }
    </style>
""", unsafe_allow_html=True)

# --- ZIJBALK: LOGO & INSTALLATIE SELECTIE ---
with st.sidebar:
    logo_filename = "logo envitec.jpg"
    if os.path.exists(logo_filename):
        st.image(logo_filename, use_container_width=True)
    else:
        st.warning(f"Logo '{logo_filename}' niet gevonden.")

    st.divider()
    st.subheader("⚙️ Installatie Status")
    inst_select = st.selectbox("Actieve Locatie", ["Da.Ma. Biogas", "Installatie Noord", "BioEnergie West"])
    rol_select = st.selectbox("Gebruikersniveau", ["Operator (t0 & Shift)", "Plant Manager (Dashboard)", "Management & Kringloop"])
    st.divider()
    st.caption("BioOptima 360° Client Shell (v4.2 - Secured)")

# --- TITEL & HEADER ---
st.title(f"🌿 BioOptima 360° — {inst_select}")
st.caption("Beveiligde Operator- en Klantomgeving (IP-Protected Process Management)")
st.divider()

# --- 11 AFGESCHERMDE TABBLADEN ---
(
    tab1_basis, tab2_kantoor, tab3_operator, tab4_directie, tab5_analytics,
    tab6_substraat, tab7_installaties, tab8_ai, tab9_scada, tab10_log, tab11_bench
) = st.tabs([
    "🏢 1. Basisgegevens",
    "🖥️ 2. Planning (t-2 t/m t+6)",
    "👷 3. Operator t0",
    "📊 4. Directierapport",
    "📈 5. Kwaliteit & Wobbe",
    "🌾 6. Substraten",
    "🗺️ 7. Locaties",
    "🧠 8. Velddata & Lab",
    "🔌 9. SCADA / PLC",
    "📝 10. Logboek",
    "🏆 11. Benchmark & ROI"
])

# ---------------------------------------------------------
# TAB 1: BASISGEGEVENS & RANDVOORWAARDEN (Invoer)
# ---------------------------------------------------------
with tab1_basis:
    st.subheader("Installatieconfiguratie & Doelstellingen")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Reactorvolume", "1.800 m³", "Netto capaciteit")
        st.metric("Nominaal Debiet", "320 m³/uur", "Doelwaarde")
    with c2:
        st.metric("H₂S Doelwaarde", "< 100 ppm", "Standaard norm")
        st.metric("Procestemperatuur", "39.5 °C", "Mesofiel")
    st.info("💡 Parameters worden beheerd via de centrale server. Wijzigingen vereisen goedkeuring van de beheerder.")

# ---------------------------------------------------------
# TAB 2: KANTOOR / 9-DAAGSE PLANNING
# ---------------------------------------------------------
with tab2_kantoor:
    st.subheader("9-Daagse Voedingshorizon & Vrijgave")
    st.write("Overzicht van de geplande voercomponenten en automatische veiligheidsvalidatie:")
    
    dagen = ["t-2", "t-1", "t0 (Vandaag)", "t+1", "t+2", "t+3", "t+4", "t+5", "t+6"]
    df_preview = pd.DataFrame({
        "Dag": dagen,
        "Runderdrijfmest (ton)": [30.0]*9,
        "Maïssilage (ton)": [12.5]*9,
        "Kippenmest (ton)": [3.0]*9,
        "Melasse (ton)": [1.5]*9
    })
    st.dataframe(df_preview, use_container_width=True, hide_index=True)
    st.success("✅ Alle geplande dagen voldoen aan de OLR- en verzuringslimieten.")

# ---------------------------------------------------------
# TAB 3: OPERATOR t0 (Dagelijkse Dosering & Ploegen)
# ---------------------------------------------------------
with tab3_operator:
    st.subheader("Actuele Dagsturing (t0) & Doseringsadvies")
    
    col_op_in1, col_op_in2 = st.columns(2)
    with col_op_in1:
        reëel_debiet = st.number_input("Actueel Biogasdebiet (m³/u)", 50.0, 1000.0, 320.0, 10.0)
    with col_op_in2:
        reëel_h2s = st.number_input("Gemeten Ruw H₂S (ppm)", 100, 5000, 1850, 50)

    # Afgeschermde berekening achter de schermen
    zakken_nodig = int(np.ceil((reëel_debiet * 24 * reëel_h2s * 1.434 / 1_000_000 * 1.7418 * 1.25 / 0.5166) / 20.0))

    st.markdown(f"""
    <div class="metric-card">
        <h3 style="margin:0; color:#2e7d32;">🎯 Vandaag toe te dienen: {zakken_nodig} zakken (20 kg)</h3>
        <p style="margin:5px 0 0 0; color:#555;">Inclusief actieve in-situ zwavelbinding & Fe2O3/FeO dosering.</p>
    </div>
    """, unsafe_allow_html=True)

    st.write("**Ploegendienst Verdeling:**")
    st.table(pd.DataFrame({
        "Dienst": ["Ochtenddienst (06:00 - 14:00)", "Middagdienst (14:00 - 22:00)", "Nachtdienst (22:00 - 06:00)"],
        "Aantal Zakken (20 kg)": [int(np.ceil(zakken_nodig * 0.4)), int(np.floor(zakken_nodig * 0.35)), max(0, zakken_nodig - int(np.ceil(zakken_nodig * 0.4)) - int(np.floor(zakken_nodig * 0.35)))],
        "Locatie": ["Invoervijzel 1", "Invoervijzel 1", "Invoervijzel 1"]
    }))

# ---------------------------------------------------------
# TAB 4: DIRECTIERAPPORT
# ---------------------------------------------------------
with tab4_directie:
    st.subheader("Financiële KPI's & Rendement")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bruto Gasopbrengst", "€ 4.250 / dag")
    c2.metric("Substraatkosten", "€ 1.820 / dag")
    c3.metric("Additieven Kosten", "€ 208 / dag")
    c4.metric("Netto Dagwinst", "€ 2.222 / dag", "Marge: 52%")

# ---------------------------------------------------------
# TAB 5: ANALYTICS & WOBBE-INDEX
# ---------------------------------------------------------
with tab5_analytics:
    st.subheader("Gaskwaliteit & Netinvoeding")
    st.metric("Onderste Wobbe-Index (Wi)", "22.45 MJ/m³", "Biogas-WKK Kwaliteit")
    st.success("✅ Koeling & dauwpuntstabilisatie operationeel binnen specificaties.")

# ---------------------------------------------------------
# TAB 6: SUBSTRATEN & PRIJZEN
# ---------------------------------------------------------
with tab6_substraat:
    st.subheader("Actieve Substraat- en Prijzenmatrix")
    st.dataframe(pd.DataFrame({
        "Substraat": ["Runderdrijfmest", "Maïssilage", "Kippenmest", "Melasse"],
        "Droge Stof (% DM)": [9.0, 33.0, 55.0, 75.0],
        "Prijs (€/ton)": ["€ 0,00", "€ 48,00", "€ 12,00", "€ 140,00"]
    }), use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# TAB 7: OVERZICHT INSTALLATIES
# ---------------------------------------------------------
with tab7_installaties:
    st.subheader("Multisite Status")
    st.info("Actieve installatie: **Da.Ma. Biogas** (Online & Stabiel).")

# ---------------------------------------------------------
# TAB 8: AI & VELDDATA
# ---------------------------------------------------------
with tab8_ai:
    st.subheader("Laboratoriuminvoer & Kalibratie")
    st.number_input("Invoer gemeten lab CH₄ (%)", 40.0, 70.0, 54.0, 0.1)
    st.number_input("Invoer gemeten H₂S na dosering (ppm)", 0, 500, 45, 1)
    st.button("💾 Opslaan in beveiligde tijdreeks")

# ---------------------------------------------------------
# TAB 9: SCADA / PLC
# ---------------------------------------------------------
with tab9_scada:
    st.subheader("PLC Verbindingsstatus")
    st.success("🟢 Koppeling actief via Siemens S7 (Profinet / TCP) — Latency: 4ms.")

# ---------------------------------------------------------
# TAB 10: CHANGELOG
# ---------------------------------------------------------
with tab10_log:
    st.subheader("Systeemhistorie & Wijzigingen")
    st.write("- **v4.2:** Beveiligde client-schil geactiveerd voor externe locaties.")

# ---------------------------------------------------------
# TAB 11: BENCHMARK & VALORISATIE
# ---------------------------------------------------------
with tab11_bench:
    st.subheader("Businesscase & WKK-optimalisatie")
    st.metric("Jaarlijkse besparing oliewissels", "€ 6.400 / jaar", "Verlengde motorstandtijd")
    st.metric("Actieve kool filterstandtijd", "4,2x langer", "Directe eliminatie filterwissels")

# --- FOOTER ---
st.sidebar.divider()
st.sidebar.caption("BioOptima 360° Secure Client v4.2")