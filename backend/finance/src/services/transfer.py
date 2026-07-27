from datetime import datetime, timezone
import hashlib
from typing import Dict, Any
from fastapi import HTTPException
from loguru import logger
from uuid6 import uuid7

from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
from src.core.infrastructure.redis import redis
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings
from src.schemas.wallet import TransferRequest, TransactionType

class TransferService:

    @staticmethod
    @log_logic_execution
    async def verify_recipient(identifier: str) -> Dict[str, Any]:
        identifier_clean = identifier.strip()
        humanity_db = database.mongodb[settings.HUMANITY_DB_NAME]
        
        recipient = await humanity_db.users.find_one({
            "$or": [
                {"_id": identifier_clean},
                {"email": identifier_clean},
                {"slug": identifier_clean},
                {"account_number": identifier_clean}
            ]
        })

        if not recipient:
            raise HTTPException(status_code=404, detail="Không tìm thấy người nhận với thông tin đã cung cấp")

        recipient_id = str(recipient["_id"])
        full_name = recipient.get("full_name") or recipient.get("email") or recipient_id
        email = recipient.get("email", "")

        return {
            "recipient_id": recipient_id,
            "full_name": full_name,
            "email": email,
            "slug": recipient.get("slug", ""),
            "account_number": recipient.get("account_number", f"DL-{recipient_id[:8].upper()}")
        }

    @staticmethod
    @log_logic_execution
    async def transfer_funds(sender_user, req: TransferRequest) -> Dict[str, Any]:
        sender_id = str(sender_user.id)
        amount = req.amount
        identifier = req.recipient_identifier.strip()

        if amount <= 0:
            raise HTTPException(status_code=400, detail="Số tiền chuyển phải lớn hơn 0")

        idempotency_raw = req.idempotency_key or f"{sender_id}:{identifier}:{amount}:{req.note}"
        idempotency_hash = hashlib.sha256(idempotency_raw.encode()).hexdigest()[:16]
        lock_key = f"lock:transfer:{sender_id}:{idempotency_hash}"

        try:
            acquired = await redis.get_client().set(lock_key, "1", nx=True, ex=10)
            if not acquired:
                raise HTTPException(
                    status_code=409,
                    detail="Yêu cầu chuyển tiền trùng lặp đang được xử lý. Vui lòng chờ vài giây"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning("Redis idempotency lock bypass fallback")

        recipient_info = await TransferService.verify_recipient(identifier)
        recipient_id = recipient_info["recipient_id"]
        recipient_name = recipient_info["full_name"]

        if sender_id == recipient_id:
            raise HTTPException(status_code=400, detail="Bạn không thể tự chuyển tiền cho chính mình")

        sender_wallet = await mongo.find_one(collection="wallets", query={"_id": sender_id})
        sender_balance = sender_wallet.get("balance", 0) if sender_wallet else 0

        if sender_balance < amount:
            raise HTTPException(status_code=400, detail=f"Số dư tài khoản không đủ. Số dư hiện tại: {sender_balance} dl")

        now = datetime.now(timezone.utc)
        note_text = req.note.strip() if req.note else "Chuyển tiền nội bộ"

        await mongo.get_db()["wallets"].update_one(
            {"_id": sender_id},
            {
                "$inc": {"balance": -amount},
                "$set": {"updated_at": now}
            },
            upsert=True
        )

        await mongo.get_db()["wallets"].update_one(
            {"_id": recipient_id},
            {
                "$inc": {"balance": amount},
                "$set": {"updated_at": now}
            },
            upsert=True
        )

        sender_tx_id = str(uuid7())
        sender_tx = {
            "_id": sender_tx_id,
            "user_id": sender_id,
            "type": TransactionType.TRANSFER.value,
            "amount": -amount,
            "reference_id": recipient_id,
            "note": f"Chuyển {amount} dl cho {recipient_name}. Ghi chú: {note_text}",
            "created_at": now
        }
        await mongo.insert_one(collection="transactions", doc=sender_tx)

        sender_name = getattr(sender_user, "full_name", None) or getattr(sender_user, "email", None) or sender_id
        recipient_tx_id = str(uuid7())
        recipient_tx = {
            "_id": recipient_tx_id,
            "user_id": recipient_id,
            "type": TransactionType.RECEIVE.value,
            "amount": amount,
            "reference_id": sender_id,
            "note": f"Nhận {amount} dl từ {sender_name}. Ghi chú: {note_text}",
            "created_at": now
        }
        await mongo.insert_one(collection="transactions", doc=recipient_tx)

        outbox_doc = {
            "_id": str(uuid7()),
            "type": "p2p_transfer_completed",
            "payload": {
                "sender_id": sender_id,
                "recipient_id": recipient_id,
                "amount": amount,
                "note": note_text,
                "timestamp": now.isoformat()
            },
            "status": "pending",
            "created_at": now
        }
        await mongo.insert_one(collection="outbox", doc=outbox_doc)

        logger.info(f"P2P Transfer completed: {sender_id} -> {recipient_id} | Amount: {amount} dl")

        new_sender_wallet = await mongo.find_one(collection="wallets", query={"_id": sender_id})
        new_balance = new_sender_wallet.get("balance", 0) if new_sender_wallet else 0

        return {
            "transaction_id": sender_tx_id,
            "recipient": recipient_info,
            "amount_transferred": amount,
            "remaining_balance": new_balance,
            "note": note_text,
            "transferred_at": now.isoformat()
        }
