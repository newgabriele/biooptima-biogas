# app.py
import streamlit as st
import json
import os
import pandas as pd
from formulas import PlantProfile

# Veilige imports van de tabbladen
try:
    from tabs import tab1_plant_config
except ImportError:
    tab1_plant_config = None

try:
    from tabs import tab2_kinetics
except ImportError:
    tab2_kinetics = None

try:
    from tabs import tab3_kinetics
except ImportError:
    tab3_kinetics = None

try:
    from tabs import tab4_economics
except ImportError:
    tab4_economics = None

try:
    from tabs import tab12_questions
except ImportError:
    tab12_questions = None

try:
    from tabs import tab13_sustainability
except ImportError:
    tab13_sustainability = None

st.set_page_config(
    page_title="BioOptima 360° - Biogas Optimalisatie",
    page_icon="♻️",
    layout="wide"
)

DATA_FILE = "clients_db.json"

def main():
    # 1. Laad de klanten- en installatiedatabase permanent vanuit JSON indien aanwezig
    if "clients_db" not in st.session_state:
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    st.session_state.clients_db = json.load(f)
            except Exception:
                st.session_state.clients_db = {}
        else:
            st.session_state.clients_db = {
                "SwissBiogas AG": {
                    "installations": {
                        "Corte Pila (1MW CSTR)": {
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

    # 2. Initialiseer active_plant als deze nog niet bestaat
    if "active_plant" not in st.session_state or not st.session_state.active_plant:
        try:
            first_c = list(st.session_state.clients_db.keys())[0]
            first_i = list(st.session_state.clients_db[first_c]["installations"].keys())[0]
            meta = st.session_state.clients_db[first_c]["installations"][first_i]
            st.session_state.active_plant = PlantProfile(
                name=f"{first_c} - {first_i}",
                inst_type=meta["inst_type"],
                volume_m3=meta["volume_m3"],
                biogas_flow_m3_h=meta["flow_m3_h"],
                ph_nominal=meta["ph_nominal"],
                temp_c=meta["temp_c"],
                biogas_price_per_m3=meta["biogas_price_per_m3"]
            )
        except Exception:
            st.session_state.active_plant = PlantProfile(
                name="Corte Pila (1MW CSTR)",
                inst_type="agro",
                volume_m3=2500.0,
                biogas_flow_m3_h=500.0,
                ph_nominal=7.65,
                temp_c=38.5,
                biogas_price_per_m3=0.68
            )

    # 3. Zijbalk navigatie met heldere benamingen
    st.sidebar.title("🧭 Navigatie")
    
    selected_tab = st.sidebar.radio(
        "Ga naar Tabblad",
        [
            "Tab 1: Klanten & Installatiebeheer",
            "Tab 2: Kinetica & Systeem",
            "Tab 3: Kinetica (H₂S & IJzeroxide)",
            "Tab 4: Economie & ROI",
            "Tab 5: Optimalisatie",
            "Tab 6: Substraten & VFA/TAC",
            "Tab 7: Monitoring",
            "Tab 8: Installaties",
            "Tab 9: Rapportage",
            "Tab 10: Extra 2",
            "Tab 11: Extra 3",
            "Tab 12: Register & Ideeën",
            "Tab 13: RED Duurzaamheid Programma"
        ],
        key="sidebar_tab_navigation"
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🟢 Actieve Plant")
    if hasattr(st.session_state.active_plant, "name"):
        st.sidebar.info(f"**{st.session_state.active_plant.name}**")
    else:
        st.sidebar.info(f"**{st.session_state.active_plant}**")

    # 4. Veilige routering naar de tabbladen
    if "Tab 1:" in selected_tab:
        if tab1_plant_config:
            tab1_plant_config.render()
        else:
            st.error("Tab 1 bestand kon niet worden geladen.")
    elif "Tab 2:" in selected_tab:
        if tab2_kinetics:
            tab2_kinetics.render()
        else:
            st.info("Tab 2 (Kinetica) bestand is niet gevonden.")
    elif "Tab 3:" in selected_tab:
        if tab3_kinetics:
            tab3_kinetics.render()
        else:
            st.info("Tab 3 is in voorbereiding.")
    elif "Tab 4:" in selected_tab:
        if tab4_economics:
            tab4_economics.render()
        else:
            st.info("Tab 4 (Economie) is in voorbereiding.")
    elif "Tab 5:" in selected_tab:
        st.subheader("Tab 5: Optimalisatie")
    elif "Tab 6:" in selected_tab:
        st.subheader("Tab 6: Substraten & VFA/TAC")
    elif "Tab 7:" in selected_tab:
        st.subheader("Tab 7: Monitoring")
    elif "Tab 8:" in selected_tab:
        st.subheader("Tab 8: Installaties")
    elif "Tab 9:" in selected_tab:
        st.subheader("Tab 9: Rapportage")
    elif "Tab 10:" in selected_tab:
        st.subheader("Tab 10: Extra 2")
    elif "Tab 11:" in selected_tab:
        st.subheader("Tab 11: Extra 3")
    elif "Tab 12:" in selected_tab:
        if tab12_questions:
            tab12_questions.render()
        else:
            st.info("Tab 12 is in voorbereiding.")
    elif "Tab 13:" in selected_tab:
        if tab13_sustainability:
            tab13_sustainability.render()
        else:
            st.info("Tab 13 is in voorbereiding.")

if __name__ == "__main__":
    main()