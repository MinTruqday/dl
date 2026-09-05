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


LEAD = identity("design-lead")
TESTER = identity("design-tester")
VIEWER = identity("design-viewer")


def request(client, method, path, expected=200, headers=LEAD, **kwargs):
    response = client.request(method, path, headers=headers, **kwargs)
    assert response.status_code == expected, f"{method} {path} {response.status_code} {response.text}"
    body = response.json()
    return body.get("data") if expected < 400 else body


with httpx.Client(base_url=BASE_URL, timeout=60) as client:
    stamp = int(time.time() * 1000)
    project = request(
        client,
        "POST",
        "/kiem-thu/du-an",
        201,
        json={"key": f"SD{stamp}", "name": "Thiết kế kiểm thử chuyên sâu", "project_type": "web"},
    )
    project_id = project["_id"]
    for user_id, role in [("design-tester", "TESTER"), ("design-viewer", "VIEWER")]:
        request(
            client,
            "POST",
            f"/kiem-thu/du-an/{project_id}/thanh-vien",
            201,
            json={"user_id": user_id, "project_role": role},
        )
    security = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ai/goi-y-kiem-thu-bao-mat",
        201,
        headers=TESTER,
        json={
            "categories": ["authorization", "input_validation", "session"],
            "context": "Luồng đăng nhập và quản trị dự án",
            "idempotency_key": f"security-{stamp}",
        },
    )
    assert security["candidate_only"] is True
    assert security["vulnerability_scan_performed"] is False
    assert all(item["status"] == "SUGGESTED" for item in security["candidates"])
    replayed = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ai/goi-y-kiem-thu-bao-mat",
        201,
        headers=TESTER,
        json={
            "categories": ["authorization", "input_validation", "session"],
            "context": "Luồng đăng nhập và quản trị dự án",
            "idempotency_key": f"security-{stamp}",
        },
    )
    assert replayed["_id"] == security["_id"]
    assert request(
        client,
        "GET",
        f"/kiem-thu/du-an/{project_id}/ai/goi-y-kiem-thu-bao-mat",
        headers=TESTER,
    )[0]["_id"] == security["_id"]
    performance = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ai/ke-hoach-hieu-nang",
        201,
        headers=TESTER,
        json={
            "name": "Kế hoạch tải đăng nhập",
            "objective": "Đánh giá tải mục tiêu không thực thi phát tải trong bước thiết kế",
            "workload_types": ["baseline", "load", "spike", "soak"],
            "target_virtual_users": 100,
            "target_requests_per_second": 50,
            "duration_minutes": 30,
            "response_time_p95_ms": 800,
            "maximum_error_rate": 0.01,
            "idempotency_key": f"performance-{stamp}",
        },
    )
    assert performance["status"] == "DRAFT"
    assert performance["load_execution_performed"] is False
    assert len(performance["scenarios"]) == 4
    assert request(
        client,
        "GET",
        f"/kiem-thu/du-an/{project_id}/ai/ke-hoach-hieu-nang",
        headers=TESTER,
    )[0]["_id"] == performance["_id"]
    denied = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ai/ke-hoach-hieu-nang",
        403,
        headers=VIEWER,
        json={
            "name": "Không được phép",
            "idempotency_key": f"performance-viewer-{stamp}",
        },
    )
    assert denied["error"]["code"] == "PROJECT_PERMISSION_DENIED"

print("specialized AI design integration passed")
