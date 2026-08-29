import streamlit as st

def render():
    st.subheader("⚙️ Tab 1: Plant Configuratie & Asset Beheer")
    st.markdown("Centraal beheer van industriële CSTR-installaties, reactorvolumeflows en de actieve dual-valence additiefsamenstelling per werf.")

    st.info("💡 **Enterprise Asset Management:** Selecteer een bestaande installatie of voeg een nieuwe werf toe. Alle instellingen worden direct gekoppeld aan de actieve plant.")

    # Initialiseer de installatielijst in session_state
    if "installations_dict" not in st.session_state:
        st.session_state.installations_dict = {
            "Corte Pila (Italië) - 1MW CSTR": {
                "flow": 500.0,
                "volume": 3500.0,
                "temp": 38.5,
                "fe2o3": 35,
                "feo": 35,
                "target_h2s": 80,
                "status": "Actief (Optimized)"
            },
            "BioEnergy Noord (Nederland) - 0.8MW": {
                "flow": 400.0,
                "volume": 2800.0,
                "temp": 38.0,
                "fe2o3": 35,
                "feo": 35,
                "target_h2s": 90,
                "status": "Actief (Standard)"
            },
            "Biogás Sur (Frankrijk) - 1.2MW": {
                "flow": 600.0,
                "volume": 4200.0,
                "temp": 39.0,
                "fe2o3": 40,
                "target_h2s": 75,
                "status": "In Kalibratie"
            }
        }

    if "active_plant" not in st.session_state:
        st.session_state.active_plant = list(st.session_state.installations_dict.keys())[0]

    col_sel1, col_sel2 = st.columns([2, 1])
    
    with col_sel1:
        selected_plant = st.selectbox(
            "🏭 Selecteer Actieve Werf / Installatie",
            list(st.session_state.installations_dict.keys()),
            index=list(st.session_state.installations_dict.keys()).index(st.session_state.active_plant)
        )
        st.session_state.active_plant = selected_plant

    with col_sel2:
        with st.expander("➕ Nieuwe Werf Toevoegen"):
            new_plant_name = st.text_input("Naam & Capaciteit (bijv. BioPlant DE - 1MW)")
            if st.button("Voeg Toe"):
                if new_plant_name and new_plant_name not in st.session_state.installations_dict:
                    st.session_state.installations_dict[new_plant_name] = {
                        "flow": 500.0,
                        "volume": 3500.0,
                        "temp": 38.5,
                        "fe2o3": 35,
                        "feo": 35,
                        "target_h2s": 80,
                        "status": "Nieuw"
                    }
                    st.session_state.active_plant = new_plant_name
                    st.success(f"Werf '{new_plant_name}' toegevoegd!")
                    st.rerun()

    # Haal de data op van de momenteel geselecteerde plant
    plant_data = st.session_state.installations_dict[selected_plant]

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🏭 Reactor & Procesparameters")
        biogas_flow = st.number_input("Nominaal Biogasdebiet (m³/h)", value=float(plant_data["flow"]), step=10.0, key="cfg_flow")
        reactor_volume = st.number_input("Reactor Volume (m³)", value=float(plant_data["volume"]), step=50.0, key="cfg_vol")
        reactor_temp = st.number_input("Verteringstemperatuur (°C)", value=float(plant_data["temp"]), step=0.5, format="%.1f", key="cfg_temp")
        reactor_type = st.selectbox("Type Verter", ["CSTR (Continu Stirred-Tank Reactor)", "Plug Flow Reactor", "Upflow Anaerobic Sludge Blanket (UASB)"])

    with col2:
        st.markdown("### 🧪 Additief & Chemie Specificatie")
        fe2o3_pct = st.slider("Fe₂O₃ Percentage (%)", 0, 100, int(plant_data["fe2o3"]), key="cfg_fe2o3")
        feo_pct = st.slider("FeO Percentage (%)", 0, 100, int(plant_data["feo"]), key="cfg_feo")
        
        total_active = fe2o3_pct + feo_pct
        st.markdown(f"**Totaal Actieve Componenten:** {total_active}%")
        if total_active != 70:
            st.warning("⚠️ Standaard BioOptima formulering adviseert een gebalanceerde 35%/35% dual-valence mix.")
        else:
            st.success("✅ Dual-valence balans optimaal ingesteld (35% Fe₂O₃ / 35% FeO).")

        target_h2s = st.number_input("Doel H₂S vloeistoffase (ppm)", value=int(plant_data["target_h2s"]), min_value=20, max_value=200, key="cfg_h2s")

    st.markdown("---")
    if st.button("💾 Opslaan & Validatie Configuratie voor deze Werf"):
        # Sla wijzigingen direct op in het dictionary van deze specifieke plant
        plant_data["flow"] = biogas_flow
        plant_data["volume"] = reactor_volume
        plant_data["temp"] = reactor_temp
        plant_data["fe2o3"] = fe2o3_pct
        plant_data["feo"] = feo_pct
        plant_data["target_h2s"] = target_h2s
        st.success(f"Configuratie voor **{selected_plant}** succesvol opgeslagen en doorgevoerd naar het kinetisch model!")