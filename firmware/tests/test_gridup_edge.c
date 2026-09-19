#include "gridup_edge.h"

#include <assert.h>
#include <math.h>
#include <stdio.h>

static gridup_raw_sample_t normal_sample(void) {
    return (gridup_raw_sample_t){
        .current_secondary_ma = 80.0F,
        .ambient_temperature_c = 27.0F,
        .relative_humidity_pct = 48.0F,
        .busbar_temperature_c = {32.0F, 31.0F, 33.0F},
        .dew_point_c = 15.0F,
        .condensation_margin_k = 13.0F,
        .risk_score = 20.0F,
        .hfct_signal_mv = 32.0F,
        .max_feeder_loading_ratio = 0.75F,
        .auxiliary_supply_v = 24.0F,
    };
}

int main(void) {
    assert(fabsf(gridup_primary_current_a(80.0F) - 480.0F) < 0.001F);
    assert(isnan(gridup_primary_current_a(101.0F)));

    gridup_raw_sample_t raw = normal_sample();
    gridup_edge_state_t state = {0};
    assert(gridup_edge_sample(&raw, &state));
    assert(!state.arc_detected_only && !state.arc_tripped);
    assert(state.heartbeat == 1U);

    raw.tvoc_detector_active = true;
    assert(gridup_edge_sample(&raw, &state));
    assert(state.arc_detected_only && !state.arc_tripped);

    raw.tvoc_trip_relay_active = true;
    assert(gridup_edge_sample(&raw, &state));
    assert(!state.arc_detected_only && state.arc_tripped);

    uint16_t registers[GRIDUP_CUSTOM_REGISTER_COUNT] = {0};
    gridup_edge_custom_registers(&raw, &state, registers);
    assert(registers[11] == 0U);
    assert(registers[12] == 1U);
    assert(registers[13] == 240U);

    raw.relative_humidity_pct = 101.0F;
    assert(!gridup_edge_sample(&raw, &state));
    puts("gridup firmware core tests passed");
    return 0;
}
