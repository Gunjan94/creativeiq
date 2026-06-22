"""
imagegen.py — net-new AI image generation for the no-Bedrock demo path.

The marquee capability of CreativeIQ is *generating a new ad image* from the
product + segment + brand style — not compositing the catalog photo. When live
Bedrock (Nova Canvas) is credentialed, generate.py uses that. When it is not
(the zero-AWS-credentials demo), this module produces a genuinely NEW image with
a keyless, open text-to-image endpoint (Pollinations · Flux/SD), so the demo
still shows real AI generation rather than a re-framed stock photo.

Design for a reliable demo:
  * deterministic seed per (product, segment, format) -> stable, reproducible output;
  * on-disk cache in data/generated/ -> a cached combo returns instantly with no
    network call (so a recorded walkthrough never waits or fails);
  * generated at the FORMAT's aspect ratio -> the image fills the ad frame with no
    cropping of the subject;
  * graceful failure -> returns None so the caller falls back to composing over the
    reference photo. The demo never hard-fails.
"""
from __future__ import annotations

import hashlib
import os
import urllib.parse
import urllib.request

from . import data

GEN_DIR = os.path.join(data.DATA_DIR, "generated")
ENDPOINT = "https://image.pollinations.ai/prompt/"
TIMEOUT_S = float(os.environ.get("CREATIVEIQ_IMAGEGEN_TIMEOUT", "45"))
# Allow disabling network generation entirely (pure-offline CI / air-gapped).
ENABLED = os.environ.get("CREATIVEIQ_IMAGEGEN", "1") == "1"

# Per-format output dimensions (match the ad frame so nothing is cropped).
FORMAT_DIMS = {
    "social_square": (1024, 1024),
    "story": (768, 1344),
    "email_hero": (1344, 768),
    "display_banner": (1280, 672),
}

# Segment -> visual direction for the generated scene.
_SEGMENT_VIBE = {
    "genz-instagram": "vibrant playful trend-led social-media aesthetic, youthful energy, candid",
    "millennials-email": "aspirational warm premium lifestyle, relatable, golden light",
    "genx-display": "clean trustworthy premium catalog look, product-forward, uncluttered",
    "professionals-social": "polished sophisticated weekend-resort lifestyle, refined",
}

_BRAND_STYLE = (
    "editorial fashion advertising photograph, natural light, real fabric texture, "
    "coastal resort palette of sand off-white muted teal and terracotta, minimal clean "
    "composition, high-end commercial photography, sharp focus, no text, no watermark, no logo"
)


def _key(product_id: str, segment_id: str, fmt: str) -> str:
    return f"{product_id}__{segment_id}__{fmt}"


def _seed(key: str) -> int:
    return int(hashlib.sha256(key.encode()).hexdigest(), 16) % 1_000_000


def build_prompt(product: dict, segment: dict, fmt: str) -> str:
    """Compose the text-to-image prompt from product + segment + brand style."""
    vibe = _SEGMENT_VIBE.get(segment.get("id", ""), "premium lifestyle")
    desc = product.get("description") or product.get("name", "resort wear")
    name = product.get("name", "")
    return (
        f"{_BRAND_STYLE}. Subject: {name} — {desc}. "
        f"Styled for {segment.get('name','')} on {segment.get('channel','')}: {vibe}."
    )


def cached_path_url(product_id: str, segment_id: str, fmt: str):
    """Return (abs_path, url) for the cached image of this combo, or (None, None)."""
    fname = f"{_key(product_id, segment_id, fmt)}.jpg"
    abs_path = os.path.join(GEN_DIR, fname)
    if os.path.isfile(abs_path) and os.path.getsize(abs_path) > 1024:
        return abs_path, f"/data/generated/{fname}"
    return None, None


def generate(product: dict, segment: dict, fmt: str, force: bool = False):
    """
    Generate (or fetch cached) a NEW AI image for product x segment x format.
    Returns a "/data/generated/..." URL the frontend can load, or None on failure.
    """
    product_id = product.get("id", "uploaded")
    segment_id = segment.get("id", "seg")

    cached_abs, cached_url = cached_path_url(product_id, segment_id, fmt)
    if cached_abs and not force:
        return cached_url

    if not ENABLED:
        return None

    w, h = FORMAT_DIMS.get(fmt, (1024, 1024))
    prompt = build_prompt(product, segment, fmt)
    seed = _seed(_key(product_id, segment_id, fmt))
    url = (
        ENDPOINT
        + urllib.parse.quote(prompt)
        + f"?width={w}&height={h}&seed={seed}&nologo=true&model=flux"
    )

    # Lambda / read-only filesystem: don't download+serve (the task dir is
    # read-only and /data only serves bundled files). Return the keyless image
    # URL directly so the browser loads the genuinely-generated image client-side.
    if os.environ.get("CREATIVEIQ_IMAGE_DIRECT") == "1":
        return url

    os.makedirs(GEN_DIR, exist_ok=True)
    fname = f"{_key(product_id, segment_id, fmt)}.jpg"
    abs_path = os.path.join(GEN_DIR, fname)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CreativeIQ/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            ctype = resp.headers.get("Content-Type", "")
            data_bytes = resp.read()
        if not ctype.startswith("image") or len(data_bytes) < 1024:
            return None
        with open(abs_path, "wb") as f:
            f.write(data_bytes)
        return f"/data/generated/{fname}"
    except Exception:  # noqa: BLE001 — never break the demo path
        return None
