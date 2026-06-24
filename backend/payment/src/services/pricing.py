from datetime import datetime, timezone

from fastapi import HTTPException
from loguru import logger

from shared.infrastructure.database import database
from src.repositories.pricing import PricingRepository


class PricingService:

    @staticmethod
    async def set_document_pricing(
        document_id: str, data: dict, current_user, db=None
    ) -> dict:
        doc = await PricingRepository.get_document(document_id, str(current_user.id))
        if not doc:
            raise HTTPException(status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn")
        update = {
            "price_dl": max(0, data.get("price_dl", 0)),
            "is_drm_protected": data.get("is_drm_protected", True),
            "updated_at": datetime.now(timezone.utc),
        }
        await PricingRepository.update_document(document_id, {"$set": update})
        logger.info("Cập nhật giá tài liệu thành công")
        return {"message": "Cập nhật cấu hình giá tài liệu thành công"}

    @staticmethod
    async def get_pricing_config(db=None) -> dict:
        config = await PricingRepository.get_pricing_config()
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

        await PricingRepository.update_pricing_config({"$set": default_config}, upsert=True)
        return default_config
