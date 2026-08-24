import json
import uuid
from fastapi import WebSocket, WebSocketDisconnect
from app.database import async_session_maker
from app.config import settings
from app.models import SessionStatus
from app.websockets import manager
from app.services import matchmaking

async def on_session_complete(session_id: str):
    async with async_session_maker() as db:
        await matchmaking.update_session_status(db, uuid.UUID(session_id), SessionStatus.FEEDBACK)


async def on_preparation_complete(session_id: str):
    async with async_session_maker() as db:
        started = await matchmaking.begin_session_in_progress(
            db, uuid.UUID(session_id)
        )
    if not started:
        await manager.broadcast(session_id, {
            "type": "SESSION_START_CANCELLED",
            "payload": {"reason": "A seat reopened before the discussion began."},
        })
        return

    await manager.broadcast(session_id, {
        "type": "SESSION_STARTED",
        "payload": {"duration": settings.GD_DISCUSSION_DURATION},
    })
    await manager.start_timer(
        session_id, settings.GD_DISCUSSION_DURATION, on_session_complete
    )


async def deactivate_disconnected_participant(
    session_id: str, participant_id: str
) -> tuple[bool, bool]:
    """Persist a dropped active connection without erasing round membership."""
    async with async_session_maker() as db:
        session = await matchmaking.get_session_detail(db, uuid.UUID(session_id))
        if not session or session.status not in (
            SessionStatus.FILLING,
            SessionStatus.STARTING,
            SessionStatus.IN_PROGRESS,
        ):
            return False, False
        return await matchmaking.leave_session(
            db, uuid.UUID(session_id), uuid.UUID(participant_id)
        )


async def get_host_participant_id(session_id: str) -> str | None:
    async with async_session_maker() as db:
        session = await matchmaking.get_session_detail(db, uuid.UUID(session_id))
        host = matchmaking.get_host_participant(session) if session else None
        return str(host.id) if host else None


async def broadcast_host_update(session_id: str) -> None:
    await manager.broadcast(
        session_id,
        {
            "type": "HOST_UPDATED",
            "payload": {"hostParticipantId": await get_host_participant_id(session_id)},
        },
    )


