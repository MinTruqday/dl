from datetime import datetime, timezone
from core.database import db_client
from fastapi import HTTPException
from loguru import logger

class PricingService:

    @staticmethod
    async def set_document_pricing(document_id: str, data: dict, current_user, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        doc = await target_db["documents"].find_one({"_id": document_id, "creator_id": str(current_user.get("id"))})
        
        if not doc:
            raise HTTPException(status_code=404, detail="Lỗi truy xuất cơ sở dữ liệu hệ thống")
            
        update = {
            "price_dl": max(0, data.get("price_dl", 0)),
            "is_drm_protected": data.get("is_drm_protected", True),
            "updated_at": datetime.now(timezone.utc),
        }
        await target_db["documents"].update_one({"_id": document_id}, {"$set": update})
        logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        return {"message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"}

    @staticmethod
    async def get_pricing_config(db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        config = await target_db["system_config"].find_one({"_id": "pricing_tiers"})
        if config:
            return config

        default_config = {
            "tiers": {
                "BASIC": {
                    "monthly_price": 0.0,
                    "features": ["Standard reading access", "Basic collection tools"],
                },
                "PRO": {
                    "monthly_price": 99000.0,
                    "features": ["Advanced artificial intelligence suggestions", "Priority administrative support"],
                },
                "PREMIUM": {
                    "monthly_price": 199000.0,
                    "features": ["Unlimited resource access", "Advanced logical verification tools"],
                },
            }
        }

        await target_db["system_config"].update_one({"_id": "pricing_tiers"}, {"$set": default_config}, upsert=True)
        return default_config