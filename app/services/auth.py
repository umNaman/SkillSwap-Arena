from datetime import datetime, timedelta, timezone
import hashlib
import uuid
from typing import Optional

import bcrypt
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User
from app.config import settings

PASSWORD_HASH_PREFIX = "$skillswap-bcrypt-sha256$"

def hash_password(password: str) -> str:
    password_digest = hashlib.sha256(password.encode("utf-8")).digest()
    bcrypt_hash = bcrypt.hashpw(password_digest, bcrypt.gensalt()).decode("ascii")
    return f"{PASSWORD_HASH_PREFIX}{bcrypt_hash}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if hashed_password.startswith(PASSWORD_HASH_PREFIX):
            stored_hash = hashed_password.removeprefix(PASSWORD_HASH_PREFIX).encode("ascii")
            candidate = hashlib.sha256(plain_password.encode("utf-8")).digest()
        else:
            # Compatibility for conventional bcrypt hashes created by earlier builds.
            stored_hash = hashed_password.encode("ascii")
            candidate = plain_password.encode("utf-8")
        return bcrypt.checkpw(candidate, stored_hash)
    except (ValueError, UnicodeError):
        return False

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
    result = await db.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one_or_none()
    if not user:
        return None
    if not user.password_hash or not verify_password(password, user.password_hash):
        return None
    return user

async def create_user(db: AsyncSession, email: str, password: str, alias: str, cohort: Optional[str] = None) -> User:
    hashed_password = hash_password(password)
    user = User(
        id=uuid.uuid4(),
        email=email.lower(),
        password_hash=hashed_password,
        default_alias=alias,
        cohort_code=cohort,
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
        password_hash=None,
        default_alias=alias,
        cohort_code=cohort,
        is_anonymous=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()