async def session_websocket_endpoint(websocket: WebSocket, session_id: str, participant_id: str):
    try:
        parsed_session_id = uuid.UUID(session_id)
        parsed_participant_id = uuid.UUID(participant_id)
    except ValueError:
        await websocket.close(code=1008, reason="Invalid session or participant ID")
        return

    async with async_session_maker() as db:
        session_info = await matchmaking.get_session_detail(db, parsed_session_id)
        participant = next(
            (
                item
                for item in session_info.participants
                if item.id == parsed_participant_id and item.is_active
            ),
            None,
        ) if session_info else None
        if not participant:
            await websocket.close(code=1008, reason="Active participant not found")
            return
        host = matchmaking.get_host_participant(session_info)

    await manager.connect(session_id, participant_id, websocket)
    try:
        await manager.send_personal(session_id, participant_id, {
            "type": "SESSION_STATE",
            "payload": {
                "sessionId": session_id,
                "participants": manager.get_participant_ids(session_id),
                "arenaParticipants": manager.get_arena_participants(session_id),
                "status": session_info.status.value,
                "hostParticipantId": str(host.id) if host else None,
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
                async with async_session_maker() as db:
                    _, start_cancelled = await matchmaking.leave_session(
                        db, parsed_session_id, parsed_participant_id
                    )
                await manager.disconnect(session_id, participant_id)
                await manager.broadcast(session_id, {
                    "type": "QUEUE_UPDATED",
                    "payload": {"participants": manager.get_participant_ids(session_id)}
                })
                if start_cancelled:
                    await manager.stop_timer(session_id)
                    await manager.broadcast(session_id, {
                        "type": "SESSION_START_CANCELLED",
                        "payload": {"reason": "A participant left before the round started."},
                    })
                await broadcast_host_update(session_id)
                break
            elif msg_type == "ARENA_JOINED":
                host_participant_id = await get_host_participant_id(session_id)
                arena_participant = {
                    "participantId": participant_id,
                    "alias": participant.alias,
                    "agoraUid": participant.agora_uid,
                    "micEnabled": participant.mic_on,
                    "seatIndex": participant.seat_index,
                    "isHost": host_participant_id == participant_id,
                }
                manager.set_arena_participant(
                    session_id, participant_id, arena_participant
                )
                await manager.broadcast(session_id, {
                    "type": "USER_JOINED_ARENA",
                    "payload": arena_participant,
                })
                await broadcast_host_update(session_id)
            elif msg_type == "LEAVE_ARENA":
                async with async_session_maker() as db:
                    _, start_cancelled = await matchmaking.leave_session(
                        db, parsed_session_id, parsed_participant_id
                    )
                await manager.disconnect(session_id, participant_id)
                await manager.broadcast(session_id, {
                    "type": "USER_LEFT_ARENA",
                    "payload": {"participantId": participant_id}
                })
                if start_cancelled:
                    await manager.stop_timer(session_id)
                    await manager.broadcast(session_id, {
                        "type": "QUEUE_UPDATED",
                        "payload": {"participants": manager.get_participant_ids(session_id)},
                    })
                    await manager.broadcast(session_id, {
                        "type": "SESSION_START_CANCELLED",
                        "payload": {"reason": "A participant left during preparation."},
                    })
                await broadcast_host_update(session_id)
                break
            elif msg_type == "motion_data":
                await manager.broadcast_except(session_id, participant_id, {
                    "type": "motion_broadcast",
                    "payload": {"participantId": participant_id, "data": payload}
                })
            elif msg_type == "mic_status":
                mic_enabled = payload.get("enabled")
                if not isinstance(mic_enabled, bool):
                    continue
                async with async_session_maker() as db:
                    await matchmaking.update_participant_media_state(
                        db,
                        parsed_session_id,
                        parsed_participant_id,
                        mic_on=mic_enabled,
                    )
                manager.update_arena_participant(
                    session_id, participant_id, micEnabled=mic_enabled
                )
                await manager.broadcast(session_id, {
                    "type": "mic_status",
                    "payload": {
                        "participantId": participant_id,
                        "agoraUid": participant.agora_uid,
                        "enabled": mic_enabled,
                    }
                })
            elif msg_type == "camera_status":
                camera_enabled = payload.get("enabled")
                if not isinstance(camera_enabled, bool):
                    continue
                async with async_session_maker() as db:
                    await matchmaking.update_participant_media_state(
                        db,
                        parsed_session_id,
                        parsed_participant_id,
                        camera_on=camera_enabled,
                    )
                await manager.broadcast(session_id, {
                    "type": "camera_status",
                    "payload": {
                        "participantId": participant_id,
                        "agoraUid": participant.agora_uid,
                        "enabled": camera_enabled,
                    }
                })
            elif msg_type == "chat":
                await manager.broadcast(session_id, {
                    "type": "chat",
                    "payload": {"participantId": participant_id, "message": payload.get("message")}
                })
            elif msg_type == "start_session":
                if len(manager.get_participant_ids(session_id)) >= settings.MAX_SEATS:
                    async with async_session_maker() as db:
                        starting = await matchmaking.begin_session_starting(
                            db, parsed_session_id
                        )
                    if starting:
                        await manager.broadcast(session_id, {
                            "type": "SESSION_STARTING",
                            "payload": {
                                "preparationDuration": settings.GD_PREPARATION_DURATION,
                                "discussionDuration": settings.GD_DISCUSSION_DURATION,
                            },
                        })
                        await manager.start_preparation(
                            session_id,
                            settings.GD_PREPARATION_DURATION,
                            on_preparation_complete,
                        )
            elif msg_type == "complete_session":
                if not manager.has_arena_participant(session_id, participant_id):
                    await manager.send_personal(session_id, participant_id, {
                        "type": "SESSION_ACTION_REJECTED",
                        "payload": {
                            "action": "complete_session",
                            "reason": "Only an active arena host can complete the session.",
                        },
                    })
                    continue
                async with async_session_maker() as db:
                    session = await matchmaking.get_session_detail(db, parsed_session_id)
                    if not session or session.status != SessionStatus.IN_PROGRESS:
                        await manager.send_personal(session_id, participant_id, {
                            "type": "SESSION_ACTION_REJECTED",
                            "payload": {
                                "action": "complete_session",
                                "reason": "The discussion is not currently in progress.",
                            },
                        })
                        continue
                    host = matchmaking.get_host_participant(session)
                    if not host or str(host.id) != participant_id:
                        await manager.send_personal(session_id, participant_id, {
                            "type": "SESSION_ACTION_REJECTED",
                            "payload": {
                                "action": "complete_session",
                                "reason": "Only the current room host can complete the session.",
                                "hostParticipantId": str(host.id) if host else None,
                            },
                        })
                        continue
                    await matchmaking.update_session_status(
                        db, parsed_session_id, SessionStatus.FEEDBACK
                    )
                await manager.stop_timer(session_id)
                await manager.broadcast(session_id, {
                    "type": "SESSION_COMPLETED",
                    "payload": {
                        "sessionId": session_id,
                        "feedbackOpen": True,
                        "completedByParticipant": participant_id,
                    },
                })

    except WebSocketDisconnect:
        left, start_cancelled = await deactivate_disconnected_participant(
            session_id, participant_id
        )
        await manager.disconnect(session_id, participant_id)
        if left:
            await manager.broadcast(session_id, {
                "type": "QUEUE_UPDATED",
                "payload": {"participants": manager.get_participant_ids(session_id)},
            })
        if start_cancelled:
            await manager.stop_timer(session_id)
            await manager.broadcast(session_id, {
                "type": "SESSION_START_CANCELLED",
                "payload": {"reason": "A participant disconnected before the round started."},
            })
        await manager.broadcast(session_id, {
            "type": "USER_LEFT_ARENA",
            "payload": {"participantId": participant_id}
        })
        await broadcast_host_update(session_id)
    except Exception:
        left, start_cancelled = await deactivate_disconnected_participant(
            session_id, participant_id
        )
        await manager.disconnect(session_id, participant_id)
        if left:
            await manager.broadcast(session_id, {
                "type": "QUEUE_UPDATED",
                "payload": {"participants": manager.get_participant_ids(session_id)},
            })
        if start_cancelled:
            await manager.stop_timer(session_id)
            await manager.broadcast(session_id, {
                "type": "SESSION_START_CANCELLED",
                "payload": {"reason": "A participant disconnected before the round started."},
            })
        await manager.broadcast(session_id, {
            "type": "USER_LEFT_ARENA",
            "payload": {"participantId": participant_id},
        })
        await broadcast_host_update(session_id)
