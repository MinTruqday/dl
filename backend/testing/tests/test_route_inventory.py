from src.main import app
import httpx
import pytest


def _api_operations():
    operations = []
    for route in app.routes:
        if not route.path.startswith("/kiem-thu/"):
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
        if not operation.get("security") and path != "/kiem-thu/noi-bo/tac-vu/{event}":
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
        if not has_success or (path != "/kiem-thu/noi-bo/tac-vu/{event}" and not has_client_error):
            incomplete.append(f"{method} {path}")
    assert None not in operation_ids
    assert len(operation_ids) == len(set(operation_ids))
    assert incomplete == []


def test_v43_route_groups_are_registered():
    paths = {path for _, path, _ in _api_operations()}
    required_prefixes = {
        "/kiem-thu/du-an/{project_id}/yeu-cau",
        "/kiem-thu/du-an/{project_id}/ca-kiem-thu",
        "/kiem-thu/du-an/{project_id}/ke-hoach-kiem-thu",
        "/kiem-thu/du-an/{project_id}/bo-kiem-thu",
        "/kiem-thu/du-an/{project_id}/lan-chay-kiem-thu",
        "/kiem-thu/du-an/{project_id}/loi",
        "/kiem-thu/du-an/{project_id}/truy-vet",
        "/kiem-thu/du-an/{project_id}/bo-thay-doi",
        "/kiem-thu/du-an/{project_id}/tri-thuc/tim-kiem",
        "/kiem-thu/du-an/{project_id}/bao-cao/thuc-thi",
        "/kiem-thu/du-an/{project_id}/bao-cao/loi",
    }
    assert required_prefixes <= paths


def test_template_routes_expose_canonical_function_ids():
    spec = app.openapi()
    assert spec["paths"]["/kiem-thu/du-an/{project_id}/mau-ca-kiem-thu"]["get"][
        "x-function-ids"
    ] == ["TPLT-01"]
    assert spec["paths"]["/kiem-thu/du-an/{project_id}/mau-ca-kiem-thu"]["post"][
        "x-function-ids"
    ] == ["TPLT-02"]
    assert spec["paths"]["/kiem-thu/mau-ca-kiem-thu/{template_id}/luu-tru"]["post"][
        "x-function-ids"
    ] == ["TPLT-03"]


def test_resume_and_not_applicable_routes_expose_canonical_function_ids():
    spec = app.openapi()
    assert spec["paths"][
        "/kiem-thu/du-an/{project_id}/lan-chay-kiem-thu/{run_id}/tiep-tuc"
    ]["post"]["x-function-ids"] == ["RUN-15"]
    assert "RUN-16" in spec["paths"][
        "/kiem-thu/lan-chay-kiem-thu/{run_id}/ket-qua/{test_case_version_id}"
    ]["post"]["x-function-ids"]
    assert "RUN-16" in spec["paths"][
        "/kiem-thu/du-an/{project_id}/thuc-thi-kiem-thu/{execution_id}"
    ]["patch"]["x-function-ids"]


def test_bug_trace_routes_separate_ai_candidates_from_human_confirmation():
    spec = app.openapi()
    assert spec["paths"][
        "/kiem-thu/du-an/{project_id}/ai/loi/{defect_id}/goi-y-truy-vet"
    ]["post"]["x-function-ids"] == ["AI-10"]
    assert spec["paths"]["/kiem-thu/du-an/{project_id}/loi/{defect_id}/truy-vet"][
        "patch"
    ]["x-function-ids"] == ["DEF-07"]


def test_defect_detail_route_does_not_shadow_duplicate_detection():
    spec = app.openapi()
    assert spec["paths"]["/kiem-thu/du-an/{project_id}/loi/{defect_id}"]["get"][
        "x-function-ids"
    ] == ["DEF-02"]
    assert spec["paths"]["/kiem-thu/du-an/{project_id}/loi/trung-lap"]["get"][
        "x-function-ids"
    ] == ["DEF-17", "DEF-20"]


