from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException, WebSocket, WebSocketDisconnect
from core.response import APIResponse
from api.dependency import get_current_user, require_role
from models.user import UserInDB, RoleEnum
from core.config import settings
import httpx
import websockets
import asyncio

CONTENT_URL = settings.CONTENT_SERVICE_URL
CONTENT_WS_URL = CONTENT_URL.replace("http://", "ws://").replace("https://", "wss://")

async def _proxy(method: str, path: str, **kwargs):
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            res = await client.request(method, f"{CONTENT_URL}{path}", **kwargs)
            if res.status_code >= 400:
                raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Lỗi"))
            return res.json()
        except HTTPException:
            raise
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Lỗi kết nối Content Service: {e}")

from models.user import UserInDB, RoleEnum
from models.chapter import ChapterCreate
from models.editor import PlagiarismCheckRequest, KeystrokeSyncRequest, InlineSuggestionRequest, ResolveSuggestionRequest, PomodoroSyncRequest, FindReplaceRequest, AutoSaveRequest, CoverGenerateRequest, AISuggestionRequest, InlineCommentRequest, VersionDiffRequest
router = APIRouter(prefix='/soan-thao')

@router.post('/{document_id}/kiem-tra-dao-van', response_model=APIResponse[Any])
async def analyze_internal_plagiarism(document_id: str, payload: PlagiarismCheckRequest, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    return APIResponse(data=await EditorService.analyze_internal_plagiarism(document_id, payload.model_dump(), current_user, db=db), message='Phân tích đạo văn nội bộ thành công', status=200)

@router.post('/{document_id}/dong-bo-thao-tac', response_model=APIResponse[Any])
async def sync_keystroke_buffer(document_id: str, payload: KeystrokeSyncRequest, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    return APIResponse(data=await EditorService.sync_keystroke_buffer(document_id, payload.model_dump(), current_user, db=db), message='Đồng bộ bộ đệm gõ phím thành công', status=200)

@router.get('/latex', response_model=APIResponse[Any])
async def get_latex(db=Depends(get_db)):
    return APIResponse(data=await EditorService.get_latex(db=db), message='Lấy mã nguồn LaTeX thành công', status=200)

@router.post('/tai-lieu/{document_id}/goi-y', response_model=APIResponse[Any])
async def add_inline_suggestion(document_id: str, payload: InlineSuggestionRequest, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    return APIResponse(data=await EditorService.add_inline_suggestion(document_id, payload.model_dump(), current_user, db=db), message='Thêm gợi ý nội dòng thành công', status=201)

@router.put('/goi-y/{suggestion_id}/giai-quyet', response_model=APIResponse[Any])
async def resolve_suggestion(suggestion_id: str, payload: ResolveSuggestionRequest, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    return APIResponse(data=await EditorService.resolve_suggestion(suggestion_id, payload.model_dump(), current_user, db=db), message='Xử lý gợi ý thành công', status=200)

@router.post('/pomodoro', response_model=APIResponse[Any])
async def sync_pomodoro_session(payload: PomodoroSyncRequest, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    return APIResponse(data=await EditorService.sync_pomodoro_session(payload.model_dump(), current_user, db=db), message='Đồng bộ phiên Pomodoro thành công', status=200)

@router.post('/{document_id}/tu-dong-luu', response_model=APIResponse[Any])
async def auto_save_draft(document_id: str, payload: AutoSaveRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await EditorService.auto_save_draft(document_id, payload.content, current_user, db=db), message='Tự động lưu bản nháp thành công', status=200)

@router.post('/{document_id}/gui-duyet', response_model=APIResponse[Any])
async def submit_for_review(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await EditorService.submit_for_review(document_id, current_user, db=db), message='Gửi tài liệu để xem xét thành công', status=201)

@router.post('/{document_id}/kiem-tra-dao-van-chuyen-sau', response_model=APIResponse[Any])
async def check_deep_plagiarism(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await EditorService.check_deep_plagiarism(document_id, current_user, db=db), message='Kiểm tra đạo văn chuyên sâu thành công', status=200)

@router.post('/{document_id}/thay-the-toan-cuc', response_model=APIResponse[Any])
async def global_find_replace(document_id: str, payload: FindReplaceRequest, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    return APIResponse(data=await EditorService.global_find_replace(document_id, payload.search, payload.replace, payload.match_case, current_user, db=db), message='Thay thế toàn cục thành công', status=200)

@router.get('/{document_id}/ngu-phap/{chapter_id}', response_model=APIResponse[Any])
async def check_grammar(document_id: str, chapter_id: str, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR])), db=Depends(get_db)):
    return APIResponse(data=await EditorService.check_grammar(document_id, chapter_id, current_user, db=db), message='Kiểm tra ngữ pháp hoàn tất')

@router.post('/{document_id}/anh-bia/tao-ai', response_model=APIResponse[Any])
async def generate_cover(document_id: str, payload: CoverGenerateRequest, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR])), db=Depends(get_db)):
    return APIResponse(data=await EditorService.generate_cover(document_id, payload.style, current_user, db=db), message='Khởi tạo ảnh bìa AI thành công')

