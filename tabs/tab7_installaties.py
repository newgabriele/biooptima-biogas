# tabs/tab7_installaties.py
import streamlit as st
import pandas as pd

def render_tab7(selected_lang="Nederlands", is_admin=True):
    if selected_lang == "Italiano":
        st.markdown("### 🏭 Gestione Impianti (Tab 7)")
        if is_admin:
            st.info("💡 Pannello Administrator: visualizza e gestisce tutti i clienti e le relative installazioni per test e supervisione.")
        else:
            st.info("💡 Panoramica delle installazioni collegate al vostro account cliente.")
    elif selected_lang == "English":
        st.markdown("### 🏭 Installations Management (Tab 7)")
        if is_admin:
            st.info("💡 Administrator Panel: view and manage all customers and their installations for testing and supervision.")
        else:
            st.info("💡 Overview of installations linked to your customer account.")
    else:
        st.markdown("### 🏭 Installaties Beheer (Tab 7)")
        if is_admin:
            st.info("💡 Administrator Paneel: overzicht en beheer van alle klanten en al hun installaties om te testen en te configureren.")
        else:
            st.info("💡 Overzicht van uw eigen installaties en gekoppelde installatiegegevens.")

    if "installations_df" not in st.session_state:
        st.session_state.installations_df = pd.DataFrame([
            {"Klant": "Bioman Srl", "Installatie / Plant": "CSTR Digester 1", "Volume (m³)": 4500.0, "Status": "Actief"},
            {"Klant": "Bioman Srl", "Installatie / Plant": "Thermophilic Reactor 2", "Volume (m³)": 3200.0, "Status": "Actief"},
            {"Klant": "BioPower Teglio", "Installatie / Plant": "Teglio Plant Central", "Volume (m³)": 2800.0, "Status": "Actief"},
            {"Klant": "AgroEnergy BV", "Installatie / Plant": "Almere Digester North", "Volume (m³)": 5000.0, "Status": "Planning"},
            {"Klant": "AgroEnergy BV", "Installatie / Plant": "Almere Digester South", "Volume (m³)": 4500.0, "Status": "Planning"}
        ])

    if is_admin:
        st.markdown("##### 📋 Alle Klanten & Installaties (Administrator Beheer & Testoverzicht)")
        edited_df = st.data_editor(
            st.session_state.installations_df,
            num_rows="dynamic",
            use_container_width=True,
            key="editable_installations"
        )
        
        if st.button("💾 Wijzigingen Opslaan", type="primary"):
            st.session_state.installations_df = edited_df
            st.success("✅ Alle installaties en klanten succesvol bijgewerkt voor tests!")
            st.rerun()
    else:
        st.markdown("##### 📋 Uw Geregistreerde Installaties")
        client_view_df = st.session_state.installations_df[st.session_state.installations_df["Klant"] == "Bioman Srl"]
        st.dataframe(client_view_df, use_container_width=True)