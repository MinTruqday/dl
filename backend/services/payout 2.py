from core.database import db_client
from fastapi import HTTPException
from datetime import datetime
import uuid
from loguru import logger
from models.wallet import Transaction, TransactionType

ALLOWED_PAYOUT_QUEUE_STATUSES = {"PENDING", "APPROVED", "REJECTED", "CANCELLED"}
ALLOWED_PAYOUT_ACTIONS = {"approve", "reject"}

class PayoutService:
    @staticmethod
    async def request_payout(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        amount = int(data.get("amount", 0))
        bank_info = data.get("bank_info", {})
        
        if amount < 100000:
            raise HTTPException(status_code=400, detail="Số tiền rút tối thiểu là 100,000 dl.")

        wallet = await db["users"].find_one({"_id": str(current_user.id)})
        if not wallet or wallet.get("wallet_balance", 0) < amount:
            raise HTTPException(status_code=400, detail="Số dư không đủ để thực hiện yêu cầu rút tiền.")

        payout_id = str(uuid.uuid4())
        session = await db_client.mongodb.start_session()
        try:
            async with session.start_transaction():
                deduct_result = await db["users"].update_one(
                    {"_id": str(current_user.id), "wallet_balance": {"$gte": amount}},
                    {"$inc": {"wallet_balance": -amount}},
                    session=session
                )
                if deduct_result.modified_count == 0:
                    await session.abort_transaction()
                    raise HTTPException(status_code=400, detail="Số dư không đủ để thực hiện yêu cầu rút tiền.")

                payout_request = {
                    "_id": payout_id,
                    "user_id": str(current_user.id),
                    "amount": amount,
                    "bank_info": bank_info,
                    "status": "PENDING",
                    "created_at": datetime.utcnow()
                }
                await db["payout_requests"].insert_one(payout_request, session=session)

                transaction = Transaction(
                    user_id=str(current_user.id),
                    amount=-amount,
                    type=TransactionType.WITHDRAW,
                    note=f"Yêu cầu rút tiền {payout_id}",
                    reference_id=payout_id
                )
                await db["transactions"].insert_one(transaction.model_dump(by_alias=True), session=session)

                await session.commit_transaction()
                logger.info(f"Payout requested by user {current_user.id} for {amount} dl")
                return {"message": "Yêu cầu rút tiền đã được gửi thành công.", "payout_id": payout_id}
        except HTTPException:
            raise
        except Exception as e:
            await session.abort_transaction()
            logger.error(f"Payout request failed for user {current_user.id}: {e}")
            raise HTTPException(status_code=500, detail="Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.")
        finally:
            await session.end_session()

    @staticmethod
    async def get_payout_queue(status: str = "pending") -> list:
        db = db_client.mongodb.get_default_database()
        normalized_status = status.upper()
        if normalized_status not in ALLOWED_PAYOUT_QUEUE_STATUSES:
            raise HTTPException(status_code=400, detail="Trạng thái yêu cầu rút tiền không hợp lệ.")
        payouts = await db["payout_requests"].find({"status": normalized_status}).sort("created_at", -1).to_list(length=100)
        result = []
        for p in payouts:
            user = await db["users"].find_one({"_id": p.get("user_id")}, {"full_name": 1})
            result.append({
                "id": str(p["_id"]),
                "user_id": p.get("user_id"),
                "user_name": user.get("full_name") if user else "Unknown",
                "amount": p.get("amount"),
                "status": p.get("status"),
                "created_at": p["created_at"].isoformat() if isinstance(p.get("created_at"), datetime) else p.get("created_at")
            })
        return result

    @staticmethod
    async def verify_payout(payout_id: str, action: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        normalized_action = action.strip().lower()
        if normalized_action not in ALLOWED_PAYOUT_ACTIONS:
            raise HTTPException(status_code=400, detail="Hành động xử lý yêu cầu rút tiền không hợp lệ.")

        payout = await db["payout_requests"].find_one({"_id": payout_id})
        if not payout:
            raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu thanh toán.")

        current_status = payout.get("status")
        if current_status != "PENDING":
            raise HTTPException(status_code=400, detail="Yêu cầu rút tiền đã được xử lý trước đó.")

        status = "APPROVED" if normalized_action == "approve" else "REJECTED"
        session = await db_client.mongodb.start_session()
        try:
            async with session.start_transaction():
                await db["payout_requests"].update_one(
                    {"_id": payout_id, "status": "PENDING"},
                    {"$set": {"status": status, "processed_by": str(current_moderator.id), "processed_at": datetime.utcnow()}},
                    session=session
                )

                if status == "REJECTED":
                    await db["users"].update_one(
                        {"_id": payout.get("user_id")},
                        {"$inc": {"wallet_balance": payout.get("amount", 0)}},
                        session=session
                    )
                    refund_transaction = Transaction(
                        user_id=payout.get("user_id"),
                        amount=payout.get("amount", 0),
                        type=TransactionType.TOPUP,
                        note=f"Hoàn tiền yêu cầu rút tiền {payout_id}",
                        reference_id=payout_id
                    )
                    await db["transactions"].insert_one(refund_transaction.model_dump(by_alias=True), session=session)

                await db["audit_logs"].insert_one({
                    "action": f"PAYOUT_{status}",
                    "actor_id": str(current_moderator.id),
                    "payout_id": payout_id,
                    "timestamp": datetime.utcnow()
                }, session=session)

                await session.commit_transaction()
                logger.info(f"Audit: Payout {payout_id} {status} by moderator {current_moderator.id}")
                return {"message": f"Đã {status.lower()} yêu cầu rút tiền thành công."}
        except HTTPException:
            raise
        except Exception as e:
            await session.abort_transaction()
            logger.error(f"Verify payout failed for {payout_id}: {e}")
            raise HTTPException(status_code=500, detail="Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.")
        finally:
            await session.end_session()

    @staticmethod
    async def cancel_payout(payout_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        payout = await db["payout_requests"].find_one({"_id": payout_id, "user_id": str(current_user.id)})
        if not payout:
            raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu rút tiền.")
        if payout.get("status") != "PENDING":
            raise HTTPException(status_code=400, detail="Chỉ có thể hủy yêu cầu đang chờ xử lý.")

        session = await db_client.mongodb.start_session()
        try:
            async with session.start_transaction():
                await db["payout_requests"].update_one(
                    {"_id": payout_id, "user_id": str(current_user.id), "status": "PENDING"},
                    {"$set": {"status": "CANCELLED", "cancelled_at": datetime.utcnow()}},
                    session=session
                )
                await db["users"].update_one(
                    {"_id": str(current_user.id)},
                    {"$inc": {"wallet_balance": payout.get("amount", 0)}},
                    session=session
                )
                refund_transaction = Transaction(
                    user_id=str(current_user.id),
                    amount=payout.get("amount", 0),
                    type=TransactionType.TOPUP,
                    note=f"Hủy yêu cầu rút tiền {payout_id}",
                    reference_id=payout_id
                )
                await db["transactions"].insert_one(refund_transaction.model_dump(by_alias=True), session=session)
                await session.commit_transaction()
                logger.info(f"Payout {payout_id} cancelled by user {current_user.id}")
                return {"message": "Đã hủy yêu cầu rút tiền thành công."}
        except HTTPException:
            raise
        except Exception as e:
            await session.abort_transaction()
            logger.error(f"Cancel payout failed for {payout_id}: {e}")
            raise HTTPException(status_code=500, detail="Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.")
        finally:
            await session.end_session()

    @staticmethod
    async def get_my_payouts(current_user) -> list:
        db = db_client.mongodb.get_default_database()
        payouts = await db["payout_requests"].find(
            {"user_id": str(current_user.id)}
        ).sort("created_at", -1).to_list(length=100)
        return payouts
