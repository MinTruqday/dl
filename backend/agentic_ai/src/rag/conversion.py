import asyncio
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import boto3
from loguru import logger

from src.core.infrastructure.configuration import settings

MODEL_ID = settings.DOCLING_MODEL

class _DoclingModel:
    def __init__(self):
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.datamodel.base_models import InputFormat

        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True

        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

    def convert(self, file_path: Path):
        return self.converter.convert(str(file_path))

def _extract_tables_from_html(html: str) -> List[Dict]:
    from bs4 import BeautifulSoup

    tables = []
    soup = BeautifulSoup(html, "html.parser")
    for i, table in enumerate(soup.find_all("table")):
        html_str = str(table)
        tables.append({"text": html_str, "chunk_type": "table", "index": i})
    return tables

class ConversionRag:
    def __init__(self):
        self._minio_base = settings.MINIO_ENDPOINT.rstrip("/")
        self._minio_private_bucket = settings.MINIO_PRIVATE_BUCKET
        self._minio_public_bucket = settings.MINIO_PUBLIC_BUCKET
        self._minio_access = settings.MINIO_ACCESS_KEY
        self._minio_secret = settings.MINIO_SECRET_KEY
        self._minio_region = settings.MINIO_REGION
        self._docling: Optional[_DoclingModel] = None
        logger.info("Document analysis tool initialized")

    def _get_docling(self) -> _DoclingModel:
        if self._docling is None:
            logger.info("Loading Docling document converter engine")
            self._docling = _DoclingModel()
            logger.info("Docling document converter loaded")
        return self._docling

    def _parse_file_with_docling(self, file_path: Path) -> Dict:
        try:
            docling = self._get_docling()
            conv_res = docling.convert(file_path)
            doc = conv_res.document
            markdown = doc.export_to_markdown()

            page_count = 1
            if hasattr(doc, "pages") and doc.pages:
                page_count = len(doc.pages)

            chunks = []
            try:
                from docling.chunking import HybridChunker
                chunker = HybridChunker()
                doc_chunks = list(chunker.chunk(doc))
                for c in doc_chunks:
                    text_content = c.text.strip()
                    if len(text_content) >= 30:
                        chunks.append({"text": text_content, "chunk_type": "text"})
            except Exception:
                chunks = self._split_markdown_to_chunks(markdown)

            if not chunks:
                chunks = self._split_markdown_to_chunks(markdown)

            return {
                "markdown": markdown,
                "chunks": chunks,
                "chunk_count": len(chunks),
                "page_count": page_count,
                "docling_document": doc,
            }
        except Exception as err:
            logger.warning(f"Docling conversion fallback triggered for {file_path.name}: {err}")
            markdown = ""
            try:
                from markitdown import MarkItDown
                md = MarkItDown()
                res = md.convert(str(file_path))
                markdown = res.text_content
                logger.info("Converted document using MarkItDown fallback")
            except Exception as md_err:
                logger.warning(f"MarkItDown fallback error for {file_path.name}: {md_err}")
                try:
                    markdown = file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    markdown = ""

            chunks = self._split_markdown_to_chunks(markdown)
            return {
                "markdown": markdown,
                "chunks": chunks,
                "chunk_count": len(chunks),
                "page_count": 1,
            }

    async def parse_document(self, file_url: str) -> Dict:
        file_bytes, file_ext = await self._download_from_minio(file_url)
        if not file_bytes:
            return {"error": "File load failed"}

        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = Path(tmp.name)

        try:
            if file_ext in [".doclib", ".doclibx"]:
                if len(file_bytes) < 60:
                    return {"error": "invalid_doclib_file"}

                import uuid
                import base64
                from cryptography.hazmat.primitives.ciphers.aead import AESGCM
                from motor.motor_asyncio import AsyncIOMotorClient
                from src.core.infrastructure.configuration import settings

                file_id_bytes = file_bytes[:16]
                nonce = file_bytes[48:60]
                ciphertext = file_bytes[60:]
                file_id = str(uuid.UUID(bytes=file_id_bytes))

                mongo_client = AsyncIOMotorClient(settings.MONGODB_URI)
                db = mongo_client.doclib
                license_doc = await db.drm_licenses.find_one({"file_id": file_id})

                if not license_doc or not license_doc.get("aes_key"):
                    return {"error": "document_decryption_license_not_found"}

                aes_key = base64.b64decode(license_doc.get("aes_key"))
                try:
                    aesgcm = AESGCM(aes_key)
                    decrypted_data = aesgcm.decrypt(nonce, ciphertext, None)
                    raw_text = decrypted_data.decode("utf-8")
                except Exception:
                    return {"error": "document_decryption_failed"}

                chunks = self._split_markdown_to_chunks(raw_text)
                return {
                    "markdown": raw_text,
                    "chunks": chunks,
                    "chunk_count": len(chunks),
                    "page_count": 1
                }

            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(None, self._parse_file_with_docling, tmp_path)
            res.pop("docling_document", None)
            return res
        except Exception:
            logger.exception("Document content analysis error")
            return {"error": "document_parsing_failed"}
        finally:
            await asyncio.to_thread(tmp_path.unlink, missing_ok=True)

    async def extract_tables(self, file_url: str) -> List[Dict]:
        file_bytes, file_ext = await self._download_from_minio(file_url)
        if not file_bytes:
            return []

        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = Path(tmp.name)

        try:
            loop = asyncio.get_event_loop()

            def _extract():
                parsed = self._parse_file_with_docling(tmp_path)
                doc = parsed.get("docling_document")
                extracted = []

                if doc and hasattr(doc, "tables") and doc.tables:
                    for i, tbl in enumerate(doc.tables):
                        tbl_html = ""
                        if hasattr(tbl, "export_to_html"):
                            tbl_html = tbl.export_to_html()
                        elif hasattr(tbl, "export_to_markdown"):
                            tbl_html = tbl.export_to_markdown()

                        if tbl_html.strip():
                            extracted.append({"text": tbl_html, "chunk_type": "table", "index": i})

                if not extracted:
                    markdown = parsed.get("markdown", "")
                    extracted = _extract_tables_from_html(markdown)

                return extracted

            tables = await loop.run_in_executor(None, _extract)
            logger.info("Extracted data tables")
            return tables
        except Exception:
            logger.exception("Data table extraction error")
            return []
        finally:
            await asyncio.to_thread(tmp_path.unlink, missing_ok=True)

    def _split_markdown_to_chunks(self, markdown: str) -> List[Dict]:
        if not markdown:
            return []

        chunks = []
        current_chunk = ""
        current_type = "text"

        for line in markdown.split("\n"):
            if line.startswith("#"):
                if current_chunk.strip() and len(current_chunk.strip()) > 30:
                    chunks.append(
                        {"text": current_chunk.strip(), "chunk_type": current_type}
                    )
                current_chunk = line + "\n"
                current_type = "heading"
            elif line.startswith("|") or line.startswith("<table"):
                if (
                    current_chunk.strip()
                    and current_type != "table"
                    and len(current_chunk.strip()) > 30
                ):
                    chunks.append(
                        {"text": current_chunk.strip(), "chunk_type": current_type}
                    )
                    current_chunk = ""
                current_chunk += line + "\n"
                current_type = "table"
            elif line.startswith("```"):
                if (
                    current_chunk.strip()
                    and current_type != "code"
                    and len(current_chunk.strip()) > 30
                ):
                    chunks.append(
                        {"text": current_chunk.strip(), "chunk_type": current_type}
                    )
                    current_chunk = ""
                current_chunk += line + "\n"
                current_type = "code" if current_type != "code" else "text"
            elif line.startswith("$$") or line.startswith("\\["):
                if (
                    current_chunk.strip()
                    and current_type != "equation"
                    and len(current_chunk.strip()) > 30
                ):
                    chunks.append(
                        {"text": current_chunk.strip(), "chunk_type": current_type}
                    )
                    current_chunk = ""
                current_chunk += line + "\n"
                current_type = "equation"
            else:
                if current_type in ("heading",) and line.strip() == "":
                    current_chunk += line + "\n"
                    if len(current_chunk.strip()) > 30:
                        chunks.append(
                            {"text": current_chunk.strip(), "chunk_type": current_type}
                        )
                    current_chunk = ""
                    current_type = "text"
                else:
                    current_chunk += line + "\n"

                if len(current_chunk) > 1500 and current_type == "text":
                    chunks.append(
                        {"text": current_chunk.strip(), "chunk_type": current_type}
                    )
                    current_chunk = ""

        if current_chunk.strip() and len(current_chunk.strip()) > 30:
            chunks.append({"text": current_chunk.strip(), "chunk_type": current_type})

        return chunks

    async def get_doc_chunks_for_ingestion(self, file_url: str) -> List[Dict]:
        parse_result = await self.parse_document(file_url)
        if parse_result.get("error"):
            logger.warning("Document parsing error")
            return []

        chunks = parse_result.get("chunks", [])

        file_ext = ""
        if "." in file_url:
            file_ext = "." + file_url.rsplit(".", 1)[-1].lower()

        doc_exts = [".pdf", ".docx", ".epub", ".pptx", ".xlsx", ".html", ".adoc"]
        if file_ext in doc_exts:
            table_chunks = await self.extract_tables(file_url)
            if table_chunks:
                chunks.extend(table_chunks)

        ingestion_chunks = []
        for i, chunk in enumerate(chunks):
            text = chunk.get("text", "")
            if len(text.strip()) < 30:
                continue
            ingestion_chunks.append(
                {
                    "text": text,
                    "chunk_type": chunk.get("chunk_type", "text"),
                    "index": i,
                }
            )

        logger.info("Created text chunks")
        return ingestion_chunks

    async def get_markdown(self, file_url: str) -> str:
        parse_result = await self.parse_document(file_url)
        return parse_result.get("markdown", "")

    async def _download_from_minio(self, file_url: str) -> tuple:
        try:
            from urllib.parse import urlparse

            if file_url.startswith("http"):
                parsed = urlparse(file_url)
                path_parts = parsed.path.lstrip("/").split("/", 1)
                object_key = path_parts[1] if len(path_parts) == 2 else parsed.path.lstrip("/")
            else:
                object_key = file_url

            bucket = self._minio_private_bucket if object_key.startswith("system/") else self._minio_public_bucket

            if ".." in object_key:
                logger.error("Prevented path traversal attempt")
                return None, ""

            s3 = boto3.client(
                "s3",
                endpoint_url=self._minio_base,
                aws_access_key_id=self._minio_access,
                aws_secret_access_key=self._minio_secret,
                region_name=self._minio_region,
            )
            obj = s3.get_object(Bucket=bucket, Key=object_key)
            data = obj["Body"].read()

            ext_map = {
                ".pdf": ".pdf",
                ".docx": ".docx",
                ".doc": ".doc",
                ".pptx": ".pptx",
                ".ppt": ".ppt",
                ".xlsx": ".xlsx",
                ".xls": ".xls",
                ".csv": ".csv",
                ".epub": ".epub",
                ".html": ".html",
                ".htm": ".htm",
                ".md": ".md",
                ".txt": ".md",
                ".adoc": ".adoc",
                ".png": ".png",
                ".jpg": ".jpg",
                ".jpeg": ".jpeg",
                ".bmp": ".bmp",
                ".tiff": ".tiff",
                ".webp": ".webp",
            }
            ext = ".pdf"
            for suffix, mapped_ext in ext_map.items():
                if object_key.lower().endswith(suffix):
                    ext = mapped_ext
                    break

            logger.info("Retrieved file content from storage")
            return data, ext

        except Exception:
            logger.exception("File download connection error")
            return None, ""

document_parser = ConversionRag()
