# tabs/tab1_plant_config.py
import streamlit as st
import pandas as pd
import os
import json

DATA_FILE = "clients_db.json"

def load_db():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_db(db):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Fout bij opslaan database: {e}")
        return False

def render():
    st.subheader("🏢 Tab 1: Klanten- & Installatiebeheer")
    st.markdown(
        "Beheer hier de klantgegevens, installaties en technische configuraties "
        "(inclusief enkelvoudige reactoren of multi-traps fermenter-architecturen)."
    )

    if "clients_db" not in st.session_state:
        st.session_state.clients_db = load_db()

    db = st.session_state.clients_db

    # --- ACTIE SELECTIE ---
    action = st.radio(
        "Kies actie", 
        [
            "📂 Overzicht & Bestaande Installaties Beheren", 
            "➕ Nieuwe Klant / Installatie Toevoegen",
            "✏️ Bestaande Installatie Bewerken / Muteren"
        ],
        horizontal=True,
        key="tab1_action_radio"
    )

    if action == "➕ Nieuwe Klant / Installatie Toevoegen":
        st.markdown("### ➕ Nieuwe Klant en Biogasinstallatie Registreren")
        
        with st.form("new_plant_form"):
            col1, col2 = st.columns(2)
            with col1:
                client_name = st.text_input("Klant / Bedrijfsnaam", placeholder="Bijv. Biogas Merlara S.r.l.")
                installation_name = st.text_input("Naam Installatie / Locatie", placeholder="Bijv. Installatie 1MW Envitec")
                inst_type = st.selectbox("Installatie Type", ["agro", "covergister", "industrial", "flex"])
            with col2:
                flow_m3_h = st.number_input("Ruw Biogas Debiet (m³/h)", min_value=50.0, max_value=5000.0, value=500.0, step=25.0)
                temp_c = st.number_input("Reactor Temperatuur (°C)", min_value=20.0, max_value=60.0, value=38.5, step=0.5)
                ph_nominal = st.number_input("Nominale pH", min_value=6.5, max_value=8.5, value=7.65, step=0.01)
                nitrogen_target = st.number_input("Stikstof Indicator (N)", min_value=0.1, max_value=100.0, value=3.0, step=0.1, key="new_nitrogen_target")

            st.markdown("---")
            st.markdown("#### ⚙️ Fermenter-Architectuur (Reactor Configuratie)")
            
            fermenter_setup = st.selectbox(
                "Aantal Fermenters / Trappen",
                ["1 Reactor (Enkelvoudig)", "2 Reactors (Primair + Secundair / Envitec Standaard)", "3+ Reactors (Complexe Cascadesysteem)"],
                index=1,
                key="new_fermenter_setup"
            )

            if "1 Reactor" in fermenter_setup:
                volume_m3 = st.number_input("Totaal Reactor Volume (m³)", min_value=100.0, max_value=10000.0, value=2500.0, step=50.0, key="new_vol_single")
                vol_primary = volume_m3
                vol_secondary = 0.0
            else:
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    vol_primary = st.number_input("Volume Primaire Fermenter (m³)", min_value=100.0, max_value=10000.0, value=1500.0, step=50.0, key="new_vol_prim")
                with col_f2:
                    vol_secondary = st.number_input("Volume Secundaire Fermenter / Navergister (m³)", min_value=100.0, max_value=10000.0, value=1000.0, step=50.0, key="new_vol_sec")
                volume_m3 = vol_primary + vol_secondary

            st.info(f"💡 Totaal berekend reactorvolume: **{volume_m3} m³**")

            submitted = st.form_submit_button("💾 Opslaan in Database")
            if submitted:
                if not client_name or not installation_name:
                    st.error("⚠️ Vul alstublieft minimaal de klantnaam en installatienaam in.")
                else:
                    if client_name not in db:
                        db[client_name] = {"installations": {}}
                    
                    db[client_name]["installations"][installation_name] = {
                        "inst_type": inst_type,
                        "flow_m3_h": flow_m3_h,
                        "volume_m3": volume_m3,
                        "fermenter_setup": fermenter_setup,
                        "vol_primary": vol_primary,
                        "vol_secondary": vol_secondary,
                        "temp_c": temp_c,
                        "ph_nominal": ph_nominal,
                        "nitrogen_target": nitrogen_target
                    }
                    st.session_state.clients_db = db
                    if save_db(db):
                        st.success(f"✅ Installatie **{installation_name}** voor **{client_name}** succesvol opgeslagen!")

    elif action == "✏️ Bestaande Installatie Bewerken / Muteren":
        st.markdown("### ✏️ Bestaande Installatie Gegevens Muteren")
        
        all_insts = []
        lookup = {}
        for c_name, c_data in db.items():
            for i_name in c_data.get("installations", {}).keys():
                disp = f"{c_name} — {i_name}"
                all_insts.append(disp)
                lookup[disp] = (c_name, i_name)
        
        if not all_insts:
            st.warning("⚠️ Geen installaties beschikbaar om te bewerken. Voeg er eerst een toe via 'Nieuwe Klant / Installatie Toevoegen'.")
        else:
            chosen_inst = st.selectbox("Selecteer installatie om te muteren", all_insts, key="edit_inst_select")
            c_name, i_name = lookup[chosen_inst]
            meta = db[c_name]["installations"][i_name]
            
            with st.form("edit_plant_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_client_name = st.text_input("Klant / Bedrijfsnaam", value=c_name)
                    new_installation_name = st.text_input("Naam Installatie / Locatie", value=i_name)
                    
                    inst_types = ["agro", "covergister", "industrial", "flex"]
                    cur_type = meta.get("inst_type", "agro")
                    type_idx = inst_types.index(cur_type) if cur_type in inst_types else 0
                    inst_type = st.selectbox("Installatie Type", inst_types, index=type_idx)
                with col2:
                    flow_m3_h = st.number_input("Ruw Biogas Debiet (m³/h)", min_value=50.0, max_value=5000.0, value=float(meta.get("flow_m3_h", 500.0)), step=25.0)
                    temp_c = st.number_input("Reactor Temperatuur (°C)", min_value=20.0, max_value=60.0, value=float(meta.get("temp_c", 38.5)), step=0.5)
                    ph_nominal = st.number_input("Nominale pH", min_value=6.5, max_value=8.5, value=float(meta.get("ph_nominal", 7.65)), step=0.01)
                    cur_n_target = float(meta.get("nitrogen_target", 3.0))
                    nitrogen_target = st.number_input("Stikstof Indicator (N)", min_value=0.1, max_value=100.0, value=cur_n_target, step=0.1, key="edit_nitrogen_target")

                st.markdown("---")
                st.markdown("#### ⚙️ Fermenter-Architectuur (Reactor Configuratie)")
                
                setup_options = [
                    "1 Reactor (Enkelvoudig)", 
                    "2 Reactors (Primair + Secundair / Envitec Standaard)", 
                    "3+ Reactors (Complexe Cascadesysteem)"
                ]
                cur_setup = meta.get("fermenter_setup", setup_options[1])
                setup_idx = setup_options.index(cur_setup) if cur_setup in setup_options else 0
                
                fermenter_setup = st.selectbox(
                    "Aantal Fermenters / Trappen",
                    setup_options,
                    index=setup_idx,
                    key="edit_fermenter_setup"
                )

                val_tot = float(meta.get("volume_m3", 2500.0))
                if val_tot < 100.0: val_tot = 2500.0

                val_prim = float(meta.get("vol_primary", 1500.0))
                if val_prim < 100.0: val_prim = 1500.0

                val_sec = float(meta.get("vol_secondary", 1000.0))
                if val_sec < 0.0: val_sec = 0.0

                if "1 Reactor" in fermenter_setup:
                    volume_m3 = st.number_input("Totaal Reactor Volume (m³)", min_value=100.0, max_value=10000.0, value=val_tot, step=50.0, key="edit_vol_single")
                    vol_primary = volume_m3
                    vol_secondary = 0.0
                else:
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        vol_primary = st.number_input("Volume Primaire Fermenter (m³)", min_value=100.0, max_value=10000.0, value=val_prim if val_prim >= 100 else 1500.0, step=50.0, key="edit_vol_prim")
                    with col_f2:
                        vol_secondary = st.number_input("Volume Secundaire Fermenter / Navergister (m³)", min_value=100.0, max_value=10000.0, value=val_sec if val_sec >= 100 else 1000.0, step=50.0, key="edit_vol_sec")
                    volume_m3 = vol_primary + vol_secondary

                st.info(f"💡 Totaal berekend reactorvolume: **{volume_m3} m³**")

                submitted_edit = st.form_submit_button("💾 Wijzigingen Opslaan")
                if submitted_edit:
                    if not new_client_name or not new_installation_name:
                        st.error("⚠️ Vul alstublieft minimaal de klantnaam en installatienaam in.")
                    else:
                        if c_name != new_client_name or i_name != new_installation_name:
                            del db[c_name]["installations"][i_name]
                            if not db[c_name]["installations"]:
                                del db[c_name]
                            if new_client_name not in db:
                                db[new_client_name] = {"installations": {}}

                        existing_recipe = meta.get("recipe", None)

                        updated_meta = {
                            "inst_type": inst_type,
                            "flow_m3_h": flow_m3_h,
                            "volume_m3": volume_m3,
                            "fermenter_setup": fermenter_setup,
                            "vol_primary": vol_primary,
                            "vol_secondary": vol_secondary,
                            "temp_c": temp_c,
                            "ph_nominal": ph_nominal,
                            "nitrogen_target": nitrogen_target
                        }
                        if existing_recipe is not None:
                            updated_meta["recipe"] = existing_recipe

                        db[new_client_name]["installations"][new_installation_name] = updated_meta
                        st.session_state.clients_db = db
                        if save_db(db):
                            st.success(f"✅ Installatie **{new_installation_name}** succesvol bijgewerkt!")
                            st.rerun()

    else:
        st.markdown("### 📂 Overzicht Opgeslagen Klanten & Installaties")
        if not db:
            st.info("ℹ️ Nog geen klanten of installaties gevonden in de database. Voeg er hierboven een toe.")
        else:
            for c_name, c_data in list(db.items()):
                with st.expander(f"🏢 Klant: {c_name}", expanded=True):
                    insts = c_data.get("installations", {})
                    if not insts:
                        st.markdown("_Geen installaties geregistreerd._")
                    for i_name, i_meta in list(insts.items()):
                        col_d1, col_d2, col_d3 = st.columns([3, 2, 1])
                        with col_d1:
                            st.markdown(f"**Installatie:** `{i_name}`")
                            st.markdown(f"- Type: `{i_meta.get('inst_type', 'agro').upper()}`")
                            st.markdown(f"- Configuratie: `{i_meta.get('fermenter_setup', '1 Reactor')}`")
                            if i_meta.get('vol_secondary', 0) > 0:
                                st.markdown(f"  - Primair: `{i_meta.get('vol_primary', 0)} m³` | Secundair: `{i_meta.get('vol_secondary', 0)} m³`")
                            else:
                                st.markdown(f"  - Enkelvoudige reactor (Geen secundair volume)")
                        with col_d2:
                            st.markdown(f"- Totaal Volume: **{i_meta.get('volume_m3', 2500)} m³**")
                            st.markdown(f"- Biogas Debiet: **{i_meta.get('flow_m3_h', 500)} m³/h**")
                            st.markdown(f"- Temp / pH: {i_meta.get('temp_c', 38.5)} °C | pH {i_meta.get('ph_nominal', 7.65)}")
                            st.markdown(f"- Stikstof Indicator (N): **{i_meta.get('nitrogen_target', 3.0)}**")
                        with col_d3:
                            if st.button("🗑️ Verwijder", key=f"del_inst_{c_name}_{i_name}"):
                                del db[c_name]["installations"][i_name]
                                if not db[c_name]["installations"]:
                                    del db[c_name]
                                st.session_state.clients_db = db
                                save_db(db)
                                st.rerun()
                
                if st.button(f"🗑️ Verwijder gehele klant: {c_name}", key=f"del_client_{c_name}"):
                    del db[c_name]
                    st.session_state.clients_db = db
                    save_db(db)
                    st.rerun()

    st.markdown("---")
    if st.button("🔄 Herlaad Database uit Bestand"):
        st.session_state.clients_db = load_db()
        st.success("Database herladen!")
        st.rerun()