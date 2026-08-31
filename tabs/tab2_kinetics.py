# tabs/tab2_kinetics.py
import streamlit as st
import pandas as pd
import numpy as np
import os
import json

# Importeer centrale formules uit formulas.py
import formulas

DATA_FILE = "clients_db.json"

@st.cache_data
def load_substrates_db():
    """Zoekt en laadt substrates_cleaned.csv op meerdere mogelijke locaties inclusief werkmap."""
    current_cwd = os.getcwd()
    base_dir = os.path.dirname(os.path.abspath(__file__)) # tabs/ map
    root_dir = os.path.dirname(base_dir) # hoofdmap

    possible_paths = [
        os.path.join(current_cwd, "substrates_cleaned.csv"),
        os.path.join(current_cwd, "Substrates_Cleaned.csv"),
        "substrates_cleaned.csv",
        os.path.join(root_dir, "substrates_cleaned.csv"),
        os.path.join(base_dir, "substrates_cleaned.csv"),
        r"C:\BiogasApp\substrates_cleaned.csv",
        r"C:\biogasapp\substrates_cleaned.csv"
    ]

    for path in possible_paths:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                return df, path
            except Exception:
                pass
    
    # Dynamisch zoeken naar bestanden met 'substrate' of 'cleaned'
    search_dirs = [current_cwd, root_dir, base_dir, r"C:\BiogasApp", r"C:\biogasapp"]
    for d in search_dirs:
        if os.path.exists(d):
            try:
                for file in os.listdir(d):
                    if "substrate" in file.lower() and file.endswith(".csv"):
                        full_path = os.path.join(d, file)
                        if os.path.isfile(full_path):
                            df = pd.read_csv(full_path)
                            return df, full_path
            except Exception:
                pass

    # Fallback ingebouwde standaardbibliotheek
    fallback_data = {
        "Substraat": [
            "Maïskuil (Hoofdsubstraat)", "Rundvee Drijfmest", "Varkensmest", 
            "Kippenmest", "Glycerine / Eiwitrijk Co-product", "Vetslurven / Vet", 
            "Grasuil / Grasland", "Aardappelresten / Zetmeel", "Recirculaat (Digestaat)"
        ],
        "DS (%)": [35.0, 9.0, 6.5, 30.0, 85.0, 90.0, 30.0, 22.0, 5.0],
        "oDS (% oDS)": [92.0, 80.0, 75.0, 85.0, 98.0, 95.0, 90.0, 95.0, 60.0],
        "Biogaspotentieel (m³/ton)": [210.0, 55.0, 40.0, 120.0, 650.0, 950.0, 170.0, 320.0, 0.0]
    }
    return pd.DataFrame(fallback_data), None

