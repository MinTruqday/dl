from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.database import db_client


class WalletRepository:
    @staticmethod
    async def get_wallet_by_user_id(user_id: str, db=None) -> Optional[Dict[str, Any]]:
        if db is None:
            db = db_client.mongodb.get_default_database()
        return await db["wallets"].find_one({"_id": user_id})

    @staticmethod
    async def increment_balance(user_id: str, amount: int, db=None, session=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        return await db["wallets"].update_one(
            {"_id": user_id},
            {"$inc": {"balance": amount}},
            upsert=True,
            session=session,
        )

    @staticmethod
    async def get_coupon_by_code(
        code: str, db=None, session=None
    ) -> Optional[Dict[str, Any]]:
        if db is None:
            db = db_client.mongodb.get_default_database()
        return await db["coupons"].find_one({"code": code}, session=session)

    @staticmethod
    async def mark_coupon_as_used(coupon_id: Any, user_id: str, db=None, session=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        return await db["coupons"].update_one(
            {"_id": coupon_id, "is_used": False},
            {
                "$set": {
                    "is_used": True,
                    "used_by": user_id,
                    "used_at": datetime.now(timezone.utc),
                }
            },
            session=session,
        )

    @staticmethod
    async def insert_transaction(tx_data: dict, db=None, session=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        return await db["transactions"].insert_one(tx_data, session=session)

    @staticmethod
    async def get_transactions(
        query: dict, skip: int = 0, limit: int = 30, db=None
    ) -> List[Dict[str, Any]]:
        if db is None:
            db = db_client.mongodb.get_default_database()
        tx_cursor = db["transactions"].find(query).sort("created_at", -1)
        if skip > 0:
            tx_cursor = tx_cursor.skip(skip)
        tx_cursor = tx_cursor.limit(limit)
        return await tx_cursor.to_list(length=limit)
