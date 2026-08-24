import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models import GDSession, SessionStatus, Participant
from app.config import settings


PUBLIC_GD_TOPICS = (
    {
        "category": "General",
        "difficulty": "Beginner",
        "prompt": "Does social media create more meaningful connection than social pressure?",
    },
    {
        "category": "General",
        "difficulty": "Intermediate",
        "prompt": "Should success early in a career be measured more by learning than by salary?",
    },
    {
        "category": "General",
        "difficulty": "Advanced",
        "prompt": "When public safety and individual privacy conflict, which should take priority?",
    },
    {
        "category": "Corporate",
        "difficulty": "Beginner",
        "prompt": "For fresh graduates, is a structured office environment better than remote work?",
    },
    {
        "category": "Corporate",
        "difficulty": "Intermediate",
        "prompt": "Should companies hire primarily for proven skills or for long-term potential?",
    },
    {
        "category": "Corporate",
        "difficulty": "Advanced",
        "prompt": "Should businesses accept slower growth when it protects employee wellbeing?",
    },
    {
        "category": "Current Affairs",
        "difficulty": "Beginner",
        "prompt": "Should cities prioritise affordable public transport over expanding roads for cars?",
    },
    {
        "category": "Current Affairs",
        "difficulty": "Intermediate",
        "prompt": "Should governments regulate misinformation even when it risks limiting free expression?",
    },
    {
        "category": "Current Affairs",
        "difficulty": "Advanced",
        "prompt": "Can rapid economic development be justified when it increases environmental inequality?",
    },
    {
        "category": "Technology",
        "difficulty": "Beginner",
        "prompt": "Should AI-generated work always carry a disclosure label?",
    },
    {
        "category": "Technology",
        "difficulty": "Intermediate",
        "prompt": "Will AI make entry-level jobs more valuable as learning roles, or make them disappear?",
    },
    {
        "category": "Technology",
        "difficulty": "Advanced",
        "prompt": "Should high-impact automated decisions be allowed when their reasoning cannot be fully explained?",
    },
)

_matchmaking_lock = asyncio.Lock()


def _active_participants(session: GDSession) -> list[Participant]:
    return [participant for participant in session.participants if participant.is_active]


def get_host_participant(session: GDSession) -> Optional[Participant]:
    """Derive the current moderator from persisted active seat order."""
    active = _active_participants(session)
    if not active:
        return None
    return min(
        active,
        key=lambda item: (
            item.seat_index or settings.MAX_SEATS + 1,
            _as_utc(item.joined_at) or datetime.min.replace(tzinfo=timezone.utc),
            str(item.id),
        ),
    )


def _as_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def participants_who_took_part(session: GDSession) -> list[Participant]:
    """Return persistent round membership, independent of current presence.

    A participant counts once the live discussion began while they were still in
    the room. People who left during matchmaking/preparation are intentionally
    excluded, while people who left after the discussion began remain rateable.
    """
    started_at = _as_utc(session.started_at)
    if not started_at:
        return []

    participants: dict[uuid.UUID, Participant] = {}
    for participant in session.participants:
        joined_at = _as_utc(participant.joined_at)
        left_at = _as_utc(participant.left_at)
        if joined_at and joined_at <= started_at and (
            left_at is None or left_at >= started_at
        ):
            participants[participant.id] = participant
    return sorted(
        participants.values(),
        key=lambda item: (
            item.seat_index or settings.MAX_SEATS + 1,
            _as_utc(item.joined_at) or datetime.min.replace(tzinfo=timezone.utc),
        ),
    )


async def recover_stale_sessions(
    db: AsyncSession, connected_session_ids: set[uuid.UUID]
) -> None:
    """Recover abandoned rooms without deleting legitimate session history."""
    sessions = (
        await db.execute(
            select(GDSession)
            .where(
                GDSession.status.in_(
                    [
                        SessionStatus.FILLING,
                        SessionStatus.STARTING,
                        SessionStatus.IN_PROGRESS,
                    ]
                )
            )
            .options(selectinload(GDSession.participants))
        )
    ).scalars().all()

    now = datetime.now(timezone.utc)
    prestart_cutoff = now - timedelta(
        seconds=settings.STALE_PRESTART_SESSION_SECONDS
    )
    starting_cutoff = now - timedelta(
        seconds=settings.GD_PREPARATION_DURATION + 60
    )
    changed = False

    for session in sessions:
        if session.id in connected_session_ids:
            continue

        active_participants = _active_participants(session)
        if session.status == SessionStatus.FILLING:
            for participant in active_participants:
                joined_at = _as_utc(participant.joined_at)
                if joined_at and joined_at <= prestart_cutoff:
                    participant.is_active = False
                    participant.left_at = participant.left_at or now
                    changed = True

        elif session.status == SessionStatus.STARTING:
            latest_join = max(
                (
                    joined_at
                    for item in active_participants
                    if (joined_at := _as_utc(item.joined_at)) is not None
                ),
                default=None,
            )
            if latest_join is None or latest_join <= starting_cutoff:
                for participant in active_participants:
                    participant.is_active = False
                    participant.left_at = participant.left_at or now
                session.status = SessionStatus.FILLING
                session.started_at = None
                changed = True

        elif session.status == SessionStatus.IN_PROGRESS:
            started_at = _as_utc(session.started_at)
            stale_after = settings.GD_DISCUSSION_DURATION + settings.STALE_IN_PROGRESS_GRACE_SECONDS
            if started_at and started_at <= now - timedelta(seconds=stale_after):
                session.status = SessionStatus.FEEDBACK
                session.ended_at = session.ended_at or now
                changed = True

    if changed:
        await db.commit()


