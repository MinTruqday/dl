import json
from typing import List

import httpx
from fastapi import APIRouter, Depends, HTTPException
from huggingface_hub import AsyncInferenceClient
from loguru import logger

from src.core.dependency import CurrentUser, Role, get_current_user, verify_internal_token
from src.core.infrastructure.configuration import settings
from src.core.logging_route import LoggingRoute
from src.core.model_runtime import run_chat_completion
from src.core.registry import PromptType, registry
from src.utils.structured_output import extract_json_value
from src.schemas.inference import (
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
    GlossaryRequest,
    StyleImitationRequest,
    DraftWithMemoryRequest,
    ExtractToStorageRequest,
    WebFactCheckRequest,
    ComplianceScreenRequest,
    SemanticDiffRequest,
    QuickRepliesRequest,
)
from src.schemas.auth import Tier

router = APIRouter(route_class=LoggingRoute, prefix="/suy-luan")

client = AsyncInferenceClient(token=settings.HF_TOKEN)

async def _check_quota(current_user: CurrentUser):
    logger.info("AI quota verification started")
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            resp = await c.get(
                f"{settings.USAGE_URL}/han-muc/xac-minh",
                params={
                    "user_id": str(current_user.id),
                    "role": current_user.role.value,
                    "ai_tier": current_user.ai_tier.value,
                    "feature": "chat",
                },
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=429,
                    detail={"code": "ai_quota_exceeded"},
                )
            return resp.json().get("data", {})
    except HTTPException:
        raise
    except Exception:
        logger.exception("AI quota verification error")
        raise HTTPException(status_code=503, detail={"code": "quota_service_unavailable"})

