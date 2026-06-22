# BUILDER.md — CreativeIQ Build Playbook

> The mechanical guide. Repo layout, exact stack, day-by-day with gates, endpoint specs, the perf model, the generation spec, caching/fallback, synthetic data, frontend breakdown, deploy, and Definition-of-Done. Follow it top to bottom.

---

## 1. Repo layout

```
scenario-b-retail-ad-studio/
├── README.md                # setup + run (see README.md deliverable)
├── frontend/                # React + TS + Vite
│   ├── src/
│   │   ├── App.tsx
│   │   ├── views/
│   │   │   ├── StudioView.tsx        # the hero: generate panel + segment switcher
│   │   │   ├── CatalogView.tsx       # browse products
│   │   │   └── SegmentsView.tsx      # browse segments
│   │   ├── components/
│   │   │   ├── GeneratePanel.tsx     # product + segment pickers + Generate button
│   │   │   ├── CreativeCard.tsx      # rendered image + streamed copy + format tag
│   │   │   ├── SegmentSwitcher.tsx   # the live retarget control
│   │   │   ├── PredictedCtrBadge.tsx # CTR % + "based on N campaigns"
│   │   │   └── BeforeAfterPanel.tsx  # 3–5 days vs <1 min
│   │   ├── lib/api.ts                # typed fetch wrappers, SSE reader
│   │   └── theme.ts                  # brand tokens, touch sizing
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── backend/                 # Python on AWS Lambda
│   ├── handlers/
│   │   ├── generate.py      # POST /generate
│   │   ├── predict.py       # POST /predict
│   │   ├── segments.py      # GET /segments
│   │   └── catalog.py       # GET /catalog
│   ├── core/
│   │   ├── bedrock.py       # Claude (copy, streamed) + Nova Canvas (image)
│   │   ├── perf_model.py    # historical-data CTR predictor
│   │   ├── prompts.py       # brand tokens + segment-conditioned prompt builders
│   │   ├── cache.py         # hero-set cache lookup + fallback
│   │   └── data.py          # load synthetic JSON
│   └── requirements.txt
├── data/                    # synthetic / sample (NO real customer data)
│   ├── catalog.json
│   ├── segments.json
│   ├── campaign_history.json
│   └── hero_set/            # pre-generated images + manifest.json
├── scripts/
│   ├── seed_hero_set.py     # pre-generates the cached hero creatives (run Day 2)
│   └── verify_bedrock.py    # Day-1 model-access check (text + image)
└── infra/                   # AWS CDK (TypeScript)
    ├── bin/app.ts
    ├── lib/creativeiq-stack.ts
    ├── cdk.json
    └── package.json
```

---

## 2. Exact tech stack + versions

| Layer | Choice | Version (pin in lockfile) |
|---|---|---|
| Frontend framework | React + TypeScript | React 18.3.x, TypeScript 5.4.x |
| Build tool | Vite | 5.2.x |
| UI | Tailwind CSS + Recharts | Tailwind 3.4.x, Recharts 2.12.x |
| HTTP/stream | native `fetch` + SSE (`ReadableStream`) | — |
| Backend runtime | Python on AWS Lambda | Python 3.12 |
| AWS SDK | boto3 | ≥ 1.34.x (bundled or layer) |
| AI — copy | Amazon Bedrock → Claude Sonnet 4.6 | model id `anthropic.claude-sonnet-4-6` |
| AI — image | Amazon Bedrock → Amazon Nova Canvas | model id `amazon.nova-canvas-v1:0` (fallback: `amazon.titan-image-generator-v2:0`) |
| Assets | Amazon S3 | — |
| API | API Gateway (HTTP API) + Lambda; streaming via Lambda response streaming or chunked SSE | — |
| Infra | AWS CDK | v2 (latest) |
| Region | `ap-southeast-1` (Singapore); fall back to `us-east-1` if Bedrock image access is gated | — |

> **Bedrock model-id note (load-bearing):** On Amazon Bedrock, Anthropic model IDs carry an `anthropic.` prefix — use `anthropic.claude-sonnet-4-6`, **never** the bare `claude-sonnet-4-6` (the bare form is for the first-party Anthropic API and will fail on Bedrock). If you bump the copy model to Opus, the Bedrock id is `anthropic.claude-opus-4-8`. Verify exact available IDs in your region on Day 1 with `scripts/verify_bedrock.py` / `aws bedrock list-foundation-models`. Nova Canvas / Titan are AWS-native (Amazon) models, not Anthropic. **Reasoning for model choice:** Sonnet 4.6 is the speed/quality sweet spot for short ad copy and keeps streaming latency low for the demo; Opus 4.8 is available if copy quality needs a bump and latency budget allows.

