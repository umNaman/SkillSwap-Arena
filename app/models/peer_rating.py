import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Float, Text, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base

class PeerRating(Base):
    __tablename__ = 'peer_ratings'
    __table_args__ = (
        UniqueConstraint('session_id', 'rater_id', 'ratee_id', name='uq_session_rater_ratee'),
        CheckConstraint('communication >= 1.0 AND communication <= 5.0', name='chk_communication'),
        CheckConstraint('confidence >= 1.0 AND confidence <= 5.0', name='chk_confidence'),
        CheckConstraint('relevance >= 1.0 AND relevance <= 5.0', name='chk_relevance'),
        CheckConstraint('participation >= 1.0 AND participation <= 5.0', name='chk_participation'),
        CheckConstraint('leadership >= 1.0 AND leadership <= 5.0', name='chk_leadership'),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('gd_sessions.id'), nullable=False)
    rater_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('participants.id'), nullable=False)
    ratee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('participants.id'), nullable=False)
    
    communication: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    relevance: Mapped[float] = mapped_column(Float, nullable=False)
    participation: Mapped[float] = mapped_column(Float, nullable=False)
    leadership: Mapped[float] = mapped_column(Float, nullable=False)
    
    feedback_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["GDSession"] = relationship("GDSession", back_populates="ratings")
    rater: Mapped["Participant"] = relationship("Participant", foreign_keys=[rater_id], back_populates="ratings_given")
    ratee: Mapped["Participant"] = relationship("Participant", foreign_keys=[ratee_id], back_populates="ratings_received")
