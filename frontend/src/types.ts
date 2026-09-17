export type Severity = "normal" | "watch" | "warning" | "critical";
export type Scenario =
  | "normal"
  | "overload"
  | "phase_imbalance"
  | "loose_contact"
  | "humidity_ingress"
  | "pd_activity"
  | "arc_detect_only"
  | "arc_trip";

export interface PhaseValues {
  l1: number;
  l2: number;
  l3: number;
}

export interface Finding {
  expert: string;
  score: number;
  severity: Severity;
  code: string;
  evidence: string[];
  likely_cause: string;
  recommended_action: string;
}

export interface PanelSnapshot {
  telemetry: {
    panel_id: string;
    timestamp: string;
    scenario: Scenario;
    scenario_progress: number;
    currents_a: PhaseValues;
    neutral_current_a: number;
    phase_voltages_v: PhaseValues;
    line_voltages_v: PhaseValues;
    busbar_temperatures_c: PhaseValues;
    expected_temperatures_c: PhaseValues;
    ambient_temperature_c: number;
    cold_surface_temperature_c: number;
    relative_humidity_pct: number;
    dew_point_c: number;
    condensation_margin_k: number;
    frequency_hz: number;
    active_power_w: number;
    apparent_power_va: number;
    power_factor: number;
    feeders: Array<{
      feeder_id: string;
      active: boolean;
      nominal_current_a: number;
      current_a: number;
    }>;
    auxiliary_supply_v: number;
    hfct_signal_mv: number;
    pd_apparent_charge_pc: number;
    arc_detected_only: boolean;
    arc_tripped: boolean;
    arc_detector: number | null;
    tvoc_trip_counter: number;
    breaker_trip_counter: number;
  };
  assessment: {
    score: number;
    severity: Severity;
    summary: string;
    findings: Finding[];
  };
}

export interface TrendPoint {
  time: string;
  current: number;
  temperature: number;
  expected: number;
  risk: number;
  humidity: number;
}
