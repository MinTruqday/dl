from bson import ObjectId
from datetime import datetime, timezone
from fastapi import HTTPException
from core.database import db_client
from models.wallet import Transaction, TransactionType
from loguru import logger

class DonationService:
    @staticmethod
    async def vote_item(req, current_user):
        db = db_client.mongodb.get_default_database()
        users = db["users"]
        transactions = db["transactions"]
        status_updates = db["status_updates"]
        
        if req.amount <= 0:
            raise HTTPException(status_code=400, detail="Số dl không hợp lệ.")
            
        target_post = await status_updates.find_one({"_id": ObjectId(req.item_id)})
        if not target_post:
            raise HTTPException(status_code=404, detail="Bài viết không tồn tại.")
            
        author_id = target_post.get("user_id")
        if author_id == str(current_user.id):
            raise HTTPException(status_code=400, detail="Bạn không thể tự ủng hộ bài viết của chính mình.")
            
        session = await db_client.mongodb.start_session()
        try:
            async with session.start_transaction():
                deduct_result = await users.update_one(
                    {"_id": str(current_user.id), "wallet_balance": {"$gte": req.amount}},
                    {"$inc": {"wallet_balance": -req.amount}},
                    session=session
                )
                if deduct_result.modified_count == 0:
                    await session.abort_transaction()
                    raise HTTPException(status_code=400, detail="Số dư ví không đủ.")
                
                await users.update_one(
                    {"_id": author_id},
                    {"$inc": {"wallet_balance": req.amount}},
                    session=session
                )
                
                tx_sender = Transaction(
                    user_id=str(current_user.id),
                    type=TransactionType.WITHDRAW,
                    amount=-req.amount,
                    note=f"Tặng dl cho tác giả bài viết {req.item_id}"
                )
                tx_receiver = Transaction(
                    user_id=author_id,
                    type=TransactionType.RECEIVE,
                    amount=req.amount,
                    note=f"Nhận dl từ người dùng {current_user.id} cho bài viết {req.item_id}"
                )
                
                txs = [tx_sender.model_dump(by_alias=True), tx_receiver.model_dump(by_alias=True)]
                cashback = 0
                if req.amount >= 50:
                    cashback = int(req.amount * 0.1)
                    if cashback > 0:
                        await users.update_one(
                            {"_id": str(current_user.id)}, 
                            {"$inc": {"wallet_balance": cashback}},
                            session=session
                        )
                        tx_cashback = Transaction(
                            user_id=str(current_user.id),
                            type=TransactionType.RECEIVE,
                            amount=cashback,
                            note=f"Hoàn 10% dl khi tặng cho bài viết {req.item_id}!"
                        )
                        txs.append(tx_cashback.model_dump(by_alias=True))
                await transactions.insert_many(txs, session=session)
                await session.commit_transaction()
                
                msg = f"Đã gửi tặng dl thành công."
                if cashback > 0:
                    msg += f" Bạn đã nhận được mức hoàn lại {cashback} dl."

                logger.info(f"Donation: User {current_user.id} voted {req.amount} dl for post {req.item_id}")
                return {"message": msg}
        except HTTPException:
            raise
        except Exception as e:
            await session.abort_transaction()
            logger.error(f"Vote item transaction failed for user {current_user.id}: {e}")
            raise HTTPException(status_code=500, detail="Giao dịch thất bại. Vui lòng thử lại sau.")
        finally:
            await session.end_session()

    @staticmethod
    async def unlock_post(req, current_user):
        db = db_client.mongodb.get_default_database()
        target_post = await db["status_updates"].find_one({"_id": ObjectId(req.item_id)})
        if not target_post:
            raise HTTPException(status_code=404, detail="Bài viết không tồn tại.")
            
        if not target_post.get("is_premium"):
            raise HTTPException(status_code=400, detail="Thao tác không hợp lệ. Bài viết này không yêu cầu phí mở khóa.")
            
        if str(current_user.id) in target_post.get("paid_by", []):
            return {"message": "Bạn đã mở khóa bài viết này."}
            
        price = target_post.get("price", 0)
        author_id = target_post.get("user_id")
        
        session = await db_client.mongodb.start_session()
        try:
            async with session.start_transaction():
                deduct_result = await db["users"].update_one(
                    {"_id": str(current_user.id), "wallet_balance": {"$gte": price}},
                    {"$inc": {"wallet_balance": -price}},
                    session=session
                )
                if deduct_result.modified_count == 0:
                    await session.abort_transaction()
                    raise HTTPException(status_code=400, detail=f"Số dư không đủ để mở khóa (Cần {price} dl).")
                
                if author_id:
                    await db["users"].update_one(
                        {"_id": author_id},
                        {"$inc": {"wallet_balance": price}},
                        session=session
                    )
                
                await db["status_updates"].update_one(
                    {"_id": ObjectId(req.item_id)}, 
                    {"$push": {"paid_by": str(current_user.id)}},
                    session=session
                )
                
                tx_sender = Transaction(
                    user_id=str(current_user.id),
                    type=TransactionType.WITHDRAW,
                    amount=-price,
                    note=f"Mở khóa bài viết Premium: {req.item_id}"
                )
                tx_receiver = Transaction(
                    user_id=author_id,
                    type=TransactionType.RECEIVE,
                    amount=price,
                    note=f"Nhận dl từ giao dịch mở khóa bài viết {req.item_id}"
                )
                await db["transactions"].insert_many([
                    tx_sender.model_dump(by_alias=True), 
                    tx_receiver.model_dump(by_alias=True)
                ], session=session)
                
                await session.commit_transaction()
                logger.info(f"Donation: User {current_user.id} unlocked post {req.item_id}")
                return {"message": "Mở khóa bài viết thành công.", "success": True}
        except HTTPException:
            raise
        except Exception as e:
            await session.abort_transaction()
            logger.error(f"Unlock post failed for user {current_user.id}: {e}")
            raise HTTPException(status_code=500, detail="Giao dịch thất bại. Vui lòng thử lại sau.")
        finally:
            await session.end_session()

    @staticmethod
    async def virtual_tip(target_user_id: str, amount: int, current_user, message: str = ""):
        if not target_user_id:
            raise HTTPException(status_code=400, detail="Mã người nhận không hợp lệ.")
        db = db_client.mongodb.get_default_database()
        if target_user_id == str(current_user.id):
            raise HTTPException(status_code=400, detail="Bạn không thể tự tặng dl cho chính mình.")

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
                    raise HTTPException(status_code=400, detail="Số dư ví không đủ.")
                
                await db["users"].update_one(
                    {"_id": target_user_id}, 
                    {"$inc": {"wallet_balance": amount}},
                    session=session
                )
                
                tx_sender = Transaction(
                    user_id=str(current_user.id),
                    type=TransactionType.TIP,
                    amount=-amount,
                    note=f"Ủng hộ cho người dùng {target_user_id}: {message}"
                )
                tx_receiver = Transaction(
                    user_id=target_user_id,
                    type=TransactionType.RECEIVE,
                    amount=amount,
                    note=f"Nhận dl ủng hộ từ người dùng {current_user.id}: {message}"
                )
                await db["transactions"].insert_many([
                    tx_sender.model_dump(by_alias=True), 
                    tx_receiver.model_dump(by_alias=True)
                ], session=session)
                
                await session.commit_transaction()
                logger.info(f"Donation: User {current_user.id} tipped {amount} dl to user {target_user_id}")
                return {"message": "Đã thực hiện ủng hộ thành công."}
        except HTTPException:
            raise
        except Exception as e:
            await session.abort_transaction()
            logger.error(f"Virtual tip failed for user {current_user.id}: {e}")
            raise HTTPException(status_code=500, detail="Giao dịch thất bại. Vui lòng thử lại sau.")
        finally:
            await session.end_session()

    @staticmethod
    async def get_top_donators():
        db = db_client.mongodb.get_default_database()
        pipeline = [
            {"$match": {"type": "withdraw", "amount": {"$lt": 0}, "note": {"$regex": "^Tặng dl"}}},
            {"$group": {"_id": "$user_id", "total_donated": {"$sum": {"$abs": "$amount"}}}},
            {"$sort": {"total_donated": -1}},
            {"$limit": 5},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "user_info"
                }
            },
            {"$unwind": {"path": "$user_info", "preserveNullAndEmptyArrays": True}}
        ]
        top_donators = await db["transactions"].aggregate(pipeline).to_list(length=5)
        result = []
        for td in top_donators:
            user = td.get("user_info", {})
            result.append({
                "user_id": td["_id"],
                "name": user.get("full_name", "Ẩn danh") if user else "Ẩn danh",
                "avatar": user.get("avatar_url") if user else None,
                "total_donated": int(td["total_donated"])
            })
        return result
