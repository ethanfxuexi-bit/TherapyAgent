from __future__ import annotations

import logging

from app.config import Settings, get_settings
from app.services.analyzer.base import MoodAnalyzer
from app.services.analyzer.mock_analyzer import MockMoodAnalyzer

logger = logging.getLogger(__name__)

_analyzer: MoodAnalyzer | None = None


def create_analyzer(settings: Settings | None = None) -> MoodAnalyzer:
    settings = settings or get_settings()
    if settings.analyzer_type == "mock":
        return MockMoodAnalyzer()
    from app.services.analyzer.clip_analyzer import CLIPMoodAnalyzer

    return CLIPMoodAnalyzer(settings)


def get_analyzer() -> MoodAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = create_analyzer()
    return _analyzer


def reset_analyzer() -> None:
    """Reset singleton — used in tests."""
    global _analyzer
    _analyzer = None
