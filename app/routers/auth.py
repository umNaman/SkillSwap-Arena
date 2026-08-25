from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, AnonymousLoginRequest, AuthResponse, AnonymousAuthResponse
from app.services import auth as auth_service
from app.config import settings
import httpx

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate_user(db, request.email, request.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    expires = timedelta(days=30) if request.stay_signed_in else None
    token = auth_service.create_access_token({"sub": str(user.id)}, expires)
    return {"success": True, "token": token, "user": _serialize_user(user)}

@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if await auth_service.get_user_by_email(db, request.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    try:
        user = await auth_service.create_user(
            db,
            request.email,
            request.password,
            request.default_alias,
            request.cohort_code,
        )
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    token = auth_service.create_access_token({"sub": str(user.id)})
    return {"success": True, "token": token, "user": _serialize_user(user)}

@router.post("/anonymous", response_model=AnonymousAuthResponse)
async def login_anonymous(request: AnonymousLoginRequest, db: AsyncSession = Depends(get_db)):
    if not request.turnstile_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CAPTCHA verification required.")
    
    try:
        async with httpx.AsyncClient() as client:
            verify_response = await client.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data={
                    "secret": settings.TURNSTILE_SECRET_KEY,
                    "response": request.turnstile_token,
                },
                timeout=10.0
            )
            data = verify_response.json()
            if not data.get("success"):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CAPTCHA verification failed.")
    except httpx.HTTPError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not communicate with CAPTCHA service.")

    user = await auth_service.create_anonymous_user(db, request.alias, request.cohort_code)
    guest_id = str(user.id)
    return {
        "success": True,
        "guest_token": auth_service.create_guest_token(guest_id, request.alias),
        "guest_id": guest_id,
        "alias": request.alias,
    }


def _serialize_user(user) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "default_alias": user.default_alias,
        "cohort_code": user.cohort_code,
        "is_anonymous": user.is_anonymous,
    }

@router.get("/config/turnstile")
async def get_turnstile_config():
    return {"site_key": settings.TURNSTILE_SITE_KEY}

@router.get("/oauth/google")
async def oauth_google():
    return {"message": "Google OAuth integration pending", "redirect_url": "/oauth/google/callback"}

@router.get("/oauth/github")
async def oauth_github():
    return {"message": "GitHub OAuth integration pending", "redirect_url": "/oauth/github/callback"}
