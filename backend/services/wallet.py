from bson import ObjectId
from datetime import datetime
from fastapi import HTTPException, status
from core.database import db_client
from models.wallet import Transaction, TransactionType
import json
import uuid
from loguru import logger

class WalletService:
    @staticmethod
    async def vote_item(req, current_user):
        db = db_client.mongodb.get_default_database()
        users = db["users"]
        transactions = db["transactions"]
        status_updates = db["status_updates"]
        
        if req.amount <= 0:
            raise HTTPException(status_code=400, detail="Số dl không hợp lệ.")
            
        user = await users.find_one({"_id": current_user.id})
        if not user or user.get("wallet_balance", 0) < req.amount:
            raise HTTPException(status_code=400, detail="Số dư ví không đủ.")
            
        target_post = await status_updates.find_one({"_id": ObjectId(req.item_id)})
        if not target_post:
            raise HTTPException(status_code=404, detail="Bài viết không tồn tại.")
            
        author_id = target_post.get("user_id")
        if author_id == current_user.id:
            raise HTTPException(status_code=400, detail="Bạn không thể tự ủng hộ bài viết của chính mình.")
            
        await users.update_one({"_id": current_user.id}, {"$inc": {"wallet_balance": -req.amount}})
        await users.update_one({"_id": author_id}, {"$inc": {"wallet_balance": req.amount}})
        
        tx_sender = Transaction(
            user_id=current_user.id,
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
                await users.update_one({"_id": current_user.id}, {"$inc": {"wallet_balance": cashback}})
                tx_cashback = Transaction(
                    user_id=current_user.id,
                    type=TransactionType.RECEIVE,
                    amount=cashback,
                    note=f"Hoàn 10% dl khi tặng cho bài viết {req.item_id}!"
                )
                txs.append(tx_cashback.model_dump(by_alias=True))
                
        await transactions.insert_many(txs)
        msg = f"Đã gửi tặng dl thành công."
        if cashback > 0:
            msg += f" Bạn đã nhận được mức hoàn lại {cashback} dl."
        
        logger.info(f"User {current_user.id} voted {req.amount} dl for post {req.item_id}")
        return {"message": msg}

    @staticmethod
    async def get_balance(current_user):
        db = db_client.mongodb.get_default_database()
        fresh_user = await db["users"].find_one({"_id": current_user.id})
        return {"balance": fresh_user.get("wallet_balance", 0) if fresh_user else 0}

    @staticmethod
    async def redeem_voucher(req, current_user):
        if not db_client.redis:
            logger.error("Redis client not available for voucher redemption")
            raise HTTPException(status_code=500, detail="Dịch vụ nạp thẻ hiện đang bảo trì, vui lòng thử lại sau.")
            
        lock_key = f"lock:voucher:{req.code}"
        is_locked = await db_client.redis.set(lock_key, "locked", nx=True, ex=10)
        if not is_locked:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Mã nạp này đang được xử lý, vui lòng chờ giây lát.")
            
        try:
            db = db_client.mongodb.get_default_database()
            vouchers = db["vouchers"]
            users = db["users"]
            transactions = db["transactions"]
            
            voucher = await vouchers.find_one({"code": req.code})
            if not voucher:
                raise HTTPException(status_code=404, detail="Mã nạp không hợp lệ hoặc không tồn tại.")
            if voucher.get("is_used"):
                raise HTTPException(status_code=400, detail="Mã nạp này đã được sử dụng trước đó.")
                
            bonus_dl = voucher.get("amount_dl", voucher.get("amount_dls", 0))
            result = await vouchers.update_one(
                {"_id": voucher["_id"], "is_used": False},
                {"$set": {
                    "is_used": True,
                    "used_by": current_user.id,
                    "used_at": datetime.utcnow()
                }}
            )
            
            if result.modified_count == 0:
                raise HTTPException(status_code=400, detail="Mã nạp vừa được sử dụng bởi người dùng khác.")
                
            await users.update_one(
                {"_id": current_user.id},
                {"$inc": {"wallet_balance": bonus_dl}}
            )
            
            tx = Transaction(
                user_id=current_user.id,
                type=TransactionType.TOPUP,
                amount=bonus_dl,
                note=f"Nạp voucher: {req.code}"
            )
            await transactions.insert_one(tx.model_dump(by_alias=True))
            
            if getattr(db_client, "redis", None):
                await db_client.redis.publish(
                    f"user_notifications:{current_user.id}", 
                    json.dumps({"title": "Nạp dl thành công", "body": f"Tài khoản vừa được cộng thêm {bonus_dl} dl."})
                )
            
            logger.info(f"User {current_user.id} redeemed voucher {req.code} for {bonus_dl} dl")
            return {"message": "Nạp thẻ thành công", "bonus_dl": bonus_dl, "status": "success"}
        finally:
            await db_client.redis.delete(lock_key)

    @staticmethod
    async def get_history(current_user):
        db = db_client.mongodb.get_default_database()
        cursor = db["transactions"].find({"user_id": current_user.id}).sort("created_at", -1)
        txs = await cursor.to_list(length=30)
        for tx in txs:
            tx["_id"] = str(tx["_id"])
        return txs

    @staticmethod
    async def unlock_post(req, current_user):
        db = db_client.mongodb.get_default_database()
        target_post = await db["status_updates"].find_one({"_id": ObjectId(req.post_id)})
        if not target_post:
            raise HTTPException(status_code=404, detail="Bài viết không tồn tại.")
            
        if not target_post.get("is_premium"):
            raise HTTPException(status_code=400, detail="Thao tác không hợp lệ. Bài viết này không yêu cầu phí mở khóa.")
            
        if str(current_user.id) in target_post.get("paid_by", []):
            return {"message": "Bạn đã mở khóa bài viết này."}
            
        price = target_post.get("price", 0)
        user = await db["users"].find_one({"_id": current_user.id})
        if not user or user.get("wallet_balance", 0) < price:
            raise HTTPException(status_code=400, detail=f"Số dư không đủ để mở khóa (Cần {price} dl).")
            
        await db["users"].update_one({"_id": current_user.id}, {"$inc": {"wallet_balance": -price}})
        author_id = target_post.get("user_id")
        await db["users"].update_one({"_id": author_id}, {"$inc": {"wallet_balance": price}})
        await db["status_updates"].update_one(
            {"_id": ObjectId(req.post_id)}, 
            {"$push": {"paid_by": str(current_user.id)}}
        )
        
        tx_sender = Transaction(
            user_id=str(current_user.id),
            type=TransactionType.WITHDRAW,
            amount=-price,
            note=f"Mở khóa bài viết Premium: {req.post_id}"
        )
        tx_receiver = Transaction(
            user_id=author_id,
            type=TransactionType.RECEIVE,
            amount=price,
            note=f"Nhận dl từ giao dịch mở khóa bài viết {req.post_id}"
        )
        await db["transactions"].insert_many([tx_sender.model_dump(by_alias=True), tx_receiver.model_dump(by_alias=True)])
        
        logger.info(f"User {current_user.id} unlocked post {req.post_id}")
        return {"message": "Mở khóa bài viết thành công.", "success": True}

    @staticmethod
    async def get_top_donators():
        db = db_client.mongodb.get_default_database()
        redis = db_client.redis
        
        if redis:
            try:
                cached = await redis.get("wallet:top_donators")
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Failed to get top donators from cache: {e}")
                
        pipeline = [
            {"$match": {"type": "withdraw", "amount": {"$lt": 0}, "note": {"$regex": "^Tặng dl"}}},
            {"$group": {
                "_id": "$user_id",
                "total_donated": {"$sum": {"$abs": "$amount"}}
            }},
            {"$sort": {"total_donated": -1}},
            {"$limit": 5}
        ]
        
        try:
            cursor = db["transactions"].aggregate(pipeline)
            top_donators = await cursor.to_list(length=5)
            if not top_donators:
                return []
                
            uids = [td["_id"] for td in top_donators]
            users_cursor = db["users"].find({"_id": {"$in": uids}})
            users = await users_cursor.to_list(length=5)
            u_map = {str(u["_id"]): {"name": u.get("full_name", "Người dùng ẩn danh"), "avatar": u.get("avatar_url")} for u in users}
            
            result = []
            for td in top_donators:
                u_info = u_map.get(td["_id"], {})
                result.append({
                    "user_id": td["_id"],
                    "name": u_info.get("name", "Ẩn danh"),
                    "avatar": u_info.get("avatar"),
                    "total_donated": int(td["total_donated"])
                })
                
            if redis:
                try:
                    await redis.setex("wallet:top_donators", 300, json.dumps(result))
                except Exception as e:
                    logger.warning(f"Failed to cache top donators: {e}")
            return result
        except Exception as e:
            logger.error(f"Error calculating top donators: {e}")
            return []

    @staticmethod
    async def virtual_tip(target_user_id: str, amount: int, current_user):
        db = db_client.mongodb.get_default_database()
        user = await db["users"].find_one({"_id": str(current_user.id)})
        if not user or user.get("wallet_balance", 0) < amount:
            raise HTTPException(status_code=400, detail="Số dư ví không đủ.")
            
        await db["users"].update_one({"_id": str(current_user.id)}, {"$inc": {"wallet_balance": -amount}})
        await db["users"].update_one({"_id": target_user_id}, {"$inc": {"wallet_balance": amount}})
        
        tx_sender = Transaction(
            user_id=str(current_user.id),
            type=TransactionType.TIP,
            amount=-amount,
            note=f"Ủng hộ cho người dùng {target_user_id}"
        )
        tx_receiver = Transaction(
            user_id=target_user_id,
            type=TransactionType.RECEIVE,
            amount=amount,
            note=f"Nhận dl ủng hộ từ người dùng {current_user.id}"
        )
        await db["transactions"].insert_many([tx_sender.model_dump(by_alias=True), tx_receiver.model_dump(by_alias=True)])
        
        logger.info(f"User {current_user.id} tipped {amount} dl to user {target_user_id}")
        return {"message": "Đã thực hiện ủng hộ thành công."}

    @staticmethod
    async def get_revenue(current_user):
        db = db_client.mongodb.get_default_database()
        pipeline = [
            {"$match": {"user_id": str(current_user.id), "type": "receive"}},
            {"$group": {"_id": None, "total_revenue": {"$sum": "$amount"}}}
        ]
        cursor = db["transactions"].aggregate(pipeline)
        res = await cursor.to_list(length=1)
        total_revenue = res[0]["total_revenue"] if res else 0
        
        payout_res = await db["payouts"].aggregate([
            {"$match": {"author_id": str(current_user.id), "status": "pending"}},
            {"$group": {"_id": None, "pending": {"$sum": "$amount"}}}
        ]).to_list(length=1)
        pending_payout = payout_res[0]["pending"] if payout_res else 0
        
        return {"total_revenue": total_revenue, "pending_payout": pending_payout, "currency": "dl"}

    @staticmethod
    async def request_payout(amount: int, current_user):
        db = db_client.mongodb.get_default_database()
        if current_user.wallet_balance < amount:
            raise HTTPException(status_code=400, detail="Số dư không đủ để thực hiện yêu cầu rút tiền.")
            
        await db["payouts"].insert_one({
            "author_id": str(current_user.id),
            "amount": amount,
            "status": "pending",
            "created_at": datetime.utcnow()
        })
        await db["users"].update_one({"_id": current_user.id}, {"$inc": {"wallet_balance": -amount}})
        
        logger.info(f"User {current_user.id} requested payout of {amount} dl")
        return {"message": "Đã gửi yêu cầu rút tiền thành công."}

    @staticmethod
    async def purchase_document(document_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")
            
        price = doc.get("price_dl", doc.get("price_dls", 0))
        if price <= 0:
            return {"message": "Tài liệu này được cung cấp miễn phí.", "status": "free"}
            
        user = await db["users"].find_one({"_id": str(current_user.id)})
        if not user or user.get("wallet_balance", 0) < price:
            raise HTTPException(status_code=400, detail=f"Số dư ví không đủ để mua tài liệu này (Cần {price} dl).")
            
        existing = await db["purchases"].find_one({
            "user_id": str(current_user.id),
            "document_id": document_id,
            "item_type": "document"
        })
        if existing:
            return {"message": "Bạn đã sở hữu tài liệu này.", "status": "owned"}
            
        await db["users"].update_one({"_id": str(current_user.id)}, {"$inc": {"wallet_balance": -price}})
        author_id = doc.get("author_id")
        if author_id:
            await db["users"].update_one({"_id": author_id}, {"$inc": {"wallet_balance": price}})
            
        await db["purchases"].insert_one({
            "_id": str(uuid.uuid4()),
            "user_id": str(current_user.id),
            "document_id": document_id,
            "item_type": "document",
            "price": price,
            "purchased_at": datetime.utcnow(),
        })
        
        tx_buyer = Transaction(
            user_id=str(current_user.id),
            type=TransactionType.WITHDRAW,
            amount=-price,
            note=f"Mua tài liệu: {doc.get('title', document_id)}"
        )
        tx_seller = Transaction(
            user_id=author_id,
            type=TransactionType.RECEIVE,
            amount=price,
            note=f"Bán tài liệu: {doc.get('title', document_id)}"
        )
        await db["transactions"].insert_many([
            tx_buyer.model_dump(by_alias=True),
            tx_seller.model_dump(by_alias=True),
        ])
        
        if db_client.redis and author_id:
            await db_client.redis.publish(
                f"user_notifications:{author_id}",
                json.dumps({"title": "Giao dịch mới", "body": f"Tài liệu '{doc.get('title')}' vừa được mua."})
            )
            
        from services.author import AuthorService
        await AuthorService.notify_purchase(document_id, str(current_user.id))
        
        logger.info(f"Document {document_id} purchased by user {current_user.id} for {price} dl")
        return {"message": "Mua tài liệu thành công.", "status": "purchased"}

    @staticmethod
    async def purchase_chapter(document_id: str, chapter_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")
            
        chapter = None
        for ch in doc.get("chapters", []):
            if ch.get("id") == chapter_id:
                chapter = ch
                break
        if not chapter:
            raise HTTPException(status_code=404, detail="Chương không tồn tại.")
            
        price = chapter.get("price_dl", chapter.get("price_dls", 0))
        if price <= 0:
            return {"message": "Chương này hoàn toàn miễn phí.", "status": "free"}
            
        user = await db["users"].find_one({"_id": str(current_user.id)})
        if not user or user.get("wallet_balance", 0) < price:
            raise HTTPException(status_code=400, detail="Số dư ví không đủ.")
            
        existing = await db["purchases"].find_one({
            "user_id": str(current_user.id),
            "item_id": chapter_id,
            "item_type": "chapter"
        })
        if existing:
            return {"message": "Bạn đã sở hữu chương này.", "status": "owned"}
            
        await db["users"].update_one({"_id": str(current_user.id)}, {"$inc": {"wallet_balance": -price}})
        await db["purchases"].insert_one({
            "_id": str(uuid.uuid4()),
            "user_id": str(current_user.id),
            "document_id": document_id,
            "item_id": chapter_id,
            "item_type": "chapter",
            "price": price,
            "purchased_at": datetime.utcnow(),
        })
        
        logger.info(f"Chapter {chapter_id} of document {document_id} purchased by user {current_user.id} for {price} dl")
        return {"message": "Mua chương thành công.", "status": "purchased"}
