import httpx
import json
from src.core.infrastructure.configuration import settings

class RedisAPIClient:
    def __init__(self):
        self.base_url = settings.CACHE_URL
        self._client = None

    def get_client(self):
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)
        return self._client

    async def _post(self, path: str, json_data: dict):
        try:
            client = self.get_client()
            response = await client.post(path, json=json_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return None

    async def set(self, key: str, value: str):
        return await self._post("/set", {"key": key, "value": value})

    async def setex(self, key: str, expire: int, value: str):
        return await self._post("/set", {"key": key, "value": value, "expire": expire})

    async def get(self, key: str):
        res = await self._post("/get", {"key": key})
        return res.get("value") if res else None

    async def delete(self, key: str):
        return await self._post("/delete", {"key": key})

    async def sadd(self, key: str, member: str):
        return await self._post("/sadd", {"key": key, "member": member})

    async def sismember(self, key: str, member: str):
        res = await self._post("/sismember", {"key": key, "member": member})
        return res.get("is_member") if res else False

    async def smembers(self, key: str):
        res = await self._post("/smembers", {"key": key})
        return res.get("members") if res else []

    async def publish(self, channel: str, message: str):
        return await self._post("/publish", {"channel": channel, "message": message})

    async def pipeline_incr_expire(self, key: str, expire: int):
        res = await self._post("/pipeline_incr", {"key": key, "expire": expire})
        return res.get("values") if res else []


    async def aclose(self):
        if hasattr(self, '_client'):
            await self._client.aclose()

redis_client = RedisAPIClient()
