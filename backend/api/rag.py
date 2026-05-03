from typing import Any, Optional
from core.response import APIResponse
from fastapi import APIRouter, Depends, Request, HTTPException
from .dependency import get_current_user_optional, get_db
from models.user import UserInDB
from services.rag import RagService
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/ai")

@router.post("/stream", response_model=Any)
async def proxy_rag_stream(
    payload: dict, 
    req: Request, 
    current_user: UserInDB = Depends(get_current_user_optional)
):
    auth_header = req.headers.get("Authorization")
    return await RagService.proxy_rag_stream(payload, auth_header, current_user)

@router.post("/query", response_model=APIResponse[Any])
async def proxy_rag_chat(
    payload: dict, 
    req: Request, 
    current_user: UserInDB = Depends(get_current_user_optional),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    use_pro = payload.get("usePro", False)
    
    if use_pro:
        if not current_user:
            raise HTTPException(status_code=401, detail="Vui lòng đăng nhập để sử dụng tính năng Pro.")

        user_wallet = await db.wallets.find_one({"user_id": current_user.id})
        balance = user_wallet.get("balance", 0) if user_wallet else 0
        
        if balance < 10:
            raise HTTPException(status_code=400, detail="Số dư không đủ để sử dụng AI Pro. Vui lòng nạp thêm dl.")

    auth_header = req.headers.get("Authorization")
    result = await RagService.proxy_rag_chat(payload, auth_header, current_user)
    
    if isinstance(result, dict) and result.get("status") in [500, 503]:
         raise HTTPException(status_code=result["status"], detail=result.get("answer", "Dịch vụ AI hiện đang bảo trì."))

    return APIResponse(data=result, message="Phản hồi từ trợ lý AI thành công.", status=200)

@router.post("/ingest/{document_id}", response_model=APIResponse[Any])
async def ingest_document(document_id: str, current_user: UserInDB = Depends(get_current_user_optional)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Bạn cần đăng nhập để thực hiện hành động này.")
    
    result = await RagService.ingest(document_id)
    return APIResponse(data=result, message="Tiến trình đồng bộ tri thức AI đã được bắt đầu.", status=200)
