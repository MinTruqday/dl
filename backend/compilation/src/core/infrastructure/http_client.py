import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from loguru import logger
from fastapi import HTTPException
from src.core.infrastructure.configuration import settings

class CircuitBreakerOpenException(Exception):
    code = "circuit_breaker_open"

class InternalHttpClient:
    def __init__(self):
        self._client = httpx.AsyncClient(timeout=10.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=3),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        reraise=True
    )
    async def request(self, method: str, url: str, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["X-Internal-Token"] = settings.SECRET_KEY
        kwargs["headers"] = headers
        try:
            response = await self._client.request(method, url, **kwargs)
            
            if response.status_code >= 500:
                raise httpx.RequestError(f"Internal service error: {response.status_code}")
            return response
        except (httpx.RequestError, httpx.TimeoutException):
            logger.exception(f"Failed to execute internal HTTP request to endpoint {url}")
            raise

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
