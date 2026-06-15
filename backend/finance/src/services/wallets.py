import json
import httpx
from datetime import datetime, timezone
from core.config import settings
from core.database import db_client
from fastapi import HTTPException, status, Query
from loguru import logger
from src.schemas.finance import Transaction, TransactionType
from src.repositories.wallets import WalletRepository

class WalletService:

    @staticmethod
    async def get_balance(current_user, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        wallet = await target_db["wallets"].find_one({"_id": str(current_user.id)})
        return {"balance": wallet.get("balance", 0) if wallet else 0}

    @staticmethod
    async def redeem_coupon(req, current_user, db=None, session=None) -> dict:
        should_close_session = False
        lock_key = f"lock:coupon:{req.code}"
        is_locked = False

        if db_client.redis:
            user_rl_key = f"rl:coupon:{current_user.id}"
            try:
                attempts = await db_client.redis.incr(user_rl_key)
                if attempts == 1:
                    await db_client.redis.expire(user_rl_key, 300)
                if attempts > 10:
                    raise HTTPException(status_code=429, detail="System temporarily restricted access due to excessive attempts so please wait five minutes")
            except HTTPException:
                raise
            except Exception:
                logger.error("System encountered caching access error while attempting to verify transaction rate limits")

        if db_client.redis:
            try:
                is_locked = await db_client.redis.set(lock_key, "locked", nx=True, ex=10)
                if not is_locked:
                    raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Coupon redemption process is currently actively being handled by another concurrent transaction")
            except HTTPException:
                raise
            except Exception:
                logger.error("System failed to acquire secure session lock within distributed caching layer")
                raise HTTPException(status_code=500, detail="System encountered internal caching connectivity issue and could not proceed with transaction")

        target_db = db or db_client.mongodb.get_default_database()

        if session is None:
            session = await db_client.mongodb.start_session()
            session.start_transaction()
            should_close_session = True

        try:
            coupon = await target_db["coupons"].find_one({"code": req.code}, session=session)
            if not coupon:
                if should_close_session:
                    await session.abort_transaction()
                raise HTTPException(status_code=404, detail="Provided promotional code is invalid or does not exist within current campaign records")
                
            if coupon.get("is_used"):
                if should_close_session:
                    await session.abort_transaction()
                raise HTTPException(status_code=400, detail="Submitted promotional code has already been successfully redeemed and cannot be reused")

            bonus_dl = coupon.get("amount_dl", coupon.get("amount_dls", 0))
            result = await target_db["coupons"].update_one(
                {"_id": coupon["_id"]},
                {"$set": {"is_used": True, "used_by": str(current_user.id), "used_at": datetime.now(timezone.utc)}},
                session=session
            )
            
            if result.modified_count == 0:
                if should_close_session:
                    await session.abort_transaction()
                raise HTTPException(status_code=400, detail="Submitted promotional code reached maximum redemption capacity or was claimed by another account")

            await target_db["wallets"].update_one(
                {"_id": str(current_user.id)}, {"$inc": {"balance": bonus_dl}}, upsert=True, session=session
            )
            
            tx = Transaction(
                user_id=str(current_user.id),
                type=TransactionType.TOPUP,
                amount=bonus_dl,
                note="Promotional coupon successfully redeemed and credited to digital wallet",
            )
            await target_db["transactions"].insert_one(tx.model_dump(by_alias=True), session=session)

            if should_close_session:
                await session.commit_transaction()

            try:
                if settings.SIGNAL_URL:
                    async with httpx.AsyncClient() as client:
                        await client.post(
                            f"{settings.SIGNAL_URL}/notifications/dispatch",
                            json={
                                "target_user_id": str(current_user.id),
                                "title": "Deposit transaction completed",
                                "body": "Digital wallet successfully credited with requested promotional bonus balance",
                                "type": "topup",
                            },
                            timeout=settings.DEFAULT_HTTP_TIMEOUT,
                        )
            except Exception:
                logger.warning("System encountered minor network disruption attempting to dispatch coupon redemption success notification")
                
            logger.info("Authenticated user successfully redeemed promotional code for allocated digital balance")
            return {
                "message": "Promotional coupon successfully redeemed and bonus balance has been credited",
                "bonus_dl": bonus_dl,
                "status": "success",
            }
        except HTTPException:
            raise
        except Exception:
            if should_close_session:
                await session.abort_transaction()
            logger.error("System encountered unexpected structural error during coupon redemption processing sequence")
            raise HTTPException(status_code=500, detail="Financial service is undergoing routine maintenance so please attempt your transaction again later")
        finally:
            if should_close_session:
                await session.end_session()
            if db_client.redis and is_locked:
                try:
                    await db_client.redis.delete(lock_key)
                except Exception:
                    logger.error("System encountered minor issue while releasing secure session lock in cache")

    @staticmethod
    async def get_history(current_user, cursor: str = None, limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), tx_type: str = None, skip: int = 0, db=None) -> list:
        target_db = db or db_client.mongodb.get_default_database()
        query = {"user_id": str(current_user.id)}
        if tx_type:
            query["type"] = tx_type.lower()
            
        if cursor:
            try:
                query["created_at"] = {"$lt": datetime.fromisoformat(cursor.replace("Z", "+00:00"))}
            except Exception:
                logger.warning("Pagination process interrupted because provided cursor value was incorrectly formatted")
                
        txs = await target_db["transactions"].find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
        type_translations = {
            "topup": "Deposit",
            "purchase": "Document Purchase",
            "receive": "Funds Received",
            "withdraw": "Withdrawal",
            "tip": "Author Tip",
            "refund": "Refund",
        }
        for tx in txs:
            tx["_id"] = str(tx["_id"])
            if isinstance(tx.get("created_at"), datetime):
                tx["created_at"] = tx["created_at"].isoformat()
            raw_type = tx.get("type", "")
            tx["type"] = raw_type.upper()
            tx["type_display"] = type_translations.get(raw_type, "Transaction")
            tx["description"] = tx.get("note", "")
            tx["status"] = "COMPLETED"
        return txs