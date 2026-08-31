import os

import httpx
import jwt


SERVICES = {
    "authentication": os.getenv("AUTH_TEST_URL", "http://authentication:8000"),
    "content": os.getenv("CONTENT_TEST_URL", "http://content:8000"),
    "knowledge": os.getenv("KNOWLEDGE_TEST_URL", "http://ai:8000"),
    "ai": os.getenv("AI_TEST_URL", "http://ai:8000"),
    "testing": os.getenv("TESTING_TEST_URL", "http://testing:8000"),
}


for name, base_url in SERVICES.items():
    with httpx.Client(base_url=base_url, timeout=20) as client:
        health = client.get("/health")
        assert health.status_code == 200, f"{name} health contract failed {health.text}"
        schema = client.get("/openapi.json")
        assert schema.status_code == 200, f"{name} schema contract failed {schema.text}"
        assert schema.json().get("paths"), f"{name} exposes no API paths"

with httpx.Client(base_url=SERVICES["testing"], timeout=20) as client:
    unauthenticated = client.get("/api/qa/projects")
    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["error"]["code"] == "AUTH_REQUIRED"
    malformed = client.post(
        "/api/qa/projects",
        headers={
            "Authorization": "Bearer "
            + jwt.encode(
                {"uid": "contract-user", "sub": "contract-user@example.com", "system_role": "USER"},
                os.environ["SECRET_KEY"],
                algorithm="HS256",
            )
        },
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
        "/api/qa/projects/{project_id}/requirements/{requirement_id}",
        "/api/qa/projects/{project_id}/test-cases/{draft_id}",
        "/api/qa/projects/{project_id}/test-executions/{execution_id}",
        "/api/qa/projects/{project_id}/test-results",
        "/api/qa/projects/{project_id}/coverage-snapshots",
        "/api/qa/requirements/{requirement_id}/diff",
        "/api/qa/test-cases/{test_case_id}/trace",
        "/api/qa/requirements/{requirement_id}/obsolete",
        "/api/qa/test-cases/{test_case_id}/clone",
        "/api/qa/test-cases/{test_case_id}/obsolete",
        "/api/qa/requirement-imports/{job_id}",
        "/api/qa/requirement-documents/{document_id}/retry-parse",
        "/api/qa/change-sets/{change_set_id}/review",
        "/api/qa/projects/{project_id}/data-sets",
        "/api/qa/data-sets/{data_set_id}/versions",
        "/api/qa/defects/{defect_id}/trace-candidates",
        "/api/qa/maintenance-proposals/{proposal_id}/regenerate",
        "/api/qa/projects/{project_id}/bulk/tags",
        "/api/qa/projects/{project_id}/bulk/test-cases/add-to-suite",
        "/api/qa/projects/{project_id}/bulk/test-cases/mark-review-required",
        "/api/qa/projects/{project_id}/bulk/archive",
        "/api/qa/projects/{project_id}/bulk/impact-proposals",
        "/api/qa/projects/{project_id}/bulk/approve-proposals",
        "/api/qa/operations",
        "/api/qa/operations/jobs/{job_id}/retry",
        "/api/qa/projects/{project_id}/trace-links",
        "/api/qa/projects/{project_id}/trace-links/{link_id}/confirm",
        "/api/qa/projects/{project_id}/changesets/{change_set_id}/analyze-impact",
        "/api/qa/projects/{project_id}/ai-proposals/{proposal_id}/review",
        "/api/qa/projects/{project_id}/ai-proposals/{proposal_id}/approve",
        "/api/qa/projects/{project_id}/regression/generate",
        "/api/qa/projects/{project_id}/regression/{recommendation_id}/approve",
        "/api/qa/projects/{project_id}/test-runs",
        "/api/qa/projects/{project_id}/test-runs/{run_id}",
        "/api/qa/projects/{project_id}/test-runs/{run_id}/assign",
        "/api/qa/projects/{project_id}/defects/{defect_id}",
        "/api/qa/requirements/{requirement_id}/restore",
        "/api/qa/projects/{project_id}/reports/execution",
        "/api/qa/projects/{project_id}/reports/defects",
        "/api/qa/projects/{project_id}/activity",
        "/api/qa/projects/{project_id}/ai/ask",
        "/api/qa/requirements/{requirement_id}/dependencies",
        "/api/qa/requirements/{requirement_id}/dependencies/{dependency_requirement_id}",
        "/api/qa/test-plans/{plan_id}/clone",
        "/api/qa/test-scenarios/{scenario_id}",
        "/api/qa/maintenance-proposals/{proposal_id}",
        "/api/qa/regression-recommendations/{recommendation_id}",
        "/api/qa/requirement-documents/{document_id}/reindex",
    }
    assert required <= set(paths)

print("service contracts passed")
