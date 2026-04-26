from fastapi import APIRouter, Depends, HTTPException, Request
from .dependencies import get_current_user
from models.user import UserInDB
import httpx
import os

router = APIRouter(prefix="/inference")

RAG_SERVICE_URL = os.environ["AGENTIC_RAG_URL"]

async def proxy_post(path: str, payload: dict):
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(f"{RAG_SERVICE_URL}/api/inference/{path}", json=payload)
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi kết nối AI: {str(e)}")

@router.post("/generate-cover")
async def generate_cover(payload: dict, current_user: UserInDB = Depends(get_current_user)):
    return await proxy_post("generate-cover", payload)

@router.post("/analyze-sentiment")
async def analyze_sentiment(payload: dict, current_user: UserInDB = Depends(get_current_user)):
    return await proxy_post("analyze-sentiment", payload)

@router.post("/grammar-check")
async def grammar_check(payload: dict, current_user: UserInDB = Depends(get_current_user)):
    return await proxy_post("grammar-check", payload)

@router.post("/synonyms")
async def get_synonyms(payload: dict, current_user: UserInDB = Depends(get_current_user)):
    return await proxy_post("synonyms", payload)
