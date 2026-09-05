import asyncio
import os
import time

import httpx
import jwt
from motor.motor_asyncio import AsyncIOMotorClient


BASE_URL = os.getenv("TESTING_TEST_URL", "http://127.0.0.1:8000")
SECRET_KEY = os.environ["SECRET_KEY"]


def identity(user_id):
    return {
        "Authorization": "Bearer "
        + jwt.encode(
            {"uid": user_id, "sub": f"{user_id}@test.local", "system_role": "USER"},
            SECRET_KEY,
            algorithm="HS256",
        )
    }


QA = identity("bulk-qa-lead")
TESTER = identity("bulk-tester")


def doc(text):
    return {
        "type": "doc",
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
    }


def request(client, method, path, expected=200, headers=QA, **kwargs):
    response = client.request(method, path, headers=headers, **kwargs)
    assert response.status_code == expected, f"{method} {path} {response.status_code} {response.text}"
    body = response.json()
    if expected < 400:
        assert body["meta"]["trace_id"]
        return body["data"]
    assert body["trace_id"]
    return body


def create_case(client, project_id, stamp, suffix):
    draft = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ban-nhap-ca-kiem-thu",
        201,
        json={
            "test_case_key": f"TC-BULK-{suffix}-{stamp}",
            "title": f"Ca kiểm thử hàng loạt {suffix}",
            "type": "happy_path",
            "priority": "high",
            "risk": "high",
            "objective_doc": doc("Kiểm tra thao tác hàng loạt"),
            "preconditions_doc": doc("Hệ thống sẵn sàng"),
            "steps": [
                {
                    "id": f"step-{suffix}",
                    "order": 1,
                    "action_doc": doc("Thực hiện thao tác"),
                    "test_data": {},
                    "expected_doc": doc("Hệ thống phản hồi đúng"),
                }
            ],
            "expected_result_doc": doc("Hệ thống phản hồi đúng"),
            "postconditions_doc": doc("Không có thay đổi ngoài phạm vi"),
        },
    )
    reviewed = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ca-kiem-thu/{draft['_id']}/gui-ra-soat",
        json={"expected_revision": 1, "review_note": "Đã kiểm tra nội dung"},
    )
    approved = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/ca-kiem-thu/{draft['_id']}/phe-duyet",
        201,
        json={
            "expected_revision": reviewed["revision"],
            "change_reason": "Tạo dữ liệu bulk",
            "review_note": "Đã phê duyệt",
        },
    )
    return approved["test_case"], approved["version"]


async def insert_proposal(db, proposal):
    await db.maintenance_proposals.insert_one(proposal)


