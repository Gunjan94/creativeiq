import { useState } from "react";
import { getComparable, type Prediction, type Comparable } from "../lib/api";

// Big predicted-CTR % + grounding, with a "why this number?" drill-down that
// shows the per-factor multipliers and the real comparable campaigns the
// prediction is computed from. Grounded in campaign_history.json — never invented.
export default function PredictedCtrBadge({ pred, segmentId }: { pred: Prediction | null; segmentId?: string | null }) {
  const [open, setOpen] = useState(false);
  const [comp, setComp] = useState<Comparable | null>(null);
  const [loading, setLoading] = useState(false);

  if (!pred) {
    return (
      <div className="rounded-2xl bg-panel/60 border border-stone/20 p-5 text-stone">
        <div className="text-sm uppercase tracking-wider">Predicted CTR</div>
        <div className="text-3xl font-serif mt-1">—</div>
      </div>
    );
  }
  const liftNum = parseInt(pred.lift_vs_segment_avg_pct.replace(/[+%]/g, ""), 10);
  const positive = liftNum >= 0;
  const strong = liftNum >= 20;
  const ring = strong ? "ring-teal" : positive ? "ring-teal/60" : "ring-terracotta";
  const liftColor = positive ? "text-teal-deep" : "text-terracotta";
  const confColor =
    pred.confidence === "high" ? "bg-teal text-white"
    : pred.confidence === "medium" ? "bg-stone text-white"
    : "bg-terracotta/80 text-white";

  const f = pred.factors || {};

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (next && !comp && segmentId) {
      setLoading(true);
      try {
        const c = await getComparable({
          segment_id: segmentId,
          format: f.format?.value,
          image_style: f.image_style?.value,
          copy_tone: f.copy_tone?.value,
        });
        setComp(c);
      } finally {
        setLoading(false);
      }
    }
  }

  const FACTOR_LABEL: Record<string, string> = {
    format: "Format",
    image_style: "Image style",
    copy_tone: "Copy tone",
  };

  return (
    <div className={`rounded-2xl bg-panel shadow-card p-5 ring-2 ${ring}`} key={pred.predicted_ctr_pct}>
      <div className="flex items-center justify-between">
        <div className="text-xs uppercase tracking-widest text-stone">Predicted CTR</div>
        <span className={`text-[10px] uppercase tracking-wider px-2 py-1 rounded-full ${confColor}`}>
          {pred.confidence} confidence
        </span>
      </div>
      <div className="flex items-end gap-3 mt-1">
        <div className="text-5xl font-serif font-bold text-ink leading-none">{pred.predicted_ctr_pct}</div>
        <div className={`text-lg font-semibold ${liftColor} mb-1`}>
          {pred.lift_vs_segment_avg_pct} <span className="text-stone text-sm font-normal">vs segment avg</span>
        </div>
      </div>
      <div className="mt-2 text-sm text-stone">
        Grounded in <span className="font-semibold text-ink">{pred.based_on_n_campaigns}</span> comparable historical campaigns ·
        segment avg <span className="font-semibold text-ink">{pred.segment_avg_ctr_pct}</span>
      </div>

      <button
        onClick={toggle}
        className="mt-3 text-sm font-semibold text-teal-deep underline underline-offset-2"
      >
        {open ? "Hide the math" : "Why this number?"}
      </button>

      {open && (
        <div className="mt-3 rounded-xl bg-panel2 border border-line p-4">
          <div className="text-xs uppercase tracking-wider text-stone mb-2">
            Segment average {pred.segment_avg_ctr_pct}, adjusted by what works for this segment:
          </div>
          <div className="space-y-1.5">
            {Object.entries(f).map(([k, v]) => {
              const up = v.factor >= 1;
              return (
                <div key={k} className="flex items-center justify-between text-sm">
                  <span className="text-ink">
                    {FACTOR_LABEL[k] || k}: <span className="font-medium">{String(v.value).replace(/_/g, " ")}</span>
                    <span className="text-stone text-xs"> · {v.n} campaigns</span>
                  </span>
                  <span className={`tabular-nums font-semibold ${up ? "text-teal-deep" : "text-terracotta"}`}>
                    ×{v.factor.toFixed(2)}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="mt-3 border-t border-line pt-3">
            <div className="text-xs uppercase tracking-wider text-stone mb-2">
              {comp ? `${comp.matched_count} closest comparable campaigns` : "Comparable campaigns"}
              {comp && <span className="normal-case tracking-normal"> · avg {comp.avg_ctr_pct}</span>}
            </div>
            {loading && <div className="text-sm text-stone">Loading comparable campaigns…</div>}
            {comp && (
              <div className="space-y-1 max-h-44 overflow-auto pr-1">
                {comp.campaigns.map((c) => (
                  <div key={c.campaign_id} className="flex items-center justify-between text-xs">
                    <span className="text-ink capitalize truncate">
                      {c.product_id.replace(/-/g, " ")}
                      <span className="text-stone"> · {c.format.replace(/_/g, " ")}</span>
                    </span>
                    <span className="tabular-nums font-semibold text-ink shrink-0">{c.ctr_pct}</span>
                  </div>
                ))}
              </div>
            )}
            {!segmentId && !loading && (
              <div className="text-sm text-stone">Generate a creative to load the comparable campaigns.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