---

## 3. Day-by-day with gates (this scenario)

**D1 — Data + skeleton calling Bedrock text.**
- Write the three synthetic datasets (`catalog.json`, `segments.json`, `campaign_history.json` — see §8).
- Run `scripts/verify_bedrock.py` in `ap-southeast-1`: confirm `anthropic.claude-sonnet-4-6` **and** `amazon.nova-canvas-v1:0` invoke successfully. If image model is gated, switch region to `us-east-1` now and record it everywhere.
- Stand up `/generate` (copy only, streamed) + `/catalog` + `/segments`. Vite app with a Generate button.
- **GATE:** UI button calls backend and returns a REAL Claude-generated caption for a real product×segment.

**D2 — Image gen + caching/fallback.**
- Add Nova Canvas image generation to `/generate`; upload result to S3, return URL.
- Build `scripts/seed_hero_set.py`; pre-generate the seeded hero combos (§7) into `data/hero_set/` + `manifest.json`.
- Wire `core/cache.py`: cache key = `product_id × segment_id`; on live-gen failure/timeout, serve hero set.
- **GATE:** changing an input (product or segment) changes the output image+copy live; killing Bedrock mid-demo still yields a coherent cached creative.

**D3 — Segment-aware generation + performance prediction + UI.**
- Implement `core/perf_model.py` + `/predict` (§6). Feed the segment's top-performing style/tone/format back into the generation prompt.
- Build `SegmentSwitcher`, `PredictedCtrBadge`, `CatalogView`, `SegmentsView`.
- **GATE:** all views navigable and coherent; switching segment re-renders copy + format + prediction.

**D4 — Before/after + polish + one-command deploy.**
- Build `BeforeAfterPanel` (3–5 day agency wait vs <1 min, side by side, on screen).
- First-10-seconds polish: hero screen, brand theme, touch-sized controls, streaming-copy animation.
- Finish CDK; one-command deploy; fresh-clone smoke test.
- **GATE:** fresh clone → follow README → working demo.

**D5 — Write-ups + record + buffer.**
- Fill `[fill after building]` blanks in BUILD_APPROACH.md; record the ~8-min walkthrough (DEMO_SCRIPT.md).
- **GATE:** all 4 deliverables done; ≥ ½ day buffer remaining.

---

## 4. Backend endpoint specs

All JSON unless noted. Errors return `{ "error": string }` with a 4xx/5xx — but on the **demo path** `/generate` never hard-fails: it degrades to the cached hero set (§7).

### `POST /generate`
Generate an ad creative for a product × segment.

- **Request:**
  ```json
  { "product_id": "linen-resort-shirt", "segment_id": "genz-instagram" }
  ```
- **Response (non-streaming summary; copy is also streamed — see below):**
  ```json
  {
    "product_id": "linen-resort-shirt",
    "segment_id": "genz-instagram",
    "format": "social_square",        // chosen per segment
    "copy": { "headline": "...", "body": "...", "cta": "..." },
    "image_url": "https://<bucket>.s3.../creatives/linen-resort-shirt_genz-instagram.png",
    "source": "live",                  // "live" | "cache"
    "brand_tokens_applied": ["palette:coastal", "voice:playful"]
  }
  ```
- **Streaming:** copy streams as SSE `text` deltas while the image renders asynchronously; final event carries `image_url` + `format`. Frontend shows copy typing in, then the image fades in.
- **Logic:**
  1. Load product (catalog) + segment profile.
  2. Query `perf_model` for the segment's best-performing **image style**, **copy tone**, and **format** (so creative is data-informed).
  3. Build the copy prompt (brand tokens + segment conditioning, §5) → stream Claude.
  4. Build the image prompt (brand tokens + style + segment) → Nova Canvas → S3.
  5. On any Bedrock error/timeout (e.g. > 12s for image): return the cached hero creative for this key with `"source": "cache"`. **Never throw on the demo path.**

### `POST /predict`
Predict performance for a product × segment × format over the historical dataset.

- **Request:**
  ```json
  { "segment_id": "genz-instagram", "format": "social_square", "image_style": "lifestyle", "copy_tone": "playful" }
  ```
