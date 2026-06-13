import re


def _sanitize_text(text: str) -> bool:
    pattern = r"(?i)(ignore all previous instructions|bỏ qua mọi lệnh|bypass|jailbreak|bạn đã bị hack|print out|forget the previous)"
    if re.search(pattern, text):
        return False
    return True


import re
import uuid

from uuid6 import uuid7


def _sanitize_text(text: str) -> bool:
    pattern = r"(?i)(ignore all previous instructions|bỏ qua mọi lệnh|bypass|jailbreak|bạn đã bị hack|print out|forget the previous)"
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
        logger.info("Initializing Chonkie Chunkers")
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
                logger.info(f"Loaded Chonkie SemanticChunker with {model_name}")
            except Exception as e:
                logger.warning(
                    f"Tải Chonkie SemanticChunker thất bại: {e}. Đang chuyển sang dự phòng TokenChunker"
                )
                try:
                    self.chunker = TokenChunker(
                        chunk_size=settings.DEFAULT_CHUNK_SIZE,
                        chunk_overlap=settings.DEFAULT_CHUNK_OVERLAP,
                    )
                    self.type = "chonkie_token"
                    logger.info("Loaded Chonkie TokenChunker")
                except Exception as e2:
                    logger.error(f"Chonkie TokenChunker thất bại: {e2}")

    def chunk_document(self, text: str, metadata: Dict) -> List[Dict]:
        logger.info(f"Chunking text of length {len(text)}")

        if not self.chunker:
            logger.warning(
                "Đang sử dụng dự phòng Langchain CharSplit do lỗi khởi tạo Chonkie"
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
                f"Hoàn thành phân nhỏ bằng Chonkie với số lượng: {len(chunks)}, loại: {self.type}"
            )
            return chunks

        except Exception as e:
            logger.error(f"Chạy Chonkie gặp lỗi: {e}. Đang sử dụng dự phòng")
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
