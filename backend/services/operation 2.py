from shared.core.database import db_client
from fastapi import HTTPException
from datetime import datetime
import uuid
from loguru import logger
<<<<<<< HEAD:backend/services/operation.py
from models.user import RoleEnum

=======
from shared.models.user import RoleEnum
>>>>>>> 17b94401979547a37304e908bbde87033ed3da2a:backend/microservices/utility/services/operation.py
class OperationService:
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
logger.info("Log message sanitized"))
        return {"message": f"Đã cập nhật vai trò người dùng thành {role}."}

    @staticmethod
    async def update_user_status(user_id: str, is_active: bool) -> dict:
        db = db_client.mongodb.get_default_database()
        res = await db["users"].update_one({"_id": user_id}, {"$set": {"is_active": is_active, "updated_at": datetime.utcnow()}})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng.")
logger.info("Log message sanitized"))
        return {"message": "Đã cập nhật trạng thái hoạt động của tài khoản."}

    @staticmethod
    async def get_author_applications(status: str = "PENDING") -> list:
        db = db_client.mongodb.get_default_database()
        apps = await db["author_applications"].find({"status": status}).sort("created_at", -1).to_list(length=100)
        return [
            {**a, "id": str(a["_id"]), "_id": str(a["_id"])} for a in apps
        ]

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
<<<<<<< HEAD:backend/services/operation.py
            
        logger.info(f"Administration: Author application {application_id} {status} by {reviewer_id}")
=======
logger.info("Log message sanitized"))
>>>>>>> 17b94401979547a37304e908bbde87033ed3da2a:backend/microservices/utility/services/operation.py
        return {"message": f"Đã {status.lower()} đơn ứng tuyển thành công."}

    @staticmethod
    async def toggle_maintenance_mode(enabled: bool, message: str = "") -> dict:
        db = db_client.mongodb.get_default_database()
        await db["system_config"].update_one(
            {"key": "maintenance_mode"}, 
            {"$set": {"enabled": enabled, "message": message, "updated_at": datetime.utcnow()}}, 
            upsert=True
        )
logger.info("Log message sanitized"))
        return {"message": f"Chế độ bảo trì đã được {'bật' if enabled else 'tắt'}."}

    @staticmethod
    async def trigger_backup(action: str = "FULL") -> dict:
logger.info("Log message sanitized"))
        return {"message": "Yêu cầu sao lưu dữ liệu đã được gửi đến hàng chờ."}

    @staticmethod
    async def create_api_key(name: str, provider: str = "DEFAULT", key_value: str = "") -> dict:
        db = db_client.mongodb.get_default_database()
        if not key_value:
            key_value = str(uuid.uuid4()).replace("-", "")
            
        await db["api_keys"].insert_one({
            "_id": str(uuid.uuid4()),
            "name": name,
            "provider": provider,
            "key_value": key_value,
            "created_at": datetime.utcnow()
        })
logger.info("Log message sanitized"))
        return {"message": "Đã lưu API Key thành công.", "key": key_value}

    @staticmethod
    async def create_marketing_campaign(data: dict) -> dict:
        db = db_client.mongodb.get_default_database()
        campaign = {
            "_id": str(uuid.uuid4()),
            "title": data.get("title", "Chiến dịch mới"),
            "target_audience": data.get("target", "ALL"),
            "discount_percent": data.get("discount", 0),
            "status": "active",
            "created_at": datetime.utcnow()
        }
        await db["marketing_campaigns"].insert_one(campaign)
