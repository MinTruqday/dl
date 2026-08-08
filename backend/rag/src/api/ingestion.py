from fastapi import APIRouter, Depends, HTTPException
from src.core.logging_route import LoggingRoute
from src.core.logic_logger import log_logic_execution
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, get_current_user_optional, verify_internal_token
from src.schemas.ingestion import IngestRequest, IngestResponse
from src.services.pipeline import ingestion_pipeline
from src.services.content_client import content_client
from src.services.conversion import document_parser
from src.store.graph import graph_store
from src.store.vector import vector_store

router = APIRouter(
    route_class=LoggingRoute,
    dependencies=[Depends(verify_internal_token)],
)

def resolve_requester(req: IngestRequest, user: CurrentUser):
    requester_id = str(user.id) if user else str(req.requester_id or "")
    if not requester_id:
        raise HTTPException(status_code=403, detail="Missing document requester")
    return requester_id, user.is_admin() if user else req.is_admin

def document_error(error: Exception):
    if isinstance(error, PermissionError):
        return HTTPException(status_code=403, detail="Document access denied")
    if isinstance(error, ValueError):
        return HTTPException(status_code=404, detail=str(error))
    return error

@router.post("/ingest", response_model=APIResponse[IngestResponse])
@log_logic_execution
async def ingest_document(
    req: IngestRequest,
    user: CurrentUser = Depends(get_current_user_optional),
):
    requester_id, is_admin = resolve_requester(req, user)
    try:
        result = await ingestion_pipeline.ingest_document(
            req.document_id,
            requester_id,
            is_admin,
        )
    except Exception as error:
        raise document_error(error)
    return APIResponse(
        data=IngestResponse(
            document_id=result.get("document_id", req.document_id),
            status=result.get("status", "indexed"),
            chunks_count=result.get("chunks_count", 0),
            extraction_method=result.get("extraction_method", "local"),
            graph_text=result.get("graph_text", ""),
        ),
        message="Nạp và chỉ mục hóa tài liệu thành công",
    )

@router.post("/extract", response_model=APIResponse[dict])
@log_logic_execution
async def extract_document(
    req: IngestRequest,
    user: CurrentUser = Depends(get_current_user_optional),
):
    requester_id, is_admin = resolve_requester(req, user)
    try:
        document = await content_client.authorize_document(
            req.document_id,
            requester_id,
            is_admin,
        )
    except Exception as error:
        raise document_error(error)
    file_url = str(document.get("file_url") or "")
    if not file_url:
        raise HTTPException(status_code=404, detail="Document file not found")
    markdown = await document_parser.get_markdown(
        file_url,
        visibility=document.get("visibility") or "private",
    )
    if not markdown:
        raise HTTPException(status_code=422, detail="Document text unavailable")
    return APIResponse(
        data={"document_id": req.document_id, "text": markdown},
        message="Trích xuất nội dung tài liệu thành công",
    )

@router.delete("/document/{document_id}", response_model=APIResponse[dict])
@log_logic_execution
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
        await content_client.authorize_document(
            document_id,
            resolved_id,
            resolved_admin,
            True,
        )
    except Exception as error:
        raise document_error(error)
    await vector_store.delete_by_document(document_id)
    await graph_store.delete_document(document_id)
    await content_client.mark_unindexed(document_id)
    return APIResponse(
        data={"document_id": document_id, "status": "deleted"},
        message="Xóa chỉ mục tài liệu thành công",
    )
