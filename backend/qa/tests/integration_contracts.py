import os

import httpx


SERVICES = {
    "authentication": os.getenv("AUTH_TEST_URL", "http://authentication:8000"),
    "content": os.getenv("CONTENT_TEST_URL", "http://content:8000"),
    "rag": os.getenv("RAG_TEST_URL", "http://rag:8000"),
    "ai": os.getenv("AI_TEST_URL", "http://ai:8000"),
    "qa": os.getenv("QA_TEST_URL", "http://qa:8000"),
}


for name, base_url in SERVICES.items():
    with httpx.Client(base_url=base_url, timeout=20) as client:
        health = client.get("/health")
        assert health.status_code == 200, f"{name} health contract failed {health.text}"
        schema = client.get("/openapi.json")
        assert schema.status_code == 200, f"{name} schema contract failed {schema.text}"
        assert schema.json().get("paths"), f"{name} exposes no API paths"

with httpx.Client(base_url=SERVICES["qa"], timeout=20) as client:
    unauthenticated = client.get("/api/qa/projects")
    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["error"]["code"] == "REQUEST_FAILED"
    malformed = client.post(
        "/api/qa/projects",
        headers={"x-test-user-id": "contract-user", "x-test-user-role": "author"},
        json={"key": "invalid key", "name": ""},
    )
    assert malformed.status_code == 422
    assert malformed.json()["error"]["code"] == "VALIDATION_ERROR"
    paths = client.get("/openapi.json").json()["paths"]
    required = {
        "/api/qa/projects",
        "/api/qa/projects/{project_id}/requirements",
        "/api/qa/projects/{project_id}/test-case-drafts",
        "/api/qa/projects/{project_id}/traceability",
        "/api/qa/change-sets/{change_set_id}/impact-analysis",
        "/api/qa/test-runs/{run_id}/report",
    }
    assert required <= set(paths)

print("service contracts passed")
