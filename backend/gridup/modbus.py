from __future__ import annotations

import asyncio
from dataclasses import dataclass

from .domain import PanelSnapshot, Severity


def _u16(value: int) -> int:
    """Clamp an integer value into a single unsigned 16-bit register (0x0000 to 0xFFFF)."""
    return max(0, min(0xFFFF, int(value)))


def _u32_words(value: int) -> tuple[int, int]:
    """Split an unsigned 32-bit integer into big-endian high and low 16-bit words."""
    bounded = max(0, min(0xFFFFFFFF, int(value)))
    return ((bounded >> 16) & 0xFFFF, bounded & 0xFFFF)


def _put_u32(registers: dict[int, int], address: int, value: int) -> None:
    """Store a 32-bit unsigned value across two consecutive 16-bit registers (address, address+1)."""
    high, low = _u32_words(value)
    registers[address] = high
    registers[address + 1] = low


@dataclass(frozen=True, slots=True)
class DeviceAddress:
    """Modbus slave/unit ID pairing for an individual monitored AG panel."""

    panel_id: str
    mpr_unit_id: int
    tvoc_unit_id: int


def device_addresses(panel_ids: list[str]) -> list[DeviceAddress]:
    """Generate deterministic odd/even Modbus unit IDs for energy analyzers and arc monitors.

    Each panel is allocated two unit IDs:
    - Odd IDs (1, 3, 5, ...): ENTES MPR-53CS Energy Analyzer.
    - Even IDs (2, 4, 6, ...): ABB TVOC-2 Optical Arc Guard System.
    """
    return [
        DeviceAddress(panel_id=panel_id, mpr_unit_id=index * 2 - 1, tvoc_unit_id=index * 2)
        for index, panel_id in enumerate(panel_ids, start=1)
    ]


def mpr_registers(snapshot: PanelSnapshot, ct_ratio: float = 500.0) -> dict[int, int]:
    """Build the holding register map for the ENTES MPR-53CS analyzer and extended telemetry.

    Register Architecture:
    1. Standard MPR-53CS Block (Registers 0-85): 32-bit electrical measurements
       (voltages, currents, power, frequency) scaled according to manufacturer CT ratio.
       Digital I/O registers 84-85 are reserved and held independent from the TVOC unit.
    2. Vendor-Neutral Telemetry Block (Registers 10000-10019): High-level digital twin
       metrics, environmental conditions (T/RH, Dew point, Condensation margin), HFCT
       signals, and thermal anomaly residual scores. All signed temperatures use a +50.0 C
       offset and 0.1 C scaling factor.
    """
    t = snapshot.telemetry
    registers: dict[int, int] = {}

    for address, value in zip((0, 2, 4), t.phase_voltages_v.values(), strict=True):
        _put_u32(registers, address, round(value / 0.1))

    for address, value in zip((6, 8, 10), t.currents_a.values(), strict=True):
        _put_u32(registers, address, round(value / (0.001 * ct_ratio)))

    _put_u32(registers, 12, round(t.neutral_current_a / (0.001 * ct_ratio)))

    for address, value in zip((14, 16, 18), t.line_voltages_v.values(), strict=True):
        _put_u32(registers, address, round(value / 0.1))

    _put_u32(registers, 44, round(t.active_power_w / (0.1 * ct_ratio)))
    _put_u32(registers, 52, round(t.apparent_power_va / (0.1 * ct_ratio)))
    _put_u32(registers, 58, round(t.frequency_hz / 0.01))

    registers[84] = 0
    registers[85] = 0

    registers[10_000] = _u16(round((t.ambient_temperature_c + 50.0) * 10))
    registers[10_001] = _u16(round(t.relative_humidity_pct * 10))
    for address, value in zip(
        (10_002, 10_003, 10_004), t.busbar_temperatures_c.values(), strict=True
    ):
        registers[address] = _u16(round((value + 50.0) * 10))

    registers[10_005] = _u16(round((t.dew_point_c + 50.0) * 10))
    registers[10_006] = _u16(round((t.condensation_margin_k + 50.0) * 10))
    registers[10_007] = _u16(round(snapshot.assessment.score * 10))
    registers[10_008] = {
        Severity.NORMAL: 0,
        Severity.WATCH: 1,
        Severity.WARNING: 2,
        Severity.CRITICAL: 3,
    }[snapshot.assessment.severity]
    registers[10_009] = _u16(round(t.hfct_signal_mv * 10))
    registers[10_010] = _u16(round(max(feeder.loading_ratio for feeder in t.feeders) * 1000))
    registers[10_011] = 1 if t.arc_detected_only else 0
    registers[10_012] = 1 if t.arc_tripped else 0
    registers[10_013] = _u16(round(t.auxiliary_supply_v * 10))
    registers[10_014] = _u16(round((t.thermal_residual_k + 50.0) * 10))
    registers[10_015] = _u16(round(t.residual_z_score * 100))
    registers[10_016] = _u16(round(t.residual_anomaly_score * 10))
    registers[10_017] = _u16(t.current_profile_index or 0)
    registers[10_018] = _u16(round((t.source_secondary_current_ma or 0.0) * 10))
    registers[10_019] = _u16(t.current_profile_elapsed_minutes or 0)
    return registers


