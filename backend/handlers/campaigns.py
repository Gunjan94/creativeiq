"""
campaigns.py — serves the historical campaign performance log.

This is the data that GROUNDS the CTR prediction (perf_model.py reads the same
rows). Exposing it makes the prediction auditable: a marketer can see the real
past campaigns the predicted-CTR badge is computed from. Lambda-shaped: a plain
function the local app and an API Gateway proxy can both call.
"""
from core import data


def _ctr_pct(ctr: float) -> str:
    return f"{ctr * 100:.2f}%"


def get_campaigns(limit: int = 60) -> dict:
    """Return recent campaigns (most recent first) + book-level rollups.

    Each row is a real historical campaign from campaign_history.json. We add a
    display CTR and flag the top performers so the UI can highlight what worked —
    the evidence base the predictor stands on.
    """
    history = list(data.campaign_history())
    # Sort most-recent first for a log feel.
    history.sort(key=lambda r: r.get("date", ""), reverse=True)

    if not history:
        return {"campaigns": [], "stats": {}}

    ctrs = [r["ctr"] for r in history]
    # "Top performer" = CTR in the top quartile of the whole book.
    threshold = sorted(ctrs, reverse=True)[max(0, len(ctrs) // 4 - 1)]

    total_impr = sum(r["impressions"] for r in history)
    total_clk = sum(r["clicks"] for r in history)
    book_ctr = (total_clk / total_impr) if total_impr else 0.0

    rows = []
    for r in history[:limit]:
        rows.append({
            "campaign_id": r["campaign_id"],
            "date": r["date"],
            "product_id": r["product_id"],
            "segment_id": r["segment_id"],
            "channel": r["channel"],
            "format": r["format"],
            "image_style": r["image_style"],
            "copy_tone": r["copy_tone"],
            "impressions": r["impressions"],
            "clicks": r["clicks"],
            "ctr": r["ctr"],
            "ctr_pct": _ctr_pct(r["ctr"]),
            "top_performer": r["ctr"] >= threshold,
        })

    return {
        "campaigns": rows,
        "stats": {
            "total_campaigns": len(history),
            "shown": len(rows),
            "book_avg_ctr": round(book_ctr, 4),
            "book_avg_ctr_pct": _ctr_pct(book_ctr),
            "total_impressions": total_impr,
            "total_clicks": total_clk,
            "date_range": f"{history[-1]['date']} → {history[0]['date']}",
        },
    }


# API Gateway / Lambda proxy entrypoint (parity with the other handlers).
def lambda_handler(event, _context=None):
    qs = (event or {}).get("queryStringParameters") or {}
    try:
        limit = int(qs.get("limit", 60))
    except (TypeError, ValueError):
        limit = 60
    return {"statusCode": 200, "body": get_campaigns(limit)}
