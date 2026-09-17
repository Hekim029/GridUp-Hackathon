import type { PanelSnapshot } from "../types";

const phaseColors = ["#fb7185", "#fbbf24", "#60a5fa"];

export function PanelTwin({ panel }: { panel: PanelSnapshot }) {
  const phases = [
    [panel.telemetry.currents_a.l1, panel.telemetry.busbar_temperatures_c.l1],
    [panel.telemetry.currents_a.l2, panel.telemetry.busbar_temperatures_c.l2],
    [panel.telemetry.currents_a.l3, panel.telemetry.busbar_temperatures_c.l3],
  ];
  const severity = panel.assessment.severity;

  return (
    <div className={`twin-shell twin-${severity}`}>
      <div className="flex items-center justify-between px-4 pt-4">
        <div>
          <p className="eyebrow">Dinamik ön görünüş</p>
          <h2 className="text-xl font-semibold text-white">1600 kVA AG pano</h2>
        </div>
        <div className="text-right text-xs text-slate-400">
          <div>1600 × 1500 × 450 mm</div>
          <div>CT 2500/5</div>
        </div>
      </div>
      <svg viewBox="0 0 640 510" role="img" aria-label="1600 kVA AG pano dinamik ön görünüşü" className="w-full">
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>
        <rect x="40" y="30" width="560" height="430" rx="8" fill="#0a1728" stroke="#475569" strokeWidth="3" />
        <rect x="60" y="50" width="400" height="120" rx="4" fill="#102238" stroke="#334155" />
        <rect x="478" y="50" width="102" height="120" rx="4" fill="#102238" stroke="#334155" />
        <text x="492" y="73" fill="#94a3b8" fontSize="10">ENERJİ ANALİZÖRÜ</text>
        <text x="501" y="112" fill="#f8fafc" fontSize="20" fontWeight="700">
          {(panel.telemetry.apparent_power_va / 1_000_000).toFixed(2)}
        </text>
        <text x="520" y="130" fill="#94a3b8" fontSize="10">MVA</text>

        {phases.map(([current, temp], index) => {
          const x = 108 + index * 112;
          const hot = temp > 60;
          return (
            <g key={x} filter={hot ? "url(#glow)" : undefined}>
              <rect x={x} y="62" width="30" height="94" rx="5" fill={phaseColors[index]} opacity={0.20 + Math.min(current / 2309, 1) * 0.65} />
              <rect x={x + 8} y="62" width="6" height="94" fill={phaseColors[index]} />
              <rect x={x + 16} y="62" width="6" height="94" fill={phaseColors[index]} opacity="0.78" />
              <text x={x - 4} y="185" fill={phaseColors[index]} fontSize="12" fontWeight="700">L{index + 1}</text>
              <text x={x - 8} y="203" fill="#cbd5e1" fontSize="11">{current.toFixed(0)} A</text>
              <text x={x - 8} y="219" fill="#cbd5e1" fontSize="11">{temp.toFixed(1)} °C</text>
            </g>
          );
        })}

        <line x1="60" y1="238" x2="580" y2="238" stroke="#334155" strokeWidth="2" />
        {Array.from({ length: 7 }).map((_, index) => {
          const x = 64 + index * 72;
          const spare = index >= 5;
          return (
            <g key={x}>
              <rect x={x} y="258" width="58" height="92" rx="4" fill={spare ? "#0f1d2e" : "#172c44"} stroke="#475569" />
              <rect x={x + 8} y="270" width="42" height="24" rx="2" fill="#091522" stroke="#64748b" />
              <circle cx={x + 29} cy="312" r="7" fill={spare ? "#475569" : "#2dd4bf"} opacity="0.8" />
              <text x={x + 11} y="338" fill="#94a3b8" fontSize="9">{spare ? "YEDEK" : `ÇIKIŞ ${index + 1}`}</text>
            </g>
          );
        })}
        <rect x="64" y="374" width="350" height="60" rx="4" fill="#0d1b2e" stroke="#334155" />
        <text x="80" y="400" fill="#94a3b8" fontSize="10">YOĞUŞMA MARJI</text>
        <text x="80" y="420" fill={panel.telemetry.condensation_margin_k < 3 ? "#fb7185" : "#2dd4bf"} fontSize="18" fontWeight="700">
          {panel.telemetry.condensation_margin_k.toFixed(1)} K
        </text>
        <rect x="432" y="374" width="148" height="60" rx="4" fill={panel.telemetry.arc_detected_only || panel.telemetry.arc_tripped ? "#7f1d1d" : "#0d1b2e"} stroke={panel.telemetry.arc_detected_only || panel.telemetry.arc_tripped ? "#fb7185" : "#334155"} />
        <text x="448" y="400" fill="#94a3b8" fontSize="10">TVOC-2 ARK</text>
        <text x="448" y="420" fill={panel.telemetry.arc_detected_only || panel.telemetry.arc_tripped ? "#fecdd3" : "#2dd4bf"} fontSize="14" fontWeight="700">
          {panel.telemetry.arc_tripped
            ? `TRIP D${panel.telemetry.arc_detector}`
            : panel.telemetry.arc_detected_only
              ? `ALARM D${panel.telemetry.arc_detector}`
              : "HAZIR"}
        </text>
      </svg>
    </div>
  );
}
