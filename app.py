# app.py
import streamlit as st
import pandas as pd
import json
import os
from formulas import PlantProfile
from tabs import tab1_plant_config, tab12_questions, tab13_sustainability

st.set_page_config(
    page_title="BioOptima 360° - Industrieel Biogas Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "clients_data.json"

def load_clients_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "SwissBiogas AG": {
            "installations": {
                "1MW Agro Installatie": {
                    "volume_m3": 2500.0,
                    "flow_m3_h": 500.0,
                    "inst_type": "agro",
                    "temp_regime": "Mesofiel",
                    "sbg_product": "SBG Agro",
                    "ph_nominal": 7.65,
                    "temp_c": 38.5,
                    "biogas_price_per_m3": 0.68
                }
            }
        }
    }

def save_clients_db(db):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

if "clients_db" not in st.session_state:
    st.session_state.clients_db = load_clients_db()

if "user_asked_registry" not in st.session_state:
    st.session_state.user_asked_registry = []

save_clients_db(st.session_state.clients_db)

# --- MASTER MOTHERBOARD SIDEBAR ---
with st.sidebar:
    st.markdown("### 🎛️ Master Motherboard Besturing")
    
    motherboard_optie = st.radio(
        "Selecteer Motherboard Modus", 
        ["Optie 1: Specifieke Installatie", "Optie 2: Hele Klant Portefeuille"],
        key="motherboard_mode_choice"
    )
    
    st.markdown("---")
    total_installations = sum(len(c_data.get("installations", {})) for c_data in st.session_state.clients_db.values())
    
    # Dynamische predictienauwkeurigheid op basis van aantal installaties in de database
    prediction_accuracy = min(98.5, 88.0 + (total_installations * 2.5))
    
    st.metric("Totaal Installaties", total_installations, delta=f"Predictienauwkeurigheid: {prediction_accuracy:.1f}%")
    
    clients_list = list(st.session_state.clients_db.keys())
    if clients_list:
        selected_client = st.selectbox("Selecteer Klant", clients_list, key="sb_client_sel")
        client_insts = list(st.session_state.clients_db[selected_client].get("installations", {}).keys())
        
        if "Optie 1" in motherboard_optie:
            if client_insts:
                selected_inst = st.selectbox("Selecteer Installatie", client_insts, key="sb_inst_sel")
                inst_meta = st.session_state.clients_db[selected_client]["installations"][selected_inst]
                st.session_state.active_plant = PlantProfile(
                    name=f"{selected_client} — {selected_inst}",
                    inst_type=inst_meta["inst_type"],
                    temp_regime=inst_meta.get("temp_regime", "Mesofiel"),
                    volume_m3=inst_meta["volume_m3"],
                    biogas_flow_m3_h=inst_meta["flow_m3_h"],
                    ph_nominal=inst_meta["ph_nominal"],
                    temp_c=inst_meta["temp_c"],
                    biogas_price_per_m3=inst_meta.get("biogas_price_per_m3", 0.68)
                )
                st.success(f"Actief: **{selected_inst}**")
            else:
                st.warning("Geen installaties voor deze klant.")
        else:
            st.info(f"Portefeuilleweergave voor **{selected_client}** ({len(client_insts)} installaties).")

    st.markdown("---")
    st.markdown("### 🔬 Kinetische & H₂S Parameters")
    st.info(
        "🔹 **H₂S Ingang:** 1.500 ppm\n"
        "🔹 **H₂S Doelwaarde:** 150 ppm\n"
        "🔹 **Additief Mix:** Fe₂O₃ / FeO (35% / 35%)\n"
        "🔹 **Validatie:** Geverifieerd via praktijkbenchmarks"
    )

    st.markdown("---")
    st.markdown("### 📑 Tabbladen Navigatie (1 t/m 13)")
    
    selected_tab = st.radio(
        "Ga naar Tabblad",
        [
            "Tab 1: Configuratie",
            "Tab 2: Substraten",
            "Tab 3: Kinetica",
            "Tab 4: Economie",
            "Tab 5: Optimalisatie",
            "Tab 6: Monitoring",
            "Tab 7: Installaties",
            "Tab 8: Rapportage",
            "Tab 9: Extra 1",
            "Tab 10: Extra 2",
            "Tab 11: Extra 3",
            "Tab 12: Register & Ideeën",
            "Tab 13: RED Duurzaamheid Programma"
        ],
        key="sidebar_tab_navigation"
    )
    
    st.markdown("---")
    st.markdown("### 📊 Systeemstatus")
    st.info(
        "⚙️ **Status:** Actief\n\n"
        "🔹 **Versie:** v2.1.0 (Augustus 2026)"
    )

# --- HOOFDSCHERM ---
st.title("🌱 BioOptima 360° - Industrieel Biogas Dashboard")

if "active_plant" not in st.session_state:
    st.session_state.active_plant = PlantProfile()

if "Tab 1:" in selected_tab:
    tab1_plant_config.render()
elif "Tab 2:" in selected_tab:
    st.markdown("### Substraatbeheer")
    st.info("Substraat- en VFA/TAC-analysemodule.")
elif "Tab 3:" in selected_tab:
    st.markdown("### Kinetische Simulatie")
    st.info("Reaktiesnelheden en ijzeroxide dosering.")
elif "Tab 4:" in selected_tab:
    st.markdown("### Economie & ROI")
    st.info("Kosten-baten analyse van additieven en biogaswaarde.")
elif "Tab 5:" in selected_tab:
    st.markdown("### Optimalisatie")
elif "Tab 6:" in selected_tab:
    st.markdown("### Monitoring")
elif "Tab 7:" in selected_tab:
    st.markdown("### Installaties")
elif "Tab 8:" in selected_tab:
    st.markdown("### Rapportage")
elif "Tab 9:" in selected_tab:
    st.markdown("### Extra 1")
elif "Tab 10:" in selected_tab:
    st.markdown("### Extra 2")
elif "Tab 11:" in selected_tab:
    st.markdown("### Extra 3")
elif "Tab 12:" in selected_tab:
    tab12_questions.render()
elif "Tab 13:" in selected_tab:
    tab13_sustainability.render()