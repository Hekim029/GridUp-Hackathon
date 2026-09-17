from __future__ import annotations

import statistics
import time

from gridup.simulator import SimulationEngine


def main() -> None:
    engine = SimulationEngine(panel_count=100)
    durations_ms = []
    for _ in range(200):
        started = time.perf_counter()
        snapshots = engine.step(1.0)
        durations_ms.append((time.perf_counter() - started) * 1000.0)
        assert len(snapshots) == 100
    print("panels=100 iterations=200")
    print(f"median_ms={statistics.median(durations_ms):.3f}")
    print(f"p95_ms={statistics.quantiles(durations_ms, n=20)[18]:.3f}")


if __name__ == "__main__":
    main()
