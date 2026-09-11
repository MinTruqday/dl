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
        "/kiem-thu/du-an",
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
        call(client, "POST", f"/kiem-thu/du-an/{project_id}/thanh-vien", expected=201, json={"user_id": user_id, "project_role": role})

    maintenance = call(
        client,
        "GET",
        f"/kiem-thu/du-an/{project_id}/phan-tich-bao-tri",
        headers=viewer,
    )
    assert set(maintenance) == {"impact_analysis_count", "tests_stale"}
    denied_ai_analytics = call(
        client,
        "GET",
        f"/kiem-thu/du-an/{project_id}/phan-tich-ai",
        headers=viewer,
        expected=403,
    )
    assert denied_ai_analytics["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    ai_analytics = call(
        client,
        "GET",
        f"/kiem-thu/du-an/{project_id}/phan-tich-ai",
        headers=ba,
    )
    assert {
        "proposal_acceptance_rate",
        "override_count",
        "average_latency_ms",
        "degraded_rate",
        "model_versions",
    } <= set(ai_analytics)
    assert call(client, "GET", f"/kiem-thu/du-an/{project_id}/bao-cao/thuc-thi", headers=viewer)["run_count"] == 0
    assert call(client, "GET", f"/kiem-thu/du-an/{project_id}/bao-cao/loi", headers=viewer)["defect_count"] == 0
    call(client, "GET", f"/kiem-thu/du-an/{project_id}/hoat-dong", headers=viewer)

    denied_settings = call(
        client,
        "PATCH",
        f"/kiem-thu/du-an/{project_id}",
        headers=tester,
        expected=403,
        json={"expected_revision": project["revision"], "settings": {"tester_can_create_run": True}},
    )
    assert denied_settings["error"]["code"] == "PROJECT_PERMISSION_DENIED"

    denied_knowledge_source = call(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/nguon-tri-thuc",
        headers=tester,
        expected=403,
        json={"title": "Nguồn bị từ chối", "content": "Không được tạo mặc định"},
    )
    assert denied_knowledge_source["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    teacher_source = call(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/nguon-tri-thuc",
        headers=ba,
        expected=201,
        json={
            "title": "Tài liệu phương pháp của giáo viên",
            "content": "Giáo viên hướng dẫn kiểm tra biên và dữ liệu không hợp lệ",
            "source_type": "BRD",
            "authority": "APPROVED_SOURCE",
            "owner_id": "catalog-ba-v43",
            "module": "Xác thực",
            "component": "Đăng nhập",
            "product_area": "Quản lý tài khoản",
            "approval_status": "APPROVED",
            "approved_by": "catalog-ba-v43",
            "approved_at": "2026-09-01T00:00:00Z",
            "source_version": "1.0",
            "tags": ["phuong-phap", "bien"],
        },
    )
    textbook_source = call(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/nguon-tri-thuc",
        headers=ba,
        expected=201,
        json={
            "title": "Sách giáo khoa chính thức",
            "content": "Sách giáo khoa hướng dẫn kiểm tra biên và dữ liệu không hợp lệ",
            "source_type": "SRS",
            "authority": "CONTROLLED_SOURCE",
            "module": "Xác thực",
            "component": "Đăng nhập",
            "product_area": "Quản lý tài khoản",
            "approval_status": "DRAFT",
            "source_version": "1.0",
        },
    )
    sources = call(client, "GET", f"/kiem-thu/du-an/{project_id}/nguon-tri-thuc", headers=viewer)
    assert [item["_id"] for item in sources[:2]] == [teacher_source["_id"], textbook_source["_id"]]
    search = call(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/tri-thuc/tim-kiem",
        headers=viewer,
        json={"query": "kiểm tra biên", "artifact_types": ["requirement_document"], "limit": 10},
    )
    assert search["items"][0]["authority"] == "APPROVED_SOURCE"
    archived_source = call(
        client,
        "POST",
        f"/kiem-thu/nguon-tri-thuc/{teacher_source['_id']}/luu-tru",
        headers=ba,
        json={"expected_revision": teacher_source["revision"], "reason": "Nguồn đã được thay thế"},
    )
    assert archived_source["status"] == "ARCHIVED"

    attachment = call(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/tep-dinh-kem",
        headers=ba,
        expected=201,
        json={"filename": "teacher-note.txt", "url": "teacher/teacher-note.txt", "size": 42, "content_type": "text/plain"},
    )
    call(client, "GET", f"/kiem-thu/du-an/{project_id}/tep-dinh-kem", headers=viewer)
    denied_attachment_delete = call(
        client,
        "DELETE",
        f"/kiem-thu/tep-dinh-kem/{attachment['_id']}",
        headers=viewer,
        expected=403,
    )
    assert denied_attachment_delete["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    deleted_attachment = call(
        client,
        "DELETE",
        f"/kiem-thu/tep-dinh-kem/{attachment['_id']}",
        headers=ba,
    )
    assert deleted_attachment["deleted"] is True
    moderated_attachment = call(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/tep-dinh-kem",
        headers=ba,
        expected=201,
        json={"filename": "moderated-note.txt", "url": "teacher/kiem-duyetd-note.txt", "size": 21, "content_type": "text/plain"},
    )
    moderated = call(
        client,
        "POST",
        f"/kiem-thu/tep-dinh-kem/{moderated_attachment['_id']}/kiem-duyet",
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
                f"/kiem-thu/du-an/{project_id}/yeu-cau",
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
        f"/kiem-thu/yeu-cau/{first['_id']}/phu-thuoc",
        headers=viewer,
        expected=403,
        json={"dependency_requirement_id": second["_id"], "expected_revision": 1},
    )
    assert denied_dependency["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    first_version = call(
        client,
        "POST",
        f"/kiem-thu/yeu-cau/{first['_id']}/phu-thuoc",
        headers=ba,
        json={"dependency_requirement_id": second["_id"], "expected_revision": 1},
    )
    assert second["_id"] in first_version["dependencies"]
    call(
        client,
        "POST",
        f"/kiem-thu/yeu-cau/{second['_id']}/phu-thuoc",
        headers=ba,
        json={"dependency_requirement_id": third["_id"], "expected_revision": 1},
    )
    cycle = call(
        client,
        "POST",
        f"/kiem-thu/yeu-cau/{third['_id']}/phu-thuoc",
        headers=ba,
        expected=422,
        json={"dependency_requirement_id": first["_id"], "expected_revision": 1},
    )
    assert cycle["error"]["code"] == "REQUIREMENT_DEPENDENCY_CYCLE"
    removed = call(
        client,
        "DELETE",
        f"/kiem-thu/yeu-cau/{first['_id']}/phu-thuoc/{second['_id']}?expected_revision=2",
        headers=ba,
    )
    assert second["_id"] not in removed["dependencies"]

    restorable = call(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/yeu-cau",
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
        f"/kiem-thu/yeu-cau/{restorable['_id']}/ngung-hieu-luc",
        json={"expected_current_version_id": restorable["current_version"]["_id"], "reason": "Kiểm tra trạng thái lưu trữ"},
    )
    assert restorable["status"] == "OBSOLETE"
    denied_restore = call(
        client,
        "POST",
        f"/kiem-thu/yeu-cau/{restorable['_id']}/khoi-phuc",
        headers=ba,
        expected=403,
        json={"expected_current_version_id": restorable["current_version"]["_id"], "reason": "BA chưa được policy cấp quyền"},
    )
    assert denied_restore["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    restored = call(
        client,
        "POST",
        f"/kiem-thu/yeu-cau/{restorable['_id']}/khoi-phuc",
        json={"expected_current_version_id": restorable["current_version"]["_id"], "reason": "Khôi phục sau khi kiểm chứng"},
    )
    assert restored["status"] == "DRAFT" and restored["current_version"]["status"] == "DRAFT"

    strategy_payload = {
        "key": "STR_CATALOG",
        "name": "Chiến lược kiểm thử catalog",
        "objective": "Kiểm chứng đầy đủ vòng đời kiểm thử",
        "test_levels": ["SYSTEM"],
        "test_types": ["FUNCTIONAL"],
        "approach": "Kiểm thử dựa trên rủi ro và test basis đã baseline",
        "risk_model": {
            "probability_scale": [{"value": 1, "label": "Thấp"}, {"value": 2, "label": "Cao"}],
            "impact_scale": [{"value": 1, "label": "Thấp"}, {"value": 2, "label": "Cao"}],
            "risk_exposure_formula": "probability * impact",
            "thresholds": [{"level": "HIGH", "min": 3}],
        },
        "reviewer_ids": ["catalog-tester-v43"],
    }
    strategy = call(client, "POST", f"/kiem-thu/du-an/{project_id}/chien-luoc", expected=201, json=strategy_payload)
    call(client, "GET", f"/kiem-thu/du-an/{project_id}/chien-luoc", headers=viewer)
    call(client, "GET", f"/kiem-thu/chien-luoc/{strategy['_id']}", headers=viewer)
    strategy = call(client, "PATCH", f"/kiem-thu/chien-luoc/{strategy['_id']}", headers=tester, json={"expected_revision": strategy["revision"], "approach": "Kiểm thử dựa trên rủi ro và bằng chứng đã kiểm soát"})
    strategy = call(client, "POST", f"/kiem-thu/chien-luoc/{strategy['_id']}/gui-ra-soat", headers=tester, json={"expected_revision": strategy["revision"], "note": "Gửi rà soát"})
    strategy = call(client, "POST", f"/kiem-thu/chien-luoc/{strategy['_id']}/yeu-cau-chinh-sua", headers=tester, json={"expected_revision": strategy["revision"], "note": "Bổ sung bằng chứng"})
    strategy = call(client, "POST", f"/kiem-thu/chien-luoc/{strategy['_id']}/gui-ra-soat", headers=tester, json={"expected_revision": strategy["revision"], "note": "Gửi lại"})
    strategy = call(client, "POST", f"/kiem-thu/chien-luoc/{strategy['_id']}/phe-duyet", json={"expected_revision": strategy["revision"], "note": "Phê duyệt"})
    strategy_version = call(client, "POST", f"/kiem-thu/chien-luoc/{strategy['_id']}/tao-phien-ban", expected=201, json={"expected_revision": strategy["revision"], "change_reason": "Chuẩn bị phiên bản kế tiếp"})
    strategy_version = call(client, "POST", f"/kiem-thu/chien-luoc/{strategy_version['_id']}/luu-tru", json={"expected_revision": strategy_version["revision"], "note": "Chưa áp dụng"})
    assert strategy_version["status"] == "ARCHIVED"

    condition_payload = {
        "title": "Đăng nhập theo requirement đã baseline",
        "description_doc": doc("Kiểm tra hành vi đăng nhập theo test basis"),
        "basis_refs": [{"artifact_type": "REQUIREMENT_VERSION", "artifact_id": first["_id"], "artifact_version_id": first["current_version"]["_id"]}],
        "coverage_item": "Hành vi xác thực",
        "test_level": "SYSTEM",
        "test_type": "FUNCTIONAL",
        "risk": "HIGH",
        "priority": "HIGH",
        "analysis_findings": [{"finding_id": "FIND-1", "finding_type": "AMBIGUITY", "severity": "LOW", "source_ref": {"artifact_type": "REQUIREMENT_VERSION", "artifact_id": first["_id"], "artifact_version_id": first["current_version"]["_id"]}, "description": "Cần làm rõ dữ liệu biên"}],
    }
    condition = call(client, "POST", f"/kiem-thu/du-an/{project_id}/dieu-kien-kiem-thu", headers=tester, expected=201, json=condition_payload)
    call(client, "GET", f"/kiem-thu/du-an/{project_id}/dieu-kien-kiem-thu", headers=viewer)
    call(client, "GET", f"/kiem-thu/dieu-kien-kiem-thu/{condition['_id']}", headers=viewer)
    condition = call(client, "PATCH", f"/kiem-thu/dieu-kien-kiem-thu/{condition['_id']}", headers=tester, json={"expected_revision": condition["revision"], "coverage_item": "Hành vi xác thực thành công và thất bại"})
    condition = call(client, "POST", f"/kiem-thu/dieu-kien-kiem-thu/{condition['_id']}/ket-qua/FIND-1/giai-quyet", headers=tester, json={"expected_revision": condition["revision"], "status": "RESOLVED", "resolution_ref": first["current_version"]["_id"], "note": "Đã xác minh test basis"})
    condition = call(client, "POST", f"/kiem-thu/dieu-kien-kiem-thu/{condition['_id']}/gui-ra-soat", headers=tester, json={"expected_revision": condition["revision"], "note": "Gửi rà soát"})
    condition = call(client, "POST", f"/kiem-thu/dieu-kien-kiem-thu/{condition['_id']}/phe-duyet", json={"expected_revision": condition["revision"], "note": "Phê duyệt"})
    call(client, "GET", f"/kiem-thu/du-an/{project_id}/phan-tich-kiem-thu/truy-vet", headers=viewer)
    call(client, "POST", f"/kiem-thu/du-an/{project_id}/phan-tich-kiem-thu/ai", headers=tester, expected=201, json={"basis_refs": condition_payload["basis_refs"], "instruction": "Đề xuất condition từ test basis", "idempotency_key": f"analysis-{stamp}"})
    archived_condition = call(client, "POST", f"/kiem-thu/dieu-kien-kiem-thu/{condition['_id']}/luu-tru", json={"expected_revision": condition["revision"], "note": "Hoàn tất kiểm tra vòng đời"})
    assert archived_condition["status"] == "ARCHIVED"

    release = call(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ban-phat-hanh",
        headers=tester,
        expected=201,
        json={"key": f"REL-{stamp}", "name": "Bản phát hành báo cáo", "version": "1.0"},
    )
    build = call(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ban-dung",
        headers=tester,
        expected=201,
        json={"identifier": f"BUILD-{stamp}", "version": "1.0.0", "release_id": release["_id"], "idempotency_key": f"build-{stamp}"},
    )
    plan = call(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ke-hoach-kiem-thu",
        headers=tester,
        expected=201,
        json={"project_id": project_id, "name": "Kế hoạch V4.3", "strategy_version_id": strategy["_id"], "release_id": release["_id"], "build_id": build["_id"], "quality_targets": [{"criterion_id": "EXIT-1", "criterion": "Không có blocker", "type": "OPEN_BLOCKER_MAX", "threshold": 0}, {"criterion_id": "EXIT-2", "criterion": "Xác nhận nghiệp vụ", "type": "CUSTOM_MANUAL_GATE", "threshold": False}]},
    )
    cloned_plan = call(client, "POST", f"/kiem-thu/ke-hoach-kiem-thu/{plan['_id']}/nhan-ban", headers=tester, expected=201)
    assert cloned_plan["_id"] != plan["_id"] and cloned_plan["status"] == "DRAFT"
    call(client, "POST", f"/kiem-thu/ke-hoach-kiem-thu/{plan['_id']}/phe-duyet", headers=tester, expected=403, json={"expected_revision": 1, "review_note": "Không được duyệt"})
    plan = call(client, "POST", f"/kiem-thu/ke-hoach-kiem-thu/{plan['_id']}/phe-duyet", json={"expected_revision": plan["revision"], "review_note": "Phê duyệt để giám sát"})
    completion_critical_defect = call(client, "POST", f"/kiem-thu/du-an/{project_id}/loi", headers=tester, expected=201, json={"project_id": project_id, "title": "Lỗi nghiêm trọng tại thời điểm hoàn tất", "severity": "critical", "priority": "critical", "release_id": release["_id"], "build_id": build["_id"], "assignee": "catalog-tester-v43"})
    call(client, "GET", f"/kiem-thu/du-an/{project_id}/giam-sat-kiem-thu", headers=viewer)
    snapshot = call(client, "POST", f"/kiem-thu/du-an/{project_id}/giam-sat-kiem-thu/snapshot", expected=201, json={"test_plan_id": plan["_id"], "actual_effort": 4, "risks": [], "blockers": []})
    snapshot = call(client, "GET", f"/kiem-thu/giam-sat-kiem-thu/snapshot/{snapshot['_id']}", headers=viewer)
    snapshot = call(client, "POST", f"/kiem-thu/giam-sat-kiem-thu/snapshot/{snapshot['_id']}/ghi-de-tieu-chi", json={"expected_revision": snapshot["revision"], "criterion_id": "EXIT-2", "status": "PASS", "reason": "Product Owner đã xác nhận", "evidence_refs": [plan["_id"]]})
    assert snapshot["effective_quality_gate_status"] == "PASS"
    action = call(client, "POST", f"/kiem-thu/du-an/{project_id}/hanh-dong-dieu-khien", headers=tester, expected=201, json={"snapshot_id": snapshot["_id"], "type": "REQUEST_RETEST", "title": "Kiểm thử lại phạm vi ưu tiên", "owner_id": "catalog-tester-v43", "due_at": "2030-09-30T12:00:00Z", "priority": "HIGH", "decision_reason": "Xác nhận control action", "evidence_refs": [snapshot["_id"]]})
    call(client, "GET", f"/kiem-thu/du-an/{project_id}/hanh-dong-dieu-khien", headers=viewer)
    action = call(client, "PATCH", f"/kiem-thu/hanh-dong-dieu-khien/{action['_id']}", headers=tester, json={"expected_revision": action["revision"], "status": "IN_PROGRESS"})
    assert action["status"] == "IN_PROGRESS"

    call(client, "GET", f"/kiem-thu/du-an/{project_id}/bao-cao-trang-thai", headers=viewer)
    denied_status_report = call(client, "POST", f"/kiem-thu/du-an/{project_id}/bao-cao-trang-thai/tao-tu-snapshot", headers=viewer, expected=403, json={"snapshot_id": snapshot["_id"], "build_id": build["_id"], "reporting_period": {"start_at": "2026-09-01T00:00:00Z", "end_at": "2026-09-07T23:59:59Z"}})
    assert denied_status_report["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    status_report = call(client, "POST", f"/kiem-thu/du-an/{project_id}/bao-cao-trang-thai/tao-tu-snapshot", headers=tester, expected=201, json={"snapshot_id": snapshot["_id"], "build_id": build["_id"], "reporting_period": {"start_at": "2026-09-01T00:00:00Z", "end_at": "2026-09-07T23:59:59Z"}, "executive_summary": "Báo cáo trạng thái tuần", "forecast": "Hoàn tất theo kế hoạch", "distribution": ["qa-lead@test.local"], "evidence_refs": [snapshot["_id"]]})
    call(client, "GET", f"/kiem-thu/bao-cao-trang-thai/{status_report['_id']}", headers=viewer)
    status_report = call(client, "PATCH", f"/kiem-thu/bao-cao-trang-thai/{status_report['_id']}", headers=tester, json={"expected_revision": status_report["revision"], "progress_summary": "Đã kiểm chứng tiến độ từ snapshot", "recommendation": "ON_TRACK"})
    status_report = call(client, "POST", f"/kiem-thu/bao-cao-trang-thai/{status_report['_id']}/bang-chung", headers=tester, json={"expected_revision": status_report["revision"], "evidence_refs": [plan["_id"]]})
    status_report = call(client, "POST", f"/kiem-thu/bao-cao-trang-thai/{status_report['_id']}/gui-ra-soat", headers=tester, json={"expected_revision": status_report["revision"], "note": "Gửi báo cáo rà soát"})
    status_report = call(client, "POST", f"/kiem-thu/bao-cao-trang-thai/{status_report['_id']}/yeu-cau-chinh-sua", json={"expected_revision": status_report["revision"], "note": "Bổ sung nhận định điều hành"})
    status_report = call(client, "PATCH", f"/kiem-thu/bao-cao-trang-thai/{status_report['_id']}", headers=tester, json={"expected_revision": status_report["revision"], "executive_summary": "Báo cáo trạng thái đã hoàn thiện"})
    status_report = call(client, "POST", f"/kiem-thu/bao-cao-trang-thai/{status_report['_id']}/gui-ra-soat", headers=tester, json={"expected_revision": status_report["revision"], "note": "Gửi lại"})
    denied_status_approval = call(client, "POST", f"/kiem-thu/bao-cao-trang-thai/{status_report['_id']}/phe-duyet", headers=tester, expected=403, json={"expected_revision": status_report["revision"], "note": "Tester không được duyệt"})
    assert denied_status_approval["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    status_report = call(client, "POST", f"/kiem-thu/bao-cao-trang-thai/{status_report['_id']}/phe-duyet", json={"expected_revision": status_report["revision"], "note": "Phê duyệt báo cáo"})
    approved_hash = status_report["approved_snapshot_hash"]
    immutable_status_report = call(client, "PATCH", f"/kiem-thu/bao-cao-trang-thai/{status_report['_id']}", headers=tester, expected=409, json={"expected_revision": status_report["revision"], "forecast": "Không được sửa"})
    assert immutable_status_report["error"]["code"] == "STATUS_REPORT_IMMUTABLE"
    status_report = call(client, "POST", f"/kiem-thu/bao-cao-trang-thai/{status_report['_id']}/phat-hanh", json={"expected_revision": status_report["revision"], "note": "Phát hành báo cáo"})
    assert status_report["status"] == "PUBLISHED" and status_report["approved_snapshot_hash"] == approved_hash
    second_status_report = call(client, "POST", f"/kiem-thu/du-an/{project_id}/bao-cao-trang-thai/tao-tu-snapshot", headers=tester, expected=201, json={"snapshot_id": snapshot["_id"], "build_id": build["_id"], "reporting_period": {"start_at": "2026-09-08T00:00:00Z", "end_at": "2026-09-14T23:59:59Z"}, "executive_summary": "Báo cáo kỳ tiếp theo", "forecast": "Tiếp tục thực thi"})
    comparison = call(client, "GET", f"/kiem-thu/bao-cao-trang-thai/{status_report['_id']}/so-sanh?other_report_id={second_status_report['_id']}", headers=viewer)
    assert comparison["changes"] and second_status_report["sequence"] == status_report["sequence"] + 1
    for export_format, content_type in [("pdf", "application/pdf"), ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"), ("csv", "text/csv")]:
        exported = client.get(f"/kiem-thu/bao-cao-trang-thai/{status_report['_id']}/xuat?format={export_format}", headers=tester)
        assert exported.status_code == 200 and content_type in exported.headers["content-type"] and exported.content

    call(client, "GET", f"/kiem-thu/du-an/{project_id}/hoan-tat-kiem-thu", headers=viewer)
    denied_completion = call(client, "POST", f"/kiem-thu/du-an/{project_id}/hoan-tat-kiem-thu", headers=viewer, expected=403, json={"snapshot_id": snapshot["_id"], "build_id": build["_id"]})
    assert denied_completion["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    completion_idempotency_key = f"completion-{stamp}"
    completion = call(client, "POST", f"/kiem-thu/du-an/{project_id}/hoan-tat-kiem-thu", headers=tester, expected=201, json={"idempotency_key": completion_idempotency_key, "snapshot_id": snapshot["_id"], "build_id": build["_id"], "residual_risks": [{"risk_id": "RISK-COMP-1", "title": "Rủi ro tương thích trình duyệt cũ", "severity": "MEDIUM", "owner_id": "catalog-tester-v43"}], "lessons_learned": [{"category": "WORKED", "text": "Rà soát test basis sớm giúp giảm sai lệch"}], "improvement_actions": [{"action_id": "ACTION-COMP-1", "title": "Tăng độ phủ trình duyệt", "owner_id": "catalog-tester-v43", "status": "OPEN", "evidence_refs": [snapshot["_id"]]}]})
    replayed_completion = call(client, "POST", f"/kiem-thu/du-an/{project_id}/hoan-tat-kiem-thu", headers=tester, expected=201, json={"idempotency_key": completion_idempotency_key, "snapshot_id": snapshot["_id"], "build_id": build["_id"]})
    assert replayed_completion["_id"] == completion["_id"] and replayed_completion["revision"] == completion["revision"]
    assert completion["test_plan_id"] == plan["_id"]
    assert completion["release_id"] == release["_id"]
    assert completion["build_id"] == build["_id"]
    assert completion["strategy_version_id"] == strategy["_id"]
    assert completion["monitoring_snapshot_id"] == snapshot["_id"]
    assert completion["scope_snapshot"]["plan_snapshot_hash"] == plan["approved_snapshot_hash"]
    assert completion["exit_criteria_evaluation"][1]["overridden"] is True
    assert any(item.get("defect_id") == completion_critical_defect["_id"] and item.get("severity") == "critical" for item in completion["unresolved_items"])
    completion = call(client, "PATCH", f"/kiem-thu/hoan-tat-kiem-thu/{completion['_id']}", headers=tester, json={"expected_revision": completion["revision"], "recommendation": "NOT_READY"})
    completion = call(client, "POST", f"/kiem-thu/hoan-tat-kiem-thu/{completion['_id']}/rui-ro/RISK-COMP-1/xu-ly", headers=ba, json={"expected_revision": completion["revision"], "acceptance": "ACCEPTED", "reason": "Phạm vi trình duyệt này không thuộc bản phát hành"})
    assert completion["residual_risks"][0]["accepted_by"] == "catalog-ba-v43"
    project = call(client, "PATCH", f"/kiem-thu/du-an/{project_id}", json={"expected_revision": project["revision"], "settings": {"require_completion_report_before_release_close": True}})
    release = call(client, "POST", f"/kiem-thu/ban-phat-hanh/{release['_id']}/kich-hoat", headers=tester, json={"expected_revision": release["revision"], "reason": "Bắt đầu bản phát hành"})
    blocked_release_close = call(client, "POST", f"/kiem-thu/ban-phat-hanh/{release['_id']}/dong", headers=tester, expected=409, json={"expected_revision": release["revision"], "reason": "Chưa có báo cáo được duyệt"})
    assert blocked_release_close["error"]["code"] == "COMPLETION_REPORT_REQUIRED"
    completion = call(client, "POST", f"/kiem-thu/hoan-tat-kiem-thu/{completion['_id']}/gui-ra-soat", headers=tester, json={"expected_revision": completion["revision"], "note": "Gửi báo cáo hoàn tất"})
    completion = call(client, "POST", f"/kiem-thu/hoan-tat-kiem-thu/{completion['_id']}/yeu-cau-chinh-sua", headers=ba, json={"expected_revision": completion["revision"], "note": "Bổ sung bài học kinh nghiệm"})
    completion = call(client, "PATCH", f"/kiem-thu/hoan-tat-kiem-thu/{completion['_id']}", headers=tester, json={"expected_revision": completion["revision"], "lessons_learned": [*completion["lessons_learned"], {"category": "IMPROVEMENT", "text": "Chuẩn hóa checklist trước khi bắt đầu"}]})
    completion = call(client, "POST", f"/kiem-thu/hoan-tat-kiem-thu/{completion['_id']}/gui-ra-soat", headers=tester, json={"expected_revision": completion["revision"], "note": "Gửi lại báo cáo hoàn tất"})
    completion = call(client, "POST", f"/kiem-thu/hoan-tat-kiem-thu/{completion['_id']}/ky-xac-nhan", headers=tester, json={"expected_revision": completion["revision"], "decision": "APPROVE", "note": "Đã kiểm tra bằng chứng thực thi"})
    completion = call(client, "POST", f"/kiem-thu/hoan-tat-kiem-thu/{completion['_id']}/ky-xac-nhan", json={"expected_revision": completion["revision"], "decision": "APPROVE", "note": "QA Lead xác nhận nội dung hoàn tất"})
    denied_completion_approval = call(client, "POST", f"/kiem-thu/hoan-tat-kiem-thu/{completion['_id']}/phe-duyet", headers=tester, expected=403, json={"expected_revision": completion["revision"], "note": "Tester không được duyệt"})
    assert denied_completion_approval["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    completion = call(client, "POST", f"/kiem-thu/hoan-tat-kiem-thu/{completion['_id']}/phe-duyet", json={"expected_revision": completion["revision"], "note": "Phê duyệt báo cáo hoàn tất"})
    completion_hash = completion["approved_snapshot_hash"]
    immutable_completion = call(client, "PATCH", f"/kiem-thu/hoan-tat-kiem-thu/{completion['_id']}", headers=tester, expected=409, json={"expected_revision": completion["revision"], "recommendation": "READY_FOR_RELEASE"})
    assert immutable_completion["error"]["code"] == "COMPLETION_REPORT_IMMUTABLE"
    release = call(client, "POST", f"/kiem-thu/ban-phat-hanh/{release['_id']}/dong", headers=tester, json={"expected_revision": release["revision"], "reason": "Báo cáo hoàn tất đã được phê duyệt"})
    completion = call(client, "POST", f"/kiem-thu/hoan-tat-kiem-thu/{completion['_id']}/dong", json={"expected_revision": completion["revision"], "note": "Đóng quy trình kiểm thử"})
    assert completion["status"] == "CLOSED" and completion["approved_snapshot_hash"] == completion_hash

    scenario = call(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/kich-ban-kiem-thu",
        headers=tester,
        expected=201,
        json={"title": "Kịch bản V4.3", "objective": "Kiểm tra catalog", "requirement_version_ids": [first["current_version"]["_id"]]},
    )
    scenario_detail = call(client, "GET", f"/kiem-thu/kich-ban-kiem-thu/{scenario['_id']}", headers=viewer)
    assert scenario_detail["_id"] == scenario["_id"]

    draft = call(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ban-nhap-ca-kiem-thu",
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
    reviewed_draft = call(client, "POST", f"/kiem-thu/du-an/{project_id}/ca-kiem-thu/{draft['_id']}/gui-ra-soat", json={"expected_revision": 1, "review_note": "Gửi duyệt"})
    suite = call(
        client,
        "POST",
        "/kiem-thu/bo-kiem-thu",
        expected=201,
        json={"project_id": project_id, "name": "Suite kiểm tra quyền bulk", "suite_type": "custom", "test_case_version_ids": []},
    )
    bulk_result = call(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/hang-loat/ca-kiem-thu/them-vao-bo-kiem-thu",
        headers=tester,
        json={"suite_id": suite["_id"], "test_case_ids": [draft["_id"]], "expected_revision": 1},
    )
    assert bulk_result["failed"] == [{"id": draft["_id"], "code": "ENTITY_NOT_FOUND"}]
    denied_changes = call(client, "POST", f"/kiem-thu/du-an/{project_id}/ca-kiem-thu/{draft['_id']}/yeu-cau-chinh-sua", headers=tester, expected=403, json={"expected_revision": reviewed_draft["revision"], "review_note": "Yêu cầu sửa"})
    assert denied_changes["error"]["code"] == "PROJECT_ACTION_POLICY_DENIED"

    denied_question = call(client, "POST", f"/kiem-thu/du-an/{project_id}/ai/hoi-dap", headers=viewer, expected=403, json={"question": "Yêu cầu nào đang tồn tại", "artifact_types": ["not_available"]})
    assert denied_question["error"]["code"] == "PROJECT_PERMISSION_DENIED"
    denied_plan_assignment = call(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ke-hoach-kiem-thu",
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
        f"/kiem-thu/du-an/{project_id}",
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
        f"/kiem-thu/du-an/{project_id}/ke-hoach-kiem-thu",
        headers=tester,
        expected=201,
        json={
            "project_id": project_id,
            "name": "Kế hoạch phân công theo policy",
            "members": ["catalog-tester-v43"],
        },
    )
    assert assigned_plan["members"] == ["catalog-tester-v43"]
    changed_draft = call(client, "POST", f"/kiem-thu/du-an/{project_id}/ca-kiem-thu/{draft['_id']}/yeu-cau-chinh-sua", headers=tester, json={"expected_revision": reviewed_draft["revision"], "review_note": "Yêu cầu sửa theo policy"})
    assert changed_draft["status"] == "DRAFT"
    answer = call(client, "POST", f"/kiem-thu/du-an/{project_id}/ai/hoi-dap", headers=viewer, json={"question": "Yêu cầu nào đang tồn tại", "artifact_types": ["not_available"]})
    assert answer["confidence"] == 0 and answer["evidence"] == []

    defect = call(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/loi",
        expected=201,
        json={"project_id": project_id, "title": "Lỗi được giao cho developer", "assignee": "catalog-developer-v43"},
    )
    viewer_export = client.get(
        f"/kiem-thu/du-an/{project_id}/loi/xuat", headers=viewer
    )
    assert viewer_export.status_code == 403, viewer_export.text
    ba_export = client.get(f"/kiem-thu/du-an/{project_id}/loi/xuat", headers=ba)
    assert ba_export.status_code == 200, ba_export.text
    assert "defect_key,title,severity" in ba_export.text
    defect = call(client, "POST", f"/kiem-thu/loi/{defect['_id']}/chuyen-trang-thai", json={"expected_revision": defect["revision"], "to_status": "CONFIRMED", "reason": "Xác nhận lỗi"})
    call(client, "POST", f"/kiem-thu/loi/{defect['_id']}/chuyen-trang-thai", headers=other_developer, expected=403, json={"expected_revision": defect["revision"], "to_status": "IN_PROGRESS", "reason": "Không được nhận lỗi của người khác"})
    defect = call(client, "POST", f"/kiem-thu/loi/{defect['_id']}/chuyen-trang-thai", headers=developer, json={"expected_revision": defect["revision"], "to_status": "IN_PROGRESS", "reason": "Bắt đầu xử lý"})
    assert defect["status"] == "IN_PROGRESS"

    rejected_defect = call(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/loi",
        headers=tester,
        expected=201,
        json={"project_id": project_id, "title": "Lỗi cần từ chối theo policy"},
    )
    rejected_defect = call(client, "POST", f"/kiem-thu/loi/{rejected_defect['_id']}/chuyen-trang-thai", headers=tester, json={"expected_revision": rejected_defect["revision"], "to_status": "REJECTED", "reason": "Không tái hiện được"})
    assert rejected_defect["status"] == "REJECTED"

    run = call(client, "POST", f"/kiem-thu/du-an/{project_id}/lan-chay-kiem-thu", expected=201, json={"project_id": project_id, "name": "Run catalog V4.3"})
    run = call(client, "PATCH", f"/kiem-thu/du-an/{project_id}/lan-chay-kiem-thu/{run['_id']}", json={"expected_revision": run["revision"], "build": "v4.3"})
    assigned = call(client, "POST", f"/kiem-thu/du-an/{project_id}/lan-chay-kiem-thu/{run['_id']}/phan-cong", json={"expected_revision": run["revision"], "assignee_id": "catalog-tester-v43", "test_case_assignments": {}})
    assert assigned["assignee_id"] == "catalog-tester-v43"

    archived_project = call(client, "POST", f"/kiem-thu/du-an/{project_id}/luu-tru", json={"expected_revision": project["revision"], "reason": "Xác minh lưu giữ bài học hoàn tất"})
    assert archived_project["status"] == "archived"
    retained_completion = call(client, "GET", f"/kiem-thu/hoan-tat-kiem-thu/{completion['_id']}", headers=viewer)
    assert retained_completion["lessons_learned"] == completion["lessons_learned"]

print("V4.3 role catalog integration passed")
