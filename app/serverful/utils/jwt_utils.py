from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from app.serverful.config.config import settings


def generate_token(user_id: str, user_name: str, role: str) -> str:
    expiration_time: datetime = datetime.now(timezone.utc) + timedelta(
        hours=settings.JWT_EXPIRATION_HOURS
    )
    payload: Dict[str, Any] = {
        "user_id": user_id,
        "user_name": user_name,
        "role": role,
        "exp": expiration_time,
        "iat": datetime.now(timezone.utc),
    }
    token: str = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


def validate_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload: Dict[str, Any] = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
