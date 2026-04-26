from fastapi import APIRouter, Depends, Request
from .dependencies import get_current_user_optional
from models.user import UserInDB
from services.rag import RagService

router = APIRouter(prefix="/rag")

@router.post("/stream")
async def proxy_rag_stream(
    payload: dict, 
    req: Request, 
    current_user: UserInDB = Depends(get_current_user_optional)
):
    auth_header = req.headers.get("Authorization")
    return await RagService.proxy_rag_stream(payload, auth_header, current_user)

@router.post("/chat")
async def proxy_rag_chat(
    payload: dict, 
    req: Request, 
    current_user: UserInDB = Depends(get_current_user_optional)
):
    auth_header = req.headers.get("Authorization")
    return await RagService.proxy_rag_chat(payload, auth_header, current_user)
