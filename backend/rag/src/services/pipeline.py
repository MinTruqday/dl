import asyncio
from hashlib import sha256
from typing import Dict
from uuid import NAMESPACE_URL, uuid5
from loguru import logger
from src.store.vector import vector_store
from src.store.bm25 import bm25_store
from src.services.embedding import embedder
from src.services.chunking import chunker
from src.services.conversion import document_parser
from src.clients.content import content_client
from src.clients.agentic import agentic_client
from src.services.security import prompt_injection_flags


async def embed_available_chunks(chunks):
    texts = [chunk["text"] for chunk in chunks]
    try:
        vectors = await embedder.embed_batch(texts)
        if len(vectors) != len(chunks) or any(not isinstance(vector, list) or not vector for vector in vectors):
            raise ValueError("embedding_batch_shape_invalid")
        return chunks, vectors, []
    except Exception:
        available_chunks = []
        vectors = []
        failed_chunks = []
        for chunk in chunks:
            try:
                vector = await embedder.embed_query(chunk["text"])
                if not isinstance(vector, list) or not vector:
                    raise ValueError("embedding_shape_invalid")
                available_chunks.append(chunk)
                vectors.append(vector)
            except Exception as error:
                failed_chunks.append(
                    {
                        "chunk_id": chunk.get("metadata", {}).get("chunk_id") or chunk.get("id"),
                        "stage": "embedding",
                        "error_code": type(error).__name__,
                    }
                )
        if not available_chunks:
            raise RuntimeError("No chunks could be embedded")
        return available_chunks, vectors, failed_chunks


