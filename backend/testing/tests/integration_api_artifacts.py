import os
import time

import httpx
import jwt


BASE_URL = os.getenv("TESTING_TEST_URL", "http://testing:8000")
SECRET_KEY = os.environ["SECRET_KEY"]


def headers(user_id):
    token = jwt.encode(
        {"uid": user_id, "sub": f"{user_id}@test.local", "system_role": "USER"},
        SECRET_KEY,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def call(client, method, path, expected, **kwargs):
    response = client.request(method, path, **kwargs)
    assert response.status_code == expected, f"{method} {path} {response.status_code} {response.text}"
    return response.json().get("data")


with httpx.Client(base_url=BASE_URL, timeout=60, headers=headers("api-artifact-lead")) as client:
    stamp = int(time.time() * 1000)
    project = call(
        client,
        "POST",
        "/kiem-thu/du-an",
        201,
        json={"key": f"API{stamp}", "name": "API artifact integration", "project_type": "web", "settings": {}},
    )
    project_id = project["_id"]
    openapi = {
        "openapi": "3.1.0",
        "paths": {
            "/users/{id}": {
                "get": {
                    "operationId": "readUser",
                    "summary": "Read user",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {"200": {"description": "ok"}, "401": {"description": "unauthorized"}, "404": {"description": "missing"}},
                }
            }
        },
    }
    imported = call(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/dac-ta-giao-dien/nhap",
        201,
        json={"filename": "openapi.json", "format": "openapi", "content": openapi},
    )
    assert imported["status"] == "PREVIEW_READY"
    assert len(imported["preview"]) == 1
    reviewed = call(
        client,
        "PATCH",
        f"/kiem-thu/dac-ta-giao-dien/{imported['_id']}/ra-soat",
        200,
        json={"expected_revision": 1, "selected_indexes": [0], "review_note": "Đã rà soát"},
    )
    confirmed = call(
        client,
        "POST",
        f"/kiem-thu/dac-ta-giao-dien/{imported['_id']}/xac-nhan",
        200,
        json={"expected_revision": reviewed["revision"], "idempotency_key": f"confirm-{stamp}"},
    )
    operation_id = confirmed["operations"][0]["_id"]
    operations = call(client, "GET", f"/kiem-thu/du-an/{project_id}/dac-ta-giao-dien/thao-tac", 200)
    assert operations[0]["operation_id"] == "readUser"
    generated = call(client, "POST", f"/kiem-thu/dac-ta-giao-dien/thao-tac/{operation_id}/sinh-ca-kiem-thu", 201)
    assert {"success", "required_missing", "auth", "not_found"} <= {item["tags"][1] for item in generated["items"]}
    postman = {
        "variable": [{"key": "baseUrl", "value": "https://example.test"}],
        "item": [{"name": "List users", "request": {"method": "GET", "url": "{{baseUrl}}/users"}}],
    }
    imported_postman = call(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/dac-ta-giao-dien/nhap",
        201,
        json={"filename": "collection.json", "format": "postman", "content": postman},
    )
    assert imported_postman["preview"][0]["source_type"] == "postman"

print("API artifact integration passed")
