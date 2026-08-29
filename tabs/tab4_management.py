import streamlit as st

def render():
    st.subheader("📈 Tab 4: Directie & Financiële ROI (Management Dashboard)")
    st.markdown("Consolidated executive audit, financial impact matrix, and net economic value creation per standard 1 MW CSTR asset (500 m³/h biogas flow)[cite: 2].")

    st.info("💡 **Total Net Value Creation:** Optimized operations deliver an estimated **+€85,000 to €175,000/year** in Net Economic ROI[cite: 2].")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💶 Financiële Rendementspijlers")
        st.markdown("""
        - **Power & Biomethane Revenue:** +€60,000 to €115,000/yr due to higher methane concentration (>5.20 kWh/m³) and gas volume expansion (+5.6% to +10.7%)[cite: 2].
        - **Feedstock Input Savings:** +€30,000 to €50,000/yr from a 3.5% to 5.0% reduction in raw substrate mass[cite: 2].
        - **Digestate Hauling & Spreading:** +€11,000 to €18,000/yr by minimizing total output mass[cite: 2].
        """)

    with col2:
        st.markdown("### 🛠️ OPEX & Onderhoudsbesparingen")
        st.markdown("""
        - **CHP Engine Protection:** +€6,000 to €10,000/yr by extending oil service intervals from 1,200–1,500 hours to 2,000+ operating hours[cite: 2].
        - **Activated Carbon Filtration:** +€12,000 to €25,000/yr via 100% filter bypass or extended media service life[cite: 2].
        - **ARBO / CAPEX Compliance:** Nul CAPEX investment needed, avoiding costly plant reconstructions.
        """)

    st.markdown("---")
    st.markdown("### 📊 Gecorrigeerde Bedrijfskosten- en ROI Matrix (1 MW Referentie)")
    
    data = [
        {"Parameter": "Raw H₂S Belasting", "Baseline": "400 – 900 ppm[cite: 2]", "Met BioOptima 360°": "< 100 ppm[cite: 2]", "Netto Financiële Impact": "-85% tot -90% acid corrosion load[cite: 2]"},
        {"Parameter": "Methaan & Energie", "Baseline": "53.5% CH₄ (4.97 kWh/m³)[cite: 2]", "Met BioOptima 360°": "54.8% – 56.5% CH₄ (>5.20 kWh/m³)[cite: 2]", "Netto Financiële Impact": "+€60,000 – €115,000/jaar[cite: 2]"},
        {"Parameter": "Feedstock Inkoop", "Baseline": "≈ 25,000 ton/jaar[cite: 2]", "Met BioOptima 360°": "-3.5% tot -5.0% massa[cite: 2]", "Netto Financiële Impact": "+€30,000 – €50,000/jaar[cite: 2]"},
        {"Parameter": "Digestate Afvoer", "Baseline": "≈ 23,000 ton/jaar[cite: 2]", "Met BioOptima 360°": "-800 tot -1,150 ton/jaar[cite: 2]", "Netto Financiële Impact": "+€11,000 – €18,000/jaar[cite: 2]"},
        {"Parameter": "CHP Olie & Onderhoud", "Baseline": "Elke 1,200 – 1,500 uur[cite: 2]", "Met BioOptima 360°": "2,000+ bedrijfsuren[cite: 2]", "Netto Financiële Impact": "+€6,000 – €10,000/jaar[cite: 2]"},
        {"Parameter": "Actieve Koolfilters", "Baseline": "Frequent filtervervanging[cite: 2]", "Met BioOptima 360°": "100% Bypass / Polishing[cite: 2]", "Netto Financiële Impact": "+€12,000 – €25,000/jaar[cite: 2]"}
    ]
    st.table(data)