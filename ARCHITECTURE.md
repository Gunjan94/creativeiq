# CreativeIQ — Architecture Overview

**AI retail ad studio for a SE-Asia fashion retailer ("Lumen & Coast").** Two audiences: the **CMO**
(speed-to-trend, on-brand creative) and the **CEO/CFO** (cost + media ROI). The CTR prediction is a real,
transparent model over the retailer's own campaign history; image + copy are AI-generated; the analytics
and money views make it all auditable.

## Diagram
```
┌──────────────────────────────────────────────────────────────────────────────┐
│  BROWSER  (React 18 + TypeScript + Vite + Tailwind)                             │
│  ┌────────────────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────────┐  │
│  │ Studio (HERO)          │ │ Campaigns    │ │ Segments     │ │ Catalog     │  │
│  │  • product × segment   │ │  • CTR       │ │              │ │             │  │
│  │    → Generate          │ │    heatmap   │ │              │ │             │  │
│  │  • AI image + streamed │ │   (seg×fmt)  │ │              │ │             │  │
│  │    copy + CTR badge    │ │  • 160-row   │ │              │ │             │  │
│  │  • "Why this number?"  │ │    history   │ │              │ │             │  │
│  │    drill-down          │ │              │ │              │ │             │  │
│  │  • Before/After + ≈$1.2M│ └──────┬───────┘ └──────────────┘ └─────────────┘  │
│  └──────────┬─────────────┘        │                                            │
└─────────────┼──────────────────────┼────────────────────────────────────────────┘
   /generate (SSE)   /predict     /analytics   /comparable    /campaigns /segments /catalog
        │               │             │            │
        ▼               ▼             ▼            ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  AWS Lambda  (Python 3.12, FastAPI via Mangum, Function URL)  — app.py          │
│   ┌──────────────────┐  ┌───────────────────┐  ┌───────────────────────────┐   │
│   │ core/perf_model  │  │ core/imagegen     │  │ handlers/generate + copy   │   │
│   │  • CTR predict   │  │  • keyless text-  │  │  • streams copy (LLM/Claude)│   │
│   │    over 160      │  │    to-image (Flux)│  │  • orchestrates image+copy │   │
│   │    campaigns     │  │  • DIRECT mode on │  │ handlers/analytics         │   │
│   │  • seg×fmt×style │  │    Lambda (returns│  │  • seg×fmt CTR matrix      │   │
│   │    ×tone factors │  │    image URL,     │  │  • comparable campaigns    │   │
│   │  • grounded, not │  │    no disk write) │  │    (the prediction's       │   │
│   │    invented      │  └─────────┬─────────┘  │    grounding, auditable)   │   │
│   └───────┬──────────┘            │            └─────────────┬──────────────┘   │
│           ▼                       ▼                          ▼                  │
│   data/campaign_history.json   image.pollinations.ai    Amazon Bedrock (opt):   │
│   (160 synthetic)   data/catalog, segments, generated/  Claude copy + Nova Canvas│
│                     (served at /data)                   image when USE_BEDROCK=1 │
└──────────────────────────────────────────────────────────────────────────────┘
   Region ap-southeast-1.  Frontend → private S3 + CloudFront; /data images via the Function URL
   (frontend built with VITE_ASSET_BASE = the Function URL).  CDK (infra/cdk/), LIVE. ~$0 idle.
```

## Data flow
1. **Studio → Generate** (`POST /generate`, SSE): `perf_model.best_features_for_segment` mines the
   historically best format/style/tone for the segment → `copywriter`/Claude streams the copy →
   `imagegen` produces a **net-new AI image** (keyless Flux text-to-image; cached hero combos instant) →
   `perf_model.predict` returns a **grounded CTR** (segment avg × format/style/tone factors, clamped),
   with `based_on_n_campaigns`. Switching the segment re-runs all three live.
2. **"Why this number?"** → `GET /comparable?segment_id&format&image_style&copy_tone` returns the real
   campaigns the prediction is computed from (auditable, not invented) + their avg CTR.
3. **Campaigns** → `GET /analytics` returns the **segment × format CTR matrix** (heatmap) + book avg
   2.68% + best combo (Gen-Z social 3.51%); `GET /campaigns` the 160-row history.
4. **Before/After** → per-campaign (3–5 days → seconds) + an annual roll-up (≈$1.2M/yr agency → ≈$0).
5. **Lambda image handling (DIRECT mode):** a cache-miss returns the **keyless image URL** for the browser
   to load (no writes to the read-only Lambda FS); the 12 bundled hero combos serve from `/data`.
6. **Degradation:** offline copy template; cached hero set; the prediction is real local compute either way.

## Why these choices
- **Transparent CTR model, not an AI black box** — the number is grounded in real history and *auditable*
  via the drill-down, so a media budget can sit behind it. This is the load-bearing "it's real" proof.
- **Keyless image gen by default, Bedrock Nova Canvas optional** — genuinely AI-generated images with zero
  AWS setup; `USE_BEDROCK=1` swaps in Nova Canvas + Claude.
- **DIRECT image mode on Lambda** — avoids writing to the read-only task FS; bundled hero combos stay instant.
- **Two-audience IA** — CMO (create/speed) vs CEO/CFO (annual money) clearly separated.
- **Serverless Lambda + Mangum + CDK** — already live; ~$0 idle. Synthetic data only.
