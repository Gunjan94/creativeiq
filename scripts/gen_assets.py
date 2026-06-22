#!/usr/bin/env python3
"""
gen_assets.py — Compose branded OFFLINE placeholder images locally (no AWS, no Bedrock).

Generates, under ../data/:
  - catalog/<product>.svg         simple branded product cards
  - hero_set/<product>__<segment>.svg   pre-generated hero ad creatives (one per seeded combo,
                                  plus a full grid so any product x segment click has an offline image)
  - hero_set/manifest.json        key -> {image_url, copy, format, predicted_ctr, image_style, copy_tone}

These are intentionally PLACEHOLDER creatives (branded SVG composed locally) so the full demo
runs offline with zero AWS credentials. When USE_BEDROCK=1 + creds are present, the backend
calls real Nova Canvas / Claude instead; these assets are the cache/fallback floor.

Run AFTER seed_data.py:  python scripts/gen_assets.py
"""
import json
import os
import html

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data")
CATALOG_DIR = os.path.join(DATA_DIR, "catalog")
HERO_DIR = os.path.join(DATA_DIR, "hero_set")

# Brand palette (coastal neutrals)
PALETTE = {
    "sand": "#E8DFD2",
    "offwhite": "#F6F2EA",
    "teal": "#5C8A8A",
    "teal_deep": "#3F6B6B",
    "terracotta": "#C97B5A",
    "ink": "#2B2B28",
    "stone": "#9A9387",
}

# Per-segment visual styling so each rendered creative *looks* segment-specific.
SEGMENT_STYLE = {
    "genz-instagram":       {"bg": PALETTE["terracotta"], "accent": PALETTE["offwhite"], "mood": "playful"},
    "millennials-email":    {"bg": PALETTE["teal_deep"],  "accent": PALETTE["sand"],     "mood": "aspirational"},
    "genx-display":         {"bg": PALETTE["stone"],      "accent": PALETTE["ink"],      "mood": "trustworthy"},
    "professionals-social": {"bg": PALETTE["teal"],       "accent": PALETTE["offwhite"], "mood": "polished"},
}

# Format -> aspect (w,h)
FORMAT_DIMS = {
    "social_square": (1024, 1024),
    "email_hero":    (1280, 720),
    "display_banner": (1200, 628),
    "story":         (720, 1280),
}

# Segment -> recommended format / data-informed style+tone (mirrors perf model picks).
SEGMENT_FORMAT = {
    "genz-instagram":       ("social_square", "lifestyle", "playful"),
    "millennials-email":    ("email_hero", "lifestyle", "benefit-led"),
    "genx-display":         ("display_banner", "studio", "benefit-led"),
    "professionals-social": ("social_square", "lifestyle", "aspirational"),
}

# Canned but on-brand copy per (product, segment). Used in offline mode + as cache fallback.
# (product_id, segment_id) -> {headline, body, cta}
CANNED_COPY = {
    ("linen-resort-shirt", "genz-instagram"): {
        "headline": "Sun's out, linen's on ☀️", "body": "Your new everyday flex. Breezy, easy, done.",
        "cta": "Shop the drop"},
    ("linen-resort-shirt", "millennials-email"): {
        "headline": "The linen shirt you'll live in all summer",
        "body": "European linen, relaxed fit, mother-of-pearl detail. Effortless from beach to dinner — and built to last seasons, not weeks.",
        "cta": "Discover the shirt"},
    ("linen-resort-shirt", "genx-display"): {
        "headline": "Premium European linen. Made to last.",
        "body": "Relaxed-fit comfort, timeless cut.", "cta": "Shop now"},
    ("linen-resort-shirt", "professionals-social"): {
        "headline": "Off-duty, perfectly put together",
        "body": "The weekend uniform: relaxed linen, quiet confidence.", "cta": "Explore the edit"},
    ("straw-tote-bag", "genz-instagram"): {
        "headline": "Beach day starter pack 🧺", "body": "Throw it all in. Look effortless. You're welcome.",
        "cta": "Grab the tote"},
    ("silk-scarf", "professionals-social"): {
        "headline": "One scarf. Every look.",
        "body": "Hand-painted mulberry silk that elevates the simplest outfit.", "cta": "Discover silk"},
}

