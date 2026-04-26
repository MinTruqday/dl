from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from models.user import UserInDB, RoleEnum
from api.dependencies import require_role
from services.compile import CompileService
from services.editor import EditorService
from io import BytesIO

router = APIRouter(prefix="/compile")

@router.post("/pdf", response_class=StreamingResponse)
async def compile_latex_to_pdf(
    payload: dict,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    content = payload.get("content", "")
    pdf_data = await CompileService.compile_latex_to_pdf(content)
    
    return StreamingResponse(
        BytesIO(pdf_data), 
        media_type="application/pdf",
        headers={"CContent-Disposition": "inline; filename=preview.pdf"}
    )

@router.get("/latex")
async def get_latex():
    return await EditorService.get_latex()
