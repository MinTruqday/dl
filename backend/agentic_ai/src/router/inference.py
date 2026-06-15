import httpx
import json as json_mod
import re
from collections import Counter
from core.config import settings
from core.dependency import get_current_user
from core.repositories.base_repository import RepositoryFactory
from core.schemas.user import RoleEnum, UserInDB
from fastapi import APIRouter, Depends, HTTPException
from huggingface_hub import AsyncInferenceClient
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from src.core.prompt import PromptType, prompt_registry
from src.rag.embedder import embedding_service
from src.schemas.requests import ActionRequest, CitationRequest, CodeRequest, GenerationRequest, GrammarRequest, ReviewRequest, SentimentRequest, SummarizeRequest, SynthesisRequest, ToneRequest
from src.store.vector import vector_store

router = APIRouter(prefix="/inference")
client = AsyncInferenceClient(token=settings.HF_TOKEN)

async def _check_quota(current_user: UserInDB):
    try:
        async with httpx.AsyncClient() as c:
            resp = await c.get(f"{settings.PROVISION_URL}/quota/verify", params={"user_id": str(current_user.id), "role": current_user.role.value, "ai_tier": current_user.ai_tier.value, "feature": "chat"}, timeout=settings.DEFAULT_HTTP_TIMEOUT)
            if resp.status_code != 200:
                raise HTTPException(status_code=429, detail="Your account has aggressively exceeded strictly allocated operational artificial intelligence network computation query quotas")
            return resp.json().get("data", {})
    except HTTPException:
        raise
    except Exception:
        logger.error("The system failed executing necessary authentication checks verifying current individual active user query limits")
        return {"model": settings.QWEN_MODEL, "req_reset_hours": 24}

async def _consume_quota(current_user: UserInDB, tokens: int, req_reset_hours: int = 24):
    try:
        async with httpx.AsyncClient() as c:
            await c.post(f"{settings.PROVISION_URL}/quota/consume", json={"user_id": str(current_user.id), "feature": "chat", "req_reset_hours": req_reset_hours, "tokens": tokens}, timeout=settings.DEFAULT_HTTP_TIMEOUT)
    except Exception:
        logger.error("The backend infrastructure fundamentally failed correctly subtracting completely consumed computational tokens active user profile")

async def _chat_direct(messages: list, max_tokens: int = 500, temperature: float = 0.3, model: str = settings.LLAMA_MODEL) -> str:
    try:
        response = await client.chat_completion(model=model, messages=messages, max_tokens=max_tokens, temperature=temperature)
        return response.choices[0].message.content
    except Exception:
        logger.error("The artificial intelligence system encountered an unexpected structural exception during language textual generation processing")
        raise Exception("The system encountered an unexpected error and requires you to try again later")

async def _run_ai_with_quota(current_user: UserInDB, messages: list, max_tokens: int = 500, temperature: float = 0.3) -> str:
    limits = await _check_quota(current_user)
    model = limits.get("model", settings.QWEN_MODEL)
    result = await _chat_direct(messages, max_tokens, temperature, model)
    prompt_len = sum((len(m.get("content", "")) for m in messages))
    tokens_used = (prompt_len + len(result)) // 4
    await _consume_quota(current_user, tokens_used, limits.get("req_reset_hours", 24))
    return result

@router.post("/generate-content")
async def generate_text(req: GenerationRequest, current_user: UserInDB = Depends(get_current_user)):
    try:
        result = await _run_ai_with_quota(current_user, messages=[{"role": "user", "content": req.prompt}], max_tokens=req.max_tokens, temperature=req.temperature)
        return {"result": result}
    except Exception:
        raise HTTPException(status_code=500, detail="The system encountered an unexpected error and requires you to try again later")

@router.post("/translate")
async def translate_text(req: TranslationRequest, current_user: UserInDB = Depends(get_current_user)):
    try:
        prompt = prompt_registry.get(PromptType.TRANSLATE).format(target_lang=req.target_lang, text=req.text)
        result = await _run_ai_with_quota(current_user, messages=[{"role": "user", "content": prompt}], max_tokens=len(req.text) * 3, temperature=0.1)
        return {"translation": result.strip()}
    except Exception:
        raise HTTPException(status_code=500, detail="The system encountered an unexpected error and requires you to try again later")

