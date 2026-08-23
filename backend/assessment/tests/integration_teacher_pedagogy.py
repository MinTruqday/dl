import os
from uuid import uuid4

import httpx


base_url = os.getenv("ASSESSMENT_TEST_URL", "http://assessment:8000")
run_id = uuid4().hex
teacher_id = f"teacher-pedagogy-{run_id}"
headers = {"x-test-user-id": teacher_id, "x-test-user-role": "author"}


def doc(text):
    return {
        "type": "doc",
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
    }


with httpx.Client(base_url=base_url, timeout=60) as client:
    draft = client.post(
        "/assessment-drafts",
        headers=headers,
        json={
            "title": f"Pedagogy {run_id}",
            "context": {"education_level": "THPT", "subject": "math", "target_program": "grade_12"},
            "layout_doc": doc("Đề kiểm tra"),
        },
    )
    draft.raise_for_status()
    generated = client.post(
        f"/assessment-drafts/{draft.json()['_id']}/generate",
        headers=headers,
        json={
            "idempotency_key": f"pedagogy-{run_id}",
            "education_level": "THPT",
            "target_program": "grade_12",
            "subject": "math",
            "topic": "đạo hàm",
            "question_type": "single_choice",
            "count": 2,
            "target_difficulty": 3,
            "use_teacher_materials": True,
            "source_scope": "curriculum_and_owned_material",
            "source_evidence": [
                {
                    "source_type": "curriculum",
                    "authority": "official",
                    "text": "Chuẩn kiến thức đạo hàm",
                },
                {
                    "source_type": "teacher_material",
                    "owner_id": teacher_id,
                    "content_type": "solution",
                    "text": "Bài mẫu giải từng bước bằng cách 1 và cách 2 Lưu ý lỗi sai dễ nhầm",
                },
            ],
        },
    )
    if generated.status_code != 201:
        raise AssertionError(f"generation failed {generated.status_code} {generated.text}")
    questions = generated.json()["questions"]
    assert len(questions) == 2
    context = questions[0]["generation_provenance"]["pedagogical_context"]
    assert context["source_mode"] == "curriculum_and_teacher_material"
    assert "step_by_step" in context["preferred_solution_patterns"]
    assert (
        questions[0]["generation_provenance"]["variation_directive"]
        != questions[1]["generation_provenance"]["variation_directive"]
    )

print("teacher pedagogy integration passed")
