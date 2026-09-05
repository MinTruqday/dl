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


LEAD = identity("device-matrix-lead")
TESTER = identity("device-matrix-tester")
VIEWER = identity("device-matrix-viewer")


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
        json={"key": f"DM{stamp}", "name": "Ma trận thiết bị", "project_type": "web"},
    )
    project_id = project["_id"]
    for user_id, role in [
        ("device-matrix-tester", "TESTER"),
        ("device-matrix-viewer", "VIEWER"),
    ]:
        request(
            client,
            "POST",
            f"/kiem-thu/du-an/{project_id}/thanh-vien",
            201,
            json={"user_id": user_id, "project_role": role},
        )
    matrix = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ma-tran-thiet-bi",
        201,
        json={
            "name": "Trình duyệt chính",
            "description": "Phạm vi trình duyệt được hỗ trợ",
            "profiles": [
                {
                    "key": "chrome-desktop",
                    "name": "Chrome máy tính",
                    "device_type": "desktop",
                    "operating_system": "Windows",
                    "operating_system_version": "11",
                    "browser": "Chrome",
                    "browser_version": "ổn định",
                    "viewport_width": 1440,
                    "viewport_height": 900,
                },
                {
                    "key": "safari-mobile",
                    "name": "Safari điện thoại",
                    "device_type": "mobile",
                    "operating_system": "iOS",
                    "browser": "Safari",
                    "viewport_width": 390,
                    "viewport_height": 844,
                },
            ],
        },
    )
    matrix_id = matrix["_id"]
    assert len(request(client, "GET", f"/kiem-thu/du-an/{project_id}/ma-tran-thiet-bi", headers=VIEWER)) == 1
    assert request(client, "GET", f"/kiem-thu/ma-tran-thiet-bi/{matrix_id}", headers=VIEWER)["_id"] == matrix_id
    denied = request(
        client,
        "PATCH",
        f"/kiem-thu/ma-tran-thiet-bi/{matrix_id}",
        403,
        headers=TESTER,
        json={"expected_revision": 1, "description": "Không được quản lý"},
    )
    assert denied["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    plan = request(
        client,
        "POST",
        "/kiem-thu/ke-hoach-kiem-thu",
        201,
        json={"project_id": project_id, "name": "Kế hoạch đa thiết bị"},
    )
    assigned_plan = request(
        client,
        "POST",
        f"/kiem-thu/ma-tran-thiet-bi/{matrix_id}/gan",
        headers=TESTER,
        json={
            "target_type": "test_plan",
            "target_id": plan["_id"],
            "expected_target_revision": plan["revision"],
            "profile_keys": ["chrome-desktop"],
        },
    )
    assert assigned_plan["device_matrix_snapshot"]["profile_keys"] == ["chrome-desktop"]
    run = request(
        client,
        "POST",
        "/kiem-thu/lan-chay-kiem-thu",
        201,
        json={
            "project_id": project_id,
            "name": "Lần chạy đa thiết bị",
            "test_plan_id": plan["_id"],
        },
    )
    assert run["device_matrix_id"] == matrix_id
    assert run["device_matrix_snapshot"] == assigned_plan["device_matrix_snapshot"]
    request(client, "POST", f"/kiem-thu/lan-chay-kiem-thu/{run['_id']}/bat-dau")
    frozen = request(
        client,
        "POST",
        f"/kiem-thu/ma-tran-thiet-bi/{matrix_id}/gan",
        409,
        headers=TESTER,
        json={
            "target_type": "test_run",
            "target_id": run["_id"],
            "expected_target_revision": 2,
            "profile_keys": ["safari-mobile"],
        },
    )
    assert frozen["error"]["code"] == "DEVICE_MATRIX_TARGET_SCOPE_FROZEN"
    archived = request(
        client,
        "POST",
        f"/kiem-thu/ma-tran-thiet-bi/{matrix_id}/luu-tru",
        json={"expected_revision": matrix["revision"], "reason": "Đã thay bằng phạm vi mới"},
    )
    assert archived["status"] == "ARCHIVED"

print("device matrix integration passed")