async def ensure_joinable_public_sessions(db: AsyncSession) -> list[GDSession]:
    """Maintain a bounded target pool of public rooms that can still accept users."""
    async with _matchmaking_lock:
        candidates = (
            await db.execute(
                select(GDSession)
                .where(GDSession.status == SessionStatus.FILLING)
                .options(selectinload(GDSession.participants))
                .order_by(GDSession.created_at.asc())
            )
        ).scalars().all()
        joinable = [
            session
            for session in candidates
            if len(_active_participants(session)) < session.max_seats
        ]
        missing = max(0, settings.PUBLIC_ROOM_POOL_SIZE - len(joinable))
        if not missing:
            return joinable

        session_count = await db.scalar(select(func.count(GDSession.id))) or 0
        now = datetime.now(timezone.utc)
        created: list[GDSession] = []
        for offset in range(missing):
            topic = PUBLIC_GD_TOPICS[
                (session_count + offset) % len(PUBLIC_GD_TOPICS)
            ]
            session = GDSession(
                topic=topic["prompt"],
                max_seats=settings.MAX_SEATS,
                status=SessionStatus.FILLING,
                starts_at=now + timedelta(minutes=5),
                duration_seconds=settings.GD_ROUND_DURATION,
            )
            db.add(session)
            created.append(session)
        await db.commit()
        for session in created:
            await db.refresh(session)
        return [*joinable, *created]


async def list_open_sessions(
    db: AsyncSession, connected_session_ids: Optional[set[uuid.UUID]] = None
) -> list[dict]:
    await recover_stale_sessions(db, connected_session_ids or set())
    await ensure_joinable_public_sessions(db)
    query = select(GDSession).where(
        GDSession.status.in_(
            [SessionStatus.FILLING, SessionStatus.STARTING, SessionStatus.IN_PROGRESS]
        )
    ).options(selectinload(GDSession.participants)).order_by(GDSession.created_at.asc())
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    response = []
    now = datetime.now(timezone.utc)
    for session in sessions:
        active_participants = _active_participants(session)
        starts_at = session.starts_at
        if starts_at and starts_at.tzinfo is None:
            starts_at = starts_at.replace(tzinfo=timezone.utc)
        starts_in = max(0, int((starts_at - now).total_seconds())) if starts_at else 0
        response.append({
            "id": session.id,
            "topic": session.topic,
            "status": session.status.value,
            "capacity": session.max_seats,
            "occupied_seats": len(active_participants),
            "starts_in_seconds": starts_in,
            "participants": [
                {"id": p.id, "alias": p.alias, "avatar_color": p.avatar_color}
                for p in active_participants
            ],
        })
    return response

