import os
import io
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
from src.core.config import settings
from src.ingestion.chunker import chunker
from src.ingestion.embedder import embedding_service
from src.store.vector_store import vector_store

class IngestionPipeline:
    def __init__(self):
        mongo_uri = settings.MONGODB_URI
        self._mongo = AsyncIOMotorClient(mongo_uri)
        self._db = self._mongo.doclib
        minio_endpoint = settings.MINIO_ENDPOINT
        self._minio_base = minio_endpoint.rstrip("/")
        self._bucket = settings.MINIO_BUCKET_NAME

    async def ingest_document(self, document_id: str) -> Dict:
        document = await self._db.documents.find_one({"_id": __import__("bson").ObjectId(document_id)})
        if not document:
            raise ValueError(f"Document {document_id} not found in database")

        file_url = document.get("file_url", "")
        title = document.get("title", "Untitled")
        author = document.get("author", "Unknown")

        if not file_url:
            raise ValueError(f"Document {document_id} has no file_url")

        logger.info(f"Ingesting: {title} by {author}")

        metadata = {
            "document_id": document_id,
            "title": title,
            "author": author,
            "content_format": document.get("content_format", "unknown"),
            "source": "anna_archive"
        }

        extraction_method = "local"
        chunks = []

        from src.agents.ade_agent import ade_agent
        ade_chunks = await ade_agent.get_ade_chunks_for_ingestion(file_url)

        def get_summary_chunk(first_pages, extract_method):
            try:
                from langchain_huggingface import HuggingFaceEndpoint
                from langchain_core.prompts import PromptTemplate
                
                llama_model = settings.LLAMA_MODEL
                hf_token = settings.HF_TOKEN
                
                _hf = HuggingFaceEndpoint(repo_id=llama_model, huggingfacehub_api_token=hf_token, temperature=0.1)
                llm_summary = _hf
                prompt = PromptTemplate(
                    template="Dựa vào phần trích xuất văn bản sau, hãy tóm tắt các thông tin cốt lõi của tài liệu này theo định dạng:\nTên tài liệu: ...\nTác giả: ...\nNăm xuất bản/Bối cảnh: ...\nTóm tắt nội dung chính: ...\n\nVăn bản:\n{text}\n\nTạo Tóm Tắt Định Danh (Global Summary):",
                    input_variables=["text"]
                )
                global_summary_text = llm_summary.invoke(prompt.format(text=first_pages)).strip()
                
                logger.info(f"Generated Global Summary Chunk for {title}")
                return {
                    "id": f"{document_id}_global_summary",
                    "text": f"[GLOBAL METADATA - SUMMARY CHUNK]\nTài liệu: {title}\nTác giả: {author}\n{global_summary_text}",
                    "metadata": {**metadata, "chunk_id": "summary_001", "chunk_type": "summary", "chunk_index": -1, "extraction_method": extract_method}
                }
            except Exception as e:
                logger.warning(f"Failed to generate Global Summary Chunk: {e}")
                return None

        if ade_chunks:
            extraction_method = "ade"
            first_few_pages = " ".join([ac["text"] for ac in ade_chunks[:5]])[:15000]
            summary_chunk = get_summary_chunk(first_few_pages, "ade_llm")
            if summary_chunk:
                chunks.append(summary_chunk)

            for i, ac in enumerate(ade_chunks):
                chunk_id = str(uuid.uuid4())[:12]
                chunk_meta = {
                    **metadata,
                    "chunk_id": chunk_id,
                    "chunk_type": ac.get("chunk_type", "text"),
                    "chunk_index": i,
                    "extraction_method": "ade",
                }
                chunks.append({
                    "id": f"{document_id}_{chunk_id}",
                    "text": ac["text"],
                    "metadata": chunk_meta,
                })
            logger.info(f"ADE extraction: {len(chunks)} chunks")
        else:
            logger.info("ADE unavailable or failed, using local extraction")
            raw_text = await self._extract_text(file_url)
            if not raw_text or len(raw_text.strip()) < 100:
                raise ValueError(f"Extracted text too short for document {document_id}")
                
            first_few_pages = raw_text[:15000]
            summary_chunk = get_summary_chunk(first_few_pages, "local")
            if summary_chunk:
                chunks.append(summary_chunk)

            extracted_chunks = chunker.chunk_document(raw_text, metadata)
            chunks.extend(extracted_chunks)

        if not chunks:
            raise ValueError(f"No chunks produced for document {document_id}")

        texts = [c["text"] for c in chunks]
        embeddings = embedding_service.embed_batch(texts)
        ids = [c["id"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        vector_store.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

        await self._db.documents.update_one(
            {"_id": __import__("bson").ObjectId(document_id)},
            {"$set": {
                "indexing_status": "indexed",
                "indexed_chunks": len(chunks),
                "extraction_method": extraction_method,
            }}
        )

        result = {
            "document_id": document_id,
            "title": title,
            "chunks": len(chunks),
            "extraction_method": extraction_method,
            "status": "indexed"
        }
        logger.info(f"Ingestion complete: {result}")
        return result

    async def _extract_text(self, file_url: str) -> str:
        file_bytes = await self._download_file(file_url)
        if not file_bytes:
            return ""
        if file_url.endswith(".pdf"):
            return self._extract_pdf(file_bytes)
        elif file_url.endswith(".epub"):
            return self._extract_epub(file_bytes)
        else:
            return self._extract_pdf(file_bytes)

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

            logger.info(f"Downloading: bucket={bucket}, key={object_key}")

            import boto3
            s3 = boto3.client(
                "s3",
                endpoint_url=self._minio_base,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name="us-east-1"
            )
            obj = s3.get_object(Bucket=bucket, Key=object_key)
            data = obj["Body"].read()
            logger.info(f"Downloaded {len(data)} bytes from MinIO")
            return data
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None

    def _extract_pdf(self, data: bytes) -> str:
        try:
            import pdf2image
            import pytesseract
            
            logger.info("Starting OCR extraction for PDF using pytesseract")
            images = pdf2image.convert_from_bytes(data)
            pages_text = []
            
            for i, img in enumerate(images):
                text = pytesseract.image_to_string(img, lang="vie+eng")
                if text.strip():
                    pages_text.append(text.strip())
                    
            full_text = "\n\n".join(pages_text)
            logger.info(f"PDF OCR extracted: {len(images)} pages, {len(full_text)} chars")
            return full_text
        except ImportError:
            logger.error("Missing pdf2image or pytesseract. Please install them to use OCR.")
            return ""
        except Exception as e:
            logger.error(f"PDF OCR extraction error: {e}")
            return ""

    def _extract_epub(self, data: bytes) -> str:
        try:
            import zipfile
            from html.parser import HTMLParser

            class HTMLStripper(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.result = []
                    self._skip = False

                def handle_starttag(self, tag, attrs):
                    if tag in ("script", "style"):
                        self._skip = True
                    elif tag in ("p", "div", "br", "h1", "h2", "h3", "h4", "li"):
                        self.result.append("\n")

                def handle_endtag(self, tag):
                    if tag in ("script", "style"):
                        self._skip = False

                def handle_data(self, data):
                    if not self._skip:
                        self.result.append(data)

                def get_text(self):
                    return "".join(self.result)

            buf = io.BytesIO(data)
            parts = []
            with zipfile.ZipFile(buf) as zf:
                html_files = sorted([
                    n for n in zf.namelist()
                    if n.endswith((".xhtml", ".html", ".htm"))
                    and "toc" not in n.lower()
                    and "nav" not in n.lower()
                ])
                for html_file in html_files:
                    raw_html = zf.read(html_file).decode("utf-8", errors="ignore")
                    stripper = HTMLStripper()
                    stripper.feed(raw_html)
                    text = stripper.get_text().strip()
                    if len(text) > 50:
                        parts.append(text)
            full_text = "\n\n".join(parts)
            logger.info(f"EPUB extracted: {len(parts)} sections, {len(full_text)} chars")
            return full_text
        except Exception as e:
            logger.error(f"EPUB extraction error: {e}")
            return ""

ingestion_pipeline = IngestionPipeline()
