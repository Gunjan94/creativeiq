"""data.py — load synthetic datasets (catalog, segments, campaign history, hero manifest)."""
import json
import os
import functools

# data/ lives at repo root; backend/ is a sibling.
_HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("CREATIVEIQ_DATA_DIR", os.path.join(_HERE, "..", "..", "data"))


def _load(name):
    with open(os.path.join(DATA_DIR, name)) as f:
        return json.load(f)


@functools.lru_cache(maxsize=1)
def catalog():
    return _load("catalog.json")


@functools.lru_cache(maxsize=1)
def segments():
    return _load("segments.json")


@functools.lru_cache(maxsize=1)
def campaign_history():
    return _load("campaign_history.json")


@functools.lru_cache(maxsize=1)
def hero_manifest():
    path = os.path.join(DATA_DIR, "hero_set", "manifest.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def get_product(product_id):
    return next((p for p in catalog() if p["id"] == product_id), None)


def get_segment(segment_id):
    return next((s for s in segments() if s["id"] == segment_id), None)
