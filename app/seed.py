import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import GDSession, Participant, SessionStatus


DEMO_OPEN_SESSION_ID = uuid.UUID("11111111-1111-4111-8111-111111111111")
DEMO_FEEDBACK_SESSION_ID = uuid.UUID("22222222-2222-4222-8222-222222222222")
DEMO_RATER_ID = uuid.UUID("33333333-3333-4333-8333-333333333333")
DEMO_RATEE_ID = uuid.UUID("44444444-4444-4444-8444-444444444444")


async def seed_demo_data(db: AsyncSession) -> None:
    if not settings.SEED_DEMO_DATA:
        return

    now = datetime.now(timezone.utc)
    existing = set(
        (await db.execute(select(GDSession.id))).scalars().all()
    )

    if DEMO_OPEN_SESSION_ID not in existing:
        db.add(
            GDSession(
                id=DEMO_OPEN_SESSION_ID,
                topic="Should AI-generated work always carry a disclosure label?",
                max_seats=settings.MAX_SEATS,
                status=SessionStatus.FILLING,
                starts_at=now + timedelta(minutes=5),
                duration_seconds=settings.GD_ROUND_DURATION,
            )
        )

    if DEMO_FEEDBACK_SESSION_ID not in existing:
        feedback_session = GDSession(
            id=DEMO_FEEDBACK_SESSION_ID,
            topic="Should companies hire primarily for proven skills or for long-term potential?",
            max_seats=settings.MAX_SEATS,
            status=SessionStatus.FEEDBACK,
            starts_at=now - timedelta(minutes=20),
            started_at=now - timedelta(minutes=20),
            ended_at=now - timedelta(minutes=5),
            duration_seconds=settings.GD_ROUND_DURATION,
        )
        feedback_session.participants.extend(
            [
                Participant(
                    id=DEMO_RATER_ID,
                    alias="CalmFalcon42",
                    avatar_color="#7C6FF0",
                    seat_index=1,
                    agora_uid=330001,
                    is_active=True,
                    joined_at=now - timedelta(minutes=20),
                ),
                Participant(
                    id=DEMO_RATEE_ID,
                    alias="BrightEcho17",
                    avatar_color="#38D9C9",
                    seat_index=2,
                    agora_uid=440002,
                    is_active=True,
                    joined_at=now - timedelta(minutes=20),
                ),
            ]
        )
        db.add(feedback_session)

    await db.commit()
