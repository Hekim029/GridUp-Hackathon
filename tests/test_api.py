from __future__ import annotations

import importlib

import httpx
import pytest


@pytest.mark.asyncio
async def test_api_lifecycle_without_modbus(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GRIDUP_MODBUS_ENABLED", "false")
    monkeypatch.setenv("GRIDUP_PANEL_COUNT", "3")
    monkeypatch.setenv("GRIDUP_DATABASE_PATH", str(tmp_path / "api.db"))
    api = importlib.import_module("gridup.api")

    transport = httpx.ASGITransport(app=api.app)
    async with (
        api.lifespan(api.app),
        httpx.AsyncClient(transport=transport, base_url="http://test") as client,
    ):
        health = await client.get("/health")
        assert health.status_code == 200
        assert health.json()["panels"] == 3

        panels = await client.get("/api/v1/panels")
        assert panels.status_code == 200
        assert len(panels.json()) == 3

        config = await client.get("/api/v1/config")
        assert config.status_code == 200
        assert config.json()["panel"]["rated_current_a"] > 2300
        assert config.json()["hardware"]["primary_power"] == "panel_auxiliary_24_v_dc"
        assert config.json()["hardware"]["wireless_required"] is False
        assert config.json()["simulation"]["current_source"] == "competition_xlsx_replay"
        assert config.json()["simulation"]["current_profile_points"] == 152

        profile = await client.get("/api/v1/current-profile")
        assert profile.status_code == 200
        assert len(profile.json()) == 152
        assert profile.json()[0]["primary_current_a"] == 318.0
