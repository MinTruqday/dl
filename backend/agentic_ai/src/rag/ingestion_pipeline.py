import os
import uuid
from typing import Dict, List, Optional

from core.config import settings
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from src.rag.chunker import chunker
from src.rag.embedder import embedding_service
from src.store.vector_store import vector_store
from uuid6 import uuid7


class IngestionPipeline:
    _mongo_client = None

    def __init__(self):
        mongo_uri = settings.MONGODB_URI
        if IngestionPipeline._mongo_client is None:
            IngestionPipeline._mongo_client = AsyncIOMotorClient(
                mongo_uri, maxPoolSize=100
            )
        self._mongo = IngestionPipeline._mongo_client
        self._db = self._mongo.doclib
        minio_endpoint = settings.MINIO_ENDPOINT
        self._minio_base = minio_endpoint.rstrip("/")
        self._bucket = settings.MINIO_BUCKET_NAME

    async def ingest_document(self, document_id: str) -> Dict:
        document = await self._db.documents.find_one(
            {"_id": __import__("bson").ObjectId(document_id)}
        )
        if not document:
            raise ValueError(f"Document {document_id} not found in database")

        file_url = document.get("file_url", "")
        title = document.get("title", "Untitled")
        author = document.get("author", "Unknown")

        if not file_url:
            raise ValueError(f"Document {document_id} has no file_url")

        logger.info(f"Đang nạp dữ liệu: {title} của {author}")

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

        from src.rag.document_parser import document_parser

        doc_chunks = await document_parser.get_doc_chunks_for_ingestion(file_url)

        async def get_summary_chunk(first_pages, extract_method):
            try:
                from langchain_core.prompts import PromptTemplate
                from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

                llama_model = settings.LLAMA_MODEL
                hf_token = settings.HF_TOKEN

                _hf = HuggingFaceEndpoint(
                    task="conversational",
                    repo_id=llama_model,
                    huggingfacehub_api_token=hf_token,
                    temperature=0.1,
                )
                llm_summary = ChatHuggingFace(llm=_hf)
                prompt = PromptTemplate(
                    template="Dựa vào phần trích xuất văn bản sau, hãy tóm tắt các thông tin cốt lõi của tài liệu này theo định dạng:\nTên tài liệu: (Tên)\nTác giả: (Tác giả)\nNăm xuất bản/Bối cảnh: (Năm/Bối cảnh)\nTóm tắt nội dung chính: (Nội dung)\n\nVăn bản:\n{text}\n\nTạo Tóm Tắt Định Danh (Global Summary):",
                    input_variables=["text"],
                )
                response = await llm_summary.ainvoke(prompt.format(text=first_pages))
                global_summary_text = response.content.strip()

                return {
                    "id": f"{document_id}_global_summary",
                    "text": f"[GLOBAL METADATA - SUMMARY CHUNK]\nTài liệu: {title}\nTác giả: {author}\n{global_summary_text}",
                    "metadata": {
                        **metadata,
                        "chunk_id": "summary_001",
                        "chunk_type": "summary",
                        "chunk_index": -1,
                        "extraction_method": extract_method,
                    },
                }
            except Exception as e:
                logger.error("Không thể tạo đoạn tóm tắt toàn cục")
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
                raise ValueError(
                    f"Văn bản trích xuất quá ngắn đối với tài liệu {document_id}"
                )

            first_few_pages = raw_text[:15000]
            summary_chunk = await get_summary_chunk(first_few_pages, "local")
            if summary_chunk:
                chunks.append(summary_chunk)

            extracted_chunks = chunker.chunk_document(raw_text, metadata)
            chunks.extend(extracted_chunks)

        if not chunks:
            raise ValueError(f"Không thể phân mảnh nội dung cho tài liệu {document_id}")

        texts = [c["text"] for c in chunks]
        embeddings = await embedding_service.embed_batch(texts)
        ids = [c["id"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        await vector_store.upsert(
            ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas
        )
        await vector_store.wait_upsert()

        await self._db.documents.update_one(
            {"_id": __import__("bson").ObjectId(document_id)},
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
            logger.info(f"Phát hiện tệp ZIP trong quá trình nạp dữ liệu: {file_url}")
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
                logger.info(f"Navigating into nested folder: {top_contents[0]}")

            for root, _, files in os.walk(search_root):
                for f in files:
                    f_ext = os.path.splitext(f)[1].lower()
                    if f_ext in supported_exts:
                        f_path = os.path.join(root, f)
                        logger.info(f"Đang trích xuất nội dung từ tệp con: {f}")
                        try:
                            with open(f_path, "rb") as f_handle:
                                content_bytes = f_handle.read()
                                file_text = self._extract_with_markitdown(
                                    content_bytes, f
                                )
                                if file_text:
                                    all_text.append(f"--- FILE: {f} ---\n{file_text}")
                        except Exception as e:
                            logger.error("Lỗi nạp dữ liệu từ {f}")

        return "\n\n".join(all_text)

    async def _download_file(self, url: str) -> Optional[bytes]:
        try:
            from urllib.parse import urlparse

            access_key = settings.MINIO_ACCESS_KEY
            secret_key = settings.MINIO_SECRET_KEY

            if url.startswith("http"):
                parsed = urlparse(url)
                path_parts = parsed.path.lstrip("/").split("/", 1)
                if len(path_parts) == 2:
                    bucket = path_parts[0]
                    object_key = path_parts[1]
                else:
                    bucket = self._bucket
                    object_key = parsed.path.lstrip("/")
            else:
                bucket = self._bucket
                object_key = url

            logger.info(
                f"Đang tải xuống từ không gian lưu trữ {bucket}, key={object_key}"
            )

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
            logger.info(f"Đã tải xuống {len(data)} byte từ MinIO")
            return data
        except Exception as e:
            logger.error("Download lỗi")
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

            logger.info(f"Đang tiến hành phân tích dữ liệu cho tệp {ext}")
            md = MarkItDown()
            result = md.convert(tmp_path)
            full_text = result.text_content

            os.remove(tmp_path)

            logger.info(f"Đã phân tích thành công {len(full_text)} ký tự")
            return full_text
        except ImportError:
            logger.error("Hệ thống đang thiếu thư viện phân tích nội dung")
            return ""
        except Exception as e:
            logger.error("Quá trình phân tích dữ liệu thất bại do lỗi")
            return ""


ingestion_pipeline = IngestionPipeline()
