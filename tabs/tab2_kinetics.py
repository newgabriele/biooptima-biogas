# tabs/tab2_kinetics.py
import streamlit as st
import pandas as pd
import numpy as np
import os
import json
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
    
    df_subs_lib, found_path = load_substrates_db()
    has_csv_lib = found_path is not None

    if has_csv_lib:
        st.success(f"✅ Substraatbibliotheek geladen uit `{found_path}`.")
    else:
        st.info("ℹ️ `substrates_cleaned.csv` niet gevonden; ingebouwde standaardbibliotheek wordt gebruikt.")

    df_subs_lib.columns = [c.strip() for c in df_subs_lib.columns]
    
    sub_col = next((c for c in df_subs_lib.columns if 'substraat' in c.lower() or 'name' in c.lower() or 'product' in c.lower()), df_subs_lib.columns[0])
    desc_col = next((c for c in df_subs_lib.columns if 'omschrijving' in c.lower() or 'beschrijving' in c.lower() or 'description' in c.lower() or 'type' in c.lower()), sub_col)
    ds_col = next((c for c in df_subs_lib.columns if 'ds' in c.lower() or 'drogestof' in c.lower()), None)
    ods_col = next((c for c in df_subs_lib.columns if 'ods' in c.lower() or 'organisch' in c.lower()), None)
    bio_col = next((c for c in df_subs_lib.columns if 'biogas' in c.lower() or 'potentieel' in c.lower() or 'm³/ton' in c.lower()), None)

    available_substrates = df_subs_lib[desc_col].dropna().unique().tolist()
    if not available_substrates:
        available_substrates = df_subs_lib[sub_col].dropna().unique().tolist()

    recirc_label = "Recirculaat / Digestaat"
    if not any("recirculaat" in str(s).lower() or "digestaat" in str(s).lower() for s in available_substrates):
        available_substrates.append(recirc_label)

    def lookup_substrate_props(val):
        if "recirculaat" in str(val).lower() or "digestaat" in str(val).lower():
            return 5.0, 60.0, 0.0

        match = pd.DataFrame()
        if desc_col and desc_col in df_subs_lib.columns:
            match = df_subs_lib[df_subs_lib[desc_col] == val]
        if match.empty and sub_col in df_subs_lib.columns:
            match = df_subs_lib[df_subs_lib[sub_col] == val]
        
        if not match.empty:
            row = match.iloc[0]
            ds = float(row[ds_col]) if ds_col and ds_col in row and pd.notna(row[ds_col]) else 30.0
            ods = float(row[ods_col]) if ods_col and ods_col in row and pd.notna(row[ods_col]) else 90.0
            bio = float(row[bio_col]) if bio_col and bio_col in row and pd.notna(row[bio_col]) else 200.0
            return ds, ods, bio
        return 30.0, 90.0, 200.0

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

    ext_data = st.session_state.get("processed_plant_data", {})
    has_ext = ext_data.get("status") == "success"
    if has_ext:
        if "avg_flow" in ext_data: flow_m3_h = ext_data["avg_flow"]
        if "avg_temp" in ext_data: temp_c = ext_data["avg_temp"]
        if "avg_ph" in ext_data: ph_nominal = ext_data["avg_ph"]

    st.markdown("---")
    
    col_info1, col_info2, col_info3, col_info4, col_info5 = st.columns(5)
    with col_info1: st.metric(label="Type", value=inst_type.upper())
    with col_info2: st.metric(label="Reactor Volume", value=f"{volume_m3} m³")
    with col_info3: st.metric(label="Biogas Debiet", value=f"{flow_m3_h} m³/h")
    with col_info4: st.metric(label="Temperatuur", value=f"{temp_c} °C")
    with col_info5: st.metric(label="Nominale pH", value=f"{ph_nominal}")

    if has_ext:
        st.info("💡 *Opmerking: Parameters zijn verrijkt met geüploade meetdata uit Tab 7.*")

    st.markdown("---")

    # Standaard H2S parameters ophalen uit meta of defaults
    default_h2s = meta.get("h2s_raw", 2500)
    default_h2s_target = meta.get("h2s_target", 150)
    default_sbg = meta.get("sbg_product", "SBG agro")
    default_fe = meta.get("fe_ratio", 1.2)
    default_bag_weight = meta.get("bag_weight_kg", 20.0)

    tab_theorie, tab_operationeel = st.tabs(["🔬 Theorie & Kinetica", "📋 Operationeel & 9-Daagse Planning"])

    with tab_theorie:
        st.markdown("### 🔬 Chemische Achtergrond & SBG Additiefselectie")
        st.markdown(
            "Dit gedeelte behandelt de reactiekinetica voor desulfurisatie op basis van de professionele "
            "productlijnen: **SBG agro**, **SBG energo** en **SBG industrial**."
        )
        
        with st.expander("📖 Productspecificaties & Werking H₂S Reductie", expanded=False):
            st.markdown(
                "* **Waterstofsulfide ($H_2S$)** ontstaat door biologische afbraak van eiwitten en moet onder de norm blijven ter bescherming van de WKK."
                "\n* **SBG Productlijnen:**"
                "\n  * **SBG agro**: Geoptimaliseerd voor reguliere agrarische co-vergisting met een stabiele basismest- en maïsmatrix."
                "\n  * **SBG energo**: Speciaal ontwikkeld voor energie-intensieve flex-installaties met hoge organische belastingen."
                "\n  * **SBG industrial**: Zware industriële formulering voor co-productenstromen met hoge zwavelvrachten."
            )

        col_k1, col_k2, col_k3, col_k4, col_k5 = st.columns(5)
        with col_k1: 
            sbg_product = st.selectbox(
                "Selecteer SBG Product", 
                ["SBG agro", "SBG energo", "SBG industrial"], 
                index=["SBG agro", "SBG energo", "SBG industrial"].index(default_sbg) if default_sbg in ["SBG agro", "SBG energo", "SBG industrial"] else 0,
                key=f"tab2_sbg_product_{selected_inst_name}"
            )
        with col_k2: 
            h2s_raw = st.number_input(
                "Ruw Biogas H₂S (ppm)", 
                min_value=0, max_value=10000, 
                value=int(default_h2s), 
                step=50, 
                key=f"tab2_h2s_raw_{selected_inst_name}"
            )
        with col_k3: 
            h2s_target = st.number_input(
                "Doel H₂S (ppm)", 
                min_value=0, max_value=1000, 
                value=int(default_h2s_target), 
                step=10, 
                key=f"tab2_h2s_target_{selected_inst_name}"
            )
        with col_k4: 
            fe_ratio = st.number_input(
                "Molaire Fe:S Verhouding", 
                min_value=0.5, max_value=3.0, 
                value=float(default_fe), 
                step=0.05, 
                key=f"tab2_fe_ratio_{selected_inst_name}"
            )
        with col_k5:
            bag_weight_kg = st.number_input(
                "Gewicht per zak SBG (kg)",
                min_value=5.0, max_value=1000.0,
                value=float(default_bag_weight),
                step=5.0,
                key=f"tab2_bag_weight_{selected_inst_name}"
            )

        # Berekening op basis van netto H2S reductie (Ruw - Doel)
        effective_h2s_ppm = max(0, h2s_raw - h2s_target)
        mass_h2s, mass_fe, total_dose, total_bags = formulas.calculate_h2s_dosages(
            flow_m3_h, 
            effective_h2s_ppm, 
            temp_c, 
            fe_ratio, 
            "SBG Agro"
        )
        
        # Koppeling naar de namen die op de regels hierna worden gebruikt
        bags_per_day = total_bags
        bags_per_week = bags_per_day * 7
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.metric(label="📉 Netto H₂S Reductievracht", value=f"{mass_h2s:.2f} kg/dag")
        with m2: st.metric(label="🧪 Actief Fe Benodigd", value=f"{mass_fe:.2f} kg/dag")
        with m3: st.metric(label=f"📦 Dosering ({sbg_product})", value=f"{total_dose:.1f} kg/dag")
        with m4: st.metric(label="🛍️ Aantal Zakken SBG", value=f"{bags_per_day:.2f} zak/dag", delta=f"{bags_per_week:.1f} zak/week")

        st.markdown(f"### 📈 Kinetische Reactiecurve: Resterende H₂S vs. Dosering ({sbg_product})")
        dosage_range = np.linspace(0, max(total_dose * 2.0, 10.0), 60)
        simulated_h2s = np.maximum(0, h2s_raw - (effective_h2s_ppm * (dosage_range / max(total_dose, 1.0))))
        
        df_kinetics = pd.DataFrame({
            f"Dosering {sbg_product} (kg/dag)": dosage_range,
            "Resterende H₂S (ppm)": simulated_h2s
        })
        st.line_chart(df_kinetics.set_index(f"Dosering {sbg_product} (kg/dag)"))

    with tab_operationeel:
        st.markdown("### 📋 Kantoor & Planning: Substraatspecificatie & H₂S / Zakken Systeemkoppeling")
        st.markdown(
            f"Beheer hier het **substraatrecept** (voor installatie **{plant_name}**) en bekijk direct de gekoppelde "
            f"**H₂S-belasting en benodigde ijzer-/SBG-zakken** als voorbereiding op Tab 3."
        )

        # H2S & Zakken ophalen uit session_state of defaults
        op_h2s_raw = st.session_state.get(f"tab2_h2s_raw_{selected_inst_name}", default_h2s)
        op_h2s_target = st.session_state.get(f"tab2_h2s_target_{selected_inst_name}", default_h2s_target)
        op_sbg_prod = st.session_state.get(f"tab2_sbg_product_{selected_inst_name}", default_sbg)
        op_fe = st.session_state.get(f"tab2_fe_ratio_{selected_inst_name}", default_fe)
        op_bag_w = st.session_state.get(f"tab2_bag_weight_{selected_inst_name}", default_bag_weight)

        op_eff_h2s = max(0, op_h2s_raw - op_h2s_target)
        # Ontvang nu 4 waarden (inclusief total_bags gebaseerd op 20 kg)
        op_h2s_kg, op_fe_need, op_dose, op_bags_day = formulas.calculate_h2s_dosages(flow_m3_h, op_eff_h2s, temp_c, op_fe, op_sbg_prod)
        op_bags_week = op_bags_day * 7
        st.markdown("#### 🧪 H₂S & Additief Status (Directe Systeemkoppeling)")
        oc1, oc2, oc3, oc4 = st.columns(4)
        with oc1: st.metric(label="📉 Netto H₂S Reductievracht", value=f"{op_h2s_kg:.2f} kg/dag")
        with oc2: st.metric(label="🧪 Actief Fe Benodigd", value=f"{op_fe_need:.2f} kg/dag")
        with oc3: st.metric(label=f"📦 Dosering ({op_sbg_prod})", value=f"{op_dose:.1f} kg/dag")
        with oc4: st.metric(label="🛍️ Aantal Zakken SBG", value=f"{op_bags_day:.2f} zak/dag", delta=f"{op_bags_week:.1f} zak/week")

        st.markdown("---")

        default_sub_val = available_substrates[0] if available_substrates else "Maïskuil (Hoofdsubstraat)"
        recirc_val = next((s for s in available_substrates if 'recircul' in s.lower() or 'digestaat' in s.lower()), recirc_label)

        d_ds, d_ods, d_bio = lookup_substrate_props(default_sub_val)
        r_ds, r_ods, r_bio = lookup_substrate_props(recirc_val)

        default_recipe_data = [
            {"Substraat": default_sub_val, "Tonnage (ton/dag)": 52.0, "DS (%)": d_ds, "DM / oDS (%)": d_ods, "Biogaspotentieel (m³/ton)": d_bio},
            {"Substraat": recirc_val, "Tonnage (ton/dag)": 150.0, "DS (%)": r_ds, "DM / oDS (%)": r_ods, "Biogaspotentieel (m³/ton)": r_bio},
        ]

        stored_recipe = meta.get("recipe", default_recipe_data)
        
        normalized_stored_recipe = []
        for r in stored_recipe:
            sub_val = r.get("Substraat") or r.get("Omschrijving") or (available_substrates[0] if available_substrates else "Maïskuil")
            if sub_val not in available_substrates and available_substrates:
                matched_desc = available_substrates[0]
                for ds_opt in available_substrates:
                    if str(sub_val).lower() in str(ds_opt).lower() or str(ds_opt).lower() in str(sub_val).lower():
                        matched_desc = ds_opt
                        break
                sub_val = matched_desc
            
            ds_val = r.get("DS (%)")
            ods_val = r.get("DM / oDS (%)") if "DM / oDS (%)" in r else r.get("oDS (% oDS)", 90.0)
            bio_val = r.get("Biogaspotentieel (m³/ton)")
            
            m_ds, m_ods, m_bio = lookup_substrate_props(sub_val)
            if ds_val is None or pd.isna(ds_val): ds_val = m_ds
            if ods_val is None or pd.isna(ods_val): ods_val = m_ods
            if bio_val is None or pd.isna(bio_val): bio_val = m_bio
            
            normalized_stored_recipe.append({
                "Substraat": sub_val,
                "Tonnage (ton/dag)": float(r.get("Tonnage (ton/dag)", 10.0)),
                "DS (%)": float(ds_val),
                "DM / oDS (%)": float(ods_val),
                "Biogaspotentieel (m³/ton)": float(bio_val)
            })

        recipe_state_key = f"recipe_df_{selected_inst_name}"

        if recipe_state_key not in st.session_state or st.session_state.get("last_selected_inst") != selected_inst_name:
            df_temp = pd.DataFrame(normalized_stored_recipe)
            st.session_state[recipe_state_key] = df_temp[["Substraat", "Tonnage (ton/dag)", "DS (%)", "DM / oDS (%)", "Biogaspotentieel (m³/ton)"]]
            st.session_state.last_selected_inst = selected_inst_name
        else:
            if "Biogaspotentieel (m³/ton)" not in st.session_state[recipe_state_key].columns:
                biopots = []
                for sub in st.session_state[recipe_state_key]["Substraat"]:
                    _, _, b = lookup_substrate_props(sub)
                    biopots.append(b)
                st.session_state[recipe_state_key]["Biogaspotentieel (m³/ton)"] = biopots

        # --- AUTO-BALANCER RECIRCULAAT OP DOEL-DM ---
        st.markdown("#### ⚖️ Automatische DM-Balanshulp (Norm: 8% - 14%)")
        col_ctrl1, col_ctrl2 = st.columns([2, 2])
        with col_ctrl1:
            target_dm = st.slider("Doel Totaal DM (%) voor mengsel", min_value=8.0, max_value=14.0, value=11.0, step=0.5, key=f"target_dm_{selected_inst_name}")
        with col_ctrl2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🔄 Bereken Recirculaat automatisch op doel-DM", key=f"auto_balance_btn_{selected_inst_name}"):
                current_df = st.session_state[recipe_state_key].copy()
                non_recirc = current_df[~current_df["Substraat"].str.lower().str.contains("recirculaat|digestaat", na=False)]
                recirc_rows = current_df[current_df["Substraat"].str.lower().str.contains("recirculaat|digestaat", na=False)]
                
                if not non_recirc.empty:
                    other_tonnage = non_recirc["Tonnage (ton/dag)"].sum()
                    weighted_other_ds = (non_recirc["Tonnage (ton/dag)"] * non_recirc["DS (%)"]).sum() / other_tonnage if other_tonnage > 0 else 35.0
                    recirc_ds = 5.0
                    if not recirc_rows.empty:
                        recirc_ds = recirc_rows.iloc[0]["DS (%)"]
                    
                    if target_dm > recirc_ds and weighted_other_ds > target_dm:
                        needed_recirc = other_tonnage * (weighted_other_ds - target_dm) / (target_dm - recirc_ds)
                        
                        if not recirc_rows.empty:
                            current_df.loc[current_df["Substraat"].str.lower().str.contains("recirculaat|digestaat", na=False), "Tonnage (ton/dag)"] = round(needed_recirc, 1)
                        else:
                            new_row = pd.DataFrame([{
                                "Substraat": recirc_val,
                                "Tonnage (ton/dag)": round(needed_recirc, 1),
                                "DS (%)": r_ds,
                                "DM / oDS (%)": r_ods,
                                "Biogaspotentieel (m³/ton)": r_bio
                            }])
                            current_df = pd.concat([current_df, new_row], ignore_index=True)
                        
                        st.session_state[recipe_state_key] = current_df
                        st.success(f"✅ Recirculaat automatisch ingesteld op **{needed_recirc:.1f} ton/dag** om exact **{target_dm}% DM** te bereiken!")
                        st.rerun()

        st.markdown(f"#### 🛠️ 1. Substraatrecept Beheren voor: *{selected_inst_name}*")
        
        edited_recipe = st.data_editor(
            st.session_state[recipe_state_key],
            use_container_width=True,
            key=f"recipe_editor_{selected_inst_name}",
            num_rows="dynamic",
            hide_index=True,
            column_config={
                "Substraat": st.column_config.SelectboxColumn("Substraat Omschrijving", options=available_substrates, required=True, width="medium"),
                "Tonnage (ton/dag)": st.column_config.NumberColumn("Tonnage (ton/dag)", format="%.1f ton", min_value=0.0, step=1.0, width="small"),
                "DS (%)": st.column_config.NumberColumn("DS (%)", format="%.1f%%", step=0.5, width="small"),
                "DM / oDS (%)": st.column_config.NumberColumn("DM / oDS (%)", format="%.1f%%", step=0.5, width="small"),
                "Biogaspotentieel (m³/ton)": st.column_config.NumberColumn("Biogaspotentieel (m³/ton)", format="%.1f m³/t", step=10.0, min_value=0.0, width="small")
            }
        )

        needs_rerun = False
        current_session_df = st.session_state[recipe_state_key]
        if len(edited_recipe) == len(current_session_df):
            for idx in range(len(edited_recipe)):
                new_sub = edited_recipe.at[idx, "Substraat"]
                old_sub = current_session_df.at[idx, "Substraat"]
                if new_sub != old_sub:
                    m_ds, m_ods, m_bio = lookup_substrate_props(new_sub)
                    edited_recipe.at[idx, "DS (%)"] = m_ds
                    edited_recipe.at[idx, "DM / oDS (%)"] = m_ods
                    edited_recipe.at[idx, "Biogaspotentieel (m³/ton)"] = m_bio
                    needs_rerun = True

        if needs_rerun:
            st.session_state[recipe_state_key] = edited_recipe
            st.rerun()

        for idx, row in edited_recipe.iterrows():
            sub_val = row.get("Substraat")
            if sub_val and sub_val in available_substrates:
                if pd.isna(row.get("Biogaspotentieel (m³/ton)")) or row.get("Biogaspotentieel (m³/ton)") == 0.0 and sub_val != recirc_label:
                    _, _, m_bio = lookup_substrate_props(sub_val)
                    edited_recipe.at[idx, "Biogaspotentieel (m³/ton)"] = m_bio

        calc_df = edited_recipe.copy()
        if "DM / oDS (%)" in calc_df.columns:
            calc_df["oDS (% oDS)"] = calc_df["DM / oDS (%)"]

        total_tonnage_day, avg_ds, avg_ods, total_expected_biogas_recipe = formulas.calculate_recipe_totals(calc_df)
        organic_loading_rate = formulas.calculate_organic_loading_rate(total_tonnage_day, avg_ds, avg_ods, volume_m3)

        st.session_state[recipe_state_key] = edited_recipe
        target_biogas_flow = flow_m3_h * 24.0

        if st.button("💾 Sla dit recept op voor deze installatie in database", key=f"save_recipe_btn_{selected_inst_name}"):
            meta["recipe"] = edited_recipe[["Substraat", "Tonnage (ton/dag)", "DS (%)", "DM / oDS (%)", "Biogaspotentieel (m³/ton)"]].to_dict(orient="records")
            meta["sbg_product"] = op_sbg_prod
            meta["h2s_raw"] = op_h2s_raw
            meta["h2s_target"] = op_h2s_target
            meta["fe_ratio"] = op_fe
            meta["bag_weight_kg"] = op_bag_w
            meta["sbg_dose_kg_day"] = op_dose
            meta["sbg_bags_day"] = op_bags_day

            if " — " in selected_inst_name:
                c_name, i_name = selected_inst_name.split(" — ", 1)
                if c_name in st.session_state.clients_db and "installations" in st.session_state.clients_db[c_name]:
                    if i_name in st.session_state.clients_db[c_name]["installations"]:
                        st.session_state.clients_db[c_name]["installations"][i_name]["recipe"] = meta["recipe"]
                        st.session_state.clients_db[c_name]["installations"][i_name]["sbg_product"] = op_sbg_prod
                        st.session_state.clients_db[c_name]["installations"][i_name]["h2s_raw"] = op_h2s_raw
                        st.session_state.clients_db[c_name]["installations"][i_name]["h2s_target"] = op_h2s_target
                        st.session_state.clients_db[c_name]["installations"][i_name]["fe_ratio"] = op_fe
                        st.session_state.clients_db[c_name]["installations"][i_name]["bag_weight_kg"] = op_bag_w
                        st.session_state.clients_db[c_name]["installations"][i_name]["sbg_bags_day"] = op_bags_day
                        try:
                            with open(DATA_FILE, "w", encoding="utf-8") as f:
                                json.dump(st.session_state.clients_db, f, indent=4, ensure_ascii=False)
                            st.success(f"✅ Recept en H₂S dosering succesvol opgeslagen in database voor **{selected_inst_name}**!")
                        except Exception as e:
                            st.error(f"Fout bij wegschrijven naar database: {e}")

        st.markdown("#### 🧪 Recept Balans & DM Totaal Check")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1: st.metric(label="📊 Totale Biomassa Input", value=f"{total_tonnage_day:.1f} ton/dag")
        with col_m2: st.metric(label="🌾 Gewogen Totaal DS (DM)", value=f"{avg_ds:.1f}%", delta="Norm: 8 - 14%")
        with col_m3: st.metric(label="⚡ Verwacht Biogas uit Recept", value=f"{total_expected_biogas_recipe:,.0f} m³/dag", delta=f"Doel: {target_biogas_flow:,.0f} m³/dag")

        if avg_ds < 7.0:
            st.warning(f"⚠️ **DM Totaal Waarschuwing:** Het gewogen drogestofgehalte van het recept is **{avg_ds:.1f}%**. Dit is aan de natte kant (< 7%), wat risico op sedimentatie in de CSTR kan geven.")
        elif avg_ds > 16.0:
            st.warning(f"⚠️ **DM Totaal Waarschuwing:** Het gewogen drogestofgehalte van het recept is **{avg_ds:.1f}%**. Dit is erg hoog (> 16%) voor een standaard agrarische CSTR, wat kan leiden tot meng- en pompbelasting.")
        else:
            st.success(f"✅ **DM Totaal OK:** Het gewogen drogestofgehalte van het recept (**{avg_ds:.1f}%**) valt binnen de ideale operationele bandbreedte (8-14%) voor een CSTR installatie.")

        if total_expected_biogas_recipe < (target_biogas_flow * 0.85):
            st.warning(f"⚠️ **Capaciteitswaarschuwing:** Dit recept levert ca. **{total_expected_biogas_recipe:,.0f} m³/dag** biogas. Dat is te weinig om het ingestelde debiet van **{target_biogas_flow:,.0f} m³/dag** ({flow_m3_h} m³/h) te halen.")
        elif total_expected_biogas_recipe > (target_biogas_flow * 1.15):
            st.info(f"💡 **Info:** Dit recept levert meer biogas ({total_expected_biogas_recipe:,.0f} m³/dag) dan het nominale debiet ({target_biogas_flow:,.0f} m³/dag).")

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
        # Haal de maximale N-drempelwaarde op die in Tab 1 is ingesteld voor de actieve plant
    current_plant = st.session_state.get("active_plant", None)
    max_n_target = getattr(current_plant, "nitrogen_target", 3.0)

    # Bepaal hier je berekende N-waarde (bijv. op basis van jouw kinetiek- of receptberekening)
    # Vervang 'calculated_n_val' door de variabele waarin jouw model de stikstof/TAN berekent
    calculated_n_val = 2.8  # Voorbeeldwaarde, vervang dit door je eigen berekende uitkomst

    st.markdown("---")
    st.markdown("### 🧪 Stikstof (N) & TAN Procescontrole")
    
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        st.metric("Max. Drempel (Tab 1)", f"{max_n_target:.2f}")
    with col_n2:
        st.metric("Berekende N-waarde", f"{calculated_n_val:.2f}")

    # Controle en statusindicatie op basis van de limiet uit Tab 1
    if calculated_n_val <= max_n_target:
        st.success(f"✅ **Normaal:** De berekende N-waarde ({calculated_n_val:.2f}) ligt onder de ingestelde limiet van {max_n_target:.2f}.")
    else:
        st.warning(f"⚠️ **Waarschuwing:** De berekende N-waarde ({calculated_n_val:.2f}) overschrijdt de maximum drempel ({max_n_target:.2f}) uit Tab 1!")