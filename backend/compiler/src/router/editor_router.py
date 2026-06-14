# src/router/editor_router.py
from typing import Any, List, Optional

from core.config import settings
from core.dependency import AuthenticatedUser, Depends, Header, HTTPException
from core.dependency import get_current_user_from_header as get_current_user
from core.schemas.inference import (
    AISuggestionRequest,
    CoverGenerateRequest,
    PlagiarismCheckRequest,
)
from fastapi import APIRouter
from loguru import logger
from src.schemas.editor_schema import (
    AutoSaveRequest,
    FindReplaceRequest,
    InlineCommentRequest,
    InlineSuggestionRequest,
    KeystrokeSyncRequest,
    PomodoroSyncRequest,
    ResolveSuggestionRequest,
    VersionDiffRequest,
)
from src.services.editor_service import EditorService

def require_premium_ai(current_user: AuthenticatedUser = Depends(get_current_user)):
    if current_user.ai_tier.value not in ["PREMIUM"] and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Premium AI features require a premium subscription")
    return current_user

router = APIRouter(prefix="/editor")


@router.post("/{document_id}/plagiarism-check")
async def check_plagiarism(
    document_id: str,
    current_user=Depends(require_premium_ai),
    agentic_ai_url: str = Header(settings.AGENTIC_AI_URL),
):
    return {
        "data": await EditorService.check_deep_plagiarism(
            document_id, current_user, agentic_ai_url
        ),
        "message": "Plagiarism check completed successfully",
        "status": 200,
    }


@router.post("/{document_id}/sync")
async def sync_keystroke_buffer(
    document_id: str,
    payload: KeystrokeSyncRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await EditorService.sync_keystroke_buffer(
            document_id, payload.model_dump(), current_user
        ),
        "message": "Keystroke buffer synchronized",
        "status": 200,
    }


@router.post("/{document_id}/suggestions")
async def add_inline_suggestion(
    document_id: str,
    payload: InlineSuggestionRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await EditorService.add_inline_suggestion(
            document_id, payload.model_dump(), current_user
        ),
        "message": "Inline suggestion added successfully",
        "status": 201,
    }


@router.put("/suggestions/{suggestion_id}/resolve")
async def resolve_suggestion(
    suggestion_id: str,
    payload: ResolveSuggestionRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await EditorService.resolve_suggestion(
            suggestion_id, payload.model_dump(), current_user
        ),
        "message": "Inline suggestion resolved",
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
        "message": "Pomodoro session synced successfully",
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
        "message": "Draft saved automatically",
        "status": 200,
    }


@router.post("/{document_id}/submit-review")
async def submit_for_review(document_id: str, current_user=Depends(get_current_user)):
    return {
        "data": await EditorService.submit_for_review(document_id, current_user),
        "message": "Document submitted for review",
        "status": 201,
    }


@router.post("/{document_id}/find-replace")
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
        "message": "Global find and replace completed",
        "status": 200,
    }


@router.post("/{document_id}/ai-suggestions")
async def get_ai_suggestions(
    document_id: str,
    payload: AISuggestionRequest,
    current_user=Depends(require_premium_ai),
    agentic_ai_url: str = Header(settings.AGENTIC_AI_URL),
):
    return {
        "data": await EditorService.get_ai_suggestions(
            document_id, payload.context, current_user, agentic_ai_url
        ),
        "message": "AI suggestions retrieved successfully",
        "status": 200,
    }


@router.post("/{document_id}/summarize")
async def summarize_document(
    document_id: str,
    current_user=Depends(require_premium_ai),
    agentic_ai_url: str = Header(settings.AGENTIC_AI_URL),
):
    return {
        "data": await EditorService.summarize_document(
            document_id, current_user, agentic_ai_url
        ),
        "message": "Document summarized successfully",
        "status": 200,
    }


@router.post("/{document_id}/extract-tags")
async def extract_smart_tags(
    document_id: str,
    current_user=Depends(require_premium_ai),
    agentic_ai_url: str = Header(settings.AGENTIC_AI_URL),
):
    return {
        "data": await EditorService.extract_smart_tags(
            document_id, current_user, agentic_ai_url
        ),
        "message": "Smart tags extracted successfully",
        "status": 200,
    }


@router.post("/{document_id}/check-logic")
async def check_logic(
    document_id: str,
    payload: dict,
    current_user=Depends(require_premium_ai),
    agentic_ai_url: str = Header(settings.AGENTIC_AI_URL),
):
    return {
        "data": await EditorService.check_logic(
            document_id, payload.get("content", ""), current_user, agentic_ai_url
        ),
        "message": "Logic check completed successfully",
        "status": 200,
    }


@router.post("/{document_id}/check-grammar")
async def check_grammar(
    document_id: str,
    current_user=Depends(require_premium_ai),
    agentic_ai_url: str = Header(settings.AGENTIC_AI_URL),
):
    return {
        "data": await EditorService.check_grammar(
            document_id, current_user, agentic_ai_url
        ),
        "message": "Grammar check completed successfully",
        "status": 200,
    }


@router.post("/{document_id}/comments")
async def add_inline_comment(
    document_id: str,
    payload: InlineCommentRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await EditorService.add_inline_comment(
            document_id, payload.model_dump(), current_user
        ),
        "message": "Inline comment added successfully",
        "status": 200,
    }


@router.get("/{document_id}/comments")
async def get_inline_comments(document_id: str, current_user=Depends(get_current_user)):
    return {
        "data": await EditorService.get_inline_comments(document_id, current_user),
        "message": "Inline comments retrieved successfully",
        "status": 200,
    }


@router.put("/comments/{comment_id}/resolve")
async def resolve_comment(comment_id: str, current_user=Depends(get_current_user)):
    return {
        "data": await EditorService.resolve_comment(comment_id, current_user),
        "message": "Inline comment resolved",
        "status": 200,
    }


@router.post("/{document_id}/compare-versions")
async def get_version_diff(
    document_id: str,
    payload: VersionDiffRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await EditorService.get_version_diff(
            document_id, payload.version_id_a, payload.version_id_b, current_user
        ),
        "message": "Version comparison retrieved successfully",
        "status": 200,
    }
