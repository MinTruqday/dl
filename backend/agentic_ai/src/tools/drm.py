import httpx
from langchain_core.tools import tool
from loguru import logger

from src.core.infrastructure.configuration import settings


async def _drm_request(path: str, params: dict, method: str = "GET") -> dict:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{settings.DRM_URL}{path}",
                params=params,
                headers={"X-Internal-Token": settings.SECRET_KEY},
                timeout=5.0,
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("DRM response must be an object")
            return payload
    except Exception as exc:
        logger.exception("DRM request failed")
        raise RuntimeError("DRM service unavailable") from exc


@tool
async def generate_dynamic_watermark(
    user_id: str,
    client_ip: str,
    email: str = "",
) -> dict:
    """
    <module_purpose>Generate a persisted DRM service watermark payload</module_purpose>
    <contract>Requires a user identifier and valid client IP address</contract>
    """
    return await _drm_request(
        "/bao-ve/thuy-an-dong",
        {"user_id": user_id, "client_ip": client_ip, "email": email},
    )


@tool
async def issue_temporary_aes_key(
    document_id: str,
    user_id: str,
    ttl_seconds: int = 300,
) -> dict:
    """
    <module_purpose>Issue a temporary AES key persisted by the DRM service</module_purpose>
    <contract>Requires an existing document and active user</contract>
    """
    return await _drm_request(
        "/bao-ve/cap-khoa-aes",
        {
            "document_id": document_id,
            "user_id": user_id,
            "ttl_seconds": ttl_seconds,
        },
        method="POST",
    )


@tool
async def verify_device_fingerprint(
    user_id: str,
    client_ip: str,
    device_fingerprint: str,
) -> dict:
    """
    <module_purpose>Verify an enrolled DRM device fingerprint and network address</module_purpose>
    <contract>Requires a nonempty enrolled device fingerprint</contract>
    """
    return await _drm_request(
        "/bao-ve/xac-minh-van-tay",
        {
            "user_id": user_id,
            "client_ip": client_ip,
            "device_fingerprint": device_fingerprint,
        },
    )


@tool
async def check_network_anomaly(user_id: str, client_ip: str) -> dict:
    """
    <module_purpose>Measure current network access behavior through the DRM service</module_purpose>
    <contract>Returns measured request and IP counts or raises when unavailable</contract>
    """
    return await _drm_request(
        "/bao-ve/kiem-tra-bat-thuong-mang",
        {"user_id": user_id, "client_ip": client_ip},
    )


@tool
async def get_user_trust_profile(user_id: str) -> dict:
    """
    <module_purpose>Calculate trust from persisted user license and access records</module_purpose>
    <contract>Requires an existing user</contract>
    """
    return await _drm_request(
        "/bao-ve/ho-so-tin-cay",
        {"user_id": user_id},
    )


@tool
async def analyze_document_risk(document_id: str) -> dict:
    """
    <module_purpose>Calculate document risk from persisted protection and dispute records</module_purpose>
    <contract>Requires an existing document</contract>
    """
    return await _drm_request(
        "/bao-ve/rui-ro-tai-lieu",
        {"document_id": document_id},
    )
