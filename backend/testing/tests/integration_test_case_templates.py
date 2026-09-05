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


QA_LEAD = identity("template-qa-lead")
TESTER = identity("template-tester")
VIEWER = identity("template-viewer")
OUTSIDER = identity("template-outsider")


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
            "key": f"TP{stamp}",
            "name": "Quản lý mẫu ca kiểm thử",
            "project_type": "web",
        },
    )
    project_id = project["_id"]
    request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/thanh-vien",
        201,
        json={"user_id": "template-tester", "project_role": "TESTER"},
    )
    request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/thanh-vien",
        201,
        json={"user_id": "template-viewer", "project_role": "VIEWER"},
    )
    assert request(
        client,
        "GET",
        f"/kiem-thu/du-an/{project_id}/mau-ca-kiem-thu",
        headers=VIEWER,
    ) == []
    template = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/mau-ca-kiem-thu",
        201,
        headers=TESTER,
        json={
            "name": "Đăng nhập chức năng",
            "template_type": "functional",
            "description": "Mẫu kiểm tra luồng đăng nhập",
            "definition": {
                "preconditions": ["Tài khoản đang hoạt động"],
                "steps": ["Nhập thông tin đăng nhập", "Gửi biểu mẫu"],
                "expected": ["Hệ thống tạo phiên đăng nhập"],
            },
            "tags": ["xác thực", "hồi quy"],
        },
    )
    template_id = template["_id"]
    assert template["revision"] == 1
    assert request(
        client,
        "GET",
        f"/kiem-thu/mau-ca-kiem-thu/{template_id}",
        headers=VIEWER,
    )["definition"]["steps"]
    filtered = request(
        client,
        "GET",
        f"/kiem-thu/du-an/{project_id}/mau-ca-kiem-thu?template_type=functional",
        headers=VIEWER,
    )
    assert [item["_id"] for item in filtered] == [template_id]
    invalid_filter = request(
        client,
        "GET",
        f"/kiem-thu/du-an/{project_id}/mau-ca-kiem-thu?template_type=unknown",
        422,
        headers=VIEWER,
    )
    assert invalid_filter["error"]["code"] == "VALIDATION_ERROR"
    updated = request(
        client,
        "PATCH",
        f"/kiem-thu/mau-ca-kiem-thu/{template_id}",
        headers=TESTER,
        json={
            "expected_revision": 1,
            "description": "Mẫu kiểm tra đăng nhập đã rà soát",
            "definition": {
                "preconditions": ["Tài khoản đang hoạt động"],
                "steps": ["Nhập thông tin hợp lệ", "Gửi biểu mẫu"],
                "expected": ["Hệ thống tạo phiên và ghi nhật ký"],
            },
        },
    )
    assert updated["revision"] == 2
    stale = request(
        client,
        "PATCH",
        f"/kiem-thu/mau-ca-kiem-thu/{template_id}",
        409,
        headers=TESTER,
        json={"expected_revision": 1, "description": "Ghi đè dữ liệu cũ"},
    )
    assert stale["error"]["code"] == "REVISION_CONFLICT"
    denied_archive = request(
        client,
        "POST",
        f"/kiem-thu/mau-ca-kiem-thu/{template_id}/luu-tru",
        403,
        headers=TESTER,
        json={"expected_revision": 2, "reason": "Thử lưu trữ khi chưa được cấp chính sách"},
    )
    assert denied_archive["error"]["code"] == "PROJECT_ACTION_POLICY_DENIED"
    archived = request(
        client,
        "POST",
        f"/kiem-thu/mau-ca-kiem-thu/{template_id}/luu-tru",
        headers=QA_LEAD,
        json={"expected_revision": 2, "reason": "Thay thế bằng mẫu đã chuẩn hóa"},
    )
    assert archived["status"] == "ARCHIVED"
    assert archived["revision"] == 3
    assert request(
        client,
        "GET",
        f"/kiem-thu/du-an/{project_id}/mau-ca-kiem-thu",
        headers=VIEWER,
    ) == []
    retained = request(
        client,
        "GET",
        f"/kiem-thu/mau-ca-kiem-thu/{template_id}",
        headers=VIEWER,
    )
    assert retained["definition"] == updated["definition"]
    assert retained["archive_reason"] == "Thay thế bằng mẫu đã chuẩn hóa"
    denied_create = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/mau-ca-kiem-thu",
        403,
        headers=VIEWER,
        json={"name": "Mẫu Viewer", "template_type": "api"},
    )
    assert denied_create["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    outsider_read = request(
        client,
        "GET",
        f"/kiem-thu/mau-ca-kiem-thu/{template_id}",
        403,
        headers=OUTSIDER,
    )
    assert outsider_read["error"]["code"] == "PROJECT_MEMBERSHIP_REQUIRED"
    policy_template = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/mau-ca-kiem-thu",
        201,
        headers=TESTER,
        json={
            "name": "Kiểm tra phân quyền",
            "template_type": "rbac",
            "description": "Mẫu kiểm tra vai trò và quyền",
            "definition": {"roles": ["QA_LEAD", "TESTER"], "expected": ["Từ chối sai quyền"]},
        },
    )
    request(
        client,
        "PATCH",
        f"/kiem-thu/du-an/{project_id}/cai-dat",
        json={
            "expected_revision": 1,
            "settings": {
                "tester_can_archive_testcase_templates": True,
                "action_policies": {"testcase.template.archive": ["QA_LEAD", "TESTER"]},
            },
        },
    )
    policy_archived = request(
        client,
        "POST",
        f"/kiem-thu/mau-ca-kiem-thu/{policy_template['_id']}/luu-tru",
        headers=TESTER,
        json={"expected_revision": 1, "reason": "Tester được phép theo chính sách dự án"},
    )
    assert policy_archived["status"] == "ARCHIVED"
    audit_events = request(client, "GET", f"/kiem-thu/du-an/{project_id}/nhat-ky")
    actions = {item["action"] for item in audit_events}
    assert {
        "test_case_template_created",
        "test_case_template_updated",
        "test_case_template_archived",
    } <= actions

print("test case template integration passed")
