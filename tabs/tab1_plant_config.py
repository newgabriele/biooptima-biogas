# tabs/tab1_plant_config.py
import streamlit as st
import pandas as pd
from formulas import PlantProfile

def render():
    st.subheader("Klanten- en Installatiebeheer (Tab 1)")
    
    # Master Dashboard rechts bovenaan in Tab 1
    if "active_plant" in st.session_state and st.session_state.active_plant:
        plant = st.session_state.active_plant
        col_head, col_dash = st.columns([2, 1])
        with col_head:
            st.markdown("Beheer alle installaties en parameters direct via onderstaande bewerkbare tabel. Het thermisch regime past automatisch de standaardtemperatuur aan (38.5°C voor Mesofiel, 52.0°C voor Thermofiel).")
        with col_dash:
            st.markdown("##### 🎛️ Master Dashboard")
            st.info(
                f"🏢 **Plant:** {plant.name}\n\n"
                f"💨 **Debiet:** {plant.biogas_flow_m3_h} m³/h | 📦 **Volume:** {plant.volume_m3} m³\n\n"
                f"🌡️ **Regime:** {plant.temp_regime} ({plant.temp_c}°C) | **pH:** {plant.ph_nominal}"
            )
    else:
        st.markdown("Beheer alle installaties en parameters direct via onderstaande bewerkbare tabel.")

    st.markdown("---")

    if "clients_db" not in st.session_state:
        st.session_state.clients_db = {
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

    flat_data = []
    for client_name, client_data in st.session_state.clients_db.items():
        for inst_name, inst_meta in client_data.get("installations", {}).items():
            flat_data.append({
                "Klant": client_name,
                "Installatie": inst_name,
                "Type": inst_meta.get("inst_type", "agro"),
                "Volume (m³)": inst_meta.get("volume_m3", 2500.0),
                "Debiet (m³/h)": inst_meta.get("flow_m3_h", 500.0),
                "Regime": inst_meta.get("temp_regime", "Mesofiel"),
                "Temperatuur (°C)": inst_meta.get("temp_c", 38.5),
                "SBG Product": inst_meta.get("sbg_product", "SBG Agro"),
                "pH": inst_meta.get("ph_nominal", 7.65)
            })

    df_inst = pd.DataFrame(flat_data)
    if df_inst.empty:
        df_inst = pd.DataFrame([{
            "Klant": "SwissBiogas AG",
            "Installatie": "1MW Agro Installatie",
            "Type": "agro",
            "Volume (m³)": 2500.0,
            "Debiet (m³/h)": 500.0,
            "Regime": "Mesofiel",
            "Temperatuur (°C)": 38.5,
            "SBG Product": "SBG Agro",
            "pH": 7.65
        }])

    edited_df = st.data_editor(
        df_inst, 
        use_container_width=True, 
        height=300, 
        key="editable_installations_grid",
        num_rows="dynamic",
        column_config={
            "Type": st.column_config.SelectboxColumn("Type", options=["agro", "covergisting", "industrie"], required=True),
            "Regime": st.column_config.SelectboxColumn("Regime", options=["Mesofiel", "Thermofiel"], required=True),
            "SBG Product": st.column_config.SelectboxColumn("SBG Product", options=["SBG Agro", "SBG Energo", "SBG Industrial"], required=True),
            "Volume (m³)": st.column_config.NumberColumn(format="%.1f", step=100.0),
            "Debiet (m³/h)": st.column_config.NumberColumn(format="%.1f", step=25.0),
            "pH": st.column_config.NumberColumn(format="%.2f", step=0.05),
            "Temperatuur (°C)": st.column_config.NumberColumn(format="%.1f", step=0.5)
        }
    )

    for _, row in edited_df.iterrows():
        i_name = str(row["Installatie"]).strip()
        c_name = str(row["Klant"]).strip()
        inst_type = row["Type"]
        regime = row["Regime"]
        temp = row["Temperatuur (°C)"]

        if inst_type == "agro" and (regime == "Thermofiel" or (not pd.isna(temp) and temp > 45.0)):
            st.warning(f"⚠️ **Sanity Check:** Installatie *'{i_name}'* ({c_name}) is geconfigureerd als **agro** met een thermofiele instelling ({regime} / {temp}°C). In de praktijk komt dit vrijwel nooit voor (~99% ongebruikelijk voor agro-vergisters). Controleer of dit correct is.")

    temp_updated_db = {}
    needs_rerun = False

    for _, row in edited_df.iterrows():
        c_name = str(row["Klant"]).strip()
        i_name = str(row["Installatie"]).strip()
        if not c_name or c_name == "nan" or not i_name or i_name == "nan":
            continue
        
        new_regime = row["Regime"]
        current_temp = row["Temperatuur (°C)"]

        existing_inst = st.session_state.clients_db.get(c_name, {}).get("installations", {}).get(i_name, {})
        old_regime = existing_inst.get("temp_regime", "Mesofiel")
        
        target_temp = current_temp
        if new_regime != old_regime:
            needs_rerun = True
            target_temp = 52.0 if new_regime == "Thermofiel" else 38.5
        elif pd.isna(current_temp):
            needs_rerun = True
            target_temp = 38.5 if new_regime == "Mesofiel" else 52.0

        if c_name not in temp_updated_db:
            temp_updated_db[c_name] = {"installations": {}}
        
        temp_updated_db[c_name]["installations"][i_name] = {
            "inst_type": row["Type"],
            "volume_m3": float(row["Volume (m³)"]) if not pd.isna(row["Volume (m³)"]) else 2500.0,
            "flow_m3_h": float(row["Debiet (m³/h)"]) if not pd.isna(row["Debiet (m³/h)"]) else 500.0,
            "temp_regime": new_regime,
            "temp_c": float(target_temp),
            "sbg_product": row["SBG Product"],
            "ph_nominal": float(row["pH"]) if not pd.isna(row["pH"]) else 7.65,
            "biogas_price_per_m3": existing_inst.get("biogas_price_per_m3", 0.68)
        }

    if needs_rerun:
        st.session_state.clients_db = temp_updated_db
        st.session_state.pop("editable_installations_grid", None)
        st.rerun()

    if st.button("💾 Alle Tabelwijzigingen & Nieuwe Installaties Opslaan & Doorvoeren"):
        st.session_state.clients_db = temp_updated_db
        st.session_state.pop("editable_installations_grid", None)
        st.success("Alle installaties en wijzigingen succesvol opgeslagen en doorgevoerd naar alle tabs!")
        st.rerun()

    st.markdown("---")
    st.markdown("#### 🏢 Klantenbeheer (Toevoegen of Hernoemen)")
    clients_list = list(st.session_state.clients_db.keys())
    
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        with st.form("add_client_bottom_form"):
            new_client_name = st.text_input("Nieuwe Klantnaam toevoegen")
            if st.form_submit_button("Klant Toevoegen"):
                if new_client_name and new_client_name not in st.session_state.clients_db:
                    st.session_state.clients_db[new_client_name] = {"installations": {}}
                    st.success(f"Klant '{new_client_name}' toegevoegd.")
                    st.rerun()
                else:
                    st.error("Vul een unieke en geldige klantnaam in.")
    
    with col_k2:
        if clients_list:
            with st.form("rename_client_bottom_form"):
                target_client = st.selectbox("Selecteer te hernoemen klant", clients_list)
                rename_client_to = st.text_input("Nieuwe klantnaam", value=target_client)
                if st.form_submit_button("Klantnaam Wijzigen"):
                    if rename_client_to and rename_client_to != target_client:
                        st.session_state.clients_db[rename_client_to] = st.session_state.clients_db.pop(target_client)
                        st.success(f"Klant hernoemd naar '{rename_client_to}'.")
                        st.rerun()