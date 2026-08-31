# app.py
import streamlit as st
import json
import os
import importlib
import pandas as pd
from formulas import PlantProfile

st.set_page_config(
    page_title="BioOptima 360° - Biogas Optimalisatie",
    page_icon="♻️",
    layout="wide"
)

DATA_FILE = "clients_db.json"

def main():
    # 1. Laad de klanten- en installatiedatabase permanent vanuit JSON
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

    # 2. Initialiseer actieve plant
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

    # 3. Dynamisch inladen van alle tab-bestanden in de map 'tabs'
    tabs_modules = {}
    tabs_dir = "tabs"
    if os.path.exists(tabs_dir):
        for fname in sorted(os.listdir(tabs_dir)):
            if fname.endswith(".py") and fname.startswith("tab"):
                num_str = ''.join(filter(str.isdigit, fname.split("_")[0]))
                if num_str:
                    tab_num = int(num_str)
                    module_name = fname[:-3]
                    try:
                        mod = importlib.import_module(f"tabs.{module_name}")
                        tabs_modules[tab_num] = mod
                    except Exception:
                        pass

    # Koppel Tab 1 expliciet aan onze nieuwe beheer-module
    try:
        from tabs import tab1_plant_config
        tabs_modules[1] = tab1_plant_config
    except Exception:
        pass

    # 4. Correcte benamingen van de zijbalk conform Versie 5
    tab_labels = {
        1: "Tab 1: Klanten & Installatiebeheer",
        2: "Tab 2: Kinetica & Systeem",
        3: "Tab 3: Operator",
        4: "Tab 4: Economie & ROI",
        5: "Tab 5: Optimalisatie",
        6: "Tab 6: Simulatie & Optimalisaties",
        7: "Tab 7: Monitoring",
        8: "Tab 8: Installaties",
        9: "Tab 9: Rapportage",
        10: "Tab 10: Extra 2",
        11: "Tab 11: Extra 3",
        12: "Tab 12: Register & Ideeën",
        13: "Tab 13: RED Duurzaamheid Programma"
    }

    menu_options = []
    mapping_options = {}
    for i in range(1, 14):
        label = tab_labels.get(i, f"Tab {i}")
        menu_options.append(label)
        mapping_options[label] = i

    st.sidebar.title("🧭 Navigatie")
    selected_label = st.sidebar.radio("Ga naar Tabblad", menu_options, key="sidebar_tab_navigation")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🟢 Actieve Plant")
    if hasattr(st.session_state.active_plant, "name"):
        st.sidebar.info(f"**{st.session_state.active_plant.name}**")
    else:
        st.sidebar.info(f"**{st.session_state.active_plant}**")

    # 5. Render het geselecteerde tabblad vanuit de echte module
    selected_num = mapping_options.get(selected_label, 1)
    
    if selected_num in tabs_modules and hasattr(tabs_modules[selected_num], "render"):
        tabs_modules[selected_num].render()
    else:
        st.subheader(selected_label)
        st.warning(f"⚠️ Voor dit tabblad kon geen gekoppeld Python-bestand in de map 'tabs' worden gevonden.")

if __name__ == "__main__":
    main()