from src.core.infrastructure.configuration import settings
from src.core.infrastructure.redis import redis


class CacheRepository:
    @staticmethod
    async def store_google_oauth_state(state: str):
        return await redis.setex(
            f"google_oauth_state:{state}",
            settings.GOOGLE_OAUTH_STATE_EXPIRE_SECONDS,
            "valid",
        )

    @staticmethod
    async def consume_google_oauth_state(state: str):
        return await redis.get_client().getdel(f"google_oauth_state:{state}")

    @staticmethod
    async def count_patterns(patterns: list[str]):
        client = redis.get_client()
        total = 0
        for pattern in patterns:
            async for _ in client.scan_iter(match=pattern):
                total += 1
        return total

    @staticmethod
    async def delete_patterns(patterns: list[str]):
        client = redis.get_client()
        keys = []
        for pattern in patterns:
            keys.extend([key async for key in client.scan_iter(match=pattern)])
        if keys:
            await client.delete(*keys)
        return len(keys)
