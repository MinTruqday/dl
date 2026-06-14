import uuid
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from core.database import db_client
from fastapi import HTTPException
from loguru import logger
from src.schemas.wallet_schema import Transaction, TransactionType
from uuid6 import uuid7


class PurchaseService:

    @staticmethod
    async def buy_ai_tier(tier: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()

        tier = tier.upper()
        if tier not in ["PRO", "PREMIUM"]:
            raise HTTPException(
                status_code=400,
                detail="The selected membership plan is not recognized. Please choose a valid tier.",
            )

        price = 750 if tier == "PRO" else 2500

        if current_user.ai_tier and current_user.ai_tier.value == tier:
            raise HTTPException(
                status_code=400,
                detail=f"Your account already has an active {tier} membership plan.",
            )

        wallet = await db["wallets"].find_one({"_id": str(current_user.id)})
        if not wallet or wallet.get("balance", 0) < price:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient balance. This membership plan requires {price} dl.",
            )

        session = await db_client.mongodb.start_session()
        session.start_transaction()
        try:
            deduct_result = await db["wallets"].update_one(
                {"_id": str(current_user.id), "balance": {"$gte": price}},
                {"$inc": {"balance": -price}},
                session=session,
            )
            if deduct_result.modified_count == 0:
                await session.abort_transaction()
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient balance. This membership plan requires {price} dl.",
                )

            await db["users"].update_one(
                {"_id": str(current_user.id)},
                {"$set": {"ai_tier": tier}},
                session=session,
            )

            tx = Transaction(
                user_id=str(current_user.id),
                type=TransactionType.PURCHASE,
                amount=-price,
                note=f"Membership upgrade to {tier} plan",
            )
            await db["transactions"].insert_one(
                tx.model_dump(by_alias=True), session=session
            )

            await session.commit_transaction()
            logger.info(f"User {current_user.id} upgraded membership to {tier} tier")
            return {
                "tier": tier,
                "status": "active",
            }
        except HTTPException:
            raise
        except Exception:
            await session.abort_transaction()
            logger.error(f"Membership upgrade failed for user {current_user.id}")
            raise HTTPException(
                status_code=500,
                detail="The membership upgrade could not be completed. Please try again later.",
            )
        finally:
            await session.end_session()

    @staticmethod
    async def purchase_document(
        document_id: str, current_user, db=None, session=None
    ) -> dict:
        should_close_session = False
        if db is None:
            db = db_client.mongodb.get_default_database()

        if session is None:
            session = await db_client.mongodb.start_session()
            session.start_transaction()
            should_close_session = True

        doc = await db["documents"].find_one({"_id": document_id})
        if not doc:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(status_code=404, detail="The requested digital document could not be located in the primary storage repository")
        price = doc.get("price_dl", doc.get("price_dls", 0))
        if price <= 0:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            return {"message": "The specified digital document is currently freely accessible and does not require a financial purchase", "status": "free"}
        wallet = await db["wallets"].find_one({"_id": str(current_user.id)})
        if not wallet or wallet.get("balance", 0) < price:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=400, detail="The transaction cannot proceed due to insufficient funds available in the digital wallet"
            )
        lock = None
        if hasattr(db_client, "redis") and db_client.redis:
            lock = db_client.redis.lock(
                f"purchase:{current_user.id}:{document_id}",
                timeout=settings.DEFAULT_HTTP_TIMEOUT,
            )
            await lock.acquire()
        try:
            existing = await db["purchases"].find_one(
                {
                    "user_id": str(current_user.id),
                    "document_id": document_id,
                    "item_type": "document",
                }
            )
            if existing:
                if should_close_session:
                    await session.abort_transaction()
                return {"message": "The specified digital document has already been purchased and is accessible in your library", "status": "owned"}
            author_id = doc.get("author_id")

            try:
                deduct_result = await db["wallets"].update_one(
                    {"_id": str(current_user.id), "balance": {"$gte": price}},
                    {"$inc": {"balance": -price}},
                    session=session,
                )
                if deduct_result.modified_count == 0:
                    if should_close_session:
                        await session.abort_transaction()
                    raise HTTPException(
                        status_code=400, detail="The transaction cannot proceed due to insufficient funds available in the digital wallet"
                    )
                if author_id:
                    await db["wallets"].update_one(
                        {"_id": author_id},
                        {"$inc": {"balance": price}},
                        upsert=True,
                        session=session,
                    )
                await db["purchases"].insert_one(
                    {
                        "_id": str(uuid7()),
                        "user_id": str(current_user.id),
                        "document_id": document_id,
                        "item_type": "document",
                        "price": price,
                        "purchased_at": datetime.now(timezone.utc),
                    },
                    session=session,
                )
                tx_buyer = Transaction(
                    user_id=str(current_user.id),
                    type=TransactionType.WITHDRAW,
                    amount=-price,
                    note="Payment processed for digital document acquisition",
                )
                tx_seller = Transaction(
                    user_id=author_id,
                    type=TransactionType.RECEIVE,
                    amount=price,
                    note="Revenue earned from the sale of a published digital document",
                )
                await db["transactions"].insert_one(
                    tx_buyer.model_dump(by_alias=True), session=session
                )
                await db["transactions"].insert_one(
                    tx_seller.model_dump(by_alias=True), session=session
                )

                if should_close_session:
                    await session.commit_transaction()

                if author_id:
                    notif_id = str(uuid7())
                    notification = {
                        "_id": notif_id,
                        "target_user_id": author_id,
                        "title": "New transaction recorded",
                        "body": "A user has successfully purchased your published document",
                        "is_read": False,
                        "type": "purchase",
                        "created_at": datetime.now(timezone.utc),
                    }
                    await db["notifications"].insert_one(notification, session=session)
                    if hasattr(db_client, "redis") and db_client.redis:
                        try:
                            import httpx
                            from core.config import settings

                            if settings.SIGNAL_URL:
                                async with httpx.AsyncClient() as client:
                                    await client.post(
                                        f"{settings.SIGNAL_URL}/thong-bao/kich-hoat",
                                        json={
                                            "target_user_id": author_id,
                                            "title": notification["title"],
                                            "body": notification["body"],
                                            "type": "purchase",
                                        },
                                        timeout=settings.DEFAULT_HTTP_TIMEOUT,
                                    )
                        except Exception:
                            logger.error("The system encountered a minor disruption while attempting to dispatch the transaction success notification")
                logger.info(
                    "The digital document purchase transaction has been successfully processed and recorded"
                )
                return {
                    "message": "The digital document purchase transaction has been completed successfully and access has been granted",
                    "status": "purchased",
                }
            except HTTPException:
                raise
            except Exception:
                if should_close_session:
                    await session.abort_transaction()
                logger.error("An unexpected disruption occurred while attempting to process the financial transactions for the document purchase")
                raise HTTPException(status_code=500, detail="The requested financial transaction encountered an internal failure and could not be processed")
            finally:
                if should_close_session:
                    await session.end_session()
        finally:
            if (
                hasattr(db_client, "redis")
                and db_client.redis
                and lock
                and lock.locked()
            ):
                try:
                    await lock.release()
                except Exception:
                    pass

    @staticmethod
    async def cancel_purchase(
        purchase_id: str, current_user, db=None, session=None
    ) -> dict:
        should_close_session = False
        if db is None:
            db = db_client.mongodb.get_default_database()

        if session is None:
            session = await db_client.mongodb.start_session()
            session.start_transaction()
            should_close_session = True

        purchase = await db["purchases"].find_one(
            {"_id": purchase_id, "user_id": str(current_user.id)}
        )
        if not purchase:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(status_code=404, detail="The specified purchase transaction record could not be located within the system")
        purchased_at = purchase.get("purchased_at", datetime.now(timezone.utc))
        if isinstance(purchased_at, str):
            purchased_at = datetime.fromisoformat(purchased_at)
        if datetime.now(timezone.utc) - purchased_at > timedelta(hours=48):
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=400, detail="The refund request was rejected because it falls outside the permissible forty eight hour window"
            )
        price = purchase.get("price", 0)
        doc_id = purchase.get("document_id")
        doc = await db["documents"].find_one({"_id": doc_id}) if doc_id else None
        author_id = doc.get("author_id") if doc else None

        try:
            await db["wallets"].update_one(
                {"_id": str(current_user.id)},
                {"$inc": {"balance": price}},
                upsert=True,
                session=session,
            )
            if author_id:
                deduct_result = await db["wallets"].update_one(
                    {"_id": author_id, "balance": {"$gte": price}},
                    {"$inc": {"balance": -price}},
                    session=session,
                )
                if deduct_result.modified_count == 0:
                    if should_close_session:
                        await session.abort_transaction()
                    raise HTTPException(
                        status_code=400,
                        detail="The refund cannot be processed because the author account currently has insufficient funds to reverse the transaction",
                    )

            await db["purchases"].update_one(
                {"_id": purchase_id},
                {
                    "$set": {
                        "status": "CANCELLED",
                        "cancelled_at": datetime.now(timezone.utc),
                    }
                },
                session=session,
            )
            tx_refund_buyer = Transaction(
                user_id=str(current_user.id),
                type=TransactionType.REFUND,
                amount=price,
                note="Refund issued for previously cancelled purchase transaction",
            )
            tx_refund_seller = Transaction(
                user_id=author_id,
                type=TransactionType.REFUND,
                amount=-price,
                note="Funds deducted for previously cancelled purchase transaction refund",
            )
            await db["transactions"].insert_one(
                tx_refund_buyer.model_dump(by_alias=True), session=session
            )
            await db["transactions"].insert_one(
                tx_refund_seller.model_dump(by_alias=True), session=session
            )

            if should_close_session:
                await session.commit_transaction()
            return {"message": "The refund request has been successfully processed and the funds have been restored", "refunded_amount": price}
        except HTTPException:
            raise
        except Exception:
            if should_close_session:
                await session.abort_transaction()
            logger.error("An unexpected error occurred while attempting to process the refund request and adjust the associated balances")
            raise HTTPException(status_code=500, detail="The system encountered an internal failure while attempting to process the refund transaction")
        finally:
            if should_close_session:
                await session.end_session()