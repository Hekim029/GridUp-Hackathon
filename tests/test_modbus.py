from __future__ import annotations

from gridup.domain import Scenario
from gridup.modbus import device_addresses, mpr_registers, tvoc_registers
from gridup.simulator import SimulationEngine


def u32(registers: dict[int, int], address: int) -> int:
    return (registers[address] << 16) | registers[address + 1]


def test_device_unit_ids_support_100_panels() -> None:
    addresses = device_addresses([f"AG-{index:03d}" for index in range(1, 101)])
    assert addresses[0].mpr_unit_id == 1
    assert addresses[0].tvoc_unit_id == 2
    assert addresses[-1].tvoc_unit_id == 200


def test_mpr_current_scaling_uses_source_multiplier_and_ct_ratio() -> None:
    snapshot = SimulationEngine(panel_count=1).step(0.0)[0]
    registers = mpr_registers(snapshot)
    decoded_current = u32(registers, 6) * 0.001 * 500.0
    assert abs(decoded_current - snapshot.telemetry.currents_a.l1) <= 0.25


def test_tvoc_detect_only_sets_event_and_detector_without_relay() -> None:
    engine = SimulationEngine(panel_count=1)
    state = engine.states["AG-001"]
    engine.set_scenario("AG-001", Scenario.ARC_DETECT_ONLY)
    state.scenario_started_at -= 10.0
    snapshot = engine.step(1.0)[0]
    registers = tvoc_registers(snapshot)
    assert registers[1300] & 0b1 == 1
    assert registers[206] == 1
    assert registers[210] == 0b100
    assert registers[212] == 0
    assert registers[149] == 1


def test_tvoc_trip_sets_k4_relay_and_custom_breaker_flag() -> None:
    engine = SimulationEngine(panel_count=1)
    state = engine.states["AG-001"]
    engine.set_scenario("AG-001", Scenario.ARC_TRIP)
    state.scenario_started_at -= 10.0
    snapshot = engine.step(1.0)[0]
    tvoc = tvoc_registers(snapshot)
    mpr = mpr_registers(snapshot)
    assert tvoc[1300] & 0b1 == 1
    assert tvoc[210] == 0b100
    assert tvoc[212] == 0b001
    assert mpr[10_011] == 0
    assert mpr[10_012] == 1
    assert mpr[10_013] == 240
