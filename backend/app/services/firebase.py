from __future__ import annotations

import json
import logging
import os
from typing import Any

import firebase_admin
from firebase_admin import auth, credentials, firestore

from app.config import Settings, get_settings
from app.services.storage import (
    FirestoreHistoryRepository,
    FirestoreRewardsRepository,
    HistoryRepository,
    InMemoryHistoryRepository,
    InMemoryRewardsRepository,
    RewardsRepository,
)

logger = logging.getLogger(__name__)

_firebase_initialized = False
_db: Any = None
_history_repo: HistoryRepository | None = None
_rewards_repo: RewardsRepository | None = None


def init_firebase(settings: Settings | None = None) -> bool:
    global _firebase_initialized, _db
    settings = settings or get_settings()

    if settings.environment == "test":
        return False

    if settings.use_firestore_emulator:
        os.environ["FIRESTORE_EMULATOR_HOST"] = settings.firestore_emulator_host

    if _firebase_initialized:
        return True

    try:
        if settings.firebase_credentials_json:
            cred_dict = json.loads(settings.firebase_credentials_json)
            cred = credentials.Certificate(cred_dict)
        elif settings.firebase_credentials_path and os.path.exists(settings.firebase_credentials_path):
            cred = credentials.Certificate(settings.firebase_credentials_path)
        else:
            logger.warning("No Firebase credentials found — using in-memory storage")
            return False

        firebase_admin.initialize_app(cred, {"projectId": settings.firestore_project_id})
        _db = firestore.client()
        _firebase_initialized = True
        logger.info("Firebase initialized")
        return True
    except Exception as e:
        logger.warning("Firebase init failed: %s — using in-memory storage", e)
        return False


def get_history_repository() -> HistoryRepository:
    global _history_repo
    if _history_repo is None:
        if _firebase_initialized and _db is not None:
            _history_repo = FirestoreHistoryRepository(_db)
        else:
            _history_repo = InMemoryHistoryRepository()
    return _history_repo


def get_rewards_repository() -> RewardsRepository:
    global _rewards_repo
    if _rewards_repo is None:
        if _firebase_initialized and _db is not None:
            _rewards_repo = FirestoreRewardsRepository(_db)
        else:
            _rewards_repo = InMemoryRewardsRepository()
    return _rewards_repo


def reset_repositories() -> None:
    global _history_repo, _rewards_repo
    _history_repo = None
    _rewards_repo = None


async def verify_firebase_token(token: str) -> dict[str, Any]:
    """Verify Firebase ID token and return decoded claims."""
    try:
        decoded = auth.verify_id_token(token)
        return decoded
    except Exception as e:
        raise ValueError(str(e)) from e
