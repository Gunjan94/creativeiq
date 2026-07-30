"""
analytics.py — aggregate views over campaign_history.json for the rich
Campaigns analytics (segment x format CTR heatmap) and the CTR-transparency
drill-down (the comparable campaigns a prediction is grounded in).

Same source rows as perf_model.py, so the analytics and the predictions always
tell one story. Lambda-shaped plain functions.
"""
from core import data, perf_model

FORMATS = ["social_square", "story", "email_hero", "display_banner"]


def _weighted_ctr(rows):
    imp = sum(r["impressions"] for r in rows)
    clk = sum(r["clicks"] for r in rows)
    return (clk / imp) if imp else 0.0


def get_analytics() -> dict:
    """Segment x format CTR matrix + book rollups for the analytics heatmap."""
    history = data.campaign_history()
    segments = data.segments()

    formats_present = [f for f in FORMATS if any(r["format"] == f for r in history)]
    book_ctr = _weighted_ctr(history)

    matrix = []
    for seg in segments:
        sid = seg["id"]
        seg_rows = [r for r in history if r["segment_id"] == sid]
        cells = []
        for fmt in formats_present:
            cell_rows = [r for r in seg_rows if r["format"] == fmt]
            cells.append({
                "format": fmt,
                "n": len(cell_rows),
                "ctr": round(_weighted_ctr(cell_rows), 4) if cell_rows else None,
                "ctr_pct": f"{_weighted_ctr(cell_rows) * 100:.2f}%" if cell_rows else "—",
            })
        matrix.append({
            "segment_id": sid,
            "segment_name": seg["name"],
            "channel": seg["channel"],
            "segment_ctr": round(_weighted_ctr(seg_rows), 4),
            "segment_ctr_pct": f"{_weighted_ctr(seg_rows) * 100:.2f}%",
            "n": len(seg_rows),
            "cells": cells,
        })

    # Best segment x format combo (highest CTR with enough rows).
    best = None
    for row in matrix:
        for c in row["cells"]:
            if c["ctr"] is not None and c["n"] >= 3:
                if best is None or c["ctr"] > best["ctr"]:
                    best = {"segment_name": row["segment_name"], "format": c["format"],
                            "ctr_pct": c["ctr_pct"], "ctr": c["ctr"]}

    return {
        "formats": formats_present,
        "matrix": matrix,
        "book_avg_ctr": round(book_ctr, 4),
        "book_avg_ctr_pct": f"{book_ctr * 100:.2f}%",
        "total_campaigns": len(history),
        "best_combo": best,
    }


def get_comparable(segment_id: str, format=None, image_style=None, copy_tone=None, limit: int = 12) -> dict:
    """The real historical campaigns a prediction is grounded in.

    Filters to the segment, then (when provided) the same format / image_style /
    copy_tone. Returns the matching rows (highest CTR first) + their weighted CTR,
    so the predicted-CTR badge is auditable: 'here are the campaigns behind it.'
    """
    history = data.campaign_history()
    seg_rows = [r for r in history if r["segment_id"] == segment_id]

    matched = seg_rows
    applied = []
    if format:
        matched = [r for r in matched if r["format"] == format]
        applied.append(("format", format))
    if image_style:
        m2 = [r for r in matched if r["image_style"] == image_style]
        if m2:
            matched = m2
            applied.append(("image_style", image_style))
    if copy_tone:
        m3 = [r for r in matched if r["copy_tone"] == copy_tone]
        if m3:
            matched = m3
            applied.append(("copy_tone", copy_tone))

    matched = sorted(matched, key=lambda r: r["ctr"], reverse=True)
    rows = [{
        "campaign_id": r["campaign_id"],
        "date": r["date"],
        "product_id": r["product_id"],
        "format": r["format"],
        "image_style": r["image_style"],
        "copy_tone": r["copy_tone"],
        "impressions": r["impressions"],
        "ctr": r["ctr"],
        "ctr_pct": f"{r['ctr'] * 100:.2f}%",
    } for r in matched[:limit]]

    return {
        "segment_id": segment_id,
        "matched_count": len(matched),
        "segment_count": len(seg_rows),
        "avg_ctr_pct": f"{_weighted_ctr(matched) * 100:.2f}%" if matched else "—",
        "filters_applied": [{"field": f, "value": v} for f, v in applied],
        "campaigns": rows,
    }
