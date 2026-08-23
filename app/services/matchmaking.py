import random
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models import GDSession, SessionStatus, Participant
from app.config import settings

async def list_open_sessions(db: AsyncSession) -> list[dict]:
    query = select(GDSession).where(
        GDSession.status.in_([SessionStatus.FILLING, SessionStatus.IN_PROGRESS])
    ).options(selectinload(GDSession.participants))
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    response = []
    now = datetime.now(timezone.utc)
    for session in sessions:
        active_participants = [p for p in session.participants if p.is_active]
        starts_in = max(0, int((session.starts_at - now).total_seconds())) if session.starts_at else 0
        response.append({
            "id": session.id,
            "topic": session.topic,
            "status": session.status,
            "max_seats": session.max_seats,
            "occupied_seats": len(active_participants),
            "starts_in_seconds": starts_in,
        })
    return response

async def get_session_detail(db: AsyncSession, session_id: uuid.UUID) -> Optional[GDSession]:
    query = select(GDSession).where(GDSession.id == session_id).options(selectinload(GDSession.participants))
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def join_session(
    db: AsyncSession, 
    session_id: uuid.UUID, 
    alias: str, 
    avatar_color: str, 
    mic_on: bool, 
    cam_on: bool, 
    user_id: Optional[uuid.UUID] = None
) -> Participant:
    session = await get_session_detail(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session.status != SessionStatus.FILLING:
        raise HTTPException(status_code=409, detail="Session is not accepting participants")
        
    active_participants = [p for p in session.participants if p.is_active]
    if len(active_participants) >= session.max_seats:
        raise HTTPException(status_code=409, detail="Session is full")
        
    for p in active_participants:
        if p.alias == alias:
            raise HTTPException(status_code=400, detail="Alias already taken in this session")
            
    seat_index = len(active_participants) + 1
    agora_uid = random.randint(10000, 99999)
    
    participant = Participant(
        id=uuid.uuid4(),
        session_id=session.id,
        user_id=user_id,
        alias=alias,
        avatar_color=avatar_color,
        seat_index=seat_index,
        agora_uid=agora_uid,
        is_active=True,
        mic_on=mic_on,
        cam_on=cam_on,
        joined_at=datetime.now(timezone.utc)
    )
    
    db.add(participant)
    session.participants.append(participant)
    await db.commit()
    await db.refresh(participant)
    
    active_participants = [p for p in session.participants if p.is_active]
    if len(active_participants) >= session.max_seats:
        await check_auto_start(db, session)
        
    return participant

async def leave_session(db: AsyncSession, session_id: uuid.UUID, participant_id: uuid.UUID) -> bool:
    query = select(Participant).where(
        and_(Participant.session_id == session_id, Participant.id == participant_id)
    )
    result = await db.execute(query)
    participant = result.scalar_one_or_none()
    
    if not participant or not participant.is_active:
        return False
        
    participant.is_active = False
    participant.left_at = datetime.now(timezone.utc)
    await db.commit()
    return True

async def check_auto_start(db: AsyncSession, session: GDSession) -> bool:
    active_participants = [p for p in session.participants if p.is_active]
    if len(active_participants) >= session.max_seats and session.status == SessionStatus.FILLING:
        session.status = SessionStatus.IN_PROGRESS
        session.started_at = datetime.now(timezone.utc)
        await db.commit()
        return True
    return False
