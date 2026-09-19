from __future__ import annotations

import asyncio
import csv
import math
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic

from .anomaly import score_thermal_residual
from .domain import FeederTelemetry, PanelSnapshot, PanelTelemetry, PhaseValues, Scenario
from .physics import (
    PanelPhysicalParameters,
    dew_point_c,
    electrical_quantities,
    neutral_current_a,
    thermal_step_c,
)
from .risk import assess

COMPETITION_PROFILE_PRIMARY_FULL_SCALE_A = 600.0


@dataclass(slots=True)
class PanelState:
    panel_id: str
    scenario: Scenario = Scenario.NORMAL
    scenario_started_at: float = field(default_factory=monotonic)
    temperatures_c: list[float] = field(default_factory=lambda: [28.0, 28.0, 28.0])
    expected_temperatures_c: list[float] = field(default_factory=lambda: [28.0, 28.0, 28.0])
    trip_counter: int = 0
    breaker_trip_counter: int = 0
    arc_event_latched: bool = False
    breaker_trip_latched: bool = False
    residual_history_k: list[float] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class CurrentProfilePoint:
    source_index: int
    elapsed_minutes: int
    source_clock: str
    secondary_current_ma: float
    multiplier: float
    primary_current_a: float


def load_competition_current_profile(
    csv_path: str | Path | None = None,
) -> list[CurrentProfilePoint]:
    path = (
        Path(csv_path)
        if csv_path is not None
        else Path(__file__).resolve().parents[2] / "resources" / "competition_current_profile.csv"
    )
    if not path.is_absolute():
        working_directory_path = Path.cwd() / path
        repository_path = Path(__file__).resolve().parents[2] / path
        path = working_directory_path if working_directory_path.exists() else repository_path
    points: list[CurrentProfilePoint] = []
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            point = CurrentProfilePoint(
                source_index=int(row["source_index"]),
                elapsed_minutes=int(row["elapsed_minutes"]),
                source_clock=row["source_clock"],
                secondary_current_ma=float(row["secondary_current_ma"]),
                multiplier=float(row["multiplier"]),
                primary_current_a=float(row["primary_current_a"]),
            )
            calculated_primary = point.secondary_current_ma * point.multiplier / 1000.0
            if not 0.0 <= point.secondary_current_ma <= 100.0:
                raise ValueError(f"Geçersiz 0-100 mA profil değeri: {point.secondary_current_ma}")
            if not math.isclose(point.primary_current_a, calculated_primary, abs_tol=1e-9):
                raise ValueError(f"Akım dönüşümü tutarsız: profil satırı {point.source_index}")
            points.append(point)
    if len(points) != 152 or [point.source_index for point in points] != list(range(152)):
        raise ValueError("Yarışma akım profili 0-151 arasında tam 152 nokta içermelidir")
    return points


