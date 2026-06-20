import asyncio
import base64
from typing import Any, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from huggingface_hub import AsyncInferenceClient
from loguru import logger
from src.core.prompt_registry import PromptType, prompt_registry

from core.config import settings
from core.dependency import get_current_user
from core.repositories.base_repository import RepositoryFactory
from core.schemas.inference import (
    ActionRequest,
    CitationRequest,
    CodeRequest,
    GenerationRequest,
    GrammarRequest,
    ReviewRequest,
    SummarizeRequest,
    SynthesisRequest,
    ToneRequest,
    TranslationRequest,
)
from core.schemas.user import RoleEnum, UserInDB

router = APIRouter(prefix="/suy-luan")

client = AsyncInferenceClient(token=settings.HF_TOKEN)


async def _check_quota(current_user: UserInDB):
    try:
        async with httpx.AsyncClient() as c:
            resp = await c.get(
                f"{settings.MANAGEMENT_URL}/han-muc/xac-minh",
                params={
                    "user_id": str(current_user.id),
                    "role": current_user.role.value,
                    "ai_tier": current_user.ai_tier.value,
                    "feature": "chat",
                },
                timeout=settings.DEFAULT_HTTP_TIMEOUT,
            )
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=429,
                    detail="Đã hết dung lượng sử dụng AI",
                )
            return resp.json().get("data", {})
    except HTTPException:
        raise
    except Exception:
        logger.error("Lỗi kiểm tra dung lượng sử dụng")
        return {"model": settings.QWEN_MODEL, "req_reset_hours": 24}


async def _consume_quota(
    current_user: UserInDB, tokens: int, req_reset_hours: int = 24
):
    try:
        async with httpx.AsyncClient() as c:
            await c.post(
                f"{settings.MANAGEMENT_URL}/han-muc/su-dung",
                json={
                    "user_id": str(current_user.id),
                    "feature": "chat",
                    "req_reset_hours": req_reset_hours,
                    "tokens": tokens,
                },
                timeout=settings.DEFAULT_HTTP_TIMEOUT,
            )
    except Exception:
        logger.error("Lỗi trừ dung lượng đã sử dụng")


async def _chat_direct(
    messages: List[dict],
    max_tokens: int = 500,
    temperature: float = 0.3,
    model: str = settings.LLAMA_MODEL,
) -> str:
    try:
        response = await client.chat_completion(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception:
        logger.error("Lỗi tạo văn bản tự động")
        raise Exception("Đã xảy ra lỗi, vui lòng thử lại sau")


async def _run_ai_with_quota(
    current_user: UserInDB,
    messages: List[dict],
    max_tokens: int = 500,
    temperature: float = 0.3,
) -> str:
    limits = await _check_quota(current_user)
    model = limits.get("model", settings.QWEN_MODEL)

    result = await _chat_direct(messages, max_tokens, temperature, model)

    prompt_len = sum(len(m.get("content", "")) for m in messages)
    tokens_used = (prompt_len + len(result)) // 4
    await _consume_quota(current_user, tokens_used, limits.get("req_reset_hours", 24))

    return result


@router.post("/tao-noi-dung")
async def generate_text(
    req: GenerationRequest, current_user: UserInDB = Depends(get_current_user)
):
    try:
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": req.prompt}],
            max_tokens=req.max_tokens,
            temperature=req.temperature,
        )
        return {"result": result}
    except Exception:
        raise HTTPException(
            status_code=500, detail="Đã xảy ra lỗi, vui lòng thử lại sau"
        )


@router.post("/dich-thuat")
async def translate_text(
    req: TranslationRequest, current_user: UserInDB = Depends(get_current_user)
):
    try:
        prompt = prompt_registry.get(PromptType.TRANSLATE).format(
            target_lang=req.target_lang, text=req.text
        )
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=len(req.text) * 3,
            temperature=0.1,
        )
        return {"translation": result.strip()}
    except Exception:
        raise HTTPException(
            status_code=500, detail="Đã xảy ra lỗi, vui lòng thử lại sau"
        )


