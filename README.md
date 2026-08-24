# SkillSwap API

The existing hackathon backend has been consolidated into one FastAPI
application backed by async SQLAlchemy. It runs locally with SQLite by default
and supports PostgreSQL through `DATABASE_URL`.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # optional; environment variables also work
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/app` for the SkillSwap application,
`http://127.0.0.1:8000/docs` for API documentation, or call `GET /health` for
a database-backed health check. `/video_session.html` remains a compatibility
redirect.

The deterministic demo seed creates:

- Open session: `11111111-1111-4111-8111-111111111111`
- Feedback session: `22222222-2222-4222-8222-222222222222`
- Feedback rater: `33333333-3333-4333-8333-333333333333`
- Feedback recipient: `44444444-4444-4444-8444-444444444444`

Set `SEED_DEMO_DATA=false` to disable seeding. Seed records are idempotent.

## Agora real-time audio setup

1. Sign in to the Agora Console and create an RTC project with token
   authentication/App Certificate enabled.
2. In the project's configuration, copy its 32-character App ID and enable/copy
   its 32-character primary App Certificate.
3. Put both values only in the backend `.env` file:

   ```dotenv
   AGORA_APP_ID=<32-character Agora App ID>
   AGORA_APP_CERTIFICATE=<32-character primary App Certificate>
   AGORA_TOKEN_EXPIRE_SECONDS=3600
   ```

4. Restart Uvicorn after changing `.env`:

   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

The App Certificate is read only by the FastAPI token service and is never
returned to or embedded in the browser. The browser obtains a short-lived token
from `POST /api/sessions/{session_id}/agora-token`. The channel is always
`skillswap-gd-{session_id}`, and the server binds the token to the participant's
persistent numeric Agora UID.

If either Agora credential is missing or invalid, the token endpoint returns
`503 Service Unavailable` and the page displays the configuration error. It
never attempts to join with a fake token.

### Test with two browser windows

1. Start the backend with valid Agora credentials.
2. Open `http://127.0.0.1:8000/video_session.html` in two separate browser
   windows (an ordinary window plus a private/incognito window is convenient).
3. In each window, keep the same GD topic selected. The seeded open session ID
   is `11111111-1111-4111-8111-111111111111`.
4. Use different aliases, keep the microphone on, and leave the camera off.
5. Click **Join a live GD**, then **Enter arena** in each window.
6. Allow microphone permission in both windows. Use headphones to avoid acoustic
   echo or feedback.
7. Speak into one microphone at a time. The other window should hear the live
   audio and show the speaker indicator.
8. Click **Mute microphone** and **Unmute microphone** and verify the remote
   participant card changes state and audio stops/resumes.
9. Click **Leave Arena** and verify the other window removes that participant.

For two physical devices, run Uvicorn on an externally reachable interface and
put it behind HTTPS, then open `https://<your-host>/video_session.html` on both
devices. Browsers generally allow microphone capture only from secure contexts;
plain `http://<LAN-IP>` is not sufficient even though `http://localhost` is.

## Other external services

Without `OPENAI_API_KEY` or a real audio recording, analysis is marked
unavailable and the UI shows an explicit coming-soon state. No mock performance
analysis is persisted or presented as measured data. Set the key (and optionally
`OPENAI_MODEL`) when the participant-specific recording pipeline is ready.

The `database/` folder contains only compatibility shims and the archived
PostgreSQL dump. All runtime database access goes through `app/database.py`.

## Persisted dashboard and report data

- `GET /api/users/me/dashboard` returns authenticated registered-user history,
  completed-session counts, received peer-rating averages, average clarity,
  this-week participation, and real rated-session chart points.
- `GET /api/sessions/{session_id}/participants/{participant_id}/report` returns
  only feedback received by that participant, including partial feedback counts
  and actual room averages.
- WebSocket presence, microphone state, and Agora connection state are realtime
  only. Speaking time, interruptions, filler words, WPM, and participant-specific
  AI analysis are displayed as unavailable unless a real pipeline persists them.

The isolated six-participant regression check does not touch `skillswap.db`:

```bash
.venv/bin/python tests/automated_stabilization_check.py
```

It verifies host authorization and transfer, timer completion, zero/partial/full
received feedback, two-session registered-user history, server-restart
persistence, and direct reconstruction of received ratings from SQLite rows.
