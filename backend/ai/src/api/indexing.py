from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from src.schemas.response import APIResponse
from src.core.dependency import CurrentUser, Role, get_current_user, get_current_user_optional, verify_internal_token
from src.schemas.ingestion import AttachmentConversionRequest, IngestRequest, IngestResponse
from src.services.ingestion import convert_attachment as convert_attachment_data
from src.services.ingestion import extract_document as extract_document_text
from src.services.ingestion import index_document, remove_document
from src.services.knowledge import knowledge_service

router = APIRouter(prefix="/tiep-nap")
indexing_router = APIRouter(dependencies=[Depends(verify_internal_token)])


@router.post("")
async def ingest_endpoint(
    req: IngestRequest, current_user: CurrentUser = Depends(get_current_user)
):
    logger.info(f"Started document ingestion process document_id={req.document_id}")
    try:
        result = await knowledge_service.ingest_document(
            req.document_id, str(current_user.id), current_user.role == Role.ADMIN
        )
        logger.info(f"Document ingestion completed document_id={req.document_id}")
        return result
    except Exception:
        logger.exception("Document ingestion pipeline error")
        raise


@router.delete("/tai-lieu/{document_id}")
async def delete_document_endpoint(
    document_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    logger.info(f"Started document deletion from vector store document_id={document_id}")
    try:
        await knowledge_service.delete_document(
            document_id, str(current_user.id), current_user.role == Role.ADMIN
        )
        logger.info(f"Document deletion completed document_id={document_id}")
        return {"status": "success", "message_code": "document_vectors_deleted"}
    except Exception:
        logger.exception("Document deletion error")
        raise


def resolve_requester(req: IngestRequest, user: CurrentUser):
    requester_id = str(user.id) if user else str(req.requester_id or "")
    if not requester_id and not user and req.is_admin:
        requester_id = "platform-system"
    if not requester_id:
        raise HTTPException(status_code=403, detail="Missing document requester")
    return requester_id, user.is_admin() if user else req.is_admin


def document_error(error: Exception):
    if isinstance(error, HTTPException):
        return error
    if isinstance(error, PermissionError):
        return HTTPException(status_code=403, detail="Document access denied")
    if isinstance(error, ValueError):
        return HTTPException(status_code=404, detail=str(error))
    return HTTPException(status_code=502, detail={"code": "knowledge_dependency_failed"})


@indexing_router.post("/ingest", response_model=APIResponse[IngestResponse], description="Nạp và chỉ mục hóa tài liệu vào knowledge")
async def ingest_document(
    req: IngestRequest, user: CurrentUser = Depends(get_current_user_optional)
):
    requester_id, is_admin = resolve_requester(req, user)
    try:
        result = await index_document(req.document_id, requester_id, is_admin)
    except Exception as error:
        raise document_error(error)
    return APIResponse(
        data=IngestResponse(
            document_id=result.get("document_id", req.document_id),
            status=result.get("status", "indexed"),
            chunks_count=result.get("chunks_count", 0),
            extraction_method=result.get("extraction_method", "local"),
            quarantined_chunks=result.get("quarantined_chunks", []),
            failed_chunks=result.get("failed_chunks", []),
        ),
        message="Nạp và chỉ mục hóa tài liệu thành công",
    )


@indexing_router.post("/extract", response_model=APIResponse[dict], description="Trích xuất nội dung tài liệu cho knowledge")
async def extract_document(
    req: IngestRequest, user: CurrentUser = Depends(get_current_user_optional)
):
    requester_id, is_admin = resolve_requester(req, user)
    try:
        markdown = await extract_document_text(req.document_id, requester_id, is_admin)
    except Exception as error:
        raise document_error(error)
    return APIResponse(
        data={"document_id": req.document_id, "text": markdown},
        message="Trích xuất nội dung tài liệu thành công",
    )


@indexing_router.post("/convert", response_model=APIResponse[dict], description="Chuyển đổi attachment thành nội dung có cấu trúc")
async def convert_attachment(req: AttachmentConversionRequest):
    try:
        result = await convert_attachment_data(req.data, req.filename)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return APIResponse(
        data=result,
        message="Chuyển đổi tài liệu thành công",
    )


@indexing_router.delete("/document/{document_id}", response_model=APIResponse[dict], description="Xóa chỉ mục knowledge của tài liệu")
async def delete_document(
    document_id: str,
    requester_id: str = "",
    is_admin: bool = False,
    user: CurrentUser = Depends(get_current_user_optional),
):
    resolved_id = str(user.id) if user else requester_id
    resolved_admin = user.is_admin() if user else is_admin
    if not resolved_id:
        raise HTTPException(status_code=403, detail="Missing document requester")
    try:
        result = await remove_document(document_id, resolved_id, resolved_admin)
    except Exception as error:
        raise document_error(error)
    return APIResponse(
        data=result,
        message="Xóa chỉ mục tài liệu thành công",
    )
