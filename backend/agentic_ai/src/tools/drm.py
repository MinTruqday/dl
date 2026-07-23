import hashlib
import json
import secrets
from typing import Dict, Optional
import httpx
from langchain_core.tools import tool
from loguru import logger
from src.core.infrastructure.configuration import settings

@tool
async def generate_dynamic_watermark(user_id: str, client_ip: str, email: str = "") -> dict:
    """
    <module_purpose>Generate contextual dynamic micro-watermark payload for client rendering (Zero Token Cost).</module_purpose>
    <contract>Requires user_id and client_ip. Returns SVG/Canvas watermark token dictionary.</contract>
    """
    import datetime
    timestamp_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    display_text = f"CONFIDENTIAL | {email or user_id} | {client_ip} | {timestamp_str}"
    watermark_token = hashlib.sha256(f"{user_id}:{client_ip}:{timestamp_str}".encode()).hexdigest()[:16]

    return {
        "enabled": True,
        "text": display_text,
        "watermark_token": watermark_token,
        "opacity": 0.15,
        "font_size": 16,
        "color": "#888888"
    }

@tool
async def issue_temporary_aes_key(document_id: str, user_id: str, ttl_seconds: int = 300) -> dict:
    """
    <module_purpose>Generate temporary 256-bit AES-GCM decryption key stored in Redis with TTL (Zero Token Cost).</module_purpose>
    <contract>Requires document_id and user_id. Returns key_id, key_hex, and expiration TTL.</contract>
    """
    try:
        key_id = f"aes_key:{document_id}:{user_id}:{secrets.token_hex(4)}"
        raw_key = secrets.token_hex(32)

        import redis as redis_lib
        redis_client = redis_lib.from_url(settings.REDIS_URI, decode_responses=True)
        redis_client.setex(key_id, ttl_seconds, raw_key)

        return {
            "key_id": key_id,
            "key_hex": raw_key,
            "ttl_seconds": ttl_seconds,
            "status": "issued"
        }
    except Exception as e:
        logger.warning(f"Redis key issuance fallback: {e}")
        fallback_key = secrets.token_hex(32)
        return {
            "key_id": f"fallback_key:{document_id}:{user_id}",
            "key_hex": fallback_key,
            "ttl_seconds": ttl_seconds,
            "status": "issued_fallback"
        }

@tool
async def verify_device_fingerprint(user_id: str, device_fingerprint: Optional[str], client_ip: str) -> dict:
    """
    <module_purpose>Verify device hardware fingerprint and IP geofence via deterministic SHA-256 hashing (Zero Token Cost).</module_purpose>
    <contract>Requires user_id and client_ip. Returns boolean fingerprint verification result.</contract>
    """
    if not device_fingerprint:
        return {"matched": True, "risk_multiplier": 1.0, "reason": "No fingerprint enforced"}

    expected_hash = hashlib.sha256(f"{user_id}:{client_ip}".encode()).hexdigest()[:16]
    is_match = device_fingerprint == expected_hash

    return {
        "matched": is_match,
        "risk_multiplier": 1.0 if is_match else 2.5,
        "reason": "Fingerprint verified" if is_match else "Mismatch hardware signature detected"
    }

@tool
async def check_network_anomaly(user_id: str, client_ip: str) -> dict:
    """
    <module_purpose>Check network behavior for anomalies (e.g. rate-limiting, IP hopping) within the last minute.</module_purpose>
    <contract>Requires user_id and client_ip. Returns dict with anomaly flags.</contract>
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.DRM_URL}/bao-ve/kiem-tra-bat-thuong-mang",
                params={"user_id": user_id, "client_ip": client_ip},
                headers={"X-Internal-Token": settings.SECRET_KEY},
                timeout=3.0
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.warning(f"DRM network anomaly check fallback: {e}")
        return {"system_flag_anomaly": False, "error": str(e)}

@tool
async def get_user_trust_profile(user_id: str, user_tier: str = "BASIC") -> dict:
    """
    <module_purpose>Retrieve user trust score based on user tier and history.</module_purpose>
    <contract>Requires user_id. Returns trust score dict.</contract>
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.DRM_URL}/bao-ve/ho-so-tin-cay",
                params={"user_id": user_id, "user_tier": user_tier},
                headers={"X-Internal-Token": settings.SECRET_KEY},
                timeout=3.0
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.warning(f"DRM trust profile fallback: {e}")
        base_score = 90 if user_tier == "ENTERPRISE" else 75 if user_tier == "PRO" else 50
        return {"user_id": user_id, "trust_score": base_score, "error": str(e)}

@tool
async def analyze_document_risk(document_id: str, document_type: str = "standard") -> dict:
    """
    <module_purpose>Analyze risk level of the target document ('sensitive', 'exam', 'premium').</module_purpose>
    <contract>Requires document_id. Returns risk_level.</contract>
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.DRM_URL}/bao-ve/rui-ro-tai-lieu",
                params={"document_id": document_id, "document_type": document_type},
                headers={"X-Internal-Token": settings.SECRET_KEY},
                timeout=3.0
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.warning(f"DRM document risk fallback: {e}")
        risk = "HIGH" if document_type in ["sensitive", "exam"] else "LOW"
        return {"document_id": document_id, "risk_level": risk, "error": str(e)}
