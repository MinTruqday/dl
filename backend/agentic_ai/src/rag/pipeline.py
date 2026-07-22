import os
import uuid
from typing import Dict, List, Optional

from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

from src.rag.chunk import chunker
from src.rag.embedding import embedder
from src.store.vector import vector_store
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings

class PipelineRag:
    """
    <module_purpose>
    <purpose>Manages the end-to-end data ingestion and vector indexing pipeline.</purpose>
    <metis_behavior>Extracts raw data robustly across formats. Never drops exceptions silently; routes errors to system logs. Integrates Neo4j for GraphRAG entity extraction.</metis_behavior>
    </module_purpose>
    """
    _mongo_client = None

    def __init__(self):
        mongo_uri = settings.MONGODB_URI
        if PipelineRag._mongo_client is None:
            PipelineRag._mongo_client = AsyncIOMotorClient(
                mongo_uri, maxPoolSize=100
            )
        self._mongo = PipelineRag._mongo_client
        self._db = self._mongo.doclib
        minio_endpoint = settings.MINIO_ENDPOINT
        self._minio_base = minio_endpoint.rstrip("/")
        self._minio_private_bucket = settings.MINIO_PRIVATE_BUCKET
        self._minio_public_bucket = settings.MINIO_PUBLIC_BUCKET
        
    async def authorize_document(
        self, document_id: str, user_id: str, is_admin: bool = False
    ) -> Dict:
        document = await self._db.documents.find_one({"_id": document_id})
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
                from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

                llama_model = settings.LLM_MODEL
                hf_token = settings.HF_TOKEN

                _hf = HuggingFaceEndpoint(
                    task="conversational",
                    repo_id=llama_model,
                    huggingfacehub_api_token=hf_token,
                    temperature=0.1,
                )
                llm_summary = ChatHuggingFace(llm=_hf)
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
            except Exception as e:
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

        await self._db.documents.update_one(
            {"_id": document_id},
            {
                "$set": {
                    "indexing_status": "indexed",
                    "indexed_chunks": len(chunks),
                    "extraction_method": extraction_method,
                }
            },
        )

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

        return self._extract_with_markitdown(file_bytes, file_url)

    async def _extract_from_zip(self, zip_data: bytes) -> str:
        import shutil
        import tempfile
        import zipfile

        all_text = []
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

        with tempfile.TemporaryDirectory(prefix="ingestion_zip_") as tmp_dir:
            zip_path = os.path.join(tmp_dir, "archive.zip")
            with open(zip_path, "wb") as f:
                f.write(zip_data)

            extract_path = os.path.join(tmp_dir, "extracted")
            os.makedirs(extract_path)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_path)

            search_root = extract_path
            top_contents = os.listdir(extract_path)
            if len(top_contents) == 1 and os.path.isdir(
                os.path.join(extract_path, top_contents[0])
            ):
                search_root = os.path.join(extract_path, top_contents[0])
                logger.info("Opening subdirectory inside compressed file")

            for root, _, files in os.walk(search_root):
                for f in files:
                    f_ext = os.path.splitext(f)[1].lower()
                    if f_ext in supported_exts:
                        f_path = os.path.join(root, f)
                        logger.info("Extracting file content")
                        try:
                            with open(f_path, "rb") as f_handle:
                                content_bytes = f_handle.read()
                                file_text = self._extract_with_markitdown(
                                    content_bytes, f
                                )
                                if file_text:
                                    all_text.append(f"--- FILE: {f} ---\n{file_text}")
                        except Exception as e:
                            logger.exception("Error loading data from compressed file")

        return "\n\n".join(all_text)

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
            logger.info("File data downloaded successfully")
            return data
        except Exception as e:
            logger.exception("File download error")
            return None

    def _extract_with_markitdown(self, data: bytes, file_url: str) -> str:
        try:
            import os
            import tempfile

            from markitdown import MarkItDown

            ext = os.path.splitext(file_url)[1] or ".pdf"

            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(data)
                tmp_path = tmp.name

            logger.info("Analyzing downloaded file data")
            md = MarkItDown()
            result = md.convert(tmp_path)
            full_text = result.text_content

            os.remove(tmp_path)

            logger.info("Document content analyzed successfully")
            return full_text
        except ImportError as e:
            logger.exception("Missing content analysis library")
            return ""
        except Exception as e:
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
                logger.info("Successfully pushed entities to GraphRAG store")
        except Exception as e:
            logger.exception("GraphRAG entity extraction failed")

ingestion_pipeline = PipelineRag()
