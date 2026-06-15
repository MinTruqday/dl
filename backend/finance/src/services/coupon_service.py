import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from core.database import db_client
from core.schemas.user import RoleEnum
from fastapi import HTTPException
from loguru import logger
from src.schemas.wallet_schema import CouponStatus, CouponTargetType
from uuid6 import uuid7


class CouponService:

    @staticmethod
    async def create_coupon(data: dict, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        status = (
            CouponStatus.APPROVED
            if current_user.role == RoleEnum.ADMIN
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
            "status": status,
            "expires_at": (
                datetime.fromisoformat(data["expires_at"])
                if data.get("expires_at")
                else None
            ),
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
        existing = await db["coupons"].find_one({"code": coupon["code"]})
        if existing:
            raise HTTPException(status_code=400, detail="The provided promotional code is already registered within the active campaigns")
        await db["coupons"].insert_one(coupon)
        logger.info(
            "A new promotional coupon has been successfully configured and activated within the system"
        )
        return {
            "message": "The promotional coupon has been successfully generated and recorded",
            "coupon_id": coupon["_id"],
        }

    @staticmethod
    async def get_coupons(current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        query = {}
        if current_user.role != RoleEnum.ADMIN:
            query["creator_id"] = str(current_user.id)
        coupons = (
            await db["coupons"].find(query).sort("created_at", -1).to_list(length=100)
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
            db = db_client.mongodb.get_default_database()
        if current_user.role != RoleEnum.ADMIN:
            raise HTTPException(
                status_code=403, detail="The current account lacks the necessary administrative privileges to perform this restricted action"
            )
        status = CouponStatus.APPROVED if action == "approve" else CouponStatus.REJECTED
        res = await db["coupons"].update_one(
            {"_id": coupon_id}, {"$set": {"status": status}}
        )
        if res.modified_count == 0:
            raise HTTPException(status_code=404, detail="The specified promotional coupon could not be located in the active database records")
        logger.info(
            "The designated promotional coupon has been successfully updated following administrative review"
        )
        return {
            "message": "The administrative action has been successfully applied to the specified promotional coupon"
        }

    @staticmethod
    async def validate_coupon(
        code: str, user: Any, document_id: Optional[str] = None, db=None
    ) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        coupon = await db["coupons"].find_one(
            {"code": code.upper(), "is_active": True, "status": CouponStatus.APPROVED}
        )
        if not coupon:
            raise HTTPException(
                status_code=404, detail="The submitted promotional code is either invalid or currently awaiting administrative approval"
            )
        if coupon.get("expires_at") and coupon["expires_at"].replace(
            tzinfo=timezone.utc
        ) < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="The submitted promotional code has exceeded its designated expiration period and is no longer valid")
        if coupon.get("used_count", 0) >= coupon.get("max_uses", 0):
            raise HTTPException(
                status_code=400, detail="The submitted promotional code has reached its maximum allowed redemption limit"
            )
        if coupon.get("document_id") and coupon["document_id"] != document_id:
            raise HTTPException(
                status_code=400, detail="The submitted promotional code is not applicable to the currently selected digital document"
            )
        target = coupon.get("target_type", CouponTargetType.ALL)
        if target == CouponTargetType.NEW_USER:
            purchase_count = await db["purchases"].count_documents(
                {"user_id": str(user.id)}
            )
            if purchase_count > 0:
                raise HTTPException(
                    status_code=400, detail="The specified promotional code is exclusively reserved for first time purchasers"
                )
        return {
            "code": coupon["code"],
            "discount_percent": coupon["discount_percent"],
            "target_type": target,
        }

    @staticmethod
    async def toggle_coupon_status(coupon_id: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        query = {"_id": coupon_id}
        if current_user.role != RoleEnum.ADMIN:
            query["creator_id"] = str(current_user.id)
        coupon = await db["coupons"].find_one(query)
        if not coupon:
            raise HTTPException(status_code=404, detail="The specified promotional coupon could not be located in the active database records")
        new_status = not coupon.get("is_active", True)
        await db["coupons"].update_one(
            {"_id": coupon_id}, {"$set": {"is_active": new_status}}
        )
        logger.info("The operational status of the designated promotional coupon has been successfully toggled")
        return {
            "message": "The operational status of the specified promotional coupon has been successfully updated",
            "is_active": new_status,
        }

    @staticmethod
    async def delete_coupon(coupon_id: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        query = {"_id": coupon_id}
        if current_user.role != RoleEnum.ADMIN:
            query["creator_id"] = str(current_user.id)
        res = await db["coupons"].delete_one(query)
        if res.deleted_count == 0:
            raise HTTPException(status_code=404, detail="The specified promotional coupon could not be located in the active database records")
        logger.info("The designated promotional coupon has been successfully and permanently removed from the system")
        return {"message": "The specified promotional coupon has been permanently removed from the active system records"}