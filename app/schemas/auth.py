from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, ConfigDict, Field

class LoginRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    stay_signed_in: bool = False

class RegisterRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    default_alias: str = Field(min_length=1, max_length=50)
    cohort_code: Optional[str] = None

class AnonymousLoginRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    alias: str = Field(min_length=1, max_length=14)
    cohort_code: Optional[str] = None
    turnstile_token: Optional[str] = None

class AuthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    success: bool
    token: str
    user: Dict[str, Any]

class AnonymousAuthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    success: bool
    guest_token: str
    guest_id: str
    alias: str
