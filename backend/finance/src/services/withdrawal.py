from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
from datetime import datetime, timezone

import httpx
from fastapi import HTTPException
from loguru import logger
from src.schemas.wallet import Transaction, TransactionType
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database

ALLOWED_WITHDRAWAL_QUEUE_STATUSES = {"PENDING", "APPROVED", "REJECTED", "CANCELLED"}
ALLOWED_WITHDRAWAL_ACTIONS = {"approve", "reject"}

class WithdrawalService:

    @staticmethod
    @log_logic_execution
    async def get_revenue(current_user):
        pipeline = [
            {
                "$match": {
                    "user_id": str(current_user.id),
                    "type": {"$in": ["receive", "tip"]},
                }
            },
            {"$group": {"_id": None, "total_revenue": {"$sum": "$amount"}}},
        ]
        cursor = mongo.aggregate(collection="transactions", pipeline=pipeline)
        res = await cursor 
        total_revenue = res[0]["total_revenue"] if res else 0
        withdrawal_res = (
            await database.mongodb["withdrawal_requests"]
            .aggregate(
                [
                    {"$match": {"user_id": str(current_user.id), "status": "PENDING"}},
                    {"$group": {"_id": None, "pending": {"$sum": "$amount"}}},
                ]
            )
            .execute()
        )
        pending_withdrawal = withdrawal_res[0]["pending"] if withdrawal_res else 0
        return {
            "total_revenue": total_revenue,
            "pending_withdrawal": pending_withdrawal,
            "currency": "dl",
        }

    @staticmethod
    @log_logic_execution
    async def request_withdrawal(
        data: dict, current_user, session=None
    ) -> dict:
        should_close_session = False
        if session is None:
            session = await database.mongodb.start_session()
            session.start_transaction()
            should_close_session = True

        amount = int(data.get("amount", 0))
        bank_info = data.get("bank_info", "")
        if amount < 50:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=400, detail="Số tiền giao dịch chưa đạt hạn mức rút tiền tối thiểu quy định"
            )

        wallet = await mongo.find_one(collection="wallets", query={"_id": str(current_user.id)})
        if not wallet or wallet.get("balance", 0) < amount:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=400, detail="Số dư ví không đủ để thực hiện giao dịch rút tiền"
            )

        now = datetime.now(timezone.utc)

        user_info = {}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{settings.MANAGEMENT_URL}/nguoi-dung/{current_user.id}",
                )
                if resp.status_code == 200:
                    user_info = resp.json().get("data") or {}
        except Exception as e:
            logger.exception("User profile synchronization with external management service failed")

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
                    detail="Tính năng rút tiền bị tạm khóa vì lý do bảo mật sau khi đổi mật khẩu",
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
                    detail="Tính năng rút tiền bị tạm khóa vì lý do bảo mật sau khi cập nhật thông tin ngân hàng",
                )

        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        daily_withdrawals = (
            await database.mongodb["withdrawal_requests"]
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
            .to_list(length=None)
        )

        if daily_withdrawals:
            stats = daily_withdrawals[0]
            if stats["count"] >= 3:
                if should_close_session:
                    await session.abort_transaction()
                    await session.end_session()
                raise HTTPException(
                    status_code=429, detail="Giao dịch vượt quá số lần rút tiền tối đa cho phép trong ngày"
                )
            if stats["total_amount"] + amount > 20000000:
                if should_close_session:
                    await session.abort_transaction()
                    await session.end_session()
                raise HTTPException(
                    status_code=429,
                    detail="Giao dịch vượt quá hạn mức rút tiền tối đa cho phép trong ngày",
                )

        withdrawal_id = str(uuid7())
        try:
            deduct_result = await mongo.update_one("wallets", 
                {"_id": str(current_user.id), "balance": {"$gte": amount}},
                {"$inc": {"balance": -amount}},
                session=session,
            )
            if deduct_result.modified_count == 0:
                if should_close_session:
                    await session.abort_transaction()
                raise HTTPException(
                    status_code=400, detail="Số dư ví không đủ để thực hiện giao dịch rút tiền"
                )

            withdrawal_request = {
                "_id": withdrawal_id,
                "user_id": str(current_user.id),
                "amount": amount,
                "bank_info": bank_info,
                "status": "PENDING",
                "created_at": datetime.now(timezone.utc),
            }
            await mongo.insert_one("withdrawal_requests", 
                withdrawal_request, session=session
            )
            transaction = Transaction(
                user_id=str(current_user.id),
                amount=-amount,
                type=TransactionType.WITHDRAW,
                note="Funds temporarily reserved for pending withdrawal processing",
                reference_id=withdrawal_id,
            )
            await mongo.insert_one("transactions", 
                transaction.model_dump(by_alias=True), session=session
            )

            if should_close_session:
                await session.commit_transaction()

            logger.info("Withdrawal request successfully registered and pending review")
            return {
                "message": "Gửi yêu cầu khởi tạo giao dịch rút tiền hoàn tất",
                "withdrawal_id": withdrawal_id,
            }
        except HTTPException:
            raise
        except Exception as e:
            if should_close_session:
                await session.abort_transaction()
            logger.exception("Failed to initialize withdrawal transaction workflow")
            raise HTTPException(
                status_code=500, detail="Không thể xử lý yêu cầu rút tiền vào lúc này"
            )
        finally:
            if should_close_session:
                await session.end_session()

    @staticmethod
    @log_logic_execution
    async def get_withdrawal_queue(status: str = "pending", limit: int = 100) -> list:
        normalized_status = status.upper()
        if normalized_status not in ALLOWED_WITHDRAWAL_QUEUE_STATUSES:
            raise HTTPException(
                status_code=400, detail="Tham số trạng thái lọc giao dịch rút tiền không hợp lệ"
            )
        pipeline = [
            {"$match": {"status": normalized_status}},
            {"$sort": {"created_at": -1}},
            {"$limit": limit},
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
        withdrawal = (
            await mongo.aggregate(collection="withdrawal_requests", pipeline=pipeline).execute()
        )
        result = []
        for p in withdrawal:
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
    @log_logic_execution
    async def verify_withdrawal(
        withdrawal_id: str, action: str, current_user, session=None
    ) -> dict:
        should_close_session = False
        if session is None:
            session = await database.mongodb.start_session()
            session.start_transaction()
            should_close_session = True

        normalized_action = action.strip().lower()
        if normalized_action not in ALLOWED_WITHDRAWAL_ACTIONS:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(status_code=400, detail="Tham số hành động xác thực giao dịch không hợp lệ")

        withdrawal = await mongo.find_one(collection="withdrawal_requests", query={"_id": withdrawal_id})
        if not withdrawal:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy yêu cầu rút tiền khớp với mã giao dịch cung cấp",
            )

        if str(current_user.id) == withdrawal.get("user_id"):
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=403, detail="Hệ thống không cho phép người dùng tự phê duyệt yêu cầu rút tiền của chính mình"
            )

        current_status = withdrawal.get("status")
        if current_status != "PENDING":
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=400, detail="Yêu cầu rút tiền này đã được hệ thống xử lý trước đó"
            )

        status = "APPROVED" if normalized_action == "approve" else "REJECTED"

        try:
            update_result = await mongo.update_one("withdrawal_requests", 
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
                await mongo.update_one("wallets", 
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
                await mongo.insert_one("transactions", 
                    refund_transaction.model_dump(by_alias=True), session=session
                )

            bank_info = str(withdrawal.get("bank_info", ""))
            masked_bank = (
                bank_info[:4] + "***" + bank_info[-3:] if len(bank_info) > 8 else "***"
            )
            await mongo.insert_one("audit_logs", 
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

            logger.info("Administrative verification of withdrawal request completed successfully")
            return {"message": "Xử lý xác minh yêu cầu rút tiền hoàn tất"}
        except HTTPException:
            raise
        except Exception as e:
            if should_close_session:
                await session.abort_transaction()
            logger.exception("Failed to process administrative verification of withdrawal request")
            raise HTTPException(
                status_code=500, detail="Giao dịch thanh toán đang gặp sự cố gián đoạn"
            )
        finally:
            if should_close_session:
                await session.end_session()

    @staticmethod
    @log_logic_execution
    async def cancel_withdrawal(
        withdrawal_id: str, current_user, session=None
    ) -> dict:
        should_close_session = False
        if session is None:
            session = await database.mongodb.start_session()
            session.start_transaction()
            should_close_session = True

        withdrawal = await mongo.find_one("withdrawal_requests", 
            {"_id": withdrawal_id, "user_id": str(current_user.id)}
        )
        if not withdrawal:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy yêu cầu rút tiền khớp với mã giao dịch cung cấp",
            )
        if withdrawal.get("status") != "PENDING":
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=400, detail="Hệ thống chỉ hỗ trợ hủy các yêu cầu rút tiền đang ở trạng thái chờ xử lý"
            )

        try:
            update_result = await mongo.update_one("withdrawal_requests", 
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
                    status_code=400, detail="Không thể cập nhật trạng thái yêu cầu rút tiền"
                )

            await mongo.update_one("wallets", 
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
            await mongo.insert_one("transactions", 
                refund_transaction.model_dump(by_alias=True), session=session
            )

            if should_close_session:
                await session.commit_transaction()

            logger.info("Withdrawal request successfully cancelled and reserved funds restored")
            return {"message": "Hủy yêu cầu rút tiền và hoàn trả số dư hoàn tất"}
        except HTTPException:
            raise
        except Exception as e:
            if should_close_session:
                await session.abort_transaction()
            logger.exception("Failed to process cancellation of withdrawal request")
            raise HTTPException(
                status_code=500, detail="Giao dịch thanh toán đang gặp sự cố gián đoạn"
            )
        finally:
            if should_close_session:
                await session.end_session()
