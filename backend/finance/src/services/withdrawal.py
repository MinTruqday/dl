from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from uuid6 import uuid7
import httpx
from loguru import logger
from src.core.dependency import Tier
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.logic_logger import log_logic_execution
from src.schemas.wallet import Transaction, TransactionType
from src.services.deposit import DepositService


ALLOWED_WITHDRAWAL_QUEUE_STATUSES = {"PENDING", "APPROVED", "REJECTED", "CANCELLED"}


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
        auth_db = database.mongodb[settings.AUTHENTICATION_DB_NAME]
        credential = await auth_db.auth_credentials.find_one(
            {"_id": user_id},
            {"last_password_change": 1},
        )
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
                        "status": {"$in": ["PENDING", "APPROVED"]},
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

        AUTO_PAYOUT_THRESHOLD_DL = 500_000
        is_auto_payout = amount < AUTO_PAYOUT_THRESHOLD_DL
        initial_status = "APPROVED" if is_auto_payout else "PENDING"

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
                        "status": initial_status,
                        "auto_payout": is_auto_payout,
                        "created_at": now,
                    },
                    session=session,
                )
                transaction = Transaction(
                    user_id=user_id,
                    amount=-total_deduction,
                    type=TransactionType.WITHDRAW,
                    note=f"Rút {amount} dl về ngân hàng qua Napas 24/7 (Phí thuế {tax_percent}%: {tax_amount} dl - Status: {initial_status})",
                    reference_id=withdrawal_id,
                )
                await db.transactions.insert_one(
                    transaction.model_dump(by_alias=True),
                    session=session,
                )

        if is_auto_payout and settings.PAYOS_CLIENT_ID and settings.PAYOS_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=15.0) as http_client:
                    bank_info_obj = data.get("bank_info", {})
                    payout_data = {
                        "accountNumber": bank_info_obj.get("account_number", ""),
                        "bankCode": bank_info_obj.get("bank_code", "VCB"),
                        "amount": amount,
                        "description": f"DocLib rut tien tu dong {withdrawal_id[:8]}"
                    }
                    signature = DepositService._generate_payos_signature(payout_data)
                    payout_headers = {
                        "x-client-id": settings.PAYOS_CLIENT_ID,
                        "x-api-key": settings.PAYOS_API_KEY,
                        "x-signature": signature
                    }
                    resp = await http_client.post("https://api-merchant.payos.vn/v2/payouts", json=payout_data, headers=payout_headers)
                    if resp.status_code == 200:
                        logger.info(f"Instant Auto-Payout executed successfully for withdrawal {withdrawal_id}")
                    else:
                        logger.warning(f"Instant Auto-Payout response code {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.error(f"Instant Auto-Payout API integration error: {e}")

        if is_auto_payout:
            msg = f"Hệ thống đã tự động duyệt và chuyển {amount} dl về tài khoản ngân hàng của bạn qua Napas 24/7!"
        else:
            msg = f"Yêu cầu rút tiền {amount} dl đã được ghi nhận và đang chờ Admin duyệt an toàn (do vượt hạn mức tự động 500.000 dl)"

        return {"message": msg, "withdrawal_id": withdrawal_id, "status": initial_status, "auto_payout": is_auto_payout}

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
        profiles = await database.mongodb[settings.HUMANITY_DB_NAME].users.find(
            {"_id": {"$in": user_ids}},
            {"full_name": 1},
        ).to_list(length=None)
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
        if normalized_action not in {"approve", "reject"}:
            raise HTTPException(status_code=400, detail="Hành động xử lý không hợp lệ")
        if normalized_action == "reject" and len(reason.strip()) < 5:
            raise HTTPException(status_code=400, detail="Lý do từ chối phải có ít nhất 5 ký tự")
        db = WithdrawalService._finance_db()
        withdrawal = await db.withdrawal_requests.find_one({"_id": withdrawal_id})
        if not withdrawal:
            raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu rút tiền")
        if withdrawal["user_id"] == str(current_user.id):
            raise HTTPException(status_code=403, detail="Không thể tự xử lý yêu cầu rút tiền của chính mình")
        new_status = "APPROVED" if normalized_action == "approve" else "REJECTED"
        async with await database.mongodb.start_session() as session:
            async with session.start_transaction():
                update = await db.withdrawal_requests.update_one(
                    {"_id": withdrawal_id, "status": "PENDING"},
                    {
                        "$set": {
                            "status": new_status,
                            "processed_by": str(current_user.id),
                            "processed_at": datetime.now(timezone.utc),
                            "rejection_reason": reason.strip() if new_status == "REJECTED" else None,
                        }
                    },
                    session=session,
                )
                if update.modified_count != 1:
                    raise HTTPException(status_code=409, detail="Yêu cầu rút tiền đã được xử lý")
                if new_status == "REJECTED":
                    await db.wallets.update_one(
                        {"_id": withdrawal["user_id"]},
                        {
                            "$inc": {
                                "balance": withdrawal["amount"],
                                "withdrawable_balance": withdrawal["amount"],
                            }
                        },
                        session=session,
                    )
                    refund = Transaction(
                        user_id=withdrawal["user_id"],
                        amount=withdrawal["amount"],
                        type=TransactionType.REFUND,
                        note="Reserved withdrawal funds restored after rejection",
                        reference_id=withdrawal_id,
                    )
                    await db.transactions.insert_one(
                        refund.model_dump(by_alias=True),
                        session=session,
                    )
                bank_info = str(withdrawal["bank_info"])
                masked_bank = bank_info[:4] + "***" + bank_info[-3:] if len(bank_info) > 8 else "***"

                if new_status == "APPROVED" and settings.PAYOS_CLIENT_ID and settings.PAYOS_API_KEY:
                    try:
                        async with httpx.AsyncClient(timeout=15.0) as http_client:
                            payout_data = {
                                "accountNumber": withdrawal.get("bank_info", {}).get("account_number", ""),
                                "bankCode": withdrawal.get("bank_info", {}).get("bank_code", ""),
                                "amount": withdrawal["amount"],
                                "description": f"DocLib rut tien {withdrawal_id[:8]}"
                            }
                            signature = DepositService._generate_payos_signature(payout_data)
                            payout_headers = {
                                "x-client-id": settings.PAYOS_CLIENT_ID,
                                "x-api-key": settings.PAYOS_API_KEY,
                                "x-signature": signature
                            }
                            resp = await http_client.post("https://api-merchant.payos.vn/v2/payouts", json=payout_data, headers=payout_headers)
                            if resp.status_code == 200:
                                logger.info(f"PayOS Payout Gateway executed successfully for withdrawal {withdrawal_id}")
                            else:
                                logger.warning(f"PayOS Payout response code {resp.status_code}: {resp.text}")
                    except Exception as e:
                        logger.error(f"PayOS Payout API integration error: {e}")

                await db.audit_logs.insert_one(
                    {
                        "action": f"WITHDRAWAL_{new_status}",
                        "actor_id": str(current_user.id),
                        "withdrawal_id": withdrawal_id,
                        "bank_info_masked": masked_bank,
                        "reason": reason.strip(),
                        "timestamp": datetime.now(timezone.utc),
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
                await db.wallets.update_one(
                    {"_id": user_id},
                    {
                        "$inc": {
                            "balance": withdrawal["amount"],
                            "withdrawable_balance": withdrawal["amount"],
                        }
                    },
                    session=session,
                )
                refund = Transaction(
                    user_id=user_id,
                    amount=withdrawal["amount"],
                    type=TransactionType.REFUND,
                    note="Reserved withdrawal funds restored after cancellation",
                    reference_id=withdrawal_id,
                )
                await db.transactions.insert_one(
                    refund.model_dump(by_alias=True),
                    session=session,
                )
        return {"message": "Hủy yêu cầu rút tiền hoàn tất"}
