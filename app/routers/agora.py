from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.services import agora

router = APIRouter(prefix="/api/sessions", tags=["Agora"])

class AgoraTokenRequest(BaseModel):
    participant_id: str
    role: Optional[str] = "publisher"

@router.post("/{session_id}/agora-token")
async def generate_agora_token(session_id: str, request: AgoraTokenRequest):
    token = await agora.generate_rtc_token(session_id, request.participant_id, request.role)
    return {"token": token, "channel_name": session_id}
