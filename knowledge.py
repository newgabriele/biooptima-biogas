# knowledge.py - Kennisbank & Live Gemini AI Integratie
import os
from google import genai
from pypdf import PdfReader

DOCS_DIR = "docs"


def haal_relevante_fragmenten_uit(tekst, zoekterm, max_fragmenten=3):
    """Knipt tekst op in alinea's en geeft alleen de alinea's terug waarin de zoekterm voorkomt."""
    regels = [r.strip() for r in tekst.split("\n") if len(r.strip()) > 10]
    relevante_fragmenten = []
    zoekterm_lower = zoekterm.lower()

    for regel in regels:
        if zoekterm_lower in regel.lower():
            relevante_fragmenten.append(f"> ... {regel} ...")
            if len(relevante_fragmenten) >= max_fragmenten:
                break

    return relevante_fragmenten


def zoek_advies_in_documenten(zoekterm):
    """Doorzoekt de lokale map 'docs/' op trefwoorden in .txt en .pdf bestanden."""
    if not os.path.exists(DOCS_DIR):
        return "De map 'docs' bestaat nog niet."

    if not zoekterm or len(zoekterm.strip()) < 2:
        return "Voer een zoekterm in van minimaal 2 tekens."

    resultaten = []

    try:
        bestanden = os.listdir(DOCS_DIR)
    except Exception as e:
        return f"⚠️ Kon de map 'docs' niet openen: {e}"

    for bestandsnaam in bestanden:
        pad = os.path.join(DOCS_DIR, bestandsnaam)

        if os.path.isfile(pad) and bestandsnaam.endswith(".txt"):
            try:
                with open(pad, "r", encoding="utf-8") as f:
                    inhoud = f.read()
                    fragmenten = haal_relevante_fragmenten_uit(
                        inhoud, zoekterm
                    )
                    if fragmenten:
                        tekst_block = "\n\n".join(fragmenten)
                        resultaten.append(
                            f"📄 **[Tekstbestand: {bestandsnaam}]**\n{tekst_block}"
                        )
            except Exception as e:
                print(f"Fout bij lezen van {bestandsnaam}: {e}")

        elif os.path.isfile(pad) and bestandsnaam.endswith(".pdf"):
            try:
                reader = PdfReader(pad)
                pdf_fragmenten = []

                for pagina_nr, page in enumerate(reader.pages, start=1):
                    tekst = page.extract_text() or ""
                    fragmenten = haal_relevante_fragmenten_uit(
                        tekst, zoekterm
                    )
                    if fragmenten:
                        tekst_block = "\n".join(fragmenten)
                        pdf_fragmenten.append(
                            f"📍 *Pagina {pagina_nr}:*\n{tekst_block}"
                        )

                if pdf_fragmenten:
                    geboekte_tekst = (
                        f"📚 **[PDF Handboek: {bestandsnaam}]**\n"
                        + "\n\n".join(pdf_fragmenten)
                    )
                    resultaten.append(geboekte_tekst)
            except Exception as e:
                print(f"Fout bij lezen van PDF {bestandsnaam}: {e}")

    if resultaten:
        return "\n\n---\n\n".join(resultaten)
    else:
        return f"Geen specifieke fragmenten gevonden voor zoekterm '{zoekterm}'."


def stel_vraag_aan_ai(vraag, api_key):
    """Stuurt een vraag naar het gratis Google Gemini AI-model met een specifieke System Prompt."""
    if not api_key:
        return "⚠️ Voer eerst een geldige Gemini API Key in."

    try:
        client = genai.Client(api_key=api_key)

        system_prompt = (
            "Je bent een senior procestechnoloog en expert op het gebied van "
            "anaërobe digestie, biogasinstallaties, chemie (H2S, Fe2O3, FeO, pH, VFA/TIC), "
            "en procesoptimalisatie voor biomethaan. "
            "Geef heldere, praktische en technisch onderbouwde antwoorden in het Nederlands."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{system_prompt}\n\nVraag van de gebruiker:\n{vraag}",
        )
        return response.text
    except Exception as e:
        return f"❌ Fout bij verbinden met de Gemini AI API: {e}"