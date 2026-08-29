import asyncio
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from src.core.infrastructure.configuration import settings


class ConversionService:
    """Convert stored documents with Docling and expose structured text to KNOWLEDGE."""

    def __init__(self):
        self._minio_base = settings.MINIO_ENDPOINT.rstrip("/")
        self._minio_private_bucket = settings.MINIO_PRIVATE_BUCKET
        self._minio_public_bucket = settings.MINIO_PUBLIC_BUCKET
        self._minio_access = settings.MINIO_ACCESS_KEY
        self._minio_secret = settings.MINIO_SECRET_KEY
        self._docling = None
        logger.info("Docling document conversion service initialized")

    def _resolve_bucket(self, object_key: str, visibility: str) -> str:
        if visibility in ("private", "restricted"):
            return self._minio_private_bucket
        return self._minio_public_bucket

    def _get_docling(self):
        if self._docling is None:
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
            from docling.document_converter import DocumentConverter, PdfFormatOption

            pdf_options = PdfPipelineOptions()
            pdf_options.do_ocr = True
            pdf_options.do_table_structure = True
            hf_home = Path(os.environ.get("HF_HOME", str(Path.home() / ".cache" / "huggingface")))
            rapidocr_cache = hf_home / "rapidocr"
            rapidocr_cache.mkdir(parents=True, exist_ok=True)
            pdf_options.ocr_options = RapidOcrOptions(
                backend="onnxruntime", rapidocr_params={"Global.model_root_dir": rapidocr_cache}
            )
            self._docling = DocumentConverter(
                format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_options)}
            )
            logger.info("Docling document converter loaded")
        return self._docling

    @staticmethod
    def _extract_structure(document) -> List[Dict]:
        """Expose Docling elements without making any chunking decisions."""
        structure = []
        for item, level in document.iterate_items():
            label = getattr(item, "label", type(item).__name__)
            label = getattr(label, "value", str(label))
            text = str(getattr(item, "text", "") or "").strip()
            if not text and label == "table" and hasattr(item, "export_to_markdown"):
                text = str(item.export_to_markdown(doc=document) or "").strip()
            if not text:
                continue
            provenance = getattr(item, "prov", None) or []
            page_no = getattr(provenance[0], "page_no", None) if provenance else None
            structure.append({"text": text, "type": label, "level": int(level), "page_no": page_no})
        return structure

    def _parse_file(self, file_path: Path) -> Dict:
        conversion = self._get_docling().convert(str(file_path))
        document = conversion.document
        markdown = document.export_to_markdown()
        page_count = len(document.pages) if getattr(document, "pages", None) else 1
        try:
            structure = self._extract_structure(document)
        except Exception as error:
            logger.warning(
                "Docling structure extraction failed; chunking will use Markdown ({})",
                type(error).__name__,
            )
            structure = []

        return {"markdown": markdown, "structure": structure, "page_count": page_count}

    async def parse_document(self, file_url: str, visibility: str = "public") -> Dict:
        file_bytes, file_ext = await self._download_from_minio(file_url, visibility=visibility)
        if not file_bytes:
            return {"error": "File load failed"}

        return await self.parse_bytes(file_bytes, file_ext)

    async def parse_bytes(self, file_bytes: bytes, file_ext: str = ".pdf") -> Dict:
        """Convert in-memory document bytes without leaking conversion into callers."""
        normalized_ext = file_ext.lower() if file_ext.startswith(".") else f".{file_ext.lower()}"
        if not normalized_ext[1:].isalnum():
            normalized_ext = ".pdf"

        with tempfile.NamedTemporaryFile(suffix=normalized_ext, delete=False) as temporary:
            temporary.write(file_bytes)
            temporary_path = Path(temporary.name)

        try:
            return await asyncio.to_thread(self._parse_file, temporary_path)
        except Exception:
            logger.exception("Docling document conversion failed")
            return {"error": "document_parsing_failed"}
        finally:
            await asyncio.to_thread(temporary_path.unlink, missing_ok=True)

    async def get_markdown(self, file_url: str, visibility: str = "private") -> str:
        parse_result = await self.parse_document(file_url, visibility=visibility)
        return parse_result.get("markdown", "")

    async def _download_from_minio(
        self, file_url: str, visibility: str = "public"
    ) -> tuple[Optional[bytes], str]:
        try:
            import boto3
            from urllib.parse import urlparse

            if file_url.startswith("http"):
                parsed = urlparse(file_url)
                path_parts = parsed.path.lstrip("/").split("/", 1)
                object_key = path_parts[1] if len(path_parts) == 2 else parsed.path.lstrip("/")
            else:
                object_key = file_url

            if ".." in object_key:
                logger.error("Prevented path traversal attempt")
                return None, ""

            bucket = self._resolve_bucket(object_key, visibility)
            s3 = boto3.client(
                "s3",
                endpoint_url=self._minio_base,
                aws_access_key_id=self._minio_access,
                aws_secret_access_key=self._minio_secret,
                region_name="us-east-1",
            )
            obj = await asyncio.to_thread(s3.get_object, Bucket=bucket, Key=object_key)
            data = await asyncio.to_thread(obj["Body"].read)
            extension = f".{object_key.rsplit('.', 1)[-1].lower()}" if "." in object_key else ".pdf"
            logger.info("Retrieved file content from storage")
            return data, extension
        except Exception:
            logger.exception("File download connection error")
            return None, ""


document_parser = ConversionService()
