from fastapi import APIRouter
from src.core.logging_route import LoggingRoute
from src.core.logic_logger import log_logic_execution
from src.core.response import APIResponse
from src.schemas.cache import (
    CacheGetRequest,
    CacheGetResponse,
    CacheSetRequest,
)
from src.services.cache import cache_service

router = APIRouter(route_class=LoggingRoute)

@router.post("/get", response_model=APIResponse[CacheGetResponse])
@log_logic_execution
async def get_cache(req: CacheGetRequest):
    res = await cache_service.get_response(req.query_text, req.query_vector)
    return APIResponse(
        data=res,
        message="Truy vấn semantic cache thành công",
    )

@router.post("/set", response_model=APIResponse[dict])
@log_logic_execution
async def set_cache(req: CacheSetRequest):
    await cache_service.set_response(req.query_text, req.response_text, req.query_vector)
    return APIResponse(
        data={"status": "stored"},
        message="Lưu semantic cache thành công",
    )
