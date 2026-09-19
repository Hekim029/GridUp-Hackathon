from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise
from math import isfinite, sqrt
from statistics import pstdev


@dataclass(frozen=True, slots=True)
class ResidualAnomaly:
    """Thermal residual anomaly metrics and baseline tracking metadata."""

    z_score: float
    score: float
    reference_samples: int


def score_thermal_residual(
    history: list[float],
    current_residual_k: float,
    *,
    window: int = 30,
    minimum_samples: int = 12,
    noise_sigma_k: float = 1.5,
) -> ResidualAnomaly:
    """Score positive thermal residual against the healthy physical baseline.

    A calibrated, healthy thermal twin maintains an expected residual of zero
    (E[e] = 0). Historical observations are used exclusively to estimate high-frequency
    measurement noise using a first-difference estimator (std(diff) / sqrt(2)),
    ensuring that a persistent elevated temperature from a developing fault cannot
    adaptively shift the healthy baseline or suppress long-term alarms.

    Args:
        history: Chronological sequence of prior thermal residuals in Kelvin.
        current_residual_k: Instantaneous thermal residual (T_actual - T_expected).
        window: Maximum number of trailing observations to evaluate.
        minimum_samples: Minimum required baseline points before scoring is activated.
        noise_sigma_k: Minimum physical noise floor threshold in Kelvin.

    Returns:
        ResidualAnomaly: Encapsulating the raw Z-score, normalized risk score [0, 100],
        and the count of valid historical samples utilized.

    Raises:
        ValueError: If configuration limits are invalid or if non-finite float
            values are encountered.
    """
    if window < 2:
        raise ValueError("window must be at least 2")
    if minimum_samples < 2 or minimum_samples > window:
        raise ValueError("minimum_samples must be between 2 and window")
    if not isfinite(noise_sigma_k) or noise_sigma_k <= 0.0:
        raise ValueError("noise_sigma_k must be finite and positive")
    if not isfinite(current_residual_k):
        raise ValueError("current_residual_k must be finite")

    reference = history[-window:]
    if any(not isfinite(value) for value in reference):
        raise ValueError("history must contain only finite residuals")

    if len(reference) < minimum_samples:
        return ResidualAnomaly(
            z_score=0.0,
            score=0.0,
            reference_samples=len(reference),
        )

    differences = [current - previous for previous, current in pairwise(reference)]
    measured_sigma_k = pstdev(differences) / sqrt(2.0) if len(differences) >= 2 else 0.0

    sigma_k = max(noise_sigma_k, measured_sigma_k)
    positive_residual_k = max(0.0, current_residual_k)
    z_score = positive_residual_k / sigma_k
    score = min(100.0, z_score / 4.0 * 100.0)

    return ResidualAnomaly(
        z_score=round(z_score, 2),
        score=round(score, 1),
        reference_samples=len(reference),
    )