from __future__ import annotations

import pytest
from gridup.domain import Scenario
from gridup.repository import SQLiteRepository
from gridup.simulator import SimulationEngine


@pytest.mark.asyncio
async def test_critical_transition_creates_two_simulated_notifications(tmp_path) -> None:
    repository = SQLiteRepository(str(tmp_path / "events.db"))
    repository.initialize()
    engine = SimulationEngine(panel_count=1)
    engine.set_scenario("AG-001", Scenario.ARC_TRIP)
    engine.states["AG-001"].scenario_started_at -= 10.0
    snapshots = engine.step(1.0)

    await repository.save(snapshots)
    await repository.save(snapshots)

    notifications = repository.notifications()
    assert len(notifications) == 2
    assert {item.channel for item in notifications} == {"sms_simulated", "whatsapp_simulated"}


def test_repository_uses_wal_mode(tmp_path) -> None:
    repository = SQLiteRepository(str(tmp_path / "wal.db"))
    repository.initialize()
    with repository._connect() as connection:
        mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode.lower() == "wal"
