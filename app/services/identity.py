import uuid
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models import Participant
from app.utils import alias_generator

VALID_COLORS: List[str] = ['#7C6FF0', '#38D9C9', '#FF6FA8', '#FFC94A', '#4FD1C5', '#9B8CFF']

def generate_random_alias() -> str:
    # Assuming there's a generate_alias function in app.utils.alias_generator
    try:
        return alias_generator.generate_alias()
    except AttributeError:
        # Fallback if alias_generator doesn't exist
        adjectives = ["Happy", "Swift", "Brave", "Calm", "Fierce", "Clever"]
        nouns = ["Panda", "Fox", "Tiger", "Owl", "Bear", "Lion"]
        import random
        return f"{random.choice(adjectives)}{random.choice(nouns)}{random.randint(10, 99)}"

def validate_avatar_color(color: str) -> bool:
    return color.upper() in [c.upper() for c in VALID_COLORS]

async def check_alias_available(db: AsyncSession, session_id: uuid.UUID, alias: str) -> bool:
    query = select(Participant).where(
        and_(
            Participant.session_id == session_id,
            Participant.alias == alias,
            Participant.is_active == True
        )
    )
    result = await db.execute(query)
    participant = result.scalar_one_or_none()
    return participant is None


def create_identity(alias: str, avatar_color: str) -> dict:
    cleaned_alias = alias.strip()
    return {
        "alias": cleaned_alias,
        "avatar_color": avatar_color,
        "valid": bool(cleaned_alias) and validate_avatar_color(avatar_color),
    }