# Generic fallbacks per tone (when no specific canned copy exists, offline mode still works).
GENERIC_COPY = {
    "playful":     lambda p: {"headline": f"Meet your new favourite ✨", "body": f"{p['name']} — {p['description'].split(',')[0]}. Yes please.", "cta": "Shop the drop"},
    "benefit-led": lambda p: {"headline": f"{p['name']}: quality you'll feel", "body": f"{p['description']} Designed for the way you actually live — and made to last.", "cta": "Discover more"},
    "minimal":     lambda p: {"headline": p["name"], "body": p["description"].split(",")[0] + ".", "cta": "Shop now"},
    "aspirational":lambda p: {"headline": f"Effortless, always", "body": f"The {p['name'].lower()} — {p['description'].split(',')[0].lower()}. Quietly confident.", "cta": "Explore the edit"},
}


def esc(s):
    return html.escape(str(s))


def product_svg(p):
    initials = "".join(w[0] for w in p["name"].split()[:2]).upper()
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600" viewBox="0 0 600 600">
  <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{PALETTE['offwhite']}"/><stop offset="1" stop-color="{PALETTE['sand']}"/>
  </linearGradient></defs>
  <rect width="600" height="600" fill="url(#g)"/>
  <circle cx="300" cy="250" r="150" fill="{PALETTE['teal']}" opacity="0.15"/>
  <text x="300" y="285" font-family="Georgia, serif" font-size="120" fill="{PALETTE['teal_deep']}"
        text-anchor="middle" opacity="0.9">{esc(initials)}</text>
  <text x="300" y="470" font-family="Helvetica, Arial, sans-serif" font-size="34" fill="{PALETTE['ink']}"
        text-anchor="middle" font-weight="600">{esc(p['name'])}</text>
  <text x="300" y="510" font-family="Helvetica, Arial, sans-serif" font-size="24" fill="{PALETTE['stone']}"
        text-anchor="middle">${p['price']} · {esc(p['category'])}</text>
  <text x="300" y="560" font-family="Georgia, serif" font-size="22" fill="{PALETTE['terracotta']}"
        text-anchor="middle" letter-spacing="3">LUMEN &amp; COAST</text>
