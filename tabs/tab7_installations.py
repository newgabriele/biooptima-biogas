# tabs/tab7_installations.py
import streamlit as st
import pandas as pd
import json
import os

DATA_FILE = "clients_db.json"

def load_clients_db():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def render():
    st.subheader("⚙️ Tab 7: Installaties & Predictieve Data Nauwkeurigheid")
    st.markdown(
        "Dit dashboard toont het operationele overzicht van alle actieve installaties, "
        "de **predictieve data nauwkeurigheid** van de ingevoerde parameters voor betrouwbare simulaties, "
        "en de operationele veiligheidsnorm zoals de **H₂S bovengrens (< 100 ppm)**."
    )
    st.markdown("---")

    if "clients_db" not in st.session_state:
        st.session_state.clients_db = load_clients_db()

    # Bereken statistieken en predictieve datanauwkeurigheid automatisch uit de database
    total_installations = 0
    total_fields = 0
    valid_fields = 0
    
    for client_name, client_data in st.session_state.clients_db.items():
        for inst_name, inst_meta in client_data.get("installations", {}).items():
            total_installations += 1
            for key in ["volume_m3", "flow_m3_h", "ph_nominal", "temp_c"]:
                total_fields += 1
                val = inst_meta.get(key)
                if val is not None and not pd.isna(val) and val > 0:
                    valid_fields += 1

    data_accuracy = (valid_fields / total_fields * 100) if total_fields > 0 else 100.0

    # 📊 KPI Kaartjes met Predictieve Data Nauwkeurigheid & H2S Norm
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="📊 Actieve Installaties", value=total_installations, help="Totaal aantal geregistreerde installaties in de portefeuille")
    with col2:
        st.metric(label="🎯 Predictieve Data Nauwkeurigheid", value=f"{data_accuracy:.1f}%", help="Datakwaliteit en volledigheid voor kinetische en economische simulaties")
    with col3:
        st.metric(label="⚠️ H₂S Bovengrens Norm", value="< 100 ppm", help="Strenge operationele veiligheidsgrens voor ruw biogas / desulfurisatie")

    st.markdown("---")
    st.markdown("### 📋 Gedetailleerd Portefeuilleoverzicht per Klant")

    if not st.session_state.clients_db:
        st.warning("⚠️ Nog geen installaties gevonden. Voeg deze toe via Tab 1.")
        return

    for client_name, client_data in st.session_state.clients_db.items():
        with st.expander(f"🏢 Klant: {client_name}", expanded=True):
            installations = client_data.get("installations", {})
            if not installations:
                st.info("Geen installaties geregistreerd voor deze klant.")
                continue

            inst_list = []
            for i_name, i_meta in installations.items():
                inst_list.append({
                    "Installatie": i_name,
                    "Type": i_meta.get("inst_type", "agro"),
                    "Regime": i_meta.get("temp_regime", "Mesofiel"),
                    "Volume (m³)": i_meta.get("volume_m3", 0),
                    "Debiet (m³/h)": i_meta.get("flow_m3_h", 0),
                    "Temperatuur (°C)": i_meta.get("temp_c", 38.5),
                    "pH": i_meta.get("ph_nominal", 7.65),
                    "SBG Product": i_meta.get("sbg_product", "SBG Agro")
                })
            
            df_client = pd.DataFrame(inst_list)
            st.dataframe(df_client, use_container_width=True)