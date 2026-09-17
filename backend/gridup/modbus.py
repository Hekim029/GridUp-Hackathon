from __future__ import annotations

import asyncio
from dataclasses import dataclass

from .domain import PanelSnapshot, Severity


def _u16(value: int) -> int:
    return max(0, min(0xFFFF, int(value)))


def _u32_words(value: int) -> tuple[int, int]:
    bounded = max(0, min(0xFFFFFFFF, int(value)))
    return ((bounded >> 16) & 0xFFFF, bounded & 0xFFFF)


def _put_u32(registers: dict[int, int], address: int, value: int) -> None:
    high, low = _u32_words(value)
    registers[address] = high
    registers[address + 1] = low


@dataclass(frozen=True, slots=True)
class DeviceAddress:
    panel_id: str
    mpr_unit_id: int
    tvoc_unit_id: int


def device_addresses(panel_ids: list[str]) -> list[DeviceAddress]:
    return [
        DeviceAddress(panel_id=panel_id, mpr_unit_id=index * 2 - 1, tvoc_unit_id=index * 2)
        for index, panel_id in enumerate(panel_ids, start=1)
    ]


def mpr_registers(snapshot: PanelSnapshot, ct_ratio: float = 500.0) -> dict[int, int]:
    """MPR-53CS PDU addresses. 32-bit values occupy address and address+1."""
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
    # MPR digital I/O is independent from the TVOC device in this prototype.
    registers[84] = 0
    registers[85] = 0

    # Vendor-neutral demo block. These are explicitly not MPR/TVOC source registers.
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
    return registers


def tvoc_registers(snapshot: PanelSnapshot) -> dict[int, int]:
    """ABB TVOC-2 PDU addresses; register number shown to users is address+1."""
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
    def __init__(self, host: str, port: int, panel_ids: list[str]) -> None:
        self.host = host
        self.port = port
        self.addresses = device_addresses(panel_ids)
        self._contexts: dict[int, object] = {}
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        from pymodbus.datastore import (
            ModbusDeviceContext,
            ModbusSequentialDataBlock,
            ModbusServerContext,
        )
        from pymodbus.server import StartAsyncTcpServer

        devices = {}
        for address in self.addresses:
            # DeviceContext converts zero-based PDU addresses to the data block's
            # one-based internal address space.
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
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
