from src.core.infrastructure.redis import redis
from src.core.infrastructure.mongo import mongo
import json
import math
from datetime import datetime, timezone

from fastapi import HTTPException
from loguru import logger

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.schemas.quota import QuotaLimit

class QuotaService:
    @staticmethod
    async def get_global_config_from_db() -> dict:
        config = await mongo.find_one(collection="quota_configs", query={"_id": "global"})
        if config and "role_limits" in config:
            return config["role_limits"]

        default_limits = {
            "BASIC": {
                "daily_requests": 10,
                "daily_tokens": 3000,
                "req_reset_hours": 24,
                "max_docs": 1,
                "model": settings.QWEN_MODEL,
                "thinking": False,
            },
            "PRO": {
                "daily_requests": 25,
                "daily_tokens": 7500,
                "req_reset_hours": 5,
                "max_docs": 5,
                "model": settings.LLAMA_MODEL,
                "thinking": False,
            },
            "PREMIUM": {
                "daily_requests": 100,
                "daily_tokens": 30000,
                "req_reset_hours": 5,
                "max_docs": -1,
                "model": settings.LLAMA_MODEL,
                "thinking": True,
            },
            "admin": {
                "daily_requests": -1,
                "daily_tokens": -1,
                "req_reset_hours": 24,
                "max_docs": -1,
                "model": settings.LLAMA_MODEL,
                "thinking": True,
            },
        }

        await db.quota_configs.update_one(
            {"_id": "global"}, {"$set": {"role_limits": default_limits}}, upsert=True
        )
        return default_limits

    @staticmethod
    async def update_role_quota(tier: str, limits_dict: dict):
        global_cfg = await QuotaService.get_global_config_from_db()
        if tier in global_cfg:
            global_cfg[tier].update(limits_dict)
            await db.quota_configs.update_one(
                {"_id": "global"}, {"$set": {f"role_limits.{tier}": global_cfg[tier]}}
            )

    @staticmethod
    async def get_user_limits(
        user_id: str, role: str, ai_tier: str = "BASIC"
    ) -> QuotaLimit:
        global_cfg = await QuotaService.get_global_config_from_db()

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
    async def check_quota(
        user_id: str, role: str, ai_tier: str = "BASIC", feature: str = "chat"
    ):
        limits = await QuotaService.get_user_limits(user_id, role, ai_tier)

        req_key = f"quota:{user_id}:{feature}:req"
        current_reqs = await redis.get(req_key)
        current_reqs = int(current_reqs) if current_reqs else 0

        if current_reqs >= limits.daily_requests:
            raise HTTPException(
                status_code=429, detail="Đã vượt quá giới hạn yêu cầu trong ngày"
            )

        token_key = f"quota:{user_id}:{feature}:token"
        current_tokens = await redis.get(token_key)
        current_tokens = int(current_tokens) if current_tokens else 0

        if current_tokens >= limits.daily_tokens:
            raise HTTPException(
                status_code=429, detail="Đã hết hạn mức sử dụng mã thông báo trong ngày"
            )
        return limits

    @staticmethod
    async def consume_request(
        user_id: str, feature: str = "chat", req_reset_hours: int = 24
    ):
        req_key = f"quota:{user_id}:{feature}:req"
        current = await redis.incr(req_key)
        if current == 1:
            await redis.expire(req_key, req_reset_hours * 3600)

    @staticmethod
    async def consume_tokens(
        user_id: str,
        tokens: int,
        feature: str = "chat",
        req_reset_hours: int = 24,
    ):
        if tokens <= 0:
            return
        token_key = f"quota:{user_id}:{feature}:token"
        current = await redis.incrby(token_key, tokens)
        if current == tokens:
            await redis.expire(token_key, req_reset_hours * 3600)

    @staticmethod
    async def get_current_usage(
        user_id: str, role: str, ai_tier: str = "BASIC", feature: str = "chat"
    ):
        limits = await QuotaService.get_user_limits(user_id, role, ai_tier)
        req_key = f"quota:{user_id}:{feature}:req"
        token_key = f"quota:{user_id}:{feature}:token"
        used_reqs = int(await redis.get(req_key) or 0)
        used_tokens = int(await redis.get(token_key) or 0)
        return {
            "limit_requests": (
                limits.daily_requests if limits.daily_requests != math.inf else -1
            ),
            "limit_tokens": (
                limits.daily_tokens if limits.daily_tokens != math.inf else -1
            ),
            "used_requests": used_reqs,
            "used_tokens": used_tokens,
            "remaining_requests": (
                max(0, limits.daily_requests - used_reqs)
                if limits.daily_requests != math.inf
                else -1
            ),
            "remaining_tokens": (
                max(0, limits.daily_tokens - used_tokens)
                if limits.daily_tokens != math.inf
                else -1
            ),
            "tier": ai_tier,
            "reset_hours": limits.req_reset_hours,
        }
