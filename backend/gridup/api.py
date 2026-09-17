from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import asdict

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .domain import NotificationRecord, PanelSnapshot, Scenario, ScenarioRequest
from .modbus import ModbusServer, device_addresses
from .physics import PanelPhysicalParameters
from .repository import SQLiteRepository
from .simulator import SimulationEngine

settings = get_settings()
params = PanelPhysicalParameters()
engine = SimulationEngine(
    panel_count=settings.panel_count,
    tick_seconds=settings.tick_seconds,
    simulation_speed=settings.simulation_speed,
    params=params,
)
repository = SQLiteRepository(settings.database_path)
modbus = ModbusServer(settings.modbus_host, settings.modbus_port, list(engine.states))


@asynccontextmanager
async def lifespan(app: FastAPI):
    repository.initialize()

    async def on_tick(snapshots: list[PanelSnapshot]) -> None:
        if settings.modbus_enabled:
            modbus.update(snapshots)
        await repository.save(snapshots)

    engine.set_tick_callback(on_tick)
    if settings.modbus_enabled:
        await modbus.start()
    engine.start()
    yield
    await engine.stop()
    if settings.modbus_enabled:
        await modbus.stop()


app = FastAPI(
    title="GridUp 1600 kVA AG Pano API",
    version="0.2.0",
    description="Fizik tabanlı simülasyon, açıklanabilir risk ve Modbus/SCADA prototipi",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "panels": len(engine.states),
        "modbus_enabled": settings.modbus_enabled,
        "model": "1600 kVA AG pano",
    }


@app.get("/api/v1/config")
def configuration() -> dict:
    return {
        "panel": {
            "apparent_power_va": params.apparent_power_va,
            "line_voltage_v": params.line_voltage_v,
            "rated_current_a": params.rated_current_a,
            "busbar": "2 x (100 x 10 mm²)",
            "current_transformer": "2500/5",
            "dimensions_mm": {"width": 1600, "height": 1500, "depth": 450},
        },
        "simulation": {
            "tick_seconds": settings.tick_seconds,
            "time_acceleration": settings.simulation_speed,
            "assumption_status": "uncalibrated_demo_model",
            "labeled_field_fault_data": "unavailable_due_to_confidentiality",
            "jury_numeric_latency_target": None,
        },
        "hardware": {
            "primary_power": "panel_auxiliary_24_v_dc",
            "power_conditioning": "isolated_din_rail_dc_dc_proposed",
            "wireless_required": False,
            "communications": "industrial_modem",
        },
        "modbus_devices": [asdict(item) for item in device_addresses(list(engine.states))],
    }


@app.get("/api/v1/scenarios")
def scenarios() -> list[str]:
    return [scenario.value for scenario in Scenario]


@app.get("/api/v1/panels", response_model=list[PanelSnapshot])
def panels() -> list[PanelSnapshot]:
    if not engine.snapshots:
        engine.step(0.0)
    return list(engine.snapshots.values())


@app.get("/api/v1/panels/{panel_id}", response_model=PanelSnapshot)
def panel(panel_id: str) -> PanelSnapshot:
    snapshot = engine.snapshots.get(panel_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Pano bulunamadı")
    return snapshot


@app.post("/api/v1/panels/{panel_id}/scenario", response_model=PanelSnapshot)
def set_scenario(panel_id: str, request: ScenarioRequest) -> PanelSnapshot:
    if panel_id not in engine.states:
        raise HTTPException(status_code=404, detail="Pano bulunamadı")
    engine.set_scenario(panel_id, request.scenario)
    engine.step(0.0)
    return engine.snapshots[panel_id]


@app.get("/api/v1/panels/{panel_id}/history")
def panel_history(panel_id: str, limit: int = Query(default=120, ge=1, le=1000)) -> list[dict]:
    if panel_id not in engine.states:
        raise HTTPException(status_code=404, detail="Pano bulunamadı")
    return repository.history(panel_id, limit)


@app.get("/api/v1/notifications", response_model=list[NotificationRecord])
def notifications(limit: int = Query(default=50, ge=1, le=500)) -> list[NotificationRecord]:
    return repository.notifications(limit)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    queue = engine.subscribe()
    try:
        if not engine.snapshots:
            engine.step(0.0)
        await websocket.send_json(
            [snapshot.model_dump(mode="json") for snapshot in engine.snapshots.values()]
        )
        while True:
            snapshots = await queue.get()
            await websocket.send_json([snapshot.model_dump(mode="json") for snapshot in snapshots])
    except WebSocketDisconnect:
        pass
    finally:
        engine.unsubscribe(queue)
