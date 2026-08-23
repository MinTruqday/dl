import os
import time
from copy import deepcopy
from uuid import uuid4

import httpx


base_url = os.getenv("ASSESSMENT_TEST_URL", "http://assessment:8000")
run_id = uuid4().hex
teacher_headers = {"x-test-user-id": f"teacher-{run_id}", "x-test-user-role": "author"}


def student_headers(index):
    return {"x-test-user-id": f"student-{index}-{run_id}", "x-test-user-role": "reader"}


def request(client, method, path, headers, expected, **kwargs):
    response = client.request(method, path, headers=headers, **kwargs)
    if response.status_code != expected:
        raise AssertionError(f"{method} {path} returned {response.status_code} {response.text}")
    if expected == 204:
        return None
    return response.json()


def doc(text):
    return {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]}


with httpx.Client(base_url=base_url, timeout=30) as client:
    profile = request(
        client,
        "PUT",
        "/education/profiles/me",
        teacher_headers,
        200,
        json={"personas": ["teacher"]},
    )
    assert profile["personas"] == ["teacher"]
    settings = request(
        client,
        "PUT",
        "/education/profiles/me/settings",
        teacher_headers,
        200,
        json={
            "ui_language": "vi",
            "theme": "dark",
            "notifications_enabled": False,
            "accessibility_preferences": {"reduced_motion": True},
            "default_subject": "math",
            "privacy_mode": True,
            "data_export_format": "json",
        },
    )
    assert settings["theme"] == "dark"
    loaded_settings = request(client, "GET", "/education/profiles/me/settings", teacher_headers, 200)
    assert loaded_settings["accessibility_preferences"]["reduced_motion"] is True

    draft = request(
        client,
        "POST",
        "/assessment-drafts",
        teacher_headers,
        201,
        json={
            "title": f"Đề kiểm thử {run_id}",
            "context": {"education_level": "THPT", "subject": "math", "target_program": "grade_12"},
            "layout_doc": doc("Đề kiểm tra Toán"),
            "research_blind_mode": True,
        },
    )

    question = request(
        client,
        "POST",
        f"/assessment-drafts/{draft['_id']}/questions",
        teacher_headers,
        201,
        json={
            "question_type": "single_choice",
            "authoring_source": "manual_tiptap",
            "stem_doc": doc("Kết quả của hai cộng hai là bao nhiêu"),
            "options": [
                {"id": "A", "content_doc": doc("Ba")},
                {"id": "B", "content_doc": doc("Bốn")},
            ],
            "answer_key": {"option_id": "B"},
            "solution_doc": doc("Hai cộng hai bằng bốn"),
            "scoring_rule": {"points": 1},
            "curriculum_links": [{"subject": "math", "target_program": "grade_12", "concept_id": "arithmetic"}],
            "concept_ids": ["arithmetic"],
            "skill_ids": ["addition"],
            "cognitive_level": "recognition",
            "construct": {
                "primary_concept": "arithmetic",
                "primary_skill": "addition",
                "learning_objective": "add_small_integers",
                "reasoning_steps": 1,
            },
            "source_evidence": [{"chunk_id": "chunk-test", "authority": "official"}],
        },
    )

    blocked_prediction = client.post(
        f"/question-drafts/{question['_id']}/predict-difficulty",
        headers=teacher_headers,
        json={"model_version": "integration-v1"},
    )
    assert blocked_prediction.status_code == 409

    estimate = request(
        client,
        "POST",
        f"/question-drafts/{question['_id']}/teacher-estimate",
        teacher_headers,
        201,
        json={"estimated_difficulty": 2.5, "self_confidence": "high"},
    )
    assert estimate["ai_prediction_visible_before_estimate"] is False
    assert estimate["research_eligible"] is True

    request(
        client,
        "POST",
        f"/question-drafts/{question['_id']}/target-difficulty",
        teacher_headers,
        201,
        json={"target_difficulty": 2.0},
    )
    prediction = request(
        client,
        "POST",
        f"/question-drafts/{question['_id']}/predict-difficulty",
        teacher_headers,
        201,
        json={"model_version": "integration-v1"},
    )
    assert prediction["status"] == "provisional"
    assert prediction["confidence"] < 1
    assert prediction["ui_difficulty_level"] in {1, 2, 3, 4, 5}
    assert prediction["calibrated_difficulty"] is None
    assert prediction["calibration_sample_size"] == 0

    validation = request(client, "POST", f"/question-drafts/{question['_id']}/validate", teacher_headers, 200)
    assert validation["status"] == "NEEDS_REVIEW"
    assert all(check.get("status") for check in validation["checks"])
    assert all(isinstance(check.get("confidence"), (int, float)) for check in validation["checks"])
    frozen = request(client, "POST", f"/question-drafts/{question['_id']}/freeze", teacher_headers, 201)
    assert frozen["version"] == 1
    frozen_again = request(client, "POST", f"/question-drafts/{question['_id']}/freeze", teacher_headers, 201)
    assert frozen_again["_id"] == frozen["_id"]

    suggestion = request(
        client,
        "POST",
        "/blueprints/suggest-distribution",
        teacher_headers,
        200,
        json={"total_questions": 1, "current_distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}},
    )
    assert sum(suggestion["suggested_distribution"].values()) == 1
    assert suggestion["requires_teacher_acceptance"] is True
    assert suggestion["mutated"] is False

    blueprint = request(
        client,
        "POST",
        "/blueprints",
        teacher_headers,
        201,
        json={
            "name": "Mẫu một câu",
            "total_questions": 1,
            "difficulty_distribution": {"1": 0, "2": 1, "3": 0, "4": 0, "5": 0},
            "question_type_constraints": {"single_choice": 1},
            "duration_minutes": 15,
            "is_template": True,
        },
    )
    templates = request(client, "GET", "/blueprints?templates_only=true", teacher_headers, 200)
    assert [item["_id"] for item in templates] == [blueprint["_id"]]
    cloned_blueprint = request(
        client,
        "POST",
        f"/blueprints/{blueprint['_id']}/clone",
        teacher_headers,
        201,
    )
    assert cloned_blueprint["cloned_from_blueprint_id"] == blueprint["_id"]
    assert cloned_blueprint["is_template"] is False
    patched = request(
        client,
        "PATCH",
        f"/assessment-drafts/{draft['_id']}",
        teacher_headers,
        200,
        json={"expected_revision": 2, "blueprint_id": cloned_blueprint["_id"], "status": "ready"},
    )
    conflict = client.patch(
        f"/assessment-drafts/{draft['_id']}",
        headers=teacher_headers,
        json={"expected_revision": 2, "title": "Xung đột"},
    )
    assert conflict.status_code == 409

    assessment = request(
        client,
        "POST",
        "/assessments",
        teacher_headers,
        201,
        json={"assessment_draft_id": draft["_id"], "delivery_policy": {"review_answers": True}},
    )
    request(
        client,
        "POST",
        f"/question-drafts/{question['_id']}/target-difficulty",
        teacher_headers,
        201,
        json={"target_difficulty": 3.0},
    )
    blueprint_mismatch = request(client, "POST", f"/assessment-drafts/{draft['_id']}/validate", teacher_headers, 200)
    assert blueprint_mismatch["valid"] is False
    assert "blueprint_difficulty_mismatch" in {issue["code"] for issue in blueprint_mismatch["issues"]}
    blocked_publish = client.post(
        f"/assessments/{assessment['_id']}/publish",
        headers=teacher_headers,
        json={"assessment_draft_id": draft["_id"], "expected_revision": patched["revision"], "idempotency_key": f"publish-blocked-{run_id}"},
    )
    assert blocked_publish.status_code == 422
    time.sleep(0.01)
    request(
        client,
        "POST",
        f"/question-drafts/{question['_id']}/target-difficulty",
        teacher_headers,
        201,
        json={"target_difficulty": 2.0},
    )
    published = request(
        client,
        "POST",
        f"/assessments/{assessment['_id']}/publish",
        teacher_headers,
        201,
        json={"assessment_draft_id": draft["_id"], "expected_revision": patched["revision"], "idempotency_key": f"publish-{run_id}"},
    )
    published_again = request(
        client,
        "POST",
        f"/assessments/{assessment['_id']}/publish",
        teacher_headers,
        201,
        json={"assessment_draft_id": draft["_id"], "expected_revision": patched["revision"], "idempotency_key": f"publish-{run_id}"},
    )
    assert published_again["_id"] == published["_id"]

    request(
        client,
        "POST",
        f"/assessments/{assessment['_id']}/assignments",
        teacher_headers,
        201,
        json={
            "student_ids": [student_headers(index)["x-test-user-id"] for index in [1, 2]],
            "idempotency_key": f"assign-v1-{run_id}",
        },
    )

    for index, answer in enumerate(["B", "A"], start=1):
        headers = student_headers(index)
        player = request(client, "GET", f"/assessments/{assessment['_id']}/player", headers, 200)
        assert "answer_key" not in player["items"][0]["question"]
        attempt = request(
            client,
            "POST",
            f"/assessments/{assessment['_id']}/attempts",
            headers,
            201,
            json={"attempt_number": 1, "idempotency_key": f"attempt-{index}-{run_id}"},
        )
        response = request(
            client,
            "POST",
            f"/attempts/{attempt['_id']}/responses",
            headers,
            200,
            json={
                "question_version_id": frozen["_id"],
                "answer": {"option_id": answer},
                "response_sequence": 1,
                "client_revision": 1,
                "response_time_ms": 100 + index,
                "is_first_exposure": False,
                "exposure_index": 99,
                "answer_change_count": 99,
                "hint_used": True,
                "explanation_seen_before_answer": True,
                "delivery_context": "practice",
                "technical_flags": ["leaked"],
                "flag_for_review": True,
                "idempotency_key": f"response-{index}-{run_id}",
            },
        )
        assert response["evidence_eligibility"] == "eligible"
        assert response["is_first_exposure"] is True
        assert response["exposure_index"] == 1
        assert response["answer_change_count"] == 0
        assert response["hint_used"] is False
        assert response["explanation_seen_before_answer"] is False
        assert response["technical_flags"] == []
        assert response["flag_for_review"] is True
        assert response["delivery_context"] == "assigned"
        assert "student_id" not in response
        assert response["participant_id"] != headers["x-test-user-id"]
        saved_again = request(
            client,
            "POST",
            f"/attempts/{attempt['_id']}/responses",
            headers,
            200,
            json={
                "question_version_id": frozen["_id"],
                "answer": {"option_id": answer},
                "response_sequence": 1,
                "client_revision": 1,
                "response_time_ms": 100 + index,
                "idempotency_key": f"response-{index}-{run_id}",
            },
        )
        assert saved_again["_id"] == response["_id"]
        changed = request(
            client,
            "POST",
            f"/attempts/{attempt['_id']}/responses",
            headers,
            200,
            json={
                "question_version_id": frozen["_id"],
                "answer": {"option_id": "A" if answer == "B" else "B"},
                "response_sequence": 99,
                "client_revision": 2,
                "response_time_ms": 200 + index,
                "answer_change_count": 100,
                "idempotency_key": f"response-changed-{index}-{run_id}",
            },
        )
        assert changed["answer_change_count"] == 1
        restored = request(
            client,
            "POST",
            f"/attempts/{attempt['_id']}/responses",
            headers,
            200,
            json={
                "question_version_id": frozen["_id"],
                "answer": {"option_id": answer},
                "response_sequence": 100,
                "client_revision": 3,
                "response_time_ms": 300 + index,
                "answer_change_count": 101,
                "idempotency_key": f"response-restored-{index}-{run_id}",
            },
        )
        assert restored["answer_change_count"] == 2
        stale_response = client.post(
            f"/attempts/{attempt['_id']}/responses",
            headers=headers,
            json={
                "question_version_id": frozen["_id"],
                "answer": {"option_id": "A" if answer == "B" else "B"},
                "response_sequence": 1,
                "client_revision": 2,
                "response_time_ms": 400 + index,
                "idempotency_key": f"response-stale-{index}-{run_id}",
            },
        )
        assert stale_response.status_code == 409
        assert stale_response.json()["detail"]["code"] == "stale_response_revision"
        submitted = request(client, "POST", f"/attempts/{attempt['_id']}/submit", headers, 200)
        submitted_again = request(client, "POST", f"/attempts/{attempt['_id']}/submit", headers, 200)
        assert submitted_again["_id"] == submitted["_id"]
        result = request(client, "GET", f"/attempts/{attempt['_id']}/result", headers, 200)
        assert result["review_answers"] is True
        assert result["responses"][0]["answer_key"] == {"option_id": "B"}
        assert result["responses"][0]["solution_doc"]["type"] == "doc"

    attempt_limit = client.post(
        f"/assessments/{assessment['_id']}/attempts",
        headers=student_headers(1),
        json={"attempt_number": 2, "idempotency_key": f"attempt-limit-{run_id}"},
    )
    assert attempt_limit.status_code == 409
    assert attempt_limit.json()["detail"]["code"] == "attempt_limit_reached"

    calibration = request(
        client,
        "POST",
        "/calibration/run",
        teacher_headers,
        201,
        json={
            "question_version_ids": [frozen["_id"]],
            "population_context": {"education_level": "THPT", "subject": "math", "target_program": "grade_12"},
            "method": "CTT",
            "evidence_policy_version": "integration-v1",
        },
    )
    assert calibration["snapshots"][0]["status"] == "calibrated"
    assert calibration["snapshots"][0]["sample_size"] == 2
    contextual_prediction = request(
        client,
        "POST",
        f"/question-drafts/{question['_id']}/predict-difficulty",
        teacher_headers,
        201,
        json={"model_version": "integration-v1"},
    )
    assert contextual_prediction["calibrated_difficulty"] == 3.0
    assert contextual_prediction["calibration_sample_size"] == 2
    assert contextual_prediction["calibration_population_context"]["education_level"] == "THPT"
    assert contextual_prediction["predicted_empirical_gap"] is not None

    calibration_job = request(
        client,
        "POST",
        "/calibration/jobs",
        teacher_headers,
        202,
        json={
            "question_version_ids": [frozen["_id"]],
            "population_context": {"education_level": "THPT", "subject": "math", "target_program": "grade_12"},
            "method": "Rasch",
            "evidence_policy_version": "integration-worker-v1",
            "idempotency_key": f"worker-calibration-{run_id}",
        },
    )
    for _ in range(100):
        job_state = request(client, "GET", f"/calibration/jobs/{calibration_job['job_id']}", teacher_headers, 200)
        if job_state["status"] in {"completed", "failed"}:
            break
        time.sleep(0.1)
    assert job_state["status"] == "completed"
    assert job_state["result"]["snapshots"][0]["question_version_id"] == frozen["_id"]

    signals = request(client, "GET", f"/questions/{frozen['_id']}/difficulty-signals", teacher_headers, 200)
    assert signals["target"] == 2.0
    assert signals["teacher_estimate"] == 2.5
    assert signals["ai_prediction"] is not None
    assert signals["empirical"] == 3.0

    proposed_version = deepcopy(frozen)
    for key in ["_id", "version", "created_at", "parent_version_id"]:
        proposed_version.pop(key, None)
    proposed_version["stem_doc"] = doc("Kết quả của phép cộng hai với hai là bao nhiêu")
    proposal = request(
        client,
        "POST",
        f"/questions/{frozen['question_id']}/revisions",
        teacher_headers,
        201,
        json={
            "target_difficulty": 2.0,
            "proposed_version": proposed_version,
            "reason_codes": ["difficulty_target_mismatch"],
            "evidence_ids": [calibration["snapshots"][0]["_id"]],
            "construct_check": {"passed": True, "concept_preserved": True, "skill_preserved": True},
        },
    )
    revised = request(client, "POST", f"/revisions/{proposal['_id']}/approve", teacher_headers, 201)
    assert revised["version"] == 2
    assert revised["parent_version_id"] == frozen["_id"]
    revised_again = request(client, "POST", f"/revisions/{proposal['_id']}/approve", teacher_headers, 201)
    assert revised_again["_id"] == revised["_id"]
    revised_draft = request(client, "GET", f"/assessment-drafts/{draft['_id']}", teacher_headers, 200)
    assert revised_draft["questions"][0]["stem_doc"] == revised["stem_doc"]
    assert revised_draft["questions"][0]["frozen_revision"] == revised_draft["questions"][0]["revision"]

    republished = request(
        client,
        "POST",
        f"/assessments/{assessment['_id']}/publish",
        teacher_headers,
        201,
        json={
            "assessment_draft_id": draft["_id"],
            "expected_revision": patched["revision"],
            "idempotency_key": f"publish-v2-{run_id}",
        },
    )
    assert republished["version"] == 2
    assert republished["items"][0]["question_version_id"] == revised["_id"]
    old_assignment_player = request(client, "GET", f"/assessments/{assessment['_id']}/player", student_headers(1), 200)
    assert old_assignment_player["assessment_version_id"] == published["_id"]
    request(
        client,
        "POST",
        f"/assessments/{assessment['_id']}/assignments",
        teacher_headers,
        201,
        json={
            "student_ids": [student_headers(index)["x-test-user-id"] for index in [3, 4]],
            "idempotency_key": f"assign-v2-{run_id}",
        },
    )

    for index, answer in enumerate(["B", "A"], start=3):
        headers = student_headers(index)
        attempt = request(
            client,
            "POST",
            f"/assessments/{assessment['_id']}/attempts",
            headers,
            201,
            json={"attempt_number": 1, "idempotency_key": f"attempt-v2-{index}-{run_id}"},
        )
        request(
            client,
            "POST",
            f"/attempts/{attempt['_id']}/responses",
            headers,
            200,
            json={
                "question_version_id": revised["_id"],
                "answer": {"option_id": answer},
                "response_sequence": 1,
                "response_time_ms": 100 + index,
                "idempotency_key": f"response-v2-{index}-{run_id}",
            },
        )
        request(client, "POST", f"/attempts/{attempt['_id']}/submit", headers, 200)

    recalibration = request(
        client,
        "POST",
        "/calibration/run",
        teacher_headers,
        201,
        json={
            "question_version_ids": [revised["_id"]],
            "population_context": {"education_level": "THPT", "subject": "math", "target_program": "grade_12"},
            "method": "Rasch",
            "evidence_policy_version": "integration-v2",
        },
    )
    assert recalibration["snapshots"][0]["status"] == "calibrated"
    research_metrics = request(client, "GET", f"/questions/{frozen['question_id']}/research-metrics", teacher_headers, 200)
    assert research_metrics["error_v1"] is not None
    assert research_metrics["error_v2"] is not None
    assert research_metrics["error_reduction"] is not None
    research_evaluation = request(client, "GET", "/research/evaluation", teacher_headers, 200)
    assert research_evaluation["ai"]["count"] >= 2
    assert research_evaluation["teacher"]["count"] >= 1
    assert research_evaluation["leakage"]["passed"] is True

    analytics = request(client, "GET", f"/assessments/{assessment['_id']}/analytics", teacher_headers, 200)
    assert analytics["attempts"] == 4
    assert analytics["completion_rate"] == 1
    assert analytics["difficulty_comparison"][0]["empirical"] == 3.0
    assert sum(analytics["score_distribution"].values()) == 4
    assert analytics["average_completion_seconds"] is not None
    assert analytics["topic_performance"][0]["responses"] == 4
    assert sum(item["exposure_count"] for item in analytics["item_analysis"]) == 4
    assert max(item["average_answer_changes"] for item in analytics["item_analysis"]) == 2
    teacher_profile = request(client, "GET", "/education/teacher-profile/me", teacher_headers, 200)
    assert teacher_profile["inferred_preferences"]["signal_count"] >= 1
    profile_events = request(client, "GET", "/education/teacher-profile/me/events", teacher_headers, 200)
    assert "difficulty_targeted" in {event["event_type"] for event in profile_events}
    explicit_profile = request(
        client,
        "PUT",
        "/education/teacher-profile/me",
        teacher_headers,
        200,
        json={"explicit_preferences": {"preferred_question_types": ["single_choice"]}, "use_own_materials": False},
    )
    assert explicit_profile["use_own_materials"] is False
    restored_draft = request(
        client,
        "POST",
        f"/question-drafts/{question['_id']}/restore-version/{frozen['_id']}",
        teacher_headers,
        200,
    )
    assert restored_draft["restored_from_version_id"] == frozen["_id"]
    assert restored_draft["frozen_version_id"] is None
    assert restored_draft["revision"] > frozen["source_draft_revision"]
    forbidden_restore = client.post(
        f"/question-drafts/{question['_id']}/restore-version/{frozen['_id']}",
        headers={**teacher_headers, "x-test-user-id": "different-teacher"},
    )
    assert forbidden_restore.status_code == 403
    reset_profile = request(client, "DELETE", "/education/teacher-profile/me/personalization", teacher_headers, 200)
    assert reset_profile["status"] == "reset"
    reset_events = request(client, "GET", "/education/teacher-profile/me/events", teacher_headers, 200)
    assert reset_events == []
    user_export = request(client, "GET", "/education/profiles/me/export", teacher_headers, 200)
    assert user_export["export_id"].startswith("EXP-")
    assert user_export["education_profile"]["settings"]["theme"] == "dark"
    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    for metric_name in [
        "assessment_import_duration",
        "question_validation_failures",
        "difficulty_prediction_mae",
        "calibration_valid_n",
        "teacher_revision_acceptance_rate",
        "construct_preservation_failure_rate",
        "cross_tenant_filter_denials",
    ]:
        assert metric_name in metrics_response.text

print("assessment integration passed")
