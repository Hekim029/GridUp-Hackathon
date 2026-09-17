from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Scenario(StrEnum):
    NORMAL = "normal"
    OVERLOAD = "overload"
    PHASE_IMBALANCE = "phase_imbalance"
    LOOSE_CONTACT = "loose_contact"
    HUMIDITY_INGRESS = "humidity_ingress"
    PD_ACTIVITY = "pd_activity"
    ARC_DETECT_ONLY = "arc_detect_only"
    ARC_TRIP = "arc_trip"


class Severity(StrEnum):
    NORMAL = "normal"
    WATCH = "watch"
    WARNING = "warning"
    CRITICAL = "critical"


class Provenance(StrEnum):
    SOURCE = "source"
    DERIVED = "derived"
    MODEL_ASSUMPTION = "model_assumption"


class PhaseValues(BaseModel):
    l1: float
    l2: float
    l3: float

    def values(self) -> tuple[float, float, float]:
        return (self.l1, self.l2, self.l3)


class FeederTelemetry(BaseModel):
    feeder_id: str
    active: bool
    nominal_current_a: float = Field(gt=0)
    current_a: float = Field(ge=0)

    @property
    def loading_ratio(self) -> float:
        return self.current_a / self.nominal_current_a


class PanelTelemetry(BaseModel):
    panel_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    scenario: Scenario
    scenario_progress: float = Field(ge=0, le=1)
    currents_a: PhaseValues
    neutral_current_a: float = Field(ge=0)
    phase_voltages_v: PhaseValues
    line_voltages_v: PhaseValues
    busbar_temperatures_c: PhaseValues
    expected_temperatures_c: PhaseValues
    ambient_temperature_c: float
    cold_surface_temperature_c: float
    relative_humidity_pct: float = Field(ge=0, le=100)
    dew_point_c: float
    condensation_margin_k: float
    frequency_hz: float
    active_power_w: float
    apparent_power_va: float
    power_factor: float
    feeders: list[FeederTelemetry]
    auxiliary_supply_v: float
    hfct_signal_mv: float = Field(ge=0)
    pd_apparent_charge_pc: float = Field(ge=0)
    arc_detected_only: bool
    arc_tripped: bool
    arc_detector: int | None = None
    tvoc_trip_counter: int = Field(ge=0)
    breaker_trip_counter: int = Field(ge=0)


class ExpertFinding(BaseModel):
    expert: str
    score: float = Field(ge=0, le=100)
    severity: Severity
    code: str
    evidence: list[str]
    likely_cause: str
    recommended_action: str


class RiskAssessment(BaseModel):
    score: float = Field(ge=0, le=100)
    severity: Severity
    summary: str
    findings: list[ExpertFinding]


class PanelSnapshot(BaseModel):
    telemetry: PanelTelemetry
    assessment: RiskAssessment


class ScenarioRequest(BaseModel):
    scenario: Scenario


class NotificationRecord(BaseModel):
    id: int
    panel_id: str
    channel: str
    severity: Severity
    message: str
    created_at: datetime
