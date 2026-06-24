from src.core.api_client import db_client
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException
from loguru import logger
from src.schemas.wallet import CouponStatus, CouponTargetType
from uuid6 import uuid7

from src.core.infrastructure.database import database
from src.core.dependency import CurrentUser, Role


class CouponService:

    @staticmethod
    async def create_coupon(data: dict, current_user, db=None) -> dict:
        if db is None:
            db = database.mongodb.get_default_database()
        status = (
            CouponStatus.APPROVED
            if current_user.role == Role.ADMIN
            else CouponStatus.PENDING
        )
        coupon = {
            "_id": str(uuid7()),
            "creator_id": str(current_user.id),
            "code": data["code"].upper(),
            "discount_percent": min(100, max(1, data.get("discount_percent", 10))),
            "max_uses": data.get("max_uses", 100),
            "used_count": 0,
            "document_id": data.get("document_id"),
            "target_type": data.get("target_type", CouponTargetType.ALL),
            "amount_dl": data.get("amount_dl", 0),
            "status": status,
            "expires_at": (
                datetime.fromisoformat(data["expires_at"]) if isinstance(data.get("expires_at"), str)
                else data.get("expires_at")
            ),
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
        existing = await db_client.find_one(collection="coupons", query={"code": coupon["code"]})
        if existing:
            raise HTTPException(status_code=400, detail="Mã giảm giá đã được sử dụng")
        await db_client.insert_one(collection="coupons", document=coupon)
        logger.info("Tạo mã giảm giá thành công")
        return {
            "message": "Tạo mã giảm giá thành công",
            "coupon_id": coupon["_id"],
        }

    @staticmethod
    async def get_coupons(current_user, db=None) -> list:
        if db is None:
            db = database.mongodb.get_default_database()
        query = {}
        if current_user.role != Role.ADMIN:
            query["creator_id"] = str(current_user.id)
        coupons = (
            await db_client.find(collection="coupons", query=query, sort=[("created_at", -1)], limit=100)
        )
        return [
            {
                "_id": c["_id"],
                "code": c.get("code", ""),
                "discount_percent": c.get("discount_percent", 0),
                "max_uses": c.get("max_uses", 0),
                "used_count": c.get("used_count", 0),
                "document_id": c.get("document_id"),
                "target_type": c.get("target_type", CouponTargetType.ALL),
                "status": c.get("status", CouponStatus.APPROVED),
                "is_active": c.get("is_active", True),
                "expires_at": (
                    c["expires_at"].isoformat()
                    if isinstance(c.get("expires_at"), datetime)
                    else c.get("expires_at")
                ),
            }
            for c in coupons
        ]

    @staticmethod
    async def approve_coupon(
        coupon_id: str, action: str, current_user, db=None
    ) -> dict:
        if db is None:
            db = database.mongodb.get_default_database()
        if current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=403, detail="Không có quyền thực hiện thao tác này"
            )
        status = CouponStatus.APPROVED if action == "approve" else CouponStatus.REJECTED
        res = await db["coupons"].update_one(
            {"_id": coupon_id}, {"$set": {"status": status}}
        )
        if res.modified_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy mã giảm giá")
        logger.info("Cập nhật mã giảm giá thành công")
        return {"message": "Áp dụng thao tác lên mã giảm giá thành công"}

    @staticmethod
    async def validate_coupon(
        code: str, user: Any, document_id: Optional[str] = None, db=None
    ) -> dict:
        if db is None:
            db = database.mongodb.get_default_database()
        coupon = await db["coupons"].find_one(
            {"code": code.upper(), "is_active": True, "status": CouponStatus.APPROVED}
        )
        if not coupon:
            raise HTTPException(
                status_code=404, detail="Mã giảm giá không hợp lệ hoặc đang chờ duyệt"
            )
        if coupon.get("expires_at") and coupon["expires_at"].replace(
            tzinfo=timezone.utc
        ) < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Mã giảm giá đã hết hạn")
        if coupon.get("used_count", 0) >= coupon.get("max_uses", 0):
            raise HTTPException(
                status_code=400, detail="Mã giảm giá đã đạt giới hạn sử dụng tối đa"
            )
        if coupon.get("document_id") and coupon["document_id"] != document_id:
            raise HTTPException(
                status_code=400, detail="Mã giảm giá không áp dụng cho tài liệu này"
            )
        target = coupon.get("target_type", CouponTargetType.ALL)
        if target == CouponTargetType.NEW_USER:
            purchase_count = await db["purchases"].count_documents(
                {"user_id": str(user.id)}
            )
            if purchase_count > 0:
                raise HTTPException(
                    status_code=400,
                    detail="Mã giảm giá này chỉ dành cho người mua lần đầu",
                )
        return {
            "code": coupon["code"],
            "discount_percent": coupon["discount_percent"],
            "target_type": target,
        }

    @staticmethod
    async def toggle_coupon_status(coupon_id: str, current_user, db=None) -> dict:
        if db is None:
            db = database.mongodb.get_default_database()
        query = {"_id": coupon_id}
        if current_user.role != Role.ADMIN:
            query["creator_id"] = str(current_user.id)
        coupon = await db_client.find_one(collection="coupons", query=query)
        if not coupon:
            raise HTTPException(status_code=404, detail="Không tìm thấy mã giảm giá")
        new_status = not coupon.get("is_active", True)
        await db["coupons"].update_one(
            {"_id": coupon_id}, {"$set": {"is_active": new_status}}
        )
        logger.info("Cập nhật trạng thái mã giảm giá thành công")
        return {
            "message": "Cập nhật trạng thái mã giảm giá thành công",
            "is_active": new_status,
        }

    @staticmethod
    async def delete_coupon(coupon_id: str, current_user, db=None) -> dict:
        if db is None:
            db = database.mongodb.get_default_database()
        query = {"_id": coupon_id}
        if current_user.role != Role.ADMIN:
            query["creator_id"] = str(current_user.id)
        res = await db_client.delete_one(collection="coupons", filter=query)
        if res.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy mã giảm giá")
        logger.info("Xóa vĩnh viễn mã giảm giá thành công")
        return {"message": "Xóa vĩnh viễn mã giảm giá thành công"}
