# ============================================================================
# plants.py - Centrale opslag van installaties, substraten, scenario's en export
# ============================================================================

import io
import datetime
import pandas as pd

BAG_WEIGHT_KG = 20.0

COUNTRY_DEFAULT_PRICES = {
    "Nederland (NL)": {"drijfmest_rund": -8.0, "maissilage": 46.0, "kippenmest_droog": 14.0, "melasse": 170.0, "slachtafval_vloeibaar": -15.0},
    "Italië (IT)": {"drijfmest_rund": 0.0, "maissilage": 52.0, "kippenmest_droog": 20.0, "melasse": 180.0, "slachtafval_vloeibaar": -8.0},
    "Duitsland (DE)": {"drijfmest_rund": -3.0, "maissilage": 49.0, "kippenmest_droog": 16.0, "melasse": 175.0, "slachtafval_vloeibaar": -10.0}
}

MASTER_SUBSTRATE_TEMPLATES = {
    "maissilage": {
        "ts_pct": 0.33, "vs_pct": 0.92, "s_g_per_kg_ts": 1.2, "n_g_per_kg_ts": 3.0,
        "biogas_m3_per_ton_odm": 580.0, "price_per_ton": 48.0,
        "f_fast": 0.05, "k_fast": 0.80, "f_med": 0.25, "k_med": 0.25, "f_slow": 0.70, "k_slow": 0.05,
        "vfa_risk": 0.4
    },
    "drijfmest_rund": {
        "ts_pct": 0.09, "vs_pct": 0.80, "s_g_per_kg_ts": 3.5, "n_g_per_kg_ts": 4.5,
        "biogas_m3_per_ton_odm": 310.0, "price_per_ton": -4.0,
        "f_fast": 0.15, "k_fast": 1.20, "f_med": 0.35, "k_med": 0.30, "f_slow": 0.50, "k_slow": 0.08,
        "vfa_risk": 0.1
    },
    "kippenmest_droog": {
        "ts_pct": 0.55, "vs_pct": 0.75, "s_g_per_kg_ts": 5.0, "n_g_per_kg_ts": 32.0,
        "biogas_m3_per_ton_odm": 460.0, "price_per_ton": 18.0,
        "f_fast": 0.40, "k_fast": 1.80, "f_med": 0.50, "k_med": 0.40, "f_slow": 0.10, "k_slow": 0.05,
        "vfa_risk": 1.0
    },
    "melasse": {
        "ts_pct": 0.75, "vs_pct": 0.90, "s_g_per_kg_ts": 8.0, "n_g_per_kg_ts": 8.0,
        "biogas_m3_per_ton_odm": 620.0, "price_per_ton": 175.0,
        "f_fast": 0.85, "k_fast": 2.50, "f_med": 0.15, "k_med": 0.50, "f_slow": 0.00, "k_slow": 0.05,
        "vfa_risk": 1.5
    },
    "slachtafval_vloeibaar": {
        "ts_pct": 0.20, "vs_pct": 0.85, "s_g_per_kg_ts": 12.0, "n_g_per_kg_ts": 25.0,
        "biogas_m3_per_ton_odm": 720.0, "price_per_ton": -12.0,
        "f_fast": 0.20, "k_fast": 1.50, "f_med": 0.70, "k_med": 0.40, "f_slow": 0.10, "k_slow": 0.06,
        "vfa_risk": 0.8
    }
}

SUBSTRATE_KEYWORDS = {
    "maize": ["mais", "maize", "corn", "silage", "silomaize", "insilato"],
    "manure": ["drijf", "slurry", "cattle", "rund", "liquame", "manure_liquid", "bovino", "cow"],
    "poultry": ["kip", "poultry", "chicken", "pollina", "broiler"],
    "molasses": ["melas", "molas", "sugar", "zucker"],
    "slaughter": ["slacht", "slaughter", "macello", "afval", "waste", "vet", "fat"]
}

def resolve_substrate_key(role: str, available_db: dict):
    role_words = SUBSTRATE_KEYWORDS.get(role, [])
    for k in available_db.keys():
        k_lower = k.lower()
        if any(w in k_lower for w in role_words):
            return k
    return None

