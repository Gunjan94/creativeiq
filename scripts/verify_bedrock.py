#!/usr/bin/env python3
"""
verify_bedrock.py — Day-1 model-access check (BUILDER §10).

Invokes the copy model (anthropic.claude-sonnet-4-6) and the image model
(amazon.nova-canvas-v1:0) in the target region. If image access is gated, re-run with
--region us-east-1 and use that region everywhere.

Usage:
  USE_BEDROCK=1 python scripts/verify_bedrock.py --region ap-southeast-1
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "backend"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="ap-southeast-1")
    args = ap.parse_args()

    os.environ["USE_BEDROCK"] = "1"
    os.environ["CREATIVEIQ_REGION"] = args.region

    # reload module config with the chosen region
    from importlib import reload
    from core import bedrock
    reload(bedrock)

    print(f"Region: {args.region}")
    if not bedrock.available():
        print("FAIL: Bedrock not available (set USE_BEDROCK=1 and install boto3 + AWS creds).")
        sys.exit(1)

    print(f"Copy model:  {bedrock.COPY_MODEL}")
    print(f"Image model: {bedrock.IMAGE_MODEL} (fallback {bedrock.IMAGE_MODEL_FALLBACK})")

    ok = True
    try:
        text = bedrock.generate_copy(
            "You write JSON only.",
            'Return {"headline":"hello","body":"world","cta":"go"} exactly.')
        print(f"  TEXT OK -> {text[:80]!r}")
    except Exception as e:  # noqa: BLE001
        print(f"  TEXT FAIL -> {e}")
        ok = False

    try:
        png = bedrock.generate_image("a calm coastal scene, sand and muted teal", 1024, 1024)
        print(f"  IMAGE OK -> {len(png)} bytes")
    except Exception as e:  # noqa: BLE001
        print(f"  IMAGE FAIL -> {e}")
        print("  If AccessDenied on the image model, request access in the Bedrock console,")
        print("  or re-run: python scripts/verify_bedrock.py --region us-east-1")
        ok = False

    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
