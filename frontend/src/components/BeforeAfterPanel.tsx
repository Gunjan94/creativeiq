// Quantified before/after: traditional agency creative vs CreativeIQ.
// Figures are grounded in 2025-26 industry benchmarks (see README · Market context):
//   · Fashion studio shoot: US$1,500–7,500/day, 4–15 usable assets (Creatify, Sovran.ai)
//   · Testing 100 creative variations: US$20,000–50,000 (Creatify case study)
//   · Agency revision cycle: 3–5 business days each (thefword.ai)
//   · AI workflows cut development time ~70%, sampling cost 40–50% (McKinsey / Style3D)
export default function BeforeAfterPanel({ elapsedMs }: { elapsedMs: number | null }) {
  const secs = elapsedMs != null ? (elapsedMs / 1000).toFixed(1) : null;

  // At-volume annual roll-up (conservative, benchmark-grounded).
  //   ~50 campaign concepts / month -> ~600 / year.
  //   Agency cost per *concept* ~US$2,000 (a fraction of a $1.5–7.5k shoot day).
  const CONCEPTS_PER_YEAR = 600;
  const AGENCY_PER_CONCEPT = 2000;
  const annualAgency = CONCEPTS_PER_YEAR * AGENCY_PER_CONCEPT; // ~US$1.2M
  const fmtM = (n: number) => `$${(n / 1_000_000).toFixed(1)}M`;

  return (
    <div>
      <div className="text-xs uppercase tracking-widest text-stone mb-1">The business case</div>
      <div className="text-xs text-stone/80 mb-3">For the marketing team · speed &amp; reach per campaign</div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* BEFORE */}
        <div className="rounded-2xl border-2 border-stone/20 bg-panel/40 p-5">
          <div className="text-xs uppercase tracking-widest text-stone">Today · Agency + studio shoot</div>
          <div className="text-3xl font-serif font-bold text-stone mt-1">3–5 days</div>
          <div className="text-sm text-stone/90">per creative concept · per revision cycle</div>
          <ul className="mt-3 text-sm text-stone/90 space-y-1.5">
            <li className="flex justify-between"><span>Studio shoot (1 day)</span><span className="font-semibold">$1,500–7,500</span></li>
            <li className="flex justify-between"><span>Usable assets / shoot</span><span className="font-semibold">4–15</span></li>
            <li className="flex justify-between"><span>Test 100 variations</span><span className="font-semibold">$20k–50k</span></li>
            <li className="flex justify-between"><span>Data-informed?</span><span className="font-semibold">No</span></li>
          </ul>
        </div>

        {/* AFTER */}
        <div className="rounded-2xl border-2 border-teal bg-teal-deep text-offwhite p-5 shadow-card">
          <div className="text-xs uppercase tracking-widest text-offwhite/70">With CreativeIQ</div>
          <div className="text-3xl font-serif font-bold mt-1">{secs ? `${secs}s` : "under a minute"}</div>
          <div className="text-sm text-offwhite/80">per on-brand, segment-targeted concept</div>
          <ul className="mt-3 text-sm text-offwhite/90 space-y-1.5">
            <li className="flex justify-between"><span>Marginal cost / variant</span><span className="font-semibold">~$0</span></li>
            <li className="flex justify-between"><span>Variants / afternoon</span><span className="font-semibold">100s</span></li>
            <li className="flex justify-between"><span>CTR predicted from</span><span className="font-semibold">your own data</span></li>
            <li className="flex justify-between"><span>Retarget a segment</span><span className="font-semibold">instant</span></li>
          </ul>
          {secs && <div className="mt-3 text-xs text-offwhite/70">↑ actual time for the last generation</div>}
        </div>
      </div>

      {/* Annual roll-up — the CEO/CFO money view */}
      <div className="text-xs text-stone/80 mt-6 mb-2">For the CEO &amp; CFO · at your volume (≈600 concepts/yr)</div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <RollupStat label="Agency spend / year" value={`≈ ${fmtM(annualAgency)}`} note="~600 concepts × ~$2k each" />
        <RollupStat label="With CreativeIQ" value="≈ $0" note="marginal cost per concept" />
        <RollupStat label="Saved / year" value={`≈ ${fmtM(annualAgency)}`} note="redeploy to media + more tests" accent />
      </div>
      <p className="text-sm text-ink/80 mt-3">
        And throughput is no longer capped by an agency queue — every trend window (11.11, 12.12, Hari Raya,
        year-end) gets an on-brand, data-tuned campaign on time, instead of arriving days late.
      </p>

      <p className="text-[11px] text-stone/70 mt-3">
        Benchmarks: fashion studio shoot $1.5–7.5k/day for 4–15 assets; 100-variation test $20–50k;
        agency revisions 3–5 days each. AI workflows cut development time ~70% (McKinsey, Creatify, Style3D, 2025–26).
        Annual figures are conservative, illustrative estimates on ~50 concepts/month.
      </p>
    </div>
  );
}

function RollupStat({ label, value, note, accent }: { label: string; value: string; note: string; accent?: boolean }) {
  return (
    <div className={`rounded-2xl border-2 p-4 ${accent ? "border-teal bg-teal/10" : "border-stone/20 bg-panel/40"}`}>
      <div className="text-xs uppercase tracking-widest text-stone">{label}</div>
      <div className={`font-serif font-bold text-3xl mt-1 ${accent ? "text-teal-deep" : "text-ink"}`}>{value}</div>
      <div className="text-xs text-stone/80 mt-0.5">{note}</div>
    </div>
  );
}
