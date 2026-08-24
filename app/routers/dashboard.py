from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.dashboard import get_registered_user_dashboard
from app.utils.dependencies import get_current_user


router = APIRouter(prefix="/api/users/me", tags=["Dashboard"])


@router.get("/dashboard")
async def registered_user_dashboard(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_registered_user_dashboard(db, current_user)
