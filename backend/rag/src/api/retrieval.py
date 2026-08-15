from fastapi import APIRouter, Depends
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
from src.services.retrieval import retriever

router = APIRouter(
    dependencies=[Depends(verify_internal_token)],
)

@router.post("/retrieve", response_model=APIResponse[RetrieveResponse])
async def retrieve_documents(
    req: RetrieveRequest,
    user: CurrentUser = Depends(get_current_user_optional),
):
    docs = await retriever.retrieve(
        query=req.query,
        document_ids=req.document_ids,
        k=req.k,
        query_vector_override=req.query_vector_override,
        requester_id=str(user.id) if user else req.requester_id,
        is_admin=user.is_admin() if user else req.is_admin,
    )
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
        data=RetrieveResponse(documents=retrieved_docs, citations=citations),
        message="Truy xuất tài liệu thành công",
    )

@router.post("/multi-query-retrieve", response_model=APIResponse[RetrieveResponse])
async def multi_query_retrieve(
    req: MultiQueryRetrieveRequest,
    user: CurrentUser = Depends(get_current_user_optional),
):
    docs = await retriever.multi_query_retrieve(
        question=req.question,
        document_ids=req.document_ids,
        k=req.k,
        requester_id=str(user.id) if user else req.requester_id,
        is_admin=user.is_admin() if user else req.is_admin,
    )
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
        data=RetrieveResponse(documents=retrieved_docs, citations=citations),
        message="Truy xuất đa chiều thành công",
    )

@router.post("/cross-document-retrieve", response_model=APIResponse[RetrieveResponse])
async def cross_document_retrieve(
    req: CrossDocRetrieveRequest,
    user: CurrentUser = Depends(get_current_user_optional),
):
    docs = await retriever.cross_document_retrieve(
        question=req.question,
        document_ids=req.document_ids,
        k=req.k,
        requester_id=str(user.id) if user else req.requester_id,
        is_admin=user.is_admin() if user else req.is_admin,
    )
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
        data=RetrieveResponse(documents=retrieved_docs, citations=citations),
        message="Truy xuất liên tài liệu thành công",
    )
