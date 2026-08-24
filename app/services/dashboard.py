from datetime import datetime, timezone, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import GDSession, Participant, PeerRating, SessionStatus, User
from app.services.matchmaking import participants_who_took_part


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _overall(rating: PeerRating) -> float:
    return (
        rating.communication
        + rating.confidence
        + rating.relevance
        + rating.participation
        + rating.leadership
    ) / 5


def _round(value: float | None) -> float | None:
    return round(value, 2) if value is not None else None


async def get_registered_user_dashboard(
    db: AsyncSession, user: User
) -> dict:
    if user.is_anonymous:
        raise HTTPException(
            status_code=403,
            detail="Anonymous sessions do not provide cross-login history",
        )

    participant_rows = (
        await db.execute(
            select(Participant)
            .where(Participant.user_id == user.id)
            .options(
                selectinload(Participant.ratings_received),
                selectinload(Participant.ratings_given),
                selectinload(Participant.session).selectinload(GDSession.participants),
                selectinload(Participant.session).selectinload(GDSession.ratings),
            )
            .order_by(Participant.joined_at.desc())
        )
    ).scalars().unique().all()

    activity = []
    all_received: list[PeerRating] = []
    rated_sessions = []
    now = datetime.now(timezone.utc)
    week_start = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    gds_this_week = 0

    for participant in participant_rows:
        session = participant.session
        took_part = participants_who_took_part(session)
        if not any(item.id == participant.id for item in took_part):
            continue

        joined_at = _as_utc(participant.joined_at)
        if joined_at and joined_at >= week_start:
            gds_this_week += 1

        received = list(participant.ratings_received)
        all_received.extend(received)
        expected_count = max(0, len(took_part) - 1)
        received_count = len({item.rater_id for item in received})
        session_rating = (
            sum(_overall(item) for item in received) / len(received)
            if received
            else None
        )
        if session_rating is not None:
            rated_sessions.append(
                {
                    "session_id": str(session.id),
                    "occurred_at": joined_at.isoformat() if joined_at else None,
                    "average_rating": _round(session_rating),
                }
            )

        left_early = participant.left_at is not None
        if left_early:
            participation_status = "left_early"
        elif session.status in (SessionStatus.FEEDBACK, SessionStatus.COMPLETED):
            participation_status = "completed"
        elif session.status == SessionStatus.IN_PROGRESS:
            participation_status = "in_progress"
        elif session.status == SessionStatus.STARTING:
            participation_status = "preparing"
        else:
            participation_status = "joined"

        activity.append(
            {
                "session_id": str(session.id),
                "participant_id": str(participant.id),
                "topic": session.topic,
                "occurred_at": joined_at.isoformat() if joined_at else None,
                "participation_status": participation_status,
                "feedback_status": (
                    "submitted" if participant.ratings_given else "awaiting_submission"
                ),
                "received_feedback_count": received_count,
                "expected_feedback_count": expected_count,
                "received_rating": _round(session_rating),
            }
        )

    activity.sort(key=lambda item: item["occurred_at"] or "", reverse=True)
    rated_sessions.sort(key=lambda item: item["occurred_at"] or "")

    average_peer_rating = (
        sum(_overall(item) for item in all_received) / len(all_received)
        if all_received
        else None
    )
    average_clarity = (
        sum(item.communication for item in all_received) / len(all_received)
        if all_received
        else None
    )

    return {
        "user_id": str(user.id),
        "stats": {
            "sessions_completed": sum(
                item["participation_status"] == "completed" for item in activity
            ),
            "average_peer_rating": _round(average_peer_rating),
            "average_clarity": _round(average_clarity),
            "gds_this_week": gds_this_week,
        },
        "recent_activity": activity[:5],
        "history": activity,
        "performance": rated_sessions,
    }
