from shared.core.database import db_client
from fastapi import HTTPException
from datetime import datetime
import uuid
from loguru import logger
class CouponService:
    @staticmethod
    async def create_coupon(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        coupon = {
            "_id": str(uuid.uuid4()),
            "author_id": str(current_user.id),
            "code": data["code"].upper(),
            "discount_percent": min(100, max(1, data.get("discount_percent", 10))),
            "max_uses": data.get("max_uses", 100),
            "used_count": 0,
            "document_id": data.get("document_id"),
            "expires_at": datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            "is_active": True,
            "created_at": datetime.utcnow(),
        }
        existing = await db["coupons"].find_one({"code": coupon["code"]})
        if existing:
            raise HTTPException(status_code=400, detail="Mã giảm giá này đã tồn tại trên hệ thống.")
        await db["coupons"].insert_one(coupon)
logger.info("Log message sanitized"))
        return {"message": "Tạo mã giảm giá thành công.", "coupon_id": coupon["_id"]}
    @staticmethod
    async def get_my_coupons(current_user) -> list:
        db = db_client.mongodb.get_default_database()
        coupons = await db["coupons"].find(
            {"author_id": str(current_user.id)}
        ).sort("created_at", -1).to_list(length=50)
        return [
            {
                "id": c["_id"],
                "code": c.get("code", ""),
                "discount_percent": c.get("discount_percent", 0),
                "max_uses": c.get("max_uses", 0),
                "used_count": c.get("used_count", 0),
                "document_id": c.get("document_id"),
                "is_active": c.get("is_active", True),
                "expires_at": c["expires_at"].isoformat() if isinstance(c.get("expires_at"), datetime) else c.get("expires_at"),
            }
            for c in coupons
        ]
    @staticmethod
    async def toggle_coupon_status(coupon_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        coupon = await db["coupons"].find_one({"_id": coupon_id, "author_id": str(current_user.id)})
        if not coupon:
            raise HTTPException(status_code=404, detail="Mã giảm giá không tồn tại.")
        new_status = not coupon.get("is_active", True)
        await db["coupons"].update_one({"_id": coupon_id}, {"$set": {"is_active": new_status}})
logger.info("Log message sanitized"))
        return {"message": "Đã cập nhật trạng thái mã giảm giá.", "is_active": new_status}
    @staticmethod
    async def delete_coupon(coupon_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        res = await db["coupons"].delete_one({"_id": coupon_id, "author_id": str(current_user.id)})
        if res.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Mã giảm giá không tồn tại.")
logger.info("Log message sanitized"))
        return {"message": "Đã xóa mã giảm giá thành công."}
