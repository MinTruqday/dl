from typing import Any

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, Response, HTTPException, Request
from src.core.dependency import get_current_user, get_db

from src.services.watermark import WatermarkService

from src.core.response import APIResponse
from src.core.dependency import CurrentUser, Role, require_role

router = APIRouter(route_class=LoggingRoute, prefix="/ket-xuat")

@router.get("/{document_id}/drm")
async def export_document_pdf(
    document_id: str,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    client_ip = request.client.host if request.client else "127.0.0.1"
    file_content, ext, mime_type = await WatermarkService.export_document_pdf_watermarked(
        document_id, current_user, client_ip
    )
    headers = {
        "Content-Disposition": f'attachment; filename="TaiLieuBaoMat.{ext}"'
    }
    return Response(
        content=file_content, media_type=mime_type, headers=headers
    )

from src.schemas.watermark import TextPayload

@router.post("/giai-ma-truy-vet")
async def verify_document_watermark(
    payload: TextPayload,
    current_user: CurrentUser = Depends(require_role([Role.ADMIN]))
):
    user_id = await WatermarkService.verify_watermark(payload.text)
    if user_id:
        return APIResponse(
            data={"user_id": user_id},
            message="Trích xuất mã định danh ẩn trong tài liệu hoàn tất",
            status=200
        )
    raise HTTPException(
        status_code=404,
        detail="Không tìm thấy mã định danh ẩn trong tài liệu",
    )
