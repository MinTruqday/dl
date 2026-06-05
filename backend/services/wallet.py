from datetime import datetime, timezone
import json
from fastapi import HTTPException, status
from core.database import db_client
from models.wallet import Transaction, TransactionType
from loguru import logger

class WalletService:

    @staticmethod
    async def get_balance(current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        fresh_user = await db['users'].find_one({'_id': str(current_user.id)})
        return {'balance': fresh_user.get('wallet_balance', 0) if fresh_user else 0}

    @staticmethod
    async def redeem_voucher(req, current_user, db=None):
        lock_key = f'lock:voucher:{req.code}'
        is_locked = False
        if db_client.redis:
            try:
                is_locked = await db_client.redis.set(lock_key, 'locked', nx=True, ex=10)
                if not is_locked:
                    raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail='Mã nạp này đang được xử lý, vui lòng chờ giây lát.')
            except Exception as e:
                logger.warning(f'Redis set lock failed: {e}')
        try:
            if db is None:
                db = db_client.mongodb.get_default_database()
            vouchers = db['vouchers']
            users = db['users']
            transactions = db['transactions']
            voucher = await vouchers.find_one({'code': req.code})
            if not voucher:
                raise HTTPException(status_code=404, detail='Mã nạp không hợp lệ hoặc không tồn tại.')
            if voucher.get('is_used'):
                raise HTTPException(status_code=400, detail='Mã nạp này đã được sử dụng trước đó.')
            bonus_dl = voucher.get('amount_dl', voucher.get('amount_dls', 0))
            result = await vouchers.update_one({'_id': voucher['_id'], 'is_used': False}, {'$set': {'is_used': True, 'used_by': str(current_user.id), 'used_at': datetime.now(timezone.utc)}})
            if result.modified_count == 0:
                raise HTTPException(status_code=400, detail='Mã nạp vừa được sử dụng bởi người dùng khác.')
            await users.update_one({'_id': str(current_user.id)}, {'$inc': {'wallet_balance': bonus_dl}})
            tx = Transaction(user_id=str(current_user.id), type=TransactionType.TOPUP, amount=bonus_dl, note=f'Đổi voucher: {req.code}')
            await transactions.insert_one(tx.model_dump(by_alias=True))
            if db_client.redis:
                try:
                    await db_client.redis.publish(f'user_notifications:{current_user.id}', json.dumps({'title': 'Nạp dl thành công', 'body': f'Tài khoản vừa được cộng thêm {bonus_dl} dl.'}))
                except Exception as e:
                    logger.warning(f'Redis publish notification failed: {e}')
            logger.info(f'User {current_user.id} redeemed voucher {req.code} for {bonus_dl} dl')
            return {'message': 'Đổi voucher thành công', 'bonus_dl': bonus_dl, 'status': 'success'}
        finally:
            if db_client.redis and is_locked:
                try:
                    await db_client.redis.delete(lock_key)
                except Exception as e:
                    logger.error(f'Failed to release Redis lock: {e}')

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
                logger.warning(f'Invalid cursor format: {e}')
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