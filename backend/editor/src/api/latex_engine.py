import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from fastapi.responses import Response
from loguru import logger
from src.schemas.document_editing import CompileRequest
from src.engines.latex_engine import LatexEngine
from core.system_dependency import get_current_user, get_current_user_optional, CurrentUser
from core.infrastructure.database_client import db_client

router = APIRouter()


@router.post("/bien-dich")
async def compile_latex(req: CompileRequest):
    try:
        pdf_bytes = await LatexEngine.compile_to_pdf(req.content)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception:
        logger.error("Lỗi biên dịch tài liệu định dạng")
        raise HTTPException(
            status_code=400, detail="Lỗi biên dịch do cú pháp không hợp lệ"
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
    except Exception:
        logger.error("Lỗi chuyển đổi định dạng tài liệu")
        raise HTTPException(status_code=500, detail="Lỗi xuất tài liệu")


@router.post("/dinh-dang")
async def format_latex(req: CompileRequest):
    return LatexEngine.format_latex(req.content)


@router.post("/ket-xuat-zip")
async def export_project_zip(req: CompileRequest):
    zip_bytes = LatexEngine.export_project_zip(req.content)
    return Response(content=zip_bytes, media_type="application/x-zip-compressed")


@router.delete("/don-dep")
async def clean_temp_files(current_user: CurrentUser = Depends(get_current_user_optional)):
    if current_user and hasattr(db_client, "redis") and db_client.redis:
        await db_client.redis.delete(f"latex_draft:{current_user.id}")
    return {"message": "Dọn dẹp tập tin tạm thời thành công", "data": {}}

@router.post("/tu-dong-luu")
async def auto_save_latex(payload: dict, current_user: CurrentUser = Depends(get_current_user)):
    if hasattr(db_client, "redis") and db_client.redis:
        content = payload.get("content", "")
        if content:
            await db_client.redis.setex(f"latex_draft:{current_user.id}", 604800, content)
    return {"message": "Tự động lưu mã nguồn LaTeX thành công", "data": {}}

@router.get("/ban-nhap")
async def get_latex_draft(current_user: CurrentUser = Depends(get_current_user)):
    if hasattr(db_client, "redis") and db_client.redis:
        draft = await db_client.redis.get(f"latex_draft:{current_user.id}")
        if draft:
            return {"message": "Lấy bản nháp thành công", "data": {"content": draft.decode('utf-8') if isinstance(draft, bytes) else draft}}
    return {"message": "Không có bản nháp", "data": {"content": None}}
