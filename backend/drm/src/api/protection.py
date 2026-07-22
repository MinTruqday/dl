import time
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from src.core.dependency import verify_internal_token
from src.core.infrastructure.redis import redis

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
async def get_user_trust_profile(user_id: str, user_tier: str = "BASIC") -> Dict[str, Any]:
    return {
        "user_id": user_id,
        "user_tier": user_tier,
        "trust_score": 90 if user_tier == "PRO" else 50,
    }

@router.get("/rui-ro-tai-lieu")
async def analyze_document_risk(document_id: str, document_type: str = "standard") -> Dict[str, Any]:
    is_sensitive = document_type in ["sensitive", "exam", "premium"]
    return {
        "document_id": document_id,
        "document_type": document_type,
        "is_sensitive": is_sensitive,
        "risk_level": "HIGH" if is_sensitive else "LOW"
    }
