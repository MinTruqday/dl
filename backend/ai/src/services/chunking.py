import math
import re
from hashlib import sha256
from typing import Dict, List, Optional, Sequence

from loguru import logger
from uuid import NAMESPACE_URL, uuid5

from src.services.embedding import embedder


class ChunkingService:
    """Docling structure -> semantic refinement -> deterministic size guard."""

    STRUCTURAL_BOUNDARIES = {"title", "section_header", "chapter", "heading"}

    def __init__(
        self,
        min_chars: int = 200,
        target_chars: int = 900,
        max_chars: int = 1600,
        semantic_threshold: float = 0.55,
        soft_threshold: float = 0.72,
    ):
        if not 0 < min_chars <= target_chars <= max_chars:
            raise ValueError("chunk_size_bounds_invalid")
        self.min_chars = min_chars
        self.target_chars = target_chars
        self.max_chars = max_chars
        self.semantic_threshold = semantic_threshold
        self.soft_threshold = soft_threshold
        logger.info("Initializing unified document ChunkingService")

    async def chunk_document(
        self, markdown: str, metadata: Dict, structure: Optional[List[Dict]] = None
    ) -> List[Dict]:
        units = self._structure_units(markdown, structure or [])
        if not units:
            return []

        texts = [unit["text"] for unit in units]
        try:
            embeddings = await embedder.embed_batch(texts)
            if len(embeddings) != len(units):
                raise ValueError("semantic_embedding_count_mismatch")
            semantic_groups = self._semantic_refinement(units, embeddings)
            chunk_type = "docling_structure_semantic"
        except Exception as error:
            logger.warning(
                "Semantic refinement failed; preserving Docling boundaries ({})",
                type(error).__name__,
            )
            semantic_groups = self._structural_groups(units)
            chunk_type = "docling_structure_fallback"

        guarded_groups = self._size_guard(semantic_groups)
        return self._serialize_groups(guarded_groups, metadata, chunk_type)

    def _structure_units(self, markdown: str, structure: List[Dict]) -> List[Dict]:
        units = []
        previous_text = None
        for item in structure:
            text = str(item.get("text") or "").strip()
            if not text or text == previous_text:
                continue
            item_type = str(item.get("type") or "text").casefold()
            units.append(
                {
                    "text": text,
                    "type": item_type,
                    "level": item.get("level"),
                    "page_no": item.get("page_no"),
                    "hard_boundary": item_type in self.STRUCTURAL_BOUNDARIES,
                }
            )
            previous_text = text
        if units:
            return units

        return [
            {
                "text": text,
                "type": item_type,
                "level": None,
                "page_no": None,
                "hard_boundary": item_type == "section_header",
            }
            for text, item_type in self._markdown_units(markdown)
        ]

    @staticmethod
    def _markdown_units(markdown: str) -> List[tuple[str, str]]:
        units = []
        for part in re.split(r"\n\s*\n+", markdown):
            text = part.strip()
            if not text:
                continue
            item_type = "section_header" if re.match(r"^#{1,6}\s+", text) else "text"
            units.append((text, item_type))
        return units

    @staticmethod
    def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
        if len(left) != len(right) or not left:
            raise ValueError("semantic_embedding_dimension_mismatch")
        dot_product = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return dot_product / (left_norm * right_norm)

    def _semantic_refinement(
        self, units: List[Dict], embeddings: List[List[float]]
    ) -> List[List[Dict]]:
        groups: List[List[Dict]] = []
        current = [units[0]]
        current_length = len(units[0]["text"])

        for index, unit in enumerate(units[1:], start=1):
            similarity = self._cosine_similarity(embeddings[index - 1], embeddings[index])
            topic_changed = similarity < self.semantic_threshold
            soft_boundary = current_length >= self.target_chars and similarity < self.soft_threshold
            structure_boundary = unit["hard_boundary"]
            should_split = current_length >= self.min_chars and (
                structure_boundary or topic_changed or soft_boundary
            )
            if should_split:
                groups.append(current)
                current = [unit]
                current_length = len(unit["text"])
            else:
                current.append(unit)
                current_length += len(unit["text"]) + 2
        groups.append(current)
        return groups

    def _structural_groups(self, units: List[Dict]) -> List[List[Dict]]:
        groups: List[List[Dict]] = []
        current: List[Dict] = []
        current_length = 0
        for unit in units:
            if current and unit["hard_boundary"] and current_length >= self.min_chars:
                groups.append(current)
                current = []
                current_length = 0
            current.append(unit)
            current_length += len(unit["text"]) + (2 if current_length else 0)
        if current:
            groups.append(current)
        return groups

    def _size_guard(self, groups: List[List[Dict]]) -> List[List[Dict]]:
        guarded: List[List[Dict]] = []
        for group in groups:
            current: List[Dict] = []
            current_length = 0
            for unit in group:
                for bounded_unit in self._split_oversized_unit(unit):
                    projected = current_length + len(bounded_unit["text"]) + (2 if current else 0)
                    if current and projected > self.max_chars:
                        guarded.append(current)
                        current = [bounded_unit]
                        current_length = len(bounded_unit["text"])
                    else:
                        current.append(bounded_unit)
                        current_length = projected
            if current:
                guarded.append(current)
        return guarded

    def _split_oversized_unit(self, unit: Dict) -> List[Dict]:
        text = unit["text"]
        if len(text) <= self.max_chars:
            return [unit]

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?。！？])\s+", text)
            if sentence.strip()
        ]
        pieces: List[str] = []
        current = ""
        for sentence in sentences or [text]:
            if len(sentence) > self.max_chars:
                if current:
                    pieces.append(current)
                    current = ""
                pieces.extend(
                    sentence[start : start + self.max_chars]
                    for start in range(0, len(sentence), self.max_chars)
                )
            elif current and len(current) + len(sentence) + 1 > self.max_chars:
                pieces.append(current)
                current = sentence
            else:
                current = f"{current} {sentence}".strip()
        if current:
            pieces.append(current)
        return [{**unit, "text": piece} for piece in pieces]

    @staticmethod
    def _serialize_groups(groups: List[List[Dict]], metadata: Dict, chunk_type: str) -> List[Dict]:
        chunks = []
        for chunk_index, group in enumerate(groups):
            text = "\n\n".join(unit["text"] for unit in group).strip()
            if not text:
                continue
            identity = ":".join(
                [
                    str(metadata.get("document_id") or ""),
                    str(metadata.get("source_version") or ""),
                    str(chunk_index),
                    sha256(text.encode()).hexdigest(),
                ]
            )
            chunk_id = str(uuid5(NAMESPACE_URL, identity))
            chunks.append(
                {
                    "id": chunk_id,
                    "text": text,
                    "metadata": {
                        **metadata,
                        "chunk_id": chunk_id,
                        "chunk_index": chunk_index,
                        "char_count": len(text),
                        "word_count": len(text.split()),
                        "chunk_type": chunk_type,
                        "structure_types": list(dict.fromkeys(unit["type"] for unit in group)),
                    },
                }
            )
        return chunks


chunker = ChunkingService()
