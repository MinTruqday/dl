import json
from datetime import datetime, timezone

from fastapi import HTTPException, Query, status
from loguru import logger
from src.schemas.wallet import Transaction, TransactionType

from core.config import settings
from core.database import db_client


class WalletManager:

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
                        detail="Truy cập bị hạn chế, vui lòng thử lại sau 5 phút",
                    )
            except HTTPException:
                raise
            except Exception:
                logger.error("Lỗi bộ đệm khi kiểm tra giới hạn")

        if db_client.redis:
            try:
                is_locked = await db_client.redis.set(
                    lock_key, "locked", nx=True, ex=10
                )
                if not is_locked:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Mã giảm giá đang được xử lý trong một giao dịch khác",
                    )
            except HTTPException:
                raise
            except Exception:
                logger.error("Lỗi bảo mật phiên đăng nhập")
                raise HTTPException(
                    status_code=500, detail="Lỗi kết nối bộ đệm lưu trữ"
                )

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
            result = await WalletRepository.mark_coupon_as_used(
                coupon["_id"], str(current_user.id), db=db, session=session
            )
            if result.modified_count == 0:
                if should_close_session:
                    await session.abort_transaction()
                raise HTTPException(
                    status_code=400, detail="Mã giảm giá đã hết lượt sử dụng"
                )

            await WalletRepository.increment_balance(
                str(current_user.id), bonus_dl, db=db, session=session
            )
            tx = Transaction(
                user_id=str(current_user.id),
                type=TransactionType.TOPUP,
                amount=bonus_dl,
                note="Promotional coupon successfully redeemed and credited",
            )
            await WalletRepository.insert_transaction(
                tx.model_dump(by_alias=True), db=db, session=session
            )

            if should_close_session:
                await session.commit_transaction()

            try:
                import httpx

                from core.config import settings

                if settings.NOTIFICATION_URL:
                    async with httpx.AsyncClient() as client:
                        await client.post(
                            f"{settings.NOTIFICATION_URL}/notifications/dispatch",
                            json={
                                "target_user_id": str(current_user.id),
                                "title": "Deposit transaction completed",
                                "body": "Your digital wallet has been successfully credited with the requested bonus balance",
                                "type": "topup",
                            },
                            timeout=settings.DEFAULT_HTTP_TIMEOUT,
                        )
            except Exception:
                logger.warning("Lỗi gửi thông báo thành công")
            logger.info("Đổi mã giảm giá thành công")
            return {
                "message": "Đổi mã giảm giá thành công",
                "bonus_dl": bonus_dl,
                "status": "success",
            }
        except HTTPException:
            raise
        except Exception:
            if should_close_session:
                await session.abort_transaction()
            logger.error("Lỗi đổi mã giảm giá")
            raise HTTPException(
                status_code=500,
                detail="Tính năng thanh toán đang bảo trì, vui lòng thử lại sau",
            )
        finally:
            if should_close_session:
                await session.end_session()
            if db_client.redis and is_locked:
                try:
                    await db_client.redis.delete(lock_key)
                except Exception:
                    logger.error("Lỗi mở khóa phiên bảo mật")

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
            except Exception:
                logger.warning("Lỗi định dạng phân trang")
        txs = await WalletRepository.get_transactions(
            query, skip=skip, limit=limit, db=db
        )
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
