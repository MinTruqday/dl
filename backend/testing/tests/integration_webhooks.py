import hashlib
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


LEAD = identity("webhook-lead")
TESTER = identity("webhook-tester")


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
        json={"key": f"WH{stamp}", "name": "Móc gọi dự án", "project_type": "web"},
    )
    project_id = project["_id"]
    request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/thanh-vien",
        201,
        json={"user_id": "webhook-tester", "project_role": "TESTER"},
    )
    denied = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/moc-goi",
        403,
        headers=TESTER,
        json={
            "name": "Không được phép",
            "endpoint_reference": "endpoint://platform/denied",
            "secret_reference": "secret://platform/denied",
            "events": ["DEFECT_CREATED"],
        },
    )
    assert denied["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    raw_reference = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/moc-goi",
        422,
        json={
            "name": "Điểm cuối không hợp lệ",
            "endpoint_reference": "https://example.test/hook",
            "secret_reference": "plain-secret",
            "events": ["DEFECT_CREATED"],
        },
    )
    assert raw_reference["error"]["code"] == "VALIDATION_ERROR"
    subscription = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/moc-goi",
        201,
        json={
            "name": "Thông báo lỗi mới",
            "endpoint_reference": "endpoint://platform/webhook-primary",
            "secret_reference": "secret://platform/webhook-primary",
            "events": ["DEFECT_CREATED", "DEFECT_READY_FOR_RETEST"],
        },
    )
    assert subscription["endpoint_reference"] == "Đã cấu hình"
    assert subscription["secret_reference"] == "Đã cấu hình"
    subscription_id = subscription["_id"]
    listed = request(client, "GET", f"/kiem-thu/du-an/{project_id}/moc-goi")
    assert listed[0]["_id"] == subscription_id
    assert "endpoint://" not in str(listed)
    updated = request(
        client,
        "PATCH",
        f"/kiem-thu/du-an/{project_id}/moc-goi/{subscription_id}",
        json={
            "expected_revision": 1,
            "events": ["DEFECT_CREATED"],
            "enabled": True,
        },
    )
    assert updated["revision"] == 2
    delivery_id = f"WHD-{stamp}"
    recorded = request(
        client,
        "POST",
        "/noi-bo/kiem-thu/moc-goi/ket-qua",
        headers={"X-Internal-Token": os.environ["SECRET_KEY"]},
        json={
            "delivery_id": delivery_id,
            "project_id": project_id,
            "subscription_id": subscription_id,
            "event_type": "DEFECT_CREATED",
            "status": "FAILED",
            "attempt": 1,
            "response_status": 503,
            "error_code": "TARGET_UNAVAILABLE",
            "payload_hash": hashlib.sha256(b"redacted-payload").hexdigest(),
            "duration_ms": 125.5,
        },
    )
    assert recorded["status"] == "FAILED"
    assert "payload" not in recorded
    deliveries = request(
        client,
        "GET",
        f"/kiem-thu/du-an/{project_id}/moc-goi/giao-hang",
    )
    assert deliveries[0]["_id"] == delivery_id
    assert deliveries[0]["response_status"] == 503
    replay_key = f"webhook-replay-{stamp}"
    replayed = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/moc-goi/giao-hang/{delivery_id}/phat-lai",
        202,
        json={
            "idempotency_key": replay_key,
            "reason": "Điểm cuối đã hoạt động trở lại",
        },
    )
    assert replayed["status"] == "QUEUED"
    assert "secret_reference" not in replayed
    repeated = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/moc-goi/giao-hang/{delivery_id}/phat-lai",
        202,
        json={
            "idempotency_key": replay_key,
            "reason": "Phát lại an toàn",
        },
    )
    assert repeated["_id"] == replayed["_id"]

print("webhook integration passed")
