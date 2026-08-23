from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

class MetricRatings(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    communication: float = Field(ge=1, le=5)
    confidence: float = Field(ge=1, le=5)
    relevance: float = Field(ge=1, le=5)
    participation: float = Field(ge=1, le=5)
    leadership: float = Field(ge=1, le=5)

class PeerRatingCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    target_participant_id: str
    target_alias: str
    metrics: MetricRatings
    feedback_text: Optional[str] = None

class FeedbackSubmission(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    session_id: str
    rater_participant_id: str
    ratings: List[PeerRatingCreate]

class FeedbackAverages(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    communication: float
    confidence: float
    relevance: float
    participation: float
    leadership: float

class FeedbackSummaryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    participant_id: str
    alias: str
    averages: FeedbackAverages
    total_raters: int

class FeedbackSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    session_id: str
    summaries: List[FeedbackSummaryItem]
