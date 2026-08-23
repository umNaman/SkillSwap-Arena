from fastapi import APIRouter, Depends, BackgroundTasks, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database import get_db
from app.schemas.ai_insight import InsightListResponse
from app.services import ai_pipeline

router = APIRouter(prefix="/api/sessions", tags=["AI Insights"])

@router.post("/{session_id}/analyze")
async def analyze_session(
    session_id: str,
    background_tasks: BackgroundTasks,
    audio: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    insight = await ai_pipeline.trigger_analysis(db, session_id, audio)
    background_tasks.add_task(ai_pipeline.process_analysis, db, insight.id)
    return insight

@router.get("/{session_id}/insights", response_model=InsightListResponse)
async def get_insights(session_id: str, db: AsyncSession = Depends(get_db)):
    return await ai_pipeline.get_session_insights(db, session_id)
