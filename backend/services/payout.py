from core.database import db_client
from fastapi import HTTPException
from datetime import datetime
import uuid
from loguru import logger
from models.wallet import Transaction, TransactionType

class PayoutService:
    @staticmethod
    async def request_payout(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        amount = data.get("amount", 0)
        
        if amount < 100000:
            raise HTTPException(status_code=400, detail="Số tiền rút tối thiểu là 100,000 DL.")
            
        wallet = await db["wallets"].find_one({"user_id": str(current_user.id)})
        if not wallet or wallet.get("balance", 0) < amount:
            raise HTTPException(status_code=400, detail="Số dư không đủ để thực hiện yêu cầu rút tiền.")
            
        payout_id = str(uuid.uuid4())
        payout_request = {
            "_id": payout_id,
            "user_id": str(current_user.id),
            "amount": amount,
            "bank_info": data.get("bank_info", {}),
            "status": "PENDING",
            "created_at": datetime.utcnow()
        }
        
        await db["payout_requests"].insert_one(payout_request)
        
        await db["wallets"].update_one(
            {"user_id": str(current_user.id)},
            {"$inc": {"balance": -amount}}
        )
        
        transaction = Transaction(
            user_id=str(current_user.id),
            amount=-amount,
            type=TransactionType.WITHDRAWAL,
            description=f"Yêu cầu rút tiền {payout_id}",
            reference_id=payout_id
        )
        await db["transactions"].insert_one(transaction.model_dump())
        
        logger.info(f"Monetization: Author {current_user.id} requested payout of {amount} dl")
        return {"message": "Yêu cầu rút tiền đã được gửi thành công.", "payout_id": payout_req["_id"]}

    @staticmethod
    async def get_payout_queue(status: str = "pending") -> list:
        db = db_client.mongodb.get_default_database()
        payouts = await db["payout_requests"].find({"status": status}).sort("created_at", -1).to_list(length=100)
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
        payout = await db["payout_requests"].find_one({"_id": payout_id})
        if not payout: 
            raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu thanh toán.")
        
        status = "APPROVED" if action == "approve" else "REJECTED"
        await db["payout_requests"].update_one(
            {"_id": payout_id}, 
            {"$set": {"status": status, "processed_by": str(current_moderator.id), "processed_at": datetime.utcnow()}}
        )
        
        await db["audit_logs"].insert_one({
            "action": f"PAYOUT_{status}", 
            "actor_id": str(current_moderator.id), 
            "payout_id": payout_id, 
            "timestamp": datetime.utcnow()
        })
        logger.info(f"Audit: Payout {payout_id} {status} by moderator {current_moderator.id}")
        return {"message": f"Đã {status.lower()} yêu cầu rút tiền thành công."}

    @staticmethod
    async def get_my_payouts(current_user) -> list:
        db = db_client.mongodb.get_default_database()
        payouts = await db["payout_requests"].find(
            {"user_id": str(current_user.id)}
        ).sort("created_at", -1).to_list(length=100)
        return payouts
