"""
copywriter.py — deterministic, segment-aware offline copy generator.

This is the OFFLINE fallback for ad copy (used when live Bedrock is not
credentialed). It is NOT an LLM — it composes on-brand copy from segment-tone
templates and the product's own attributes, so:

  * every (product x segment x format) yields coherent, varied, on-brand copy;
  * it generalises to ANY product — including a photo the user just uploaded —
    so the "generate" action works even for items with no hand-authored entry;
  * changing the segment visibly changes tone, length and CTA (the demo proof
    that the output is conditioned on real inputs, not a static string).

When Bedrock IS credentialed, generate.py uses Claude instead and this module
is bypassed — the framing in the UI is therefore honest: "grounded preview,
net-new copy when the model is live."

Design: templates are keyed by the segment's copy tone (playful / benefit-led /
aspirational / trustworthy). A stable hash over (product, segment, format)
picks one variant deterministically, so the same inputs always reproduce the
same creative (reliable for a recorded demo) while different inputs diverge.
"""
from __future__ import annotations

import hashlib


# A short, human descriptor per category — keeps copy concrete without inventing
# attributes. Falls back to a generic noun for uploaded/unknown products.
_CATEGORY_NOUN = {
    "tops": "shirt",
    "bottoms": "trouser",
    "dresses": "piece",
    "footwear": "pair",
    "bags": "carry",
    "accessories": "finishing touch",
    "swim": "swim short",
}

# CTA phrasing per tone.
_CTAS = {
    "playful": ["Shop the drop", "Get the look", "Cop it now", "Add to cart"],
    "benefit-led": ["Discover the piece", "Shop the edit", "See the details", "Shop now"],
    "aspirational": ["Explore the edit", "Discover the look", "Shop the collection", "View the piece"],
    "trustworthy": ["Shop now", "See the quality", "Discover more", "View details"],
}

# Headline + body templates per tone. {name}=product name, {noun}=category noun.
# Multiple variants per tone so output varies across products/formats.
_TEMPLATES = {
    "playful": [
        ("Sun's out, {noun}'s on \u2600\ufe0f", "Your new everyday flex. Breezy, easy, done."),
        ("This is your summer {noun}", "Lightweight, effortless, made for the feed."),
        ("Warm-weather, sorted", "Meet the {name}. Pack it, wear it, live in it."),
    ],
    "benefit-led": [
        ("The {name} you'll live in all summer", "Effortless from beach to dinner \u2014 and built to last seasons, not weeks."),
        ("One {noun}, every warm day ahead", "Quality you can feel, comfort you'll reach for first."),
        ("Made for the way you actually dress", "The {name}: easy to wear, easy to love, easy to keep."),
    ],
    "aspirational": [
        ("Off-duty, perfectly put together", "The weekend uniform: relaxed lines, quiet confidence."),
        ("Slow mornings, golden light", "The {name} \u2014 for the days worth dressing for."),
        ("Understated. Unmistakable.", "Elevated resort essentials, designed to be remembered."),
    ],
    "trustworthy": [
        ("Premium fabric. Made to last.", "The {name}: timeless cut, considered detail, real quality."),
        ("Quality you can see and feel", "Crafted to last beyond the season \u2014 the {name}."),
        ("The essential, done right", "Honest materials, a fit that works, a price that makes sense."),
    ],
}

# Subject lines & preheaders for the email format (richer than social).
_EMAIL = {
    "playful": ("\u2600\ufe0f Your summer {noun} just landed", "Limited drop \u2014 move quick before it's gone."),
    "benefit-led": ("The {name}, ready when you are", "Free returns. Made to last. Loved on arrival."),
    "aspirational": ("An invitation to slow down", "The resort edit you'll reach for all season."),
    "trustworthy": ("Quality that earns its place", "Considered design, honest materials, fair pricing."),
}


def _tone_key(segment: dict) -> str:
    tone = (segment.get("tone") or "").lower()
    if "playful" in tone or "trend" in tone:
        return "playful"
    if "aspirational" in tone or "benefit" in tone:
        return "benefit-led"
    if "polished" in tone or "lifestyle" in tone:
        return "aspirational"
    return "trustworthy"


def _pick(seq, seed: str):
    h = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
    return seq[h % len(seq)]


def _noun(category: str) -> str:
    return _CATEGORY_NOUN.get((category or "").lower(), "piece")


def write_copy(product: dict, segment: dict, fmt: str, tone_hint: str | None = None) -> dict:
    """Compose on-brand {headline, body, cta} for product x segment x format.

    `product` only needs `name` and (optionally) `category` — so an uploaded
    item described as {"name": "...", "category": "..."} works the same as a
    catalog product.
    """
    name = product.get("name", "this piece")
    noun = _noun(product.get("category", ""))
    tone = tone_hint or _tone_key(segment)
    if tone not in _TEMPLATES:
        tone = "benefit-led"

    seed = f"{product.get('id', name)}|{segment.get('id','')}|{fmt}"

    # Email gets a subject + preheader shape; everything else gets headline+body.
    if fmt == "email_hero":
        subj, pre = _EMAIL[tone]
        headline = subj.format(name=name, noun=noun)
        body = pre.format(name=name, noun=noun)
    else:
        h, b = _pick(_TEMPLATES[tone], seed)
        headline = h.format(name=name, noun=noun)
        body = b.format(name=name, noun=noun)
        # Banners stay terse — clip the body to one short clause.
        if fmt == "display_banner":
            body = body.split(".")[0].split("\u2014")[0].strip() + "."

    cta = _pick(_CTAS[tone], seed + "|cta")
    return {"headline": headline, "body": body, "cta": cta}
