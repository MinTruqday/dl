import math
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from src.core.dependency import Role
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.mongo import mongo
from src.core.infrastructure.redis import redis
from src.core.logic_logger import log_logic_execution
from src.schemas.quota import QuotaLimit, Tier


def period_windows(user_id: str, feature: str) -> list[dict]:
    now = datetime.now(timezone.utc)
    tomorrow = datetime.combine(
        now.date() + timedelta(days=1), datetime.min.time(), timezone.utc
    )
    week_start = now - timedelta(
        days=now.weekday(),
        hours=now.hour,
        minutes=now.minute,
        seconds=now.second,
        microseconds=now.microsecond,
    )
    next_week = week_start + timedelta(days=7)
    iso_year, iso_week, _ = now.isocalendar()
    prefix = f"quota:{user_id}:{feature}"
    return [
        {
            "name": "session",
            "request_key": f"{prefix}:session:req",
            "token_key": f"{prefix}:session:token",
            "ttl": 5 * 3600,
            "reset_at": None,
        },
        {
            "name": "daily",
            "request_key": f"{prefix}:daily:{now.date().isoformat()}:req",
            "token_key": f"{prefix}:daily:{now.date().isoformat()}:token",
            "ttl": max(1, int((tomorrow - now).total_seconds())),
            "reset_at": tomorrow,
        },
        {
            "name": "weekly",
            "request_key": f"{prefix}:weekly:{iso_year}-{iso_week:02d}:req",
            "token_key": f"{prefix}:weekly:{iso_year}-{iso_week:02d}:token",
            "ttl": max(1, int((next_week - now).total_seconds())),
            "reset_at": next_week,
        },
    ]


