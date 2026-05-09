from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from models.user import UserInDB, RoleEnum
from api.dependency import require_role
from services.compilation import CompilationService
from services.editor import EditorService
from io import BytesIO

router = APIRouter(prefix="/bien-dich")

@router.post("/pdf", response_model=Any)
async def compile_latex_to_pdf(
    payload: dict,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    content = payload.get("content", "")
    pdf_data = await CompilationService.compile_latex_to_pdf(content)
    
    return StreamingResponse(
        BytesIO(pdf_data), 
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=preview.pdf"}
    )

@router.get("/latex", response_model=APIResponse[Any])
async def get_latex():
    return APIResponse(data=await EditorService.get_latex(), message="Lấy mã nguồn LaTeX thành công.", status=200)
