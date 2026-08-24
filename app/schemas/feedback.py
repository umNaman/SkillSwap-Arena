from typing import List, Optional
import uuid
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
    target_participant_id: uuid.UUID
    target_alias: str
    metrics: MetricRatings
    feedback_text: Optional[str] = None

class FeedbackSubmission(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    session_id: uuid.UUID
    rater_participant_id: uuid.UUID
    ratings: List[PeerRatingCreate] = Field(min_length=1)

class FeedbackAverages(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    communication: float
    confidence: float
    relevance: float
    participation: float
    leadership: float

class FeedbackSummaryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    participant_id: uuid.UUID
    alias: str
    averages: FeedbackAverages
    total_raters: int

class FeedbackSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    session_id: uuid.UUID
    summaries: List[FeedbackSummaryItem]


class ParticipantReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    session_id: uuid.UUID
    participant_id: uuid.UUID
    alias: str
    received_count: int
    expected_count: int
    overall_rating: Optional[float] = None
    averages: Optional[FeedbackAverages] = None
    room_average: Optional[float] = None
    ai_analysis: Optional[dict] = None
    speech_metrics_available: bool = False
