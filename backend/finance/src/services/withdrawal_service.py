from datetime import datetime, timezone

from core.config import settings
from core.database import db_client
from fastapi import HTTPException
from loguru import logger
from src.schemas.wallet_schema import Transaction, TransactionType
from uuid6 import uuid7

ALLOWED_WITHDRAWAL_QUEUE_STATUSES = {"PENDING", "APPROVED", "REJECTED", "CANCELLED"}
ALLOWED_WITHDRAWAL_ACTIONS = {"approve", "reject"}


class WithdrawalService:

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
                status_code=400, detail="The requested withdrawal amount falls below the minimum required processing threshold"
            )

        wallet = await db["wallets"].find_one({"_id": str(current_user.id)})
        if not wallet or wallet.get("balance", 0) < amount:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(status_code=400, detail="The requested withdrawal cannot proceed due to insufficient available funds in the account balance")

        now = datetime.now(timezone.utc)

        user_info = {}
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.PROVISION_URL}/users/{current_user.id}",
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                if resp.status_code == 200:
                    user_info = resp.json().get("data") or {}
        except Exception:
            logger.warning("The system encountered a minor disruption while synchronizing external account profile information")

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
                    detail="Financial withdrawals are temporarily restricted for security purposes following a recent password modification",
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
                    detail="Financial withdrawals are temporarily restricted for security purposes following a recent update to the linked banking information",
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
                    status_code=429, detail="The account has exceeded the maximum permissible number of daily withdrawal requests"
                )
            if stats["total_amount"] + amount > 20000000:
                if should_close_session:
                    await session.abort_transaction()
                    await session.end_session()
                raise HTTPException(
                    status_code=429,
                    detail="The requested amount exceeds the maximum permissible daily withdrawal limit",
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
                    status_code=400, detail="The requested withdrawal cannot proceed due to insufficient available funds in the account balance"
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

            logger.info(
                "The withdrawal request has been successfully registered and the corresponding funds have been securely reserved"
            )
            return {
                "message": "The withdrawal request has been successfully submitted and is currently pending processing",
                "withdrawal_id": withdrawal_id,
            }
        except HTTPException:
            raise
        except Exception:
            if should_close_session:
                await session.abort_transaction()
            logger.error("An unexpected structural or network failure occurred while attempting to initiate the withdrawal transaction")
            raise HTTPException(status_code=500, detail="The financial service is currently experiencing technical difficulties and cannot process the withdrawal request")
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
                status_code=400, detail="The requested withdrawal status filter is not recognized by the system"
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
        withdrawal_id: str, action: str, current_moderator, db=None, session=None
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
            raise HTTPException(
                status_code=400, detail="The provided administrative action code is not recognized by the transaction verification system"
            )

        withdrawal = await db["withdrawal_requests"].find_one({"_id": withdrawal_id})
        if not withdrawal:
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=404, detail="The system was unable to locate a withdrawal request matching the provided transaction identifier"
            )

        if str(current_moderator.id) == withdrawal.get("user_id"):
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=403, detail="Administrative policies restrict accounts from verifying their own withdrawal requests"
            )

        current_status = withdrawal.get("status")
        if current_status != "PENDING":
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=400, detail="The specified withdrawal request has already been processed by the administrative team and cannot be modified"
            )

        status = "APPROVED" if normalized_action == "approve" else "REJECTED"

        try:
            update_result = await db["withdrawal_requests"].update_one(
                {"_id": withdrawal_id, "status": "PENDING"},
                {
                    "$set": {
                        "status": status,
                        "processed_by": str(current_moderator.id),
                        "processed_at": datetime.now(timezone.utc),
                    }
                },
                session=session,
            )
            if update_result.modified_count == 0:
                if should_close_session:
                    await session.abort_transaction()
                raise HTTPException(
                    status_code=400, detail="The database engine encountered an issue while attempting to update the status of the withdrawal request"
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
                    "actor_id": str(current_moderator.id),
                    "withdrawal_id": withdrawal_id,
                    "bank_info_masked": masked_bank,
                    "timestamp": datetime.now(timezone.utc),
                },
                session=session,
            )

            if should_close_session:
                await session.commit_transaction()

            logger.info(
                "The withdrawal request has been officially verified and its status has been successfully updated"
            )
            return {"message": "The administrative verification process for the specified withdrawal request has been completed successfully"}
        except HTTPException:
            raise
        except Exception:
            if should_close_session:
                await session.abort_transaction()
            logger.error("An unexpected error occurred while attempting to process the verification of the withdrawal request")
            raise HTTPException(status_code=500, detail="The financial service is currently experiencing technical difficulties and cannot process the request")
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
                status_code=404, detail="The system was unable to locate a withdrawal request matching the provided transaction identifier"
            )
        if withdrawal.get("status") != "PENDING":
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            raise HTTPException(
                status_code=400, detail="The system restricts cancellation operations to withdrawal requests that are currently in a pending state"
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
                    status_code=400, detail="The database engine encountered an issue while attempting to update the status of the withdrawal request"
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

            logger.info(
                "The pending withdrawal request has been successfully cancelled by the account owner and funds have been restored"
            )
            return {"message": "The pending withdrawal request has been successfully cancelled and the reserved funds have been refunded"}
        except HTTPException:
            raise
        except Exception:
            if should_close_session:
                await session.abort_transaction()
            logger.error("An unexpected system error occurred while attempting to cancel the active withdrawal request")
            raise HTTPException(status_code=500, detail="The financial service is currently experiencing technical difficulties and cannot process the request")
        finally:
            if should_close_session:
                await session.end_session()