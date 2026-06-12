from core.database import db_client
from core.config import settings
from fastapi import HTTPException
from datetime import datetime, timezone
from loguru import logger
from src.schemas.quota import QuotaLimit, GlobalQuotaConfig
import json

class QuotaService:

    @staticmethod
    async def _get_global_config(db=None):
        if db is None:
            db = db_client.mongodb[settings.MONGODB_DB_NAME]
        config_data = await db['quota_configs'].find_one({'_id': 'global'})
        default_config = GlobalQuotaConfig()
        if not config_data:
            await db['quota_configs'].insert_one({'_id': 'global', **default_config.model_dump()})
            return default_config
        db_role_limits = config_data.get('role_limits', {})
        merged_limits = default_config.role_limits.copy()
        for (role, limits) in db_role_limits.items():
            if role in merged_limits:
                merged_limits[role] = QuotaLimit(**limits)
        default_config.role_limits = merged_limits
        return default_config

    @staticmethod
    async def get_user_limits(user_id: str, role: str, db=None) -> QuotaLimit:
        if db is None:
            db = db_client.mongodb[settings.MONGODB_DB_NAME]
        user_override = await db['user_quotas'].find_one({'user_id': user_id})
        if user_override:
            return QuotaLimit(**user_override['limits'])
        global_config = await QuotaService._get_global_config()
        return global_config.role_limits.get(role, global_config.role_limits['reader'])

    @staticmethod
    async def check_quota(user_id: str, role: str, feature: str='chat', db=None):
        limits = await QuotaService.get_user_limits(user_id, role)
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        req_key = f'quota:{user_id}:{feature}:req:{today}'
        current_reqs = await db_client.redis.get(req_key)
        current_reqs = int(current_reqs) if current_reqs else 0
        if current_reqs >= limits.daily_requests:
            raise HTTPException(status_code=429, detail='Bạn đã hết lượt yêu cầu trong ngày')
        token_key = f'quota:{user_id}:{feature}:token:{today}'
        current_tokens = await db_client.redis.get(token_key)
        current_tokens = int(current_tokens) if current_tokens else 0
        if current_tokens >= limits.daily_tokens:
            raise HTTPException(status_code=429, detail='Bạn đã hết hạn mức token trong ngày')
        return limits

    @staticmethod
    async def consume_request(user_id: str, feature: str='chat', db=None):
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        req_key = f'quota:{user_id}:{feature}:req:{today}'
        await db_client.redis.incr(req_key)
        await db_client.redis.expire(req_key, 86400)

    @staticmethod
    async def consume_tokens(user_id: str, tokens: int, feature: str='chat', db=None):
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        token_key = f'quota:{user_id}:{feature}:token:{today}'
        await db_client.redis.incrby(token_key, tokens)
        await db_client.redis.expire(token_key, 86400)

    @staticmethod
    async def get_current_usage(user_id: str, role: str, feature: str='chat', db=None):
        limits = await QuotaService.get_user_limits(user_id, role)
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        req_key = f'quota:{user_id}:{feature}:req:{today}'
        token_key = f'quota:{user_id}:{feature}:token:{today}'
        used_reqs = int(await db_client.redis.get(req_key) or 0)
        used_tokens = int(await db_client.redis.get(token_key) or 0)
        return {'limit_requests': limits.daily_requests, 'limit_tokens': limits.daily_tokens, 'used_requests': used_reqs, 'used_tokens': used_tokens, 'remaining_requests': max(0, limits.daily_requests - used_reqs), 'remaining_tokens': max(0, limits.daily_tokens - used_tokens)}

    @staticmethod
    async def update_global_limits(role: str, limits: QuotaLimit, db=None):
        if db is None:
            db = db_client.mongodb[settings.MONGODB_DB_NAME]
        await db['quota_configs'].update_one({'_id': 'global'}, {'$set': {f'role_limits.{role}': limits.model_dump(), 'updated_at': datetime.now(timezone.utc)}}, upsert=True)
        return {'message': f'Cập nhật hạn mức cho nhóm {role}'}