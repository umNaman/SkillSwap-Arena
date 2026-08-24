from typing import List, Optional
from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, Field

class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    session_id: uuid.UUID

class InsightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    session_id: uuid.UUID
    participant_id: Optional[uuid.UUID] = None
    transcription: Optional[str] = None
    strengths: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    overall_score: Optional[int] = None
    summary: Optional[str] = None
    status: str
    generated_at: Optional[datetime] = None

class InsightListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    insights: List[InsightResponse]
