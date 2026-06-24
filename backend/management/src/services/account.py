import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException, Query
from loguru import logger
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.schemas.account import Role
from src.repositories.user import UserRepository
from src.repositories.moderation import ModerationRepository
from src.repositories.system import SystemRepository
from src.repositories.moderation import ModerationRepository
from src.repositories.moderation import ModerationRepository


class AccountService:

    @staticmethod
    async def get_all_users(
        limit: int = 50,
        offset: int = 0,
        cursor: str = None,
        db=None,
    ) -> List[Dict[str, Any]]:
        if db is None:
            db = database.mongodb.get_default_database()
        query = {}
        if cursor and isinstance(cursor, str):
            query["created_at"] = {
                "$lt": datetime.fromisoformat(cursor.replace("Z", "+00:00"))
            }
        users = (
            await UserRepository
            .find(query)
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
            .to_list(length=limit)
        )
        return [
            {
                "_id": str(u["_id"]),
                "email": u.get("email"),
                "full_name": u.get("full_name"),
                "role": u.get("role"),
                "is_active": u.get("is_active", True),
                "created_at": (
                    u["created_at"].isoformat()
                    if isinstance(u.get("created_at"), datetime)
                    else u.get("created_at")
                ),
            }
            for u in users
        ]

    @staticmethod
    async def update_user_role(user_id: str, role: str, db=None) -> Dict[str, str]:
        if db is None:
            db = database.mongodb.get_default_database()
        res = await UserRepository.update_one(
            {"_id": user_id},
            {"$set": {"role": role, "updated_at": datetime.now(timezone.utc)}},
        )
        if res.matched_count == 0:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy hồ sơ người dùng"
            )
        logger.info("Cập nhật quyền truy cập tài khoản thành công")
        return {"message": "Cập nhật quyền truy cập thành công"}

    @staticmethod
    async def update_user_status(
        user_id: str, is_active: bool, db=None
    ) -> Dict[str, str]:
        if db is None:
            db = database.mongodb.get_default_database()
        res = await UserRepository.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "is_active": is_active,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        if res.matched_count == 0:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy hồ sơ người dùng"
            )
        logger.info("Cập nhật trạng thái hoạt động tài khoản thành công")
        return {"message": "Cập nhật trạng thái hoạt động thành công"}

    @staticmethod
    async def warn_user(user_id: str, reason: str, current_user, db=None) -> dict:
        if db is None:
            db = database.mongodb.get_default_database()
        user = await UserRepository.find_one({"_id": user_id})
        if not user:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy hồ sơ người dùng"
            )
        warning = {
            "_id": str(uuid7()),
            "user_id": user_id,
            "actor_id": str(current_user.id),
            "reason": reason,
            "created_at": datetime.now(timezone.utc),
        }
        await ModerationRepository.insert_warning(warning)
        await SystemRepository.insert_audit_log(
            {
                "action": "WARN_USER",
                "actor_id": str(current_user.id),
                "target_user_id": user_id,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc),
            }
        )
        try:
            from src.core.infrastructure.configuration import settings as shared_settings

            if shared_settings.NOTIFICATION_URL:
                async with httpx.AsyncClient(timeout=shared_settings.DEFAULT_HTTP_TIMEOUT) as client:
                    await client.post(
                        f"{shared_settings.NOTIFICATION_URL}/thong-bao/kich-hoat",
                        json={
                            "target_user_id": user_id,
                            "title": "You have a new system administrative warning notification",
                            "body": f"An official violation warning has been recorded for your account due to the following reason provided by the administration {reason}",
                            "type": "WARNING",
                        },
                    )
        except Exception as e:
            logger.warning(f"Không thể gửi thông báo cảnh báo qua hệ thống bên ngoài: {e}")
        logger.info("Cảnh báo vi phạm đã được ghi nhận vào hệ thống thành công")
        return {"message": "Gửi cảnh báo quản trị thành công"}

    @staticmethod
    async def lock_user(
        user_id: str, reason: str, duration_hours: int, current_user, db=None
    ) -> dict:
        if db is None:
            db = database.mongodb.get_default_database()
        lock_until = datetime.now(timezone.utc) + timedelta(hours=duration_hours)
        await UserRepository.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "is_active": False,
                    "locked_until": lock_until,
                    "lock_reason": reason,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        await SystemRepository.insert_audit_log(
            {
                "action": "LOCK_USER",
                "actor_id": str(current_user.id),
                "target_user_id": user_id,
                "reason": reason,
                "duration": duration_hours,
                "timestamp": datetime.now(timezone.utc),
            }
        )
        logger.info("Tài khoản đã bị đình chỉ")
        return {"message": "Tạm khóa tài khoản thành công"}

    @staticmethod
    async def shadowban_user(
        user_id: str, is_banned: bool, current_user, db=None
    ) -> dict:
        if db is None:
            db = database.mongodb.get_default_database()
        await UserRepository.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "is_shadowbanned": is_banned,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        action = "SHADOWBAN" if is_banned else "UNSHADOWBAN"
        await SystemRepository.insert_audit_log(
            {
                "action": action,
                "actor_id": str(current_user.id),
                "target_user_id": user_id,
                "timestamp": datetime.now(timezone.utc),
            }
        )
        logger.info("Cập nhật quyền hiển thị tài khoản thành công")
        return {"message": "Cập nhật trạng thái hiển thị thành công"}

    @staticmethod
    async def verify_kyc(user_id: str, status: str, current_user, db=None) -> dict:
        if db is None:
            db = database.mongodb.get_default_database()
        await UserRepository.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "kyc_status": status,
                    "is_kyc_verified": status == "VERIFIED",
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        await SystemRepository.insert_audit_log(
            {
                "action": f"KYC_{status}",
                "actor_id": str(current_user.id),
                "target_user_id": user_id,
                "timestamp": datetime.now(timezone.utc),
            }
        )
        logger.info("Xác minh danh tính thành công")
        return {"message": "Đã cập nhật trạng thái xác minh"}

    @staticmethod
    async def get_notes(user_id: str, db=None) -> list:
        if db is None:
            db = database.mongodb.get_default_database()
        notes = (
            await ModeratorNoteRepository
            .find({"user_id": user_id})
            .sort("created_at", -1)
            .to_list(length=100)
        )
        return [
            {
                "_id": str(n["_id"]),
                "note": n.get("note", ""),
                "actor_id": n.get("actor_id"),
                "created_at": (
                    n["created_at"].isoformat()
                    if isinstance(n.get("created_at"), datetime)
                    else ""
                ),
            }
            for n in notes
        ]

    @staticmethod
    async def add_note(user_id: str, note: str, current_user, db=None) -> dict:
        if db is None:
            db = database.mongodb.get_default_database()
        await ModerationRepository.insert_moderator_note(
            {
                "_id": str(uuid7()),
                "user_id": user_id,
                "actor_id": str(current_user.id),
                "note": note,
                "created_at": datetime.now(timezone.utc),
            }
        )
        logger.info("Đã thêm ghi chú vào hồ sơ")
        return {"message": "Ghi chú kiểm duyệt thành công"}

    @staticmethod
    async def get_report_queue(
        status_filter: str = "pending",
        cursor: str = None,
        limit: int = 50,
        skip: int = 0,
        db=None,
    ) -> list:
        if db is None:
            db = database.mongodb.get_default_database()
        match_query = {"status": status_filter} if status_filter else {}
        if cursor:
            try:
                match_query["created_at"] = {
                    "$lt": datetime.fromisoformat(cursor.replace("Z", "+00:00"))
                }
            except ValueError as e:
                logger.warning(f"Lỗi định dạng phân trang: {e}")
        pipeline = [{"$match": match_query}, {"$sort": {"created_at": -1}}]
        if skip > 0:
            pipeline.append({"$skip": skip})
        pipeline.append({"$limit": limit})
        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "users",
                        "localField": "reporter_id",
                        "foreignField": "_id",
                        "as": "reporter",
                    }
                },
                {"$unwind": {"path": "$reporter", "preserveNullAndEmptyArrays": True}},
            ]
        )
        reports = (
            await ReportRepository
            .aggregate(pipeline)
            .to_list(length=limit)
        )
        result = []
        for r in reports:
            reporter = r.get("reporter", {})
            result.append(
                {
                    "_id": str(r["_id"]),
                    "item_type": r.get("item_type", ""),
                    "item_id": r.get("item_id", ""),
                    "reason": r.get("reason", ""),
                    "description": r.get("description", ""),
                    "status": r.get("status", "pending"),
                    "reporter_name": (
                        reporter.get("full_name", "Anonymous User")
                        if reporter
                        else "Anonymous User"
                    ),
                    "created_at": (
                        r["created_at"].isoformat()
                        if isinstance(r.get("created_at"), datetime)
                        else r.get("created_at")
                    ),
                }
            )
        return result

    @staticmethod
    async def resolve_report(
        report_id: str, action: str, current_user, db=None
    ) -> dict:
        if db is None:
            db = database.mongodb.get_default_database()
        await ModerationRepository.update_report(
            {"_id": report_id},
            {
                "$set": {
                    "status": "resolved",
                    "action_taken": action,
                    "resolved_by": str(current_user.id),
                    "resolved_at": datetime.now(timezone.utc),
                }
            },
        )
        logger.info("Đã giải quyết báo cáo vi phạm")
        return {"message": "Xử lý báo cáo vi phạm thành công"}

    @staticmethod
    async def get_moderator_activity_log(actor_id: str, db=None) -> list:
        if db is None:
            db = database.mongodb.get_default_database()
        logs = (
            await AuditLogRepository
            .find({"actor_id": actor_id})
            .sort("timestamp", -1)
            .limit(50)
            .to_list(length=50)
        )
        result = []
        for l in logs:
            target_id = (
                l.get("document_id")
                or l.get("target_user_id")
                or l.get("withdrawal_id")
                or l.get("item_id")
                or "N/A"
            )
            target_type = (
                "Document File"
                if "document_id" in l
                else (
                    "User Account"
                    if "target_user_id" in l
                    else (
                        "Financial Transaction"
                        if "withdrawal_id" in l
                        else "General Object"
                    )
                )
            )
            result.append(
                {
                    "action": l.get("action"),
                    "target_id": target_id,
                    "target_type": target_type,
                    "reason": l.get("reason", ""),
                    "created_at": (
                        l["timestamp"].isoformat()
                        if isinstance(l.get("timestamp"), datetime)
                        else l.get("timestamp", "")
                    ),
                }
            )
        return result

    @staticmethod
    async def search_users(
        query: str,
        limit: int = 50,
        db=None,
    ) -> List[Dict[str, Any]]:
        if db is None:
            db = database.mongodb.get_default_database()
        search_query = {
            "$or": [
                {"full_name": {"$regex": query, "$options": "i"}},
                {"username": {"$regex": query, "$options": "i"}},
                {"slug": {"$regex": query, "$options": "i"}},
            ],
            "is_active": True,
        }
        users = (
            await UserRepository
            .find(
                search_query,
                {"full_name": 1, "username": 1, "slug": 1, "avatar_url": 1, "role": 1},
            )
            .limit(limit)
            .to_list(length=limit)
        )
        return [
            {
                "_id": str(u["_id"]),
                "full_name": u.get("full_name")
                or u.get("username")
                or "Anonymous User",
                "username": u.get("username", ""),
                "slug": u.get("slug", ""),
                "avatar_url": u.get("avatar_url"),
                "role": u.get("role", "READER"),
            }
            for u in users
        ]

    @staticmethod
    async def unlock_accounts_task(db=None):
        if db is None:
            db = database.mongodb.get_default_database()
        now = datetime.now(timezone.utc)
        res = await UserRepository.update_many(
            {"locked_until": {"$lt": now}, "is_active": False},
            {
                "$set": {"is_active": True},
                "$unset": {"locked_until": "", "lock_reason": ""},
            },
        )
        if res.modified_count > 0:
            logger.info("Đã khôi phục quyền truy cập tài khoản")
        return res.modified_count

    @staticmethod
    async def internal_get_user_by_id(
        user_id: str, db=None
    ) -> Optional[Dict[str, Any]]:
        if db is None:
            db = database.mongodb.get_default_database()
        user = await UserRepository.find_one(
            {"_id": user_id}, {"password_hash": 0, "passkeys": 0}
        )
        if not user:
            return None
        user["_id"] = str(user["_id"])
        if isinstance(user.get("created_at"), datetime):
            user["created_at"] = user["created_at"].isoformat()
        if isinstance(user.get("updated_at"), datetime):
            user["updated_at"] = user["updated_at"].isoformat()
        return user

    @staticmethod
    async def internal_get_users_by_ids(
        user_ids: List[str], db=None
    ) -> List[Dict[str, Any]]:
        if db is None:
            db = database.mongodb.get_default_database()
        users = (
            await UserRepository
            .find({"_id": {"$in": user_ids}}, {"password_hash": 0, "passkeys": 0})
            .to_list(length=len(user_ids))
        )
        for user in users:
            user["_id"] = str(user["_id"])
            if isinstance(user.get("created_at"), datetime):
                user["created_at"] = user["created_at"].isoformat()
            if isinstance(user.get("updated_at"), datetime):
                user["updated_at"] = user["updated_at"].isoformat()
        return users

    @staticmethod
    async def internal_get_user_by_email(
        email: str, db=None
    ) -> Optional[Dict[str, Any]]:
        if db is None:
            db = database.mongodb.get_default_database()
        user = await UserRepository.find_one({"email": email})
        if not user:
            return None
        user["_id"] = str(user["_id"])
        if isinstance(user.get("created_at"), datetime):
            user["created_at"] = user["created_at"].isoformat()
        if isinstance(user.get("updated_at"), datetime):
            user["updated_at"] = user["updated_at"].isoformat()
        return user

    @staticmethod
    async def internal_get_user_by_slug(slug: str, db=None) -> Optional[Dict[str, Any]]:
        if db is None:
            db = database.mongodb.get_default_database()
        user = await UserRepository.find_one({"slug": slug})
        if not user:
            return None
        user["_id"] = str(user["_id"])
        if isinstance(user.get("created_at"), datetime):
            user["created_at"] = user["created_at"].isoformat()
        if isinstance(user.get("updated_at"), datetime):
            user["updated_at"] = user["updated_at"].isoformat()
        return user

    @staticmethod
    async def internal_create_user(user_data: Dict[str, Any], db=None) -> str:
        if db is None:
            db = database.mongodb.get_default_database()
        user_id = str(uuid7())
        user_data["_id"] = user_id
        user_data["created_at"] = datetime.now(timezone.utc)
        user_data["is_active"] = True
        user_data["wallet_balance"] = 0
        await UserRepository.insert_one(user_data)
        return user_id
