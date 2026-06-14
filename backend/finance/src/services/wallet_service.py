from core.config import settings
import json
from datetime import datetime, timezone

from core.database import db_client
from fastapi import HTTPException, status, Query
from loguru import logger
from src.schemas.wallet_schema import Transaction, TransactionType


class WalletService:

    @staticmethod
    async def get_balance(current_user, db=None):
        from src.repositories.wallet_repository import WalletRepository

        wallet = await WalletRepository.get_wallet_by_user_id(
            str(current_user.id), db=db
        )
        return {"balance": wallet.get("balance", 0) if wallet else 0}

    @staticmethod
    async def redeem_coupon(req, current_user, db=None, session=None):
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
                    raise HTTPException(
                        status_code=429,
                        detail="Too many attempts. Please try again after 5 minutes",
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Cache rate limit access error")

        if db_client.redis:
            try:
                is_locked = await db_client.redis.set(
                    lock_key, "locked", nx=True, ex=10
                )
                if not is_locked:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Coupon redemption is currently in progress",
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Cache session locking error")
                raise HTTPException(status_code=500, detail="Cache connection error")

        if db is None:
            db = db_client.mongodb.get_default_database()

        if session is None:
            session = await db_client.mongodb.start_session()
            session.start_transaction()
            should_close_session = True

        from src.repositories.wallet_repository import WalletRepository

        try:
            coupon = await WalletRepository.get_coupon_by_code(
                req.code, db=db, session=session
            )
            if not coupon:
                if should_close_session:
                    await session.abort_transaction()
                raise HTTPException(
                    status_code=404, detail="Invalid or non-existent coupon code"
                )
            if coupon.get("is_used"):
                if should_close_session:
                    await session.abort_transaction()
                raise HTTPException(status_code=400, detail="Coupon code has already been redeemed")

            bonus_dl = coupon.get("amount_dl", coupon.get("amount_dls", 0))
            result = await WalletRepository.mark_coupon_as_used(
                coupon["_id"], str(current_user.id), db=db, session=session
            )
            if result.modified_count == 0:
                if should_close_session:
                    await session.abort_transaction()
                raise HTTPException(
                    status_code=400, detail="Coupon code has already been redeemed by another user"
                )

            await WalletRepository.increment_balance(
                str(current_user.id), bonus_dl, db=db, session=session
            )
            tx = Transaction(
                user_id=str(current_user.id),
                type=TransactionType.TOPUP,
                amount=bonus_dl,
                note=f"Coupon redeemed: {req.code}",
            )
            await WalletRepository.insert_transaction(
                tx.model_dump(by_alias=True), db=db, session=session
            )

            if should_close_session:
                await session.commit_transaction()

            try:
                import httpx
                from core.config import settings

                if settings.SIGNAL_URL:
                    async with httpx.AsyncClient() as client:
                        await client.post(
                            f"{settings.SIGNAL_URL}/thong-bao/kich-hoat",
                            json={
                                "target_user_id": str(current_user.id),
                                "title": "Deposit Successful",
                                "body": f"Your account has been credited with {bonus_dl} dl",
                                "type": "topup",
                            },
                            timeout=settings.DEFAULT_HTTP_TIMEOUT,
                        )
            except Exception as e:
                logger.warning("Failed to send notification")
            logger.info(
                f"User {current_user.id} redeemed coupon {req.code} for {bonus_dl} dl"
            )
            return {
                "message": "Coupon redeemed successfully",
                "bonus_dl": bonus_dl,
                "status": "success",
            }
        except HTTPException:
            raise
        except Exception as e:
            if should_close_session:
                await session.abort_transaction()
            logger.exception("Coupon redemption error")
            raise HTTPException(status_code=500, detail="System under maintenance. Please try again later")
        finally:
            if should_close_session:
                await session.end_session()
            if db_client.redis and is_locked:
                try:
                    await db_client.redis.delete(lock_key)
                except Exception as e:
                    logger.error("Cache session unlock error")

    @staticmethod
    async def get_history(
        current_user,
        cursor: str = None,
        limit: int = Query(
            default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT
        ),
        tx_type: str = None,
        skip: int = 0,
        db=None,
    ):
        from src.repositories.wallet_repository import WalletRepository

        query = {"user_id": str(current_user.id)}
        if tx_type:
            query["type"] = tx_type.lower()
        if cursor:
            try:
                query["created_at"] = {
                    "$lt": datetime.fromisoformat(cursor.replace("Z", "+00:00"))
                }
            except Exception as e:
                logger.warning("Invalid pagination cursor format")
        txs = await WalletRepository.get_transactions(
            query, skip=skip, limit=limit, db=db
        )
        type_translations = {
            "topup": "Deposit",
            "purchase": "Document Purchase",
            "receive": "Funds Received",
            "withdraw": "Withdrawal",
            "tip": "Author Tip",
            "subscription": "Plan Subscription",
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
