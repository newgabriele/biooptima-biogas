# tabs/tab12_report.py
import streamlit as st
from datetime import datetime

def render():
    st.subheader("Intelligente Vragen & Rekenregister (Tab 12)")
    st.markdown("Beheer alle 6 systeemgebonden expertvragen en leg ideeën, losse opmerkingen en praktijkbenchmarks vast via de ideeënbox.")

    if "user_asked_registry" not in st.session_state:
        st.session_state.user_asked_registry = [
            {
                "id": 1,
                "vraag": "Wat is de impact van een verhoogde maissilage-invoer op de VFA/TAC-ratio bij 500 m³/h?",
                "categorie": "Substraat & Verzuringsrisico",
                "gekoppelde_consequentie": "Tab 3 Kinetische simulatiewaarschuwing geactiveerd; OLR-grens aangescherpt.",
                "status": "Verwerkt in Code",
                "datum": "2026-08-30 11:15"
            },
            {
                "id": 2,
                "vraag": "Merlara envitec, agro 1 mw, mais en recirculaat, houd met 20kg in de ochtend 150 ppm H2S",
                "categorie": "Benchmark & Praktijkcase",
                "gekoppelde_consequentie": "Vastgelegd als geverifieerde praktijkbenchmark voor de validatie van de kinetische ijzerdosering in Tab 3 en Tab 7.",
                "status": "Actief / Benchmark",
                "datum": "2026-08-30 14:25"
            },
            {
                "id": 3,
                "vraag": "Een agro installatie kan bijna voor 99% geen thermofiel installatietemperatuur hebben, gewoon een controle check doen als dat voorkomt",
                "categorie": "Validatie & Procescontrole",
                "gekoppelde_consequentie": "Sanity check ingebouwd in Tab 1: visuele waarschuwing zodra een agro-installatie op thermofiele temperatuur (> 45°C) wordt gezet.",
                "status": "Verwerkt in Code (Tab 1)",
                "datum": "2026-08-30 16:35"
            }
        ]

    system_questions = [
        {
            "id": 1,
            "titel": "H₂S Reductie & SBG Productdosering",
            "doel": "Optimalisatie van H₂S-verwijdering in gashouder of reactor.",
            "context": "Standaard biogasflow van 500 m³/h gebruikmakend van de SBG-productlijn.",
            "gekoppelde_formules": ["calculate_fe_dissolution_rate()", "calculate_h2s_gas_fraction()", "run_kinetics_calculation()"],
            "actieve_tabs": ["Tab 3 (Kinetica)", "Tab 4 (Economie)", "Tab 7 (Installaties)"],
            "code_impact": "Koppelt de pH-afhankelijke oplosbaarheid van ijzeroxide direct aan de gasfase-sulfidefractie en berekent de optimale dagelijkse productdosering.",
            "template": "Bereken de benodigde dosering van de SBG-productlijn bij een gasproductie van {biogas_flow} m³/h om de H2S-concentratie terug te brengen van {h2s_ingang} ppm naar beneden de {h2s_doel} ppm."
        },
        {
            "id": 2,
            "titel": "Thermofiele vs. Mesofiele Kinetiek & NH₃ Inhibitie",
            "doel": "Bewaking hydraulische verblijftijd (HRT) en toxische ammoniakremming.",
            "context": "CSTR reactor onder mesofiele (~38.5°C) versus thermofiele (~52°C) condities.",
            "gekoppelde_formules": ["calculate_free_ammonia_nh3()", "run_kinetics_calculation()"],
            "actieve_tabs": ["Tab 1 (Configuratie)", "Tab 3 (Kinetica)", "Tab 5 (Optimalisatie)"],
            "code_impact": "Past automatisch de hydrolysesnelheid en de kritieke NH₃-alarmgrens aan op basis van het gekozen thermisch regime.",
            "template": "Beoordeel of een HRT van {hrt_dagen} dagen veilig is voor een thermofiele CSTR bij een organische belasting van {olr} kg ODM/m³-dag."
        },
        {
            "id": 3,
            "titel": "Organische Belasting (OLR) & VFA/TAC-ratio Risico's",
            "doel": "Vroegtijdige detectie van verzuringsrisico's bij piekbelasting.",
            "context": "Evaluatie van de stabiele werking bij intensieve co-vergisting of maissilage.",
            "gekoppelde_formules": ["calculate_vfa_tac_risk()", "check_olr_limits()"],
            "actieve_tabs": ["Tab 2 (Substraten)", "Tab 3 (Kinetica)", "Tab 6 (Monitoring)"],
            "code_impact": "Berekent de verwachte VFA/TAC-verschuiving op basis van de dagelijkse organische belasting en activeert waarschuwingen bij overschrijding.",
            "template": "Wat is het effect op de VFA/TAC-ratio als de organische belasting toeneemt naar {olr_nieuw} kg ODM/m³-dag bij een reactorvolume van {volume} m³?"
        },
        {
            "id": 4,
            "titel": "Hydraulische Verblijftijd (HRT) & Reactorvolume Beheer",
            "doel": "Gegarandeerde biologische afbraak en voorkomen van uitspoeling.",
            "context": "Afstemming tussen het actieve vloeistofvolume en het dagelijkse voedingsdebiet.",
            "gekoppelde_formules": ["calculate_hrt()", "validate_reactor_capacity()"],
            "actieve_tabs": ["Tab 1 (Configuratie)", "Tab 3 (Kinetica)"],
            "code_impact": "Berekent de HRT in dagen en toetst deze aan de minimale grenswaarden voor agro- en industriële vergisters.",
            "template": "Controleer of de huidige HRT voldoende is bij een substraatinput van {substraat_m3_dag} m³/dag in een reactor van {volume} m³."
        },
        {
            "id": 5,
            "titel": "Economische Waardering & Biogasopbrengst Optimalisatie",
            "doel": "Kosten-baten analyse van additieven ten opzichte van gasopbrengst en opbrengstwaarde.",
            "context": "Berekening van netto rendement op basis van biogas- en productprijzen.",
            "gekoppelde_formules": ["calculate_economic_return()", "optimize_dosage_cost()"],
            "actieve_tabs": ["Tab 4 (Economie)", "Tab 8 (Rapportage)"],
            "code_impact": "Integreert de productkosten van SBG-lijnen met de actuele biogasmarktprijs voor directe ROI-bepaling.",
            "template": "Wat is de verwachte maandelijkse netto opbrengstverbetering bij toepassing van de optimale SBG-dosering bij een biogasgasprijs van €{prijs} per m³?"
        },
        {
            "id": 6,
            "titel": "IJzeroxide Additieven & Chemische Reactiekinetiek (Fe₂O₃ / FeO mix)",
            "doel": "Kinetische modellering van de 35%/35% ijzeroxide-activering.",
            "context": "Binding van H₂S in de gashouder en vloeistofsfase op basis van specifieke actieve fracties.",
            "gekoppelde_formules": ["calculate_fe_dissolution_rate()", "run_kinetics_calculation()"],
            "actieve_tabs": ["Tab 3 (Kinetica)", "Tab 7 (Installaties)"],
            "code_impact": "Berekent de oplossingssnelheid en reactiecoëfficiënten voor de specifieke 35% Fe₂O₃ en 35% FeO mengselverhouding.",
            "template": "Simuleer de reactiesnelheid van een 35% Fe2O3 en 35% FeO additief bij een nominale pH van {ph} en temperatuur van {temp}°C."
        }
    ]

    tab_sys, tab_user = st.tabs(["⚙️ Systeemvragen & Formule-Relaties (6)", "💡 Ideeënbox, Notities & Backlog"])

    with tab_sys:
        st.markdown("#### Systeemgebonden Expertvragen & Formule-Interconnecties (6 Stuks)")
        sys_titles = [f"Systeemvraag {q['id']}: {q['titel']}" for q in system_questions]
        selected_sys = st.selectbox("Selecteer Systeemvraag", sys_titles, key="sys_q_select_expanded")
        q_data = next(q for q in system_questions if f"Systeemvraag {q['id']}: {q['titel']}" == selected_sys)
        
        st.markdown(f"**Doel:** {q_data['doel']}")
        st.markdown(f"**Context:** {q_data['context']}")
        st.markdown(f"**Code & Formule Impact:** {q_data['code_impact']}")
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown("**Gekoppelde Formules (`formulas.py`):**")
            for f in q_data["gekoppelde_formules"]:
                st.code(f, language="python")
        with col_s2:
            st.markdown("**Actieve App-Tabbladen:**")
            for t in q_data["actieve_tabs"]:
                st.text(f"📁 {t}")
        st.info(f"**AI Vraag-Template:** `{q_data['template']}`")

    with tab_user:
        st.markdown("#### 💡 Ideeënbox & Backlog")
        st.markdown("Bekijk hier al je opgekomen ideeën en opmerkingen, beoordeel de status, of leg direct een nieuwe gedachte vast.")

        status_filter = st.selectbox("Filter op Status", ["Alle", "Te beoordelen (Idee)", "Verwerkt in Code", "Actief / Benchmark", "Geparkeerd / Afgewezen"], key="status_filter_box")

        filtered_registry = st.session_state.user_asked_registry
        if status_filter != "Alle":
            filtered_registry = [item for item in st.session_state.user_asked_registry if status_filter.lower() in item['status'].lower()]

        if filtered_registry:
            user_titles = [f"[{uq['status']}] {uq['vraag'][:50]}..." for uq in filtered_registry]
            selected_user = st.selectbox("Selecteer Item om te Bekijken / Beoordelen", user_titles, key="user_q_select_backlog")
            
            uq_data = next(uq for uq in filtered_registry if f"[{uq['status']}] {uq['vraag'][:50]}..." == selected_user)
            
            st.markdown(f"**Inhoud / Idee:** {uq_data['vraag']}")
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.markdown(f"**Categorie:** {uq_data['categorie']}")
                st.markdown(f"**Registratiedatum:** {uq_data['datum']}")
            with col_info2:
                status_options = ["Te beoordelen (Idee)", "In uitvoering", "Verwerkt in Code", "Actief / Benchmark", "Geparkeerd / Afgewezen"]
                current_idx = status_options.index(uq_data['status']) if uq_data['status'] in status_options else 0
                
                new_stat = st.selectbox("Status Beheren", status_options, index=current_idx, key=f"status_select_{uq_data['id']}")
                if new_stat != uq_data['status']:
                    uq_data['status'] = new_stat
                    st.success("Status bijgewerkt!")
                    st.rerun()
            
            st.markdown(f"**Notitie / Doel:** {uq_data['gekoppelde_consequentie']}")
        else:
            st.info("Geen items gevonden voor dit filter.")

        st.markdown("---")
        st.markdown("#### ➕ Nieuw Idee of Notitie Vastleggen")
        
        with st.form("registreer_form_backlog"):
            input_text = st.text_area("Typ je idee, opmerking of praktijkkreet")
            cat = st.selectbox("Categorie", ["Idee / Backlog", "Validatie & Procescontrole", "Benchmark & Praktijkcase", "Dosering & Chemie", "Substraat & Verzuringsrisico", "Economie & ROI"])
            cons = st.text_input("Eventuele notitie of gewenst doel (optioneel)")
            
            if st.form_submit_button("Opslaan in Ideeënbox"):
                if input_text:
                    new_id = len(st.session_state.user_asked_registry) + 1
                    st.session_state.user_asked_registry.append({
                        "id": new_id,
                        "datum": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "vraag": input_text.strip(),
                        "categorie": cat,
                        "gekoppelde_consequentie": cons if cons else "Vastgelegd ter beoordeling",
                        "status": "Te beoordelen (Idee)"
                    })
                    st.success("Idee succesvol toegevoegd aan de ideeënbox met status 'Te beoordelen (Idee)'!")
                    st.rerun()
                else:
                    st.error("Vul een geldige invoer in.")