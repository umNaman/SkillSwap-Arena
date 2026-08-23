from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, AnonymousLoginRequest, AuthResponse, AnonymousAuthResponse
from app.services import auth as auth_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    auth_resp = await auth_service.authenticate_user(db, request.email, request.password)
    if not auth_resp:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return auth_resp

@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    auth_resp = await auth_service.create_user(db, request)
    if not auth_resp:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    return auth_resp

@router.post("/anonymous", response_model=AnonymousAuthResponse)
async def login_anonymous(request: AnonymousLoginRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.create_anonymous_user(db, request)

@router.get("/oauth/google")
async def oauth_google():
    return {"message": "Google OAuth integration pending", "redirect_url": "/oauth/google/callback"}

@router.get("/oauth/github")
async def oauth_github():
    return {"message": "GitHub OAuth integration pending", "redirect_url": "/oauth/github/callback"}
