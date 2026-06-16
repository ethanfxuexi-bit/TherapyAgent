from __future__ import annotations

import logging
import random

from PIL import Image

from app.models.schemas import AnalysisDetails, MoodName, MoodScores
from app.services.analyzer.base import AnalyzerResult, MoodAnalyzer
from app.services.analyzer.color_heuristics import color_mood_hint, extract_dominant_colors

logger = logging.getLogger(__name__)

MOOD_PROMPTS: dict[MoodName, list[str]] = {
    "Happy": [
        "a joyful colorful drawing with smiles and sunshine",
        "a cheerful bright artwork expressing happiness",
        "a playful happy sketch with warm colors",
    ],
    "Sad": [
        "a melancholic drawing with tears and rain",
        "a somber gray artwork expressing sadness",
        "a lonely figure in a sad emotional sketch",
    ],
    "Calm": [
        "a peaceful serene drawing with soft waves",
        "a tranquil calm artwork with gentle lines",
        "a relaxing meditative sketch in muted tones",
    ],
    "Angry": [
        "an aggressive drawing with sharp jagged lines",
        "a furious red artwork expressing anger",
        "a chaotic angry sketch with intense strokes",
    ],
    "Anxious": [
        "a nervous scribbled drawing with tension",
        "an anxious artwork with swirling chaotic lines",
        "a worried unsettling sketch with dark edges",
    ],
    "Excited": [
        "an energetic vibrant drawing full of motion",
        "an excited colorful artwork with exclamation",
        "a dynamic enthusiastic sketch with bold strokes",
    ],
}


class MockMoodAnalyzer(MoodAnalyzer):
    """Deterministic-enough mock for tests and CI."""

    def __init__(self) -> None:
        self._ready = False

    def warmup(self) -> None:
        self._ready = True
        logger.info("Mock analyzer warmed up")

    def is_ready(self) -> bool:
        return self._ready

    def get_device(self) -> str:
        return "mock"

    def get_model_name(self) -> str:
        return "mock-v1"

    def analyze(self, image: Image.Image) -> AnalyzerResult:
        colors = extract_dominant_colors(image)
        # Seed from image hash for reproducibility in tests
        seed = sum(image.getdata()[0]) if image.size[0] > 0 else 42
        rng = random.Random(seed)
        raw = {mood: rng.random() for mood in MOOD_PROMPTS}
        total = sum(raw.values())
        scores_dict = {mood: v / total for mood, v in raw.items()}
        top_mood = max(scores_dict, key=scores_dict.get)  # type: ignore[arg-type]
        confidence = scores_dict[top_mood]

        return AnalyzerResult(
            mood=top_mood,  # type: ignore[arg-type]
            confidence=confidence,
            scores=MoodScores(**scores_dict),
            analysis_details=AnalysisDetails(
                method="mock_softmax",
                model="mock-v1",
                device="mock",
                explanation=f"Mock analysis suggests {top_mood.lower()} themes. {color_mood_hint(colors)}",
                dominant_colors=colors,
                top_prompts=MOOD_PROMPTS[top_mood][:2],  # type: ignore[index]
            ),
        )
