import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.feedback import (
    FeedbackSubmission,
    FeedbackSummaryResponse,
    ParticipantReportResponse,
)
from app.services import feedback

router = APIRouter(prefix="/api/sessions", tags=["Feedback"])


@router.get("/{session_id}/rating-participants")
async def get_rating_participants(
    session_id: uuid.UUID,
    rater_participant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return {
        "session_id": session_id,
        "participants": await feedback.get_rateable_participants(
            db, session_id, rater_participant_id
        ),
    }

@router.post("/{session_id}/feedback")
async def submit_feedback(session_id: uuid.UUID, request: FeedbackSubmission, db: AsyncSession = Depends(get_db)):
    if request.session_id != session_id:
        raise HTTPException(status_code=400, detail="Path and body session IDs do not match")
    ratings = await feedback.submit_ratings(
        db, session_id, request.rater_participant_id, request.ratings
    )
    return {"message": "Feedback submitted successfully", "count": len(ratings)}

@router.get("/{session_id}/feedback/summary", response_model=FeedbackSummaryResponse)
async def get_feedback_summary(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return {
        "session_id": session_id,
        "summaries": await feedback.get_feedback_summary(db, session_id),
    }


@router.get(
    "/{session_id}/participants/{participant_id}/report",
    response_model=ParticipantReportResponse,
)
async def get_participant_report(
    session_id: uuid.UUID,
    participant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await feedback.get_participant_report(db, session_id, participant_id)
