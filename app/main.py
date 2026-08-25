from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.config import settings
from app.database import async_session_maker, engine, init_db
from app.routers import agora, ai_insights, auth, coding_arena, dashboard, feedback, identity, sessions
from app.seed import seed_demo_data
from app.websockets.session_ws import session_websocket_endpoint
from app.websockets.coding_ws import coding_websocket_endpoint


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    async with async_session_maker() as db:
        await seed_demo_data(db)
    yield
    await engine.dispose()


app = FastAPI(
    title="SkillSwap API",
    version="1.0.0",
    lifespan=lifespan,
)

allow_all_origins = settings.CORS_ORIGINS == ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=not allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(sessions.router)
app.include_router(feedback.router)
app.include_router(identity.router)
app.include_router(agora.router)
app.include_router(ai_insights.router)
app.include_router(coding_arena.router)

app.mount("/static", StaticFiles(directory=PROJECT_ROOT / "static"), name="static")


@app.get("/health", tags=["System"])
async def health() -> dict[str, str]:
    async with async_session_maker() as db:
        await db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


@app.get("/", include_in_schema=False)
async def index_page() -> FileResponse:
    return FileResponse(PROJECT_ROOT / "index.html")


@app.get("/auth", include_in_schema=False)
@app.get("/auth.html", include_in_schema=False)
async def auth_page() -> FileResponse:
    return FileResponse(PROJECT_ROOT / "auth.html")


@app.get("/app", include_in_schema=False)
@app.get("/app.html", include_in_schema=False)
async def app_page() -> FileResponse:
    return FileResponse(PROJECT_ROOT / "app.html")


@app.get("/coding-arena", include_in_schema=False)
@app.get("/coding-arena.html", include_in_schema=False)
async def coding_arena_page() -> FileResponse:
    return FileResponse(PROJECT_ROOT / "coding-arena.html")


@app.get("/index.html", include_in_schema=False)
async def index_html() -> FileResponse:
    return FileResponse(PROJECT_ROOT / "index.html")


# Legacy redirect — keep old URL working
@app.get("/video_session.html", include_in_schema=False)
async def video_session_redirect() -> RedirectResponse:
    return RedirectResponse(url="/app")


@app.websocket("/ws/sessions/{session_id}/{participant_id}")
async def session_websocket(websocket: WebSocket, session_id: str, participant_id: str) -> None:
    await session_websocket_endpoint(websocket, session_id, participant_id)


@app.websocket("/ws/coding/{battle_id}")
async def coding_websocket(websocket: WebSocket, battle_id: str, token: str = "") -> None:
    await coding_websocket_endpoint(websocket, battle_id, token)
