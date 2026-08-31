import io
import os
import time
import zipfile

import httpx
import jwt


BASE_URL = os.getenv("TESTING_TEST_URL", "http://127.0.0.1:8000")
def identity(user_id, system_role="USER"):
    return {
        "Authorization": "Bearer "
        + jwt.encode(
            {"uid": user_id, "sub": f"{user_id}@test.local", "system_role": system_role},
            os.environ["SECRET_KEY"],
            algorithm="HS256",
        )
    }


HEADERS = identity("qa-lead-e2e")
OUTSIDER = identity("outsider-e2e")
SYSTEM_ADMIN = identity("platform-admin-e2e", "ADMIN")


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
    request(client, "GET", "/api/qa/operations", 403)
    operations = request(client, "GET", "/api/qa/operations", headers=SYSTEM_ADMIN)
    assert "ai_models" in operations and "knowledge_indexing_backlog" in operations
    missing_retry = request(
        client,
        "POST",
        "/api/qa/operations/jobs/JOB-NOT-FOUND/retry",
        404,
        headers=SYSTEM_ADMIN,
    )
    assert missing_retry["error"]["code"] == "JOB_NOT_FOUND"
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
    assert request(client, "GET", f"/api/qa/projects/{project_id}/members")
    request(
        client,
        "PATCH",
        f"/api/qa/projects/{project_id}/members/qa-lead-e2e",
        422,
        json={"expected_revision": 1, "project_role": "VIEWER"},
    )
    comment = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/review-comments",
        201,
        json={"artifact_type": "project", "artifact_id": project_id, "body_doc": doc("Cần rà soát phạm vi")},
    )
    comments = request(client, "GET", f"/api/qa/projects/{project_id}/review-comments")
    assert comments[0]["_id"] == comment["_id"]
    request(client, "POST", f"/api/qa/review-comments/{comment['_id']}/resolve", json={"reason": "Đã xử lý"})
    reopened_comment = request(client, "POST", f"/api/qa/review-comments/{comment['_id']}/reopen", json={"reason": "Cần bổ sung"})
    assert reopened_comment["status"] == "OPEN"
    edited_comment = request(
        client,
        "PATCH",
        f"/api/qa/review-comments/{comment['_id']}",
        json={"body_doc": doc("Cần rà soát phạm vi đã cập nhật")},
    )
    assert edited_comment["body_doc"] == doc("Cần rà soát phạm vi đã cập nhật")
    deleted_comment = request(client, "DELETE", f"/api/qa/review-comments/{comment['_id']}")
    assert deleted_comment["deleted"] is True
    document = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/requirement-documents",
        201,
        json={"filename": "profile.md", "format": "md", "content": "Người dùng đăng nhập bằng email. Sau 5 lần sai tài khoản bị khóa 15 phút."},
    )
    assert document["status"] == "READY"
    assert document["raw_source"]["storage"] == "embedded"
    assert document["raw_source"]["sha256"] == document["content_hash"]
    assert request(client, "GET", f"/api/qa/requirement-documents/{document['_id']}")["_id"] == document["_id"]
    document = request(
        client,
        "PATCH",
        f"/api/qa/requirement-documents/{document['_id']}",
        json={"expected_revision": 1, "title": "Tài liệu yêu cầu hồ sơ"},
    )
    reindexed_document = request(client, "POST", f"/api/qa/requirement-documents/{document['_id']}/reindex", 202)
    assert reindexed_document["_id"] == document["_id"]
    repeated_document = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/requirement-documents",
        201,
        json={"filename": "profile-copy.md", "format": "md", "content": "Người dùng đăng nhập bằng email. Sau 5 lần sai tài khoản bị khóa 15 phút."},
    )
    assert repeated_document["_id"] == document["_id"]
    uploaded_source = client.post(
        f"/api/qa/projects/{project_id}/requirement-documents/upload",
        headers=HEADERS,
        data={"format": "md"},
        files={"file": ("uploaded.md", b"Requirement upload duoc luu tru truoc khi parse", "text/markdown")},
    )
    assert uploaded_source.status_code == 201, uploaded_source.text
    uploaded_document = uploaded_source.json()["data"]
    assert uploaded_document["status"] == "READY"
    assert uploaded_document["raw_source"]["object_key"].startswith(f"system/qa/{project_id}/requirements/")
    repeated_upload = client.post(
        f"/api/qa/projects/{project_id}/requirement-documents/upload",
        headers=HEADERS,
        data={"format": "md"},
        files={"file": ("uploaded-copy.md", b"Requirement upload duoc luu tru truoc khi parse", "text/markdown")},
    )
    assert repeated_upload.status_code == 201, repeated_upload.text
    assert repeated_upload.json()["data"]["_id"] == uploaded_document["_id"]
    failed_parse = client.post(
        f"/api/qa/projects/{project_id}/requirement-documents/upload",
        headers=HEADERS,
        data={"format": "docx"},
        files={"file": ("broken.docx", b"not-a-docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert failed_parse.status_code == 201, failed_parse.text
    failed_document = failed_parse.json()["data"]
    assert failed_document["status"] == "PARSE_FAILED"
    assert failed_document["raw_source"]["sha256"]
    failed_retry = request(
        client,
        "POST",
        f"/api/qa/requirement-documents/{failed_document['_id']}/retry-parse",
        json={"expected_revision": failed_document["revision"]},
    )
    assert failed_retry["status"] == "PARSE_FAILED"
    assert failed_retry["revision"] > failed_document["revision"]
    extraction = request(
        client,
        "POST",
        f"/api/qa/requirement-documents/{document['_id']}/extract",
        201,
        json={"idempotency_key": f"extract-{stamp}"},
    )
    assert extraction["candidate_count"] == 2
    first_candidate, second_candidate = extraction["preview"]
    merged_candidate = {
        **first_candidate,
        "title": "Đăng nhập và khóa tài khoản",
        "content_doc": doc("Người dùng đăng nhập bằng email và tài khoản bị khóa sau 5 lần sai"),
        "source_refs": first_candidate["source_refs"] + second_candidate["source_refs"],
        "extraction_confidence": min(first_candidate["extraction_confidence"], second_candidate["extraction_confidence"]),
        "candidate_relation": "merged",
    }
    reviewed_import = request(
        client,
        "PATCH",
        f"/api/qa/requirement-imports/{extraction['_id']}",
        json={"expected_revision": 1, "preview": [merged_candidate], "review_note": "Gộp hai ứng viên"},
    )
    assert reviewed_import["candidate_count"] == 1
    split_candidates = [
        {**merged_candidate, "title": "Đăng nhập bằng email", "content_doc": doc("Người dùng đăng nhập bằng email"), "candidate_relation": "split-1"},
        {**merged_candidate, "title": "Khóa tài khoản sau năm lần sai", "content_doc": doc("Tài khoản bị khóa sau 5 lần sai"), "candidate_relation": "split-2"},
    ]
    reviewed_import = request(
        client,
        "PATCH",
        f"/api/qa/requirement-imports/{extraction['_id']}",
        json={"expected_revision": 2, "preview": split_candidates, "review_note": "Tách lại hai ứng viên"},
    )
    assert reviewed_import["candidate_count"] == 2
    confirmed_import = request(
        client,
        "POST",
        f"/api/qa/requirement-imports/{extraction['_id']}/confirm",
        json={"selected_indexes": [0], "expected_revision": 3},
    )
    assert len(confirmed_import["requirements"]) == 1
    assert confirmed_import["requirements"][0]["current_version"]["title"] == "Đăng nhập bằng email"
    direct_import = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/requirement-imports",
        201,
        json={"filename": "direct.md", "format": "md", "content": "Hệ thống ghi nhận lịch sử thay đổi"},
    )
    assert direct_import["status"] == "PREVIEW_READY"
    assert request(client, "GET", f"/api/qa/requirement-imports/{direct_import['_id']}")["_id"] == direct_import["_id"]
    uploaded_import_response = client.post(
        f"/api/qa/projects/{project_id}/requirement-imports/upload",
        headers=HEADERS,
        data={"format": "txt"},
        files={"file": ("direct.txt", b"He thong cho phep xuat bao cao", "text/plain")},
    )
    assert uploaded_import_response.status_code == 201, uploaded_import_response.text
    assert uploaded_import_response.json()["data"]["status"] == "PREVIEW_READY"
    repeated_extraction = request(
        client,
        "POST",
        f"/api/qa/requirement-documents/{document['_id']}/extract",
        201,
        json={"idempotency_key": f"extract-retry-{stamp}"},
    )
    assert repeated_extraction["_id"] == extraction["_id"]
    assert repeated_extraction["status"] == "CONFIRMED"
    request(client, "GET", f"/api/qa/projects/{project_id}", 403, headers=OUTSIDER)
    request(client, "GET", f"/api/qa/projects/{project_id}", 403, headers=SYSTEM_ADMIN)
    member = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/members",
        201,
        json={"user_id": "outsider-e2e", "project_role": "VIEWER"},
    )
    assert member["membership_revision"] == 1
    outsider_project = request(client, "GET", f"/api/qa/projects/{project_id}", headers=OUTSIDER)
    assert outsider_project["current_membership"]["project_role"] == "VIEWER"
    request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/requirements",
        403,
        headers=OUTSIDER,
        json={"title": "Viewer không được tạo requirement"},
    )
    member = request(
        client,
        "PATCH",
        f"/api/qa/projects/{project_id}/members/outsider-e2e",
        json={"expected_revision": 1, "project_role": "TESTER"},
    )
    assert member["project_role"] == "TESTER"
    request(
        client,
        "DELETE",
        f"/api/qa/projects/{project_id}/members/outsider-e2e",
    )
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
    requirement_detail = request(client, "GET", f"/api/qa/requirements/{requirement_id}")
    assert requirement_detail["_id"] == requirement_id
    updated_requirement = request(
        client,
        "PATCH",
        f"/api/qa/projects/{project_id}/requirements/{requirement_id}",
        json={"expected_revision": 1, "tags": ["profile", "boundary"]},
    )
    version_1 = updated_requirement["current_version"]
    requirement_page = request(
        client,
        "GET",
        f"/api/qa/projects/{project_id}/requirements?page=1&page_size=1&sort=requirement_key&q=profile",
    )
    assert requirement_page["page"] == 1
    assert requirement_page["page_size"] == 1
    assert requirement_page["total"] == 1
    lint = request(client, "POST", f"/api/qa/requirement-versions/{version_1['_id']}/ai/lint")
    assert lint["valid"] is True
    assert request(client, "POST", f"/api/qa/requirements/{requirement_id}/lint")["valid"] is True
    assert request(client, "POST", f"/api/qa/projects/{project_id}/requirements/{requirement_id}/lint")["valid"] is True
    version_1 = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/requirements/{requirement_id}/submit-review",
        json={"expected_revision": 2, "review_note": "Sẵn sàng duyệt baseline"},
    )
    version_1 = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/requirements/{requirement_id}/request-changes",
        json={"expected_revision": 3, "review_note": "Bổ sung xác nhận trước khi duyệt"},
    )
    version_1 = request(
        client,
        "POST",
        f"/api/qa/requirements/{requirement_id}/review",
        json={"expected_revision": 4, "review_note": "Đã bổ sung và gửi lại"},
    )
    version_1 = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/requirements/{requirement_id}/approve",
        json={"expected_revision": 5, "review_note": "Đã duyệt yêu cầu"},
    )
    approved_alias = request(
        client,
        "POST",
        f"/api/qa/requirements/{requirement_id}/approve",
        json={"expected_revision": version_1["revision"], "review_note": "Xác nhận idempotent"},
    )
    assert approved_alias["_id"] == version_1["_id"]
    alias_draft = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/test-cases",
        201,
        json={"title": "Kiểm thử alias tạo draft", "requirement_version_ids": [version_1["_id"]]},
    )
    assert alias_draft["project_id"] == project_id
    generated_scenarios = request(
        client,
        "POST",
        f"/api/qa/requirement-versions/{version_1['_id']}/ai/generate-scenarios",
        201,
        json={"categories": ["boundary"], "count_per_category": 1},
    )
    assert len(generated_scenarios["items"]) == 1
    generated_tests = request(
        client,
        "POST",
        f"/api/qa/requirement-versions/{version_1['_id']}/ai/generate-test-cases",
        201,
        json={"categories": ["negative"], "count_per_category": 1},
    )
    assert len(generated_tests["items"]) == 1
    project_generated_tests = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/test-cases/generate",
        201,
        json={"requirement_version_id": version_1["_id"], "categories": ["permission"], "count_per_category": 1},
    )
    assert len(project_generated_tests["items"]) == 1
    isolated_project = request(
        client,
        "POST",
        "/api/qa/projects",
        201,
        json={"key": f"ISO{stamp}", "name": "Isolation Project", "project_type": "web"},
    )
    request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/data-sets",
        422,
        json={"name": "Unsafe data", "variables": {"admin_password": "plain"}},
    )
    data_set = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/data-sets",
        201,
        json={
            "name": "Profile boundary data",
            "variables": {"valid_phone": "0912345678"},
            "secret_refs": {"admin_password": "secret://vault/project/admin_password"},
        },
    )
    assert request(client, "GET", f"/api/qa/data-sets/{data_set['_id']}")["_id"] == data_set["_id"]
    data_set_version_1 = data_set["current_version"]
    data_set_version_2 = request(
        client,
        "POST",
        f"/api/qa/data-sets/{data_set['_id']}/versions",
        201,
        json={
            "expected_current_version_id": data_set_version_1["_id"],
            "name": "Profile boundary data",
            "variables": {"valid_phone": "0912345678", "invalid_phone": "09123456789"},
            "secret_refs": {"admin_password": "secret://vault/project/admin_password"},
            "change_reason": "Bổ sung dữ liệu ngoài biên",
        },
    )
    assert request(client, "GET", f"/api/qa/projects/{project_id}/data-sets")
    assert len(request(client, "GET", f"/api/qa/data-sets/{data_set['_id']}/versions")) == 2
    request(
        client,
        "POST",
        f"/api/qa/data-sets/{data_set['_id']}/versions",
        409,
        json={
            "expected_current_version_id": data_set_version_1["_id"],
            "name": "Profile boundary data",
            "variables": {},
            "change_reason": "Ghi đè phiên bản cũ",
        },
    )
    request(
        client,
        "POST",
        f"/api/qa/projects/{isolated_project['_id']}/test-scenarios",
        422,
        json={"title": "Cross project source", "requirement_version_ids": [version_1["_id"]]},
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
    scenario = request(
        client,
        "PATCH",
        f"/api/qa/test-scenarios/{scenario['_id']}",
        json={"expected_revision": 1, "objective": "Kiểm tra biên 9 10 và 11 chữ số"},
    )
    assert request(client, "GET", f"/api/qa/projects/{project_id}/test-scenarios")
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
            "data_set_version_ids": [data_set_version_2["_id"]],
            "requirement_version_ids": [version_1["_id"]],
            "acceptance_criterion_ids": version_1["acceptance_criterion_ids"],
            "scenario_id": scenario["_id"],
            "origin": "manual",
        },
    )
    assert request(client, "GET", f"/api/qa/projects/{project_id}/test-case-drafts")
    test_lint = request(client, "POST", f"/api/qa/test-case-drafts/{draft['_id']}/lint")
    assert test_lint["valid"] is True
    assert request(client, "GET", f"/api/qa/test-case-drafts/{draft['_id']}")["_id"] == draft["_id"]
    assert request(client, "POST", f"/api/qa/test-cases/{draft['_id']}/lint")["valid"] is True
    assert request(client, "POST", f"/api/qa/projects/{project_id}/test-cases/{draft['_id']}/lint")["valid"] is True
    draft = request(
        client,
        "PATCH",
        f"/api/qa/test-cases/{draft['_id']}/draft",
        json={"expected_revision": 1, "title": "Số điện thoại 11 chữ số phải bị từ chối"},
    )
    draft = request(
        client,
        "PATCH",
        f"/api/qa/test-case-drafts/{draft['_id']}",
        json={"expected_revision": 2, "priority": "high"},
    )
    draft = request(
        client,
        "PATCH",
        f"/api/qa/projects/{project_id}/test-cases/{draft['_id']}",
        json={"expected_revision": 3, "risk": "high"},
    )
    draft = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/test-cases/{draft['_id']}/submit-review",
        json={"expected_revision": 4, "review_note": "Sẵn sàng duyệt test case"},
    )
    draft = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/test-cases/{draft['_id']}/request-changes",
        json={"expected_revision": 5, "review_note": "Bổ sung xác nhận dữ liệu biên"},
    )
    draft = request(
        client,
        "POST",
        f"/api/qa/test-cases/{draft['_id']}/review",
        json={"expected_revision": 6, "review_note": "Đã bổ sung và gửi lại"},
    )
    frozen = request(
        client,
        "POST",
        f"/api/qa/test-cases/{draft['_id']}/approve",
        201,
        json={"expected_revision": 7, "change_reason": "Phê duyệt test biên v1", "review_note": "Đã duyệt"},
    )
    replayed_frozen = request(
        client,
        "POST",
        f"/api/qa/test-case-drafts/{draft['_id']}/freeze",
        201,
        json={"expected_revision": 7, "change_reason": "Phê duyệt test biên v1", "review_note": "Đã duyệt"},
    )
    assert replayed_frozen["version"]["_id"] == frozen["version"]["_id"]
    project_replayed_frozen = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/test-cases/{draft['_id']}/approve",
        201,
        json={"expected_revision": 7, "change_reason": "Phê duyệt test biên v1", "review_note": "Đã duyệt"},
    )
    assert project_replayed_frozen["version"]["_id"] == frozen["version"]["_id"]
    test_case = frozen["test_case"]
    test_version_1 = frozen["version"]
    assert request(client, "GET", f"/api/qa/test-cases/{test_case['_id']}")["_id"] == test_case["_id"]
    assert request(client, "GET", f"/api/qa/test-cases/{test_case['_id']}/trace")["test_case"]["_id"] == test_case["_id"]
    assert test_version_1["data_set_version_ids"] == [data_set_version_2["_id"]]
    recovered_trace = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/trace-recovery",
        201,
    )
    assert recovered_trace["model"]["model"] == "trace-recovery-v1"
    assert isinstance(recovered_trace["items"], list)
    suggested_trace = request(
        client,
        "POST",
        "/api/qa/trace-links",
        201,
        json={"project_id": project_id, "source_type": "requirement_version", "source_id": version_1["_id"], "target_type": "test_case_version", "target_id": test_version_1["_id"], "link_type": "covers", "confidence": 0.8, "origin": "ai_suggested"},
    )
    confirmed_trace = request(client, "POST", f"/api/qa/trace-links/{suggested_trace['_id']}/confirm")
    assert confirmed_trace["status"] == "CONFIRMED"
    revoked_trace = request(client, "DELETE", f"/api/qa/projects/{project_id}/trace-links/{suggested_trace['_id']}")
    assert revoked_trace["status"] == "REVOKED"
    direct_revoke_trace = request(
        client,
        "POST",
        "/api/qa/trace-links",
        201,
        json={"project_id": project_id, "source_type": "requirement_version", "source_id": version_1["_id"], "target_type": "test_case_version", "target_id": test_version_1["_id"], "link_type": "derived_from", "confidence": 0.7, "origin": "ai_suggested"},
    )
    direct_revoke_trace = request(client, "POST", f"/api/qa/projects/{project_id}/trace-links/{direct_revoke_trace['_id']}/confirm")
    assert direct_revoke_trace["status"] == "CONFIRMED"
    direct_revoke_trace = request(client, "DELETE", f"/api/qa/trace-links/{direct_revoke_trace['_id']}")
    assert direct_revoke_trace["status"] == "REVOKED"
    rejected_trace = request(
        client,
        "POST",
        "/api/qa/trace-links",
        201,
        json={"project_id": project_id, "source_type": "requirement_version", "source_id": version_1["_id"], "target_type": "test_case_version", "target_id": test_version_1["_id"], "link_type": "relates_to", "confidence": 0.6, "origin": "ai_suggested"},
    )
    rejected_trace = request(client, "POST", f"/api/qa/trace-links/{rejected_trace['_id']}/reject")
    assert rejected_trace["status"] == "REJECTED"
    project_rejected_trace = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/trace-links",
        201,
        json={"project_id": project_id, "source_type": "test_scenario", "source_id": scenario["_id"], "target_type": "test_case_version", "target_id": test_version_1["_id"], "link_type": "verifies", "confidence": 0.5, "origin": "ai_suggested"},
    )
    project_rejected_trace = request(client, "POST", f"/api/qa/projects/{project_id}/trace-links/{project_rejected_trace['_id']}/reject")
    assert project_rejected_trace["status"] == "REJECTED"
    trace_export = client.get(f"/api/qa/projects/{project_id}/traceability/export", headers=HEADERS)
    assert trace_export.status_code == 200 and "source_type,source_id" in trace_export.text
    tagged = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/bulk/tags",
        json={"artifact_type": "test_case", "ids": [test_case["_id"]], "add_tags": ["profile", "boundary"]},
    )
    assert tagged["succeeded"] == [test_case["_id"]]
    test_page = request(
        client,
        "GET",
        f"/api/qa/projects/{project_id}/test-cases?page=1&page_size=1&tag=profile&sort=test_case_key",
    )
    assert test_page["total"] == 1
    assert test_page["items"][0]["_id"] == test_case["_id"]
    cloned_draft = request(
        client,
        "POST",
        f"/api/qa/test-cases/{test_case['_id']}/clone",
        201,
        json={"expected_current_version_id": test_version_1["_id"], "title": "Bản sao kiểm thử số điện thoại"},
    )
    assert cloned_draft["origin"] == "clone"
    assert any(
        item.get("artifact_version_id") == test_version_1["_id"]
        for item in cloned_draft["source_evidence"]
    )
    xlsx_export = client.get(f"/api/qa/projects/{project_id}/test-cases/export?format=xlsx", headers=HEADERS)
    assert xlsx_export.status_code == 200
    assert xlsx_export.headers["content-type"].startswith("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with zipfile.ZipFile(io.BytesIO(xlsx_export.content)) as workbook:
        assert "TC-PROFILE-043" in workbook.read("xl/worksheets/sheet1.xml").decode("utf-8")
    coverage = request(client, "GET", f"/api/qa/projects/{project_id}/coverage")
    assert coverage["requirement_coverage"] == 100
    assert coverage["acceptance_criterion_coverage"] == 100
    snapshot = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/coverage-snapshots",
        201,
        json={"label": "Baseline v1", "idempotency_key": f"coverage-{stamp}"},
    )
    snapshots = request(client, "GET", f"/api/qa/projects/{project_id}/coverage-snapshots")
    assert snapshots[0]["_id"] == snapshot["_id"]
    plan = request(
        client,
        "POST",
        "/api/qa/test-plans",
        201,
        json={"project_id": project_id, "name": "Kế hoạch Profile", "objective": "Xác nhận release", "scope_in": ["Profile"], "environment": "staging", "build": "1.0.0"},
    )
    assert request(client, "GET", f"/api/qa/test-plans/{plan['_id']}")["_id"] == plan["_id"]
    assert request(client, "GET", f"/api/qa/projects/{project_id}/test-plans")
    suite = request(
        client,
        "POST",
        "/api/qa/test-suites",
        201,
        json={"project_id": project_id, "name": "Regression Profile", "suite_type": "regression", "test_case_version_ids": [test_version_1["_id"]]},
    )
    assert request(client, "GET", f"/api/qa/test-suites/{suite['_id']}")["_id"] == suite["_id"]
    assert request(client, "GET", f"/api/qa/projects/{project_id}/test-suites")
    suite_bulk = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/bulk/test-cases/add-to-suite",
        json={"suite_id": suite["_id"], "test_case_ids": [test_case["_id"]], "expected_revision": 1},
    )
    assert suite_bulk["succeeded"] == [test_case["_id"]]
    abort_run = request(
        client,
        "POST",
        "/api/qa/test-runs",
        201,
        json={"project_id": project_id, "name": "Run bị hủy", "test_case_version_ids": [test_version_1["_id"]], "environment": "staging", "build": "abort-1"},
    )
    aborted = request(client, "POST", f"/api/qa/test-runs/{abort_run['_id']}/abort", json={"reason": "Dừng để đổi build"})
    assert aborted["status"] == "ABORTED"
    run = request(
        client,
        "POST",
        "/api/qa/test-runs",
        201,
        json={"project_id": project_id, "name": "Run build 1.0.0", "test_plan_id": plan["_id"], "test_suite_ids": [suite["_id"]], "test_case_version_ids": [], "environment": "staging", "build": "1.0.0"},
    )
    request(client, "POST", f"/api/qa/test-runs/{run['_id']}/start")
    blocked_archive = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/bulk/archive",
        json={"artifact_type": "test_case", "ids": [test_case["_id"]], "reason": "Kiểm tra ràng buộc lần chạy"},
    )
    assert blocked_archive["failed"] == [{"id": test_case["_id"], "code": "ACTIVE_RUN_LINK"}]
    run_page = request(
        client,
        "GET",
        f"/api/qa/projects/{project_id}/test-runs?page=1&page_size=1&status=IN_PROGRESS&sort=-created_at",
    )
    assert run_page["total"] == 1
    run_detail = request(client, "GET", f"/api/qa/test-runs/{run['_id']}")
    result = next(item for item in run_detail["results"] if item["test_case_version_id"] == test_version_1["_id"])
    assert request(client, "GET", f"/api/qa/projects/{project_id}/test-results")
    patched_execution = request(
        client,
        "PATCH",
        f"/api/qa/projects/{project_id}/test-executions/{result['_id']}",
        json={"status": "IN_PROGRESS", "step_results": [], "attachments": [], "note": "Bắt đầu execution", "idempotency_key": f"execution-start-{stamp}", "expected_revision": 1},
    )
    assert patched_execution["execution"]["revision"] == 2
    replayed_execution = request(
        client,
        "PATCH",
        f"/api/qa/projects/{project_id}/test-executions/{result['_id']}",
        json={"status": "IN_PROGRESS", "step_results": [], "attachments": [], "note": "Bắt đầu execution", "idempotency_key": f"execution-start-{stamp}", "expected_revision": 1},
    )
    assert replayed_execution["update"]["_id"] == patched_execution["update"]["_id"]
    completed_execution = request(
        client,
        "PATCH",
        f"/api/qa/projects/{project_id}/test-executions/{result['_id']}",
        json={"status": "FAIL", "step_results": [{"step_id": "step-1", "status": "FAIL"}], "actual_result_doc": doc("Ứng dụng chấp nhận 11 số"), "attachments": [], "note": "Đã xác nhận execution", "idempotency_key": f"execution-complete-{stamp}", "expected_revision": 2},
    )
    result = completed_execution["execution"]
    correction = request(
        client,
        "POST",
        f"/api/qa/test-results/{result['_id']}/corrections",
        json={"status": "FAIL", "reason": "Xác nhận lại sau khi đối chiếu evidence", "idempotency_key": f"correction-{stamp}"},
    )
    assert correction["result"]["status"] == "FAIL"
    duplicate_correction = request(
        client,
        "POST",
        f"/api/qa/test-results/{result['_id']}/corrections",
        json={"status": "FAIL", "reason": "Xác nhận lại sau khi đối chiếu evidence", "idempotency_key": f"correction-{stamp}"},
    )
    assert duplicate_correction["correction"]["_id"] == correction["correction"]["_id"]
    defect = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/defects",
        201,
        json={"project_id": project_id, "title": "Ứng dụng chấp nhận 11 số ngoài baseline", "description_doc": doc("Sai giới hạn"), "steps_to_reproduce": [], "actual_result_doc": doc("Chấp nhận"), "expected_result_doc": doc("Từ chối"), "severity": "major", "priority": "high", "environment": "staging", "build": "1.0.0", "linked_test_result_id": result["_id"], "linked_test_case_version_id": test_version_1["_id"], "linked_requirement_version_ids": [version_1["_id"]]},
    )
    assert defect["status"] == "NEW"
    assert isinstance(request(client, "GET", f"/api/qa/projects/{project_id}/defects/duplicates"), list)
    assert isinstance(request(client, "GET", f"/api/qa/projects/{project_id}/test-cases/duplicates"), list)
    trace_candidates = request(
        client,
        "GET",
        f"/api/qa/defects/{defect['_id']}/trace-candidates",
    )
    assert trace_candidates[0]["test_case_version_id"] == test_version_1["_id"]
    assert "CURRENT_LINK" in trace_candidates[0]["reason_codes"]
    defect = request(
        client,
        "PATCH",
        f"/api/qa/defects/{defect['_id']}",
        json={"expected_revision": defect["revision"], "assignee": "developer-e2e"},
    )
    assert defect["assignee"] == "developer-e2e"
    defect = request(
        client,
        "PATCH",
        f"/api/qa/projects/{project_id}/defects/{defect['_id']}",
        json={"expected_revision": defect["revision"], "priority": "high"},
    )
    assert request(client, "GET", f"/api/qa/projects/{project_id}/defects")["items"]
    defect = request(client, "POST", f"/api/qa/defects/{defect['_id']}/transition", json={"expected_revision": defect["revision"], "to_status": "CONFIRMED", "reason": "Đã tái hiện"})
    request(client, "POST", f"/api/qa/test-runs/{run['_id']}/complete")
    partial_run = request(
        client,
        "POST",
        "/api/qa/test-runs",
        201,
        json={
            "project_id": project_id,
            "name": "Run hoàn tất một phần",
            "test_case_version_ids": [test_version_1["_id"]],
            "environment": "staging",
            "build": "1.0.0-partial",
        },
    )
    request(client, "POST", f"/api/qa/test-runs/{partial_run['_id']}/start")
    denied_partial = request(
        client,
        "POST",
        f"/api/qa/test-runs/{partial_run['_id']}/complete",
        409,
    )
    assert denied_partial["error"]["code"] == "PARTIAL_EXECUTION"
    updated_project = request(
        client,
        "PATCH",
        f"/api/qa/projects/{project_id}",
        json={
            "expected_revision": updated_project["revision"],
            "settings": {"partial_complete_allowed": True},
        },
    )
    completed_partial = request(
        client,
        "POST",
        f"/api/qa/test-runs/{partial_run['_id']}/complete",
    )
    assert completed_partial["partial_completion"] is True
    assert completed_partial["completed_result_count"] == 0
    assert completed_partial["total_result_count"] == 1
    late_result = client.post(f"/api/qa/test-runs/{run['_id']}/results/{test_version_1['_id']}", headers=HEADERS, json={"status": "PASS", "step_results": [], "attachments": [], "note": "late", "idempotency_key": f"late-{stamp}"})
    assert late_result.status_code == 409
    assert late_result.json()["status"] == "FAILED"
    assert late_result.json()["error_code"] == "TEST_RUN_NOT_IN_PROGRESS"
    run_report = client.get(f"/api/qa/test-runs/{run['_id']}/report", headers=HEADERS)
    assert run_report.status_code == 200
    assert "TC-PROFILE-043" in run_report.text and "FAIL" in run_report.text
    defect = request(client, "POST", f"/api/qa/defects/{defect['_id']}/transition", json={"expected_revision": defect["revision"], "to_status": "IN_PROGRESS", "reason": "Bắt đầu sửa lỗi"})
    defect = request(client, "POST", f"/api/qa/defects/{defect['_id']}/transition", json={"expected_revision": defect["revision"], "to_status": "RESOLVED", "reason": "Đã sửa giới hạn"})
    defect = request(client, "POST", f"/api/qa/defects/{defect['_id']}/transition", json={"expected_revision": defect["revision"], "to_status": "READY_FOR_RETEST", "reason": "Sẵn sàng kiểm tra lại"})
    request(
        client,
        "POST",
        f"/api/qa/defects/{defect['_id']}/transition",
        409,
        json={"expected_revision": defect["revision"], "to_status": "CLOSED", "reason": "Không có retest"},
    )
    retest_run = request(
        client,
        "POST",
        "/api/qa/test-runs",
        201,
        json={"project_id": project_id, "name": "Retest build 1.0.1", "test_case_version_ids": [test_version_1["_id"]], "environment": "staging", "build": "1.0.1"},
    )
    request(client, "POST", f"/api/qa/test-runs/{retest_run['_id']}/start")
    retest_result = request(
        client,
        "POST",
        f"/api/qa/test-runs/{retest_run['_id']}/results/{test_version_1['_id']}",
        json={"status": "PASS", "step_results": [{"step_id": "step-1", "status": "PASS"}], "attachments": [], "note": "Giới hạn đã đúng", "idempotency_key": f"retest-result-{stamp}"},
    )
    request(client, "POST", f"/api/qa/test-runs/{retest_run['_id']}/complete")
    retest = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/defects/{defect['_id']}/retest",
        json={"test_result_id": retest_result["_id"], "expected_revision": defect["revision"], "note": "Retest đạt", "idempotency_key": f"defect-retest-{stamp}"},
    )
    assert retest["defect"]["status"] == "CLOSED"
    duplicate_retest = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/defects/{defect['_id']}/retest",
        json={"test_result_id": retest_result["_id"], "expected_revision": defect["revision"], "note": "Retest đạt", "idempotency_key": f"defect-retest-{stamp}"},
    )
    assert duplicate_retest["retest"]["_id"] == retest["retest"]["_id"]
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
    version_2 = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/requirements/{requirement_id}/submit-review",
        json={"expected_revision": 1, "review_note": "Duyệt thay đổi giới hạn"},
    )
    version_2 = request(client, "POST", f"/api/qa/requirement-versions/{version_2['_id']}/baseline", json={"expected_revision": 2, "review_note": "Đã duyệt thay đổi"})
    assert len(request(client, "GET", f"/api/qa/requirements/{requirement_id}/versions")) == 2
    comparison = request(
        client,
        "POST",
        f"/api/qa/requirements/{requirement_id}/compare",
        json={"from_version_id": version_1["_id"], "to_version_id": version_2["_id"]},
    )
    assert comparison["comparison_algorithm_version"] == "semantic-diff-v1"
    diff_alias = request(
        client,
        "GET",
        f"/api/qa/requirements/{requirement_id}/diff?from={version_1['_id']}&to={version_2['_id']}",
    )
    assert diff_alias["comparison_algorithm_version"] == "semantic-diff-v1"
    assert request(client, "GET", f"/api/qa/requirements/{requirement_id}/coverage")["requirement_id"] == requirement_id
    change_set = request(
        client,
        "POST",
        f"/api/qa/requirements/{requirement_id}/change-sets",
        201,
        json={"from_version_id": version_1["_id"], "to_version_id": version_2["_id"]},
    )
    assert change_set["changes"][0]["type"] == "MODIFIED_BOUNDARY"
    assert request(client, "GET", f"/api/qa/change-sets/{change_set['_id']}")["_id"] == change_set["_id"]
    assert request(client, "GET", f"/api/qa/projects/{project_id}/change-sets")
    change_set = request(
        client,
        "POST",
        f"/api/qa/change-sets/{change_set['_id']}/review",
        json={"expected_revision": 1, "changes": change_set["changes"], "review_note": "Đã xác nhận ChangeFact"},
    )
    assert change_set["status"] == "REVIEWED"
    impact = request(client, "POST", f"/api/qa/change-sets/{change_set['_id']}/impact-analysis", 201)
    project_impact = request(client, "POST", f"/api/qa/projects/{project_id}/changesets/{change_set['_id']}/analyze-impact", 201)
    assert project_impact["_id"] == impact["_id"]
    assert request(client, "GET", f"/api/qa/change-sets/{change_set['_id']}/impact-analysis")["_id"] == impact["_id"]
    assert request(client, "GET", f"/api/qa/impact-analyses/{impact['_id']}")["_id"] == impact["_id"]
    perspective = request(
        client,
        "POST",
        f"/api/qa/impact-analyses/{impact['_id']}/perspectives",
        201,
        json={"review_note": "Góc nhìn bổ sung từ QA Lead"},
    )
    assert perspective["impact_analysis_id"] == impact["_id"]
    impacted = next(item for item in impact["affected_test_cases"] if item["test_case_id"] == test_case["_id"])
    assert impacted["classification"] == "NEEDS_UPDATE"
    impact = request(
        client,
        "POST",
        f"/api/qa/impact-analyses/{impact['_id']}/review",
        json={"expected_revision": 1, "review_note": "Tester xác nhận phân tích tác động"},
    )
    assert impact["status"] == "REVIEWED"
    proposals = request(client, "POST", f"/api/qa/impact-analyses/{impact['_id']}/maintenance-proposals", 201)
    proposal = next(item for item in proposals if item["proposal_type"] == "UPDATE_TEST_CASE")
    assert request(client, "GET", f"/api/qa/maintenance-proposals/{proposal['_id']}")["_id"] == proposal["_id"]
    assert request(client, "GET", f"/api/qa/projects/{project_id}/maintenance-proposals")
    proposal = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/ai-proposals/{proposal['_id']}/review",
        json={"expected_revision": 1, "review_note": "Rà soát trước khi từ chối"},
    )
    rejected_proposal = request(
        client,
        "POST",
        f"/api/qa/maintenance-proposals/{proposal['_id']}/reject",
        json={"expected_revision": 2, "review_note": "Từ chối bản đề xuất đầu tiên"},
    )
    assert rejected_proposal["status"] == "REJECTED"
    rejected_bulk = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/bulk/approve-proposals",
        json={"proposal_ids": [proposal["_id"]], "review_note": "Không áp dụng đề xuất đã từ chối"},
    )
    assert rejected_bulk["failed"][0]["code"] == "INVALID_STATE_TRANSITION"
    rejected_proposal = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/ai-proposals/{proposal['_id']}/reject",
        json={"expected_revision": rejected_proposal["revision"], "review_note": "Xác nhận từ chối idempotent"},
    )
    assert rejected_proposal["status"] == "REJECTED"
    generated = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/bulk/impact-proposals",
        json={"impact_analysis_ids": [impact["_id"]]},
    )
    assert generated["succeeded"] == [impact["_id"]]
    proposal = next(
        item
        for item in request(client, "GET", f"/api/qa/projects/{project_id}/maintenance-proposals?status=PENDING")
        if item["proposal_type"] == "UPDATE_TEST_CASE"
    )
    proposal = request(
        client,
        "POST",
        f"/api/qa/maintenance-proposals/{proposal['_id']}/regenerate",
        201,
        json={"expected_revision": 1, "instruction": "Ưu tiên cập nhật kết quả mong đợi theo biên mới"},
    )
    assert proposal["parent_proposal_id"]
    applied = request(
        client,
        "POST",
        f"/api/qa/maintenance-proposals/{proposal['_id']}/accept-with-edit",
        201,
        json={"expected_revision": 1, "patch": {"expected_result_doc": doc("Hệ thống chấp nhận số điện thoại 11 chữ số")}, "review_note": "Tester xác nhận thay đổi"},
    )
    test_version_2 = applied["result"]
    assert test_version_2["version"] == 2
    accepted_replay = request(
        client,
        "POST",
        f"/api/qa/maintenance-proposals/{proposal['_id']}/accept",
        201,
        json={"expected_revision": 1, "review_note": "Xác nhận áp dụng idempotent"},
    )
    assert accepted_replay["result"]["_id"] == test_version_2["_id"]
    project_accepted_replay = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/ai-proposals/{proposal['_id']}/approve",
        201,
        json={"expected_revision": 1, "review_note": "Xác nhận áp dụng idempotent theo project"},
    )
    assert project_accepted_replay["result"]["_id"] == test_version_2["_id"]
    test_diff = request(
        client,
        "GET",
        f"/api/qa/test-cases/{test_case['_id']}/diff?from={test_version_1['_id']}&to={test_version_2['_id']}",
    )
    assert test_diff["changes"]
    version_draft = request(
        client,
        "POST",
        f"/api/qa/test-cases/{test_case['_id']}/versions/draft",
        201,
        json={"expected_current_version_id": test_version_2["_id"], "change_reason": "Chuẩn bị phiên bản tiếp theo"},
    )
    assert version_draft["origin"] == "manual"
    versions = request(client, "GET", f"/api/qa/test-cases/{test_case['_id']}/versions")
    assert [item["version"] for item in versions] == [2, 1]
    run_detail = request(client, "GET", f"/api/qa/test-runs/{run['_id']}")
    assert run_detail["test_case_version_ids"] == [test_version_1["_id"]]
    regression = request(client, "POST", f"/api/qa/change-sets/{change_set['_id']}/regression-recommendation", 201)
    assert regression["items"][0]["level"] == "MUST_RUN"
    assert request(client, "GET", f"/api/qa/change-sets/{change_set['_id']}/regression-recommendation")["_id"] == regression["_id"]
    project_regression = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/regression/generate",
        201,
        json={"change_set_id": change_set["_id"]},
    )
    assert project_regression["_id"] == regression["_id"]
    assert request(client, "GET", f"/api/qa/regression-recommendations/{regression['_id']}")["_id"] == regression["_id"]
    regression = request(
        client,
        "PATCH",
        f"/api/qa/regression-recommendations/{regression['_id']}",
        json={"expected_revision": 1, "selected_test_case_version_ids": [test_version_2["_id"]], "review_note": "Chốt phạm vi regression"},
    )
    approved_regression = request(
        client,
        "POST",
        f"/api/qa/regression-recommendations/{regression['_id']}/approve",
        201,
        json={"expected_revision": 2, "review_note": "QA Lead duyệt regression scope"},
    )
    assert approved_regression["test_suite"]["test_case_version_ids"] == [test_version_2["_id"]]
    project_approved_regression = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/regression/{regression['_id']}/approve",
        201,
        json={"expected_revision": approved_regression["recommendation"]["revision"], "review_note": "Xác nhận regression idempotent"},
    )
    assert project_approved_regression["test_suite"]["_id"] == approved_regression["test_suite"]["_id"]
    search = request(client, "POST", f"/api/qa/projects/{project_id}/knowledge/search", json={"query": "điện thoại 11", "artifact_types": ["requirement_version", "test_case_version"], "limit": 20})
    assert search["items"] and all(item["project_id"] == project_id for item in search["items"])
    audits = request(client, "GET", f"/api/qa/projects/{project_id}/audit")
    assert any(item["action"] == "maintenance_proposal_applied" for item in audits)
    dashboard = request(client, "GET", f"/api/qa/projects/{project_id}/dashboard")
    assert dashboard["requirements"] == 1 and dashboard["active_tests"] == 1
    review_required = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/bulk/test-cases/mark-review-required",
        json={"test_case_ids": [test_case["_id"]], "reason": "Rà soát sau thay đổi regression"},
    )
    assert review_required["succeeded"] == [test_case["_id"]]
    obsolete_requirement = request(
        client,
        "POST",
        f"/api/qa/requirements/{requirement_id}/obsolete",
        json={"expected_current_version_id": version_2["_id"], "reason": "Hành vi không còn thuộc phạm vi"},
    )
    assert obsolete_requirement["status"] == "OBSOLETE"
    obsolete_test_case = request(
        client,
        "POST",
        f"/api/qa/test-cases/{test_case['_id']}/obsolete",
        json={"expected_current_version_id": test_version_2["_id"], "reason": "Ca kiểm thử không còn thuộc phạm vi"},
    )
    assert obsolete_test_case["status"] == "OBSOLETE"
    obsolete_matrix = request(client, "GET", f"/api/qa/projects/{project_id}/traceability")
    assert any(
        item["obsolete"] and "OBSOLETE_SOURCE" in item["obsolete_reasons"]
        for item in obsolete_matrix["trace_links"]
    )
    assert any(
        item["obsolete"] and "OBSOLETE_TARGET" in item["obsolete_reasons"]
        for item in obsolete_matrix["trace_links"]
    )
    restored_test_case = request(
        client,
        "POST",
        f"/api/qa/test-cases/{test_case['_id']}/restore",
        json={"expected_current_version_id": test_version_2["_id"], "reason": "Khôi phục để tiếp tục regression"},
    )
    assert restored_test_case["status"] == "ACTIVE"
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
    direct_test_import = request(
        client,
        "POST",
        f"/api/qa/projects/{project_id}/test-case-imports",
        201,
        json={"filename": "direct.csv", "format": "csv", "content": "title,type,action,expected\nDirect imported case,validation,Submit,Accepted\n"},
    )
    assert direct_test_import["status"] == "PREVIEW_READY"
    assert import_job["status"] == "PREVIEW_READY" and len(import_job["preview"]) == 1
    imported = request(
        client,
        "POST",
        f"/api/qa/test-case-imports/{import_job['_id']}/confirm",
        json={"selected_indexes": [0]},
    )
    assert len(imported["drafts"]) == 1

print("testing vertical integration passed")
