from core.database import db_client
from fastapi import HTTPException
from datetime import datetime, timezone
from core.repositories.base_repository import RepositoryFactory
from loguru import logger


class PricingService:

    @staticmethod
    async def set_document_pricing(
        document_id: str, data: dict, current_user, db=None
    ) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
        update = {
            "price_dl": max(0, data.get("price_dl", 0)),
            "is_drm_protected": data.get("is_drm_protected", True),
            "updated_at": datetime.now(timezone.utc),
        }
        await db["documents"].update_one({"_id": document_id}, {"$set": update})
        logger.info("Cập nhật giá tài liệu thành công")
        return {"message": "Cập nhật cấu hình giá tài liệu thành công"}

    @staticmethod
    async def get_pricing_config(db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()

        config = await RepositoryFactory.get("system_config").find_one(
            {"_id": "pricing_tiers"}
        )
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
                    "features": [
                        "Advanced artificial intelligence suggestions",
                        "Priority administrative support",
                    ],
                },
                "PREMIUM": {
                    "monthly_price": 199000.0,
                    "features": [
                        "Unlimited resource access",
                        "Advanced logical verification tools",
                    ],
                },
            }
        }

        await RepositoryFactory.get("system_config").update_one(
            {"_id": "pricing_tiers"}, {"$set": default_config}, upsert=True
        )
        return default_config