import asyncio

from src.services import chunking


def test_semantic_refinement_uses_docling_structure(monkeypatch):
    paragraphs = [
        ("Tài liệu và thư viện số " * 12).strip(),
        ("Tìm kiếm tài liệu học thuật " * 12).strip(),
        ("Công thức nấu ăn gia đình " * 12).strip(),
    ]
    structure = [
        {"text": text, "type": "text", "level": 1} for text in paragraphs
    ]

    async def fake_embed_batch(texts):
        assert texts == paragraphs
        return [[1.0, 0.0], [0.99, 0.01], [-1.0, 0.0]]

    monkeypatch.setattr(chunking.embedder, "embed_batch", fake_embed_batch)
    service = chunking.ChunkingService(max_chars=1000)
    chunks = asyncio.run(
        service.chunk_document(
            "ignored Markdown fallback",
            {"document_id": "doc-1"},
            structure=structure,
        )
    )

    assert len(chunks) == 2
    assert paragraphs[0] in chunks[0]["text"]
    assert paragraphs[1] in chunks[0]["text"]
    assert chunks[1]["text"] == paragraphs[2]
    assert all(
        item["metadata"]["chunk_type"] == "docling_structure_semantic"
        for item in chunks
    )


def test_size_guard_runs_after_semantic_refinement(monkeypatch):
    async def same_topic(texts):
        return [[1.0, 0.0] for _ in texts]

    monkeypatch.setattr(chunking.embedder, "embed_batch", same_topic)
    service = chunking.ChunkingService(
        min_chars=50,
        target_chars=120,
        max_chars=180,
    )
    long_text = "Một câu nội dung có cùng chủ đề. " * 30
    chunks = asyncio.run(
        service.chunk_document(long_text, {"document_id": "doc-size"})
    )

    assert len(chunks) > 1
    assert all(len(item["text"]) <= 180 for item in chunks)


def test_semantic_failure_preserves_structure_then_applies_size_guard(monkeypatch):
    async def unavailable_embedding(_texts):
        raise RuntimeError("embedding unavailable")

    monkeypatch.setattr(chunking.embedder, "embed_batch", unavailable_embedding)
    service = chunking.ChunkingService(target_chars=300, max_chars=500)
    text = "Đoạn văn kiểm thử fallback " * 40
    chunks = asyncio.run(service.chunk_document(text, {"document_id": "doc-2"}))

    assert chunks
    assert all(
        item["metadata"]["chunk_type"] == "docling_structure_fallback"
        for item in chunks
    )
    assert all(len(item["text"]) <= 500 for item in chunks)
