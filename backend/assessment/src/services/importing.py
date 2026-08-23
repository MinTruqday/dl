import hashlib
import re
from typing import Any

from src.services.validation import text_projection


QUESTION_BOUNDARY = re.compile(r"(?im)^\s*(?:câu|question|q)\s*(\d+)\s*[\.:\)]\s*")
OPTION_BOUNDARY = re.compile(r"(?im)^\s*([A-H])\s*[\.:\)]?\s+(.+)$")


def tiptap_doc(text: str):
    return {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text.strip()}] if text.strip() else [],
            }
        ],
    }


def split_page(page: dict[str, Any]):
    text = page.get("text", "")
    matches = [
        {"start": match.start(), "end": match.end(), "number": match.group(1)}
        for match in QUESTION_BOUNDARY.finditer(text)
    ]
    if not matches and text.strip():
        matches = [{"start": 0, "end": 0, "number": "1"}]
    candidates = []
    for index, match in enumerate(matches):
        start = match["end"]
        end = matches[index + 1]["start"] if index + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        option_matches = list(OPTION_BOUNDARY.finditer(block))
        stem_end = option_matches[0].start() if option_matches else len(block)
        stem = block[:stem_end].strip()
        options = [
            {"id": option.group(1), "content_doc": tiptap_doc(option.group(2).strip())}
            for option in option_matches
        ]
        source_number = match["number"]
        digest = hashlib.sha256(f"{page['page_number']}:{source_number}:{stem}".encode()).hexdigest()
        candidates.append(
            {
                "candidate_id": f"IMPQ-{digest[:24]}",
                "source_number": source_number,
                "source_page": page["page_number"],
                "question_type": "single_choice" if options else "short_answer",
                "authoring_source": "import",
                "stem_doc": tiptap_doc(stem),
                "options": options,
                "answer_key": {},
                "solution_doc": tiptap_doc(""),
                "scoring_rule": {"points": 1},
                "curriculum_links": [],
                "concept_ids": [],
                "skill_ids": [],
                "tags": [],
                "construct": {},
                "source_evidence": [
                    {
                        "document_id": page.get("document_id"),
                        "source_page": page["page_number"],
                        "image_refs": page.get("image_refs", []),
                        "formula_refs": page.get("formula_refs", []),
                    }
                ],
                "parse_confidence": parse_confidence(stem, options, page),
                "needs_teacher_review": True,
                "recognized": bool(stem),
            }
        )
    return candidates


def parse_confidence(stem: str, options: list[dict[str, Any]], page: dict[str, Any]):
    score = 0.35
    if len(stem) >= 10:
        score += 0.25
    if len(options) >= 2:
        score += 0.2
    if page.get("formula_refs") or page.get("image_refs"):
        score += 0.05
    return round(min(score, 0.95), 3)


def candidate_projection(candidate: dict[str, Any]):
    return text_projection(candidate.get("stem_doc", {})).casefold().strip()


def duplicate_fingerprint(candidate: dict[str, Any]):
    return hashlib.sha256(candidate_projection(candidate).encode()).hexdigest()


def structure_pages(document_id: str, markdown: str, structure: list[dict[str, Any]]):
    grouped: dict[int, dict[str, Any]] = {}
    for element in structure:
        page_number = max(1, int(element.get("page_no") or 1))
        page = grouped.setdefault(
            page_number,
            {"page_number": page_number, "text_parts": [], "image_refs": [], "formula_refs": []},
        )
        text = str(element.get("text") or "").strip()
        if text:
            page["text_parts"].append(text)
        element_type = str(element.get("type") or "").casefold()
        if any(value in element_type for value in ["formula", "equation"]):
            page["formula_refs"].append({"latex": text or None, "source_page": page_number})
        if any(value in element_type for value in ["picture", "image", "figure"]):
            page["image_refs"].append({"url": None, "source_page": page_number, "label": text or None})
    if not grouped:
        grouped[1] = {"page_number": 1, "text_parts": [markdown], "image_refs": [], "formula_refs": []}
    return [
        {
            "document_id": document_id,
            "page_number": number,
            "text": "\n".join(page["text_parts"]).strip(),
            "image_refs": page["image_refs"],
            "formula_refs": page["formula_refs"],
        }
        for number, page in sorted(grouped.items())
    ]
