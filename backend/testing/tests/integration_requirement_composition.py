import os
import time

import httpx
import jwt


BASE_URL = os.getenv("TESTING_TEST_URL", "http://127.0.0.1:8000")
HEADERS = {
    "Authorization": "Bearer "
    + jwt.encode(
        {"uid": "requirement-composition-lead", "sub": "requirement-composition@test.local", "system_role": "USER"},
        os.environ["SECRET_KEY"],
        algorithm="HS256",
    )
}


def doc(text):
    return {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]}


def request(client, method, path, expected=200, **kwargs):
    response = client.request(method, path, headers=HEADERS, **kwargs)
    assert response.status_code == expected, f"{method} {path} {response.status_code} {response.text}"
    body = response.json()
    assert body["meta"]["trace_id"]
    return body["data"]


def create_baseline(client, project_id, key, title, behavior):
    requirement = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/yeu-cau",
        201,
        json={
            "requirement_key": key,
            "title": title,
            "type": "functional",
            "priority": "high",
            "risk": "high",
            "content_doc": doc(f"Khi người dùng thao tác thì hệ thống phải {behavior}"),
            "acceptance_criteria": [
                {"key": "AC-01", "content_doc": doc(f"Khi thao tác hợp lệ thì hệ thống phải {behavior}")}
            ],
            "business_rules": [behavior],
            "actors": ["Người dùng"],
        },
    )
    version = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/yeu-cau/{requirement['_id']}/gui-ra-soat",
        json={"expected_revision": 1, "review_note": "Đã kiểm tra nội dung và tiêu chí"},
    )
    version = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/yeu-cau/{requirement['_id']}/phe-duyet",
        json={"expected_revision": version["revision"], "review_note": "Phê duyệt làm nguồn chuẩn"},
    )
    return requirement["_id"], version


