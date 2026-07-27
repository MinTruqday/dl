from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Dict, Any, Optional
from loguru import logger
from src.agents.drm import evaluate_drm_policy
from src.core.infrastructure.configuration import settings

router = APIRouter(prefix="/drm-ai")

from src.schemas.drm import DRMContextRequest
@router.post("/danh-gia")
async def evaluate_drm_request(
    request: DRMContextRequest,
    x_internal_token: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    if x_internal_token != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Mã xác thực nội bộ không hợp lệ")
    try:
        policy = await evaluate_drm_policy(
            user_id=request.user_id,
            document_id=request.document_id,
            client_ip=request.client_ip,
            user_tier=request.user_tier,
            document_type=request.document_type
        )
        return {"status": "success", "data": policy}
    except Exception as e:
        logger.exception("Failed to evaluate DRM policy")
        raise HTTPException(status_code=500, detail=str(e))
