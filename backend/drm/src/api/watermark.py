from typing import Any

from fastapi import APIRouter, Depends, Response, HTTPException
from src.core.dependency import get_current_user, get_db

from src.services.watermark import WatermarkService

from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role

router = APIRouter(prefix="/ket-xuat")

@router.get("/{document_id}/drm")
async def export_document_pdf(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    pdf_content = await WatermarkService.export_document_pdf_watermarked(
        document_id, current_user
    )
    headers = {
        "Content-Disposition": 'attachment; filename="TaiLieuBaoMat.doclib"'
    }
    return Response(
        content=pdf_content, media_type="application/octet-stream", headers=headers
    )

from src.schemas.watermark import TextPayload

@router.post("/giai-ma-truy-vet")
async def verify_document_watermark(
    payload: TextPayload,
    current_user: CurrentUser = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Chỉ quản trị viên mới có quyền giải mã truy vết")
    
    user_id = await WatermarkService.verify_watermark(payload.text)
    if user_id:
        return APIResponse(
            data={"user_id": user_id},
            message="Phát hiện mã định danh ẩn trong tài liệu",
            status=200
        )
    return APIResponse(
        data=None,
        message="Không tìm thấy mã định danh ẩn trong tài liệu",
        status=404
    )
