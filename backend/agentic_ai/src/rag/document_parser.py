import asyncio
import tempfile
from pathlib import Path
from typing import Dict, List

import boto3
from core.config import settings
from loguru import logger


class DocumentParser:
    def __init__(self):
        self._minio_base = settings.MINIO_ENDPOINT.rstrip("/")
        self._bucket = settings.MINIO_BUCKET_NAME
        self._minio_access = settings.MINIO_ACCESS_KEY
        self._minio_secret = settings.MINIO_SECRET_KEY
        self._minio_region = settings.MINIO_REGION
        self._marker_models = None
        self._ocr_engine = None
        self._pp_structure = None
        logger.info("Khởi tạo công cụ phân tích tài liệu thành công")

    def _get_marker_models(self):
        if self._marker_models is None:
            from marker.models import create_model_dict

            self._marker_models = create_model_dict()
            logger.info("Tải cấu hình phân tích tài liệu thành công")
        return self._marker_models

    def _get_ocr_engine(self, lang: str = "en"):
        if self._ocr_engine is None or getattr(self, "_ocr_lang", None) != lang:
            from paddleocr import PaddleOCR

            self._ocr_engine = PaddleOCR(
                use_angle_cls=True,
                lang=lang,
                show_log=False,
            )
            self._ocr_lang = lang
            logger.info("Khởi tạo công cụ trích xuất văn bản thành công")
        return self._ocr_engine

    def _get_pp_structure(self, lang: str = "en"):
        if self._pp_structure is None or getattr(self, "_pp_lang", None) != lang:
            from paddleocr import PPStructure

            self._pp_structure = PPStructure(
                show_log=False,
                image_orientation=True,
                layout=True,
                table=True,
                ocr=True,
                lang=lang,
            )
            self._pp_lang = lang
            logger.info("Khởi tạo công cụ trích xuất bố cục thành công")
        return self._pp_structure

    async def parse_document(self, file_url: str) -> Dict:
        file_bytes, file_ext = await self._download_from_minio(file_url)
        if not file_bytes:
            return {"error": "Lỗi tải tệp tin từ hệ thống lưu trữ"}

        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = Path(tmp.name)

        try:
            image_exts = [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"]
            if file_ext in image_exts:
                return await self._parse_image_with_structure(tmp_path)
            return await self._parse_with_marker(tmp_path)
        except Exception:
            logger.error("Lỗi phân tích nội dung tài liệu")
            return {"error": "Lỗi phân tích cú pháp tài liệu"}
        finally:
            tmp_path.unlink(missing_ok=True)

    async def _parse_with_marker(self, file_path: Path) -> Dict:
        loop = asyncio.get_event_loop()
        artifact_dict = self._get_marker_models()

        def _convert():
            from marker.config.parser import ConfigParser
            from marker.converters.pdf import PdfConverter
            from marker.output import text_from_rendered

            config = {
                "output_format": "markdown",
                "force_ocr": False,
                "paginate_output": True,
                "use_llm": True,
                "llm_service": "marker.services.ollama.OllamaService",
                "ollama_base_url": settings.OLLAMA_BASE_URL,
                "ollama_model": settings.OLLAMA_MODEL,
            }
            config_parser = ConfigParser(config)

            converter = PdfConverter(
                artifact_dict=artifact_dict,
                config=config_parser.generate_config_dict(),
                processor_list=config_parser.get_processors(),
                renderer=config_parser.get_renderer(),
                llm_service=config_parser.get_llm_service(),
            )
            rendered = converter(str(file_path))
            text, _, images = text_from_rendered(rendered)
            return text, rendered

        text, rendered = await loop.run_in_executor(None, _convert)
        markdown = text if text else ""

        chunks = self._split_markdown_to_chunks(markdown)

        page_count = 0
        if hasattr(rendered, "metadata") and rendered.metadata:
            page_count = (
                rendered.metadata.get("page_count", 0)
                if isinstance(rendered.metadata, dict)
                else 0
            )

        logger.info("Trích xuất văn bản từ tài liệu thành công")
        return {
            "markdown": markdown,
            "chunks": chunks,
            "chunk_count": len(chunks),
            "page_count": page_count,
        }

    async def extract_tables(self, file_url: str) -> List[Dict]:
        file_bytes, file_ext = await self._download_from_minio(file_url)
        if not file_bytes:
            return []

        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = Path(tmp.name)

        try:
            loop = asyncio.get_event_loop()
            artifact_dict = self._get_marker_models()

            def _extract():
                from marker.config.parser import ConfigParser
                from marker.converters.table import TableConverter
                from marker.output import text_from_rendered

                config = {
                    "output_format": "json",
                    "use_llm": True,
                    "llm_service": "marker.services.ollama.OllamaService",
                    "ollama_base_url": settings.OLLAMA_BASE_URL,
                    "ollama_model": settings.OLLAMA_MODEL,
                }
                config_parser = ConfigParser(config)

                converter = TableConverter(
                    artifact_dict=artifact_dict,
                    config=config_parser.generate_config_dict(),
                    processor_list=config_parser.get_processors(),
                    renderer=config_parser.get_renderer(),
                    llm_service=config_parser.get_llm_service(),
                )
                rendered = converter(str(tmp_path))
                text, _, _ = text_from_rendered(rendered)
                return text

            table_text = await loop.run_in_executor(None, _extract)
            tables = []
            if table_text:
                for i, block in enumerate(table_text.split("\n\n")):
                    cleaned = block.strip()
                    if cleaned and ("|" in cleaned or "<table" in cleaned.lower()):
                        tables.append(
                            {
                                "text": cleaned,
                                "chunk_type": "table",
                                "index": i,
                            }
                        )

            logger.info("Trích xuất bảng dữ liệu thành công")
            return tables
        except Exception:
            logger.error("Lỗi trích xuất bảng dữ liệu")
            return []
        finally:
            tmp_path.unlink(missing_ok=True)

    async def _parse_image_with_structure(self, file_path: Path) -> Dict:
        loop = asyncio.get_event_loop()

        def _run_structure():
            import cv2

            img = cv2.imread(str(file_path))
            if img is None:
                return None
            engine = self._get_pp_structure()
            return engine(img)

        result = await loop.run_in_executor(None, _run_structure)
        if result is None:
            return await self._parse_with_raw_ocr(file_path)

        chunks = []
        markdown_parts = []

        for block in result:
            block_type = block.get("type", "text")
            text_results = block.get("res", [])

            if block_type == "table":
                html = block.get("res", {}).get("html", "")
                if html:
                    chunks.append({"text": html, "chunk_type": "table"})
                    markdown_parts.append(html)
            elif isinstance(text_results, list):
                block_text = ""
                for line in text_results:
                    if isinstance(line, dict) and "text" in line:
                        block_text += line["text"] + "\n"
                    elif isinstance(line, (list, tuple)) and len(line) >= 2:
                        line_text = (
                            line[1][0]
                            if isinstance(line[1], (list, tuple))
                            else str(line[1])
                        )
                        block_text += line_text + "\n"
                block_text = block_text.strip()
                if len(block_text) > 10:
                    chunks.append({"text": block_text, "chunk_type": block_type})
                    if block_type == "title":
                        markdown_parts.append(f"## {block_text}")
                    else:
                        markdown_parts.append(block_text)

        if not chunks:
            return await self._parse_with_raw_ocr(file_path)

        full_markdown = "\n\n".join(markdown_parts)
        logger.info("Trích xuất cấu trúc hình ảnh thành công")
        return {
            "markdown": full_markdown,
            "chunks": chunks,
            "chunk_count": len(chunks),
        }

    async def _parse_with_raw_ocr(self, file_path: Path) -> Dict:
        loop = asyncio.get_event_loop()
        ocr = self._get_ocr_engine()

        def _run_ocr():
            return ocr.ocr(str(file_path), cls=True)

        result = await loop.run_in_executor(None, _run_ocr)

        lines = []
        if result and result[0]:
            for line_info in result[0]:
                text = line_info[1][0]
                confidence = line_info[1][1]
                if confidence > 0.5 and len(text.strip()) > 2:
                    lines.append(text.strip())

        full_text = "\n".join(lines)
        chunks = self._group_lines_to_chunks(lines)

        logger.info("Trích xuất văn bản từ hình ảnh thành công")
        return {
            "markdown": full_text,
            "chunks": chunks,
            "chunk_count": len(chunks),
        }

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

    def _group_lines_to_chunks(self, lines: List[str]) -> List[Dict]:
        chunks = []
        buffer = ""
        for line in lines:
            buffer += line + "\n"
            if len(buffer) > 300:
                chunks.append({"text": buffer.strip(), "chunk_type": "ocr"})
                buffer = ""
        if len(buffer.strip()) > 30:
            chunks.append({"text": buffer.strip(), "chunk_type": "ocr"})
        return chunks

    async def get_doc_chunks_for_ingestion(self, file_url: str) -> List[Dict]:
        parse_result = await self.parse_document(file_url)
        if parse_result.get("error"):
            logger.warning("Lỗi phân tích tài liệu")
            return []

        chunks = parse_result.get("chunks", [])

        file_ext = ""
        if "" in file_url:
            file_ext = "" + file_url.rsplit("", 1)[-1].lower()

        doc_exts = [".pdf", ".docx", ".epub", ".pptx", ".xlsx"]
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

        logger.info("Tạo phân mảnh văn bản thành công")
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
                bucket = path_parts[0] if len(path_parts) == 2 else self._bucket
                object_key = (
                    path_parts[1] if len(path_parts) == 2 else parsed.path.lstrip("/")
                )
            else:
                bucket = self._bucket
                object_key = file_url

            if "" in object_key:
                logger.error("Ngăn chặn rủi ro bảo mật")
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
                ".epub": ".epub",
                ".docx": ".docx",
                ".xlsx": ".xlsx",
                ".pptx": ".pptx",
                ".html": ".html",
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

            logger.info("Lấy nội dung tệp từ kho lưu trữ thành công")
            return data, ext

        except Exception:
            logger.error("Lỗi kết nối tải tệp")
            return None, ""


document_parser = DocumentParser()