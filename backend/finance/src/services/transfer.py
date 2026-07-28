import asyncio
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import HTTPException
from loguru import logger
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.infrastructure.mongo import mongo
from src.core.infrastructure.redis import redis
from src.core.logic_logger import log_logic_execution
from src.schemas.wallet import TransactionType, TransferRequest


class TransferService:
    @staticmethod
    @log_logic_execution
    async def verify_recipient(identifier: str) -> Dict[str, Any]:
        value = identifier.strip()
        recipient = await database.mongodb[settings.HUMANITY_DB_NAME].users.find_one(
            {
                "$or": [
                    {"_id": value},
                    {"email": value},
                    {"slug": value},
                    {"account_number": value},
                ],
                "is_active": {"$ne": False},
            }
        )
        if not recipient:
            raise HTTPException(
                status_code=404,
                detail={"code": "transfer_recipient_not_found"},
            )
        recipient_id = str(recipient["_id"])
        return {
            "recipient_id": recipient_id,
            "full_name": recipient.get("full_name")
            or recipient.get("email")
            or recipient_id,
            "email": recipient.get("email", ""),
            "slug": recipient.get("slug", ""),
            "account_number": recipient.get(
                "account_number",
                f"DL-{recipient_id[:8].upper()}",
            ),
        }

    @staticmethod
    async def _release_lock(lock_key: str, lock_value: str):
        await redis.get_client().eval(
            "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end",
            1,
            lock_key,
            lock_value,
        )

    @staticmethod
    async def _wallet_has_marker(user_id: str, field: str, transfer_id: str) -> bool:
        wallet = await mongo.get_db().wallets.find_one(
            {"_id": user_id, field: transfer_id},
            {"_id": 1},
        )
        return wallet is not None

    @staticmethod
    async def _execute_transfer(transfer: Dict[str, Any]) -> Dict[str, Any]:
        transfer_id = transfer["_id"]
        sender_id = transfer["sender_id"]
        recipient_id = transfer["recipient_id"]
        amount = transfer["amount"]
        now = datetime.now(timezone.utc)
        wallets = mongo.get_db().wallets

        debited_wallet = await wallets.find_one_and_update(
            {
                "_id": sender_id,
                "balance": {"$gte": amount},
                "outgoing_transfer_ids": {"$ne": transfer_id},
            },
            {
                "$inc": {"balance": -amount},
                "$addToSet": {"outgoing_transfer_ids": transfer_id},
                "$set": {"updated_at": now},
            },
            return_document=ReturnDocument.AFTER,
        )
        if debited_wallet is None:
            already_debited = await TransferService._wallet_has_marker(
                sender_id,
                "outgoing_transfer_ids",
                transfer_id,
            )
            if not already_debited:
                wallet = await wallets.find_one({"_id": sender_id}, {"balance": 1})
                await mongo.get_db().transfers.update_one(
                    {"_id": transfer_id, "status": {"$ne": "completed"}},
                    {
                        "$set": {
                            "status": "failed",
                            "failure_code": "insufficient_balance",
                            "updated_at": now,
                        }
                    },
                )
                raise HTTPException(
                    status_code=409,
                    detail={
                        "code": "insufficient_balance",
                        "balance": int((wallet or {}).get("balance", 0)),
                    },
                )

        await mongo.get_db().transfers.update_one(
            {"_id": transfer_id, "status": {"$in": ["pending", "debited"]}},
            {"$set": {"status": "debited", "updated_at": now}},
        )

        try:
            await wallets.update_one(
                {
                    "_id": recipient_id,
                    "incoming_transfer_ids": {"$ne": transfer_id},
                },
                {
                    "$inc": {"balance": amount},
                    "$set": {"updated_at": now},
                    "$setOnInsert": {"withdrawable_balance": 0},
                    "$addToSet": {"incoming_transfer_ids": transfer_id},
                },
                upsert=True,
            )
        except DuplicateKeyError:
            if not await TransferService._wallet_has_marker(
                recipient_id,
                "incoming_transfer_ids",
                transfer_id,
            ):
                raise

        await mongo.get_db().transfers.update_one(
            {"_id": transfer_id, "status": {"$in": ["debited", "credited"]}},
            {"$set": {"status": "credited", "updated_at": now}},
        )

        transaction_rows = [
            {
                "_id": f"{transfer_id}:out",
                "user_id": sender_id,
                "type": TransactionType.TRANSFER_OUT.value,
                "amount": -amount,
                "reference_id": recipient_id,
                "note": transfer["note"],
                "created_at": transfer["created_at"],
            },
            {
                "_id": f"{transfer_id}:in",
                "user_id": recipient_id,
                "type": TransactionType.TRANSFER_IN.value,
                "amount": amount,
                "reference_id": sender_id,
                "note": transfer["note"],
                "created_at": transfer["created_at"],
            },
        ]
        for row in transaction_rows:
            await mongo.get_db().transactions.update_one(
                {"_id": row["_id"]},
                {"$setOnInsert": row},
                upsert=True,
            )

        await mongo.get_db().outbox_events.update_one(
            {"_id": f"transfer-notification:{transfer_id}"},
            {
                "$setOnInsert": {
                    "_id": f"transfer-notification:{transfer_id}",
                    "event_type": "notification",
                    "payload": {
                        "target_user_id": recipient_id,
                        "title": "Funds received",
                        "body": f"Received {amount} dl from {transfer['sender_name']}",
                        "type": "wallet_transfer",
                        "idempotency_key": f"transfer:{transfer_id}",
                    },
                    "status": "pending",
                    "attempts": 0,
                    "created_at": now,
                    "next_attempt_at": now,
                }
            },
            upsert=True,
        )

        remaining_wallet = await wallets.find_one({"_id": sender_id}, {"balance": 1})
        response = {
            "transaction_id": transfer_id,
            "recipient": transfer["recipient"],
            "amount_transferred": amount,
            "remaining_balance": int((remaining_wallet or {}).get("balance", 0)),
            "note": transfer["note"],
            "transferred_at": transfer["created_at"].isoformat(),
        }
        await mongo.get_db().transfers.update_one(
            {"_id": transfer_id},
            {
                "$set": {
                    "status": "completed",
                    "response": response,
                    "completed_at": now,
                    "updated_at": now,
                }
            },
        )
        return response

    @staticmethod
    @log_logic_execution
    async def transfer_funds(sender_user, req: TransferRequest) -> Dict[str, Any]:
        sender_id = str(sender_user.id)
        recipient = await TransferService.verify_recipient(
            req.recipient_identifier
        )
        recipient_id = recipient["recipient_id"]
        if sender_id == recipient_id:
            raise HTTPException(
                status_code=400,
                detail={"code": "self_transfer_not_allowed"},
            )

        fingerprint_source = (
            f"{sender_id}\n{recipient_id}\n{req.amount}\n{req.note.strip()}"
        )
        request_fingerprint = hashlib.sha256(
            fingerprint_source.encode()
        ).hexdigest()
        transfer_id = hashlib.sha256(
            f"{sender_id}\n{req.idempotency_key}".encode()
        ).hexdigest()
        lock_key = f"lock:transfer:{transfer_id}"
        lock_value = str(uuid7())
        try:
            acquired = await redis.get_client().set(
                lock_key,
                lock_value,
                nx=True,
                ex=30,
            )
        except Exception:
            logger.exception("Transfer lock service unavailable")
            raise HTTPException(
                status_code=503,
                detail={"code": "transfer_lock_unavailable"},
            )
        if not acquired:
            raise HTTPException(
                status_code=409,
                detail={"code": "transfer_in_progress"},
            )

        try:
            now = datetime.now(timezone.utc)
            transfer = {
                "_id": transfer_id,
                "sender_id": sender_id,
                "sender_name": getattr(sender_user, "full_name", None)
                or getattr(sender_user, "email", None)
                or sender_id,
                "recipient_id": recipient_id,
                "recipient": recipient,
                "amount": req.amount,
                "note": req.note.strip() or "Internal transfer",
                "idempotency_key": req.idempotency_key,
                "request_fingerprint": request_fingerprint,
                "status": "pending",
                "created_at": now,
                "updated_at": now,
            }
            try:
                await mongo.get_db().transfers.insert_one(transfer)
            except DuplicateKeyError:
                transfer = await mongo.get_db().transfers.find_one(
                    {"_id": transfer_id}
                )
                if transfer["request_fingerprint"] != request_fingerprint:
                    raise HTTPException(
                        status_code=409,
                        detail={"code": "idempotency_key_reused"},
                    )
                if transfer["status"] == "completed":
                    return transfer["response"]
                if transfer["status"] == "failed":
                    raise HTTPException(
                        status_code=409,
                        detail={"code": transfer["failure_code"]},
                    )
            return await TransferService._execute_transfer(transfer)
        finally:
            try:
                await TransferService._release_lock(lock_key, lock_value)
            except Exception:
                logger.exception("Transfer lock release failed")

    @staticmethod
    async def recover_pending_transfers():
        logger.info("Transfer recovery worker started")
        while True:
            try:
                transfer = await mongo.get_db().transfers.find_one(
                    {"status": {"$in": ["pending", "debited", "credited"]}},
                    sort=[("created_at", 1)],
                )
                if not transfer:
                    await asyncio.sleep(2)
                    continue
                try:
                    await TransferService._execute_transfer(transfer)
                except HTTPException:
                    pass
                except Exception:
                    logger.exception("Transfer recovery attempt failed")
                    await asyncio.sleep(2)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Transfer recovery worker failed")
                await asyncio.sleep(2)
