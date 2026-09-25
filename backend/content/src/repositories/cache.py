from src.core.infrastructure.configuration import settings
from src.core.infrastructure.redis import redis


class DocumentCacheRepository:
    @staticmethod
    async def invalidate_document(document_id: str, slug: str | None = None):
        await redis.delete(f"document:{document_id}")
        if slug:
            await redis.delete(f"document:slug:{slug}")

    @staticmethod
    def _unlock_key(document_id: str, user_id: str | None):
        return f"rl:unlock:{document_id}:{user_id or 'anonymous'}"

    @staticmethod
    async def password_attempts(document_id: str, user_id: str | None):
        value = await redis.get(DocumentCacheRepository._unlock_key(document_id, user_id))
        return int(value) if value else 0

    @staticmethod
    async def record_password_failure(document_id: str, user_id: str | None):
        key = DocumentCacheRepository._unlock_key(document_id, user_id)
        await redis.incr(key)
        return await redis.expire(key, settings.DOCUMENT_PASSWORD_RATE_LIMIT_SECONDS)

    @staticmethod
    async def clear_password_failures(document_id: str, user_id: str | None):
        return await redis.delete(DocumentCacheRepository._unlock_key(document_id, user_id))
