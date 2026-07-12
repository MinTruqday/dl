import httpx
from langchain_core.tools import tool
from loguru import logger
from src.core.infrastructure.configuration import settings

@tool
async def check_network_anomaly(user_id: str, client_ip: str) -> dict:
    """
    Check network behavior for anomalies (e.g. rate-limiting, IP hopping) within the last minute.

    WHEN TO USE THIS TOOL:
    Use this when you suspect a user might be performing suspicious activities, sending too many requests, or sharing accounts.

    CRITICAL: Requires the exact user_id and client_ip. Returns a dict containing anomaly flags.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.DRM_URL}/bao-ve/kiem-tra-bat-thuong-mang",
                params={"user_id": user_id, "client_ip": client_ip},
                headers={"X-Internal-Token": settings.SECRET_KEY},
                timeout=5.0
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.exception("Failed to check network anomaly via DRM service")
        return {"system_flag_anomaly": False, "error": str(e)}

@tool
async def get_user_trust_profile(user_id: str, user_tier: str = "BASIC") -> dict:
    """
    Retrieve the trust profile of the user (e.g., trust score based on user tier).

    WHEN TO USE THIS TOOL:
    Use this when evaluating whether a user should be permitted to perform a sensitive action (like mass exporting, bulk downloading, or modifying critical data).
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.DRM_URL}/bao-ve/ho-so-tin-cay",
                params={"user_id": user_id, "user_tier": user_tier},
                headers={"X-Internal-Token": settings.SECRET_KEY},
                timeout=5.0
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.exception("Failed to get trust profile via DRM service")
        return {"user_id": user_id, "trust_score": 50, "error": str(e)}

@tool
async def analyze_document_risk(document_id: str, document_type: str = "standard") -> dict:
    """
    Analyze the risk level of the document (e.g. 'sensitive', 'exam', 'premium').

    WHEN TO USE THIS TOOL:
    Use this when a user is trying to access or manipulate a document, and you need to verify if the document's risk level permits the requested action.

    CRITICAL: Returns 'HIGH' or 'LOW' risk level.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.DRM_URL}/bao-ve/rui-ro-tai-lieu",
                params={"document_id": document_id, "document_type": document_type},
                headers={"X-Internal-Token": settings.SECRET_KEY},
                timeout=5.0
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.exception("Failed to analyze document risk via DRM service")
        return {"document_id": document_id, "risk_level": "HIGH", "error": str(e)}