def build_preset_diet(scenario_type: str, available_db: dict):
    avail_keys = list(available_db.keys())
    k_maize = resolve_substrate_key("maize", available_db) or avail_keys[0]
    k_manure = resolve_substrate_key("manure", available_db)
    k_poultry = resolve_substrate_key("poultry", available_db)
    k_molasses = resolve_substrate_key("molasses", available_db)
    k_slaughter = resolve_substrate_key("slaughter", available_db)

    diet = {}
    active_subs = []

    if scenario_type == "A":
        if k_maize: diet[k_maize] = 36.0; active_subs.append(k_maize)
        if k_manure: diet[k_manure] = 38.0; active_subs.append(k_manure)
        if k_poultry: diet[k_poultry] = 12.0; active_subs.append(k_poultry)
        if k_molasses: diet[k_molasses] = 6.1; active_subs.append(k_molasses)
    elif scenario_type == "B":
        if k_maize: diet[k_maize] = 20.0; active_subs.append(k_maize)
        if k_manure: diet[k_manure] = 35.0; active_subs.append(k_manure)
        if k_poultry: diet[k_poultry] = 8.0; active_subs.append(k_poultry)
        if k_molasses: diet[k_molasses] = 4.5; active_subs.append(k_molasses)
        if k_slaughter: diet[k_slaughter] = 35.0; active_subs.append(k_slaughter)
    else:
        for k in avail_keys[:4]:
            diet[k] = 20.0 if k == k_maize else (35.0 if k == k_manure else 10.0)
            active_subs.append(k)

    diet["recirc_m3_day"] = 15.0
    diet["fe_product_dosed_kg"] = 100.0 if scenario_type == "A" else 140.0
    return active_subs, diet

def parse_substrates_df_to_dict(df: pd.DataFrame):
    substrates_dict = {}
    col_map = {str(c).lower().strip(): c for c in df.columns}
    name_col = next((col_map[k] for k in ["naam", "name", "substraat", "substrate", "substraat key"] if k in col_map), df.columns[0])
    ts_col = next((col_map[k] for k in ["ts_pct", "ts", "ds", "ds_pct", "droge_stof", "drogestof"] if k in col_map), None)
    vs_col = next((col_map[k] for k in ["vs_pct", "vs", "os", "os_pct", "organische_stof"] if k in col_map), None)
    s_col = next((col_map[k] for k in ["s_g_per_kg_ts", "s", "zwavel", "s_g_kg_ts"] if k in col_map), None)
    n_col = next((col_map[k] for k in ["n_g_per_kg_ts", "n", "stikstof", "n_g_kg_ts"] if k in col_map), None)
    yield_col = next((col_map[k] for k in ["biogas_m3_per_ton_odm", "gas_yield", "opbrengst", "biogas_yield"] if k in col_map), None)
    price_col = next((col_map[k] for k in ["price_per_ton", "prijs", "prijs_ton", "price"] if k in col_map), None)
    vfa_col = next((col_map[k] for k in ["vfa_risk", "vfa", "vzv_risico"] if k in col_map), None)

    for _, row in df.iterrows():
        raw_name = str(row[name_col]).strip()
        if not raw_name or raw_name.lower() == "nan": continue
        key_clean = raw_name.lower().replace(" ", "_").replace("-", "_").replace(".", "")
        ts_val = float(row[ts_col]) if ts_col and pd.notnull(row[ts_col]) else 0.25
        if ts_val > 1.0: ts_val /= 100.0
        vs_val = float(row[vs_col]) if vs_col and pd.notnull(row[vs_col]) else 0.85
        if vs_val > 1.0: vs_val /= 100.0
        s_val = float(row[s_col]) if s_col and pd.notnull(row[s_col]) else 3.0
        n_val = float(row[n_col]) if n_col and pd.notnull(row[n_col]) else 6.0
        yield_val = float(row[yield_col]) if yield_col and pd.notnull(row[yield_col]) else 480.0
        price_val = float(row[price_col]) if price_col and pd.notnull(row[price_col]) else 25.0
        vfa_val = float(row[vfa_col]) if vfa_col and pd.notnull(row[vfa_col]) else 0.5

        substrates_dict[key_clean] = {
            "ts_pct": ts_val, "vs_pct": vs_val, "s_g_per_kg_ts": s_val, "n_g_per_kg_ts": n_val,
            "biogas_m3_per_ton_odm": yield_val, "price_per_ton": price_val,
            "f_fast": float(row.get("f_fast", 0.20)) if "f_fast" in row else 0.20,
            "k_fast": float(row.get("k_fast", 1.80)) if "k_fast" in row else 1.80,
            "f_med": float(row.get("f_med", 0.50)) if "f_med" in row else 0.50,
            "k_med": float(row.get("k_med", 0.35)) if "k_med" in row else 0.35,
            "f_slow": float(row.get("f_slow", 0.30)) if "f_slow" in row else 0.30,
            "k_slow": float(row.get("k_slow", 0.05)) if "k_slow" in row else 0.05,
            "vfa_risk": vfa_val
        }
    return substrates_dict

