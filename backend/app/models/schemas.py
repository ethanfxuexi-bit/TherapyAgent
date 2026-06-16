from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

MOOD_CATEGORIES = ["Happy", "Sad", "Calm", "Angry", "Anxious", "Excited"]
MoodName = Literal["Happy", "Sad", "Calm", "Angry", "Anxious", "Excited"]


class MoodScores(BaseModel):
    Happy: float = 0.0
    Sad: float = 0.0
    Calm: float = 0.0
    Angry: float = 0.0
    Anxious: float = 0.0
    Excited: float = 0.0


class AnalysisDetails(BaseModel):
    method: str
    model: str
    device: str
    explanation: str
    dominant_colors: list[str] | None = None
    top_prompts: list[str] | None = None


class MoodPrediction(BaseModel):
    mood: MoodName
    confidence: float = Field(ge=0.0, le=1.0)
    scores: MoodScores
    analysis_details: AnalysisDetails
    history_id: str | None = None


class HistoryEntry(BaseModel):
    id: str
    user_id: str
    timestamp: datetime
    mood: MoodName
    confidence: float
    scores: MoodScores
    thumbnail_url: str | None = None
    notes: str | None = None
    analysis_details: AnalysisDetails | None = None


class HistoryListResponse(BaseModel):
    items: list[HistoryEntry]
    total: int
    limit: int
    offset: int


class RewardsStatus(BaseModel):
    coins: int
    streak: int
    last_earned: datetime | None = None
    can_claim_today: bool


class HealthResponse(BaseModel):
    status: str
    analyzer_ready: bool
    analyzer_device: str | None = None
    analyzer_model: str | None = None
