import asyncio

from src.services import retrieval
import pytest

from src.services.retrieval import RetrievalService, RetrievalUnavailableError


def test_rrf_fuses_independent_dense_and_bm25_candidates():
    service = RetrievalService()
    dense = [
        {"id": "dense-only", "text": "dense", "metadata": {}, "score": 0.9},
        {"id": "shared", "text": "shared", "metadata": {}, "score": 0.8},
    ]
    sparse = [
        {"id": "lexical-only", "text": "lexical", "metadata": {}, "score": 3.0},
        {"id": "shared", "text": "shared", "metadata": {}, "score": 2.0},
    ]

    fused = service._rrf_fuse(dense, sparse)

    assert fused[0]["id"] == "shared"
    assert {item["id"] for item in fused} == {
        "dense-only",
        "lexical-only",
        "shared",
    }
    assert fused[0]["retrieval_sources"] == ["dense", "bm25"]


def test_retrieve_calls_bm25_as_an_independent_candidate_source(monkeypatch):
    service = RetrievalService()
    service._reranker = False

    async def fake_embed_query(_query):
        return [1.0, 0.0]

    async def fake_dense_query(**_kwargs):
        return [
            {"id": "dense-only", "text": "dense", "metadata": {}, "score": 0.9}
        ]

    async def fake_bm25_search(**_kwargs):
        return [
            {
                "id": "lexical-only",
                "text": "exact keyword",
                "metadata": {},
                "score": 4.0,
                "bm25_score": 4.0,
            }
        ]

    monkeypatch.setattr(retrieval.embedder, "embed_query", fake_embed_query)
    monkeypatch.setattr(retrieval.vector_store, "query", fake_dense_query)
    monkeypatch.setattr(retrieval.bm25_store, "search", fake_bm25_search)

    results = asyncio.run(service.retrieve("exact keyword", k=2))

    assert {item["id"] for item in results} == {"dense-only", "lexical-only"}
    lexical = next(item for item in results if item["id"] == "lexical-only")
    assert lexical["retrieval_sources"] == ["bm25"]


def test_retrieve_keeps_bm25_when_query_embedding_fails(monkeypatch):
    service = RetrievalService()
    service._reranker = False

    async def failed_embedding(_query):
        raise RuntimeError("embedding unavailable")

    async def fake_bm25_search(**_kwargs):
        return [
            {
                "id": "lexical-only",
                "text": "exact keyword",
                "metadata": {},
                "score": 4.0,
                "bm25_score": 4.0,
            }
        ]

    monkeypatch.setattr(retrieval.embedder, "embed_query", failed_embedding)
    monkeypatch.setattr(retrieval.bm25_store, "search", fake_bm25_search)

    results = asyncio.run(service.retrieve("exact keyword", k=1))

    assert [item["id"] for item in results] == ["lexical-only"]
    assert results[0]["retrieval_sources"] == ["bm25"]


def test_retrieve_fails_explicitly_when_dense_and_sparse_are_unavailable(monkeypatch):
    service = RetrievalService()
    service._reranker = False

    async def failed(*_args, **_kwargs):
        raise RuntimeError("unavailable")

    monkeypatch.setattr(retrieval.embedder, "embed_query", failed)
    monkeypatch.setattr(retrieval.bm25_store, "search", failed)

    with pytest.raises(RetrievalUnavailableError):
        asyncio.run(service.retrieve("curriculum evidence", k=1))
