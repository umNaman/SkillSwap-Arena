import asyncio
import json
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # {session_id: {participant_id: WebSocket}}
        self.rooms: dict[str, dict[str, WebSocket]] = {}
        # {session_id: asyncio.Task} for round timers
        self.timers: dict[str, asyncio.Task] = {}

    async def connect(self, session_id: str, participant_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if session_id not in self.rooms:
            self.rooms[session_id] = {}
        self.rooms[session_id][participant_id] = websocket

    async def disconnect(self, session_id: str, participant_id: str) -> None:
        if session_id in self.rooms:
            self.rooms[session_id].pop(participant_id, None)
            if not self.rooms[session_id]:
                del self.rooms[session_id]
                await self.stop_timer(session_id)

    async def broadcast(self, session_id: str, message: dict) -> None:
        if session_id in self.rooms:
            dead = []
            for pid, ws in self.rooms[session_id].items():
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append(pid)
            for pid in dead:
                self.rooms[session_id].pop(pid, None)

    async def broadcast_except(self, session_id: str, exclude_id: str, message: dict) -> None:
        if session_id in self.rooms:
            for pid, ws in self.rooms[session_id].items():
                if pid != exclude_id:
                    try:
                        await ws.send_json(message)
                    except Exception:
                        pass

    async def send_personal(self, session_id: str, participant_id: str, message: dict) -> None:
        if session_id in self.rooms and participant_id in self.rooms[session_id]:
            await self.rooms[session_id][participant_id].send_json(message)

    def get_participant_count(self, session_id: str) -> int:
        return len(self.rooms.get(session_id, {}))

    def get_participant_ids(self, session_id: str) -> list[str]:
        return list(self.rooms.get(session_id, {}).keys())

    async def start_timer(self, session_id: str, duration: int, on_complete=None) -> None:
        if session_id in self.timers:
            self.timers[session_id].cancel()
        self.timers[session_id] = asyncio.create_task(
            self._run_timer(session_id, duration, on_complete)
        )

    async def stop_timer(self, session_id: str) -> None:
        if session_id in self.timers:
            self.timers[session_id].cancel()
            del self.timers[session_id]

    async def _run_timer(self, session_id: str, duration: int, on_complete=None) -> None:
        try:
            for remaining in range(duration, 0, -1):
                await self.broadcast(session_id, {
                    "type": "TIMER_TICK",
                    "payload": {"remainingSeconds": remaining}
                })
                await asyncio.sleep(1)
            # Timer expired
            await self.broadcast(session_id, {
                "type": "SESSION_COMPLETED",
                "payload": {"sessionId": session_id, "feedbackOpen": True}
            })
            if on_complete:
                await on_complete(session_id)
        except asyncio.CancelledError:
            pass
        finally:
            self.timers.pop(session_id, None)
