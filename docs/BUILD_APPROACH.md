> **Current-state addendum (2026-06-22).** This build write-up predates the 2026-06-22 upgrade. Authoritative
> current docs: **README.md**, **ARCHITECTURE.md**, **DEMO_SCRIPT.md**. What changed: **image generation is now
> genuinely live** (keyless text-to-image — no longer a "preview"); a **CTR transparency drill-down** (`GET
> /comparable`); a **segment×format CTR heatmap** (`GET /analytics`); an **annual money roll-up** (≈$1.2M/yr);
> **two-audience** framing; and a full AWS deploy path (Mangum Lambda + CDK). **Deployed & live:**
> https://d33y5855vpqrlk.cloudfront.net.

---

# BUILD_APPROACH.md — CreativeIQ

> Deliverable (3): build approach & considerations (1–2 pages). Pre-filled where determinable; `[fill after building]` marks spots needing real results. Scenario B: AI-Powered Retail Ad Studio.

## How we approached it

We started from the hero moment, not the feature list. The brief is graded like a senior-bar hire — the default is no-hire and the demo path has to overwhelm it. So we picked one loop that, if it lands at a 5, wins on its own: **pick a product and a segment, watch an on-brand creative generate with a grounded CTR prediction, then switch the segment and watch everything re-render.** Every build decision was judged against "does this make that 90-second loop unbreakable and beautiful?" Everything off that path (analytics drill-downs, export, batch generation) was explicitly deprioritized — one thing at a 5, not three at a 3.

We sequenced to hit a hard gate each day: Day 1, a button that returns real Claude-generated copy; Day 2, a live image plus the cached fallback that de-risks demo day; Day 3, segment-aware generation and the grounded prediction wired into the UI; Day 4, the before/after panel, polish, and one-command deploy verified from a fresh clone; Day 5, write-ups, recording, and buffer. The riskiest item — Bedrock image-model access in the Singapore region — was verified on Day 1 with a throwaway script, so we never discovered a blocker late.

## Production-realism iteration

After the hero loop landed, a second pass made the prototype read like a product a CMO would actually trust — not a tech demo — without touching the core loop:

- **Light/dark theme toggle (default light).** A single `theme.ts` owns the palette and writes it onto `<html>` as CSS variables (hex + `-rgb` channels) that `tailwind.config.js` and `index.css` consume, so every surface follows the active mode. We added semantic tokens (`panel` / `panel2` / `line`) and swapped literal `bg-white` surfaces to `bg-panel` so cards adapt to dark; per-segment accents are a theme-aware Proxy. The warm "Lumen & Coast" brand palette is preserved in light; dark is a warm-charcoal variant. Demos record in light.
- **A Campaigns evidence-base view.** The biggest credibility lever was making the prediction *auditable*. A new `CampaignsView` (backed by `GET /campaigns`) shows the retailer's own 160-campaign performance history — real CTR per row, book-average CTR, top-quartile performers flagged, segment filter — i.e. the exact rows the predicted-CTR badge is computed from. The pitch beat: "the model didn't invent 4.8% — here are the 40 comparable campaigns it stands on." It's the before-state (data sitting unused) made visible and useful.
- **Honest image badge.** The CreativeCard source badge changed from "cached hero" to **"on-brand preview"** (and "live Bedrock" only when live). Offline images are previews, not live Nova Canvas renders, and the UI now says so plainly.

`DEMO_SCRIPT.md` was rewritten as a CEO/CMO pitch (problem → stakes → live proof → business case → pilot ask) with an explicit honesty note about image generation.

## Technology chosen + why

- **React + TypeScript + Vite + Tailwind (frontend):** fast iteration, and Tailwind let us hit a showroom-grade, touch-sized look without a design system. The first 10 seconds set the impression, so the hero screen got disproportionate attention.
- **Python on AWS Lambda + API Gateway (backend):** minimal surface, fast to write, scales to zero. Four small handlers (`/generate`, `/predict`, `/segments`, `/catalog`) — orchestration quality over service count.
- **Amazon Bedrock for AI:** Claude (`anthropic.claude-sonnet-4-6` — the Bedrock model id carries the `anthropic.` prefix) for copy, streamed token-by-token so text appears within ~1s; Amazon Nova Canvas (`amazon.nova-canvas-v1:0`) for on-brand images. One managed surface, one IAM permission, no key management. We chose Sonnet 4.6 over Opus for copy because short ad copy doesn't need Opus-tier reasoning and Sonnet keeps streaming latency low — the latency budget matters more than marginal copy quality here. Opus 4.8 (`anthropic.claude-opus-4-8`) is a drop-in if copy quality ever needs a bump.
- **Transparent feature model for prediction (not an LLM):** the prediction has to be *grounded in the historical dataset* and stable when judges change inputs. A deterministic aggregate over real campaign rows (segment × format × style × tone → CTR, with lift and sample count) is defensible on camera and explains itself.
- **S3 + a pre-generated hero set:** images live in S3; a cached hero set keyed by product×segment backs every demo-clicked combo.
- **AWS CDK:** one-command, serverless deploy; ~$0 idle; clean clone-to-run for judges.

