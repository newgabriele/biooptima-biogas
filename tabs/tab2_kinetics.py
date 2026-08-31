# tabs/tab2_kinetics.py
import streamlit as st
import pandas as pd
import numpy as np
import os
import json

DATA_FILE = "clients_db.json"

def render():
    st.subheader("⚙️ Tab 2: Kinetica, H₂S Systeem & Kantoorplanning")
    
    # --- INSTALLATIE SELECTIE UIT TAB 1 DATABASE (Globaal voor Tab 2) ---
    if "clients_db" not in st.session_state:
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    st.session_state.clients_db = json.load(f)
            except Exception:
                st.session_state.clients_db = {}
        else:
            st.session_state.clients_db = {}

    all_inst_options = []
    inst_lookup = {}
    for c_name, c_data in st.session_state.clients_db.items():
        for i_name, i_meta in c_data.get("installations", {}).items():
            display_name = f"{c_name} — {i_name}"
            all_inst_options.append(display_name)
            inst_lookup[display_name] = i_meta

    if all_inst_options:
        selected_inst_name = st.selectbox(
            "🏢 Selecteer actieve installatie (inlezen van gegevens uit Tab 1 database)",
            all_inst_options,
            key="tab2_installation_selector"
        )
        meta = inst_lookup[selected_inst_name]
        plant_name = selected_inst_name
        flow_m3_h = meta.get("flow_m3_h", 500.0)
        volume_m3 = meta.get("volume_m3", 2500.0)
        temp_c = meta.get("temp_c", 38.5)
        ph_nominal = meta.get("ph_nominal", 7.65)
        inst_type = meta.get("inst_type", "agro")
    else:
        st.warning("⚠️ Nog geen installaties gevonden in Tab 1 database. Standaardwaarden worden aangehouden.")
        plant_name = "Standaard CSTR Installatie"
        flow_m3_h = 500.0
        volume_m3 = 2500.0
        temp_c = 38.5
        ph_nominal = 7.65
        inst_type = "agro"

    # Externe meetdata controle uit Tab 7
    ext_data = st.session_state.get("processed_plant_data", {})
    has_ext = ext_data.get("status") == "success"
    if has_ext:
        if "avg_flow" in ext_data: flow_m3_h = ext_data["avg_flow"]
        if "avg_temp" in ext_data: temp_c = ext_data["avg_temp"]
        if "avg_ph" in ext_data: ph_nominal = ext_data["avg_ph"]

    st.markdown("---")
    
    # Overzicht parameters geselecteerde installatie
    col_info1, col_info2, col_info3, col_info4, col_info5 = st.columns(5)
    with col_info1:
        st.metric(label="Type", value=inst_type.upper())
    with col_info2:
        st.metric(label="Reactor Volume", value=f"{volume_m3} m³")
    with col_info3:
        st.metric(label="Biogas Debiet", value=f"{flow_m3_h} m³/h")
    with col_info4:
        st.metric(label="Temperatuur", value=f"{temp_c} °C")
    with col_info5:
        st.metric(label="Nominale pH", value=f"{ph_nominal}")

    if has_ext:
        st.info("💡 *Opmerking: Parameters zijn verrijkt met geüploade meetdata uit Tab 7.*")

    st.markdown("---")

    # --- SUBTABS CREËREN VOOR OVERZICHTELIJKHEID ---
    tab_theorie, tab_operationeel = st.tabs(["🔬 Theorie & Kinetica", "📋 Operationeel & 9-Daagse Planning"])

    with tab_theorie:
        st.markdown("### 🔬 Chemische Achtergrond & Kinetische Modellering")
        st.markdown(
            "Dit gedeelte behandelt de theoretische achtergrond van biologische en chemische desulfurisatie "
            "en de reactiekinetica voor het actieve additiefmengsel van **35% $\text{Fe}_2\text{O}_3$** en **35% $\text{FeO}$**."
        )
        
        with st.expander("📖 Uitgebreide Procesuitleg H₂S Reductie", expanded=False):
            st.markdown(
                "* **Waterstofsulfide ($H_2S$)** ontstaat door de afbraak van eiwitrijke biomassa in de CSTR-reactor. "
                "Dit gas is extreem corrosief voor WKK-installaties en gasopwerking en moet onder de **100 ppm** norm blijven."
                "\n* **Synergetische Werking Additieven:**"
                "\n  * De **$\text{FeO}$ fractie (35%)** reageert snel en direct in de vloeistoffase."
                "\n  * De **$\text{Fe}_2\text{O}_3$ fractie (35%)** zorgt voor een langdurige, bufferende capaciteit."
            )

        col_k1, col_k2, col_k3 = st.columns(3)
        with col_k1:
            h2s_raw = st.number_input("Ruw Biogas H₂S (ppm)", min_value=100, max_value=10000, value=2500, step=100, key="tab2_h2s_raw")
        with col_k2:
            h2s_target = st.number_input("Doel H₂S (ppm)", min_value=10, max_value=500, value=80, step=10, help="Operationele grens < 100 ppm", key="tab2_h2s_target")
        with col_k3:
            fe_ratio = st.number_input("Molaire Fe:S Verhouding", min_value=1.0, max_value=3.0, value=1.2, step=0.05, key="tab2_fe_ratio")

        daily_biogas = flow_m3_h * 24.0
        molar_volume_t = 0.0224 * ((temp_c + 273.15) / 273.15)
        mol_h2s = (daily_biogas * (h2s_raw / 1_000_000.0)) / molar_volume_t
        mass_h2s_kg = mol_h2s * 34.08 / 1000.0
        mass_fe_needed = mol_h2s * fe_ratio * 55.845 / 1000.0
        
        prod_fe2o3 = (mass_fe_needed * 0.5) / 0.35
        prod_feo = (mass_fe_needed * 0.5) / 0.35
        total_dose = prod_fe2o3 + prod_feo

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric(label="📉 H₂S Vracht", value=f"{mass_h2s_kg:.2f} kg/dag")
        with m2:
            st.metric(label="🧪 Actief Fe Benodigd", value=f"{mass_fe_needed:.2f} kg/dag")
        with m3:
            st.metric(label="📦 Aanbevolen Mengsel (35% Fe2O3 / 35% FeO)", value=f"{total_dose:.1f} kg/dag")

        st.markdown("### 📈 Kinetische Reactiecurve: Resterende H₂S vs. Additiefdosering")
        dosage_range = np.linspace(0, max(total_dose * 2.0, 10.0), 60)
        simulated_h2s = h2s_raw * np.exp(-1.5 * (dosage_range / max(total_dose, 1.0)))
        
        df_kinetics = pd.DataFrame({
            "Additief Dosering (kg/dag)": dosage_range,
            "Resterende H₂S (ppm)": simulated_h2s
        })
        st.line_chart(df_kinetics.set_index("Additief Dosering (kg/dag)"))

    with tab_operationeel:
        st.markdown("### 📋 Kantoor & Planning: Substraatspecificatie & 9-Daagse Voedingshorizon")
        st.markdown(
            f"Beheer hier het **substraatrecept** en bekijk de **9-daagse voedingshorizon** "
            f"specifiek doorgerekend voor installatie **{plant_name}**."
        )

        if "base_recipe_df" not in st.session_state:
            st.session_state.base_recipe_df = pd.DataFrame([
                {"Substraat": "Maïskuil (Hoofdsubstraat)", "Aandeel (%)": 45.0, "DS (%)": 35.0, "oDS (% oDS)": 92.0, "Biogaspotentieel (m³/ton)": 210.0},
                {"Substraat": "Rundvee Drijfmest", "Aandeel (%)": 30.0, "DS (%)": 9.0, "oDS (% oDS)": 80.0, "Biogaspotentieel (m³/ton)": 55.0},
                {"Substraat": "Varkensmest", "Aandeel (%)": 15.0, "DS (%)": 6.5, "oDS (% oDS)": 75.0, "Biogaspotentieel (m³/ton)": 40.0},
                {"Substraat": "Glycerine / Eiwitrijk Co-product", "Aandeel (%)": 10.0, "DS (%)": 85.0, "oDS (% oDS)": 98.0, "Biogaspotentieel (m³/ton)": 650.0}
            ])

        st.markdown("#### 🛠️ 1. Substraatrecept Beheren")
        edited_recipe = st.data_editor(
            st.session_state.base_recipe_df,
            use_container_width=True,
            key="recipe_editor_table",
            num_rows="dynamic",
            column_config={
                "Substraat": st.column_config.TextColumn("Substraat Naam / Product", required=True),
                "Aandeel (%)": st.column_config.NumberColumn("Aandeel (%)", format="%.1f%%", min_value=0.0, max_value=100.0, step=1.0),
                "DS (%)": st.column_config.NumberColumn("Drogestof (DS %)", format="%.1f%%", step=0.5),
                "oDS (% oDS)": st.column_config.NumberColumn("Organische DS (%)", format="%.1f%%", step=0.5),
                "Biogaspotentieel (m³/ton)": st.column_config.NumberColumn("Biogaspotentieel (m³/ton)", format="%.1f", step=10.0)
            }
        )

        total_share = edited_recipe["Aandeel (%)"].sum()
        if abs(total_share - 100.0) > 0.01:
            st.warning(f"⚠️ Let op: Het totale aandeel van het recept is **{total_share:.1f}%** (advies is exact 100%).")
        else:
            st.success("✅ Substraatrecept is perfect in balans (totaal 100%).")

        st.session_state.base_recipe_df = edited_recipe

        st.markdown("---")
        st.markdown("#### 📅 2. Automatische 9-Daagse Voedingshorizon & Productieprognose")

        horizon_days = 9
        dates = pd.date_range(start=pd.Timestamp.today().normalize(), periods=horizon_days, freq="D")
        
        np.random.seed(42)
        fluctuations = np.random.normal(1.0, 0.02, horizon_days)

        horizon_records = []
        base_tonnage_day = (flow_m3_h * 24.0) / 180.0

        total_pct = total_share if total_share > 0 else 100.0
        avg_biogas_pot = (edited_recipe["Aandeel (%)"] * edited_recipe["Biogaspotentieel (m³/ton)"]).sum() / total_pct
        avg_ds = (edited_recipe["Aandeel (%)"] * edited_recipe["DS (%)"]).sum() / total_pct
        avg_ods = (edited_recipe["Aandeel (%)"] * edited_recipe["oDS (% oDS)"]).sum() / total_pct

        for i, d in enumerate(dates):
            factor = fluctuations[i]
            daily_ton = base_tonnage_day * factor
            expected_gas = daily_ton * avg_biogas_pot
            organic_load = daily_ton * (avg_ds / 100.0) * (avg_ods / 100.0)

            horizon_records.append({
                "Datum": d.strftime("%d-%m-%Y"),
                "Dag": f"Dag {i+1}",
                "Totale Biomassa (ton/dag)": round(daily_ton, 1),
                "Gem. DS (%)": round(avg_ds, 1),
                "Organische Belasting (ton oDS/dag)": round(organic_load, 2),
                "Verwacht Biogas (m³/dag)": round(expected_gas, 0),
                "Status": "Definitief" if i < 3 else ("Voorlopig" if i < 6 else "Prognose")
            })

        df_horizon = pd.DataFrame(horizon_records)
        st.dataframe(df_horizon, use_container_width=True)

        st.markdown("### 📊 Productieprognose Biogas (9-Daagse Horizon)")
        df_chart_horizon = pd.DataFrame({
            "Dag": [r["Dag"] for r in horizon_records],
            "Verwacht Biogas (m³/dag)": [r["Verwacht Biogas (m³/dag)"] for r in horizon_records]
        }).set_index("Dag")
        st.bar_chart(df_chart_horizon)

        st.info(f"💡 **Planning Resultaat:** Met dit recept en een reactorvolume van `{volume_m3} m³` bedraagt de organische belasting ca. **{(base_tonnage_day * (avg_ds/100) * (avg_ods/100) / volume_m3):.2f} kg oDS / m³·dag**.")