import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.database import async_session_maker
from app.models import User, AttackSession
import uuid
import uuid as uuid_mod

# I will write an integration test using TestClient, but since FastAPI is async and the endpoints use async db, it might be easier to use httpx directly or pytest.
