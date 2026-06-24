from shared.infrastructure.configuration import settings
import uuid
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from fastapi import HTTPException
from loguru import logger
from src.schemas.wallet import Transaction, TransactionType
from uuid6 import uuid7

from shared.infrastructure.database import database


class PurchaseService:

    @staticmethod
    async def get_revenue(current_user, db=None) -> dict:
        if db is None:
            db = database.mongodb.get_default_database()
            
        docs_cursor = db["documents"].find({"creator_id": str(current_user.id)})
        documents = await docs_cursor.to_list(length=None)
        doc_ids = [str(doc["_id"]) for doc in documents]
        
        total_views = sum(doc.get("view_count", 0) for doc in documents)
        
        pipeline = [
            {"$match": {"document_id": {"$in": doc_ids}, "status": {"$ne": "CANCELLED"}}},
            {"$group": {"_id": "$document_id", "revenue": {"$sum": "$price"}, "purchases": {"$sum": 1}}}
        ]
        revenue_res = await db["purchases"].aggregate(pipeline).to_list(length=None)
        
        revenue_map = {item["_id"]: {"revenue": item["revenue"], "purchases": item["purchases"]} for item in revenue_res}
        total_revenue = sum(item["revenue"] for item in revenue_res)
        
        user_doc = await db["users"].find_one({"_id": str(current_user.id)})
        wallet = await db["wallets"].find_one({"_id": str(current_user.id)})
        
        available_balance = wallet.get("balance", total_revenue) if wallet else total_revenue
        total_points = user_doc.get("reward_points", 0) if user_doc else 0

        revenue_data = {
            "total_revenue": total_revenue,
            "total_views": total_views,
            "total_points": total_points,
            "available_balance": available_balance,
            "documents": [
                {
                    "id": str(doc["_id"]),
                    "title": doc.get("title", "Không có tiêu đề"),
                    "views": doc.get("view_count", 0),
                    "price": doc.get("price_dl", doc.get("price_dls", 0)),
                    "purchases": revenue_map.get(str(doc["_id"]), {}).get("purchases", 0),
                    "revenue": revenue_map.get(str(doc["_id"]), {}).get("revenue", 0)
                }
                for doc in documents
            ]
        }
        return revenue_data

    @staticmethod
    async def buy_ai_tier(tier: str, current_user, db=None) -> dict:
        if db is None:
            db = database.mongodb.get_default_database()

        tier = tier.upper()
        if tier not in ["PRO", "PREMIUM"]:
            raise HTTPException(
                status_code=400,
                detail="Gói hội viên không hợp lệ, vui lòng chọn lại",
            )

        price = 750 if tier == "PRO" else 2500

        if current_user.ai_tier and current_user.ai_tier.value == tier:
            raise HTTPException(
                status_code=400,
                detail="Tài khoản đã có gói thành viên này",
            )

        wallet = await db["wallets"].find_one({"_id": str(current_user.id)})
        if not wallet or wallet.get("balance", 0) < price:
            raise HTTPException(
                status_code=400,
                detail="Số dư không đủ để đăng ký gói thành viên",
            )

        session = await database.mongodb.start_session()
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
                    detail="Số dư không đủ để đăng ký gói thành viên",
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
            logger.info("Nâng cấp gói thành viên thành công")
            return {
                "tier": tier,
                "status": "active",
            }
        except HTTPException:
            raise
        except Exception as e:
            await session.abort_transaction()
            logger.error(f"Lỗi nâng cấp gói thành viên: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Lỗi nâng cấp gói thành viên, vui lòng thử lại sau: {e}",
            )
        finally:
            await session.end_session()

    @staticmethod
    async def purchase_document(
        document_id: str, current_user, db=None, session=None
    ) -> dict:
        should_close_session = False
        if db is None:
            db = database.mongodb.get_default_database()

        if session is None:
            session = await database.mongodb.start_session()
            session.start_transaction()
            should_close_session = True

        doc = await db["documents"].find_one({"_id": document_id})
        if not doc:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn")
        price = doc.get("price_dl", doc.get("price_dls", 0))
        if price <= 0:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            return {"message": "Tài liệu đang được truy cập miễn phí", "status": "free"}
        wallet = await db["wallets"].find_one({"_id": str(current_user.id)})
        if not wallet or wallet.get("balance", 0) < price:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=400, detail="Tài khoản không đủ tiền để giao dịch"
            )
        lock = None
        if hasattr(database, "redis") and database.redis:
            lock = database.redis.lock(
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
                return {"message": "Tài liệu đã được mua", "status": "owned"}
            creator_id = doc.get("creator_id")

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
                        status_code=400, detail="Tài khoản không đủ tiền để giao dịch"
                    )
                if creator_id:
                    await db["wallets"].update_one(
                        {"_id": creator_id},
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
                    user_id=creator_id,
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

                if creator_id:
                    notif_id = str(uuid7())
                    notification = {
                        "_id": notif_id,
                        "target_user_id": creator_id,
                        "title": "New transaction recorded",
                        "body": "A user has successfully purchased your published document",
                        "is_read": False,
                        "type": "purchase",
                        "created_at": datetime.now(timezone.utc),
                    }
                    await db["notifications"].insert_one(notification, session=session)
                    if hasattr(database, "redis") and database.redis:
                        try:
                            import httpx

                            from shared.infrastructure.configuration import settings

                            if settings.NOTIFICATION_URL:
                                async with httpx.AsyncClient() as client:
                                    await client.post(
                                        f"{settings.NOTIFICATION_URL}/thong-bao/gui-di",
                                        json={
                                            "target_user_id": creator_id,
                                            "title": notification["title"],
                                            "body": notification["body"],
                                            "type": "purchase",
                                        },
                                        timeout=settings.DEFAULT_HTTP_TIMEOUT,
                                    )
                        except Exception as e:
                            logger.error(f"Lỗi gửi thông báo giao dịch thành công: {e}")
                logger.info("Giao dịch mua tài liệu thành công")
                return {
                    "message": "Thanh toán mua tài liệu thành công",
                    "status": "purchased",
                }
            except HTTPException:
                raise
            except Exception as e:
                if should_close_session:
                    await session.abort_transaction()
                logger.error(f"Lỗi xử lý thanh toán tài liệu: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Lỗi xử lý giao dịch tài chính: {e}"
                )
            finally:
                if should_close_session:
                    await session.end_session()
        finally:
            if (
                hasattr(database, "redis")
                and database.redis
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
            db = database.mongodb.get_default_database()

        if session is None:
            session = await database.mongodb.start_session()
            session.start_transaction()
            should_close_session = True

        purchase = await db["purchases"].find_one(
            {"_id": purchase_id, "user_id": str(current_user.id)}
        )
        if not purchase:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=404, detail="Không tìm thấy lịch sử giao dịch mua hàng"
            )
        purchased_at = purchase.get("purchased_at", datetime.now(timezone.utc))
        if isinstance(purchased_at, str):
            purchased_at = datetime.fromisoformat(purchased_at)
        if datetime.now(timezone.utc) - purchased_at > timedelta(hours=48):
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(status_code=400, detail="Từ chối hoàn tiền do quá hạn")
        price = purchase.get("price", 0)
        doc_id = purchase.get("document_id")
        doc = await db["documents"].find_one({"_id": doc_id}) if doc_id else None
        creator_id = doc.get("creator_id") if doc else None

        try:
            await db["wallets"].update_one(
                {"_id": str(current_user.id)},
                {"$inc": {"balance": price}},
                upsert=True,
                session=session,
            )
            if creator_id:
                deduct_result = await db["wallets"].update_one(
                    {"_id": creator_id, "balance": {"$gte": price}},
                    {"$inc": {"balance": -price}},
                    session=session,
                )
                if deduct_result.modified_count == 0:
                    if should_close_session:
                        await session.abort_transaction()
                    raise HTTPException(
                        status_code=400,
                        detail="Tài khoản không đủ số dư để hoàn tiền",
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
                user_id=creator_id,
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
            return {"message": "Hoàn tiền thành công", "refunded_amount": price}
        except HTTPException:
            raise
        except Exception as e:
            if should_close_session:
                await session.abort_transaction()
            logger.error(f"Lỗi xử lý hoàn tiền: {e}")
            raise HTTPException(status_code=500, detail=f"Lỗi xử lý hoàn tiền: {e}")
        finally:
            if should_close_session:
                await session.end_session()
