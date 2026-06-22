> **Current-state addendum (2026-06-22).** Kept as build history. For the current build see **README.md**,
> **ARCHITECTURE.md**, **DEMO_SCRIPT.md**. Net change: **live keyless image generation** (no longer a
> "preview"), **CTR transparency drill-down** (`/comparable`), **segment×format heatmap** (`/analytics`),
> **annual money roll-up**, two-audience framing, and a full AWS deploy path. **Live:**
> https://d33y5855vpqrlk.cloudfront.net.

---

# BUILD_NOTES.md — CreativeIQ (Scenario B)

What was actually built, how to run it, what is real vs mocked, and verification evidence.

## What this is

A full, locally-runnable prototype of **CreativeIQ**: pick a product + segment → an on-brand
ad (image + copy + format) appears with a predicted-CTR badge grounded in a historical
campaign dataset → switching the segment live re-renders copy, format, and prediction → a
before/after panel shows "3–5 day agency wait" vs the real elapsed time of the last generation.

**It runs with ZERO AWS credentials** (the design requirement). Real Bedrock is wired behind
`USE_BEDROCK=1` but was not exercised in this build (no creds available).

## How to run (verified)

```bash
./run.sh           # one command: data + assets + backend(:8000) + frontend(:5173)
# open http://localhost:5173
```
Manual / two-terminal steps and the optional live-Bedrock mode are in `README.md`.

Backend smoke tests (offline, no network): `cd backend && ./.venv/bin/python test_smoke.py` → 7/7 pass.

## Architecture as built

