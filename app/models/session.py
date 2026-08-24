import uuid
import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, DateTime, Enum, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class SessionStatus(str, enum.Enum):
    FILLING = 'filling'
    STARTING = 'starting'
    IN_PROGRESS = 'in_progress'
    FEEDBACK = 'feedback'
    COMPLETED = 'completed'

class GDSession(Base):
    __tablename__ = 'gd_sessions'

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    max_seats: Mapped[int] = mapped_column(Integer, default=6)
    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus), default=SessionStatus.FILLING)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=900)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    participants: Mapped[List["Participant"]] = relationship("Participant", back_populates="session", lazy="selectin")
    ratings: Mapped[List["PeerRating"]] = relationship("PeerRating", back_populates="session", lazy="selectin")
    insights: Mapped[List["AIInsight"]] = relationship("AIInsight", back_populates="session", lazy="selectin")