@router.post("/sentiment-analysis")
async def analyze_sentiment(req: SentimentRequest, current_user: UserInDB = Depends(get_current_user)):
    try:
        texts_to_analyze = req.texts or []
        if req.document_id:
            mongo_client = AsyncIOMotorClient(settings.MONGODB_URI)
            db = mongo_client.get_default_database()
            comments = await RepositoryFactory.get("comments").find({"document_id": req.document_id}, {"content": 1}).limit(20).to_list(length=20)
            texts_to_analyze.extend([c["content"] for c in comments if c.get("content")])
            mongo_client.close()
        if not texts_to_analyze:
            return {"sentiment_score": 0.0, "mood": "unknown", "summary": "There is structurally absolutely no valid text metadata available executing meaningful rigorous analytical sentiment extraction", "top_emotions": []}
        results = []
        for text in texts_to_analyze[:10]:
            prompt = prompt_registry.get(PromptType.SENTIMENT_ANALYSIS).format(text=text)
            sentiment = await _run_ai_with_quota(current_user, messages=[{"role": "user", "content": prompt}], max_tokens=10, temperature=0.1)
            results.append(sentiment.strip())
        pos = sum((1 for r in results if r.lower() in ["positive", "positive"]))
        neg = sum((1 for r in results if r.lower() in ["negative", "negative"]))
        total = len(results)
        score = (pos - neg) / total if total > 0 else 0
        mood = "neutral"
        if score > 0.2: mood = "positive"
        elif score < -0.2: mood = "negative"
        summary_prompt = prompt_registry.get(PromptType.SENTIMENT_SUMMARY).format(reviews="; ".join(texts_to_analyze[:5]))
        summary = await _run_ai_with_quota(current_user, messages=[{"role": "user", "content": summary_prompt}], max_tokens=100)
        emotions_map = Counter(results)
        top_emotions = [{"emotion": k, "count": v} for (k, v) in emotions_map.most_common()]
        return {"sentiment_score": score, "mood": mood, "summary": summary.strip(), "top_emotions": top_emotions, "analysis": [{"text": t, "sentiment": s} for (t, s) in zip(texts_to_analyze, results)]}
    except Exception:
        logger.error("The specific active sentiment linguistic parsing analytics functionality encountered an unpredictable severe formatting processing failure")
        raise HTTPException(status_code=500, detail="The system encountered an unexpected error and requires you to try again later")

@router.post("/generate-code")
async def generate_code(req: CodeRequest, current_user: UserInDB = Depends(get_current_user)):
    try:
        prompt = prompt_registry.get(PromptType.CODE_GENERATION).format(language=req.language, prompt=req.prompt)
        result = await _run_ai_with_quota(current_user, messages=[{"role": "user", "content": prompt}], max_tokens=1024, temperature=0.2)
        return {"code": result.strip()}
    except Exception:
        raise HTTPException(status_code=500, detail="The system encountered an unexpected error and requires you to try again later")

@router.post("/check-grammar")
async def grammar_check(req: GrammarRequest, current_user: UserInDB = Depends(get_current_user)):
    import difflib
    try:
        if current_user.role != RoleEnum.ADMIN and current_user.ai_tier.value != "PREMIUM":
            raise HTTPException(status_code=403, detail="This specific advanced functional processing feature is strictly restricted allowing premium operational subscription profile access only")
        prompt = prompt_registry.get(PromptType.GRAMMAR_CHECK).format(text=req.text)
        result = await _run_ai_with_quota(current_user, messages=[{"role": "user", "content": prompt}], max_tokens=len(req.text) + 200, temperature=0.1)
        similarity = difflib.SequenceMatcher(None, req.text, result.strip()).ratio()
        return {"corrected_text": result.strip(), "score": round(similarity * 100, 1), "message": "The spelling and linguistic grammar extraction logic and statistical structural evaluation finished processing safely completely"}
    except Exception:
        raise HTTPException(status_code=500, detail="The system encountered an unexpected error and requires you to try again later")

@router.post("/check-plagiarism")
async def check_plagiarism(req: GrammarRequest, current_user: UserInDB = Depends(get_current_user)):
    try:
        if current_user.role != RoleEnum.ADMIN and current_user.ai_tier.value != "PREMIUM":
            raise HTTPException(status_code=403, detail="This specific advanced functional processing feature is strictly restricted allowing premium operational subscription profile access only")
        query_vector = await embedding_service.embed_query(req.text[:2000])
        matches = await vector_store.query(query_vector=query_vector, limit=5)
        significant_matches = [m for m in matches if m["score"] > 0.75]
        if not significant_matches:
            return {"plagiarism_score": 0.0, "status": "clean", "message": "The system discovered completely zero analogous linguistic paragraphs indicating inherently highly unique individual composition entirely", "matches": []}
        context = "\n".join([f"- Match (Score: {m['score']:.2f}): {m['text'][:200]}" for m in significant_matches])
        prompt = prompt_registry.get(PromptType.PLAGIARISM_DETECTION).format(text=req.text[:1000], context=context)
        result = await _run_ai_with_quota(current_user, messages=[{"role": "user", "content": prompt}], max_tokens=300, temperature=0.1)
        try:
            json_match = re.search(r"\{.*\}", result, re.DOTALL)
            if json_match:
                return json_mod.loads(json_match.group())
        except Exception:
            logger.warning("The operational diagnostic routine stumbled briefly actively interpreting algorithmic textual sequence parsing validation checking format")
        max_score = max([m["score"] for m in significant_matches]) * 100
        return {"plagiarism_score": round(max_score, 1), "status": ("warning" if max_score > 60 else "danger" if max_score > 85 else "clean"), "message": "The advanced automated checking component observed highly concerning semantic similarity within indexed fundamental library structural archives", "matches": significant_matches[:3]}
    except Exception:
        logger.error("The critical structural checking diagnostic procedure experienced disastrous internal routing calculation engine execution parsing failure")
        raise HTTPException(status_code=500, detail="The system encountered an unexpected error and requires you to try again later")