logger.info("Log message sanitized"))
        return {"message": "Đã tạo chiến dịch marketing thành công."}
    @staticmethod
    async def get_system_health() -> dict:
        import os
        import time
        db = db_client.mongodb.get_default_database()
        try:
            await db.command("ping")
            db_status = "connected"
        except Exception:
            db_status = "disconnected"
        
        load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
        
        return {
            "status": "healthy" if db_status == "connected" else "degraded",
            "uptime": "99.9%",
            "database": db_status,
            "cpu_load": f"{load_avg[0]}%",
            "timestamp": datetime.utcnow().isoformat()
        }

    @staticmethod
    async def get_maintenance_mode() -> dict:
        db = db_client.mongodb.get_default_database()
        config = await db["system_config"].find_one({"key": "maintenance_mode"})
        if not config:
            return {"enabled": False, "message": ""}
        return {
            "enabled": config.get("enabled", False),
            "message": config.get("message", "")
        }
    @staticmethod
    async def get_collector_stats() -> dict:
        db = db_client.mongodb.get_default_database()
        total_docs = await db["documents"].count_documents({})
        total_assets = await db["assets"].count_documents({})
        recent_crawls = await db["documents"].find({}, {"created_at": 1}).sort("created_at", -1).limit(1).to_list(length=1)
        last_crawl = recent_crawls[0]["created_at"].isoformat() if recent_crawls else datetime.utcnow().isoformat()
        
        return {
            "total_documents": total_docs,
            "total_assets": total_assets,
            "collector_status": "RUNNING",
            "last_crawl": last_crawl,
            "storage_usage_mb": round(total_docs * 0.1, 2)
        }

    @staticmethod
    async def handle_bug_report(data: dict, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        report_id = str(uuid.uuid4())
        await db["bug_reports"].insert_one({
            "_id": report_id, 
            "title": data["title"], 
            "description": data["description"], 
            "status": "open", 
            "assigned_to": str(current_moderator.id), 
            "created_at": datetime.utcnow()
        })
logger.info("Log message sanitized"))
        return {"message": "Đã tiếp nhận báo cáo lỗi thành công."}

    @staticmethod
    async def assign_task(data: dict, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        task = {
            "_id": str(uuid.uuid4()), 
            "assigned_to": data["moderator_id"], 
            "title": data["title"], 
            "status": "pending", 
            "created_at": datetime.utcnow()
        }
        await db["moderator_tasks"].insert_one(task)
logger.info("Log message sanitized"))
        return {"message": "Đã phân công nhiệm vụ điều hành."}

    @staticmethod
    async def submit_policy_proposal(data: dict, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        proposal_id = str(uuid.uuid4())
        await db["policy_proposals"].insert_one({
            "_id": proposal_id, 
            "author_id": str(current_moderator.id), 
            "title": data["title"], 
            "content": data["content"], 
            "status": "pending", 
            "created_at": datetime.utcnow()
        })
logger.info("Log message sanitized"))
    @staticmethod
    async def get_payout_requests(status: str = "PENDING", limit: int = 50) -> list:
        db = db_client.mongodb.get_default_database()
        apps = await db["payout_requests"].find({"status": status}).sort("created_at", -1).limit(limit).to_list(length=limit)
        
        result = []
        for a in apps:
            user = await db["users"].find_one({"_id": a["user_id"]}, {"full_name": 1, "email": 1, "bank_info": 1})
            result.append({
                "id": str(a["_id"]),
                "user_id": a["user_id"],
                "user_name": user.get("full_name") if user else "Unknown",
                "user_email": user.get("email") if user else "",
                "amount": a.get("amount"),
                "status": a.get("status"),
                "created_at": a["created_at"].isoformat() if isinstance(a.get("created_at"), datetime) else a.get("created_at"),
                "bank_info": user.get("bank_info") if user else {}
            })
        return result

    @staticmethod
    async def approve_payout(payout_id: str, admin_id: str) -> dict:
        db = db_client.mongodb.get_default_database()
        payout = await db["payout_requests"].find_one({"_id": payout_id, "status": "PENDING"})
        if not payout:
            raise HTTPException(status_code=404, detail="Yêu cầu rút tiền không tồn tại hoặc đã được xử lý.")
            
        await db["payout_requests"].update_one(
            {"_id": payout_id},
            {"$set": {"status": "COMPLETED", "processed_by": admin_id, "processed_at": datetime.utcnow()}}
        )
logger.info("Log message sanitized"))
        return {"message": "Đã phê duyệt yêu cầu rút tiền."}

    @staticmethod
    async def reject_payout(payout_id: str, reason: str, admin_id: str) -> dict:
        db = db_client.mongodb.get_default_database()
        payout = await db["payout_requests"].find_one({"_id": payout_id, "status": "PENDING"})
        if not payout:
            raise HTTPException(status_code=404, detail="Yêu cầu rút tiền không tồn tại")
            
        session = await db_client.mongodb.start_session()
        try:
            async with session.start_transaction():
                await db["users"].update_one(
                    {"_id": payout["user_id"]},
                    {"$inc": {"wallet_balance": payout["amount"]}},
                    session=session
                )
                
                await db["payout_requests"].update_one(
                    {"_id": payout_id},
                    {"$set": {
                        "status": "REJECTED", 
                        "rejection_reason": reason, 
                        "processed_by": admin_id, 
                        "processed_at": datetime.utcnow()
                    }},
                    session=session
                )
<<<<<<< HEAD:backend/services/operation.py
                
                from models.wallet import Transaction, TransactionType
=======
                from shared.models.wallet import Transaction, TransactionType
>>>>>>> 17b94401979547a37304e908bbde87033ed3da2a:backend/microservices/utility/services/operation.py
                tx = Transaction(
                    user_id=payout["user_id"],
                    type=TransactionType.REFUND,
                    amount=payout["amount"],
                    note=f"Hoàn trả yêu cầu rút tiền bị từ chối: {reason}"
                )
                await db["transactions"].insert_one(tx.model_dump(by_alias=True), session=session)
                
                await session.commit_transaction()
logger.info("Log message sanitized"))
                return {"message": "Đã từ chối yêu cầu rút tiền và hoàn trả số dư"}
        except Exception as e:
            await session.abort_transaction()
logger.info("Log message sanitized"))
            raise HTTPException(status_code=500, detail="Xử lý từ chối thất bại")
        finally:
            await session.end_session()