## Tradeoffs given the time box

- **Latency is the headline tradeoff (call it out).** Image generation is the slowest step and the highest-variance one for both speed and brand consistency. Rather than chase a faster-but-worse image path, we hide latency behind UX: copy **streams in immediately** while the image renders asynchronously, and a **pre-generated, hand-checked hero set** is served if live generation is slow, errors, or comes back off-brand. The cost is that the very best on-camera combos are warm-cached — but they're still produced by the same real pipeline, and judges changing inputs still get live generation. We traded "every single generation is freshly live" for "the demo never stalls and never looks off-brand," which is the right trade for a showroom.
- **Aggregate model over trained ML:** we used an explainable feature model instead of training a CTR model. Faster to build, easier to defend, and the synthetic history is engineered with clear patterns so it looks smart. A real deployment would train on real campaigns.
- **Synthetic data with engineered patterns:** no real customer data (per the brief), and we deliberately baked defensible signal into the history so the prediction visibly reflects it.
- **Off-path features stubbed or cut:** export and analytics views are intentionally rough or absent — they're off camera and off the clone-to-run path.

## What we'd do differently with more time

- Train a real CTR model on real historical data and add confidence intervals.
- Add A/B variant generation (show 2–3 creatives per combo and let the model rank them).
- Brand-style fine-tuning / reference-image conditioning on the image model for even tighter brand consistency.
- A genuine "publish to channel" integration instead of a stub.
- Per-segment prompt libraries learned from what actually performed, closing the loop from outcomes back into prompts.

## Interesting challenges

- **Brand consistency from a general image model** — solved with brand-token-constrained prompts (palette, voice, imagery do's/don'ts) plus the cached hero set as a quality floor. In the offline build, the brand-consistency floor is enforced directly: hero creatives are composed locally from the same coastal palette + per-segment styling, so every creative is on-brand by construction. (Live Nova Canvas prompt iteration is the cloud follow-up; not exercised here — no Bedrock access.)
- **Making "the prediction is real" legible in one glance** — solved by showing lift vs the segment average and the number of comparable campaigns on the badge, so the grounding is visible, not asserted. The badge reads e.g. "4.8% · +56% vs segment avg · grounded in 40 comparable campaigns."
- **Hiding image latency without faking it** — streaming copy first + async image + cache fallback. Offline, the copy types in word-by-word over the cached text and the image fades in, so the UX is identical to the live path. Measured offline `/generate` round-trip is ~370ms (cache hit). Live p50/p90 will be dominated by Nova Canvas (~2–6s) and is the figure to capture once Bedrock access is available.
- **Bedrock region/model access** — not shipped against live Bedrock in this build: no AWS credentials were available in the build environment, so the prototype was built and verified entirely in **offline mode** (the design goal — zero-credential demo). The live code paths (Claude `converse_stream`, Nova Canvas `invoke_model` with Titan fallback) are implemented behind `USE_BEDROCK=1` and a Day-1 `verify_bedrock.py` access check; region defaults to `ap-southeast-1` with a `us-east-1` fallback documented.
- **npm registry** — the build host defaulted to an authenticated internal CodeArtifact registry with an expired token; pinned `frontend/.npmrc` to the public npm registry so the prototype installs cleanly on any machine.

## Build results (verified)

- **Frontend build passes:** `npm run build` — TypeScript strict + `vite build` succeed; the theme toggle, Campaigns view, and honest badge all compile clean.
- **Backend live (offline mode), verified by request:**
  - `GET /campaigns` → **160 campaigns** on record, **book avg CTR 2.68%**, top-quartile performers flagged, segment filter working.
  - `POST /predict` (linen-resort-shirt × Gen-Z · Instagram) → **4.8% predicted CTR, +56% vs segment avg, grounded in 40 comparable campaigns** — and those 40 are visible in the Campaigns view, so the number is auditable.
  - Switching segment re-rates live (format flips, CTR changes) — computed from data, not canned.
- **Live Bedrock NOT exercised — credentials expired in this environment.** The `USE_BEDROCK=1` paths (Claude `converse_stream`, Nova Canvas `invoke_model` with Titan fallback) are implemented but never ran here.
- **Images are on-brand previews offline, not live renders.** This is the prototype's biggest open gap: the headline feature — AI image generation — is precisely the part not running. Copy streams from Claude when live; the prediction is genuinely real either way. Frame images as "on-brand previews; live Nova Canvas renders once image-gen is wired + credentialed."
