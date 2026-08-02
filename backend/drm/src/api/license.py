import base64
from datetime import datetime, timezone

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger

from src.core.dependency import CurrentUser, Role, get_current_user
from src.core.infrastructure.redis import redis
from src.core.logging_route import LoggingRoute
from src.repositories.license import LicenseRepository
from src.schemas.license import Acquisition, Token

router = APIRouter(route_class=LoggingRoute, prefix="/drm")


async def owned_license(file_id: str, current_user: CurrentUser):
    license_doc = await LicenseRepository.find_license_by_file_id(file_id)
    if not license_doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy giấy phép bản quyền của tài liệu")
    role = getattr(current_user.role, "value", current_user.role)
    if license_doc.get("user_id") != str(current_user.id) and role != Role.ADMIN.value:
        raise HTTPException(status_code=403, detail="Bạn không có quyền thay đổi giấy phép này")
    return license_doc


@router.post("/{file_id}/thu-hoi")
async def revoke_license(
    file_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    license_doc = await owned_license(file_id, current_user)
    now = datetime.now(timezone.utc)
    await LicenseRepository.update_license(
        license_doc["_id"],
        {"$set": {"status": "REVOKED", "revoked_at": now}},
    )
    await LicenseRepository.record_audit_log(
        {
            "event": "license_revoked",
            "file_id": file_id,
            "document_id": license_doc["document_id"],
            "user_id": str(current_user.id),
            "created_at": now,
        }
    )
    return {"status": "revoked", "file_id": file_id}

@router.post("/kiem-tra", response_model=Token)
async def acquire_license(req: Acquisition, request: Request, current_user: CurrentUser = Depends(get_current_user)):
    try:
        license_doc = await LicenseRepository.find_license_by_file_id(req.file_id)
        if not license_doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy giấy phép bản quyền của tài liệu")

        if license_doc.get("status") != "ACTIVE":
            raise HTTPException(status_code=403, detail="Giấy phép bản quyền tài liệu đã hết hạn hoặc bị thu hồi")

        now = datetime.now(timezone.utc)
        expires_at = license_doc.get("expires_at")
        if expires_at and expires_at <= now:
            await LicenseRepository.update_license(
                license_doc["_id"], {"$set": {"status": "EXPIRED"}}
            )
            raise HTTPException(status_code=403, detail="Giấy phép bản quyền tài liệu đã hết hạn hoặc bị thu hồi")
        if int(license_doc.get("open_count", 0)) >= int(
            license_doc.get("max_open_count", 100)
        ):
            await LicenseRepository.update_license(
                license_doc["_id"], {"$set": {"status": "EXHAUSTED"}}
            )
            raise HTTPException(status_code=403, detail="Giấy phép bản quyền tài liệu đã hết hạn hoặc bị thu hồi")

        if license_doc["user_id"] != str(current_user.id):
            raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập và giải mã tài liệu này")

        user_id = str(current_user.id)
        client_ip = request.client.host if request.client else "0.0.0.0"

        document = await LicenseRepository.get_document(license_doc["document_id"])
        if not document:
            raise HTTPException(status_code=404, detail="Tài liệu liên kết với giấy phép không còn tồn tại")
        from src.core.dependency import Role
        is_privileged = getattr(current_user.role, "value", current_user.role) == Role.ADMIN.value
        if document.get("is_premium") and document.get("creator_id") != user_id and not is_privileged:
            purchase = await LicenseRepository.get_purchase(user_id, license_doc["document_id"])
            if not purchase:
                await LicenseRepository.update_license(license_doc["_id"], {"$set": {"status": "REVOKED"}})
                raise HTTPException(status_code=403, detail="Giấy phép bản quyền tài liệu đã hết hạn hoặc bị thu hồi")

        try:
            public_key = serialization.load_pem_public_key(req.client_public_key.encode("utf-8"))
            raw_aes_key = base64.b64decode(license_doc["aes_key"])
            encrypted_aes_key = public_key.encrypt(
                raw_aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            encoded_encrypted_key = base64.b64encode(encrypted_aes_key).decode("utf-8")
        except Exception:
            logger.exception("RSA encryption failed for client public key")
            raise HTTPException(status_code=400, detail="Khóa công khai (Public Key) không hợp lệ")

        minute = int(datetime.now(timezone.utc).timestamp() / 60)
        req_key = f"drm:license:reqs:{user_id}:{minute}"
        ip_key = f"drm:license:ips:{user_id}:{minute}"
        req_count = (await redis.pipeline_incr_expire(req_key, 60))[0]
        await redis.sadd(ip_key, client_ip)
        await redis.get_client().expire(ip_key, 60)
        ip_count = len(await redis.smembers(ip_key))
        if req_count > 5 and ip_count > 1:
            await LicenseRepository.update_license(license_doc["_id"], {"$set": {"status": "REVOKED"}})
            raise HTTPException(status_code=403, detail="Giấy phép bản quyền tài liệu đã bị thu hồi do hành vi truy cập bất thường")

        current_time = now
        claimed = await LicenseRepository.claim_access(
            license_doc["_id"],
            req.hardware_signature,
            current_time,
            client_ip,
        )
        if not claimed:
            latest = await LicenseRepository.find_license_by_file_id(req.file_id)
            if latest and latest.get("status") != "ACTIVE":
                raise HTTPException(status_code=403, detail="Giấy phép bản quyền tài liệu đã hết hạn hoặc bị thu hồi")
            raise HTTPException(status_code=403, detail="Giấy phép bản quyền không khớp với thiết bị hiện tại")

        await LicenseRepository.record_audit_log(
            {
                "event": "license_access_granted",
                "file_id": req.file_id,
                "document_id": license_doc["document_id"],
                "user_id": user_id,
                "client_ip": client_ip,
                "created_at": current_time,
            }
        )
        logger.info(f"Granted DRM access for document {req.file_id} to user {user_id}")
        return Token(
            encrypted_aes_key=encoded_encrypted_key,
            expires_at=license_doc.get("expires_at"),
            rights=license_doc.get("rights", {}),
            profile=license_doc.get("profile", "doclib-drm-2026"),
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to acquire DRM license")
        raise HTTPException(status_code=500, detail="Đã xảy ra lỗi hệ thống khi cấp phép bản quyền")
