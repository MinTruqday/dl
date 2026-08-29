from datetime import datetime, timezone
import hashlib
import hmac
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from src.schemas.response import APIResponse
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
from src.core.infrastructure.mongo import mongo
from src.core.infrastructure.configuration import settings

router = APIRouter(dependencies=[Depends(verify_internal_token)])


async def record_retrieval_access(operation, query, requester_id, is_admin, docs):
    document_ids = sorted(
        {
            str((doc.get("metadata") or {}).get("document_id"))
            for doc in docs
            if (doc.get("metadata") or {}).get("document_id")
        }
    )
    await mongo.get_db().retrieval_audit.insert_one(
        {
            "_id": f"KNOWLEDGE-AUD-{uuid4().hex}",
            "operation": operation,
            "requester_id": requester_id or "unknown",
            "is_admin": bool(is_admin),
            "project_ids": sorted(
                {
                    str((doc.get("metadata") or {}).get("project_id"))
                    for doc in docs
                    if (doc.get("metadata") or {}).get("project_id")
                }
            ),
            "document_ids": document_ids,
            "chunk_count": len(docs),
            "query_sha256": hmac.new(
                settings.SECRET_KEY.encode("utf-8"), query.encode("utf-8"), hashlib.sha256
            ).hexdigest(),
            "created_at": datetime.now(timezone.utc),
        }
    )


@router.get("/audit/retrieval-access", description="Truy vấn audit access của knowledge retrieval")
async def list_retrieval_access_audit(
    requester_id: str | None = None,
    project_id: str | None = None,
    document_id: str | None = None,
    limit: int = Query(default=500, ge=1, le=5000),
):
    query = {}
    if requester_id:
        query["requester_id"] = requester_id
    if project_id:
        query["project_ids"] = project_id
    if document_id:
        query["document_ids"] = document_id
    return (
        await mongo.get_db().retrieval_audit.find(query)
        .sort("created_at", -1)
        .limit(limit)
        .to_list(limit)
    )


@router.post("/retrieve", response_model=APIResponse[RetrieveResponse], description="Truy xuất knowledge bằng dense sparse fusion và rerank")
async def retrieve_documents(
    req: RetrieveRequest, user: CurrentUser = Depends(get_current_user_optional)
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
    await record_retrieval_access("retrieve", req.query, requester_id, is_admin, docs)
    metrics_collector.record_artifact_retrieval(docs, req.metadata_filters.artifact_type)
    citations_data = retriever.get_citations(docs)
    retrieved_docs = [
        RetrievedDocument(
            text=d.get("text", ""), metadata=d.get("metadata", {}), score=float(d.get("score", 0.0))
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
        data=RetrieveResponse(
            documents=retrieved_docs,
            citations=citations,
            conflicts=retriever.detect_source_conflicts(docs),
        ),
        message="Truy xuất tài liệu thành công",
    )


@router.post("/multi-query-retrieve", response_model=APIResponse[RetrieveResponse], description="Truy xuất knowledge bằng mở rộng truy vấn")
async def multi_query_retrieve(
    req: MultiQueryRetrieveRequest, user: CurrentUser = Depends(get_current_user_optional)
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
    await record_retrieval_access("multi_query_retrieve", req.question, requester_id, is_admin, docs)
    metrics_collector.record_artifact_retrieval(docs, req.metadata_filters.artifact_type)
    citations_data = retriever.get_citations(docs)
    retrieved_docs = [
        RetrievedDocument(
            text=d.get("text", ""), metadata=d.get("metadata", {}), score=float(d.get("score", 0.0))
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
        data=RetrieveResponse(
            documents=retrieved_docs,
            citations=citations,
            conflicts=retriever.detect_source_conflicts(docs),
        ),
        message="Truy xuất đa chiều thành công",
    )


@router.post("/cross-document-retrieve", response_model=APIResponse[RetrieveResponse], description="Truy xuất knowledge liên tài liệu")
async def cross_document_retrieve(
    req: CrossDocRetrieveRequest, user: CurrentUser = Depends(get_current_user_optional)
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
    await record_retrieval_access(
        "cross_document_retrieve", req.question, requester_id, is_admin, docs
    )
    metrics_collector.record_artifact_retrieval(docs, req.metadata_filters.artifact_type)
    citations_data = retriever.get_citations(docs)
    retrieved_docs = [
        RetrievedDocument(
            text=d.get("text", ""), metadata=d.get("metadata", {}), score=float(d.get("score", 0.0))
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
        data=RetrieveResponse(
            documents=retrieved_docs,
            citations=citations,
            conflicts=retriever.detect_source_conflicts(docs),
        ),
        message="Truy xuất liên tài liệu thành công",
    )
