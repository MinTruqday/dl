import asyncio
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
import boto3
from loguru import logger
from src.core.infrastructure.configuration import settings

class ConversionService:
    def __init__(self):
        self._minio_base = settings.MINIO_ENDPOINT.rstrip("/")
        self._minio_private_bucket = settings.MINIO_PRIVATE_BUCKET
        self._minio_public_bucket = settings.MINIO_PUBLIC_BUCKET
        self._minio_access = settings.MINIO_ACCESS_KEY
        self._minio_secret = settings.MINIO_SECRET_KEY
        logger.info("Document analysis tool initialized")

    def _resolve_bucket(self, object_key: str, visibility: str) -> str:
        if visibility in ("private", "restricted"):
            return self._minio_private_bucket
        return self._minio_public_bucket

    def _parse_file(self, file_path: Path) -> Dict:
        markdown = ""
        try:
            from markitdown import MarkItDown
            md = MarkItDown()
            res = md.convert(str(file_path))
            markdown = res.text_content
            logger.info("Converted document using MarkItDown")
        except Exception as md_err:
            logger.warning(f"MarkItDown error for {file_path.name}: {md_err}")
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

    async def parse_document(self, file_url: str, visibility: str = "public") -> Dict:
        file_bytes, file_ext = await self._download_from_minio(file_url, visibility=visibility)
        if not file_bytes:
            return {"error": "File load failed"}

        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = Path(tmp.name)

        try:
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(None, self._parse_file, tmp_path)
            return res
        except Exception:
            logger.exception("Document content analysis error")
            return {"error": "document_parsing_failed"}
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

    async def get_doc_chunks_for_ingestion(self, file_url: str, visibility: str = "public") -> List[Dict]:
        parse_result = await self.parse_document(file_url, visibility=visibility)
        if parse_result.get("error"):
            logger.warning("Document parsing error")
            return []

        chunks = parse_result.get("chunks", [])
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

    async def get_markdown(self, file_url: str, visibility: str = "private") -> str:
        parse_result = await self.parse_document(file_url, visibility=visibility)
        return parse_result.get("markdown", "")

    async def _download_from_minio(self, file_url: str, visibility: str = "public") -> tuple:
        try:
            from urllib.parse import urlparse

            if file_url.startswith("http"):
                parsed = urlparse(file_url)
                path_parts = parsed.path.lstrip("/").split("/", 1)
                object_key = path_parts[1] if len(path_parts) == 2 else parsed.path.lstrip("/")
            else:
                object_key = file_url

            bucket = self._resolve_bucket(object_key, visibility)

            if ".." in object_key:
                logger.error("Prevented path traversal attempt")
                return None, ""

            s3 = boto3.client(
                "s3",
                endpoint_url=self._minio_base,
                aws_access_key_id=self._minio_access,
                aws_secret_access_key=self._minio_secret,
                region_name="us-east-1",
            )
            obj = s3.get_object(Bucket=bucket, Key=object_key)
            data = obj["Body"].read()

            ext = ".pdf"
            if "." in object_key:
                ext = "." + object_key.rsplit(".", 1)[-1].lower()

            logger.info("Retrieved file content from storage")
            return data, ext

        except Exception:
            logger.exception("File download connection error")
            return None, ""

document_parser = ConversionService()