with httpx.Client(base_url=BASE_URL, timeout=30) as client:
    stamp = int(time.time() * 1000)
    project = request(
        client,
        "POST",
        "/kiem-thu/du-an",
        201,
        json={"key": f"RC{stamp}", "name": "Requirement Composition", "project_type": "web"},
    )
    project_id = project["_id"]
    document = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/tai-lieu-yeu-cau",
        201,
        json={
            "filename": "candidate-workflow.md",
            "format": "md",
            "content": "Người dùng đăng nhập bằng email. Hệ thống ghi nhật ký đăng nhập. Quản trị viên xuất báo cáo.",
        },
    )
    extraction = request(
        client,
        "POST",
        f"/kiem-thu/tai-lieu-yeu-cau/{document['_id']}/trich-xuat",
        201,
        json={"idempotency_key": f"candidate-extract-{stamp}"},
    )
    assert len(extraction["preview"]) == 3
    assert all(item["candidate_id"] for item in extraction["preview"])
    first_candidate, second_candidate, _ = extraction["preview"]
    merged_candidates = request(
        client,
        "POST",
        f"/kiem-thu/nhap-yeu-cau/{extraction['_id']}/ung-vien/gop",
        json={
            "expected_revision": 1,
            "candidate_ids": [first_candidate["candidate_id"], second_candidate["candidate_id"]],
            "merged": {
                "title": "Đăng nhập và ghi nhật ký",
                "content_doc": doc("Khi đăng nhập thì hệ thống phải xác thực và ghi nhật ký"),
                "acceptance_criteria": [],
            },
            "reason": "Hai câu cùng mô tả luồng đăng nhập",
        },
    )
    assert merged_candidates["candidate_count"] == 2
    merged_candidate = merged_candidates["preview"][0]
    assert len(merged_candidate["source_refs"]) == 2
    assert merged_candidate["parent_candidate_ids"] == [
        first_candidate["candidate_id"],
        second_candidate["candidate_id"],
    ]
    split_candidates = request(
        client,
        "POST",
        f"/kiem-thu/nhap-yeu-cau/{extraction['_id']}/ung-vien/{merged_candidate['candidate_id']}/tach",
        json={
            "expected_revision": 2,
            "drafts": [
                {
                    "title": "Đăng nhập bằng email",
                    "content_doc": doc("Khi đăng nhập thì hệ thống phải xác thực email"),
                },
                {
                    "title": "Ghi nhật ký đăng nhập",
                    "content_doc": doc("Khi đăng nhập thì hệ thống phải ghi nhật ký"),
                },
            ],
            "reason": "Tách lại thành hai trách nhiệm",
        },
    )
    assert split_candidates["candidate_count"] == 3
    assert all(
        item["parent_candidate_ids"] == [merged_candidate["candidate_id"]]
        and len(item["source_refs"]) == 2
        for item in split_candidates["preview"][:2]
    )
    edited_preview = [{**item, "title": item["title"].strip()} for item in split_candidates["preview"]]
    reviewed_candidates = request(
        client,
        "PATCH",
        f"/kiem-thu/nhap-yeu-cau/{extraction['_id']}",
        json={
            "expected_revision": 3,
            "preview": edited_preview,
            "review_note": "Đã kiểm tra nguồn sau khi tách",
        },
    )
    assert all(item["source_refs"] for item in reviewed_candidates["preview"])
    rejected_id = reviewed_candidates["preview"][-1]["candidate_id"]
    rejected_candidates = request(
        client,
        "POST",
        f"/kiem-thu/nhap-yeu-cau/{extraction['_id']}/ung-vien/{rejected_id}/tu-choi",
        json={"expected_revision": 4, "reason": "Không thuộc phạm vi xác thực"},
    )
    assert rejected_candidates["candidate_count"] == 2
    assert rejected_id not in {item["candidate_id"] for item in rejected_candidates["preview"]}
    assert rejected_candidates["rejected_candidates"][-1]["candidate_status"] == "REJECTED"
    assert rejected_candidates["rejected_candidates"][-1]["source_refs"]
    first_id, first_version = create_baseline(
        client,
        project_id,
        f"REQ-SPLIT-{stamp}",
        "Xác thực và ghi nhật ký đăng nhập",
        "xác thực thông tin và ghi nhật ký đăng nhập",
    )
    duplicate_id, duplicate_version = create_baseline(
        client,
        project_id,
        f"REQ-DUP-{stamp}",
        "Xác thực và lưu nhật ký đăng nhập",
        "xác thực thông tin và ghi nhật ký đăng nhập",
    )
    merge_left_id, merge_left_version = create_baseline(
        client,
        project_id,
        f"REQ-MERGE-A-{stamp}",
        "Tạo tài khoản",
        "tạo tài khoản mới",
    )
    merge_right_id, merge_right_version = create_baseline(
        client,
        project_id,
        f"REQ-MERGE-B-{stamp}",
        "Gửi thư xác nhận",
        "gửi thư xác nhận tài khoản",
    )
    scan = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/yeu-cau/kiem-tra-trung-lap",
        201,
        json={"requirement_ids": [first_id, duplicate_id], "threshold": 0.5, "limit": 10},
    )
    assert scan["status"] == "COMPLETED"
    assert scan["candidate_count"] == 1
    assert scan["candidates"][0]["status"] == "CANDIDATE"
    split_payload = {
        "expected_source_version_id": first_version["_id"],
        "idempotency_key": f"split-{stamp}",
        "reason": "Tách xác thực và nhật ký thành hai trách nhiệm độc lập",
        "drafts": [
            {
                "title": "Xác thực thông tin đăng nhập",
                "content_doc": doc("Khi đăng nhập thì hệ thống phải xác thực thông tin"),
                "acceptance_criteria": [
                    {"key": "AC-01", "content_doc": doc("Khi thông tin đúng thì hệ thống phải xác thực thành công")}
                ],
                "actors": ["Người dùng"],
            },
            {
                "title": "Ghi nhật ký đăng nhập",
                "content_doc": doc("Khi đăng nhập thì hệ thống phải ghi nhật ký"),
                "acceptance_criteria": [
                    {"key": "AC-01", "content_doc": doc("Khi đăng nhập hoàn tất thì hệ thống phải lưu thời điểm")}
                ],
                "actors": ["Người dùng"],
            },
        ],
    }
    split = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/yeu-cau/{first_id}/tach",
        201,
        json=split_payload,
    )
    assert split["transformation"]["status"] == "CONFIRMED"
    assert len(split["requirements"]) == 2
    assert all(item["current_version"]["status"] == "DRAFT" for item in split["requirements"])
    assert all(
        item["current_version"]["derived_from"][0]["requirement_version_id"] == first_version["_id"]
        for item in split["requirements"]
    )
    replayed_split = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/yeu-cau/{first_id}/tach",
        201,
        json=split_payload,
    )
    assert replayed_split["transformation"]["_id"] == split["transformation"]["_id"]
    assert {item["_id"] for item in replayed_split["requirements"]} == {
        item["_id"] for item in split["requirements"]
    }
    superseded = request(client, "GET", f"/kiem-thu/yeu-cau/{first_id}")
    assert superseded["status"] == "SUPERSEDED"
    assert superseded["current_version"]["status"] == "SUPERSEDED"
    assert superseded["current_version"]["title"] == "Xác thực và ghi nhật ký đăng nhập"
    merge_payload = {
        "source_requirement_ids": [merge_left_id, merge_right_id],
        "expected_source_version_ids": {
            merge_left_id: merge_left_version["_id"],
            merge_right_id: merge_right_version["_id"],
        },
        "idempotency_key": f"merge-{stamp}",
        "reason": "Hợp nhất luồng tạo và xác nhận tài khoản",
        "draft": {
            "title": "Tạo và xác nhận tài khoản",
            "content_doc": doc("Khi đăng ký thì hệ thống phải tạo tài khoản và gửi thư xác nhận"),
            "acceptance_criteria": [
                {"key": "AC-01", "content_doc": doc("Khi dữ liệu hợp lệ thì hệ thống phải gửi thư xác nhận")}
            ],
            "actors": ["Người dùng"],
        },
    }
    merged = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/yeu-cau/gop",
        201,
        json=merge_payload,
    )
    assert merged["transformation"]["status"] == "CONFIRMED"
    assert len(merged["requirements"]) == 1
    assert len(merged["requirements"][0]["current_version"]["derived_from"]) == 2
    replayed_merge = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/yeu-cau/gop",
        201,
        json=merge_payload,
    )
    assert replayed_merge["transformation"]["_id"] == merged["transformation"]["_id"]
    for source_id in (merge_left_id, merge_right_id):
        source = request(client, "GET", f"/kiem-thu/yeu-cau/{source_id}")
        assert source["status"] == "SUPERSEDED"
        assert source["current_version"]["status"] == "SUPERSEDED"
    changed_version = request(
        client,
        "POST",
        f"/kiem-thu/yeu-cau/{duplicate_id}/phien-ban",
        201,
        json={
            "requirement_key": f"REQ-DUP-{stamp}",
            "title": "Xác thực và lưu nhật ký đăng nhập mở rộng",
            "type": "functional",
            "priority": "high",
            "risk": "high",
            "content_doc": doc("Khi người dùng đăng nhập thì hệ thống phải xác thực và lưu địa chỉ mạng trong nhật ký"),
            "acceptance_criteria": [
                {"key": "AC-01", "content_doc": doc("Khi đăng nhập thành công thì hệ thống phải lưu địa chỉ mạng")}
            ],
            "business_rules": ["Lưu địa chỉ mạng trong nhật ký"],
            "actors": ["Người dùng"],
            "change_reason": "Bổ sung địa chỉ mạng vào nhật ký",
            "expected_current_version_id": duplicate_version["_id"],
        },
    )
    changed_version = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/yeu-cau/{duplicate_id}/gui-ra-soat",
        json={"expected_revision": 1, "review_note": "Rà soát thay đổi nhật ký"},
    )
    changed_version = request(
        client,
        "POST",
        f"/kiem-thu/phien-ban-yeu-cau/{changed_version['_id']}/chot-chuan",
        json={"expected_revision": changed_version["revision"], "review_note": "Phê duyệt thay đổi nhật ký"},
    )
    change_set = request(
        client,
        "POST",
        f"/kiem-thu/yeu-cau/{duplicate_id}/bo-thay-doi",
        201,
        json={"from_version_id": duplicate_version["_id"], "to_version_id": changed_version["_id"]},
    )
    change_set = request(
        client,
        "POST",
        f"/kiem-thu/bo-thay-doi/{change_set['_id']}/ra-soat",
        json={
            "expected_revision": change_set["revision"],
            "changes": change_set["changes"],
            "review_note": "Xác nhận thay đổi để phân tích",
        },
    )
    first_impact = request(
        client,
        "POST",
        f"/kiem-thu/bo-thay-doi/{change_set['_id']}/phan-tich-anh-huong",
        201,
    )
    rerun_impact = request(
        client,
        "POST",
        f"/kiem-thu/phan-tich-anh-huong/{first_impact['_id']}/chay-lai",
        201,
        json={
            "expected_revision": first_impact["revision"],
            "reason": "Xác minh snapshot sau khi chỉ mục thay đổi",
            "knowledge_index_version": f"composition-{stamp}",
            "algorithm_version": "impact-pipeline-v1",
        },
    )
    assert rerun_impact["snapshot_number"] == 2
    assert rerun_impact["supersedes_analysis_id"] == first_impact["_id"]
    assert request(client, "GET", f"/kiem-thu/phan-tich-anh-huong/{first_impact['_id']}")["status"] == "SUPERSEDED"
    closed_impact = request(
        client,
        "POST",
        f"/kiem-thu/phan-tich-anh-huong/{rerun_impact['_id']}/ra-soat",
        json={
            "expected_revision": rerun_impact["revision"],
            "overrides": [],
            "review_note": "Đã kiểm tra snapshot chạy lại",
        },
    )
    assert closed_impact["status"] == "REVIEWED"

print("requirement composition integration passed")
