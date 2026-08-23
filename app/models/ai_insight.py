import uuid
import enum
from datetime import datetime
from typing import Optional, Any
from sqlalchemy import Text, Integer, DateTime, Enum, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base

class InsightStatus(str, enum.Enum):
    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'

class AIInsight(Base):
    __tablename__ = 'ai_insights'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('gd_sessions.id'), nullable=False)
    participant_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey('participants.id'), nullable=True)
    
    transcription: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    strengths: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    improvements: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    overall_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[InsightStatus] = mapped_column(Enum(InsightStatus), default=InsightStatus.PENDING)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["GDSession"] = relationship("GDSession", back_populates="insights")
    # Note: Using string "Participant" if participant has back_populates, else omitting back_populates.
    participant: Mapped[Optional["Participant"]] = relationship("Participant")
