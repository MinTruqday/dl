from datetime import datetime, timezone
import hashlib
import hmac
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from src.core.response import APIResponse
from src.core.dependency import CurrentUser, get_current_user_optional, verify_internal_token
from src.schemas.retrieval import (
    RetrieveRequest,
    MultiQueryRetrieveRequest,
    CrossDocRetrieveRequest,
    RetrieveResponse,
    RetrievedDocument,
    CitationItem,
)
from src.services.retrieval import RetrievalUnavailableError, retriever
from src.core.metrics import metrics_collector
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

router = APIRouter(
    dependencies=[Depends(verify_internal_token)],
)


async def record_material_access(operation, query, requester_id, is_admin, source_type, docs):
    material_docs = [
        doc
        for doc in docs
        if (doc.get("metadata") or {}).get("source_type") == "teacher_material"
    ]
    if source_type != "teacher_material" and not material_docs:
        return
    document_ids = sorted(
        {
            str((doc.get("metadata") or {}).get("document_id"))
            for doc in material_docs
            if (doc.get("metadata") or {}).get("document_id")
        }
    )
    await database.mongodb.retrieval_audit.insert_one(
        {
            "_id": f"RAG-AUD-{uuid4().hex}",
            "operation": operation,
            "requester_id": requester_id or "unknown",
            "is_admin": bool(is_admin),
            "source_type": "teacher_material",
            "document_ids": document_ids,
            "chunk_count": len(material_docs),
            "query_sha256": hmac.new(
                settings.SECRET_KEY.encode("utf-8"),
                query.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest(),
            "created_at": datetime.now(timezone.utc),
        }
    )


@router.get("/audit/material-access")
async def list_material_access_audit(
    requester_id: str | None = None,
    document_id: str | None = None,
    limit: int = Query(default=500, ge=1, le=5000),
):
    query = {"source_type": "teacher_material"}
    if requester_id:
        query["requester_id"] = requester_id
    if document_id:
        query["document_ids"] = document_id
    return await database.mongodb.retrieval_audit.find(query).sort("created_at", -1).limit(limit).to_list(limit)

@router.post("/retrieve", response_model=APIResponse[RetrieveResponse])
async def retrieve_documents(
    req: RetrieveRequest,
    user: CurrentUser = Depends(get_current_user_optional),
):
    requester_id = str(user.id) if user else req.requester_id
    is_admin = user.is_admin() if user else req.is_admin
    try:
        docs = await retriever.retrieve(
            query=req.query,
            document_ids=req.document_ids,
            k=req.k,
            query_vector_override=req.query_vector_override,
            requester_id=requester_id,
            is_admin=is_admin,
            metadata_filters=req.metadata_filters.model_dump(exclude_none=True),
        )
    except RetrievalUnavailableError as error:
        raise HTTPException(status_code=503, detail={"code": str(error)}) from error
    await record_material_access(
        "retrieve",
        req.query,
        requester_id,
        is_admin,
        req.metadata_filters.source_type,
        docs,
    )
    metrics_collector.record_curriculum_retrieval(docs, req.metadata_filters.source_type)
    citations_data = retriever.get_citations(docs)
    retrieved_docs = [
        RetrievedDocument(
            text=d.get("text", ""),
            metadata=d.get("metadata", {}),
            score=float(d.get("score", 0.0)),
        )
        for d in docs
    ]
    citations = [
        CitationItem(
            chunk_id=c.get("chunk_id", ""),
            document_id=c.get("document_id", ""),
            title=c.get("title", ""),
            chunk_index=c.get("chunk_index", ""),
            label=c.get("label", ""),
        )
        for c in citations_data
    ]
    return APIResponse(
        data=RetrieveResponse(documents=retrieved_docs, citations=citations, conflicts=retriever.detect_source_conflicts(docs)),
        message="Truy xuất tài liệu thành công",
    )

@router.post("/multi-query-retrieve", response_model=APIResponse[RetrieveResponse])
async def multi_query_retrieve(
    req: MultiQueryRetrieveRequest,
    user: CurrentUser = Depends(get_current_user_optional),
):
    requester_id = str(user.id) if user else req.requester_id
    is_admin = user.is_admin() if user else req.is_admin
    try:
        docs = await retriever.multi_query_retrieve(
            question=req.question,
            document_ids=req.document_ids,
            k=req.k,
            requester_id=requester_id,
            is_admin=is_admin,
            metadata_filters=req.metadata_filters.model_dump(exclude_none=True),
        )
    except RetrievalUnavailableError as error:
        raise HTTPException(status_code=503, detail={"code": str(error)}) from error
    await record_material_access(
        "multi_query_retrieve",
        req.question,
        requester_id,
        is_admin,
        req.metadata_filters.source_type,
        docs,
    )
    metrics_collector.record_curriculum_retrieval(docs, req.metadata_filters.source_type)
    citations_data = retriever.get_citations(docs)
    retrieved_docs = [
        RetrievedDocument(
            text=d.get("text", ""),
            metadata=d.get("metadata", {}),
            score=float(d.get("score", 0.0)),
        )
        for d in docs
    ]
    citations = [
        CitationItem(
            chunk_id=c.get("chunk_id", ""),
            document_id=c.get("document_id", ""),
            title=c.get("title", ""),
            chunk_index=c.get("chunk_index", ""),
            label=c.get("label", ""),
        )
        for c in citations_data
    ]
    return APIResponse(
        data=RetrieveResponse(documents=retrieved_docs, citations=citations, conflicts=retriever.detect_source_conflicts(docs)),
        message="Truy xuất đa chiều thành công",
    )

@router.post("/cross-document-retrieve", response_model=APIResponse[RetrieveResponse])
async def cross_document_retrieve(
    req: CrossDocRetrieveRequest,
    user: CurrentUser = Depends(get_current_user_optional),
):
    requester_id = str(user.id) if user else req.requester_id
    is_admin = user.is_admin() if user else req.is_admin
    try:
        docs = await retriever.cross_document_retrieve(
            question=req.question,
            document_ids=req.document_ids,
            k=req.k,
            requester_id=requester_id,
            is_admin=is_admin,
            metadata_filters=req.metadata_filters.model_dump(exclude_none=True),
        )
    except RetrievalUnavailableError as error:
        raise HTTPException(status_code=503, detail={"code": str(error)}) from error
    await record_material_access(
        "cross_document_retrieve",
        req.question,
        requester_id,
        is_admin,
        req.metadata_filters.source_type,
        docs,
    )
    metrics_collector.record_curriculum_retrieval(docs, req.metadata_filters.source_type)
    citations_data = retriever.get_citations(docs)
    retrieved_docs = [
        RetrievedDocument(
            text=d.get("text", ""),
            metadata=d.get("metadata", {}),
            score=float(d.get("score", 0.0)),
        )
        for d in docs
    ]
    citations = [
        CitationItem(
            chunk_id=c.get("chunk_id", ""),
            document_id=c.get("document_id", ""),
            title=c.get("title", ""),
            chunk_index=c.get("chunk_index", ""),
            label=c.get("label", ""),
        )
        for c in citations_data
    ]
    return APIResponse(
        data=RetrieveResponse(documents=retrieved_docs, citations=citations, conflicts=retriever.detect_source_conflicts(docs)),
        message="Truy xuất liên tài liệu thành công",
    )
