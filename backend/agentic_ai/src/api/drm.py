from fastapi import APIRouter, HTTPException, Header
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
    """Evaluate an internal document rights policy request"""
    if x_internal_token != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail={"code": "invalid_internal_token"})
    try:
        policy = await evaluate_drm_policy(
            user_id=request.user_id,
            document_id=request.document_id,
            client_ip=request.client_ip,
            user_tier=request.user_tier,
            document_type=request.document_type,
            device_fingerprint=request.device_fingerprint,
        )
        return {"status": "success", "data": policy}
    except Exception:
        logger.exception("Failed to evaluate DRM policy")
        raise HTTPException(
            status_code=503,
            detail={"code": "drm_policy_unavailable"},
        )
