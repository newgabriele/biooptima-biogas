# app.py
import streamlit as st
import pandas as pd
from tabs.tab2_kantoor import render_tab2
from tabs.tab7_installaties import render_tab7
from tabs import tab12_master

st.set_page_config(
    page_title="BioOptima 360° — Biogas Process Optimization",
    page_icon="⚡",
    layout="wide"
)

translations = {
    "Nederlands": {
        "sidebar_settings": "⚙️ Instellingen & Installatie",
        "lang_label": "Taal / Language",
        "role_label": "Rol / Modus",
        "client_label": "Klant",
        "plant_label": "Installatie / Plant",
        "vol_label": "Reactor Volume (m³)",
        "strip_label": "Gas Stripping Factor",
        "tab1": "📊 Tab 1: Dashboard & Overzicht",
        "tab2": "🎛️ Tab 2: Kantoor & Receptbeheer",
        "tab7": "🏭 Tab 7: Installaties Beheer",
        "tab12": "🧠 Master Dashboard & AI Register",
        "dash_title": "Dashboard & Monitoring",
        "dash_info": "Overzicht van de actieve reactorparameters, biologische belasting en gasproductie.",
        "vol_metric": "Reactor Volume",
        "biogas_target": "Doel Biogas",
        "h2s_target": "Doel H2S",
        "status_title": "Systeemstatus & Basisparameters (Bewerkbaar)",
        "admin_badge": "🛠️ Administrator Modus: Volledig beheer, R&D testing en master code-generatie actief (alle installaties zichtbaar).",
        "client_badge": "👤 Klant / Gebruiker Modus: Alleen data-invoer en inzicht in globale kennis voor uw installaties."
    },
    "Italiano": {
        "sidebar_settings": "⚙️ Impostazioni & Impianto",
        "lang_label": "Lingua / Language",
        "role_label": "Ruolo / Modalità",
        "client_label": "Cliente",
        "plant_label": "Impianto / Unità",
        "vol_label": "Volume Reattore (m³)",
        "strip_label": "Fattore di Stripping Gas",
        "tab1": "📊 Tab 1: Dashboard & Panoramica",
        "tab2": "🎛️ Tab 2: Ufficio & Gestione Ricette",
        "tab7": "🏭 Tab 7: Gestione Impianti",
        "tab12": "🧠 Master Dashboard & Registro AI",
        "dash_title": "Dashboard & Monitoraggio",
        "dash_info": "Panoramica dei parametri attivi del reattore, carico biologico e produzione di gas.",
        "vol_metric": "Volume Reattore",
        "biogas_target": "Target Biogas",
        "h2s_target": "Target H2S",
        "status_title": "Stato del Sistema & Parametri Base (Modificabile)",
        "admin_badge": "🛠️ Modalità Administrator: Gestione completa, test R&D e generazione codici master attivi (tutti gli impianti visibili).",
        "client_badge": "👤 Modalità Cliente / Utente: Solo inserimento dati e visualizzazione conoscenza globale per i vostri impianti."
    },
    "English": {
        "sidebar_settings": "⚙️ Settings & Plant Setup",
        "lang_label": "Language",
        "role_label": "Role / Mode",
        "client_label": "Customer",
        "plant_label": "Reactor Unit",
        "vol_label": "Reactor Volume (m³)",
        "strip_label": "Gas Stripping Factor",
        "tab1": "📊 Tab 1: Dashboard & Overview",
        "tab2": "🎛️ Tab 2: Office & Recipe Management",
        "tab7": "🏭 Tab 7: Installations Management",
        "tab12": "🧠 Master Dashboard & AI Register",
        "dash_title": "Dashboard & Monitoring",
        "dash_info": "Overview of active reactor parameters, organic loading rate, and gas production.",
        "vol_metric": "Reactor Volume",
        "biogas_target": "Biogas Target",
        "h2s_target": "H2S Target",
        "status_title": "System Status & Baseline Parameters (Editable)",
        "admin_badge": "🛠️ Administrator Mode: Full management, R&D testing and master code generation active (all installations visible).",
        "client_badge": "👤 Customer / User Mode: Data input and global knowledge overview for your installations."
    }
}

selected_lang = st.sidebar.selectbox("Taal / Language", ["Nederlands", "Italiano", "English"])
t = translations[selected_lang]

st.sidebar.markdown(f"## {t['sidebar_settings']}")

role_options = ["Administrator (Beheer & Test)", "Klant / Gebruiker (Data & Kennis)"]
selected_role = st.sidebar.selectbox(t["role_label"], role_options)
is_admin = ("Administrator" in selected_role)

if "installations_df" not in st.session_state:
    st.session_state.installations_df = pd.DataFrame([
        {"Klant": "Bioman Srl", "Installatie / Plant": "CSTR Digester 1", "Volume (m³)": 4500.0, "Status": "Actief"},
        {"Klant": "Bioman Srl", "Installatie / Plant": "Thermophilic Reactor 2", "Volume (m³)": 3200.0, "Status": "Actief"},
        {"Klant": "BioPower Teglio", "Installatie / Plant": "Teglio Plant Central", "Volume (m³)": 2800.0, "Status": "Actief"},
        {"Klant": "AgroEnergy BV", "Installatie / Plant": "Almere Digester North", "Volume (m³)": 5000.0, "Status": "Planning"},
        {"Klant": "AgroEnergy BV", "Installatie / Plant": "Almere Digester South", "Volume (m³)": 4500.0, "Status": "Planning"}
    ])
