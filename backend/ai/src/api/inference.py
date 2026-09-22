import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse

from src.core.dependency import verify_internal_token
from src.schemas.inference import (
    CrossDocumentExpansionRequest,
    KnowledgeChunkSafetyRequest,
    KnowledgeDocumentSummaryRequest,
    RetrievalExpansionRequest,
    TestingAssistanceRequest,
    TestingAssistanceResult,
)
from src.services.inference import (
    decompose_retrieval,
    expand_retrieval,
    inspect_chunks,
    stream_sink,
    summarize_document,
)
from src.services.testing_assistance import generate_testing_assistance

router = APIRouter(prefix="/suy-luan")


@router.post(
    "/noi-bo/mo-rong-truy-van",
    dependencies=[Depends(verify_internal_token)],
    description="Mở rộng truy vấn thành giả thuyết và các truy vấn con phục vụ knowledge",
)
async def expand_retrieval_query(req: RetrievalExpansionRequest):
    return await expand_retrieval(req.question)


@router.post(
    "/noi-bo/phan-ra-lien-tai-lieu",
    dependencies=[Depends(verify_internal_token)],
    description="Phân rã truy vấn theo từng tài liệu đã được chỉ định",
)
async def decompose_cross_document_query(req: CrossDocumentExpansionRequest):
    try:
        queries = await decompose_retrieval(req.question, req.document_ids)
    except ValueError as error:
        raise HTTPException(status_code=502, detail={"code": str(error)}) from error
    return {"queries": queries}


@router.post(
    "/noi-bo/kiem-tra-doan-tri-thuc",
    dependencies=[Depends(verify_internal_token)],
    description="Kiểm tra prompt injection và độ an toàn của các đoạn knowledge",
)
async def inspect_knowledge_chunks(req: KnowledgeChunkSafetyRequest):
    return {"safe_indices": sorted(await inspect_chunks(req.texts))}


@router.post(
    "/noi-bo/tom-tat-tai-lieu-tri-thuc",
    dependencies=[Depends(verify_internal_token)],
    description="Tóm tắt tài liệu knowledge sau khi kiểm tra an toàn",
)
async def summarize_knowledge_document(req: KnowledgeDocumentSummaryRequest):
    try:
        summary = await summarize_document(req.text)
    except ValueError as error:
        raise HTTPException(status_code=422, detail={"code": str(error)}) from error
    return {"summary": summary}


@router.post(
    "/noi-bo/kiem-thu/ho-tro",
    dependencies=[Depends(verify_internal_token)],
    response_model=TestingAssistanceResult,
    description="Sinh đề xuất kiểm thử có bằng chứng và không tự thực hiện quyết định dành cho con người",
)
async def testing_assistance(req: TestingAssistanceRequest):
    return await generate_testing_assistance(req)


@router.post("/noi-bo/kiem-thu/ho-tro/stream", dependencies=[Depends(verify_internal_token)])
async def stream_testing_assistance(req: TestingAssistanceRequest):
    queue = asyncio.Queue()

    async def emit(piece):
        from src.core.security.guardrails import guardrails_engine

        assessment = guardrails_engine.inspect_output(piece)
        if not assessment.get("is_safe", False):
            raise ValueError("AI_STREAM_OUTPUT_UNSAFE")
        safe_piece = str(assessment.get("sanitized_text") or "")
        if safe_piece:
            await queue.put({"type": "delta", "delta": safe_piece})

    async def run():
        token = stream_sink.set(emit)
        try:
            result = await testing_assistance(req)
            await queue.put({"type": "result", "data": jsonable_encoder(result)})
        except Exception as error:
            await queue.put({"type": "error", "code": type(error).__name__})
        finally:
            stream_sink.reset(token)
            await queue.put(None)

    async def events():
        task = asyncio.create_task(run())
        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
