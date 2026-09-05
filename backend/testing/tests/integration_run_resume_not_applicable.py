import os
import time

import httpx
import jwt


BASE_URL = os.getenv("TESTING_TEST_URL", "http://127.0.0.1:8000")


def identity(user_id):
    return {
        "Authorization": "Bearer "
        + jwt.encode(
            {"uid": user_id, "sub": f"{user_id}@test.local", "system_role": "USER"},
            os.environ["SECRET_KEY"],
            algorithm="HS256",
        )
    }


QA_LEAD = identity("run-resume-lead")
TESTER = identity("run-resume-tester")


def doc(text):
    return {
        "type": "doc",
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
    }


def request(client, method, path, expected=200, headers=QA_LEAD, **kwargs):
    response = client.request(method, path, headers=headers, **kwargs)
    assert response.status_code == expected, f"{method} {path} {response.status_code} {response.text}"
    body = response.json()
    if expected < 400:
        assert body["meta"]["trace_id"]
        return body["data"]
    assert body["trace_id"]
    return body


def create_test_case(client, project_id, key, title):
    draft = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ban-nhap-ca-kiem-thu",
        201,
        json={
            "test_case_key": key,
            "title": title,
            "type": "happy_path",
            "priority": "high",
            "risk": "high",
            "objective_doc": doc(title),
            "preconditions_doc": doc("Hệ thống sẵn sàng"),
            "steps": [
                {
                    "id": f"step-{key}",
                    "order": 1,
                    "action_doc": doc("Thực hiện thao tác kiểm thử"),
                    "test_data": {},
                    "expected_doc": doc("Hệ thống phản hồi đúng"),
                }
            ],
            "expected_result_doc": doc("Hệ thống phản hồi đúng"),
            "postconditions_doc": doc("Dữ liệu được giữ ổn định"),
        },
    )
    reviewed = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ca-kiem-thu/{draft['_id']}/gui-ra-soat",
        json={"expected_revision": 1, "review_note": "Sẵn sàng phê duyệt"},
    )
    frozen = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ca-kiem-thu/{draft['_id']}/phe-duyet",
        201,
        json={
            "expected_revision": reviewed["revision"],
            "change_reason": "Tạo dữ liệu kiểm tra resume",
            "review_note": "Đã kiểm tra nội dung",
        },
    )
    return frozen["version"]


