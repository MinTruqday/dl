from typing import List
from core.config import settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger

class DocumentChunker:
    def __init__(self):
        self.chunk_size = settings.DEFAULT_CHUNK_SIZE
        self.chunk_overlap = settings.DEFAULT_CHUNK_OVERLAP
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
        )

    def split_text(self, text: str) -> List[str]:
        try:
            if not text or not text.strip():
                return []
            chunks = self.splitter.split_text(text)
            logger.info("Phân tích tài liệu hoàn tất")
            return chunks
        except Exception:
            logger.error("Lỗi khi truy xuất tài liệu")
            return []

document_chunker = DocumentChunker()