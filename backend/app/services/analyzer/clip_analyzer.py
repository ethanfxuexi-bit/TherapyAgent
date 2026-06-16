from __future__ import annotations

import logging
from typing import Any

import torch
from PIL import Image

from app.config import Settings
from app.models.schemas import AnalysisDetails, MoodName, MoodScores
from app.services.analyzer.base import AnalyzerResult, MoodAnalyzer
from app.services.analyzer.color_heuristics import color_mood_hint, extract_dominant_colors
from app.services.analyzer.mock_analyzer import MOOD_PROMPTS

logger = logging.getLogger(__name__)


def _get_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _softmax(scores: dict[str, float], temperature: float) -> dict[str, float]:
    import math

    scaled = {k: v / temperature for k, v in scores.items()}
    max_val = max(scaled.values())
    exp_vals = {k: math.exp(v - max_val) for k, v in scaled.items()}
    total = sum(exp_vals.values())
    return {k: v / total for k, v in exp_vals.items()}


def _build_explanation(mood: MoodName, colors: list[str], top_prompts: list[str]) -> str:
    mood_lower = mood.lower()
    prompt_hint = top_prompts[0] if top_prompts else ""
    base = f"Your drawing most closely matched {mood_lower}, peaceful imagery"
    if mood == "Calm":
        base = f"Your drawing most closely matched calm, peaceful imagery"
    elif mood == "Happy":
        base = "Your drawing most closely matched joyful, uplifting imagery"
    elif mood == "Sad":
        base = "Your drawing most closely matched melancholic, somber imagery"
    elif mood == "Angry":
        base = "Your drawing most closely matched intense, aggressive imagery"
    elif mood == "Anxious":
        base = "Your drawing most closely matched tense, unsettled imagery"
    elif mood == "Excited":
        base = "Your drawing most closely matched energetic, vibrant imagery"

    color_hint = color_mood_hint(colors)
    return f"{base}. {color_hint}"


class CLIPMoodAnalyzer(MoodAnalyzer):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._model: Any = None
        self._preprocess: Any = None
        self._device = _get_device()
        self._ready = False
        self._model_name = settings.clip_model

    def warmup(self) -> None:
        if self._ready:
            return
        logger.info("Loading CLIP model %s on %s", self._model_name, self._device)
        import clip

        self._model, self._preprocess = clip.load(self._model_name, device=self._device)
        self._model.eval()
        self._ready = True
        logger.info("CLIP model ready on %s", self._device)

    def is_ready(self) -> bool:
        return self._ready

    def get_device(self) -> str:
        return self._device

    def get_model_name(self) -> str:
        return self._model_name

    def analyze(self, image: Image.Image) -> AnalyzerResult:
        if not self._ready:
            raise RuntimeError("Analyzer not warmed up")

        import clip

        image_rgb = image.convert("RGB")
        colors = extract_dominant_colors(image_rgb)

        # Flatten all prompts with mood labels
        all_prompts: list[str] = []
        prompt_to_mood: list[MoodName] = []
        for mood, prompts in MOOD_PROMPTS.items():
            for p in prompts:
                all_prompts.append(p)
                prompt_to_mood.append(mood)  # type: ignore[arg-type]

        image_input = self._preprocess(image_rgb).unsqueeze(0).to(self._device)
        text_tokens = clip.tokenize(all_prompts).to(self._device)

        with torch.no_grad():
            image_features = self._model.encode_image(image_input)
            text_features = self._model.encode_text(text_tokens)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            similarities = (image_features @ text_features.T).squeeze(0).cpu().tolist()

        # Aggregate per mood (max similarity per mood group)
        mood_raw: dict[str, float] = {m: 0.0 for m in MOOD_PROMPTS}
        mood_best_prompt: dict[str, str] = {}
        for sim, mood, prompt in zip(similarities, prompt_to_mood, all_prompts):
            if sim > mood_raw[mood]:
                mood_raw[mood] = sim
                mood_best_prompt[mood] = prompt

        probs = _softmax(mood_raw, self._settings.clip_temperature)
        top_mood = max(probs, key=probs.get)  # type: ignore[arg-type]
        confidence = probs[top_mood]
        top_prompts = [mood_best_prompt[top_mood]]

        return AnalyzerResult(
            mood=top_mood,  # type: ignore[arg-type]
            confidence=confidence,
            scores=MoodScores(**probs),
            analysis_details=AnalysisDetails(
                method="clip_softmax",
                model=self._model_name,
                device=self._device,
                explanation=_build_explanation(top_mood, colors, top_prompts),  # type: ignore[arg-type]
                dominant_colors=colors,
                top_prompts=top_prompts,
            ),
        )