@router.post("/tao-ma")
async def generate_code(
    req: CodeRequest, current_user: UserInDB = Depends(get_current_user)
):
    try:
        prompt = prompt_registry.get(PromptType.CODE_GENERATION).format(
            language=req.language, prompt=req.prompt
        )
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.2,
        )
        return {"code": result.strip()}
    except Exception:
        raise HTTPException(
            status_code=500, detail="Đã xảy ra lỗi, vui lòng thử lại sau"
        )


@router.post("/kiem-tra-ngu-phap")
async def grammar_check(
    req: GrammarRequest, current_user: UserInDB = Depends(get_current_user)
):
    try:
        if (
            current_user.role != RoleEnum.ADMIN
            and current_user.ai_tier.value != "PREMIUM"
        ):
            raise HTTPException(
                status_code=403,
                detail="Tính năng chỉ dành cho gói trả phí",
            )

        prompt = prompt_registry.get(PromptType.GRAMMAR_CHECK).format(text=req.text)
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=len(req.text) + 200,
            temperature=0.1,
        )
        import difflib

        similarity = difflib.SequenceMatcher(None, req.text, result.strip()).ratio()
        grammar_score = round(similarity * 100, 1)

        return {
            "corrected_text": result.strip(),
            "score": grammar_score,
            "message": "Hoàn tất kiểm tra ngữ pháp",
        }
    except Exception:
        raise HTTPException(
            status_code=500, detail="Đã xảy ra lỗi, vui lòng thử lại sau"
        )


@router.post("/tom-tat")
async def summarize_text(
    req: SummarizeRequest, current_user: UserInDB = Depends(get_current_user)
):
    try:
        prompt = prompt_registry.get(PromptType.SUMMARIZE).format(
            language=req.language, text=req.text
        )
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3,
        )
        return {"summary": result.strip()}
    except Exception:
        raise HTTPException(
            status_code=500, detail="Đã xảy ra lỗi, vui lòng thử lại sau"
        )


@router.post("/kiem-tra-dao-van")
async def check_plagiarism(
    req: GrammarRequest, current_user: UserInDB = Depends(get_current_user)
):
    try:
        if (
            current_user.role != RoleEnum.ADMIN
            and current_user.ai_tier.value != "PREMIUM"
        ):
            raise HTTPException(
                status_code=403,
                detail="Tính năng chỉ dành cho gói trả phí",
            )

        from src.rag.embedder import embedder
        from src.store.vector import vector_store

        query_vector = await embedding.embed_query(req.text[:2000])
        matches = await vector_store.query(query_vector=query_vector, limit=5)

        significant_matches = [m for m in matches if m["score"] > 0.75]

        if not significant_matches:
            return {
                "plagiarism_score": 0.0,
                "status": "clean",
                "message": "Tài liệu có tính nguyên bản cao, không phát hiện trùng lặp",
                "matches": [],
            }

        context = "\n".join(
            [
                f"- Match (Score: {m['score']:.2f}): {m['text'][:200]}"
                for m in significant_matches
            ]
        )
        prompt = prompt_registry.get(PromptType.PLAGIARISM_DETECTION).format(
            text=req.text[:1000], context=context
        )
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.1,
        )

        try:
            import json as json_mod
            import re

            json_match = re.search(r"\{.*\}", result, re.DOTALL)
            if json_match:
                return json_mod.loads(json_match.group())
        except Exception:
            logger.warning("Lỗi định dạng dữ liệu kiểm tra đạo văn")

        max_score = max([m["score"] for m in significant_matches]) * 100
        return {
            "plagiarism_score": round(max_score, 1),
            "status": (
                "warning" if max_score > 60 else "danger" if max_score > 85 else "clean"
            ),
            "message": "Phát hiện nội dung trùng lặp",
            "matches": significant_matches[:3],
        }
    except Exception:
        logger.error("Lỗi kiểm tra đạo văn")
        raise HTTPException(
            status_code=500, detail="Đã xảy ra lỗi, vui lòng thử lại sau"
        )


