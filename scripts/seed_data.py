#!/usr/bin/env python3
"""
seed_data.py — Generate synthetic CreativeIQ datasets with engineered, defensible patterns.

Produces (under ../data/):
  - catalog.json            10 Lumen & Coast resort-wear products
  - segments.json           4 customer segments
  - campaign_history.json   ~160 historical campaign rows with clear CTR patterns

Run:  python scripts/seed_data.py
Deterministic (seeded) so the perf model + predictions are stable across runs.
"""
import json
import os
import random

SEED = 42
random.seed(SEED)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data")

# ---------------------------------------------------------------------------
# Catalog — fictional "Lumen & Coast" resort-wear retailer
# ---------------------------------------------------------------------------
CATALOG = [
    {"id": "linen-resort-shirt", "name": "Linen Resort Shirt", "category": "tops", "price": 89,
     "description": "Breathable European linen, relaxed fit, mother-of-pearl buttons.",
     "tags": ["linen", "summer", "unisex", "resort"]},
    {"id": "straw-tote-bag", "name": "Woven Straw Tote", "category": "bags", "price": 64,
     "description": "Hand-woven seagrass tote with leather handles, roomy beach-day carry.",
     "tags": ["straw", "beach", "accessory", "summer"]},
    {"id": "silk-scarf", "name": "Coastal Silk Scarf", "category": "accessories", "price": 72,
     "description": "Lightweight mulberry silk in a hand-painted tidal print.",
     "tags": ["silk", "print", "premium", "accessory"]},
    {"id": "linen-wide-trouser", "name": "Wide-Leg Linen Trouser", "category": "bottoms", "price": 98,
     "description": "Fluid wide-leg cut in washed linen, elastic comfort waist.",
     "tags": ["linen", "relaxed", "unisex", "resort"]},
    {"id": "cotton-sundress", "name": "Sunwashed Cotton Dress", "category": "dresses", "price": 119,
     "description": "Airy tiered cotton midi with adjustable straps and side pockets.",
     "tags": ["cotton", "dress", "summer", "womens"]},
    {"id": "leather-sandals", "name": "Handmade Leather Sandals", "category": "footwear", "price": 84,
     "description": "Vegetable-tanned leather slides, cushioned cork footbed.",
     "tags": ["leather", "footwear", "handmade", "unisex"]},
    {"id": "panama-hat", "name": "Brisa Panama Hat", "category": "accessories", "price": 58,
     "description": "Hand-blocked toquilla straw with grosgrain band, packable brim.",
     "tags": ["straw", "hat", "sun", "accessory"]},
    {"id": "swim-shorts", "name": "Tide Swim Shorts", "category": "swim", "price": 52,
     "description": "Quick-dry recycled fabric, tailored mid-length, drawcord waist.",
     "tags": ["swim", "recycled", "mens", "beach"]},
    {"id": "knit-polo", "name": "Coastal Knit Polo", "category": "tops", "price": 76,
     "description": "Breathable cotton-silk knit polo with a soft ribbed collar.",
     "tags": ["knit", "polo", "smart-casual", "mens"]},
    {"id": "linen-jumpsuit", "name": "Harbour Linen Jumpsuit", "category": "dresses", "price": 138,
     "description": "Belted wide-leg linen jumpsuit with utility pockets.",
     "tags": ["linen", "jumpsuit", "premium", "womens"]},
]

# ---------------------------------------------------------------------------
# Segments — 4 customer segments
# ---------------------------------------------------------------------------
SEGMENTS = [
    {"id": "genz-instagram", "name": "Gen-Z", "channel": "Instagram", "age_band": "18-24",
     "tone": "playful, trend-led, emoji-friendly", "top_format": "social_square",
     "blurb": "Mobile-first, scroll-stopping visuals, short punchy copy."},
    {"id": "millennials-email", "name": "Millennials", "channel": "Email", "age_band": "28-40",
     "tone": "aspirational, benefit-led", "top_format": "email_hero",
     "blurb": "Value + quality story, responds to subject lines and preheaders."},
    {"id": "genx-display", "name": "Gen-X", "channel": "Display", "age_band": "41-55",
     "tone": "clear, trustworthy, quality-forward", "top_format": "display_banner",
     "blurb": "Banner placements, concise value proposition."},
    {"id": "professionals-social", "name": "Urban Professionals", "channel": "Facebook", "age_band": "30-45",
     "tone": "polished, lifestyle", "top_format": "social_square",
     "blurb": "Weekend/resort positioning, premium feel."},
]

IMAGE_STYLES = ["lifestyle", "studio", "flatlay"]
COPY_TONES = ["playful", "benefit-led", "minimal", "aspirational"]
FORMATS = ["social_square", "email_hero", "display_banner", "story"]

