"""
formulas/__init__.py - Package initialisatie en re-exports.
"""

from .core import (
    PlantProfile,
    M_S, M_FE, M_FE2O3, M_FEO, FE_PER_KG_PRODUCT, FE_TO_S_RATIO,
    calculate_h2s_gas_fraction,
    calculate_fe_dissolution_rate,
    calculate_free_ammonia_nh3,
    calculate_fos_tac_soft_sensor,
    calculate_wobbe_index,
    calculate_red_ii_ghg_balance
)

from .kinetics import (
    run_kinetics_calculation,
    validate_plan_safety
)

from .economics import (
    calculate_h2s_valorisation_and_yield_gain,
    calculate_activated_carbon_benchmark,
    calculate_field_vs_potential_benchmark
)

from .optimization import (
    optimize_least_cost_recipe,
    optimize_multiday_least_cost_recipe,
    calculate_substrate_sensitivity_analysis
)