def tvoc_registers(snapshot: PanelSnapshot) -> dict[int, int]:
    """Build the holding register map for the ABB TVOC-2 Optical Arc Guard device.

    Registers correspond to zero-based PDU addresses (displayed in vendor manuals as PDU + 1):
    - 149: Internal cumulative trip counter.
    - 206: Optical arc detection flag across any sensor channel.
    - 210: 10-bit bitmask identifying the specific triggered optical detector (D1-D10).
    - 212: Solid-state breaker trip output status (K4 relay trip state).
    - 222-225: Optical sensor channel configuration and health bitmasks.
    - 1300: Overall supervisory system state.
    """
    t = snapshot.telemetry
    detector_bit = 0 if t.arc_detector is None else 1 << (t.arc_detector - 1)
    arc_detected = t.arc_detected_only or t.arc_tripped
    system_state = 1 if arc_detected else 0
    return {
        149: _u16(t.tvoc_trip_counter),
        206: 1 if arc_detected else 0,
        210: detector_bit,
        211: 0,
        212: 1 if t.arc_tripped else 0,
        222: 0x03FF,
        223: 0x03FF,
        224: 0x03FF,
        225: 0x03FF,
        1300: system_state,
    }


class ModbusServer:
    """Asynchronous Modbus TCP server gateway interfacing SCADA/RTU to the digital twin fleet."""

    def __init__(self, host: str, port: int, panel_ids: list[str]) -> None:
        self.host = host
        self.port = port
        self.addresses = device_addresses(panel_ids)
        self._contexts: dict[int, object] = {}
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Initialize slave context data blocks and bind the asynchronous Modbus TCP socket.

        Pymodbus DeviceContext internally translates zero-based protocol PDU offsets into
        one-based sequential memory addresses.
        """
        from pymodbus.datastore import (
            ModbusDeviceContext,
            ModbusSequentialDataBlock,
            ModbusServerContext,
        )
        from pymodbus.server import StartAsyncTcpServer

        devices = {}
        for address in self.addresses:
            mpr_block = ModbusSequentialDataBlock(1, [0] * 10_200)
            tvoc_block = ModbusSequentialDataBlock(1, [0] * 1_400)
            mpr_context = ModbusDeviceContext(hr=mpr_block, ir=mpr_block)
            tvoc_context = ModbusDeviceContext(hr=tvoc_block, ir=tvoc_block)
            devices[address.mpr_unit_id] = mpr_context
            devices[address.tvoc_unit_id] = tvoc_context
            self._contexts[address.mpr_unit_id] = mpr_context
            self._contexts[address.tvoc_unit_id] = tvoc_context

        context = ModbusServerContext(devices=devices, single=False)
        self._task = asyncio.create_task(
            StartAsyncTcpServer(context=context, address=(self.host, self.port)),
            name="gridup-modbus",
        )

    def update(self, snapshots: list[PanelSnapshot]) -> None:
        """Synchronize the latest physical simulation snapshots into active Modbus register banks."""
        if not self._contexts:
            return
        by_panel = {snapshot.telemetry.panel_id: snapshot for snapshot in snapshots}
        for address in self.addresses:
            snapshot = by_panel[address.panel_id]
            for unit_id, values in (
                (address.mpr_unit_id, mpr_registers(snapshot)),
                (address.tvoc_unit_id, tvoc_registers(snapshot)),
            ):
                context = self._contexts[unit_id]
                for register, value in values.items():
                    context.setValues(3, register, [value])

    async def stop(self) -> None:
        """Terminate the background TCP server listener task cleanly."""
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None