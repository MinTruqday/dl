from fastapi import APIRouter, Depends
from src.core.logging_route import LoggingRoute
from src.core.logic_logger import log_logic_execution
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, require_role, Role
from src.schemas.ingestion import IngestRequest, IngestResponse
from src.services.pipeline import ingestion_pipeline

router = APIRouter(route_class=LoggingRoute)

@router.post("/ingest", response_model=APIResponse[IngestResponse])
@log_logic_execution
async def ingest_document(
    req: IngestRequest,
    user: CurrentUser = Depends(require_role([Role.AUTHOR, Role.ADMIN])),
):
    result = await ingestion_pipeline.ingest_document(req.document_id)
    return APIResponse(
        data=IngestResponse(
            document_id=result.get("document_id", req.document_id),
            status=result.get("status", "indexed"),
            chunks_count=result.get("chunks_count", 0),
            extraction_method=result.get("extraction_method", "local"),
        ),
        message="Nạp và chỉ mục hóa tài liệu thành công",
    )
