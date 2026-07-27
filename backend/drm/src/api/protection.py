import datetime
from enum import Enum
import hashlib
import secrets
import time
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from src.core.dependency import verify_internal_token
from src.core.infrastructure.redis import redis

class Tier(str, Enum):
    BASIC = "BASIC"
    PRO = "PRO"
    PREMIUM = "PREMIUM"

router = APIRouter(
    prefix="/bao-ve",
    dependencies=[Depends(verify_internal_token)],
)

@router.get("/kiem-tra-bat-thuong-mang")
async def check_network_anomaly(user_id: str, client_ip: str) -> Dict[str, Any]:
    current_minute = int(time.time() / 60)
    req_key = f"drm:reqs:{user_id}:{current_minute}"
    ip_key = f"drm:ips:{user_id}:{current_minute}"
    
    try:
        req_responses = await redis.pipeline_incr_expire(req_key, 60)
        req_count = req_responses[0]
        
        await redis.sadd(ip_key, client_ip)
        await redis.get_client().expire(ip_key, 60)
        
        unique_ips = await redis.smembers(ip_key)
        ip_count = len(unique_ips)
        
        is_anomalous = req_count > 5 and ip_count > 1
        return {
            "user_id": user_id,
            "current_ip": client_ip,
            "metrics_last_60s": {
                "total_requests": req_count,
                "unique_ip_count": ip_count,
                "ips_used": list(unique_ips)
            },
            "system_flag_anomaly": is_anomalous
        }
    except Exception:
        logger.exception("Network anomaly evaluation failed")
        raise HTTPException(
            status_code=503,
            detail="Dịch vụ đánh giá bất thường tạm thời không khả dụng",
        )

@router.get("/ho-so-tin-cay")
async def get_user_trust_profile(user_id: str, user_tier: str = Tier.BASIC.value) -> Dict[str, Any]:
    tier_upper = str(user_tier).upper()
    score = 90 if tier_upper == Tier.PREMIUM.value else 75 if tier_upper == Tier.PRO.value else 50
    return {
        "user_id": user_id,
        "user_tier": tier_upper,
        "trust_score": score,
    }

@router.get("/rui-ro-tai-lieu")
async def analyze_document_risk(document_id: str, document_type: str = "standard") -> Dict[str, Any]:
    is_sensitive = document_type in ["sensitive", "exam", "premium"]
    return {
        "document_id": document_id,
        "document_type": document_type,
        "risk_level": "HIGH" if is_sensitive else "LOW",
    }

@router.get("/thuy-an-dong")
async def generate_dynamic_watermark(user_id: str, client_ip: str, email: str = "") -> Dict[str, Any]:
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

@router.post("/cap-khoa-aes")
async def issue_temporary_aes_key(document_id: str, user_id: str, ttl_seconds: int = 300) -> Dict[str, Any]:
    key_id = f"aes_key:{document_id}:{user_id}:{secrets.token_hex(4)}"
    raw_key = secrets.token_hex(32)

    try:
        await redis.get_client().setex(key_id, ttl_seconds, raw_key)
        status = "issued"
    except Exception as e:
        logger.warning("DRM Redis key issuance fallback")
        status = "issued_fallback"

    return {
        "key_id": key_id,
        "key_hex": raw_key,
        "ttl_seconds": ttl_seconds,
        "status": status
    }

@router.get("/xac-minh-van-tay")
async def verify_device_fingerprint(user_id: str, client_ip: str, device_fingerprint: Optional[str] = None) -> Dict[str, Any]:
    if not device_fingerprint:
        return {"matched": True, "risk_multiplier": 1.0, "reason": "No fingerprint enforced"}

    expected_hash = hashlib.sha256(f"{user_id}:{client_ip}".encode()).hexdigest()[:16]
    is_match = device_fingerprint == expected_hash

    return {
        "matched": is_match,
        "risk_multiplier": 1.0 if is_match else 2.5,
        "reason": "Fingerprint verified" if is_match else "Mismatch hardware signature detected"
    }
