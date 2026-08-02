from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from uuid6 import uuid7

from src.core.dependency import Tier
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.logic_logger import log_logic_execution
from src.schemas.wallet import Transaction, TransactionType
from src.services.authentication_client import AuthenticationClient
from src.services.humanity_client import HumanityClient


ALLOWED_WITHDRAWAL_QUEUE_STATUSES = {
    "PENDING",
    "APPROVED",
    "COMPLETED",
    "REJECTED",
    "CANCELLED",
}


class WithdrawalService:
    @staticmethod
    def _finance_db():
        return database.mongodb[settings.FINANCE_DB_NAME]

    @staticmethod
    @log_logic_execution
    async def get_revenue(current_user):
        db = WithdrawalService._finance_db()
        user_id = str(current_user.id)
        rows = await db.transactions.aggregate(
            [
                {"$match": {"user_id": user_id, "type": {"$in": ["receive", "tip"]}}},
                {"$group": {"_id": None, "total_revenue": {"$sum": "$amount"}}},
            ]
        ).to_list(length=None)
        pending_rows = await db.withdrawal_requests.aggregate(
            [
                {"$match": {"user_id": user_id, "status": "PENDING"}},
                {"$group": {"_id": None, "pending": {"$sum": "$amount"}}},
            ]
        ).to_list(length=None)
        wallet = await db.wallets.find_one({"_id": user_id})
        return {
            "total_revenue": rows[0]["total_revenue"] if rows else 0,
            "pending_withdrawal": pending_rows[0]["pending"] if pending_rows else 0,
            "withdrawable_balance": wallet.get("withdrawable_balance", 0) if wallet else 0,
            "currency": "dl",
        }

    @staticmethod
    @log_logic_execution
    async def request_withdrawal(data: dict, current_user) -> dict:
        db = WithdrawalService._finance_db()
        user_id = str(current_user.id)
        amount = int(data["amount"])
        wallet = await db.wallets.find_one({"_id": user_id})
        if not wallet or min(
            int(wallet.get("balance", 0)),
            int(wallet.get("withdrawable_balance", 0)),
        ) < amount:
            raise HTTPException(status_code=400, detail="Số dư doanh thu khả dụng không đủ để rút tiền")

        now = datetime.now(timezone.utc)
        credential = await AuthenticationClient.security_state(user_id)
        last_password_change = credential.get("last_password_change") if credential else None
        if isinstance(last_password_change, datetime):
            if last_password_change.tzinfo is None:
                last_password_change = last_password_change.replace(tzinfo=timezone.utc)
            if (now - last_password_change).total_seconds() < 86400:
                raise HTTPException(status_code=403, detail="Rút tiền tạm khóa trong 24 giờ sau khi đổi mật khẩu")

        last_bank_update = wallet.get("last_bank_update")
        if isinstance(last_bank_update, datetime):
            if last_bank_update.tzinfo is None:
                last_bank_update = last_bank_update.replace(tzinfo=timezone.utc)
            if (now - last_bank_update).total_seconds() < 86400:
                raise HTTPException(status_code=403, detail="Rút tiền tạm khóa trong 24 giờ sau khi đổi tài khoản ngân hàng")

        user_tier_val = getattr(current_user, "ai_tier", Tier.BASIC.value)
        if hasattr(user_tier_val, "value"):
            user_tier_val = user_tier_val.value
        user_tier_val = str(user_tier_val).upper()

        max_weekly_withdrawals = 7 if user_tier_val == Tier.PREMIUM.value else 5 if user_tier_val == Tier.PRO.value else 3

        days_since_monday = now.weekday()
        week_start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)

        weekly_rows = await db.withdrawal_requests.aggregate(
            [
                {
                    "$match": {
                        "user_id": user_id,
                        "created_at": {"$gte": week_start},
                        "status": {"$in": ["PENDING", "APPROVED", "COMPLETED"]},
                    }
                },
                {"$group": {"_id": None, "count": {"$sum": 1}}},
            ]
        ).to_list(length=None)

        weekly_count = weekly_rows[0]["count"] if weekly_rows else 0
        if weekly_count >= max_weekly_withdrawals:
            raise HTTPException(
                status_code=429,
                detail=f"Đã đạt giới hạn rút tiền hàng tuần ({max_weekly_withdrawals} lượt/tuần cho gói {user_tier_val})"
            )

        tax_percent = weekly_count + 1
        tax_amount = int(round(amount * (tax_percent / 100.0)))
        total_deduction = amount + tax_amount

        wallet_bal = int(wallet.get("balance", 0)) if wallet else 0
        wallet_withdrawable = int(wallet.get("withdrawable_balance", 0)) if wallet else 0

        if wallet_bal < total_deduction or wallet_withdrawable < total_deduction:
            raise HTTPException(
                status_code=400,
                detail=f"Số dư khả dụng không đủ chi trả khoản rút {amount} dl cộng phí thuế {tax_amount} dl ({tax_percent}% cho lượt thứ {tax_percent} trong tuần). Tổng trừ: {total_deduction} dl"
            )

        withdrawal_id = str(uuid7())
        async with await database.mongodb.start_session() as session:
            async with session.start_transaction():
                deduction = await db.wallets.update_one(
                    {
                        "_id": user_id,
                        "balance": {"$gte": total_deduction},
                        "withdrawable_balance": {"$gte": total_deduction},
                    },
                    {"$inc": {"balance": -total_deduction, "withdrawable_balance": -total_deduction}},
                    session=session,
                )
                if deduction.modified_count != 1:
                    raise HTTPException(status_code=409, detail="Số dư đã thay đổi, vui lòng kiểm tra lại")
                await db.withdrawal_requests.insert_one(
                    {
                        "_id": withdrawal_id,
                        "user_id": user_id,
                        "amount": amount,
                        "tax_amount": tax_amount,
                        "tax_percent": tax_percent,
                        "total_deducted": total_deduction,
                        "bank_info": data["bank_info"],
                        "note": data.get("note"),
                        "status": "PENDING",
                        "created_at": now,
                    },
                    session=session,
                )
                transaction = Transaction(
                    user_id=user_id,
                    amount=-total_deduction,
                    type=TransactionType.WITHDRAW,
                    note=f"Giữ {total_deduction} dl cho yêu cầu rút tiền, gồm {amount} dl và phí {tax_amount} dl",
                    reference_id=withdrawal_id,
                )
                await db.transactions.insert_one(
                    transaction.model_dump(by_alias=True),
                    session=session,
                )

        return {
            "message": f"Yêu cầu rút tiền {amount} dl đang chờ xác minh",
            "withdrawal_id": withdrawal_id,
            "status": "PENDING",
        }

    @staticmethod
    @log_logic_execution
    async def get_withdrawal_queue(status: str = "PENDING", limit: int = 100) -> list:
        normalized_status = status.upper()
        if normalized_status not in ALLOWED_WITHDRAWAL_QUEUE_STATUSES:
            raise HTTPException(status_code=400, detail="Trạng thái giao dịch rút tiền không hợp lệ")
        db = WithdrawalService._finance_db()
        rows = await db.withdrawal_requests.find(
            {"status": normalized_status}
        ).sort("created_at", -1).limit(limit).to_list(length=None)
        user_ids = list({row["user_id"] for row in rows})
        profiles = await HumanityClient.get_many(user_ids) or []
        names = {str(profile["_id"]): profile.get("full_name", "Unknown") for profile in profiles}
        return [
            {
                "_id": str(row["_id"]),
                "user_id": row["user_id"],
                "user_name": names.get(row["user_id"], "Unknown"),
                "amount": row["amount"],
                "status": row["status"],
                "bank_info": row["bank_info"],
                "note": row.get("note"),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    @staticmethod
    @log_logic_execution
    async def verify_withdrawal(
        withdrawal_id: str,
        action: str,
        reason: str,
        current_user,
    ) -> dict:
        normalized_action = action.lower()
        if normalized_action not in {"approve", "reject", "complete"}:
            raise HTTPException(status_code=400, detail="Hành động xử lý không hợp lệ")
        reason_value = reason.strip()
        if normalized_action in {"reject", "complete"} and len(reason_value) < 5:
            detail = (
                "Lý do từ chối phải có ít nhất 5 ký tự"
                if normalized_action == "reject"
                else "Mã đối soát phải có ít nhất 5 ký tự"
            )
            raise HTTPException(status_code=400, detail=detail)
        db = WithdrawalService._finance_db()
        withdrawal = await db.withdrawal_requests.find_one({"_id": withdrawal_id})
        if not withdrawal:
            raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu rút tiền")
        if withdrawal["user_id"] == str(current_user.id):
            raise HTTPException(status_code=403, detail="Không thể tự xử lý yêu cầu rút tiền của chính mình")
        new_status = {
            "approve": "APPROVED",
            "reject": "REJECTED",
            "complete": "COMPLETED",
        }[normalized_action]
        expected_status = "APPROVED" if new_status == "COMPLETED" else "PENDING"
        now = datetime.now(timezone.utc)
        update_fields = {
            "status": new_status,
            "processed_by": str(current_user.id),
            "processed_at": now,
        }
        if new_status == "REJECTED":
            update_fields["rejection_reason"] = reason_value
        if new_status == "COMPLETED":
            update_fields["completed_at"] = now
            update_fields["payout_reference"] = reason_value
        async with await database.mongodb.start_session() as session:
            async with session.start_transaction():
                update = await db.withdrawal_requests.update_one(
                    {"_id": withdrawal_id, "status": expected_status},
                    {"$set": update_fields},
                    session=session,
                )
                if update.modified_count != 1:
                    raise HTTPException(status_code=409, detail="Yêu cầu rút tiền đã được xử lý")
                if new_status == "REJECTED":
                    refund_amount = int(
                        withdrawal.get("total_deducted", withdrawal["amount"])
                    )
                    await db.wallets.update_one(
                        {"_id": withdrawal["user_id"]},
                        {
                            "$inc": {
                                "balance": refund_amount,
                                "withdrawable_balance": refund_amount,
                            }
                        },
                        session=session,
                    )
                    refund = Transaction(
                        user_id=withdrawal["user_id"],
                        amount=refund_amount,
                        type=TransactionType.REFUND,
                        note="Reserved withdrawal funds restored after rejection",
                        reference_id=withdrawal_id,
                    )
                    await db.transactions.insert_one(
                        refund.model_dump(by_alias=True),
                        session=session,
                    )
                bank_info = withdrawal.get("bank_info", {})
                account_number = (
                    str(bank_info.get("account_number", ""))
                    if isinstance(bank_info, dict)
                    else str(bank_info)
                )
                masked_bank = (
                    account_number[:3] + "***" + account_number[-3:]
                    if len(account_number) > 8
                    else "***"
                )
                await db.audit_logs.insert_one(
                    {
                        "action": f"WITHDRAWAL_{new_status}",
                        "actor_id": str(current_user.id),
                        "withdrawal_id": withdrawal_id,
                        "bank_info_masked": masked_bank,
                        "reason": reason_value,
                        "timestamp": now,
                    },
                    session=session,
                )
        return {"message": "Xử lý yêu cầu rút tiền hoàn tất", "status": new_status}

    @staticmethod
    @log_logic_execution
    async def cancel_withdrawal(withdrawal_id: str, current_user) -> dict:
        db = WithdrawalService._finance_db()
        user_id = str(current_user.id)
        withdrawal = await db.withdrawal_requests.find_one(
            {"_id": withdrawal_id, "user_id": user_id, "status": "PENDING"}
        )
        if not withdrawal:
            raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu rút tiền đang chờ xử lý")
        async with await database.mongodb.start_session() as session:
            async with session.start_transaction():
                update = await db.withdrawal_requests.update_one(
                    {"_id": withdrawal_id, "user_id": user_id, "status": "PENDING"},
                    {"$set": {"status": "CANCELLED", "cancelled_at": datetime.now(timezone.utc)}},
                    session=session,
                )
                if update.modified_count != 1:
                    raise HTTPException(status_code=409, detail="Yêu cầu rút tiền đã được xử lý")
                refund_amount = int(
                    withdrawal.get("total_deducted", withdrawal["amount"])
                )
                await db.wallets.update_one(
                    {"_id": user_id},
                    {
                        "$inc": {
                            "balance": refund_amount,
                            "withdrawable_balance": refund_amount,
                        }
                    },
                    session=session,
                )
                refund = Transaction(
                    user_id=user_id,
                    amount=refund_amount,
                    type=TransactionType.REFUND,
                    note="Reserved withdrawal funds restored after cancellation",
                    reference_id=withdrawal_id,
                )
                await db.transactions.insert_one(
                    refund.model_dump(by_alias=True),
                    session=session,
                )
        return {"message": "Hủy yêu cầu rút tiền hoàn tất"}
