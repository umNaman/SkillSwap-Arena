import time
import logging

from app.config import settings

logger = logging.getLogger(__name__)

def generate_rtc_token(channel_name: str, uid: int, role: int = 1, expire_seconds: int = 3600) -> dict:
    app_id = settings.AGORA_APP_ID
    app_certificate = settings.AGORA_APP_CERTIFICATE
    channel = f"skillswap-gd-{channel_name}"
    
    expires_at = int(time.time()) + expire_seconds

    if not app_id or not app_certificate:
        logger.warning("AGORA_APP_ID or AGORA_APP_CERTIFICATE is not set. Using placeholder token.")
        return {
            "app_id": "placeholder_app_id",
            "channel": channel,
            "token": "placeholder_token",
            "uid": uid,
            "expires_at": expires_at,
            "duration_seconds": expire_seconds
        }
        
    try:
        from app.utils.agora_token_builder import RtcTokenBuilder
        # role: 1 for publisher, 2 for subscriber
        token = RtcTokenBuilder.buildTokenWithUid(
            app_id, 
            app_certificate, 
            channel, 
            uid, 
            role, 
            expires_at
        )
    except ImportError:
        logger.warning("agora_token_builder not found. Using placeholder token.")
        token = "placeholder_token"
        
    return {
        "app_id": app_id,
        "channel": channel,
        "token": token,
        "uid": uid,
        "expires_at": expires_at,
        "duration_seconds": expire_seconds
    }