def test_bulk_routes_expose_canonical_function_ids():
    spec = app.openapi()
    expected = {
        "/kiem-thu/du-an/{project_id}/hang-loat/nhan": ["BULK-01"],
        "/kiem-thu/du-an/{project_id}/hang-loat/ca-kiem-thu/them-vao-bo-kiem-thu": ["BULK-02"],
        "/kiem-thu/du-an/{project_id}/hang-loat/ca-kiem-thu/danh-dau-can-ra-soat": ["BULK-03"],
        "/kiem-thu/du-an/{project_id}/hang-loat/de-xuat-anh-huong": ["BULK-04"],
        "/kiem-thu/du-an/{project_id}/hang-loat/phe-duyet-de-xuat": ["BULK-05"],
        "/kiem-thu/du-an/{project_id}/hang-loat/luu-tru": ["BULK-06"],
    }
    for path, function_ids in expected.items():
        assert spec["paths"][path]["post"]["x-function-ids"] == function_ids


def test_device_matrix_routes_expose_canonical_function_ids():
    spec = app.openapi()
    collection = "/kiem-thu/du-an/{project_id}/ma-tran-thiet-bi"
    detail = "/kiem-thu/ma-tran-thiet-bi/{matrix_id}"
    assert spec["paths"][collection]["get"]["x-function-ids"] == ["DEVMTX-01"]
    assert spec["paths"][collection]["post"]["x-function-ids"] == ["DEVMTX-02"]
    assert spec["paths"][detail]["patch"]["x-function-ids"] == ["DEVMTX-02"]
    assert spec["paths"][f"{detail}/gan"]["post"]["x-function-ids"] == ["DEVMTX-03"]


def test_project_notification_routes_expose_canonical_function_ids():
    spec = app.openapi()
    prefix = "/kiem-thu/du-an/{project_id}/thong-bao"
    assert spec["paths"][f"{prefix}/theo-doi"]["get"]["x-function-ids"] == ["NTF-04"]
    assert spec["paths"][f"{prefix}/theo-doi/{{artifact_type}}/{{artifact_id}}"]["put"][
        "x-function-ids"
    ] == ["NTF-04"]
    assert spec["paths"][f"{prefix}/quy-tac"]["patch"]["x-function-ids"] == ["NTF-05"]
    assert spec["paths"][f"{prefix}/tuy-chon"]["patch"]["x-function-ids"] == ["NTF-06"]


def test_specialized_ai_design_routes_expose_canonical_function_ids():
    spec = app.openapi()
    security = "/kiem-thu/du-an/{project_id}/ai/goi-y-kiem-thu-bao-mat"
    performance = "/kiem-thu/du-an/{project_id}/ai/ke-hoach-hieu-nang"
    assert spec["paths"][security]["get"]["x-function-ids"] == ["SEC-TST-01"]
    assert spec["paths"][security]["post"]["x-function-ids"] == ["SEC-TST-01"]
    assert spec["paths"][performance]["get"]["x-function-ids"] == ["PERF-01"]
    assert spec["paths"][performance]["post"]["x-function-ids"] == ["PERF-01"]


def test_webhook_routes_expose_canonical_function_ids():
    spec = app.openapi()
    subscriptions = "/kiem-thu/du-an/{project_id}/moc-goi"
    deliveries = f"{subscriptions}/giao-hang"
    replay = f"{deliveries}/{{delivery_id}}/phat-lai"
    assert spec["paths"][subscriptions]["get"]["x-function-ids"] == ["WH-01"]
    assert spec["paths"][subscriptions]["post"]["x-function-ids"] == ["WH-01"]
    assert spec["paths"][f"{subscriptions}/{{subscription_id}}"]["patch"][
        "x-function-ids"
    ] == ["WH-01"]
    assert spec["paths"][deliveries]["get"]["x-function-ids"] == ["WH-02"]
    assert spec["paths"][replay]["post"]["x-function-ids"] == ["WH-03"]


