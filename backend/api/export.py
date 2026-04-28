from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, Response
from api.dependencies import get_current_user
from models.user import UserInDB
from services.export import ExportService

router = APIRouter()

@router.get("/documents/{document_id}/export/pdf", response_model=APIResponse[Any])
async def export_document_pdf_watermarked(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    pdf_content = await ExportService.export_document_pdf_watermarked(document_id, current_user)
    headers = {"Content-Disposition": f'attachment; filename="DocLib_Export_{document_id}_Watermarked.pdf"'}
    return APIResponse(data=Response(content=pdf_content, media_type="application/pdf", headers=headers), message="Xuất bản sao PDF đính kèm dấu bản quyền thành công.", status=200)
