import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import Response
from loguru import logger
from src.schemas.latex import CompileRequest
from src.services.latex_engine import LatexEngine

router = APIRouter()


@router.post("/bien-dich")
async def compile_latex(req: CompileRequest):
    try:
        pdf_bytes = await LatexEngine.compile_to_pdf(req.content)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception:
        logger.error("Lỗi biên dịch tài liệu định dạng")
        raise HTTPException(
            status_code=500, detail="Lỗi biên dịch do cú pháp không hợp lệ"
        )


@router.post("/export/{format}")
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
