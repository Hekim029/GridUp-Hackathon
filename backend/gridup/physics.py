from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PanelPhysicalParameters:
    # source: 1600kVA AG Pano Teknik Özellikleri.pdf
    apparent_power_va: float = 1_600_000.0
    line_voltage_v: float = 400.0
    busbar_count_parallel: int = 2
    busbar_width_m: float = 0.100
    busbar_thickness_m: float = 0.010
    current_transformer_primary_a: float = 2500.0
    current_transformer_secondary_a: float = 5.0

    # prior-plan physical constants; must remain visible and replaceable.
    copper_resistivity_20_ohm_m: float = 1.68e-8
    copper_temperature_coefficient_per_k: float = 0.0039

    # model_assumption: source drawing does not specify the effective heated joint.
    effective_conductor_length_m: float = 1.0
    normal_contact_resistance_ohm: float = 2.0e-6
    loose_contact_resistance_ohm: float = 80.0e-6
    thermal_capacitance_j_per_k: float = 15_000.0
    thermal_resistance_k_per_w: float = 0.15

    @property
    def rated_current_a(self) -> float:
        return self.apparent_power_va / (math.sqrt(3.0) * self.line_voltage_v)

    @property
    def busbar_area_total_m2(self) -> float:
        return self.busbar_count_parallel * self.busbar_width_m * self.busbar_thickness_m

    @property
    def ct_ratio(self) -> float:
        return self.current_transformer_primary_a / self.current_transformer_secondary_a


def sensor_secondary_ma_to_primary_a(secondary_ma: float, primary_a: float = 600.0) -> float:
    """İstenen Veriler.xlsx: 100 mA sekonderin 600 A primere karşılığı."""
    return secondary_ma * primary_a / 100.0


def copper_resistance_ohm(
    temperature_c: float,
    params: PanelPhysicalParameters,
) -> float:
    rho_t = params.copper_resistivity_20_ohm_m * (
        1.0 + params.copper_temperature_coefficient_per_k * (temperature_c - 20.0)
    )
    return rho_t * params.effective_conductor_length_m / params.busbar_area_total_m2


def thermal_step_c(
    temperature_c: float,
    ambient_temperature_c: float,
    current_a: float,
    contact_resistance_ohm: float,
    dt_seconds: float,
    params: PanelPhysicalParameters,
) -> float:
    """Explicit Euler solution of C*dT/dt = I²R - (T-Ta)/Rth."""
    bulk = copper_resistance_ohm(temperature_c, params)
    heat_w = current_a**2 * (bulk + contact_resistance_ohm)
    cooling_w = (temperature_c - ambient_temperature_c) / params.thermal_resistance_k_per_w
    derivative_k_per_s = (heat_w - cooling_w) / params.thermal_capacitance_j_per_k
    return temperature_c + derivative_k_per_s * dt_seconds


def saturation_vapor_pressure_hpa(temperature_c: float) -> float:
    return 6.112 * math.exp((17.67 * temperature_c) / (243.5 + temperature_c))


def dew_point_c(temperature_c: float, relative_humidity_pct: float) -> float:
    bounded_rh = min(max(relative_humidity_pct, 0.1), 100.0)
    vapor_pressure = saturation_vapor_pressure_hpa(temperature_c) * bounded_rh / 100.0
    log_term = math.log(vapor_pressure / 6.112)
    return 243.5 * log_term / (17.67 - log_term)


def neutral_current_a(currents: tuple[float, float, float]) -> float:
    """Fundamental-frequency phasor sum for phases separated by 120 degrees."""
    i1, i2, i3 = currents
    x = i1 - 0.5 * i2 - 0.5 * i3
    y = (math.sqrt(3.0) / 2.0) * (i2 - i3)
    return math.hypot(x, y)


def electrical_quantities(
    currents: tuple[float, float, float],
    line_voltage_v: float,
    power_factor: float,
) -> tuple[float, float]:
    mean_current = sum(currents) / 3.0
    apparent_power = math.sqrt(3.0) * line_voltage_v * mean_current
    return apparent_power * power_factor, apparent_power
