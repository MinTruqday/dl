import base64
import binascii
from loguru import logger
from src.rag.parser import document_parser

def extract_text_from_base64(b64_string: str) -> str:
    try:
        if "," in b64_string:
            header, encoded = b64_string.split(",", 1)
        else:
            encoded = b64_string
            
        file_bytes = base64.b64decode(encoded)
        
        if file_bytes.startswith(b"%PDF"):
            return document_parser.parse_pdf(file_bytes) or ""
        elif file_bytes.startswith(b"PK\x03\x04"):
            return document_parser.parse_docx(file_bytes) or ""
        else:
            return document_parser.parse_txt(file_bytes) or ""
    except binascii.Error:
        logger.error("Lỗi khi truy xuất tài liệu")
        return ""
    except Exception:
        logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
        return ""