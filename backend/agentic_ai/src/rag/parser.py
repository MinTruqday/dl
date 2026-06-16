import io
from typing import Optional
import docx
import fitz
from loguru import logger

class DocumentParser:
    @staticmethod
    def parse_pdf(file_bytes: bytes) -> Optional[str]:
        try:
            text = ""
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                for page in doc:
                    text += page.get_text("text") + "\n"
            return text.strip()
        except Exception:
            logger.error("Lỗi khi truy xuất tài liệu")
            return None

    @staticmethod
    def parse_docx(file_bytes: bytes) -> Optional[str]:
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            return "\n".join([paragraph.text for paragraph in doc.paragraphs]).strip()
        except Exception:
            logger.error("Lỗi khi truy xuất tài liệu")
            return None

    @staticmethod
    def parse_txt(file_bytes: bytes) -> Optional[str]:
        try:
            return file_bytes.decode("utf-8").strip()
        except UnicodeDecodeError:
            try:
                return file_bytes.decode("latin-1").strip()
            except Exception:
                logger.error("Lỗi khi truy xuất tài liệu")
                return None

document_parser = DocumentParser()