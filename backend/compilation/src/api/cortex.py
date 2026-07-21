from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from loguru import logger

from src.core.logging_route import LoggingRoute
from src.engines.cortex import CortexEngine
from src.schemas.composition import CompileRequest

router = APIRouter(route_class=LoggingRoute, prefix="/soan-thao/cortex")

@router.post("/bien-dich")
async def compile_cortex(req: CompileRequest):
    try:
        logger.info("Handling PDF compilation request for Cortex document")
        pdf_bytes = await CortexEngine.compile_to_pdf(req.content)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as e:
        logger.exception("Failed to compile Cortex document to PDF")
        raise HTTPException(
            status_code=400,
            detail="Quá trình biên dịch tài liệu Cortex thất bại do lỗi cú pháp trong mã nguồn",
        )

@router.post("/ket-xuat/doclibx")
async def export_doclibx(req: CompileRequest):
    try:
        logger.info("Handling doclibx export request for Cortex document")
        zip_bytes = CortexEngine.compile_to_doclibx(req.content)
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=document.doclibx"},
        )
    except Exception as e:
        logger.exception("Failed to export Cortex document to doclibx")
        raise HTTPException(
            status_code=500,
            detail="Quá trình kết xuất tài liệu doclibx gặp sự cố kỹ thuật",
        )

@router.post("/dinh-dang")
async def format_cortex_document(req: CompileRequest):
    try:
        logger.info("Handling formatting request for Cortex document")
        formatted = CortexEngine.format_cortex(req.content)
        return {"formatted_content": formatted}
    except Exception as e:
        logger.exception("Failed to format Cortex document")
        raise HTTPException(
            status_code=400,
            detail="Quá trình định dạng tài liệu Cortex gặp sự cố do lỗi cấu trúc",
        )
