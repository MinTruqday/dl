import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from core.database import db_client
from core.schemas.user import RoleEnum
from fastapi import HTTPException
from loguru import logger
from uuid6 import uuid7


class UserService:

    @staticmethod
    async def get_all_users(
        limit: int = 50, offset: int = 0, cursor: str = None, db=None
    ) -> List[Dict[str, Any]]:
        if db is None:
            db = db_client.mongodb.get_default_database()
        query = {}
        if cursor and isinstance(cursor, str):
            query["created_at"] = {
                "$lt": datetime.fromisoformat(cursor.replace("Z", "+00:00"))
            }
        users = (
            await db["users"]
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
            db = db_client.mongodb.get_default_database()
        res = await db["users"].update_one(
            {"_id": user_id},
            {"$set": {"role": role, "updated_at": datetime.now(timezone.utc)}},
        )
        if res.matched_count == 0:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy thông tin người dùng này"
            )
        logger.info(f"Phân quyền của người dùng {user_id} đã đổi thành {role}")
        return {"message": f"Đã cập nhật vai trò người dùng thành {role}"}

    @staticmethod
    async def update_user_status(
        user_id: str, is_active: bool, db=None
    ) -> Dict[str, str]:
        if db is None:
            db = db_client.mongodb.get_default_database()
        res = await db["users"].update_one(
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
                status_code=404, detail="Không tìm thấy thông tin người dùng này"
            )
        logger.info(f"Trạng thái tài khoản {user_id} đã đổi thành {is_active}")
        return {"message": "Đã cập nhật trạng thái hoạt động của tài khoản"}

    @staticmethod
    async def warn_user(user_id: str, reason: str, current_moderator, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        user = await db["users"].find_one({"_id": user_id})
        if not user:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy thông tin người dùng này"
            )
        warning = {
            "_id": str(uuid7()),
            "user_id": user_id,
            "moderator_id": str(current_moderator.id),
            "reason": reason,
            "created_at": datetime.now(timezone.utc),
        }
        await db["warnings"].insert_one(warning)
        await db["audit_logs"].insert_one(
            {
                "action": "WARN_USER",
                "actor_id": str(current_moderator.id),
                "target_user_id": user_id,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc),
            }
        )
        try:
            import httpx
            from core.config import settings

            if settings.SIGNAL_URL:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{settings.SIGNAL_URL}/notification/trigger",
                        json={
                            "target_user_id": user_id,
                            "title": "Bạn có một thông báo nhắc nhở từ hệ thống",
                            "body": f"Hệ thống ghi nhận vi phạm từ tài khoản của bạn. Lý do: {reason}",
                            "type": "WARNING",
                        },
                        timeout=3.0,
                    )
        except Exception as e:
            logger.warning("Lỗi khi gửi thông báo")
        logger.info(f"Thành viên {user_id} vừa bị nhắc nhở bởi {current_moderator.id}")
        return {"message": "Đã gửi cảnh báo đến người dùng"}

    @staticmethod
    async def lock_user(
        user_id: str, reason: str, duration_hours: int, current_moderator, db=None
    ) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        lock_until = datetime.now(timezone.utc) + timedelta(hours=duration_hours)
        await db["users"].update_one(
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
        await db["audit_logs"].insert_one(
            {
                "action": "LOCK_USER",
                "actor_id": str(current_moderator.id),
                "target_user_id": user_id,
                "reason": reason,
                "duration": duration_hours,
                "timestamp": datetime.now(timezone.utc),
            }
        )
        logger.info(
            f"Người dùng {user_id} đã bị cấm {duration_hours} tiếng bởi {current_moderator.id}"
        )
        return {"message": f"Đã tạm khóa tài khoản trong {duration_hours} giờ"}

    @staticmethod
    async def shadowban_user(
        user_id: str, is_banned: bool, current_moderator, db=None
    ) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        await db["users"].update_one(
            {"_id": user_id},
            {
                "$set": {
                    "is_shadowbanned": is_banned,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        action = "SHADOWBAN" if is_banned else "UNSHADOWBAN"
        await db["audit_logs"].insert_one(
            {
                "action": action,
                "actor_id": str(current_moderator.id),
                "target_user_id": user_id,
                "timestamp": datetime.now(timezone.utc),
            }
        )
        logger.info(
            f"Người dùng {user_id} đã được {action.lower()} bởi {current_moderator.id}"
        )
        return {"message": "Đã cập nhật trạng thái hạn chế"}

    @staticmethod
    async def verify_kyc(user_id: str, status: str, current_moderator, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        await db["users"].update_one(
            {"_id": user_id},
            {
                "$set": {
                    "kyc_status": status,
                    "is_kyc_verified": status == "VERIFIED",
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        await db["audit_logs"].insert_one(
            {
                "action": f"KYC_{status}",
                "actor_id": str(current_moderator.id),
                "target_user_id": user_id,
                "timestamp": datetime.now(timezone.utc),
            }
        )
        logger.info(
            f"Thông tin KYC của {user_id} đã cập nhật thành {status} bởi {current_moderator.id}"
        )
        return {"message": "Đã cập nhật thông tin định danh KYC"}

    @staticmethod
    async def get_moderator_notes(user_id: str, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        notes = (
            await db["moderator_notes"]
            .find({"user_id": user_id})
            .sort("created_at", -1)
            .to_list(length=100)
        )
        return [
            {
                "_id": str(n["_id"]),
                "note": n.get("note", ""),
                "moderator_id": n.get("moderator_id"),
                "created_at": (
                    n["created_at"].isoformat()
                    if isinstance(n.get("created_at"), datetime)
                    else ""
                ),
            }
            for n in notes
        ]

    @staticmethod
    async def add_moderator_note(
        user_id: str, note: str, current_moderator, db=None
    ) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        await db["moderator_notes"].insert_one(
            {
                "_id": str(uuid7()),
                "user_id": user_id,
                "moderator_id": str(current_moderator.id),
                "note": note,
                "created_at": datetime.now(timezone.utc),
            }
        )
        logger.info(
            f"Vừa thêm ghi chú cho người dùng {user_id} bởi {current_moderator.id}"
        )
        return {"message": "Đã lưu ghi chú điều hành"}

    @staticmethod
    async def get_report_queue(
        status_filter: str = "pending",
        cursor: str = None,
        limit: int = 30,
        skip: int = 0,
        db=None,
    ) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        match_query = {"status": status_filter} if status_filter else {}
        if cursor:
            try:
                match_query["created_at"] = {
                    "$lt": datetime.fromisoformat(cursor.replace("Z", "+00:00"))
                }
            except ValueError as e:
                logger.warning(
                    "Thời gian của con trỏ phân trang không hợp lệ: {cursor}, lỗi"
                )
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
        reports = await db["reports"].aggregate(pipeline).to_list(length=limit)
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
                        reporter.get("full_name", "Ẩn danh") if reporter else "Ẩn danh"
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
        report_id: str, action: str, current_moderator, db=None
    ) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        await db["reports"].update_one(
            {"_id": report_id},
            {
                "$set": {
                    "status": "resolved",
                    "action_taken": action,
                    "resolved_by": str(current_moderator.id),
                    "resolved_at": datetime.now(timezone.utc),
                }
            },
        )
        logger.info(
            f"Báo cáo {report_id} đã xử lý xong với hình thức '{action}' bởi {current_moderator.id}"
        )
        return {"message": "Đã xử lý báo cáo vi phạm"}

    @staticmethod
    async def get_moderator_activity_log(moderator_id: str, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        logs = (
            await db["audit_logs"]
            .find({"actor_id": moderator_id})
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
                "Tài liệu"
                if "document_id" in l
                else (
                    "Người dùng"
                    if "target_user_id" in l
                    else "Thanh toán" if "withdrawal_id" in l else "Đối tượng"
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
        query: str, limit: int = 10, db=None
    ) -> List[Dict[str, Any]]:
        if db is None:
            db = db_client.mongodb.get_default_database()
        search_query = {
            "$or": [
                {"full_name": {"$regex": query, "$options": "i"}},
                {"username": {"$regex": query, "$options": "i"}},
                {"slug": {"$regex": query, "$options": "i"}},
            ],
            "is_active": True,
        }
        users = (
            await db["users"]
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
                "full_name": u.get("full_name") or u.get("username") or "Người dùng",
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
            db = db_client.mongodb.get_default_database()
        now = datetime.now(timezone.utc)
        res = await db["users"].update_many(
            {"locked_until": {"$lt": now}, "is_active": False},
            {
                "$set": {"is_active": True},
                "$unset": {"locked_until": "", "lock_reason": ""},
            },
        )
        if res.modified_count > 0:
            logger.info(f"Đã tự động mở khóa {res.modified_count} tài khoản")
        return res.modified_count

    @staticmethod
    async def internal_get_user_by_id(
        user_id: str, db=None
    ) -> Optional[Dict[str, Any]]:
        if db is None:
            db = db_client.mongodb.get_default_database()
        user = await db["users"].find_one(
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
            db = db_client.mongodb.get_default_database()
        users = (
            await db["users"]
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
            db = db_client.mongodb.get_default_database()
        user = await db["users"].find_one({"email": email})
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
            db = db_client.mongodb.get_default_database()
        user = await db["users"].find_one({"slug": slug})
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
            db = db_client.mongodb.get_default_database()
        user_id = str(uuid7())
        user_data["_id"] = user_id
        user_data["created_at"] = datetime.now(timezone.utc)
        user_data["is_active"] = True
        user_data["wallet_balance"] = 0
        await db["users"].insert_one(user_data)
        return user_id
