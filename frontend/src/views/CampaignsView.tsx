import { useEffect, useState } from "react";
import { getCampaigns, getSegments, getAnalytics, type CampaignsResponse, type Segment, type Analytics } from "../lib/api";
import { SEGMENT_ACCENT, FORMAT_LABEL } from "../theme";

/**
 * Campaign performance history — the system-of-record / evidence base.
 *
 * Pitch hook: this is the marketing team's *own* historical data, and it's
 * exactly what the predicted-CTR badge is computed from. Showing it makes the
 * prediction auditable ("the model didn't invent that number — here are the 40
 * comparable campaigns it's grounded in"). It's the B-equivalent of a records
 * ledger: the before-state (data sitting unused) made visible and useful.
 */
export default function CampaignsView() {
  const [data, setData] = useState<CampaignsResponse | null>(null);
  const [segs, setSegs] = useState<Record<string, Segment>>({});
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    getCampaigns(120).then(setData);
    getSegments().then((s) => setSegs(Object.fromEntries(s.map((x) => [x.id, x]))));
    getAnalytics().then(setAnalytics);
  }, []);

  if (!data) return <div className="max-w-7xl mx-auto px-4 md:px-8 py-10 text-stone">Loading campaign history…</div>;

  const rows = filter === "all" ? data.campaigns : data.campaigns.filter((c) => c.segment_id === filter);
  const segIds = Array.from(new Set(data.campaigns.map((c) => c.segment_id)));

  return (
    <div className="max-w-7xl mx-auto px-4 md:px-8 py-8">
      <div className="mb-2">
        <h1 className="font-serif text-3xl text-ink">Campaign performance history</h1>
        <p className="text-stone mt-1 max-w-2xl">
          Your team's own past campaigns — impressions, clicks, and click-through rate. This is the
          data CreativeIQ grounds every prediction in. Today it sits unused in a spreadsheet.
        </p>
      </div>

      {/* Rollup stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5">
        <Stat label="Campaigns on record" value={String(data.stats.total_campaigns)} />
        <Stat label="Book avg CTR" value={data.stats.book_avg_ctr_pct} accent />
        <Stat label="Total impressions" value={data.stats.total_impressions.toLocaleString()} />
        <Stat label="Date range" value={data.stats.date_range} small />
      </div>

      {/* CTR heatmap — what works for whom */}
      {analytics && <Heatmap a={analytics} />}

      {/* Segment filter */}
      <div className="mt-6 flex flex-wrap gap-2">
        <FilterChip id="all" label="All segments" active={filter === "all"} onClick={() => setFilter("all")} />
        {segIds.map((id) => (
          <FilterChip
            key={id}
            id={id}
            label={segs[id]?.name || id}
            active={filter === id}
            accent={SEGMENT_ACCENT[id]}
            onClick={() => setFilter(id)}
          />
        ))}
      </div>

      {/* Table */}
      <div className="mt-4 rounded-2xl bg-panel shadow-card border border-stone/10 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-panel2 text-stone uppercase text-xs tracking-wider">
              <tr>
                <th className="px-4 py-3">Campaign</th>
                <th className="px-4 py-3">Segment</th>
                <th className="px-4 py-3">Channel · Format</th>
                <th className="px-4 py-3">Style · Tone</th>
                <th className="px-4 py-3 text-right">Impressions</th>
                <th className="px-4 py-3 text-right">CTR</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((c) => (
                <tr key={c.campaign_id} className="border-t border-line">
                  <td className="px-4 py-3">
                    <div className="font-medium text-ink">{c.product_id.replace(/-/g, " ")}</div>
                    <div className="text-xs text-stone">{c.date} · {c.campaign_id}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className="inline-block rounded-full px-2.5 py-1 text-xs font-medium text-white"
                      style={{ backgroundColor: SEGMENT_ACCENT[c.segment_id] }}
                    >
                      {segs[c.segment_id]?.name || c.segment_id}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-stone">{c.channel} · {c.format.replace(/_/g, " ")}</td>
                  <td className="px-4 py-3 text-stone">{c.image_style} · {c.copy_tone}</td>
                  <td className="px-4 py-3 text-right tabular-nums text-ink">{c.impressions.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right">
                    <span className={`font-semibold tabular-nums ${c.top_performer ? "text-teal-deep" : "text-ink"}`}>
                      {c.ctr_pct}
                    </span>
                    {c.top_performer && (
                      <span className="ml-2 text-[10px] uppercase tracking-wide text-teal-deep">▲ top</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <p className="text-xs text-stone mt-3">
        Top performers (▲) are the top-quartile CTR across the whole book — the patterns CreativeIQ
        reuses when it generates and predicts. Synthetic data.
      </p>
    </div>
  );
}

function Stat({ label, value, accent, small }: { label: string; value: string; accent?: boolean; small?: boolean }) {
  return (
    <div className="rounded-2xl bg-panel shadow-card border border-stone/10 p-4">
      <div className={`font-serif font-bold ${small ? "text-base" : "text-3xl"} ${accent ? "text-teal-deep" : "text-ink"}`}>
        {value}
      </div>
      <div className="text-xs uppercase tracking-wider text-stone mt-1">{label}</div>
    </div>
  );
}

// Segment × format CTR heatmap — the data-informed "what works for whom" view
// that the generator and predictor draw on. Cells coloured by CTR intensity.
function Heatmap({ a }: { a: Analytics }) {
  const vals: number[] = [];
  a.matrix.forEach((row) => row.cells.forEach((c) => { if (c.ctr != null) vals.push(c.ctr); }));
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const alpha = (ctr: number) => (max > min ? 0.12 + 0.78 * ((ctr - min) / (max - min)) : 0.5);

  return (
    <div className="mt-4 rounded-2xl bg-panel shadow-card border border-stone/10 p-4 md:p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-serif text-xl text-ink">What works for whom · CTR by segment × format</h2>
        {a.best_combo && (
          <span className="text-sm text-stone">
            Best combo: <span className="font-semibold text-teal-deep">{a.best_combo.segment_name} · {FORMAT_LABEL[a.best_combo.format] || a.best_combo.format} ({a.best_combo.ctr_pct})</span>
          </span>
        )}
      </div>
      <p className="text-xs text-stone mt-1">Impression-weighted CTR from {a.total_campaigns} real campaigns · book average {a.book_avg_ctr_pct}. Darker = higher.</p>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full border-separate" style={{ borderSpacing: "4px" }}>
          <thead>
            <tr>
              <th className="text-left text-xs uppercase tracking-wider text-stone font-medium px-2"> </th>
              {a.formats.map((f) => (
                <th key={f} className="text-xs uppercase tracking-wider text-stone font-medium px-2 py-1 text-center">
                  {FORMAT_LABEL[f] || f.replace(/_/g, " ")}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {a.matrix.map((row) => (
              <tr key={row.segment_id}>
                <td className="px-2 py-1 text-sm font-medium text-ink whitespace-nowrap">
                  <span className="inline-block w-2.5 h-2.5 rounded-full mr-2 align-middle" style={{ background: SEGMENT_ACCENT[row.segment_id] }} />
                  {row.segment_name}
                  <span className="text-stone text-xs"> · {row.segment_ctr_pct}</span>
                </td>
                {row.cells.map((c) => (
                  <td key={c.format} className="text-center">
                    <div
                      className="rounded-lg py-3 px-2"
                      style={{
                        background: c.ctr != null ? `rgba(63,107,107,${alpha(c.ctr)})` : "var(--panel2)",
                        color: c.ctr != null && alpha(c.ctr) > 0.55 ? "#fff" : "var(--ink)",
                      }}
                      title={`${row.segment_name} · ${c.format}: ${c.ctr_pct} (${c.n} campaigns)`}
                    >
                      <div className="text-sm font-bold tabular-nums">{c.ctr_pct}</div>
                      <div className="text-[10px] opacity-70">{c.n} camp.</div>
                    </div>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function FilterChip({ label, active, accent, onClick }: { id: string; label: string; active: boolean; accent?: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full px-4 py-2 text-sm font-medium min-h-[44px] border-2 transition-all ${
        active ? "text-white" : "bg-panel border-stone/15 text-ink hover:border-stone/40"
      }`}
      style={active ? { backgroundColor: accent || "var(--ink)", borderColor: accent || "var(--ink)" } : {}}
    >
      {label}
    </button>
  );
}
