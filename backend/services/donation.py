from datetime import datetime, timezone
from fastapi import HTTPException
from core.database import db_client
from models.wallet import Transaction, TransactionType
from loguru import logger

class DonationService:

    @staticmethod
    async def virtual_tip(target_user_id: str, amount: int, current_user, message: str='', db=None):
        if not target_user_id:
            raise HTTPException(status_code=400, detail='Mã người nhận không hợp lệ.')
        if db is None:
            db = db_client.mongodb.get_default_database()
        if target_user_id == str(current_user.id):
            raise HTTPException(status_code=400, detail='Bạn không thể tự tặng dl cho chính mình.')
        session = await db_client.mongodb.start_session()
        try:
            async with session.start_transaction():
                deduct_result = await db['users'].update_one({'_id': str(current_user.id), 'wallet_balance': {'$gte': amount}}, {'$inc': {'wallet_balance': -amount}}, session=session)
                if deduct_result.modified_count == 0:
                    await session.abort_transaction()
                    raise HTTPException(status_code=400, detail='Số dư ví không đủ.')
                await db['users'].update_one({'_id': target_user_id}, {'$inc': {'wallet_balance': amount}}, session=session)
                tx_sender = Transaction(user_id=str(current_user.id), type=TransactionType.TIP, amount=-amount, note=f'Ủng hộ cho người dùng {target_user_id}: {message}')
                tx_receiver = Transaction(user_id=target_user_id, type=TransactionType.RECEIVE, amount=amount, note=f'Nhận dl ủng hộ từ người dùng {current_user.id}: {message}')
                await db['transactions'].insert_many([tx_sender.model_dump(by_alias=True), tx_receiver.model_dump(by_alias=True)], session=session)
                await session.commit_transaction()
                logger.info(f'Donation: User {current_user.id} tipped {amount} dl to user {target_user_id}')
                return {'message': 'Đã thực hiện ủng hộ thành công.'}
        except HTTPException:
            raise
        except Exception as e:
            await session.abort_transaction()
            logger.error(f'Virtual tip failed for user {current_user.id}: {e}')
            raise HTTPException(status_code=500, detail='Giao dịch thất bại. Vui lòng thử lại sau.')
        finally:
            await session.end_session()

    @staticmethod
    async def get_top_donators(db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        pipeline = [{'$match': {'type': 'withdraw', 'amount': {'$lt': 0}, 'note': {'$regex': '^Tặng dl'}}}, {'$group': {'_id': '$user_id', 'total_donated': {'$sum': {'$abs': '$amount'}}}}, {'$sort': {'total_donated': -1}}, {'$limit': 5}, {'$lookup': {'from': 'users', 'localField': '_id', 'foreignField': '_id', 'as': 'user_info'}}, {'$unwind': {'path': '$user_info', 'preserveNullAndEmptyArrays': True}}]
        top_donators = await db['transactions'].aggregate(pipeline).to_list(length=5)
        result = []
        for td in top_donators:
            user = td.get('user_info', {})
            result.append({'user_id': td['_id'], 'name': user.get('full_name', 'Ẩn danh') if user else 'Ẩn danh', 'avatar': user.get('avatar_url') if user else None, 'total_donated': int(td['total_donated'])})
        return result