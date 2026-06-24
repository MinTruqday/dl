import base64
import os
import uuid
import datetime
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger

from src.repositories.license import LicenseRepository

router = APIRouter(prefix="/drm")

from src.core.dependency import CurrentUser, get_current_user
from src.schemas.license import Acquisition, Token

@router.post("/kiem-tra", response_model=Token)
async def acquire_license(req: Acquisition, current_user: CurrentUser = Depends(get_current_user)):
    try:
        license_doc = await LicenseRepository.find_license_by_file_id(req.file_id)
        if not license_doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy giấy phép bản quyền của tài liệu")
            
        if license_doc.get("status") != "ACTIVE":
            raise HTTPException(status_code=403, detail="Giấy phép bản quyền đã bị thu hồi hoặc hết hạn")
            
        if license_doc["user_id"] != str(current_user.id):
            raise HTTPException(status_code=403, detail="Tài khoản không có quyền giải mã file này")
            
        user_id = str(current_user.id)
        
        # Kiểm tra lại quyền hạn Real-time
        document = await LicenseRepository.get_document(license_doc["document_id"])
        if document and document.get("is_premium") and document.get("creator_id") != user_id:
            purchase = await LicenseRepository.get_purchase(user_id, license_doc["document_id"])
            if not purchase:
                # Thu hồi giấy phép ngay lập tức
                await LicenseRepository.update_license(license_doc["_id"], {"$set": {"status": "REVOKED"}})
                raise HTTPException(status_code=403, detail="Bạn đã hết hạn hoặc bị thu hồi quyền truy cập tài liệu này")

        await LicenseRepository.update_license(
            license_doc["_id"],
            {"$inc": {"open_count": 1}, "$set": {"last_opened_at": datetime.datetime.now(datetime.timezone.utc)}}
        )
        
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives import hashes, serialization
        
        try:
            public_key = serialization.load_pem_public_key(req.client_public_key.encode('utf-8'))
            raw_aes_key = base64.b64decode(license_doc["aes_key"])
            encrypted_aes_key = public_key.encrypt(
                raw_aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            encoded_encrypted_key = base64.b64encode(encrypted_aes_key).decode('utf-8')
        except Exception as e:
            logger.error(f"Lỗi mã hóa RSA: {e}")
            raise HTTPException(status_code=400, detail="Public Key không hợp lệ")
        
        logger.info(f"Đã cấp phép truy cập cho tài liệu {req.file_id} cho người dùng {user_id}")
        return Token(encrypted_aes_key=encoded_encrypted_key)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi yêu cầu cấp phép bản quyền: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống nội bộ: {e}")
