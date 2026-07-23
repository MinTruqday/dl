import base64
import os
import tempfile
from pathlib import Path

from loguru import logger
from src.rag.conversion import document_parser

def extract_text_from_base64(base64_data: str, filename: str = "temp_file") -> str:
    try:
        if "," in base64_data:
            base64_data = base64_data.split(",")[1]

        file_bytes = base64.b64decode(base64_data)

        ext = os.path.splitext(filename)[1] or ".pdf"

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = Path(tmp.name)

        try:
            logger.info("Extracting text content using Docling")
            res = document_parser._parse_file_with_docling(tmp_path)
            full_text = res.get("markdown", "")
            logger.info("Text extraction successful")
            return full_text
        finally:
            tmp_path.unlink(missing_ok=True)
    except Exception as e:
        logger.exception("File text extraction error")
        return ""
