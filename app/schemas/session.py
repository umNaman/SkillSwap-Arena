from typing import List, Optional
from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, Field

class ParticipantBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    alias: str
    avatar_color: str

class SessionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    topic: str
    capacity: int
    occupied_seats: int
    status: str
    starts_in_seconds: int
    participants: List[ParticipantBrief]

class SessionListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    sessions: List[SessionListItem]

class SessionDetail(SessionListItem):
    model_config = ConfigDict(from_attributes=True)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: int = 900
    preparation_duration_seconds: int = 120
    discussion_duration_seconds: int = 780

class JoinSessionRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    alias: str = Field(max_length=14)
    avatar_color: str
    mic_enabled: bool = True
    cam_enabled: bool = False

class JoinSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    session_id: uuid.UUID
    participant_id: uuid.UUID
    seat_number: int
    seats_filled: int
    capacity: int
    status: str
