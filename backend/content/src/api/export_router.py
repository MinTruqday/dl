from typing import Any

from core.response import APIResponse
from core.schemas.user import UserInDB
from fastapi import APIRouter, Depends, Response
from src.api.dependency_router import get_current_user, get_db
from src.services.document_service import DocumentService
from src.services.export_service import ExportService

router = APIRouter(prefix="/export-tai-lieu")


@router.get("/{document_id}/pdf", response_model=APIResponse[Any])
async def export_document_pdf(
    document_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    pdf_content = await ExportService.export_document_pdf_watermarked(
        document_id, current_user, db=db
    )
    headers = {
        "Content-Disposition": 'attachment; filename="DocLib_Export_{document_id}_Watermarked.pdf"'
    }
    return APIResponse(
        data=Response(
            content=pdf_content, media_type="application/pdf", headers=headers
        ),
        message="Đã xuất bản sao PDF đính kèm dấu bản quyền",
        status=200,
    )
