import httpx
from datetime import datetime, timedelta, timezone
from core.config import settings
from core.database import db_client
from fastapi import HTTPException
from loguru import logger
from src.schemas.finance import Transaction, TransactionType
from uuid6 import uuid7

class PurchaseService:

    @staticmethod
    async def buy_ai_tier(tier: str, current_user, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        tier = tier.upper()
        if tier not in ["PRO", "PREMIUM"]:
            raise HTTPException(status_code=400, detail="Selected membership plan is not recognized so please choose valid tier")

        price = 750 if tier == "PRO" else 2500

        if current_user.ai_tier and current_user.ai_tier.value == tier:
            raise HTTPException(status_code=400, detail="Account already has active plan matching selected membership subscription tier")

        wallet = await target_db["wallets"].find_one({"_id": str(current_user.get("id"))})
        if not wallet or wallet.get("balance", 0) < price:
            raise HTTPException(status_code=400, detail="Insufficient digital balance to acquire requested membership subscription plan tier")

        session = await db_client.mongodb.start_session()
        session.start_transaction()
        try:
            deduct_result = await target_db["wallets"].update_one(
                {"_id": str(current_user.get("id")), "balance": {"$gte": price}},
                {"$inc": {"balance": -price}},
                session=session,
            )
            if deduct_result.modified_count == 0:
                await session.abort_transaction()
                raise HTTPException(status_code=400, detail="Insufficient digital balance to acquire requested membership subscription plan tier")

            await target_db["users"].update_one(
                {"_id": str(current_user.get("id"))},
                {"$set": {"ai_tier": tier}},
                session=session,
            )

            tx = Transaction(
                user_id=str(current_user.get("id")),
                type=TransactionType.PURCHASE,
                amount=-price,
                note=f"Membership upgrade to requested premium tier plan",
            )
            await target_db["transactions"].insert_one(tx.model_dump(by_alias=True), session=session)

            await session.commit_transaction()
            logger.info("Account owner successfully upgraded artificial intelligence membership subscription plan tier")
            return {"tier": tier, "status": "active"}
        except HTTPException:
            raise
        except Exception:
            await session.abort_transaction()
            logger.error("Membership upgrade sequence encountered unexpected failure preventing transaction completion")
            raise HTTPException(status_code=500, detail="Membership upgrade could not be completed at this time please try again")
        finally:
            await session.end_session()

    @staticmethod
    async def purchase_document(document_id: str, current_user, db=None, session=None) -> dict:
        should_close_session = False
        target_db = db or db_client.mongodb.get_default_database()

        if session is None:
            session = await db_client.mongodb.start_session()
            session.start_transaction()
            should_close_session = True

        doc = await target_db["documents"].find_one({"_id": document_id})
        if not doc:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(status_code=404, detail="Requested digital document could not be located in primary storage repository")
            
        price = doc.get("price_dl", doc.get("price_dls", 0))
        if price <= 0:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            return {"message": "Specified digital document is currently freely accessible without financial purchase", "status": "free"}
            
        wallet = await target_db["wallets"].find_one({"_id": str(current_user.get("id"))})
        if not wallet or wallet.get("balance", 0) < price:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(status_code=400, detail="Transaction cannot proceed due to insufficient funds available in digital wallet")
            
        lock = None
        if hasattr(db_client, "redis") and db_client.redis:
            lock = db_client.redis.lock(f"purchase:{current_user.get('id')}:{document_id}", timeout=settings.DEFAULT_HTTP_TIMEOUT)
            await lock.acquire()
            
        try:
            existing = await target_db["purchases"].find_one({"user_id": str(current_user.get("id")), "document_id": document_id, "item_type": "document"})
            if existing:
                if should_close_session:
                    await session.abort_transaction()
                return {"message": "Specified digital document has already been purchased and is accessible", "status": "owned"}
                
            creator_id = doc.get("creator_id")
            try:
                deduct_result = await target_db["wallets"].update_one(
                    {"_id": str(current_user.get("id")), "balance": {"$gte": price}},
                    {"$inc": {"balance": -price}},
                    session=session,
                )
                if deduct_result.modified_count == 0:
                    if should_close_session:
                        await session.abort_transaction()
                    raise HTTPException(status_code=400, detail="Transaction cannot proceed due to insufficient funds available in digital wallet")
                    
                if creator_id:
                    await target_db["wallets"].update_one({"_id": creator_id}, {"$inc": {"balance": price}}, upsert=True, session=session)
                    
                await target_db["purchases"].insert_one(
                    {
                        "_id": str(uuid7()),
                        "user_id": str(current_user.get("id")),
                        "document_id": document_id,
                        "item_type": "document",
                        "price": price,
                        "purchased_at": datetime.now(timezone.utc),
                    },
                    session=session,
                )
                
                tx_buyer = Transaction(
                    user_id=str(current_user.get("id")),
                    type=TransactionType.WITHDRAW,
                    amount=-price,
                    note="Payment processed for digital document acquisition",
                )
                tx_seller = Transaction(
                    user_id=creator_id,
                    type=TransactionType.RECEIVE,
                    amount=price,
                    note="Revenue earned from sale of published digital document",
                )
                await target_db["transactions"].insert_one(tx_buyer.model_dump(by_alias=True), session=session)
                await target_db["transactions"].insert_one(tx_seller.model_dump(by_alias=True), session=session)

                if should_close_session:
                    await session.commit_transaction()

                if creator_id:
                    notif_id = str(uuid7())
                    notification = {
                        "_id": notif_id,
                        "target_user_id": creator_id,
                        "title": "New transaction recorded",
                        "body": "User successfully purchased your published digital document",
                        "is_read": False,
                        "type": "purchase",
                        "created_at": datetime.now(timezone.utc),
                    }
                    await target_db["notifications"].insert_one(notification)
                    if hasattr(db_client, "redis") and db_client.redis:
                        try:
                            if settings.NOTIFICATION_URL:
                                async with httpx.AsyncClient() as client:
                                    await client.post(
                                        f"{settings.NOTIFICATION_URL}/notifications/dispatch",
                                        json={"target_user_id": creator_id, "title": notification["title"], "body": notification["body"], "type": "purchase"},
                                        timeout=settings.DEFAULT_HTTP_TIMEOUT,
                                    )
                        except Exception:
                            logger.error("System encountered minor disruption attempting to dispatch transaction success notification payload")
                            
                logger.info("Digital document purchase transaction has been successfully processed and recorded")
                return {"message": "Digital document purchase transaction completed successfully and access has been granted", "status": "purchased"}
            except HTTPException:
                raise
            except Exception:
                if should_close_session:
                    await session.abort_transaction()
                logger.error("Unexpected disruption occurred attempting to process financial transactions for document purchase")
                raise HTTPException(status_code=500, detail="Requested financial transaction encountered internal failure and could not be processed")
        finally:
            if should_close_session:
                await session.end_session()
            if hasattr(db_client, "redis") and db_client.redis and lock and lock.locked():
                try:
                    await lock.release()
                except Exception:
                    pass

    @staticmethod
    async def cancel_purchase(purchase_id: str, current_user, db=None, session=None) -> dict:
        should_close_session = False
        target_db = db or db_client.mongodb.get_default_database()

        if session is None:
            session = await db_client.mongodb.start_session()
            session.start_transaction()
            should_close_session = True

        purchase = await target_db["purchases"].find_one({"_id": purchase_id, "user_id": str(current_user.get("id"))})
        if not purchase:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(status_code=404, detail="Specified purchase transaction record could not be located within system database")
            
        purchased_at = purchase.get("purchased_at", datetime.now(timezone.utc))
        if isinstance(purchased_at, str):
            purchased_at = datetime.fromisoformat(purchased_at)
            
        if datetime.now(timezone.utc) - purchased_at > timedelta(hours=48):
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(status_code=400, detail="Refund request rejected because it falls outside permissible forty eight hour window")
            
        price = purchase.get("price", 0)
        doc_id = purchase.get("document_id")
        doc = await target_db["documents"].find_one({"_id": doc_id}) if doc_id else None
        creator_id = doc.get("creator_id") if doc else None

        try:
            await target_db["wallets"].update_one({"_id": str(current_user.get("id"))}, {"$inc": {"balance": price}}, upsert=True, session=session)
            if creator_id:
                deduct_result = await target_db["wallets"].update_one(
                    {"_id": creator_id, "balance": {"$gte": price}},
                    {"$inc": {"balance": -price}},
                    session=session,
                )
                if deduct_result.modified_count == 0:
                    if should_close_session:
                        await session.abort_transaction()
                    raise HTTPException(status_code=400, detail="Refund cannot be processed because author account currently has insufficient funds")

            await target_db["purchases"].update_one(
                {"_id": purchase_id},
                {"$set": {"status": "CANCELLED", "cancelled_at": datetime.now(timezone.utc)}},
                session=session,
            )
            
            tx_refund_buyer = Transaction(
                user_id=str(current_user.get("id")),
                type=TransactionType.REFUND,
                amount=price,
                note="Refund issued for previously cancelled purchase transaction",
            )
            tx_refund_seller = Transaction(
                user_id=creator_id,
                type=TransactionType.REFUND,
                amount=-price,
                note="Funds deducted for previously cancelled purchase transaction refund",
            )
            await target_db["transactions"].insert_one(tx_refund_buyer.model_dump(by_alias=True), session=session)
            await target_db["transactions"].insert_one(tx_refund_seller.model_dump(by_alias=True), session=session)

            if should_close_session:
                await session.commit_transaction()
            return {"message": "Refund request successfully processed and digital funds have been fully restored", "refunded_amount": price}
        except HTTPException:
            raise
        except Exception:
            if should_close_session:
                await session.abort_transaction()
            logger.error("Unexpected error occurred attempting to process refund request and adjust associated balances")
            raise HTTPException(status_code=500, detail="System encountered internal failure attempting to process requested refund financial transaction")
        finally:
            if should_close_session:
                await session.end_session()