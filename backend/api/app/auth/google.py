from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.config import settings


def verify_google_id_token(token: str) -> dict[str, Any]:
    if settings.auth_mock:
        # Local dev: accept any token and fabricate stable claims.
        fake_sub = f"dev:{token[:16]}"
        return {"sub": fake_sub, "email": "dev@example.com", "name": "Dev User"}

    if not settings.google_client_id:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID not configured")

    try:
        req = google_requests.Request()
        claims = id_token.verify_oauth2_token(token, req, settings.google_client_id)
        if claims.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
            raise ValueError("Invalid issuer")
        return claims
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid id_token: {e}") from e

