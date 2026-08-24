import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Literal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Participant
from app.services import agora

router = APIRouter(prefix="/api/sessions", tags=["Agora"])

class AgoraTokenRequest(BaseModel):
    participant_id: uuid.UUID
    role: Literal["publisher", "subscriber"] = "publisher"

@router.post("/{session_id}/agora-token")
async def generate_agora_token(
    session_id: uuid.UUID,
    request: AgoraTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    participant = (
        await db.execute(
            select(Participant).where(
                Participant.id == request.participant_id,
                Participant.session_id == session_id,
                Participant.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if not participant:
        raise HTTPException(status_code=404, detail="Active participant not found")
    role = 1 if request.role == "publisher" else 2
    try:
        return agora.generate_rtc_token(str(session_id), participant.agora_uid, role)
    except agora.AgoraConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