class SimulationEngine:
    def __init__(
        self,
        panel_count: int = 10,
        tick_seconds: float = 1.0,
        simulation_speed: float = 120.0,
        params: PanelPhysicalParameters | None = None,
        current_profile: list[CurrentProfilePoint] | None = None,
    ) -> None:
        self.params = params or PanelPhysicalParameters()
        self.tick_seconds = tick_seconds
        self.simulation_speed = simulation_speed
        self.current_profile = (
            load_competition_current_profile() if current_profile is None else current_profile
        )
        self.states = {
            f"AG-{index:03d}": PanelState(panel_id=f"AG-{index:03d}")
            for index in range(1, panel_count + 1)
        }
        self.snapshots: dict[str, PanelSnapshot] = {}
        self._simulated_seconds = 0.0
        self._subscribers: set[asyncio.Queue[list[PanelSnapshot]]] = set()
        self._task: asyncio.Task[None] | None = None
        self._on_tick = None

    def set_tick_callback(self, callback) -> None:
        self._on_tick = callback

    def set_scenario(self, panel_id: str, scenario: Scenario) -> None:
        state = self.states[panel_id]
        state.scenario = scenario
        state.scenario_started_at = monotonic()
        state.arc_event_latched = False
        state.breaker_trip_latched = False

    def _progress(self, state: PanelState) -> float:
        """Calculate linear transition progress over a 10-second wall-clock ramp."""
        return min(1.0, max(0.0, (monotonic() - state.scenario_started_at) / 10.0))

    @staticmethod
    def _smooth(progress: float) -> float:
        return progress * progress * (3.0 - 2.0 * progress)

    def _scenario_inputs(
        self, state: PanelState, panel_index: int, base_current_a: float
    ) -> tuple[
        tuple[float, float, float],
        float,
        float,
        tuple[float, float, float],
        bool,
        bool,
        int | None,
    ]:
        p = self._smooth(self._progress(state))
        phase_factors = (1.00, 0.99, 1.01)
        humidity = 48.0 + 4.0 * math.sin(self._simulated_seconds / 1800.0 + panel_index)
        cold_surface_offset = 1.0
        contact = (
            self.params.normal_contact_resistance_ohm,
            self.params.normal_contact_resistance_ohm,
            self.params.normal_contact_resistance_ohm,
        )
        arc_detected_only = False
        arc_tripped = False
        arc_detector = None

        if state.scenario == Scenario.OVERLOAD:
            target_current = self.params.rated_current_a * 1.15
            base_current_a = base_current_a * (1.0 - p) + target_current * p
        elif state.scenario == Scenario.PHASE_IMBALANCE:
            phase_factors = (
                1.0 + 0.10 * p,
                0.99 - 0.24 * p,
                1.01 - 0.46 * p,
            )
        elif state.scenario == Scenario.LOOSE_CONTACT:
            target = self.params.loose_contact_resistance_ohm
            l1_contact = self.params.normal_contact_resistance_ohm * (1.0 - p) + target * p
            contact = (l1_contact, contact[1], contact[2])
        elif state.scenario == Scenario.HUMIDITY_INGRESS:
            humidity = humidity * (1.0 - p) + 95.0 * p
            cold_surface_offset = 1.0 * (1.0 - p) - 2.0 * p
        elif state.scenario in {Scenario.ARC_DETECT_ONLY, Scenario.ARC_TRIP} and p >= 0.55:
            arc_detected_only = state.scenario == Scenario.ARC_DETECT_ONLY
            arc_tripped = state.scenario == Scenario.ARC_TRIP
            arc_detector = 3
            if not state.arc_event_latched:
                state.trip_counter += 1
                state.arc_event_latched = True
            if arc_tripped and not state.breaker_trip_latched:
                state.breaker_trip_counter += 1
                state.breaker_trip_latched = True

        currents = tuple(base_current_a * factor for factor in phase_factors)
        return (
            currents,
            humidity,
            cold_surface_offset,
            contact,
            arc_detected_only,
            arc_tripped,
            arc_detector,
        )

    @staticmethod
    def _feeders(currents: tuple[float, float, float]) -> list[FeederTelemetry]:
        """Distribute three-phase current across five 400 A DSYA feeders and two spare ways."""
        mean_current = sum(currents) / 3.0
        weights = (0.20, 0.20, 0.20, 0.20, 0.20)
        active = [
            FeederTelemetry(
                feeder_id=f"F{index:02d}",
                active=True,
                nominal_current_a=400.0,
                current_a=mean_current * weight,
            )
            for index, weight in enumerate(weights, start=1)
        ]
        spares = [
            FeederTelemetry(
                feeder_id=f"F{index:02d}",
                active=False,
                nominal_current_a=400.0,
                current_a=0.0,
            )
            for index in (6, 7)
        ]
        return active + spares

    def _current_input(self, panel_index: int) -> tuple[float, CurrentProfilePoint | None, str]:
        if self.current_profile:
            base_index = int(self._simulated_seconds // (15 * 60))
            point = self.current_profile[(base_index + panel_index - 1) % len(self.current_profile)]
            load_pu = point.primary_current_a / COMPETITION_PROFILE_PRIMARY_FULL_SCALE_A
            if not math.isfinite(load_pu) or not 0.0 <= load_pu <= 1.0:
                raise ValueError(
                    "Yarışma akım profili CT tam ölçek aralığı dışında: "
                    f"satır {point.source_index}, {point.primary_current_a} A"
                )

            scaled_current_a = self.params.rated_current_a * load_pu
            return scaled_current_a, point, "competition_xlsx_replay"
        daily = 0.62 + 0.13 * math.sin(self._simulated_seconds / 3600.0 + panel_index * 0.41)
        ripple = 0.012 * math.sin(self._simulated_seconds / 47.0 + panel_index)
        return self.params.rated_current_a * max(0.15, daily + ripple), None, "synthetic_sine"

    def step(self, dt_seconds: float | None = None) -> list[PanelSnapshot]:
        dt_wall = dt_seconds if dt_seconds is not None else self.tick_seconds
        dt_sim = dt_wall * self.simulation_speed
        self._simulated_seconds += dt_sim
        generated: list[PanelSnapshot] = []

        for panel_index, state in enumerate(self.states.values(), start=1):
            base_current_a, profile_point, current_data_source = self._current_input(panel_index)
            (
                currents,
                humidity,
                cold_offset,
                contacts,
                arc_detected_only,
                arc_tripped,
                arc_detector,
            ) = self._scenario_inputs(state, panel_index, base_current_a)
            ambient = 27.0 + 2.0 * math.sin(self._simulated_seconds / 3600.0 + panel_index / 7.0)

            for phase in range(3):
                state.temperatures_c[phase] = thermal_step_c(
                    state.temperatures_c[phase],
                    ambient,
                    currents[phase],
                    contacts[phase],
                    dt_sim,
                    self.params,
                )
                state.expected_temperatures_c[phase] = thermal_step_c(
                    state.expected_temperatures_c[phase],
                    ambient,
                    currents[phase],
                    self.params.normal_contact_resistance_ohm,
                    dt_sim,
                    self.params,
                )

            thermal_residual_k = max(
                actual - baseline
                for actual, baseline in zip(
                    state.temperatures_c, state.expected_temperatures_c, strict=True
                )
            )
            residual_anomaly = score_thermal_residual(state.residual_history_k, thermal_residual_k)
            if residual_anomaly.score < 25.0:
                state.residual_history_k.append(thermal_residual_k)
                state.residual_history_k[:] = state.residual_history_k[-30:]

            line_voltage = max(360.0, self.params.line_voltage_v - max(currents) * 0.003)
            phase_voltage = line_voltage / math.sqrt(3.0)
            pf = 0.92
            active_power, apparent_power = electrical_quantities(currents, line_voltage, pf)
            dew_point = dew_point_c(ambient, humidity)
            cold_surface = ambient + cold_offset
            condensation_margin = cold_surface - dew_point
            pd_pc = 8.0 + 2.0 * math.sin(self._simulated_seconds / 19.0 + panel_index)
            if state.scenario == Scenario.HUMIDITY_INGRESS:
                pd_pc += 18.0 * self._progress(state)
            elif state.scenario == Scenario.PD_ACTIVITY:
                pd_pc += 60.0 * self._progress(state)
            hfct_mv = max(0.0, pd_pc * 4.0)

            telemetry = PanelTelemetry(
                panel_id=state.panel_id,
                timestamp=datetime.now(UTC),
                scenario=state.scenario,
                scenario_progress=self._progress(state),
                currents_a=PhaseValues(l1=currents[0], l2=currents[1], l3=currents[2]),
                current_data_source=current_data_source,
                current_profile_index=(
                    profile_point.source_index if profile_point is not None else None
                ),
                current_profile_elapsed_minutes=(
                    profile_point.elapsed_minutes if profile_point is not None else None
                ),
                current_profile_clock=(
                    profile_point.source_clock if profile_point is not None else None
                ),
                source_secondary_current_ma=(
                    profile_point.secondary_current_ma if profile_point is not None else None
                ),
                source_current_multiplier=(
                    profile_point.multiplier if profile_point is not None else None
                ),
                neutral_current_a=neutral_current_a(currents),
                phase_voltages_v=PhaseValues(l1=phase_voltage, l2=phase_voltage, l3=phase_voltage),
                line_voltages_v=PhaseValues(l1=line_voltage, l2=line_voltage, l3=line_voltage),
                busbar_temperatures_c=PhaseValues(
                    l1=state.temperatures_c[0],
                    l2=state.temperatures_c[1],
                    l3=state.temperatures_c[2],
                ),
                expected_temperatures_c=PhaseValues(
                    l1=state.expected_temperatures_c[0],
                    l2=state.expected_temperatures_c[1],
                    l3=state.expected_temperatures_c[2],
                ),
                thermal_residual_k=thermal_residual_k,
                residual_z_score=residual_anomaly.z_score,
                residual_anomaly_score=residual_anomaly.score,
                residual_reference_samples=residual_anomaly.reference_samples,
                ambient_temperature_c=ambient,
                cold_surface_temperature_c=cold_surface,
                relative_humidity_pct=min(100.0, max(0.0, humidity)),
                dew_point_c=dew_point,
                condensation_margin_k=condensation_margin,
                frequency_hz=50.0,
                active_power_w=active_power,
                apparent_power_va=apparent_power,
                power_factor=pf,
                feeders=self._feeders(currents),
                auxiliary_supply_v=24.0,
                hfct_signal_mv=hfct_mv,
                pd_apparent_charge_pc=max(0.0, pd_pc),
                arc_detected_only=arc_detected_only,
                arc_tripped=arc_tripped,
                arc_detector=arc_detector,
                tvoc_trip_counter=state.trip_counter,
                breaker_trip_counter=state.breaker_trip_counter,
            )
            snapshot = PanelSnapshot(telemetry=telemetry, assessment=assess(telemetry, self.params))
            self.snapshots[state.panel_id] = snapshot
            generated.append(snapshot)
        return generated

    def subscribe(self) -> asyncio.Queue[list[PanelSnapshot]]:
        queue: asyncio.Queue[list[PanelSnapshot]] = asyncio.Queue(maxsize=2)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[list[PanelSnapshot]]) -> None:
        self._subscribers.discard(queue)

    async def _run(self) -> None:
        while True:
            snapshots = self.step()
            if self._on_tick is not None:
                await self._on_tick(snapshots)
            for queue in tuple(self._subscribers):
                if queue.full():
                    queue.get_nowait()
                queue.put_nowait(snapshots)
            await asyncio.sleep(self.tick_seconds)

    def start(self) -> None:
        if self._task is None:
            self.step(0.0)
            self._task = asyncio.create_task(self._run(), name="gridup-simulation")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
