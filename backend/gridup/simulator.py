from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass, field
from datetime import UTC, datetime
from time import monotonic

from .domain import FeederTelemetry, PanelSnapshot, PanelTelemetry, PhaseValues, Scenario
from .physics import (
    PanelPhysicalParameters,
    dew_point_c,
    electrical_quantities,
    neutral_current_a,
    thermal_step_c,
)
from .risk import assess


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


class SimulationEngine:
    def __init__(
        self,
        panel_count: int = 10,
        tick_seconds: float = 1.0,
        simulation_speed: float = 120.0,
        params: PanelPhysicalParameters | None = None,
    ) -> None:
        self.params = params or PanelPhysicalParameters()
        self.tick_seconds = tick_seconds
        self.simulation_speed = simulation_speed
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
        # Demo sequence ramps in ten wall-clock seconds, as defined in the earlier plan.
        return min(1.0, max(0.0, (monotonic() - state.scenario_started_at) / 10.0))

    @staticmethod
    def _smooth(progress: float) -> float:
        return progress * progress * (3.0 - 2.0 * progress)

    def _scenario_inputs(
        self, state: PanelState, panel_index: int
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
        daily = 0.62 + 0.13 * math.sin(self._simulated_seconds / 3600.0 + panel_index * 0.41)
        ripple = 0.012 * math.sin(self._simulated_seconds / 47.0 + panel_index)
        load = max(0.15, daily + ripple)
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
            load = load * (1.0 - p) + 1.15 * p
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

        currents = tuple(self.params.rated_current_a * load * factor for factor in phase_factors)
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
        # Source panel offers 250 A or 400 A DSYA variants. The MVP selects the
        # 400 A variant and keeps conductor-specific ampacity as a future input.
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

    def step(self, dt_seconds: float | None = None) -> list[PanelSnapshot]:
        dt_wall = dt_seconds if dt_seconds is not None else self.tick_seconds
        dt_sim = dt_wall * self.simulation_speed
        self._simulated_seconds += dt_sim
        generated: list[PanelSnapshot] = []

        for panel_index, state in enumerate(self.states.values(), start=1):
            (
                currents,
                humidity,
                cold_offset,
                contacts,
                arc_detected_only,
                arc_tripped,
                arc_detector,
            ) = self._scenario_inputs(state, panel_index)
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
            hfct_mv = max(0.0, pd_pc * 4.0)  # 0.4 Vpp/100 pC = 4 mV/pC source ratio.

            telemetry = PanelTelemetry(
                panel_id=state.panel_id,
                timestamp=datetime.now(UTC),
                scenario=state.scenario,
                scenario_progress=self._progress(state),
                currents_a=PhaseValues(l1=currents[0], l2=currents[1], l3=currents[2]),
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
