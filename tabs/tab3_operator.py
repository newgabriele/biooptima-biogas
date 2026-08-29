import streamlit as st

def render():
    st.subheader("👷 Tab 3: Operator Werkinstructies & 20kg Bag Dosing")
    st.markdown("Mobiel shift-dashboard voor operators en praktische dagelijkse doseringsinstructies van de verzegelde 20 kg zakken.")

    st.info("💡 **ARBO & Veiligheid:** Voldoet aan de strenge Europese en nationale normen (uiterlijk eind 2026) door het uitfaseren van stoffige 1.000 kg Big Bags ten gunste van ergonomische 20 kg zakken[cite: 1].")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🕒 Actieve Ploegendienst & Shift Status")
        shift = st.selectbox("Selecteer Huidige Ploeg", ["Ochtendploeg (06:00 - 14:00)", "Middagploeg (14:00 - 22:00)", "Nachtploeg (22:00 - 06:00)"])
        st.metric("Actueel Biogas Debiet", "500 m³/h", "Actieve Fe-Depot buffer in reactor[cite: 1]")
        
        st.markdown("#### 📋 Shift Doseringsinstructie")
        st.markdown("""
        - **Voorgeschreven Dosis:** Exact 3 zakken van 20 kg (totaal 60 kg) per shift.
        - **Invoerwijze:** Gecontroleerde handmatige toevoeging via de doseerhopper.
        - **Doel:** Handhaving van in-situ vloeistoffase H₂S beneden 100 ppm[cite: 1].
        """)

    with col2:
        st.markdown("### ✅ Shift Afmelding & Registratie")
        operator_name = st.text_input("Naam Operator", "Bijv. Jan de Vries")
        bags_used = st.number_input("Aantal gebruikte 20 kg zakken deze shift", min_value=0, max_value=10, value=3)
        shift_notes = st.text_area("Bijzonderheden / Observaties", "Geen schommelingen in VFA; ontzwaveling stabiel.")

        if st.button("💾 Registreer Shift Dosering"):
            st.success(f"Shift registratie succesvol opgeslagen voor {shift} door {operator_name}!")

    st.markdown("---")
    st.markdown("### 📦 Verpakkings- en Ergonomie Tijdlijn (ARBO 2026)")
    st.markdown("Overzicht van de transitie naar stofvrije micro-dosering.")

    data = [
        {"Tijdsframe": "Uiterlijk Eind 2026", "Verpakkingstype": "Big Bags (1.000 kg)", "Impact": "Uitfasering wegens ARBO-fijnstofnormen en chemische schommelingen."},
        {"Tijdsframe": "2026 – 2030 (Transitie)", "Verpakkingstype": "Handzame Zakken (20 kg)", "Impact": "Ergonomisch en hanteerbaar voor dagelijkse shift-frequentiedosering."},
        {"Tijdsframe": "Vanaf 2030", "Verpakkingstype": "1 kg Wateroplosbare Pouches", "Impact": "100% stofvrij, smelt op in de mixer, nul ombouwkosten."}
    ]
    st.table(data)