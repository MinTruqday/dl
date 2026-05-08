from bson import ObjectId
from datetime import datetime, timezone, timedelta
import json
import uuid
from typing import Optional, List
from fastapi import HTTPException, status
from core.database import db_client
from models.wallet import Transaction, TransactionType
from loguru import logger

class TransactionService:
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

                logger.info(f"User {current_user.id} voted {req.amount} dl for post {req.item_id} (atomic)")
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
        target_post = await db["status_updates"].find_one({"_id": ObjectId(req.post_id)})
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
                    {"_id": ObjectId(req.post_id)}, 
                    {"$push": {"paid_by": str(current_user.id)}},
                    session=session
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
                await db["transactions"].insert_many([
                    tx_sender.model_dump(by_alias=True), 
                    tx_receiver.model_dump(by_alias=True)
                ], session=session)
                
                await session.commit_transaction()
                logger.info(f"User {current_user.id} unlocked post {req.post_id} (atomic)")
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
    async def virtual_tip(target_user_id: str, amount: int, current_user):
        db = db_client.mongodb.get_default_database()
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
                    note=f"Ủng hộ cho người dùng {target_user_id}"
                )
                tx_receiver = Transaction(
                    user_id=target_user_id,
                    type=TransactionType.RECEIVE,
                    amount=amount,
                    note=f"Nhận dl ủng hộ từ người dùng {current_user.id}"
                )
                await db["transactions"].insert_many([
                    tx_sender.model_dump(by_alias=True), 
                    tx_receiver.model_dump(by_alias=True)
                ], session=session)
                
                await session.commit_transaction()
                logger.info(f"User {current_user.id} tipped {amount} dl to user {target_user_id} (atomic)")
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
        
        author_id = doc.get("author_id")
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
                    raise HTTPException(status_code=400, detail=f"Số dư ví không đủ để mua tài liệu này (Cần {price} dl).")
                
                if author_id:
                    await db["users"].update_one(
                        {"_id": author_id},
                        {"$inc": {"wallet_balance": price}},
                        session=session
                    )
                
                await db["purchases"].insert_one({
                    "_id": str(uuid.uuid4()),
                    "user_id": str(current_user.id),
                    "document_id": document_id,
                    "item_type": "document",
                    "price": price,
                    "purchased_at": datetime.now(timezone.utc),
                }, session=session)
                
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
                ], session=session)
                
                await session.commit_transaction()
                
                from services.notification import NotificationService
                if author_id:
                    await NotificationService.notify_purchase(
                        document_id, 
                        doc.get('title', document_id), 
                        author_id, 
                        current_user.full_name or "Một độc giả"
                    )
                
                logger.info(f"Document {document_id} purchased by user {current_user.id} for {price} dl (atomic)")
                return {"message": "Mua tài liệu thành công.", "status": "purchased"}
        except HTTPException:
            raise
        except Exception as e:
            await session.abort_transaction()
            logger.error(f"Document purchase transaction failed for user {current_user.id}: {e}")
            raise HTTPException(status_code=500, detail="Giao dịch thất bại. Vui lòng thử lại sau.")
        finally:
            await session.end_session()

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
        
        author_id = doc.get("author_id")
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
                    raise HTTPException(status_code=400, detail="Số dư ví không đủ.")
                
                if author_id:
                    await db["users"].update_one(
                        {"_id": author_id},
                        {"$inc": {"wallet_balance": price}},
                        session=session
                    )
                
                await db["purchases"].insert_one({
                    "_id": str(uuid.uuid4()),
                    "user_id": str(current_user.id),
                    "document_id": document_id,
                    "item_id": chapter_id,
                    "item_type": "chapter",
                    "price": price,
                    "purchased_at": datetime.now(timezone.utc),
                }, session=session)
                
                await session.commit_transaction()
                
                from services.notification import NotificationService
                if author_id:
                    await NotificationService.notify_purchase(
                        document_id, 
                        f"{doc.get('title')} - {chapter.get('title')}", 
                        author_id, 
                        current_user.full_name or "Một độc giả"
                    )
                    
                logger.info(f"Chapter {chapter_id} purchase by user {current_user.id} (atomic)")
                return {"message": "Mua chương thành công.", "status": "purchased"}
        except HTTPException:
            raise
        except Exception as e:
            await session.abort_transaction()
            logger.error(f"Chapter purchase failed for user {current_user.id}: {e}")
            raise HTTPException(status_code=500, detail="Giao dịch thất bại. Vui lòng thử lại sau.")
        finally:
            await session.end_session()

    @staticmethod
    async def cancel_purchase(purchase_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        purchase = await db["purchases"].find_one({"_id": purchase_id, "user_id": str(current_user.id)})
        if not purchase:
            raise HTTPException(status_code=404, detail="Không tìm thấy ghi nhận mua này.")
        
        purchased_at = purchase.get("purchased_at", datetime.now(timezone.utc))
        if isinstance(purchased_at, str):
            purchased_at = datetime.fromisoformat(purchased_at)
        
        if datetime.now(timezone.utc) - purchased_at > timedelta(hours=48):
            raise HTTPException(status_code=400, detail="Chỉ có thể hoàn tiền trong vòng 48 giờ sau khi mua.")
        
        price = purchase.get("price", 0)
        doc_id = purchase.get("document_id")
        doc = await db["documents"].find_one({"_id": doc_id}) if doc_id else None
        author_id = doc.get("author_id") if doc else None
        
        session = await db_client.mongodb.start_session()
        try:
            async with session.start_transaction():
                await db["users"].update_one({"_id": str(current_user.id)}, {"$inc": {"wallet_balance": price}}, session=session)
                if author_id:
                    await db["users"].update_one({"_id": author_id}, {"$inc": {"wallet_balance": -price}}, session=session)
                
                await db["purchases"].update_one({"_id": purchase_id}, {"$set": {"status": "CANCELLED", "cancelled_at": datetime.now(timezone.utc)}}, session=session)
                
                tx_refund_buyer = Transaction(user_id=str(current_user.id), type=TransactionType.REFUND, amount=price, note=f"Hoàn tiền giao dịch: {purchase_id}")
                tx_refund_seller = Transaction(user_id=author_id, type=TransactionType.REFUND, amount=-price, note=f"Hoàn tiền giao dịch: {purchase_id}")
                await db["transactions"].insert_many([tx_refund_buyer.model_dump(by_alias=True), tx_refund_seller.model_dump(by_alias=True)], session=session)
                await session.commit_transaction()
                return {"message": "Hoàn tiền thành công.", "refunded_amount": price}
        except Exception as e:
            await session.abort_transaction()
            logger.error(f"Refund failed: {e}")
            raise HTTPException(status_code=500, detail="Hoàn tiền thất bại.")
        finally:
            await session.end_session()

    @staticmethod
    async def request_withdrawal(amount: int, current_user):
        db = db_client.mongodb.get_default_database()
        if amount < 100000:
            raise HTTPException(status_code=400, detail="Số tiền rút tối thiểu là 100,000 dl.")

        user = await db["users"].find_one({"_id": str(current_user.id)})
        if not user or user.get("wallet_balance", 0) < amount:
            raise HTTPException(status_code=400, detail="Số dư không đủ.")

        withdrawal_id = str(uuid.uuid4())
        session = await db_client.mongodb.start_session()
        try:
            async with session.start_transaction():
                await db["users"].update_one({"_id": str(current_user.id)}, {"$inc": {"wallet_balance": -amount}}, session=session)
                await db["withdrawal_requests"].insert_one({
                    "_id": withdrawal_id,
                    "user_id": str(current_user.id),
                    "amount": amount,
                    "status": "PENDING",
                    "created_at": datetime.now(timezone.utc)
                }, session=session)
                
                tx = Transaction(user_id=str(current_user.id), amount=-amount, type=TransactionType.WITHDRAW, note=f"Yêu cầu rút tiền {withdrawal_id}", reference_id=withdrawal_id)
                await db["transactions"].insert_one(tx.model_dump(by_alias=True), session=session)
                
                await session.commit_transaction()
                return {"message": "Đã gửi yêu cầu rút tiền.", "withdrawal_id": withdrawal_id}
        except Exception as e:
            await session.abort_transaction()
            raise HTTPException(status_code=500, detail="Yêu cầu rút tiền thất bại.")
        finally:
            await session.end_session()

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
        
        withdrawal_res = await db["withdrawal_requests"].aggregate([
            {"$match": {"user_id": str(current_user.id), "status": "PENDING"}},
            {"$group": {"_id": None, "pending": {"$sum": "$amount"}}}
        ]).to_list(length=1)
        pending_withdrawal = withdrawal_res[0]["pending"] if withdrawal_res else 0
        
        return {"total_revenue": total_revenue, "pending_withdrawal": pending_withdrawal, "currency": "dl"}

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

