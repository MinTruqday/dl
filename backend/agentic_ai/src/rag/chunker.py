import re


def _sanitize_text(text: str) -> bool:
    pattern = r"(?i)(ignore all previous instructions|bypass|jailbreak|you have been hacked|print out|forget the previous)"
    if re.search(pattern, text):
        return False
    return True


import re
import uuid

from uuid6 import uuid7


def _sanitize_text(text: str) -> bool:
    pattern = r"(?i)(ignore all previous instructions|bypass|jailbreak|you have been hacked|print out|forget the previous)"
    if re.search(pattern, text):
        return False
    return True


from typing import Dict, List

from core.config import settings
from loguru import logger

try:
    from chonkie import SemanticChunker, TokenChunker

    HAS_CHONKIE = True
except ImportError:
    HAS_CHONKIE = False


class AdvancedSemanticChunker:
    def __init__(self):
        logger.info("Đang khởi tạo hệ thống phân mảnh văn bản")
        self.chunker = None
        self.type = "fallback"

        if HAS_CHONKIE:
            try:
                model_name = settings.EMBEDDING_MODEL
                self.chunker = SemanticChunker(
                    embedding_model=model_name,
                    chunk_size=settings.DEFAULT_CHUNK_SIZE,
                    similarity_threshold=0.5,
                )
                self.type = "chonkie_semantic"
                logger.info("Khởi tạo công cụ phân mảnh ngữ nghĩa thành công")
            except Exception:
                logger.warning(
                    "Lỗi khởi tạo hệ thống phân mảnh văn bản, đang dùng chế độ tiêu chuẩn"
                )
                try:
                    self.chunker = TokenChunker(
                        chunk_size=settings.DEFAULT_CHUNK_SIZE,
                        chunk_overlap=settings.DEFAULT_CHUNK_OVERLAP,
                    )
                    self.type = "chonkie_token"
                    logger.info("Tải công cụ phân đoạn văn bản thành công")
                except Exception:
                    logger.error("Lỗi khởi tạo hệ thống phân mảnh văn bản")

    def chunk_document(self, text: str, metadata: Dict) -> List[Dict]:
        logger.info("Đang xử lý phân đoạn văn bản")

        if not self.chunker:
            logger.warning(
                "Đang dùng phương pháp phân mảnh thay thế"
            )
            return self._fallback_chunking(text, metadata)

        try:
            chonkie_chunks = self.chunker.chunk(text)
            chunks = []

            for i, chunk_obj in enumerate(chonkie_chunks):
                chunk_text = chunk_obj.text.strip()
                if len(chunk_text) < 30 or not _sanitize_text(chunk_text):
                    continue

                chunk_id = str(uuid7())[:12]
                chunk_meta = {
                    **metadata,
                    "chunk_id": chunk_id,
                    "chunk_index": i,
                    "char_count": len(chunk_text),
                    "word_count": len(chunk_text.split()),
                    "chunk_type": self.type,
                }

                chunks.append(
                    {
                        "id": f"{metadata.get('document_id', 'unknown')}_{chunk_id}",
                        "text": chunk_text,
                        "metadata": chunk_meta,
                    }
                )

            logger.info(
                "Xử lý phân mảnh văn bản thành công"
            )
            return chunks

        except Exception:
            logger.error("Lỗi phân mảnh văn bản, đang chuyển sang phương pháp thay thế")
            return self._fallback_chunking(text, metadata)

    def _fallback_chunking(self, text: str, metadata: Dict) -> List[Dict]:
        from langchain_text_splitters import (
            MarkdownHeaderTextSplitter,
            RecursiveCharacterTextSplitter,
        )

        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        try:
            markdown_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=headers_to_split_on
            )
            md_documents = markdown_splitter.split_text(text)
            texts = [doc.page_content for doc in md_documents]
        except Exception:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.DEFAULT_CHUNK_SIZE,
                chunk_overlap=settings.DEFAULT_CHUNK_OVERLAP,
            )
            texts = splitter.split_text(text)

        chunks = []
        for i, chunk_text in enumerate(texts):
            clean_text = chunk_text.strip()
            if len(clean_text) < 30 or not _sanitize_text(clean_text):
                continue
            chunk_id = str(uuid7())[:12]

            chunks.append(
                {
                    "id": f"{metadata.get('document_id', 'unknown')}_{chunk_id}",
                    "text": clean_text,
                    "metadata": {
                        **metadata,
                        "chunk_id": chunk_id,
                        "chunk_index": i,
                        "chunk_type": "markdown_structure",
                    },
                }
            )

        return chunks


chunker = AdvancedSemanticChunker()