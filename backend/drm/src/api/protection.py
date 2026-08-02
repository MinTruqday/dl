import datetime
import hashlib
import ipaddress
import secrets
import time
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from src.core.dependency import verify_internal_token
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.infrastructure.redis import redis
from src.services.humanity_client import HumanityClient
from src.services.content_client import ContentClient

router = APIRouter(
    prefix="/bao-ve",
    dependencies=[Depends(verify_internal_token)],
)

@router.get("/kiem-tra-bat-thuong-mang")
async def check_network_anomaly(user_id: str, client_ip: str) -> Dict[str, Any]:
    try:
        ipaddress.ip_address(client_ip)
    except ValueError:
        raise HTTPException(status_code=422, detail="Địa chỉ IP không hợp lệ")
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
async def get_user_trust_profile(
    user_id: str = Query(min_length=1, max_length=128),
) -> Dict[str, Any]:
    user = await HumanityClient.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    drm_db = database.mongodb[settings.DRM_DB_NAME]
    active_licenses = await drm_db.drm_licenses.count_documents(
        {"user_id": user_id, "status": "ACTIVE"}
    )
    revoked_licenses = await drm_db.drm_licenses.count_documents(
        {"user_id": user_id, "status": "REVOKED"}
    )
    denied_accesses = await drm_db.audit_logs.count_documents(
        {
            "user_id": user_id,
            "event": {"$in": ["license_access_denied", "license_access_anomaly"]},
        }
    )
    score = 100 if user.get("is_active", True) else 0
    score = max(0, score - min(60, revoked_licenses * 15) - min(40, denied_accesses * 10))
    return {
        "user_id": user_id,
        "user_tier": str(user.get("ai_tier") or user.get("role") or "unknown"),
        "trust_score": score,
        "active_licenses": active_licenses,
        "revoked_licenses": revoked_licenses,
        "denied_accesses": denied_accesses,
    }

@router.get("/rui-ro-tai-lieu")
async def analyze_document_risk(
    document_id: str = Query(min_length=1, max_length=128),
) -> Dict[str, Any]:
    document = await ContentClient.get(document_id)
    if not document or document.get("is_deleted"):
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
    drm_db = database.mongodb[settings.DRM_DB_NAME]
    drm_settings = await drm_db.document_drm_settings.find_one(
        {"document_id": document_id}
    )
    open_disputes = await drm_db.copyright_disputes.count_documents(
        {
            "document_id": document_id,
            "status": {"$in": ["PENDING", "OPEN", "UNDER_REVIEW"]},
        }
    )
    revoked_licenses = await drm_db.drm_licenses.count_documents(
        {"document_id": document_id, "status": "REVOKED"}
    )
    factors = []
    score = 0
    if document.get("is_premium"):
        score += 25
        factors.append("premium_content")
    if document.get("visibility") == "private":
        score += 15
        factors.append("private_visibility")
    if drm_settings and any(
        drm_settings.get(field)
        for field in ["disable_copy", "disable_print", "watermark_enabled"]
    ):
        score += 20
        factors.append("active_protection")
    if open_disputes:
        score += 40
        factors.append("copyright_dispute")
    if revoked_licenses:
        score += min(30, revoked_licenses * 5)
        factors.append("revoked_licenses")
    risk_level = "HIGH" if score >= 60 else "MEDIUM" if score >= 25 else "LOW"
    return {
        "document_id": document_id,
        "risk_level": risk_level,
        "risk_score": min(score, 100),
        "factors": factors,
        "open_disputes": open_disputes,
        "revoked_licenses": revoked_licenses,
    }

@router.get("/thuy-an-dong")
async def generate_dynamic_watermark(user_id: str, client_ip: str, email: str = "") -> Dict[str, Any]:
    try:
        ipaddress.ip_address(client_ip)
    except ValueError:
        raise HTTPException(status_code=422, detail="Địa chỉ IP không hợp lệ")
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
async def issue_temporary_aes_key(
    document_id: str = Query(min_length=1, max_length=128),
    user_id: str = Query(min_length=1, max_length=128),
    ttl_seconds: int = Query(default=300, ge=60, le=3600),
) -> Dict[str, Any]:
    document = await ContentClient.get(document_id)
    user = await HumanityClient.get(user_id)
    if not document:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    key_id = f"aes_key:{document_id}:{user_id}:{secrets.token_hex(4)}"
    raw_key = secrets.token_hex(32)

    try:
        await redis.get_client().setex(key_id, ttl_seconds, raw_key)
    except Exception:
        logger.exception("DRM key persistence failed")
        raise HTTPException(
            status_code=503,
            detail="Dịch vụ cấp khóa tạm thời không khả dụng",
        )

    return {
        "key_id": key_id,
        "key_hex": raw_key,
        "ttl_seconds": ttl_seconds,
        "status": "issued"
    }

