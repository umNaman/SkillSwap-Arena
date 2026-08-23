from pydantic import BaseModel, ConfigDict, Field, field_validator

VALID_AVATAR_COLORS = ['#7C6FF0', '#38D9C9', '#FF6FA8', '#FFC94A', '#4FD1C5', '#9B8CFF']

class RandomAliasResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    alias: str

class IdentityRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    alias: str = Field(max_length=14)
    avatar_color: str

    @field_validator('avatar_color')
    @classmethod
    def check_color(cls, v: str) -> str:
        if v not in VALID_AVATAR_COLORS:
            raise ValueError(f"avatar_color must be one of {VALID_AVATAR_COLORS}")
        return v

class IdentityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    alias: str
    avatar_color: str
    valid: bool
