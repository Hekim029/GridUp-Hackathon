from __future__ import annotations

import pytest
from gridup.physics import (
    PanelPhysicalParameters,
    copper_resistance_ohm,
    dew_point_c,
    neutral_current_a,
    sensor_secondary_ma_to_primary_a,
    thermal_step_c,
)


def test_rated_current_for_1600_kva_400_v() -> None:
    params = PanelPhysicalParameters()
    assert params.rated_current_a == pytest.approx(2309.401, rel=1e-6)


def test_given_current_sensor_conversion() -> None:
    assert sensor_secondary_ma_to_primary_a(100.0) == pytest.approx(600.0)
    assert sensor_secondary_ma_to_primary_a(53.0) == pytest.approx(318.0)


def test_parallel_busbar_area_and_resistance() -> None:
    params = PanelPhysicalParameters()
    assert params.busbar_area_total_m2 == pytest.approx(0.002)
    assert copper_resistance_ohm(20.0, params) == pytest.approx(8.4e-6)


def test_thermal_step_heats_under_load_and_cools_without_load() -> None:
    params = PanelPhysicalParameters()
    heated = thermal_step_c(27.0, 27.0, 2300.0, 80e-6, 10.0, params)
    cooled = thermal_step_c(50.0, 27.0, 0.0, 2e-6, 10.0, params)
    assert heated > 27.0
    assert cooled < 50.0


def test_dew_point_and_balanced_neutral_current() -> None:
    assert dew_point_c(30.0, 100.0) == pytest.approx(30.0, abs=0.01)
    assert neutral_current_a((100.0, 100.0, 100.0)) == pytest.approx(0.0, abs=1e-9)
    assert neutral_current_a((100.0, 0.0, 0.0)) == pytest.approx(100.0)
