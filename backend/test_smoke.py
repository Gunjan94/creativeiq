"""
test_smoke.py — fast offline smoke tests for the CreativeIQ backend (no AWS, no network).
Run:  python -m pytest test_smoke.py   (or)   python test_smoke.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import perf_model, data  # noqa: E402
from handlers import catalog, segments, predict, generate  # noqa: E402


def test_catalog_and_segments():
    assert len(catalog.get_catalog()) == 10
    segs = segments.get_segments()
    assert len(segs) == 4
    for s in segs:
        assert s["n_campaigns"] > 0
        assert s["avg_ctr"] > 0


def test_prediction_is_grounded_and_clamped():
    p = perf_model.predict("genz-instagram", "social_square", "lifestyle", "playful")
    assert p["based_on_n_campaigns"] == 40
    assert 0.002 <= p["predicted_ctr"] <= 0.09
    assert p["confidence"] in ("high", "medium", "low")


def test_inputs_change_output():
    # Same segment, strong vs weak feature combo -> materially different CTR.
    strong = perf_model.predict("genz-instagram", "social_square", "lifestyle", "playful")
    weak = perf_model.predict("genz-instagram", "email_hero", "studio", "benefit-led")
    assert strong["predicted_ctr"] > weak["predicted_ctr"]


def test_segment_switch_changes_format_and_ctr():
    a = generate.generate_summary({"product_id": "linen-resort-shirt", "segment_id": "genz-instagram"})
    b = generate.generate_summary({"product_id": "linen-resort-shirt", "segment_id": "millennials-email"})
    assert a["format"] != b["format"]  # social_square vs email_hero
    assert a["prediction"]["predicted_ctr"] != b["prediction"]["predicted_ctr"]


def test_offline_generate_serves_image():
    # Offline generation now returns a genuinely-generated image (keyless
    # text-to-image), so source is "generated" (or "preview" if the image path
    # is unreachable and it composes over the product photo). Either way the
    # creative has a usable image reference and grounded copy.
    s = generate.generate_summary({"product_id": "linen-resort-shirt", "segment_id": "genz-instagram"})
    assert s["source"] in ("generated", "preview", "cache")
    assert s["image_url"] or s["product_image_url"]
    assert s["copy"]["headline"]


def test_unseeded_combo_falls_back():
    s = generate.generate_summary({"product_id": "knit-polo", "segment_id": "millennials-email"})
    assert s["image_url"] is not None
    assert s["copy"] is not None


def test_sse_event_sequence():
    events = [e["event"] for e in generate.generate_events(
        {"product_id": "straw-tote-bag", "segment_id": "genz-instagram"})]
    assert "meta" in events and "image" in events and "done" in events
    assert events.count("delta") > 0


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} tests passed.")
