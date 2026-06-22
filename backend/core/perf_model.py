"""
perf_model.py — transparent, feature-based CTR predictor over campaign_history.json.

NOT an LLM. Deterministic aggregate over real historical rows, per BUILDER §6:

  predict(segment_id, format, image_style, copy_tone):
    S = history rows for segment_id
    segment_avg_ctr = impression-weighted mean CTR over S
    f_format = mean_ctr(S where format=...) / segment_avg_ctr   (1.0 if <3 rows)
    f_style  = mean_ctr(S where image_style=...) / segment_avg_ctr
    f_tone   = mean_ctr(S where copy_tone=...) / segment_avg_ctr
    predicted_ctr = segment_avg_ctr * f_format * f_style * f_tone, clamped 0.2%..9%
    confidence = high if all 3 slices >=3 rows, else medium/low
    lift = predicted_ctr / segment_avg_ctr - 1

This grounding is the "not invented" proof: changing inputs changes the slice -> changes output.
"""
from . import data

CTR_MIN = 0.002
CTR_MAX = 0.09
MIN_ROWS_FOR_FACTOR = 3


def _weighted_ctr(rows):
    imp = sum(r["impressions"] for r in rows)
    clk = sum(r["clicks"] for r in rows)
    return (clk / imp) if imp else 0.0


def _factor(seg_rows, field, value, seg_avg):
    sub = [r for r in seg_rows if r.get(field) == value]
    if len(sub) < MIN_ROWS_FOR_FACTOR or seg_avg <= 0:
        return 1.0, len(sub), False  # insufficient evidence -> no adjustment
    return (_weighted_ctr(sub) / seg_avg), len(sub), True


def predict(segment_id, format, image_style, copy_tone):
    history = data.campaign_history()
    seg_rows = [r for r in history if r["segment_id"] == segment_id]
    n_segment = len(seg_rows)

    if n_segment == 0:
        # No history for this segment — return a neutral, honest result.
        return {
            "predicted_ctr": round(CTR_MIN, 4),
            "predicted_ctr_pct": f"{CTR_MIN*100:.1f}%",
            "confidence": "low",
            "based_on_n_campaigns": 0,
            "segment_avg_ctr": 0.0,
            "segment_avg_ctr_pct": "0.0%",
            "lift_vs_segment_avg_pct": "+0%",
            "factors": {},
        }

    seg_avg = _weighted_ctr(seg_rows)
    f_format, n_fmt, ok_fmt = _factor(seg_rows, "format", format, seg_avg)
    f_style, n_sty, ok_sty = _factor(seg_rows, "image_style", image_style, seg_avg)
    f_tone, n_tone, ok_tone = _factor(seg_rows, "copy_tone", copy_tone, seg_avg)

    predicted = seg_avg * f_format * f_style * f_tone
    predicted = max(CTR_MIN, min(CTR_MAX, predicted))

    ok_count = sum([ok_fmt, ok_sty, ok_tone])
    confidence = "high" if ok_count == 3 else ("medium" if ok_count == 2 else "low")

    lift = (predicted / seg_avg - 1.0) if seg_avg else 0.0

    return {
        "predicted_ctr": round(predicted, 4),
        "predicted_ctr_pct": f"{predicted*100:.1f}%",
        "confidence": confidence,
        "based_on_n_campaigns": n_segment,
        "segment_avg_ctr": round(seg_avg, 4),
        "segment_avg_ctr_pct": f"{seg_avg*100:.1f}%",
        "lift_vs_segment_avg_pct": f"{'+' if lift >= 0 else ''}{round(lift*100)}%",
        "factors": {
            "format": {"value": format, "factor": round(f_format, 3), "n": n_fmt},
            "image_style": {"value": image_style, "factor": round(f_style, 3), "n": n_sty},
            "copy_tone": {"value": copy_tone, "factor": round(f_tone, 3), "n": n_tone},
        },
    }


def best_features_for_segment(segment_id):
    """
    Mine the segment's historically best-performing format / image_style / copy_tone.
    Used by /generate to make the creative data-informed. Returns the single best value
    of each feature (by impression-weighted CTR, requiring >=MIN_ROWS_FOR_FACTOR rows).

    Format is additionally constrained to be channel-appropriate (an Email segment
    should never be handed a 'social_square' Instagram layout, etc.) — the pick is
    still the best *valid* format by real CTR, so the choice stays data-informed.
    """
    history = data.campaign_history()
    seg_rows = [r for r in history if r["segment_id"] == segment_id]

    def best(field, fallback, allowed=None):
        groups = {}
        for r in seg_rows:
            groups.setdefault(r[field], []).append(r)
        ranked = [(v, _weighted_ctr(rs), len(rs)) for v, rs in groups.items()
                  if len(rs) >= MIN_ROWS_FOR_FACTOR and (allowed is None or v in allowed)]
        if not ranked:
            return fallback
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked[0][0]

    seg = data.get_segment(segment_id)
    fallback_fmt = seg["top_format"] if seg else "social_square"
    # Channel-appropriate formats — keeps the layout consistent with where the ad runs.
    channel = (seg or {}).get("channel", "").lower()
    allowed_formats = {
        "instagram": {"social_square", "story"},
        "email": {"email_hero"},
        "display": {"display_banner", "social_square"},
        "facebook": {"social_square", "story", "display_banner"},
    }.get(channel)
    return {
        "format": best("format", fallback_fmt, allowed_formats),
        "image_style": best("image_style", "lifestyle"),
        "copy_tone": best("copy_tone", "benefit-led"),
    }


def segment_stats(segment_id):
    """avg_ctr + top_format for /segments enrichment."""
    history = data.campaign_history()
    seg_rows = [r for r in history if r["segment_id"] == segment_id]
    if not seg_rows:
        return {"avg_ctr": 0.0, "avg_ctr_pct": "0.0%", "top_format": None, "n_campaigns": 0}
    avg = _weighted_ctr(seg_rows)
    best = best_features_for_segment(segment_id)
    return {
        "avg_ctr": round(avg, 4),
        "avg_ctr_pct": f"{avg*100:.1f}%",
        "top_format": best["format"],
        "n_campaigns": len(seg_rows),
    }
