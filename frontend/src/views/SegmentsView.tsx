import { useEffect, useState } from "react";
import { getSegments, type Segment } from "../lib/api";
import { SEGMENT_ACCENT, FORMAT_LABEL } from "../theme";
import {
  BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, Tooltip,
} from "recharts";

export default function SegmentsView() {
  const [segments, setSegments] = useState<Segment[]>([]);
  useEffect(() => { getSegments().then(setSegments); }, []);

  const chartData = segments.map((s) => ({
    name: s.name, ctr: +(s.avg_ctr * 100).toFixed(2), id: s.id,
  }));

  return (
    <div className="max-w-7xl mx-auto px-4 md:px-8 py-8">
      <h2 className="font-serif text-3xl text-ink mb-1">Customer Segments</h2>
      <p className="text-stone mb-6">Profiles + historical performance from the campaign dataset.</p>

      <div className="rounded-2xl bg-panel shadow-card p-5 mb-6">
        <div className="text-xs uppercase tracking-widest text-stone mb-3">Average CTR by segment (historical)</div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chartData}>
            <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#9A9387" }} />
            <YAxis unit="%" tick={{ fontSize: 12, fill: "#9A9387" }} />
            <Tooltip formatter={(v) => `${v}%`} />
            <Bar dataKey="ctr" radius={[8, 8, 0, 0]}>
              {chartData.map((d) => <Cell key={d.id} fill={SEGMENT_ACCENT[d.id] || "#5C8A8A"} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {segments.map((s) => (
          <div key={s.id} className="rounded-2xl bg-panel shadow-card p-5 border-l-4" style={{ borderColor: SEGMENT_ACCENT[s.id] }}>
            <div className="flex items-baseline justify-between">
              <div className="font-serif text-xl text-ink">{s.name}</div>
              <div className="text-sm text-stone">{s.channel} · {s.age_band}</div>
            </div>
            <p className="text-sm text-stone mt-1">{s.blurb}</p>
            <div className="mt-3 flex gap-4 text-sm">
              <div><span className="text-stone">Avg CTR </span><span className="font-semibold text-ink">{s.avg_ctr_pct}</span></div>
              <div><span className="text-stone">Top format </span><span className="font-semibold text-ink">{FORMAT_LABEL[s.top_format] || s.top_format}</span></div>
              <div><span className="text-stone">Campaigns </span><span className="font-semibold text-ink">{s.n_campaigns}</span></div>
            </div>
            <div className="mt-2 text-xs text-stone">Tone: {s.tone}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
