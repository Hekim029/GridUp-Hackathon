#ifndef GRIDUP_EDGE_H
#define GRIDUP_EDGE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define GRIDUP_CUSTOM_REGISTER_COUNT 14U

typedef struct {
    float current_secondary_ma;
    float ambient_temperature_c;
    float relative_humidity_pct;
    float busbar_temperature_c[3];
    float dew_point_c;
    float condensation_margin_k;
    float risk_score;
    float hfct_signal_mv;
    float max_feeder_loading_ratio;
    float auxiliary_supply_v;
    bool tvoc_detector_active;
    bool tvoc_trip_relay_active;
} gridup_raw_sample_t;

typedef struct {
    float primary_current_a;
    bool arc_detected_only;
    bool arc_tripped;
    uint32_t heartbeat;
} gridup_edge_state_t;

float gridup_primary_current_a(float secondary_ma);
bool gridup_edge_sample(
    const gridup_raw_sample_t *raw,
    gridup_edge_state_t *state
);
void gridup_edge_custom_registers(
    const gridup_raw_sample_t *raw,
    const gridup_edge_state_t *state,
    uint16_t registers[GRIDUP_CUSTOM_REGISTER_COUNT]
);

#endif