else:
    df_check = st.session_state.installations_df
    if "Klant" not in df_check.columns:
        if "Klant / Gebruiker" in df_check.columns:
            df_check["Klant"] = df_check["Klant / Gebruiker"]
        elif "Moederklant" in df_check.columns:
            df_check["Klant"] = df_check["Moederklant"]
        else:
            st.session_state.installations_df = pd.DataFrame([
                {"Klant": "Bioman Srl", "Installatie / Plant": "CSTR Digester 1", "Volume (m³)": 4500.0, "Status": "Actief"},
                {"Klant": "Bioman Srl", "Installatie / Plant": "Thermophilic Reactor 2", "Volume (m³)": 3200.0, "Status": "Actief"},
                {"Klant": "BioPower Teglio", "Installatie / Plant": "Teglio Plant Central", "Volume (m³)": 2800.0, "Status": "Actief"},
                {"Klant": "AgroEnergy BV", "Installatie / Plant": "Almere Digester North", "Volume (m³)": 5000.0, "Status": "Planning"},
                {"Klant": "AgroEnergy BV", "Installatie / Plant": "Almere Digester South", "Volume (m³)": 4500.0, "Status": "Planning"}
            ])

if is_admin:
    filtered_df = st.session_state.installations_df
else:
    filtered_df = st.session_state.installations_df[st.session_state.installations_df["Klant"] == "Bioman Srl"]

client_hierarchy = {}
for _, row in filtered_df.iterrows():
    customer = row.get("Klant", "Bioman Srl")
    plant = row.get("Installatie / Plant", "Plant 1")
    
    if customer not in client_hierarchy:
        client_hierarchy[customer] = []
    if plant not in client_hierarchy[customer]:
        client_hierarchy[customer].append(plant)

selected_customer = st.sidebar.selectbox(t["client_label"], list(client_hierarchy.keys()))
selected_plant = st.sidebar.selectbox(t["plant_label"], client_hierarchy[selected_customer])

reactor_vol = st.sidebar.number_input(t["vol_label"], min_value=500.0, max_value=10000.0, value=4500.0, step=100.0)
gas_stripping_factor = st.sidebar.slider(t["strip_label"], min_value=0.5, max_value=2.0, value=1.0, step=0.1)

st.sidebar.markdown("---")
temp_regime = st.sidebar.radio("🌡️ Temperatuurregime (T)", ["Mesofiel (~38°C)", "Thermofiel (~52°C)"])

st.sidebar.markdown("---")
st.sidebar.markdown("**BioOptima 360° v2.4**\n*Direct Interspecies Electron Transfer (DIET) & Micro-dosing*")

st.markdown(f"# 🔋 BioOptima 360° — {selected_customer} ({selected_plant})")

if is_admin:
    st.success(t["admin_badge"])
else:
    st.info(t["client_badge"])

if "system_status_store" not in st.session_state:
    st.session_state.system_status_store = {}

if selected_plant not in st.session_state.system_status_store:
    if "Thermofiel" in temp_regime:
        t_w = "52.2 °C (Thermofiel)"
        ph_w = "8.0 (NH3 balans)"
    else:
        t_w = "38.5 °C (Mesofiel)"
        ph_w = "7.8 (Optimaal)"

    st.session_state.system_status_store[selected_plant] = pd.DataFrame({
        "Parameter": ["Reactortemperatuur", "Procesregime", "pH Waarde", "VFA / TAC Ratio", "Ammonium (NH4+)", "H2S Gasfase"],
        "Waarde": [t_w, temp_regime, ph_w, "0.22", "2450 mg/L", "81 ppm"],
        "Status": ["Optimaal", "Actief", "Optimaal", "Stabiel", "Normaal", "Doelbereik"]
    })

# Dynamisch tabbladen toewijzen op basis van Administrator-rol
if is_admin:
    tab1, tab2, tab7, tab12 = st.tabs([
        t["tab1"], 
        t["tab2"],
        t["tab7"],
        t["tab12"]
    ])
else:
    tab1, tab2, tab7 = st.tabs([
        t["tab1"], 
        t["tab2"],
        t["tab7"]
    ])

with tab1:
    st.markdown(f"### 📊 {t['dash_title']} — {selected_plant}")
    st.info(f"💡 {t['dash_info']}")
    
    def_sub_tons = {"Maissilage": 25.0, "Drijfmest (rund)": 120.0, "Kippenmest": 10.0, "Glycerine": 2.0}
    total_sub_calc = sum(st.session_state.get(f"input_ton_{sub}", val) for sub, val in def_sub_tons.items())
    current_hrt_calc = reactor_vol / total_sub_calc if total_sub_calc > 0 else 0.0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric(t["vol_metric"], f"{reactor_vol:,.0f} m³")
    col2.metric("Tijdsregime (HRT)", f"{current_hrt_calc:.1f} dagen")
    col3.metric("Regime (T)", temp_regime)
    col4.metric(t["biogas_target"], "500.0 m³/h")
    col5.metric(t["h2s_target"], "80 ppm")

    st.markdown("---")
    st.markdown(f"##### 📈 {t['status_title']}")
    st.caption("💡 Pas hieronder direct de actuele lab- of sensorwaarden aan voor deze installatie zodat je ze morgen live kunt tonen.")

    current_status_df = st.session_state.system_status_store[selected_plant]
    edited_status_df = st.data_editor(
        current_status_df,
        use_container_width=True,
        key=f"status_editor_{selected_plant}"
    )
    st.session_state.system_status_store[selected_plant] = edited_status_df

with tab2:
    render_tab2(selected_customer, selected_plant, reactor_vol, gas_stripping_factor, selected_lang, is_admin, temp_regime)

with tab7:
    render_tab7(selected_lang, is_admin)

if is_admin:
    with tab12:
        tab12_master.render()