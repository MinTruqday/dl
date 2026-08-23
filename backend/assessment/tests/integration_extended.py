import os
from uuid import uuid4

import httpx


base_url = os.getenv("ASSESSMENT_TEST_URL", "http://assessment:8000")
run_id = uuid4().hex
teacher_headers = {"x-test-user-id": f"teacher-extended-{run_id}", "x-test-user-role": "author"}
other_teacher_headers = {"x-test-user-id": f"teacher-other-{run_id}", "x-test-user-role": "author"}
student_headers = {"x-test-user-id": f"student-assigned-{run_id}", "x-test-user-role": "reader"}
unassigned_headers = {"x-test-user-id": f"student-unassigned-{run_id}", "x-test-user-role": "reader"}
admin_headers = {"x-test-user-id": f"admin-{run_id}", "x-test-user-role": "admin"}
internal_headers = {"x-internal-token": os.environ["SECRET_KEY"]}


def request(client, method, path, headers, expected, **kwargs):
    response = client.request(method, path, headers=headers, **kwargs)
    if response.status_code != expected:
        raise AssertionError(f"{method} {path} returned {response.status_code} {response.text}")
    return response.json() if response.content else None


def doc(text):
    return {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]}


def question_payload(source):
    return {
        "question_type": "single_choice",
        "authoring_source": source,
        "stem_doc": doc("Hai cộng ba bằng bao nhiêu"),
        "options": [
            {"id": "A", "content_doc": doc("Bốn")},
            {"id": "B", "content_doc": doc("Năm")},
        ],
        "answer_key": {"option_id": "B"},
        "solution_doc": doc("Hai cộng ba bằng năm"),
        "scoring_rule": {"points": 1},
        "curriculum_links": [{"subject": "math", "target_program": "grade_12"}],
        "concept_ids": ["addition"],
        "skill_ids": ["calculate"],
        "construct": {
            "primary_concept": "addition",
            "primary_skill": "calculate",
            "learning_objective": "basic_addition",
        },
        "source_evidence": [{"document_id": "source-test", "source_page": 3}],
    }


