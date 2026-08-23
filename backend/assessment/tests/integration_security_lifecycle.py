import os
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx


base_url = os.getenv("ASSESSMENT_TEST_URL", "http://assessment:8000")
content_url = os.getenv("CONTENT_TEST_URL", "http://content:8000")
internal_headers = {"X-Internal-Token": os.environ["SECRET_KEY"]}
run_id = uuid4().hex
teacher_headers = {"x-test-user-id": f"teacher-lifecycle-{run_id}", "x-test-user-role": "author"}
other_teacher_headers = {"x-test-user-id": f"teacher-other-lifecycle-{run_id}", "x-test-user-role": "author"}
student_headers = {"x-test-user-id": f"student-lifecycle-{run_id}", "x-test-user-role": "reader"}
upcoming_student_headers = {"x-test-user-id": f"student-upcoming-{run_id}", "x-test-user-role": "reader"}
admin_headers = {"x-test-user-id": f"admin-lifecycle-{run_id}", "x-test-user-role": "admin"}


def request(client, method, path, headers, expected, **kwargs):
    response = client.request(method, path, headers=headers, **kwargs)
    if response.status_code != expected:
        raise AssertionError(f"{method} {path} returned {response.status_code} {response.text}")
    return response.json() if response.content else None


def doc(text):
    return {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]}


def question_payload():
    return {
        "question_type": "single_choice",
        "authoring_source": "manual_tiptap",
        "stem_doc": doc("Một cộng một bằng bao nhiêu"),
        "options": [
            {"id": "A", "content_doc": doc("Một")},
            {"id": "B", "content_doc": doc("Hai")},
        ],
        "answer_key": {"option_id": "B"},
        "solution_doc": doc("Một cộng một bằng hai"),
        "scoring_rule": {"points": 1},
        "curriculum_links": [{"subject": "math", "target_program": "grade_12"}],
        "concept_ids": ["addition"],
        "skill_ids": ["calculate"],
        "cognitive_level": "recognition",
        "construct": {
            "primary_concept": "addition",
            "primary_skill": "calculate",
            "learning_objective": "basic_addition",
        },
        "source_evidence": [{"chunk_id": f"chunk-{run_id}", "authority": "official"}],
        "locked": True,
    }


