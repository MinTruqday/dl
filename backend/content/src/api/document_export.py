from typing import Any

from fastapi import APIRouter, Depends, Response
from src.api.system_dependency import get_current_user, get_db
from src.services.document_metadata import DocumentMetadata
from src.services.document_export import DocumentExport

from core.api_response import APIResponse
from core.system_dependency import CurrentUser, RoleEnum

router = APIRouter(prefix="/ket-xuat")


@router.get("/{document_id}/pdf")
async def export_document_pdf(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db=Depends(get_db),
):
    pdf_content = await DocumentExport.export_document_pdf_watermarked(
        document_id, current_user, db=db
    )
    headers = {
        "Content-Disposition": 'attachment; filename="Document_Export_Watermarked.pdf"'
    }
    return Response(
        content=pdf_content, media_type="application/pdf", headers=headers
    )
