import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import AIInsight, InsightStatus
from app.models import GDSession
from app.config import settings
from app.database import async_session_maker
from fastapi import HTTPException

logger = logging.getLogger(__name__)

async def trigger_analysis(db: AsyncSession, session_id: uuid.UUID, audio_data: Optional[bytes] = None) -> AIInsight:
    session = (await db.execute(select(GDSession).where(GDSession.id == session_id))).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    insight = AIInsight(
        id=uuid.uuid4(),
        session_id=session_id,
        status=InsightStatus.PENDING,
        created_at=datetime.now(timezone.utc)
    )
    db.add(insight)
    await db.commit()
    await db.refresh(insight)
    return insight

async def process_analysis(db: AsyncSession, insight_id: uuid.UUID, audio_data: Optional[bytes] = None) -> None:
    query = select(AIInsight).where(AIInsight.id == insight_id)
    result = await db.execute(query)
    insight = result.scalar_one_or_none()
    
    if not insight:
        logger.error(f"Insight {insight_id} not found.")
        return
        
    insight.status = InsightStatus.PROCESSING
    await db.commit()
    
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        insight.status = InsightStatus.FAILED
        insight.error_message = "AI analysis is unavailable because OPENAI_API_KEY is not configured."
        await db.commit()
        return

    if not audio_data:
        insight.status = InsightStatus.FAILED
        insight.error_message = "AI analysis requires a real session audio recording."
        await db.commit()
        return

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Step 1: Transcription
            files = {'file': ('audio.m4a', audio_data, 'audio/m4a')}
            data = {'model': 'whisper-1'}
            headers = {'Authorization': f'Bearer {api_key}'}
            transcription_response = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers=headers,
                files=files,
                data=data
            )
            transcription_response.raise_for_status()
            transcript = transcription_response.json().get('text', '')
            if not transcript.strip():
                raise ValueError("The supplied recording did not produce a transcript.")
            insight.transcription = transcript

            # Step 2: LLM analysis
            prompt = f"Analyze the following group discussion transcript:\n\n{transcript}\n\n"
            system_prompt = (
                "You are an expert AI evaluator for group discussions. "
                "Provide a JSON response with: 'strengths' (list of strings), 'improvements' (list of strings), "
                "'overall_score' (integer 0-100), and 'summary' (string)."
            )
            
            chat_payload = {
                "model": settings.OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"}
            }
            chat_headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            chat_response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=chat_headers,
                json=chat_payload
            )
            chat_response.raise_for_status()
            
            # Step 3: Parse response
            content = chat_response.json()['choices'][0]['message']['content']
            parsed_data = json.loads(content)
            
            insight.strengths = parsed_data.get('strengths', [])
            insight.improvements = parsed_data.get('improvements', [])
            insight.overall_score = parsed_data.get('overall_score', 0)
            insight.summary = parsed_data.get('summary', '')
            insight.status = InsightStatus.COMPLETED
            insight.generated_at = datetime.now(timezone.utc)
            
    except Exception as e:
        logger.error(f"Error processing AI insight {insight_id}: {e}")
        insight.status = InsightStatus.FAILED
        insight.error_message = str(e)
        
    finally:
        await db.commit()


async def process_analysis_task(insight_id: uuid.UUID, audio_data: Optional[bytes] = None) -> None:
    async with async_session_maker() as db:
        await process_analysis(db, insight_id, audio_data)


async def get_session_insights(db: AsyncSession, session_id: uuid.UUID) -> dict:
    insights = (
        await db.execute(
            select(AIInsight)
            .where(AIInsight.session_id == session_id)
            .order_by(AIInsight.created_at.desc())
        )
    ).scalars().all()
    return {
        "insights": [
            {
                "session_id": insight.session_id,
                "participant_id": insight.participant_id,
                "transcription": insight.transcription,
                "strengths": insight.strengths or [],
                "improvements": insight.improvements or [],
                "overall_score": insight.overall_score,
                "summary": insight.summary,
                "status": insight.status.value,
                "generated_at": insight.generated_at,
            }
            for insight in insights
        ]
    }
