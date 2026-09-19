from __future__ import annotations

from .domain import ExpertFinding, PanelTelemetry, RiskAssessment, Severity
from .physics import PanelPhysicalParameters


def severity_for(score: float) -> Severity:
    """Map a continuous composite risk score [0, 100] to discrete severity levels.

    Threshold Tiers:
    - [80, 100]: CRITICAL (immediate intervention, trip or severe condensation).
    - [55, 80):  WARNING (abnormal trending, feeder overload, thermal imbalance).
    - [25, 55):  WATCH (minor baseline deviation, preliminary HFCT indicator).
    - [0, 25):   NORMAL (healthy physical and electrical operation).
    """
    if score >= 80:
        return Severity.CRITICAL
    if score >= 55:
        return Severity.WARNING
    if score >= 25:
        return Severity.WATCH
    return Severity.NORMAL


def _thermal_finding(t: PanelTelemetry, p: PanelPhysicalParameters) -> ExpertFinding:
    """Evaluate thermal and current loading anomalies using physics-informed thresholds.

    Evaluates busbar thermal residuals, first-difference Z-score anomalies, feeder
    loading ratios, and phase imbalances. Prioritizes physical loose contact indicators
    over pure overcurrent loading.
    """
    currents = t.currents_a.values()
    temperatures = t.busbar_temperatures_c.values()
    expected = t.expected_temperatures_c.values()
    overload = max(currents) / p.rated_current_a
    feeder_loading = max(feeder.loading_ratio for feeder in t.feeders)
    mean_current = sum(currents) / 3.0
    imbalance = (
        0.0 if mean_current == 0 else max(abs(i - mean_current) for i in currents) / mean_current
    )
    residual = max(
        actual - baseline for actual, baseline in zip(temperatures, expected, strict=True)
    )

    score = max(
        max(0.0, (overload - 0.85) / 0.30) * 70.0,
        max(0.0, (feeder_loading - 0.80) / 0.40) * 100.0,
        max(0.0, (imbalance - 0.10) / 0.25) * 70.0,
        max(0.0, residual / 35.0) * 85.0,
        t.residual_anomaly_score * 0.80,
    )
    score = min(score, 100.0)

    if residual >= 12.0:
        code = "THERMAL_RESIDUAL"
        cause = "Akıma göre beklenenden yüksek faz sıcaklığı; temas direnci artışı olası"
        action = (
            "İlgili faz bağlantısını planlı ve güvenli bakımda termal/temas açısından kontrol et"
        )
    elif t.residual_anomaly_score >= 75.0:
        code = "THERMAL_RESIDUAL_STATISTICAL"
        cause = "Fiziksel sıcaklık artığı kendi yakın geçmişinden istatistiksel olarak saptı"
        action = "Artık trendini izle; devam ederse bağlantıyı planlı bakımda doğrula"
    elif feeder_loading >= 1.0:
        code = "FEEDER_OVERLOAD"
        cause = "En az bir çıkış fideri seçili 400 A nominal değeri aşıyor"
        action = "Fider yükünü, koruma ayarını, kablo ürününü ve döşeme koşulunu doğrula"
    elif imbalance >= 0.20:
        code = "PHASE_IMBALANCE"
        cause = "Faz akımları arasında belirgin dengesizlik"
        action = "Yük dağılımını ve nötr iletken akımını kontrol et"
    elif overload >= 1.0:
        code = "OVERLOAD"
        cause = "Anma akımına göre aşırı yük"
        action = "Yükü azalt ve besleme çıkışlarını incele"
    else:
        code = "THERMAL_NORMAL"
        cause = "Termal ve yük ilişkisi beklenen bantta"
        action = "İzlemeye devam et"

    return ExpertFinding(
        expert="thermal_load",
        score=round(score, 1),
        severity=severity_for(score),
        code=code,
        evidence=[
            f"maksimum yük oranı={overload:.3f}",
            f"maksimum fider yük oranı={feeder_loading:.3f}",
            f"faz dengesizliği={imbalance:.3f}",
            f"maksimum termal artık={residual:.1f} K",
            f"residual Z-skoru={t.residual_z_score:.2f}",
            f"istatistiksel anomali skoru={t.residual_anomaly_score:.1f}/100",
            f"referans örnek sayısı={t.residual_reference_samples}",
        ],
        likely_cause=cause,
        recommended_action=action,
    )