async def _consume_quota(
    current_user: CurrentUser, tokens: int, req_reset_hours: int = 24
):
    logger.info("AI quota consumption started tokens={}", tokens)
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            response = await c.post(
                f"{settings.USAGE_URL}/han-muc/su-dung",
                json={
                    "user_id": str(current_user.id),
                    "feature": "chat",
                    "req_reset_hours": req_reset_hours,
                    "tokens": tokens,
                },
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
            response.raise_for_status()
    except Exception:
        logger.exception("AI quota consumption error")
        raise HTTPException(status_code=503, detail={"code": "quota_consumption_failed"})

async def _chat_direct(
    messages: List[dict],
    max_tokens: int = 500,
    temperature: float = 0.3,
    model: str = settings.LLM_MODEL,
) -> str:
    return await run_chat_completion(
        client=client,
        messages=messages,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
    )


def _public_ai_error(operation: str, exc: Exception) -> HTTPException:
    if isinstance(exc, HTTPException):
        return exc
    logger.exception("AI endpoint failed operation={}", operation)
    return HTTPException(
        status_code=500,
        detail={"code": f"{operation}_failed"},
    )

async def _run_ai_with_quota(
    current_user: CurrentUser,
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
    req: GenerationRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """Generate bounded text under the authenticated user quota"""
    logger.info("Text generation started")
    try:
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": req.prompt}],
            max_tokens=req.max_tokens,
            temperature=req.temperature,
        )
        logger.info("Text generation completed")
        return {"result": result}
    except Exception as exc:
        raise _public_ai_error("text_generation", exc)

@router.post("/dich-thuat")
async def translate_text(
    req: TranslationRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """Translate bounded text into the requested target language"""
    logger.info("Translation started target_language={}", req.target_lang)
    try:
        prompt = registry.get(PromptType.TRANSLATE).format(
            target_lang=req.target_lang, text=req.text
        )
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=min(len(req.text) * 3, 4000),
            temperature=0.1,
        )
        logger.info("Translation completed")
        return {"translation": result.strip()}
    except Exception as exc:
        raise _public_ai_error("translation", exc)

@router.post("/goi-y-tra-loi")
async def generate_quick_replies(
    req: QuickRepliesRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """Generate structured quick replies from bounded conversation history"""
    logger.info("Quick reply generation started")
    try:
        history_text = "\n".join(req.history_messages)
        prompt = registry.get(PromptType.QUICK_REPLIES).format(
            history=history_text
        )
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.3,
        )
        try:
            replies = extract_json_value(result)
            valid = (
                isinstance(replies, list)
                and len(replies) == 3
                and all(
                    isinstance(reply, str)
                    and 1 <= len(reply.split()) <= 6
                    and "." * 3 not in reply
                    and chr(8230) not in reply
                    and not any(ord(char) >= 0x1F000 for char in reply)
                    for reply in replies
                )
            )
            if not valid:
                replies = []
        except (TypeError, ValueError):
            replies = []
            
        logger.info("Quick reply generation completed")
        return {
            "replies": replies[:3],
            "error_code": None if replies else "quick_replies_invalid_output",
        }
    except Exception:
        logger.exception("Quick reply generation failed")
        return {"replies": [], "error_code": "quick_replies_unavailable"}

@router.post("/tao-ma")
async def generate_code(
    req: CodeRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """Generate complete source code for the requested language and task"""
    try:
        prompt = registry.get(PromptType.CODE_GENERATION).format(
            language=req.language, prompt=req.prompt
        )
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.2,
        )
        return {"code": result.strip()}
    except Exception as exc:
        raise _public_ai_error("code_generation", exc)

@router.post("/kiem-tra-ngu-phap")
async def grammar_check(
    req: GrammarRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """Check and correct grammar for an eligible authenticated user"""
    try:
        if (
            current_user.role != Role.ADMIN
            and current_user.ai_tier.value != Tier.PREMIUM.value
        ):
            raise HTTPException(
                status_code=403,
                detail={"code": "premium_tier_required"},
            )

        prompt = registry.get(PromptType.GRAMMAR_CHECK).format(text=req.text)
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=min(len(req.text) + 200, 4000),
            temperature=0.1,
        )
        import difflib

        similarity = difflib.SequenceMatcher(None, req.text, result.strip()).ratio()
        grammar_score = round(similarity * 100, 1)

        return {
            "corrected_text": result.strip(),
            "score": grammar_score,
            "message_code": "grammar_check_completed",
        }
    except Exception as exc:
        raise _public_ai_error("grammar_check", exc)

@router.post("/tom-tat")
async def summarize_text(
    req: SummarizeRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """Summarize bounded text in the requested language"""
    logger.info("Text summarization started")
    try:
        prompt = registry.get(PromptType.SUMMARIZE).format(
            language=req.language, text=req.text
        )
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3,
        )
        logger.info("Text summarization completed")
        return {"summary": result.strip()}
    except Exception as exc:
        raise _public_ai_error("summarization", exc)

@router.post("/kiem-tra-dao-van")
async def check_plagiarism(
    req: GrammarRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """Estimate plagiarism risk and return structured matching evidence"""
    logger.info("Plagiarism detection started")
    try:
        if (
            current_user.role != Role.ADMIN
            and current_user.ai_tier.value != Tier.PREMIUM.value
        ):
            logger.warning("Plagiarism detection access denied due to service tier")
            raise HTTPException(
                status_code=403,
                detail={"code": "premium_tier_required"}
            )

        from src.rag.embedding import embedder
        from src.store.vector import vector_store

        query_vector = await embedder.embed_query(req.text[:2000])
        matches = await vector_store.query(query_vector=query_vector, limit=5)

        significant_matches = [m for m in matches if m["score"] > 0.75]

        if not significant_matches:
            return {
                "plagiarism_score": 0.0,
                "status": "clean",
                "message_code": "plagiarism_not_detected",
                "matches": [],
            }

        context = "\n".join(
            [
                "- Match (Score: {m['score']:.2f}): {m['text'][:200]}"
                for m in significant_matches
            ]
        )
        prompt = registry.get(PromptType.PLAGIARISM_DETECTION).format(
            text=req.text[:1000], context=context
        )
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.1,
        )

        try:
            parsed_result = extract_json_value(result)
            if isinstance(parsed_result, dict):
                return parsed_result
        except (TypeError, ValueError):
            logger.warning("Plagiarism model output was not valid JSON")

        max_score = max([m["score"] for m in significant_matches]) * 100
        return {
            "plagiarism_score": round(max_score, 1),
            "status": "danger" if max_score > 85 else "warning",
            "message_code": "plagiarism_detected",
            "matches": significant_matches[:3],
        }
    except Exception as exc:
        raise _public_ai_error("plagiarism_detection", exc)

@router.post("/hanh-dong")
async def unified_action(
    req: ActionRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """Run one supported editor action against bounded text context"""
    logger.info("Unified action started action={}", req.action)
    try:
        prompts = {
            "autocomplete": registry.get(PromptType.AUTOCOMPLETE).format(
                context=req.context, text=req.text
            ),
            "grammar": registry.get(PromptType.GRAMMAR_CHECK).format(
                text=req.text
            ),
            "summarize": registry.get(PromptType.SUMMARIZE).format(
                language="the input language", text=req.text
            ),
            "ai_suggestions": registry.get(PromptType.AI_SUGGESTIONS).format(
                context=req.context, text=req.text
            ),
            "check_logic": registry.get(PromptType.CHECK_LOGIC).format(
                context=req.context, text=req.text
            ),
        }

        prompt = prompts.get(req.action)
        if not prompt:
            logger.warning(f"Invalid unified action requested {req.action}")
            raise HTTPException(status_code=400, detail={"code": "invalid_action"})

        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3,
        )
        logger.info("Unified action completed action={}", req.action)
        return {"result": result.strip()}
    except Exception as exc:
        raise _public_ai_error("unified_action", exc)

@router.post("/tu-dong-nghia")
async def get_synonyms(
    req: GrammarRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """Generate context aware synonyms for eligible users"""
    logger.info("Synonym retrieval started")
    try:
        if (
            current_user.role != Role.ADMIN
            and current_user.ai_tier.value != Tier.PREMIUM.value
        ):
            logger.warning("Synonym retrieval access denied due to service tier")
            raise HTTPException(
                status_code=403,
                detail={"code": "premium_tier_required"}
            )

        prompt = registry.get(PromptType.SYNONYMS).format(text=req.text)
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.5,
        )
        logger.info("Synonym retrieval completed")
        return {"synonyms": [s.strip() for s in result.split(",")]}
    except Exception as exc:
        raise _public_ai_error("synonym_retrieval", exc)

@router.post("/trich-dan-thong-minh")
async def suggest_citations(
    req: CitationRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """Suggest citations for bounded content and source context"""
    logger.info("Citation suggestion started")
    try:
        if (
            current_user.role != Role.ADMIN
            and current_user.ai_tier.value != Tier.PREMIUM.value
        ):
            logger.warning("Citation suggestion access denied due to service tier")
            raise HTTPException(
                status_code=403,
                detail={"code": "premium_tier_required"}
            )

        from src.rag.embedding import embedder
        from src.store.vector import vector_store

        query_vector = await embedder.embed_query(req.text[:500])
        matches = await vector_store.query(query_vector=query_vector, limit=3)

        sources = []
        for m in matches:
            meta = m.get("metadata", {})
            sources.append(
                f"Document: {meta.get('title', 'N/A')}, Author: {meta.get('author', 'N/A')}. Content: {m['text'][:200]}"
            )

        prompt = registry.get(PromptType.SUGGEST_CITATIONS).format(
            style=req.style, text=req.text, sources="\\n".join(sources)
        )
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3,
        )
        logger.info("Citation suggestion completed")
        return {"citations": result.strip()}
    except Exception as exc:
        raise _public_ai_error("citation_suggestion", exc)

@router.post("/bien-doi-van-ban")
async def transform_tone(
    req: ToneRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """Rewrite bounded content using the requested tone"""
    logger.info("Tone transformation started")
    try:
        if (
            current_user.role != Role.ADMIN
            and current_user.ai_tier.value != Tier.PREMIUM.value
        ):
            logger.warning("Tone transformation access denied due to service tier")
            raise HTTPException(
                status_code=403,
                detail={"code": "premium_tier_required"}
            )

        action = "expand and transform" if req.expansion else "transform"
        prompt = registry.get(PromptType.TRANSFORM_TONE).format(
            action=action.capitalize(), tone=req.tone, text=req.text
        )
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000 if req.expansion else 500,
            temperature=0.4,
        )
        logger.info("Tone transformation completed")
        return {"transformed_text": result.strip()}
    except Exception as exc:
        raise _public_ai_error("tone_transformation", exc)

@router.post("/kiem-duyet-noi-dung")
async def peer_review(
    req: ReviewRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """Review bounded content against the requested criteria"""
    logger.info("Content review started")
    try:
        if (
            current_user.role != Role.ADMIN
            and current_user.ai_tier.value != Tier.PREMIUM.value
        ):
            logger.warning("Content review access denied due to service tier")
            raise HTTPException(
                status_code=403,
                detail={"code": "premium_tier_required"}
            )

        criteria_str = (
            ", ".join(req.criteria)
            if req.criteria
            else "logic, clarity, persuasiveness"
        )
        prompt = registry.get(PromptType.CONTENT_REVIEW).format(
            criteria_str=criteria_str, text=req.text[:3000]
        )
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.2,
        )
        logger.info("Content review completed")
        return {"review_report": result.strip()}
    except Exception as exc:
        raise _public_ai_error("content_review", exc)

@router.post("/tong-hop-tai-lieu")
async def multi_doc_synthesis(
    req: SynthesisRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """Synthesize evidence from an authorized set of indexed documents"""
    logger.info("Multi-document synthesis started document_count={}", len(req.document_ids))
    try:
        from src.rag.embedding import embedder
        from src.store.vector import vector_store

        query_vector = await embedder.embed_query(req.query)

        all_context = []
        for doc_id in req.document_ids:
            matches = await vector_store.query(
                query_vector=query_vector, document_ids=[doc_id], limit=3
            )
            for m in matches:
                all_context.append(f"[From document {doc_id}]: {m['text']}")

        prompt = registry.get(PromptType.MULTI_DOC_SYNTHESIS).format(
            query=req.query, context="\\n".join(all_context[:10])
        )
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.3,
        )
        logger.info("Multi-document synthesis completed")
        return {"synthesis": result.strip(), "sources_count": len(req.document_ids)}
    except Exception as exc:
        raise _public_ai_error("multi_document_synthesis", exc)

@router.post("/trich-xuat-van-ban")
async def extract_text(req: dict, current_user: CurrentUser = Depends(get_current_user)):
    """Extract normalized text from an authorized cloud file"""
    logger.info("Document text extraction started")
    try:
        file_url = req.get("file_url")
        if not file_url:
            logger.warning("Missing file location URL in request")
            raise HTTPException(
                status_code=400, detail={"code": "file_path_required"}
            )

        from src.rag.pipeline import ingestion_pipeline

        extracted_text = await ingestion_pipeline._extract_text(file_url)

        logger.info("Document text extraction completed")
        return {"extracted_text": extracted_text}
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise
        logger.exception("Document text extraction failed")
        raise HTTPException(
            status_code=500,
            detail={"code": "file_text_extraction_failed"},
        )

@router.post("/phan-tich-tai-lieu")
async def analyze_document(
    req: dict, current_user: CurrentUser = Depends(get_current_user)
):
    """Analyze bounded document content and return structured findings"""
    logger.info(f"Started document analysis API request (folder {req.get('folder_str')}) for user_id={current_user.id}")
    try:
        context = req.get("context", "")
        ext = req.get("ext", "txt")
        folder_str = req.get("folder_str", "None")

        prompt = registry.get(PromptType.STORAGE_FILE_ANALYSIS).format(
            ext=ext, folder_str=folder_str, context=context[:3000]
        )

        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.2,
        )

        parsed_result = extract_json_value(result)
        if isinstance(parsed_result, dict):
            logger.info("Document analysis completed")
            return parsed_result
        else:
            logger.warning("LLM returned malformed JSON response during document analysis")
            raise ValueError("Language model returned invalid format")
    except Exception as exc:
        raise _public_ai_error("document_analysis", exc)

