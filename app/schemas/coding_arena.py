from pydantic import BaseModel, Field, field_validator


LANGUAGES = {"python", "cpp", "java"}
DIFFICULTIES = {"easy", "medium", "hard"}
TOPICS = {"arrays", "strings", "searching", "sorting"}
MODES = {"head_to_head", "attack", "friend"}


class ArenaFilters(BaseModel):
    language: str
    difficulty: str
    topic: str

    @field_validator("language")
    @classmethod
    def language_valid(cls, value):
        if value not in LANGUAGES: raise ValueError("Unsupported language")
        return value

    @field_validator("difficulty")
    @classmethod
    def difficulty_valid(cls, value):
        if value not in DIFFICULTIES: raise ValueError("Unsupported difficulty")
        return value

    @field_validator("topic")
    @classmethod
    def topic_valid(cls, value):
        if value not in TOPICS: raise ValueError("Unsupported topic")
        return value


class RunRequest(BaseModel):
    problem_id: str
    language: str
    source_code: str = Field(max_length=100_000)
    stdin: str = Field(default="", max_length=20_000)

    @field_validator("language")
    @classmethod
    def language_valid(cls, value):
        if value not in LANGUAGES: raise ValueError("Unsupported language")
        return value


class SubmitRequest(RunRequest):
    mode: str
    session_id: str | None = None
    solve_seconds: int = Field(default=0, ge=0, le=86_400)

    @field_validator("mode")
    @classmethod
    def mode_valid(cls, value):
        if value not in MODES: raise ValueError("Unsupported mode")
        return value


class HintRequest(BaseModel):
    problem_id: str
    hint_index: int = Field(ge=0, le=20)
    attack_session_id: str | None = None


class JoinRoomRequest(BaseModel):
    room_code: str = Field(min_length=6, max_length=6)
