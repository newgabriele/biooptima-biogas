import streamlit as st
import os
import sys

# Zorg ervoor dat Python de map correct herkent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Expliciete en veilige imports van alle tabbladen (1 t/m 12)
try:
    from tabs import tab1_plant_config as t1
except ImportError:
    t1 = None

try:
    from tabs import tab2_kinetics as t2
except ImportError:
    t2 = None

try:
    from tabs import tab3_operator as t3
except ImportError:
    t3 = None

try:
    from tabs import tab4_management as t4
except ImportError:
    t4 = None

try:
    from tabs import tab5_analytics as t5
except ImportError:
    t5 = None

try:
    from tabs import tab6_substrates as t6
except ImportError:
    t6 = None

try:
    from tabs import tab7_installations as t7
except ImportError:
    t7 = None

try:
    from tabs import tab8_ai_calibration as t8
except ImportError:
    t8 = None

try:
    from tabs import tab9_reports as t9
except ImportError:
    t9 = None

try:
    from tabs import tab10_changelog as t10
except ImportError:
    t10 = None

try:
    from tabs import tab11_benchmark as t11
except ImportError:
    t11 = None

try:
    from tabs import tab12_questions as t12
except ImportError:
    t12 = None


def main():
    st.set_page_config(
        page_title="BioOptima 360° | Industrial Biogas Digital Twin",
        page_icon="♻️",
        layout="wide"
    )

    st.sidebar.title("🌿 BioOptima 360°")
    st.sidebar.markdown("**Digital Twin & Dynamic Dosing**")
    st.sidebar.markdown("---")

    menu_options = [
        "🏠 Master Dashboard",
        "👤 Klanten & Installatie Beheer",
        "⚙️ Tab 1: Plant Configuratie",
        "🧪 Tab 2: Kinetisch Model & Basisdoses",
        "👷 Tab 3: Operator & 20kg Bag Dosing",
        "📈 Tab 4: Directie & Financiële ROI",
        "📊 Tab 5: Analytics & Wobbe-Index",
        "🌾 Tab 6: Substraten & Marktprijzen",
        "🏭 Tab 7: Installaties & Werfbeheer",
        "🔬 Tab 8: AI-kalibratie & Sensor Validatie",
        "📋 Tab 9: Rapportage & Logs",
        "📋 Tab 10: Systeem Changelog & Release",
        "⚙️ Tab 11: Benchmark & Valorisatie",
        "💡 Tab 12: Intelligente Vragen & Registratie"
    ]

    choice = st.sidebar.radio("Navigatie", menu_options)

    # Dynamische weergave van de actieve werf uit Tab 7
    current_plant = st.session_state.get('active_plant', 'Corte Pila (Italië) - 1MW CSTR')

    st.sidebar.markdown("---")
    st.sidebar.info(
        f"🏭 **Actieve Werf:**\n{current_plant}\n\n"
        "⚙️ **Plant Status:** Actief\n"
        "🔹 **Additief:** Fe₂O₃/FeO (35%/35%)\n"
        "🔹 **Versie:** v2.0.0 (Augustus 2026)"
    )

    # Routering op basis van menukeuze
    if choice == "🏠 Master Dashboard":
        st.title("🏠 BioOptima 360° — Master Dashboard")
        st.markdown("Centraal besturingsplatform voor industriële anaerobe vergisting en biomethaan optimalisatie.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Actief Biogas Debiet", value="500 m³/h", delta="+5.6% TalTech Yield")
        with col2:
            st.metric(label="H₂S Vloeistoffase Doel", value="< 100 ppm", delta="-85% Ontzwaveling")
        with col3:
            st.metric(label="Prediktieve Nauwkeurigheid", value="95.4%", delta="ML Engine Active")

    elif choice == "👤 Klanten & Installatie Beheer":
        st.title("👤 Klanten & Gebruikersbeheer")
        st.markdown("Overzicht van actieve klantdossiers, installaties en toegangsrechten.")

    elif "Tab 1:" in choice:
        render_tab(t1, "Tab 1: Plant Configuratie & Systeemparameters")
    elif "Tab 2:" in choice:
        render_tab(t2, "Tab 2: Kinetisch Model & Gasexpansie")
    elif "Tab 3:" in choice:
        render_tab(t3, "Tab 3: Operator Werkinstructies & 20kg Bag Dosing")
    elif "Tab 4:" in choice:
        render_tab(t4, "Tab 4: Directie & Financiële ROI")
    elif "Tab 5:" in choice:
        render_tab(t5, "Tab 5: Analytics, Wobbe-Index & Vochtbalans")
    elif "Tab 6:" in choice:
        render_tab(t6, "Tab 6: Substraten & Marktprijzen")
    elif "Tab 7:" in choice:
        render_tab(t7, "Tab 7: Installaties & Werfbeheer")
    elif "Tab 8:" in choice:
        render_tab(t8, "Tab 8: AI-kalibratie & Sensor Validatie")
    elif "Tab 9:" in choice:
        render_tab(t9, "Tab 9: Rapportage & Systeem Logs")
    elif "Tab 10:" in choice:
        render_tab(t10, "Tab 10: Systeem Changelog & Release Historie")
    elif "Tab 11:" in choice:
        render_tab(t11, "Tab 11: Benchmark & Valorisatie Matrix")
    elif "Tab 12:" in choice:
        render_tab(t12, "Tab 12: Intelligente Vragen & Registratie")

def render_tab(module, title):
    st.title(title)
    if module is not None and hasattr(module, "render"):
        module.render()
    else:
        st.error(f"⚠️ Het bijbehorende tab-bestand kon niet worden geladen of mist de `render()` functie.")

if __name__ == "__main__":
    main()