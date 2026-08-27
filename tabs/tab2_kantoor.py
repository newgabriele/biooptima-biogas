# tabs/tab2_kantoor.py
import streamlit as st
import pandas as pd
import numpy as np
import datetime
from utils.calculations import calculate_process_metrics, TARGET_BIOGAS_FLOW

def render_tab2(selected_customer, selected_plant, reactor_vol, gas_stripping_factor, selected_lang="Nederlands", is_admin=True, temp_regime="Mesofiel (~38°C)"):
    st.markdown(f"### 🎛️ {selected_customer} — {selected_plant} | Kantoor & Receptbeheer")

    if not is_admin:
        st.info("ℹ️ **Klant / Gebruiker Modus:** U voert hier data in voor uw installatie en heeft inzicht in globale proceskennis. Geavanceerde R&D-testparameters en code-generatie zijn voorbehouden aan de Administrator.")
    else:
        st.success(f"🔓 **Administrator Modus Actief:** Volledige controle voor beheer, testen en procescode-generatie. Actief regime: {temp_regime}")

    defaults = {
        "Maissilage": 25.0,
        "Drijfmest (rund)": 120.0,
        "Kippenmest": 10.0,
        "Glycerine": 2.0
    }
    recirc_defaults = {
        "Maissilage": 0.0,
        "Drijfmest (rund)": 40.0,
        "Kippenmest": 0.0,
        "Glycerine": 0.0
    }

    for sub, def_val in defaults.items():
        if f"input_ton_{sub}" not in st.session_state:
            st.session_state[f"input_ton_{sub}"] = def_val

    for sub, def_val in recirc_defaults.items():
        if f"input_recirc_{sub}" not in st.session_state:
            st.session_state[f"input_recirc_{sub}"] = def_val

    sub_specs = {
        "Maissilage": {"dm": 32.0, "odm": 95.0, "s": 0.12},
        "Drijfmest (rund)": {"dm": 8.5, "odm": 75.0, "s": 0.45},
        "Kippenmest": {"dm": 35.0, "odm": 80.0, "s": 0.85},
        "Glycerine": {"dm": 95.0, "odm": 98.0, "s": 0.05}
    }

    b1, b2, b3, b4 = st.columns([1.5, 1, 1, 1.5])
    with b1:
        auto_balance_clicked = st.button("⚖️ Auto-Balance (500 m³/h Doel)", type="primary", use_container_width=True)
    with b2:
        reset_clicked = st.button("🔄 Reset", type="secondary", use_container_width=True)
    with b3:
        if is_admin:
            approve_clicked = st.button("💾 Genereer Test / Master Code", type="secondary", use_container_width=True)
        else:
            approve_clicked = st.button("💾 Gegevens Opslaan", type="secondary", use_container_width=True)
    with b4:
        st.empty()

    if reset_clicked:
        for sub, def_val in defaults.items():
            st.session_state[f"input_ton_{sub}"] = def_val
        for sub, def_val in recirc_defaults.items():
            st.session_state[f"input_recirc_{sub}"] = def_val
        st.success("🔄 Standaardwaarden hersteld!")
        st.rerun()

    if auto_balance_clicked:
        target_odm_total = (TARGET_BIOGAS_FLOW * 24.0) / 0.6  
        
        co_odm_sum = 0.0
        mais_odm_per_ton = 1.0
        
        for sub, specs in sub_specs.items():
            ton = st.session_state[f"input_ton_{sub}"]
            recirc = st.session_state[f"input_recirc_{sub}"]
            eff_dm = (specs["dm"] / 100.0) * (1.0 - 0.35 * (recirc / 100.0))
            odm_p_ton = 1000 * eff_dm * (specs["odm"] / 100.0)
            
            if "Mais" in sub:
                mais_odm_per_ton = odm_p_ton
            else:
                co_odm_sum += ton * odm_p_ton
                
        remaining_odm = target_odm_total - co_odm_sum
        if remaining_odm < 0:
            remaining_odm = 0.0
            st.warning("⚠️ Co-substraten overschreiden reeds het 500 m³/h ijkpunt! Maissilage is op 0 gezet.")
            
        if mais_odm_per_ton > 0:
            new_mais = remaining_odm / mais_odm_per_ton
            st.session_state["input_ton_Maissilage"] = round(max(0.0, new_mais), 1)

        kippenmest_ton = st.session_state["input_ton_Kippenmest"]
        glycerine_ton = st.session_state["input_ton_Glycerine"]
        extra_dry_load = max(0.0, kippenmest_ton - 10.0) * 0.8 + max(0.0, glycerine_ton - 2.0) * 1.5
        new_recirc_drijfmest = min(85.0, max(30.0, 40.0 + extra_dry_load))
        
        st.session_state["input_recirc_Drijfmest (rund)"] = round(new_recirc_drijfmest, 1)

        st.success(f"⚖️ Auto-Balance doorgevoerd! Recirculatie op drijfmest aangepast naar {st.session_state['input_recirc_Drijfmest (rund)']}% vakkundig bijgestuurd.")
        st.rerun()

    if approve_clicked:
        if is_admin:
            st.success("🔑 Master Code succesvol gegenereerd in Administrator test-omgeving!")
        else:
            st.success("💾 Invoer en recept succesvol opgeslagen voor installatie!")

    st.markdown("##### 📝 Actieve Substraat Invoer & Recirculatie Beheer")
    
    col_headers = st.columns([2, 1.2, 1.2, 1.2, 1.2, 1.5])
    col_headers[0].markdown("**Substraat**")
    col_headers[1].markdown("**ton/d**")
    col_headers[2].markdown("**DM %**")
    col_headers[3].markdown("**ODM %**")
    col_headers[4].markdown("**S %**")
    col_headers[5].markdown("**Recirc. %**")

    df_rows = []
    for sub, specs in sub_specs.items():
        c = st.columns([2, 1.2, 1.2, 1.2, 1.2, 1.5])
        c[0].write(sub)
        
        t_val = c[1].number_input(
            f"ton_{sub}", 
            min_value=0.0, max_value=500.0, 
            step=1.0, label_visibility="collapsed", key=f"input_ton_{sub}"
        )
        
        c[2].write(f"{specs['dm']}%")
        c[3].write(f"{specs['odm']}%")
        c[4].write(f"{specs['s']}%")
        
        r_val = c[5].number_input(
            f"recirc_{sub}", 
            min_value=0.0, max_value=100.0, 
            step=5.0, label_visibility="collapsed", key=f"input_recirc_{sub}"
        )

        df_rows.append({
            "Substraat": sub,
            "ton/d": t_val,
            "DM %": specs["dm"],
            "ODM %": specs["odm"],
            "S %": specs["s"],
            "Recirc. %": r_val
        })

    active_recipe_df = pd.DataFrame(df_rows)

    metrics = calculate_process_metrics(active_recipe_df, reactor_vol, gas_stripping_factor, temp_regime)
    current_olr = metrics["current_olr"]
    current_vzv = metrics["current_vzv"]
    avg_dm_system = metrics["avg_dm"]
    calc_biogas = metrics["calc_biogas"]
    total_substraat_dag = metrics["total_substraat"]
    product_needed_kg = metrics["product_needed"]
    bags_needed_day = metrics["bags_needed"]
    current_hrt = metrics["current_hrt"]
    min_safe_hrt = metrics["min_safe_hrt"]

    st.markdown("---")
    st.markdown("##### 📊 Live KPI's & Ijkpunt 500 m³/h (H2S Doel: ~80 ppm)")

    olr_alert = current_olr > metrics["max_safe_olr"]
    vzv_alert = current_vzv > 50.0
    dm_alert = avg_dm_system > 14.0 or avg_dm_system < 6.0
    hrt_alert = current_hrt < min_safe_hrt
    
    if olr_alert or vzv_alert or dm_alert or hrt_alert:
        reasons = []
        if olr_alert: reasons.append(f"OLR te hoog ({current_olr:.2f} > {metrics['max_safe_olr']})")
        if vzv_alert: reasons.append(f"VZV verzuringsrisico ({current_vzv:.1f} > 50)")
        if dm_alert: reasons.append(f"Systeem DM buiten marge ({avg_dm_system:.1f}%)")
        if hrt_alert: reasons.append(f"Tijdsregime/HRT te kort ({current_hrt:.1f}d < min {min_safe_hrt}d)")
        st.error(f"🔴 **Proces Alert:** " + " | ".join(reasons) + ". Controleer uw invoer of pas het tijdsregime aan.")
    else:
        st.success("🟢 **Systeem Status: Optimaal binnen alle veiligheidsmarges (Doel H2S ~80 ppm via DIET/IJzer)**")

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Totale Invoer", f"{total_substraat_dag:.1f} ton/d")
    with m2:
        st.metric("Berekende OLR", f"{current_olr:.2f} kg/m³d", delta=f"Max {metrics['max_safe_olr']}" if olr_alert else "Veilig", delta_color="inverse" if olr_alert else "normal")
    with m3:
        st.metric("Tijdsregime (HRT)", f"{current_hrt:.1f} dagen", delta=f"Min {min_safe_hrt}d", delta_color="inverse" if hrt_alert else "normal")
    with m4:
        biogas_delta = f"{calc_biogas - TARGET_BIOGAS_FLOW:+.1f} m³/h"
        st.metric("Biogas Ijkpunt", f"{calc_biogas:.1f} m³/h", delta=biogas_delta, delta_color="off")
    with m5:
        st.metric("Benodigd IJzer", f"{product_needed_kg:.1f} kg/d", delta=f"{int(bags_needed_day)} zakken")

    st.markdown("---")
    st.markdown("##### 📈 Planningshorizon (-2 Dagen tot +5 Dagen in de Toekomst)")
    st.info("💡 Globale kennis & theoretische simulatie van de installatieprestaties over een horizon van 8 dagen.")

    today = datetime.date.today()
    horizon_days = [(today + datetime.timedelta(days=i)) for i in range(-2, 6)]
    horizon_labels = [d.strftime("%d-%m (%a)") for d in horizon_days]
    horizon_labels[2] = "Vandaag (T0)"

    vars_biogas = [1.02, 0.96, 1.0, 1.05, 0.97, 1.03, 0.98, 1.01]
    vars_substraat = [0.99, 1.02, 1.0, 0.95, 1.04, 0.98, 1.02, 0.97]
    vars_product = [0.97, 1.04, 1.0, 1.02, 0.96, 1.05, 0.99, 1.03]
    vals_h2s = [82.0, 77.5, 80.0, 84.5, 76.0, 83.0, 78.5, 81.0]

    horizon_df = pd.DataFrame({
        "Dag": horizon_labels,
        "Biogas (m³/h)": [round(calc_biogas * v, 1) for v in vars_biogas],
        "Substraat (ton/d)": [round(total_substraat_dag * v, 1) for v in vars_substraat],
        "IJzerproduct (kg/d)": [round(product_needed_kg * v, 1) for v in vars_product],
        "H2S (ppm)": vals_h2s
    }).set_index("Dag")

    st.line_chart(horizon_df)

    st.markdown("---")
    st.markdown("##### 👥 Ploegendienst & Operator Planning (7 Dagen)")
    st.info("💡 Verdeling over de drie dagdelen: Ochtend (06:00 - 14:00), Middag (14:00 - 22:00) en Nacht (22:00 - 06:00).")

    shift_days = [(today + datetime.timedelta(days=i)) for i in range(7)]
    shift_day_labels = [d.strftime("%d-%m (%a)") for d in shift_days]

    shift_data = {
        "Dag": shift_day_labels,
        "Ochtend (06:00 - 14:00)": ["Pietro", "Guido", "Ali", "Franco", "Mohammed", "Salvatore", "Aldo"],
        "Middag (14:00 - 22:00)": ["Salvatore", "Aldo", "Pietro", "Guido", "Ali", "Franco", "Mohammed"],
        "Nacht (22:00 - 06:00)": ["Franco", "Mohammed", "Salvatore", "Aldo", "Pietro", "Guido", "Ali"]
    }
    
    shift_df = pd.DataFrame(shift_data).set_index("Dag")
    st.dataframe(shift_df, use_container_width=True)