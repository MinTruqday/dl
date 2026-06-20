from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from loguru import logger
from pydantic import BaseModel, Field
from src.services.editorjs_engine import EditorJSEngine

router = APIRouter()


class CompileRequest(BaseModel):
    content: str = Field(...)


@router.post("/compile")
async def compile_editorjs(req: CompileRequest):
    try:
        pdf_bytes = await EditorJSEngine.compile_to_pdf(req.content)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception:
        logger.error("Lỗi biên dịch nội dung tài liệu")
        raise HTTPException(status_code=500, detail="Lỗi biên dịch tài liệu")