class IngestionPipelineService:
    async def ingest_document(
        self,
        document_id: str,
        requester_id: str,
        is_admin: bool = False,
    ) -> Dict:
        logger.info(f"Starting ingestion for document {document_id}")
        doc = await content_client.authorize_document(
            document_id,
            requester_id,
            is_admin,
        )
        
        file_url = doc.get("file_url", "") if doc else ""
        title = doc.get("title") or ""
        author = doc.get("author") or doc.get("author_name") or ""
        visibility = doc.get("visibility") or "private"
        content_format = doc.get("content_format") or ""
        content_source = doc.get("source") or doc.get("content_source") or doc.get("source_name") or "user_upload"
        education_metadata = doc.get("education_metadata") or {}
        def education_value(key: str, default=None):
            value = education_metadata.get(key)
            return doc.get(key, default) if value is None else value
        source_type = doc.get("source_type") or education_metadata.get("source_type") or "teacher_material"
        authority = doc.get("authority") or education_metadata.get("authority") or "supplementary"
        owner_id = str(doc.get("owner_id") or doc.get("creator_id") or "")

        if not file_url:
            raise ValueError(f"Document {document_id} not found or missing file_url")

        metadata = {
            "document_id": document_id,
            "title": title,
            "author": author,
            "content_format": content_format,
            "source": content_source,
            "visibility": visibility,
            "creator_id": str(doc.get("creator_id") or ""),
            "owner_id": owner_id,
            "file_url": file_url,
            "source_url": doc.get("source_url"),
            "source_name": doc.get("source_name"),
            "source_type": source_type,
            "authority": authority,
            "publisher": doc.get("publisher") or doc.get("publisher_name"),
            "book_title": doc.get("book_title") or title,
            "collector_version": doc.get("collector_version"),
            "education_level": education_value("education_level"),
            "subject": education_value("subject"),
            "target_program": education_value("target_program"),
            "chapter_id": education_value("chapter_id"),
            "lesson_id": education_value("lesson_id"),
            "section_id": education_value("section_id"),
            "concept_ids": education_value("concept_ids", []),
            "skill_ids": education_value("skill_ids", []),
            "learning_objective_ids": education_value("learning_objective_ids", []),
            "content_type": education_value("content_type"),
            "source_version": education_value("source_version") or doc.get("version"),
            "mapping_confidence": education_value("mapping_confidence"),
            "mapping_status": education_value("mapping_status"),
            "conflict_key": education_value("conflict_key"),
            "claim_value": education_value("claim_value"),
        }

        parse_result = await document_parser.parse_document(
            file_url,
            visibility=visibility,
        )
        if parse_result.get("error"):
            raise ValueError("Failed to convert document with Docling")
        raw_markdown = parse_result.get("markdown", "")
        document_structure = parse_result.get("structure", [])

        if not raw_markdown:
            raise ValueError("Failed to extract document text")
        extraction_method = "docling_structure_semantic"
        chunks = await chunker.chunk_document(
            raw_markdown,
            {**metadata, "extraction_method": extraction_method},
            structure=document_structure,
        )
        quarantined_chunks = []
        if chunks:
            locally_safe = []
            for chunk in chunks:
                flags = prompt_injection_flags(chunk["text"])
                if flags:
                    quarantined_chunks.append({"chunk_id": chunk["metadata"].get("chunk_id"), "flags": flags})
                else:
                    locally_safe.append(chunk)
            chunks = locally_safe

        if chunks:
            safe_indices = await agentic_client.inspect_rag_chunks(
                [chunk["text"] for chunk in chunks]
            )
            rejected = [chunk for index, chunk in enumerate(chunks) if index not in safe_indices]
            quarantined_chunks.extend(
                {"chunk_id": chunk["metadata"].get("chunk_id"), "flags": ["agentic_safety_rejection"]}
                for chunk in rejected
            )
            chunks = [
                chunk for index, chunk in enumerate(chunks) if index in safe_indices
            ]

        first_pages = "\n".join(chunk["text"] for chunk in chunks)[:15000]

        if len(first_pages) < 500:
            summary = first_pages.strip()
        else:
            try:
                summary = await agentic_client.summarize_rag_document(first_pages)
            except Exception:
                logger.exception("Document summary generation error")
                summary = ""
        if summary:
            summary_point_id = str(
                uuid5(
                    NAMESPACE_URL,
                    ":".join(
                        [
                            document_id,
                            str(metadata.get("source_version") or ""),
                            "summary",
                            sha256(summary.encode()).hexdigest(),
                        ]
                    ),
                )
            )
            chunks.insert(
                0,
                {
                    "id": summary_point_id,
                    "text": (
                        f"[GLOBAL METADATA - SUMMARY CHUNK]\n"
                        f"Document: {title}\n"
                        f"Author: {author}\n"
                        f"{summary}"
                    ),
                    "metadata": {
                        **metadata,
                        "chunk_id": "summary_001",
                        "chunk_type": "summary",
                        "chunk_index": -1,
                        "extraction_method": f"{extraction_method}_llm",
                    },
                },
            )

        if not chunks:
            raise ValueError("No chunks extracted from document")

        chunks, embeddings, failed_chunks = await embed_available_chunks(chunks)
        texts = [c["text"] for c in chunks]
        ids = [c["id"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        previous_vector_ids, previous_bm25_ids = await asyncio.gather(
            vector_store.ids_by_document(document_id),
            bm25_store.ids_by_document(document_id),
        )

        await vector_store.upsert(
            ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas
        )
        await vector_store.wait_upsert()
        await bm25_store.upsert(chunks)
        current_ids = set(ids)
        await asyncio.gather(
            vector_store.delete_ids([point_id for point_id in previous_vector_ids if point_id not in current_ids]),
            bm25_store.delete_ids([point_id for point_id in previous_bm25_ids if point_id not in current_ids]),
        )

        index_report = {
            "failed_chunks": failed_chunks,
            "quarantined_chunks": quarantined_chunks,
        }
        await content_client.mark_indexed(
            document_id,
            len(chunks),
            index_report,
            raw_markdown,
            extraction_method,
        )

        return {
            "document_id": document_id,
            "title": title,
            "chunks_count": len(chunks),
            "extraction_method": extraction_method,
            "status": "indexed",
            "quarantined_chunks": quarantined_chunks,
            "failed_chunks": failed_chunks,
        }

ingestion_pipeline = IngestionPipelineService()
