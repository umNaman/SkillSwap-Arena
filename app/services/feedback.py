import uuid
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models import (
    AIInsight,
    InsightStatus,
    PeerRating,
    GDSession,
    SessionStatus,
    Participant,
)
from app.services.matchmaking import participants_who_took_part


async def get_rateable_participants(
    db: AsyncSession, session_id: uuid.UUID, rater_id: uuid.UUID
) -> List[dict]:
    session = (
        await db.execute(
            select(GDSession)
            .where(GDSession.id == session_id)
            .options(selectinload(GDSession.participants))
        )
    ).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status not in [SessionStatus.FEEDBACK, SessionStatus.COMPLETED]:
        raise HTTPException(status_code=409, detail="Peer rating is not open for this session")

    participants = participants_who_took_part(session)
    if not any(item.id == rater_id for item in participants):
        raise HTTPException(
            status_code=400,
            detail="Rater did not participate in the live discussion",
        )
    return [
        {
            "id": participant.id,
            "alias": participant.alias,
            "avatar_color": participant.avatar_color,
            "seat_index": participant.seat_index,
        }
        for participant in participants
        if participant.id != rater_id
    ]

async def submit_ratings(db: AsyncSession, session_id: uuid.UUID, rater_id: uuid.UUID, ratings: list) -> List[PeerRating]:
    # Check session
    query = select(GDSession).where(GDSession.id == session_id).options(selectinload(GDSession.participants))
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session.status not in [SessionStatus.FEEDBACK, SessionStatus.COMPLETED]:
        raise HTTPException(status_code=400, detail="Session is not in feedback or completed state")
        
    participants_by_id = {
        participant.id: participant
        for participant in participants_who_took_part(session)
    }
    if rater_id not in participants_by_id:
        raise HTTPException(
            status_code=400,
            detail="Rater did not participate in the live discussion",
        )

    created_ratings = []
    seen_ratees: set[uuid.UUID] = set()
    for r in ratings:
        ratee_id = r.target_participant_id
        if ratee_id == rater_id:
            raise HTTPException(status_code=400, detail="Participants cannot rate themselves")
        if ratee_id not in participants_by_id:
            raise HTTPException(status_code=400, detail="Rating target did not participate in this discussion")
        if ratee_id in seen_ratees:
            raise HTTPException(status_code=400, detail="Duplicate rating target")
        seen_ratees.add(ratee_id)

        result = await db.execute(
            select(PeerRating).where(
                PeerRating.session_id == session_id,
                PeerRating.rater_id == rater_id,
                PeerRating.ratee_id == ratee_id,
            )
        )
        rating_obj = result.scalar_one_or_none()
        if rating_obj is None:
            rating_obj = PeerRating(
                id=uuid.uuid4(),
                session_id=session_id,
                rater_id=rater_id,
                ratee_id=ratee_id,
            )
            db.add(rating_obj)
        rating_obj.communication = r.metrics.communication
        rating_obj.confidence = r.metrics.confidence
        rating_obj.relevance = r.metrics.relevance
        rating_obj.participation = r.metrics.participation
        rating_obj.leadership = r.metrics.leadership
        rating_obj.feedback_text = r.feedback_text
        created_ratings.append(rating_obj)

    if session.status == SessionStatus.FEEDBACK:
        session.status = SessionStatus.COMPLETED

    await db.commit()
    for rating_obj in created_ratings:
        await db.refresh(rating_obj)
        
    return created_ratings

async def get_feedback_summary(db: AsyncSession, session_id: uuid.UUID) -> List[dict]:
    session_exists = (
        await db.execute(select(GDSession.id).where(GDSession.id == session_id))
    ).scalar_one_or_none()
    if not session_exists:
        raise HTTPException(status_code=404, detail="Session not found")

    query = select(
        PeerRating.ratee_id,
        func.avg(PeerRating.communication).label('avg_communication'),
        func.avg(PeerRating.confidence).label('avg_confidence'),
        func.avg(PeerRating.relevance).label('avg_relevance'),
        func.avg(PeerRating.participation).label('avg_participation'),
        func.avg(PeerRating.leadership).label('avg_leadership'),
        func.count(func.distinct(PeerRating.rater_id)).label('total_raters'),
        Participant.alias
    ).join(
        Participant, PeerRating.ratee_id == Participant.id
    ).where(
        PeerRating.session_id == session_id
    ).group_by(
        PeerRating.ratee_id, Participant.alias
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    summary = []
    for row in rows:
        summary.append({
            "participant_id": row.ratee_id,
            "alias": row.alias,
            "averages": {
                "communication": float(row.avg_communication) if row.avg_communication else 0,
                "confidence": float(row.avg_confidence) if row.avg_confidence else 0,
                "relevance": float(row.avg_relevance) if row.avg_relevance else 0,
                "participation": float(row.avg_participation) if row.avg_participation else 0,
                "leadership": float(row.avg_leadership) if row.avg_leadership else 0,
            },
            "total_raters": int(row.total_raters)
        })
    return summary


def _rating_overall(rating: PeerRating) -> float:
    return (
        rating.communication
        + rating.confidence
        + rating.relevance
        + rating.participation
        + rating.leadership
    ) / 5


async def get_participant_report(
    db: AsyncSession, session_id: uuid.UUID, participant_id: uuid.UUID
) -> dict:
    """Build a report only from feedback received by the requested participant."""
    session = (
        await db.execute(
            select(GDSession)
            .where(GDSession.id == session_id)
            .options(selectinload(GDSession.participants))
        )
    ).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    participants = participants_who_took_part(session)
    participant = next((item for item in participants if item.id == participant_id), None)
    if not participant:
        raise HTTPException(
            status_code=404,
            detail="Participant did not take part in this discussion",
        )

    received = (
        await db.execute(
            select(PeerRating).where(
                PeerRating.session_id == session_id,
                PeerRating.ratee_id == participant_id,
            )
        )
    ).scalars().all()
    received_count = len({rating.rater_id for rating in received})
    expected_count = max(0, len(participants) - 1)

    averages = None
    overall_rating = None
    if received:
        count = len(received)
        averages = {
            "communication": sum(item.communication for item in received) / count,
            "confidence": sum(item.confidence for item in received) / count,
            "relevance": sum(item.relevance for item in received) / count,
            "participation": sum(item.participation for item in received) / count,
            "leadership": sum(item.leadership for item in received) / count,
        }
        overall_rating = sum(averages.values()) / len(averages)

    all_session_ratings = (
        await db.execute(
            select(PeerRating).where(PeerRating.session_id == session_id)
        )
    ).scalars().all()
    room_average = (
        sum(_rating_overall(item) for item in all_session_ratings)
        / len(all_session_ratings)
        if all_session_ratings
        else None
    )

    insight = (
        await db.execute(
            select(AIInsight)
            .where(
                AIInsight.session_id == session_id,
                AIInsight.participant_id == participant_id,
                AIInsight.status == InsightStatus.COMPLETED,
            )
            .order_by(AIInsight.created_at.desc())
        )
    ).scalars().first()
    ai_analysis = None
    if insight and (insight.summary or insight.strengths or insight.improvements):
        ai_analysis = {
            "summary": insight.summary,
            "strengths": insight.strengths or [],
            "improvements": insight.improvements or [],
            "generated_at": insight.generated_at,
        }

    return {
        "session_id": session_id,
        "participant_id": participant_id,
        "alias": participant.alias,
        "received_count": received_count,
        "expected_count": expected_count,
        "overall_rating": overall_rating,
        "averages": averages,
        "room_average": room_average,
        "ai_analysis": ai_analysis,
        "speech_metrics_available": False,
    }
