from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    session_id: str

class InsightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    session_id: str
    participant_id: Optional[str] = None
    transcription: Optional[str] = None
    strengths: List[str]
    improvements: List[str]
    overall_score: Optional[int] = None
    summary: Optional[str] = None
    status: str
    generated_at: Optional[datetime] = None

class InsightListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    insights: List[InsightResponse]
