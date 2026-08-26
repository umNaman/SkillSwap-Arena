import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BattleStatus(str, enum.Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ArenaProfile(Base):
    __tablename__ = "arena_profiles"
    __table_args__ = (CheckConstraint("points >= 0", name="ck_arena_points_nonnegative"),)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    points: Mapped[int] = mapped_column(Integer, default=200)
    solved_count: Mapped[int] = mapped_column(Integer, default=0)
    attempted_count: Mapped[int] = mapped_column(Integer, default=0)
    total_solve_seconds: Mapped[int] = mapped_column(Integer, default=0)
    h2h_wins: Mapped[int] = mapped_column(Integer, default=0)
    attack_best_streak: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ArenaTransaction(Base):
    __tablename__ = "arena_transactions"
    __table_args__ = (UniqueConstraint("user_id", "event_key", name="uq_arena_transaction_event"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    amount: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(24))
    event_key: Mapped[str] = mapped_column(String(160))
    problem_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HintUnlock(Base):
    __tablename__ = "arena_hint_unlocks"
    __table_args__ = (UniqueConstraint("user_id", "problem_id", "hint_index", name="uq_arena_hint_unlock"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    problem_id: Mapped[str] = mapped_column(String(64), index=True)
    hint_index: Mapped[int] = mapped_column(Integer)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CodingSubmission(Base):
    __tablename__ = "coding_submissions"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    problem_id: Mapped[str] = mapped_column(String(64), index=True)
    language: Mapped[str] = mapped_column(String(16))
    mode: Mapped[str] = mapped_column(String(20), index=True)
    session_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    passed_tests: Mapped[int] = mapped_column(Integer, default=0)
    total_tests: Mapped[int] = mapped_column(Integer, default=0)
    solve_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProblemCommunityStat(Base):
    __tablename__ = "coding_problem_stats"
    problem_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    seeded_attempts: Mapped[int] = mapped_column(Integer, default=0)
    seeded_solves: Mapped[int] = mapped_column(Integer, default=0)
    seeded_total_seconds: Mapped[int] = mapped_column(Integer, default=0)
    seeded_fastest_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    real_attempts: Mapped[int] = mapped_column(Integer, default=0)
    real_solves: Mapped[int] = mapped_column(Integer, default=0)
    real_total_seconds: Mapped[int] = mapped_column(Integer, default=0)
    real_fastest_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)


class AttackSession(Base):
    __tablename__ = "attack_sessions"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    language: Mapped[str] = mapped_column(String(16))
    difficulty: Mapped[str] = mapped_column(String(16))
    topic: Mapped[str] = mapped_column(String(24))
    attempted: Mapped[int] = mapped_column(Integer, default=0)
    submission_attempts: Mapped[int] = mapped_column(Integer, default=0)
    solved: Mapped[int] = mapped_column(Integer, default=0)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    best_streak: Mapped[int] = mapped_column(Integer, default=0)
    hints_used: Mapped[int] = mapped_column(Integer, default=0)
    points_earned: Mapped[int] = mapped_column(Integer, default=0)
    total_seconds: Mapped[int] = mapped_column(Integer, default=0)
    fastest_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CodingBattle(Base):
    __tablename__ = "coding_battles"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kind: Mapped[str] = mapped_column(String(16), index=True)
    room_code: Mapped[str | None] = mapped_column(String(8), nullable=True, unique=True, index=True)
    language: Mapped[str] = mapped_column(String(16), index=True)
    difficulty: Mapped[str] = mapped_column(String(16), index=True)
    topic: Mapped[str] = mapped_column(String(24), index=True)
    problem_id: Mapped[str] = mapped_column(String(64))
    player_one_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), index=True)
    player_two_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    player_one_alias: Mapped[str] = mapped_column(String(32))
    player_two_alias: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[BattleStatus] = mapped_column(Enum(BattleStatus), default=BattleStatus.WAITING, index=True)
    winner_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    winner_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
