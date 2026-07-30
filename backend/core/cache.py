"""cache.py — hero-set cache lookup + fallback (BUILDER §7).

Cache key = f"{product_id}__{segment_id}". Falls back to nearest-product within the
same segment so even an unseeded combo yields a coherent, on-brand image.
"""
from . import data


def key(product_id, segment_id):
    return f"{product_id}__{segment_id}"


def get(product_id, segment_id):
    """Exact hero creative for this product x segment, or None."""
    return data.hero_manifest().get(key(product_id, segment_id))


def get_with_fallback(product_id, segment_id):
    """
    Exact hit if present; otherwise nearest creative in the SAME segment
    (keeps the format/styling segment-appropriate). Returns (entry, exact: bool) or (None, False).
    """
    exact = get(product_id, segment_id)
    if exact:
        return exact, True
    manifest = data.hero_manifest()
    for k, v in manifest.items():
        if v.get("segment_id") == segment_id:
            return v, False
    # last resort: any entry
    if manifest:
        return next(iter(manifest.values())), False
    return None, False
