from __future__ import annotations

import math

from gridup.anomaly import score_thermal_residual
from gridup.domain import PhaseValues, Scenario, Severity
from gridup.risk import assess
from gridup.simulator import SimulationEngine, load_competition_current_profile


def test_competition_profile_preserves_all_152_xlsx_points() -> None:
    profile = load_competition_current_profile()
    assert len(profile) == 152
    assert profile[0].source_clock == "00:00"
    assert profile[0].secondary_current_ma == 53.0
    assert profile[0].primary_current_a == 318.0
    assert profile[-1].elapsed_minutes == 2265
    assert profile[-1].source_clock == "13:45"
    assert min(point.primary_current_a for point in profile) == 90.0
    assert max(point.primary_current_a for point in profile) == 540.0


def test_default_simulation_replays_competition_profile_into_l1() -> None:
    engine = SimulationEngine(panel_count=1)
    snapshot = engine.step(0.0)[0]
    assert snapshot.telemetry.current_data_source == "competition_xlsx_replay"
    assert snapshot.telemetry.current_profile_index == 0
    assert snapshot.telemetry.source_secondary_current_ma == 53.0
    assert snapshot.telemetry.source_current_multiplier == 6000.0
    expected_current_a = engine.params.rated_current_a * (318.0 / 600.0)
    assert math.isclose(snapshot.telemetry.currents_a.l1, expected_current_a, rel_tol=1e-9)


def test_residual_zscore_uses_prior_window_and_warmup() -> None:
    assert score_thermal_residual([0.0] * 11, 5.0).score == 0.0

    sensor_noise = score_thermal_residual([0.0] * 12, 0.4)
    assert sensor_noise.z_score == 0.27
    assert sensor_noise.score == 6.7
    assert sensor_noise.reference_samples == 12

    threshold_event = score_thermal_residual([0.0] * 12, 6.0)
    assert threshold_event.z_score == 4.0
    assert threshold_event.score == 100.0


def test_persistent_positive_residual_does_not_become_normal() -> None:
    result = score_thermal_residual([25.0] * 30, 25.0)
    assert result.z_score > 4.0
    assert result.score == 100.0


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
    engine = SimulationEngine(panel_count=1)
    for _ in range(15):
        engine.step(1.0)
    snapshot = mature_scenario(engine, Scenario.LOOSE_CONTACT, steps=5)
    residual = (
        snapshot.telemetry.busbar_temperatures_c.l1 - snapshot.telemetry.expected_temperatures_c.l1
    )
    assert residual > 0.2
    assert snapshot.telemetry.residual_z_score >= 3.0
    assert any(item.code == "THERMAL_RESIDUAL_STATISTICAL" for item in snapshot.assessment.findings)


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
