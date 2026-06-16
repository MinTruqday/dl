from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, Response
from core.dependency import get_current_user, get_db
from src.services.exports import ExportService

router = APIRouter(prefix="/export")

@router.get("/{document_id}/pdf", response_model=APIResponse[Any])
async def export_document_pdf(document_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    pdf_content = await ExportService.export_document_pdf_watermarked(document_id, current_user, db=db)
    headers = {"Content-Disposition": 'attachment; filename="Document_Export_Watermarked.pdf"'}
    return APIResponse(
        data=Response(content=pdf_content, media_type="application/pdf", headers=headers),
        message="Portable document format duplication successfully generated incorporating appropriate copyright watermark security",
        status=200,
    )