</svg>'''


def wrap_text(text, max_chars):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= max_chars:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def hero_svg(product, segment_id, fmt, copy, style_name, tone):
    w, h = FORMAT_DIMS[fmt]
    st = SEGMENT_STYLE[segment_id]
    seg = next(s for s in SEGMENTS if s["id"] == segment_id)
    # scale font to canvas
    base = min(w, h)
    head_size = int(base * 0.072)
    body_size = int(base * 0.040)
    cta_size = int(base * 0.038)
    pad = int(base * 0.07)

    head_lines = wrap_text(copy["headline"], max_chars=max(14, int(w / (head_size * 0.55))))
    body_lines = wrap_text(copy["body"], max_chars=max(20, int(w / (body_size * 0.50))))

    # Layout text in lower portion over a soft scrim
    text_y = int(h * 0.52)
    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{st['bg']}"/><stop offset="1" stop-color="{PALETTE['sand']}"/>
    </linearGradient>
    <linearGradient id="scrim" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{st['bg']}" stop-opacity="0"/>
      <stop offset="1" stop-color="{st['bg']}" stop-opacity="0.55"/>
    </linearGradient>
  </defs>
  <rect width="{w}" height="{h}" fill="url(#bg)"/>
  <circle cx="{int(w*0.78)}" cy="{int(h*0.28)}" r="{int(base*0.30)}" fill="{PALETTE['offwhite']}" opacity="0.20"/>
  <circle cx="{int(w*0.20)}" cy="{int(h*0.18)}" r="{int(base*0.14)}" fill="{st['accent']}" opacity="0.18"/>
  <rect x="0" y="{int(h*0.45)}" width="{w}" height="{int(h*0.55)}" fill="url(#scrim)"/>
  <text x="{pad}" y="{pad+head_size}" font-family="Georgia, serif" font-size="{int(base*0.030)}"
        fill="{st['accent']}" letter-spacing="4" opacity="0.85">LUMEN &amp; COAST</text>''']

    y = text_y
    for ln in head_lines:
        parts.append(f'<text x="{pad}" y="{y}" font-family="Georgia, serif" font-size="{head_size}" '
                     f'fill="{st["accent"]}" font-weight="700">{esc(ln)}</text>')
        y += int(head_size * 1.15)
    y += int(body_size * 0.6)
    for ln in body_lines:
        parts.append(f'<text x="{pad}" y="{y}" font-family="Helvetica, Arial, sans-serif" font-size="{body_size}" '
                     f'fill="{st["accent"]}" opacity="0.92">{esc(ln)}</text>')
        y += int(body_size * 1.35)

    # CTA pill
    cta = copy["cta"]
    cta_w = int(len(cta) * cta_size * 0.62) + pad
    cta_y = y + int(body_size * 0.6)
    parts.append(f'<rect x="{pad}" y="{cta_y}" rx="{int(cta_size*0.9)}" width="{cta_w}" height="{int(cta_size*2.2)}" '
                 f'fill="{PALETTE["terracotta"]}"/>')
    parts.append(f'<text x="{pad + cta_w//2}" y="{cta_y + int(cta_size*1.5)}" font-family="Helvetica, Arial, sans-serif" '
                 f'font-size="{cta_size}" fill="{PALETTE["offwhite"]}" text-anchor="middle" font-weight="600">{esc(cta)}</text>')
    # format/channel tag top-right
    parts.append(f'<text x="{w-pad}" y="{pad+head_size}" font-family="Helvetica, Arial, sans-serif" '
                 f'font-size="{int(base*0.026)}" fill="{st["accent"]}" text-anchor="end" opacity="0.8">'
                 f'{esc(seg["channel"])} · {esc(fmt.replace("_"," "))}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def resolve_copy(product, segment_id, tone):
    key = (product["id"], segment_id)
    if key in CANNED_COPY:
        return CANNED_COPY[key]
    return GENERIC_COPY.get(tone, GENERIC_COPY["minimal"])(product)


def main():
    global SEGMENTS
    with open(os.path.join(DATA_DIR, "catalog.json")) as f:
        catalog = json.load(f)
    with open(os.path.join(DATA_DIR, "segments.json")) as f:
        SEGMENTS = json.load(f)

    os.makedirs(CATALOG_DIR, exist_ok=True)
    os.makedirs(HERO_DIR, exist_ok=True)

    # product cards
    for p in catalog:
        with open(os.path.join(CATALOG_DIR, f"{p['id']}.svg"), "w") as f:
            f.write(product_svg(p))

    # Import the perf model to compute grounded predicted_ctr for the manifest.
    import sys
    sys.path.insert(0, os.path.join(HERE, "..", "backend"))
    from core.perf_model import predict as perf_predict
    from core import data as datamod

    manifest = {}
    # Generate a full grid so ANY product x segment offline click has an image + copy.
    for p in catalog:
        for seg in SEGMENTS:
            sid = seg["id"]
            fmt, style, tone = SEGMENT_FORMAT[sid]
            copy = resolve_copy(p, sid, tone)
            svg = hero_svg(p, sid, fmt, copy, style, tone)
            fname = f"{p['id']}__{sid}.svg"
            with open(os.path.join(HERO_DIR, fname), "w") as f:
                f.write(svg)
            pred = perf_predict(sid, fmt, style, tone)
            manifest[f"{p['id']}__{sid}"] = {
                "product_id": p["id"],
                "segment_id": sid,
                "image_url": f"/data/hero_set/{fname}",
                "format": fmt,
                "image_style": style,
                "copy_tone": tone,
                "copy": copy,
                "predicted_ctr": pred["predicted_ctr"],
                "predicted_ctr_pct": pred["predicted_ctr_pct"],
            }

    with open(os.path.join(HERO_DIR, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Wrote {len(catalog)} product cards + {len(manifest)} hero creatives + manifest.json")


if __name__ == "__main__":
    main()
