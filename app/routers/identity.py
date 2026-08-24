from fastapi import APIRouter
from app.schemas.participant import RandomAliasResponse, IdentityRequest, IdentityResponse
from app.services import identity

router = APIRouter(prefix="/api", tags=["Identity"])

@router.get("/alias/random", response_model=RandomAliasResponse)
async def get_random_alias():
    alias = identity.generate_random_alias()
    return {"alias": alias}

@router.post("/identity", response_model=IdentityResponse)
async def create_identity(request: IdentityRequest):
    return identity.create_identity(request.alias, request.avatar_color)
