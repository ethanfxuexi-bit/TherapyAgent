"""Color heuristics as supplementary signal for mood explanations."""

from collections import Counter

from PIL import Image


def extract_dominant_colors(image: Image.Image, n: int = 3) -> list[str]:
    """Return human-readable dominant color names from an image."""
    small = image.convert("RGB").resize((64, 64))
    pixels = list(small.getdata())

    # Bucket colors into coarse names
    buckets: Counter[str] = Counter()
    for r, g, b in pixels:
        brightness = (r + g + b) / 3
        if brightness > 230:
            buckets["white/light"] += 1
        elif brightness < 40:
            buckets["dark/black"] += 1
        elif r > g + 30 and r > b + 30:
            buckets["red/warm"] += 1
        elif b > r + 20 and b > g + 10:
            buckets["blue/cool"] += 1
        elif g > r + 10 and g > b + 10:
            buckets["green/natural"] += 1
        elif r > 180 and g > 150 and b < 100:
            buckets["yellow/bright"] += 1
        elif r > 150 and g > 100 and b > 150:
            buckets["purple/mixed"] += 1
        elif 100 < brightness < 180:
            buckets["neutral/gray"] += 1
        else:
            buckets["mixed tones"] += 1

    return [name for name, _ in buckets.most_common(n)]


def color_mood_hint(colors: list[str]) -> str:
    """Generate a short color-based supplementary hint."""
    hints: list[str] = []
    color_set = set(colors)
    if "blue/cool" in color_set:
        hints.append("cool blue tones often suggest calm or melancholy")
    if "red/warm" in color_set:
        hints.append("warm red tones can indicate energy or strong emotion")
    if "yellow/bright" in color_set:
        hints.append("bright yellows often appear in uplifting drawings")
    if "dark/black" in color_set:
        hints.append("darker areas may reflect heavier feelings")
    if "green/natural" in color_set:
        hints.append("greens often connect to growth or balance")
    if not hints:
        return "Your color palette adds context to the mood reading."
    return " ".join(hints[:2]).capitalize() + "."