# --- DEFINITIES STAAN NU CORRECT BOVENAAN ---
DEFAULT_SHIFTS_TEMPLATE = [
    {"naam": "Ochtendploeg / Shift 1", "percentage": 35.0, "uren": 8.0, "operator": "Jan Janssen"},
    {"naam": "Middagploeg / Shift 2", "percentage": 35.0, "uren": 8.0, "operator": "Marco Rossi"},
    {"naam": "Nachtploeg / Shift 3", "percentage": 30.0, "uren": 8.0, "operator": "Hans Schmidt"}
]

def generate_annual_shifts_dict(base_shifts):
    return {w: [dict(s) for s in base_shifts] for w in range(1, 53)}

DEFAULT_PLANTS = {
    "dama_plant": {
        "name": "Da.Ma. Biogas", "country": "Italië (IT)", "volume_m3": 2500.0, "biogas_flow_m3_h": 500.0,
        "ph_nominal": 7.65, "ph_crit_low": 7.30, "temp_c": 38.5, "target_h2s_ppm": 100.0, "alarm_h2s_ppm": 200.0,
        "target_depot_buffer_kg": 100.0, "initial_fe_depot_kg": 120.0, "safety_margin": 1.25, "max_vfa_shock_risk": 2.5,
        "max_dm_pct": 10.5, "initial_dm_pct": 8.5, "initial_tan_mg_l": 2400.0, "hrt_days": 50.0,
        "biogas_price_per_m3": 0.68, "fe_product_price_per_kg": 1.20, "bunker_type": "Schroefvijzel / Mengbunker",
        "fe_dosing_method": "Bovenop substraat (Top-loaded)", "fe_transport_lag_hours": 3.5,
        "recirculation_type": "Eigen Digestaat-Circulaat (Dunne fractie)", "scada_protocol": "Siemens S7 (Profinet / TCP)",
        "scada_ip": "192.168.1.100", "scada_port": 102, "scada_rack": 0, "scada_slot": 2, "scada_db_number": 50,
        "client_name": "Envitec", "client_visible": True,
        "shifts": DEFAULT_SHIFTS_TEMPLATE, "annual_shifts": generate_annual_shifts_dict(DEFAULT_SHIFTS_TEMPLATE)
    },
    "sesa_plant": {
        "name": "Sesa Biogas Installatie", "country": "Italië (IT)", "volume_m3": 2200.0, "biogas_flow_m3_h": 450.0,
        "ph_nominal": 7.70, "ph_crit_low": 7.30, "temp_c": 39.0, "target_h2s_ppm": 80.0, "alarm_h2s_ppm": 180.0,
        "target_depot_buffer_kg": 100.0, "initial_fe_depot_kg": 110.0, "safety_margin": 1.25, "max_vfa_shock_risk": 2.5,
        "max_dm_pct": 10.5, "initial_dm_pct": 8.5, "initial_tan_mg_l": 2400.0, "hrt_days": 48.0,
        "biogas_price_per_m3": 0.68, "fe_product_price_per_kg": 1.20, "bunker_type": "Schroefvijzel / Mengbunker",
        "fe_dosing_method": "Bovenop substraat (Top-loaded)", "fe_transport_lag_hours": 3.0,
        "recirculation_type": "Eigen Digestaat-Circulaat (Dunne fractie)", "scada_protocol": "Siemens S7 (Profinet / TCP)",
        "scada_ip": "192.168.1.110", "scada_port": 102, "scada_rack": 0, "scada_slot": 2, "scada_db_number": 50,
        "client_name": "Sesa", "client_visible": True,
        "shifts": DEFAULT_SHIFTS_TEMPLATE, "annual_shifts": generate_annual_shifts_dict(DEFAULT_SHIFTS_TEMPLATE)
    },
    "plant_nord": {
        "name": "Installatie Noord (Biomethaan)", "country": "Nederland (NL)", "volume_m3": 4000.0, "biogas_flow_m3_h": 850.0,
        "ph_nominal": 7.80, "ph_crit_low": 7.45, "temp_c": 39.0, "target_h2s_ppm": 20.0, "alarm_h2s_ppm": 50.0,
        "target_depot_buffer_kg": 250.0, "initial_fe_depot_kg": 300.0, "safety_margin": 1.35, "max_vfa_shock_risk": 2.0,
        "max_dm_pct": 9.5, "initial_dm_pct": 7.8, "initial_tan_mg_l": 3100.0, "hrt_days": 45.0,
        "biogas_price_per_m3": 0.75, "fe_product_price_per_kg": 1.25, "bunker_type": "Duwbodem met freeswals",
        "fe_dosing_method": "Voormenging / Direct onderin", "fe_transport_lag_hours": 1.0,
        "recirculation_type": "Schoon Proceswater / Condensaat", "scada_protocol": "OPC-UA Server",
        "scada_ip": "opc.tcp://10.0.0.50", "scada_port": 4840, "scada_rack": 0, "scada_slot": 1, "scada_db_number": 100,
        "client_name": "BioEnergy Nederland", "client_visible": False,
        "shifts": DEFAULT_SHIFTS_TEMPLATE, "annual_shifts": generate_annual_shifts_dict(DEFAULT_SHIFTS_TEMPLATE)
    }
}