with httpx.Client(base_url=BASE_URL, timeout=30) as client:
    stamp = int(time.time() * 1000)
    project = request(
        client,
        "POST",
        "/kiem-thu/du-an",
        201,
        json={
            "key": f"BK{stamp}",
            "name": "Kiểm tra thao tác hàng loạt",
            "project_type": "web",
            "settings": {
                "requirement_lint_blocking": False,
                "testcase_lint_blocking": False,
            },
        },
    )
    project_id = project["_id"]
    request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/thanh-vien",
        201,
        json={"user_id": "bulk-tester", "project_role": "TESTER"},
    )
    first, first_version = create_case(client, project_id, stamp, "A")
    second, second_version = create_case(client, project_id, stamp, "B")

    tag_payload = {
        "artifact_type": "test_case",
        "ids": [first["_id"], second["_id"]],
        "add_tags": ["smoke", "bulk"],
        "remove_tags": [],
        "preview": True,
        "idempotency_key": f"bulk-tags-preview-{stamp}",
    }
    preview = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/hang-loat/nhan",
        headers=TESTER,
        json=tag_payload,
    )
    assert preview["preview"] is True and len(preview["results"]) == 2
    current = request(client, "GET", f"/kiem-thu/du-an/{project_id}/ca-kiem-thu", headers=TESTER)
    assert all(not item.get("tags") for item in current["items"])
    tagged = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/hang-loat/nhan",
        headers=TESTER,
        json={**tag_payload, "preview": False, "idempotency_key": f"bulk-tags-{stamp}"},
    )
    assert tagged["succeeded"] == [first["_id"], second["_id"]]
    replayed = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/hang-loat/nhan",
        headers=TESTER,
        json={**tag_payload, "preview": False, "idempotency_key": f"bulk-tags-{stamp}"},
    )
    assert replayed["operation_id"] == tagged["operation_id"]

    suite = request(
        client,
        "POST",
        "/kiem-thu/bo-kiem-thu",
        201,
        headers=TESTER,
        json={
            "project_id": project_id,
            "name": "Bộ kiểm thử bulk",
            "suite_type": "custom",
            "test_case_version_ids": [],
        },
    )
    suite_preview = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/hang-loat/ca-kiem-thu/them-vao-bo-kiem-thu",
        headers=TESTER,
        json={
            "suite_id": suite["_id"],
            "test_case_ids": [first["_id"], second["_id"]],
            "expected_revision": 1,
            "preview": True,
            "idempotency_key": f"bulk-suite-preview-{stamp}",
        },
    )
    assert suite_preview["preview"] is True
    suite_after_preview = request(client, "GET", f"/kiem-thu/bo-kiem-thu/{suite['_id']}", headers=TESTER)
    assert suite_after_preview["test_case_version_ids"] == []
    suite_added = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/hang-loat/ca-kiem-thu/them-vao-bo-kiem-thu",
        headers=TESTER,
        json={
            "suite_id": suite["_id"],
            "test_case_ids": [first["_id"], second["_id"]],
            "expected_revision": 1,
            "idempotency_key": f"bulk-suite-{stamp}",
        },
    )
    assert suite_added["succeeded"] == [first["_id"], second["_id"]]

    review_preview = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/hang-loat/ca-kiem-thu/danh-dau-can-ra-soat",
        headers=TESTER,
        json={
            "test_case_ids": [first["_id"]],
            "reason": "Cần đối chiếu sau thay đổi",
            "preview": True,
            "idempotency_key": f"bulk-review-preview-{stamp}",
        },
    )
    assert review_preview["preview"] is True
    first_before_review = request(client, "GET", f"/kiem-thu/ca-kiem-thu/{first['_id']}", headers=TESTER)
    assert first_before_review["status"] == "ACTIVE"
    review_result = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/hang-loat/ca-kiem-thu/danh-dau-can-ra-soat",
        headers=TESTER,
        json={
            "test_case_ids": [first["_id"]],
            "reason": "Cần đối chiếu sau thay đổi",
            "idempotency_key": f"bulk-review-{stamp}",
        },
    )
    assert review_result["succeeded"] == [first["_id"]]

    db = AsyncIOMotorClient(os.environ["MONGODB_URI"])[os.environ["TESTING_DB_NAME"]]
    proposal = {
        "_id": f"MP-BULK-{stamp}",
        "project_id": project_id,
        "proposal_type": "MARK_OBSOLETE",
        "target_artifact_id": second["_id"],
        "base_version_id": second_version["_id"],
        "patch": {},
        "reason": "Đề xuất bulk kiểm tra human gate",
        "confidence": 0.99,
        "evidence": [{"artifact_type": "test_case_version", "artifact_id": second_version["_id"]}],
        "status": "PENDING",
        "last_reviewed_by": "bulk-qa-lead",
        "revision": 1,
        "created_by": "bulk-qa-lead",
        "created_at": "2026-09-01T00:00:00Z",
        "updated_at": "2026-09-01T00:00:00Z",
    }
    asyncio.run(insert_proposal(db, proposal))
    approval_preview = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/hang-loat/phe-duyet-de-xuat",
        headers=QA,
        json={
            "proposal_ids": [proposal["_id"]],
            "review_note": "Đã đối chiếu mục tiêu",
            "preview": True,
            "idempotency_key": f"bulk-approval-preview-{stamp}",
        },
    )
    assert approval_preview["preview"] is True and approval_preview["succeeded"] == [proposal["_id"]]
    second_before_approval = request(client, "GET", f"/kiem-thu/ca-kiem-thu/{second['_id']}")
    assert second_before_approval["status"] == "ACTIVE"
    approved = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/hang-loat/phe-duyet-de-xuat",
        headers=QA,
        json={
            "proposal_ids": [proposal["_id"]],
            "review_note": "Đã đối chiếu mục tiêu",
            "idempotency_key": f"bulk-approval-{stamp}",
        },
    )
    assert approved["succeeded"] == [proposal["_id"]]

    run = request(
        client,
        "POST",
        "/kiem-thu/lan-chay-kiem-thu",
        201,
        headers=QA,
        json={
            "project_id": project_id,
            "name": "Lần chạy khóa lưu trữ",
            "test_case_version_ids": [first_version["_id"]],
            "environment": "staging",
            "build": "bulk-build",
        },
    )
    request(client, "POST", f"/kiem-thu/lan-chay-kiem-thu/{run['_id']}/bat-dau", headers=QA)
    blocked = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/hang-loat/luu-tru",
        headers=QA,
        json={
            "artifact_type": "test_case",
            "ids": [first["_id"]],
            "reason": "Kiểm tra ràng buộc lịch sử",
            "preview": True,
            "idempotency_key": f"bulk-archive-blocked-{stamp}",
        },
    )
    assert blocked["failed"] == [{"id": first["_id"], "code": "ACTIVE_RUN_LINK"}]
    request(client, "POST", f"/kiem-thu/lan-chay-kiem-thu/{run['_id']}/huy", headers=QA, json={"reason": "Kết thúc dữ liệu kiểm thử"})
    archive_preview = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/hang-loat/luu-tru",
        headers=QA,
        json={
            "artifact_type": "test_case",
            "ids": [first["_id"]],
            "reason": "Kiểm tra lưu trữ có human gate",
            "preview": True,
            "idempotency_key": f"bulk-archive-preview-{stamp}",
        },
    )
    assert archive_preview["succeeded"] == [first["_id"]]
    archived = request(
        client,
        "POST",
        f"/kiem-thu/du-an/{project_id}/hang-loat/luu-tru",
        headers=QA,
        json={
            "artifact_type": "test_case",
            "ids": [first["_id"]],
            "reason": "Kiểm tra lưu trữ có human gate",
            "idempotency_key": f"bulk-archive-{stamp}",
        },
    )
    assert archived["succeeded"] == [first["_id"]]
    db.client.close()

print("bulk operations integration passed")
