from typing import Any
from shared.core.response import APIResponse
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from shared.models.user import UserInDB, RoleEnum
from api.dependency import require_role, get_current_user
from services.editor import EditorService, manager
from typing import List, Optional
from loguru import logger
from services.document import DocumentService
from pydantic import BaseModel
router = APIRouter(prefix="/soan-thao")
class ChapterCreate(BaseModel):
    title: str
    content: str
    is_premium: bool = False
    price_dl: int = 0
@router.websocket("/o-cam/{document_id}")
async def editor_websocket(websocket: WebSocket, document_id: str):
    try:
        await manager.connect(websocket, document_id)
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data.encode("utf-8"), document_id, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, document_id)
    except Exception as e:
logger.info("Log message sanitized"))
        manager.disconnect(websocket, document_id)
@router.websocket("/o-cam-crdt/{document_id}")
async def editor_crdt_websocket(websocket: WebSocket, document_id: str):
    try:
        await manager.connect(websocket, document_id)
        while True:
            data = await websocket.receive_bytes()
            await manager.broadcast(data, document_id, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, document_id)
    except Exception as e:
logger.info("Log message sanitized"))
        manager.disconnect(websocket, document_id)
@router.post("/{document_id}/kiem-tra-dao-van", response_model=APIResponse[Any])
async def analyze_internal_plagiarism(
    document_id: str,
    content_payload: dict,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    return APIResponse(data=await EditorService.analyze_internal_plagiarism(document_id, content_payload, current_user), message="Phân tích đạo văn nội bộ thành công", status=200)
@router.post("/{document_id}/dong-bo-thao-tac", response_model=APIResponse[Any])
async def sync_keystroke_buffer(
    document_id: str,
    payload: dict,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    return APIResponse(data=await EditorService.sync_keystroke_buffer(document_id, payload, current_user), message="Đồng bộ bộ đệm gõ phím thành công", status=200)
@router.get("/latex", response_model=APIResponse[Any])
async def get_latex():
    return APIResponse(data=await EditorService.get_latex(), message="Lấy mã nguồn LaTeX thành công", status=200)
@router.post("/tai-lieu/{document_id}/goi-y", response_model=APIResponse[Any])
async def add_inline_suggestion(
    document_id: str, 
    payload: dict, 
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    return APIResponse(data=await EditorService.add_inline_suggestion(document_id, payload, current_user), message="Thêm gợi ý nội dòng thành công", status=201)
@router.put("/goi-y/{suggestion_id}/giai-quyet", response_model=APIResponse[Any])
async def resolve_suggestion(
    suggestion_id: str, 
    payload: dict, 
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    return APIResponse(data=await EditorService.resolve_suggestion(suggestion_id, payload, current_user), message="Xử lý gợi ý thành công", status=200)
@router.post("/pomodoro", response_model=APIResponse[Any])
async def sync_pomodoro_session(
    payload: dict, 
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    return APIResponse(data=await EditorService.sync_pomodoro_session(payload, current_user), message="Đồng bộ phiên Pomodoro thành công", status=200)
@router.post("/{document_id}/tu-dong-luu", response_model=APIResponse[Any])
async def auto_save_draft(document_id: str, content: dict, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await EditorService.auto_save_draft(document_id, content, current_user), message="Tự động lưu bản nháp thành công", status=200)
@router.post("/{document_id}/gui-duyet", response_model=APIResponse[Any])
async def submit_for_review(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await EditorService.submit_for_review(document_id, current_user), message="Gửi tài liệu để xem xét thành công", status=201)
@router.post("/{document_id}/kiem-tra-dao-van-chuyen-sau", response_model=APIResponse[Any])
async def check_deep_plagiarism(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await EditorService.check_deep_plagiarism(document_id, current_user), message="Kiểm tra đạo văn chuyên sâu thành công", status=200)
@router.post("/{document_id}/thay-the-toan-cuc", response_model=APIResponse[Any])
async def global_find_replace(
    document_id: str, 
    payload: dict, 
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
):
    search_term = payload.get("search")
    replace_term = payload.get("replace")
    match_case = payload.get("match_case", False)
    return APIResponse(data=await EditorService.global_find_replace(document_id, search_term, replace_term, match_case, current_user), message="Thay thế toàn cục thành công", status=200)
@router.get("/{document_id}/ngu-phap/{chapter_id}", response_model=APIResponse[Any])
async def check_grammar(document_id: str, chapter_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await EditorService.check_grammar(document_id, chapter_id, current_user),
        message="Kiểm tra ngữ pháp hoàn tất"
    )
@router.post("/{document_id}/anh-bia/tao-ai", response_model=APIResponse[Any])
async def generate_cover(document_id: str, style: str = "minimalist", current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR]))):
    return APIResponse(
        data=await EditorService.generate_cover(document_id, style, current_user),
        message="Khởi tạo ảnh bìa AI thành công"
    )
@router.post("/{document_id}/chuong", response_model=APIResponse[Any])
async def add_chapter(
    document_id: str,
    chapter_in: ChapterCreate,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
) -> Any:
    return APIResponse(data=await DocumentService.add_chapter(document_id, chapter_in, current_user), message="Thêm chương mới thành công", status=201)
@router.put("/{document_id}/anh-bia", response_model=APIResponse[Any])
async def update_cover(
    document_id: str,
    cover_url: str,
    current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))
) -> Any:
    return APIResponse(data=await DocumentService.update_cover(document_id, cover_url, current_user), message="Cập nhật ảnh bìa thành công", status=200)
@router.post("/{document_id}/anh-bia-ai", response_model=APIResponse[Any])
async def generate_ai_cover(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await DocumentService.generate_ai_cover(document_id, current_user), message="Khởi tạo ảnh bìa AI thành công", status=200)
