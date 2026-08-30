# tabs/tab6_substrates.py
import streamlit as st
import pandas as pd
from formulas import optimize_least_cost_recipe, optimize_multiday_least_cost_recipe, calculate_substrate_sensitivity_analysis
from test_data import TEST_SUBSTRATES_DB

def render():
    st.subheader("🌾 Substraat- en Recepturenoptimalisatie (MPC & Marktanalyse)")
    st.markdown("Beheer de substraatdatabase, draai 7-daagse MPC scenario's en voer gevoeligheidsanalyses uit voor het grondstoffenteam.")

    # We splitsen Tab 6 op in twee sub-tabbladen voor maximale overzichtelijkheid
    sub_tab1, sub_tab2 = st.tabs(["📊 Least-Cost & 7d MPC Optimalisatie", "📈 Marktspecialist Gevoeligheidsanalyse"])

    with sub_tab1:
        st.markdown("### 📂 Externe Dataset Importeren (CSV / Excel)")
        uploaded_file = st.file_uploader("Upload eigen substraatbestand (.csv of .xlsx)", type=["csv", "xlsx"], key="sub_upload_file")
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_upload = pd.read_csv(uploaded_file)
                else:
                    df_upload = pd.read_excel(uploaded_file)
                    
                new_db = {}
                for _, row in df_upload.iterrows():
                    sub_name = str(row["substraat"]).strip().lower().replace(" ", "_")
                    new_db[sub_name] = {
                        "ts_pct": float(row["ts_pct"]),
                        "vs_pct": float(row["vs_pct"]),
                        "s_g_per_kg_ts": float(row["s_g_per_kg_ts"]),
                        "n_g_per_kg_ts": float(row.get("n_g_per_kg_ts", 10.0)),
                        "biogas_m3_per_ton_odm": float(row["biogas_m3_per_ton_odm"]),
                        "price_per_ton": float(row["price_per_ton"]),
                        "f_fast": float(row.get("f_fast", 0.3)),
                        "f_med": float(row.get("f_med", 0.5)),
                        "f_slow": float(row.get("f_slow", 0.2)),
                        "vfa_risk": float(row.get("vfa_risk", 1.0))
                    }
                st.session_state.substrates_db = new_db
                st.success(f"✅ Bestand '{uploaded_file.name}' succesvol ingeladen!")
            except Exception as e:
                st.error(f"⚠️ Fout bij inlezen: {e}")

        if st.button("📥 Laad Standaard Corte Pila Testdataset", key="btn_load_test_data"):
            st.session_state.substrates_db = TEST_SUBSTRATES_DB.copy()
            st.success("✅ Standaard testdataset ingeladen!")
            st.rerun()

        if "substrates_db" not in st.session_state:
            st.session_state.substrates_db = TEST_SUBSTRATES_DB

        st.markdown("---")
        st.markdown("### 📋 Overzicht Actieve Substraatdatabase")
        db_rows = []
        for sub_key, meta in st.session_state.substrates_db.items():
            db_rows.append({
                "Substraat": sub_key.replace("_", " ").title(),
                "Drogestof (TS %)": f"{meta.get('ts_pct', 0)*100:.1f}%",
                "Organische Stof (VS %)": f"{meta.get('vs_pct', 0)*100:.1f}%",
                "Zwavel (g/kg TS)": meta.get('s_g_per_kg_ts', 0),
                "Gasopbrengst (m³/ton ODM)": meta.get('biogas_m3_per_ton_odm', 0),
                "Standaard Prijs (€/ton)": meta.get('price_per_ton', 0)
            })
        st.dataframe(pd.DataFrame(db_rows), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### 💶 Marktprijs Beheer")
        sub_items = list(st.session_state.substrates_db.items())
        cols = st.columns(min(len(sub_items), 3))
        
        updated_prices = {}
        for idx, (sub, meta) in enumerate(sub_items):
            col_target = cols[idx % len(cols)]
            with col_target:
                updated_prices[sub] = st.number_input(
                    f"Prijs {sub.replace('_', ' ').title()} (€/ton)", 
                    -50.0, 200.0, 
                    float(meta.get("price_per_ton", 0.0)), 
                    1.0, 
                    key=f"price_input_{sub}"
                )

        st.markdown("---")
        st.markdown("### ⚙️ Optimalisatie & IJzerkoppeling")
        opt_mode = st.radio("Kies Optimalisatiemodus", ["Dagelijkse Least-Cost Receptuur", "7-Daagse Model Predictive Control (MPC) Horizon"])
        
        opt_col1, opt_col2, opt_col3, opt_col4 = st.columns(4)
        with opt_col1:
            target_gas = st.number_input("Doel Biogasproductie (m³/dag)", 5000.0, 30000.0, 12000.0, 500.0, key="opt_target_gas_input")
        with opt_col2:
            max_olr_limit = st.number_input("Maximale OLR (kg ODM/m³·d)", 5.0, 15.0, 11.5, 0.5, key="opt_max_olr_input")
        with opt_col3:
            max_tan_limit = st.number_input("Max. TAN Limiet (mg/L)", 1500.0, 5000.0, 3000.0, 100.0, key="opt_max_tan_input")
        with opt_col4:
            fe_price_input = st.number_input("IJzeradditief (€/kg)", 0.5, 5.0, 1.20, 0.05, key="opt_fe_price_input")

        if st.button("🚀 Voer Optimalisatie Uit", key="btn_calc_recipe_action"):
            if opt_mode == "Dagelijkse Least-Cost Receptuur":
                result = optimize_least_cost_recipe(
                    substrates_db=st.session_state.substrates_db,
                    substrate_prices=updated_prices,
                    target_daily_biogas_m3=target_gas,
                    reactor_volume_m3=2500.0,
                    max_olr=max_olr_limit,
                    max_tan_mg_l=max_tan_limit,
                    fe_product_price_per_kg=fe_price_input
                )

                if result["success"]:
                    st.success("✅ Optimale dagelijkse voermix berekend!")
                    m1, m2, m3, m4, m5 = st.columns(5)
                    m1.metric("Substraatkosten", f"€ {result['total_substrate_cost_eur']:,.2f}")
                    m2.metric("Ontzwavelingstotaal", f"€ {result['fe_cost_eur']:,.2f}", f"{result['fe_bags_day']} zakken")
                    m3.metric("Totale Kosten", f"€ {result['total_cost_eur']:,.2f} / dag")
                    m4.metric("Zwavelvracht (S)", f"{result['total_s_kg']} kg S/dag")
                    m5.metric("Est. TAN", f"{result['estimated_tan_mg_l']:,.0f} mg/L")

                    opt_df = pd.DataFrame([
                        {"Substraat": k.replace("_", " ").title(), "Optimale Tonage (ton/dag)": v, "Marktprijs (€/ton)": updated_prices[k], "Dagkosten (€)": round(v * updated_prices[k], 2)}
                        for k, v in result["optimal_diet"].items()
                    ])
                    st.dataframe(opt_df, use_container_width=True, hide_index=True)
                else:
                    st.error("⚠️ Geen sluitende oplossing gevonden.")
            else:
                mpc_result = optimize_multiday_least_cost_recipe(
                    substrates_db=st.session_state.substrates_db,
                    substrate_prices=updated_prices,
                    target_daily_biogas_m3=target_gas,
                    reactor_volume_m3=2500.0,
                    max_olr=max_olr_limit,
                    max_tan_mg_l=max_tan_limit,
                    fe_product_price_per_kg=fe_price_input,
                    horizon_days=7
                )
                if mpc_result["success"]:
                    st.success("✅ 7-daagse MPC voerstrategie berekend!")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Totale Horizon Kosten", f"€ {mpc_result['total_cost_eur']:,.2f}")
                    m2.metric("Substraatkosten", f"€ {mpc_result['total_substrate_cost_eur']:,.2f}")
                    m3.metric("IJzeradditief Kosten", f"€ {mpc_result['total_fe_cost_eur']:,.2f}")

                    schedule_rows = []
                    for day_item in mpc_result["schedule"]:
                        row_data = {
                            "Dag": day_item["dag"], 
                            "Substraat (€)": day_item["dag_sub_cost_eur"], 
                            "Fe Zakken": f"{day_item['fe_bags']} zak",
                            "Totaal (€)": day_item["dag_totaal_kosten_eur"],
                            "Biogas (m³)": day_item["dag_biogas_m3"]
                        }
                        for sub_k, tons in day_item["diet"].items():
                            row_data[sub_k.replace("_", " ").title() + " (t)"] = tons
                        schedule_rows.append(row_data)
                    st.dataframe(pd.DataFrame(schedule_rows), use_container_width=True, hide_index=True)
                else:
                    st.error("⚠️ Geen sluitende MPC oplossing gevonden.")

    with sub_tab2:
        st.markdown("### 📈 Prijsvolatiliteit & Gevoeligheidsanalyse")
        st.markdown("Analyseer hoe de optimale receptuur en dagkosten reageren op prijsschommelingen van een specifiek substraat.")
        
        if "substrates_db" not in st.session_state:
            st.session_state.substrates_db = TEST_SUBSTRATES_DB

        sens_sub = st.selectbox("Selecteer Substraat voor Scenario-analyse", list(st.session_state.substrates_db.keys()))
        
        if st.button("📊 Genereer Gevoeligheidsmatrix", key="btn_run_sensitivity"):
            # Haal huidige prijzen op uit session of standaard
            current_prices = {k: float(v.get("price_per_ton", 0.0)) for k, v in st.session_state.substrates_db.items()}
            
            sens_df = calculate_substrate_sensitivity_analysis(
                substrates_db=st.session_state.substrates_db,
                base_substrate_prices=current_prices,
                target_daily_biogas_m3=12000.0,
                reactor_volume_m3=2500.0,
                max_olr=11.5,
                target_substrate=sens_sub,
                price_variation_pct_range=[-50.0, -25.0, 0.0, 25.0, 50.0, 100.0]
            )
            
            st.success(f"✅ Gevoeligheidsanalyse voltooid voor **{sens_sub.replace('_', ' ').title()}**!")
            st.dataframe(sens_df, use_container_width=True, hide_index=True)
            
            # Eenvoudige visualisatie van de kostenimpact
            st.markdown("### 📉 Kostenimpact Grafiek")
            chart_data = sens_df.set_index("Prijsvariatie (%)")[["Totale Dagkosten (€/dag)"]]
            st.line_chart(chart_data)