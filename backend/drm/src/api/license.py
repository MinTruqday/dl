import base64
import os
import uuid
import datetime
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger

from shared.repositories.base_repository import RepositoryFactory

router = APIRouter(prefix="/drm")

from shared.dependency import CurrentUser, get_current_user
from src.schemas.license import Acquisition, Token

@router.post("/kiem-tra", response_model=Token)
async def acquire_license(req: Acquisition, current_user: CurrentUser = Depends(get_current_user)):
    try:
        licenses_col = RepositoryFactory.get("drm_licenses")
        
        license_doc = await licenses_col.find_one({"file_id": req.file_id})
        if not license_doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy giấy phép bản quyền của tài liệu")
            
        if license_doc.get("status") != "ACTIVE":
            raise HTTPException(status_code=403, detail="Giấy phép bản quyền đã bị thu hồi hoặc hết hạn")
            
        if license_doc["user_id"] != str(current_user.id):
            raise HTTPException(status_code=403, detail="Tài khoản không có quyền giải mã file này")
            
        user_id = str(current_user.id)

        await licenses_col.update_one(
            {"_id": license_doc["_id"]},
            {"$inc": {"open_count": 1}, "$set": {"last_opened_at": datetime.datetime.now(datetime.timezone.utc)}}
        )
        
        logger.info(f"Đã cấp phép truy cập cho tài liệu {req.file_id} cho người dùng {user_id}")
        return Token(aes_key=license_doc["aes_key"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi yêu cầu cấp phép bản quyền: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống nội bộ: {e}")
