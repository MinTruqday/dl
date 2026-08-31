import os
import time

import httpx
import jwt


base_url = os.getenv("TESTING_TEST_URL", "http://testing:8000")
lead = {
    "Authorization": "Bearer "
    + jwt.encode(
        {"uid": "planning-lead-v42", "sub": "planning-lead-v42@test.local", "system_role": "USER"},
        os.environ["SECRET_KEY"],
        algorithm="HS256",
    )
}


with httpx.Client(base_url=base_url, timeout=30) as client:
    stamp = int(time.time() * 1000)
    created = client.post(
        "/kiem-thu/du-an",
        headers=lead,
        json={
            "key": f"PLN{stamp}",
            "name": "V4.2 Test Planning",
            "description": "Test plan and suite lifecycle",
            "project_type": "web",
            "settings": {},
        },
    )
    assert created.status_code == 201, created.text
    project_id = created.json()["data"]["_id"]

    scenario = client.post(
        f"/kiem-thu/du-an/{project_id}/kich-ban-kiem-thu",
        headers=lead,
        json={
            "title": "Đăng nhập thành công",
            "objective": "Xác nhận người dùng hợp lệ truy cập được hệ thống",
            "category": "happy_path",
        },
    )
    assert scenario.status_code == 201, scenario.text
    scenario_value = scenario.json()["data"]
    scenario_id = scenario_value["_id"]
    scenario_clone = client.post(
        f"/kiem-thu/kich-ban-kiem-thu/{scenario_id}/nhan-ban",
        headers=lead,
    )
    assert scenario_clone.status_code == 201, scenario_clone.text
    assert scenario_clone.json()["data"]["_id"] != scenario_id
    scenario_archive = client.post(
        f"/kiem-thu/kich-ban-kiem-thu/{scenario_id}/luu-tru",
        headers=lead,
        json={"expected_revision": 1, "reason": "Thay thế bằng kịch bản mới"},
    )
    assert scenario_archive.status_code == 200, scenario_archive.text
    assert scenario_archive.json()["data"]["status"] == "archived"

    plan = client.post(
        f"/kiem-thu/du-an/{project_id}/ke-hoach-kiem-thu",
        headers=lead,
        json={
            "project_id": project_id,
            "name": "Kế hoạch kiểm thử bản phát hành",
            "objective": "Xác nhận luồng nghiệp vụ chính",
            "release": "4.2",
            "build": "v42",
        },
    )
    assert plan.status_code == 201, plan.text
    plan_value = plan.json()["data"]
    plan_id = plan_value["_id"]
    updated = client.patch(
        f"/kiem-thu/ke-hoach-kiem-thu/{plan_id}",
        headers=lead,
        json={
            "expected_revision": 1,
            "objective": "Xác nhận đầy đủ luồng nghiệp vụ và phi chức năng",
            "entry_criteria": ["Bản dựng sẵn sàng"],
            "exit_criteria": ["Không còn lỗi nghiêm trọng"],
        },
    )
    assert updated.status_code == 200, updated.text
    submitted = client.post(
        f"/kiem-thu/ke-hoach-kiem-thu/{plan_id}/gui-ra-soat",
        headers=lead,
        json={"expected_revision": 2, "review_note": "Sẵn sàng rà soát"},
    )
    assert submitted.status_code == 200, submitted.text
    approved = client.post(
        f"/kiem-thu/ke-hoach-kiem-thu/{plan_id}/phe-duyet",
        headers=lead,
        json={"expected_revision": 3, "review_note": "Đã phê duyệt phạm vi"},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["data"]["status"] == "APPROVED"
    archived = client.post(
        f"/kiem-thu/ke-hoach-kiem-thu/{plan_id}/luu-tru",
        headers=lead,
        json={"expected_revision": 4, "reason": "Kết thúc bản phát hành"},
    )
    assert archived.status_code == 200, archived.text
    assert archived.json()["data"]["status"] == "ARCHIVED"

    suite = client.post(
        f"/kiem-thu/du-an/{project_id}/bo-kiem-thu",
        headers=lead,
        json={
            "project_id": project_id,
            "name": "Bộ kiểm thử smoke",
            "suite_type": "smoke",
            "test_case_version_ids": [],
        },
    )
    assert suite.status_code == 201, suite.text
    suite_value = suite.json()["data"]
    suite_id = suite_value["_id"]
    assert suite_value["status"] == "ACTIVE"
    suite_update = client.patch(
        f"/kiem-thu/bo-kiem-thu/{suite_id}",
        headers=lead,
        json={"expected_revision": 1, "name": "Bộ kiểm thử smoke chuẩn"},
    )
    assert suite_update.status_code == 200, suite_update.text
    cloned = client.post(f"/kiem-thu/bo-kiem-thu/{suite_id}/nhan-ban", headers=lead)
    assert cloned.status_code == 201, cloned.text
    assert cloned.json()["data"]["_id"] != suite_id
    assert cloned.json()["data"]["status"] == "ACTIVE"
    suite_archive = client.post(
        f"/kiem-thu/bo-kiem-thu/{suite_id}/luu-tru",
        headers=lead,
        json={"expected_revision": 2, "reason": "Thay bằng bộ kiểm thử mới"},
    )
    assert suite_archive.status_code == 200, suite_archive.text
    assert suite_archive.json()["data"]["status"] == "ARCHIVED"

print("V4.2 test plan and suite integration passed")
