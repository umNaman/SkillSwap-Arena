"""Hold matchmaking/WebSocket participants for browser UI verification."""

import asyncio
import json
import sys

import httpx
import websockets


async def main(base_url: str, participant_count: int = 5) -> None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        sessions = (await client.get(f"{base_url}/api/sessions/")).json()["sessions"]
        room = next(item for item in sessions if item["status"] == "filling")
        participants = []
        for index in range(participant_count):
            response = await client.post(
                f"{base_url}/api/sessions/{room['id']}/join",
                json={
                    "alias": f"NavBot{index + 1}",
                    "avatar_color": "#38D9C9",
                    "mic_enabled": True,
                    "cam_enabled": False,
                },
            )
            response.raise_for_status()
            participants.append(response.json())

    ws_base = base_url.replace("http://", "ws://")
    sockets = []
    listeners = []

    async def follow_session(websocket) -> None:
        async for raw_message in websocket:
            message = json.loads(raw_message)
            if message.get("type") == "SESSION_STARTING":
                await websocket.send(json.dumps({"type": "ARENA_JOINED", "payload": {}}))

    try:
        for participant in participants:
            websocket = await websockets.connect(
                f"{ws_base}/ws/sessions/{room['id']}/{participant['participant_id']}"
            )
            await websocket.recv()
            await websocket.send(json.dumps({"type": "JOIN_WAITING_ROOM", "payload": {}}))
            sockets.append(websocket)
            listeners.append(asyncio.create_task(follow_session(websocket)))
        print(json.dumps({"ready": True, "session_id": room["id"]}), flush=True)
        await asyncio.Event().wait()
    finally:
        for listener in listeners:
            listener.cancel()
        for websocket in sockets:
            await websocket.close()


if __name__ == "__main__":
    try:
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        asyncio.run(main(sys.argv[1], count))
    except KeyboardInterrupt:
        pass
