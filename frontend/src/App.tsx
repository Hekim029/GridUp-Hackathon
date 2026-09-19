import { useEffect, useMemo, useState } from "react";
import { PanelMap } from "./components/PanelMap";
import { PanelTwin } from "./components/PanelTwin";
import { NotificationPanel } from "./components/NotificationPanel";
import { SeverityBadge } from "./components/SeverityBadge";
import { TrendChart } from "./components/TrendChart";
import type { PanelSnapshot, Scenario, TrendPoint } from "./types";

const scenarioLabels: Record<Scenario, string> = {
  normal: "Normal çalışma",
  overload: "Aşırı yük",
  phase_imbalance: "Faz dengesizliği",
  loose_contact: "Gevşek L1 teması",
  humidity_ingress: "Nem girişi",
  pd_activity: "HFCT aktivitesi",
  arc_detect_only: "Ark algıla · açtırma yok",
  arc_trip: "Ark algıla · kesiciyi açtır",
};

const scenarios = Object.keys(scenarioLabels) as Scenario[];

function toTrend(panel: PanelSnapshot): TrendPoint {
  return {
    time: new Date(panel.telemetry.timestamp).toLocaleTimeString("tr-TR"),
    current: Number(panel.telemetry.currents_a.l1.toFixed(1)),
    temperature: Number(panel.telemetry.busbar_temperatures_c.l1.toFixed(2)),
    expected: Number(panel.telemetry.expected_temperatures_c.l1.toFixed(2)),
    risk: panel.assessment.score,
    humidity: panel.telemetry.relative_humidity_pct,
  };
}

