from typing import Any, List, Optional

from src.core.logging_route import LoggingRoute
from fastapi import APIRouter
from loguru import logger
from src.schemas.composition import (
    AutoSaveRequest,
    FindReplaceRequest,
    InlineCommentRequest,
    InlineSuggestionRequest,
    KeystrokeSyncRequest,
    PomodoroSyncRequest,
    ResolveSuggestionRequest,
    VersionDiffRequest,
)
from src.services.composition import CompositionService

from src.core.infrastructure.configuration import settings
from src.core.dependency import AuthenticatedUser, Depends, Header, HTTPException
from src.core.dependency import get_current_user

def require_premium_ai(current_user: AuthenticatedUser = Depends(get_current_user)):
    from src.core.dependency import Role, Tier
    if (
        getattr(current_user.ai_tier, "value", current_user.ai_tier) != Tier.PREMIUM.value
        and getattr(current_user.role, "value", current_user.role) != Role.ADMIN.value
    ):
        raise HTTPException(
            status_code=403, detail="Tính năng AI nâng cao chỉ dành cho tài khoản đã nâng cấp gói trả phí"
        )
    return current_user

router = APIRouter(route_class=LoggingRoute, prefix="/soan-thao")

@router.post("/{document_id}/dong-bo")
async def sync_keystroke_buffer(
    document_id: str,
    payload: KeystrokeSyncRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await CompositionService.sync_keystroke_buffer(
            document_id, payload.model_dump(), current_user
        ),
        "message": "Thực hiện đồng bộ hóa dữ liệu phiên bản chỉnh sửa hoàn tất",
        "status": 200,
    }

@router.post("/{document_id}/goi-y")
async def add_inline_suggestion(
    document_id: str,
    payload: InlineSuggestionRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await CompositionService.add_inline_suggestion(
            document_id, payload.model_dump(), current_user
        ),
        "message": "Thực hiện ghi nhận thông tin đề xuất chỉnh sửa hoàn tất",
        "status": 201,
    }

@router.put("/goi-y/{suggestion_id}/giai-quyet")
async def resolve_suggestion(
    suggestion_id: str,
    payload: ResolveSuggestionRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await CompositionService.resolve_suggestion(
            suggestion_id, payload.model_dump(), current_user
        ),
        "message": "Thực hiện xử lý đề xuất chỉnh sửa hoàn tất",
        "status": 200,
    }

@router.post("/dong-ho-pomodoro")
async def sync_pomodoro_session(
    payload: PomodoroSyncRequest, current_user=Depends(get_current_user)
):
    return {
        "data": await CompositionService.sync_pomodoro_session(
            payload.model_dump(), current_user
        ),
        "message": "Đồng bộ dữ liệu thời gian phiên tập trung (Pomodoro) hoàn tất",
        "status": 200,
    }

@router.post("/{document_id}/tu-dong-luu")
async def auto_save_draft(
    document_id: str, payload: AutoSaveRequest, current_user=Depends(get_current_user)
):
    return {
        "data": await CompositionService.auto_save_draft(
            document_id, payload.content, current_user
        ),
        "message": "Thực hiện thao tác lưu tự động bản nháp hoàn tất",
        "status": 200,
    }

@router.post("/{document_id}/gui-danh-gia")
async def submit_for_review(document_id: str, current_user=Depends(get_current_user)):
    return {
        "data": await CompositionService.submit_for_review(document_id, current_user),
        "message": "Đưa tài liệu vào hàng đợi xét duyệt hoàn tất",
        "status": 201,
    }

@router.post("/{document_id}/tim-va-thay-the")
async def global_find_replace(
    document_id: str,
    payload: FindReplaceRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await CompositionService.global_find_replace(
            document_id,
            payload.search,
            payload.replace,
            payload.match_case,
            current_user,
        ),
        "message": "Thao tác tìm kiếm và thay thế hoàn tất",
        "status": 200,
    }

@router.post("/{document_id}/binh-luan")
async def add_inline_comment(
    document_id: str,
    payload: InlineCommentRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await CompositionService.add_inline_comment(
            document_id, payload.model_dump(), current_user
        ),
        "message": "Thực hiện thêm mới bình luận theo ngữ cảnh hoàn tất",
        "status": 200,
    }

@router.get("/{document_id}/binh-luan")
async def get_inline_comments(document_id: str, current_user=Depends(get_current_user)):
    return {
        "data": await CompositionService.get_inline_comments(document_id, current_user),
        "message": "Trích xuất danh sách bình luận trực tiếp hoàn tất",
        "status": 200,
    }

@router.put("/binh-luan/{comment_id}/giai-quyet")
async def resolve_comment(comment_id: str, current_user=Depends(get_current_user)):
    return {
        "data": await CompositionService.resolve_comment(comment_id, current_user),
        "message": "Thực hiện đánh dấu giải quyết bình luận hoàn tất",
        "status": 200,
    }

@router.post("/{document_id}/so-sanh-phien-ban")
async def get_version_diff(
    document_id: str,
    payload: VersionDiffRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await CompositionService.get_version_diff(
            document_id, payload.version_id_a, payload.version_id_b, current_user
        ),
        "message": "Phân tích so sánh các phiên bản tài liệu hoàn tất",
        "status": 200,
    }
