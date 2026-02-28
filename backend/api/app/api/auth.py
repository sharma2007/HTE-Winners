from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.auth.google import verify_google_id_token
from app.auth.jwt import create_access_token
from app.db import get_db
from app.models import User
from app.schemas import AuthGoogleRequest, TokenResponse

router = APIRouter()


@router.post("/google", response_model=TokenResponse)
def auth_google(payload: AuthGoogleRequest, db: Session = Depends(get_db)) -> TokenResponse:
    claims = verify_google_id_token(payload.id_token)
    provider_sub = claims["sub"]
    email = claims.get("email")
    name = claims.get("name")

    user = (
        db.query(User)
        .filter(User.auth_provider == "google")
        .filter(User.provider_sub == provider_sub)
        .one_or_none()
    )
    if user is None:
        user = User(email=email, name=name, auth_provider="google", provider_sub=provider_sub)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        changed = False
        if email and user.email != email:
            user.email = email
            changed = True
        if name and user.name != name:
            user.name = name
            changed = True
        if changed:
            db.commit()

    token = create_access_token(user_id=str(user.id))
    return TokenResponse(access_token=token)


@router.post("/apple")
def auth_apple_stub() -> dict:
    # Stub for hackathon MVP (Apple Sign In wiring requires additional client config).
    raise HTTPException(status_code=501, detail="Apple OAuth not implemented yet")


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    return {"id": str(user.id), "email": user.email, "name": user.name}

