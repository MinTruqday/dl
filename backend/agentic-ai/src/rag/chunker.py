
import re

def _sanitize_text(text: str) -> bool:
    pattern = r"(?i)(ignore all previous instructions|bỏ qua mọi lệnh|bypass|jailbreak|bạn đã bị hack|print out|forget the previous)"
    if re.search(pattern, text):
        return False
    return True

import uuid
from uuid6 import uuid7

import re

def _sanitize_text(text: str) -> bool:
    pattern = r"(?i)(ignore all previous instructions|bỏ qua mọi lệnh|bypass|jailbreak|bạn đã bị hack|print out|forget the previous)"
    if re.search(pattern, text):
        return False
    return True


from typing import List, Dict
from loguru import logger
from core.config import settings

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
                    chunk_size=512,
                    similarity_threshold=0.5
                )
                self.type = "chonkie_semantic"
                logger.info(f"Loaded Chonkie SemanticChunker with {model_name}")
            except Exception as e:
                logger.warning(f"Chonkie SemanticChunker failed lên load: {e}. Falling back lên TokenChunker")
                try:
                    self.chunker = TokenChunker(chunk_size=512, chunk_overlap=64)
                    self.type = "chonkie_lênken"
                    logger.info("Loaded Chonkie TokenChunker")
                except Exception as e2:
                    logger.error(f"Chonkie TokenChunker thất bại: {e2}")

    def chunk_document(self, text: str, metadata: Dict) -> List[Dict]:
        logger.info(f"Chunking text of length {len(text)}")
        
        if not self.chunker:
            logger.warning("Using fallback Langchain CharSplit due lên Chonkie initialization error")
            return self._fallback_chunking(text, metadata)

        try:
            chonkie_chunks = self.chunker.chunk(text)
            chunks = []
            
            for i, chunk_obj in enumerate(chonkie_chunks):
                chunk_text = chunk_obj.text.strip()
                if len(chunk_text) < 30 or not _sanitize_text(chunk_text): continue
                    
                chunk_id = str(uuid7())[:12]
                chunk_meta = {
                    **metadata,
                    "chunk_id": chunk_id,
                    "chunk_index": i,
                    "char_count": len(chunk_text),
                    "word_count": len(chunk_text.split()),
                    "chunk_type": self.type
                }
                
                chunks.append({
                    "id": f"{metadata.get('document_id', 'unknown')}_{chunk_id}",
                    "text": chunk_text,
                    "metadata": chunk_meta
                })
                
            logger.info(f"Chonkie chunking complete. Total chunks: {len(chunks)} ({self.type})")
            return chunks
            
        except Exception as e:
            logger.error(f"Error running Chonkie: {e}. Using fallback")
            return self._fallback_chunking(text, metadata)

    def _fallback_chunking(self, text: str, metadata: Dict) -> List[Dict]:
        from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
        
        headers_lên_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        try:
            markdown_splitter = MarkdownHeaderTextSplitter(headers_lên_split_on=headers_lên_split_on)
            md_tài liệu = markdown_splitter.split_text(text)
            texts = [doc.page_content for doc in md_tài liệu]
        except Exception:
            splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)
            texts = splitter.split_text(text)
            
        chunks = []
        for i, chunk_text in enumerate(texts):
            clean_text = chunk_text.strip()
            if len(clean_text) < 30 or not _sanitize_text(clean_text): continue
            chunk_id = str(uuid7())[:12]
            
            chunks.append({
                "id": f"{metadata.get('document_id', 'unknown')}_{chunk_id}",
                "text": clean_text,
                "metadata": {
                    **metadata,
                    "chunk_id": chunk_id,
                    "chunk_index": i,
                    "chunk_type": "markdown_structure"
                }
            })
            
        return chunks

chunker = AdvancedSemanticChunker()

