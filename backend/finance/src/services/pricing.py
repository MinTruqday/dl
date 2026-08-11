from src.core.logic_logger import log_logic_execution
from datetime import datetime, timezone

from fastapi import HTTPException
from loguru import logger

from src.core.infrastructure.database import database
from src.repositories.pricing import PricingRepository

class PricingService:

    @staticmethod
    @log_logic_execution
    async def set_document_pricing(
        document_id: str, data: dict, current_user
    ) -> dict:
        doc = await PricingRepository.get_document(document_id, str(current_user.id))
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu tài liệu yêu cầu để cập nhật giá")
        update = {
            "price_dl": max(0, data.get("price_dl", 0)),
            "is_drm_protected": data.get("is_drm_protected", True),
            "updated_at": datetime.now(timezone.utc),
        }
        await PricingRepository.update_document(
            document_id,
            {"$set": update},
            str(current_user.id),
            getattr(current_user.role, "value", current_user.role) == "admin",
        )
        logger.info("Document pricing configuration updated")
        return {"message": "Cập nhật cấu hình giá bán tài liệu hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def get_pricing_config() -> dict:
        config = await PricingRepository.get_pricing_config()
        if config:
            tiers = config.setdefault("tiers", {})
            basic = tiers.setdefault("BASIC", {})
            features = list(basic.get("features") or [])
            qwen_features = [
                feature for feature in features if "qwen" in str(feature).lower()
            ]
            if qwen_features:
                features = [
                    "Trợ lý AI tiêu chuẩn"
                    if "qwen" in str(feature).lower()
                    else feature
                    for feature in features
                ]
                basic["features"] = features
                await PricingRepository.update_pricing_config(
                    {"$set": {"tiers.BASIC.features": features}},
                    upsert=True,
                )
            elif not any("trợ lý ai" in str(feature).lower() for feature in features):
                features.insert(0, "Trợ lý AI tiêu chuẩn")
                basic["features"] = features
                await PricingRepository.update_pricing_config(
                    {"$set": {"tiers.BASIC.features": features}},
                    upsert=True,
                )
            return config

        default_config = {
            "tiers": {
                "BASIC": {
                    "name": "Cơ bản",
                    "monthly_price": 0.0,
                    "features": [
                        "Trợ lý AI tiêu chuẩn",
                        "Truy cập đọc tài liệu tiêu chuẩn",
                        "Các công cụ sưu tầm cơ bản",
                    ],
                },
                "PRO": {
                    "name": "Chuyên sâu",
                    "monthly_price": 99000.0,
                    "features": [
                        "Gợi ý trí tuệ nhân tạo nâng cao",
                        "Hỗ trợ quản trị ưu tiên",
                    ],
                },
                "PREMIUM": {
                    "name": "Toàn năng",
                    "monthly_price": 199000.0,
                    "features": [
                        "Truy cập tài nguyên không giới hạn",
                        "Công cụ xác minh logic chuyên sâu",
                    ],
                },
            }
        }

        await PricingRepository.update_pricing_config({"$set": default_config}, upsert=True)
        return default_config