with httpx.Client(base_url=base_url, timeout=30) as client:
    draft = request(
        client,
        "POST",
        "/assessment-drafts",
        teacher_headers,
        201,
        json={
            "title": f"Đề nhập {run_id}",
            "context": {"education_level": "THPT", "subject": "math", "target_program": "grade_12"},
            "layout_doc": doc("Đề nhập"),
        },
    )
    imported = request(
        client,
        "POST",
        f"/assessment-drafts/{draft['_id']}/import",
        teacher_headers,
        202,
        json={
            "idempotency_key": f"import-{run_id}",
            "document_id": f"document-{run_id}",
            "file_name": "de-toan.pdf",
            "pages": [
                {
                    "page_number": 3,
                    "text": "Câu 1 Hai cộng ba bằng bao nhiêu\nA Bốn\nB Năm",
                    "formula_refs": [{"latex": "2+3"}],
                }
            ],
            "answer_key": {"1": "B"},
        },
    )
    assert imported["status"] == "needs_review"
    assert imported["candidates"][0]["source_page"] == 3
    confirmed = request(
        client,
        "POST",
        f"/imports/{imported['_id']}/confirm",
        teacher_headers,
        201,
        json={
            "selected_candidate_ids": [imported["candidates"][0]["candidate_id"]],
            "corrected_questions": {imported["candidates"][0]["candidate_id"]: question_payload("import")},
        },
    )
    imported_question = confirmed["questions"][0]
    confirmed_again = request(
        client,
        "POST",
        f"/imports/{imported['_id']}/confirm",
        teacher_headers,
        201,
        json={
            "selected_candidate_ids": [imported["candidates"][0]["candidate_id"]],
            "corrected_questions": {imported["candidates"][0]["candidate_id"]: question_payload("import")},
        },
    )
    assert confirmed_again["questions"][0]["_id"] == imported_question["_id"]
    assert imported_question["authoring_source"] == "import"
    assert imported_question["source_page"] == 3
    frozen = request(client, "POST", f"/question-drafts/{imported_question['_id']}/freeze", teacher_headers, 201)
    bank = request(client, "GET", "/questions?search=Hai%20cộng%20ba&question_type=single_choice", teacher_headers, 200)
    assert any(item["_id"] == frozen["question_id"] for item in bank)
    duplicated_bank_item = request(
        client,
        "POST",
        f"/questions/{frozen['question_id']}/duplicate",
        teacher_headers,
        201,
    )
    assert duplicated_bank_item["_id"] != frozen["question_id"]
    request(
        client,
        "POST",
        f"/questions/{duplicated_bank_item['_id']}/archive",
        teacher_headers,
        200,
        json={"reason": "Kiểm thử lưu trữ"},
    )
    archived_bank = request(client, "GET", "/questions?status=archived", teacher_headers, 200)
    assert any(item["_id"] == duplicated_bank_item["_id"] for item in archived_bank)
    bank_target_draft = request(
        client,
        "POST",
        "/assessment-drafts",
        teacher_headers,
        201,
        json={
            "title": f"Đề từ ngân hàng {run_id}",
            "context": {"education_level": "THPT", "subject": "math", "target_program": "grade_12"},
            "layout_doc": doc("Đề từ ngân hàng"),
        },
    )
    added_from_bank = request(
        client,
        "POST",
        "/question-bank/add-to-draft",
        teacher_headers,
        201,
        json={"assessment_draft_id": bank_target_draft["_id"], "question_ids": [frozen["question_id"]]},
    )
    assert added_from_bank["questions"][0]["authoring_source"] == "hybrid"
    duplicate_add = client.post(
        "/question-bank/add-to-draft",
        headers=teacher_headers,
        json={"assessment_draft_id": bank_target_draft["_id"], "question_ids": [frozen["question_id"]]},
    )
    assert duplicate_add.status_code == 409

    forbidden = client.get(f"/assessment-drafts/{draft['_id']}", headers=other_teacher_headers)
    assert forbidden.status_code == 403

    assessment = request(
        client,
        "POST",
        "/assessments",
        teacher_headers,
        201,
        json={"assessment_draft_id": draft["_id"], "delivery_policy": {"review_answers": False}},
    )
    published = request(
        client,
        "POST",
        f"/assessments/{assessment['_id']}/publish",
        teacher_headers,
        201,
        json={
            "assessment_draft_id": draft["_id"],
            "expected_revision": 2,
            "idempotency_key": f"publish-extended-{run_id}",
        },
    )
    immutable = client.patch(f"/assessment-versions/{published['_id']}", headers=teacher_headers, json={"title": "changed"})
    assert immutable.status_code == 409
    assert immutable.json()["detail"]["code"] == "immutable_assessment_version"
    request(
        client,
        "POST",
        f"/assessments/{assessment['_id']}/assignments",
        teacher_headers,
        201,
        json={"student_ids": [student_headers["x-test-user-id"]], "idempotency_key": f"assign-{run_id}"},
    )
    assert client.get(f"/assessments/{assessment['_id']}/player", headers=unassigned_headers).status_code == 403
    assigned = request(client, "GET", "/students/me/assessments", student_headers, 200)
    assert assigned[0]["assessment_id"] == assessment["_id"]
    attempt = request(
        client,
        "POST",
        f"/assessments/{assessment['_id']}/attempts",
        student_headers,
        201,
        json={"idempotency_key": f"attempt-extended-{run_id}"},
    )
    request(
        client,
        "POST",
        f"/attempts/{attempt['_id']}/responses",
        student_headers,
        200,
        json={
            "question_version_id": frozen["_id"],
            "answer": {"option_id": "B"},
            "response_sequence": 1,
            "response_time_ms": 1000,
            "idempotency_key": f"response-extended-{run_id}",
        },
    )
    request(client, "POST", f"/attempts/{attempt['_id']}/submit", student_headers, 200)
    result = request(client, "GET", f"/attempts/{attempt['_id']}/result", student_headers, 200)
    assert result["responses"][0]["is_correct"] is None
    assert result["responses"][0]["score"] is None
    assert result["responses"][0]["answer_key"] is None

    blind_draft = request(
        client,
        "POST",
        "/assessment-drafts",
        teacher_headers,
        201,
        json={
            "title": f"Đề AI {run_id}",
            "context": {"education_level": "THPT", "subject": "math", "target_program": "grade_12"},
            "layout_doc": doc("Đề AI"),
            "research_blind_mode": True,
        },
    )
    foreign_material = client.post(
        f"/assessment-drafts/{blind_draft['_id']}/generate",
        headers=teacher_headers,
        json={
            "idempotency_key": f"generate-foreign-{run_id}",
            "education_level": "THPT",
            "target_program": "grade_12",
            "subject": "math",
            "topic": "đạo hàm",
            "count": 1,
            "use_teacher_materials": True,
            "source_evidence": [{"source_type": "teacher_material", "creator_id": "another-teacher"}],
        },
    )
    assert foreign_material.status_code == 403
    request(
        client,
        "PUT",
        "/education/teacher-profile/me",
        teacher_headers,
        200,
        json={"explicit_preferences": {}, "use_own_materials": False},
    )
    material_policy = request(
        client,
        "GET",
        f"/education/internal/teacher-profile/{teacher_headers['x-test-user-id']}/material-policy",
        internal_headers,
        200,
    )
    assert material_policy["use_own_materials"] is False
    disabled_material = client.post(
        f"/assessment-drafts/{blind_draft['_id']}/generate",
        headers=teacher_headers,
        json={
            "idempotency_key": f"generate-disabled-{run_id}",
            "education_level": "THPT",
            "target_program": "grade_12",
            "subject": "math",
            "topic": "đạo hàm",
            "count": 1,
            "use_teacher_materials": True,
            "source_evidence": [{"source_type": "teacher_material", "creator_id": teacher_headers["x-test-user-id"]}],
        },
    )
    assert disabled_material.status_code == 409
    assert disabled_material.json()["detail"]["code"] == "teacher_material_use_disabled"
    request(
        client,
        "PUT",
        "/education/teacher-profile/me",
        teacher_headers,
        200,
        json={"explicit_preferences": {}, "use_own_materials": True},
    )
    generated = request(
        client,
        "POST",
        f"/assessment-drafts/{blind_draft['_id']}/generate",
        teacher_headers,
        201,
        json={
            "idempotency_key": f"generate-{run_id}",
            "education_level": "THPT",
            "target_program": "grade_12",
            "subject": "math",
            "topic": "đạo hàm",
            "count": 1,
            "target_difficulty": 3,
            "source_evidence": [{"source_type": "curriculum", "authority": "official", "chunk_id": "chunk-1"}],
        },
    )
    generated_question = generated["questions"][0]
    assert generated_question["difficulty_prediction"] is None
    estimate = request(
        client,
        "POST",
        f"/question-drafts/{generated_question['_id']}/teacher-estimate",
        teacher_headers,
        201,
        json={"estimated_difficulty": 3, "self_confidence": "medium"},
    )
    assert estimate["research_eligible"] is True
    revealed = request(
        client,
        "POST",
        f"/question-drafts/{generated_question['_id']}/predict-difficulty",
        teacher_headers,
        201,
        json={"model_version": "structured_generation_v1"},
    )
    assert revealed["revealed_at"] is not None
    request(
        client,
        "POST",
        f"/question-drafts/{generated_question['_id']}/target-difficulty",
        teacher_headers,
        201,
        json={"target_difficulty": 1 if revealed["predicted_difficulty"] >= 3 else 5},
    )
    distribution = request(
        client,
        "GET",
        f"/assessment-drafts/{blind_draft['_id']}/difficulty-analysis",
        teacher_headers,
        200,
    )
    assert sum(distribution["predicted_distribution"].values()) == 1
    assert sum(distribution["teacher_distribution"].values()) == 1
    assert sum(distribution["calibrated_distribution"].values()) == 0
    assert distribution["mutated"] is False
    assert distribution["requires_teacher_acceptance"] is True
    learner_fit = request(
        client,
        "POST",
        f"/assessment-drafts/{blind_draft['_id']}/learner-fit",
        teacher_headers,
        200,
        json={
            "target_learner": {"ability_band": [2.5, 3.5], "confidence": 0.6, "source": "generic_learner_band"},
            "target_success_range": [0.45, 0.8],
        },
    )
    assert learner_fit["question_count"] == 1
    assert learner_fit["items"][0]["difficulty_source"] == "predicted"
    assert learner_fit["expected_success_range"][0] <= learner_fit["expected_success_range"][1]
    assert learner_fit["mutated"] is False
    assert learner_fit["requires_teacher_acceptance"] is True
    optimizer_level = str(revealed["ui_difficulty_level"])
    optimizer_distribution = {str(level): int(str(level) == optimizer_level) for level in range(1, 6)}
    optimizer_blueprint = request(
        client,
        "POST",
        "/blueprints",
        teacher_headers,
        201,
        json={
            "total_questions": 1,
            "difficulty_distribution": optimizer_distribution,
            "coverage_constraints": [],
            "question_type_constraints": {"single_choice": 1},
            "cognitive_level_constraints": {generated_question["cognitive_level"]: 1},
            "target_learner": {"ability_band": [2.5, 3.5]},
            "duration_minutes": 15,
            "assessment_purpose": "assigned_assessment",
            "total_points": 1,
        },
    )
    current_blind_draft = request(client, "GET", f"/assessment-drafts/{blind_draft['_id']}", teacher_headers, 200)
    blueprint_draft = request(
        client,
        "PATCH",
        f"/assessment-drafts/{blind_draft['_id']}",
        teacher_headers,
        200,
        json={"expected_revision": current_blind_draft["revision"], "blueprint_id": optimizer_blueprint["_id"]},
    )
    rebalance = request(
        client,
        "POST",
        f"/assessment-drafts/{blind_draft['_id']}/rebalance",
        teacher_headers,
        201,
        json={"expected_revision": blueprint_draft["revision"], "idempotency_key": f"rebalance-{run_id}"},
    )
    assert rebalance["status"] == "proposed"
    assert rebalance["construct_check"]["passed"] is True
    assert rebalance["infeasibility"] == []
    applied_rebalance = request(
        client,
        "POST",
        f"/assessment-drafts/{blind_draft['_id']}/rebalance-proposals/{rebalance['_id']}/approve",
        teacher_headers,
        200,
    )
    assert applied_rebalance["assessment_draft"]["revision"] == blueprint_draft["revision"] + 1
    applied_again = request(
        client,
        "POST",
        f"/assessment-drafts/{blind_draft['_id']}/rebalance-proposals/{rebalance['_id']}/approve",
        teacher_headers,
        200,
    )
    assert applied_again["assessment_draft_revision"] == applied_rebalance["assessment_draft"]["revision"]
    undone_rebalance = request(
        client,
        "POST",
        f"/assessment-drafts/{blind_draft['_id']}/rebalance-proposals/{rebalance['_id']}/undo",
        teacher_headers,
        200,
    )
    assert undone_rebalance["assessment_draft"]["revision"] == applied_rebalance["assessment_draft"]["revision"] + 1
    assert undone_rebalance["question_order"] == [generated_question["_id"]]
    review_queue = request(client, "GET", "/review-queue", teacher_headers, 200)
    queued_generated = next(question for question in review_queue["questions"] if question["_id"] == generated_question["_id"])
    assert "difficulty_mismatch" in queued_generated["review_reason_codes"]

    audits = request(client, "GET", f"/audit?actor_id={teacher_headers['x-test-user-id']}", admin_headers, 200)
    assert any(event["action"] == "assessment_import_confirmed" for event in audits)
    assert any(event["action"] == "assessment_learner_fit_analyzed" for event in audits)

print("assessment extended integration passed")
