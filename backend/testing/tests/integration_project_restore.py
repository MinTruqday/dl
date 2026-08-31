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


lead = identity("restore-lead-v42")
viewer = identity("restore-viewer-v42")


with httpx.Client(base_url=base_url, timeout=30) as client:
    stamp = int(time.time() * 1000)
    created = client.post(
        "/kiem-thu/du-an",
        headers=lead,
        json={
            "key": f"RST{stamp}",
            "name": "V4.2 Project Restore",
            "description": "Project lifecycle integration",
            "project_type": "web",
            "settings": {
                "timezone": "Asia/Ho_Chi_Minh",
                "locale": "vi",
                "read_after_archive_policy": "DENY_READ",
            },
        },
    )
    assert created.status_code == 201, created.text
    project = created.json()["data"]
    project_id = project["_id"]

    member = client.post(
        f"/kiem-thu/du-an/{project_id}/thanh-vien",
        headers=lead,
        json={"user_id": "restore-viewer-v42", "project_role": "VIEWER"},
    )
    assert member.status_code == 201, member.text

    invitation = client.post(
        f"/kiem-thu/du-an/{project_id}/loi-moi",
        headers=lead,
        json={"user_id": "restore-invited-v42", "project_role": "TESTER"},
    )
    assert invitation.status_code == 201, invitation.text
    resent = client.post(
        f"/kiem-thu/du-an/{project_id}/thanh-vien/khoi-phuc-invited-v42/gui-lai-loi-moi",
        headers=lead,
    )
    assert resent.status_code == 200, resent.text
    cancelled = client.post(
        f"/kiem-thu/du-an/{project_id}/thanh-vien/khoi-phuc-invited-v42/huy-loi-moi",
        headers=lead,
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["data"]["status"] == "CANCELLED"

    accepted_invitation = client.post(
        f"/kiem-thu/du-an/{project_id}/loi-moi",
        headers=lead,
        json={"user_id": "restore-accept-v42", "project_role": "BA"},
    )
    assert accepted_invitation.status_code == 201, accepted_invitation.text
    accepted = client.post(
        f"/kiem-thu/du-an/{project_id}/thanh-vien/khoi-phuc-accept-v42/chap-nhan",
        headers=identity("restore-accept-v42"),
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["data"]["status"] == "ACTIVE"

    source = client.post(
        f"/kiem-thu/du-an/{project_id}/tai-lieu-yeu-cau",
        headers=lead,
        json={
            "filename": "v42-source.md",
            "format": "md",
            "content": "Nguồn yêu cầu V4.2",
        },
    )
    assert source.status_code == 201, source.text
    source_id = source.json()["data"]["_id"]
    sources = client.get(
        f"/kiem-thu/du-an/{project_id}/tai-lieu-yeu-cau",
        headers=lead,
    )
    assert sources.status_code == 200, sources.text
    assert source_id in {item["_id"] for item in sources.json()["data"]}
    downloaded = client.get(
        f"/kiem-thu/tai-lieu-yeu-cau/{source_id}/tai-xuong",
        headers=lead,
    )
    assert downloaded.status_code == 200, downloaded.text
    assert downloaded.content == "Nguồn yêu cầu V4.2".encode()
    viewer_download = client.get(
        f"/kiem-thu/tai-lieu-yeu-cau/{source_id}/tai-xuong",
        headers=viewer,
    )
    assert viewer_download.status_code == 403, viewer_download.text
    archived_source = client.post(
        f"/kiem-thu/tai-lieu-yeu-cau/{source_id}/luu-tru",
        headers=lead,
        json={"expected_revision": 1, "reason": "Kiểm tra lưu trữ nguồn"},
    )
    assert archived_source.status_code == 200, archived_source.text
    restored_source = client.post(
        f"/kiem-thu/tai-lieu-yeu-cau/{source_id}/khoi-phuc",
        headers=lead,
        json={"expected_revision": 2, "reason": "Kiểm tra khôi phục nguồn"},
    )
    assert restored_source.status_code == 200, restored_source.text
    assert restored_source.json()["data"]["status"] == "READY"

    archived = client.post(
        f"/kiem-thu/du-an/{project_id}/luu-tru",
        headers=lead,
        json={"expected_revision": 1, "reason": "Kiểm tra lưu trữ dự án V4.2"},
    )
    assert archived.status_code == 200, archived.text
    assert archived.json()["data"]["status"] == "archived"

    denied_archived_artifacts = client.get(
        f"/kiem-thu/du-an/{project_id}/yeu-cau",
        headers=viewer,
    )
    assert denied_archived_artifacts.status_code == 403, denied_archived_artifacts.text
    assert (
        denied_archived_artifacts.json()["error"]["code"]
        == "PROJECT_ARCHIVED_READ_DENIED"
    )

    archived_project = client.get(
        f"/kiem-thu/du-an/{project_id}",
        headers=viewer,
    )
    assert archived_project.status_code == 200, archived_project.text

    mutation = client.post(
        f"/kiem-thu/du-an/{project_id}/yeu-cau",
        headers=lead,
        json={"title": "Không được tạo khi dự án đã lưu trữ"},
    )
    assert mutation.status_code == 409, mutation.text

    viewer_restore = client.post(
        f"/kiem-thu/du-an/{project_id}/khoi-phuc",
        headers=viewer,
        json={"expected_revision": 2, "reason": "Viewer không được khôi phục"},
    )
    assert viewer_restore.status_code == 403, viewer_restore.text

    restored = client.post(
        f"/kiem-thu/du-an/{project_id}/khoi-phuc",
        headers=lead,
        json={"expected_revision": 2, "reason": "Khôi phục dự án V4.2"},
    )
    assert restored.status_code == 200, restored.text
    assert restored.json()["data"]["status"] == "active"
    assert restored.json()["meta"]["revision"] == 3

    audits = client.get(f"/kiem-thu/du-an/{project_id}/nhat-ky", headers=lead)
    assert audits.status_code == 200, audits.text
    actions = {item["action"] for item in audits.json()["data"]}
    assert {"project_archived", "project_restored"} <= actions

print("V4.2 project archive and restore integration passed")
