"""End-to-end persistence, host, lifecycle, and feedback integrity check.

Runs against a disposable SQLite database and a real Uvicorn process. It does
not touch the repository's working database or attempt to validate RTC audio.
"""

import asyncio
import json
import os
import signal
import socket
import sqlite3
import subprocess
import tempfile
from pathlib import Path

import httpx
import websockets


ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


async def wait_for_server(base_url: str) -> None:
    async with httpx.AsyncClient() as client:
        for _ in range(80):
            try:
                response = await client.get(f"{base_url}/health", timeout=0.5)
                if response.status_code == 200:
                    return
            except httpx.HTTPError:
                pass
            await asyncio.sleep(0.1)
    raise RuntimeError("Test server did not become healthy")


def start_server(database_path: Path, port: int) -> subprocess.Popen:
    env = os.environ.copy()
    env.update(
        {
            "DATABASE_URL": f"sqlite+aiosqlite:///{database_path}",
            "SECRET_KEY": "isolated-stabilization-check-secret-key",
            "SEED_DEMO_DATA": "false",
            "GD_PREPARATION_DURATION": "1",
            "GD_DISCUSSION_DURATION": "2",
            "GD_ROUND_DURATION": "3",
            "STALE_PRESTART_SESSION_SECONDS": "60",
        }
    )
    return subprocess.Popen(
        [str(ROOT / ".venv/bin/python"), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


async def recv_type(websocket, message_type: str, timeout: float = 8.0) -> dict:
    async def receive() -> dict:
        while True:
            message = json.loads(await websocket.recv())
            if message.get("type") == message_type:
                return message

    return await asyncio.wait_for(receive(), timeout=timeout)


async def join_six(client: httpx.AsyncClient, base_url: str, token: str):
    sessions = (await client.get(f"{base_url}/api/sessions/")).json()["sessions"]
    initial_joinable = [
        item for item in sessions
        if item["status"] == "filling" and item["occupied_seats"] < item["capacity"]
    ]
    assert len(initial_joinable) >= 3
    assert len({item["id"] for item in initial_joinable}) == len(initial_joinable)
    room = max(initial_joinable, key=lambda item: item["occupied_seats"])
    aliases = ["HostOne", "RegisteredA", "PeerThree", "PeerFour", "PeerFive", "PeerSix"]
    participants = []
    for index, alias in enumerate(aliases):
        headers = {"Authorization": f"Bearer {token}"} if index == 1 else {}
        response = await client.post(
            f"{base_url}/api/sessions/{room['id']}/join",
            headers=headers,
            json={
                "alias": alias,
                "avatar_color": "#7C6FF0",
                "mic_enabled": True,
                "cam_enabled": False,
            },
        )
        response.raise_for_status()
        participants.append(response.json())
    assert [item["seat_number"] for item in participants] == [1, 2, 3, 4, 5, 6]
    detail = (await client.get(f"{base_url}/api/sessions/{room['id']}")).json()
    assert detail["occupied_seats"] == 6 and detail["status"] == "filling"

    overfill = await client.post(
        f"{base_url}/api/sessions/{room['id']}/join",
        json={
            "alias": "SeventhUser",
            "avatar_color": "#7C6FF0",
            "mic_enabled": True,
            "cam_enabled": False,
        },
    )
    assert overfill.status_code == 409

    after_fill = (await client.get(f"{base_url}/api/sessions/")).json()["sessions"]
    joinable_after = [
        item for item in after_fill
        if item["status"] == "filling" and item["occupied_seats"] < item["capacity"]
    ]
    assert len(joinable_after) >= 3
    assert room["id"] not in {item["id"] for item in joinable_after}
    remaining_initial_ids = {item["id"] for item in initial_joinable} - {room["id"]}
    assert remaining_initial_ids.issubset({item["id"] for item in joinable_after})
    return room["id"], participants


async def open_live_room(
    client: httpx.AsyncClient,
    base_url: str,
    session_id: str,
    participants: list[dict],
):
    sockets = []
    ws_base = base_url.replace("http://", "ws://")
    for participant in participants:
        websocket = await websockets.connect(
            f"{ws_base}/ws/sessions/{session_id}/{participant['participant_id']}"
        )
        state = await recv_type(websocket, "SESSION_STATE")
        assert state["payload"]["hostParticipantId"] == participants[0]["participant_id"]
        sockets.append(websocket)
    for websocket in sockets:
        await websocket.send(json.dumps({"type": "JOIN_WAITING_ROOM", "payload": {}}))
    await sockets[0].send(json.dumps({"type": "start_session", "payload": {}}))
    for websocket in sockets:
        await recv_type(websocket, "SESSION_STARTING")

    starting_join = await client.post(
        f"{base_url}/api/sessions/{session_id}/join",
        json={
            "alias": "StartingLate",
            "avatar_color": "#7C6FF0",
            "mic_enabled": True,
            "cam_enabled": False,
        },
    )
    assert starting_join.status_code == 409

    for websocket in sockets:
        await websocket.send(json.dumps({"type": "ARENA_JOINED", "payload": {}}))
    for websocket in sockets:
        await recv_type(websocket, "SESSION_STARTED")
    return sockets


def feedback_body(session_id: str, rater_id: str, ratee_id: str, values: tuple[int, ...]) -> dict:
    return {
        "session_id": session_id,
        "rater_participant_id": rater_id,
        "ratings": [
            {
                "target_participant_id": ratee_id,
                "target_alias": "target",
                "metrics": {
                    "communication": values[0],
                    "confidence": values[1],
                    "relevance": values[2],
                    "participation": values[3],
                    "leadership": values[4],
                },
            }
        ],
    }


async def add_feedback_and_verify(
    client: httpx.AsyncClient,
    base_url: str,
    session_id: str,
    participants: list[dict],
) -> None:
    target = participants[1]["participant_id"]
    report_url = f"{base_url}/api/sessions/{session_id}/participants/{target}/report"
    report = (await client.get(report_url)).json()
    assert report["received_count"] == 0
    assert report["overall_rating"] is None
    assert report["averages"] is None

    # A rates B: this must never affect A's received score.
    response = await client.post(
        f"{base_url}/api/sessions/{session_id}/feedback",
        json=feedback_body(
            session_id,
            target,
            participants[2]["participant_id"],
            (1, 1, 1, 1, 1),
        ),
    )
    response.raise_for_status()
    unchanged = (await client.get(report_url)).json()
    assert unchanged["received_count"] == 0 and unchanged["overall_rating"] is None

    peer_values = [
        (1, 2, 3, 4, 5),
        (2, 3, 4, 5, 1),
        (3, 4, 5, 1, 2),
        (4, 5, 1, 2, 3),
        (5, 1, 2, 3, 4),
    ]
    peer_indexes = [0, 2, 3, 4, 5]
    for offset, (peer_index, values) in enumerate(zip(peer_indexes, peer_values), start=1):
        response = await client.post(
            f"{base_url}/api/sessions/{session_id}/feedback",
            json=feedback_body(
                session_id,
                participants[peer_index]["participant_id"],
                target,
                values,
            ),
        )
        response.raise_for_status()
        if offset == 2:
            partial = (await client.get(report_url)).json()
            assert partial["received_count"] == 2 and partial["expected_count"] == 5

    full = (await client.get(report_url)).json()
    assert full["received_count"] == 5 and full["expected_count"] == 5
    assert full["averages"] == {
        "communication": 3.0,
        "confidence": 3.0,
        "relevance": 3.0,
        "participation": 3.0,
        "leadership": 3.0,
    }
    assert full["overall_rating"] == 3.0
    assert full["speech_metrics_available"] is False
    assert full["ai_analysis"] is None


async def run_flow(base_url: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        registration = await client.post(
            f"{base_url}/api/auth/register",
            json={
                "email": "registered-history@example.com",
                "password": "TestPass123!",
                "default_alias": "RegisteredA",
            },
        )
        registration.raise_for_status()
        token = registration.json()["token"]

        # Session one: host authorization and deterministic transfer.
        session_one, participants_one = await join_six(client, base_url, token)
        sockets = await open_live_room(client, base_url, session_one, participants_one)

        closed_join = await client.post(
            f"{base_url}/api/sessions/{session_one}/join",
            json={
                "alias": "LateArrival",
                "avatar_color": "#7C6FF0",
                "mic_enabled": True,
                "cam_enabled": False,
            },
        )
        assert closed_join.status_code == 409

        await sockets[2].send(json.dumps({"type": "complete_session", "payload": {}}))
        rejection = await recv_type(sockets[2], "SESSION_ACTION_REJECTED")
        assert "Only the current room host" in rejection["payload"]["reason"]
        live_detail = (await client.get(f"{base_url}/api/sessions/{session_one}")).json()
        assert live_detail["status"] == "in_progress" and live_detail["occupied_seats"] == 6

        # A cancelled navigation attempt sends no leave event: occupancy remains 6/6.
        await asyncio.sleep(0.2)
        unchanged = (await client.get(f"{base_url}/api/sessions/{session_one}")).json()
        assert unchanged["occupied_seats"] == 6

        await sockets[0].send(json.dumps({"type": "LEAVE_ARENA", "payload": {}}))
        host_update = await recv_type(sockets[1], "HOST_UPDATED")
        assert host_update["payload"]["hostParticipantId"] == participants_one[1]["participant_id"]
        after_leave = (await client.get(f"{base_url}/api/sessions/{session_one}")).json()
        assert after_leave["status"] == "in_progress" and after_leave["occupied_seats"] == 5

        await sockets[1].send(json.dumps({"type": "complete_session", "payload": {}}))
        await recv_type(sockets[1], "SESSION_COMPLETED")
        for websocket in sockets[1:]:
            await websocket.close()
        await add_feedback_and_verify(client, base_url, session_one, participants_one)

        # Session two: the server timer completes the room without a host action.
        session_two, participants_two = await join_six(client, base_url, token)
        sockets = await open_live_room(client, base_url, session_two, participants_two)
        for websocket in sockets:
            await recv_type(websocket, "SESSION_COMPLETED", timeout=8.0)
            await websocket.close()
        await add_feedback_and_verify(client, base_url, session_two, participants_two)

        dashboard = (
            await client.get(
                f"{base_url}/api/users/me/dashboard",
                headers={"Authorization": f"Bearer {token}"},
            )
        ).json()
        assert dashboard["stats"] == {
            "sessions_completed": 2,
            "average_peer_rating": 3.0,
            "average_clarity": 3.0,
            "gds_this_week": 2,
        }
        assert len(dashboard["performance"]) == 2
        assert all(item["participation_status"] == "completed" for item in dashboard["history"])
        assert all("occupied_seats" not in item for item in dashboard["history"])
        assert all("filling" not in json.dumps(item) for item in dashboard["history"])
        return token, participants_one[1]["participant_id"], participants_two[1]["participant_id"]


async def verify_after_restart(base_url: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        login = await client.post(
            f"{base_url}/api/auth/login",
            json={
                "email": "registered-history@example.com",
                "password": "TestPass123!",
                "stay_signed_in": False,
            },
        )
        login.raise_for_status()
        token = login.json()["token"]
        response = await client.get(
            f"{base_url}/api/users/me/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        dashboard = response.json()
        assert dashboard["stats"]["sessions_completed"] == 2
        assert dashboard["stats"]["average_peer_rating"] == 3.0
        assert dashboard["stats"]["average_clarity"] == 3.0
        assert dashboard["stats"]["gds_this_week"] == 2
        assert len(dashboard["history"]) == 2
        assert len(dashboard["performance"]) == 2

        # Provisioning a new filling room must not rewrite historical statuses.
        sessions = (await client.get(f"{base_url}/api/sessions/")).json()["sessions"]
        joinable = [
            item for item in sessions
            if item["status"] == "filling" and item["occupied_seats"] < item["capacity"]
        ]
        assert len(joinable) >= 3
        assert len({item["id"] for item in joinable}) == len(joinable)
        again = (
            await client.get(
                f"{base_url}/api/users/me/dashboard",
                headers={"Authorization": f"Bearer {token}"},
            )
        ).json()
        assert all(item["participation_status"] == "completed" for item in again["history"])
        return again


async def main() -> None:
    with tempfile.TemporaryDirectory(prefix="skillswap-stabilization-") as temp_dir:
        database_path = Path(temp_dir) / "isolated.db"
        port = free_port()
        base_url = f"http://127.0.0.1:{port}"
        server = start_server(database_path, port)
        try:
            await wait_for_server(base_url)
            _, participant_one, participant_two = await run_flow(base_url)
        finally:
            server.send_signal(signal.SIGTERM)
            server.wait(timeout=10)

        server = start_server(database_path, port)
        try:
            await wait_for_server(base_url)
            dashboard = await verify_after_restart(base_url)
        finally:
            server.send_signal(signal.SIGTERM)
            server.wait(timeout=10)

        connection = sqlite3.connect(database_path)
        try:
            counts = {
                "users": connection.execute("SELECT COUNT(*) FROM users").fetchone()[0],
                "participants": connection.execute("SELECT COUNT(*) FROM participants").fetchone()[0],
                "feedback": connection.execute("SELECT COUNT(*) FROM peer_ratings").fetchone()[0],
                "sessions": connection.execute("SELECT COUNT(*) FROM gd_sessions").fetchone()[0],
                "completed_sessions": connection.execute(
                    "SELECT COUNT(*) FROM gd_sessions WHERE status = 'COMPLETED'"
                ).fetchone()[0],
            }
            reconstructed = connection.execute(
                "SELECT p.alias, COUNT(*), AVG((r.communication + r.confidence + r.relevance + r.participation + r.leadership) / 5.0) "
                "FROM peer_ratings r JOIN participants p ON r.ratee_id = p.id "
                "WHERE p.alias = 'RegisteredA' GROUP BY r.ratee_id ORDER BY r.ratee_id"
            ).fetchall()
        finally:
            connection.close()

        assert counts["users"] >= 1
        assert counts["participants"] == 12
        assert counts["feedback"] == 12
        assert counts["sessions"] >= 5
        assert counts["completed_sessions"] >= 2
        assert len(reconstructed) == 2
        assert all(row[1] == 5 and row[2] == 3.0 for row in reconstructed)
        print(json.dumps({
            "result": "PASS",
            "isolated_database": str(database_path),
            "persisted_counts": counts,
            "received_feedback_reconstruction": reconstructed,
            "dashboard_stats_after_restart": dashboard["stats"],
            "history_entries_after_restart": len(dashboard["history"]),
        }, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
