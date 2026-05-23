from bson import ObjectId
from datetime import datetime, timezone, timedelta
import uuid
from uuid6 import uuid7
from fastapi import HTTPException
from core.database import db_client
from models.wallet import Transaction, TransactionType
from loguru import logger

class PurchaseService:
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
                    "_id": str(uuid7()),
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
                
                logger.info(f"Purchase: Document {document_id} purchased by user {current_user.id} for {price} dl")
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
                    "_id": str(uuid7()),
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
                    
                logger.info(f"Purchase: Chapter {chapter_id} purchase by user {current_user.id}")
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
