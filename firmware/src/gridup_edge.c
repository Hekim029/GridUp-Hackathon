#include "gridup_edge.h"

#include <math.h>

static uint16_t clamp_u16(float value) {
    if (!isfinite(value) || value <= 0.0F) {
        return 0U;
    }
    if (value >= 65535.0F) {
        return 65535U;
    }
    return (uint16_t)lroundf(value);
}

float gridup_primary_current_a(float secondary_ma) {
    if (!isfinite(secondary_ma) || secondary_ma < 0.0F || secondary_ma > 100.0F) {
        return NAN;
    }
    return secondary_ma * 6.0F;
}

bool gridup_edge_sample(const gridup_raw_sample_t *raw, gridup_edge_state_t *state) {
    if (raw == NULL || state == NULL) {
        return false;
    }
    const float primary_current = gridup_primary_current_a(raw->current_secondary_ma);
    if (!isfinite(primary_current)) {
        return false;
    }
    if (!isfinite(raw->relative_humidity_pct) || raw->relative_humidity_pct < 0.0F ||
        raw->relative_humidity_pct > 100.0F) {
        return false;
    }

    state->primary_current_a = primary_current;
    state->arc_tripped = raw->tvoc_detector_active && raw->tvoc_trip_relay_active;
    state->arc_detected_only = raw->tvoc_detector_active && !raw->tvoc_trip_relay_active;
    state->heartbeat += 1U;
    return true;
}

void gridup_edge_custom_registers(
    const gridup_raw_sample_t *raw,
    const gridup_edge_state_t *state,
    uint16_t registers[GRIDUP_CUSTOM_REGISTER_COUNT]
) {
    registers[0] = clamp_u16((raw->ambient_temperature_c + 50.0F) * 10.0F);
    registers[1] = clamp_u16(raw->relative_humidity_pct * 10.0F);
    registers[2] = clamp_u16((raw->busbar_temperature_c[0] + 50.0F) * 10.0F);
    registers[3] = clamp_u16((raw->busbar_temperature_c[1] + 50.0F) * 10.0F);
    registers[4] = clamp_u16((raw->busbar_temperature_c[2] + 50.0F) * 10.0F);
    registers[5] = clamp_u16((raw->dew_point_c + 50.0F) * 10.0F);
    registers[6] = clamp_u16((raw->condensation_margin_k + 50.0F) * 10.0F);
    registers[7] = clamp_u16(raw->risk_score * 10.0F);
    registers[8] = raw->risk_score >= 80.0F ? 3U : raw->risk_score >= 55.0F ? 2U :
                   raw->risk_score >= 25.0F ? 1U : 0U;
    registers[9] = clamp_u16(raw->hfct_signal_mv * 10.0F);
    registers[10] = clamp_u16(raw->max_feeder_loading_ratio * 1000.0F);
    registers[11] = state->arc_detected_only ? 1U : 0U;
    registers[12] = state->arc_tripped ? 1U : 0U;
    registers[13] = clamp_u16(raw->auxiliary_supply_v * 10.0F);
}
