import asyncio
from typing import Optional
import httpx
import jwt
from loguru import logger
from src.core.infrastructure.configuration import settings

INTERNAL_API_URL = settings.INTERNAL_API_URL

_http_client: Optional[httpx.AsyncClient] = None

def get_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            timeout=httpx.Timeout(30.0),
        )
    return _http_client

async def make_api_request(method: str, url: str, **kwargs) -> httpx.Response:
    from uuid6 import uuid7

    if method.upper() in ["POST", "PUT", "PATCH", "DELETE"]:
        headers = kwargs.get("headers", {})
        if "Idempotency-Key" not in headers:
            headers["Idempotency-Key"] = str(uuid7())
        kwargs["headers"] = headers

    max_retries = 3 if method.upper() == "GET" else 1
    client = get_client()
    for attempt in range(max_retries):
        try:
            response = await client.request(method, url, **kwargs)
            if response.status_code not in [429, 500, 502, 503, 504]:
                return response
            if attempt == max_retries - 1:
                response.raise_for_status()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
        await asyncio.sleep(2**attempt)
    return response

def check_system_access(token: str) -> bool:
    try:
        raw_token = token.removeprefix("Bearer ").strip()
        payload = jwt.decode(raw_token, settings.SECRET_KEY, algorithms=["HS256"])
        from src.schemas.auth import Role
        return role == Role.ADMIN.value
    except Exception:
        return False
