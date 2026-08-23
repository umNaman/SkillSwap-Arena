import json
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.websockets import manager
from app.services import matchmaking, agora

async def on_session_complete(session_id: str):
    async with AsyncSessionLocal() as db:
        await matchmaking.update_session_status(db, session_id, "feedback")
        await db.commit()

async def session_websocket_endpoint(websocket: WebSocket, session_id: str, participant_id: str):
    await manager.connect(session_id, participant_id, websocket)
    try:
        async with AsyncSessionLocal() as db:
            session_info = await matchmaking.get_session_detail(db, session_id)
            status = getattr(session_info, "status", "unknown") if session_info else "unknown"
            
            await manager.send_personal(session_id, participant_id, {
                "type": "SESSION_STATE",
                "payload": {
                    "sessionId": session_id,
                    "participants": manager.get_participant_ids(session_id),
                    "status": status
                }
            })
            
            token = await agora.generate_rtc_token(session_id, participant_id, "publisher")
            await manager.send_personal(session_id, participant_id, {
                "type": "AGORA_TOKEN",
                "payload": {
                    "token": token,
                    "channelName": session_id
                }
            })

        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except Exception:
                continue
            
            msg_type = msg.get("type")
            payload = msg.get("payload", {})

            if msg_type == "JOIN_WAITING_ROOM":
                await manager.broadcast(session_id, {
                    "type": "QUEUE_UPDATED",
                    "payload": {"participants": manager.get_participant_ids(session_id)}
                })
            elif msg_type == "LEAVE_WAITING_ROOM":
                await manager.disconnect(session_id, participant_id)
                await manager.broadcast(session_id, {
                    "type": "QUEUE_UPDATED",
                    "payload": {"participants": manager.get_participant_ids(session_id)}
                })
            elif msg_type == "ARENA_JOINED":
                agora_uid = payload.get("agora_uid")
                await manager.broadcast(session_id, {
                    "type": "USER_JOINED_ARENA",
                    "payload": {"participantId": participant_id, "agoraUid": agora_uid}
                })
            elif msg_type == "LEAVE_ARENA":
                async with AsyncSessionLocal() as db:
                    await matchmaking.leave_session(db, session_id, participant_id)
                await manager.broadcast(session_id, {
                    "type": "USER_LEFT_ARENA",
                    "payload": {"participantId": participant_id}
                })
            elif msg_type == "motion_data":
                await manager.broadcast_except(session_id, participant_id, {
                    "type": "motion_broadcast",
                    "payload": {"participantId": participant_id, "data": payload}
                })
            elif msg_type == "mic_status":
                await manager.broadcast(session_id, {
                    "type": "mic_status",
                    "payload": {"participantId": participant_id, "status": payload.get("status")}
                })
            elif msg_type == "camera_status":
                await manager.broadcast(session_id, {
                    "type": "camera_status",
                    "payload": {"participantId": participant_id, "status": payload.get("status")}
                })
            elif msg_type == "chat":
                await manager.broadcast(session_id, {
                    "type": "chat",
                    "payload": {"participantId": participant_id, "message": payload.get("message")}
                })
            elif msg_type == "start_session":
                participants = manager.get_participant_ids(session_id)
                if len(participants) > 0:
                    await manager.start_timer(session_id, 900, on_session_complete)
                    await manager.broadcast(session_id, {
                        "type": "SESSION_STARTING",
                        "payload": {"duration": 900}
                    })

    except WebSocketDisconnect:
        await manager.disconnect(session_id, participant_id)
        await manager.broadcast(session_id, {
            "type": "USER_LEFT_ARENA",
            "payload": {"participantId": participant_id}
        })
    except Exception as e:
        await manager.disconnect(session_id, participant_id)
