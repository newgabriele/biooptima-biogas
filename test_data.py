# Complete Test Dataset for BioOptima 360° (1 MW CSTR Industrial Profile)

TEST_PLANT_PROFILE = {
    "name": "Corte Pila 1MW Industrial CSTR",
    "inst_type": "covergisting",
    "volume_m3": 2500.0,
    "biogas_flow_m3_h": 500.0,
    "ph_nominal": 7.65,
    "ph_crit_low": 7.30,
    "temp_c": 38.5,
    "target_h2s_ppm": 100.0,
    "alarm_h2s_ppm": 200.0,
    "target_depot_buffer_kg": 100.0,
    "initial_fe_depot_kg": 120.0,
    "safety_margin": 1.25,
    "max_vfa_shock_risk": 2.5,
    "initial_tan_mg_l": 2200.0,
    "hrt_days": 50.0,
    "biogas_price_per_m3": 0.68,
    "fe_product_price_per_kg": 1.20
}

TEST_SUBSTRATES_DB = {
    "runderdrijfmest": {
        "ts_pct": 0.09, 
        "vs_pct": 0.75, 
        "s_g_per_kg_ts": 4.0, 
        "n_g_per_kg_ts": 42.0,
        "biogas_m3_per_ton_odm": 350.0, 
        "price_per_ton": -5.0, 
        "f_fast": 0.2, 
        "f_med": 0.5, 
        "f_slow": 0.3, 
        "vfa_risk": 0.5
    },
    "varkensdrijfmest": {
        "ts_pct": 0.06, 
        "vs_pct": 0.80, 
        "s_g_per_kg_ts": 5.5, 
        "n_g_per_kg_ts": 55.0,
        "biogas_m3_per_ton_odm": 380.0, 
        "price_per_ton": -3.0, 
        "f_fast": 0.3, 
        "f_med": 0.5, 
        "f_slow": 0.2, 
        "vfa_risk": 0.8
    },
    "maissilage": {
        "ts_pct": 0.33, 
        "vs_pct": 0.95, 
        "s_g_per_kg_ts": 1.5, 
        "n_g_per_kg_ts": 14.0,
        "biogas_m3_per_ton_odm": 620.0, 
        "price_per_ton": 48.0, 
        "f_fast": 0.5, 
        "f_med": 0.4, 
        "f_slow": 0.1, 
        "vfa_risk": 2.5
    },
    "kippenmest": {
        "ts_pct": 0.55, 
        "vs_pct": 0.80, 
        "s_g_per_kg_ts": 12.0, 
        "n_g_per_kg_ts": 65.0,
        "biogas_m3_per_ton_odm": 480.0, 
        "price_per_ton": 12.0, 
        "f_fast": 0.6, 
        "f_med": 0.3, 
        "f_slow": 0.1, 
        "vfa_risk": 4.0
    },
    "melasse": {
        "ts_pct": 0.75, 
        "vs_pct": 0.98, 
        "s_g_per_kg_ts": 0.8, 
        "n_g_per_kg_ts": 5.0,
        "biogas_m3_per_ton_odm": 750.0, 
        "price_per_ton": 120.0, 
        "f_fast": 0.9, 
        "f_med": 0.1, 
        "f_slow": 0.0, 
        "vfa_risk": 6.0
    }
}

TEST_FEEDING_SCHEDULE = [
    {
        "day": "t-2", 
        "substrates": {"runderdrijfmest": 45.0, "varkensdrijfmest": 20.0, "maissilage": 28.0, "kippenmest": 5.0, "melasse": 1.0}, 
        "fe_product_dosed_kg": 18.0,
        "recirc_m3_day": 35.0
    },
    {
        "day": "t-1", 
        "substrates": {"runderdrijfmest": 45.0, "varkensdrijfmest": 20.0, "maissilage": 28.0, "kippenmest": 5.0, "melasse": 1.0}, 
        "fe_product_dosed_kg": 20.0,
        "recirc_m3_day": 35.0
    },
    {
        "day": "t0 (Vandaag)", 
        "substrates": {"runderdrijfmest": 50.0, "varkensdrijfmest": 15.0, "maissilage": 30.0, "kippenmest": 6.0, "melasse": 1.5}, 
        "fe_product_dosed_kg": 22.0,
        "recirc_m3_day": 40.0
    },
    {
        "day": "t+1", 
        "substrates": {"runderdrijfmest": 50.0, "varkensdrijfmest": 15.0, "maissilage": 32.0, "kippenmest": 6.0, "melasse": 2.0}, 
        "fe_product_dosed_kg": 25.0,
        "recirc_m3_day": 40.0
    },
    {
        "day": "t+2", 
        "substrates": {"runderdrijfmest": 48.0, "varkensdrijfmest": 18.0, "maissilage": 30.0, "kippenmest": 5.0, "melasse": 1.5}, 
        "fe_product_dosed_kg": 20.0,
        "recirc_m3_day": 38.0
    },
    {
        "day": "t+3", 
        "substrates": {"runderdrijfmest": 45.0, "varkensdrijfmest": 20.0, "maissilage": 28.0, "kippenmest": 5.0, "melasse": 1.0}, 
        "fe_product_dosed_kg": 18.0,
        "recirc_m3_day": 35.0
    },
    {
        "day": "t+4", 
        "substrates": {"runderdrijfmest": 45.0, "varkensdrijfmest": 20.0, "maissilage": 28.0, "kippenmest": 5.0, "melasse": 1.0}, 
        "fe_product_dosed_kg": 18.0,
        "recirc_m3_day": 35.0
    },
    {
        "day": "t+5", 
        "substrates": {"runderdrijfmest": 50.0, "varkensdrijfmest": 15.0, "maissilage": 30.0, "kippenmest": 6.0, "melasse": 1.5}, 
        "fe_product_dosed_kg": 22.0,
        "recirc_m3_day": 40.0
    },
    {
        "day": "t+6", 
        "substrates": {"runderdrijfmest": 50.0, "varkensdrijfmest": 15.0, "maissilage": 30.0, "kippenmest": 6.0, "melasse": 1.5}, 
        "fe_product_dosed_kg": 22.0,
        "recirc_m3_day": 40.0
    }
]