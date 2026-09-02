import streamlit as st
import pandas as pd

def render():
    st.subheader("📈 Tab 4: Directie & Financiële ROI (Management Dashboard)")
    st.markdown("Consolidated executive audit, financial impact matrix, and net economic value creation per standard 1 MW CSTR asset (500 m³/h biogas flow).")

    # Zoek flexibel naar data in st.session_state
    df_raw = None
    source_name = "Geen"
    
    for key in list(st.session_state.keys()):
        if "uploaded_data" in key or key == "processed_plant_data":
            val = st.session_state[key]
            if isinstance(val, dict):
                if "data" in val and isinstance(val["data"], pd.DataFrame):
                    df_raw = val["data"]
                    source_name = key
                    break
                elif "raw_data" in val and isinstance(val["raw_data"], pd.DataFrame):
                    df_raw = val["raw_data"]
                    source_name = key
                    break
            elif isinstance(val, pd.DataFrame):
                df_raw = val
                source_name = key
                break

    if df_raw is not None:
        st.success(f"🟢 **Live Data Gekoppeld (bron: `{source_name}`):** {len(df_raw)} rijen beschikbaar voor analyse.")

        try:
            def get_val_by_keyword(keyword):
                # Doorzoek elke kolom in het DataFrame naar het trefwoord
                for col in df_raw.columns:
                    mask = df_raw[col].astype(str).str.contains(keyword, case=False, na=False, regex=False)
                    if mask.any():
                        # Zoek in dezelfde rijen naar numerieke waardes in het hele DataFrame
                        for val_col in df_raw.columns:
                            numeric_vals = pd.to_numeric(
                                df_raw[val_col].astype(str).str.strip().str.replace('.', '', regex=False).str.replace(',', '.', regex=False),
                                errors='coerce'
                            )
                            if numeric_vals[mask].notna().sum() > 0:
                                val_mean = numeric_vals[mask].mean()
                                if not pd.isna(val_mean):
                                    return val_mean
                return float('nan')

            # Zoek op unieke trefwoorden uit de Merlara dataset
            ch4_avg = get_val_by_keyword("CH4")
            h2s_avg = get_val_by_keyword("H2S")
            power = get_val_by_keyword("U5201")
            if pd.isna(power):
                power = get_val_by_keyword("Potenza")
            
            temp = get_val_by_keyword("Temperatura")

            st.markdown("### ⚡ Live Merlara Operationele Status (Auto-Scannend)")
            mcol1, mcol2, mcol3, mcol4 = st.columns(4)
            with mcol1:
                st.metric("Gem. CH₄", f"{ch4_avg:.1f}%" if not pd.isna(ch4_avg) else "N/B")
            with mcol2:
                st.metric("Gem. H₂S", f"{h2s_avg:.0f} ppm" if not pd.isna(h2s_avg) else "N/B")
            with mcol3:
                st.metric("WKK Vermogen", f"{power:.0f} kW" if not pd.isna(power) else "N/B")
            with mcol4:
                st.metric("Fermentator Temp", f"{temp:.1f} °C" if not pd.isna(temp) else "N/B")
            st.markdown("---")
        except Exception as e:
            st.warning(f"Kon metrische waarden niet berekenen: {e}")
    else:
        st.info("💡 **Tip:** Upload eerst een gegevensbestand via **Tab 7** om dit management dashboard automatisch te vullen.")

    st.info("💡 **Total Net Value Creation:** Optimized operations deliver an estimated **+€85,000 to €175,000/year** in Net Economic ROI.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💶 Financiële Rendementspijlers")
        st.markdown("""
        - **Power & Biomethane Revenue:** +€60,000 to €115,000/yr due to higher methane concentration (>5.20 kWh/m³) and gas volume expansion (+5.6% to +10.7%).
        - **Feedstock Input Savings:** +€30,000 to €50,000/yr from a 3.5% to 5.0% reduction in raw substrate mass.
        - **Digestate Hauling & Spreading:** +€11,000 to €18,000/yr by minimizing total output mass.
        """)

    with col2:
        st.markdown("### 🛠️ OPEX & Onderhoudsbesparingen")
        st.markdown("""
        - **CHP Engine Protection:** +€6,000 to €10,000/yr by extending oil service intervals from 1,200–1,500 hours to 2,000+ operating hours.
        - **Activated Carbon Filtration:** +€12,000 to €25,000/yr via 100% filter bypass or extended media service life.
        - **ARBO / CAPEX Compliance:** Nul CAPEX investment needed, avoiding costly plant reconstructions.
        """)

    st.markdown("---")
    st.markdown("### 📊 Gecorrigeerde Bedrijfskosten- en ROI Matrix (1 MW Referentie)")
    
    data = [
        {"Parameter": "Raw H₂S Belasting", "Baseline": "400 – 900 ppm", "Met BioOptima 360°": "< 100 ppm", "Netto Financiële Impact": "-85% tot -90% acid corrosion load"},
        {"Parameter": "Methaan & Energie", "Baseline": "53.5% CH₄ (4.97 kWh/m³)", "Met BioOptima 360°": "54.8% – 56.5% CH₄ (>5.20 kWh/m³)", "Netto Financiële Impact": "+€60,000 – €115,000/jaar"},
        {"Parameter": "Feedstock Inkoop", "Baseline": "≈ 25,000 ton/jaar", "Met BioOptima 360°": "-3.5% tot -5.0% massa", "Netto Financiële Impact": "+€30,000 – €50,000/jaar"},
        {"Parameter": "Digestate Afvoer", "Baseline": "≈ 23,000 ton/jaar", "Met BioOptima 360°": "-800 tot -1,150 ton/jaar", "Netto Financiële Impact": "+€11,000 – €18,000/jaar"},
        {"Parameter": "CHP Olie & Onderhoud", "Baseline": "Elke 1,200 – 1,500 uur", "Met BioOptima 360°": "2,000+ bedrijfsuren", "Netto Financiële Impact": "+€6,000 – €10,000/jaar"},
        {"Parameter": "Actieve Koolfilters", "Baseline": "Frequent filtervervanging", "Met BioOptima 360°": "100% Bypass / Polishing", "Netto Financiële Impact": "+€12,000 – €25,000/jaar"}
    ]
    st.table(data)