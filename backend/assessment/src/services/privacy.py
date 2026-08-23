from hashlib import sha256
import hmac

from src.core.configuration import settings


def participant_id(user_id: str):
    return hmac.new(
        settings.SECRET_KEY.encode(),
        f"assessment-response:{user_id}".encode(),
        sha256,
    ).hexdigest()
