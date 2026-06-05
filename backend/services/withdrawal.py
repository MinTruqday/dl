from core.database import db_client
from fastapi import HTTPException
from datetime import datetime, timezone
from uuid6 import uuid7
from loguru import logger
from models.wallet import Transaction, TransactionType

ALLOWED_WITHDRAWAL_QUEUE_STATUSES = {'PENDING', 'APPROVED', 'REJECTED', 'CANCELLED'}
ALLOWED_WITHDRAWAL_ACTIONS = {'approve', 'reject'}

class WithdrawalService:

    @staticmethod
    async def get_revenue(current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        pipeline = [{'$match': {'user_id': str(current_user.id), 'type': {'$in': ['receive', 'tip']}}}, {'$group': {'_id': None, 'total_revenue': {'$sum': '$amount'}}}]
        cursor = db['transactions'].aggregate(pipeline)
        res = await cursor.to_list(length=1)
        total_revenue = res[0]['total_revenue'] if res else 0
        withdrawal_res = await db['withdrawal_requests'].aggregate([{'$match': {'user_id': str(current_user.id), 'status': 'PENDING'}}, {'$group': {'_id': None, 'pending': {'$sum': '$amount'}}}]).to_list(length=1)
        pending_withdrawal = withdrawal_res[0]['pending'] if withdrawal_res else 0
        return {'total_revenue': total_revenue, 'pending_withdrawal': pending_withdrawal, 'currency': 'dl'}

    @staticmethod
    async def request_withdrawal(data: dict, current_user, db=None, session=None) -> dict:
        should_close_session = False
        if db is None:
            db = db_client.mongodb.get_default_database()
            
        if session is None:
            session = await db_client.mongodb.start_session()
            session.start_transaction()
            should_close_session = True
            
        amount = int(data.get('amount', 0))
        bank_info = data.get('bank_info', '')
        if amount < 100000:
            if should_close_session: await session.abort_transaction(); await session.end_session()
            raise HTTPException(status_code=400, detail='Số tiền rút tối thiểu là 100,000 dl.')
            
        wallet = await db['users'].find_one({'_id': str(current_user.id)})
        if not wallet or wallet.get('wallet_balance', 0) < amount:
            if should_close_session: await session.abort_transaction(); await session.end_session()
            raise HTTPException(status_code=400, detail='Số dư không đủ để thực hiện yêu cầu rút tiền.')

        now = datetime.now(timezone.utc)
        
        # AML Cooldown
        if wallet.get('last_password_change'):
            last_pw = wallet['last_password_change'].replace(tzinfo=timezone.utc) if wallet['last_password_change'].tzinfo is None else wallet['last_password_change']
            if (now - last_pw).total_seconds() < 86400:
                if should_close_session: await session.abort_transaction(); await session.end_session()
                raise HTTPException(status_code=403, detail='Không thể rút tiền trong vòng 24h sau khi đổi mật khẩu để bảo vệ tài sản.')
                
        if wallet.get('last_bank_update'):
            last_bank = wallet['last_bank_update'].replace(tzinfo=timezone.utc) if wallet['last_bank_update'].tzinfo is None else wallet['last_bank_update']
            if (now - last_bank).total_seconds() < 86400:
                if should_close_session: await session.abort_transaction(); await session.end_session()
                raise HTTPException(status_code=403, detail='Không thể rút tiền trong vòng 24h sau khi cập nhật thông tin ngân hàng.')

        # AML Velocity Limits
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        daily_withdrawals = await db['withdrawal_requests'].aggregate([
            {'$match': {'user_id': str(current_user.id), 'created_at': {'$gte': today_start}, 'status': {'$in': ['PENDING', 'APPROVED']}}},
            {'$group': {'_id': None, 'count': {'$sum': 1}, 'total_amount': {'$sum': '$amount'}}}
        ]).to_list(length=1)
        
        if daily_withdrawals:
            stats = daily_withdrawals[0]
            if stats['count'] >= 3:
                if should_close_session: await session.abort_transaction(); await session.end_session()
                raise HTTPException(status_code=429, detail='Vượt quá giới hạn rút tiền (tối đa 3 lần/ngày).')
            if stats['total_amount'] + amount > 20000000:
                if should_close_session: await session.abort_transaction(); await session.end_session()
                raise HTTPException(status_code=429, detail='Vượt quá hạn mức rút tiền (tối đa 20.000.000 dl/ngày).')

        withdrawal_id = str(uuid7())
        try:
            deduct_result = await db['users'].update_one({'_id': str(current_user.id), 'wallet_balance': {'$gte': amount}}, {'$inc': {'wallet_balance': -amount}}, session=session)
            if deduct_result.modified_count == 0:
                if should_close_session: await session.abort_transaction()
                raise HTTPException(status_code=400, detail='Số dư không đủ để thực hiện yêu cầu rút tiền.')
                
            withdrawal_request = {'_id': withdrawal_id, 'user_id': str(current_user.id), 'amount': amount, 'bank_info': bank_info, 'status': 'PENDING', 'created_at': datetime.now(timezone.utc)}
            await db['withdrawal_requests'].insert_one(withdrawal_request, session=session)
            transaction = Transaction(user_id=str(current_user.id), amount=-amount, type=TransactionType.WITHDRAW, note=f'Yêu cầu rút tiền {withdrawal_id}', reference_id=withdrawal_id)
            await db['transactions'].insert_one(transaction.model_dump(by_alias=True), session=session)
            
            if should_close_session:
                await session.commit_transaction()
                
            masked_bank_info = bank_info[:4] + "***" + bank_info[-3:] if len(bank_info) > 8 else "***"
            logger.info(f'Withdrawal: Requested by user {current_user.id} for {amount} dl. Bank: {masked_bank_info}')
            return {'message': 'Yêu cầu rút tiền đã được gửi thành công.', 'withdrawal_id': withdrawal_id}
        except HTTPException:
            raise
        except Exception as e:
            if should_close_session:
                await session.abort_transaction()
            logger.exception(f'Withdrawal: Request failed for user {current_user.id}: {e}')
            raise HTTPException(status_code=500, detail='Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.')
        finally:
            if should_close_session:
                await session.end_session()

    @staticmethod
    async def get_withdrawal_queue(status: str='pending', db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        normalized_status = status.upper()
        if normalized_status not in ALLOWED_WITHDRAWAL_QUEUE_STATUSES:
            raise HTTPException(status_code=400, detail='Trạng thái yêu cầu rút tiền không hợp lệ.')
        pipeline = [{'$match': {'status': normalized_status}}, {'$sort': {'created_at': -1}}, {'$limit': 100}, {'$lookup': {'from': 'users', 'localField': 'user_id', 'foreignField': '_id', 'as': 'user_info'}}, {'$unwind': {'path': '$user_info', 'preserveNullAndEmptyArrays': True}}]
        withdrawals = await db['withdrawal_requests'].aggregate(pipeline).to_list(length=100)
        result = []
        for p in withdrawals:
            user = p.get('user_info', {})
            result.append({
                '_id': str(p['_id']), 
                'user_id': p.get('user_id'), 
                'user_name': user.get('full_name') if user else 'Unknown', 
                'amount': p.get('amount'), 
                'status': p.get('status'), 
                'bank_info': p.get('bank_info', {}),
                'created_at': p['created_at'].isoformat() if isinstance(p.get('created_at'), datetime) else p.get('created_at')
            })
        return result

    @staticmethod
    async def verify_withdrawal(withdrawal_id: str, action: str, current_moderator, db=None, session=None) -> dict:
        should_close_session = False
        if db is None:
            db = db_client.mongodb.get_default_database()
            
        if session is None:
            session = await db_client.mongodb.start_session()
            session.start_transaction()
            should_close_session = True
            
        normalized_action = action.strip().lower()
        if normalized_action not in ALLOWED_WITHDRAWAL_ACTIONS:
            if should_close_session: await session.abort_transaction(); await session.end_session()
            raise HTTPException(status_code=400, detail='Hành động xử lý yêu cầu rút tiền không hợp lệ.')
            
        withdrawal = await db['withdrawal_requests'].find_one({'_id': withdrawal_id})
        if not withdrawal:
            if should_close_session: await session.abort_transaction(); await session.end_session()
            raise HTTPException(status_code=404, detail='Không tìm thấy yêu cầu rút tiền.')
            
        if str(current_moderator.id) == withdrawal.get('user_id'):
            if should_close_session: await session.abort_transaction(); await session.end_session()
            raise HTTPException(status_code=403, detail="Không thể tự duyệt yêu cầu của chính mình.")
            
        current_status = withdrawal.get('status')
        if current_status != 'PENDING':
            if should_close_session: await session.abort_transaction(); await session.end_session()
            raise HTTPException(status_code=400, detail='Yêu cầu rút tiền đã được xử lý trước đó.')
            
        status = 'APPROVED' if normalized_action == 'approve' else 'REJECTED'
        
        try:
            update_result = await db['withdrawal_requests'].update_one({'_id': withdrawal_id, 'status': 'PENDING'}, {'$set': {'status': status, 'processed_by': str(current_moderator.id), 'processed_at': datetime.now(timezone.utc)}}, session=session)
            if update_result.modified_count == 0:
                if should_close_session: await session.abort_transaction()
                raise HTTPException(status_code=400, detail="Không thể cập nhật trạng thái yêu cầu.")
                
            if status == 'REJECTED':
                await db['users'].update_one({'_id': withdrawal.get('user_id')}, {'$inc': {'wallet_balance': withdrawal.get('amount', 0)}}, session=session)
                refund_transaction = Transaction(user_id=withdrawal.get('user_id'), amount=withdrawal.get('amount', 0), type=TransactionType.REFUND, note=f'Hoàn tiền yêu cầu rút tiền {withdrawal_id}', reference_id=withdrawal_id)
                await db['transactions'].insert_one(refund_transaction.model_dump(by_alias=True), session=session)
                
            bank_info = str(withdrawal.get('bank_info', ''))
            masked_bank = bank_info[:4] + "***" + bank_info[-3:] if len(bank_info) > 8 else "***"
            await db['audit_logs'].insert_one({'action': f'WITHDRAWAL_{status}', 'actor_id': str(current_moderator.id), 'withdrawal_id': withdrawal_id, 'bank_info_masked': masked_bank, 'timestamp': datetime.now(timezone.utc)}, session=session)
            
            if should_close_session:
                await session.commit_transaction()
                
            logger.info(f'Audit: Withdrawal {withdrawal_id} {status} by moderator {current_moderator.id}')
            return {'message': f'Đã {status.lower()} yêu cầu rút tiền thành công.'}
        except HTTPException:
            raise
        except Exception as e:
            if should_close_session:
                await session.abort_transaction()
            logger.exception(f'Withdrawal: Verify failed for {withdrawal_id}: {e}')
            raise HTTPException(status_code=500, detail='Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.')
        finally:
            if should_close_session:
                await session.end_session()

    @staticmethod
    async def cancel_withdrawal(withdrawal_id: str, current_user, db=None, session=None) -> dict:
        should_close_session = False
        if db is None:
            db = db_client.mongodb.get_default_database()
            
        if session is None:
            session = await db_client.mongodb.start_session()
            session.start_transaction()
            should_close_session = True
            
        withdrawal = await db['withdrawal_requests'].find_one({'_id': withdrawal_id, 'user_id': str(current_user.id)})
        if not withdrawal:
            if should_close_session: await session.abort_transaction(); await session.end_session()
            raise HTTPException(status_code=404, detail='Không tìm thấy yêu cầu rút tiền.')
        if withdrawal.get('status') != 'PENDING':
            if should_close_session: await session.abort_transaction(); await session.end_session()
            raise HTTPException(status_code=400, detail='Chỉ có thể hủy yêu cầu đang chờ xử lý.')
            
        try:
            update_result = await db['withdrawal_requests'].update_one({'_id': withdrawal_id, 'user_id': str(current_user.id), 'status': 'PENDING'}, {'$set': {'status': 'CANCELLED', 'cancelled_at': datetime.now(timezone.utc)}}, session=session)
            if update_result.modified_count == 0:
                if should_close_session: await session.abort_transaction()
                raise HTTPException(status_code=400, detail="Không thể cập nhật trạng thái yêu cầu.")
                
            await db['users'].update_one({'_id': str(current_user.id)}, {'$inc': {'wallet_balance': withdrawal.get('amount', 0)}}, session=session)
            refund_transaction = Transaction(user_id=str(current_user.id), amount=withdrawal.get('amount', 0), type=TransactionType.TOPUP, note=f'Hủy yêu cầu rút tiền {withdrawal_id}', reference_id=withdrawal_id)
            await db['transactions'].insert_one(refund_transaction.model_dump(by_alias=True), session=session)
            
            if should_close_session:
                await session.commit_transaction()
                
            logger.info(f'Withdrawal: {withdrawal_id} cancelled by user {current_user.id}')
            return {'message': 'Đã hủy yêu cầu rút tiền thành công.'}
        except HTTPException:
            raise
        except Exception as e:
            if should_close_session:
                await session.abort_transaction()
            logger.exception(f'Withdrawal: Cancel failed for {withdrawal_id}: {e}')
            raise HTTPException(status_code=500, detail='Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.')
        finally:
            if should_close_session:
                await session.end_session()

    @staticmethod
    async def get_my_withdrawals(current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        withdrawals = await db['withdrawal_requests'].find({'user_id': str(current_user.id)}).sort('created_at', -1).to_list(length=100)
        return withdrawals