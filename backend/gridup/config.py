from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="GRIDUP_", extra="ignore")

    panel_count: int = Field(default=10, ge=1, le=100)
    tick_seconds: float = Field(default=1.0, gt=0.05, le=60)
    simulation_speed: float = Field(default=120.0, gt=0, le=3600)
    database_path: str = "data/gridup.db"
    modbus_enabled: bool = True
    modbus_host: str = "0.0.0.0"
    modbus_port: int = Field(default=1502, ge=1, le=65535)
    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
