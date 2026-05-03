from core.database import db_client
from fastapi import HTTPException
from datetime import datetime, timedelta
import uuid
from loguru import logger
from models.wallet import Transaction, TransactionType
from models.user import UserInDB

class MonetizationService:
    @staticmethod
    async def create_subscription_plan(plan_data: dict, current_user: UserInDB):
        db = db_client.mongodb.get_default_database()
        
        plan_doc = {
            "_id": str(uuid.uuid4()),
            "author_id": str(current_user.id),
            "name": plan_data["name"],
            "description": plan_data["description"],
            "price_dl": plan_data.get("price_dl"),
            "benefits": plan_data.get("benefits", []),
            "created_at": datetime.utcnow()
        }
        await db["subscription_plans"].insert_one(plan_doc)
        logger.info(f"Monetization: Author {current_user.id} created subscription plan {plan_doc['name']}")
        return plan_doc

    @staticmethod
    async def subscribe_to_author(plan_id: str, current_user: UserInDB):
        db = db_client.mongodb.get_default_database()
        plan = await db["subscription_plans"].find_one({"_id": plan_id})
        if not plan:
            raise HTTPException(status_code=404, detail="Gói đăng ký không tồn tại trên hệ thống.")
        
        author_id = plan["author_id"]
        if author_id == str(current_user.id):
            raise HTTPException(status_code=400, detail="Bạn không thể đăng ký gói hội viên của chính mình.")
            
        price = plan.get("price_dl", 0)
        user = await db["users"].find_one({"_id": str(current_user.id)})
        if not user or user.get("wallet_balance", 0) < price:
            raise HTTPException(status_code=400, detail=f"Số dư tài khoản không đủ để thực hiện đăng ký (Cần {price} dl).")

        await db["users"].update_one({"_id": str(current_user.id)}, {"$inc": {"wallet_balance": -price}})
        await db["users"].update_one({"_id": author_id}, {"$inc": {"wallet_balance": price}})
        
        subscription = {
            "_id": str(uuid.uuid4()),
            "user_id": str(current_user.id),
            "author_id": author_id,
            "plan_id": plan_id,
            "start_date": datetime.utcnow(),
            "end_date": datetime.utcnow() + timedelta(days=30),
            "status": "ACTIVE"
        }
        await db["subscriptions"].insert_one(subscription)
        
        tx_buyer = Transaction(
            user_id=str(current_user.id),
            type=TransactionType.SUBSCRIPTION,
            amount=-price,
            note=f"Đăng ký hội viên: {plan['name']} (Tác giả ID: {author_id})"
        )
        tx_seller = Transaction(
            user_id=author_id,
            type=TransactionType.RECEIVE,
            amount=price,
            note=f"Hội viên mới đăng ký: {plan['name']} (User ID: {current_user.id})"
        )
        await db["transactions"].insert_many([tx_buyer.model_dump(by_alias=True), tx_seller.model_dump(by_alias=True)])
        
        logger.info(f"Monetization: User {current_user.id} subscribed to author {author_id} plan {plan_id}")
        return {"message": "Đăng ký hội viên thành công.", "end_date": subscription["end_date"]}

    @staticmethod
    async def get_author_plans(author_id: str):
        db = db_client.mongodb.get_default_database()
        cursor = db["subscription_plans"].find({"author_id": author_id})
        return await cursor.to_list(length=10)

    @staticmethod
    async def tip_author(author_id: str, amount: int, current_user: UserInDB, message: str = ""):
        db = db_client.mongodb.get_default_database()
        if author_id == str(current_user.id):
            raise HTTPException(status_code=400, detail="Bạn không thể tự tặng dl cho chính mình.")
            
        user = await db["users"].find_one({"_id": str(current_user.id)})
        if not user or user.get("wallet_balance", 0) < amount:
            raise HTTPException(status_code=400, detail=f"Số dư không đủ để thực hiện ủng hộ (Cần {amount} dl).")
            
        await db["users"].update_one({"_id": str(current_user.id)}, {"$inc": {"wallet_balance": -amount}})
        await db["users"].update_one({"_id": author_id}, {"$inc": {"wallet_balance": amount}})
        
        tx_sender = Transaction(
            user_id=str(current_user.id),
            type=TransactionType.TIP,
            amount=-amount,
            note=f"Ủng hộ tác giả: {message}"
        )
        tx_receiver = Transaction(
            user_id=author_id,
            type=TransactionType.RECEIVE,
            amount=amount,
            note=f"Nhận ủng hộ từ người dùng: {message}"
        )
        await db["transactions"].insert_many([tx_sender.model_dump(by_alias=True), tx_receiver.model_dump(by_alias=True)])
        
        logger.info(f"Monetization: User {current_user.id} tipped {amount} dl to author {author_id}")
        return {"message": f"Bạn đã gửi {amount} dl ủng hộ tác giả thành công."}

    @staticmethod
    async def set_document_pricing(document_id: str, data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")
            
        update = {
            "price_dl": max(0, data.get("price_dl", 0)),
            "is_drm_protected": data.get("is_drm_protected", True),
            "updated_at": datetime.utcnow(),
        }
        await db["documents"].update_one({"_id": document_id}, {"$set": update})
        logger.info(f"Monetization: Pricing updated for {document_id} by {current_user.id}")
        return {"message": "Đã cập nhật giá bán thành công."}

    @staticmethod
    async def set_flash_sale(document_id: str, data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
        
        flash_sale_price = int(data.get("price", 0))
        expires_at = datetime.fromisoformat(data["expires_at"])
        
        await db["documents"].update_one(
            {"_id": document_id},
            {"$set": {
                "flash_sale": {
                    "price_dl": flash_sale_price,
                    "expires_at": expires_at,
                    "is_active": True
                },
                "updated_at": datetime.utcnow()
            }}
        )
        logger.info(f"Monetization: Flash sale set for {document_id} until {expires_at}")
        return {"message": f"Thiết lập Flash Sale thành công ({flash_sale_price} dl)."}

    @staticmethod
    async def get_author_revenue_analytics(current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        author_id = str(current_user.id)
        
        pipeline = [
            {"$match": {"user_id": author_id, "type": TransactionType.RECEIVE}},
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": "$amount"},
                "transaction_count": {"$sum": 1}
            }}
        ]
        
        result = await db["transactions"].aggregate(pipeline).to_list(length=1)
        stats = result[0] if result else {"total_revenue": 0, "transaction_count": 0}
        
        return {
            "total_revenue": stats.get("total_revenue", 0),
            "transaction_count": stats.get("transaction_count", 0),
            "currency": "DL",
            "timestamp": datetime.utcnow()
        }
