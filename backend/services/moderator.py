from core.database import db_client
from fastapi import HTTPException
from datetime import datetime, timedelta
import uuid
import json
from loguru import logger


class ModeratorService:
    @staticmethod
    async def get_report_queue(status_filter: str = "pending", skip: int = 0, limit: int = 30) -> list:
        db = db_client.mongodb.get_default_database()
        query = {"status": status_filter} if status_filter else {}
        reports = await db["reports"].find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
        result = []
        for r in reports:
            reporter = await db["users"].find_one({"_id": r.get("reporter_id")}, {"full_name": 1})
            result.append({
                "id": str(r["_id"]),
                "item_type": r.get("item_type", ""),
                "item_id": r.get("item_id", ""),
                "reason": r.get("reason", ""),
                "description": r.get("description", ""),
                "status": r.get("status", "pending"),
                "reporter_name": reporter.get("full_name", "Ẩn danh") if reporter else "Ẩn danh",
                "created_at": r["created_at"].isoformat() if isinstance(r.get("created_at"), datetime) else r.get("created_at"),
            })
        return result

    @staticmethod
    async def warn_user(user_id: str, reason: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        user = await db["users"].find_one({"_id": user_id})
        if not user: raise HTTPException(status_code=404, detail="Không tìm thấy người dùng.")
        warning = {"_id": str(uuid.uuid4()), "user_id": user_id, "moderator_id": str(current_moderator.id), "reason": reason, "created_at": datetime.utcnow()}
        await db["warnings"].insert_one(warning)
        await db["audit_logs"].insert_one({"action": "WARN_USER", "actor_id": str(current_moderator.id), "target_user_id": user_id, "reason": reason, "timestamp": datetime.utcnow()})
        if db_client.redis:
            await db_client.redis.publish(f"user_notifications:{user_id}", json.dumps({"title": "Cảnh báo hệ thống", "body": f"Bạn nhận được cảnh báo: {reason}"}))
        return {"message": "Đã gửi cảnh báo."}

    @staticmethod
    async def lock_user(user_id: str, reason: str, duration_hours: int, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        lock_until = datetime.utcnow() + timedelta(hours=duration_hours)
        await db["users"].update_one({"_id": user_id}, {"$set": {"is_active": False, "locked_until": lock_until, "lock_reason": reason, "updated_at": datetime.utcnow()}})
        await db["audit_logs"].insert_one({"action": "LOCK_USER", "actor_id": str(current_moderator.id), "target_user_id": user_id, "reason": reason, "duration": duration_hours, "timestamp": datetime.utcnow()})
        return {"message": f"Đã khóa tài khoản {duration_hours} giờ."}

    @staticmethod
    async def manage_tags(action: str, tag_name: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        if action == "create":
            await db["system_tags"].insert_one({"_id": str(uuid.uuid4()), "name": tag_name.lower(), "created_at": datetime.utcnow()})
            return {"message": f"Đã tạo thẻ '{tag_name}'."}
        elif action == "delete":
            await db["system_tags"].delete_one({"name": tag_name.lower()})
            return {"message": f"Đã xóa thẻ '{tag_name}'."}
        return {"message": "Hành động không hợp lệ."}

    @staticmethod
    async def get_all_tags() -> list:
        db = db_client.mongodb.get_default_database()
        tags = await db["system_tags"].find().to_list(length=200)
        return [{"id": t["_id"], "name": t.get("name", "")} for t in tags]

    @staticmethod
    async def manage_blacklist(action: str, keyword: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        if action == "add":
            await db["blacklist_keywords"].insert_one({"_id": str(uuid.uuid4()), "keyword": keyword.lower(), "created_at": datetime.utcnow()})
            return {"message": f"Đã thêm '{keyword}' vào danh sách cấm."}
        elif action == "remove":
            await db["blacklist_keywords"].delete_one({"keyword": keyword.lower()})
            return {"message": f"Đã xóa '{keyword}' khỏi danh sách cấm."}
        return {"message": "Hành động không hợp lệ."}

    @staticmethod
    async def get_blacklist() -> list:
        db = db_client.mongodb.get_default_database()
        keywords = await db["blacklist_keywords"].find().to_list(length=500)
        return [{"id": k["_id"], "keyword": k.get("keyword", "")} for k in keywords]

    @staticmethod
    async def remove_violating_content(item_type: str, item_id: str, reason: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        collection_map = {"document": "documents", "story": "stories", "comment": "comments"}
        coll = collection_map.get(item_type)
        if not coll: raise HTTPException(status_code=400, detail="Loại nội dung không hợp lệ.")
        await db[coll].update_one({"_id": item_id}, {"$set": {"is_removed": True, "removal_reason": reason, "removed_at": datetime.utcnow()}})
        return {"message": "Đã gỡ bỏ nội dung."}

    @staticmethod
    async def get_community_metrics() -> dict:
        db = db_client.mongodb.get_default_database()
        total_users = await db["users"].count_documents({})
        total_documents = await db["documents"].count_documents({})
        return {"total_users": total_users, "total_documents": total_documents, "timestamp": datetime.utcnow()}

    @staticmethod
    async def get_moderator_activity_log(moderator_id: str) -> list:
        db = db_client.mongodb.get_default_database()
        logs = await db["audit_logs"].find({"actor_id": moderator_id}).sort("timestamp", -1).limit(50).to_list(length=50)
        return [{"action": l.get("action"), "timestamp": l["timestamp"].isoformat() if isinstance(l.get("timestamp"), datetime) else ""} for l in logs]

    @staticmethod
    async def resolve_copyright_dispute(dispute_id: str, resolution: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["copyright_disputes"].update_one({"_id": dispute_id}, {"$set": {"status": "resolved", "resolution": resolution, "resolved_by": str(current_moderator.id), "resolved_at": datetime.utcnow()}})
        return {"message": "Đã giải quyết tranh chấp bản quyền."}

    @staticmethod
    async def handle_bug_report(data: dict, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["bug_reports"].insert_one({"_id": str(uuid.uuid4()), "title": data["title"], "description": data["description"], "status": "open", "assigned_to": str(current_moderator.id), "created_at": datetime.utcnow()})
        return {"message": "Đã tiếp nhận báo cáo lỗi."}

    @staticmethod
    async def set_nsfw_sensitivity(level: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["system_config"].update_one({"key": "nsfw_filter_level"}, {"$set": {"value": level, "updated_at": datetime.utcnow()}}, upsert=True)
        return {"message": f"Thiết lập bộ lọc NSFW mức '{level}'."}

    @staticmethod
    async def assign_task(data: dict, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        task = {"_id": str(uuid.uuid4()), "assigned_to": data["moderator_id"], "title": data["title"], "status": "pending", "created_at": datetime.utcnow()}
        await db["moderator_tasks"].insert_one(task)
        return {"message": "Đã phân công nhiệm vụ."}

    @staticmethod
    async def submit_policy_proposal(data: dict, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["policy_proposals"].insert_one({"_id": str(uuid.uuid4()), "author_id": str(current_moderator.id), "title": data["title"], "content": data["content"], "status": "pending", "created_at": datetime.utcnow()})
        return {"message": "Đề xuất đã được ghi nhận."}
    @staticmethod
    async def get_payout_queue(status: str = "pending") -> list:
        db = db_client.mongodb.get_default_database()
        payouts = await db["payout_requests"].find({"status": status}).sort("created_at", -1).to_list(length=100)
        result = []
        for p in payouts:
            user = await db["users"].find_one({"_id": p.get("user_id")}, {"full_name": 1})
            result.append({
                "id": str(p["_id"]),
                "user_id": p.get("user_id"),
                "user_name": user.get("full_name") if user else "Unknown",
                "amount": p.get("amount"),
                "status": p.get("status"),
                "created_at": p["created_at"].isoformat() if isinstance(p.get("created_at"), datetime) else p.get("created_at")
            })
        return result

    @staticmethod
    async def verify_payout(payout_id: str, action: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        payout = await db["payout_requests"].find_one({"_id": payout_id})
        if not payout: raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu.")
        
        status = "approved" if action == "approve" else "rejected"
        await db["payout_requests"].update_one({"_id": payout_id}, {"$set": {"status": status, "processed_by": str(current_moderator.id), "processed_at": datetime.utcnow()}})
        
        await db["audit_logs"].insert_one({"action": f"PAYOUT_{action.upper()}", "actor_id": str(current_moderator.id), "payout_id": payout_id, "timestamp": datetime.utcnow()})
        return {"message": f"Đã {status} yêu cầu rút tiền."}

    @staticmethod
    async def get_approval_queue(skip: int = 0, limit: int = 30) -> list:
        db = db_client.mongodb.get_default_database()
        documents = await db["documents"].find({"status": "processing_publish"}).sort("updated_at", 1).skip(skip).limit(limit).to_list(length=limit)
        return [{
            "id": str(b["_id"]),
            "title": b.get("title", ""),
            "author_id": b.get("author_id"),
            "submitted_at": b.get("updated_at", datetime.utcnow()).isoformat() if isinstance(b.get("updated_at"), datetime) else ""
        } for b in documents]

    @staticmethod
    async def moderate_document(document_id: str, action: str, reason: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        status = "published" if action == "approve" else "rejected"
        await db["documents"].update_one(
            {"_id": document_id},
            {"$set": {"status": status, "moderation_reason": reason, "moderated_by": str(current_moderator.id), "moderated_at": datetime.utcnow()}}
        )
        await db["audit_logs"].insert_one({"action": f"DOCUMENT_{action.upper()}", "actor_id": str(current_moderator.id), "document_id": document_id, "reason": reason, "timestamp": datetime.utcnow()})
        return {"message": f"Đã {status} tài liệu."}

    @staticmethod
    async def shadowban_user(user_id: str, is_banned: bool, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["users"].update_one({"_id": user_id}, {"$set": {"is_shadowbanned": is_banned, "updated_at": datetime.utcnow()}})
        action = "SHADOWBAN" if is_banned else "UNSHADOWBAN"
        await db["audit_logs"].insert_one({"action": action, "actor_id": str(current_moderator.id), "target_user_id": user_id, "timestamp": datetime.utcnow()})
        return {"message": f"Đã {'shadowban' if is_banned else 'gỡ shadowban'} người dùng."}

    @staticmethod
    async def verify_kyc(user_id: str, status: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["users"].update_one({"_id": user_id}, {"$set": {"kyc_status": status, "is_kyc_verified": status == "VERIFIED", "updated_at": datetime.utcnow()}})
        await db["audit_logs"].insert_one({"action": f"KYC_{status}", "actor_id": str(current_moderator.id), "target_user_id": user_id, "timestamp": datetime.utcnow()})
        return {"message": f"Đã cập nhật trạng thái KYC: {status}."}

    @staticmethod
    async def bulk_delete_comments(user_id: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        result = await db["comments"].delete_many({"user_id": user_id})
        await db["audit_logs"].insert_one({"action": "BULK_DELETE_COMMENTS", "actor_id": str(current_moderator.id), "target_user_id": user_id, "count": result.deleted_count, "timestamp": datetime.utcnow()})
        return {"message": f"Đã xóa {result.deleted_count} bình luận."}

    @staticmethod
    async def get_moderator_notes(user_id: str) -> list:
        db = db_client.mongodb.get_default_database()
        notes = await db["moderator_notes"].find({"user_id": user_id}).sort("created_at", -1).to_list(length=100)
        return [{
            "id": str(n["_id"]),
            "note": n.get("note", ""),
            "moderator_id": n.get("moderator_id"),
            "created_at": n["created_at"].isoformat() if isinstance(n.get("created_at"), datetime) else ""
        } for n in notes]

    @staticmethod
    async def add_moderator_note(user_id: str, note: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["moderator_notes"].insert_one({
            "_id": str(uuid.uuid4()),
            "user_id": user_id,
            "moderator_id": str(current_moderator.id),
            "note": note,
            "created_at": datetime.utcnow()
        })
        return {"message": "Đã thêm ghi chú."}
