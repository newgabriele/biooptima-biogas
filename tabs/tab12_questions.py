# tabs/tab12_report.py
import streamlit as st
from datetime import datetime

def render():
    st.subheader("Intelligente Vragen & Rekenregister (Tab 12)")
    st.markdown("Beheer systeemgebonden expertvragen en leg losse praktijknotities, benchmarks en gestelde vragen vast via 'registreer:'.")

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
            }
        ]

    system_questions = [
        {
            "id": 1,
            "titel": "H₂S Reductie & SBG Productdosering",
            "doel": "Optimalisatie van H₂S-verwijdering in gashouder of reactor[cite: 2].",
            "context": "Standaard biogasflow van 500 m³/h gebruikmakend van de SBG-productlijn[cite: 2].",
            "gekoppelde_formules": ["calculate_fe_dissolution_rate()", "calculate_h2s_gas_fraction()", "run_kinetics_calculation()"],
            "actieve_tabs": ["Tab 3 (Kinetica)", "Tab 4 (Economie)", "Tab 7 (Installaties)"],
            "code_impact": "Koppelt de pH-afhankelijke oplosbaarheid van ijzeroxide direct aan de gasfase-sulfidefractie en berekent de optimale dagelijkse productdosering.",
            "template": "Bereken de benodigde dosering van de SBG-productlijn bij een gasproductie van {biogas_flow} m³/h om de H2S-concentratie terug te brengen van {h2s_ingang} ppm naar beneden de {h2s_doel} ppm[cite: 2]."
        },
        {
            "id": 2,
            "titel": "Thermofiele vs. Mesofiele Kinetiek & NH₃ Inhibitie",
            "doel": "Bewaking hydraulische verblijftijd (HRT) en toxische ammoniakremming.",
            "context": "CSTR reactor onder mesofiele (~38.5°C) versus thermofiele (~52°C) condities[cite: 2].",
            "gekoppelde_formules": ["calculate_free_ammonia_nh3()", "run_kinetics_calculation()"],
            "actieve_tabs": ["Tab 1 (Configuratie)", "Tab 3 (Kinetica)", "Tab 5 (Optimalisatie)"],
            "code_impact": "Past automatisch de hydrolysesnelheid (multiplier 1.45) en de kritieke NH₃-alarmgrens (180 mg/L i.p.v. 350 mg/L) aan op basis van het gekozen thermisch regime.",
            "template": "Beoordeel of een HRT van {hrt_dagen} dagen veilig is voor een thermofiele CSTR bij een organische belasting van {olr} kg ODM/m³-dag, rekening houdend met de NH₃-inhibitiegrens[cite: 2]."
        },
        {
            "id": 3,
            "titel": "FOS/TAC Soft-Sensor & Verzuringsrisico",
            "doel": "Dynamische bewaking van de biologische stabiliteit en buffercapaciteit.",
            "context": "Koppeling tussen VFA-risicolading, organische belasting (OLR) en totale alkaliniteit (TAN/TAC).",
            "gekoppelde_formules": ["calculate_fos_tac_soft_sensor()", "run_kinetics_calculation()"],
            "actieve_tabs": ["Tab 3 (Soft-Sensors)", "Tab 5 (MPC Optimalisatie)"],
            "code_impact": "Berekent real-time de FOS/TAC-ratio en activeert automatisch statusmeldingen (groen/oranje/rood) bij verzuringsdruk.",
            "template": "Wat is het effect van een OLR-piek van {olr} op de berekende FOS/TAC-ratio en de benodigde pH-correctie?"
        },
        {
            "id": 4,
            "titel": "Effluent Recirculatie & Bufferwerking",
            "doel": "Berekening van recirculatiefactor voor VFA/TIC stabilisatie[cite: 2].",
            "context": "Processturing en vloeistofbalans in BioOptima 360°[cite: 2].",
            "gekoppelde_formules": ["bereken_recirculatie()", "vfa_tic_balans()"],
            "actieve_tabs": ["Tab 2 (Substraten)", "Tab 3 (Kinetica)"],
            "code_impact": "Past de buffercapaciteit (TAC) en VFA/TIC-verhouding dynamisch aan op basis van de retourgestuurde effluentstroom[cite: 2].",
            "template": "What is het effect op de alkaliniteit (TIC) en VFA/TIC-ratio als we {recirculatie_percentage}% effluent terugvoeren naar de hydrolysetank?[cite: 2]"
        },
        {
            "id": 5,
            "titel": "Wobbe-Index & Gaskwaliteit Compliance",
            "doel": "Toetsing van de energetische gaskwaliteit aan openbare netwerknormen.",
            "context": "Samenstelling van CH₄, CO₂, O₂ en N₂ in verhouding tot Wobbe-upper en ondergrens.",
            "gekoppelde_formules": ["calculate_wobbe_index()"],
            "actieve_tabs": ["Tab 6 (Kwaliteitsnormen)", "Tab 12 (Rapportage)"],
            "code_impact": "Berekent PCS, PCI en relatieve dichtheid om te bepalen of het gas voldoet aan het Nederlandse G-gas of H-gas netwerk.",
            "template": "Voldoet het geproduceerde biogas met {ch4_pct}% CH₄ aan de strenge Wobbe-index eisen voor injectie in het H-gas transportnet?"
        },
        {
            "id": 6,
            "titel": "RED II GHG-Balans & Duurzaamheidscertificering",
            "doel": "Verificatie van broeikasgasreductie ten opzichte van de fossiele referentie.",
            "context": "Invoerdieet (mest, maïs, afval), transportkilometers en methaanlekkage.",
            "gekoppelde_formules": ["calculate_red_ii_ghg_balance()"],
            "actieve_tabs": ["Tab 6 (Kwaliteitsnormen)", "Tab 12 (Executive Rapport)"],
            "code_impact": "Berekent de totale ketenemissie en toetst automatisch aan de Europese drempel van ≥ 80% reductie.",
            "template": "Behaal ik met een aandeel van {manure_share_pct}% mest en {maissilage_share_pct}% maïs de vereiste 80% GHG-reductie onder RED II?"
        }
    ]

    tab_sys, tab_user = st.tabs(["⚙️ Systeemvragen & Formule-Relaties (6)", "📝 Gestelde Vragen, Notities & Benchmarks"])

    with tab_sys:
        st.markdown("#### Systeemgebonden Expertvragen & Formule-Interconnecties")
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
        st.markdown("#### Gebruikerslogboek, Notities & Benchmarks via 'registreer:'")
        
        if st.session_state.user_asked_registry:
            user_titles = [f"[{uq['categorie'][:10]}] Vraag/Notitie {uq['id']}: {uq['vraag'][:40]}..." for uq in st.session_state.user_asked_registry]
            selected_user = st.selectbox("Selecteer Geregistreerd Item / Benchmark", user_titles, key="user_q_select_bench")
            uq_data = next(uq for uq in st.session_state.user_asked_registry if f"[{uq['categorie'][:10]}] Vraag/Notitie {uq['id']}: {uq['vraag'][:40]}..." == selected_user)
            
            st.markdown(f"**Inhoud / Opmerking:** {uq_data['vraag']}")
            st.markdown(f"**Categorie:** {uq_data['categorie']}")
            st.markdown(f"**Registratiedatum:** {uq_data['datum']}")
            st.markdown(f"**Status:** `{uq_data['status']}`")
            st.success(f"**Gekoppelde Consequentie / Doel:** {uq_data['gekoppelde_consequentie']}")
        else:
            st.info("Nog geen items geregistreerd.")

        st.markdown("---")
        st.markdown("#### ➕ Nieuwe Vraag, Notitie of Benchmark Vastleggen")
        
        with st.form("registreer_form_benchmark"):
            input_text = st.text_area("Typ 'registreer: [uw vraag, kreet of praktijkcase]' (bijv. Merlara benchmark)")
            cat = st.selectbox("Categorie", ["Benchmark & Praktijkcase", "Dosering & Chemie", "Substraat & Verzuringsrisico", "Thermodynamica & Warmte", "Economie & ROI"])
            cons = st.text_input("Technische Consequentie / Doel voor Controle of Validatie")
            
            if st.form_submit_button("Vastleggen in Register"):
                if input_text:
                    clean_text = input_text
                    if input_text.lower().startswith("registreer:"):
                        clean_text = input_text[10:].strip()
                        
                    new_id = len(st.session_state.user_asked_registry) + 1
                    st.session_state.user_asked_registry.append({
                        "id": new_id,
                        "datum": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "vraag": clean_text,
                        "categorie": cat,
                        "gekoppelde_consequentie": cons if cons else "Vastgelegd als benchmark/notitie voor toekomstige controle",
                        "status": "Actief / Benchmark"
                    })
                    st.success("Item succesvol toegevoegd aan het register!")
                    st.rerun()
                else:
                    st.error("Vul een geldige invoer in.")