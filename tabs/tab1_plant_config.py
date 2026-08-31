# tabs/tab1_plant_config.py
import streamlit as st
import pandas as pd
import json
import os
from formulas import PlantProfile

DATA_FILE = "clients_db.json"

def load_clients_db():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
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
                },
                "Installatie 2 (Noord-Italië)": {
                    "volume_m3": 1800.0,
                    "flow_m3_h": 350.0,
                    "inst_type": "agro",
                    "temp_regime": "Mesofiel",
                    "sbg_product": "SBG Agro",
                    "ph_nominal": 7.50,
                    "temp_c": 38.5,
                    "biogas_price_per_m3": 0.68
                }
            }
        }
    }

def save_clients_db(db):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=4, ensure_ascii=False)
    except Exception as e:
        st.error(f"Fout bij opslaan naar bestand: {e}")

def render():
    st.subheader("🏢 Klanten- & Installatiebeheer (Tab 1)")
    st.markdown(
        "Beheer hieronder jouw portefeuille in een **bewerkbare tabel**. "
        "Wanneer je het **Regime** wijzigt naar Thermofiel of Mesofiel en op opslaan klikt, "
        "schakelt de temperatuur direct mee naar 52.0°C of 38.5°C."
    )

    if "clients_db" not in st.session_state:
        st.session_state.clients_db = load_clients_db()

    flat_data = []
    for client_name, client_data in st.session_state.clients_db.items():
        for inst_name, inst_meta in client_data.get("installations", {}).items():
            regime = inst_meta.get("temp_regime", "Mesofiel")
            default_temp = 38.5 if regime == "Mesofiel" else 52.0
            flat_data.append({
                "Klant": client_name,
                "Installatie": inst_name,
                "Type": inst_meta.get("inst_type", "agro"),
                "Volume (m³)": inst_meta.get("volume_m3", 2500.0),
                "Debiet (m³/h)": inst_meta.get("flow_m3_h", 500.0),
                "Regime": regime,
                "Temperatuur (°C)": inst_meta.get("temp_c", default_temp),
                "SBG Product": inst_meta.get("sbg_product", "SBG Agro"),
                "pH": inst_meta.get("ph_nominal", 7.65)
            })

    df_inst = pd.DataFrame(flat_data)
    if df_inst.empty:
        df_inst = pd.DataFrame([{
            "Klant": "Nieuwe Klant",
            "Installatie": "Nieuwe Installatie",
            "Type": "agro",
            "Volume (m³)": 2500.0,
            "Debiet (m³/h)": 500.0,
            "Regime": "Mesofiel",
            "Temperatuur (°C)": 38.5,
            "SBG Product": "SBG Agro",
            "pH": 7.65
        }])

    st.markdown("### 📊 Portefeuille Overzicht & Mutatietabel")
    
    edited_df = st.data_editor(
        df_inst, 
        use_container_width=True, 
        height=350, 
        key="editable_installations_grid",
        num_rows="dynamic",
        column_config={
            "Klant": st.column_config.TextColumn("Klant / Eigenaar", required=True),
            "Installatie": st.column_config.TextColumn("Naam Installatie", required=True),
            "Type": st.column_config.SelectboxColumn("Type", options=["agro", "covergisting", "industrie"], required=True),
            "Regime": st.column_config.SelectboxColumn("Regime", options=["Mesofiel", "Thermofiel"], required=True),
            "SBG Product": st.column_config.SelectboxColumn("SBG Product", options=["SBG Agro", "SBG Energo", "SBG Industrial"], required=True),
            "Volume (m³)": st.column_config.NumberColumn(format="%.1f", step=100.0),
            "Debiet (m³/h)": st.column_config.NumberColumn(format="%.1f", step=25.0),
            "pH": st.column_config.NumberColumn(format="%.2f", step=0.05),
            "Temperatuur (°C)": st.column_config.NumberColumn(format="%.1f", step=0.5, help="Mesofiel = 38.5°C, Thermofiel = 52.0°C")
        }
    )

    col_btn1, col_btn2 = st.columns([1, 2])
    with col_btn1:
        save_clicked = st.button("💾 Wijzigingen Opslaan & Doorvoeren", type="primary")

    if save_clicked:
        new_clients_db = {}
        for _, row in edited_df.iterrows():
            c_name = str(row["Klant"]).strip()
            i_name = str(row["Installatie"]).strip()
            
            if not c_name or c_name == "nan" or not i_name or i_name == "nan":
                continue
            
            new_regime = row["Regime"]
            current_temp = row["Temperatuur (°C)"]
            
            # Zoek het vorige regime op in de bestaande database
            old_regime = "Mesofiel"
            old_meta = {}
            if c_name in st.session_state.clients_db:
                if i_name in st.session_state.clients_db[c_name].get("installations", {}):
                    old_meta = st.session_state.clients_db[c_name]["installations"][i_name]
                    old_regime = old_meta.get("temp_regime", "Mesofiel")
            
            # Bepaal de standaardtemperaturen
            default_old = 38.5 if old_regime == "Mesofiel" else 52.0
            default_new = 38.5 if new_regime == "Mesofiel" else 52.0
            
            # LOGICA: Als het regime is gewijzigd OF de temperatuur stond nog op de oude standaardwaarde, 
            # pas dan automatisch de temperatuur aan naar de nieuwe standaard. 
            # Anders blijft de handmatig ingevoerde temperatuur behouden.
            if new_regime != old_regime:
                target_temp = default_new
            else:
                curr_float = float(current_temp) if not pd.isna(current_temp) else default_new
                # Als de gebruiker handmatig de temperatuur op de oude standaard liet staan terwijl regime gelijk is
                if curr_float == default_old and new_regime != old_regime:
                    target_temp = default_new
                else:
                    target_temp = curr_float
            
            old_price = old_meta.get("biogas_price_per_m3", 0.68)

            if c_name not in new_clients_db:
                new_clients_db[c_name] = {"installations": {}}

            new_clients_db[c_name]["installations"][i_name] = {
                "inst_type": row["Type"],
                "volume_m3": float(row["Volume (m³)"]) if not pd.isna(row["Volume (m³)"]) else 2500.0,
                "flow_m3_h": float(row["Debiet (m³/h)"]) if not pd.isna(row["Debiet (m³/h)"]) else 500.0,
                "temp_regime": new_regime,
                "temp_c": target_temp,
                "sbg_product": row["SBG Product"],
                "ph_nominal": float(row["pH"]) if not pd.isna(row["pH"]) else 7.65,
                "biogas_price_per_m3": old_price
            }

        st.session_state.clients_db = new_clients_db
        save_clients_db(new_clients_db)
        
        first_c = list(new_clients_db.keys())[0]
        first_i = list(new_clients_db[first_c]["installations"].keys())[0]
        meta = new_clients_db[first_c]["installations"][first_i]
        
        # Geef de actieve installatie mee inclusief de correcte temperatuur voor formules.py
        st.session_state.active_plant = PlantProfile(
            name=f"{first_c} - {first_i}",
            inst_type=meta["inst_type"],
            volume_m3=meta["volume_m3"],
            biogas_flow_m3_h=meta["flow_m3_h"],
            ph_nominal=meta["ph_nominal"],
            temp_c=meta["temp_c"],
            biogas_price_per_m3=meta["biogas_price_per_m3"]
        )

        st.success("✅ Wijzigingen opgeslagen! Temperatuur is succesvol aangepast aan het regime en doorgevoerd in de formules.")
        st.rerun()

    st.markdown("---")
    st.markdown("### 🎯 Huidige Actieve Selectie voor Berekeningen")
    if "active_plant" in st.session_state and st.session_state.active_plant:
        p = st.session_state.active_plant
        if hasattr(p, "name"):
            st.info(f"🟢 **Actieve Installatie:** `{p.name}` — Debiet: **{p.biogas_flow_m3_h} m³/h** | Volume: **{p.volume_m3} m³** | Temperatuur: **{p.temp_c}°C**")
        else:
            st.info(f"🟢 **Actieve Installatie:** `{p}`")
    else:
        st.warning("⚠️ Klik op 'Wijzigingen Opslaan & Doorvoeren' om een actieve installatie te activeren.")