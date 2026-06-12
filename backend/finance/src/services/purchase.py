from bson import ObjectId
from datetime import datetime, timezone, timedelta
import uuid
from uuid6 import uuid7
from fastapi import HTTPException
from core.database import db_client
from src.schemas.wallet import Transaction, TransactionType
from loguru import logger

class PurchaseService:

    @staticmethod
    async def purchase_document(document_id: str, current_user, db=None, session=None) -> dict:
        should_close_session = False
        if db is None:
            db = db_client.mongodb.get_default_database()
            
        if session is None:
            session = await db_client.mongodb.start_session()
            session.start_transaction()
            should_close_session = True
            
        doc = await db['documents'].find_one({'_id': document_id})
        if not doc:
            if should_close_session: await session.abort_transaction(); await session.end_session()
            raise HTTPException(status_code=404, detail='Tài liệu không tồn tại.')
        price = doc.get('price_dl', doc.get('price_dls', 0))
        if price <= 0:
            if should_close_session: await session.abort_transaction(); await session.end_session()
            return {'message': 'Tài liệu này được cung cấp miễn phí.', 'status': 'free'}
        wallet = await db['wallets'].find_one({'_id': str(current_user.id)})
        if not wallet or wallet.get('balance', 0) < price:
            if should_close_session: await session.abort_transaction(); await session.end_session()
            raise HTTPException(status_code=400, detail=f'Số dư ví không đủ để mua tài liệu này (Cần {price} dl).')
        lock = None
        if hasattr(db_client, 'redis') and db_client.redis:
            lock = db_client.redis.lock(f"purchase:{current_user.id}:{document_id}", timeout=15)
            await lock.acquire()
        try:
            existing = await db['purchases'].find_one({'user_id': str(current_user.id), 'document_id': document_id, 'item_type': 'document'})
            if existing:
                if should_close_session: await session.abort_transaction()
                return {'message': 'Bạn đã sở hữu tài liệu này.', 'status': 'owned'}
            author_id = doc.get('author_id')
            
            try:
                deduct_result = await db['wallets'].update_one({'_id': str(current_user.id), 'balance': {'$gte': price}}, {'$inc': {'balance': -price}}, session=session)
                if deduct_result.modified_count == 0:
                    if should_close_session: await session.abort_transaction()
                    raise HTTPException(status_code=400, detail=f'Số dư ví không đủ để mua tài liệu này (Cần {price} dl).')
                if author_id:
                    await db['wallets'].update_one({'_id': author_id}, {'$inc': {'balance': price}}, upsert=True, session=session)
                await db['purchases'].insert_one({'_id': str(uuid7()), 'user_id': str(current_user.id), 'document_id': document_id, 'item_type': 'document', 'price': price, 'purchased_at': datetime.now(timezone.utc)}, session=session)
                tx_buyer = Transaction(user_id=str(current_user.id), type=TransactionType.WITHDRAW, amount=-price, note=f"Mua tài liệu: {doc.get('title', document_id)}")
                tx_seller = Transaction(user_id=author_id, type=TransactionType.RECEIVE, amount=price, note=f"Bán tài liệu: {doc.get('title', document_id)}")
                await db['transactions'].insert_many([tx_buyer.model_dump(by_alias=True), tx_seller.model_dump(by_alias=True)], session=session)
                
                if should_close_session:
                    await session.commit_transaction()
                    
                if author_id:
                    notif_id = str(uuid7())
                    buyer_name = current_user.full_name or 'Độc giả'
                    doc_title = doc.get('title', document_id)
                    notification = {'_id': notif_id, 'target_user_id': author_id, 'title': 'Giao dịch mới', 'body': f"{buyer_name} vừa mua tài liệu '{doc_title}'", 'is_read': False, 'type': 'purchase', 'created_at': datetime.now(timezone.utc)}
                    await db['notifications'].insert_one(notification, session=session)
                    if hasattr(db_client, 'redis') and db_client.redis:
                        try:
                            import httpx
                            from core.config import settings
                            if settings.SIGNAL_URL:
                                async with httpx.AsyncClient() as client:
                                    await client.post(
                                        f"{settings.SIGNAL_URL}/thong-bao/kich-hoat",
                                        json={
                                            "target_user_id": author_id,
                                            "title": notification['title'],
                                            "body": notification['body'],
                                            "type": 'purchase'
                                        },
                                        timeout=3.0
                                    )
                        except Exception as e:
                            logger.error(f"Notification failed: {e}")
                logger.info(f'Purchase: Document {document_id} purchased by user {current_user.id} for {price} dl')
                return {'message': 'Mua tài liệu thành công.', 'status': 'purchased'}
            except HTTPException:
                raise
            except Exception as e:
                if should_close_session:
                    await session.abort_transaction()
                logger.error(f'Document purchase transaction failed for user {current_user.id}: {e}')
                raise HTTPException(status_code=500, detail='Giao dịch thất bại. Vui lòng thử lại sau.')
            finally:
                if should_close_session:
                    await session.end_session()
        finally:
            if hasattr(db_client, 'redis') and db_client.redis and lock and lock.locked():
                try:
                    await lock.release()
                except Exception:
                    pass

    @staticmethod
    async def cancel_purchase(purchase_id: str, current_user, db=None, session=None) -> dict:
        should_close_session = False
        if db is None:
            db = db_client.mongodb.get_default_database()
            
        if session is None:
            session = await db_client.mongodb.start_session()
            session.start_transaction()
            should_close_session = True
            
        purchase = await db['purchases'].find_one({'_id': purchase_id, 'user_id': str(current_user.id)})
        if not purchase:
            if should_close_session: await session.abort_transaction(); await session.end_session()
            raise HTTPException(status_code=404, detail='Không tìm thấy ghi nhận mua này.')
        purchased_at = purchase.get('purchased_at', datetime.now(timezone.utc))
        if isinstance(purchased_at, str):
            purchased_at = datetime.fromisoformat(purchased_at)
        if datetime.now(timezone.utc) - purchased_at > timedelta(hours=48):
            if should_close_session: await session.abort_transaction(); await session.end_session()
            raise HTTPException(status_code=400, detail='Chỉ có thể hoàn tiền trong vòng 48 giờ sau khi mua.')
        price = purchase.get('price', 0)
        doc_id = purchase.get('document_id')
        doc = await db['documents'].find_one({'_id': doc_id}) if doc_id else None
        author_id = doc.get('author_id') if doc else None
        
        try:
            await db['wallets'].update_one({'_id': str(current_user.id)}, {'$inc': {'balance': price}}, upsert=True, session=session)
            if author_id:
                deduct_result = await db['wallets'].update_one({'_id': author_id, 'balance': {'$gte': price}}, {'$inc': {'balance': -price}}, session=session)
                if deduct_result.modified_count == 0:
                    if should_close_session: await session.abort_transaction()
                    raise HTTPException(status_code=400, detail='Không thể hoàn tiền vì tác giả đã rút hoặc số dư tác giả không đủ.')
                    
            await db['purchases'].update_one({'_id': purchase_id}, {'$set': {'status': 'CANCELLED', 'cancelled_at': datetime.now(timezone.utc)}}, session=session)
            tx_refund_buyer = Transaction(user_id=str(current_user.id), type=TransactionType.REFUND, amount=price, note=f'Hoàn tiền giao dịch: {purchase_id}')
            tx_refund_seller = Transaction(user_id=author_id, type=TransactionType.REFUND, amount=-price, note=f'Hoàn tiền giao dịch: {purchase_id}')
            await db['transactions'].insert_many([tx_refund_buyer.model_dump(by_alias=True), tx_refund_seller.model_dump(by_alias=True)], session=session)
            
            if should_close_session:
                await session.commit_transaction()
            return {'message': 'Hoàn tiền thành công.', 'refunded_amount': price}
        except HTTPException:
            raise
        except Exception as e:
            if should_close_session:
                await session.abort_transaction()
            logger.error(f'Refund failed: {e}')
            raise HTTPException(status_code=500, detail='Hoàn tiền thất bại.')
        finally:
            if should_close_session:
                await session.end_session()