from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, HTTPException
from fastapi.response import Response
from loguru import logger
from pydantic import BaseModel, Field
from src.schemas.composition import CompileRequest
from src.services.composition import EditorjsEngine

router = APIRouter(route_class=LoggingRoute, prefix="/soan-thao/editorjs")

@router.post("/bien-dich")
async def compile_editorjs(req: CompileRequest):
    try:
        pdf_bytes = await EditorjsEngine.compile_to_pdf(req.content)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as e:
        logger.exception("Lỗi xử lý biên dịch nội dung EditorJS")
        raise HTTPException(status_code=500, detail=f"Lỗi biên dịch tài liệu: {e}")

@router.post("/ket-xuat/{format}")
async def export_editorjs(
    format: str,
    req: CompileRequest,
):
    try:
        if format == "pdf":
            pdf_bytes = await EditorjsEngine.compile_to_pdf(req.content)
            return Response(content=pdf_bytes, media_type="application/pdf")
        else:
            out_bytes = await EditorjsEngine.export_to_format(req.content, format)
            return Response(
                content=out_bytes, media_type="application/octet-stream"
            )
    except Exception as e:
        logger.exception("Lỗi xử lý kết xuất tài liệu")
        raise HTTPException(status_code=500, detail=f"Lỗi kết xuất tài liệu: {e}")