export default function App() {
  const [panels, setPanels] = useState<PanelSnapshot[]>([]);
  const [selectedId, setSelectedId] = useState("AG-001");
  const [connected, setConnected] = useState(false);
  const [history, setHistory] = useState<Record<string, TrendPoint[]>>({});
  const [commandPending, setCommandPending] = useState(false);

  useEffect(() => {
    let socket: WebSocket | undefined;
    let retry: number | undefined;

    const connect = () => {
      const protocol = window.location.protocol === "https:" ? "wss" : "ws";
      socket = new WebSocket(`${protocol}://${window.location.host}/ws`);
      socket.onopen = () => setConnected(true);
      socket.onclose = () => {
        setConnected(false);
        retry = window.setTimeout(connect, 1500);
      };
      socket.onmessage = (event) => {
        const incoming = JSON.parse(event.data) as PanelSnapshot[];
        setPanels(incoming);
        setHistory((previous) => {
          const next = { ...previous };
          for (const panel of incoming) {
            const id = panel.telemetry.panel_id;
            next[id] = [...(next[id] ?? []), toTrend(panel)].slice(-90);
          }
          return next;
        });
      };
    };

    connect();
    return () => {
      if (retry) window.clearTimeout(retry);
      socket?.close();
    };
  }, []);

  const selected = useMemo(
    () => panels.find((panel) => panel.telemetry.panel_id === selectedId) ?? panels[0],
    [panels, selectedId],
  );

  async function setScenario(scenario: Scenario) {
    if (!selected) return;
    setCommandPending(true);
    try {
      await fetch(`/api/v1/panels/${selected.telemetry.panel_id}/scenario`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario }),
      });
    } finally {
      setCommandPending(false);
    }
  }

  if (!selected) {
    return (
      <main className="grid min-h-screen place-items-center bg-ink text-slate-200">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-cyan border-t-transparent" />
          <p>On-premise simülatöre bağlanılıyor…</p>
        </div>
      </main>
    );
  }

  const t = selected.telemetry;
  const a = selected.assessment;
  const maxCurrent = Math.max(...Object.values(t.currents_a));
  const maxTemp = Math.max(...Object.values(t.busbar_temperatures_c));
  const maxFeederLoading = Math.max(
    ...t.feeders.map((feeder) => feeder.current_a / feeder.nominal_current_a),
  );

  return (
    <main className="min-h-screen bg-ink text-slate-200">
      <div className="mx-auto max-w-[1560px] px-4 py-5 lg:px-8">
        <header className="mb-5 flex flex-col gap-4 border-b border-white/10 pb-5 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="eyebrow">ADM/GDZ Grid Up Hackathon</p>
            <h1 className="text-2xl font-semibold tracking-tight text-white md:text-3xl">Pano içi erken uyarı dijital ikizi</h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-400">1600 kVA AG pano · fizik tabanlı termal/yük modeli · Modbus/SCADA görünümü</p>
          </div>
          <div className="flex items-center gap-3 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs">
            <span className={`h-2 w-2 rounded-full ${connected ? "bg-emerald-400" : "bg-rose-400"}`} />
            {connected ? "Canlı veri akışı" : "Bağlantı bekleniyor"}
          </div>
        </header>

        <PanelMap panels={panels} selectedId={selected.telemetry.panel_id} onSelect={setSelectedId} />

        <section className="card mt-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="eyebrow">Akım veri kaynağı</p>
            <h2 className="text-lg font-semibold text-white">
              Yarışma XLSX profili · 152 nokta · 15 dakika
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              Sentetik Akım Sensörü sayfası · L1 kaynak değeri I²R termal modele doğrudan girer
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3 text-right text-sm">
            <div>
              <div className="text-xs text-slate-500">Replay noktası</div>
              <div className="font-semibold text-white">
                #{(t.current_profile_index ?? 0) + 1}/152 · {t.current_profile_clock ?? "—"}
              </div>
            </div>
            <div>
              <div className="text-xs text-slate-500">Kaynak dönüşümü</div>
              <div className="font-semibold text-white">
                {(t.source_secondary_current_ma ?? 0).toFixed(0)} mA × {(t.source_current_multiplier ?? 0).toFixed(0)}
              </div>
            </div>
          </div>
        </section>

        <div className="mt-5 grid gap-5 xl:grid-cols-[1.25fr_0.75fr]">
          <PanelTwin panel={selected} />
          <section className="card flex flex-col">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="eyebrow">Orkestratör kararı</p>
                <h2 className="text-xl font-semibold text-white">{t.panel_id}</h2>
              </div>
              <SeverityBadge severity={a.severity} />
            </div>
            <div className="my-5 flex items-end gap-3">
              <span className="text-6xl font-semibold tracking-tight text-white">{a.score.toFixed(0)}</span>
              <span className="pb-2 text-sm text-slate-500">/ 100 risk</span>
            </div>
            <p className="text-sm leading-6 text-slate-300">{a.summary}</p>
            <div className="mt-5 grid grid-cols-2 gap-3">
              <Metric label="Maks. akım" value={`${maxCurrent.toFixed(0)} A`} />
              <Metric label="Maks. sıcaklık" value={`${maxTemp.toFixed(1)} °C`} />
              <Metric label="Nem" value={`%${t.relative_humidity_pct.toFixed(1)}`} />
              <Metric label="Çiy marjı" value={`${t.condensation_margin_k.toFixed(1)} K`} />
              <Metric label="Maks. fider yükü" value={`%${(maxFeederLoading * 100).toFixed(0)}`} />
              <Metric label="Yardımcı besleme" value={`${t.auxiliary_supply_v.toFixed(0)} V DC`} />
              <Metric label="Nötr akımı" value={`${t.neutral_current_a.toFixed(0)} A`} />
              <Metric label="HFCT gösterge" value={`${t.hfct_signal_mv.toFixed(1)} mV`} />
              <Metric label="Termal artık" value={`${t.thermal_residual_k.toFixed(2)} K`} />
              <Metric label="Residual Z-skoru" value={t.residual_z_score.toFixed(2)} />
              <Metric label="İstatistiksel skor" value={`${t.residual_anomaly_score.toFixed(0)}/100`} />
              <Metric label="Referans pencere" value={`${t.residual_reference_samples}/30`} />
            </div>
          </section>
        </div>

        <section className="card mt-5">
          <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="eyebrow">Demo kontrolü</p>
              <h2 className="text-lg font-semibold text-white">Senaryo enjekte et</h2>
            </div>
            <span className="text-xs text-slate-500">10 saniyelik kontrollü geçiş · 120× demo zaman ölçeği</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {scenarios.map((scenario) => (
              <button
                type="button"
                key={scenario}
                disabled={commandPending}
                onClick={() => setScenario(scenario)}
                className={`scenario-button ${t.scenario === scenario ? "scenario-active" : ""}`}
              >
                {scenarioLabels[scenario]}
              </button>
            ))}
          </div>
        </section>

        <div className="mt-5 grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
          <TrendChart data={history[t.panel_id] ?? []} />
          <section className="card">
            <div className="mb-4">
              <p className="eyebrow">Açıklanabilir analiz</p>
              <h2 className="text-lg font-semibold text-white">Uzman modüller</h2>
            </div>
            <div className="space-y-3">
              {a.findings.map((finding) => (
                <article key={finding.expert} className="rounded-xl border border-white/10 bg-white/[0.025] p-4">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="text-sm font-semibold text-slate-100">{finding.expert.replaceAll("_", " ")}</h3>
                    <span className="text-sm font-semibold text-white">{finding.score.toFixed(0)}</span>
                  </div>
                  <p className="mt-2 text-sm text-slate-300">{finding.likely_cause}</p>
                  <p className="mt-2 text-xs leading-5 text-slate-500">{finding.evidence.join(" · ")}</p>
                </article>
              ))}
            </div>
          </section>
        </div>

        <NotificationPanel />

        <footer className="py-6 text-center text-xs text-slate-600">
          Eşikler ve ısıl parametreler saha verisiyle henüz kalibre edilmemiş demo varsayımlarıdır.
        </footer>
      </div>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.025] p-3">
      <div className="text-[11px] uppercase tracking-[0.16em] text-slate-500">{label}</div>
      <div className="mt-1 text-lg font-semibold text-slate-100">{value}</div>
    </div>
  );
}
