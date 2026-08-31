from src.main import app
import httpx
import pytest


def _api_operations():
    operations = []
    for route in app.routes:
        if not route.path.startswith("/api/"):
            continue
        for method in route.methods or set():
            if method in {"HEAD", "OPTIONS"}:
                continue
            operations.append((method, route.path, route))
    return operations


def test_api_route_inventory_has_no_duplicate_operations():
    operations = _api_operations()
    keys = [(method, path) for method, path, _ in operations]
    assert len(keys) == len(set(keys))
    assert len(keys) >= 200


def test_api_routes_require_identity_or_internal_authentication():
    spec = app.openapi()
    unprotected = []
    for method, path, _ in _api_operations():
        operation = spec["paths"][path][method.lower()]
        if not operation.get("security") and path != "/api/qa/internal/jobs/{event}":
            unprotected.append(f"{method} {path}")
    assert unprotected == []


def test_api_operations_have_unique_ids_and_success_error_responses():
    spec = app.openapi()
    operation_ids = []
    incomplete = []
    for method, path, _ in _api_operations():
        operation = spec["paths"][path][method.lower()]
        operation_ids.append(operation.get("operationId"))
        responses = operation.get("responses", {})
        has_success = any(code.startswith("2") for code in responses)
        has_client_error = any(code in responses for code in ("401", "403", "422"))
        if not has_success or (path != "/api/qa/internal/jobs/{event}" and not has_client_error):
            incomplete.append(f"{method} {path}")
    assert None not in operation_ids
    assert len(operation_ids) == len(set(operation_ids))
    assert incomplete == []


def test_v43_route_groups_are_registered():
    paths = {path for _, path, _ in _api_operations()}
    required_prefixes = {
        "/api/qa/projects/{project_id}/requirements",
        "/api/qa/projects/{project_id}/test-cases",
        "/api/qa/projects/{project_id}/test-plans",
        "/api/qa/projects/{project_id}/test-suites",
        "/api/qa/projects/{project_id}/test-runs",
        "/api/qa/projects/{project_id}/defects",
        "/api/qa/projects/{project_id}/traceability",
        "/api/qa/projects/{project_id}/change-sets",
        "/api/qa/projects/{project_id}/knowledge/search",
        "/api/qa/projects/{project_id}/reports/execution",
        "/api/qa/projects/{project_id}/reports/defects",
    }
    assert required_prefixes <= paths


@pytest.mark.asyncio
async def test_every_api_operation_rejects_anonymous_requests_without_server_error():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        for method, path, _ in _api_operations():
            request_path = path.replace("{project_id}", "PROJECT-1")
            request_path = request_path.replace("{", "").replace("}", "")
            response = await client.request(method, request_path)
            assert response.status_code in {401, 403, 405, 422}, (
                method,
                path,
                response.status_code,
                response.text[:300],
            )
