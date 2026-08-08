import os
import tempfile
import asyncio
from typing import Dict, List, Optional
from uuid6 import uuid7
from loguru import logger
from src.core.infrastructure.configuration import settings
from src.store.vector import vector_store
from src.services.embedding import embedder
from src.services.chunking import chunker
from src.services.conversion import document_parser
from src.services.ast_indexer import ASTIndexer
from src.core.infrastructure.mongo import mongo

class IngestionPipelineService:
    async def ingest_document(self, document_id: str) -> Dict:
        logger.info(f"Starting ingestion for document {document_id}")
        doc = await mongo.find_one("documents", {"_id": document_id}, db_name=settings.CONTENT_DB_NAME)
        if not doc:
            doc = await mongo.find_one("documents", {"id": document_id}, db_name=settings.CONTENT_DB_NAME)
        
        file_url = doc.get("file_url", "") if doc else ""
        title = doc.get("title", "Untitled") if doc else "Untitled"
        author = doc.get("author", "Unknown") if doc else "Unknown"
        visibility = doc.get("visibility", "public") if doc else "public"
        content_format = doc.get("content_format", "unknown") if doc else "unknown"

        if not file_url:
            raise ValueError(f"Document {document_id} not found or missing file_url")

        metadata = {
            "document_id": document_id,
            "title": title,
            "author": author,
            "content_format": content_format,
            "visibility": visibility,
            "file_url": file_url,
        }

        chunks = []
        doc_chunks = await document_parser.get_doc_chunks_for_ingestion(file_url, visibility=visibility)

        await vector_store.delete_by_document(document_id)

        if doc_chunks:
            extraction_method = "ade"
            for i, ac in enumerate(doc_chunks):
                chunk_text = ac.get("text", "").strip()
                if len(chunk_text) < 30:
                    continue
                chunk_id = str(uuid7())[:12]
                chunk_meta = {
                    **metadata,
                    "chunk_id": chunk_id,
                    "chunk_type": ac.get("chunk_type", "text"),
                    "chunk_index": i,
                    "extraction_method": "ade",
                }
                chunks.append({
                    "id": f"{document_id}_{chunk_id}",
                    "text": chunk_text,
                    "metadata": chunk_meta,
                })
        else:
            extraction_method = "local"
            raw_text = await document_parser.get_markdown(file_url)
            if not raw_text:
                raise ValueError("Failed to extract document text")
            extracted_chunks = await chunker.chunk_document(raw_text, metadata)
            chunks.extend(extracted_chunks)

        if not chunks:
            raise ValueError("No chunks extracted from document")

        texts = [c["text"] for c in chunks]
        embeddings = await embedder.embed_batch(texts)
        ids = [c["id"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        await vector_store.upsert(
            ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas
        )
        await vector_store.wait_upsert()

        await mongo.update_one(
            "documents",
            {"_id": document_id},
            {"$set": {"chunks_count": len(chunks), "is_indexed": True}},
            db_name=settings.CONTENT_DB_NAME
        )

        return {
            "document_id": document_id,
            "title": title,
            "chunks_count": len(chunks),
            "extraction_method": extraction_method,
            "status": "indexed",
        }

ingestion_pipeline = IngestionPipelineService()
