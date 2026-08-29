import streamlit as st

def render():
    st.subheader("🧪 Tab 2: Kinetisch Model & Gasexpansie")
    st.markdown("Biochemische kinetische modellering en berekening van de theoretische gasvolume-expansie en H₂S-binding voor de 1 MW referentie-installatie.")

    st.info("💡 **TalTech Validatie:** Kinetische simulaties tonen aan dat voorspellende micro-frequentiedosering van gebalanceerd Fe²⁺/Fe³⁺ zorgt voor een gasvolume-expansie van +5.6% tot +10.7%[cite: 2].")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📈 Kinetische Parameters & Werkingsmechanismen")
        st.markdown("""
        - **DIET Stimulatie:** Conductieve micro-ijzeroxiden versnellen direct syntrofa Verzadigde elektronenoverdracht tussen bacteriën en methanogenese[cite: 1, 2].
        - **Sulfide Toxiciteit Relief:** In-situ neerslag van FeS in de vloeistoffase herstelt de enzymkinetiek van methanogenen[cite: 2].
        - **VFA & OLR Beheersing:** Continue bewaking van de organische belasting over een rollende horizon van 9 dagen[cite: 1].
        """)

    with col2:
        st.markdown("### 📊 Gasexpansie Scenario's (500 m³/h Baseline)")
        scenario = st.selectbox(
            "Selecteer Bedrijfsscenario",
            [
                "Conservative Baseline (500 → <80 ppm H₂S)",
                "Typical Commercial Asset (900 → <80 ppm H₂S)",
                "High H₂S Co-Digestion (2,500 → <80 ppm H₂S)"
            ]
        )

        if "Conservative" in scenario:
            st.metric("Verwachte Yield Gain", "+5.56%", "Extra debiet: +668 m³/day[cite: 2]")
        elif "Typical" in scenario:
            st.metric("Verwachte Yield Gain", "+6.58%", "Extra debiet: +790 m³/day[cite: 2]")
        else:
            st.metric("Verwachte Yield Gain", "+10.67%", "Extra debiet: +1,280 m³/day[cite: 2]")

    st.markdown("---")
    st.markdown("### 📋 Stoichiometrische R&D Validatie Matrix")
    st.markdown("Overzicht van de theoretische versus gerealiseerde gas- en energieopbrengsten bij een nominaal debiet van 500 m³/h[cite: 2].")

    data = [
        {"Parameter": "Raw H₂S Reductie", "Standaard Bedrijf": "400 – 900 ppm", "Met BioOptima 360°": "< 100 ppm", "Effect": "-85% tot -90% corrosiebelasting[cite: 1, 2]"},
        {"Parameter": "Methaanconcentratie", "Standaard Bedrijf": "53.5% CH₄ (4.97 kWh/m³)", "Met BioOptima 360°": "54.8% – 56.5% CH₄ (>5.20 kWh/m³)", "Effect": "+€60k – €115k/jaar[cite: 2]"},
        {"Parameter": "Feedstock Inkoop", "Standaard Bedrijf": "≈ 25,000 ton/jaar", "Met BioOptima 360°": "-3.5% tot -5.0% massa", "Effect": "+€30k – €50k/jaar[cite: 2]"}
    ]
    st.table(data)