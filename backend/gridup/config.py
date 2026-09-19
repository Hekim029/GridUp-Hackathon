from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime configuration loaded from environment variables and defaults."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="GRIDUP_", extra="ignore")

    panel_count: int = Field(default=10, ge=1, le=100)
    tick_seconds: float = Field(default=1.0, gt=0.05, le=60)
    simulation_speed: float = Field(default=120.0, gt=0, le=3600)
    current_profile_enabled: bool = True
    current_profile_path: str = "resources/competition_current_profile.csv"
    database_path: str = "data/gridup.db"
    modbus_enabled: bool = True
    modbus_host: str = "0.0.0.0"
    modbus_port: int = Field(default=1502, ge=1, le=65535)
    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    @property
    def cors_origin_list(self) -> list[str]:
        """Return CORS origins parsed as a list of trimmed strings."""
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    """Retrieve and cache the global application settings instance."""
    return Settings()