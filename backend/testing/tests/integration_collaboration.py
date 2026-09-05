import os
import time

import httpx
import jwt


BASE_URL = os.getenv("TESTING_TEST_URL", "http://testing:8000")
HEADERS = {"Authorization": "Bearer " + jwt.encode({"uid": "collaboration-lead", "sub": "collaboration-lead@test.local", "system_role": "USER"}, os.environ["SECRET_KEY"], algorithm="HS256")}


def doc(text):
    return {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]}


def request(client, method, path, expected=200, raw=False, **kwargs):
    response = client.request(method, path, headers=HEADERS, **kwargs)
    assert response.status_code == expected, f"{method} {path} {response.status_code} {response.text}"
    body = response.json()
    return body if raw or expected >= 400 else body.get("data")


with httpx.Client(base_url=BASE_URL, timeout=60) as client:
    stamp = int(time.time() * 1000)
    project = request(client, "POST", "/kiem-thu/du-an", 201, json={"key": f"CO{stamp}", "name": "Cộng tác", "project_type": "web"})
    project_id = project["_id"]
    draft = request(client, "POST", f"/kiem-thu/du-an/{project_id}/ban-nhap-ca-kiem-thu", 201, json={"test_case_key": "TC-COL-001", "title": "Bản nháp cộng tác", "type": "happy_path", "priority": "medium", "risk": "medium", "objective_doc": doc("Cộng tác"), "preconditions_doc": doc("Có quyền"), "steps": [{"id": "step-1", "order": 1, "action_doc": doc("Sửa"), "test_data": {}, "expected_doc": doc("Đã sửa")}], "expected_result_doc": doc("Hoàn tất"), "postconditions_doc": doc("Đã lưu")})
    draft_id = draft["_id"]
    presence = request(client, "PUT", f"/kiem-thu/du-an/{project_id}/cong-tac/phien", json={"artifact_type": "test_case", "artifact_id": draft_id, "client_id": f"browser-{stamp}"})
    assert presence["user_id"] == "collaboration-lead"
    present = request(client, "GET", f"/kiem-thu/du-an/{project_id}/cong-tac/hien-dien?artifact_type=test_case&artifact_id={draft_id}")
    assert present[0]["client_id"] == f"browser-{stamp}"
    first = request(client, "POST", f"/kiem-thu/du-an/{project_id}/cong-tac/ca-kiem-thu/{draft_id}/thao-tac", raw=True, json={"base_revision": 1, "operation_id": f"operation-one-{stamp}", "changes": {"title": "Tên do người thứ nhất sửa"}})
    assert first["meta"]["revision"] == 2
    conflict_response = request(client, "POST", f"/kiem-thu/du-an/{project_id}/cong-tac/ca-kiem-thu/{draft_id}/thao-tac", 409, json={"base_revision": 1, "operation_id": f"operation-two-{stamp}", "changes": {"title": "Tên do người thứ hai sửa"}})
    conflict_id = conflict_response["error"]["details"]["conflict_id"]
    conflicts = request(client, "GET", f"/kiem-thu/du-an/{project_id}/cong-tac/xung-dot")
    assert conflicts[0]["_id"] == conflict_id
    resolved = request(client, "POST", f"/kiem-thu/du-an/{project_id}/cong-tac/xung-dot/{conflict_id}/giai-quyet", json={"expected_revision": 2, "resolution": "APPLY_INCOMING", "reason": "Chấp nhận nội dung mới sau khi rà soát"})
    assert resolved["conflict"]["status"] == "RESOLVED"
    requirement = request(client, "POST", f"/kiem-thu/du-an/{project_id}/yeu-cau", 201, json={"requirement_key": "REQ-COL-001", "title": "Yêu cầu cộng tác", "type": "functional", "priority": "high", "risk": "high", "content_doc": doc("Nội dung ban đầu"), "acceptance_criteria": [{"key": "AC-1", "content_doc": doc("Tiêu chí ban đầu")}], "business_rules": [], "actors": [], "dependencies": [], "source_refs": []})
    requirement_result = request(client, "POST", f"/kiem-thu/du-an/{project_id}/cong-tac/yeu-cau/{requirement['_id']}/thao-tac", raw=True, json={"base_revision": 1, "operation_id": f"requirement-operation-{stamp}", "changes": {"acceptance_criteria": [{"key": "AC-1", "content_doc": doc("Tiêu chí đã sửa")}, {"key": "AC-2", "content_doc": doc("Tiêu chí bổ sung")} ]}})
    assert requirement_result["meta"]["revision"] == 2
    assert len(requirement_result["data"]["current_version"]["acceptance_criterion_ids"]) == 2
    missing_requirement = request(client, "POST", f"/kiem-thu/du-an/{project_id}/cong-tac/yeu-cau/khong-ton-tai/thao-tac", 404, json={"base_revision": 1, "operation_id": f"missing-{stamp}", "changes": {"title": "Không áp dụng"}})
    assert missing_requirement["error"]["code"] == "ENTITY_NOT_FOUND"

print("collaboration integration passed")
