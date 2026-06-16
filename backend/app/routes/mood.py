from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.middleware.auth import AuthenticatedUser, get_current_user
from app.models.schemas import MOOD_CATEGORIES, HistoryEntry, HistoryListResponse, MoodPrediction, RewardsStatus
from app.services.analyzer.factory import get_analyzer, get_analyzer_readiness
from app.services.firebase import get_history_repository, get_rewards_repository
from app.services.image_validation import validate_image_upload
from app.services.storage import encode_thumbnail

router = APIRouter(tags=["mood"])

limiter = Limiter(key_func=get_remote_address)


def _user_limit_key(request):
    user = request.state.user_id if hasattr(request.state, "user_id") else get_remote_address(request)
    return str(user)


@router.get("/ping")
async def ping():
    return {"message": "pong"}


@router.get("/health")
async def health():
    readiness = get_analyzer_readiness()
    return {
        "status": "ok",
        "analyzer_ready": readiness["ready"],
        "analyzer_device": readiness["device"],
        "analyzer_model": readiness["model"],
    }


@router.post("/warmup")
async def warmup():
    analyzer = get_analyzer()
    if not analyzer.is_ready():
        analyzer.warmup()
    return {
        "status": "ready",
        "device": analyzer.get_device(),
        "model": analyzer.get_model_name(),
    }


@router.get("/moods")
async def get_moods():
    return {"moods": MOOD_CATEGORIES}


@router.post("/predict", response_model=MoodPrediction)
@limiter.limit("30/hour", key_func=_user_limit_key)
async def predict(
    request: Request,
    file: UploadFile = File(...),
    notes: str | None = Form(None),
    user: AuthenticatedUser = Depends(get_current_user),
):
    request.state.user_id = user.uid

    if not get_analyzer().is_ready():
        get_analyzer().warmup()

    content, image = await validate_image_upload(file)
    result = get_analyzer().analyze(image)

    thumbnail_b64 = encode_thumbnail(content)
    entry = await get_history_repository().create(
        user_id=user.uid,
        mood=result.mood,
        confidence=result.confidence,
        scores=result.scores,
        analysis_details=result.analysis_details,
        thumbnail_b64=thumbnail_b64,
        notes=notes,
    )

    # Auto-claim daily reward on first analysis of the day
    await get_rewards_repository().claim_daily(user.uid)

    return MoodPrediction(
        mood=result.mood,
        confidence=result.confidence,
        scores=result.scores,
        analysis_details=result.analysis_details,
        history_id=entry.id,
    )


@router.get("/history", response_model=HistoryListResponse)
async def list_history(
    user: AuthenticatedUser = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    mood: str | None = Query(None),
    from_date: datetime | None = Query(None, alias="from"),
    to_date: datetime | None = Query(None, alias="to"),
):
    if mood and mood not in MOOD_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid mood filter. Must be one of: {MOOD_CATEGORIES}")

    items, total = await get_history_repository().list(
        user_id=user.uid,
        limit=limit,
        offset=offset,
        mood=mood,  # type: ignore[arg-type]
        from_date=from_date,
        to_date=to_date,
    )
    return HistoryListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/history/{entry_id}", response_model=HistoryEntry)
async def get_history_entry(
    entry_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    entry = await get_history_repository().get(user.uid, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="History entry not found")
    return entry


@router.delete("/history/{entry_id}")
async def delete_history_entry(
    entry_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    deleted = await get_history_repository().delete(user.uid, entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="History entry not found")
    return {"deleted": True, "id": entry_id}


@router.delete("/history")
async def clear_history(user: AuthenticatedUser = Depends(get_current_user)):
    count = await get_history_repository().delete_all(user.uid)
    return {"deleted_count": count}


@router.get("/rewards/status", response_model=RewardsStatus)
async def rewards_status(user: AuthenticatedUser = Depends(get_current_user)):
    return await get_rewards_repository().get_status(user.uid)


@router.post("/rewards/claim", response_model=RewardsStatus)
async def claim_reward(user: AuthenticatedUser = Depends(get_current_user)):
    return await get_rewards_repository().claim_daily(user.uid)
