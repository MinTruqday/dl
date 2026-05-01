from core.database import db_client
from fastapi import HTTPException
from datetime import datetime
import uuid
from loguru import logger
from models.user import RoleEnum

class AdministrationService:
    @staticmethod
    async def get_all_users(limit: int = 50, offset: int = 0) -> list:
        db = db_client.mongodb.get_default_database()
        users = await db["users"].find().sort("created_at", -1).skip(offset).limit(limit).to_list(length=limit)
        return [
            {
                "id": str(u["_id"]),
                "email": u.get("email"),
                "full_name": u.get("full_name"),
                "role": u.get("role"),
                "is_active": u.get("is_active", True),
                "created_at": u["created_at"].isoformat() if isinstance(u.get("created_at"), datetime) else u.get("created_at"),
            }
            for u in users
        ]

    @staticmethod
    async def update_user_role(user_id: str, role: str) -> dict:
        db = db_client.mongodb.get_default_database()
        res = await db["users"].update_one({"_id": user_id}, {"$set": {"role": role, "updated_at": datetime.utcnow()}})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng.")
        logger.info(f"Administration: Role for user {user_id} updated to {role}")
        return {"message": f"Đã cập nhật vai trò người dùng thành {role}."}

    @staticmethod
    async def update_user_status(user_id: str, is_active: bool) -> dict:
        db = db_client.mongodb.get_default_database()
        res = await db["users"].update_one({"_id": user_id}, {"$set": {"is_active": is_active, "updated_at": datetime.utcnow()}})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng.")
        logger.info(f"Administration: User {user_id} status updated to {is_active}")
        return {"message": "Đã cập nhật trạng thái hoạt động của tài khoản."}

    @staticmethod
    async def get_author_applications(status: str = "PENDING") -> list:
        db = db_client.mongodb.get_default_database()
        return await db["author_applications"].find({"status": status}).sort("created_at", -1).to_list(length=100)

    @staticmethod
    async def review_author_application(application_id: str, status: str, reason: str, reviewer_id: str) -> dict:
        db = db_client.mongodb.get_default_database()
        app = await db["author_applications"].find_one({"_id": application_id})
        if not app:
            raise HTTPException(status_code=404, detail="Đơn ứng tuyển không tồn tại.")
        
        await db["author_applications"].update_one(
            {"_id": application_id},
            {"$set": {"status": status, "reason": reason, "reviewed_by": reviewer_id, "reviewed_at": datetime.utcnow()}}
        )
        
        if status == "APPROVED":
            await db["users"].update_one({"_id": app["user_id"]}, {"$set": {"role": RoleEnum.AUTHOR}})
            
        logger.info(f"Administration: Author application {application_id} {status} by {reviewer_id}")
        return {"message": f"Đã {status.lower()} đơn ứng tuyển thành công."}

    @staticmethod
    async def toggle_maintenance_mode(enabled: bool, message: str = "") -> dict:
        db = db_client.mongodb.get_default_database()
        await db["system_config"].update_one(
            {"key": "maintenance_mode"}, 
            {"$set": {"enabled": enabled, "message": message, "updated_at": datetime.utcnow()}}, 
            upsert=True
        )
        logger.warning(f"Administration: Maintenance mode {'enabled' if enabled else 'disabled'} by admin")
        return {"message": f"Chế độ bảo trì đã được {'bật' if enabled else 'tắt'}."}

    @staticmethod
    async def trigger_backup(action: str) -> dict:
        logger.info(f"Administration: Backup action '{action}' triggered")
        return {"message": "Yêu cầu sao lưu dữ liệu đã được gửi đến hàng chờ."}

    @staticmethod
    async def create_api_key(name: str, provider: str, key_value: str) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["api_keys"].insert_one({
            "_id": str(uuid.uuid4()),
            "name": name,
            "provider": provider,
            "key_value": key_value,
            "created_at": datetime.utcnow()
        })
        logger.info(f"Administration: API Key '{name}' for '{provider}' created")
        return {"message": "Đã lưu API Key thành công."}

    @staticmethod
    async def create_marketing_campaign(title: str, target: str, discount: int) -> dict:
        db = db_client.mongodb.get_default_database()
        campaign = {
            "_id": str(uuid.uuid4()),
            "title": title,
            "target_audience": target,
            "discount_percent": discount,
            "status": "active",
            "created_at": datetime.utcnow()
        }
        await db["marketing_campaigns"].insert_one(campaign)
        logger.info(f"Administration: Campaign '{title}' created")
        return {"message": "Đã tạo chiến dịch marketing thành công."}
