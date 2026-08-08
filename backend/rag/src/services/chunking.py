import re
from typing import Dict, List
from uuid6 import uuid7
from loguru import logger
from src.core.infrastructure.configuration import settings

async def _sanitize_text(text: str) -> bool:
    if not text or len(text.strip()) == 0:
        return False
    return True

class ChunkingService:
    def __init__(self):
        logger.info("Initializing ChunkingService")
        self.type = "character_structure"

    async def chunk_document(self, text: str, metadata: Dict) -> List[Dict]:
        logger.info("Processing text chunking")
        return await self._fallback_chunking(text, metadata)

    async def _fallback_chunking(self, text: str, metadata: Dict) -> List[Dict]:
        lines = text.split("\n\n")
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_idx = 0

        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                continue
            if current_length + len(trimmed) > 1000 and current_chunk:
                combined_text = "\n\n".join(current_chunk)
                if len(combined_text) >= 30 and await _sanitize_text(combined_text):
                    chunk_id = str(uuid7())[:12]
                    chunks.append({
                        "id": f"{metadata.get('document_id', 'unknown')}_{chunk_id}",
                        "text": combined_text,
                        "metadata": {
                            **metadata,
                            "chunk_id": chunk_id,
                            "chunk_index": chunk_idx,
                            "char_count": len(combined_text),
                            "word_count": len(combined_text.split()),
                            "chunk_type": self.type,
                        }
                    })
                    chunk_idx += 1
                current_chunk = [trimmed]
                current_length = len(trimmed)
            else:
                current_chunk.append(trimmed)
                current_length += len(trimmed)

        if current_chunk:
            combined_text = "\n\n".join(current_chunk)
            if len(combined_text) >= 30 and await _sanitize_text(combined_text):
                chunk_id = str(uuid7())[:12]
                chunks.append({
                    "id": f"{metadata.get('document_id', 'unknown')}_{chunk_id}",
                    "text": combined_text,
                    "metadata": {
                        **metadata,
                        "chunk_id": chunk_id,
                        "chunk_index": chunk_idx,
                        "char_count": len(combined_text),
                        "word_count": len(combined_text.split()),
                        "chunk_type": self.type,
                    }
                })

        return chunks

chunker = ChunkingService()