@router.delete(
    "/vector/{document_id}",
    dependencies=[Depends(verify_internal_token)],
)
async def delete_vector_document(document_id: str):
    """Delete all indexed vectors for an internal document identifier"""
    logger.info(f"Started vector index deletion for document {document_id}")
    try:
        from src.store.vector import vector_store

        await vector_store.delete_by_document(document_id)
        logger.info(f"Completed vector index deletion for document {document_id}")
        return {"status": "success", "message_code": "document_vectors_deleted"}
    except Exception:
        logger.exception("Vector index deletion error")
        raise HTTPException(status_code=500, detail={"code": "document_vector_deletion_failed"})

def _extract_json(text: str) -> dict:
    try:
        parsed = extract_json_value(text)
        return parsed if isinstance(parsed, dict) else {}
    except (TypeError, ValueError):
        return {}

@router.post("/giai-thich-thuat-ngu")
async def extract_glossary(
    req: GlossaryRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """Extract a structured glossary from bounded source text"""
    logger.info("Glossary extraction started")
    try:
        prompt = registry.get(PromptType.EXTRACT_GLOSSARY).format(text=req.text)
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.3,
        )
        data = _extract_json(result)
        logger.info("Glossary extraction completed")
        return data if data else {"glossary": []}
    except Exception as exc:
        raise _public_ai_error("glossary_extraction", exc)

