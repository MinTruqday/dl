from typing import Any

from src.services.importing import tiptap_doc


def generated_question(payload: dict[str, Any], position: int, difficulty: float, model_output: dict[str, Any] | None = None):
    topic = payload["topic"].strip()
    question_type = payload["question_type"]
    stem = f"Chọn nhận định phù hợp nhất về {topic} trong ngữ cảnh đã cho"
    options = []
    answer_key: dict[str, Any] = {}
    if question_type in {"single_choice", "multiple_choice"}:
        options = [
            {"id": "A", "content_doc": tiptap_doc(f"Nhận định đúng về {topic}")},
            {"id": "B", "content_doc": tiptap_doc(f"Nhận định chưa đầy đủ về {topic}")},
            {"id": "C", "content_doc": tiptap_doc(f"Nhận định không liên quan đến {topic}")},
            {"id": "D", "content_doc": tiptap_doc(f"Nhận định trái với bằng chứng về {topic}")},
        ]
        answer_key = {"option_id": "A"} if question_type == "single_choice" else {"option_ids": ["A"]}
    elif question_type == "true_false":
        stem = f"Nhận định cốt lõi về {topic} là đúng hay sai"
        answer_key = {"value": True}
    elif question_type == "matching":
        options = [
            {"id": "A", "content_doc": tiptap_doc(f"Khái niệm thứ nhất về {topic}")},
            {"id": "B", "content_doc": tiptap_doc(f"Khái niệm thứ hai về {topic}")},
        ]
        answer_key = {"pairs": {"A": "1", "B": "2"}}
    elif question_type == "ordering":
        options = [
            {"id": "A", "content_doc": tiptap_doc(f"Bước đầu của {topic}")},
            {"id": "B", "content_doc": tiptap_doc(f"Bước tiếp theo của {topic}")},
        ]
        answer_key = {"order": ["A", "B"]}
    elif question_type == "numeric":
        stem = f"Nhập giá trị kết quả cho bài toán số {position} về {topic}"
        answer_key = {"value": position, "tolerance": 0}
    elif question_type in {"symbolic_math", "short_answer"}:
        answer_key = {"accepted": [topic.casefold()]}
    else:
        answer_key = {}
    if model_output:
        stem = str(model_output["stem"])
        options = [
            {"id": str(option["id"]), "content_doc": tiptap_doc(str(option["text"]))}
            for option in model_output.get("options", [])
        ]
        answer_key = model_output.get("answer_key", {})
    primary_concept = str(model_output.get("primary_concept")) if model_output else payload.get("concept_ids", [topic])[0] if payload.get("concept_ids") else topic
    primary_skill = str(model_output.get("primary_skill")) if model_output else payload.get("skill_ids", ["reasoning"])[0] if payload.get("skill_ids") else "reasoning"
    concept_ids = payload.get("concept_ids") or ([primary_concept] if primary_concept else [])
    skill_ids = payload.get("skill_ids") or ([primary_skill] if primary_skill else [])
    construct = {
        "primary_concept": primary_concept,
        "primary_skill": primary_skill,
        "learning_objective": str(model_output.get("learning_objective")) if model_output else topic,
        "reasoning_steps": max(1, round(difficulty)),
    }
    return {
        "question_type": question_type,
        "authoring_source": "ai_generated",
        "stem_doc": tiptap_doc(stem),
        "options": options,
        "answer_key": answer_key,
        "solution_doc": tiptap_doc(str(model_output.get("solution")) if model_output else f"Đáp án được ràng buộc bởi bằng chứng chương trình học về {topic}"),
        "scoring_rule": {"points": 1},
        "curriculum_links": [
            {
                "education_level": payload["education_level"],
                "target_program": payload["target_program"],
                "subject": payload["subject"],
                "topic": topic,
                "chapter_id": payload.get("chapter_id"),
                "lesson_id": payload.get("lesson_id"),
            }
        ],
        "concept_ids": concept_ids,
        "skill_ids": skill_ids,
        "tags": payload.get("tags", []),
        "cognitive_level": payload.get("cognitive_level") or "understanding",
        "construct": construct,
        "source_evidence": payload.get("source_evidence", []),
        "locked": False,
        "generation_provenance": {
            "generator": "ai_rag_structured_v1" if model_output else "constrained_generation_v1",
            "request_position": position,
            "source_scope": "curriculum_and_owned_material"
            if payload.get("use_teacher_materials") or payload.get("source_scope") == "curriculum_and_owned_material"
            else "curriculum_only",
        },
        "needs_teacher_review": True,
    }


def requested_difficulties(payload: dict[str, Any]):
    distribution = payload.get("difficulty_distribution", {})
    values = []
    for level in range(1, 6):
        values.extend([float(level)] * int(distribution.get(str(level), 0)))
    if not values:
        values = [float(payload.get("target_difficulty") or 3)] * payload["count"]
    if len(values) < payload["count"]:
        values.extend([values[-1]] * (payload["count"] - len(values)))
    return values[: payload["count"]]
