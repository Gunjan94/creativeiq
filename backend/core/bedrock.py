"""
bedrock.py — Amazon Bedrock calls: Claude (copy, streamed) + Nova Canvas (image).

OFFLINE BY DEFAULT. Real Bedrock only when USE_BEDROCK=1 AND boto3 + AWS creds are present.
When offline (the zero-credentials demo path), the public helpers raise BedrockUnavailable so
callers degrade to the pre-generated hero set (core/cache.py).

Models (BUILDER §2):
  copy  = anthropic.claude-sonnet-4-6  (Bedrock converse / converse_stream)
  image = amazon.nova-canvas-v1:0      (fallback amazon.titan-image-generator-v2:0)
Region default ap-southeast-1; override with AWS_REGION / CREATIVEIQ_REGION.
"""
import base64
import json
import os

USE_BEDROCK = os.environ.get("USE_BEDROCK", "0") == "1"
REGION = os.environ.get("CREATIVEIQ_REGION") or os.environ.get("AWS_REGION") or "ap-southeast-1"

COPY_MODEL = os.environ.get("CREATIVEIQ_COPY_MODEL", "anthropic.claude-sonnet-4-6")
IMAGE_MODEL = os.environ.get("CREATIVEIQ_IMAGE_MODEL", "amazon.nova-canvas-v1:0")
IMAGE_MODEL_FALLBACK = "amazon.titan-image-generator-v2:0"


class BedrockUnavailable(Exception):
    """Raised when Bedrock is disabled or fails — callers fall back to the hero set."""


def available():
    if not USE_BEDROCK:
        return False
    try:
        import boto3  # noqa: F401
    except ImportError:
        return False
    return True


def _client():
    import boto3
    return boto3.client("bedrock-runtime", region_name=REGION)


def stream_copy(system_prompt, user_prompt):
    """
    Yield copy text deltas from Claude via Bedrock converse_stream.
    Raises BedrockUnavailable when offline so the caller can stream cached copy instead.
    """
    if not available():
        raise BedrockUnavailable("USE_BEDROCK!=1 or boto3 missing")
    try:
        client = _client()
        resp = client.converse_stream(
            modelId=COPY_MODEL,
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": user_prompt}]}],
            inferenceConfig={"maxTokens": 400, "temperature": 0.7},
        )
        for event in resp["stream"]:
            if "contentBlockDelta" in event:
                delta = event["contentBlockDelta"]["delta"].get("text", "")
                if delta:
                    yield delta
    except Exception as e:  # noqa: BLE001 — never break the demo path
        raise BedrockUnavailable(f"Claude stream failed: {e}") from e


def generate_copy(system_prompt, user_prompt):
    """Non-streaming convenience — full copy text (joins the stream)."""
    return "".join(stream_copy(system_prompt, user_prompt))


def generate_image(prompt, width, height):
    """
    Generate a PNG via Nova Canvas (Titan fallback). Returns raw PNG bytes.
    Raises BedrockUnavailable when offline.
    """
    if not available():
        raise BedrockUnavailable("USE_BEDROCK!=1 or boto3 missing")
    client = _client()

    # Nova Canvas
    try:
        body = {
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {"text": prompt},
            "imageGenerationConfig": {
                "numberOfImages": 1, "width": width, "height": height,
                "cfgScale": 7.5, "quality": "standard",
            },
        }
        resp = client.invoke_model(modelId=IMAGE_MODEL, body=json.dumps(body))
        payload = json.loads(resp["body"].read())
        return base64.b64decode(payload["images"][0])
    except Exception as nova_err:  # noqa: BLE001
        # Titan fallback
        try:
            body = {
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {"text": prompt},
                "imageGenerationConfig": {
                    "numberOfImages": 1, "width": width, "height": height, "cfgScale": 8.0,
                },
            }
            resp = client.invoke_model(modelId=IMAGE_MODEL_FALLBACK, body=json.dumps(body))
            payload = json.loads(resp["body"].read())
            return base64.b64decode(payload["images"][0])
        except Exception as titan_err:  # noqa: BLE001
            raise BedrockUnavailable(
                f"Image gen failed (Nova: {nova_err}; Titan: {titan_err})"
            ) from titan_err
