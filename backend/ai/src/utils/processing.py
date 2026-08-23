import base64

from loguru import logger
from src.clients.rag import rag_client

async def extract_text_from_base64(
    base64_data: str,
    filename: str = "attachment.pdf",
) -> str:
    """Decode plain text locally and delegate document conversion to RAG."""
    try:
        media_type = ""
        payload = base64_data
        if "," in base64_data:
            header, payload = base64_data.split(",", 1)
            media_type = header.removeprefix("data:").split(";", 1)[0].lower()

        if media_type.startswith("text/") or media_type in {
            "application/json",
            "application/xml",
            "application/javascript",
        }:
            file_bytes = base64.b64decode(payload, validate=True)
            return file_bytes.decode("utf-8", errors="replace")

        logger.info("Delegating attachment conversion to knowledge service")
        return await rag_client.extract_attachment(base64_data, filename)
    except Exception:
        logger.exception("File text extraction error")
        return ""