- **Response:**
  ```json
  {
    "predicted_ctr": 0.041,
    "predicted_ctr_pct": "4.1%",
    "confidence": "high",
    "based_on_n_campaigns": 18,
    "segment_avg_ctr": 0.033,
    "lift_vs_segment_avg_pct": "+24%"
  }
  ```
- **Logic:** see §6 — a transparent feature model over `campaign_history.json`. **No LLM call here** — this is the "grounded, not invented" proof.

### `GET /segments`
- **Response:** `[ { "id", "name", "channel", "age_band", "tone", "top_format", "avg_ctr", "blurb" }, ... ]` from `segments.json` (avg_ctr/top_format computed from history).

### `GET /catalog`
- **Response:** `[ { "id", "name", "category", "price", "description", "image_url", "tags" }, ... ]` from `catalog.json`.

---

## 5. Image + copy generation spec

**Models:** copy = `anthropic.claude-sonnet-4-6` (Bedrock, streamed); image = `amazon.nova-canvas-v1:0` (Bedrock; fallback `amazon.titan-image-generator-v2:0`).

**Brand tokens** (constrain every generation for on-brand consistency — define once in `prompts.py`):
```
BRAND = {
  "name": "Lumen & Coast",
  "palette": "coastal neutrals — sand, off-white, muted teal, terracotta accent",
  "voice": "confident, warm, effortless; never salesy or hype-y",
  "imagery": "natural light, real fabric texture, relaxed resort lifestyle, minimal props",
  "avoid": "neon, heavy filters, stock-photo stiffness, cluttered backgrounds"
}
```

**Segment conditioning** — each segment carries a `tone`, `channel`, and `top_format`. The prompt builder injects them so copy and image adapt:

- Copy prompt sketch (Claude, system + user):
  ```
  System: You write on-brand ad copy for {BRAND.name}. Brand voice: {BRAND.voice}.
          Never invent product attributes not in the description. Output JSON:
          {headline, body, cta}. Calibrate length and tone to the channel.
  User:   Product: {name} — {description}. Tags: {tags}.
          Target segment: {segment.name} ({segment.age_band}) on {segment.channel}.
          Desired tone: {segment.tone}. Format: {format} (e.g. social_square = ≤12-word
          headline + 1 short line; email_hero = subject + preheader + 2-sentence body).
          Top-performing copy tone for this segment historically: {perf.top_tone}.
  ```
- Image prompt sketch (Nova Canvas `textToImage`):
  ```
  "{BRAND.imagery}. {product.name}, {product.description}. Style: {perf.top_image_style}
   suited to {segment.name} on {segment.channel}. Palette: {BRAND.palette}.
   Composition for {format} aspect ratio. Avoid: {BRAND.avoid}."
  aspect ratio per format: social_square=1024x1024, story=720x1280, email_hero=1280x720, display=1200x628
  ```

**Streaming + async image:** start the Claude stream immediately (copy appears within ~1s — sets the first-10-seconds impression); fire the Nova Canvas call concurrently; resolve the image into the card when ready (typically a few seconds). This hides image latency behind visible copy progress.

---

## 6. Performance-prediction approach (write it explicitly — make it mechanical)

`core/perf_model.py` is a transparent, feature-based predictor over `campaign_history.json`. **No machine learning training step is required** for the demo; it's an explainable aggregate model, which is also easier to defend on camera ("grounded in your data").

**Features extracted from each historical campaign row:** `segment_id`, `channel`, `format`, `image_style`, `copy_tone`, observed `ctr`, `impressions`.

**Predict(segment_id, format, image_style, copy_tone) →**
1. Filter history to rows matching `segment_id`. Call this set `S` (size `n_segment`).
2. Compute `segment_avg_ctr = impression-weighted mean CTR over S`.
3. Within `S`, compute multiplicative adjustment factors for each chosen feature:
   - `f_format = mean_ctr(S where format=format) / segment_avg_ctr`
   - `f_style  = mean_ctr(S where image_style=image_style) / segment_avg_ctr`
   - `f_tone   = mean_ctr(S where copy_tone=copy_tone) / segment_avg_ctr`
   - If a sub-slice has < 3 rows, set its factor to 1.0 (insufficient evidence → no adjustment) and lower `confidence`.
4. `predicted_ctr = segment_avg_ctr * f_format * f_style * f_tone`, clamped to a sane range (0.2%–9%).
5. `based_on_n_campaigns = n_segment`; `confidence` = high if all three slices had ≥ 3 rows, else medium/low.
6. `lift_vs_segment_avg = predicted_ctr / segment_avg_ctr - 1`.

