# CreativeIQ — AI-Powered Retail Ad Studio

CreativeIQ compresses a fashion retailer's 3–5 day agency creative cycle into under a minute. Pick a **product** and a **target segment**, and it generates an on-brand ad — image + copy + format — informed by historical campaign performance, with a **predicted click-through-rate** grounded in the retailer's own data. Switch the segment and the copy, format, and prediction re-render live. A **Campaigns** view exposes the 160-campaign performance history the prediction is computed from — so the badge is auditable, not asserted. The UI ships with a **light/dark theme toggle** (default light).

> **Honest framing:** the **CTR prediction is real** (a transparent model over the bundled campaign history) and **copy streams from Claude** when `USE_BEDROCK=1` with creds. Product **images are on-brand *previews*** offline — live Nova Canvas image generation is wired but **not** running in this environment (no creds), so don't read the previews as live renders.

This is the prototype for **Scenario B (Retail)** of the AWS APJ Innovation Hub challenge. It uses **synthetic data only** — no real customer data, no secrets in the repo.

---

## What's inside

```
frontend/   React + TypeScript + Vite + Tailwind (the studio UI)
  src/theme.ts              CSS-variable theming (light/dark) + brand tokens
  src/views/CampaignsView.tsx  campaign-history evidence base (the prediction's grounding)
backend/    Python AWS Lambda handlers: /generate /predict /segments /catalog /campaigns
  handlers/campaigns.py     recent campaigns + book-level rollups (Lambda-shaped)
data/       Synthetic catalog, segments, campaign history, pre-generated hero set
scripts/    verify_bedrock.py (Day-1 access check), seed_hero_set.py (cache warmer)
infra/      AWS CDK (one-command deploy)
```

Architecture overview: see `ARCHITECTURE.md`. Build approach: see `BUILD_APPROACH.md`.

---

## Prerequisites

- **Node.js** ≥ 18 and npm (verified with Node 22 / npm 10)
- **Python 3.12** (the backend uses 3.12; `python3.12` on macOS Homebrew)
- **No AWS credentials required.** The full demo runs **offline** — pre-generated, on-brand
  hero creatives (branded SVG placeholders) + grounded CTR predictions are bundled in `data/`.
- *(Optional, for live Bedrock)* AWS credentials + Bedrock model access in your region:
  - Text: `anthropic.claude-sonnet-4-6` (note the Bedrock `anthropic.` prefix)
  - Image: `amazon.nova-canvas-v1:0`; fallback `amazon.titan-image-generator-v2:0`
  - Region `ap-southeast-1` preferred; `us-east-1` if the image model is gated.

---

## One-command local run (offline — zero AWS)

```bash
./run.sh
```
This generates the synthetic data + offline hero assets, installs deps, starts the backend
on **http://localhost:8000**, and the Vite dev server on **http://localhost:5173**. Open
**http://localhost:5173**. Ctrl-C stops both.

> The frontend dev server proxies `/api` and `/data` to the backend, so no env config is needed.

### Manual run (two terminals)

**Terminal 1 — data + backend:**
```bash
python3.12 scripts/seed_data.py        # synthetic catalog / segments / 160 campaign rows
python3.12 scripts/gen_assets.py       # branded offline hero creatives + manifest
cd backend
python3.12 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/python -m uvicorn app:app --port 8000
```

**Terminal 2 — frontend:**
```bash
cd frontend
npm install                            # uses the public npm registry (frontend/.npmrc)
npm run dev                            # http://localhost:5173
# or: npm run build && npm run preview
```

Quick backend sanity check (offline): `cd backend && ./.venv/bin/python test_smoke.py`

---

## Optional: live Bedrock mode

With AWS credentials configured and Bedrock model access granted:
```bash
USE_BEDROCK=1 python3.12 scripts/verify_bedrock.py --region ap-southeast-1   # Day-1 access check
# then run the backend with the flag set:
cd backend && USE_BEDROCK=1 CREATIVEIQ_REGION=ap-southeast-1 ./.venv/bin/python -m uvicorn app:app --port 8000
```
`/generate` then streams real Claude copy and renders a real Nova Canvas image; on any
error/timeout it falls back to the bundled hero set. The CTR prediction is real local
computation either way. (Live Bedrock paths are implemented but were **not** exercised here —
AWS credentials were expired/unavailable, so live Bedrock never ran. **Image generation is the
un-run part:** offline, `/generate` serves on-brand SVG *previews*, not live Nova Canvas renders —
the CreativeCard badge reads "on-brand preview" offline and "live Bedrock" only when image-gen is
wired + credentialed. Offline mode is fully verified.)

## Cloud deploy (deferred)

CDK/cloud deploy is intentionally deferred — this prototype is graded as a **local run**.
See `infra/README.md` for the intended one-command CDK deploy and the (stubbed) stack shape.

---

## What to open and click (the demo path)

1. Open the app — it lands on **StudioView** (the hero screen).
2. **The evidence base:** click the **Campaigns** tab — 160 historical campaigns with real CTR, book avg ~2.68%, top-quartile performers flagged, segment filter. This is the retailer's own unused data, and it's *exactly* what the predicted-CTR badge is computed from — so the prediction is auditable, not asserted.
3. Back to Studio. Hero combo: select product **Linen Resort Shirt** + segment **Gen-Z · Instagram** → **Generate**. Watch copy stream in, the on-brand creative preview render, and the predicted-CTR badge appear (e.g. **4.8% · +56% vs segment avg · 40 campaigns**).
4. **The money shot:** switch the segment chip to **Millennials · Email** (don't re-pick the product). Copy rewrites, format flips to email hero, prediction updates — live.
5. Glance at the **before/after panel** (3–5 day agency vs the real elapsed seconds you just saw).
6. The **sun/moon button** in the header toggles light/dark (default light; record demos in light).

> **Image honesty:** the creative shown offline is an **on-brand preview**, not a live Nova Canvas render (AWS creds are expired in this environment, so live image-gen never runs). The *prediction* (real) and *copy stream* (real when live) carry the "it's real" weight; don't claim "just generated by Nova Canvas" while running offline.

**Pre-warmed hero combos** (guaranteed fast/on-brand on camera):
- Linen Resort Shirt × Gen-Z · Instagram (social square)
- Linen Resort Shirt × Millennials · Email (email hero) ← the live switch
- Straw Tote Bag × Gen-Z · Instagram
- Linen Resort Shirt × Gen-X · Display
- Silk Scarf × Urban Professionals · Social

Changing to any other product/segment still runs the real pipeline — the **prediction recomputes live** off the campaign history (so judges can break any canned-result assumption), and **copy streams from Claude when live**. The image is an **on-brand preview** (offline) or a Nova Canvas render only when image-gen is wired + credentialed — which it isn't here, so don't expect a fresh AI image offline.

---

## Notes

- **Synthetic data only.** The campaign history is engineered with realistic, defensible patterns so the prediction reflects the data.
- **No secrets in the repo.** Region and API base come from env/CDK outputs.
- **Serverless, ~$0 idle.** Tear down with `cd infra && npx cdk destroy`.
