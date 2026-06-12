from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from loguru import logger

from src.schemas.editor import (
    PlagiarismCheckRequest, KeystrokeSyncRequest, InlineSuggestionRequest, 
    ResolveSuggestionRequest, PomodoroSyncRequest, FindReplaceRequest, 
    AutoSaveRequest, CoverGenerateRequest, AISuggestionRequest, 
    InlineCommentRequest, VersionDiffRequest
)
from src.services.editor import EditorService
from core.config import settings

router = APIRouter(prefix='/soan-thao')

class AuthenticatedUser:
    def __init__(self, user_id: str, user_name: str = "User"):
        self.id = user_id
        self.full_name = user_name

def get_current_user(x_user_id: str = Header(None), x_user_name: str = Header("User")):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Thiếu thông tin người dùng từ hệ thống")
    return AuthenticatedUser(user_id=x_user_id, user_name=x_user_name)

@router.post('/{document_id}/kiem-tra-dao-van')
async def check_plagiarism(document_id: str, current_user = Depends(get_current_user), agentic_ai_url: str = Header(settings.AGENTIC_AI_URL)):
    return {"data": await EditorService.check_deep_plagiarism(document_id, current_user, agentic_ai_url), "message": 'Đã hoàn tất kiểm tra đạo văn', "status": 200}

@router.post('/{document_id}/dong-bo-thao-tac')
async def sync_keystroke_buffer(document_id: str, payload: KeystrokeSyncRequest, current_user = Depends(get_current_user)):
    return {"data": await EditorService.sync_keystroke_buffer(document_id, payload.model_dump(), current_user), "message": 'Đã đồng bộ thao tác gõ phím', "status": 200}

@router.get('/latex')
async def get_latex():
    return {"data": await EditorService.get_latex(), "message": 'Đã tải mã nguồn tài liệu', "status": 200}

@router.post('/tai-lieu/{document_id}/goi-y')
async def add_inline_suggestion(document_id: str, payload: InlineSuggestionRequest, current_user = Depends(get_current_user)):
    return {"data": await EditorService.add_inline_suggestion(document_id, payload.model_dump(), current_user), "message": 'Đã thêm đề xuất chỉnh sửa', "status": 201}


@router.put('/goi-y/{suggestion_id}/giai-quyet')
async def resolve_suggestion(suggestion_id: str, payload: ResolveSuggestionRequest, current_user = Depends(get_current_user)):
    return {"data": await EditorService.resolve_suggestion(suggestion_id, payload.model_dump(), current_user), "message": 'Đã xử lý xong đề xuất chỉnh sửa', "status": 200}

@router.post('/pomodoro')
async def sync_pomodoro_session(payload: PomodoroSyncRequest, current_user = Depends(get_current_user)):
    return {"data": await EditorService.sync_pomodoro_session(payload.model_dump(), current_user), "message": 'Đã lưu phiên làm việc Pomodoro', "status": 200}

@router.post('/{document_id}/tu-dong-luu')
async def auto_save_draft(document_id: str, payload: AutoSaveRequest, current_user = Depends(get_current_user)):
    return {"data": await EditorService.auto_save_draft(document_id, payload.content, current_user), "message": 'Đã tự động lưu bản nháp', "status": 200}

@router.post('/{document_id}/gui-duyet')
async def submit_for_review(document_id: str, current_user = Depends(get_current_user)):
    return {"data": await EditorService.submit_for_review(document_id, current_user), "message": 'Đã gửi tài liệu để chờ xét duyệt', "status": 201}



@router.post('/{document_id}/thay-the-toan-cuc')
async def global_find_replace(document_id: str, payload: FindReplaceRequest, current_user = Depends(get_current_user)):
    return {"data": await EditorService.global_find_replace(document_id, payload.search, payload.replace, payload.match_case, current_user), "message": 'Đã thay thế từ khóa trên toàn bộ tài liệu', "status": 200}



@router.post('/{document_id}/goi-y-ai')
async def get_ai_suggestions(document_id: str, payload: AISuggestionRequest, current_user = Depends(get_current_user), agentic_ai_url: str = Header(settings.AGENTIC_AI_URL)):
    return {"data": await EditorService.get_ai_suggestions(document_id, payload.context, current_user, agentic_ai_url), "message": 'Đã tải gợi ý từ AI', "status": 200}

@router.post('/{document_id}/tom-tat')
async def summarize_document(document_id: str, current_user = Depends(get_current_user), agentic_ai_url: str = Header(settings.AGENTIC_AI_URL)):
    return {"data": await EditorService.summarize_document(document_id, current_user, agentic_ai_url), "message": 'Đã tóm tắt xong tài liệu', "status": 200}

@router.post('/{document_id}/phan-tich-the')
async def extract_smart_tags(document_id: str, current_user = Depends(get_current_user), agentic_ai_url: str = Header(settings.AGENTIC_AI_URL)):
    return {"data": await EditorService.extract_smart_tags(document_id, current_user, agentic_ai_url), "message": 'Đã phân tích và gắn thẻ tự động', "status": 200}

@router.post('/{document_id}/kiem-tra-logic')
async def check_logic(document_id: str, payload: dict, current_user = Depends(get_current_user), agentic_ai_url: str = Header(settings.AGENTIC_AI_URL)):
    return {"data": await EditorService.check_logic(document_id, payload.get('content', ''), current_user, agentic_ai_url), "message": 'Đã kiểm tra tính nhất quán', "status": 200}

@router.post('/{document_id}/kiem-tra-ngu-phap')
async def check_grammar(document_id: str, current_user = Depends(get_current_user), agentic_ai_url: str = Header(settings.AGENTIC_AI_URL)):
    return {"data": await EditorService.check_grammar(document_id, current_user, agentic_ai_url), "message": 'Đã kiểm tra ngữ pháp', "status": 200}

@router.post('/{document_id}/binh-luan')
async def add_inline_comment(document_id: str, payload: InlineCommentRequest, current_user = Depends(get_current_user)):
    return {"data": await EditorService.add_inline_comment(document_id, payload.model_dump(), current_user), "message": 'Đã thêm nhận xét', "status": 200}

@router.get('/{document_id}/binh-luan')
async def get_inline_comments(document_id: str, current_user = Depends(get_current_user)):
    return {"data": await EditorService.get_inline_comments(document_id, current_user), "message": 'Đã tải danh sách nhận xét', "status": 200}

@router.put('/binh-luan/{comment_id}/giai-quyet')
async def resolve_comment(comment_id: str, current_user = Depends(get_current_user)):
    return {"data": await EditorService.resolve_comment(comment_id, current_user), "message": 'Đã xử lý nhận xét', "status": 200}

@router.post('/{document_id}/so-sanh-phien-ban')
async def get_version_diff(document_id: str, payload: VersionDiffRequest, current_user = Depends(get_current_user)):
    return {"data": await EditorService.get_version_diff(document_id, payload.version_id_a, payload.version_id_b, current_user), "message": 'Đã tải dữ liệu so sánh phiên bản', "status": 200}