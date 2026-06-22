"""predict.py — POST /predict. Transparent feature model over campaign_history.json. No LLM."""
from core import perf_model
from core import data


def predict(body):
    segment_id = body["segment_id"]
    fmt = body.get("format")
    image_style = body.get("image_style")
    copy_tone = body.get("copy_tone")

    # If style/tone/format omitted, use the segment's data-informed best picks.
    if not (fmt and image_style and copy_tone):
        best = perf_model.best_features_for_segment(segment_id)
        fmt = fmt or best["format"]
        image_style = image_style or best["image_style"]
        copy_tone = copy_tone or best["copy_tone"]

    result = perf_model.predict(segment_id, fmt, image_style, copy_tone)
    result["inputs"] = {"segment_id": segment_id, "format": fmt,
                        "image_style": image_style, "copy_tone": copy_tone}
    return result


def lambda_handler(event, context):
    import json
    body = json.loads(event.get("body") or "{}")
    return {"statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps(predict(body))}
