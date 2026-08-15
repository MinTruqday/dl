import asyncio

from src.store.bm25 import BM25Store


def test_bm25_searches_full_corpus_and_enforces_access():
    store = BM25Store()
    asyncio.run(
        store.initialize(
            [
                {
                    "id": "dense-candidate",
                    "text": "khái niệm tổng quát về thư viện",
                    "metadata": {
                        "document_id": "doc-1",
                        "visibility": "public",
                        "creator_id": "owner-1",
                    },
                },
                {
                    "id": "lexical-only",
                    "text": "thuật-ngữ-hiếm zephyrlibrary xuất hiện chính xác",
                    "metadata": {
                        "document_id": "doc-2",
                        "visibility": "public",
                        "creator_id": "owner-2",
                    },
                },
                {
                    "id": "private",
                    "text": "zephyrlibrary bí mật",
                    "metadata": {
                        "document_id": "doc-3",
                        "visibility": "private",
                        "creator_id": "owner-3",
                    },
                },
            ]
        )
    )

    public_results = asyncio.run(store.search("zephyrlibrary", requester_id="owner-1"))
    owner_results = asyncio.run(store.search("zephyrlibrary", requester_id="owner-3"))

    assert [item["id"] for item in public_results] == ["lexical-only"]
    assert {item["id"] for item in owner_results} == {"lexical-only", "private"}


def test_bm25_updates_and_deletes_a_whole_document():
    store = BM25Store()
    asyncio.run(store.initialize([]))
    asyncio.run(
        store.upsert(
            [
                {
                    "id": "chunk-1",
                    "text": "nội dung đồng bộ",
                    "metadata": {
                        "document_id": "doc-sync",
                        "visibility": "public",
                    },
                }
            ]
        )
    )
    assert asyncio.run(store.search("đồng bộ"))

    asyncio.run(store.delete_by_document("doc-sync"))
    assert asyncio.run(store.search("đồng bộ")) == []
