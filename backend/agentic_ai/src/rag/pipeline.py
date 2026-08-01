import os
from typing import Dict, List, Optional

from loguru import logger

from src.rag.chunk import chunker
from src.rag.embedding import embedder
from src.store.vector import vector_store
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings
from src.services.content_client import ContentClient

class PipelineRag:
    """
    <module_purpose>
    <purpose>Manages the end-to-end data ingestion and vector indexing pipeline.</purpose>
    <metis_behavior>Extracts raw data robustly across formats. Never drops exceptions silently; routes errors to system logs. Integrates Neo4j for GraphRAG entity extraction.</metis_behavior>
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
        document = await ContentClient.accessible(document_id, user_id, is_admin)
        if not document:
            raise ValueError("Document not found or access denied")
        if not is_admin:
            allowed_users = {
                str(document.get("creator_id", "")),
                *[str(value) for value in document.get("coauthors", [])],
            }
            if user_id not in allowed_users:
                raise PermissionError("Document not found or access denied")
        return document

    async def ingest_document(
        self, document_id: str, user_id: str, is_admin: bool = False
    ) -> Dict:
        document = await self.authorize_document(document_id, user_id, is_admin)

        file_url = document.get("file_url", "")
        title = document.get("title", "Untitled")
        author = document.get("author", "Unknown")

        if not file_url:
            raise ValueError("Missing file path parameter")

        logger.info("Initializing document ingestion process")

        metadata = {
            "document_id": document_id,
            "title": title,
            "author": author,
            "content_format": document.get("content_format", "unknown"),
            "source": "anna_archive",
            "file_url": file_url,
        }

        extraction_method = "local"
        chunks = []

        from src.rag.conversion import document_parser

        doc_chunks = await document_parser.get_doc_chunks_for_ingestion(file_url)

        async def get_summary_chunk(first_pages, extract_method):
            try:
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
                prompt = PromptTemplate(
                    template="Based on the following extracted text, summarize the core information of this document in the format:\nDocument Name: (Name)\nAuthor: (Author)\nPublication Year/Context: (Year/Context)\nMain Content Summary: (Content)\n\nText:\n{text}\n\nGenerate Identity Summary (Global Summary):",
                    input_variables=["text"],
                )
                response = await llm_summary.ainvoke(prompt.format(text=first_pages))
                global_summary_text = response.content.strip()

                return {
                    "id": f"{document_id}_global_summary",
                    "text": f"[GLOBAL METADATA - SUMMARY CHUNK]\nDocument: {title}\nAuthor: {author}\n{global_summary_text}",
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

        if doc_chunks:
            extraction_method = "ade"
            first_few_pages = " ".join([ac["text"] for ac in doc_chunks[:5]])[:15000]
            summary_chunk = await get_summary_chunk(first_few_pages, "ade_llm")
            if summary_chunk:
                chunks.append(summary_chunk)

            for i, ac in enumerate(doc_chunks):
                chunk_id = str(uuid7())[:12]
                chunk_meta = {
                    **metadata,
                    "chunk_id": chunk_id,
                    "chunk_type": ac.get("chunk_type", "text"),
                    "chunk_index": i,
                    "extraction_method": "ade",
                }
                chunks.append(
                    {
                        "id": f"{document_id}_{chunk_id}",
                        "text": ac["text"],
                        "metadata": chunk_meta,
                    }
                )
        else:
            raw_text = await self._extract_text(file_url)
            if not raw_text or len(raw_text.strip()) < 100:
                raise ValueError("Insufficient extracted text to proceed")

            first_few_pages = raw_text[:15000]
            summary_chunk = await get_summary_chunk(first_few_pages, "local")
            if summary_chunk:
                chunks.append(summary_chunk)

            extracted_chunks = await chunker.chunk_document(raw_text, metadata)
            chunks.extend(extracted_chunks)
            
        await self._extract_entities_and_relations(first_few_pages, document_id)

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

    async def _extract_text(self, file_url: str) -> str:
        file_bytes = await self._download_file(file_url)
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

    async def _download_file(self, url: str) -> Optional[bytes]:
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
                
            bucket = self._minio_private_bucket if object_key.startswith("system/") else self._minio_public_bucket

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
            if memory_manager._redis:
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
                    await memory_manager._redis.sadd(
                        f"graphrag:edges:{document_id}", edge_data
                    )
                logger.info("Pushed entities to GraphRAG store")
        except Exception:
            logger.exception("GraphRAG entity extraction failed")

ingestion_pipeline = PipelineRag()
