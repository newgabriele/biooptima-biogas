# tabs/tab1_config.py
import streamlit as st
from formulas import PlantProfile

def render():
    st.subheader("Klanten- en Installatiebeheer")
    st.markdown("Beheer uw klantenportefeuille, installaties en het toegepaste SBG-producttype.")

    if "clients_db" not in st.session_state:
        st.session_state.clients_db = {
            "SwissBiogas AG": {
                "installations": {
                    "Biogasanlage Almere (1MW Agro)": {
                        "volume_m3": 2500.0,
                        "flow_m3_h": 450.0,
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

    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        clients_list = list(st.session_state.clients_db.keys())
        selected_client = st.selectbox("Selecteer Klant", clients_list, key="sel_client")
    
    client_data = st.session_state.clients_db[selected_client]
    installations_list = list(client_data["installations"].keys())
    
    with col_sel2:
        if installations_list:
            selected_inst = st.selectbox("Selecteer Actieve Installatie", installations_list, key="sel_inst")
        else:
            selected_inst = None
            st.warning("Geen installaties gevonden voor deze klant.")

    if selected_inst and selected_inst in client_data["installations"]:
        inst_meta = client_data["installations"][selected_inst]
        st.session_state.active_plant = PlantProfile(
            name=f"{selected_client} - {selected_inst}",
            inst_type=inst_meta["inst_type"],
            temp_regime=inst_meta.get("temp_regime", "Mesofiel"),
            volume_m3=inst_meta["volume_m3"],
            biogas_flow_m3_h=inst_meta["flow_m3_h"],
            ph_nominal=inst_meta["ph_nominal"],
            temp_c=inst_meta["temp_c"],
            biogas_price_per_m3=inst_meta.get("biogas_price_per_m3", 0.68)
        )

    st.markdown("---")

    tab_klant, tab_inst = st.tabs(["Stap 1: Klanten Beheeren", "Stap 2: Installaties Beheren"])

    with tab_klant:
        st.markdown("#### Klant toevoegen of naam wijzigen")
        
        c_col1, c_col2 = st.columns(2)
        with c_col1:
            with st.form("add_client_form"):
                new_c_name = st.text_input("Nieuwe Klantnaam")
                if st.form_submit_button("Klant Toevoegen"):
                    if new_c_name and new_c_name not in st.session_state.clients_db:
                        st.session_state.clients_db[new_c_name] = {"installations": {}}
                        st.success(f"Klant '{new_c_name}' toegevoegd.")
                        st.rerun()
                    else:
                        st.error("Vul een unieke, geldige klantnaam in.")
        
        with c_col2:
            with st.form("rename_client_form"):
                rename_to = st.text_input("Hernoem geselecteerde klant", value=selected_client)
                if st.form_submit_button("Klantnaam Wijzigen"):
                    if rename_to and rename_to != selected_client:
                        st.session_state.clients_db[rename_to] = st.session_state.clients_db.pop(selected_client)
                        st.success(f"Klant hernoemd naar '{rename_to}'.")
                        st.rerun()

    with tab_inst:
        st.markdown(f"#### Installatie toevoegen voor klant: **{selected_client}**")

        with st.form("add_installation_form"):
            i_name = st.text_input("Installatienaam", value="Biogasinstallatie (1MW Agro)")
            
            i_col1, i_col2 = st.columns(2)
            with i_col1:
                i_type = st.selectbox("Vergistingsproces", ["agro", "covergisting", "industrie"], index=0)
                i_regime = st.selectbox("Thermisch Regime", ["Mesofiel", "Thermofiel"], index=0)
                i_sbg = st.selectbox("SBG Productlijn", ["SBG Agro", "SBG Energo", "SBG Industrial"], index=0)
            with i_col2:
                i_vol = st.number_input("Reactorvolume (m³)", value=2500.0, step=100.0)
                i_flow = st.number_input("Biogasdebiet (m³/h)", value=450.0, step=25.0)
                i_temp = st.number_input("Bedrijfstemperatuur (°C)", value=38.5, step=0.5)

            i_ph = st.number_input("Nominale pH", value=7.65, step=0.05)

            if st.form_submit_button("Installatie Toevoegen"):
                if i_name:
                    st.session_state.clients_db[selected_client]["installations"][i_name] = {
                        "volume_m3": i_vol,
                        "flow_m3_h": i_flow,
                        "inst_type": i_type,
                        "temp_regime": i_regime,
                        "sbg_product": i_sbg,
                        "ph_nominal": i_ph,
                        "temp_c": i_temp,
                        "biogas_price_per_m3": 0.68
                    }
                    st.success(f"Installatie '{i_name}' toegevoegd.")
                    st.rerun()
                else:
                    st.error("Geef een geldige installatienaam op.")

        if selected_inst:
            st.markdown("---")
            st.markdown(f"#### Bewerk actieve installatie: `{selected_inst}`")
            current_meta = client_data["installations"][selected_inst]
            
            with st.form("edit_existing_inst_form"):
                e_col1, e_col2 = st.columns(2)
                type_options = ["agro", "covergisting", "industrie"]
                regime_options = ["Mesofiel", "Thermofiel"]
                sbg_options = ["SBG Agro", "SBG Energo", "SBG Industrial"]
                
                cur_sbg = current_meta.get("sbg_product", "SBG Agro")
                if cur_sbg not in sbg_options:
                    cur_sbg = "SBG Agro"

                with e_col1:
                    e_type = st.selectbox("Vergistingsproces", type_options, index=type_options.index(current_meta["inst_type"]))
                    e_regime = st.selectbox("Thermisch Regime", regime_options, index=regime_options.index(current_meta.get("temp_regime", "Mesofiel")))
                    e_sbg = st.selectbox("SBG Productlijn", sbg_options, index=sbg_options.index(cur_sbg))
                with e_col2:
                    e_vol = st.number_input("Volume (m³)", value=float(current_meta["volume_m3"]), step=100.0)
                    e_flow = st.number_input("Debiet (m³/h)", value=float(current_meta["flow_m3_h"]), step=25.0)
                    e_temp = st.number_input("Temperatuur (°C)", value=float(current_meta["temp_c"]), step=0.5)

                e_ph = st.number_input("Nominale pH", value=float(current_meta["ph_nominal"]), step=0.05)

                if st.form_submit_button("Wijzigingen Opslaan"):
                    client_data["installations"][selected_inst].update({
                        "inst_type": e_type,
                        "temp_regime": e_regime,
                        "sbg_product": e_sbg,
                        "volume_m3": e_vol,
                        "flow_m3_h": e_flow,
                        "temp_c": e_temp,
                        "ph_nominal": e_ph
                    })
                    st.success("Installatieparameters bijgewerkt.")
                    st.rerun()