from __future__ import annotations

from gridup.domain import PhaseValues, Scenario, Severity
from gridup.risk import assess
from gridup.simulator import SimulationEngine


def mature_scenario(engine: SimulationEngine, scenario: Scenario, steps: int = 30):
    panel_id = "AG-001"
    engine.set_scenario(panel_id, scenario)
    engine.states[panel_id].scenario_started_at -= 10.0
    snapshot = None
    for _ in range(steps):
        snapshot = engine.step(1.0)[0]
    assert snapshot is not None
    return snapshot


def test_normal_scenario_is_not_critical() -> None:
    snapshot = SimulationEngine(panel_count=1).step(1.0)[0]
    assert snapshot.assessment.severity != Severity.CRITICAL
    assert snapshot.telemetry.arc_detected_only is False
    assert snapshot.telemetry.arc_tripped is False


def test_loose_contact_creates_positive_thermal_residual() -> None:
    snapshot = mature_scenario(SimulationEngine(panel_count=1), Scenario.LOOSE_CONTACT)
    residual = (
        snapshot.telemetry.busbar_temperatures_c.l1 - snapshot.telemetry.expected_temperatures_c.l1
    )
    assert residual > 10.0
    assert any(item.code == "THERMAL_RESIDUAL" for item in snapshot.assessment.findings)


def test_humidity_ingress_reduces_condensation_margin() -> None:
    snapshot = mature_scenario(SimulationEngine(panel_count=1), Scenario.HUMIDITY_INGRESS, steps=2)
    assert snapshot.telemetry.condensation_margin_k < 3.0
    assert any(
        item.code in {"CONDENSATION", "CONDENSATION_NEAR"} for item in snapshot.assessment.findings
    )


def test_detect_only_arc_is_critical_without_breaker_trip() -> None:
    snapshot = mature_scenario(SimulationEngine(panel_count=1), Scenario.ARC_DETECT_ONLY, steps=1)
    assert snapshot.telemetry.arc_detected_only is True
    assert snapshot.telemetry.arc_tripped is False
    assert snapshot.assessment.severity == Severity.CRITICAL
    assert snapshot.assessment.score == 100.0


def test_arc_trip_is_critical_and_increments_breaker_counter() -> None:
    snapshot = mature_scenario(SimulationEngine(panel_count=1), Scenario.ARC_TRIP, steps=1)
    assert snapshot.telemetry.arc_tripped is True
    assert snapshot.telemetry.breaker_trip_counter == 1
    assert snapshot.assessment.severity == Severity.CRITICAL
    assert snapshot.assessment.score == 100.0


def test_pd_activity_reaches_hfct_indicator_rule() -> None:
    snapshot = mature_scenario(SimulationEngine(panel_count=1), Scenario.PD_ACTIVITY, steps=1)
    assert snapshot.telemetry.pd_apparent_charge_pc > 53.33
    assert any(item.code == "HFCT_INDICATOR" for item in snapshot.assessment.findings)


def test_overload_uses_selected_feeder_nominal_current() -> None:
    snapshot = mature_scenario(SimulationEngine(panel_count=1), Scenario.OVERLOAD, steps=1)
    loading = max(feeder.loading_ratio for feeder in snapshot.telemetry.feeders)
    assert loading > 1.0
    assert any(item.code == "FEEDER_OVERLOAD" for item in snapshot.assessment.findings)


def test_single_critical_finding_is_not_diluted() -> None:
    engine = SimulationEngine(panel_count=1)
    snapshot = engine.step(1.0)[0]
    snapshot.telemetry.busbar_temperatures_c = PhaseValues(l1=120.0, l2=30.0, l3=30.0)
    snapshot.telemetry.expected_temperatures_c = PhaseValues(l1=30.0, l2=30.0, l3=30.0)
    result = assess(snapshot.telemetry, engine.params)
    thermal = next(item for item in result.findings if item.expert == "thermal_load")
    assert thermal.score >= 80.0
    assert result.score >= thermal.score
    assert result.severity == Severity.CRITICAL


def test_100_panels_emit_in_one_step() -> None:
    snapshots = SimulationEngine(panel_count=100).step(1.0)
    assert len(snapshots) == 100
    assert len({item.telemetry.panel_id for item in snapshots}) == 100