@router.post("/bat-chuoc-van-phong")
async def imitate_style(
    req: StyleImitationRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """Rewrite bounded text using characteristics of a style sample"""
    logger.info("Style imitation started")
    try:
        prompt = registry.get(PromptType.IMITATE_STYLE).format(reference_text=req.style_sample, text=req.text)
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=min(req.target_length or 2000, 4000),
            temperature=0.5,
        )
        logger.info("Style imitation completed")
        return {"result": result}
    except Exception as exc:
        raise _public_ai_error("style_imitation", exc)

@router.post("/nhap-van-ban-voi-ky-uc")
async def draft_with_memory(
    req: DraftWithMemoryRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """Draft content using the authenticated user memory context"""
    logger.info("Memory-aware drafting started")
    try:
        from src.core.registry import registry, PromptType
        prompt = registry.get(PromptType.DRAFT_WITH_MEMORY).format(prompt=req.prompt)
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.5,
        )
        logger.info("Memory-aware drafting completed")
        return {"draft": result}
    except Exception as exc:
        raise _public_ai_error("draft_with_memory", exc)

@router.post("/trich-xuat-luu-tru")
async def extract_to_storage(
    req: ExtractToStorageRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """Extract structured artifacts according to bounded extraction goals"""
    logger.info("Artifact extraction started")
    try:
        from src.core.registry import registry, PromptType
        prompt = registry.get(PromptType.EXTRACT_TO_ARTIFACTS).format(goals=', '.join(req.extraction_goals), text=req.text[:3000])
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.1,
        )
        data = _extract_json(result)
        logger.info("Artifact extraction completed")
        return {"summary": json.dumps(data, ensure_ascii=False) if data else "{}"}
    except Exception as exc:
        raise _public_ai_error("extract_to_storage", exc)

