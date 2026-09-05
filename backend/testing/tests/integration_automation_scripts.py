import os
import time

import httpx
import jwt


BASE_URL = os.getenv("TESTING_TEST_URL", "http://testing:8000")


def identity(user_id):
    return {
        "Authorization": "Bearer "
        + jwt.encode(
            {"uid": user_id, "sub": f"{user_id}@test.local", "system_role": "USER"},
            os.environ["SECRET_KEY"],
            algorithm="HS256",
        )
    }


LEAD = identity("script-lead")
TESTER = identity("script-tester")


def doc(text):
    return {
        "type": "doc",
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
    }


def request(client, method, path, expected=200, headers=LEAD, raw=False, **kwargs):
    response = client.request(method, path, headers=headers, **kwargs)
    assert response.status_code == expected, f"{method} {path} {response.status_code} {response.text}"
    if raw:
        return response
    body = response.json()
    return body.get("data") if expected < 400 else body


def create_test_case_version(client, project_id):
    draft = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ban-nhap-ca-kiem-thu",
        201,
        json={
            "test_case_key": "TC-AUTO-001",
            "title": "Đăng nhập hợp lệ",
            "type": "happy_path",
            "priority": "high",
            "risk": "high",
            "objective_doc": doc("Kiểm tra đăng nhập"),
            "preconditions_doc": doc("Tài khoản đang hoạt động"),
            "steps": [
                {
                    "id": "step-login",
                    "order": 1,
                    "action_doc": doc("Đăng nhập bằng thông tin hợp lệ"),
                    "test_data": {},
                    "expected_doc": doc("Hệ thống tạo phiên đăng nhập"),
                }
            ],
            "expected_result_doc": doc("Hệ thống tạo phiên đăng nhập"),
            "postconditions_doc": doc("Phiên đang hoạt động"),
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
            "change_reason": "Chuẩn bị sinh kịch bản tự động",
            "review_note": "Đã rà soát",
        },
    )
    return frozen["version"]


with httpx.Client(base_url=BASE_URL, timeout=60) as client:
    stamp = int(time.time() * 1000)
    project = request(
        client,
        "POST",
        "/kiem-thu/du-an",
        201,
        json={
            "key": f"SC{stamp}",
            "name": "Kịch bản tự động hóa",
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
        json={"user_id": "script-tester", "project_role": "TESTER"},
    )
    version = create_test_case_version(client, project_id)
    draft = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ai/ban-nhap-kich-ban-tu-dong",
        201,
        headers=TESTER,
        json={
            "framework": "playwright",
            "language": "typescript",
            "test_case_version_id": version["_id"],
            "idempotency_key": f"script-{stamp}",
        },
    )
    assert draft["status"] == "DRAFT"
    assert draft["repository_write_performed"] is False
    assert "process.env.BASE_URL" in draft["source"]
    draft_id = draft["_id"]
    assert request(
        client,
        "GET",
        f"/kiem-thu/ban-nhap-kich-ban-tu-dong/{draft_id}",
        headers=TESTER,
    )["_id"] == draft_id
    assert request(
        client,
        "GET",
        f"/kiem-thu/du-an/{project_id}/ban-nhap-kich-ban-tu-dong",
        headers=TESTER,
    )[0]["_id"] == draft_id
    blocked_export = request(
        client,
        "GET",
        f"/kiem-thu/ban-nhap-kich-ban-tu-dong/{draft_id}/xuat",
        409,
        headers=TESTER,
    )
    assert blocked_export["error"]["code"] == "AUTOMATION_SCRIPT_NOT_APPROVED"
    raw_secret = request(
        client,
        "PATCH",
        f"/kiem-thu/ban-nhap-kich-ban-tu-dong/{draft_id}",
        422,
        headers=TESTER,
        json={
            "expected_revision": 1,
            "source": 'const password = "plain-password";',
        },
    )
    assert raw_secret["error"]["code"] == "RAW_SECRET_IN_SCRIPT"
    updated = request(
        client,
        "PATCH",
        f"/kiem-thu/ban-nhap-kich-ban-tu-dong/{draft_id}",
        headers=TESTER,
        json={
            "expected_revision": 1,
            "review_note": "Đã kiểm tra selector và dữ liệu",
            "filename": "dang-nhap.spec.ts",
        },
    )
    denied_approval = request(
        client,
        "POST",
        f"/kiem-thu/ban-nhap-kich-ban-tu-dong/{draft_id}/phe-duyet",
        403,
        headers=TESTER,
        json={"expected_revision": updated["revision"], "review_note": "Tự duyệt"},
    )
    assert denied_approval["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    approved = request(
        client,
        "POST",
        f"/kiem-thu/ban-nhap-kich-ban-tu-dong/{draft_id}/phe-duyet",
        json={
            "expected_revision": updated["revision"],
            "review_note": "QA Lead đã rà soát và phê duyệt xuất",
        },
    )
    assert approved["status"] == "APPROVED"
    exported = request(
        client,
        "GET",
        f"/kiem-thu/ban-nhap-kich-ban-tu-dong/{draft_id}/xuat",
        headers=TESTER,
        raw=True,
    )
    assert exported.headers["content-disposition"] == 'attachment; filename="dang-nhap.spec.ts"'
    assert "process.env.BASE_URL" in exported.text

print("automation script integration passed")