@router.post("/hanh-dong")
async def unified_action(
    req: ActionRequest, current_user: UserInDB = Depends(get_current_user)
):
    try:
        prompts = {
            "autocomplete": prompt_registry.get(PromptType.AUTOCOMPLETE).format(
                context=req.context, text=req.text
            ),
            "grammar": prompt_registry.get(PromptType.GRAMMAR_CHECK).format(
                text=req.text
            ),
            "summarize": prompt_registry.get(PromptType.SUMMARIZE).format(
                language="the input language", text=req.text
            ),
            "ai_suggestions": prompt_registry.get(PromptType.AI_SUGGESTIONS).format(
                context=req.context, text=req.text
            ),
            "check_logic": prompt_registry.get(PromptType.CHECK_LOGIC).format(
                context=req.context, text=req.text
            ),
        }

        prompt = prompts.get(req.action)
        if not prompt:
            raise HTTPException(status_code=400, detail="Thao tác không hợp lệ")

        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3,
        )
        return {"result": result.strip()}
    except Exception:
        logger.error("Lỗi thực thi tác vụ AI")
        raise HTTPException(
            status_code=500, detail="Đã xảy ra lỗi, vui lòng thử lại sau"
        )


@router.post("/tu-dong-nghia")
async def get_synonyms(
    req: GrammarRequest, current_user: UserInDB = Depends(get_current_user)
):
    try:
        if (
            current_user.role != RoleEnum.ADMIN
            and current_user.ai_tier.value != "PREMIUM"
        ):
            raise HTTPException(
                status_code=403,
                detail="Tính năng chỉ dành cho gói trả phí",
            )

        prompt = prompt_registry.get(PromptType.SYNONYMS).format(text=req.text)
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.5,
        )
        return {"synonyms": [s.strip() for s in result.split(",")]}
    except Exception:
        raise HTTPException(
            status_code=500, detail="Đã xảy ra lỗi, vui lòng thử lại sau"
        )


@router.post("/trich-dan-thong-minh")
async def suggest_citations(
    req: CitationRequest, current_user: UserInDB = Depends(get_current_user)
):
    try:
        if (
            current_user.role != RoleEnum.ADMIN
            and current_user.ai_tier.value != "PREMIUM"
        ):
            raise HTTPException(
                status_code=403,
                detail="Tính năng chỉ dành cho gói trả phí",
            )

        from src.rag.embedder import embedder
        from src.store.vector import vector_store

        query_vector = await embedding.embed_query(req.text[:500])
        matches = await vector_store.query(query_vector=query_vector, limit=3)

        sources = []
        for m in matches:
            meta = m.get("metadata", {})
            sources.append(
                f"Document: {meta.get('title', 'N/A')}, Author: {meta.get('author', 'N/A')}. Content: {m['text'][:200]}"
            )

        prompt = prompt_registry.get(PromptType.SUGGEST_CITATIONS).format(
            style=req.style, text=req.text, sources="\\n".join(sources)
        )
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3,
        )
        return {"citations": result.strip()}
    except Exception:
        raise HTTPException(
            status_code=500, detail="Đã xảy ra lỗi, vui lòng thử lại sau"
        )


@router.post("/bien-doi-van-ban")
async def transform_tone(
    req: ToneRequest, current_user: UserInDB = Depends(get_current_user)
):
    try:
        if (
            current_user.role != RoleEnum.ADMIN
            and current_user.ai_tier.value != "PREMIUM"
        ):
            raise HTTPException(
                status_code=403,
                detail="Tính năng chỉ dành cho gói trả phí",
            )

        action = "expand and transform" if req.expansion else "transform"
        prompt = prompt_registry.get(PromptType.TRANSFORM_TONE).format(
            action=action.capitalize(), tone=req.tone, text=req.text
        )
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000 if req.expansion else 500,
            temperature=0.4,
        )
        return {"transformed_text": result.strip()}
    except Exception:
        raise HTTPException(
            status_code=500, detail="Đã xảy ra lỗi, vui lòng thử lại sau"
        )