# ---------------------------------------------------------------------------
# Engineered CTR signal.
# Each segment has a baseline CTR plus multiplicative preferences for
# format / image_style / copy_tone. Matched combos cluster high; mismatched low.
# ---------------------------------------------------------------------------
# Note: sampling is biased toward each segment's strong combos (so strong slices have
# enough rows for high-confidence factors), which already lifts segment_avg_ctr. Factor
# spreads are kept modest so the best combo lands in a believable ~4-5% range with a
# sensible single-digit-to-~30% lift over the (already-strong) segment average.
SEGMENT_PROFILE = {
    "genz-instagram": {
        "base": 0.030,
        "format": {"social_square": 1.15, "story": 1.10, "display_banner": 0.82, "email_hero": 0.78},
        "image_style": {"lifestyle": 1.15, "flatlay": 1.00, "studio": 0.85},
        "copy_tone": {"playful": 1.15, "minimal": 1.00, "aspirational": 0.95, "benefit-led": 0.85},
    },
    "millennials-email": {
        "base": 0.024,
        "format": {"email_hero": 1.18, "social_square": 0.97, "display_banner": 0.88, "story": 0.82},
        "image_style": {"lifestyle": 1.12, "studio": 1.03, "flatlay": 0.92},
        "copy_tone": {"benefit-led": 1.15, "aspirational": 1.10, "minimal": 0.94, "playful": 0.85},
    },
    "genx-display": {
        "base": 0.020,
        "format": {"display_banner": 1.18, "email_hero": 1.03, "social_square": 0.90, "story": 0.80},
        "image_style": {"studio": 1.15, "lifestyle": 1.00, "flatlay": 0.97},
        "copy_tone": {"benefit-led": 1.15, "minimal": 1.08, "aspirational": 0.97, "playful": 0.82},
    },
    "professionals-social": {
        "base": 0.026,
        "format": {"social_square": 1.15, "email_hero": 1.03, "display_banner": 0.93, "story": 0.90},
        "image_style": {"lifestyle": 1.15, "studio": 1.06, "flatlay": 0.90},
        "copy_tone": {"aspirational": 1.15, "minimal": 1.06, "benefit-led": 1.00, "playful": 0.90},
    },
}


def channel_for(segment_id):
    return next(s["channel"] for s in SEGMENTS if s["id"] == segment_id)


def gen_history(n_per_segment=40):
    rows = []
    cid = 1
    product_ids = [p["id"] for p in CATALOG]
    for seg in SEGMENTS:
        sid = seg["id"]
        prof = SEGMENT_PROFILE[sid]
        for _ in range(n_per_segment):
            # Bias sampling toward the segment's strong combos so each sub-slice
            # has >=3 rows for the strong picks (drives "high confidence" demo path),
            # but still include weak combos so lift is meaningful.
            fmt = random.choices(FORMATS, weights=[prof["format"][f] for f in FORMATS])[0]
            style = random.choices(IMAGE_STYLES, weights=[prof["image_style"][s] for s in IMAGE_STYLES])[0]
            tone = random.choices(COPY_TONES, weights=[prof["copy_tone"][t] for t in COPY_TONES])[0]
            product_id = random.choice(product_ids)

            ctr = (prof["base"]
                   * prof["format"][fmt]
                   * prof["image_style"][style]
                   * prof["copy_tone"][tone])
            # multiplicative noise (lognormal-ish), keeps it realistic but defensible
            ctr *= random.uniform(0.88, 1.12)
            ctr = max(0.002, min(0.09, ctr))

            impressions = random.randint(18000, 90000)
            clicks = int(round(impressions * ctr))
            rows.append({
                "campaign_id": f"c{cid:04d}",
                "date": f"2025-{random.randint(3,11):02d}-{random.randint(1,28):02d}",
                "product_id": product_id,
                "segment_id": sid,
                "channel": channel_for(sid),
                "format": fmt,
                "image_style": style,
                "copy_tone": tone,
                "impressions": impressions,
                "clicks": clicks,
                "ctr": round(clicks / impressions, 4),
            })
            cid += 1
    random.shuffle(rows)
    return rows


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    # attach image_url to catalog (local placeholders, generated by gen_assets.py)
    for p in CATALOG:
        p["image_url"] = f"/data/catalog/{p['id']}.png"

    with open(os.path.join(DATA_DIR, "catalog.json"), "w") as f:
        json.dump(CATALOG, f, indent=2)
    with open(os.path.join(DATA_DIR, "segments.json"), "w") as f:
        json.dump(SEGMENTS, f, indent=2)
    history = gen_history(40)
    with open(os.path.join(DATA_DIR, "campaign_history.json"), "w") as f:
        json.dump(history, f, indent=2)

    print(f"Wrote {len(CATALOG)} products, {len(SEGMENTS)} segments, {len(history)} campaign rows.")
    # quick sanity: per-segment avg ctr
    from collections import defaultdict
    agg = defaultdict(lambda: [0, 0])
    for r in history:
        agg[r["segment_id"]][0] += r["clicks"]
        agg[r["segment_id"]][1] += r["impressions"]
    for sid, (c, i) in agg.items():
        print(f"  {sid:24s} avg_ctr={c/i:.4f}  ({sum(1 for r in history if r['segment_id']==sid)} rows)")


if __name__ == "__main__":
    main()
