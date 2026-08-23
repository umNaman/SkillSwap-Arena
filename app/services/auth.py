from datetime import datetime, timedelta, timezone
import uuid
from typing import Optional

from passlib.context import CryptContext
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_guest_token(guest_id: str, alias: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    data = {
        "sub": guest_id,
        "alias": alias,
        "is_anonymous": True,
        "exp": expire
    }
    encoded_jwt = jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return None
    if not user.hashed_password or not verify_password(password, user.hashed_password):
        return None
    return user

async def create_user(db: AsyncSession, email: str, password: str, alias: str, cohort: Optional[str] = None) -> User:
    hashed_password = hash_password(password)
    user = User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=hashed_password,
        alias=alias,
        cohort=cohort,
        is_anonymous=False
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def create_anonymous_user(db: AsyncSession, alias: str, cohort: Optional[str] = None) -> User:
    user = User(
        id=uuid.uuid4(),
        email=None,
        hashed_password=None,
        alias=alias,
        cohort=cohort,
        is_anonymous=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
