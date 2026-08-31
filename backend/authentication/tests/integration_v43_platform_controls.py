import os
from uuid import uuid4

import httpx
from pymongo import MongoClient
from redis import Redis


base_url = os.getenv("AUTHENTICATION_TEST_URL", "http://authentication:8000")
testing_url = os.getenv("TESTING_TEST_URL", "http://testing:8000")
run_id = uuid4().hex
password = f"V43Controls-{run_id}"


def register(client, name):
    email = f"{name}-{run_id}@example.com"
    response = client.post(
        "/xac-thuc/dang-ky",
        json={
            "email": email,
            "full_name": f"V43 {name}",
            "slug": f"{name}_{run_id[:16]}",
            "password": password,
            "agreed_to_terms": True,
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()["data"]
    return email, data.get("id") or data["_id"]


def login(client, email):
    response = client.post("/xac-thuc/dang-nhap", data={"username": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


with httpx.Client(base_url=base_url, timeout=30) as client:
    admin_email, admin_id = register(client, "controls-admin")
    user_email, user_id = register(client, "controls-user")
    deleted_email, deleted_id = register(client, "controls-delete")
    mongo = MongoClient(os.environ["MONGODB_URI"])
    auth_db = mongo[os.environ["AUTHENTICATION_DB_NAME"]]
    auth_db.auth_credentials.update_one(
        {"_id": admin_id}, {"$set": {"role": "admin", "system_role": "ADMIN"}}
    )
    admin_headers = login(client, admin_email)
    user_headers = login(client, user_email)

    assert client.get("/api/admin/operations/queue", headers=user_headers).status_code == 403
    assert client.get("/api/admin/operations/queue", headers=admin_headers).status_code == 200
    assert client.get("/api/admin/operations/rag", headers=admin_headers).status_code == 200
    assert client.get("/api/admin/operations/cache", headers=admin_headers).status_code == 200
    assert (
        client.get("/api/admin/operations/storage-usage", headers=admin_headers).status_code == 200
    )
    versions = client.get("/api/admin/operations/runtime-versions", headers=admin_headers)
    assert versions.status_code == 200, versions.text
    assert versions.json()["data"]["schema_version"] == "v4.3"

    config_paths = [
        "/api/admin/security/rate-limits",
        "/api/admin/security/break-glass-policy",
        "/api/admin/ai/limits",
        "/api/admin/ai/retrieval",
        "/api/admin/config/feature-flags",
        "/api/admin/config/localization",
        "/api/admin/config/retention",
        "/api/admin/config/default-quotas",
        "/api/admin/config/import-export",
    ]
    for path in config_paths:
        updated = client.patch(
            path,
            headers=admin_headers,
            json={"values": {"integration_marker": run_id}, "reason": "Kiểm tra V4.3"},
        )
        assert updated.status_code == 200, (path, updated.text)
        assert updated.json()["data"]["integration_marker"] == run_id
        assert client.get(path, headers=admin_headers).status_code == 200

    maintenance = client.patch(
        "/api/admin/config/maintenance",
        headers=admin_headers,
        json={"enabled": True, "banner": "Bảo trì kiểm thử", "reason": "Kiểm tra V4.3"},
    )
    assert maintenance.status_code == 200, maintenance.text
    assert maintenance.json()["data"]["enabled"] is True
    maintenance = client.patch(
        "/api/admin/config/maintenance",
        headers=admin_headers,
        json={"enabled": False, "banner": "", "reason": "Hoàn tất kiểm tra V4.3"},
    )
    assert maintenance.status_code == 200, maintenance.text

    secret = client.post(
        "/api/admin/secrets",
        headers=admin_headers,
        json={
            "name": f"secret-{run_id}",
            "provider": "vault",
            "reference": f"vault://{run_id}",
            "reason": "Kiểm tra tham chiếu V4.3",
        },
    )
    assert secret.status_code == 201, secret.text
    secret_id = secret.json()["data"]["_id"]
    assert secret.json()["data"]["reference"] == "Đã cấu hình"
    identity = client.post(
        "/api/admin/security/service-identities",
        headers=admin_headers,
        json={
            "name": f"worker-{run_id}",
            "secret_reference": secret_id,
            "scopes": ["worker.enqueue"],
            "reason": "Kiểm tra danh tính dịch vụ V4.3",
        },
    )
    assert identity.status_code == 201, identity.text
    identity_id = identity.json()["data"]["_id"]
    assert identity.json()["data"]["secret_reference"] == "Đã cấu hình"
    rotated = client.post(
        f"/api/admin/security/service-identities/{identity_id}/rotate",
        headers=admin_headers,
        json={"secret_reference": f"secret-next-{run_id}", "reason": "Luân chuyển V4.3"},
    )
    assert rotated.status_code == 200, rotated.text
    rotated_secret = client.post(
        f"/api/admin/secrets/{secret_id}/rotate",
        headers=admin_headers,
        json={"reference": f"vault://next-{run_id}", "reason": "Luân chuyển V4.3"},
    )
    assert rotated_secret.status_code == 200, rotated_secret.text
    removed_secret = client.request(
        "DELETE",
        f"/api/admin/secrets/{secret_id}",
        headers=admin_headers,
        json={"reason": "Dọn dữ liệu kiểm thử V4.3"},
    )
    assert removed_secret.status_code == 200, removed_secret.text

    bulk_preview = client.post(
        "/api/admin/users/bulk/preview",
        headers=admin_headers,
        json={
            "action": "REVOKE_SESSIONS",
            "user_ids": [user_id, "missing-user"],
            "reason": "Kiểm tra thao tác hàng loạt V4.3",
        },
    )
    assert bulk_preview.status_code == 201, bulk_preview.text
    preview = bulk_preview.json()["data"]
    assert preview["user_ids"] == [user_id]
    assert preview["missing_user_ids"] == ["missing-user"]
    bulk_confirm = client.post(
        f"/api/admin/users/bulk/{preview['_id']}/confirm",
        headers=admin_headers,
        json={"confirmation": "CONFIRM"},
    )
    assert bulk_confirm.status_code == 200, bulk_confirm.text
    assert client.get("/xac-thuc/ca-nhan", headers=user_headers).status_code == 401
    user_headers = login(client, user_email)

    project_response = httpx.post(
        f"{testing_url}/api/qa/projects",
        headers=user_headers,
        json={
            "key": f"V43-{run_id[:10].upper()}",
            "name": "Dự án kiểm tra quyền khẩn cấp V4.3",
            "description": "",
            "project_type": "web",
            "settings": {},
        },
        timeout=30,
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()["data"]
    project_id = project["_id"]
    diagnostics = client.get(f"/api/admin/projects/{project_id}/memberships", headers=admin_headers)
    assert diagnostics.status_code == 200, diagnostics.text
    assert diagnostics.json()["data"][0]["user_id"] == user_id

    grant = client.post(
        "/api/admin/security/break-glass",
        headers=admin_headers,
        json={
            "project_id": project_id,
            "user_id": admin_id,
            "permissions": ["project.read", "requirement.read"],
            "ttl_minutes": 15,
            "reason": "Kiểm tra truy cập hỗ trợ có thời hạn V4.3",
        },
    )
    assert grant.status_code == 201, grant.text
    grant_id = grant.json()["data"]["_id"]
    break_glass_project = httpx.get(
        f"{testing_url}/api/qa/projects/{project_id}", headers=admin_headers, timeout=30
    )
    assert break_glass_project.status_code == 200, break_glass_project.text
    assert break_glass_project.json()["data"]["access_context"]["mode"] == "BREAK_GLASS"
    assert "requirement.read" in break_glass_project.json()["data"]["current_permissions"]
    revoked = client.post(
        f"/api/admin/security/break-glass/{grant_id}/revoke",
        headers=admin_headers,
        json={"reason": "Hoàn tất kiểm tra quyền khẩn cấp V4.3"},
    )
    assert revoked.status_code == 200, revoked.text
    assert (
        httpx.get(
            f"{testing_url}/api/qa/projects/{project_id}", headers=admin_headers, timeout=30
        ).status_code
        == 403
    )

    reindex = client.post(
        "/api/admin/operations/rag/reindex",
        headers=admin_headers,
        json={"project_id": project_id, "artifact_version_ids": [], "reason": "Kiểm tra RAG V4.3"},
    )
    assert reindex.status_code == 202, reindex.text
    assert reindex.json()["data"]["jobs"] == []

    cache = Redis.from_url(os.environ["REDIS_URI"], decode_responses=True)
    cache.set(f"project_metadata:{run_id}", "test")
    cleared = client.post(
        "/api/admin/operations/cache/clear",
        headers=admin_headers,
        json={
            "scope": "PROJECT_METADATA",
            "confirmation": "CLEAR_SAFE_CACHE",
            "reason": "Kiểm tra xóa cache V4.3",
        },
    )
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["data"]["deleted"] >= 1
    assert cache.get(f"project_metadata:{run_id}") is None
    cache.close()

    emergency = client.post(
        "/api/admin/security/emergency-revoke",
        headers=admin_headers,
        json={
            "scope": "USER",
            "target_id": user_id,
            "confirmation": "EMERGENCY_REVOKE",
            "reason": "Kiểm tra thu hồi khẩn cấp tài khoản V4.3",
        },
    )
    assert emergency.status_code == 200, emergency.text

    deleted = client.request(
        "DELETE",
        f"/api/admin/users/{deleted_id}",
        headers=admin_headers,
        json={"confirmation": deleted_email, "reason": "Dọn tài khoản kiểm thử V4.3"},
    )
    assert deleted.status_code == 200, deleted.text
    account = auth_db.auth_credentials.find_one({"_id": deleted_id})
    assert account["account_status"] == "DELETED"
    assert "password_hash" not in account

    removed_project = client.request(
        "DELETE",
        f"/api/admin/projects/{project_id}",
        headers=admin_headers,
        json={"confirmation": project["key"], "reason": "Dọn dự án kiểm thử V4.3"},
    )
    assert removed_project.status_code == 200, removed_project.text
    assert (
        mongo[os.environ.get("TESTING_DB_NAME", "veriq_testing")].projects.count_documents(
            {"_id": project_id}
        )
        == 0
    )
    mongo.close()

print("V4.3 platform controls integration passed")
