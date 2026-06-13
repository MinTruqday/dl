from core.database import db_client
from fastapi import HTTPException
from datetime import datetime, timezone, timedelta
import uuid
from uuid6 import uuid7
from loguru import logger
from core.schemas.wallet import Transaction, TransactionType
from core.schemas.user import UserInDB

class SubscriptionService:

    @staticmethod
    async def create_subscription_plan(plan_data: dict, current_user: UserInDB, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        plan_doc = {'_id': str(uuid7()), 'author_id': str(current_user.id), 'name': plan_data['name'], 'description': plan_data['description'], 'price_dl': plan_data.get('price_dl'), 'benefits': plan_data.get('benefits', []), 'created_at': datetime.now(timezone.utc)}
        await db['subscription_plans'].insert_one(plan_doc)
        logger.info(f"Subscription: Author {current_user.id} created plan {plan_doc['name']}")
        return plan_doc

    @staticmethod
    async def subscribe_to_author(plan_id: str, current_user: UserInDB, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        plan = await db['subscription_plans'].find_one({'_id': plan_id})
        if not plan:
            raise HTTPException(status_code=404, detail='Gói đăng ký không tồn tại')
        author_id = plan['author_id']
        if author_id == str(current_user.id):
            raise HTTPException(status_code=400, detail='Bạn không thể đăng ký gói hội viên của chính mình')
        price = plan.get('price_dl', 0)
        user = await db['users'].find_one({'_id': str(current_user.id)})
        if not user or user.get('wallet_balance', 0) < price:
            raise HTTPException(status_code=400, detail=f'Số dư không đủ (Cần {price} dl).')
        existing = await db['subscriptions'].find_one({'user_id': str(current_user.id), 'plan_id': plan_id, 'status': {'$in': ['ACTIVE', 'PAUSED']}})
        if existing:
            raise HTTPException(status_code=400, detail='Bạn đã đăng ký gói hội viên này')
        session = await db_client.mongodb.start_session()
        try:
            async with session.start_transaction():
                deduct_result = await db['users'].update_one({'_id': str(current_user.id), 'wallet_balance': {'$gte': price}}, {'$inc': {'wallet_balance': -price}}, session=session)
                if deduct_result.modified_count == 0:
                    await session.abort_transaction()
                    raise HTTPException(status_code=400, detail='Số dư không đủ')
                await db['users'].update_one({'_id': author_id}, {'$inc': {'wallet_balance': price}}, session=session)
                subscription = {'_id': str(uuid7()), 'user_id': str(current_user.id), 'author_id': author_id, 'plan_id': plan_id, 'start_date': datetime.now(timezone.utc), 'end_date': datetime.now(timezone.utc) + timedelta(days=30), 'status': 'ACTIVE'}
                await db['subscriptions'].insert_one(subscription, session=session)
                tx_buyer = Transaction(user_id=str(current_user.id), type=TransactionType.SUBSCRIPTION, amount=-price, note=f"Đăng ký hội viên: {plan['name']}")
                tx_seller = Transaction(user_id=author_id, type=TransactionType.RECEIVE, amount=price, note=f"Hội viên mới đăng ký: {plan['name']}")
                await db['transactions'].insert_many([tx_buyer.model_dump(by_alias=True), tx_seller.model_dump(by_alias=True)], session=session)
                await session.commit_transaction()
                logger.info(f'Subscription: User {current_user.id} subscribed to author {author_id}')
                return {'message': 'Đã đăng ký gói hội viên', 'end_date': subscription['end_date'].isoformat()}
        except HTTPException:
            raise
        except Exception as e:
            await session.abort_transaction()
            logger.error(f'Subscription failed: {e}')
            raise HTTPException(status_code=500, detail='Giao dịch thất bại')
        finally:
            await session.end_session()

    @staticmethod
    async def get_my_subscriptions(current_user: UserInDB, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        subscriptions = await db['subscriptions'].find({'user_id': str(current_user.id)}).sort('created_at', -1).to_list(length=100)
        plan_ids = [s.get('plan_id') for s in subscriptions if s.get('plan_id')]
        plans = await db['subscription_plans'].find({'_id': {'$in': plan_ids}}).to_list(length=len(plan_ids) or 1)
        plan_map = {p['_id']: p for p in plans}
        result = []
        for s in subscriptions:
            plan = plan_map.get(s.get('plan_id'), {})
            result.append({'_id': str(s['_id']), 'plan_name': plan.get('name', 'Gói hội viên'), 'status': s.get('status'), 'end_date': s.get('end_date').isoformat() if isinstance(s.get('end_date'), datetime) else s.get('end_date')})
        return result

    @staticmethod
    async def pause_subscription(subscription_id: str, current_user: UserInDB, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        await db['subscriptions'].update_one({'_id': subscription_id, 'user_id': str(current_user.id), 'status': 'ACTIVE'}, {'$set': {'status': 'PAUSED', 'updated_at': datetime.now(timezone.utc)}})
        return {'message': 'Đã tạm dừng gói hội viên'}

    @staticmethod
    async def resume_subscription(subscription_id: str, current_user: UserInDB, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        await db['subscriptions'].update_one({'_id': subscription_id, 'user_id': str(current_user.id), 'status': 'PAUSED'}, {'$set': {'status': 'ACTIVE', 'updated_at': datetime.now(timezone.utc)}})
        return {'message': 'Đã tiếp tục gói hội viên'}

    @staticmethod
    async def cancel_subscription(subscription_id: str, current_user: UserInDB, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        await db['subscriptions'].update_one({'_id': subscription_id, 'user_id': str(current_user.id)}, {'$set': {'status': 'CANCELLED', 'updated_at': datetime.now(timezone.utc)}})
        return {'message': 'Đã hủy gói hội viên'}

    @staticmethod
    async def check_and_expire_subscriptions(db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        now = datetime.now(timezone.utc)
        result = await db['subscriptions'].update_many({'status': 'ACTIVE', 'end_date': {'$lt': now}}, {'$set': {'status': 'EXPIRED', 'updated_at': now}})
        if result.modified_count > 0:
            logger.info(f'Subscription: Expired {result.modified_count} subscriptions')
        return result.modified_count