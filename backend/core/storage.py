"""storage.py — persist live-generated images.

Local mode: write PNG under data/generated/ and return a path the frontend can fetch.
Cloud mode (later): swap this for S3 put_object + return the object URL.
"""
import os
import time
from . import data

GEN_DIR = os.path.join(data.DATA_DIR, "generated")


def save_image(product_id, segment_id, png_bytes):
    os.makedirs(GEN_DIR, exist_ok=True)
    fname = f"{product_id}__{segment_id}__{int(time.time()*1000)}.png"
    with open(os.path.join(GEN_DIR, fname), "wb") as f:
        f.write(png_bytes)
    return f"/data/generated/{fname}"
