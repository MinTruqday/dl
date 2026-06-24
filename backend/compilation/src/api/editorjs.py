from fastapi import APIRouter, HTTPException
from fastapi.response import Response
from loguru import logger
from pydantic import BaseModel, Field
from src.schemas.session import CompileRequest
from src.services.session import EditorjsEngine

router = APIRouter()


@router.post("/bien-dich")
async def compile_editorjs(req: CompileRequest):
    try:
        pdf_bytes = await EditorjsEngine.compile_to_pdf(req.content)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception:
        logger.error("Lỗi biên dịch nội dung tài liệu")
        raise HTTPException(status_code=500, detail="Lỗi biên dịch tài liệu")