with httpx.Client(base_url=BASE_URL, timeout=30) as client:
    stamp = int(time.time() * 1000)
    project = request(
        client,
        "POST",
        "/kiem-thu/du-an",
        201,
        json={
            "key": f"RR{stamp}",
            "name": "Tiếp tục thực thi và Không áp dụng",
            "project_type": "web",
            "settings": {"testcase_lint_blocking": False},
        },
    )
    project_id = project["_id"]
    request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/thanh-vien",
        201,
        json={"user_id": "run-resume-tester", "project_role": "TESTER"},
    )
    first_version = create_test_case(client, project_id, f"TC-RR-A-{stamp}", "Luồng dành cho web")
    second_version = create_test_case(
        client,
        project_id,
        f"TC-RR-B-{stamp}",
        "Luồng được bỏ qua có chủ đích",
    )
    version_ids = [first_version["_id"], second_version["_id"]]
    run = request(
        client,
        "POST",
        "/kiem-thu/lan-chay-kiem-thu",
        201,
        json={
            "project_id": project_id,
            "name": "Run kiểm tra resume",
            "test_case_version_ids": version_ids,
            "environment": "staging",
            "build": "build-resume",
        },
    )
    assigned = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/lan-chay-kiem-thu/{run['_id']}/phan-cong",
        json={
            "expected_revision": 1,
            "assignee_id": "run-resume-tester",
            "test_case_assignments": {
                first_version["_id"]: "run-resume-tester",
                second_version["_id"]: "run-resume-tester",
            },
        },
    )
    started = request(
        client,
        "POST",
        f"/kiem-thu/lan-chay-kiem-thu/{run['_id']}/bat-dau",
    )
    assert started["revision"] == assigned["revision"] + 1
    assert started["frozen_scope"]["test_case_version_ids"] == version_ids
    scope_fingerprint = started["frozen_scope_hash"]
    resume_key = f"resume-first-{stamp}"
    resumed = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/lan-chay-kiem-thu/{run['_id']}/tiep-tuc",
        headers=TESTER,
        json={"expected_revision": started["revision"], "idempotency_key": resume_key},
    )
    assert resumed["current_test_case_version"]["_id"] == first_version["_id"]
    assert resumed["current_execution"]["status"] == "NOT_RUN"
    assert resumed["position"] == 1
    assert resumed["remaining_count"] == 2
    assert resumed["assignment_mode"] == "CASE_ASSIGNMENT"
    assert resumed["scope_fingerprint"] == scope_fingerprint
    assert resumed["run"]["test_case_version_ids"] == version_ids
    replayed = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/lan-chay-kiem-thu/{run['_id']}/tiep-tuc",
        headers=TESTER,
        json={"expected_revision": started["revision"], "idempotency_key": resume_key},
    )
    assert replayed["resume_event"]["_id"] == resumed["resume_event"]["_id"]
    frozen_update = request(
        client,
        "PATCH",
        f"/kiem-thu/du-an/{project_id}/lan-chay-kiem-thu/{run['_id']}",
        409,
        json={
            "expected_revision": resumed["run"]["revision"],
            "test_case_version_ids": [first_version["_id"]],
        },
    )
    assert frozen_update["error"]["code"] == "TEST_RUN_SCOPE_FROZEN"
    execution = resumed["current_execution"]
    in_progress = request(
        client,
        "PATCH",
        f"/kiem-thu/du-an/{project_id}/thuc-thi-kiem-thu/{execution['_id']}",
        headers=TESTER,
        json={
            "status": "IN_PROGRESS",
            "step_results": [],
            "note": "Bắt đầu ca được phân công",
            "idempotency_key": f"execution-start-{stamp}",
            "expected_revision": execution["revision"],
        },
    )["execution"]
    missing_reason = request(
        client,
        "PATCH",
        f"/kiem-thu/du-an/{project_id}/thuc-thi-kiem-thu/{execution['_id']}",
        422,
        headers=TESTER,
        json={
            "status": "NOT_APPLICABLE",
            "step_results": [],
            "note": "",
            "idempotency_key": f"not-applicable-empty-{stamp}",
            "expected_revision": in_progress["revision"],
        },
    )
    assert missing_reason["error"]["code"] == "VALIDATION_ERROR"
    policy_denied = request(
        client,
        "PATCH",
        f"/kiem-thu/du-an/{project_id}/thuc-thi-kiem-thu/{execution['_id']}",
        409,
        headers=TESTER,
        json={
            "status": "NOT_APPLICABLE",
            "step_results": [
                {
                    "step_id": f"step-{first_version['test_case_key']}",
                    "status": "NOT_APPLICABLE",
                    "note": "Bước chỉ áp dụng cho ứng dụng di động",
                }
            ],
            "note": "Bản dựng này không chứa giao diện di động",
            "idempotency_key": f"not-applicable-disabled-{stamp}",
            "expected_revision": in_progress["revision"],
        },
    )
    assert policy_denied["error"]["code"] == "NOT_APPLICABLE_POLICY_DISABLED"
    request(
        client,
        "PATCH",
        f"/kiem-thu/du-an/{project_id}/cai-dat",
        json={
            "expected_revision": 1,
            "settings": {"allow_not_applicable_results": True},
        },
    )
    not_applicable = request(
        client,
        "PATCH",
        f"/kiem-thu/du-an/{project_id}/thuc-thi-kiem-thu/{execution['_id']}",
        headers=TESTER,
        json={
            "status": "NOT_APPLICABLE",
            "step_results": [
                {
                    "step_id": f"step-{first_version['test_case_key']}",
                    "status": "NOT_APPLICABLE",
                    "note": "Bước chỉ áp dụng cho ứng dụng di động",
                }
            ],
            "note": "Bản dựng này không chứa giao diện di động",
            "idempotency_key": f"not-applicable-enabled-{stamp}",
            "expected_revision": in_progress["revision"],
        },
    )["execution"]
    assert not_applicable["status"] == "NOT_APPLICABLE"
    assert not_applicable["note"] == "Bản dựng này không chứa giao diện di động"
    assert not_applicable["step_results"][0]["note"] == "Bước chỉ áp dụng cho ứng dụng di động"
    run_detail = request(client, "GET", f"/kiem-thu/lan-chay-kiem-thu/{run['_id']}")
    assert run_detail["frozen_scope_hash"] == scope_fingerprint
    resumed_second = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/lan-chay-kiem-thu/{run['_id']}/tiep-tuc",
        headers=TESTER,
        json={
            "expected_revision": run_detail["revision"],
            "idempotency_key": f"resume-second-{stamp}",
        },
    )
    assert resumed_second["current_test_case_version"]["_id"] == second_version["_id"]
    assert resumed_second["position"] == 2
    skipped = request(
        client,
        "PATCH",
        f"/kiem-thu/du-an/{project_id}/thuc-thi-kiem-thu/{resumed_second['current_execution']['_id']}",
        headers=TESTER,
        json={
            "status": "SKIPPED",
            "step_results": [],
            "note": "Bỏ qua theo phạm vi kiểm thử đã duyệt",
            "idempotency_key": f"skip-second-{stamp}",
            "expected_revision": resumed_second["current_execution"]["revision"],
        },
    )["execution"]
    assert skipped["status"] == "SKIPPED"
    final_run = request(client, "GET", f"/kiem-thu/lan-chay-kiem-thu/{run['_id']}")
    final_resume = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/lan-chay-kiem-thu/{run['_id']}/tiep-tuc",
        headers=TESTER,
        json={
            "expected_revision": final_run["revision"],
            "idempotency_key": f"resume-complete-{stamp}",
        },
    )
    assert final_resume["current_execution"] is None
    assert final_resume["remaining_count"] == 0
    assert final_resume["run"]["test_case_version_ids"] == version_ids
    statuses = {
        item["test_case_version_id"]: item["status"]
        for item in request(client, "GET", f"/kiem-thu/du-an/{project_id}/ket-qua-kiem-thu")
    }
    assert statuses[first_version["_id"]] == "NOT_APPLICABLE"
    assert statuses[second_version["_id"]] == "SKIPPED"

print("run resume and not applicable integration passed")
