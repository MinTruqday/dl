import os
from typing import Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from src.rag.chunk import chunker, _sanitize_text
from src.rag.embedding import embedder
from src.store.vector import vector_store
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings
from src.services.content_client import ContentClient


def _resolve_bucket(object_key: str, visibility: str) -> str:
    if visibility in ("private", "restricted"):
        return settings.MINIO_PRIVATE_BUCKET
    return settings.MINIO_PUBLIC_BUCKET


class PipelineRag:
    """
    <module_purpose>
    <purpose>Manages the end-to-end data ingestion and vector indexing pipeline.</purpose>
    <metis_behavior>Extracts raw data robustly across formats. Never drops exceptions silently; routes errors to system logs. Integrates GraphRAG entity extraction via Redis edge store.</metis_behavior>
    </module_purpose>
    """
    def __init__(self):
        minio_endpoint = settings.MINIO_ENDPOINT
        self._minio_base = minio_endpoint.rstrip("/")
        self._minio_private_bucket = settings.MINIO_PRIVATE_BUCKET
        self._minio_public_bucket = settings.MINIO_PUBLIC_BUCKET

    async def authorize_document(
        self, document_id: str, user_id: str, is_admin: bool = False
    ) -> Dict:
        document = await ContentClient.drm_content(
            document_id, user_id, "index", is_admin
        )
        if not document:
            raise ValueError("Document not found or access denied")
        return document

    async def ingest_document(
        self, document_id: str, user_id: str, is_admin: bool = False
    ) -> Dict:
        document = await self.authorize_document(document_id, user_id, is_admin)

        file_url = document.get("file_url", "")
        title = document.get("title", "Untitled")
        author = document.get("author", "Unknown")
        visibility = document.get("visibility", "public")
        content_source = document.get("source") or document.get("content_source") or "user_upload"

        if not file_url:
            raise ValueError("Missing file path parameter")

        logger.info("Initializing document ingestion process")

        metadata = {
            "document_id": document_id,
            "title": title,
            "author": author,
            "content_format": document.get("content_format", "unknown"),
            "source": content_source,
            "visibility": visibility,
            "file_url": file_url,
        }

        extraction_method = "local"
        chunks = []

        from src.rag.conversion import document_parser

        doc_chunks = await document_parser.get_doc_chunks_for_ingestion(file_url, visibility=visibility)

        async def get_summary_chunk(first_pages: str, extract_method: str):
            try:
                safe_text = first_pages
                if not await _sanitize_text(safe_text):
                    logger.warning("Summary input failed sanitization check, skipping summary chunk")
                    return None

                from langchain_core.prompts import PromptTemplate
                from huggingface_hub import AsyncInferenceClient
                from src.utils.huggingface import HFInferenceChat

                llama_model = settings.LLM_MODEL
                hf_token = settings.HF_TOKEN

                _hf = AsyncInferenceClient(
                    model=llama_model,
                    token=hf_token,
                )
                llm_summary = HFInferenceChat(
                    client=_hf,
                    model=llama_model,
                )
                from src.core.registry import PromptType, registry

                prompt_content = registry.get(PromptType.DOCUMENT_GLOBAL_SUMMARY).format(text=safe_text)
                response = await llm_summary.ainvoke([HumanMessage(content=prompt_content)])
                global_summary_text = response.content.strip()

                return {
                    "id": f"{document_id}_global_summary",
                    "text": f"[GLOBAL METADATA - SUMMARY CHUNK]\\nDocument: {title}\\nAuthor: {author}\\n{global_summary_text}",
                    "metadata": {
                        **metadata,
                        "chunk_id": "summary_001",
                        "chunk_type": "summary",
                        "chunk_index": -1,
                        "extraction_method": extract_method,
                    },
                }
            except Exception:
                logger.exception("Document summary generation error")
                return None

        await vector_store.delete_by_document(document_id)

        _entity_text = ""
        if doc_chunks:
            extraction_method = "ade"
            first_few_pages = " ".join([ac["text"] for ac in doc_chunks[:5]])[:15000]
            _entity_text = first_few_pages[:8000]
            summary_chunk = await get_summary_chunk(first_few_pages, "ade_llm")
            if summary_chunk:
                chunks.append(summary_chunk)

            import asyncio

            async def process_docling_chunk(i: int, ac: Dict):
                chunk_text = ac.get("text", "").strip()
                if len(chunk_text) < 30:
                    return None
                if not await _sanitize_text(chunk_text):
                    return None
                chunk_id = str(uuid7())[:12]
                chunk_meta = {
                    **metadata,
                    "chunk_id": chunk_id,
                    "chunk_type": ac.get("chunk_type", "text"),
                    "chunk_index": i,
                    "extraction_method": "ade",
                }
                return {
                    "id": f"{document_id}_{chunk_id}",
                    "text": chunk_text,
                    "metadata": chunk_meta,
                }

            results = await asyncio.gather(*(process_docling_chunk(i, ac) for i, ac in enumerate(doc_chunks)))
            chunks.extend([r for r in results if r is not None])
        else:
            raw_text = await self._extract_text(file_url, visibility=visibility)
            if not raw_text or len(raw_text.strip()) < 100:
                raise ValueError("Insufficient extracted text to proceed")

            first_few_pages = raw_text[:15000]
            _entity_text = raw_text[:8000]
            summary_chunk = await get_summary_chunk(first_few_pages, "local")
            if summary_chunk:
                chunks.append(summary_chunk)

            extracted_chunks = await chunker.chunk_document(raw_text, metadata)
            chunks.extend(extracted_chunks)

        ast_chunks = await self._index_ast_if_code(file_url, visibility, document_id, metadata)
        chunks.extend(ast_chunks)

        await self._extract_entities_and_relations(_entity_text, document_id)

        if not chunks:
            raise ValueError("Document chunking error")

        texts = [c["text"] for c in chunks]
        embeddings = await embedder.embed_batch(texts)
        ids = [c["id"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        await vector_store.upsert(
            ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas
        )
        await vector_store.wait_upsert()

        await ContentClient.update_index(document_id, len(chunks), extraction_method)

        return {
            "document_id": document_id,
            "title": title,
            "chunks": len(chunks),
            "extraction_method": extraction_method,
            "status": "indexed",
        }

    async def _index_ast_if_code(
        self,
        file_url: str,
        visibility: str,
        document_id: str,
        metadata: Dict,
    ) -> List[Dict]:
        code_exts = {".py", ".js", ".ts", ".java", ".go", ".c", ".cpp", ".rs"}
        raw_path = file_url.split("?")[0]
        ext = os.path.splitext(raw_path)[1].lower()
        if ext not in code_exts:
            return []
        try:
            import tempfile
            from pathlib import Path
            from src.rag.ast_indexer import ASTIndexer

            file_bytes = await self._download_file(file_url, visibility=visibility)
            if not file_bytes:
                return []

            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            try:
                indexer = ASTIndexer()
                ast_nodes = indexer.index_file(tmp_path)
            finally:
                Path(tmp_path).unlink(missing_ok=True)

            chunks = []
            for node in ast_nodes:
                snippet = node.get("snippet", "").strip()
                if len(snippet) < 30:
                    continue
                chunk_id = str(uuid7())[:12]
                chunks.append({
                    "id": f"{document_id}_{chunk_id}",
                    "text": f"[{node.get('type', 'code')}] {node.get('name', '')}\n{snippet}",
                    "metadata": {
                        **metadata,
                        "chunk_id": chunk_id,
                        "chunk_type": "ast_code",
                        "chunk_index": node.get("line", 0),
                        "extraction_method": "ast",
                        "ast_node_type": node.get("type", ""),
                        "ast_node_name": node.get("name", ""),
                    },
                })
            logger.info(f"AST indexing produced {len(chunks)} code chunks for document {document_id}")
            return chunks
        except Exception:
            logger.exception("AST indexing failed")
            return []

    async def _extract_text(self, file_url: str, visibility: str = "public") -> str:
        file_bytes = await self._download_file(file_url, visibility=visibility)
        if not file_bytes:
            return ""

        ext = os.path.splitext(file_url.split("?")[0])[1].lower()

        if ext == ".zip":
            logger.info("Compressed file detected")
            return await self._extract_from_zip(file_bytes)

        return self._extract_with_docling(file_bytes, file_url)

    async def _extract_from_zip(self, zip_data: bytes) -> str:
        import asyncio
        import shutil
        import stat
        import tempfile
        import zipfile
        from pathlib import Path

        supported_exts = {
            ".pdf",
            ".txt",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".epub",
            ".mobi",
            ".ppt",
            ".pptx",
            ".md",
            ".tex",
        }

        def extract_archive() -> str:
            all_text = []
            with tempfile.TemporaryDirectory(prefix="ingestion_zip_") as tmp_dir:
                zip_path = os.path.join(tmp_dir, "archive.zip")
                with open(zip_path, "wb") as archive_handle:
                    archive_handle.write(zip_data)

                extract_path = os.path.join(tmp_dir, "extracted")
                os.makedirs(extract_path)

                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    members = zip_ref.infolist()
                    files = [member for member in members if not member.is_dir()]
                    if len(files) > settings.AGENT_ARCHIVE_MAX_FILES:
                        raise ValueError("archive_file_limit_exceeded")
                    total_size = sum(member.file_size for member in files)
                    if total_size > settings.AGENT_ARCHIVE_MAX_UNCOMPRESSED_BYTES:
                        raise ValueError("archive_size_limit_exceeded")
                    compressed_size = sum(member.compress_size for member in files)
                    if (
                        total_size
                        and total_size / max(compressed_size, 1)
                        > settings.AGENT_ARCHIVE_MAX_COMPRESSION_RATIO
                    ):
                        raise ValueError("archive_compression_ratio_exceeded")

                    extraction_root = Path(extract_path).resolve()
                    for member in members:
                        mode = member.external_attr >> 16
                        if stat.S_IFMT(mode) == stat.S_IFLNK:
                            raise ValueError("archive_symbolic_link_blocked")
                        if member.flag_bits & 1:
                            raise ValueError("archive_encryption_unsupported")
                        target = (extraction_root / member.filename).resolve()
                        if not target.is_relative_to(extraction_root):
                            raise ValueError("archive_path_traversal_blocked")
                        if member.is_dir():
                            target.mkdir(parents=True, exist_ok=True)
                            continue
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with zip_ref.open(member, "r") as source_handle:
                            with open(target, "wb") as target_handle:
                                shutil.copyfileobj(source_handle, target_handle)

                search_root = extract_path
                top_contents = os.listdir(extract_path)
                if len(top_contents) == 1 and os.path.isdir(
                    os.path.join(extract_path, top_contents[0])
                ):
                    search_root = os.path.join(extract_path, top_contents[0])
                    logger.info("Opening subdirectory inside compressed file")

                for root, _, files in os.walk(search_root):
                    for file_name in files:
                        file_extension = os.path.splitext(file_name)[1].lower()
                        if file_extension not in supported_exts:
                            continue
                        file_path = os.path.join(root, file_name)
                        logger.info("Extracting file content")
                        try:
                            with open(file_path, "rb") as file_handle:
                                content_bytes = file_handle.read()
                            file_text = self._extract_with_docling(
                                content_bytes,
                                file_name,
                            )
                            if file_text:
                                all_text.append(
                                    f"--- FILE: {file_name} ---\n{file_text}"
                                )
                        except Exception:
                            logger.exception(
                                "Error loading data from compressed file"
                            )
            return "\n\n".join(all_text)

        return await asyncio.to_thread(extract_archive)

    async def _download_file(self, url: str, visibility: str = "public") -> Optional[bytes]:
        try:
            from urllib.parse import urlparse

            access_key = settings.MINIO_ACCESS_KEY
            secret_key = settings.MINIO_SECRET_KEY

            if url.startswith("http"):
                parsed = urlparse(url)
                path_parts = parsed.path.lstrip("/").split("/", 1)
                object_key = path_parts[1] if len(path_parts) == 2 else parsed.path.lstrip("/")
            else:
                object_key = url

            bucket = _resolve_bucket(object_key, visibility)

            logger.info("Downloading file from cloud storage")

            import boto3

            s3 = boto3.client(
                "s3",
                endpoint_url=self._minio_base,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=settings.MINIO_REGION,
            )
            obj = s3.get_object(Bucket=bucket, Key=object_key)
            data = obj["Body"].read()
            logger.info("File data downloaded")
            return data
        except Exception:
            logger.exception("File download error")
            return None

    def _extract_with_docling(self, data: bytes, file_url: str) -> str:
        try:
            import os
            import tempfile
            from pathlib import Path
            from src.rag.conversion import document_parser

            ext = os.path.splitext(file_url)[1] or ".pdf"

            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(data)
                tmp_path = Path(tmp.name)

            try:
                logger.info("Analyzing file data using Docling")
                parse_res = document_parser._parse_file_with_docling(tmp_path)
                full_text = parse_res.get("markdown", "")
                logger.info("Document content analyzed")
                return full_text
            finally:
                tmp_path.unlink(missing_ok=True)
        except Exception:
            logger.exception("Data analysis error")
            return ""

    async def _extract_entities_and_relations(self, text: str, document_id: str):
        if not text or not text.strip():
            return

        from src.core.registry import PromptType, registry
        from src.workflow.graph import llm
        from src.memory.management import memory_manager
        import json
        from langchain_core.messages import SystemMessage, HumanMessage
        from pydantic import BaseModel

        class GraphRelation(BaseModel):
            source: str
            target: str
            relation: str

        class ExtractedGraph(BaseModel):
            relations: List[GraphRelation]

        logger.info(f"Extracting GraphRAG entities for document {document_id}")
        system_prompt = registry.get(PromptType.GRAPHRAG_ENTITY_EXTRACTION)
        human_msg = f"Extract key entities and relationships from this text:\n\n{text[:8000]}"

        try:
            msg = [SystemMessage(content=system_prompt), HumanMessage(content=human_msg)]
            response = await llm.with_structured_output(ExtractedGraph).ainvoke(msg)
            if memory_manager._redis and response.relations:
                edge_key = f"graphrag:edges:{document_id}"
                node_key = f"graphrag:nodes:{document_id}"
                nodes: set = set()
                for relation in response.relations:
                    edge_data = json.dumps(
                        {
                            "document_id": document_id,
                            "source": relation.source,
                            "target": relation.target,
                            "relation": relation.relation,
                        },
                        ensure_ascii=False,
                    )
                    await memory_manager._redis.lpush(edge_key, edge_data)
                    nodes.add(relation.source)
                    nodes.add(relation.target)

                await memory_manager._redis.expire(edge_key, 86400 * 30)

                if nodes:
                    await memory_manager._redis.sadd(node_key, *nodes)
                    await memory_manager._redis.expire(node_key, 86400 * 30)

                logger.info(f"Pushed {len(response.relations)} GraphRAG edges and {len(nodes)} nodes for document {document_id}")
        except Exception:
            logger.exception("GraphRAG entity extraction failed")


ingestion_pipeline = PipelineRag()
