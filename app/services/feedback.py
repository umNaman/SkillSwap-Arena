import uuid
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models import PeerRating, GDSession, SessionStatus, Participant

async def submit_ratings(db: AsyncSession, session_id: uuid.UUID, rater_id: uuid.UUID, ratings: list) -> List[PeerRating]:
    # Check session
    query = select(GDSession).where(GDSession.id == session_id).options(selectinload(GDSession.participants))
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session.status not in [SessionStatus.FEEDBACK, SessionStatus.COMPLETED]:
        raise HTTPException(status_code=400, detail="Session is not in feedback or completed state")
        
    # Check rater
    rater = next((p for p in session.participants if p.id == rater_id), None)
    if not rater:
        raise HTTPException(status_code=400, detail="Rater is not a participant in this session")
        
    created_ratings = []
    for r in ratings:
        rating_obj = PeerRating(
            id=uuid.uuid4(),
            session_id=session_id,
            rater_id=rater_id,
            ratee_id=r.ratee_id,
            communication=r.communication,
            confidence=r.confidence,
            relevance=r.relevance,
            participation=r.participation,
            leadership=r.leadership
        )
        db.add(rating_obj)
        created_ratings.append(rating_obj)
        
    await db.commit()
    for rating_obj in created_ratings:
        await db.refresh(rating_obj)
        
    return created_ratings

async def get_feedback_summary(db: AsyncSession, session_id: uuid.UUID) -> List[dict]:
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
            "total_raters": row.total_raters
        })
    return summary
