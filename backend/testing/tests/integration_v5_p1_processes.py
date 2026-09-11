import os
import time

import httpx
import jwt


base_url = os.getenv("TESTING_TEST_URL", "http://testing:8000")


def identity(user_id, system_role="USER"):
    return {"Authorization": "Bearer " + jwt.encode({"uid": user_id, "sub": f"{user_id}@test.local", "system_role": system_role}, os.environ["SECRET_KEY"], algorithm="HS256")}


lead = identity("v5-p1-lead")
tester = identity("v5-p1-tester")
ba = identity("v5-p1-ba")
developer = identity("v5-p1-developer")
viewer = identity("v5-p1-viewer")
admin_without_membership = identity("v5-p1-platform-admin", "ADMIN")


def call(client, method, path, headers=lead, expected=200, **kwargs):
    response = client.request(method, path, headers=headers, **kwargs)
    assert response.status_code == expected, f"{method} {path} {response.status_code} {response.text}"
    return response.json().get("data") if expected < 400 else response.json()


def doc(text):
    return {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]}


with httpx.Client(base_url=base_url, timeout=120) as client:
    stamp = int(time.time() * 1000)
    project = call(client, "POST", "/kiem-thu/du-an", expected=201, json={"key": f"P1{stamp}", "name": "V5 P1 process", "project_type": "web", "settings": {}})
    project_id = project["_id"]
    denied_admin = call(client, "GET", f"/kiem-thu/du-an/{project_id}/phien-ra-soat", headers=admin_without_membership, expected=403)
    assert denied_admin["error"]["code"] in {"PROJECT_MEMBERSHIP_REQUIRED", "PROJECT_PERMISSION_DENIED"}
    for user_id, role in [("v5-p1-tester", "TESTER"), ("v5-p1-ba", "BA"), ("v5-p1-developer", "DEVELOPER"), ("v5-p1-viewer", "VIEWER")]:
        call(client, "POST", f"/kiem-thu/du-an/{project_id}/thanh-vien", expected=201, json={"user_id": user_id, "project_role": role})

    requirement = call(client, "POST", f"/kiem-thu/du-an/{project_id}/yeu-cau", expected=201, json={"title": "Yêu cầu P1", "content_doc": doc("Hệ thống phải phản hồi đúng"), "acceptance_criteria": [{"key": "AC-01", "content_doc": doc("Trả về thành công")} ]})
    version_id = requirement["current_version"]["_id"]

    review = call(client, "POST", f"/kiem-thu/du-an/{project_id}/phien-ra-soat", headers=tester, expected=201, json={"idempotency_key": f"review-{stamp}", "review_type": "REQUIREMENT_REVIEW", "artifact_type": "REQUIREMENT", "artifact_id": requirement["_id"], "artifact_version_id": version_id, "objective": "Rà soát khả năng kiểm thử", "checklist_version": "V5-1", "moderator_id": "v5-p1-tester", "author_id": "v5-p1-ba", "reviewers": ["v5-p1-developer"], "checklist": [{"id": "C1", "label": "Đầy đủ", "status": "PASS"}]})
    replayed = call(client, "POST", f"/kiem-thu/du-an/{project_id}/phien-ra-soat", headers=tester, expected=201, json={"idempotency_key": f"review-{stamp}", "review_type": "REQUIREMENT_REVIEW", "artifact_type": "REQUIREMENT", "artifact_id": requirement["_id"], "artifact_version_id": version_id, "objective": "Rà soát khả năng kiểm thử", "checklist_version": "V5-1", "moderator_id": "v5-p1-tester", "author_id": "v5-p1-ba", "reviewers": ["v5-p1-developer"]})
    assert replayed["_id"] == review["_id"]
    denied_review = call(client, "POST", f"/kiem-thu/du-an/{project_id}/phien-ra-soat", headers=viewer, expected=403, json={"review_type": "REQUIREMENT_REVIEW", "artifact_type": "REQUIREMENT", "artifact_id": requirement["_id"], "artifact_version_id": version_id, "objective": "Không được tạo", "checklist_version": "V5", "moderator_id": "v5-p1-viewer", "author_id": "v5-p1-ba", "reviewers": ["v5-p1-developer"]})
    assert denied_review["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    call(client, "GET", f"/kiem-thu/du-an/{project_id}/phien-ra-soat", headers=viewer)
    review = call(client, "PATCH", f"/kiem-thu/phien-ra-soat/{review['_id']}", headers=tester, json={"expected_revision": review["revision"], "objective": "Rà soát khả năng kiểm thử và truy vết"})
    call(client, "GET", f"/kiem-thu/phien-ra-soat/{review['_id']}", headers=viewer)
    review = call(client, "POST", f"/kiem-thu/phien-ra-soat/{review['_id']}/bat-dau", headers=tester, json={"expected_revision": review["revision"], "note": "Bắt đầu"})
    finding = call(client, "POST", f"/kiem-thu/phien-ra-soat/{review['_id']}/findings", headers=developer, expected=201, json={"category": "TESTABILITY", "severity": "MAJOR", "anchor": {"version_id": version_id}, "description": "Thiếu trường hợp lỗi", "suggested_action": "Bổ sung", "owner_id": "v5-p1-ba"})
    blocked_review = call(client, "POST", f"/kiem-thu/phien-ra-soat/{review['_id']}/hoan-tat", headers=tester, expected=409, json={"expected_revision": review["revision"], "decision": "ACCEPTED", "note": "Không hợp lệ"})
    assert blocked_review["error"]["code"] == "OPEN_MAJOR_REVIEW_FINDINGS"
    call(client, "PATCH", f"/kiem-thu/phien-ra-soat/finding/{finding['_id']}", headers=developer, json={"expected_revision": finding["revision"], "status": "RESOLVED", "resolution": "Đã bổ sung"})
    review = call(client, "POST", f"/kiem-thu/phien-ra-soat/{review['_id']}/hoan-tat", headers=tester, json={"expected_revision": review["revision"], "decision": "ACCEPTED", "note": "Đã xử lý"})
    assert review["metrics"]["major_count"] == 1 and review["metrics"]["open_count"] == 0

    strategy = call(client, "POST", f"/kiem-thu/du-an/{project_id}/chien-luoc", expected=201, json={"key": "P1_STRATEGY", "name": "Chiến lược P1", "objective": "Kiểm chứng P1", "test_levels": ["SYSTEM"], "test_types": ["FUNCTIONAL", "SECURITY", "PERFORMANCE"], "approach": "Dựa trên rủi ro", "risk_model": {"probability_scale": [{"value": 1, "label": "Thấp"}], "impact_scale": [{"value": 1, "label": "Thấp"}], "risk_exposure_formula": "probability * impact", "thresholds": [{"level": "LOW", "min": 1}]}, "reviewer_ids": ["v5-p1-tester"]})
    strategy = call(client, "POST", f"/kiem-thu/chien-luoc/{strategy['_id']}/gui-ra-soat", json={"expected_revision": strategy["revision"], "note": "Gửi"})
    strategy = call(client, "POST", f"/kiem-thu/chien-luoc/{strategy['_id']}/phe-duyet", json={"expected_revision": strategy["revision"], "note": "Duyệt"})
    release = call(client, "POST", f"/kiem-thu/du-an/{project_id}/ban-phat-hanh", expected=201, json={"key": f"REL-{stamp}", "name": "Release P1", "version": "1.0"})
    build = call(client, "POST", f"/kiem-thu/du-an/{project_id}/ban-dung", expected=201, json={"identifier": f"BLD-{stamp}", "version": "1.0", "release_id": release["_id"], "idempotency_key": f"build-{stamp}"})
    environment = call(client, "POST", f"/kiem-thu/du-an/{project_id}/moi-truong", expected=201, json={"name": f"Staging {stamp}", "environment_type": "staging", "availability": "AVAILABLE"})
    plan = call(client, "POST", f"/kiem-thu/du-an/{project_id}/ke-hoach-kiem-thu", expected=201, json={"project_id": project_id, "name": "Kế hoạch P1", "strategy_version_id": strategy["_id"], "release_id": release["_id"], "build_id": build["_id"], "quality_targets": [{"criterion_id": "P1-GATE", "criterion": "Không có critical", "type": "OPEN_CRITICAL_MAX", "threshold": 0}]})
    plan = call(client, "POST", f"/kiem-thu/ke-hoach-kiem-thu/{plan['_id']}/phe-duyet", json={"expected_revision": plan["revision"], "review_note": "Duyệt"})
    run = call(client, "POST", "/kiem-thu/lan-chay-kiem-thu", expected=201, json={"project_id": project_id, "name": "Run P1", "test_plan_id": plan["_id"], "test_case_version_ids": [], "environment": environment["name"], "environment_id": environment["_id"], "release_id": release["_id"], "build_id": build["_id"]})
    run = call(client, "POST", f"/kiem-thu/lan-chay-kiem-thu/{run['_id']}/bat-dau")
    incident = call(client, "POST", f"/kiem-thu/du-an/{project_id}/incident-moi-truong", headers=tester, expected=201, json={"idempotency_key": f"incident-{stamp}", "environment_id": environment["_id"], "build_id": build["_id"], "observed_at": "2026-09-11T00:00:00Z", "severity": "BLOCKER", "type": "UNAVAILABLE", "description": "Môi trường ngừng hoạt động", "affected_run_ids": [run["_id"]], "evidence_refs": ["log://incident"], "owner_id": "v5-p1-tester"})
    incidents = call(client, "GET", f"/kiem-thu/du-an/{project_id}/incident-moi-truong", headers=viewer)
    assert incidents["total"] == 1 and incidents["items"][0]["_id"] == incident["_id"]
    incident = call(client, "PATCH", f"/kiem-thu/incident-moi-truong/{incident['_id']}", headers=tester, json={"expected_revision": incident["revision"], "description": "Môi trường ngừng hoạt động trong lúc chạy kiểm thử"})
    incident = call(client, "GET", f"/kiem-thu/incident-moi-truong/{incident['_id']}", headers=viewer)
    paused_run = call(client, "GET", f"/kiem-thu/lan-chay-kiem-thu/{run['_id']}", headers=viewer)
    assert paused_run["execution_paused"] is True and paused_run["paused_by_environment_incident_id"] == incident["_id"]

    defect = call(client, "POST", f"/kiem-thu/du-an/{project_id}/loi", headers=tester, expected=201, json={"project_id": project_id, "title": "Lỗi critical P1", "severity": "critical", "priority": "critical", "release_id": release["_id"], "build_id": build["_id"], "root_cause_category": "UNKNOWN", "prevention_candidate": True})
    snapshot = call(client, "POST", f"/kiem-thu/du-an/{project_id}/giam-sat-kiem-thu/snapshot", expected=201, json={"test_plan_id": plan["_id"], "actual_effort": 1, "risks": [], "blockers": []})
    assert snapshot["quality_gate_status"] == "FAIL" and snapshot["metrics"]["blocker_environment_incidents"] == 1
    completion = call(client, "POST", f"/kiem-thu/du-an/{project_id}/hoan-tat-kiem-thu", headers=tester, expected=201, json={"idempotency_key": f"incident-completion-{stamp}", "snapshot_id": snapshot["_id"], "build_id": build["_id"], "lessons_learned": [{"category": "BLOCKER", "text": "Môi trường bị gián đoạn trong lúc thực thi"}]})
    assert any(item["criterion_id"] == "ENVIRONMENT-INCIDENT-GATE" and item["status"] == "FAIL" for item in completion["exit_criteria_evaluation"])
    completion_narrative = call(client, "POST", f"/kiem-thu/hoan-tat-kiem-thu/{completion['_id']}/ai/ban-nhap", headers=tester, json={"idempotency_key": f"completion-ai-{stamp}", "instruction": "Diễn giải đúng bằng chứng"})
    assert completion_narrative["candidate_only"] is True and completion_narrative["status"] == "SUCCESS" and completion_narrative["suggestions"][0]["executive_summary"]
    lesson_clusters = call(client, "POST", f"/kiem-thu/hoan-tat-kiem-thu/{completion['_id']}/ai/gom-bai-hoc", headers=tester, json={"idempotency_key": f"lessons-ai-{stamp}", "instruction": "Gom theo chủ đề"})
    assert lesson_clusters["candidate_only"] is True and lesson_clusters["status"] == "SUCCESS" and lesson_clusters["suggestions"][0]["source_indices"] == [0]
    status_report = call(client, "POST", f"/kiem-thu/du-an/{project_id}/bao-cao-trang-thai/tao-tu-snapshot", headers=tester, expected=201, json={"snapshot_id": snapshot["_id"], "build_id": build["_id"], "reporting_period": {"start_at": "2026-09-01T00:00:00Z", "end_at": "2026-09-11T00:00:00Z"}})
    status_narrative = call(client, "POST", f"/kiem-thu/bao-cao-trang-thai/{status_report['_id']}/ai/ban-nhap", headers=tester, json={"idempotency_key": f"status-ai-{stamp}", "instruction": "Diễn giải đúng snapshot"})
    assert status_narrative["candidate_only"] is True and status_narrative["status"] == "SUCCESS" and status_narrative["suggestions"][0]["forecast"]

    definition = call(client, "POST", f"/kiem-thu/du-an/{project_id}/dinh-nghia-do-luong", expected=201, json={"idempotency_key": f"metric-{stamp}", "key": "PASS_RATE", "name": "Tỷ lệ đạt", "objective": "Theo dõi kết quả", "formula": "pass / decisive * 100", "unit": "%", "data_sources": ["test_monitoring_snapshots"], "dimensions": ["release"], "aggregation": "RATIO", "period": "RELEASE", "target": 95, "warning_threshold": 90, "critical_threshold": 80, "owner_role": "QA_LEAD"})
    call(client, "GET", f"/kiem-thu/du-an/{project_id}/dinh-nghia-do-luong", headers=viewer)
    definition = call(client, "PATCH", f"/kiem-thu/dinh-nghia-do-luong/{definition['_id']}", json={"expected_revision": definition["revision"], "objective": "Theo dõi kết quả theo release"})
    invalid_thresholds = call(client, "PATCH", f"/kiem-thu/dinh-nghia-do-luong/{definition['_id']}", expected=422, json={"expected_revision": definition["revision"], "warning_threshold": 100})
    assert invalid_thresholds["error"]["code"] == "INVALID_MEASUREMENT_THRESHOLDS"
    definition = call(client, "POST", f"/kiem-thu/dinh-nghia-do-luong/{definition['_id']}/trang-thai", json={"expected_revision": definition["revision"], "status": "ACTIVE", "note": "Kích hoạt"})
    metric = call(client, "POST", f"/kiem-thu/du-an/{project_id}/anh-do-luong", headers=tester, expected=201, json={"idempotency_key": f"snapshot-{stamp}", "definition_id": definition["_id"], "release_id": release["_id"], "dimensions": {"release": release["_id"]}})
    assert metric["measurement_definition_version"] == definition["version"] and metric["source_fingerprint"]
    call(client, "GET", f"/kiem-thu/du-an/{project_id}/anh-do-luong", headers=viewer)
    call(client, "GET", f"/kiem-thu/anh-do-luong/{metric['_id']}", headers=viewer)

    evaluation = call(client, "POST", f"/kiem-thu/du-an/{project_id}/danh-gia-chat-luong", headers=tester, expected=201, json={"idempotency_key": f"quality-{stamp}", "release_id": release["_id"], "build_id": build["_id"], "measurement_snapshot_refs": [metric["_id"]], "monitoring_snapshot_id": snapshot["_id"], "critical_risks": [{"risk": "Môi trường chưa ổn định"}], "evidence_refs": [snapshot["_id"]], "recommendation": "NO_GO", "rationale": "Gate không đạt và còn lỗi critical"})
    call(client, "GET", f"/kiem-thu/du-an/{project_id}/danh-gia-chat-luong", headers=viewer)
    call(client, "GET", f"/kiem-thu/danh-gia-chat-luong/{evaluation['_id']}", headers=viewer)
    assert any(item["criterion_id"] == "ENVIRONMENT-INCIDENT-GATE" for item in evaluation["exit_criteria_snapshot"])
    evaluation = call(client, "POST", f"/kiem-thu/danh-gia-chat-luong/{evaluation['_id']}/waiver", headers=tester, expected=201, json={"metric_or_criterion": "P1-GATE", "reason": "Ghi nhận quyết định rủi ro", "risk": "Có thể ảnh hưởng bản phát hành", "owner_id": "v5-p1-ba", "expiry": "2030-09-30T00:00:00Z", "evidence": [snapshot["_id"]]})
    waiver = evaluation["waivers"][0]
    evaluation = call(client, "POST", f"/kiem-thu/danh-gia-chat-luong/{evaluation['_id']}/waiver/{waiver['waiver_id']}/quyet-dinh", json={"expected_revision": evaluation["revision"], "decision": "APPROVE", "note": "Phê duyệt waiver có thời hạn"})
    evaluation = call(client, "POST", f"/kiem-thu/danh-gia-chat-luong/{evaluation['_id']}/gui-ra-soat", headers=tester, json={"expected_revision": evaluation["revision"], "note": "Gửi"})
    evaluation = call(client, "POST", f"/kiem-thu/danh-gia-chat-luong/{evaluation['_id']}/ra-soat", headers=ba, json={"expected_revision": evaluation["revision"], "decision": "ENDORSE", "note": "Đồng ý bằng chứng"})
    denied_quality = call(client, "POST", f"/kiem-thu/danh-gia-chat-luong/{evaluation['_id']}/phe-duyet", headers=tester, expected=403, json={"expected_revision": evaluation["revision"], "note": "Tester không được duyệt"})
    assert denied_quality["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    evaluation = call(client, "POST", f"/kiem-thu/danh-gia-chat-luong/{evaluation['_id']}/phe-duyet", json={"expected_revision": evaluation["revision"], "note": "Phê duyệt NO GO"})
    immutable_quality = call(client, "PATCH", f"/kiem-thu/danh-gia-chat-luong/{evaluation['_id']}", headers=tester, expected=409, json={"expected_revision": evaluation["revision"], "recommendation": "GO"})
    assert immutable_quality["error"]["code"] == "QUALITY_EVALUATION_IMMUTABLE"

    analysis = call(client, "POST", f"/kiem-thu/du-an/{project_id}/phan-tich-nguyen-nhan", headers=tester, expected=201, json={"idempotency_key": f"rca-{stamp}", "defect_ids": [defect["_id"]], "problem_statement": "Lỗi critical xảy ra", "evidence": [snapshot["_id"]], "root_causes": [], "contributing_factors": [], "five_whys": [], "owner_id": "v5-p1-developer"})
    call(client, "GET", f"/kiem-thu/du-an/{project_id}/phan-tich-nguyen-nhan", headers=viewer)
    hypotheses = call(client, "POST", f"/kiem-thu/phan-tich-nguyen-nhan/{analysis['_id']}/ai/goi-y", headers=developer, json={"idempotency_key": f"rca-ai-{stamp}", "instruction": "Phân tích bằng chứng lỗi"})
    assert hypotheses["candidate_only"] is True and hypotheses["human_confirmation_required"] is True
    assert hypotheses["status"] == "SUCCESS" and len(hypotheses["suggestions"]) >= 1
    assert hypotheses["suggestions"][0]["root_cause_category"] == "CONFIGURATION"
    analysis = call(client, "PATCH", f"/kiem-thu/phan-tich-nguyen-nhan/{analysis['_id']}", headers=developer, json={"expected_revision": analysis["revision"], "root_causes": [{"category": "CONFIGURATION", "detail": "Sai cấu hình môi trường"}], "five_whys": ["Cấu hình chưa được kiểm tra"]})
    analysis = call(client, "POST", f"/kiem-thu/phan-tich-nguyen-nhan/{analysis['_id']}/phe-duyet-nguyen-nhan", json={"expected_revision": analysis["revision"], "decision": "APPROVE", "note": "Xác nhận"})
    action = call(client, "POST", f"/kiem-thu/phan-tich-nguyen-nhan/{analysis['_id']}/hanh-dong", headers=developer, expected=201, json={"action_type": "PREVENTIVE", "title": "Kiểm tra cấu hình trước deploy", "description": "Thêm gate cấu hình", "owner_id": "v5-p1-developer", "due_at": "2030-09-30T00:00:00Z", "evidence_refs": []})
    for status in ["IN_PROGRESS", "IMPLEMENTED", "EFFECTIVENESS_REVIEW", "CLOSED"]:
        action = call(client, "PATCH", f"/kiem-thu/hanh-dong-phong-ngua/{action['_id']}", headers=developer, json={"expected_revision": action["revision"], "status": status, "result": "Đã kiểm chứng"})
    analysis = call(client, "GET", f"/kiem-thu/phan-tich-nguyen-nhan/{analysis['_id']}", headers=viewer)
    for status in ["IN_PROGRESS", "IMPLEMENTED", "EFFECTIVENESS_REVIEW"]:
        analysis = call(client, "POST", f"/kiem-thu/phan-tich-nguyen-nhan/{analysis['_id']}/trang-thai", headers=developer, json={"expected_revision": analysis["revision"], "status": status, "note": "Tiến hành"})
    analysis = call(client, "POST", f"/kiem-thu/phan-tich-nguyen-nhan/{analysis['_id']}/trang-thai", json={"expected_revision": analysis["revision"], "status": "CLOSED", "note": "Đóng"})
    assert analysis["status"] == "CLOSED"

    condition = call(client, "POST", f"/kiem-thu/du-an/{project_id}/dieu-kien-kiem-thu", headers=tester, expected=201, json={"title": "Điều kiện hiệu năng", "description_doc": doc("Đo p95"), "basis_refs": [{"artifact_type": "REQUIREMENT_VERSION", "artifact_id": requirement["_id"], "artifact_version_id": version_id}], "coverage_item": "p95", "test_level": "SYSTEM", "test_type": "PERFORMANCE", "risk": "HIGH", "priority": "HIGH"})
    nfr = call(client, "POST", f"/kiem-thu/du-an/{project_id}/ke-hoach-phi-chuc-nang", headers=tester, expected=201, json={"idempotency_key": f"nfr-{stamp}", "plan_type": "PERFORMANCE_TEST_PLAN", "name": "Kế hoạch hiệu năng", "objective": "Đo p95", "scope": ["API"], "approach": "Chạy công cụ ngoài", "entry_criteria": ["Môi trường sẵn sàng"], "exit_criteria": ["p95 dưới 500ms"], "test_condition_ids": [condition["_id"]], "test_case_version_ids": [], "requirement_version_ids": [version_id], "source_ai_result_ids": [], "tools": ["k6"]})
    call(client, "GET", f"/kiem-thu/du-an/{project_id}/ke-hoach-phi-chuc-nang", headers=viewer)
    nfr = call(client, "PATCH", f"/kiem-thu/ke-hoach-phi-chuc-nang/{nfr['_id']}", headers=tester, json={"expected_revision": nfr["revision"], "approach": "Chạy công cụ ngoài và nhập bằng chứng"})
    call(client, "GET", f"/kiem-thu/ke-hoach-phi-chuc-nang/{nfr['_id']}", headers=viewer)
    nfr = call(client, "POST", f"/kiem-thu/ke-hoach-phi-chuc-nang/{nfr['_id']}/gui-ra-soat", headers=tester, json={"expected_revision": nfr["revision"], "note": "Gửi"})
    nfr = call(client, "POST", f"/kiem-thu/ke-hoach-phi-chuc-nang/{nfr['_id']}/phe-duyet", json={"expected_revision": nfr["revision"], "note": "Duyệt"})
    evidence = call(client, "POST", f"/kiem-thu/ke-hoach-phi-chuc-nang/{nfr['_id']}/bang-chung-ben-ngoai", headers=tester, expected=201, json={"idempotency_key": f"nfr-evidence-{stamp}", "provider": "K6", "external_run_ref": "k6-run-1", "executed_at": "2026-09-11T00:00:00Z", "evidence_refs": ["evidence://k6-run-1"], "result_summary": {"p95_ms": 420, "passed": True}, "raw_result_hash": "a" * 64})
    assert evidence["provider"] == "K6"

    incident = call(client, "POST", f"/kiem-thu/incident-moi-truong/{incident['_id']}/dieu-tra", headers=tester, json={"expected_revision": incident["revision"], "status": "INVESTIGATING", "resolution": ""})
    incident = call(client, "POST", f"/kiem-thu/incident-moi-truong/{incident['_id']}/dieu-tra", headers=tester, json={"expected_revision": incident["revision"], "status": "RESOLVED", "resolution": "Khôi phục cấu hình"})
    denied_incident_close = call(client, "POST", f"/kiem-thu/incident-moi-truong/{incident['_id']}/ket-thuc", headers=tester, expected=403, json={"expected_revision": incident["revision"], "status": "CLOSED", "resolution": "Tester không được đóng"})
    assert denied_incident_close["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    incident = call(client, "POST", f"/kiem-thu/incident-moi-truong/{incident['_id']}/ket-thuc", json={"expected_revision": incident["revision"], "status": "CLOSED", "resolution": "Đã xác nhận ổn định"})
    restored_environment = call(client, "GET", f"/kiem-thu/moi-truong/{environment['_id']}", headers=viewer)
    restored_run = call(client, "GET", f"/kiem-thu/lan-chay-kiem-thu/{run['_id']}", headers=viewer)
    assert incident["downtime"] >= 0 and restored_environment["availability"] == "AVAILABLE" and restored_run["execution_paused"] is False

    maintenance_environment = call(client, "POST", f"/kiem-thu/du-an/{project_id}/moi-truong", expected=201, json={"name": f"Maintenance {stamp}", "environment_type": "staging", "availability": "MAINTENANCE"})
    maintenance_incident = call(client, "POST", f"/kiem-thu/du-an/{project_id}/incident-moi-truong", headers=tester, expected=201, json={"idempotency_key": f"maintenance-incident-{stamp}", "environment_id": maintenance_environment["_id"], "observed_at": "2026-09-11T00:00:00Z", "severity": "CRITICAL", "type": "CONFIGURATION", "description": "Gián đoạn trong cửa sổ bảo trì", "affected_run_ids": [], "evidence_refs": [], "owner_id": "v5-p1-tester"})
    maintenance_incident = call(client, "POST", f"/kiem-thu/incident-moi-truong/{maintenance_incident['_id']}/dieu-tra", headers=tester, json={"expected_revision": maintenance_incident["revision"], "status": "RESOLVED", "resolution": "Đã xử lý trong cửa sổ bảo trì"})
    maintenance_environment = call(client, "GET", f"/kiem-thu/moi-truong/{maintenance_environment['_id']}", headers=viewer)
    assert maintenance_environment["availability"] == "MAINTENANCE"

    openapi = client.get("/openapi.json").json()
    found = {function_id for path in openapi["paths"].values() for operation in path.values() if isinstance(operation, dict) for function_id in operation.get("x-function-ids", [])}
    for prefix, maximum in [("RVS", 8), ("MET", 7), ("PQE", 8), ("RCA", 8), ("ENVINC", 6)]:
        assert {f"{prefix}-{index:02d}" for index in range(1, maximum + 1)} <= found

print("V5 P1 integration passed")
