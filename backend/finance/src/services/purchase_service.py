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
            raise HTTPException(status_code=400, detail="Gói AI không hợp lệ")

        price = 750 if tier == "PRO" else 2500

        wallet = await db["wallets"].find_one({"_id": str(current_user.id)})
        if not wallet or wallet.get("balance", 0) < price:
            raise HTTPException(
                status_code=400, detail=f"Số dư không đủ cần {price} dl"
            )

        if current_user.ai_tier.value == tier:
            raise HTTPException(
                status_code=400, detail=f"Bạn đang sử dụng gói {tier} rồi"
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
                    status_code=400, detail=f"Số dư không đủ cần {price} dl"
                )

            await db["users"].update_one(
                {"_id": str(current_user.id)},
                {"$set": {"ai_tier": tier}},
                session=session,
            )

            tx = Transaction(
                user_id=str(current_user.id),
                type=TransactionType.WITHDRAW,
                amount=-price,
                note=f"Nâng cấp gói AI: {tier}",
            )
            await db["transactions"].insert_one(
                tx.model_dump(by_alias=True), session=session
            )

            await session.commit_transaction()

            return {
                "message": f"Đã nâng cấp lên gói {tier} thành công",
                "status": "success",
                "tier": tier,
            }
        except HTTPException:
            raise
        except Exception:
            await session.abort_transaction()
            logger.error("Lỗi nâng cấp gói AI")
            raise HTTPException(status_code=500, detail="Giao dịch thất bại")
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
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại")
        price = doc.get("price_dl", doc.get("price_dls", 0))
        if price <= 0:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            return {"message": "Tài liệu được cung cấp miễn phí", "status": "free"}
        wallet = await db["wallets"].find_one({"_id": str(current_user.id)})
        if not wallet or wallet.get("balance", 0) < price:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=400, detail=f"Số dư không đủ cần {price} dl"
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
                return {"message": "Tài liệu đã được sở hữu", "status": "owned"}
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
                        status_code=400, detail=f"Số dư không đủ cần {price} dl"
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
                    note=f"Mua tài liệu: {doc.get('title', document_id)}",
                )
                tx_seller = Transaction(
                    user_id=author_id,
                    type=TransactionType.RECEIVE,
                    amount=price,
                    note=f"Bán tài liệu: {doc.get('title', document_id)}",
                )
                await db["transactions"].insert_many(
                    [
                        tx_buyer.model_dump(by_alias=True),
                        tx_seller.model_dump(by_alias=True),
                    ],
                    session=session,
                )

                if should_close_session:
                    await session.commit_transaction()

                if author_id:
                    notif_id = str(uuid7())
                    buyer_name = current_user.full_name or "Độc giả"
                    doc_title = doc.get("title", document_id)
                    notification = {
                        "_id": notif_id,
                        "target_user_id": author_id,
                        "title": "Giao dịch mới",
                        "body": f"{buyer_name} vừa mua tài liệu '{doc_title}'",
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
                        except Exception as e:
                            logger.error("Lỗi gửi thông báo")
                logger.info(
                    f"Người dùng {current_user.id} mua tài liệu {document_id} với giá {price} dl"
                )
                return {
                    "message": "Thanh toán mua tài liệu thành công",
                    "status": "purchased",
                }
            except HTTPException:
                raise
            except Exception as e:
                if should_close_session:
                    await session.abort_transaction()
                logger.error(f"Giao dịch mua tài liệu của {current_user.id} thất bại")
                raise HTTPException(status_code=500, detail="Giao dịch thất bại")
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
            raise HTTPException(status_code=404, detail="Giao dịch mua không tồn tại")
        purchased_at = purchase.get("purchased_at", datetime.now(timezone.utc))
        if isinstance(purchased_at, str):
            purchased_at = datetime.fromisoformat(purchased_at)
        if datetime.now(timezone.utc) - purchased_at > timedelta(hours=48):
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=400, detail="Chỉ được hoàn tiền trong vòng 48 giờ"
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
                        detail="Không thể hoàn tiền do tác giả đã rút tiền hoặc số dư không đủ",
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
                note=f"Hoàn tiền giao dịch: {purchase_id}",
            )
            tx_refund_seller = Transaction(
                user_id=author_id,
                type=TransactionType.REFUND,
                amount=-price,
                note=f"Hoàn tiền giao dịch: {purchase_id}",
            )
            await db["transactions"].insert_many(
                [
                    tx_refund_buyer.model_dump(by_alias=True),
                    tx_refund_seller.model_dump(by_alias=True),
                ],
                session=session,
            )

            if should_close_session:
                await session.commit_transaction()
            return {"message": "Hoàn tiền thành công", "refunded_amount": price}
        except HTTPException:
            raise
        except Exception as e:
            if should_close_session:
                await session.abort_transaction()
            logger.error("Lỗi hoàn tiền")
            raise HTTPException(status_code=500, detail="Hoàn tiền thất bại")
        finally:
            if should_close_session:
                await session.end_session()
