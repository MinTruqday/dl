import os

BACKEND_DIR = "backend"

http_client_content = """import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from loguru import logger
from fastapi import HTTPException
from src.core.infrastructure.configuration import settings

class CircuitBreakerOpenException(Exception):
    pass

class InternalHttpClient:
    def __init__(self):
        self._client = httpx.AsyncClient(timeout=settings.DEFAULT_HTTP_TIMEOUT)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=3),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        reraise=True
    )
    async def request(self, method: str, url: str, **kwargs):
        try:
            response = await self._client.request(method, url, **kwargs)
            # Fail-fast on 5xx errors for internal services
            if response.status_code >= 500:
                raise httpx.RequestError(f"Internal service error: {response.status_code}")
            return response
        except (httpx.RequestError, httpx.TimeoutException) as e:
            logger.error(f"HTTP call failed: {url} - {e}")
            raise e

    async def get(self, url: str, **kwargs):
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs):
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs):
        return await self.request("PUT", url, **kwargs)
        
    async def delete(self, url: str, **kwargs):
        return await self.request("DELETE", url, **kwargs)

    async def aclose(self):
        await self._client.aclose()

http_client = InternalHttpClient()
"""

for root, dirs, files in os.walk(BACKEND_DIR):
    if "core/infrastructure" in root:
        filepath = os.path.join(root, "http_client.py")
        with open(filepath, "w") as fp:
            fp.write(http_client_content)
            
print("Created http_client.py in all services.")
