from typing import Any
from shared.core.response import APIResponse
from fastapi import APIRouter, Depends, Response
from api.dependency import get_current_user
from shared.models.user import UserInDB
from services.export import ExportService
from services.document import DocumentService

router = APIRouter(prefix="/xuat-tai-lieu")

@router.get("/{document_id}/pdf", response_model=APIResponse[Any])
async def export_document_pdf(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    pdf_content = await ExportService.export_document_pdf_watermarked(document_id, current_user)
    headers = {"Content-Disposition": f'attachment; filename="DocLib_Export_{document_id}_Watermarked.pdf"'}
    return APIResponse(
        data=Response(content=pdf_content, media_type="application/pdf", headers=headers), 
        message="Xuất bản sao PDF đính kèm dấu bản quyền thành công", 
        status=200
    )

@router.get("/{document_id}/epub", response_model=APIResponse[Any])
async def export_document_epub(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    content = await DocumentService.export_epub(document_id, current_user)
    headers = {"Content-Disposition": f'attachment; filename="DocLib_{document_id}.epub"'}
    return APIResponse(
        data=Response(content=content, media_type="application/epub+zip", headers=headers), 
        message="Xuất bản sao EPUB thành công", 
        status=200
    )
