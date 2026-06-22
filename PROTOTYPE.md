# PROTOTYPE.md — CreativeIQ (Scenario B: AI-Powered Retail Ad Studio)

> The spec. What we're building, why it wins, and exactly which features carry the demo.

---

## One-line pitch

**CreativeIQ compresses a mid-sized fashion retailer's 3–5 day agency creative cycle into under a minute: pick a product and a target segment, and watch an on-brand ad — image + copy + format — generate live, with a predicted-CTR badge grounded in the retailer's own historical campaign data.**

---

## Customer problem (from the brief)

A mid-sized South-East-Asia fashion retailer runs **40–60 ad campaigns/month** across social, display, and email. Their creative production is entirely manual:

- A 5-person marketing team writes a brief and hands it to a design agency.
- They wait **3–5 days** for assets, then review, revise, and finally publish.
- They **frequently miss trend windows** — by the time the creative lands, the moment has passed.
- Creative decisions are **not data-informed**. They have three valuable datasets — historical campaign performance, a product catalog (images + descriptions), and customer segment profiles — but **none of it feeds creative production**. They don't know which images, copy styles, or formats perform best for which segments.

The gap: rich performance data sitting idle while creative is produced on instinct and a slow external vendor.

---

## Concept + flow — "CreativeIQ"

A showroom web app with one core loop:

```
  pick a PRODUCT  ──►  pick a SEGMENT  ──►  [Generate]
                                              │
                                              ▼
              ┌─────────────────────────────────────────────┐
              │  • Copy streams in (Claude on Bedrock)        │
              │  • On-brand image renders (Nova Canvas)       │
              │  • Predicted-CTR badge appears                │
              │    (perf model over historical dataset)       │
              │  • Recommended format (social / display /     │
              │    email) chosen per segment                  │
              └─────────────────────────────────────────────┘
                                              │
              switch SEGMENT ───► copy + format + prediction
                                  visibly re-render to match
```

A persistent **before/after panel** frames every generation: *"Agency: 3–5 days · CreativeIQ: under a minute."*

Alongside the Studio loop, a **Campaigns** view exposes the historical performance log — the retailer's own 160 past campaigns — as a browsable, filterable records table. It's the *system of record*: the data the prediction is grounded in, made visible. The whole UI carries a **light/dark theme toggle** (default light; demos record in light).

### Campaign history — the evidence base

The single most defensible thing in the prototype is that the **prediction is grounded, not invented** — and the Campaigns view is what makes that *auditable*. It serves the exact rows `perf_model.py` reads (segment × format × style × tone → CTR), shows the **book-average CTR (~2.68%)**, and flags **top-quartile performers**, with a per-segment filter. The pitch hook: *"the model didn't invent 4.8% — here are the 40 comparable campaigns it's computed from."* It's the B-equivalent of a records ledger: the before-state (rich data sitting unused in a spreadsheet) turned visible and useful.

The executive read-through of all this — problem → stakes → live proof → business case → pilot ask — is in **`DEMO_SCRIPT.md`**, framed as a CEO/CMO pitch.

---

## Hero moment — what a 5 looks like

This is the single take that has to land on camera:

1. The presenter picks **"Linen Resort Shirt"** and segment **"Gen-Z · Instagram"**, hits Generate.
2. In **seconds**, an on-brand square ad renders — bright, lifestyle-led image + punchy short caption + emoji-friendly tone — with a **predicted CTR badge (e.g. 4.1%)** that is *read off the historical dataset*, not invented.
3. The presenter switches the segment to **"Millennials · Email"**. Without re-picking the product, the **copy rewrites** (longer, benefit-led, subject-line + preheader), the **format flips** to a wide email hero, and the **predicted CTR updates** (e.g. 2.8%) — all visibly, live.
4. The before/after panel reads: this just replaced a 3–5 day agency round trip, on-brand and data-informed, in under a minute.

If a judge changes the product or segment and hits Generate, it produces a *different, coherent* result every time. That's the test they will run, and it passes.

