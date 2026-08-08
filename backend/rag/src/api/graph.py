from fastapi import APIRouter, Depends
from src.core.logging_route import LoggingRoute
from src.core.logic_logger import log_logic_execution
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, get_current_user_optional, require_role, Role
from src.schemas.graph import (
    GraphExpandRequest,
    GraphExpandResponse,
    ReplaceDocumentGraphRequest,
)
from src.services.graph import graph_service

router = APIRouter(route_class=LoggingRoute)

@router.post("/expand", response_model=APIResponse[GraphExpandResponse])
@log_logic_execution
async def expand_graph(
    req: GraphExpandRequest,
    user: CurrentUser = Depends(get_current_user_optional),
):
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
    user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN])),
):
    await graph_service.replace_document(req.document_id, req.relations)
    return APIResponse(
        data={"document_id": req.document_id, "status": "updated"},
        message="Cập nhật quan hệ đồ thị thành công",
    )

@router.delete("/document/{document_id}", response_model=APIResponse[dict])
@log_logic_execution
async def delete_document_graph(
    document_id: str,
    user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN])),
):
    await graph_service.delete_document(document_id)
    return APIResponse(
        data={"document_id": document_id, "status": "deleted"},
        message="Xóa quan hệ đồ thị thành công",
    )
