import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any, Dict, Optional, List
from core.response import APIResponse
from models.user import UserInDB, RoleEnum
from api.dependency import require_role, get_db
from core.config import settings

router = APIRouter(prefix="/ai")
AGENTIC_AI_URL = settings.AGENTIC_AI_URL

async def _proxy_request(method: str, url: str, json_data: dict = None, headers: dict = None) -> Any:
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            req_headers = {"Content-Type": "application/json"}
            if headers:
                req_headers.update(headers)
            res = await client.request(method, url, json=json_data, headers=req_headers)
            if res.status_code >= 400:
                detail = "Lỗi từ Agentic AI"
                try:
                    detail = res.json().get("detail", detail)
                except:
                    pass
                raise HTTPException(status_code=res.status_code, detail=detail)
            return res.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Không thể kết nối đến Agentic AI: {e}")

@router.post("/tro-chuyen")
async def chat(request: Request, payload: dict, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    auth_header = request.headers.get("Authorization", "")
    payload['user_id'] = str(current_user.id)
    purchases = await db['purchases'].find({"user_id": str(current_user.id), "item_type": "document"}).to_list(length=None)
    accessible_ids = [p["item_id"] for p in purchases]
    own_docs = await db['documents'].find({"author_id": str(current_user.id)}, {"_id": 1}).to_list(length=None)
    accessible_ids.extend([str(d["_id"]) for d in own_docs])
    payload['accessible_doc_ids'] = accessible_ids
    return await _proxy_request("POST", f"{AGENTIC_AI_URL}/tro-chuyen", json_data=payload, headers={"Authorization": auth_header})

@router.post("/luong-du-lieu")
async def chat_stream(request: Request, payload: dict, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    auth_header = request.headers.get("Authorization", "")
    payload['user_id'] = str(current_user.id)
    purchases = await db['purchases'].find({"user_id": str(current_user.id), "item_type": "document"}).to_list(length=None)
    accessible_ids = [p["item_id"] for p in purchases]
    own_docs = await db['documents'].find({"author_id": str(current_user.id)}, {"_id": 1}).to_list(length=None)
    accessible_ids.extend([str(d["_id"]) for d in own_docs])
    payload['accessible_doc_ids'] = accessible_ids
    
    async def stream_generator():
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{AGENTIC_AI_URL}/luong-du-lieu", json=payload, headers={"Authorization": auth_header}) as response:
                if response.status_code >= 400:
                    yield f'data: {{"error": "Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau."}}\n\n'.encode('utf-8')
                    return
                async for chunk in response.aiter_bytes():
                    yield chunk
    return StreamingResponse(stream_generator(), media_type="text/event-stream")

@router.get("/tim-kiem-thong-minh", response_model=APIResponse[Any])
async def smart_search(query: str, request: Request, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    payload = {"query": query, "useSmart": True}
    res = await _proxy_request("POST", f"{AGENTIC_AI_URL}/tro-chuyen", json_data=payload)
    return APIResponse(data=res, message="Tìm kiếm thông minh thành công")

@router.post("/van-ban", response_model=APIResponse[Any])
async def process_text(payload: dict, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    action = payload.get("action")
    if action == "translate":
        url = f"{AGENTIC_AI_URL}/inference/dich-thuat"
        res = await _proxy_request("POST", url, json_data={"text": payload.get("text"), "target_lang": payload.get("target_lang", "Vietnamese")})
        return APIResponse(data={"result": res.get("translation")}, message="Xử lý văn bản thành công")
    else:
        url = f"{AGENTIC_AI_URL}/inference/hanh-dong"
        res = await _proxy_request("POST", url, json_data={"action": action, "text": payload.get("text"), "context": payload.get("context", "")})
        return APIResponse(data={"result": res.get("result")}, message="Xử lý văn bản thành công")

@router.post("/kiem-tra-ngu-phap", response_model=APIResponse[Any])
async def check_grammar(payload: dict, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    url = f"{AGENTIC_AI_URL}/inference/kiem-tra-ngu-phap"
    res = await _proxy_request("POST", url, json_data={"text": payload.get("text")})
    return APIResponse(data=res, message="Kiểm tra ngữ pháp thành công")

@router.post("/tao-ma-nguon", response_model=APIResponse[Any])
async def generate_code(payload: dict, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    url = f"{AGENTIC_AI_URL}/inference/tao-ma-nguon"
    res = await _proxy_request("POST", url, json_data=payload)
    return APIResponse(data=res, message="Tạo mã nguồn thành công")

@router.get("/lich-su", response_model=APIResponse[List[dict]])
async def get_user_sessions(document_id: Optional[str] = None, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    url = f"{AGENTIC_AI_URL}/lich-su?user_id={str(current_user.id)}"
    if document_id:
        url += f"&document_id={document_id}"
    res = await _proxy_request("GET", url)
    return APIResponse(data=res, message="Lấy danh sách hội thoại thành công")

@router.get("/lich-su/{session_id}", response_model=APIResponse[dict])
async def get_session_detail(session_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    url = f"{AGENTIC_AI_URL}/lich-su/{session_id}?user_id={str(current_user.id)}"
    res = await _proxy_request("GET", url)
    return APIResponse(data=res, message="Lấy chi tiết hội thoại thành công")

@router.post("/lich-su", response_model=APIResponse[dict])
async def create_session(payload: dict, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    payload['user_id'] = str(current_user.id)
    url = f"{AGENTIC_AI_URL}/lich-su"
    res = await _proxy_request("POST", url, json_data=payload)
    return APIResponse(data=res, message="Tạo hội thoại mới thành công", status=201)

@router.put("/lich-su/{session_id}/tieu-de", response_model=APIResponse[Any])
async def update_title(session_id: str, payload: dict, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    url = f"{AGENTIC_AI_URL}/lich-su/{session_id}/tieu-de?user_id={str(current_user.id)}"
    res = await _proxy_request("PUT", url, json_data=payload)
    return APIResponse(data=res, message="Cập nhật tiêu đề hội thoại thành công")

@router.delete("/lich-su/{session_id}", response_model=APIResponse[Any])
async def delete_session(session_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    url = f"{AGENTIC_AI_URL}/lich-su/{session_id}?user_id={str(current_user.id)}"
    res = await _proxy_request("DELETE", url)
    return APIResponse(data=res, message="Xóa hội thoại thành công")

@router.get("/tai-lieu/{document_id}/cam-quan", response_model=APIResponse[dict])
async def analyze_reader_sentiment(document_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    url = f"{AGENTIC_AI_URL}/inference/phan-tich-cam-xuc"
    res = await _proxy_request("POST", url, json_data={"document_id": document_id})
    return APIResponse(data=res, message="Phân tích cảm quan thành công")

@router.post("/trich-dan-thong-minh", response_model=APIResponse[Any])
async def suggest_citations(payload: dict, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    url = f"{AGENTIC_AI_URL}/inference/trich-dan-thong-minh"
    res = await _proxy_request("POST", url, json_data=payload)
    return APIResponse(data=res, message="Đề xuất trích dẫn thành công")

@router.post("/bien-doi-van-ban", response_model=APIResponse[Any])
async def transform_tone(payload: dict, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    url = f"{AGENTIC_AI_URL}/inference/bien-doi-van-ban"
    res = await _proxy_request("POST", url, json_data=payload)
    return APIResponse(data=res, message="Biến đổi văn bản thành công")

@router.post("/tham-dinh-noi-dung", response_model=APIResponse[Any])
async def peer_review(payload: dict, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    url = f"{AGENTIC_AI_URL}/inference/tham-dinh-noi-dung"
    res = await _proxy_request("POST", url, json_data=payload)
    return APIResponse(data=res, message="Thẩm định nội dung thành công")

@router.post("/tong-hop-da-tai-lieu", response_model=APIResponse[Any])
async def multi_doc_synthesis(payload: dict, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN]))):
    url = f"{AGENTIC_AI_URL}/inference/tong-hop-da-tai-lieu"
    res = await _proxy_request("POST", url, json_data=payload)
    return APIResponse(data=res, message="Tổng hợp thông tin đa tài liệu thành công")

@router.post("/tai-lieu-luu-tru/{item_id}/dich", response_model=APIResponse[Any])
async def translate_storage_document(item_id: str, payload: dict, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    # Original logic in services/ai.py copied a storage_item and translated it.
    from services.storage import StorageService
    from models.storage import StorageItemCreate
    item = await StorageService.get_item(item_id, str(current_user.id))
    if not item or item.is_folder or not item.url:
        raise HTTPException(status_code=400, detail="Tài liệu không hợp lệ")
    url = f"{AGENTIC_AI_URL}/inference/trich-xuat-van-ban"
    try:
        ext_res = await _proxy_request("POST", url, json_data={"file_url": item.url})
        extracted_text = ext_res.get("extracted_text", "")
    except Exception:
        raise HTTPException(status_code=500, detail="Lỗi trích xuất văn bản")
        
    url2 = f"{AGENTIC_AI_URL}/inference/dich-thuat"
    trans_res = await _proxy_request("POST", url2, json_data={"text": extracted_text, "target_lang": payload.get("target_lang", "vi")})
    translation = trans_res.get("translation", "")
    
    parts = item.name.rsplit(".", 1)
    new_name = f"{parts[0]}_vi.{parts[1]}" if len(parts) > 1 else f"{item.name}_vi"
    new_item = StorageItemCreate(
        name=new_name,
        parent_id=item.parent_id,
        is_folder=False,
        size=len(translation.encode('utf-8')),
        mime_type='text/plain',
        description=item.description,
        tags=item.tags
    )
    created_item = await StorageService.create_item(str(current_user.id), new_item, db)
    # Upload text to Storage... (Monolithic domain logic belongs here, not agentic-ai)
    return APIResponse(data={"translation": translation, "item": created_item.dict(by_alias=True)}, message="Dịch tài liệu thành công")

@router.get("/tai-lieu-luu-tru/{item_id}/lien-quan", response_model=APIResponse[Any])
async def get_related_storage_items(item_id: str, current_user: UserInDB = Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    from services.storage import StorageService
    item = await StorageService.get_item(item_id, str(current_user.id))
    if not item:
        raise HTTPException(status_code=404, detail="Tài liệu không tồn tại")
    
    # We query all other files with same tags
    related = []
    if item.tags:
        cursor = db['storage_items'].find({
            "owner_id": str(current_user.id),
            "is_folder": False,
            "_id": {"$ne": item_id},
            "tags": {"$in": item.tags}
        }).limit(5)
        related = await cursor.to_list(length=5)
    return APIResponse(data=related, message="Lấy tài liệu liên quan thành công")
