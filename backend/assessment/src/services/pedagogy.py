from __future__ import annotations

import re
from collections import Counter
from typing import Any


SIGNALS = {
    "worked_example": ("ví dụ", "bài mẫu", "mẫu giải", "lời giải mẫu", "minh họa"),
    "step_by_step": ("từng bước", "bước 1", "bước đầu", "quy trình", "các bước"),
    "concept_first": ("định nghĩa", "tính chất", "nhận xét", "kiến thức trọng tâm"),
    "visual_representation": ("sơ đồ", "hình vẽ", "trực quan", "biểu diễn", "đồ thị"),
    "multiple_methods": ("cách 1", "cách 2", "nhiều cách", "phương pháp khác", "cách giải khác"),
    "misconception_guard": ("lỗi sai", "sai lầm", "dễ nhầm", "nhầm lẫn", "lưu ý"),
    "competition_extension": ("học sinh giỏi", "olympic", "quốc tế", "nâng cao", "thách thức"),
}

VARIATION_DIRECTIVES = (
    "đổi ngữ cảnh nhưng giữ nguyên mục tiêu kiến thức",
    "đổi dạng biểu diễn như lời văn công thức bảng hoặc hình",
    "kiểm tra một lỗi sai hoặc ngộ nhận thường gặp",
    "yêu cầu giải thích hoặc biện luận thay vì chỉ tính kết quả",
    "kết hợp hai kỹ năng đã có trong cùng chủ đề",
    "mở rộng theo hướng học sinh giỏi nhưng không vượt prerequisite đã xác nhận",
)


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_text(item) for item in value)
    return ""


def _signal_counts(text: str) -> Counter[str]:
    normalized = re.sub(r"\s+", " ", text.casefold()).strip()
    return Counter(
        signal
        for signal, markers in SIGNALS.items()
        if any(marker in normalized for marker in markers)
    )


def build_pedagogical_context(evidence: list[dict[str, Any]]) -> dict[str, Any]:
    teacher_chunks = [item for item in evidence if item.get("source_type") == "teacher_material"]
    if not teacher_chunks:
        return {
            "source_mode": "curriculum_only",
            "teacher_material_present": False,
            "teacher_material_chunk_count": 0,
            "signals": [],
            "preferred_solution_patterns": [],
            "presentation_preferences": [],
            "misconception_focus": [],
            "extension_focus": [],
            "confidence": 0.0,
        }

    counts: Counter[str] = Counter()
    content_types: Counter[str] = Counter()
    for item in teacher_chunks:
        counts.update(_signal_counts(_text(item.get("text", ""))))
        content_type = item.get("content_type")
        if content_type:
            content_types[str(content_type)] += 1

    signals = [signal for signal, count in counts.most_common() if count > 0]
    solution_patterns = [
        signal
        for signal in signals
        if signal in {"worked_example", "step_by_step", "multiple_methods"}
    ]
    presentation_preferences = [
        signal for signal in signals if signal in {"concept_first", "visual_representation"}
    ]
    misconception_focus = [signal for signal in signals if signal == "misconception_guard"]
    extension_focus = [signal for signal in signals if signal == "competition_extension"]
    evidence_count = len(teacher_chunks)
    signal_count = sum(counts.values())
    confidence = min(0.95, 0.4 + min(evidence_count, 6) * 0.05 + min(signal_count, 6) * 0.04)
    return {
        "source_mode": "curriculum_and_teacher_material",
        "teacher_material_present": True,
        "teacher_material_chunk_count": evidence_count,
        "signals": signals,
        "signal_counts": dict(counts),
        "content_types": dict(content_types),
        "preferred_solution_patterns": solution_patterns,
        "presentation_preferences": presentation_preferences,
        "misconception_focus": misconception_focus,
        "extension_focus": extension_focus,
        "confidence": round(confidence, 3),
    }


def variation_directive(position: int, pedagogical_context: dict[str, Any]) -> str:
    directives = list(VARIATION_DIRECTIVES)
    if pedagogical_context.get("extension_focus"):
        directives = [directives[-1], *directives[:-1]]
    if pedagogical_context.get("misconception_focus"):
        directives = [directives[2], *[item for item in directives if item != directives[2]]]
    return directives[(max(position, 1) - 1) % len(directives)]
