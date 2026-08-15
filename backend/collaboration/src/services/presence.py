import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from src.core.infrastructure.mongo import mongo
from src.repositories.cooperation import CooperationRepository, DocumentRepository
from src.services.activity import ActivityService

class PresenceService:
    @staticmethod
    def get_effective_collaboration_status(
        document: dict, user_id: str | None = None, is_admin: bool = False
    ) -> dict:
        if not document:
            return {
                "mode": "CLOSED",
                "effective_mode": "CLOSED",
                "is_effective_closed": True,
                "is_read_only": True,
                "can_edit": False,
                "can_comment": False,
                "can_view": False,
            }

        creator_id = str(document.get("creator_id") or "")
        if is_admin or (user_id and str(user_id) == creator_id):
            return {
                "mode": document.get("collaboration_mode", "OPEN"),
                "effective_mode": "OPEN",
                "is_effective_closed": False,
                "is_read_only": False,
                "can_edit": True,
                "can_comment": True,
                "can_view": True,
            }

        now = datetime.now(timezone.utc)
        schedules = document.get("collaboration_schedules") or []
        active_schedules = [s for s in schedules if s.get("is_active", True)]

        effective_mode = None
        if active_schedules:
            in_window_rule = None
            for rule in active_schedules:
                start_at = rule.get("start_at")
                end_at = rule.get("end_at")
                if isinstance(start_at, str):
                    try:
                        start_at = datetime.fromisoformat(start_at.replace("Z", "+00:00"))
                    except Exception:
                        start_at = None
                elif isinstance(start_at, datetime) and start_at.tzinfo is None:
                    start_at = start_at.replace(tzinfo=timezone.utc)

                if isinstance(end_at, str):
                    try:
                        end_at = datetime.fromisoformat(end_at.replace("Z", "+00:00"))
                    except Exception:
                        end_at = None
                elif isinstance(end_at, datetime) and end_at.tzinfo is None:
                    end_at = end_at.replace(tzinfo=timezone.utc)

                if end_at:
                    if start_at:
                        if start_at <= now <= end_at:
                            in_window_rule = rule
                            break
                    elif now <= end_at:
                        in_window_rule = rule
                        break

            if in_window_rule:
                effective_mode = in_window_rule.get("mode", "EDIT").upper()
            else:
                fallback = "READ_ONLY"
                for rule in active_schedules:
                    if rule.get("fallback_mode"):
                        fallback = rule.get("fallback_mode").upper()
                effective_mode = fallback

        if not effective_mode:
            effective_mode = str(document.get("collaboration_mode") or "OPEN").upper()

        can_view = effective_mode != "CLOSED"
        can_comment = effective_mode in ("OPEN", "COMMENT", "COMMENT_ONLY", "EDIT")
        can_edit = effective_mode in ("OPEN", "EDIT")
        is_read_only = effective_mode in ("READ_ONLY", "VIEW")
        is_effective_closed = effective_mode == "CLOSED"

        return {
            "mode": document.get("collaboration_mode", "OPEN"),
            "effective_mode": effective_mode,
            "is_effective_closed": is_effective_closed,
            "is_read_only": is_read_only,
            "can_edit": can_edit,
            "can_comment": can_comment,
            "can_view": can_view,
        }

    @staticmethod
    async def update_status(document_id: str, current_user) -> dict:
        await CooperationRepository.update_status(
            {"document_id": document_id, "user_id": str(current_user.id)},
            {
                "$set": {
                    "last_seen": datetime.now(timezone.utc),
                    "full_name": current_user.full_name,
                }
            },
            upsert=True,
        )
        return {"message": "Đồng bộ hóa trạng thái hoạt động trực tuyến hoàn tất"}

    @staticmethod
    async def get_online_collaborators(document_id: str) -> list:
        cutoff = datetime.now(timezone.utc).timestamp() - 60
        online_users = (
            await mongo
            .find("collaboration_status", {"document_id": document_id})
            .to_list(length=None)
        )
        result = []
        for u in online_users:
            last_seen = u.get("last_seen")
            last_seen_ts = (
                last_seen.timestamp() if isinstance(last_seen, datetime) else 0
            )
            is_online = last_seen_ts > cutoff
            result.append(
                {
                    "user_id": u["user_id"],
                    "full_name": u.get("full_name", "Collaborator"),
                    "status": "online" if is_online else "offline",
                }
            )
        return result

    @staticmethod
    async def update_collaboration_mode(
        document_id: str, mode: str, current_user
    ) -> dict:
        doc = await DocumentRepository.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy tài liệu")
        is_owner = str(doc.get("creator_id")) == str(current_user.id)
        is_admin = getattr(current_user, "role", None) == "admin"
        if not (is_owner or is_admin):
            raise HTTPException(
                status_code=403,
                detail="Chỉ chủ sở hữu hoặc quản trị viên mới có quyền điều chỉnh chế độ đóng mở tài liệu",
            )
        mode = mode.upper()
        if mode not in ["OPEN", "COMMENT_ONLY", "READ_ONLY", "CLOSED"]:
            raise HTTPException(status_code=400, detail="Chế độ đóng mở tài liệu không hợp lệ")

        await DocumentRepository.update_one(
            {"_id": document_id},
            {
                "$set": {
                    "collaboration_mode": mode,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        await ActivityService.log_activity(
            document_id,
            current_user.full_name,
            f"Update collaboration mode to {mode}",
            f"Document collaboration state set to {mode}",
        )
        return {
            "document_id": document_id,
            "collaboration_mode": mode,
            "message": "Cập nhật chế độ đóng mở tài liệu hoàn tất",
        }

    @staticmethod
    async def get_collaboration_mode(document_id: str, current_user) -> dict:
        doc = await DocumentRepository.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy tài liệu")
        user_id = str(current_user.id) if current_user else None
        is_admin = getattr(current_user, "role", None) == "admin"
        status_info = PresenceService.get_effective_collaboration_status(
            doc, user_id=user_id, is_admin=is_admin
        )
        return {
            "document_id": document_id,
            "collaboration_mode": doc.get("collaboration_mode", "OPEN"),
            "effective_status": status_info,
        }

    @staticmethod
    async def update_collaboration_schedules(
        document_id: str, schedules: list, current_user
    ) -> dict:
        doc = await DocumentRepository.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy tài liệu")
        is_owner = str(doc.get("creator_id")) == str(current_user.id)
        is_admin = getattr(current_user, "role", None) == "admin"
        if not (is_owner or is_admin):
            raise HTTPException(
                status_code=403,
                detail="Chỉ chủ sở hữu hoặc quản trị viên mới có quyền thiết lập lịch hẹn giờ",
            )
        processed_schedules = []
        for s in schedules:
            rule_id = s.get("id") or str(uuid.uuid4())
            start_at = s.get("start_at")
            end_at = s.get("end_at")
            if isinstance(start_at, datetime):
                start_at = start_at.isoformat()
            if isinstance(end_at, datetime):
                end_at = end_at.isoformat()
            processed_schedules.append(
                {
                    "id": rule_id,
                    "title": s.get("title") or "Khung giờ hẹn",
                    "start_at": start_at,
                    "end_at": end_at,
                    "mode": (s.get("mode") or "EDIT").upper(),
                    "fallback_mode": (s.get("fallback_mode") or "READ_ONLY").upper(),
                    "is_active": s.get("is_active", True),
                }
            )
        await DocumentRepository.update_one(
            {"_id": document_id},
            {
                "$set": {
                    "collaboration_schedules": processed_schedules,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        await ActivityService.log_activity(
            document_id,
            current_user.full_name,
            "Update collaboration schedules",
            f"Configured {len(processed_schedules)} schedule windows",
        )
        return {
            "document_id": document_id,
            "schedules": processed_schedules,
            "message": "Cập nhật lịch hẹn giờ quyền hạn cộng tác hoàn tất",
        }

    @staticmethod
    async def get_collaboration_schedules(document_id: str, current_user) -> dict:
        doc = await DocumentRepository.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy tài liệu")
        user_id = str(current_user.id) if current_user else None
        is_admin = getattr(current_user, "role", None) == "admin"
        status_info = PresenceService.get_effective_collaboration_status(
            doc, user_id=user_id, is_admin=is_admin
        )
        return {
            "document_id": document_id,
            "schedules": doc.get("collaboration_schedules") or [],
            "effective_status": status_info,
        }