default_days = list(range(-2, 7))
day_labels = [f"t{d:+d}" if d != 0 else "t0 (Vandaag)" for d in default_days]

def create_default_schedule():
    return pd.DataFrame({
        "Dag": day_labels, "day_val": default_days,
        "maissilage": [36.0] * 9,
        "drijfmest_rund": [38.0] * 9,
        "kippenmest_droog": [12.0] * 9,
        "melasse": [6.1] * 9,
        "slachtafval_vloeibaar": [0.0] * 9,
        "recirc_m3_day": [15.0] * 9,
        "downtime_hours": [0.0] * 9,
        "fe_product_dosed_kg": [100.0] * 9
    })

def create_default_lab_history():
    return pd.DataFrame({
        "Dag": ["t-2", "t-1", "t0 (Vandaag)"],
        "day_val": [-2, -1, 0],
        "downtime_hours_meas": [0.0, 0.0, 0.0],
        "measured_biogas_m3": [11850.0, 11920.0, 12050.0],
        "measured_h2s_ppm": [85.0, 92.0, 400.0],
        "measured_ph": [7.62, 7.64, 7.63],
        "measured_dm_pct": [8.4, 8.5, 8.6],
        "measured_fos_tac": [0.28, 0.29, 0.30],
        "CH4": [53.0, 53.3, 53.6],
        "CO2": [47.0, 46.7, 46.42],
        "O2": [0.2, 0.18, 0.17],
        "PCI": [14.6, 14.7, 14.8],
        "PCS": [21.1, 21.2, 21.3]
    })

DEFAULT_CHANGELOG = [
    {"Datum": "2026-08-23", "Versie": "v3.0", "Omschrijving": "Tab 11 Integrale Benchmark opgeleverd: H2S-valorisatie, actieve kool standtijd, WKK-oliewissel en Wobbe-index / PCI-PCS vochtbalans."},
    {"Datum": "2026-08-22", "Versie": "v2.6", "Omschrijving": "Ontwikkeling en release van de mobiele BioOptima 360° Client voor opdrachtgevers op locatie."},
    {"Datum": "2026-08-22", "Versie": "v2.5", "Omschrijving": "Modulaire architectuur, PCI/PCS velddata & Changelog dagboek geïntegreerd."},
    {"Datum": "2026-08-21", "Versie": "v2.0", "Omschrijving": "Robuste 500 m3/h scenario engine release, 10 tabs en 52-weken rooster."},
    {"Datum": "2026-08-15", "Versie": "v1.0", "Omschrijving": "Initiële opzet van BioOptima 360 kinetisch model en Streamlit dashboard."}
]

def generate_management_excel(results_df, plant, schedule_df, substrate_prices):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        tot_gas = results_df["biogas_m3_day"].sum()
        tot_rev = results_df["gas_revenue_eur"].sum()
        tot_sub_cost = results_df["substrate_cost_eur"].sum()
        tot_fe_cost = results_df["fe_cost_eur"].sum()
        tot_profit = results_df["net_profit_eur"].sum()
        tot_bags = int(round(results_df["manual_fe_dosed_kg"].sum() / BAG_WEIGHT_KG))

        summary_data = {
            "Parameter": ["Plant", "Date", "Biogas Total (m3)", "Revenue (EUR)", "Substrate Cost (EUR)", "Fe Cost (EUR)", "Bags (20kg)", "Net Profit (EUR)"],
            "Value": [plant.name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), f"{tot_gas:,.0f}", f"EUR {tot_rev:,.2f}", f"EUR {tot_sub_cost:,.2f}", f"EUR {tot_fe_cost:,.2f}", f"{tot_bags}", f"EUR {tot_profit:,.2f}"]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="Management Summary", index=False)
        results_df.to_excel(writer, sheet_name="Kinetics & Yield", index=False)
        schedule_df.to_excel(writer, sheet_name="Feeding Schedule", index=False)
    return output.getvalue()