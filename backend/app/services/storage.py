from __future__ import annotations

import io
import logging
from datetime import datetime, timezone

UTC = timezone.utc
from typing import Any
from uuid import uuid4

from app.models.schemas import AnalysisDetails, HistoryEntry, MoodName, MoodScores, RewardsStatus

logger = logging.getLogger(__name__)


class InMemoryStore:
    """Fallback store for development/testing without Firestore."""

    def __init__(self) -> None:
        self.history: dict[str, dict[str, Any]] = {}
        self.rewards: dict[str, dict[str, Any]] = {}

    def clear(self) -> None:
        self.history.clear()
        self.rewards.clear()


_memory = InMemoryStore()


def get_memory_store() -> InMemoryStore:
    return _memory


class HistoryRepository:
    async def create(
        self,
        user_id: str,
        mood: MoodName,
        confidence: float,
        scores: MoodScores,
        analysis_details: AnalysisDetails,
        thumbnail_b64: str | None = None,
        notes: str | None = None,
    ) -> HistoryEntry:
        raise NotImplementedError

    async def list(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        mood: MoodName | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> tuple[list[HistoryEntry], int]:
        raise NotImplementedError

    async def get(self, user_id: str, entry_id: str) -> HistoryEntry | None:
        raise NotImplementedError

    async def delete(self, user_id: str, entry_id: str) -> bool:
        raise NotImplementedError

    async def delete_all(self, user_id: str) -> int:
        raise NotImplementedError


class InMemoryHistoryRepository(HistoryRepository):
    async def create(
        self,
        user_id: str,
        mood: MoodName,
        confidence: float,
        scores: MoodScores,
        analysis_details: AnalysisDetails,
        thumbnail_b64: str | None = None,
        notes: str | None = None,
    ) -> HistoryEntry:
        entry_id = str(uuid4())
        now = datetime.now(UTC)
        doc = {
            "id": entry_id,
            "user_id": user_id,
            "timestamp": now,
            "mood": mood,
            "confidence": confidence,
            "scores": scores.model_dump(),
            "thumbnail_url": f"data:image/png;base64,{thumbnail_b64}" if thumbnail_b64 else None,
            "notes": notes,
            "analysis_details": analysis_details.model_dump(),
        }
        get_memory_store().history[entry_id] = doc
        return HistoryEntry(**doc)

    async def list(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        mood: MoodName | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> tuple[list[HistoryEntry], int]:
        items = [v for v in get_memory_store().history.values() if v["user_id"] == user_id]
        if mood:
            items = [v for v in items if v["mood"] == mood]
        if from_date:
            items = [v for v in items if v["timestamp"] >= from_date]
        if to_date:
            items = [v for v in items if v["timestamp"] <= to_date]
        items.sort(key=lambda x: x["timestamp"], reverse=True)
        total = len(items)
        page = items[offset : offset + limit]
        return [HistoryEntry(**v) for v in page], total

    async def get(self, user_id: str, entry_id: str) -> HistoryEntry | None:
        doc = get_memory_store().history.get(entry_id)
        if not doc or doc["user_id"] != user_id:
            return None
        return HistoryEntry(**doc)

    async def delete(self, user_id: str, entry_id: str) -> bool:
        doc = get_memory_store().history.get(entry_id)
        if not doc or doc["user_id"] != user_id:
            return False
        del get_memory_store().history[entry_id]
        return True

    async def delete_all(self, user_id: str) -> int:
        to_delete = [k for k, v in get_memory_store().history.items() if v["user_id"] == user_id]
        for k in to_delete:
            del get_memory_store().history[k]
        return len(to_delete)


class FirestoreHistoryRepository(HistoryRepository):
    def __init__(self, db: Any) -> None:
        self._db = db
        self._collection = "mood_history"

    def _to_entry(self, doc_id: str, data: dict[str, Any]) -> HistoryEntry:
        scores = MoodScores(**data["scores"])
        details = AnalysisDetails(**data["analysis_details"]) if data.get("analysis_details") else None
        ts = data["timestamp"]
        if hasattr(ts, "timestamp"):
            ts = ts.replace(tzinfo=UTC) if ts.tzinfo is None else ts
        return HistoryEntry(
            id=doc_id,
            user_id=data["user_id"],
            timestamp=ts,
            mood=data["mood"],
            confidence=data["confidence"],
            scores=scores,
            thumbnail_url=data.get("thumbnail_url"),
            notes=data.get("notes"),
            analysis_details=details,
        )

    async def create(
        self,
        user_id: str,
        mood: MoodName,
        confidence: float,
        scores: MoodScores,
        analysis_details: AnalysisDetails,
        thumbnail_b64: str | None = None,
        notes: str | None = None,
    ) -> HistoryEntry:
        now = datetime.now(UTC)
        doc_data = {
            "user_id": user_id,
            "timestamp": now,
            "mood": mood,
            "confidence": confidence,
            "scores": scores.model_dump(),
            "thumbnail_url": f"data:image/png;base64,{thumbnail_b64}" if thumbnail_b64 else None,
            "notes": notes,
            "analysis_details": analysis_details.model_dump(),
        }
        _, ref = self._db.collection(self._collection).add(doc_data)
        return HistoryEntry(id=ref.id, **doc_data)

    async def list(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        mood: MoodName | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> tuple[list[HistoryEntry], int]:
        query = self._db.collection(self._collection).where("user_id", "==", user_id)
        if mood:
            query = query.where("mood", "==", mood)
        if from_date:
            query = query.where("timestamp", ">=", from_date)
        if to_date:
            query = query.where("timestamp", "<=", to_date)
        query = query.order_by("timestamp", direction="DESCENDING")

        # Firestore doesn't support offset natively well; fetch and slice
        docs = list(query.stream())
        total = len(docs)
        page_docs = docs[offset : offset + limit]
        return [self._to_entry(d.id, d.to_dict()) for d in page_docs], total

    async def get(self, user_id: str, entry_id: str) -> HistoryEntry | None:
        doc = self._db.collection(self._collection).document(entry_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        if data["user_id"] != user_id:
            return None
        return self._to_entry(doc.id, data)

    async def delete(self, user_id: str, entry_id: str) -> bool:
        doc_ref = self._db.collection(self._collection).document(entry_id)
        doc = doc_ref.get()
        if not doc.exists:
            return False
        if doc.to_dict()["user_id"] != user_id:
            return False
        doc_ref.delete()
        return True

    async def delete_all(self, user_id: str) -> int:
        docs = self._db.collection(self._collection).where("user_id", "==", user_id).stream()
        count = 0
        batch = self._db.batch()
        for doc in docs:
            batch.delete(doc.reference)
            count += 1
            if count % 400 == 0:
                batch.commit()
                batch = self._db.batch()
        if count % 400 != 0:
            batch.commit()
        return count


class RewardsRepository:
    async def get_status(self, user_id: str) -> RewardsStatus:
        raise NotImplementedError

    async def claim_daily(self, user_id: str) -> RewardsStatus:
        raise NotImplementedError


class InMemoryRewardsRepository(RewardsRepository):
    DAILY_COINS = 10

    async def get_status(self, user_id: str) -> RewardsStatus:
        store = get_memory_store()
        data = store.rewards.get(user_id, {"coins": 0, "streak": 0, "last_earned": None})
        last = data.get("last_earned")
        can_claim = self._can_claim_today(last)
        return RewardsStatus(
            coins=data.get("coins", 0),
            streak=data.get("streak", 0),
            last_earned=last,
            can_claim_today=can_claim,
        )

    def _can_claim_today(self, last_earned: datetime | None) -> bool:
        if last_earned is None:
            return True
        now = datetime.now(UTC)
        last = last_earned if last_earned.tzinfo else last_earned.replace(tzinfo=UTC)
        return last.date() < now.date()

    async def claim_daily(self, user_id: str) -> RewardsStatus:
        store = get_memory_store()
        data = store.rewards.get(user_id, {"coins": 0, "streak": 0, "last_earned": None})
        last = data.get("last_earned")
        now = datetime.now(UTC)

        if not self._can_claim_today(last):
            return await self.get_status(user_id)

        streak = data.get("streak", 0)
        if last:
            last_dt = last if last.tzinfo else last.replace(tzinfo=UTC)
            days_gap = (now.date() - last_dt.date()).days
            streak = streak + 1 if days_gap == 1 else 1
        else:
            streak = 1

        data = {
            "coins": data.get("coins", 0) + self.DAILY_COINS,
            "streak": streak,
            "last_earned": now,
        }
        store.rewards[user_id] = data
        return RewardsStatus(coins=data["coins"], streak=streak, last_earned=now, can_claim_today=False)


class FirestoreRewardsRepository(RewardsRepository):
    DAILY_COINS = 10

    def __init__(self, db: Any) -> None:
        self._db = db
        self._collection = "user_rewards"

    def _doc_ref(self, user_id: str) -> Any:
        return self._db.collection(self._collection).document(user_id)

    async def get_status(self, user_id: str) -> RewardsStatus:
        doc = self._doc_ref(user_id).get()
        if not doc.exists:
            return RewardsStatus(coins=0, streak=0, last_earned=None, can_claim_today=True)
        data = doc.to_dict()
        last = data.get("last_earned")
        if last and hasattr(last, "replace"):
            last = last.replace(tzinfo=UTC) if last.tzinfo is None else last
        can_claim = self._can_claim_today(last)
        return RewardsStatus(
            coins=data.get("coins", 0),
            streak=data.get("streak", 0),
            last_earned=last,
            can_claim_today=can_claim,
        )

    def _can_claim_today(self, last_earned: datetime | None) -> bool:
        if last_earned is None:
            return True
        now = datetime.now(UTC)
        last = last_earned if last_earned.tzinfo else last_earned.replace(tzinfo=UTC)
        return last.date() < now.date()

    async def claim_daily(self, user_id: str) -> RewardsStatus:
        ref = self._doc_ref(user_id)
        doc = ref.get()
        now = datetime.now(UTC)

        if doc.exists:
            data = doc.to_dict()
            last = data.get("last_earned")
            if last and hasattr(last, "replace"):
                last = last.replace(tzinfo=UTC) if last.tzinfo is None else last
            if not self._can_claim_today(last):
                return await self.get_status(user_id)
            streak = data.get("streak", 0)
            if last:
                days_gap = (now.date() - last.date()).days
                streak = streak + 1 if days_gap == 1 else 1
            else:
                streak = 1
            new_data = {
                "coins": data.get("coins", 0) + self.DAILY_COINS,
                "streak": streak,
                "last_earned": now,
            }
        else:
            new_data = {"coins": self.DAILY_COINS, "streak": 1, "last_earned": now}

        ref.set(new_data)
        return RewardsStatus(
            coins=new_data["coins"],
            streak=new_data["streak"],
            last_earned=now,
            can_claim_today=False,
        )


def encode_thumbnail(image_bytes: bytes, max_size: int = 200) -> str:
    """Create a small base64 thumbnail for storage."""
    from PIL import Image
    import base64

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img.thumbnail((max_size, max_size))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")
