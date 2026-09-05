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


LEAD = identity("connector-lead")
TESTER = identity("connector-tester")


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
        json={"key": f"CN{stamp}", "name": "Kết nối dự án", "project_type": "web"},
    )
    project_id = project["_id"]
    request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/thanh-vien",
        201,
        json={"user_id": "connector-tester", "project_role": "TESTER"},
    )
    invalid = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ket-noi",
        422,
        json={
            "provider": "github",
            "connector_reference": "https://github.test/token",
            "external_target": "company/product",
            "confirm_external_target": True,
        },
    )
    assert invalid["error"]["code"] == "VALIDATION_ERROR"
    connector = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ket-noi",
        201,
        json={
            "provider": "github",
            "connector_reference": "connector://platform/github-primary",
            "external_target": "company/product",
            "confirm_external_target": True,
            "field_mapping": {"defect.title": "issue.title"},
        },
    )
    connector_id = connector["_id"]
    assert connector["connector_reference"] == "Đã cấu hình"
    listed = request(client, "GET", f"/kiem-thu/du-an/{project_id}/ket-noi", headers=TESTER)
    assert listed[0]["_id"] == connector_id
    updated = request(
        client,
        "PATCH",
        f"/kiem-thu/du-an/{project_id}/ket-noi/{connector_id}",
        json={
            "expected_revision": connector["revision"],
            "field_mapping": {"defect.status": "issue.state"},
        },
    )
    assert updated["mapping_version"] == 2
    sync_payload = {
        "direction": "PULL",
        "scopes": ["defects"],
        "idempotency_key": f"connector-sync-{stamp}",
    }
    first_sync = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ket-noi/{connector_id}/dong-bo",
        202,
        headers=TESTER,
        json=sync_payload,
    )
    replay_sync = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ket-noi/{connector_id}/dong-bo",
        202,
        headers=TESTER,
        json=sync_payload,
    )
    assert first_sync["_id"] == replay_sync["_id"]
    logs = request(
        client,
        "GET",
        f"/kiem-thu/du-an/{project_id}/ket-noi/nhat-ky",
        headers=TESTER,
    )
    assert logs[0]["_id"] == first_sync["_id"]
    assert request(client, "GET", f"/kiem-thu/du-an/{project_id}/ket-noi/xung-dot") == []
    missing_conflict = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ket-noi/xung-dot/khong-ton-tai/giai-quyet",
        404,
        json={
            "expected_revision": 1,
            "resolution": "KEEP_LOCAL",
            "reason": "Giữ dữ liệu đã được rà soát trong dự án",
        },
    )
    assert missing_conflict["error"]["code"] == "ENTITY_NOT_FOUND"
    unbound = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ket-noi/{connector_id}/ngat",
        json={
            "expected_revision": updated["revision"],
            "reason": "Không còn sử dụng kho mã nguồn này",
            "confirm_external_target": True,
        },
    )
    assert unbound["status"] == "UNBOUND"

print("connector integration passed")
