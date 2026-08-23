from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.identity import RandomAliasResponse, IdentityRequest, IdentityResponse
from app.services import identity

router = APIRouter(prefix="/api", tags=["Identity"])

@router.get("/alias/random", response_model=RandomAliasResponse)
async def get_random_alias():
    alias = await identity.generate_random_alias()
    return {"alias": alias}

@router.post("/identity", response_model=IdentityResponse)
async def create_identity(request: IdentityRequest, db: AsyncSession = Depends(get_db)):
    return await identity.create_identity(db, request)