def test_automation_script_routes_expose_canonical_function_ids():
    spec = app.openapi()
    collection = "/kiem-thu/du-an/{project_id}/ban-nhap-kich-ban-tu-dong"
    generate = "/kiem-thu/du-an/{project_id}/ai/ban-nhap-kich-ban-tu-dong"
    detail = "/kiem-thu/ban-nhap-kich-ban-tu-dong/{draft_id}"
    assert spec["paths"][collection]["get"]["x-function-ids"] == ["SCR-01"]
    assert spec["paths"][generate]["post"]["x-function-ids"] == ["SCR-01"]
    assert spec["paths"][detail]["patch"]["x-function-ids"] == ["SCR-02"]
    assert spec["paths"][f"{detail}/xuat"]["get"]["x-function-ids"] == ["SCR-03"]
    assert spec["paths"][f"{detail}/phe-duyet"]["post"]["x-function-ids"] == ["SCR-04"]


def test_project_connector_routes_expose_canonical_function_ids():
    spec = app.openapi()
    base = "/kiem-thu/du-an/{project_id}/ket-noi"
    detail = f"{base}/{{connector_id}}"
    assert spec["paths"][base]["get"]["x-function-ids"] == ["CONN-01"]
    assert spec["paths"][base]["post"]["x-function-ids"] == ["CONN-02"]
    assert spec["paths"][detail]["patch"]["x-function-ids"] == ["CONN-03"]
    assert spec["paths"][f"{detail}/ngat"]["post"]["x-function-ids"] == ["CONN-02"]
    assert spec["paths"][f"{detail}/dong-bo"]["post"]["x-function-ids"] == ["CONN-04"]
    assert spec["paths"][f"{base}/xung-dot"]["get"]["x-function-ids"] == ["CONN-05"]
    assert spec["paths"][f"{base}/nhat-ky"]["get"]["x-function-ids"] == ["CONN-06"]


def test_automation_execution_routes_expose_canonical_function_ids():
    spec = app.openapi()
    collection = "/kiem-thu/du-an/{project_id}/thuc-thi-tu-dong"
    detail = "/kiem-thu/thuc-thi-tu-dong/{execution_id}"
    assert spec["paths"][collection]["get"]["x-function-ids"] == ["AUTO-01"]
    assert spec["paths"][collection]["post"]["x-function-ids"] == ["AUTO-02"]
    assert spec["paths"][detail]["get"]["x-function-ids"] == ["AUTO-01"]
    assert spec["paths"][f"{detail}/bat-dau"]["post"]["x-function-ids"] == ["AUTO-03"]
    assert spec["paths"][f"{detail}/huy"]["post"]["x-function-ids"] == ["AUTO-03"]
    assert spec["paths"][f"{detail}/bang-chung"]["get"]["x-function-ids"] == ["AUTO-04"]


def test_cicd_routes_expose_canonical_function_ids():
    spec = app.openapi()
    base = "/kiem-thu/du-an/{project_id}/tich-hop-trien-khai-lien-tuc"
    assert spec["paths"][base]["get"]["x-function-ids"] == ["CI-05"]
    assert spec["paths"][base]["post"]["x-function-ids"] == ["CI-01"]
    assert spec["paths"][f"{base}/{{binding_id}}"]["patch"]["x-function-ids"] == ["CI-01"]
    retry = f"{base}/lan-chay/{{run_id}}/thu-lai"
    assert spec["paths"][retry]["post"]["x-function-ids"] == ["CI-04"]


def test_collaboration_routes_expose_canonical_function_ids():
    spec = app.openapi()
    base = "/kiem-thu/du-an/{project_id}/cong-tac"
    assert spec["paths"][f"{base}/phien"]["put"]["x-function-ids"] == ["COL-01"]
    assert spec["paths"][f"{base}/hien-dien"]["get"]["x-function-ids"] == ["COL-01"]
    assert spec["paths"][f"{base}/yeu-cau/{{artifact_id}}/thao-tac"]["post"]["x-function-ids"] == ["COL-02"]
    assert spec["paths"][f"{base}/ca-kiem-thu/{{artifact_id}}/thao-tac"]["post"]["x-function-ids"] == ["COL-03"]
    assert spec["paths"][f"{base}/xung-dot"]["get"]["x-function-ids"] == ["COL-04"]
    assert spec["paths"][f"{base}/xung-dot/{{conflict_id}}/giai-quyet"]["post"]["x-function-ids"] == ["COL-04"]


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