async def get_session_detail(db: AsyncSession, session_id: uuid.UUID) -> Optional[GDSession]:
    query = select(GDSession).where(GDSession.id == session_id).options(selectinload(GDSession.participants))
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def join_session(
    db: AsyncSession, 
    session_id: uuid.UUID, 
    alias: str, 
    avatar_color: str, 
    mic_on: bool, 
    cam_on: bool, 
    user_id: Optional[uuid.UUID] = None
) -> dict:
    replenish_pool = False
    async with _matchmaking_lock:
        session = await get_session_detail(db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session.status != SessionStatus.FILLING:
            raise HTTPException(status_code=409, detail="Session is not accepting participants")

        active_participants = _active_participants(session)
        if len(active_participants) >= session.max_seats:
            raise HTTPException(status_code=409, detail="Session is full")

        for existing_participant in session.participants:
            if existing_participant.alias == alias:
                raise HTTPException(status_code=400, detail="Alias was already used in this session")

        occupied_seats = {participant.seat_index for participant in active_participants}
        seat_index = next(
            index
            for index in range(1, session.max_seats + 1)
            if index not in occupied_seats
        )
        participant_id = uuid.uuid4()
        agora_uid = participant_id.int % 4_294_967_295 or 1

        participant = Participant(
            id=participant_id,
            session_id=session.id,
            user_id=user_id,
            alias=alias,
            avatar_color=avatar_color,
            seat_index=seat_index,
            agora_uid=agora_uid,
            is_active=True,
            mic_on=mic_on,
            camera_on=cam_on,
            joined_at=datetime.now(timezone.utc),
        )

        db.add(participant)
        session.participants.append(participant)
        await db.commit()
        await db.refresh(participant)

        seats_filled = len(active_participants) + 1
        replenish_pool = seats_filled >= session.max_seats

    if replenish_pool:
        await ensure_joinable_public_sessions(db)

    return {
        "session_id": session.id,
        "participant_id": participant.id,
        "seat_number": participant.seat_index,
        "seats_filled": seats_filled,
        "capacity": session.max_seats,
        "status": session.status.value,
    }

async def leave_session(
    db: AsyncSession, session_id: uuid.UUID, participant_id: uuid.UUID
) -> tuple[bool, bool]:
    """Deactivate a participant and report whether a pending start was cancelled."""
    async with _matchmaking_lock:
        row = (
            await db.execute(
                select(Participant, GDSession)
                .join(GDSession, Participant.session_id == GDSession.id)
                .where(
                    and_(
                        Participant.session_id == session_id,
                        Participant.id == participant_id,
                    )
                )
            )
        ).one_or_none()
        if not row:
            return False, False

        participant, session = row
        if not participant.is_active:
            return False, False

        participant.is_active = False
        participant.left_at = datetime.now(timezone.utc)
        start_cancelled = session.status == SessionStatus.STARTING
        if start_cancelled:
            session.status = SessionStatus.FILLING
            session.started_at = None
        await db.commit()
        return True, start_cancelled


async def begin_session_starting(db: AsyncSession, session_id: uuid.UUID) -> bool:
    """Move a full matchmaking room into its short client countdown."""
    async with _matchmaking_lock:
        session = await get_session_detail(db, session_id)
        if not session or session.status != SessionStatus.FILLING:
            return False
        if len(_active_participants(session)) != session.max_seats:
            return False
        session.status = SessionStatus.STARTING
        await db.commit()
        return True


async def begin_session_in_progress(db: AsyncSession, session_id: uuid.UUID) -> bool:
    """Start the GD only after the client countdown reaches the live arena."""
    async with _matchmaking_lock:
        session = await get_session_detail(db, session_id)
        if not session or session.status != SessionStatus.STARTING:
            return False
        if len(_active_participants(session)) != session.max_seats:
            session.status = SessionStatus.FILLING
            await db.commit()
            return False
        session.status = SessionStatus.IN_PROGRESS
        session.started_at = datetime.now(timezone.utc)
        await db.commit()
        return True


async def update_participant_media_state(
    db: AsyncSession,
    session_id: uuid.UUID,
    participant_id: uuid.UUID,
    *,
    mic_on: Optional[bool] = None,
    camera_on: Optional[bool] = None,
) -> Optional[Participant]:
    participant = (
        await db.execute(
            select(Participant).where(
                Participant.session_id == session_id,
                Participant.id == participant_id,
                Participant.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if not participant:
        return None
    if mic_on is not None:
        participant.mic_on = mic_on
    if camera_on is not None:
        participant.camera_on = camera_on
    await db.commit()
    return participant


async def update_session_status(
    db: AsyncSession, session_id: uuid.UUID, status: SessionStatus
) -> GDSession:
    session = await get_session_detail(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.status = status
    now = datetime.now(timezone.utc)
    if status == SessionStatus.IN_PROGRESS and not session.started_at:
        session.started_at = now
    if status in (SessionStatus.FEEDBACK, SessionStatus.COMPLETED):
        session.ended_at = session.ended_at or now
    await db.commit()
    await db.refresh(session)
    return session


def serialize_session(session: GDSession) -> dict:
    active_participants = [p for p in session.participants if p.is_active]
    now = datetime.now(timezone.utc)
    starts_at = session.starts_at
    if starts_at and starts_at.tzinfo is None:
        starts_at = starts_at.replace(tzinfo=timezone.utc)
    return {
        "id": session.id,
        "topic": session.topic,
        "capacity": session.max_seats,
        "occupied_seats": len(active_participants),
        "status": session.status.value,
        "starts_in_seconds": max(0, int((starts_at - now).total_seconds())) if starts_at else 0,
        "participants": [
            {"id": p.id, "alias": p.alias, "avatar_color": p.avatar_color}
            for p in active_participants
        ],
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "duration_seconds": session.duration_seconds,
        "preparation_duration_seconds": settings.GD_PREPARATION_DURATION,
        "discussion_duration_seconds": settings.GD_DISCUSSION_DURATION,
    }
