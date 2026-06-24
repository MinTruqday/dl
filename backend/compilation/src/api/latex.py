from src.core.infrastructure.redis import redis
import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from fastapi.responses import Response
from loguru import logger
from src.schemas.composition import CompileRequest
from src.engines.latex import LatexEngine
from src.core.dependency import get_current_user, get_current_user_optional, CurrentUser
from src.core.infrastructure.database import database

router = APIRouter()

@router.post("/bien-dich")
async def compile_latex(req: CompileRequest):
    try:
        pdf_bytes = await LatexEngine.compile_to_pdf(req.content)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as e:
        logger.error(f"Lỗi biên dịch tài liệu định dạng: {e}")
        raise HTTPException(
            status_code=400, detail=f"Lỗi biên dịch do cú pháp không hợp lệ: {e}"
        )

@router.post("/ket-xuat/{format}")
async def export_document(format: str, req: CompileRequest):
    if format not in ["docx", "html"]:
        raise HTTPException(status_code=400, detail="Không hỗ trợ định dạng xuất này")

    try:
        file_bytes = await LatexEngine.export_to_format(req.content, format)

        media_type = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        if format == "html":
            media_type = "text/html"

        return Response(content=file_bytes, media_type=media_type)
    except Exception as e:
        logger.error(f"Lỗi chuyển đổi định dạng tài liệu: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi xuất tài liệu: {e}")

@router.post("/dinh-dang")
async def format_latex(req: CompileRequest):
    return LatexEngine.format_latex(req.content)

@router.post("/ket-xuat-zip")
async def export_project_zip(req: CompileRequest):
    zip_bytes = LatexEngine.export_project_zip(req.content)
    return Response(content=zip_bytes, media_type="application/x-zip-compressed")

@router.delete("/don-dep")
async def clean_temp_files(current_user: CurrentUser = Depends(get_current_user_optional)):
    if current_user and redis:
        await redis.delete(f"latex_draft:{current_user.id}")
    return {"message": "Dọn dẹp tập tin tạm thời thành công", "data": {}}

@router.post("/tu-dong-luu")
async def auto_save_latex(payload: dict, current_user: CurrentUser = Depends(get_current_user)):
    if redis:
        content = payload.get("content", "")
        if content:
            await redis.setex(f"latex_draft:{current_user.id}", 604800, content)
    return {"message": "Tự động lưu mã nguồn LaTeX thành công", "data": {}}

@router.get("/ban-nhap")
async def get_latex_draft(current_user: CurrentUser = Depends(get_current_user)):
    if redis:
        draft = await redis.get(f"latex_draft:{current_user.id}")
        if draft:
            return {"message": "Lấy bản nháp thành công", "data": {"content": draft.decode('utf-8') if isinstance(draft, bytes) else draft}}
    return {"message": "Không có bản nháp", "data": {"content": None}}