---

## "Real backend" proof

Judges will change inputs live and try to break it. Hardcoded responses and static UIs explicitly **do not count**. Our proof of a real backend:

| Claim | How it's provably real |
|---|---|
| **Real generation** | `/generate` streams Claude (Sonnet 4.6) copy token-by-token when `USE_BEDROCK=1` + creds. New product×segment → new copy. **Image is the gap:** live Amazon Nova Canvas image generation is wired but **not running** in this environment (creds expired) — offline serves on-brand SVG **previews**, not live renders. Don't claim live image generation works. |
| **Changeable inputs drive output** | Copy, format, and prediction are all conditioned on the chosen segment's profile. Switching segment re-renders all three live. No lookup table. (The preview image swaps too, but it's a preview, not a fresh AI render.) |
| **Prediction is grounded, not invented** | `/predict` runs a transparent feature-based model over the historical campaign dataset (segment × format × style → CTR), not an LLM guess. The badge shows the comparable historical sample it's drawn from — and the **Campaigns** view (`/campaigns`) exposes those exact rows so the number is auditable. |
| **Data-informed creative** | The generation prompt is fed the top-performing image style / copy tone / format *for that segment* mined from the same historical data — so the creative itself reflects the data. |

---

## Demo narrative

> "Today, this retailer's 5-person marketing team writes a brief, sends it to an agency, and waits 3 to 5 days for creative — and by the time it's back, the trend window has often closed. Meanwhile they're sitting on years of campaign performance data, a full product catalog, and detailed customer segments — none of which touches the creative.
>
> Watch us produce a data-informed, on-brand campaign for a specific segment in under a minute. We pick a product. We pick 'Gen-Z on Instagram'. CreativeIQ generates the image, writes the copy, picks the format — and tells us it'll likely hit a 4.1% click-through, because it learned that from their own data.
>
> Now watch the same product retarget 'Millennials on Email' — the copy, the format, and the prediction all change to match. Three-to-five days, gone."

---

## Feature → scored-criteria map

The five scored criteria (from the brief): **(1)** working prototype w/ real backend, **(2)** technology integration, **(3)** UI/UX polish, **(4)** business impact clarity, **(5)** executive presence. Demo-path features must be a **5**; off-path features are allowed rough edges.

| Feature | Primary criterion served | On demo path? (must be a 5) |
|---|---|---|
| `/generate` real Bedrock image + streamed copy | 1 Working backend · 2 Tech integration | **YES — 5** |
| Live segment switch re-renders copy + format + prediction | 1 Working backend · 4 Impact | **YES — 5** |
| `/predict` perf model over historical dataset → CTR badge | 1 Working backend · 2 Tech integration · 4 Impact | **YES — 5** |
| Predicted-CTR badge with "based on N comparable campaigns" | 4 Business impact clarity | **YES — 5** |
| Before/after panel (3–5 day agency vs <1 min) on screen | 4 Business impact clarity · 5 Exec presence | **YES — 5** |
| First-10-seconds hero screen (showroom-grade, touch-sized) | 3 UI/UX polish · 5 Exec presence | **YES — 5** |
| Streaming copy animation while image renders | 3 UI/UX polish | **YES — 5** |
| Pre-generated cached hero set (graceful degradation) | 1 Working backend (reliability) | **YES — backs the demo path** |
| `/segments` and `/catalog` browsing views | 2 Tech integration | On path (navigable, coherent) |
| **Campaigns** evidence-base view (`/campaigns`) — 160-row history, book CTR, top performers | 1 Working backend · 4 Impact (the prediction's grounding, made auditable) | **ON path — opens the live demo** |
| Export / "send to channel" button | — (showroom flourish) | **OFF path — can be a stub** |
| Multi-product batch generation | — | **OFF path — out of scope** |

**Stop rule (from the brief):** done = the demo path is a 5 **and** the deadline is met. If behind, cut the off-path features to zero and keep the hero loop at a 5 — one thing at a 5, not three at a 3.
