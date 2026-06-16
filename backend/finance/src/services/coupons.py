from datetime import datetime, timezone
from typing import Any, Optional
from core.database import db_client
from fastapi import HTTPException
from loguru import logger
from src.schemas.finance import CouponStatus, CouponTargetType
from uuid6 import uuid7

class CouponService:

    @staticmethod
    async def create_coupon(data: dict, current_user: Any, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        status = CouponStatus.APPROVED if (current_user and current_user.get("role") == "admin") else CouponStatus.PENDING
        
        coupon = {
            "_id": str(uuid7()),
            "creator_id": str(current_user.get("id")) if current_user else "admin",
            "code": data["code"].upper(),
            "discount_percent": min(100, max(1, data.get("discount_percent", 10))),
            "max_uses": data.get("max_uses", 100),
            "used_count": 0,
            "document_id": data.get("document_id"),
            "target_type": data.get("target_type", CouponTargetType.ALL),
            "status": status,
            "expires_at": datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
        
        existing = await target_db["coupons"].find_one({"code": coupon["code"]})
        if existing:
            raise HTTPException(status_code=400, detail="Provided promotional code is already registered within active database campaigns")
            
        await target_db["coupons"].insert_one(coupon)
        logger.info("New promotional coupon successfully configured and activated within marketing system")
        return {"message": "Promotional coupon has been successfully generated and recorded", "coupon_id": coupon["_id"]}

    @staticmethod
    async def get_coupons(current_user: Any, db=None) -> list:
        target_db = db or db_client.mongodb.get_default_database()
        query = {}
        if current_user and current_user.get("role") != "admin":
            query["creator_id"] = str(current_user.get("id"))
            
        coupons = await target_db["coupons"].find(query).sort("created_at", -1).to_list(length=100)
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
                "expires_at": c["expires_at"].isoformat() if isinstance(c.get("expires_at"), datetime) else c.get("expires_at"),
            }
            for c in coupons
        ]

    @staticmethod
    async def approve_coupon(coupon_id: str, action: str, current_user: Any, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        if not current_user or current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Current account lacks necessary administrative privileges to perform restricted action")
            
        status = CouponStatus.APPROVED if action == "approve" else CouponStatus.REJECTED
        res = await target_db["coupons"].update_one({"_id": coupon_id}, {"$set": {"status": status}})
        
        if res.modified_count == 0:
            raise HTTPException(status_code=404, detail="Specified promotional coupon could not be located in active database records")
            
        logger.info("Designated promotional coupon successfully updated following strict administrative review")
        return {"message": "Administrative action successfully applied to specified promotional coupon records"}

    @staticmethod
    async def validate_coupon(code: str, user: Any, document_id: Optional[str] = None, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        coupon = await target_db["coupons"].find_one({"code": code.upper(), "is_active": True, "status": CouponStatus.APPROVED})
        
        if not coupon:
            raise HTTPException(status_code=404, detail="Submitted promotional code is invalid or currently awaiting administrative approval")
            
        if coupon.get("expires_at") and coupon["expires_at"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Submitted promotional code exceeded designated expiration period and is invalid")
            
        if coupon.get("used_count", 0) >= coupon.get("max_uses", 0):
            raise HTTPException(status_code=400, detail="Submitted promotional code reached maximum allowed system redemption limit")
            
        if coupon.get("document_id") and coupon["document_id"] != document_id:
            raise HTTPException(status_code=400, detail="Submitted promotional code is not applicable to currently selected digital document")
            
        target = coupon.get("target_type", CouponTargetType.ALL)
        if target == CouponTargetType.NEW_USER:
            purchase_count = await target_db["purchases"].count_documents({"user_id": str(user.id)})
            if purchase_count > 0:
                raise HTTPException(status_code=400, detail="Specified promotional code is exclusively reserved for first time purchasers")
                
        return {"code": coupon["code"], "discount_percent": coupon["discount_percent"], "target_type": target}

    @staticmethod
    async def toggle_coupon_status(coupon_id: str, current_user: Any, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        query = {"_id": coupon_id}
        if not current_user or current_user.get("role") != "admin":
            query["creator_id"] = str(current_user.get("id"))
            
        coupon = await target_db["coupons"].find_one(query)
        if not coupon:
            raise HTTPException(status_code=404, detail="Specified promotional coupon could not be located in active database records")
            
        new_status = not coupon.get("is_active", True)
        await target_db["coupons"].update_one({"_id": coupon_id}, {"$set": {"is_active": new_status}})
        logger.info("Operational status of designated promotional coupon successfully toggled by administrator")
        return {"message": "Operational status of specified promotional coupon successfully updated in system", "is_active": new_status}

    @staticmethod
    async def delete_coupon(coupon_id: str, current_user: Any, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        query = {"_id": coupon_id}
        if not current_user or current_user.get("role") != "admin":
            query["creator_id"] = str(current_user.get("id"))
            
        res = await target_db["coupons"].delete_one(query)
        if res.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Specified promotional coupon could not be located in active database records")
            
        logger.info("Designated promotional coupon successfully and permanently removed from active system")
        return {"message": "Specified promotional coupon permanently removed from active system records"}