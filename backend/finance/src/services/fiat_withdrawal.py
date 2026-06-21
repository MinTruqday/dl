from datetime import datetime, timezone

from fastapi import HTTPException
from loguru import logger
from src.schemas.account_ledger import Transaction, TransactionType
from uuid6 import uuid7

from core.config import settings
from core.database import db_client

ALLOWED_WITHDRAWAL_QUEUE_STATUSES = {"PENDING", "APPROVED", "REJECTED", "CANCELLED"}
ALLOWED_WITHDRAWAL_ACTIONS = {"approve", "reject"}


class FiatWithdrawal:

    @staticmethod
    async def get_revenue(current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        pipeline = [
            {
                "$match": {
                    "user_id": str(current_user.id),
                    "type": {"$in": ["receive", "tip"]},
                }
            },
            {"$group": {"_id": None, "total_revenue": {"$sum": "$amount"}}},
        ]
        cursor = db["transactions"].aggregate(pipeline)
        res = await cursor.to_list(length=1)
        total_revenue = res[0]["total_revenue"] if res else 0
        withdrawal_res = (
            await db["withdrawal_requests"]
            .aggregate(
                [
                    {"$match": {"user_id": str(current_user.id), "status": "PENDING"}},
                    {"$group": {"_id": None, "pending": {"$sum": "$amount"}}},
                ]
            )
            .to_list(length=1)
        )
        pending_withdrawal = withdrawal_res[0]["pending"] if withdrawal_res else 0
        return {
            "total_revenue": total_revenue,
            "pending_withdrawal": pending_withdrawal,
            "currency": "dl",
        }

    @staticmethod
    async def request_withdrawal(
        data: dict, current_user, db=None, session=None
    ) -> dict:
        should_close_session = False
        if db is None:
            db = db_client.mongodb.get_default_database()

        if session is None:
            session = await db_client.mongodb.start_session()
            session.start_transaction()
            should_close_session = True

        amount = int(data.get("amount", 0))
        bank_info = data.get("bank_info", "")
        if amount < 100000:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=400, detail="Số tiền rút dưới mức tối thiểu"
            )

        wallet = await db["wallets"].find_one({"_id": str(current_user.id)})
        if not wallet or wallet.get("balance", 0) < amount:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=400, detail="Tài khoản không đủ số dư để rút tiền"
            )

        now = datetime.now(timezone.utc)

        user_info = {}
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.MANAGEMENT_URL}/nguoi-dung/{current_user.id}",
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                if resp.status_code == 200:
                    user_info = resp.json().get("data") or {}
        except Exception:
            logger.warning("Lỗi đồng bộ hồ sơ tài khoản bên ngoài")

        if user_info.get("last_password_change"):
            last_pw_str = user_info["last_password_change"]
            last_pw = datetime.fromisoformat(last_pw_str)
            if last_pw.tzinfo is None:
                last_pw = last_pw.replace(tzinfo=timezone.utc)
            if (now - last_pw).total_seconds() < 86400:
                if should_close_session:
                    await session.abort_transaction()
                    await session.end_session()
                raise HTTPException(
                    status_code=403,
                    detail="Khóa rút tiền tạm thời do vừa đổi mật khẩu",
                )

        if wallet.get("last_bank_update"):
            last_bank = (
                wallet["last_bank_update"].replace(tzinfo=timezone.utc)
                if wallet["last_bank_update"].tzinfo is None
                else wallet["last_bank_update"]
            )
            if (now - last_bank).total_seconds() < 86400:
                if should_close_session:
                    await session.abort_transaction()
                    await session.end_session()
                raise HTTPException(
                    status_code=403,
                    detail="Tạm khóa rút tiền do vừa cập nhật tài khoản ngân hàng",
                )

        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        daily_withdrawals = (
            await db["withdrawal_requests"]
            .aggregate(
                [
                    {
                        "$match": {
                            "user_id": str(current_user.id),
                            "created_at": {"$gte": today_start},
                            "status": {"$in": ["PENDING", "APPROVED"]},
                        }
                    },
                    {
                        "$group": {
                            "_id": None,
                            "count": {"$sum": 1},
                            "total_amount": {"$sum": "$amount"},
                        }
                    },
                ]
            )
            .to_list(length=1)
        )

        if daily_withdrawals:
            stats = daily_withdrawals[0]
            if stats["count"] >= 3:
                if should_close_session:
                    await session.abort_transaction()
                    await session.end_session()
                raise HTTPException(
                    status_code=429, detail="Vượt quá số lần rút tiền tối đa trong ngày"
                )
            if stats["total_amount"] + amount > 20000000:
                if should_close_session:
                    await session.abort_transaction()
                    await session.end_session()
                raise HTTPException(
                    status_code=429,
                    detail="Vượt quá giới hạn rút tiền tối đa trong ngày",
                )

        withdrawal_id = str(uuid7())
        try:
            deduct_result = await db["wallets"].update_one(
                {"_id": str(current_user.id), "balance": {"$gte": amount}},
                {"$inc": {"balance": -amount}},
                session=session,
            )
            if deduct_result.modified_count == 0:
                if should_close_session:
                    await session.abort_transaction()
                raise HTTPException(
                    status_code=400, detail="Tài khoản không đủ số dư để rút tiền"
                )

            withdrawal_request = {
                "_id": withdrawal_id,
                "user_id": str(current_user.id),
                "amount": amount,
                "bank_info": bank_info,
                "status": "PENDING",
                "created_at": datetime.now(timezone.utc),
            }
            await db["withdrawal_requests"].insert_one(
                withdrawal_request, session=session
            )
            transaction = Transaction(
                user_id=str(current_user.id),
                amount=-amount,
                type=TransactionType.WITHDRAW,
                note="Funds temporarily reserved for pending withdrawal processing",
                reference_id=withdrawal_id,
            )
            await db["transactions"].insert_one(
                transaction.model_dump(by_alias=True), session=session
            )

            if should_close_session:
                await session.commit_transaction()

            logger.info("Đã ghi nhận yêu cầu rút tiền")
            return {
                "message": "Gửi yêu cầu rút tiền thành công",
                "withdrawal_id": withdrawal_id,
            }
        except HTTPException:
            raise
        except Exception:
            if should_close_session:
                await session.abort_transaction()
            logger.error("Lỗi khởi tạo giao dịch rút tiền")
            raise HTTPException(
                status_code=500, detail="Không thể xử lý yêu cầu rút tiền lúc này"
            )
        finally:
            if should_close_session:
                await session.end_session()

    @staticmethod
    async def get_withdrawal_queue(status: str = "pending", db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        normalized_status = status.upper()
        if normalized_status not in ALLOWED_WITHDRAWAL_QUEUE_STATUSES:
            raise HTTPException(
                status_code=400, detail="Trạng thái rút tiền không hợp lệ"
            )
        pipeline = [
            {"$match": {"status": normalized_status}},
            {"$sort": {"created_at": -1}},
            {"$limit": 100},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user_info",
                }
            },
            {"$unwind": {"path": "$user_info", "preserveNullAndEmptyArrays": True}},
        ]
        withdrawals = (
            await db["withdrawal_requests"].aggregate(pipeline).to_list(length=100)
        )
        result = []
        for p in withdrawals:
            user = p.get("user_info", {})
            result.append(
                {
                    "_id": str(p["_id"]),
                    "user_id": p.get("user_id"),
                    "user_name": user.get("full_name") if user else "Unknown",
                    "amount": p.get("amount"),
                    "status": p.get("status"),
                    "bank_info": p.get("bank_info", {}),
                    "created_at": (
                        p["created_at"].isoformat()
                        if isinstance(p.get("created_at"), datetime)
                        else p.get("created_at")
                    ),
                }
            )
        return result

    @staticmethod
    async def verify_withdrawal(
        withdrawal_id: str, action: str, current_user, db=None, session=None
    ) -> dict:
        should_close_session = False
        if db is None:
            db = db_client.mongodb.get_default_database()

        if session is None:
            session = await db_client.mongodb.start_session()
            session.start_transaction()
            should_close_session = True

        normalized_action = action.strip().lower()
        if normalized_action not in ALLOWED_WITHDRAWAL_ACTIONS:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(status_code=400, detail="Mã xác thực không hợp lệ")

        withdrawal = await db["withdrawal_requests"].find_one({"_id": withdrawal_id})
        if not withdrawal:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy yêu cầu rút tiền với mã giao dịch này",
            )

        if str(current_user.id) == withdrawal.get("user_id"):
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=403, detail="Không thể tự duyệt yêu cầu rút tiền của mình"
            )

        current_status = withdrawal.get("status")
        if current_status != "PENDING":
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=400, detail="Yêu cầu rút tiền đã được xử lý"
            )

        status = "APPROVED" if normalized_action == "approve" else "REJECTED"

        try:
            update_result = await db["withdrawal_requests"].update_one(
                {"_id": withdrawal_id, "status": "PENDING"},
                {
                    "$set": {
                        "status": status,
                        "processed_by": str(current_user.id),
                        "processed_at": datetime.now(timezone.utc),
                    }
                },
                session=session,
            )
            if update_result.modified_count == 0:
                if should_close_session:
                    await session.abort_transaction()
                raise HTTPException(
                    status_code=400, detail="Lỗi cập nhật trạng thái yêu cầu rút tiền"
                )

            if status == "REJECTED":
                await db["wallets"].update_one(
                    {"_id": withdrawal.get("user_id")},
                    {"$inc": {"balance": withdrawal.get("amount", 0)}},
                    upsert=True,
                    session=session,
                )
                refund_transaction = Transaction(
                    user_id=withdrawal.get("user_id"),
                    amount=withdrawal.get("amount", 0),
                    type=TransactionType.REFUND,
                    note="Reserved funds refunded due to rejected withdrawal application following administrative review",
                    reference_id=withdrawal_id,
                )
                await db["transactions"].insert_one(
                    refund_transaction.model_dump(by_alias=True), session=session
                )

            bank_info = str(withdrawal.get("bank_info", ""))
            masked_bank = (
                bank_info[:4] + "***" + bank_info[-3:] if len(bank_info) > 8 else "***"
            )
            await db["audit_logs"].insert_one(
                {
                    "action": f"WITHDRAWAL_{status}",
                    "actor_id": str(current_user.id),
                    "withdrawal_id": withdrawal_id,
                    "bank_info_masked": masked_bank,
                    "timestamp": datetime.now(timezone.utc),
                },
                session=session,
            )

            if should_close_session:
                await session.commit_transaction()

            logger.info("Xác minh yêu cầu rút tiền thành công")
            return {"message": "Xác minh yêu cầu rút tiền thành công"}
        except HTTPException:
            raise
        except Exception:
            if should_close_session:
                await session.abort_transaction()
            logger.error("Lỗi xác minh yêu cầu rút tiền")
            raise HTTPException(
                status_code=500, detail="Giao dịch thanh toán đang gặp lỗi"
            )
        finally:
            if should_close_session:
                await session.end_session()

    @staticmethod
    async def cancel_withdrawal(
        withdrawal_id: str, current_user, db=None, session=None
    ) -> dict:
        should_close_session = False
        if db is None:
            db = db_client.mongodb.get_default_database()

        if session is None:
            session = await db_client.mongodb.start_session()
            session.start_transaction()
            should_close_session = True

        withdrawal = await db["withdrawal_requests"].find_one(
            {"_id": withdrawal_id, "user_id": str(current_user.id)}
        )
        if not withdrawal:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy yêu cầu rút tiền với mã giao dịch này",
            )
        if withdrawal.get("status") != "PENDING":
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=400, detail="Chỉ có thể hủy yêu cầu rút tiền đang chờ xử lý"
            )

        try:
            update_result = await db["withdrawal_requests"].update_one(
                {
                    "_id": withdrawal_id,
                    "user_id": str(current_user.id),
                    "status": "PENDING",
                },
                {
                    "$set": {
                        "status": "CANCELLED",
                        "cancelled_at": datetime.now(timezone.utc),
                    }
                },
                session=session,
            )
            if update_result.modified_count == 0:
                if should_close_session:
                    await session.abort_transaction()
                raise HTTPException(
                    status_code=400, detail="Lỗi cập nhật trạng thái yêu cầu rút tiền"
                )

            await db["wallets"].update_one(
                {"_id": str(current_user.id)},
                {"$inc": {"balance": withdrawal.get("amount", 0)}},
                upsert=True,
                session=session,
            )
            refund_transaction = Transaction(
                user_id=str(current_user.id),
                amount=withdrawal.get("amount", 0),
                type=TransactionType.TOPUP,
                note="Reserved funds successfully restored following cancellation of withdrawal request",
                reference_id=withdrawal_id,
            )
            await db["transactions"].insert_one(
                refund_transaction.model_dump(by_alias=True), session=session
            )

            if should_close_session:
                await session.commit_transaction()

            logger.info("Đã hủy yêu cầu rút tiền và hoàn tiền")
            return {"message": "Đã hủy yêu cầu rút tiền và hoàn tiền"}
        except HTTPException:
            raise
        except Exception:
            if should_close_session:
                await session.abort_transaction()
            logger.error("Lỗi hủy yêu cầu rút tiền")
            raise HTTPException(
                status_code=500, detail="Giao dịch thanh toán đang gặp lỗi"
            )
        finally:
            if should_close_session:
                await session.end_session()
