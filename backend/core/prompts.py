"""prompts.py — brand tokens + segment-conditioned prompt builders (BUILDER §5)."""

BRAND = {
    "name": "Lumen & Coast",
    "palette": "coastal neutrals — sand, off-white, muted teal, terracotta accent",
    "voice": "confident, warm, effortless; never salesy or hype-y",
    "imagery": "natural light, real fabric texture, relaxed resort lifestyle, minimal props",
    "avoid": "neon, heavy filters, stock-photo stiffness, cluttered backgrounds",
}

# Aspect ratio per format (Nova Canvas allowed dims).
FORMAT_DIMS = {
    "social_square": (1024, 1024),
    "email_hero": (1280, 720),
    "display_banner": (1232, 624),  # nearest Nova-legal to 1200x628
    "story": (720, 1280),
}

FORMAT_GUIDANCE = {
    "social_square": "social_square = <=12-word headline + 1 short line",
    "email_hero": "email_hero = subject line + preheader + 2-sentence body",
    "display_banner": "display_banner = <=8-word headline + 1 punchy value line",
    "story": "story = vertical, <=8-word headline + 1 short line",
}


def copy_system_prompt():
    return (
        f"You write on-brand ad copy for {BRAND['name']}. "
        f"Brand voice: {BRAND['voice']}. "
        "Never invent product attributes not in the description. "
        "Output ONLY valid minified JSON with keys headline, body, cta. "
        "Calibrate length and tone to the channel and format."
    )


def copy_user_prompt(product, segment, fmt, top_tone):
    return (
        f"Product: {product['name']} — {product['description']} "
        f"Tags: {', '.join(product.get('tags', []))}. "
        f"Target segment: {segment['name']} ({segment['age_band']}) on {segment['channel']}. "
        f"Desired tone: {segment['tone']}. "
        f"Format: {fmt} ({FORMAT_GUIDANCE.get(fmt, '')}). "
        f"Top-performing copy tone for this segment historically: {top_tone}. "
        "Respond with JSON {headline, body, cta} only."
    )


def image_prompt(product, segment, top_image_style, fmt):
    return (
        f"{BRAND['imagery']}. {product['name']}, {product['description']} "
        f"Style: {top_image_style} suited to {segment['name']} on {segment['channel']}. "
        f"Palette: {BRAND['palette']}. "
        f"Composition for {fmt} aspect ratio. "
        f"Avoid: {BRAND['avoid']}."
    )


def brand_tokens_applied(segment):
    voice = "playful" if "playful" in segment.get("tone", "") else (
        "aspirational" if "aspirational" in segment.get("tone", "") else "polished")
    return ["palette:coastal", f"voice:{voice}"]
