from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.feedback import FeedbackSubmission, FeedbackSummaryResponse
from app.services import feedback

router = APIRouter(prefix="/api/sessions", tags=["Feedback"])

@router.post("/{session_id}/feedback")
async def submit_feedback(session_id: str, request: FeedbackSubmission, db: AsyncSession = Depends(get_db)):
    count = await feedback.submit_ratings(db, session_id, request)
    return {"message": "Feedback submitted successfully", "count": count}

@router.get("/{session_id}/feedback/summary", response_model=FeedbackSummaryResponse)
async def get_feedback_summary(session_id: str, db: AsyncSession = Depends(get_db)):
    return await feedback.get_feedback_summary(db, session_id)
