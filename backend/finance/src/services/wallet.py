from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.redis import redis
from src.core.infrastructure.mongo import mongo
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
    @log_logic_execution
    async def get_balance(current_user):
        wallet = await mongo.find_one(collection="wallets", query={"_id": str(current_user.id)})
        return {
            "balance": wallet.get("balance", 0) if wallet else 0,
            "withdrawable_balance": wallet.get("withdrawable_balance", 0) if wallet else 0,
        }
    @staticmethod
    @log_logic_execution
    async def get_history(
        current_user,
        cursor: str = None,
        limit: int = 50,
        tx_type: str = None,
        skip: int = 0,
    ):
        query = {"user_id": str(current_user.id)}
        if tx_type:
            query["type"] = tx_type.lower()
        if cursor:
            try:
                query["created_at"] = {
                    "$lt": datetime.fromisoformat(cursor.replace("Z", "+00:00"))
                }
            except ValueError:
                raise HTTPException(status_code=400, detail="Con trỏ phân trang không hợp lệ")
        txs = await mongo.find(collection="transactions", query=query, sort=[("created_at", -1)], skip=skip, limit=limit).to_list(length=None)
        type_translations = {
            "topup": "Deposit",
            "purchase": "Document Purchase",
            "receive": "Funds Received",
            "withdraw": "Withdrawal",
            "tip": "Author Tip",
            "refund": "Refund",
            "transfer_out": "Transfer Sent",
            "transfer_in": "Transfer Received",
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
