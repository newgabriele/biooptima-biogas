import streamlit as st
import pandas as pd
import numpy as np

# --- PAGINA CONFIGURATIE VOOR MOBIEL ---
st.set_page_config(
    page_title="BioOptima 360° Mobile",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Schone mobiele opmaak
st.markdown("""
    <style>
    .main {
        padding: 0rem 0rem;
    }
    h1 {
        font-size: 1.4rem !important;
    }
    h2 {
        font-size: 1.2rem !important;
    }
    h3 {
        font-size: 1.0rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. ROL SELECTIE VOOR MOBIEL (ZIJBALK) ---
st.sidebar.title("BioOptima 360°")
st.sidebar.markdown("*Procesoptimalisatie & Monitoring*")
st.sidebar.divider()

rol = st.sidebar.selectbox(
    "Selecteer gebruikersniveau:",
    [
        "Niveau 1: Operator (Shift & Actie)", 
        "Niveau 2: Kantoor (9-daags Overzicht)", 
        "Niveau 3: Management (Benchmark)"
    ]
)

st.sidebar.divider()
st.sidebar.info("💡 **Mobiele modus:** Schakel hierboven snel tussen de verschillende organisatielagen.")

# --- 2. WEERGAVE OP BASIS VAN GEKOZEN ROL ---

# --- NIVEAU 1: OPERATOR (Shift Instructies - voormalige Tab 3 logica) ---
if rol == "Niveau 1: Operator (Shift & Actie)":
    st.subheader("🛠️ Operator Dashboard")
    st.caption("Operationele processtatus en shift-instructies.")
    
    # Kernmeters
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Biogas Debiet", value="500 m³/u", delta="Nominaal")[cite: 1]
    with col2:
        st.metric(label="Reactor Temp", value="52.4 °C", delta="Stabiel")
        
    st.divider()
    
    st.write("### 📋 Shift Instructies (Vandaag)")
    st.success("✅ **Systeemstatus:** Biogasproductie stabiel op 500 m³/u[cite: 1].")
    st.warning("⚠️ **Actiepunt:** Doseer ijzerhydroxide voor directe H2S-binding en houd de Fe2O3 en FeO mix (beide op 35%) nauwlettend in de gaten[cite: 1].")
    
    with st.expander("🔍 Bekijk parameters & dosering"):
        st.write("- **H2S Doelwaarde:** < 150 ppm")
        st.write("- **Fe2O3 aandeel:** 35%[cite: 1]")
        st.write("- **FeO aandeel:** 35%[cite: 1]")
        st.write("- **Electron transfer (Magnetriet):** Actief")

# --- NIVEAU 2: KANTOOR (9-daags overzicht - voormalige Tab 2 logica) ---
elif rol == "Niveau 2: Kantoor (9-daags Overzicht)":
    st.subheader("📊 Kantoor & Technisch Overzicht")
    st.caption("9-daagse prognose en processturing.")
    
    st.write("### 📈 9-daags Prognoseoverzicht")
    
    # Gegenereerde 9-daagse data
    dagen = [Tag for Tag in [f"Dag {i}" for i in range(1, 10)]]
    prognose_df = pd.DataFrame({
        "Biogas Debiet (m³/u)": [500, 510, 495, 520, 505, 515, 510, 525, 530],[cite: 1]
        "Belasting (OLR)": [480, 490, 485, 500, 495, 505, 500, 510, 515]
    }, index=dagen)
    
    st.line_chart(prognose_df)
    
    st.divider()
    st.write("### ⚙️ Substraat & Additieven Balans")
    
    sub_table = pd.DataFrame({
        "Component": ["Maissilage", "Drijfmest", "Fe2O3", "FeO"],
        "Percentage": ["--", "--", "35%", "35%"],[cite: 1]
        "Rol in Proces": ["Hoofdsubstraat", "Basis", "H2S Binding", "Elektronenflow"]
    })
    st.table(sub_table)

# --- NIVEAU 3: MANAGEMENT (Benchmark - voormalige Tab 11 logica) ---
elif rol == "Niveau 3: Management (Benchmark)":
    st.subheader("📈 Management Dashboard")
    st.caption("Strategische KPI's en rendement benchmark.")
    
    # KPI metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Efficiëntie", "94.2%", "+1.5%")
    col2.metric("Rendement", "€ 1.24/m³", "-€0.02")
    col3.metric("Uptime", "99.1%", "Optimaal")
    
    st.divider()
    
    st.write("### 🏆 Benchmark Overzicht")
    st.info("Vergelijking van de prestaties ten opzichte van de installatiedoelstellingen.")
    
    # Benchmark bar chart simulatie
    benchmark_df = pd.DataFrame({
        "Doelstelling": [500, 500, 500, 500, 500],[cite: 1]
        "Reëel": [490, 505, 512, 498, 515]
    }, index=["Locatie 1", "Locatie 2", "Locatie 3", "Locatie 4", "Huidige Plant"])
    
    st.bar_chart(benchmark_df)
    
    st.write("### 📌 Directe Management Conclusies")
    st.markdown("""
    - **Processtabiliteit:** Het debiet van 500 m³/u[cite: 1] wordt consistent gehaald.
    - **Kostenbeheersing:** Geoptimaliseerde dosering zorgt voor een gunstig verbruiksprofiel van de additieven.
    - **Kwaliteit:** Uitstekende naleving van de contractnormen.
    """)

# --- FOOTER ---
st.sidebar.divider()
st.sidebar.text("BioOptima 360° v2.2 - Mobile Edition")