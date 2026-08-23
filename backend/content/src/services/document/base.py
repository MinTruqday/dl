from datetime import datetime, timezone
from passlib.context import CryptContext

from src.schemas.document import DocumentStatus

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def serialize_document(document):
    if not document:
        return None
    if "_id" in document:
        document["_id"] = str(document["_id"])
    if "created_at" not in document:
        document["created_at"] = datetime.now(timezone.utc)
    views = document.get("views", 0)
    document["view_count"] = views
    document["views_count"] = views
    document.pop("password", None)
    document.pop("access_password_hash", None)
    return document


def is_admin(current_user) -> bool:
    role = getattr(current_user, "role", "") if current_user else ""
    from src.core.dependency import Role

    return str(getattr(role, "value", role)).lower() == Role.ADMIN.value


async def can_read_full(document: dict, current_user) -> bool:
    if not document:
        return False
    user_id = str(current_user.id) if current_user else None
    if user_id == document.get("creator_id") or is_admin(current_user):
        return True
    if document.get("status") != DocumentStatus.PUBLISHED or document.get("is_deleted") is True:
        return False
    if document.get("visibility", "public") != "public":
        return False
    return True
