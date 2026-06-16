from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from PIL import Image

from app.models.schemas import AnalysisDetails, MoodName, MoodScores


@dataclass
class AnalyzerResult:
    mood: MoodName
    confidence: float
    scores: MoodScores
    analysis_details: AnalysisDetails


class MoodAnalyzer(ABC):
    @abstractmethod
    def warmup(self) -> None:
        """Load model weights and prepare for inference."""

    @abstractmethod
    def is_ready(self) -> bool:
        """Return True when the analyzer can accept requests."""

    @abstractmethod
    def get_device(self) -> str:
        """Return the compute device in use (cpu, cuda, mps)."""

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model identifier."""

    @abstractmethod
    def analyze(self, image: Image.Image) -> AnalyzerResult:
        """Analyze an image and return mood prediction."""
