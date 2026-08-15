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

def get_effective_collaboration_status(document: dict, user_id: str | None = None, is_adm: bool = False) -> dict:
    if not document:
        return {
            "mode": "CLOSED",
            "effective_mode": "CLOSED",
            "is_effective_closed": True,
            "is_read_only": True,
            "can_edit": False,
            "can_comment": False,
            "can_view": False,
            "closed_reason": "document_not_found",
            "closed_at": None,
            "closed_by": None,
        }
    creator_id = str(document.get("creator_id") or "")
    if is_adm or (user_id and str(user_id) == creator_id):
        return {
            "mode": document.get("collaboration_mode", "OPEN"),
            "effective_mode": "OPEN",
            "is_effective_closed": False,
            "is_read_only": False,
            "can_edit": True,
            "can_comment": True,
            "can_view": True,
            "closed_reason": None,
            "closed_at": None,
            "closed_by": None,
        }
    schedules = document.get("collaboration_schedules") or []
    active_schedules = [item for item in schedules if item.get("is_active", True)]
    effective_mode = None
    if active_schedules:
        now = datetime.now(timezone.utc)
        in_window_rule = None
        for rule in active_schedules:
            start_at = rule.get("start_at")
            end_at = rule.get("end_at")
            if isinstance(start_at, str):
                try:
                    start_at = datetime.fromisoformat(start_at.replace("Z", "+00:00"))
                except ValueError:
                    start_at = None
            elif isinstance(start_at, datetime) and start_at.tzinfo is None:
                start_at = start_at.replace(tzinfo=timezone.utc)
            if isinstance(end_at, str):
                try:
                    end_at = datetime.fromisoformat(end_at.replace("Z", "+00:00"))
                except ValueError:
                    end_at = None
            elif isinstance(end_at, datetime) and end_at.tzinfo is None:
                end_at = end_at.replace(tzinfo=timezone.utc)
            if end_at and ((start_at and start_at <= now <= end_at) or (not start_at and now <= end_at)):
                in_window_rule = rule
                break
        if in_window_rule:
            effective_mode = str(in_window_rule.get("mode") or "EDIT").upper()
        else:
            effective_mode = str(
                next(
                    (
                        item.get("fallback_mode")
                        for item in reversed(active_schedules)
                        if item.get("fallback_mode")
                    ),
                    "READ_ONLY",
                )
            ).upper()
    if not effective_mode:
        effective_mode = str(document.get("collaboration_mode") or "OPEN").upper()
    can_view = effective_mode != "CLOSED"
    can_comment = effective_mode in {"OPEN", "COMMENT", "COMMENT_ONLY", "EDIT"}
    can_edit = effective_mode in {"OPEN", "EDIT"}
    return {
        "mode": document.get("collaboration_mode", "OPEN"),
        "effective_mode": effective_mode,
        "is_effective_closed": effective_mode == "CLOSED",
        "is_read_only": effective_mode in {"READ_ONLY", "VIEW"},
        "can_edit": can_edit,
        "can_comment": can_comment,
        "can_view": can_view,
        "closed_reason": "explicitly_closed" if effective_mode == "CLOSED" else None,
        "closed_at": None,
        "closed_by": None,
    }

async def can_read_full(document: dict, current_user) -> bool:
    if not document:
        return False
    user_id = str(current_user.id) if current_user else None
    if (
        user_id == document.get("creator_id")
        or is_admin(current_user)
        or (user_id and user_id in document.get("coauthors", []))
    ):
        return True
    if document.get("status") != DocumentStatus.PUBLISHED or document.get("is_deleted") is True:
        return False
    if document.get("visibility", "public") != "public":
        return False
    return True
