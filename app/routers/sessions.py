from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.schemas.session import SessionListResponse, SessionDetail, JoinSessionRequest, JoinSessionResponse
from app.services import matchmaking

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])

class LeaveSessionRequest(BaseModel):
    participant_id: str

@router.get("/", response_model=SessionListResponse)
async def list_sessions(db: AsyncSession = Depends(get_db)):
    return await matchmaking.list_open_sessions(db)

@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await matchmaking.get_session_detail(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session

@router.post("/{session_id}/join", response_model=JoinSessionResponse)
async def join_session(session_id: str, request: JoinSessionRequest, db: AsyncSession = Depends(get_db)):
    return await matchmaking.join_session(db, session_id, request)

@router.post("/{session_id}/leave")
async def leave_session(session_id: str, request: LeaveSessionRequest, db: AsyncSession = Depends(get_db)):
    await matchmaking.leave_session(db, session_id, request.participant_id)
    return {"message": "Successfully left session"}