def render():
    st.subheader("⚙️ Tab 2: Kinetica, H₂S Systeem & Kantoorplanning")
    
    # --- LAAD SUBSTRAAT DATABASE ---
    df_subs_lib, found_path = load_substrates_db()
    has_csv_lib = found_path is not None

    if has_csv_lib:
        st.success(f"✅ Substraatbibliotheek geladen uit `{found_path}`.")
    else:
        st.info("ℹ️ `substrates_cleaned.csv` niet gevonden; ingebouwde standaardbibliotheek wordt gebruikt.")

    df_subs_lib.columns = [c.strip() for c in df_subs_lib.columns]
    sub_col = next((c for c in df_subs_lib.columns if 'substraat' in c.lower() or 'name' in c.lower() or 'product' in c.lower()), df_subs_lib.columns[0])
    available_substrates = df_subs_lib[sub_col].dropna().unique().tolist()

    # --- INSTALLATIE SELECTIE UIT TAB 1 DATABASE ---
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
        meta = {}

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
    with col_info1: st.metric(label="Type", value=inst_type.upper())
    with col_info2: st.metric(label="Reactor Volume", value=f"{volume_m3} m³")
    with col_info3: st.metric(label="Biogas Debiet", value=f"{flow_m3_h} m³/h")
    with col_info4: st.metric(label="Temperatuur", value=f"{temp_c} °C")
    with col_info5: st.metric(label="Nominale pH", value=f"{ph_nominal}")

    if has_ext:
        st.info("💡 *Opmerking: Parameters zijn verrijkt met geüploade meetdata uit Tab 7.*")

    st.markdown("---")

    # --- SUBTABS ---
    tab_theorie, tab_operationeel = st.tabs(["🔬 Theorie & Kinetica", "📋 Operationeel & 9-Daagse Planning"])

    with tab_theorie:
        st.markdown("### 🔬 Chemische Achtergrond & SBG Additiefselectie")
        st.markdown(
            "Dit gedeelte behandelt de reactiekinetica voor desulfurisatie op basis van de professionele "
            "productlijnen: **SBG agro**, **SBG energo** en **SBG industrial**."
        )
        
        with st.expander("📖 Productspecificaties & Werking H₂S Reductie", expanded=False):
            st.markdown(
                "* **Waterstofsulfide ($H_2S$)** ontstaat door biologische afbraak van eiwitten en moet onder de **100 ppm** norm blijven ter bescherming van de WKK."
                "\n* **SBG Productlijnen:**"
                "\n  * **SBG agro**: Geoptimaliseerd voor reguliere agrarische co-vergisting met een stabiele basismest- en maïsmatrix."
                "\n  * **SBG energo**: Speciaal ontwikkeld voor energie-intensieve flex-installaties met hoge organische belastingen."
                "\n  * **SBG industrial**: Zware industriële formulering voor co-productenstromen met hoge zwavelvrachten."
            )

        col_k1, col_k2, col_k3, col_k4 = st.columns(4)
        with col_k1: sbg_product = st.selectbox("Selecteer SBG Product", ["SBG agro", "SBG energo", "SBG industrial"], key="tab2_sbg_product")
        with col_k2: h2s_raw = st.number_input("Ruw Biogas H₂S (ppm)", min_value=100, max_value=10000, value=2500, step=100, key="tab2_h2s_raw")
        with col_k3: h2s_target = st.number_input("Doel H₂S (ppm)", min_value=10, max_value=500, value=80, step=10, key="tab2_h2s_target")
        with col_k4: fe_ratio = st.number_input("Molaire Fe:S Verhouding", min_value=1.0, max_value=3.0, value=1.2, step=0.05, key="tab2_fe_ratio")

        # Berekening via formulas.py
        mass_h2s_kg, mass_fe_needed, total_dose = formulas.calculate_h2s_dosages(flow_m3_h, h2s_raw, temp_c, fe_ratio, sbg_product)

        m1, m2, m3 = st.columns(3)
        with m1: st.metric(label="📉 H₂S Vracht", value=f"{mass_h2s_kg:.2f} kg/dag")
        with m2: st.metric(label="🧪 Actief Fe Benodigd", value=f"{mass_fe_needed:.2f} kg/dag")
        with m3: st.metric(label=f"📦 Dosering ({sbg_product})", value=f"{total_dose:.1f} kg/dag")

        st.markdown(f"### 📈 Kinetische Reactiecurve: Resterende H₂S vs. Dosering ({sbg_product})")
        dosage_range = np.linspace(0, max(total_dose * 2.0, 10.0), 60)
        simulated_h2s = h2s_raw * np.exp(-1.6 * (dosage_range / max(total_dose, 1.0)))
        
        df_kinetics = pd.DataFrame({
            f"Dosering {sbg_product} (kg/dag)": dosage_range,
            "Resterende H₂S (ppm)": simulated_h2s
        })
        st.line_chart(df_kinetics.set_index(f"Dosering {sbg_product} (kg/dag)"))

    with tab_operationeel:
        st.markdown("### 📋 Kantoor & Planning: Substraatspecificatie & 9-Daagse Voedingshorizon")
        st.markdown(
            f"Beheer hier het **substraatrecept** (ton/dag direct naast aandeel %) en bekijk de **9-daagse voedingshorizon** "
            f"specifiek doorgerekend voor installatie **{plant_name}**."
        )

        # Realistisch standaardrecept zuiver gekalibreerd op 1 MW / 500 m³/h (~12.500 m³/dag biogas)
        default_recipe_data = [
            {"Substraat": available_substrates[0] if available_substrates else "Maïskuil", "Tonnage (ton/dag)": 45.0, "DS (%)": 35.0, "oDS (% oDS)": 92.0, "Biogaspotentieel (m³/ton)": 210.0},
            {"Substraat": available_substrates[1] if len(available_substrates) > 1 else "Rundvee Drijfmest", "Tonnage (ton/dag)": 25.0, "DS (%)": 9.0, "oDS (% oDS)": 80.0, "Biogaspotentieel (m³/ton)": 55.0},
            {"Substraat": available_substrates[2] if len(available_substrates) > 2 else "Varkensmest", "Tonnage (ton/dag)": 10.0, "DS (%)": 6.5, "oDS (% oDS)": 75.0, "Biogaspotentieel (m³/ton)": 40.0},
            {"Substraat": available_substrates[3] if len(available_substrates) > 3 else "Glycerine", "Tonnage (ton/dag)": 2.0, "DS (%)": 85.0, "oDS (% oDS)": 98.0, "Biogaspotentieel (m³/ton)": 650.0},
            {"Substraat": available_substrates[-1] if len(available_substrates) > 4 else "Recirculaat", "Tonnage (ton/dag)": 10.0, "DS (%)": 5.0, "oDS (% oDS)": 60.0, "Biogaspotentieel (m³/ton)": 0.0}
        ]

        stored_recipe = meta.get("recipe", default_recipe_data)
        recipe_state_key = f"recipe_df_{selected_inst_name}"

        if recipe_state_key not in st.session_state or st.session_state.get("last_selected_inst") != selected_inst_name:
            df_temp = pd.DataFrame(stored_recipe)
            if "Tonnage (ton/dag)" not in df_temp.columns:
                df_temp["Tonnage (ton/dag)"] = df_temp.get("Aandeel (%)", 20.0)
            
            for col, default_val in [("Substraat", available_substrates[0]), ("Tonnage (ton/dag)", 10.0), ("DS (%)", 30.0), ("oDS (% oDS)", 90.0), ("Biogaspotentieel (m³/ton)", 200.0)]:
                if col not in df_temp.columns:
                    df_temp[col] = default_val

            tot = df_temp["Tonnage (ton/dag)"].sum()
            df_temp["Aandeel (%)"] = (df_temp["Tonnage (ton/dag)"] / tot * 100.0) if tot > 0 else 0.0

            # Strikte volgorde van links naar rechts: Substraat -> Tonnage -> Aandeel -> DS -> oDS -> Biogaspotentieel
            st.session_state[recipe_state_key] = df_temp[["Substraat", "Tonnage (ton/dag)", "Aandeel (%)", "DS (%)", "oDS (% oDS)", "Biogaspotentieel (m³/ton)"]]
            st.session_state.last_selected_inst = selected_inst_name

        st.markdown(f"#### 🛠️ 1. Substraatrecept Beheren voor: *{selected_inst_name}*")
        
        edited_recipe = st.data_editor(
            st.session_state[recipe_state_key],
            use_container_width=True,
            key=f"recipe_editor_{selected_inst_name}",
            num_rows="dynamic",
            column_config={
                "Substraat": st.column_config.SelectboxColumn("Substraat Naam / Product", options=available_substrates, required=True),
                "Tonnage (ton/dag)": st.column_config.NumberColumn("Tonnage (ton/dag)", format="%.1f ton", min_value=0.0, step=1.0),
                "Aandeel (%)": st.column_config.NumberColumn("Aandeel (%)", format="%.1f%%", disabled=True),
                "DS (%)": st.column_config.NumberColumn("Drogestof (DS %)", format="%.1f%%", step=0.5),
                "oDS (% oDS)": st.column_config.NumberColumn("Organische DS (%)", format="%.1f%%", step=0.5),
                "Biogaspotentieel (m³/ton)": st.column_config.NumberColumn("Biogaspotentieel (m³/ton)", format="%.1f", step=10.0)
            }
        )

        # Berekeningen via formulas.py
        total_tonnage_day, avg_ds, avg_ods, total_expected_biogas_recipe = formulas.calculate_recipe_totals(edited_recipe)
        organic_loading_rate = formulas.calculate_organic_loading_rate(total_tonnage_day, avg_ds, avg_ods, volume_m3)

        if total_tonnage_day > 0:
            edited_recipe["Aandeel (%)"] = (edited_recipe["Tonnage (ton/dag)"] / total_tonnage_day) * 100.0
        else:
            edited_recipe["Aandeel (%)"] = 0.0

        st.session_state[recipe_state_key] = edited_recipe
        target_biogas_flow = flow_m3_h * 24.0

        if st.button("💾 Sla dit recept op voor deze installatie in database", key=f"save_recipe_btn_{selected_inst_name}"):
            meta["recipe"] = edited_recipe[["Substraat", "Tonnage (ton/dag)", "DS (%)", "oDS (% oDS)", "Biogaspotentieel (m³/ton)"]].to_dict(orient="records")
            if " — " in selected_inst_name:
                c_name, i_name = selected_inst_name.split(" — ", 1)
                if c_name in st.session_state.clients_db and "installations" in st.session_state.clients_db[c_name]:
                    if i_name in st.session_state.clients_db[c_name]["installations"]:
                        st.session_state.clients_db[c_name]["installations"][i_name]["recipe"] = meta["recipe"]
                        try:
                            with open(DATA_FILE, "w", encoding="utf-8") as f:
                                json.dump(st.session_state.clients_db, f, indent=4, ensure_ascii=False)
                            st.success(f"✅ Recept opgeslagen in database voor **{selected_inst_name}**!")
                        except Exception as e:
                            st.error(f"Fout bij wegschrijven naar database: {e}")

        col_m1, col_m2 = st.columns(2)
        with col_m1: st.metric(label="📊 Totale Biomassa Input", value=f"{total_tonnage_day:.1f} ton/dag")
        with col_m2: st.metric(label="⚡ Verwacht Biogas uit Recept", value=f"{total_expected_biogas_recipe:,.0f} m³/dag", delta=f"Doel debiet: {target_biogas_flow:,.0f} m³/dag")

        if total_expected_biogas_recipe < (target_biogas_flow * 0.85):
            st.warning(f"⚠️ **Capaciteitswaarschuwing:** Dit recept levert ca. **{total_expected_biogas_recipe:,.0f} m³/dag** biogas. Dat is te weinig om het ingestelde debiet van **{target_biogas_flow:,.0f} m³/dag** ({flow_m3_h} m³/h) te halen.")
        elif total_expected_biogas_recipe > (target_biogas_flow * 1.15):
            st.info(f"💡 **Info:** Dit recept levert meer biogas ({total_expected_biogas_recipe:,.0f} m³/dag) dan het nominale debiet ({target_biogas_flow:,.0f} m³/dag).")
        else:
            st.success(f"✅ **Balans OK:** Dit substraatrecept komt keurig overeen met de capaciteit van de installatie ({target_biogas_flow:,.0f} m³/dag).")

        st.markdown("---")
        st.markdown("#### 📅 2. Automatische 9-Daagse Voedingshorizon & Productieprognose")

        horizon_days = 9
        dates = pd.date_range(start=pd.Timestamp.today().normalize(), periods=horizon_days, freq="D")
        np.random.seed(42)
        fluctuations = np.random.normal(1.0, 0.02, horizon_days)

        horizon_records = []
        base_tonnage_day = total_tonnage_day if total_tonnage_day > 0 else 100.0
        avg_biogas_pot = (total_expected_biogas_recipe / total_tonnage_day) if total_tonnage_day > 0 else 200.0

        for i, d in enumerate(dates):
            factor = fluctuations[i]
            daily_ton = base_tonnage_day * factor
            expected_gas = daily_ton * avg_biogas_pot
            organic_load_day = daily_ton * (avg_ds / 100.0) * (avg_ods / 100.0)

            horizon_records.append({
                "Datum": d.strftime("%d-%m-%Y"),
                "Dag": f"Dag {i+1}",
                "Totale Biomassa (ton/dag)": round(daily_ton, 1),
                "Gem. DS (%)": round(avg_ds, 1),
                "Organische Belasting (ton oDS/dag)": round(organic_load_day, 2),
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

        st.info(f"💡 **Planning Resultaat:** Met deze invoer van `{base_tonnage_day:.1f} ton/dag` en een reactorvolume van `{volume_m3} m³` bedraagt de organische belasting ca. **{organic_loading_rate:.2f} kg oDS / m³·dag**.")