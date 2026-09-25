import httpx
from fastapi import HTTPException

from src.core.configuration import settings


async def request_authentication(
    method: str,
    path: str,
    params: dict | None = None,
    payload: dict | None = None,
) -> httpx.Response:
    try:
        async with httpx.AsyncClient(
            timeout=settings.INTERNAL_REQUEST_TIMEOUT_SECONDS
        ) as client:
            return await client.request(
                method,
                f"{settings.AUTHENTICATION_URL.rstrip('/')}/{path.lstrip('/')}",
                headers={"X-Internal-Token": settings.SECRET_KEY},
                params=params,
                json=payload,
            )
    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=503, detail={"code": "AUTHENTICATION_UNAVAILABLE"}
        ) from error


async def load_accounts(user_ids: list[str]) -> dict:
    if not user_ids:
        return {}
    response = await request_authentication(
        "POST", "/xac-thuc/noi-bo/danh-tinh/tra-cuu", payload={"user_ids": user_ids}
    )
    if response.status_code >= 400:
        raise HTTPException(status_code=503, detail={"code": "AUTHENTICATION_UNAVAILABLE"})
    return response.json()["data"]


async def resolve_account(value: str) -> str:
    response = await request_authentication(
        "GET", "/xac-thuc/noi-bo/danh-tinh/giai-quyet", params={"value": value}
    )
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail={"code": "USER_NOT_FOUND"})
    if response.status_code >= 400:
        raise HTTPException(status_code=503, detail={"code": "AUTHENTICATION_UNAVAILABLE"})
    return str(response.json()["data"]["user_id"])


async def session_is_valid(session_id: str, user_id: str) -> bool:
    response = await request_authentication(
        "GET", f"/xac-thuc/noi-bo/phien/{session_id}/nguoi-dung/{user_id}"
    )
    if response.status_code >= 400:
        raise HTTPException(status_code=503, detail={"code": "AUTHENTICATION_UNAVAILABLE"})
    return bool(response.json()["data"]["valid"])


async def get_project_creation_policy() -> str:
    response = await request_authentication(
        "GET", "/xac-thuc/noi-bo/cau-hinh/chinh-sach-tao-du-an"
    )
    if response.status_code >= 400:
        raise HTTPException(status_code=503, detail={"code": "AUTHENTICATION_UNAVAILABLE"})
    return str(response.json()["data"]["project_creation_policy"])
