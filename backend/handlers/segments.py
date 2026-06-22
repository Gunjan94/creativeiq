"""segments.py — GET /segments. Enriches each segment with avg_ctr + top_format from history."""
from core import data
from core import perf_model


def get_segments():
    out = []
    for s in data.segments():
        stats = perf_model.segment_stats(s["id"])
        out.append({**s, **stats})
    return out


def lambda_handler(event, context):
    import json
    return {"statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps(get_segments())}
