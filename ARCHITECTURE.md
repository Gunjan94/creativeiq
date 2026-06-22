# ARCHITECTURE.md — CreativeIQ

> Deliverable (2): ~1-page architecture overview — diagram, data flow, and why these choices. Scenario B: AI-Powered Retail Ad Studio.

## System diagram

```
   ┌───────────────────────────────────────────────────────────────────┐
   │  BROWSER (showroom touchscreen)                                     │
   │  React + TypeScript + Vite + Tailwind                               │
   │  StudioView: GeneratePanel · CreativeCard · SegmentSwitcher         │
   │              PredictedCtrBadge · BeforeAfterPanel                    │
   │  CampaignsView: 160-row performance history (the evidence base)     │
   │  theme.ts: light/dark via CSS variables (default light)             │
   └───────────────┬───────────────────────────────┬───────────────────┘
                   │ HTTPS / SSE (streamed copy)    │ GET catalog/segments/campaigns
                   ▼                                ▼
   ┌───────────────────────────────────────────────────────────────────┐
   │  Amazon API Gateway (HTTP API)                                      │
   └───────────────┬───────────────────────────────┬───────────────────┘
                   ▼                                ▼
   ┌──────────────────────────┐   ┌──────────────────────────────────────┐
   │  Lambda: /generate        │   │  Lambda: /predict /segments /catalog │
   │  (Python 3.12)            │   │           /campaigns  (Python 3.12)   │
   │   1. load product+segment │   │   perf_model.py over campaign         │
   │   2. ask perf_model for   │   │   history → predicted CTR + lift +    │
   │      best style/tone/fmt  │   │   "based on N campaigns";             │
   │   3. stream copy (Claude) │   │   /campaigns serves those same rows   │
   │   4. render image (Nova)  │   │   (book CTR, top performers) →         │
   │      [preview offline]    │   │   makes the prediction auditable      │
   │   5. cache/preview fallbk │   └───────────────┬──────────────────────┘
   └───┬───────────┬───────────┘                   │
       │           │                               │
       ▼           ▼                               ▼
 ┌──────────┐  ┌──────────────────────────┐   ┌─────────────────────────────┐
 │ Amazon   │  │ Amazon Bedrock            │   │ Synthetic data (bundled JSON │
 │   S3     │  │  • Claude Sonnet 4.6      │   │ + S3): catalog, segments,    │
 │ creatives│  │    (copy, streamed)       │   │ campaign_history, hero_set    │
 │ + hero   │  │  • Nova Canvas (image —   │   └─────────────────────────────┘
 │   set    │  │    NOT RUN; preview only) │
 │ +preview │  └──────────────────────────┘
 └──────────┘
            ── all provisioned by AWS CDK (one-command deploy, serverless, ~$0 idle) ──
```

## Data flow (request → response)

1. The panel picks a **product** and **segment** in StudioView and hits Generate. The browser calls `POST /generate`.
2. The `/generate` Lambda loads the product (catalog) and segment profile, then asks `perf_model.py` which **image style, copy tone, and format** historically perform best **for that segment** — so the creative is data-informed, not generic.
3. The Lambda builds a **brand-token-constrained, segment-conditioned** prompt and **streams copy from Claude (Sonnet 4.6)** back over SSE — copy appears within ~1s. Concurrently it attempts an **on-brand image**: with `USE_BEDROCK=1` + creds it calls **Nova Canvas** and stores the result in **S3**; offline (the state in this environment — creds expired) it serves a pre-composed on-brand **SVG preview**, not a live render. The CreativeCard badge labels which (`live Bedrock` vs `on-brand preview`).
4. In parallel the browser calls `POST /predict`, which runs the transparent feature model over `campaign_history.json` (segment × format × style × tone → CTR) and returns a **predicted CTR, lift vs the segment average, and the number of comparable campaigns** — the grounding for the on-screen badge.
5. The browser renders the streamed copy, fades in the image (S3 render or preview), shows the format tag and the **predicted-CTR badge**, and updates the **before/after panel** with the real elapsed time. Switching the segment re-fires steps 2–5 for the same product, so copy, format, and prediction visibly re-render.
6. If image gen is slow or Bedrock errors, `/generate` serves the **pre-generated hero-set** creative (S3 or local) — the demo path never breaks.
7. The **Campaigns** view calls `GET /campaigns`, which returns recent rows from `campaign_history.json` plus book-level rollups (160 campaigns, book avg CTR ~2.68%, top-quartile performers flagged). These are the **same rows `/predict` is computed from** — exposing them makes the predicted-CTR badge auditable rather than asserted. `theme.ts` applies the active light/dark palette as CSS variables that Tailwind and the page background read.

## Why these choices

- **Serverless (Lambda + API Gateway + CDK):** one-command deploy, ~$0 idle, nothing to babysit during a 5-day build — time goes to the demo path, not ops. CDK gives the judges a clean clone-to-run.
- **Amazon Bedrock for both copy and image:** one managed AI surface, one IAM permission (`InvokeModel`), no key management. **Claude Sonnet 4.6** is the speed/quality sweet spot for short ad copy and streams smoothly (the first-10-seconds impression); **Nova Canvas** is AWS-native, fast, and brand-controllable via prompt. State the reasoning: text and image are *different* model families combined thoughtfully, which is exactly the "AI + cloud + data, orchestration over service count" the brief rewards.
- **Transparent perf model (not an LLM) for prediction:** the prediction must be *grounded in the historical dataset*, defensible, and stable when judges change inputs — a feature-based aggregate over real rows does that and explains itself ("+24% vs segment avg, 18 campaigns"). An LLM guess would fail the "not invented" bar.
- **S3 assets + pre-generated hero set:** image-gen latency/quality is the #1 demo risk; caching keyed by product×segment plus stream-text-while-image-renders turns that risk into a non-event.
- **Synthetic data only:** no real customer data, no secrets in the repo — and we engineer clear, defensible patterns into the history so the prediction visibly reflects the data.
- **Region:** Singapore (`ap-southeast-1`) for the APJ demo; fall back to `us-east-1` if Bedrock image-model access is gated (verified Day 1).
