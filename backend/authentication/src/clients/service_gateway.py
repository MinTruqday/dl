import httpx

from src.core.infrastructure.configuration import settings


SERVICE_BASE_URLS = {
    "ai": settings.AI_INTERNAL_URL.rstrip("/"),
    "authentication": settings.AUTHENTICATION_INTERNAL_URL.rstrip("/"),
    "cloud": settings.CLOUD_INTERNAL_URL.rstrip("/"),
    "content": settings.CONTENT_INTERNAL_URL.rstrip("/"),
    "testing": settings.TESTING_INTERNAL_URL.rstrip("/"),
    "worker": settings.WORKER_INTERNAL_URL.rstrip("/"),
}

SERVICE_HEALTH_PATHS = {
    "ai": "/suc-khoe",
    "authentication": "/san-sang",
    "cloud": "/san-sang",
    "content": "/san-sang",
    "testing": "/san-sang",
    "worker": "/san-sang",
}


def service_url(service_name: str, path: str = "") -> str:
    if path:
        return f"{SERVICE_BASE_URLS[service_name]}/{path.lstrip('/')}"
    return SERVICE_BASE_URLS[service_name]


def health_targets(service_names: tuple[str, ...]) -> dict[str, str]:
    return {
        service_name: service_url(service_name, SERVICE_HEALTH_PATHS[service_name])
        for service_name in service_names
    }


async def internal_request(
    method: str,
    service_name: str,
    path: str,
    *,
    params: dict | None = None,
    payload: dict | None = None,
    timeout: float | None = None,
) -> httpx.Response:
    request_timeout = timeout or settings.INTERNAL_REQUEST_TIMEOUT_SECONDS
    async with httpx.AsyncClient(timeout=request_timeout) as client:
        return await client.request(
            method,
            service_url(service_name, path),
            headers={"X-Internal-Token": settings.SECRET_KEY},
            params=params,
            json=payload,
        )


async def health_request(service_name: str) -> httpx.Response:
    return await internal_request(
        "GET", service_name, SERVICE_HEALTH_PATHS[service_name]
    )
