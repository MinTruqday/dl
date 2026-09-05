import os
import time

import httpx
import jwt


BASE_URL = os.getenv("TESTING_TEST_URL", "http://testing:8000")
HEADERS = {"Authorization": "Bearer " + jwt.encode({"uid": "cicd-lead", "sub": "cicd-lead@test.local", "system_role": "USER"}, os.environ["SECRET_KEY"], algorithm="HS256")}


def request(client, method, path, expected=200, **kwargs):
    response = client.request(method, path, headers=HEADERS, **kwargs)
    assert response.status_code == expected, f"{method} {path} {response.status_code} {response.text}"
    body = response.json()
    return body.get("data") if expected < 400 else body


with httpx.Client(base_url=BASE_URL, timeout=60) as client:
    stamp = int(time.time() * 1000)
    project = request(client, "POST", "/kiem-thu/du-an", 201, json={"key": f"CI{stamp}", "name": "Triển khai liên tục", "project_type": "api"})
    project_id = project["_id"]
    connector = request(client, "POST", f"/kiem-thu/du-an/{project_id}/ket-noi", 201, json={"provider": "github", "connector_reference": "connector://platform/github-ci", "external_target": "company/product", "confirm_external_target": True})
    binding = request(client, "POST", f"/kiem-thu/du-an/{project_id}/tich-hop-trien-khai-lien-tuc", 201, json={"name": "Pipeline chính", "connector_id": connector["_id"], "pipeline_reference": "pipeline://platform/github-main", "test_case_version_ids": []})
    state = request(client, "GET", f"/kiem-thu/du-an/{project_id}/tich-hop-trien-khai-lien-tuc")
    assert state["bindings"][0]["pipeline_reference"] == "Đã cấu hình"
    updated = request(client, "PATCH", f"/kiem-thu/du-an/{project_id}/tich-hop-trien-khai-lien-tuc/{binding['_id']}", json={"expected_revision": binding["revision"], "name": "Pipeline phát hành"})
    assert updated["name"] == "Pipeline phát hành"
    not_retryable = request(client, "POST", f"/kiem-thu/du-an/{project_id}/tich-hop-trien-khai-lien-tuc/lan-chay/khong-ton-tai/thu-lai", 404, json={"expected_revision": 1, "idempotency_key": f"retry-{stamp}", "reason": "Kiểm tra giới hạn dự án"})
    assert not_retryable["error"]["code"] == "ENTITY_NOT_FOUND"

print("cicd integration passed")
