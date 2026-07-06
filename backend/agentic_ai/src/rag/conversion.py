import asyncio
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import boto3
from loguru import logger

from src.core.infrastructure.configuration import settings

MODEL_ID = "datalab-to/chandra-ocr-2"
MAX_OUTPUT_TOKENS = 12384

class _ChandraModel:
    def __init__(self):
        from transformers import AutoProcessor, AutoModelForImageTextToText, BitsAndBytesConfig
        import torch

        quant_config = BitsAndBytesConfig(load_in_8bit=True)

        self.processor = AutoProcessor.from_pretrained(MODEL_ID)
        self.model = AutoModelForImageTextToText.from_pretrained(
            MODEL_ID,
            device_map="auto",
            quantization_config=quant_config,
            torch_dtype=torch.float16,
        )
        self.model.eval()

        import torch
        self.device = next(self.model.parameters()).device

    def generate(self, conversations: List[List[dict]]) -> List[str]:
        import torch

        inputs = self.processor.apply_chat_template(
            conversations,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
            padding=True,
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        eos_token_id = self.model.generation_config.eos_token_id
        im_end_id = self.processor.tokenizer.convert_tokens_to_ids("<|im_end|>")
        if isinstance(eos_token_id, int):
            eos_token_id = [eos_token_id]
        if im_end_id is not None and im_end_id not in eos_token_id:
            eos_token_id = eos_token_id + [im_end_id]

        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=MAX_OUTPUT_TOKENS,
                eos_token_id=eos_token_id,
                do_sample=False,
            )

        input_len = inputs["input_ids"].shape[1]
        results = []
        for ids in output_ids:
            decoded = self.processor.tokenizer.decode(
                ids[input_len:], skip_special_tokens=True
            )
            results.append(decoded)
        return results

def _build_conversation(image) -> List[dict]:
    return [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {
                    "type": "text",
                    "text": "Convert this document page to markdown. Preserve all structure including tables, headings, lists, and equations. Output only the markdown content.",
                },
            ],
        }
    ]

def _pdf_to_images(file_path: Path) -> List:
    import pypdfium2 as pdfium
    from PIL import Image as PILImage

    doc = pdfium.PdfDocument(str(file_path))
    images = []
    for i in range(len(doc)):
        page = doc[i]
        bitmap = page.render(scale=2.0)
        pil_img = bitmap.to_pil()
        images.append(pil_img)
    doc.close()
    return images

def _image_file_to_pil(file_path: Path):
    from PIL import Image as PILImage

    img = PILImage.open(str(file_path)).convert("RGB")
    return img

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
        self._chandra: Optional[_ChandraModel] = None
        logger.info("Khởi tạo công cụ phân tích tài liệu thành công")

    def _get_chandra(self) -> _ChandraModel:
        if self._chandra is None:
            logger.info("Tải mô hình Chandra OCR 2 (8-bit)")
            self._chandra = _ChandraModel()
            logger.info("Tải mô hình Chandra OCR 2 thành công")
        return self._chandra

    def _run_chandra_on_images(self, images: List) -> List[str]:
        chandra = self._get_chandra()
        conversations = [_build_conversation(img) for img in images]
        return chandra.generate(conversations)

    async def parse_document(self, file_url: str) -> Dict:
        file_bytes, file_ext = await self._download_from_minio(file_url)
        if not file_bytes:
            return {"error": "File load failed"}

        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = Path(tmp.name)

        try:
            image_exts = [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"]
            if file_ext in image_exts:
                return await self._parse_image_with_chandra(tmp_path)
            return await self._parse_pdf_with_chandra(tmp_path)
        except Exception as e:
            logger.exception("Lỗi phân tích nội dung tài liệu")
            return {"error": f"Lỗi phân tích cú pháp tài liệu: {e}"}
        finally:
            tmp_path.unlink(missing_ok=True)

    async def _parse_pdf_with_chandra(self, file_path: Path) -> Dict:
        loop = asyncio.get_event_loop()

        def _convert():
            images = _pdf_to_images(file_path)
            if not images:
                return [], 0
            page_markdowns = self._run_chandra_on_images(images)
            return page_markdowns, len(images)

        page_markdowns, page_count = await loop.run_in_executor(None, _convert)

        markdown = "\n\n---\n\n".join(page_markdowns)
        chunks = self._split_markdown_to_chunks(markdown)

        logger.info("Trích xuất văn bản từ tài liệu thành công")
        return {
            "markdown": markdown,
            "chunks": chunks,
            "chunk_count": len(chunks),
            "page_count": page_count,
        }

    async def _parse_image_with_chandra(self, file_path: Path) -> Dict:
        loop = asyncio.get_event_loop()

        def _convert():
            img = _image_file_to_pil(file_path)
            results = self._run_chandra_on_images([img])
            return results[0] if results else ""

        markdown = await loop.run_in_executor(None, _convert)
        chunks = self._split_markdown_to_chunks(markdown)

        logger.info("Trích xuất văn bản từ hình ảnh thành công")
        return {
            "markdown": markdown,
            "chunks": chunks,
            "chunk_count": len(chunks),
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

            def _extract():
                image_exts = [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"]
                if file_ext in image_exts:
                    images = [_image_file_to_pil(tmp_path)]
                else:
                    images = _pdf_to_images(tmp_path)
                if not images:
                    return []
                chandra = self._get_chandra()
                all_tables = []
                for img in images:
                    conversations = [[{
                        "role": "user",
                        "content": [
                            {"type": "image", "image": img},
                            {
                                "type": "text",
                                "text": "Extract all tables from this document page and output them as HTML <table> elements only. If there are no tables, output an empty string.",
                            },
                        ],
                    }]]
                    results = chandra.generate(conversations)
                    if results and results[0].strip():
                        tables = _extract_tables_from_html(results[0])
                        all_tables.extend(tables)
                return all_tables

            tables = await loop.run_in_executor(None, _extract)
            logger.info("Trích xuất bảng dữ liệu thành công")
            return tables
        except Exception as e:
            logger.exception("Lỗi trích xuất bảng dữ liệu")
            return []
        finally:
            tmp_path.unlink(missing_ok=True)

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
            logger.warning("Lỗi phân tích tài liệu")
            return []

        chunks = parse_result.get("chunks", [])

        file_ext = ""
        if "." in file_url:
            file_ext = "." + file_url.rsplit(".", 1)[-1].lower()

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
                object_key = path_parts[1] if len(path_parts) == 2 else parsed.path.lstrip("/")
            else:
                object_key = file_url
                
            bucket = self._minio_private_bucket if object_key.startswith("system/") else self._minio_public_bucket

            if ".." in object_key:
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

        except Exception as e:
            logger.exception("Lỗi kết nối tải tệp")
            return None, ""

document_parser = ConversionRag()
