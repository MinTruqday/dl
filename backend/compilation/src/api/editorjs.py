from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from loguru import logger
from src.schemas.composition import CompileRequest
from src.engines.editorjs import EditorjsEngine
from src.engines.editorjs_capabilities import (
    capabilities_by_id,
    capability_page,
)
from src.core.dependency import RateLimiting, get_current_user

router = APIRouter(route_class=LoggingRoute, prefix="/soan-thao/editorjs")


@router.get("/capabilities")
async def get_editorjs_capabilities(
    query: str = Query(default="", max_length=120),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    include_icons: bool = Query(default=False),
    current_user=Depends(get_current_user),
):
    return capability_page(
        query=query,
        offset=offset,
        limit=limit,
        include_icons=include_icons,
    )


@router.get("/capabilities/{feature_id}")
async def get_editorjs_capability(
    feature_id: str,
    current_user=Depends(get_current_user),
):
    feature = capabilities_by_id().get(feature_id)
    if feature is None:
        raise HTTPException(
            status_code=404,
            detail="Capability không tồn tại",
        )
    return feature


@router.post("/bien-dich", dependencies=[Depends(RateLimiting(10, 60))])
async def compile_editorjs(req: CompileRequest, current_user=Depends(get_current_user)):
    try:
        pdf_bytes = await EditorjsEngine.compile_to_pdf(req.content)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except ValueError:
        logger.warning("Rejected invalid EditorJS compilation request")
        raise HTTPException(status_code=400, detail="Quá trình biên dịch tài liệu thất bại")

@router.post("/ket-xuat/{format}", dependencies=[Depends(RateLimiting(10, 60))])
async def export_editorjs(
    format: str,
    req: CompileRequest,
    current_user=Depends(get_current_user),
):
    if format not in {"pdf", "docx", "html"}:
        raise HTTPException(status_code=400, detail="Định dạng xuất không được hỗ trợ")
    try:
        if format == "pdf":
            pdf_bytes = await EditorjsEngine.compile_to_pdf(req.content)
            return Response(content=pdf_bytes, media_type="application/pdf")
        out_bytes = await EditorjsEngine.export_to_format(req.content, format)
        media_type = "text/html" if format == "html" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        return Response(content=out_bytes, media_type=media_type)
    except ValueError:
        logger.warning("Rejected invalid EditorJS export request")
        raise HTTPException(status_code=400, detail="Quá trình kết xuất tài liệu thất bại")