This is fully deterministic, fast (pure pandas/dict ops), and explainable — the badge can show "4.1%, +24% vs this segment's average, based on 18 comparable campaigns." When a judge switches the segment, the numbers move because the underlying slice changes. That *is* the grounding proof.

---

## 7. Caching / fallback strategy (in detail)

**Why:** image-gen latency, quality variance, and brand consistency are the #1 demo-day risks. We never let a slow or off-brand image break the hero moment.

- **Pre-gen hero set (Day 2):** `scripts/seed_hero_set.py` generates creatives for every **seeded combo** (§8) and writes `data/hero_set/<product>_<segment>.png` + `manifest.json` mapping `key → {image_url, copy, format, predicted_ctr}`. These are hand-checked for brand quality.
- **Cache key:** `f"{product_id}__{segment_id}"`. `core/cache.py` exposes `get(key) -> CachedCreative | None`.
- **Fallback ladder in `/generate`:**
  1. Try live generation (copy stream + Nova Canvas image).
  2. If image gen errors or exceeds the latency budget (~12s), serve the hero-set image for the key but keep the **live-streamed copy** if it completed (best of both).
  3. If both fail, serve the full cached hero creative (`"source": "cache"`). Copy still types in from the cached text so the UX looks identical.
- **Seed data:** the seeded hero combos are the exact product×segment pairs the demo script clicks, so the on-camera path is always a cache hit *or* a fast live hit — both look great.
- **Stream-text-while-image-renders** is itself a degradation buffer: even a slow image feels responsive because copy is already on screen.

---

## 8. Synthetic data spec (no real customer data, no secrets)

All under `data/`. Brand: fictional "Lumen & Coast" resort-wear retailer.

**`catalog.json`** — 10–12 products:
```json
{ "id": "linen-resort-shirt", "name": "Linen Resort Shirt", "category": "tops",
  "price": 89, "description": "Breathable European linen, relaxed fit, mother-of-pearl buttons.",
  "image_url": "/data/catalog/linen-resort-shirt.png",
  "tags": ["linen","summer","unisex","resort"] }
```
(Provide placeholder product images in `data/catalog/`, or let Nova Canvas generate base product shots during seeding.)

**`segments.json`** — 4 segments:
```json
[
 { "id":"genz-instagram","name":"Gen-Z","channel":"Instagram","age_band":"18-24",
   "tone":"playful, trend-led, emoji-friendly","top_format":"social_square",
   "blurb":"Mobile-first, scroll-stopping visuals, short punchy copy." },
 { "id":"millennials-email","name":"Millennials","channel":"Email","age_band":"28-40",
   "tone":"aspirational, benefit-led","top_format":"email_hero",
   "blurb":"Value + quality story, responds to subject lines and preheaders." },
 { "id":"genx-display","name":"Gen-X","channel":"Display","age_band":"41-55",
   "tone":"clear, trustworthy, quality-forward","top_format":"display_banner",
   "blurb":"Banner placements, concise value proposition." },
 { "id":"professionals-social","name":"Urban Professionals","channel":"Facebook",
   "age_band":"30-45","tone":"polished, lifestyle","top_format":"social_square",
   "blurb":"Weekend/resort positioning, premium feel." }
]
```

**`campaign_history.json`** — ~120–180 rows of historical campaigns. Each row:
```json
{ "campaign_id":"c0001","date":"2025-08-14","product_id":"linen-resort-shirt",
  "segment_id":"genz-instagram","channel":"Instagram","format":"social_square",
  "image_style":"lifestyle","copy_tone":"playful","impressions":52000,"clicks":2130,
  "ctr":0.0410 }
```
Generate it so that **clear, defensible patterns exist** (this is what makes `/predict` look smart): e.g. Gen-Z×Instagram×lifestyle×playful CTR clusters high; Millennials×Email×benefit-led clusters mid; mismatched combos cluster low. Vary `image_style ∈ {lifestyle, studio, flatlay}`, `copy_tone ∈ {playful, benefit-led, minimal, aspirational}`, `format ∈ {social_square, email_hero, display_banner, story}`. Add small noise so it's not perfectly clean.

**Seeded hero combos** (must be cache-warm and demo-clicked):
```
linen-resort-shirt   × genz-instagram     (social_square)
linen-resort-shirt   × millennials-email  (email_hero)      ← the live switch
straw-tote-bag       × genz-instagram
linen-resort-shirt   × genx-display
silk-scarf           × professionals-social
```

---

## 9. Frontend view breakdown

