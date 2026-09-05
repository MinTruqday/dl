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


QA_LEAD = identity("bug-trace-lead")
BA = identity("bug-trace-ba")
DEVELOPER = identity("bug-trace-developer")


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


with httpx.Client(base_url=BASE_URL, timeout=30) as client:
    stamp = int(time.time() * 1000)
    project = request(
        client,
        "POST",
        "/kiem-thu/du-an",
        201,
        json={
            "key": f"BT{stamp}",
            "name": "Gợi ý truy vết lỗi",
            "project_type": "web",
            "settings": {
                "requirement_lint_blocking": False,
                "testcase_lint_blocking": False,
            },
        },
    )
    project_id = project["_id"]
    for user_id, role in (("bug-trace-ba", "BA"), ("bug-trace-developer", "DEVELOPER")):
        request(
            client,
            "POST",
            f"/kiem-thu/du-an/{project_id}/thanh-vien",
            201,
            json={"user_id": user_id, "project_role": role},
        )
    requirement = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/yeu-cau",
        201,
        json={
            "requirement_key": f"REQ-BT-{stamp}",
            "title": "Xác thực đăng nhập bằng thư điện tử",
            "type": "functional",
            "priority": "high",
            "risk": "high",
            "content_doc": doc("Hệ thống xác thực đăng nhập bằng thư điện tử hợp lệ"),
            "acceptance_criteria": [
                {
                    "key": "AC-01",
                    "content_doc": doc("Thông tin hợp lệ cho phép người dùng đăng nhập"),
                }
            ],
            "business_rules": ["Thư điện tử phải đúng định dạng"],
            "actors": ["Người dùng"],
        },
    )
    reviewed_requirement = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/yeu-cau/{requirement['_id']}/gui-ra-soat",
        json={"expected_revision": 1, "review_note": "Đã kiểm tra yêu cầu"},
    )
    requirement_version = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/yeu-cau/{requirement['_id']}/phe-duyet",
        json={
            "expected_revision": reviewed_requirement["revision"],
            "review_note": "Dùng làm nguồn chuẩn",
        },
    )
    draft = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ban-nhap-ca-kiem-thu",
        201,
        json={
            "test_case_key": f"TC-BT-{stamp}",
            "title": "Xác thực đăng nhập bằng thư điện tử",
            "type": "happy_path",
            "priority": "high",
            "risk": "high",
            "requirement_version_ids": [requirement_version["_id"]],
            "objective_doc": doc("Kiểm tra xác thực đăng nhập bằng thư điện tử"),
            "preconditions_doc": doc("Tài khoản đã tồn tại"),
            "steps": [
                {
                    "id": "step-login",
                    "order": 1,
                    "action_doc": doc("Nhập thư điện tử và mật khẩu hợp lệ"),
                    "test_data": {},
                    "expected_doc": doc("Người dùng đăng nhập thành công"),
                }
            ],
            "expected_result_doc": doc("Người dùng đăng nhập thành công"),
            "postconditions_doc": doc("Phiên đăng nhập được tạo"),
        },
    )
    reviewed_case = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ca-kiem-thu/{draft['_id']}/gui-ra-soat",
        json={"expected_revision": 1, "review_note": "Đã kiểm tra ca kiểm thử"},
    )
    frozen_case = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ca-kiem-thu/{draft['_id']}/phe-duyet",
        201,
        json={
            "expected_revision": reviewed_case["revision"],
            "change_reason": "Tạo dữ liệu kiểm tra truy vết",
            "review_note": "Nội dung phù hợp yêu cầu",
        },
    )
    test_case_version = frozen_case["version"]
    defect = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/loi",
        201,
        json={
            "project_id": project_id,
            "title": "Xác thực đăng nhập bằng thư điện tử",
            "description_doc": doc("Đăng nhập bằng thư điện tử hợp lệ bị từ chối"),
            "steps_to_reproduce": [],
            "actual_result_doc": doc("Hệ thống từ chối đăng nhập"),
            "expected_result_doc": doc("Người dùng đăng nhập thành công"),
            "severity": "major",
            "priority": "high",
            "environment": "staging",
            "linked_requirement_version_ids": [],
        },
    )
    denied = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ai/loi/{defect['_id']}/goi-y-truy-vet",
        403,
        headers=DEVELOPER,
        json={"idempotency_key": f"bug-trace-denied-{stamp}"},
    )
    assert denied["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    idempotency_key = f"bug-trace-suggestion-{stamp}"
    suggestion = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ai/loi/{defect['_id']}/goi-y-truy-vet",
        201,
        headers=BA,
        json={"idempotency_key": idempotency_key},
    )
    assert suggestion["candidate_only"] is True
    assert suggestion["human_confirmation_required"] is True
    assert suggestion["review_status"] == "PENDING"
    assert suggestion["requirement_candidates"]
    assert suggestion["test_case_candidates"]
    requirement_candidate = next(
        item
        for item in suggestion["requirement_candidates"]
        if item["artifact_id"] == requirement_version["_id"]
    )
    test_case_candidate = next(
        item
        for item in suggestion["test_case_candidates"]
        if item["artifact_id"] == test_case_version["_id"]
    )
    before_confirmation = request(
        client,
        "GET",
        f"/kiem-thu/du-an/{project_id}/loi",
        headers=BA,
    )["items"]
    unchanged = next(item for item in before_confirmation if item["_id"] == defect["_id"])
    assert unchanged.get("linked_test_case_version_id") is None
    assert unchanged.get("linked_requirement_version_ids") == []
    replay = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ai/loi/{defect['_id']}/goi-y-truy-vet",
        201,
        headers=BA,
        json={"idempotency_key": idempotency_key},
    )
    assert replay["_id"] == suggestion["_id"]
    linked = request(
        client,
        "PATCH",
        f"/kiem-thu/du-an/{project_id}/loi/{defect['_id']}/truy-vet",
        headers=BA,
        json={
            "expected_revision": defect["revision"],
            "reason": "Đã đối chiếu yêu cầu và ca kiểm thử với bằng chứng của lỗi",
            "linked_test_case_version_id": test_case_version["_id"],
            "linked_requirement_version_ids": [requirement_version["_id"]],
            "ai_result_id": suggestion["_id"],
            "accepted_candidate_ids": [
                requirement_candidate["candidate_id"],
                test_case_candidate["candidate_id"],
            ],
        },
    )
    assert linked["linked_test_case_version_id"] == test_case_version["_id"]
    assert linked["linked_requirement_version_ids"] == [requirement_version["_id"]]
    reviewed_suggestion = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ai/loi/{defect['_id']}/goi-y-truy-vet",
        201,
        headers=BA,
        json={"idempotency_key": idempotency_key},
    )
    assert reviewed_suggestion["review_status"] == "REVIEWED"
    assert set(reviewed_suggestion["accepted_candidate_ids"]) == {
        requirement_candidate["candidate_id"],
        test_case_candidate["candidate_id"],
    }
    invalid_candidate = request(
        client,
        "PATCH",
        f"/kiem-thu/du-an/{project_id}/loi/{defect['_id']}/truy-vet",
        422,
        headers=BA,
        json={
            "expected_revision": linked["revision"],
            "reason": "Không được nhận ứng viên ngoài kết quả AI",
            "linked_requirement_version_ids": [requirement_version["_id"]],
            "ai_result_id": suggestion["_id"],
            "accepted_candidate_ids": ["requirement_version:khong-ton-tai"],
        },
    )
    assert invalid_candidate["error"]["code"] == "INVALID_AI_CANDIDATE"
    legacy = request(
        client,
        "GET",
        f"/kiem-thu/loi/{defect['_id']}/ung-vien-truy-vet",
        headers=BA,
    )
    assert any(item["test_case_version_id"] == test_case_version["_id"] for item in legacy)

print("bug trace suggestion integration passed")