class QuotaService:
    @staticmethod
    @log_logic_execution
    async def get_global_config_from_db() -> dict:
        config = await mongo.find_one(collection="quota_configs", query={"_id": "global"})
        if config and "role_limits" in config:
            role_limits = config["role_limits"]
            changed = False
            for values in role_limits.values():
                daily_requests = int(values.get("daily_requests", 0))
                daily_tokens = int(values.get("daily_tokens", 0))
                defaults = {
                    "session_requests": daily_requests,
                    "session_tokens": daily_tokens,
                    "weekly_requests": daily_requests * 7
                    if daily_requests >= 0
                    else -1,
                    "weekly_tokens": daily_tokens * 7 if daily_tokens >= 0 else -1,
                }
                for key, value in defaults.items():
                    if key not in values:
                        values[key] = value
                        changed = True
            if changed:
                await mongo.update_one(
                    "quota_configs",
                    {"_id": "global"},
                    {"$set": {"role_limits": role_limits}},
                )
            return role_limits
        default_limits = {
            "BASIC": {
                "session_requests": 10,
                "session_tokens": 3000,
                "daily_requests": 10,
                "daily_tokens": 3000,
                "weekly_requests": 40,
                "weekly_tokens": 12000,
                "req_reset_hours": 5,
                "max_docs": 1,
                "model": settings.LLM_MODEL,
                "thinking": False,
            },
            "PRO": {
                "session_requests": 25,
                "session_tokens": 7500,
                "daily_requests": 50,
                "daily_tokens": 15000,
                "weekly_requests": 250,
                "weekly_tokens": 75000,
                "req_reset_hours": 5,
                "max_docs": 5,
                "model": settings.LLM_MODEL,
                "thinking": True,
            },
            "PREMIUM": {
                "session_requests": 100,
                "session_tokens": 30000,
                "daily_requests": 200,
                "daily_tokens": 60000,
                "weekly_requests": 1000,
                "weekly_tokens": 300000,
                "req_reset_hours": 5,
                "max_docs": -1,
                "model": settings.LLM_MODEL,
                "thinking": True,
            },
            "admin": {
                "session_requests": -1,
                "session_tokens": -1,
                "daily_requests": -1,
                "daily_tokens": -1,
                "weekly_requests": -1,
                "weekly_tokens": -1,
                "req_reset_hours": 5,
                "max_docs": -1,
                "model": settings.LLM_MODEL,
                "thinking": True,
            },
        }
        await mongo.update_one(
            "quota_configs",
            {"_id": "global"},
            {"$set": {"role_limits": default_limits}},
            upsert=True,
        )
        return default_limits

    @staticmethod
    @log_logic_execution
    async def update_role_quota(tier: str, limits_dict: dict):
        tier_upper = tier.upper()
        tier = tier_upper if tier_upper != Role.ADMIN.value.upper() else Role.ADMIN.value
        global_cfg = await QuotaService.get_global_config_from_db()
        if tier not in global_cfg:
            raise HTTPException(status_code=404, detail="Không tìm thấy nhóm hạn mức yêu cầu")
        global_cfg[tier].update(limits_dict)
        await mongo.update_one(
            "quota_configs",
            {"_id": "global"},
            {"$set": {f"role_limits.{tier}": global_cfg[tier]}},
        )

    @staticmethod
    @log_logic_execution
    async def get_user_limits(
        user_id: str, role: str, ai_tier: str = "BASIC"
    ) -> QuotaLimit:
        global_cfg = await QuotaService.get_global_config_from_db()
        normalized_role = str(role).lower()
        normalized_tier = str(ai_tier).upper()
        target = Role.ADMIN.value if normalized_role == Role.ADMIN.value else normalized_tier
        cfg = global_cfg.get(target, global_cfg.get(Tier.BASIC.value, {}))
        daily_requests = int(cfg.get("daily_requests", 0))
        daily_tokens = int(cfg.get("daily_tokens", 0))
        return QuotaLimit(
            session_requests=int(cfg.get("session_requests", daily_requests)),
            session_tokens=int(cfg.get("session_tokens", daily_tokens)),
            daily_requests=daily_requests,
            daily_tokens=daily_tokens,
            weekly_requests=int(cfg.get("weekly_requests", daily_requests * 7)),
            weekly_tokens=int(cfg.get("weekly_tokens", daily_tokens * 7)),
            req_reset_hours=5,
            max_docs=cfg.get("max_docs", 1),
            model=settings.LLM_MODEL,
            thinking=cfg.get("thinking", False),
        )

    @staticmethod
    def limits_for_window(limits: QuotaLimit, name: str) -> tuple[int, int]:
        return (
            int(getattr(limits, f"{name}_requests")),
            int(getattr(limits, f"{name}_tokens")),
        )

    @staticmethod
    @log_logic_execution
    async def check_and_reserve_quota(
        user_id: str,
        role: str,
        ai_tier: str = "BASIC",
        feature: str = "chat",
    ):
        limits = await QuotaService.get_user_limits(user_id, role, ai_tier)
        windows = period_windows(user_id, feature)
        keys = []
        args = []
        for window in windows:
            request_limit, token_limit = QuotaService.limits_for_window(
                limits, window["name"]
            )
            keys.extend([window["request_key"], window["token_key"]])
            args.extend([request_limit, token_limit, window["ttl"]])
        script = """
for i=1,#KEYS,2 do
  local p=((i-1)/2)*3+1
  local requests=tonumber(redis.call('GET',KEYS[i]) or '0')
  local tokens=tonumber(redis.call('GET',KEYS[i+1]) or '0')
  local request_limit=tonumber(ARGV[p])
  local token_limit=tonumber(ARGV[p+1])
  if request_limit>=0 and requests>=request_limit then return -1 end
  if token_limit>=0 and tokens>=token_limit then return -2 end
end
for i=1,#KEYS,2 do
  local p=((i-1)/2)*3+1
  local value=redis.call('INCR',KEYS[i])
  if value==1 or redis.call('TTL',KEYS[i])<0 then redis.call('EXPIRE',KEYS[i],ARGV[p+2]) end
end
return 1
"""
        result = await redis.get_client().eval(script, len(keys), *keys, *args)
        if int(result) == -1:
            raise HTTPException(status_code=429, detail="Đã vượt quá hạn mức yêu cầu")
        if int(result) == -2:
            raise HTTPException(status_code=429, detail="Đã sử dụng hết hạn mức xử lý")
        return limits

    @staticmethod
    @log_logic_execution
    async def consume_tokens(
        user_id: str,
        tokens: int,
        feature: str = "chat",
        role: str = "reader",
        ai_tier: str = "BASIC",
        input_tokens: int = 0,
        output_tokens: int = 0,
        cached_tokens: int = 0,
        tool_tokens: int = 0,
    ):
        units = max(
            0,
            input_tokens
            + output_tokens * 3
            + tool_tokens * 2
            + math.ceil(cached_tokens * 0.25),
        )
        if units == 0:
            units = max(0, tokens)
        if units == 0:
            return
        limits = await QuotaService.get_user_limits(user_id, role, ai_tier)
        windows = period_windows(user_id, feature)
        keys = []
        args = []
        for window in windows:
            keys.extend([window["token_key"], window["request_key"]])
            _, limit = QuotaService.limits_for_window(limits, window["name"])
            args.extend([limit, window["ttl"]])
        script = """
for i=1,#KEYS,2 do
  local p=((i-1)/2)*2+1
  local value=redis.call('INCRBY',KEYS[i],ARGV[#ARGV])
  local anchor_ttl=redis.call('TTL',KEYS[i+1])
  local ttl=anchor_ttl>=0 and anchor_ttl or tonumber(ARGV[p+1])
  if value==tonumber(ARGV[#ARGV]) or redis.call('TTL',KEYS[i])<0 then redis.call('EXPIRE',KEYS[i],ttl) end
end
return 1
"""
        await redis.get_client().eval(script, len(keys), *keys, *args, units)

    @staticmethod
    @log_logic_execution
    async def get_current_usage(
        user_id: str, role: str, ai_tier: str = "BASIC", feature: str = "chat"
    ):
        limits = await QuotaService.get_user_limits(user_id, role, ai_tier)
        result = []
        for window in period_windows(user_id, feature):
            request_limit, token_limit = QuotaService.limits_for_window(
                limits, window["name"]
            )
            used_requests = int(await redis.get(window["request_key"]) or 0)
            used_tokens = int(await redis.get(window["token_key"]) or 0)
            reset_at = window["reset_at"]
            if window["name"] == "session":
                ttl = await redis.get_client().ttl(window["request_key"])
                if ttl < 0:
                    ttl = await redis.get_client().ttl(window["token_key"])
                reset_at = (
                    datetime.now(timezone.utc) + timedelta(seconds=ttl)
                    if ttl >= 0
                    else None
                )
            result.append(
                {
                    "name": window["name"],
                    "limit_requests": request_limit,
                    "limit_tokens": token_limit,
                    "used_requests": used_requests,
                    "used_tokens": used_tokens,
                    "remaining_requests": max(0, request_limit - used_requests)
                    if request_limit >= 0
                    else -1,
                    "remaining_tokens": max(0, token_limit - used_tokens)
                    if token_limit >= 0
                    else -1,
                    "reset_at": reset_at,
                }
            )
        daily = next(item for item in result if item["name"] == "daily")
        effective_tier = (
            Tier.PREMIUM.value
            if str(role).lower() == Role.ADMIN.value
            else ai_tier
        )
        return {**daily, "tier": effective_tier, "windows": result, "unit": "capacity"}

    @staticmethod
    @log_logic_execution
    async def reserve_upload_quota(
        user_id: str,
        role: str,
        ai_tier: str,
        item_type: str,
        req_reset_hours: int = 24,
    ):
        if role == Role.ADMIN.value:
            return True
        if item_type == "folder" and ai_tier != Tier.PREMIUM.value:
            raise HTTPException(status_code=403, detail="Yêu cầu quyền tải lên thư mục")
        limits = {Tier.BASIC.value: 1, Tier.PRO.value: 5, Tier.PREMIUM.value: math.inf}
        daily_limit = limits.get(ai_tier, 1)
        if daily_limit == math.inf:
            return True
        now = datetime.now(timezone.utc)
        tomorrow = datetime.combine(
            now.date() + timedelta(days=1), datetime.min.time(), timezone.utc
        )
        key = f"quota:{user_id}:upload_{item_type}:{now.date().isoformat()}"
        reservation = await redis.reserve_below_limit(
            key,
            int(daily_limit),
            max(1, int((tomorrow - now).total_seconds())),
        )
        if reservation < 0:
            raise HTTPException(status_code=429, detail="Đã vượt quá hạn mức tải lên")
        return reservation
