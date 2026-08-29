# tabs/tab12_master.py - Master Dashboard & Intelligentie Register
import streamlit as st
from knowledge import krijg_alle_rekenvragen, krijg_praktijk_benchmarks


def render():
    st.header("🧠 Master Dashboard: Intelligentie & Rekenregister")
    st.markdown(
        "Dit overzicht toont alle **intelligente rekenvragen, expert-regels en chemische scenario's** "
        "die in de BioOptima 360° applicatie zijn verankerd, inclusief hun koppeling naar formules en tabbladen."
    )

    rekenvragen = krijg_alle_rekenvragen()

    # Statistieken bovenaan
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Totaal Expert Vragen", len(rekenvragen))
    with col2:
        st.metric("Standaard Biogasflow", "500 m³/h")
    with col3:
        st.metric("Actieve IJzer-mix", "35% Fe₂O₃ / 35% FeO")

    st.divider()

    # Weergave per intelligente vraag in een nette UI
    for sleutel, data in rekenvragen.items():
        with st.expander(f"📌 {data['titel']} (`{sleutel}`)", expanded=True):
            st.markdown(f"**Doel:** {data['doel']}")
            st.markdown(f"**Standaard Context:** {data['standaard_context']}")
            
            st.markdown("---")
            
            # Twee kolommen voor Formules vs Gebruikte Tabs
            c_formules, c_tabs = st.columns(2)
            
            with c_formules:
                st.markdown("### ⚙️ Gekoppelde Formules (`formulas.py`)")
                for formule in data["relevante_formules"]:
                    st.code(f"def {formule}()", language="python")

            with c_tabs:
                st.markdown("### 📂 Actief in App Tabs")
                for t in data["gebruikte_in_tabs"]:
                    st.markdown(f"- 📄 `tabs/{t}`")

            st.markdown("### 💬 Vraag-Template voor AI / Systeem")
            st.info(data["vraag_template"])

    st.divider()
    st.subheader("🏭 Praktijkbenchmarks & Validatie")

    for key, data in krijg_praktijk_benchmarks().items():
        with st.expander(f"📍 {data['naam']} (Referentiecase)"):
            st.markdown(f"**Substraat:** {', '.join(data['substraat_profiel'])}")
            st.markdown(f"**Dosering:** {data['dosering_strategie']}")
            st.markdown(f"**Locatie & Transtijd:** {data['dosering_locatie']} ({data['transtijd']})")
            st.markdown(f"**Resultaat:** {data['resultaat_observatie']}")
            st.info(f"**Doel:** {data['doel']}")

    st.divider()
    st.caption("BioOptima 360° Master Core — Ontworpen voor volledige procescontrole en transparantie.")