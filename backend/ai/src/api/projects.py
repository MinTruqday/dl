import hashlib
import time
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from fastapi import APIRouter, Depends, HTTPException

from src.core.dependency import verify_internal_token
from src.schemas.project import ProjectArtifactIndexRequest, ProjectKnowledgeSearchRequest
from src.services.embedding import embedder
from src.services.chunking import chunker
from src.services.retrieval import RetrievalUnavailableError, retriever
from src.store.vector import vector_store
from src.store.bm25 import bm25_store


router = APIRouter(dependencies=[Depends(verify_internal_token)])

_SEARCH_CACHE: dict[tuple, tuple[float, dict]] = {}
_SEARCH_CACHE_TTL_SECONDS = 30
_SEARCH_CACHE_MAX_SIZE = 512


def project_artifact_metadata(project_id: str, req: ProjectArtifactIndexRequest):
    return {
        **req.metadata,
        "project_id": project_id,
        "artifact_type": req.artifact_type,
        "artifact_id": req.artifact_id,
        "artifact_version_id": req.artifact_version_id,
        "title": req.title,
        "status": req.status,
        "authority": req.authority,
        "version": req.version,
        "module": req.module,
        "visibility": "project",
        "requirement_ids": req.metadata.get("requirement_ids", [req.artifact_id] if req.artifact_type == "requirement_version" else []),
        "source_document_id": req.metadata.get("source_document_id"),
        "page": req.metadata.get("page"),
        "section": req.metadata.get("section") or req.title,
        "owner_id": req.metadata.get("owner_id"),
        "source_hash": req.metadata.get("source_hash") or hashlib.sha256(req.text.encode("utf-8")).hexdigest(),
        "indexed_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/du-an/{project_id}/doi-tuong", description="Chỉ mục hóa artifact trong phạm vi Project")
async def index_project_artifact(project_id: str, req: ProjectArtifactIndexRequest):
    metadata = project_artifact_metadata(project_id, req)
    chunks = await chunker.chunk_document(req.text[:50000], metadata)
    documents = [chunk["text"] for chunk in chunks]
    vectors = await embedder.embed_batch([f"{req.title} {text}" for text in documents])
    ids = [str(uuid5(NAMESPACE_URL, f"{project_id}:{req.artifact_version_id}:{index}")) for index in range(len(chunks))]
    metadatas = [{**metadata, **chunk.get("metadata", {}), "chunk_index": index} for index, chunk in enumerate(chunks)]
    old_ids = await vector_store.ids_by_artifact_version(project_id, req.artifact_version_id)
    await vector_store.delete_ids(old_ids)
    await bm25_store.delete_ids(old_ids)
    await vector_store.upsert(ids, vectors, documents, metadatas)
    await bm25_store.upsert([{"id": point_id, "text": text, "metadata": item_metadata} for point_id, text, item_metadata in zip(ids, documents, metadatas)])
    for key in tuple(_SEARCH_CACHE):
        if key[0] == project_id:
            _SEARCH_CACHE.pop(key, None)
    return {"status": "indexed", "project_id": project_id, "artifact_version_id": req.artifact_version_id, "chunks_count": len(chunks)}


@router.post("/du-an/{project_id}/tim-kiem", description="Tìm evidence knowledge theo phạm vi Project")
async def search_project_knowledge(project_id: str, req: ProjectKnowledgeSearchRequest):
    cache_key = (project_id, req.query, tuple(sorted(req.artifact_types or [])), req.limit)
    cached = _SEARCH_CACHE.get(cache_key)
    if cached and time.monotonic() - cached[0] < _SEARCH_CACHE_TTL_SECONDS:
        return cached[1]
    if cached:
        _SEARCH_CACHE.pop(cache_key, None)
    filters = {"project_id": project_id}
    if req.artifact_types:
        filters["artifact_type"] = req.artifact_types
    try:
        documents = await retriever.retrieve(
            query=req.query,
            k=req.limit,
            requester_id=None,
            is_admin=True,
            metadata_filters=filters,
        )
    except RetrievalUnavailableError as error:
        raise HTTPException(status_code=503, detail={"code": "KNOWLEDGE_UNAVAILABLE"}) from error
    items = [
        {
            **document.get("metadata", {}),
            "text": document.get("text", ""),
            "score": document.get("score", 0),
            "retrieval_source": "knowledge",
        }
        for document in documents
    ]
    result = {"items": items, "degraded_mode": "NORMAL", "error_code": None}
    if len(_SEARCH_CACHE) >= _SEARCH_CACHE_MAX_SIZE:
        oldest_key = min(_SEARCH_CACHE, key=lambda key: _SEARCH_CACHE[key][0])
        _SEARCH_CACHE.pop(oldest_key, None)
    _SEARCH_CACHE[cache_key] = (time.monotonic(), result)
    return result
