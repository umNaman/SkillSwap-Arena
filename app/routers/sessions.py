import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.schemas.session import SessionListResponse, SessionDetail, JoinSessionRequest, JoinSessionResponse
from app.services import matchmaking
from app.services.identity import validate_avatar_color
from app.utils.dependencies import get_current_user_optional
from app.websockets import manager

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])

class LeaveSessionRequest(BaseModel):
    participant_id: str

@router.get("/", response_model=SessionListResponse)
async def list_sessions(db: AsyncSession = Depends(get_db)):
    connected_session_ids = {
        uuid.UUID(session_id) for session_id in manager.get_connected_session_ids()
    }
    return {
        "sessions": await matchmaking.list_open_sessions(db, connected_session_ids)
    }

@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    session = await matchmaking.get_session_detail(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return matchmaking.serialize_session(session)

@router.post("/{session_id}/join", response_model=JoinSessionResponse)
async def join_session(
    session_id: uuid.UUID,
    request: JoinSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    if not validate_avatar_color(request.avatar_color):
        raise HTTPException(status_code=422, detail="Invalid avatar color")
    return await matchmaking.join_session(
        db,
        session_id,
        request.alias,
        request.avatar_color,
        request.mic_enabled,
        request.cam_enabled,
        current_user.id if current_user else None,
    )

@router.post("/{session_id}/leave")
async def leave_session(session_id: uuid.UUID, request: LeaveSessionRequest, db: AsyncSession = Depends(get_db)):
    try:
        participant_id = uuid.UUID(request.participant_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid participant ID")
    left, _ = await matchmaking.leave_session(db, session_id, participant_id)
    if not left:
        raise HTTPException(status_code=404, detail="Active participant not found")
    return {"message": "Successfully left session"}
