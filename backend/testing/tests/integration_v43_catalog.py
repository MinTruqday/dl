import os
import time

import httpx
import jwt


base_url = os.getenv("TESTING_TEST_URL", "http://testing:8000")


def identity(user_id):
    return {
        "Authorization": "Bearer "
        + jwt.encode(
            {"uid": user_id, "sub": f"{user_id}@test.local", "system_role": "USER"},
            os.environ["SECRET_KEY"],
            algorithm="HS256",
        )
    }


lead = identity("catalog-lead-v43")
tester = identity("catalog-tester-v43")
ba = identity("catalog-ba-v43")
developer = identity("catalog-developer-v43")
other_developer = identity("catalog-other-developer-v43")
viewer = identity("catalog-viewer-v43")


def doc(text):
    return {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]}


def call(client, method, path, headers=lead, expected=200, **kwargs):
    response = client.request(method, path, headers=headers, **kwargs)
    assert response.status_code == expected, f"{method} {path} {response.status_code} {response.text}"
    return response.json().get("data") if expected < 400 else response.json()


with httpx.Client(base_url=base_url, timeout=60) as client:
    stamp = int(time.time() * 1000)
    project = call(
        client,
        "POST",
        "/api/qa/projects",
        expected=201,
        json={"key": f"CAT{stamp}", "name": "V4.3 Catalog", "project_type": "web", "settings": {}},
    )
    project_id = project["_id"]
    for user_id, role in [
        ("catalog-tester-v43", "TESTER"),
        ("catalog-ba-v43", "BA"),
        ("catalog-developer-v43", "DEVELOPER"),
        ("catalog-other-developer-v43", "DEVELOPER"),
        ("catalog-viewer-v43", "VIEWER"),
    ]:
        call(client, "POST", f"/api/qa/projects/{project_id}/members", expected=201, json={"user_id": user_id, "project_role": role})

    maintenance = call(
        client,
        "GET",
        f"/api/qa/projects/{project_id}/maintenance-analytics",
        headers=viewer,
    )
    assert set(maintenance) == {"impact_analysis_count", "tests_stale"}
    denied_ai_analytics = call(
        client,
        "GET",
        f"/api/qa/projects/{project_id}/ai-analytics",
        headers=viewer,
        expected=403,
    )
    assert denied_ai_analytics["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    ai_analytics = call(
        client,
        "GET",
        f"/api/qa/projects/{project_id}/ai-analytics",
        headers=ba,
    )
    assert {
        "proposal_acceptance_rate",
        "override_count",
        "average_latency_ms",
        "degraded_rate",
        "model_versions",
    } <= set(ai_analytics)
    assert call(client, "GET", f"/api/qa/projects/{project_id}/reports/execution", headers=viewer)["run_count"] == 0
    assert call(client, "GET", f"/api/qa/projects/{project_id}/reports/defects", headers=viewer)["defect_count"] == 0
    call(client, "GET", f"/api/qa/projects/{project_id}/activity", headers=viewer)

    denied_settings = call(
        client,
        "PATCH",
        f"/api/qa/projects/{project_id}",
        headers=tester,
        expected=403,
        json={"expected_revision": project["revision"], "settings": {"tester_can_create_run": True}},
    )
    assert denied_settings["error"]["code"] == "PROJECT_PERMISSION_DENIED"

    denied_knowledge_source = call(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/knowledge-sources",
        headers=tester,
        expected=403,
        json={"title": "Nguồn bị từ chối", "content": "Không được tạo mặc định"},
    )
    assert denied_knowledge_source["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    teacher_source = call(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/knowledge-sources",
        headers=ba,
        expected=201,
        json={
            "title": "Tài liệu phương pháp của giáo viên",
            "content": "Giáo viên hướng dẫn kiểm tra biên và dữ liệu không hợp lệ",
            "source_type": "teacher_material",
            "authority": "teacher",
            "teacher_id": "catalog-ba-v43",
            "subject": "Tin học",
            "grade": "10",
            "tags": ["phuong-phap", "bien"],
        },
    )
    textbook_source = call(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/knowledge-sources",
        headers=ba,
        expected=201,
        json={
            "title": "Sách giáo khoa chính thức",
            "content": "Sách giáo khoa hướng dẫn kiểm tra biên và dữ liệu không hợp lệ",
            "source_type": "official_textbook",
            "authority": "official",
            "subject": "Tin học",
            "grade": "10",
        },
    )
    sources = call(client, "GET", f"/api/qa/projects/{project_id}/knowledge-sources", headers=viewer)
    assert [item["_id"] for item in sources[:2]] == [teacher_source["_id"], textbook_source["_id"]]
    search = call(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/knowledge/search",
        headers=viewer,
        json={"query": "kiểm tra biên", "artifact_types": ["requirement_document"], "limit": 10},
    )
    assert search["items"][0]["authority"] == "teacher"
    archived_source = call(
        client,
        "POST",
        f"/api/qa/knowledge-sources/{teacher_source['_id']}/archive",
        headers=ba,
        json={"expected_revision": teacher_source["revision"], "reason": "Nguồn đã được thay thế"},
    )
    assert archived_source["status"] == "ARCHIVED"

    attachment = call(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/attachments",
        headers=ba,
        expected=201,
        json={"filename": "teacher-note.txt", "url": "teacher/teacher-note.txt", "size": 42, "content_type": "text/plain"},
    )
    call(client, "GET", f"/api/qa/projects/{project_id}/attachments", headers=viewer)
    denied_attachment_delete = call(
        client,
        "DELETE",
        f"/api/qa/attachments/{attachment['_id']}",
        headers=viewer,
        expected=403,
    )
    assert denied_attachment_delete["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    deleted_attachment = call(
        client,
        "DELETE",
        f"/api/qa/attachments/{attachment['_id']}",
        headers=ba,
    )
    assert deleted_attachment["deleted"] is True
    moderated_attachment = call(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/attachments",
        headers=ba,
        expected=201,
        json={"filename": "moderated-note.txt", "url": "teacher/moderated-note.txt", "size": 21, "content_type": "text/plain"},
    )
    moderated = call(
        client,
        "POST",
        f"/api/qa/attachments/{moderated_attachment['_id']}/moderate",
        headers=lead,
        json={"reason": "Nội dung không còn được phép sử dụng"},
    )
    assert moderated["deleted"] is True

    requirements = []
    for index in range(3):
        requirements.append(
            call(
                client,
                "POST",
                f"/api/qa/projects/{project_id}/requirements",
                expected=201,
                json={
                    "title": f"Yêu cầu phụ thuộc {index + 1}",
                    "content_doc": doc("Khi có dữ liệu hợp lệ thì hệ thống phải trả về kết quả"),
                    "acceptance_criteria": [{"key": "AC-01", "content_doc": doc("Given dữ liệu hợp lệ when gửi yêu cầu then trả về thành công")}],
                    "actors": ["User"],
                },
            )
        )
    first, second, third = requirements
    denied_dependency = call(
        client,
        "POST",
        f"/api/qa/requirements/{first['_id']}/dependencies",
        headers=viewer,
        expected=403,
        json={"dependency_requirement_id": second["_id"], "expected_revision": 1},
    )
    assert denied_dependency["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    first_version = call(
        client,
        "POST",
        f"/api/qa/requirements/{first['_id']}/dependencies",
        headers=ba,
        json={"dependency_requirement_id": second["_id"], "expected_revision": 1},
    )
    assert second["_id"] in first_version["dependencies"]
    call(
        client,
        "POST",
        f"/api/qa/requirements/{second['_id']}/dependencies",
        headers=ba,
        json={"dependency_requirement_id": third["_id"], "expected_revision": 1},
    )
    cycle = call(
        client,
        "POST",
        f"/api/qa/requirements/{third['_id']}/dependencies",
        headers=ba,
        expected=422,
        json={"dependency_requirement_id": first["_id"], "expected_revision": 1},
    )
    assert cycle["error"]["code"] == "REQUIREMENT_DEPENDENCY_CYCLE"
    removed = call(
        client,
        "DELETE",
        f"/api/qa/requirements/{first['_id']}/dependencies/{second['_id']}?expected_revision=2",
        headers=ba,
    )
    assert second["_id"] not in removed["dependencies"]

    restorable = call(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/requirements",
        expected=201,
        json={
            "title": "Yêu cầu kiểm tra khôi phục",
            "content_doc": doc("Hệ thống phải giữ lịch sử khi khôi phục yêu cầu"),
            "acceptance_criteria": [{"key": "AC-01", "content_doc": doc("Given yêu cầu cũ when khôi phục then trở lại bản nháp")}],
        },
    )
    restorable = call(
        client,
        "POST",
        f"/api/qa/requirements/{restorable['_id']}/obsolete",
        json={"expected_current_version_id": restorable["current_version"]["_id"], "reason": "Kiểm tra trạng thái lưu trữ"},
    )
    assert restorable["status"] == "OBSOLETE"
    denied_restore = call(
        client,
        "POST",
        f"/api/qa/requirements/{restorable['_id']}/restore",
        headers=ba,
        expected=403,
        json={"expected_current_version_id": restorable["current_version"]["_id"], "reason": "BA chưa được policy cấp quyền"},
    )
    assert denied_restore["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    restored = call(
        client,
        "POST",
        f"/api/qa/requirements/{restorable['_id']}/restore",
        json={"expected_current_version_id": restorable["current_version"]["_id"], "reason": "Khôi phục sau khi kiểm chứng"},
    )
    assert restored["status"] == "DRAFT" and restored["current_version"]["status"] == "DRAFT"

    plan = call(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/test-plans",
        headers=tester,
        expected=201,
        json={"project_id": project_id, "name": "Kế hoạch V4.3"},
    )
    cloned_plan = call(client, "POST", f"/api/qa/test-plans/{plan['_id']}/clone", headers=tester, expected=201)
    assert cloned_plan["_id"] != plan["_id"] and cloned_plan["status"] == "DRAFT"
    call(client, "POST", f"/api/qa/test-plans/{plan['_id']}/approve", headers=tester, expected=403, json={"expected_revision": 1, "review_note": "Không được duyệt"})

    scenario = call(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/test-scenarios",
        headers=tester,
        expected=201,
        json={"title": "Kịch bản V4.3", "objective": "Kiểm tra catalog", "requirement_version_ids": [first["current_version"]["_id"]]},
    )
    scenario_detail = call(client, "GET", f"/api/qa/test-scenarios/{scenario['_id']}", headers=viewer)
    assert scenario_detail["_id"] == scenario["_id"]

    draft = call(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/test-case-drafts",
        expected=201,
        json={
            "title": "Ca kiểm thử policy V4.3",
            "preconditions_doc": doc("Hệ thống sẵn sàng"),
            "steps": [{"id": "step-1", "order": 1, "action_doc": doc("Gửi dữ liệu hợp lệ"), "test_data": {"value": 1}, "expected_doc": doc("Hệ thống trả về thành công")}],
            "test_data": {"value": 1},
            "expected_result_doc": doc("Hệ thống trả về thành công"),
            "requirement_version_ids": [first["current_version"]["_id"]],
        },
    )
    reviewed_draft = call(client, "POST", f"/api/qa/projects/{project_id}/test-cases/{draft['_id']}/submit-review", json={"expected_revision": 1, "review_note": "Gửi duyệt"})
    suite = call(
        client,
        "POST",
        "/api/qa/test-suites",
        expected=201,
        json={"project_id": project_id, "name": "Suite kiểm tra quyền bulk", "suite_type": "custom", "test_case_version_ids": []},
    )
    bulk_result = call(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/bulk/test-cases/add-to-suite",
        headers=tester,
        json={"suite_id": suite["_id"], "test_case_ids": [draft["_id"]], "expected_revision": 1},
    )
    assert bulk_result["failed"] == [{"id": draft["_id"], "code": "ENTITY_NOT_FOUND"}]
    denied_changes = call(client, "POST", f"/api/qa/projects/{project_id}/test-cases/{draft['_id']}/request-changes", headers=tester, expected=403, json={"expected_revision": reviewed_draft["revision"], "review_note": "Yêu cầu sửa"})
    assert denied_changes["error"]["code"] == "PROJECT_ACTION_POLICY_DENIED"

    denied_question = call(client, "POST", f"/api/qa/projects/{project_id}/ai/ask", headers=viewer, expected=403, json={"question": "Yêu cầu nào đang tồn tại", "artifact_types": ["not_available"]})
    assert denied_question["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    denied_plan_assignment = call(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/test-plans",
        headers=tester,
        expected=403,
        json={
            "project_id": project_id,
            "name": "Kế hoạch phân công bị chặn",
            "members": ["catalog-tester-v43"],
        },
    )
    assert denied_plan_assignment["error"]["code"] == "PROJECT_ACTION_POLICY_DENIED"
    project = call(
        client,
        "PATCH",
        f"/api/qa/projects/{project_id}",
        json={
            "expected_revision": project["revision"],
            "settings": {
                "viewer_can_use_ai_qna": True,
                "action_policies": {
                    "testcase.request_changes": ["QA_LEAD", "TESTER"],
                    "defect.rejected": ["QA_LEAD", "TESTER"],
                    "testplan.assignments": ["QA_LEAD", "TESTER"],
                },
            },
        },
    )
    assigned_plan = call(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/test-plans",
        headers=tester,
        expected=201,
        json={
            "project_id": project_id,
            "name": "Kế hoạch phân công theo policy",
            "members": ["catalog-tester-v43"],
        },
    )
    assert assigned_plan["members"] == ["catalog-tester-v43"]
    changed_draft = call(client, "POST", f"/api/qa/projects/{project_id}/test-cases/{draft['_id']}/request-changes", headers=tester, json={"expected_revision": reviewed_draft["revision"], "review_note": "Yêu cầu sửa theo policy"})
    assert changed_draft["status"] == "DRAFT"
    answer = call(client, "POST", f"/api/qa/projects/{project_id}/ai/ask", headers=viewer, json={"question": "Yêu cầu nào đang tồn tại", "artifact_types": ["not_available"]})
    assert answer["confidence"] == 0 and answer["evidence"] == []

    defect = call(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/defects",
        expected=201,
        json={"project_id": project_id, "title": "Lỗi được giao cho developer", "assignee": "catalog-developer-v43"},
    )
    viewer_export = client.get(
        f"/api/qa/projects/{project_id}/defects/export", headers=viewer
    )
    assert viewer_export.status_code == 403, viewer_export.text
    ba_export = client.get(f"/api/qa/projects/{project_id}/defects/export", headers=ba)
    assert ba_export.status_code == 200, ba_export.text
    assert "defect_key,title,severity" in ba_export.text
    defect = call(client, "POST", f"/api/qa/defects/{defect['_id']}/transition", json={"expected_revision": defect["revision"], "to_status": "CONFIRMED", "reason": "Xác nhận lỗi"})
    call(client, "POST", f"/api/qa/defects/{defect['_id']}/transition", headers=other_developer, expected=403, json={"expected_revision": defect["revision"], "to_status": "IN_PROGRESS", "reason": "Không được nhận lỗi của người khác"})
    defect = call(client, "POST", f"/api/qa/defects/{defect['_id']}/transition", headers=developer, json={"expected_revision": defect["revision"], "to_status": "IN_PROGRESS", "reason": "Bắt đầu xử lý"})
    assert defect["status"] == "IN_PROGRESS"

    rejected_defect = call(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/defects",
        headers=tester,
        expected=201,
        json={"project_id": project_id, "title": "Lỗi cần từ chối theo policy"},
    )
    rejected_defect = call(client, "POST", f"/api/qa/defects/{rejected_defect['_id']}/transition", headers=tester, json={"expected_revision": rejected_defect["revision"], "to_status": "REJECTED", "reason": "Không tái hiện được"})
    assert rejected_defect["status"] == "REJECTED"

    run = call(client, "POST", f"/api/qa/projects/{project_id}/test-runs", expected=201, json={"project_id": project_id, "name": "Run catalog V4.3"})
    run = call(client, "PATCH", f"/api/qa/projects/{project_id}/test-runs/{run['_id']}", json={"expected_revision": run["revision"], "build": "v4.3"})
    assigned = call(client, "POST", f"/api/qa/projects/{project_id}/test-runs/{run['_id']}/assign", json={"expected_revision": run["revision"], "assignee_id": "catalog-tester-v43", "test_case_assignments": {}})
    assert assigned["assignee_id"] == "catalog-tester-v43"

print("V4.3 role catalog integration passed")
