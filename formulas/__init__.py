from dataclasses import dataclass

@dataclass
class PlantProfile:
    name: str = "Corte Pila (Italië) - 1MW CSTR"
    inst_type: str = "agro"
    temp_regime: str = "Mesofiel"
    volume_m3: float = 2500.0
    biogas_flow_m3_h: float = 500.0
    ph_nominal: float = 7.65
    temp_c: float = 38.5
    biogas_price_per_m3: float = 0.68

from .optimization import optimize_dosage_cost, calculate_economic_return
from .sustainability import calculate_red_ii_ghg_balance