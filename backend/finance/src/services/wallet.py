from datetime import datetime, timezone
import json
from fastapi import HTTPException, status
from core.database import db_client
from src.schemas.wallet import Transaction, TransactionType
from loguru import logger

class WalletService:

    @staticmethod
    async def get_balance(current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        wallet = await db['wallets'].find_one({'_id': str(current_user.id)})
        return {'balance': wallet.get('balance', 0) if wallet else 0}

    @staticmethod
    async def redeem_voucher(req, current_user, db=None, session=None):
        should_close_session = False
        lock_key = f'lock:voucher:{req.code}'
        is_locked = False
        
        if db_client.redis:
            user_rl_key = f'rl:voucher:{current_user.id}'
            try:
                attempts = await db_client.redis.incr(user_rl_key)
                if attempts == 1:
                    await db_client.redis.expire(user_rl_key, 300)
                if attempts > 10:
                    raise HTTPException(status_code=429, detail="Bạn đã thao tác quá nhiều lần, vui lòng thử lại sau 5 phút")
            except HTTPException:
                raise
            except Exception as e:
                logger.exception(f"Hệ thống giới hạn truy cập Redis gặp sự cố: {e}")
        
        if db_client.redis:
            try:
                is_locked = await db_client.redis.set(lock_key, 'locked', nx=True, ex=10)
                if not is_locked:
                    raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail='Mã nạp này đang được xử lý, vui lòng chờ giây lát')
            except HTTPException:
                raise
            except Exception as e:
                logger.exception(f'Không thể khóa phiên làm việc trên Redis: {e}')
                raise HTTPException(status_code=500, detail="Lỗi kết nối bộ đệm, vui lòng thử lại sau")

        if db is None:
            db = db_client.mongodb.get_default_database()
            
        if session is None:
            session = await db_client.mongodb.start_session()
            session.start_transaction()
            should_close_session = True
            
        vouchers = db['vouchers']
        wallets = db['wallets']
        transactions = db['transactions']
        
        try:
            voucher = await vouchers.find_one({'code': req.code}, session=session)
            if not voucher:
                if should_close_session: await session.abort_transaction()
                raise HTTPException(status_code=404, detail='Mã nạp không hợp lệ hoặc không tồn tại')
            if voucher.get('is_used'):
                if should_close_session: await session.abort_transaction()
                raise HTTPException(status_code=400, detail='Mã nạp này đã được sử dụng trước đó')
            
            bonus_dl = voucher.get('amount_dl', voucher.get('amount_dls', 0))
            result = await vouchers.update_one({'_id': voucher['_id'], 'is_used': False}, {'$set': {'is_used': True, 'used_by': str(current_user.id), 'used_at': datetime.now(timezone.utc)}}, session=session)
            if result.modified_count == 0:
                if should_close_session: await session.abort_transaction()
                raise HTTPException(status_code=400, detail='Mã nạp vừa được sử dụng bởi người dùng khác')
                
            await wallets.update_one({'_id': str(current_user.id)}, {'$inc': {'balance': bonus_dl}}, upsert=True, session=session)
            tx = Transaction(user_id=str(current_user.id), type=TransactionType.TOPUP, amount=bonus_dl, note=f'Đổi voucher: {req.code}')
            await transactions.insert_one(tx.model_dump(by_alias=True), session=session)
            
            if should_close_session:
                await session.commit_transaction()
                
            try:
                import httpx
                from core.config import settings
                if settings.SIGNAL_URL:
                    async with httpx.AsyncClient() as client:
                        await client.post(
                            f"{settings.SIGNAL_URL}/thong-bao/noi-bo/kich-hoat",
                            json={
                                "target_user_id": str(current_user.id),
                                "title": 'Nạp dl hoàn tất',
                                "body": f'Tài khoản vừa được cộng thêm {bonus_dl} dl',
                                "type": 'topup'
                            },
                            timeout=3.0
                        )
            except Exception as e:
                logger.warning(f'Không thể gửi thông báo: {e}')
            logger.info(f'Người dùng {current_user.id} đã đổi mã quà tặng {req.code} và nhận được {bonus_dl} dl')
            return {'message': 'Đổi mã quà tặng hoàn tất', 'bonus_dl': bonus_dl, 'status': 'success'}
        except HTTPException:
            raise
        except Exception as e:
            if should_close_session:
                await session.abort_transaction()
            logger.exception(f'Không thể đổi mã quà tặng: {e}')
            raise HTTPException(status_code=500, detail="Hệ thống bảo trì, thử lại sau")
        finally:
            if should_close_session:
                await session.end_session()
            if db_client.redis and is_locked:
                try:
                    await db_client.redis.delete(lock_key)
                except Exception as e:
                    logger.error(f'Không thể mở khóa phiên làm việc trên Redis: {e}')

    @staticmethod
    async def get_history(current_user, cursor: str=None, limit: int=30, tx_type: str=None, skip: int=0, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        query = {'user_id': str(current_user.id)}
        if tx_type:
            query['type'] = tx_type.lower()
        if cursor:
            try:
                query['created_at'] = {'$lt': datetime.fromisoformat(cursor.replace('Z', '+00:00'))}
            except Exception as e:
                logger.warning(f'Định dạng con trỏ phân trang không hợp lệ: {e}')
        tx_cursor = db['transactions'].find(query).sort('created_at', -1)
        if skip > 0:
            tx_cursor = tx_cursor.skip(skip)
        tx_cursor = tx_cursor.limit(limit)
        txs = await tx_cursor.to_list(length=limit)
        type_translations = {'topup': 'Nạp tiền', 'purchase': 'Mua tài liệu', 'receive': 'Nhận tiền', 'withdraw': 'Rút tiền', 'tip': 'Ủng hộ tác giả', 'subscription': 'Đăng ký thành viên', 'refund': 'Hoàn tiền'}
        for tx in txs:
            tx['_id'] = str(tx['_id'])
            if isinstance(tx.get('created_at'), datetime):
                tx['created_at'] = tx['created_at'].isoformat()
            raw_type = tx.get('type', '')
            tx['type'] = raw_type.upper()
            tx['type_display'] = type_translations.get(raw_type, 'Giao dịch')
            tx['description'] = tx.get('note', '')
            tx['status'] = 'COMPLETED'
        return txs