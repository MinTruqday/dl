import os
import tempfile
import asyncio
from typing import Dict, List, Optional
from uuid6 import uuid7
from loguru import logger
from src.store.vector import vector_store
from src.services.embedding import embedder
from src.services.chunking import chunker
from src.services.conversion import document_parser
from src.services.ast_indexer import ASTIndexer
from src.services.content_client import content_client
from src.services.agentic_client import agentic_client

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
        author = doc.get("author") or ""
        visibility = doc.get("visibility") or "private"
        content_format = doc.get("content_format") or ""
        content_source = doc.get("source") or doc.get("content_source") or "user_upload"

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
            "file_url": file_url,
        }

        chunks = []
        doc_chunks = await document_parser.get_doc_chunks_for_ingestion(file_url, visibility=visibility)

        await vector_store.delete_by_document(document_id)

        if doc_chunks:
            extraction_method = "ade"
            first_pages = " ".join(
                chunk.get("text", "") for chunk in doc_chunks[:5]
            )[:15000]
            for i, ac in enumerate(doc_chunks):
                chunk_text = ac.get("text", "").strip()
                if len(chunk_text) < 30:
                    continue
                chunk_id = str(uuid7())
                chunk_meta = {
                    **metadata,
                    "chunk_id": chunk_id,
                    "chunk_type": ac.get("chunk_type", "text"),
                    "chunk_index": i,
                    "extraction_method": "ade",
                }
                chunks.append({
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": chunk_meta,
                })
        else:
            extraction_method = "local"
            raw_text = await document_parser.get_markdown(
                file_url,
                visibility=visibility,
            )
            if not raw_text:
                raise ValueError("Failed to extract document text")
            extracted_chunks = await chunker.chunk_document(raw_text, metadata)
            chunks.extend(extracted_chunks)
            first_pages = raw_text[:15000]

        ast_chunks = await self._index_ast_if_code(
            file_url,
            visibility,
            document_id,
            metadata,
        )
        chunks.extend(ast_chunks)

        if chunks:
            safe_indices = await agentic_client.inspect_rag_chunks(
                [chunk["text"] for chunk in chunks]
            )
            chunks = [
                chunk for index, chunk in enumerate(chunks) if index in safe_indices
            ]

        try:
            summary = await agentic_client.summarize_rag_document(first_pages)
        except Exception:
            logger.exception("Document summary generation error")
            summary = ""
        if summary:
            chunks.insert(
                0,
                {
                    "id": f"{document_id}_global_summary",
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

        texts = [c["text"] for c in chunks]
        embeddings = await embedder.embed_batch(texts)
        ids = [c["id"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        await vector_store.upsert(
            ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas
        )
        await vector_store.wait_upsert()

        await content_client.mark_indexed(document_id, len(chunks))

        return {
            "document_id": document_id,
            "title": title,
            "chunks_count": len(chunks),
            "extraction_method": extraction_method,
            "status": "indexed",
            "graph_text": "\n".join(texts)[:8000],
        }

    async def _index_ast_if_code(
        self,
        file_url: str,
        visibility: str,
        document_id: str,
        metadata: Dict,
    ) -> List[Dict]:
        extension = os.path.splitext(file_url.split("?", 1)[0])[1].lower()
        if extension not in {".py", ".js", ".ts", ".java", ".go", ".c", ".cpp", ".rs"}:
            return []
        file_bytes, _ = await document_parser._download_from_minio(
            file_url,
            visibility=visibility,
        )
        if not file_bytes:
            return []
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temporary:
            temporary.write(file_bytes)
            temporary_path = temporary.name
        try:
            nodes = await asyncio.to_thread(ASTIndexer().index_file, temporary_path)
        finally:
            await asyncio.to_thread(os.unlink, temporary_path)
        chunks = []
        for node in nodes:
            snippet = node.get("snippet", "").strip()
            if len(snippet) < 30:
                continue
            chunk_id = str(uuid7())[:12]
            chunks.append(
                {
                    "id": f"{document_id}_{chunk_id}",
                    "text": (
                        f"[{node.get('type', 'code')}] "
                        f"{node.get('name', '')}\n{snippet}"
                    ),
                    "metadata": {
                        **metadata,
                        "chunk_id": chunk_id,
                        "chunk_type": "ast_code",
                        "chunk_index": node.get("line", 0),
                        "extraction_method": "ast",
                        "ast_node_type": node.get("type", ""),
                        "ast_node_name": node.get("name", ""),
                    },
                }
            )
        return chunks

ingestion_pipeline = IngestionPipelineService()
