from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from models.user import UserInDB, RoleEnum
from api.dependencies import require_role
from services.latex import LatexService
import time

router = APIRouter(prefix="/latex")

class CompileRequest(BaseModel):
    content: str
    is_fragment: bool = False

class FormatRequest(BaseModel):
    content: str

class ExportRequest(BaseModel):
    content: str
    format: str = "docx"

class AutoSaveRequest(BaseModel):
    document_id: str
    content: str

@router.delete("/clean-temp")
async def clean_temp_files(current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    return await LatexService.clean_temp_files(current_user)

@router.post("/compile-preview")
async def compile_latex_preview(
    request: CompileRequest,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    pdf_bytes = await LatexService.compile_latex_preview(request, current_user)
    return Response(content=pdf_bytes, media_type="application/pdf")

@router.post("/format")
async def format_latex(
    request: FormatRequest,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    return await LatexService.format_latex(request)

@router.post("/export")
async def export_latex(
    request: ExportRequest,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    file_bytes = await LatexService.export_latex(request, current_user)
    media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if request.format == "docx" else "text/html"
    return Response(content=file_bytes, media_type=media_type, headers={"Content-Disposition": f"attachment; filename=export.{request.format}"})

@router.post("/auto-save")
async def cloud_auto_save(
    request: AutoSaveRequest,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    return await LatexService.auto_save(request)

@router.post("/export-zip")
async def export_project_zip(
    request: CompileRequest,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    zip_bytes = await LatexService.export_project_zip(request)
    headers = {'Content-Disposition': 'attachment; filename="doclib_project.zip"'}
    return Response(zip_bytes, media_type="application/x-zip-compressed", headers=headers)
