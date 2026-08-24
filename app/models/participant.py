import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Participant(Base):
    __tablename__ = 'participants'
    __table_args__ = (
        UniqueConstraint('session_id', 'alias', name='uq_session_alias'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey('gd_sessions.id'), nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey('users.id'), nullable=True)
    alias: Mapped[str] = mapped_column(String(50), nullable=False)
    avatar_color: Mapped[str] = mapped_column(String(10), nullable=False)
    mic_on: Mapped[bool] = mapped_column(Boolean, default=True)
    camera_on: Mapped[bool] = mapped_column(Boolean, default=False)
    seat_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    agora_uid: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    left_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    session: Mapped["GDSession"] = relationship("GDSession", back_populates="participants")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="participants")
    ratings_given: Mapped[List["PeerRating"]] = relationship("PeerRating", foreign_keys="[PeerRating.rater_id]", back_populates="rater")
    ratings_received: Mapped[List["PeerRating"]] = relationship("PeerRating", foreign_keys="[PeerRating.ratee_id]", back_populates="ratee")
