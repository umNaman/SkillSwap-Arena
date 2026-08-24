import time
import re

from app.config import settings


class AgoraConfigurationError(RuntimeError):
    pass


def channel_name_for_session(session_id: str) -> str:
    return f"skillswap-gd-{session_id}"


def _validated_credentials() -> tuple[str, str]:
    app_id = settings.AGORA_APP_ID.strip()
    app_certificate = settings.AGORA_APP_CERTIFICATE.strip()
    if not app_id or not app_certificate:
        raise AgoraConfigurationError(
            "Agora calling is unavailable because AGORA_APP_ID and "
            "AGORA_APP_CERTIFICATE are not configured on the backend."
        )
    credential_pattern = re.compile(r"^[0-9a-fA-F]{32}$")
    if not credential_pattern.fullmatch(app_id) or not credential_pattern.fullmatch(app_certificate):
        raise AgoraConfigurationError(
            "Agora calling is unavailable because the configured App ID or App Certificate is invalid."
        )
    return app_id, app_certificate


def generate_rtc_token(
    session_id: str,
    uid: int,
    role: int = 1,
    expire_seconds: int | None = None,
) -> dict:
    app_id, app_certificate = _validated_credentials()
    channel = channel_name_for_session(session_id)
    expire_seconds = expire_seconds or settings.AGORA_TOKEN_EXPIRE_SECONDS
    
    expires_at = int(time.time()) + expire_seconds

    try:
        from agora_token_builder import RtcTokenBuilder
        # role: 1 for publisher, 2 for subscriber
        token = RtcTokenBuilder.buildTokenWithUid(
            app_id, 
            app_certificate, 
            channel, 
            uid, 
            role, 
            expires_at
        )
    except ImportError as exc:
        raise AgoraConfigurationError(
            "Agora credentials are set but agora-token-builder is not installed."
        ) from exc
        
    return {
        "app_id": app_id,
        "channel": channel,
        "token": token,
        "uid": uid,
        "expires_at": expires_at,
        "duration_seconds": expire_seconds,
        "configured": True,
    }
