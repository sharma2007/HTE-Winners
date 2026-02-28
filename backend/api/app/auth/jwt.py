from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings


def create_access_token(user_id: str, expires_in_minutes: int = 60 * 24 * 7) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_in_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=["HS256"],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
    )

