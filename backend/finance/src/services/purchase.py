from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from loguru import logger
from pymongo.errors import DuplicateKeyError
from redis.exceptions import LockError
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.infrastructure.redis import redis
from src.core.logic_logger import log_logic_execution
from src.schemas.wallet import Transaction, TransactionType


class PurchaseService:
    @staticmethod
    def _databases():
        client = database.mongodb
        return (
            client[settings.FINANCE_DB_NAME],
            client[settings.CONTENT_DB_NAME],
            client[settings.HUMANITY_DB_NAME],
            client[settings.USAGE_DB_NAME],
        )

    @staticmethod
    def _notification(target_user_id: str, title: str, body: str, event_type: str):
        now = datetime.now(timezone.utc)
        event_id = str(uuid7())
        return {
            "_id": event_id,
            "event_type": "notification",
            "payload": {
                "target_user_id": target_user_id,
                "title": title,
                "body": body,
                "type": event_type,
                "idempotency_key": event_id,
            },
            "status": "pending",
            "attempts": 0,
            "next_attempt_at": now,
            "created_at": now,
        }

    @staticmethod
    @log_logic_execution
    async def get_revenue(current_user) -> dict:
        finance_db, content_db, humanity_db, usage_db = PurchaseService._databases()
        documents = await content_db.documents.find(
            {"creator_id": str(current_user.id), "is_deleted": {"$ne": True}}
        ).to_list(length=None)
        document_ids = [str(document["_id"]) for document in documents]
        revenue_rows = await finance_db.purchases.aggregate(
            [
                {"$match": {"document_id": {"$in": document_ids}, "status": "ACTIVE"}},
                {"$group": {"_id": "$document_id", "revenue": {"$sum": "$price"}, "purchases": {"$sum": 1}}},
            ]
        ).to_list(length=None)
        revenue_map = {
            row["_id"]: {"revenue": row["revenue"], "purchases": row["purchases"]}
            for row in revenue_rows
        }
        wallet = await finance_db.wallets.find_one({"_id": str(current_user.id)})
        profile = await humanity_db.users.find_one({"_id": str(current_user.id)})
        return {
            "total_revenue": sum(row["revenue"] for row in revenue_rows),
            "total_views": sum(document.get("views", document.get("view_count", 0)) for document in documents),
            "total_points": profile.get("reward_points", 0) if profile else 0,
            "available_balance": wallet.get("balance", 0) if wallet else 0,
            "documents": [
                {
                    "id": str(document["_id"]),
                    "slug": document.get("slug", str(document["_id"])),
                    "title": document.get("title", "Không có tiêu đề"),
                    "views": document.get("views", document.get("view_count", 0)),
                    "price": document.get("price_dl", document.get("price_dls", 0)),
                    "purchases": revenue_map.get(str(document["_id"]), {}).get("purchases", 0),
                    "revenue": revenue_map.get(str(document["_id"]), {}).get("revenue", 0),
                }
                for document in documents
            ],
        }

    @staticmethod
    @log_logic_execution
    async def buy_ai_tier(tier: str, current_user) -> dict:
        from src.core.dependency import Tier
        tier = tier.upper()
        if tier not in {Tier.PRO.value, Tier.PREMIUM.value}:
            raise HTTPException(status_code=400, detail="Gói thành viên không hợp lệ")
        price = 750 if tier == Tier.PRO.value else 2500
        finance_db, content_db, humanity_db, usage_db = PurchaseService._databases()
        user_id = str(current_user.id)
        current_subscription = await usage_db.subscriptions.find_one({"user_id": user_id})
        if current_subscription and current_subscription.get("ai_tier") == tier:
            expires_at = current_subscription.get("expires_at")
            if isinstance(expires_at, datetime) and expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if not expires_at or expires_at > datetime.now(timezone.utc):
                raise HTTPException(status_code=409, detail="Tài khoản hiện đã sở hữu gói thành viên này")
        now = datetime.now(timezone.utc)
        async with await database.mongodb.start_session() as session:
            async with session.start_transaction():
                deduction = await finance_db.wallets.update_one(
                    {"_id": user_id, "balance": {"$gte": price}},
                    {"$inc": {"balance": -price}},
                    session=session,
                )
                if deduction.modified_count != 1:
                    raise HTTPException(status_code=400, detail="Số dư ví không đủ để nâng cấp gói thành viên")
                await usage_db.subscriptions.update_one(
                    {"user_id": user_id},
                    {
                        "$set": {
                            "ai_tier": tier,
                            "is_premium": True,
                            "purchased_at": now,
                            "expires_at": now + timedelta(days=30),
                            "updated_at": now,
                        },
                        "$setOnInsert": {"user_id": user_id, "created_at": now},
                    },
                    upsert=True,
                    session=session,
                )
                transaction = Transaction(
                    user_id=user_id,
                    type=TransactionType.PURCHASE,
                    amount=-price,
                    note=f"Membership upgrade to {tier} plan",
                    reference_id=f"membership:{tier}:{now.date().isoformat()}",
                )
                await finance_db.transactions.insert_one(
                    transaction.model_dump(by_alias=True),
                    session=session,
                )
                await finance_db.outbox_events.insert_one(
                    PurchaseService._notification(
                        user_id,
                        "Nâng cấp thành viên thành công",
                        f"Gói thành viên {tier} đã được kích hoạt trong 30 ngày",
                        "membership",
                    ),
                    session=session,
                )
        return {"tier": tier, "status": "active", "expires_at": now + timedelta(days=30)}

    @staticmethod
    @log_logic_execution
    async def purchase_document(document_id: str, current_user) -> dict:
        finance_db, content_db, humanity_db, usage_db = PurchaseService._databases()
        user_id = str(current_user.id)
        document = await content_db.documents.find_one(
            {
                "_id": document_id,
                "status": "published",
                "is_deleted": {"$ne": True},
            }
        )
        if not document:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu đang được phát hành")
        creator_id = str(document.get("creator_id", ""))
        if not creator_id:
            raise HTTPException(status_code=409, detail="Tài liệu chưa có thông tin chủ sở hữu hợp lệ")
        if creator_id == user_id:
            return {"message": "Tác giả đã có quyền sở hữu tài liệu", "status": "owned"}
        price = int(document.get("price_dl", document.get("price_dls", 0)) or 0)
        if price <= 0:
            return {"message": "Tài liệu đang được truy cập miễn phí", "status": "free"}

        lock = redis.get_client().lock(
            f"purchase:{user_id}:{document_id}",
            timeout=20,
            blocking_timeout=5,
        )
        if not await lock.acquire():
            raise HTTPException(status_code=409, detail="Một giao dịch mua tài liệu đang được xử lý")
        try:
            existing = await finance_db.purchases.find_one(
                {
                    "user_id": user_id,
                    "document_id": document_id,
                    "item_type": "document",
                    "status": "ACTIVE",
                }
            )
            if existing:
                return {"message": "Tài liệu đã được mua", "status": "owned"}
            purchase_id = str(uuid7())
            try:
                async with await database.mongodb.start_session() as session:
                    async with session.start_transaction():
                        deduction = await finance_db.wallets.update_one(
                            {"_id": user_id, "balance": {"$gte": price}},
                            {"$inc": {"balance": -price}},
                            session=session,
                        )
                        if deduction.modified_count != 1:
                            raise HTTPException(status_code=400, detail="Số dư ví không đủ để mua tài liệu")
                        await finance_db.wallets.update_one(
                            {"_id": creator_id},
                            {"$inc": {"balance": price, "withdrawable_balance": price}},
                            upsert=True,
                            session=session,
                        )
                        now = datetime.now(timezone.utc)
                        await finance_db.purchases.insert_one(
                            {
                                "_id": purchase_id,
                                "user_id": user_id,
                                "document_id": document_id,
                                "item_type": "document",
                                "price": price,
                                "status": "ACTIVE",
                                "purchased_at": now,
                            },
                            session=session,
                        )
                        buyer_transaction = Transaction(
                            user_id=user_id,
                            type=TransactionType.PURCHASE,
                            amount=-price,
                            note="Payment processed for digital document acquisition",
                            reference_id=purchase_id,
                        )
                        seller_transaction = Transaction(
                            user_id=creator_id,
                            type=TransactionType.RECEIVE,
                            amount=price,
                            note="Revenue earned from a published digital document",
                            reference_id=purchase_id,
                        )
                        await finance_db.transactions.insert_many(
                            [
                                buyer_transaction.model_dump(by_alias=True),
                                seller_transaction.model_dump(by_alias=True),
                            ],
                            session=session,
                        )
                        await finance_db.outbox_events.insert_one(
                            PurchaseService._notification(
                                creator_id,
                                "Tài liệu vừa được mua",
                                "Một người đọc đã mua tài liệu bạn đang phát hành",
                                "purchase",
                            ),
                            session=session,
                        )
            except DuplicateKeyError:
                return {"message": "Tài liệu đã được mua", "status": "owned"}
            logger.info("Document purchase transaction completed")
            return {"message": "Mua tài liệu hoàn tất", "status": "purchased", "purchase_id": purchase_id}
        finally:
            try:
                await lock.release()
            except LockError:
                logger.warning("Purchase lock expired before release")

    @staticmethod
    @log_logic_execution
    async def cancel_purchase(purchase_id: str, current_user) -> dict:
        finance_db, content_db, humanity_db, usage_db = PurchaseService._databases()
        user_id = str(current_user.id)
        purchase = await finance_db.purchases.find_one(
            {"_id": purchase_id, "user_id": user_id, "status": "ACTIVE"}
        )
        if not purchase:
            raise HTTPException(status_code=404, detail="Không tìm thấy giao dịch mua đang hoạt động")
        purchased_at = purchase.get("purchased_at")
        if isinstance(purchased_at, datetime) and purchased_at.tzinfo is None:
            purchased_at = purchased_at.replace(tzinfo=timezone.utc)
        if not isinstance(purchased_at, datetime) or datetime.now(timezone.utc) - purchased_at > timedelta(hours=48):
            raise HTTPException(status_code=400, detail="Yêu cầu hoàn tiền đã vượt quá thời hạn")
        document = await content_db.documents.find_one({"_id": purchase["document_id"]})
        creator_id = str(document.get("creator_id", "")) if document else ""
        if not creator_id:
            raise HTTPException(status_code=409, detail="Không thể xác định tài khoản người bán")
        price = int(purchase.get("price", 0))
        async with await database.mongodb.start_session() as session:
            async with session.start_transaction():
                state = await finance_db.purchases.update_one(
                    {"_id": purchase_id, "user_id": user_id, "status": "ACTIVE"},
                    {"$set": {"status": "CANCELLED", "cancelled_at": datetime.now(timezone.utc)}},
                    session=session,
                )
                if state.modified_count != 1:
                    raise HTTPException(status_code=409, detail="Giao dịch đã được xử lý trước đó")
                seller_deduction = await finance_db.wallets.update_one(
                    {
                        "_id": creator_id,
                        "balance": {"$gte": price},
                        "withdrawable_balance": {"$gte": price},
                    },
                    {"$inc": {"balance": -price, "withdrawable_balance": -price}},
                    session=session,
                )
                if seller_deduction.modified_count != 1:
                    raise HTTPException(status_code=409, detail="Giao dịch chưa đủ điều kiện hoàn tiền")
                await finance_db.wallets.update_one(
                    {"_id": user_id},
                    {"$inc": {"balance": price}},
                    upsert=True,
                    session=session,
                )
                await finance_db.transactions.insert_many(
                    [
                        Transaction(
                            user_id=user_id,
                            type=TransactionType.REFUND,
                            amount=price,
                            note="Refund issued for cancelled purchase",
                            reference_id=purchase_id,
                        ).model_dump(by_alias=True),
                        Transaction(
                            user_id=creator_id,
                            type=TransactionType.REFUND,
                            amount=-price,
                            note="Revenue reversed for cancelled purchase",
                            reference_id=purchase_id,
                        ).model_dump(by_alias=True),
                    ],
                    session=session,
                )
        return {"message": "Hoàn tiền hoàn tất", "refunded_amount": price}