@router.get("/xac-minh-van-tay")
async def verify_device_fingerprint(
    user_id: str = Query(min_length=1, max_length=128),
    client_ip: str = Query(min_length=3, max_length=45),
    device_fingerprint: str = Query(min_length=8, max_length=256),
) -> Dict[str, Any]:
    try:
        ipaddress.ip_address(client_ip)
    except ValueError:
        raise HTTPException(status_code=422, detail="Địa chỉ IP không hợp lệ")
    licenses = await database.mongodb[settings.DRM_DB_NAME].drm_licenses.find(
        {
            "user_id": user_id,
            "status": "ACTIVE",
            "hardware_signature": {"$type": "string"},
        },
        {"hardware_signature": 1, "recent_accesses": 1},
    ).to_list(length=100)
    enrolled = {
        row["hardware_signature"]
        for row in licenses
        if row.get("hardware_signature")
    }
    known_ips = {
        access.get("ip")
        for row in licenses
        for access in row.get("recent_accesses", [])
        if access.get("ip")
    }
    is_match = device_fingerprint in enrolled
    known_ip = not known_ips or client_ip in known_ips

    return {
        "matched": is_match,
        "known_ip": known_ip,
        "risk_multiplier": 1.0 if is_match and known_ip else 2.5,
        "reason": "verified" if is_match else "fingerprint_mismatch"
    }

@router.get("/noi-bo/giay-phep")
async def get_internal_license(file_id: str) -> Dict[str, Any]:
    license_doc = await database.mongodb[settings.DRM_DB_NAME].drm_licenses.find_one(
        {"file_id": file_id}
    )
    if not license_doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy giấy phép")
    license_doc["_id"] = str(license_doc["_id"])
    return {"data": license_doc}

@router.get("/noi-bo/cau-hinh")
async def get_internal_document_settings(document_id: str) -> Dict[str, Any]:
    settings_doc = await database.mongodb[settings.DRM_DB_NAME].document_drm_settings.find_one(
        {"document_id": document_id}
    )
    if not settings_doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy cấu hình DRM")
    settings_doc["_id"] = str(settings_doc["_id"])
    return {"data": settings_doc}


@router.get("/noi-bo/noi-dung-ai")
async def get_internal_ai_content(
    document_id: str = Query(min_length=1, max_length=128),
    user_id: str = Query(min_length=1, max_length=128),
    purpose: str = Query(default="answer", pattern=r"^(answer|index|summarize|learn)$"),
    is_admin: bool = False,
) -> Dict[str, Any]:
    document = await ContentClient.get_accessible(
        document_id, user_id, is_admin, edit=False
    )
    if not document:
        raise HTTPException(status_code=403, detail="Không có quyền đọc tài liệu")
    drm_db = database.mongodb[settings.DRM_DB_NAME]
    policy = await drm_db.document_drm_settings.find_one(
        {"document_id": document_id}
    )
    if policy and not policy.get("allow_internal_ai", True):
        raise HTTPException(status_code=403, detail="Tài liệu không cho phép xử lý AI")
    now = datetime.datetime.now(datetime.timezone.utc)
    await drm_db.audit_logs.insert_one(
        {
            "event": "internal_ai_content_granted",
            "document_id": document_id,
            "user_id": user_id,
            "purpose": purpose,
            "created_at": now,
        }
    )
    return {
        "data": {
            "document_id": document_id,
            "title": document.get("title", ""),
            "content": document.get("content"),
            "content_format": document.get("content_format"),
            "file_url": document.get("file_url") or document.get("pdf_url"),
            "profile": "doclib-drm-2026",
            "rights": {"internal_ai": True, "external_export": False},
        }
    }
