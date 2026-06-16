from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings
from app.services.firebase import verify_firebase_token

security = HTTPBearer(auto_error=False)


class AuthenticatedUser:
    def __init__(self, uid: str, email: str | None = None, name: str | None = None):
        self.uid = uid
        self.email = email
        self.name = name


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> AuthenticatedUser:
    settings = get_settings()

    # Allow test bypass
    if settings.environment == "test" and request.headers.get("X-Test-User-Id"):
        return AuthenticatedUser(
            uid=request.headers["X-Test-User-Id"],
            email="test@example.com",
            name="Test User",
        )

    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        decoded = await verify_firebase_token(credentials.credentials)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    return AuthenticatedUser(
        uid=decoded["uid"],
        email=decoded.get("email"),
        name=decoded.get("name"),
    )
