from typing import Any, List, Optional

from fastapi import APIRouter
from loguru import logger
from src.schemas.editor import (
    AutoSaveRequest,
    FindReplaceRequest,
    InlineCommentRequest,
    InlineSuggestionRequest,
    KeystrokeSyncRequest,
    PomodoroSyncRequest,
    ResolveSuggestionRequest,
    VersionDiffRequest,
)
from src.services.editor import EditorManager

from core.config import settings
from core.dependency import AuthenticatedUser, Depends, Header, HTTPException
from core.dependency import get_current_user_from_header as get_current_user


def require_premium_ai(current_user: AuthenticatedUser = Depends(get_current_user)):
    if (
        current_user.ai_tier.value not in ["PREMIUM"]
        and current_user.role.value != "admin"
    ):
        raise HTTPException(
            status_code=403, detail="Tính năng AI nâng cao chỉ dành cho gói trả phí"
        )
    return current_user


router = APIRouter(prefix="/trinh-soan-thao")


@router.post("/{document_id}/dong-bo")
async def sync_keystroke_buffer(
    document_id: str,
    payload: KeystrokeSyncRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await EditorManager.sync_keystroke_buffer(
            document_id, payload.model_dump(), current_user
        ),
        "message": "Đồng bộ hóa dữ liệu chỉnh sửa thành công",
        "status": 200,
    }


@router.post("/{document_id}/goi-y")
async def add_inline_suggestion(
    document_id: str,
    payload: InlineSuggestionRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await EditorManager.add_inline_suggestion(
            document_id, payload.model_dump(), current_user
        ),
        "message": "Ghi nhận đề xuất chỉnh sửa thành công",
        "status": 201,
    }


@router.put("/goi-y/{suggestion_id}/giai-quyet")
async def resolve_suggestion(
    suggestion_id: str,
    payload: ResolveSuggestionRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await EditorManager.resolve_suggestion(
            suggestion_id, payload.model_dump(), current_user
        ),
        "message": "Xử lý đề xuất chỉnh sửa thành công",
        "status": 200,
    }


@router.post("/dong-ho-pomodoro")
async def sync_pomodoro_session(
    payload: PomodoroSyncRequest, current_user=Depends(get_current_user)
):
    return {
        "data": await EditorManager.sync_pomodoro_session(
            payload.model_dump(), current_user
        ),
        "message": "Đồng bộ dữ liệu phiên tập trung thành công",
        "status": 200,
    }


@router.post("/{document_id}/tu-dong-luu")
async def auto_save_draft(
    document_id: str, payload: AutoSaveRequest, current_user=Depends(get_current_user)
):
    return {
        "data": await EditorManager.auto_save_draft(
            document_id, payload.content, current_user
        ),
        "message": "Lưu bản nháp thành công",
        "status": 200,
    }


@router.post("/{document_id}/gui-danh-gia")
async def submit_for_review(document_id: str, current_user=Depends(get_current_user)):
    return {
        "data": await EditorManager.submit_for_review(document_id, current_user),
        "message": "Đã đưa tài liệu vào hàng đợi xét duyệt",
        "status": 201,
    }


@router.post("/{document_id}/tim-va-thay-the")
async def global_find_replace(
    document_id: str,
    payload: FindReplaceRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await EditorManager.global_find_replace(
            document_id,
            payload.search,
            payload.replace,
            payload.match_case,
            current_user,
        ),
        "message": "Thao tác tìm kiếm và thay thế thành công",
        "status": 200,
    }





@router.post("/{document_id}/binh-luan")
async def add_inline_comment(
    document_id: str,
    payload: InlineCommentRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await EditorManager.add_inline_comment(
            document_id, payload.model_dump(), current_user
        ),
        "message": "Thêm bình luận ngữ cảnh thành công",
        "status": 200,
    }


@router.get("/{document_id}/binh-luan")
async def get_inline_comments(document_id: str, current_user=Depends(get_current_user)):
    return {
        "data": await EditorManager.get_inline_comments(document_id, current_user),
        "message": "Lấy bình luận trực tiếp thành công",
        "status": 200,
    }


@router.put("/binh-luan/{comment_id}/giai-quyet")
async def resolve_comment(comment_id: str, current_user=Depends(get_current_user)):
    return {
        "data": await EditorManager.resolve_comment(comment_id, current_user),
        "message": "Người dùng đã giải quyết bình luận",
        "status": 200,
    }


@router.post("/{document_id}/so-sanh-phien-ban")
async def get_version_diff(
    document_id: str,
    payload: VersionDiffRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await EditorManager.get_version_diff(
            document_id, payload.version_id_a, payload.version_id_b, current_user
        ),
        "message": "Phân tích so sánh các phiên bản tài liệu thành công",
        "status": 200,
    }
