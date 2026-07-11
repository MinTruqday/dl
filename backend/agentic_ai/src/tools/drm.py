import time
from langchain_core.tools import tool
from loguru import logger
from src.core.infrastructure.redis import redis

@tool
async def check_network_anomaly(user_id: str, client_ip: str) -> dict:
    """Check network behavior for anomalies within the last minute."""
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
    except Exception as e:
        logger.exception("Failed to check network anomaly")
        return {"system_flag_anomaly": False, "error": str(e)}

@tool
async def get_user_trust_profile(user_id: str, user_tier: str = "BASIC") -> dict:
    """Retrieve the trust profile of the user."""
    return {
        "user_id": user_id,
        "user_tier": user_tier,
        "trust_score": 90 if user_tier == "PRO" else 50,
    }

@tool
async def analyze_document_risk(document_id: str, document_type: str = "standard") -> dict:
    """Analyze the risk level of the document."""
    is_sensitive = document_type in ["sensitive", "exam", "premium"]
    return {
        "document_id": document_id,
        "document_type": document_type,
        "is_sensitive": is_sensitive,
        "risk_level": "HIGH" if is_sensitive else "LOW"
    }
