from core.config import settings
from core.dependency import AuthenticatedUser, Depends, Header, HTTPException
from core.dependency import get_current_user_from_header as get_current_user
from fastapi import APIRouter
from src.schemas.editor import (
    AISuggestionRequest,
    AutoSaveRequest,
    FindReplaceRequest,
    InlineCommentRequest,
    InlineSuggestionRequest,
    KeystrokeSyncRequest,
    PomodoroSyncRequest,
    ResolveSuggestionRequest,
    VersionDiffRequest,
)
from src.services.editor import EditorService

def require_premium_ai(current_user: AuthenticatedUser = Depends(get_current_user)):
    if current_user.ai_tier.value not in ["PREMIUM"] and current_user.get("role").value != "admin":
        raise HTTPException(
            status_code=403, 
            detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"
        )
    return current_user

router = APIRouter(prefix="/soan-thao")

@router.post("/{document_id}/dao-van-kiem-tra")
async def check_plagiarism(
    document_id: str,
    current_user=Depends(require_premium_ai),
    agentic_ai_url: str = Header(settings.AGENTIC_AI_URL),
):
    return {
        "data": await EditorService.check_deep_plagiarism(document_id, current_user, agentic_ai_url),
        "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        "status": 200,
    }

@router.post("/{document_id}/dong-bo")
async def sync_keystroke_buffer(
    document_id: str,
    payload: KeystrokeSyncRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await EditorService.sync_keystroke_buffer(document_id, payload.model_dump(), current_user),
        "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        "status": 200,
    }

@router.post("/{document_id}/goi-y")
async def add_inline_suggestion(
    document_id: str,
    payload: InlineSuggestionRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await EditorService.add_inline_suggestion(document_id, payload.model_dump(), current_user),
        "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        "status": 201,
    }

@router.put("/goi-y/{suggestion_id}/giai-quyet")
async def resolve_suggestion(
    suggestion_id: str,
    payload: ResolveSuggestionRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await EditorService.resolve_suggestion(suggestion_id, payload.model_dump(), current_user),
        "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        "status": 200,
    }

@router.post("/thoi-gian")
async def sync_pomodoro_session(
    payload: PomodoroSyncRequest, current_user=Depends(get_current_user)
):
    return {
        "data": await EditorService.sync_pomodoro_session(payload.model_dump(), current_user),
        "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        "status": 200,
    }

@router.post("/{document_id}/tu-dong-luu-lai")
async def auto_save_draft(
    document_id: str, payload: AutoSaveRequest, current_user=Depends(get_current_user)
):
    return {
        "data": await EditorService.auto_save_draft(document_id, payload.content, current_user),
        "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        "status": 200,
    }

@router.post("/{document_id}/gui-di-danh-gia")
async def submit_for_review(document_id: str, current_user=Depends(get_current_user)):
    return {
        "data": await EditorService.submit_for_review(document_id, current_user),
        "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        "status": 201,
    }

@router.post("/{document_id}/tim-kiem-thay-nhan-dan")
async def global_find_replace(
    document_id: str,
    payload: FindReplaceRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await EditorService.global_find_replace(
            document_id, payload.search, payload.replace, payload.match_case, current_user
        ),
        "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        "status": 200,
    }

@router.post("/{document_id}/ai-goi-y")
async def get_ai_suggestions(
    document_id: str,
    payload: AISuggestionRequest,
    current_user=Depends(require_premium_ai),
    agentic_ai_url: str = Header(settings.AGENTIC_AI_URL),
):
    return {
        "data": await EditorService.get_ai_suggestions(document_id, payload.context, current_user, agentic_ai_url),
        "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        "status": 200,
    }

@router.post("/{document_id}/tom-tat")
async def summarize_document(
    document_id: str,
    current_user=Depends(require_premium_ai),
    agentic_ai_url: str = Header(settings.AGENTIC_AI_URL),
):
    return {
        "data": await EditorService.summarize_document(document_id, current_user, agentic_ai_url),
        "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        "status": 200,
    }

@router.post("/{document_id}/trich-xuat-nhan-dan")
async def extract_smart_tags(
    document_id: str,
    current_user=Depends(require_premium_ai),
    agentic_ai_url: str = Header(settings.AGENTIC_AI_URL),
):
    return {
        "data": await EditorService.extract_smart_tags(document_id, current_user, agentic_ai_url),
        "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        "status": 200,
    }

@router.post("/{document_id}/kiem-tra-xu-ly")
async def check_logic(
    document_id: str,
    payload: dict,
    current_user=Depends(require_premium_ai),
    agentic_ai_url: str = Header(settings.AGENTIC_AI_URL),
):
    return {
        "data": await EditorService.check_logic(document_id, payload.get("content", ""), current_user, agentic_ai_url),
        "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        "status": 200,
    }

@router.post("/{document_id}/kiem-tra-ngu-phap")
async def check_grammar(
    document_id: str,
    current_user=Depends(require_premium_ai),
    agentic_ai_url: str = Header(settings.AGENTIC_AI_URL),
):
    return {
        "data": await EditorService.check_grammar(document_id, current_user, agentic_ai_url),
        "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        "status": 200,
    }

@router.post("/{document_id}/binh-luan")
async def add_inline_comment(
    document_id: str,
    payload: InlineCommentRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await EditorService.add_inline_comment(document_id, payload.model_dump(), current_user),
        "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        "status": 200,
    }

@router.get("/{document_id}/binh-luan")
async def get_inline_comments(document_id: str, current_user=Depends(get_current_user)):
    return {
        "data": await EditorService.get_inline_comments(document_id, current_user),
        "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        "status": 200,
    }

@router.put("/binh-luan/{comment_id}/giai-quyet")
async def resolve_comment(comment_id: str, current_user=Depends(get_current_user)):
    return {
        "data": await EditorService.resolve_comment(comment_id, current_user),
        "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        "status": 200,
    }

@router.post("/{document_id}/so-sanh-phien-lam-cam-quyen")
async def get_version_diff(
    document_id: str,
    payload: VersionDiffRequest,
    current_user=Depends(get_current_user),
):
    return {
        "data": await EditorService.get_version_diff(document_id, payload.version_id_a, payload.version_id_b, current_user),
        "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        "status": 200,
    }