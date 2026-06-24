from src.core.api_client import db_client
import json
from datetime import datetime, timezone

import httpx
from fastapi import HTTPException, Query, status
from loguru import logger
from src.schemas.wallet import Transaction, TransactionType

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database


class WalletService:

    @staticmethod
    async def get_balance(current_user, db=None):
        if db is None:
            db = database.mongodb.get_default_database()
        wallet = await db_client.find_one(collection="wallets", query={"_id": str(current_user.id)})
        return {"balance": wallet.get("balance", 0) if wallet else 0}

    @staticmethod
    async def redeem_coupon(req, current_user, db=None, session=None):
        should_close_session = False
        lock_key = f"lock:coupon:{req.code}"
        is_locked = False

        if database.redis:
            user_rl_key = f"rl:coupon:{current_user.id}"
            try:
                attempts = await database.redis.incr(user_rl_key)
                if attempts == 1:
                    await database.redis.expire(user_rl_key, 300)
                if attempts > 10:
                    raise HTTPException(
                        status_code=429,
                        detail="Truy cập bị hạn chế, vui lòng thử lại sau 5 phút",
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Lỗi bộ đệm khi kiểm tra giới hạn: {e}")

        if database.redis:
            try:
                is_locked = await database.redis.set(
                    lock_key, "locked", nx=True, ex=10
                )
                if not is_locked:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Mã giảm giá đang được xử lý trong một giao dịch khác",
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Lỗi bảo mật phiên đăng nhập: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Lỗi kết nối bộ đệm lưu trữ: {e}"
                )

        if db is None:
            db = database.mongodb.get_default_database()

        if session is None:
            session = await database.mongodb.start_session()
            session.start_transaction()
            should_close_session = True

        try:
            coupon = await db["coupons"].find_one(
                {"code": req.code}, session=session
            )
            if not coupon:
                if should_close_session:
                    await session.abort_transaction()
                raise HTTPException(
                    status_code=404,
                    detail="Mã giảm giá không hợp lệ hoặc không tồn tại",
                )
            if coupon.get("is_used"):
                if should_close_session:
                    await session.abort_transaction()
                raise HTTPException(
                    status_code=400, detail="Mã giảm giá đã được sử dụng"
                )

            bonus_dl = coupon.get("amount_dl", coupon.get("amount_dls", 0))
            result = await db["coupons"].update_one(
                {"_id": coupon["_id"]},
                {"$set": {"is_used": True, "used_by": str(current_user.id), "used_at": datetime.now(timezone.utc)}},
                session=session
            )
            if result.modified_count == 0:
                if should_close_session:
                    await session.abort_transaction()
                raise HTTPException(
                    status_code=400, detail="Mã giảm giá đã hết lượt sử dụng"
                )

            await db["wallets"].update_one(
                {"_id": str(current_user.id)},
                {"$inc": {"balance": bonus_dl}},
                upsert=True,
                session=session
            )
            tx = Transaction(
                user_id=str(current_user.id),
                type=TransactionType.TOPUP,
                amount=bonus_dl,
                note="Promotional coupon successfully redeemed and credited",
            )
            await db["transactions"].insert_one(
                tx.model_dump(by_alias=True), session=session
            )

            if should_close_session:
                await session.commit_transaction()

            try:
                from src.core.infrastructure.configuration import settings as shared_settings

                if shared_settings.NOTIFICATION_URL:
                    async with httpx.AsyncClient(timeout=shared_settings.DEFAULT_HTTP_TIMEOUT) as client:
                        await client.post(
                            f"{shared_settings.NOTIFICATION_URL}/thong-bao/gui-di",
                            json={
                                "target_user_id": str(current_user.id),
                                "title": "Deposit transaction completed",
                                "body": "Your digital wallet has been successfully credited with the requested bonus balance",
                                "type": "topup",
                            },
                        )
            except Exception as e:
                logger.warning(f"Lỗi gửi thông báo thành công: {e}")
            logger.info("Đổi mã giảm giá thành công")
            return {
                "message": "Đổi mã giảm giá thành công",
                "bonus_dl": bonus_dl,
                "status": "success",
            }
        except HTTPException:
            raise
        except Exception as e:
            if should_close_session:
                await session.abort_transaction()
            logger.error(f"Lỗi đổi mã giảm giá: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Tính năng thanh toán đang bảo trì, vui lòng thử lại sau: {e}",
            )
        finally:
            if should_close_session:
                await session.end_session()
            if database.redis and is_locked:
                try:
                    await database.redis.delete(lock_key)
                except Exception as e:
                    logger.error(f"Lỗi mở khóa phiên bảo mật: {e}")

    @staticmethod
    async def get_history(
        current_user,
        cursor: str = None,
        limit: int = 50,
        tx_type: str = None,
        skip: int = 0,
        db=None,
    ):
        if db is None:
            db = database.mongodb.get_default_database()
        query = {"user_id": str(current_user.id)}
        if tx_type:
            query["type"] = tx_type.lower()
        if cursor:
            try:
                query["created_at"] = {
                    "$lt": datetime.fromisoformat(cursor.replace("Z", "+00:00"))
                }
            except Exception as e:
                logger.warning(f"Lỗi định dạng phân trang: {e}")
        txs = await db_client.find(collection="transactions", query=query, sort=[("created_at", -1)], skip=skip, limit=limit)
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
