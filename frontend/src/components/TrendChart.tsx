import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { TrendPoint } from "../types";

export function TrendChart({ data }: { data: TrendPoint[] }) {
  return (
    <section className="card h-[320px]">
      <div className="mb-4">
        <p className="eyebrow">Zaman serisi</p>
        <h2 className="text-lg font-semibold text-white">L1 akım ve termal iz</h2>
      </div>
      <ResponsiveContainer width="100%" height="82%">
        <LineChart data={data}>
          <CartesianGrid stroke="#1e293b" strokeDasharray="4 4" />
          <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10 }} minTickGap={24} />
          <YAxis yAxisId="current" stroke="#60a5fa" tick={{ fontSize: 10 }} />
          <YAxis yAxisId="temperature" orientation="right" stroke="#fb7185" tick={{ fontSize: 10 }} />
          <Tooltip contentStyle={{ background: "#07111f", border: "1px solid #334155", borderRadius: 10 }} />
          <Legend />
          <Line yAxisId="current" type="monotone" dataKey="current" name="Akım (A)" stroke="#60a5fa" dot={false} strokeWidth={2} />
          <Line yAxisId="temperature" type="monotone" dataKey="temperature" name="Bara (°C)" stroke="#fb7185" dot={false} strokeWidth={2} />
          <Line yAxisId="temperature" type="monotone" dataKey="expected" name="Beklenen (°C)" stroke="#94a3b8" dot={false} strokeDasharray="5 5" />
        </LineChart>
      </ResponsiveContainer>
    </section>
  );
}

