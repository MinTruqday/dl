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