@router.post('/{document_id}/chuong', response_model=APIResponse[Any])
async def add_chapter(document_id: str, chapter_in: ChapterCreate, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)) -> Any:
    return APIResponse(data=await DocumentService.add_chapter(document_id, chapter_in, current_user, db=db), message='Thêm chương mới thành công', status=201)

@router.put('/{document_id}/anh-bia', response_model=APIResponse[Any])
async def update_cover(document_id: str, cover_url: str, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)) -> Any:
    return APIResponse(data=await DocumentService.update_cover(document_id, cover_url, current_user, db=db), message='Cập nhật ảnh bìa thành công', status=200)

@router.post('/{document_id}/goi-y-ai', response_model=APIResponse[Any])
async def get_ai_suggestions(document_id: str, payload: AISuggestionRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await EditorService.get_ai_suggestions(document_id, payload.context, current_user, db=db), message='Lấy gợi ý AI thành công')

@router.post('/{document_id}/tom-tat', response_model=APIResponse[Any])
async def summarize_document(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await EditorService.summarize_document(document_id, current_user, db=db), message='Tóm tắt tài liệu thành công')

@router.post('/{document_id}/phan-tich-the', response_model=APIResponse[Any])
async def extract_smart_tags(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await EditorService.extract_smart_tags(document_id, current_user, db=db), message='Tự động phân tích thẻ thành công')

@router.post('/{document_id}/kiem-tra-logic', response_model=APIResponse[Any])
async def check_logic(document_id: str, payload: dict, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await EditorService.check_logic(document_id, payload.get('content', ''), current_user, db=db), message='Kiểm tra tính nhất quán thành công')

@router.post('/{document_id}/binh-luan', response_model=APIResponse[Any])
async def add_inline_comment(document_id: str, payload: InlineCommentRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await EditorService.add_inline_comment(document_id, payload.model_dump(), current_user, db=db), message='Thêm nhận xét thành công')

@router.get('/{document_id}/binh-luan', response_model=APIResponse[Any])
async def get_inline_comments(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await EditorService.get_inline_comments(document_id, current_user, db=db), message='Lấy danh sách nhận xét thành công')

@router.put('/binh-luan/{comment_id}/giai-quyet', response_model=APIResponse[Any])
async def resolve_comment(comment_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await EditorService.resolve_comment(comment_id, current_user, db=db), message='Đã xử lý nhận xét')

@router.post('/{document_id}/so-sanh-phien-ban', response_model=APIResponse[Any])
async def get_version_diff(document_id: str, payload: VersionDiffRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await EditorService.get_version_diff(document_id, payload.version_id_a, payload.version_id_b, current_user, db=db), message='Lấy dữ liệu so sánh phiên bản thành công')