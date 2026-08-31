from fastapi import APIRouter, Depends
from src.core.dependency import verify_internal_token
from src.schemas.response import APIResponse
from src.schemas.cache import CacheGetRequest, CacheGetResponse, CacheSetRequest
from src.services.cache import cache_service

router = APIRouter(dependencies=[Depends(verify_internal_token)])


@router.post("/doc", response_model=APIResponse[CacheGetResponse], description="Đọc semantic cache của knowledge")
async def get_cache(req: CacheGetRequest):
    res = await cache_service.get_response(req.query_text, req.query_vector)
    return APIResponse(data=res, message="Truy vấn semantic cache thành công")


@router.post("/ghi", response_model=APIResponse[dict], description="Ghi semantic cache của knowledge")
async def set_cache(req: CacheSetRequest):
    await cache_service.set_response(req.query_text, req.response_text, req.query_vector)
    return APIResponse(data={"status": "stored"}, message="Lưu semantic cache thành công")
