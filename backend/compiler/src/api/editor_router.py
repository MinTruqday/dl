from typing import Any, List, Optional

from core.config import settings
from core.dependency import AuthenticatedUser, Depends, Header, HTTPException
from core.dependency import get_current_user_from_header as get_current_user
from core.schemas.inference import (AISuggestionRequest, CoverGenerateRequest,
                                    PlagiarismCheckRequest)
from fastapi import APIRouter
from loguru import logger
from src.schemas.editor_schema import (AutoSaveRequest, FindReplaceRequest,
                                       InlineCommentRequest,
                                       InlineSuggestionRequest,
                                       KeystrokeSyncRequest,
                                       PomodoroSyncRequest,
                                       ResolveSuggestionRequest,
                                       VersionDiffRequest)
from src.services.editor_service import EditorService

router = APIRouter(prefix="/soan-thao")


@router.post("/{document_id}/check-plagiarism")
async def check_plagiarism(
    document_id: str,
    current_user=Depends(get_current_user),
    agentic_ai_url: str = Header(settings.AGENTIC_AI_URL),
):
    return {
        "data": await EditorService.check_deep_plagiarism(
            document_id, current_user, agentic_ai_url
        ),
        "message": "Đã hoàn tất kiểm tra đạo văn",
        "status": 200,
    }


@router.post("/{document_id}/sync-action")
async def sync_keystroke_buffer(
    document_id: str,
    payload: KeystrokeSyncRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await EditorService.sync_keystroke_buffer(
            document_id, payload.model_dump(), current_user
        ),
        "message": "Đã đồng bộ thao tác gõ phím",
        "status": 200,
    }


@router.post("/document/{document_id}/suggestion")
async def add_inline_suggestion(
    document_id: str,
    payload: InlineSuggestionRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await EditorService.add_inline_suggestion(
            document_id, payload.model_dump(), current_user
        ),
        "message": "Đã thêm đề xuất chỉnh sửa",
        "status": 201,
    }


@router.put("/suggestion/{suggestion_id}/resolve")
async def resolve_suggestion(
    suggestion_id: str,
    payload: ResolveSuggestionRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await EditorService.resolve_suggestion(
            suggestion_id, payload.model_dump(), current_user
        ),
        "message": "Đã xử lý xong đề xuất chỉnh sửa",
        "status": 200,
    }


@router.post("/pomodoro")
async def sync_pomodoro_session(
    payload: PomodoroSyncRequest, current_user=Depends(get_current_user)
):
    return {
        "data": await EditorService.sync_pomodoro_session(
            payload.model_dump(), current_user
        ),
        "message": "Đã lưu phiên làm việc Pomodoro",
        "status": 200,
    }


@router.post("/{document_id}/auto-save")
async def auto_save_draft(
    document_id: str, payload: AutoSaveRequest, current_user=Depends(get_current_user)
):
    return {
        "data": await EditorService.auto_save_draft(
            document_id, payload.content, current_user
        ),
        "message": "Đã tự động lưu bản nháp",
        "status": 200,
    }


@router.post("/{document_id}/submit-review")
async def submit_for_review(document_id: str, current_user=Depends(get_current_user)):
    return {
        "data": await EditorService.submit_for_review(document_id, current_user),
        "message": "Đã gửi tài liệu để chờ xét duyệt",
        "status": 201,
    }


@router.post("/{document_id}/replace-all")
async def global_find_replace(
    document_id: str,
    payload: FindReplaceRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await EditorService.global_find_replace(
            document_id,
            payload.search,
            payload.replace,
            payload.match_case,
            current_user,
        ),
        "message": "Đã thay thế từ khóa trên toàn bộ tài liệu",
        "status": 200,
    }


@router.post("/{document_id}/ai-suggest")
async def get_ai_suggestions(
    document_id: str,
    payload: current_user = Depends(get_current_user),
    agentic_ai_url: str = Header(settings.AGENTIC_AI_URL),
):
    return {
        "data": await EditorService.get_ai_suggestions(
            document_id, payload.context, current_user, agentic_ai_url
        ),
        "message": "Đã tải gợi ý từ AI",
        "status": 200,
    }


@router.post("/{document_id}/summarize")
async def summarize_document(
    document_id: str,
    current_user=Depends(get_current_user),
    agentic_ai_url: str = Header(settings.AGENTIC_AI_URL),
):
    return {
        "data": await EditorService.summarize_document(
            document_id, current_user, agentic_ai_url
        ),
        "message": "Đã tóm tắt xong tài liệu",
        "status": 200,
    }


@router.post("/{document_id}/analyze-tags")
async def extract_smart_tags(
    document_id: str,
    current_user=Depends(get_current_user),
    agentic_ai_url: str = Header(settings.AGENTIC_AI_URL),
):
    return {
        "data": await EditorService.extract_smart_tags(
            document_id, current_user, agentic_ai_url
        ),
        "message": "Đã phân tích và gắn thẻ tự động",
        "status": 200,
    }


@router.post("/{document_id}/check-logic")
async def check_logic(
    document_id: str,
    payload: dict,
    current_user=Depends(get_current_user),
    agentic_ai_url: str = Header(settings.AGENTIC_AI_URL),
):
    return {
        "data": await EditorService.check_logic(
            document_id, payload.get("content", ""), current_user, agentic_ai_url
        ),
        "message": "Đã kiểm tra tính nhất quán",
        "status": 200,
    }


@router.post("/{document_id}/check-grammar")
async def check_grammar(
    document_id: str,
    current_user=Depends(get_current_user),
    agentic_ai_url: str = Header(settings.AGENTIC_AI_URL),
):
    return {
        "data": await EditorService.check_grammar(
            document_id, current_user, agentic_ai_url
        ),
        "message": "Đã kiểm tra ngữ pháp",
        "status": 200,
    }


@router.post("/{document_id}/comment")
async def add_inline_comment(
    document_id: str,
    payload: InlineCommentRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await EditorService.add_inline_comment(
            document_id, payload.model_dump(), current_user
        ),
        "message": "Đã thêm nhận xét",
        "status": 200,
    }


@router.get("/{document_id}/comment")
async def get_inline_comments(document_id: str, current_user=Depends(get_current_user)):
    return {
        "data": await EditorService.get_inline_comments(document_id, current_user),
        "message": "Đã tải danh sách nhận xét",
        "status": 200,
    }


@router.put("/comment/{comment_id}/resolve")
async def resolve_comment(comment_id: str, current_user=Depends(get_current_user)):
    return {
        "data": await EditorService.resolve_comment(comment_id, current_user),
        "message": "Đã xử lý nhận xét",
        "status": 200,
    }


@router.post("/{document_id}/compare-version")
async def get_version_diff(
    document_id: str,
    payload: VersionDiffRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await EditorService.get_version_diff(
            document_id, payload.version_id_a, payload.version_id_b, current_user
        ),
        "message": "Đã tải dữ liệu so sánh phiên bản",
        "status": 200,
    }