@router.post("/kiem-duyet-noi-dung")
async def peer_review(
    req: ReviewRequest, current_user: UserInDB = Depends(get_current_user)
):
    try:
        if (
            current_user.role != RoleEnum.ADMIN
            and current_user.ai_tier.value != "PREMIUM"
        ):
            raise HTTPException(
                status_code=403,
                detail="Tính năng chỉ dành cho gói trả phí",
            )

        criteria_str = (
            ", ".join(req.criteria)
            if req.criteria
            else "logic, clarity, persuasiveness"
        )
        prompt = prompt_registry.get(PromptType.CONTENT_REVIEW).format(
            criteria_str=criteria_str, text=req.text[:3000]
        )
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.2,
        )
        return {"review_report": result.strip()}
    except Exception:
        raise HTTPException(
            status_code=500, detail="Đã xảy ra lỗi, vui lòng thử lại sau"
        )


@router.post("/tong-hop-tai-lieu")
async def multi_doc_synthesis(
    req: SynthesisRequest, current_user: UserInDB = Depends(get_current_user)
):
    try:
        from src.rag.embedder import embedder
        from src.store.vector import vector_store

        query_vector = await embedding.embed_query(req.query)

        all_context = []
        for doc_id in req.document_ids:
            matches = await vector_store.query(
                query_vector=query_vector, document_id=doc_id, limit=3
            )
            for m in matches:
                all_context.append(f"[From document {doc_id}]: {m['text']}")

        prompt = prompt_registry.get(PromptType.MULTI_DOC_SYNTHESIS).format(
            query=req.query, context="\\n".join(all_context[:10])
        )
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.3,
        )
        return {"synthesis": result.strip(), "sources_count": len(req.document_ids)}
    except Exception:
        raise HTTPException(
            status_code=500, detail="Đã xảy ra lỗi, vui lòng thử lại sau"
        )


@router.post("/trich-xuat-van-ban")
async def extract_text(req: dict, current_user: UserInDB = Depends(get_current_user)):
    try:
        file_url = req.get("file_url")
        if not file_url:
            raise HTTPException(
                status_code=400, detail="Thiếu thông tin vị trí tệp tin"
            )

        from src.rag.pipeline import ingestion_pipeline

        extracted_text = await ingestion_pipeline._extract_text(file_url)

        return {"extracted_text": extracted_text}
    except Exception:
        logger.error("Lỗi trích xuất dữ liệu")
        raise HTTPException(
            status_code=500, detail="Không thể trích xuất văn bản từ nguồn cung cấp"
        )


@router.post("/phan-tich-tai-lieu")
async def analyze_document(
    req: dict, current_user: UserInDB = Depends(get_current_user)
):
    try:
        context = req.get("context", "")
        ext = req.get("ext", "txt")
        folder_str = req.get("folder_str", "None")

        prompt = prompt_registry.get(PromptType.STORAGE_FILE_ANALYSIS).format(
            ext=ext, folder_str=folder_str, context=context[:3000]
        )

        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.2,
        )

        import json as json_mod
        import re

        json_match = re.search(r"\{.*\}", result, re.DOTALL)
        if json_match:
            return json_mod.loads(json_match.group())
        else:
            raise ValueError("Mô hình ngôn ngữ trả về sai định dạng")
    except Exception:
        logger.error("Lỗi phân tích tài liệu")
        raise HTTPException(status_code=500, detail="Lỗi phân tích tài liệu")


@router.delete("/vector/{document_id}")
async def delete_vector_document(document_id: str):
    try:
        from src.store.vector import vector_store

        await vector_store.delete_by_document(document_id)
        return {"status": "success", "message": "Xóa chỉ mục tài liệu thành công"}
    except Exception:
        logger.error("Lỗi xóa chỉ mục tài liệu")
        raise HTTPException(status_code=500, detail="Lỗi xóa dữ liệu chỉ mục tài liệu")