- **StudioView** (the hero, default route): `GeneratePanel` (product picker + `SegmentSwitcher` + Generate) on the left; `CreativeCard` (image + streamed copy + format tag + `PredictedCtrBadge`) center; `BeforeAfterPanel` along the bottom. Big, touch-sized controls (≥48px hit targets), generous spacing, brand theme from `theme.ts`.
- **GeneratePanel:** product dropdown/grid + segment chips. Generate button is the focal CTA.
- **SegmentSwitcher:** segment chips that, when changed *after* a generation, immediately re-fire `/generate` + `/predict` for the same product — this is the live retarget. Visibly animate the copy rewrite and format change.
- **CreativeCard:** renders the streamed copy (typing animation), then fades in the image; shows the chosen `format` as a tag; hosts `PredictedCtrBadge`.
- **PredictedCtrBadge:** big % + "+24% vs segment avg · based on 18 campaigns". Color-coded (green/amber). Updates on every generation/switch.
- **BeforeAfterPanel:** two cards side by side — "Agency: 3–5 days, manual brief→wait→revise" vs "CreativeIQ: <1 min, data-informed, on-brand" — with an elapsed timer that shows the actual seconds the last generation took. On screen, not narrated.
- **CatalogView / SegmentsView:** browseable grids backed by `/catalog` and `/segments`. Navigable and coherent (Day-3 gate) but secondary to Studio.

---

## 10. Deploy steps

1. **Day-1 Bedrock access check:**
   ```
   python scripts/verify_bedrock.py --region ap-southeast-1
   # invokes anthropic.claude-sonnet-4-6 (text) + amazon.nova-canvas-v1:0 (image)
   # if image model access is gated → re-run --region us-east-1 and set REGION everywhere
   ```
   Request model access in the Bedrock console first if `AccessDeniedException`.
2. **Seed hero set (Day 2):** `python scripts/seed_hero_set.py --region <REGION>` → populates `data/hero_set/` and uploads to S3.
3. **Deploy infra (one command):**
   ```
   cd infra && npm install && npx cdk bootstrap && npx cdk deploy --require-approval never
   ```
   Stack provisions: S3 (assets), 4 Lambdas, HTTP API Gateway, IAM (least-privilege: `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`, S3 read/write on the one bucket). Serverless, ~$0 idle.
4. **Run frontend against deployed API:** set `VITE_API_BASE` to the API Gateway URL, `npm run build && npm run preview` (or `npm run dev` for local).

> **Production safety:** synthetic data only; no secrets in the repo (region + API base via env/CDK outputs). IAM scoped to InvokeModel + the single bucket — no broad permissions.

---

## 11. Graceful-degradation plan (demo-day)

| Failure | Mitigation |
|---|---|
| Image gen slow/timeout | Serve hero-set image; keep live copy. Latency hidden by streaming copy. |
| Bedrock throttling / `AccessDenied` mid-demo | Full cached hero creative; UX identical. |
| Region image-model gated | Decided Day 1 → deploy in `us-east-1`. |
| Network blip in showroom | Frontend ships hero-set manifest bundled; can render last-known creative without backend. |
| Judge picks an unseeded combo | Live gen runs; if it's slow/off-brand, fallback to nearest seeded combo's image + live copy. Still coherent. |

---

## 12. Definition of Done (mirrors the §14 / quality bar)

The DEMO PATH must be a 5 — "I'd show this to a customer CEO tomorrow, unedited." Check all:

- [ ] Fresh clone → README → one-command deploy → working demo (no hidden steps).
- [ ] First 10 seconds on the hero screen look showroom-grade (theme, spacing, touch sizing).
- [ ] Pick product + segment → live Bedrock image + streamed copy appears.
- [ ] Switching the segment live re-renders copy + format + prediction, visibly.
- [ ] Predicted-CTR badge is grounded in `campaign_history.json` (shows N campaigns / lift), not invented.
- [ ] Before/after (3–5 day agency vs <1 min) is **on screen**, with a real elapsed timer.
- [ ] Judges can change inputs and it keeps producing coherent, different results (no static/hardcoded path).
- [ ] Cached hero set covers every demo-clicked combo; killing Bedrock still yields a coherent creative.
- [ ] No real customer data; no secrets in repo; IAM least-privilege.
- [ ] All 4 deliverables present (codebase+README, ARCHITECTURE, BUILD_APPROACH, recording); ≥ ½ day buffer.
- [ ] Off-path rough edges are off the demo path only — they don't appear on camera or in clone-to-run.
