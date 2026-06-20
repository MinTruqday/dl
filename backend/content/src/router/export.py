from typing import Any

from fastapi import APIRouter, Depends, Response
from src.router.dependency import get_current_user, get_db
from src.services.document import DocumentManager
from src.services.export import ExportManager

from core.response import APIResponse
from core.schemas.user import UserInDB

router = APIRouter(prefix="/ket-xuat")


@router.get("/{document_id}/pdf", response_model=APIResponse[Any])
async def export_document_pdf(
    document_id: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db),
):
    pdf_content = await ExportManager.export_document_pdf_watermarked(
        document_id, current_user, db=db
    )
    headers = {
        "Content-Disposition": 'attachment; filename="Document_Export_Watermarked.pdf"'
    }
    return APIResponse(
        data=Response(
            content=pdf_content, media_type="application/pdf", headers=headers
        ),
        message="Tạo bản sao đóng dấu bản quyền thành công",
        status=200,
    )
