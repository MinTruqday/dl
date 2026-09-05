import os
import time

import httpx
import jwt


BASE_URL = os.getenv("TESTING_TEST_URL", "http://testing:8000")
HEADERS = {
    "Authorization": "Bearer "
    + jwt.encode(
        {"uid": "automation-lead", "sub": "automation-lead@test.local", "system_role": "USER"},
        os.environ["SECRET_KEY"],
        algorithm="HS256",
    )
}


def request(client, method, path, expected=200, **kwargs):
    response = client.request(method, path, headers=HEADERS, **kwargs)
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
        json={"key": f"AU{stamp}", "name": "Thực thi tự động", "project_type": "api"},
    )
    project_id = project["_id"]
    imported = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/dac-ta-giao-dien/nhap",
        201,
        json={
            "filename": "collection.json",
            "format": "postman",
            "content": {
                "info": {"name": "Kiểm tra sức khỏe", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"},
                "item": [
                    {
                        "name": "Sức khỏe",
                        "request": {"method": "GET", "url": {"raw": "http://nginx/suc-khoe"}},
                    }
                ],
            },
        },
    )
    reviewed = request(
        client,
        "PATCH",
        f"/kiem-thu/dac-ta-giao-dien/{imported['_id']}/ra-soat",
        json={"expected_revision": imported["revision"], "selected_indexes": [0], "review_note": "Đã rà soát"},
    )
    confirmed = request(
        client,
        "POST",
        f"/kiem-thu/dac-ta-giao-dien/{imported['_id']}/xac-nhan",
        json={"expected_revision": reviewed["revision"], "idempotency_key": f"confirm-{stamp}"},
    )
    execution = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/thuc-thi-tu-dong",
        201,
        json={"name": "Newman sức khỏe", "postman_artifact_id": confirmed["_id"], "idempotency_key": f"auto-{stamp}"},
    )
    execution_id = execution["_id"]
    assert request(client, "GET", f"/kiem-thu/du-an/{project_id}/thuc-thi-tu-dong")[0]["_id"] == execution_id
    assert request(client, "GET", f"/kiem-thu/thuc-thi-tu-dong/{execution_id}")["status"] == "CREATED"
    assert request(client, "GET", f"/kiem-thu/thuc-thi-tu-dong/{execution_id}/bang-chung")["results"] == []
    invalid_start = request(
        client,
        "POST",
        f"/kiem-thu/thuc-thi-tu-dong/{execution_id}/bat-dau",
        409,
        json={"expected_revision": execution["revision"] + 1, "idempotency_key": f"start-{stamp}"},
    )
    assert invalid_start["error"]["code"] == "AUTOMATION_STATE_CONFLICT"
    invalid_cancel = request(
        client,
        "POST",
        f"/kiem-thu/thuc-thi-tu-dong/{execution_id}/huy",
        409,
        json={"expected_revision": execution["revision"], "idempotency_key": f"cancel-{stamp}"},
    )
    assert invalid_cancel["error"]["code"] == "AUTOMATION_NOT_CANCELLABLE"

print("automation execution integration passed")
