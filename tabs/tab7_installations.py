# tabs/tab7_installations.py
import streamlit as st
import pandas as pd
import json
import os
from formulas import process_imported_plant_data

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
    st.subheader("⚙️ Tab 7: Installaties, Data Import & Predictieve Nauwkeurigheid")
    st.markdown(
        "Beheer hier uw installaties, upload externe meetdata (sensorlogging, lab-uitslagen, VFA/TAC) "
        "en bekijk de predictieve data nauwkeurigheid. **Belangrijk:** Geïmporteerde meetdata wordt via `formulas.py` "
        "verwerkt en centraal opgeslagen in `st.session_state.processed_plant_data`, zodat alle andere tabbladen "
        "hier direct gebruik van kunnen maken."
    )
    st.markdown("---")

    if "clients_db" not in st.session_state:
        st.session_state.clients_db = load_clients_db()

    # 🏢 1. Selecteer eerst de installatie voor de upload
    st.markdown("### 🏢 Installatie Selectie voor Upload")
    installatie_opties = ["Merlara", "Installatie 2", "Installatie 3"]  # Pas eventueel aan naar jouw installaties
    gekozen_installatie = st.selectbox(
        "Selecteer de installatie waarvoor het bestand bestemd is:",
        options=installatie_opties,
        key="tab7_installatie_select"
    )

    # 🔍 2. Controleer of er al data aanwezig is voor deze installatie in het geheugen
    current_key = f"uploaded_data_{gekozen_installatie.lower()}"
    if current_key in st.session_state:
        saved_file_info = st.session_state[current_key]
        st.success(
            f"📁 **Actief geladen voor {gekozen_installatie}:** "
            f"`{saved_file_info['filename']}` "
            f"({saved_file_info['processed']['total_rows']} rijen beschikbaar in geheugen)."
        )
    else:
        st.info(f"ℹ️ Er is nog geen bestand geladen voor **{gekozen_installatie}**. Upload hieronder een dataset om te beginnen.")

    # 📥 3. Externe Data Import Sectie
    st.markdown(f"### 📥 Externe Meetdata Importeren voor **{gekozen_installatie}** (CSV / Excel)")
    uploaded_file = st.file_uploader(
        f"Upload een CSV- of Excel-bestand voor {gekozen_installatie}",
        type=["csv", "xlsx", "xls"],
        key="tab7_file_uploader"
    )

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_imported = pd.read_csv(uploaded_file)
            else:
                df_imported = pd.read_excel(uploaded_file)
            
            processed_result = process_imported_plant_data(df_imported)
            
            # Sla op in zowel de globale processed_plant_data als de installatie-specifieke key
            st.session_state.processed_plant_data = processed_result
            st.session_state[current_key] = {
                "filename": uploaded_file.name,
                "data": df_imported,
                "processed": processed_result
            }
            
            st.success(f"✅ Bestand '{uploaded_file.name}' succesvol ingelezen voor **{gekozen_installatie}** en gestandaardiseerd ({processed_result['total_rows']} rijen).")
            st.rerun()
        except Exception as e:
            st.error(f"Fout bij het inlezen en verwerken van het bestand: {e}")

    has_external_data = "processed_plant_data" in st.session_state and st.session_state.processed_plant_data.get("status") == "success"

    # Bereken statistieken en predictieve datanauwkeurigheid uit de configuratie
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

    base_accuracy = (valid_fields / total_fields * 100) if total_fields > 0 else 100.0

    st.markdown("---")

    # 📊 KPI Kaartjes
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="📊 Actieve Installaties", value=total_installations, help="Totaal aantal geregistreerde installaties in de portefeuille")
    with col2:
        accuracy_display = f"{base_accuracy:.1f}%" + (" (+ Externe Data Verwerkt)" if has_external_data else "")
        st.metric(label="🎯 Predictieve Data Nauwkeurigheid", value=accuracy_display, help="Datakwaliteit gebaseerd op configuratie en gekoppelde meetsets")
    with col3:
        st.metric(label="⚠️ H₂S Bovengrens Norm", value="< 100 ppm", help="Strenge operationele veiligheidsgrens voor ruw biogas / desulfurisatie")

    if has_external_data:
        data_summary = st.session_state.processed_plant_data
        with st.expander(f"🔍 Preview Verwerkte Externe Meetdata ({gekozen_installatie})", expanded=False):
            st.dataframe(data_summary["raw_data"].head(10), use_container_width=True)
            if "avg_h2s" in data_summary:
                st.info(f"💡 Gedetecteerde gemiddelde H₂S in upload: **{data_summary['avg_h2s']:.1f} ppm**. Andere tabs kunnen dit direct uitlezen.")

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