def _environment_finding(t: PanelTelemetry) -> ExpertFinding:
    """Assess enclosure condensation and insulation breakdown risks via dew-point margin.

    Rules evaluate the temperature delta between the coldest surface and the thermodynamic
    dew point. Margins below zero indicate active condensation and lock the severity to CRITICAL.
    """
    margin = t.condensation_margin_k
    score = min(100.0, max(0.0, (10.0 - margin) / 10.0 * 90.0))

    if margin <= 0:
        code = "CONDENSATION"
        cause = "Yüzey sıcaklığı çiy noktasında veya altında"
        action = "Yoğuşma kaynağını gider; kabin ısıtma/havalandırma ve izolasyonu kontrol et"
    elif margin <= 3:
        code = "CONDENSATION_NEAR"
        cause = "Yüzey sıcaklığı çiy noktasına yaklaştı"
        action = "Nem girişini ve en soğuk yüzeyi kontrol et"
    else:
        code = "ENVIRONMENT_NORMAL"
        cause = "Yoğuşma marjı yeterli"
        action = "İzlemeye devam et"

    return ExpertFinding(
        expert="environment_insulation",
        score=round(score, 1),
        severity=severity_for(score),
        code=code,
        evidence=[
            f"bağıl nem={t.relative_humidity_pct:.1f}%",
            f"çiy noktası={t.dew_point_c:.1f}°C",
            f"en soğuk izlenen yüzey={t.cold_surface_temperature_c:.1f}°C",
            f"minimum yüzey-çiy noktası marjı={margin:.1f} K",
        ],
        likely_cause=cause,
        recommended_action=action,
    )


def _dielectric_finding(t: PanelTelemetry) -> ExpertFinding:
    """Process optical arc guard states and high-frequency current transformer indicators.

    Optical arc detection triggers instant maximum risk (100.0), distinguishing between
    tripped breakers and un-tripped sensor alerts. HFCT partial discharge activity provides
    an indicative risk score subject to field calibration.
    """
    if t.arc_tripped:
        return ExpertFinding(
            expert="dielectric_safety",
            score=100.0,
            severity=Severity.CRITICAL,
            code="TVOC_ARC_TRIP",
            evidence=[
                f"TVOC ark olayı; detektör={t.arc_detector}",
                "K4 trip çıkışı=aktif",
                f"TVOC olay sayacı={t.tvoc_trip_counter}",
                f"kesici trip sayacı={t.breaker_trip_counter}",
            ],
            likely_cause="Ark algılandı ve kesici açma çıkışı tetiklendi",
            recommended_action="Acil prosedürü uygula; enerjilendirmeden önce kök nedeni incele",
        )

    if t.arc_detected_only:
        return ExpertFinding(
            expert="dielectric_safety",
            score=100.0,
            severity=Severity.CRITICAL,
            code="TVOC_ARC_DETECTED_NO_BREAKER_TRIP",
            evidence=[
                f"TVOC ark olayı; detektör={t.arc_detector}",
                "K4/K5/K6 trip çıkışları=pasif",
                f"TVOC olay sayacı={t.tvoc_trip_counter}",
            ],
            likely_cause="Ark algılandı ancak kesici açma çıkışı tetiklenmedi",
            recommended_action=(
                "Acil inceleme başlat; algılama modu ve kesici açma zincirini doğrula"
            ),
        )

    score = min(60.0, max(0.0, (t.pd_apparent_charge_pc - 20.0) / 80.0 * 60.0))
    return ExpertFinding(
        expert="dielectric_safety",
        score=round(score, 1),
        severity=severity_for(score),
        code="HFCT_INDICATOR" if score >= 25 else "DIELECTRIC_NORMAL",
        evidence=[
            f"HFCT çıkış göstergesi={t.hfct_signal_mv:.3f} mV",
            f"sentetik görünür yük={t.pd_apparent_charge_pc:.1f} pC",
        ],
        likely_cause="Kalibrasyon gerektiren HFCT aktivitesi"
        if score >= 25
        else "Ark veya belirgin HFCT aktivitesi yok",
        recommended_action="HFCT analizörü ile doğrula" if score >= 25 else "İzlemeye devam et",
    )


def assess(t: PanelTelemetry, params: PanelPhysicalParameters) -> RiskAssessment:
    """Synthesize multi-expert domain findings into an explainable overall risk score.

    Applies non-linear risk compounding where secondary and tertiary degraded factors
    amplify the dominant risk score without artificially exceeding 100.0.
    """
    findings = [
        _thermal_finding(t, params),
        _environment_finding(t),
        _dielectric_finding(t),
    ]
    ordered = sorted((finding.score for finding in findings), reverse=True)
    base_score = ordered[0]
    multi_factor_uplift = ordered[1] * 0.20 + ordered[2] * 0.10
    score = min(100.0, base_score + multi_factor_uplift * (1.0 - base_score / 100.0))
    severity = severity_for(score)
    lead = max(findings, key=lambda finding: finding.score)
    return RiskAssessment(
        score=round(score, 1),
        severity=severity,
        summary=f"{lead.likely_cause}. Öneri: {lead.recommended_action}",
        findings=findings,
    )