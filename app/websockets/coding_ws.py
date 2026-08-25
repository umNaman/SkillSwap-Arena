import json
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from app.config import settings
from app.database import async_session_maker
from app.models import CodingBattle, User


class CodingConnectionManager:
    def __init__(self):
        self.rooms: dict[str, dict[str, WebSocket]] = {}
        self.states: dict[str, dict[str, str]] = {}

    async def connect(self, battle_id: str, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.rooms.setdefault(battle_id, {})[user_id] = websocket
        self.states.setdefault(battle_id, {})[user_id] = "Reading Problem"

    async def disconnect(self, battle_id: str, user_id: str):
        self.rooms.get(battle_id, {}).pop(user_id, None)
        self.states.get(battle_id, {}).pop(user_id, None)

    async def broadcast(self, battle_id: str, message: dict):
        for uid, socket in list(self.rooms.get(battle_id, {}).items()):
            try: await socket.send_json(message)
            except Exception: await self.disconnect(battle_id, uid)


coding_manager = CodingConnectionManager()


def _user_id_from_token(token: str) -> uuid.UUID | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return uuid.UUID(payload.get("sub", ""))
    except (JWTError, ValueError, TypeError):
        return None


async def notify_battle_result(battle_id: str, winner_id: str, seconds: int):
    await coding_manager.broadcast(battle_id, {"type": "BATTLE_COMPLETED",
        "payload": {"winner_id": winner_id, "winner_seconds": seconds}})


async def coding_websocket_endpoint(websocket: WebSocket, battle_id: str, token: str):
    user_id = _user_id_from_token(token)
    if not user_id:
        await websocket.close(code=1008, reason="Invalid token"); return
    try: parsed_battle_id = uuid.UUID(battle_id)
    except ValueError:
        await websocket.close(code=1008, reason="Invalid battle"); return
    async with async_session_maker() as db:
        battle = await db.get(CodingBattle, parsed_battle_id)
        user = await db.get(User, user_id)
        if not battle or not user or user_id not in {battle.player_one_id, battle.player_two_id}:
            await websocket.close(code=1008, reason="Battle access denied"); return
    uid = str(user_id)
    await coding_manager.connect(battle_id, uid, websocket)
    await coding_manager.broadcast(battle_id, {"type": "BATTLE_STATE", "payload": {
        "connected": len(coding_manager.rooms.get(battle_id, {})),
        "states": coding_manager.states.get(battle_id, {})}})
    try:
        while True:
            raw = await websocket.receive_text()
            try: data = json.loads(raw)
            except json.JSONDecodeError: continue
            if data.get("type") == "STATUS":
                state = data.get("payload", {}).get("state")
                if state in {"Reading Problem", "Coding", "Testing", "Submitted"}:
                    coding_manager.states[battle_id][uid] = state
                    await coding_manager.broadcast(battle_id, {"type": "OPPONENT_STATUS",
                        "payload": {"user_id": uid, "state": state}})
            elif data.get("type") == "PING":
                await websocket.send_json({"type": "PONG", "payload": {}})
    except WebSocketDisconnect:
        await coding_manager.disconnect(battle_id, uid)
        await coding_manager.broadcast(battle_id, {"type": "BATTLE_STATE", "payload": {
            "connected": len(coding_manager.rooms.get(battle_id, {})),
            "states": coding_manager.states.get(battle_id, {})}})