- **backend/** — Python, plain handler functions (`handlers/{generate,predict,segments,catalog,campaigns}.py`)
  behind a local **FastAPI** server (`app.py`, uvicorn). Each handler also has a
  `lambda_handler(event, context)` so it drops into Lambda later. Core logic in `core/`:
  `perf_model.py` (CTR predictor), `prompts.py` (brand tokens + segment conditioning),
  `cache.py` (hero-set lookup + nearest-in-segment fallback), `bedrock.py` (Claude + Nova,
  offline-safe), `data.py` (JSON loaders), `storage.py` (local image writes; swap for S3 later).
  `handlers/campaigns.py` serves recent campaign rows + book-level rollups (the same rows
  `perf_model.py` predicts from — exposing them makes the prediction auditable).
- **frontend/** — React 18 + TypeScript + Vite 5 + Tailwind 3 + Recharts. `StudioView` is the
  hero (GeneratePanel · CreativeCard · SegmentSwitcher · PredictedCtrBadge · BeforeAfterPanel);
  `CatalogView`, `SegmentsView`, and `CampaignsView` (the 160-row performance history / evidence
  base) are the browse views. `theme.ts` owns the light/dark palette (default light) as CSS
  variables consumed by `tailwind.config.js` + `index.css`; a header sun/moon button toggles it.
  SSE-over-fetch reader in `lib/api.ts` (+ `getCampaigns`). Dev server proxies `/api` + `/data`
  to the backend (no env config needed).
- **data/** — committed synthetic data: `catalog.json` (10 products), `segments.json` (4),
  `campaign_history.json` (160 rows), `hero_set/` (40 branded SVG creatives + `manifest.json`),
  `catalog/` (10 product card SVGs).
- **scripts/** — `seed_data.py` (seeded synthetic data with engineered CTR patterns),
  `gen_assets.py` (composes offline branded creatives + manifest), `seed_hero_set.py`
  (offline placeholders, or live Bedrock seeding under `USE_BEDROCK=1`),
  `verify_bedrock.py` (Day-1 model-access check).
- **infra/** — CDK **stub** (deferred per the build plan; prototype is graded as a local run).

## Real vs mocked — be explicit

| Piece | Status |
|---|---|
| **CTR prediction** (`perf_model.py`, `/predict`) | **REAL.** Deterministic feature model computed live over `campaign_history.json` (impression-weighted segment avg × format/style/tone factors, clamped, with confidence + sample count). No hardcoding — changing inputs changes the slice and the number. This is the prototype's most defensible claim. |
| **Campaign history** (`handlers/campaigns.py`, `/campaigns`) | **REAL.** Serves the actual 160 historical campaign rows + book-level rollups (book avg CTR 2.68%, top-quartile performers flagged, segment filter). These are the *same rows* `/predict` is computed from, so the `CampaignsView` makes the predicted-CTR badge auditable. |
| **Segment-aware generation** | **REAL logic.** Format, image_style, copy_tone are mined per-segment from history (`best_features_for_segment`); switching segment genuinely re-fires `/generate` + `/predict` and re-renders. |
| **Ad images** | **NOT RUN as live AI — on-brand previews offline.** Offline, `/generate` serves branded SVG creatives composed locally per product×segment from the coastal palette + per-segment styling — intentionally **previews**, NOT photographic and NOT Nova Canvas output. The CreativeCard badge says "on-brand preview" offline. The live **Nova Canvas** path (Titan fallback) is wired behind `USE_BEDROCK=1` + creds but was **never exercised** here. **This is B's headline gap: the marquee feature (AI image generation) is the part not running.** |
| **Ad copy** | **MOCKED offline (canned, on-brand), REAL when live.** Offline serves hand-written on-brand copy (specific for seeded combos, tone-templated otherwise), typed in word-by-word. With `USE_BEDROCK=1` it streams real **Claude Sonnet 4.6** copy token-by-token. |
| **Streaming** | **REAL SSE** end to end (meta → copy deltas → image → done), through the Vite proxy, both offline and live. |
| **Bedrock calls** | **IMPLEMENTED, NOT EXERCISED — creds expired.** Code is present (`converse_stream`, `invoke_model`) but AWS credentials were expired/unavailable in this environment, so live Bedrock (copy stream + image gen) never ran and is **unverified**. Offline path is fully verified. |
| **Theme (light/dark)** | **REAL.** `theme.ts` writes the active palette as CSS variables; default light, header sun/moon toggle, persisted to localStorage. |
| **Cloud deploy (CDK)** | **STUB / deferred.** Not deployed. |

## Verification evidence (what I ran and saw)

- `python3.12 scripts/seed_data.py` → "Wrote 10 products, 4 segments, 160 campaign rows"; per-segment
  avg CTR 2.3%–3.1% (sane spread).
- `python3.12 scripts/gen_assets.py` → "Wrote 10 product cards + 40 hero creatives + manifest.json".
- Backend up (`uvicorn app:app`), `GET /health` → `{"ok":true,"use_bedrock":false,"mode":"offline"}`.
- `GET /catalog` → 10 products; `GET /segments` → 4 segments enriched with avg_ctr + top_format.
- `GET /campaigns` → **160 campaigns** on record, **book avg CTR 2.68%**, top-quartile performers flagged,
  segment filter working — the evidence base `CampaignsView` renders and that `/predict` is grounded in.
- `POST /predict` grounded output, e.g. genz-instagram/social_square/lifestyle/playful →
  **4.8% CTR, +56% vs segment avg, n=40, high confidence**; a deliberately weak combo
  (email_hero/studio/benefit-led) → **2.0%, −34%**. Inputs move the number.
- `POST /generate` SSE → event sequence `meta`(1) `delta`(11) `copy`(1) `image`(1) `done`(1).
- **The money shot:** same product `linen-resort-shirt`, switching segment →
  genz-instagram = `social_square` @ **4.8% (+56%)**, millennials-email = `email_hero` @ **4.4% (+76%)**.
  Format flips and CTR changes, computed from data.
- **Through the Vite dev proxy** (browser path): `/api/catalog`, `/api/predict`, `/api/generate` (SSE),
  and `/data/*.svg` images all return correctly; app root serves 200.
- **Zero-credential guarantee:** `bedrock.available()` → `False` with no creds; with `USE_BEDROCK=1`
  but boto3/creds absent, `stream_copy` raises `BedrockUnavailable` and the handler degrades to the
  hero set — verified.
- **Frontend build:** `npm run build` → TypeScript strict passes, `vite build` succeeds
  (839 modules, dist ~523 kB JS / 14 kB CSS).
- **One-command `./run.sh`:** brings up backend + frontend; generate flow verified end-to-end via proxy.
- **Backend smoke tests:** `test_smoke.py` → 7/7 pass.

## Known rough edges (off the demo path)

- **Image generation is the headline gap.** Offline images are **on-brand previews** (SVG, composed
  from the brand palette), NOT live Nova Canvas renders — and AWS creds are expired in this environment,
  so live image-gen never ran. The marquee feature is the un-run part: don't claim live image generation
  works. Frame as "on-brand previews; live Nova Canvas renders when image-gen is wired + credentialed."
  Gap G2 (live AI) remains **OPEN**.
- **Live Bedrock unverified — creds expired.** `verify_bedrock.py` / `USE_BEDROCK=1` paths (Claude copy
  stream + Nova Canvas image) are implemented but untested against real AWS. Region/model-id assumptions
  follow the brief; confirm in-region with valid creds on Day 1.
- **CDK is a stub** — no cloud deploy. Handlers are Lambda-shaped (`lambda_handler`) and
  `storage.py` is the single seam to swap local file writes for S3.
- **`professionals-social` top_format** surfaces as `email_hero` in `/segments` (impression-weighted
  best slice), which differs from the nominal `social_square` in `segments.json`. This is correct
  data-driven behavior, not a bug, but worth a word on camera if asked.
- **npm registry pinned** to public via `frontend/.npmrc` (build host defaulted to an expired
  internal CodeArtifact token).
- **Bundle size** warning (>500 kB) from Recharts — fine for a local demo; code-split if it matters.
- `data/generated/` (live image outputs) is gitignored; offline creatives under `data/hero_set/` are committed.