@router.post("/kiem-chung-su-that")
async def web_fact_check(
    req: WebFactCheckRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """Check bounded claims using the configured web evidence workflow"""
    logger.info("Web fact check started")
    try:
        from src.core.registry import registry, PromptType
        prompt = registry.get(PromptType.WEB_FACT_CHECK).format(text=req.text[:3000])
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.2,
        )
        logger.info("Web fact check completed")
        return {"fact_check_report": result}
    except Exception as exc:
        raise _public_ai_error("web_fact_check", exc)

@router.post("/kiem-duyet-an-toan")
async def compliance_screen(
    req: ComplianceScreenRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """Screen bounded text against configured compliance requirements"""
    logger.info("Compliance screening started")
    try:
        from src.core.registry import registry, PromptType
        prompt = registry.get(PromptType.COMPLIANCE_SCREENER).format(text=req.text[:3000])
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.2,
        )
        logger.info("Compliance screening completed")
        return {"compliance_report": result}
    except Exception as exc:
        raise _public_ai_error("compliance_screen", exc)

@router.post("/so-sanh-ngu-nghia")
async def semantic_diff(
    req: SemanticDiffRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """Compare two bounded texts by meaning and material change"""
    logger.info("Semantic comparison started")
    try:
        from src.core.registry import registry, PromptType
        prompt = registry.get(PromptType.SEMANTIC_DIFF).format(text1=req.text1[:2000], text2=req.text2[:2000])
        result = await _run_ai_with_quota(
            current_user,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.3,
        )
        logger.info("Semantic comparison completed")
        return {"diff_report": result}
    except Exception as exc:
        raise _public_ai_error("semantic_diff", exc)
