from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, Request
import json
import asyncio
from api.dependency import get_db, get_current_user, check_quota
from models.user import UserInDB
from models.ai import AITextRequest, FlashcardRequest, FlashcardReviewRequest, AIMindmapRequest, AICitationRequest, AIToneRequest, AIReviewRequest, AISynthesisRequest
from core.response import APIResponse
from services.ai import AIService
router = APIRouter(prefix='/ai')

@router.post('/tro-chuyen')
async def chat_streaming(data: dict, request: Request, current_user: UserInDB=Depends(check_quota), db=Depends(get_db)):
    from services.rag import RagService
    auth_header = request.headers.get('Authorization')
    return await RagService.proxy_rag_stream(data, auth_header, current_user, db=db)

@router.get('/tim-kiem-thong-minh', response_model=APIResponse[Any])
async def smart_search(q: str=Query(), current_user: UserInDB=Depends(check_quota), db=Depends(get_db)):
    return APIResponse(data=await AIService.smart_search(q, current_user, db=db), message='Tìm kiếm thông minh hoàn tất')

@router.post('/van-ban', response_model=APIResponse[Any])
async def process_text(req: AITextRequest, current_user: UserInDB=Depends(check_quota), db=Depends(get_db)):
    return APIResponse(data=await AIService.process_text(req, current_user, db=db), message='Xử lý văn bản bằng AI thành công')

@router.post('/tai-lieu/{document_id}/the-ghi-nho', response_model=APIResponse[Any])
async def generate_flashcard(document_id: str, data: FlashcardRequest, current_user: UserInDB=Depends(check_quota), db=Depends(get_db)):
    return APIResponse(data=await AIService.generate_flashcard(document_id, data.text, data.context, current_user, db=db), message='Tạo flashcard thành công', status=201)

@router.post('/the-ghi-nho/on-tap', response_model=APIResponse[Any])
async def review_flashcard(data: FlashcardReviewRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await AIService.review_flashcard(data.card_id, data.quality, current_user, db=db), message='Đã ghi nhận ôn tập')

@router.get('/lich-su/{session_id}', response_model=APIResponse[Any])
async def get_session(session_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    from services.rag import RagService
    session = await RagService.get_session_detail(session_id, str(current_user.id), db=db)
    if not session:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail='Không tìm thấy lịch sử hội thoại')
    return APIResponse(data=session, message='Lấy chi tiết hội thoại thành công')

@router.get('/lich-su', response_model=APIResponse[Any])
async def get_sessions(document_id: Optional[str]=None, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    from services.rag import RagService
    return APIResponse(data=await RagService.get_user_sessions(str(current_user.id), document_id, db=db), message='Lấy lịch sử hội thoại thành công')

@router.post('/lich-su', response_model=APIResponse[Any])
async def create_session(data: dict, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    from services.rag import RagService
    return APIResponse(data=await RagService.create_session(str(current_user.id), data.get('document_id'), data.get('first_query', ''), db=db), message='Khởi tạo hội thoại mới thành công', status=201)

@router.put('/lich-su/{session_id}/tieu-de', response_model=APIResponse[Any])
async def update_title(session_id: str, data: dict, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    from services.rag import RagService
    success = await RagService.update_title(session_id, data.get('title', ''), str(current_user.id), db=db)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail='Không tìm thấy hội thoại')
    return APIResponse(data={}, message='Cập nhật tiêu đề thành công')

@router.delete('/lich-su/{session_id}', response_model=APIResponse[Any])
async def delete_session(session_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    from services.rag import RagService
    success = await RagService.delete_session(session_id, str(current_user.id), db=db)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail='Không tìm thấy hội thoại')
    return APIResponse(data={}, message='Xóa hội thoại thành công')

@router.get('/tai-lieu/{document_id}/cam-quan', response_model=APIResponse[Any])
async def get_reader_sentiment(document_id: str, current_user: UserInDB=Depends(check_quota), db=Depends(get_db)):
    return APIResponse(data=await AIService.analyze_reader_sentiment(document_id, current_user, db=db), message='Phân tích cảm nhận độc giả thành công')

@router.post('/tao-ban-do-tu-duy', response_model=APIResponse[Any])
async def generate_mindmap(req: AIMindmapRequest, current_user: UserInDB=Depends(check_quota), db=Depends(get_db)):
    return APIResponse(data=await AIService.generate_mindmap(req.text, req.depth, current_user, db=db), message='Tạo bản đồ tư duy thành công')

@router.post('/trich-dan-thong-minh', response_model=APIResponse[Any])
async def suggest_citations(req: AICitationRequest, current_user: UserInDB=Depends(check_quota), db=Depends(get_db)):
    return APIResponse(data=await AIService.suggest_citations(req.text, req.style, current_user, db=db), message='Gợi ý trích dẫn thành công')

@router.post('/bien-doi-van-ban', response_model=APIResponse[Any])
async def transform_tone(req: AIToneRequest, current_user: UserInDB=Depends(check_quota), db=Depends(get_db)):
    return APIResponse(data=await AIService.transform_tone(req.text, req.tone, req.expansion, current_user, db=db), message='Biến đổi văn bản thành công')

@router.post('/tham-dinh-noi-dung', response_model=APIResponse[Any])
async def peer_review(req: AIReviewRequest, current_user: UserInDB=Depends(check_quota), db=Depends(get_db)):
    return APIResponse(data=await AIService.peer_review(req.text, req.criteria, current_user, db=db), message='Thẩm định nội dung thành công')

@router.post('/tong-hop-da-tai-lieu', response_model=APIResponse[Any])
async def multi_doc_synthesis(req: AISynthesisRequest, current_user: UserInDB=Depends(check_quota), db=Depends(get_db)):
    return APIResponse(data=await AIService.multi_doc_synthesis(req.document_ids, req.query, current_user, db=db), message='Tổng hợp đa tài liệu thành công')

@router.post('/tai-lieu-luu-tru/{item_id}/dich', response_model=APIResponse[Any])
async def translate_storage_doc(item_id: str, data: dict, current_user: UserInDB=Depends(check_quota), db=Depends(get_db)):
    target_lang = data.get('target_lang', 'vi')
    new_item = await AIService.translate_storage_document(item_id, target_lang, current_user.id, db=db)
    return APIResponse(data=new_item.dict() if new_item else {}, message='Dịch tài liệu thành công')

@router.get('/tai-lieu-luu-tru/{item_id}/lien-quan', response_model=APIResponse[Any])
async def get_related_storage_items(item_id: str, current_user: UserInDB=Depends(check_quota), db=Depends(get_db)):
    related = await AIService.get_related_storage_items(item_id, current_user.id, db=db)
    return APIResponse(data=related, message='Lấy tài liệu liên quan thành công')