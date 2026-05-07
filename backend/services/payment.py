from core.config import settings
import os
from core.database import db_client
from fastapi import HTTPException
from models.wallet import Transaction, PurchaseRecord, TransactionType
from loguru import logger

class PaymentService:
    @staticmethod
    async def purchase_chapter(req, current_user):
        db = db_client.mongodb.get_default_database()
        docs = db["documents"]
        users = db["users"]
        transactions = db["transactions"]
        purchases = db["purchases"]
        user_id = str(current_user.id)
        
        doc = await docs.find_one({"_id": req.document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại trên hệ thống.")
            
        chapter = next((c for c in doc.get("chapters", []) if c.get("id") == req.chapter_id), None)
        if not chapter:
            raise HTTPException(status_code=404, detail="Nội dung chương không tồn tại.")
            
        is_premium = chapter.get("is_premium", False)
        price = chapter.get("price_dl", 0)
        
        if not is_premium or price == 0:
            return {"status": "free", "message": "Nội dung này được cung cấp miễn phí."}
            
        existing = await purchases.find_one({
            "user_id": user_id,
            "item_type": "chapter",
            "item_id": req.chapter_id
        })
        if existing:
            return {"status": "owned", "message": "Bạn đã sở hữu chương này."}
        
        author_id = doc.get("author_id")
        author_cut = int(price * 0.7)
        platform_fee = price - author_cut
        
        session = await db_client.mongodb.start_session()
        try:
            async with session.start_transaction():
                deduct_result = await users.update_one(
                    {"_id": user_id, "wallet_balance": {"$gte": price}},
                    {"$inc": {"wallet_balance": -price}},
                    session=session
                )
                
                if deduct_result.modified_count == 0:
                    await session.abort_transaction()
                    raise HTTPException(status_code=400, detail=f"Số dư không đủ. Cần thêm {price} dl để mở khóa.")
                
                await users.update_one(
                    {"_id": author_id},
                    {"$inc": {"wallet_balance": author_cut}},
                    session=session
                )
                
                await users.update_one(
                    {"_id": settings.PLATFORM_ADMIN_ID},
                    {"$inc": {"wallet_balance": platform_fee}},
                    session=session
                )
                
                title = chapter.get("title", "Nội dung")
                tx_buyer = Transaction(
                    user_id=user_id, 
                    type=TransactionType.PURCHASE, 
                    amount=-price, 
                    reference_id=req.chapter_id, 
                    note=f"Mở khóa chương: {title}"
                )
                tx_author = Transaction(
                    user_id=author_id, 
                    type=TransactionType.RECEIVE, 
                    amount=author_cut, 
                    reference_id=req.chapter_id, 
                    note=f"Thu nhập từ chương: {title}"
                )
                tx_platform = Transaction(
                    user_id=settings.PLATFORM_ADMIN_ID,
                    type=TransactionType.RECEIVE,
                    amount=platform_fee,
                    reference_id=req.chapter_id,
                    note=f"Hoa hồng từ mua chương: {title} (người dùng {user_id})"
                )
                
                await transactions.insert_many(
                    [tx_buyer.model_dump(by_alias=True), tx_author.model_dump(by_alias=True), tx_platform.model_dump(by_alias=True)],
                    session=session
                )
                
                record = PurchaseRecord(user_id=user_id, item_id=req.chapter_id, price_paid=price)
                await purchases.insert_one(record.model_dump(by_alias=True), session=session)
                
                await session.commit_transaction()
                logger.info(f"Chapter {req.chapter_id} purchased by user {user_id} (atomic)")
                return {"status": "unlocked", "message": "Giao dịch thành công. Chương đã được mở khóa."}
        except HTTPException:
            raise
        except Exception as e:
            await session.abort_transaction()
            logger.error(f"Purchase transaction failed for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Giao dịch thất bại. Vui lòng thử lại sau.")
        finally:
            await session.end_session()

    @staticmethod
    async def deposit_fiat(amount_vnd: int, current_user):
        if amount_vnd < 10000:
            raise HTTPException(status_code=400, detail="Số tiền nạp tối thiểu là 10,000 VNĐ.")
        
        dl_expected = int(amount_vnd / 1000)
        db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        
        tx_deposit = Transaction(
            user_id=user_id,
            type=TransactionType.TOPUP,
            amount=dl_expected,
            note=f"Nạp {dl_expected} dl qua cổng thanh toán."
        )
        
        result = await db["transactions"].insert_one(tx_deposit.model_dump(by_alias=True))
        transaction_id = str(result.inserted_id)
        
        gateway_url = getattr(settings, "PAYMENT_GATEWAY_URL")
        payment_url = f"{gateway_url}/checkout?tx={transaction_id}&amount={amount_vnd}"
        
        logger.info(f"Fiat deposit initiated by user {user_id}: {amount_vnd} VND")
        return {
            "status": "pending_payment",
            "payment_url": payment_url,
            "transaction_id": transaction_id,
            "dl_expected": dl_expected
        }