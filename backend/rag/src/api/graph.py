from fastapi import APIRouter, Depends, HTTPException
from src.core.logging_route import LoggingRoute
from src.core.logic_logger import log_logic_execution
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, get_current_user_optional, verify_internal_token
from src.schemas.graph import (
    GraphExpandRequest,
    GraphExpandResponse,
    ReplaceDocumentGraphRequest,
)
from src.services.graph import graph_service
from src.services.content_client import content_client

router = APIRouter(
    route_class=LoggingRoute,
    dependencies=[Depends(verify_internal_token)],
)

def document_error(error: Exception):
    if isinstance(error, HTTPException):
        return error
    if isinstance(error, PermissionError):
        return HTTPException(status_code=403, detail="Document access denied")
    if isinstance(error, ValueError):
        return HTTPException(status_code=404, detail=str(error))
    return HTTPException(
        status_code=502,
        detail={"code": "rag_dependency_failed"},
    )

@router.post("/expand", response_model=APIResponse[GraphExpandResponse])
@log_logic_execution
async def expand_graph(
    req: GraphExpandRequest,
    user: CurrentUser = Depends(get_current_user_optional),
):
    requester_id = str(user.id) if user else str(req.requester_id or "")
    is_admin = user.is_admin() if user else req.is_admin
    try:
        for document_id in req.document_ids:
            await content_client.authorize_read(document_id, requester_id, is_admin)
    except Exception as error:
        raise document_error(error)
    res = await graph_service.expand(
        document_ids=req.document_ids,
        seed_query=req.seed_query,
        limit=req.limit,
    )
    return APIResponse(
        data=res,
        message="Mở rộng tri thức đồ thị thành công",
    )

@router.post("/replace-document", response_model=APIResponse[dict])
@log_logic_execution
async def replace_document_graph(
    req: ReplaceDocumentGraphRequest,
    user: CurrentUser = Depends(get_current_user_optional),
):
    requester_id = str(user.id) if user else str(req.requester_id or "")
    is_admin = user.is_admin() if user else req.is_admin
    if not requester_id:
        raise HTTPException(status_code=403, detail="Missing document requester")
    try:
        await content_client.authorize_document(
            req.document_id,
            requester_id,
            is_admin,
        )
    except Exception as error:
        raise document_error(error)
    await graph_service.replace_document(req.document_id, req.relations)
    return APIResponse(
        data={"document_id": req.document_id, "status": "updated"},
        message="Cập nhật quan hệ đồ thị thành công",
    )

@router.delete("/document/{document_id}", response_model=APIResponse[dict])
@log_logic_execution
async def delete_document_graph(
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
        )
    except Exception as error:
        raise document_error(error)
    await graph_service.delete_document(document_id)
    return APIResponse(
        data={"document_id": document_id, "status": "deleted"},
        message="Xóa quan hệ đồ thị thành công",
    )
