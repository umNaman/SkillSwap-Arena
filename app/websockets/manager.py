import asyncio
import json
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # {session_id: {participant_id: WebSocket}}
        self.rooms: dict[str, dict[str, WebSocket]] = {}
        # {session_id: {participant_id: public arena presence data}}
        self.arena_participants: dict[str, dict[str, dict]] = {}
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
            self.arena_participants.get(session_id, {}).pop(participant_id, None)
            if not self.rooms[session_id]:
                del self.rooms[session_id]
                self.arena_participants.pop(session_id, None)
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

    def get_connected_session_ids(self) -> set[str]:
        return {session_id for session_id, room in self.rooms.items() if room}

    def set_arena_participant(self, session_id: str, participant_id: str, data: dict) -> None:
        self.arena_participants.setdefault(session_id, {})[participant_id] = data

    def update_arena_participant(self, session_id: str, participant_id: str, **changes) -> None:
        participant = self.arena_participants.get(session_id, {}).get(participant_id)
        if participant:
            participant.update(changes)

    def get_arena_participants(self, session_id: str) -> list[dict]:
        return list(self.arena_participants.get(session_id, {}).values())

    def has_arena_participant(self, session_id: str, participant_id: str) -> bool:
        return participant_id in self.arena_participants.get(session_id, {})

    async def start_timer(self, session_id: str, duration: int, on_complete=None) -> None:
        if session_id in self.timers:
            self.timers[session_id].cancel()
        self.timers[session_id] = asyncio.create_task(
            self._run_timer(session_id, duration, on_complete)
        )

    async def start_preparation(
        self, session_id: str, duration: int, on_complete=None
    ) -> None:
        if session_id in self.timers:
            self.timers[session_id].cancel()
        self.timers[session_id] = asyncio.create_task(
            self._run_preparation(session_id, duration, on_complete)
        )

    async def stop_timer(self, session_id: str) -> None:
        if session_id in self.timers:
            self.timers[session_id].cancel()
            del self.timers[session_id]

    async def _run_timer(self, session_id: str, duration: int, on_complete=None) -> None:
        current_task = asyncio.current_task()
        try:
            for remaining in range(duration, 0, -1):
                await self.broadcast(session_id, {
                    "type": "TIMER_TICK",
                    "payload": {"remainingSeconds": remaining}
                })
                await asyncio.sleep(1)
            if on_complete:
                await on_complete(session_id)
            await self.broadcast(session_id, {
                "type": "SESSION_COMPLETED",
                "payload": {"sessionId": session_id, "feedbackOpen": True}
            })
        except asyncio.CancelledError:
            pass
        finally:
            if self.timers.get(session_id) is current_task:
                self.timers.pop(session_id, None)

    async def _run_preparation(
        self, session_id: str, duration: int, on_complete=None
    ) -> None:
        current_task = asyncio.current_task()
        try:
            for remaining in range(duration, 0, -1):
                await self.broadcast(session_id, {
                    "type": "PREPARATION_TICK",
                    "payload": {"remainingSeconds": remaining},
                })
                await asyncio.sleep(1)
            if self.timers.get(session_id) is current_task:
                self.timers.pop(session_id, None)
            if on_complete:
                await on_complete(session_id)
        except asyncio.CancelledError:
            pass
        finally:
            if self.timers.get(session_id) is current_task:
                self.timers.pop(session_id, None)