with httpx.Client(base_url=base_url, timeout=30) as client:
    forbidden_authoring = client.post(
        "/assessment-drafts",
        headers=student_headers,
        json={
            "title": "Không hợp lệ",
            "context": {"education_level": "THPT", "subject": "math", "target_program": "grade_12"},
            "layout_doc": doc("Nội dung"),
        },
    )
    assert forbidden_authoring.status_code == 403

    node = request(
        client,
        "POST",
        "/education/curriculum",
        admin_headers,
        200,
        json={
            "node_type": "concept",
            "education_level": "THPT",
            "subject": "math",
            "target_program": "grade_12",
            "title": "Phép cộng",
            "canonical_code": f"math.addition.{run_id}",
            "curriculum_version": "2026",
        },
    )
    updated_node = request(
        client,
        "PATCH",
        f"/education/curriculum/{node['_id']}",
        admin_headers,
        200,
        json={"expected_revision": 1, "title": "Phép cộng số tự nhiên"},
    )
    assert updated_node["revision"] == 2
    stale_node_update = client.patch(
        f"/education/curriculum/{node['_id']}",
        headers=admin_headers,
        json={"expected_revision": 1, "title": "Ghi đè stale"},
    )
    assert stale_node_update.status_code == 409
    merge_source = request(
        client,
        "POST",
        "/education/curriculum",
        admin_headers,
        200,
        json={
            "node_type": "concept",
            "education_level": "THPT",
            "subject": "math",
            "target_program": "grade_12",
            "title": "Phép cộng tương đương",
            "canonical_code": f"math.addition.alias.{run_id}",
            "curriculum_version": "2026",
        },
    )
    merged_node = request(
        client,
        "POST",
        f"/education/curriculum/{node['_id']}/merge",
        admin_headers,
        200,
        json={
            "source_node_ids": [merge_source["_id"]],
            "expected_target_revision": 2,
            "expected_source_revisions": {merge_source["_id"]: 1},
        },
    )
    assert merged_node["revision"] == 3
    obsolete_merge_source = request(client, "GET", f"/education/curriculum/{merge_source['_id']}", admin_headers, 200)
    assert obsolete_merge_source["status"] == "obsolete"
    curriculum_mapping_payload = {
        "document_id": f"curriculum-{run_id}",
        "chunk_id": f"curriculum-chunk-{run_id}",
        "curriculum_node_ids": [node["_id"]],
        "concept_ids": ["addition"],
        "skill_ids": ["calculate"],
        "source_type": "curriculum",
        "authority": "official",
        "mapping_confidence": 0.9,
        "mapping_status": "auto",
        "source_version": "2026",
    }
    spoofed_mapping = client.post(
        f"/education/sources/curriculum-{run_id}/map",
        headers=teacher_headers,
        json=curriculum_mapping_payload,
    )
    assert spoofed_mapping.status_code == 403
    curriculum_mapping = request(
        client,
        "POST",
        f"/education/sources/curriculum-{run_id}/map",
        admin_headers,
        200,
        json=curriculum_mapping_payload,
    )
    repeated_mapping = request(
        client,
        "POST",
        f"/education/sources/curriculum-{run_id}/map",
        admin_headers,
        200,
        json=curriculum_mapping_payload,
    )
    assert repeated_mapping["_id"] == curriculum_mapping["_id"]
    conflicting_mapping = client.post(
        f"/education/sources/curriculum-{run_id}/map",
        headers=admin_headers,
        json={**curriculum_mapping_payload, "mapping_confidence": 0.2},
    )
    assert conflicting_mapping.status_code == 409
    split_node = request(
        client,
        "POST",
        f"/education/curriculum/{node['_id']}/split",
        admin_headers,
        201,
        json={
            "expected_revision": 3,
            "parts": [
                {"title": "Phép cộng số tự nhiên", "canonical_code": f"math.addition.natural.{run_id}"},
                {"title": "Phép cộng số thực", "canonical_code": f"math.addition.real.{run_id}"},
            ],
        },
    )
    assert split_node["allocation_policy"] == "existing_relations_to_first_part"
    active_curriculum_node_id = split_node["parts"][0]["_id"]
    updated_curriculum_mapping = request(
        client,
        "GET",
        f"/education/sources/curriculum-{run_id}/mapping",
        admin_headers,
        200,
    )[0]
    assert active_curriculum_node_id in updated_curriculum_mapping["curriculum_node_ids"]
    assert node["_id"] not in updated_curriculum_mapping["curriculum_node_ids"]
    active_curriculum = request(client, "GET", "/education/curriculum", admin_headers, 200)
    assert node["_id"] not in {row["_id"] for row in active_curriculum}
    curriculum_mapping_payload["curriculum_node_ids"] = [active_curriculum_node_id]
    teacher_review_curriculum = client.patch(
        f"/education/sources/curriculum-{run_id}/mapping/{curriculum_mapping['_id']}",
        headers=teacher_headers,
        json={"mapping_status": "confirmed"},
    )
    assert teacher_review_curriculum.status_code == 403

    material_document_id = f"material-{run_id}"
    with httpx.Client(base_url=content_url, timeout=30) as content_client:
        seeded_curriculum = content_client.post(
            "/tai-lieu/noi-bo/trao-doi",
            headers=internal_headers,
            json={
                "action": "upsert_collected",
                "document": {
                    "_id": f"curriculum-{run_id}",
                    "title": "Nguồn curriculum kiểm thử",
                    "slug": f"curriculum-{run_id}",
                    "source_url": f"https://nxbgd.test/{run_id}",
                    "content_hash": f"c{run_id}".ljust(64, "0")[:64],
                    "creator_id": admin_headers["x-test-user-id"],
                    "visibility": "private",
                    "education_metadata": {
                        "source_type": "curriculum",
                        "authority": "official",
                        "education_level": "THPT",
                        "subject": "math",
                        "target_program": "grade_12",
                        "source_version": "2026",
                        "mapping_status": "confirmed",
                    },
                },
            },
        )
        assert seeded_curriculum.status_code == 200, seeded_curriculum.text
        seeded_material = content_client.post(
            "/tai-lieu/noi-bo/trao-doi",
            headers=internal_headers,
            json={
                "action": "upsert_collected",
                "document": {
                    "_id": material_document_id,
                    "title": "Tài liệu riêng của giáo viên",
                    "slug": f"teacher-material-{run_id}",
                    "source_url": f"https://teacher-material.test/{run_id}",
                    "content_hash": run_id.ljust(64, "0")[:64],
                    "creator_id": teacher_headers["x-test-user-id"],
                    "visibility": "private",
                    "education_metadata": {
                        "source_type": "teacher_material",
                        "authority": "supplementary",
                        "education_level": "THPT",
                        "subject": "math",
                        "target_program": "grade_12",
                        "source_version": run_id,
                        "mapping_status": "needs_review",
                    },
                },
            },
        )
        assert seeded_material.status_code == 200, seeded_material.text

    other_teacher_mapping = client.post(
        f"/education/sources/{material_document_id}/map",
        headers=other_teacher_headers,
        json={
            **curriculum_mapping_payload,
            "document_id": material_document_id,
            "chunk_id": f"other-material-chunk-{run_id}",
            "source_type": "teacher_material",
            "authority": "supplementary",
        },
    )
    assert other_teacher_mapping.status_code == 403

    material_mapping = request(
        client,
        "POST",
        f"/education/sources/{material_document_id}/map",
        teacher_headers,
        200,
        json={
            **curriculum_mapping_payload,
            "document_id": material_document_id,
            "chunk_id": f"material-chunk-{run_id}",
            "source_type": "teacher_material",
            "authority": "supplementary",
        },
    )
    forbidden_material_review = client.patch(
        f"/education/sources/{material_document_id}/mapping/{material_mapping['_id']}",
        headers=other_teacher_headers,
        json={"mapping_status": "confirmed"},
    )
    assert forbidden_material_review.status_code == 403
    request(
        client,
        "PATCH",
        f"/education/sources/{material_document_id}/mapping/{material_mapping['_id']}",
        teacher_headers,
        200,
        json={"mapping_status": "confirmed", "mapping_confidence": 1},
    )

    high_stakes_draft = request(
        client,
        "POST",
        "/assessment-drafts",
        teacher_headers,
        201,
        json={
            "title": f"Đề quyết định quan trọng {run_id}",
            "context": {"education_level": "THPT", "subject": "math", "target_program": "grade_12", "high_stakes": True},
            "layout_doc": doc("Hướng dẫn"),
        },
    )
    high_stakes_question = request(
        client,
        "POST",
        f"/assessment-drafts/{high_stakes_draft['_id']}/questions",
        teacher_headers,
        201,
        json=question_payload(),
    )
    request(client, "POST", f"/question-drafts/{high_stakes_question['_id']}/freeze", teacher_headers, 201)
    high_stakes_blocked = request(
        client,
        "POST",
        f"/assessment-drafts/{high_stakes_draft['_id']}/validate",
        teacher_headers,
        200,
    )
    assert "high_stakes_validity_review_required" in {issue["code"] for issue in high_stakes_blocked["issues"]}
    request(
        client,
        "POST",
        f"/question-drafts/{high_stakes_question['_id']}/validity-review",
        teacher_headers,
        200,
        json={"status": "approved", "risk_flags": [], "reviewer_note": "Đã rà soát construct và cơ hội tiếp cận"},
    )
    request(client, "POST", f"/question-drafts/{high_stakes_question['_id']}/freeze", teacher_headers, 201)
    high_stakes_valid = request(
        client,
        "POST",
        f"/assessment-drafts/{high_stakes_draft['_id']}/validate",
        teacher_headers,
        200,
    )
    assert high_stakes_valid["valid"] is True

    draft = request(
        client,
        "POST",
        "/assessment-drafts",
        teacher_headers,
        201,
        json={
            "title": f"Đề vòng đời {run_id}",
            "context": {"education_level": "THPT", "subject": "math", "target_program": "grade_12"},
            "layout_doc": doc("Hướng dẫn"),
        },
    )
    question = request(
        client,
        "POST",
        f"/assessment-drafts/{draft['_id']}/questions",
        teacher_headers,
        201,
        json=question_payload(),
    )
    locked_revision = client.post(
        f"/question-drafts/{question['_id']}/ai/revise",
        headers=teacher_headers,
        json={"action": "clarify_wording", "instruction": "Làm rõ"},
    )
    assert locked_revision.status_code == 423
    unlocked = request(
        client,
        "PATCH",
        f"/question-drafts/{question['_id']}",
        teacher_headers,
        200,
        json={"expected_revision": question["revision"], "locked": False},
    )
    draft_revision = request(
        client,
        "POST",
        f"/question-drafts/{question['_id']}/ai/revise",
        teacher_headers,
        201,
        json={"action": "clarify_wording", "instruction": "Làm rõ"},
    )
    assert draft_revision["after"]["stem_doc"] == doc("Làm rõ")
    rejected_draft_revision = request(
        client,
        "POST",
        f"/draft-revisions/{draft_revision['_id']}/reject",
        teacher_headers,
        200,
    )
    assert rejected_draft_revision["status"] == "rejected"
    frozen = request(client, "POST", f"/question-drafts/{question['_id']}/freeze", teacher_headers, 201)
    refreshed_draft = request(client, "GET", f"/assessment-drafts/{draft['_id']}", teacher_headers, 200)
    assessment = request(
        client,
        "POST",
        "/assessments",
        teacher_headers,
        201,
        json={"assessment_draft_id": draft["_id"], "delivery_policy": {"attempt_limit": 1, "duration_minutes": 30}},
    )
    same_assessment = request(
        client,
        "POST",
        "/assessments",
        teacher_headers,
        201,
        json={"assessment_draft_id": draft["_id"], "delivery_policy": {"attempt_limit": 1, "duration_minutes": 30, "review_answers": True, "shuffle_options": True, "shuffle_questions": True}},
    )
    assert same_assessment["_id"] == assessment["_id"]
    scheduled = request(
        client,
        "POST",
        f"/assessments/{assessment['_id']}/publish",
        teacher_headers,
        201,
        json={
            "assessment_draft_id": draft["_id"],
            "expected_revision": refreshed_draft["revision"],
            "idempotency_key": f"scheduled-{run_id}",
            "scheduled_for": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        },
    )
    assert scheduled["published_at"] is None
    listed = request(client, "GET", "/assessments", teacher_headers, 200)
    assert next(item for item in listed if item["_id"] == assessment["_id"])["status"] == "scheduled"
    request(
        client,
        "POST",
        f"/assessments/{assessment['_id']}/unpublish",
        teacher_headers,
        200,
        json={"reason": "Đổi lịch"},
    )
    published = request(
        client,
        "POST",
        f"/assessments/{assessment['_id']}/publish",
        teacher_headers,
        201,
        json={
            "assessment_draft_id": draft["_id"],
            "expected_revision": refreshed_draft["revision"],
            "idempotency_key": f"published-{run_id}",
        },
    )
    assert published["version"] == 2
    assert published["items"][0]["question_version_id"] == frozen["_id"]
    version_forbidden = client.get(f"/assessment-versions/{published['_id']}", headers=student_headers)
    assert version_forbidden.status_code == 403
    snapshot = request(client, "GET", f"/assessment-versions/{published['_id']}", teacher_headers, 200)
    assert snapshot["_id"] == published["_id"]
    immutable = client.patch(f"/assessment-versions/{published['_id']}", headers=teacher_headers, json={"title": "Sai"})
    assert immutable.status_code == 409
    assert immutable.json()["detail"]["code"] == "immutable_assessment_version"
    immutable_question = client.patch(f"/question-versions/{frozen['_id']}", headers=teacher_headers, json={"stem_doc": doc("Sai")})
    assert immutable_question.status_code == 409
    assert immutable_question.json()["detail"]["code"] == "immutable_question_version"

    cloned = request(
        client,
        "POST",
        f"/assessments/{assessment['_id']}/clone",
        teacher_headers,
        201,
        json={"title": f"Bản sao {run_id}"},
    )
    assert cloned["status"] == "draft"
    assert cloned["questions"][0]["frozen_version_id"] is None
    assert cloned["questions"][0]["question_id"] is None

    deadline = datetime.now(timezone.utc) + timedelta(seconds=2)
    assigned = request(
        client,
        "POST",
        f"/assessments/{assessment['_id']}/assignments",
        teacher_headers,
        201,
        json={
            "student_ids": [student_headers["x-test-user-id"]],
            "due_at": deadline.isoformat(),
            "idempotency_key": f"assign-timeout-{run_id}",
        },
    )["assignments"][0]
    player = request(
        client,
        "GET",
        f"/assessments/{assessment['_id']}/player?assignment_id={assigned['_id']}",
        student_headers,
        200,
    )
    assert player["assessment_version_id"] == published["_id"]
    assert "answer_key" not in player["items"][0]["question"]
    repeated_player = request(
        client,
        "GET",
        f"/assessments/{assessment['_id']}/player?assignment_id={assigned['_id']}",
        student_headers,
        200,
    )
    assert repeated_player["items"] == player["items"]
    attempt = request(
        client,
        "POST",
        f"/assessments/{assessment['_id']}/attempts",
        student_headers,
        201,
        json={"assignment_id": assigned["_id"], "idempotency_key": f"attempt-timeout-{run_id}"},
    )
    assert attempt["option_order"][frozen["_id"]] == [option["id"] for option in player["items"][0]["question"]["options"]]
    time.sleep(2.2)
    expired_save = client.post(
        f"/attempts/{attempt['_id']}/responses",
        headers=student_headers,
        json={
            "question_version_id": frozen["_id"],
            "answer": {"option_id": "B"},
            "response_sequence": 1,
            "response_time_ms": 2200,
            "idempotency_key": f"expired-response-{run_id}",
        },
    )
    assert expired_save.status_code == 409
    assert expired_save.json()["detail"]["code"] == "attempt_time_expired"
    result = request(client, "GET", f"/attempts/{attempt['_id']}/result", student_headers, 200)
    assert result["status"] == "timed_out"

    cannot_unpublish = client.post(
        f"/assessments/{assessment['_id']}/unpublish",
        headers=teacher_headers,
        json={"reason": "Đã có attempt"},
    )
    assert cannot_unpublish.status_code == 409
    upcoming = request(
        client,
        "POST",
        f"/assessments/{assessment['_id']}/assignments",
        teacher_headers,
        201,
        json={
            "student_ids": [upcoming_student_headers["x-test-user-id"]],
            "available_from": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "idempotency_key": f"assign-upcoming-{run_id}",
        },
    )["assignments"][0]
    not_open_yet = client.get(
        f"/assessments/{assessment['_id']}/player?assignment_id={upcoming['_id']}",
        headers=upcoming_student_headers,
    )
    assert not_open_yet.status_code == 403
    archived = request(
        client,
        "POST",
        f"/assessments/{assessment['_id']}/archive",
        teacher_headers,
        200,
        json={"reason": "Hoàn tất kiểm thử"},
    )
    assert archived["status"] == "archived"
    assert client.get("/operations/privacy-policy", headers=teacher_headers).status_code == 403
    privacy_policy = request(client, "GET", "/operations/privacy-policy", admin_headers, 200)
    assert privacy_policy["response_contains_raw_student_id"] is False
    retention = request(
        client,
        "POST",
        "/operations/privacy/purge",
        admin_headers,
        200,
        json={"older_than_days": 30},
    )
    assert retention["attempts_pseudonymized"] == 0
    assert retention["responses_pseudonymized"] == 0
    assert client.get("/operations/models", headers=teacher_headers).status_code == 403
    model_monitoring = request(client, "GET", "/operations/models", admin_headers, 200)
    assert {"prediction_versions", "prediction_error_metrics", "calibration_jobs", "failed_jobs", "drift_alerts", "bank_coverage"}.issubset(model_monitoring)
    assert client.get("/operations/health", headers=teacher_headers).status_code == 403
    platform_health = request(client, "GET", "/operations/health", admin_headers, 200)
    assert platform_health["services"]["assessment"]["status"] == "ready"
    assert {
        "authentication",
        "cloud",
        "content",
        "rag",
        "agentic_ai",
        "worker",
        "compilation",
        "collection",
    }.issubset(platform_health["services"])
    cross_tenant_draft = client.get(f"/assessment-drafts/{draft['_id']}", headers=other_teacher_headers)
    assert cross_tenant_draft.status_code == 403
    access_events = request(
        client,
        "GET",
        f"/audit?actor_id={other_teacher_headers['x-test-user-id']}",
        admin_headers,
        200,
    )
    assert any(event["action"] == "cross_tenant_access_denied" for event in access_events)
    immutable_events = request(
        client,
        "GET",
        f"/audit?entity_type=AssessmentVersion&entity_id={published['_id']}",
        admin_headers,
        200,
    )
    assert any(event["action"] == "published_assessment_mutation_denied" for event in immutable_events)
    obsolete_source = request(
        client,
        "POST",
        f"/education/sources/curriculum-{run_id}/obsolete",
        admin_headers,
        200,
        json={"reason": "Nguồn kiểm thử đã thay thế"},
    )
    assert obsolete_source == {"document_id": f"curriculum-{run_id}", "status": "obsolete", "deindexed": True}

print("assessment security lifecycle integration passed")
