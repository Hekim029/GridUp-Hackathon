import type { PanelSnapshot } from "../types";
import { SeverityBadge } from "./SeverityBadge";

interface Props {
  panels: PanelSnapshot[];
  selectedId: string;
  onSelect: (panelId: string) => void;
}

export function PanelMap({ panels, selectedId, onSelect }: Props) {
  return (
    <section className="rounded-2xl border border-white/10 bg-panel/80 p-4 shadow-2xl shadow-black/20">
      <div className="mb-4 flex items-end justify-between">
        <div>
          <p className="eyebrow">Saha görünümü</p>
          <h2 className="text-lg font-semibold text-white">AG pano filosu</h2>
        </div>
        <span className="text-xs text-slate-400">{panels.length} modül canlı</span>
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
        {panels.map((panel) => {
          const { panel_id: panelId } = panel.telemetry;
          const selected = panelId === selectedId;
          return (
            <button
              type="button"
              key={panelId}
              onClick={() => onSelect(panelId)}
              className={`panel-tile panel-${panel.assessment.severity} ${selected ? "panel-selected" : ""}`}
            >
              <span className="mb-4 block h-1.5 w-10 rounded-full bg-current opacity-80" />
              <span className="block text-left text-sm font-semibold">{panelId}</span>
              <span className="mt-1 block text-left text-xs opacity-70">
                {Math.max(...Object.values(panel.telemetry.currents_a)).toFixed(0)} A
              </span>
              <span className="mt-3 block text-left">
                <SeverityBadge severity={panel.assessment.severity} />
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}

