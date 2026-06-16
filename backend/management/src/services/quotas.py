import math
from core.config import settings
from core.database import db_client
from src.schemas.quotas import QuotaLimit
from fastapi import HTTPException

class QuotaService:

    @staticmethod
    async def get_global_config_from_db(db=None) -> dict:
        config = await db_client.db.quota_configs.find_one({"_id": "global"})
        if config and "role_limits" in config:
            return config["role_limits"]

        default_limits = {
            "BASIC": {"daily_requests": 10, "daily_tokens": 3000, "req_reset_hours": 24, "max_docs": 1, "model": settings.QWEN_MODEL, "thinking": False},
            "PRO": {"daily_requests": 25, "daily_tokens": 7500, "req_reset_hours": 5, "max_docs": 5, "model": settings.LLAMA_MODEL, "thinking": False},
            "PREMIUM": {"daily_requests": 100, "daily_tokens": 30000, "req_reset_hours": 5, "max_docs": -1, "model": settings.LLAMA_MODEL, "thinking": True},
            "admin": {"daily_requests": math.inf, "daily_tokens": math.inf, "req_reset_hours": 0, "max_docs": math.inf, "model": settings.LLAMA_MODEL, "thinking": True},
        }
        await db_client.db.quota_configs.update_one({"_id": "global"}, {"$set": {"role_limits": default_limits}}, upsert=True)
        return default_limits

    @staticmethod
    async def update_role_quota(tier: str, limits_dict: dict, db=None):
        global_cfg = await QuotaService.get_global_config_from_db(db=db)
        if tier in global_cfg:
            global_cfg[tier].update(limits_dict)
            await db_client.db.quota_configs.update_one({"_id": "global"}, {"$set": {f"role_limits.{tier}": global_cfg[tier]}})

    @staticmethod
    async def get_user_limits(user_id: str, role: str, ai_tier: str = "BASIC", db=None) -> QuotaLimit:
        global_cfg = await QuotaService.get_global_config_from_db(db=db)
        target_tier = "admin" if role == "admin" else ai_tier
        tier_cfg = global_cfg.get(target_tier, global_cfg.get("BASIC", {}))

        def _parse_inf(val):
            return math.inf if val == -1 else val

        return QuotaLimit(
            daily_requests=_parse_inf(tier_cfg.get("daily_requests", 0)),
            daily_tokens=_parse_inf(tier_cfg.get("daily_tokens", 0)),
            req_reset_hours=tier_cfg.get("req_reset_hours", 24),
            max_docs=_parse_inf(tier_cfg.get("max_docs", 1)),
            model=tier_cfg.get("model", settings.QWEN_MODEL),
            thinking=tier_cfg.get("thinking", False),
        )

    @staticmethod
    async def check_quota(user_id: str, role: str, ai_tier: str = "BASIC", feature: str = "chat", db=None) -> QuotaLimit:
        limits = await QuotaService.get_user_limits(user_id, role, ai_tier, db=db)
        req_key = f"quota:{user_id}:{feature}:req"
        current_reqs = await db_client.redis.get(req_key)
        current_reqs = int(current_reqs) if current_reqs else 0

        if current_reqs >= limits.daily_requests:
            raise HTTPException(status_code=429, detail="Lỗi xử lý tài khoản")

        token_key = f"quota:{user_id}:{feature}:token"
        current_tokens = await db_client.redis.get(token_key)
        current_tokens = int(current_tokens) if current_tokens else 0

        if current_tokens >= limits.daily_tokens:
            raise HTTPException(status_code=429, detail="Lỗi xử lý tài khoản")
            
        return limits

    @staticmethod
    async def consume_request(user_id: str, feature: str = "chat", req_reset_hours: int = 24, db=None):
        req_key = f"quota:{user_id}:{feature}:req"
        current = await db_client.redis.incr(req_key)
        if current == 1:
            await db_client.redis.expire(req_key, req_reset_hours * 3600)

    @staticmethod
    async def consume_tokens(user_id: str, tokens: int, feature: str = "chat", req_reset_hours: int = 24, db=None):
        if tokens <= 0:
            return
        token_key = f"quota:{user_id}:{feature}:token"
        current = await db_client.redis.incrby(token_key, tokens)
        if current == tokens:
            await db_client.redis.expire(token_key, req_reset_hours * 3600)

    @staticmethod
    async def get_current_usage(user_id: str, role: str, ai_tier: str = "BASIC", feature: str = "chat", db=None) -> dict:
        limits = await QuotaService.get_user_limits(user_id, role, ai_tier, db=db)
        used_reqs = int(await db_client.redis.get(f"quota:{user_id}:{feature}:req") or 0)
        used_tokens = int(await db_client.redis.get(f"quota:{user_id}:{feature}:token") or 0)
        return {
            "limit_requests": limits.daily_requests if limits.daily_requests != math.inf else -1,
            "limit_tokens": limits.daily_tokens if limits.daily_tokens != math.inf else -1,
            "used_requests": used_reqs,
            "used_tokens": used_tokens,
            "remaining_requests": max(0, limits.daily_requests - used_reqs) if limits.daily_requests != math.inf else -1,
            "remaining_tokens": max(0, limits.daily_tokens - used_tokens) if limits.daily_tokens != math.inf else -1,
            "tier": ai_tier,
            "reset_hours": limits.req_reset_hours,
        }