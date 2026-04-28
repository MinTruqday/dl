from core.config import settings
from core.database import db_client
from models.user import RoleEnum
from fastapi import HTTPException
from datetime import datetime
import uuid
import os
import httpx
from loguru import logger

class AdminService:
    @staticmethod
    async def get_audit_logs(limit: int, offset: int):
        db = db_client.mongodb.get_default_database()
        cursor = db["audit_logs"].find().sort("timestamp", -1).skip(offset).limit(limit)
        logs = await cursor.to_list(length=limit)
        for log in logs:
            log["_id"] = str(log["_id"])
        return logs

    @staticmethod
    async def get_all_users(limit: int, offset: int):
        db = db_client.mongodb.get_default_database()
        cursor = db["users"].find({}, {"password_hash": 0}).skip(offset).limit(limit)
        users = await cursor.to_list(length=limit)
        for u in users:
            u["_id"] = str(u["_id"])
        return users

    @staticmethod
    async def toggle_shadowban(user_id: str, is_shadowbanned: bool):
        db = db_client.mongodb.get_default_database()
        res = await db["users"].update_one({"_id": user_id}, {"$set": {"is_shadowbanned": is_shadowbanned, "updated_at": datetime.utcnow()}})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy thông tin người dùng yêu cầu.")
        logger.info(f"Shadowban status updated for user {user_id} to {is_shadowbanned}")
        return {"status": "success", "is_shadowbanned": is_shadowbanned}

    @staticmethod
    async def update_user_role(user_id: str, role: RoleEnum):
        db = db_client.mongodb.get_default_database()
        res = await db["users"].update_one({"_id": user_id}, {"$set": {"role": role, "updated_at": datetime.utcnow()}})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng để cập nhật quyền hạn.")
        logger.info(f"User {user_id} role upgraded to {role}")
        return {"status": "success", "role": role}

    @staticmethod
    async def update_user_status(user_id: str, is_active: bool):
        db = db_client.mongodb.get_default_database()
        res = await db["users"].update_one({"_id": user_id}, {"$set": {"is_active": is_active, "updated_at": datetime.utcnow()}})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản người dùng.")
        logger.info(f"User {user_id} activation status set to {is_active}")
        return {"status": "success", "is_active": is_active}

    @staticmethod
    async def review_author_application(application_id: str, review_status: str, reason: str, admin_id: str):
        db = db_client.mongodb.get_default_database()
        app = await db["author_applications"].find_one({"_id": application_id})
        if not app:
            raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ đăng ký tác giả.")
        
        await db["author_applications"].update_one(
            {"_id": application_id},
            {"$set": {
                "status": review_status,
                "reviewed_by": admin_id,
                "reviewed_at": datetime.utcnow(),
                "review_reason": reason
            }}
        )
        
        user_update = {"author_status": review_status}
        if review_status == "APPROVED":
            user_update["role"] = RoleEnum.AUTHOR
            
        await db["users"].update_one({"_id": app["user_id"]}, {"$set": user_update})
        
        await db["notifications"].insert_one({
            "_id": str(uuid.uuid4()),
            "user_id": app["user_id"],
            "title": "Thông báo đăng ký tác giả",
            "message": f"Hồ sơ của bạn đã được {review_status}. Ghi chú: {reason}",
            "is_read": False,
            "created_at": datetime.utcnow()
        })
        logger.info(f"Author application {application_id} reviewed with status {review_status}")
        return {"status": "success", "message": "Đã xử lý hồ sơ đăng ký thành công."}

    @staticmethod
    async def get_stats():
        db = db_client.mongodb.get_default_database()
        user_count = await db["users"].count_documents({})
        document_count = await db["documents"].count_documents({})
        active_users_24h = await db["users"].count_documents({"updated_at": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0)}})
        revenue_cursor = db["transactions"].aggregate([
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ])
        revenue_res = await revenue_cursor.to_list(length=1)
        total_revenue = revenue_res[0]["total"] if revenue_res else 0
        return {
            "total_users": user_count,
            "total_documents": document_count,
            "active_users_24h": active_users_24h,
            "total_revenue": total_revenue,
            "currency": "dl",
            "timestamp": datetime.utcnow()
        }

    @staticmethod
    async def get_config():
        db = db_client.mongodb.get_default_database()
        config = await db["settings"].find_one({"_id": "system_config"})
        if not config:
            config = {
                "_id": "system_config",
                "commission_rate": 0.1,
                "withdrawal_fee_dl": 1000,
                "rag_top_k": 5,
                "ai_model": getattr(settings, "LLAMA_MODEL", None),
                "updated_at": datetime.utcnow()
            }
            await db["settings"].insert_one(config)
        return config

    @staticmethod
    async def update_config(new_config: dict):
        db = db_client.mongodb.get_default_database()
        new_config["updated_at"] = datetime.utcnow()
        await db["settings"].update_one({"_id": "system_config"}, {"$set": new_config}, upsert=True)
        logger.info("System configuration updated successfully")
        return {"status": "success", "config": new_config}

    @staticmethod
    async def get_sys_health():
        db = db_client.mongodb.get_default_database()
        health = {"status": "healthy", "mongodb": "disconnected", "redis": "disconnected"}
        try:
            await db.command("ping")
            health["mongodb"] = "connected"
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            health["status"] = "degraded"
        if db_client.redis:
            try:
                await db_client.redis.ping()
                health["redis"] = "connected"
            except Exception as e:
                logger.error(f"Redis health check failed: {e}")
                health["status"] = "degraded"
        return health

    @staticmethod
    async def get_ai_gateway_stats():
        rag_url = getattr(settings, "AGENTIC_RAG_URL", None)
        if not rag_url:
            return {"status": "not_configured", "active_models": [], "total_requests_24h": 0}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{rag_url}/api/inference/stats")
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.warning(f"Failed to fetch AI gateway stats: {e}")
        return {
            "active_models": [getattr(settings, "LLAMA_MODEL", None), getattr(settings, "EMBEDDING_MODEL", None)],
            "total_requests_24h": 0,
            "status": "operational"
        }

    @staticmethod
    async def trigger_backup(action: str):
        db = db_client.mongodb.get_default_database()
        await db["audit_logs"].insert_one({
            "action": "TRIGGER_BACKUP",
            "type": action,
            "timestamp": datetime.utcnow()
        })
        logger.info(f"System backup triggered: {action}")
        return {"message": f"Tiến trình {action} dữ liệu hệ thống đã được khởi tạo thành công."}

    @staticmethod
    async def create_marketing_campaign(title: str, target_audience: str, discount_percent: int):
        db = db_client.mongodb.get_default_database()
        campaign = {"_id": str(uuid.uuid4()), "title": title, "target_audience": target_audience, "discount_percent": discount_percent, "created_at": datetime.utcnow()}
        await db["campaigns"].insert_one(campaign)
        logger.info(f"Marketing campaign created: {title}")
        return {"message": "Chiến dịch Marketing mới đã được khởi tạo thành công.", "campaign_id": campaign["_id"]}

    @staticmethod
    async def toggle_maintenance_mode(enabled: bool, message: str = ""):
        db = db_client.mongodb.get_default_database()
        await db["system_config"].update_one({"key": "maintenance_mode"}, {"$set": {"value": {"enabled": enabled, "message": message}, "updated_at": datetime.utcnow()}}, upsert=True)
        logger.info(f"Maintenance mode set to {enabled}")
        return {"message": f"Đã {'kích hoạt' if enabled else 'tắt'} chế độ bảo trì hệ thống thành công."}

    @staticmethod
    async def get_maintenance_mode():
        db = db_client.mongodb.get_default_database()
        config = await db["system_config"].find_one({"key": "maintenance_mode"})
        return config.get("value", {"enabled": False, "message": ""}) if config else {"enabled": False, "message": ""}

    @staticmethod
    async def update_security_config(data: dict):
        db = db_client.mongodb.get_default_database()
        await db["system_config"].update_one({"key": "security_config"}, {"$set": {"value": data, "updated_at": datetime.utcnow()}}, upsert=True)
        logger.info("Security configuration updated")
        return {"message": "Cấu hình bảo mật hệ thống đã được cập nhật thành công."}

    @staticmethod
    async def create_banner(data: dict):
        db = db_client.mongodb.get_default_database()
        banner_id = str(uuid.uuid4())
        data["_id"] = banner_id
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()
        await db["banners"].insert_one(data)
        logger.info(f"New banner created: {banner_id}")
        return {"id": banner_id, "message": "Banner quảng cáo đã được tạo thành công."}

    @staticmethod
    async def get_banners(active_only: bool = False):
        db = db_client.mongodb.get_default_database()
        query = {"is_active": True} if active_only else {}
        cursor = db["banners"].find(query).sort("order", 1)
        banners = await cursor.to_list(length=100)
        for b in banners:
            b["id"] = str(b.pop("_id"))
        return banners

    @staticmethod
    async def update_banner(banner_id: str, data: dict):
        db = db_client.mongodb.get_default_database()
        data["updated_at"] = datetime.utcnow()
        res = await db["banners"].update_one({"_id": banner_id}, {"$set": data})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy Banner yêu cầu để cập nhật.")
        logger.info(f"Banner {banner_id} updated")
        return {"id": banner_id, "status": "success", "message": "Thông tin Banner đã được cập nhật."}

    @staticmethod
    async def delete_banner(banner_id: str):
        db = db_client.mongodb.get_default_database()
        res = await db["banners"].delete_one({"_id": banner_id})
        if res.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy Banner yêu cầu để xóa.")
        logger.info(f"Banner {banner_id} deleted")
        return {"status": "success", "message": "Đã xóa Banner thành công."}

    @staticmethod
    async def impersonate_user(user_id: str, current_admin) -> dict:
        db = db_client.mongodb.get_default_database()
        user = await db["users"].find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng yêu cầu hóa thân.")
        
        impersonation_token = str(uuid.uuid4())
        await db["audit_logs"].insert_one({
            "action": "IMPERSONATE_USER",
            "actor_id": str(current_admin.id),
            "target_user_id": user_id,
            "timestamp": datetime.utcnow()
        })
        logger.info(f"Admin {current_admin.id} started impersonating user {user_id}")
        return {"message": f"Phiên hóa thân (Impersonate) cho người dùng {user.get('full_name')} đã bắt đầu.", "user_id": user_id, "token": impersonation_token}

    @staticmethod
    async def manage_dl_packages(action: str, data: dict = None) -> list:
        db = db_client.mongodb.get_default_database()
        if action == "list":
            return await db["dl_packages"].find().to_list(length=50)
        elif action == "create":
            pkg = {"_id": str(uuid.uuid4()), **data, "created_at": datetime.utcnow()}
            await db["dl_packages"].insert_one(pkg)
            logger.info(f"New dl package created: {data.get('name')}")
            return {"message": "Gói nạp dl mới đã được tạo thành công."}
        return []
