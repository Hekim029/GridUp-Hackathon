import { useEffect, useState } from "react";
import type { NotificationRecord } from "../types";

const channelLabels: Record<string, string> = {
  sms_simulated: "SMS simülasyonu",
  whatsapp_simulated: "WhatsApp simülasyonu",
};

export function NotificationPanel() {
  const [notifications, setNotifications] = useState<NotificationRecord[]>([]);

  useEffect(() => {
    let active = true;

    async function refresh() {
      try {
        const response = await fetch("/api/v1/notifications?limit=8");
        if (!response.ok) return;
        const incoming = (await response.json()) as NotificationRecord[];
        if (active) setNotifications(incoming);
      } catch {
        // WebSocket connection indicator already exposes backend availability.
      }
    }

    void refresh();
    const timer = window.setInterval(refresh, 2000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  return (
    <section className="card mt-5">
      <div className="mb-4 flex items-end justify-between gap-3">
        <div>
          <p className="eyebrow">Alarm ve acil bildirim</p>
          <h2 className="text-lg font-semibold text-white">Yerel bildirim outbox</h2>
        </div>
        <span className="text-xs text-slate-500">Gerçek alıcıya gönderim yapılmaz</span>
      </div>
      {notifications.length === 0 ? (
        <p className="rounded-xl border border-white/10 bg-white/[0.025] p-4 text-sm text-slate-400">
          Uyarı veya kritik seviye yükselmesi bekleniyor.
        </p>
      ) : (
        <div className="grid gap-3 lg:grid-cols-2">
          {notifications.map((notification) => (
            <article
              key={notification.id}
              className="rounded-xl border border-rose-400/25 bg-rose-950/20 p-4"
            >
              <div className="flex items-center justify-between gap-3 text-xs">
                <span className="font-semibold uppercase tracking-[0.12em] text-rose-200">
                  {channelLabels[notification.channel] ?? notification.channel}
                </span>
                <span className="text-slate-500">
                  {new Date(notification.created_at).toLocaleTimeString("tr-TR")}
                </span>
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-300">{notification.message}</p>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
