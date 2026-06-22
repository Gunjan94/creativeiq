#!/usr/bin/env python3
"""
seed_hero_set.py — pre-generate the cached hero creatives (BUILDER §7, Day 2).

Two modes:
  OFFLINE (default): compose branded placeholder hero creatives locally (delegates to
    gen_assets.py) — zero AWS, the committed offline demo path.
  LIVE (USE_BEDROCK=1): generate real Nova Canvas images + Claude copy for the seeded
    combos and write them into data/hero_set/ (overwriting the placeholders), updating
    manifest.json. (S3 upload is a documented later step; local files back the demo.)

Usage:
  python scripts/seed_hero_set.py                       # offline placeholders
  USE_BEDROCK=1 python scripts/seed_hero_set.py --region ap-southeast-1   # real Bedrock
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data")
HERO_DIR = os.path.join(DATA_DIR, "hero_set")
sys.path.insert(0, os.path.join(HERE, "..", "backend"))

# The exact product x segment pairs the demo clicks (BUILDER §8).
SEEDED_COMBOS = [
    ("linen-resort-shirt", "genz-instagram"),
    ("linen-resort-shirt", "millennials-email"),
    ("straw-tote-bag", "genz-instagram"),
    ("linen-resort-shirt", "genx-display"),
    ("silk-scarf", "professionals-social"),
]


def offline_seed():
    """Compose placeholder hero creatives for the FULL grid (covers seeded + any click)."""
    import gen_assets
    gen_assets.main()
    print("Offline hero set composed (branded SVG placeholders).")


def live_seed(region):
    os.environ["USE_BEDROCK"] = "1"
    os.environ["CREATIVEIQ_REGION"] = region
    from importlib import reload
    from core import bedrock, perf_model, prompts, data
    reload(bedrock)

    if not bedrock.available():
        print("USE_BEDROCK=1 but Bedrock unavailable (boto3/creds). Falling back to offline.")
        offline_seed()
        return

    os.makedirs(HERO_DIR, exist_ok=True)
    manifest_path = os.path.join(HERO_DIR, "manifest.json")
    manifest = {}
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)

    from handlers.generate import _parse_copy

    for product_id, segment_id in SEEDED_COMBOS:
        product = data.get_product(product_id)
        segment = data.get_segment(segment_id)
        best = perf_model.best_features_for_segment(segment_id)
        fmt = best["format"]
        w, h = prompts.FORMAT_DIMS.get(fmt, (1024, 1024))
        key = f"{product_id}__{segment_id}"
        print(f"  seeding {key} ({fmt}) ...")

        # copy
        raw = bedrock.generate_copy(prompts.copy_system_prompt(),
                                    prompts.copy_user_prompt(product, segment, fmt, best["copy_tone"]))
        copy = _parse_copy(raw)
        # image
        png = bedrock.generate_image(
            prompts.image_prompt(product, segment, best["image_style"], fmt), w, h)
        fname = f"{key}.png"
        with open(os.path.join(HERO_DIR, fname), "wb") as f:
            f.write(png)

        pred = perf_model.predict(segment_id, fmt, best["image_style"], best["copy_tone"])
        manifest[key] = {
            "product_id": product_id, "segment_id": segment_id,
            "image_url": f"/data/hero_set/{fname}", "format": fmt,
            "image_style": best["image_style"], "copy_tone": best["copy_tone"],
            "copy": copy, "predicted_ctr": pred["predicted_ctr"],
            "predicted_ctr_pct": pred["predicted_ctr_pct"],
        }

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Live hero set seeded for {len(SEEDED_COMBOS)} combos (Bedrock).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="ap-southeast-1")
    args = ap.parse_args()
    if os.environ.get("USE_BEDROCK") == "1":
        live_seed(args.region)
    else:
        offline_seed()


if __name__ == "__main__":
    main()
