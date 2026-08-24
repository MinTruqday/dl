import io
import os
import time
import zipfile

import httpx


BASE_URL = os.getenv("QA_TEST_URL", "http://127.0.0.1:8000")
HEADERS = {"x-test-user-id": "qa-lead-e2e", "x-test-user-role": "author"}
OUTSIDER = {"x-test-user-id": "outsider-e2e", "x-test-user-role": "author"}


def doc(text):
    return {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]}


def request(client, method, path, expected=200, headers=HEADERS, **kwargs):
    response = client.request(method, path, headers=headers, **kwargs)
    assert response.status_code == expected, f"{method} {path} {response.status_code} {response.text}"
    body = response.json()
    if expected < 400:
        assert "data" in body and "meta" in body and body["meta"]["trace_id"]
        return body["data"]
    assert "error" in body and "trace_id" in body
    return body


with httpx.Client(base_url=BASE_URL, timeout=30) as client:
    stamp = int(time.time() * 1000)
    project = request(
        client,
        "POST",
        "/api/qa/projects",
        201,
        json={
            "key": f"QA{stamp}",
            "name": "Phone Profile QA",
            "description": "Vertical slice V1",
            "project_type": "web",
            "settings": {"timezone": "Asia/Ho_Chi_Minh", "locale": "vi"},
        },
    )
    project_id = project["_id"]
    request(client, "GET", f"/api/qa/projects/{project_id}", 403, headers=OUTSIDER)
    updated_project = request(
        client,
        "PATCH",
        f"/api/qa/projects/{project_id}",
        json={"expected_revision": 1, "description": "Vertical slice đã cập nhật"},
    )
    assert updated_project["revision"] == 2
    request(
        client,
        "PATCH",
        f"/api/qa/projects/{project_id}",
        409,
        json={"expected_revision": 1, "description": "Ghi đè cũ"},
    )
    requirement = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/requirements",
        201,
        json={
            "requirement_key": "REQ-PROFILE-004",
            "title": "Giới hạn số điện thoại",
            "type": "functional",
            "priority": "high",
            "risk": "high",
            "content_doc": doc("Khi người dùng nhập số điện thoại thì hệ thống chỉ chấp nhận đúng 10 chữ số"),
            "acceptance_criteria": [
                {"key": "AC-01", "content_doc": doc("GIVEN hồ sơ hợp lệ WHEN nhập 10 chữ số THEN hệ thống chấp nhận")}
            ],
            "actors": ["User"],
        },
    )
    requirement_id = requirement["_id"]
    version_1 = requirement["current_version"]
    lint = request(client, "POST", f"/api/qa/requirement-versions/{version_1['_id']}/ai/lint")
    assert lint["valid"] is True
    version_1 = request(
        client,
        "POST",
        f"/api/qa/requirement-versions/{version_1['_id']}/baseline",
        json={"expected_revision": 1},
    )
    scenario = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/test-scenarios",
        201,
        json={
            "title": "Biên số điện thoại",
            "objective": "Kiểm tra 9 10 và 11 chữ số",
            "risk": "high",
            "priority": "high",
            "requirement_version_ids": [version_1["_id"]],
            "acceptance_criterion_ids": version_1["acceptance_criterion_ids"],
            "category": "boundary",
        },
    )
    draft = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/test-case-drafts",
        201,
        json={
            "test_case_key": "TC-PROFILE-043",
            "title": "Số điện thoại 11 chữ số bị từ chối",
            "type": "boundary",
            "priority": "high",
            "risk": "high",
            "preconditions_doc": doc("Người dùng đang chỉnh sửa hồ sơ"),
            "steps": [
                {
                    "id": "step-1",
                    "order": 1,
                    "action_doc": doc("Nhập số điện thoại 09123456789 gồm 11 chữ số"),
                    "test_data": {"phone": "09123456789"},
                    "expected_doc": doc("Hệ thống hiển thị lỗi giới hạn 10 chữ số"),
                }
            ],
            "test_data": {"phone": "09123456789"},
            "expected_result_doc": doc("Hệ thống từ chối số điện thoại 11 chữ số"),
            "postconditions_doc": doc("Hồ sơ không thay đổi"),
            "requirement_version_ids": [version_1["_id"]],
            "acceptance_criterion_ids": version_1["acceptance_criterion_ids"],
            "scenario_id": scenario["_id"],
            "origin": "manual",
        },
    )
    test_lint = request(client, "POST", f"/api/qa/test-case-drafts/{draft['_id']}/lint")
    assert test_lint["valid"] is True
    frozen = request(
        client,
        "POST",
        f"/api/qa/test-case-drafts/{draft['_id']}/freeze",
        201,
        json={"expected_revision": 1, "change_reason": "Phê duyệt test biên v1"},
    )
    test_case = frozen["test_case"]
    test_version_1 = frozen["version"]
    xlsx_export = client.get(f"/api/qa/projects/{project_id}/test-cases/export?format=xlsx", headers=HEADERS)
    assert xlsx_export.status_code == 200
    assert xlsx_export.headers["content-type"].startswith("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with zipfile.ZipFile(io.BytesIO(xlsx_export.content)) as workbook:
        assert "TC-PROFILE-043" in workbook.read("xl/worksheets/sheet1.xml").decode("utf-8")
    coverage = request(client, "GET", f"/api/qa/projects/{project_id}/coverage")
    assert coverage["requirement_coverage"] == 100
    assert coverage["acceptance_criterion_coverage"] == 100
    plan = request(
        client,
        "POST",
        "/api/qa/test-plans",
        201,
        json={"project_id": project_id, "name": "Kế hoạch Profile", "objective": "Xác nhận release", "scope_in": ["Profile"], "environment": "staging", "build": "1.0.0"},
    )
    suite = request(
        client,
        "POST",
        "/api/qa/test-suites",
        201,
        json={"project_id": project_id, "name": "Regression Profile", "suite_type": "regression", "test_case_version_ids": [test_version_1["_id"]]},
    )
    run = request(
        client,
        "POST",
        "/api/qa/test-runs",
        201,
        json={"project_id": project_id, "name": "Run build 1.0.0", "test_plan_id": plan["_id"], "test_suite_ids": [suite["_id"]], "test_case_version_ids": [], "environment": "staging", "build": "1.0.0"},
    )
    request(client, "POST", f"/api/qa/test-runs/{run['_id']}/start")
    result = request(
        client,
        "POST",
        f"/api/qa/test-runs/{run['_id']}/results/{test_version_1['_id']}",
        json={"status": "FAIL", "step_results": [{"step_id": "step-1", "status": "FAIL"}], "attachments": [], "note": "Ứng dụng chấp nhận 11 số", "idempotency_key": f"result-{stamp}"},
    )
    defect = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/defects",
        201,
        json={"project_id": project_id, "title": "Ứng dụng chấp nhận 11 số ngoài baseline", "description_doc": doc("Sai giới hạn"), "steps_to_reproduce": [], "actual_result_doc": doc("Chấp nhận"), "expected_result_doc": doc("Từ chối"), "severity": "major", "priority": "high", "environment": "staging", "build": "1.0.0", "linked_test_result_id": result["_id"], "linked_test_case_version_id": test_version_1["_id"], "linked_requirement_version_ids": [version_1["_id"]]},
    )
    assert defect["status"] == "NEW"
    request(client, "POST", f"/api/qa/defects/{defect['_id']}/transition", json={"to_status": "CONFIRMED", "reason": "Đã tái hiện"})
    request(client, "POST", f"/api/qa/test-runs/{run['_id']}/complete")
    run_report = client.get(f"/api/qa/test-runs/{run['_id']}/report", headers=HEADERS)
    assert run_report.status_code == 200
    assert "TC-PROFILE-043" in run_report.text and "FAIL" in run_report.text
    version_2 = request(
        client,
        "POST",
        f"/api/qa/requirements/{requirement_id}/versions",
        201,
        json={
            "requirement_key": "REQ-PROFILE-004",
            "title": "Giới hạn số điện thoại",
            "type": "functional",
            "priority": "high",
            "risk": "high",
            "content_doc": doc("Khi người dùng nhập số điện thoại thì hệ thống chấp nhận 10 hoặc 11 chữ số"),
            "acceptance_criteria": [{"key": "AC-01", "content_doc": doc("GIVEN hồ sơ hợp lệ WHEN nhập 10 hoặc 11 chữ số THEN hệ thống chấp nhận")}],
            "actors": ["User"],
            "change_reason": "Mở rộng giới hạn",
            "expected_current_version_id": version_1["_id"],
        },
    )
    version_2 = request(client, "POST", f"/api/qa/requirement-versions/{version_2['_id']}/baseline", json={"expected_revision": 1})
    change_set = request(
        client,
        "POST",
        f"/api/qa/requirements/{requirement_id}/change-sets",
        201,
        json={"from_version_id": version_1["_id"], "to_version_id": version_2["_id"]},
    )
    assert change_set["changes"][0]["type"] == "MODIFIED_BOUNDARY"
    impact = request(client, "POST", f"/api/qa/change-sets/{change_set['_id']}/impact-analysis", 201)
    impacted = next(item for item in impact["affected_test_cases"] if item["test_case_id"] == test_case["_id"])
    assert impacted["classification"] == "NEEDS_UPDATE"
    proposals = request(client, "POST", f"/api/qa/impact-analyses/{impact['_id']}/maintenance-proposals", 201)
    proposal = next(item for item in proposals if item["proposal_type"] == "UPDATE_TEST_CASE")
    applied = request(
        client,
        "POST",
        f"/api/qa/maintenance-proposals/{proposal['_id']}/accept-with-edit",
        201,
        json={"expected_revision": 1, "patch": {"expected_result_doc": doc("Hệ thống chấp nhận số điện thoại 11 chữ số")}, "review_note": "Tester xác nhận thay đổi"},
    )
    test_version_2 = applied["result"]
    assert test_version_2["version"] == 2
    versions = request(client, "GET", f"/api/qa/test-cases/{test_case['_id']}/versions")
    assert [item["version"] for item in versions] == [2, 1]
    run_detail = request(client, "GET", f"/api/qa/test-runs/{run['_id']}")
    assert run_detail["test_case_version_ids"] == [test_version_1["_id"]]
    regression = request(client, "POST", f"/api/qa/change-sets/{change_set['_id']}/regression-recommendation", 201)
    assert regression["items"][0]["level"] == "MUST_RUN"
    search = request(client, "POST", f"/api/qa/projects/{project_id}/knowledge/search", json={"query": "điện thoại 11", "artifact_types": ["requirement_version", "test_case_version"], "limit": 20})
    assert search["items"] and all(item["project_id"] == project_id for item in search["items"])
    audits = request(client, "GET", f"/api/qa/projects/{project_id}/audit")
    assert any(item["action"] == "maintenance_proposal_applied" for item in audits)
    dashboard = request(client, "GET", f"/api/qa/projects/{project_id}/dashboard")
    assert dashboard["requirements"] == 1 and dashboard["active_tests"] == 1
    import_preview = client.post(
        f"/api/qa/projects/{project_id}/test-case-imports/upload",
        headers=HEADERS,
        data={"format": "csv"},
        files={
            "file": (
                "import.csv",
                "title,type,priority,risk,action,expected\nImported case,validation,high,high,Submit profile,Profile accepted\n",
                "text/csv",
            )
        },
    )
    assert import_preview.status_code == 201, import_preview.text
    import_job = import_preview.json()["data"]
    assert import_job["status"] == "PREVIEW_READY" and len(import_job["preview"]) == 1
    imported = request(
        client,
        "POST",
        f"/api/qa/test-case-imports/{import_job['_id']}/confirm",
        json={"selected_indexes": [0]},
    )
    assert len(imported["drafts"]) == 1

print("qa vertical integration passed")
