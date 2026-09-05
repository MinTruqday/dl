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


LEAD = identity("notification-lead")
TESTER = identity("notification-tester")
VIEWER = identity("notification-viewer")


def request(client, method, path, expected=200, headers=LEAD, **kwargs):
    response = client.request(method, path, headers=headers, **kwargs)
    assert response.status_code == expected, f"{method} {path} {response.status_code} {response.text}"
    body = response.json()
    return body.get("data") if expected < 400 else body


with httpx.Client(base_url=BASE_URL, timeout=30) as client:
    stamp = int(time.time() * 1000)
    project = request(
        client,
        "POST",
        "/kiem-thu/du-an",
        201,
        json={"key": f"NT{stamp}", "name": "Thông báo dự án", "project_type": "web"},
    )
    project_id = project["_id"]
    for user_id, role in [
        ("notification-tester", "TESTER"),
        ("notification-viewer", "VIEWER"),
    ]:
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
            "title": "Gửi thông báo khi yêu cầu thay đổi",
            "content_doc": {"type": "doc", "content": []},
        },
    )
    watched = request(
        client,
        "PUT",
        f"/kiem-thu/du-an/{project_id}/thong-bao/theo-doi/requirement/{requirement['_id']}",
        headers=VIEWER,
        json={"watching": True},
    )
    assert watched["user_id"] == "notification-viewer"
    replayed = request(
        client,
        "PUT",
        f"/kiem-thu/du-an/{project_id}/thong-bao/theo-doi/requirement/{requirement['_id']}",
        headers=VIEWER,
        json={"watching": True},
    )
    assert replayed["_id"] == watched["_id"]
    viewer_watches = request(
        client,
        "GET",
        f"/kiem-thu/du-an/{project_id}/thong-bao/theo-doi",
        headers=VIEWER,
    )
    assert [item["_id"] for item in viewer_watches] == [watched["_id"]]
    assert request(
        client,
        "GET",
        f"/kiem-thu/du-an/{project_id}/thong-bao/theo-doi",
        headers=TESTER,
    ) == []
    removed = request(
        client,
        "PUT",
        f"/kiem-thu/du-an/{project_id}/thong-bao/theo-doi/requirement/{requirement['_id']}",
        headers=VIEWER,
        json={"watching": False},
    )
    assert removed["watching"] is False
    assert request(
        client,
        "GET",
        f"/kiem-thu/du-an/{project_id}/thong-bao/quy-tac",
    )["revision"] == 0
    denied_rules = request(
        client,
        "PATCH",
        f"/kiem-thu/du-an/{project_id}/thong-bao/quy-tac",
        403,
        headers=TESTER,
        json={
            "expected_revision": 0,
            "enabled_events": ["DEFECT_CREATED"],
            "channels": ["in_app"],
            "target_roles": ["QA_LEAD"],
        },
    )
    assert denied_rules["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    rules = request(
        client,
        "PATCH",
        f"/kiem-thu/du-an/{project_id}/thong-bao/quy-tac",
        json={
            "expected_revision": 0,
            "enabled_events": ["DEFECT_CREATED", "TEST_RUN_FAILED"],
            "channels": ["in_app", "email"],
            "target_roles": ["QA_LEAD", "TESTER"],
            "escalation_minutes": 30,
        },
    )
    assert rules["revision"] == 1
    assert rules["escalation_minutes"] == 30
    assert request(
        client,
        "GET",
        f"/kiem-thu/du-an/{project_id}/thong-bao/tuy-chon",
        headers=VIEWER,
    )["revision"] == 0
    preferences = request(
        client,
        "PATCH",
        f"/kiem-thu/du-an/{project_id}/thong-bao/tuy-chon",
        headers=VIEWER,
        json={
            "expected_revision": 0,
            "digest_frequency": "daily",
            "channels": ["in_app", "email"],
            "muted_events": ["COMMENT_RESOLVED"],
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "07:00",
            "timezone": "Asia/Ho_Chi_Minh",
        },
    )
    assert preferences["user_id"] == "notification-viewer"
    assert preferences["digest_frequency"] == "daily"
    tester_preferences = request(
        client,
        "GET",
        f"/kiem-thu/du-an/{project_id}/thong-bao/tuy-chon",
        headers=TESTER,
    )
    assert tester_preferences["user_id"] == "notification-tester"
    assert tester_preferences["revision"] == 0

print("project notification integration passed")
