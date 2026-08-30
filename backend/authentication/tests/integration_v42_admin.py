import os
from uuid import uuid4

import httpx
from pymongo import MongoClient


base_url = os.getenv("AUTHENTICATION_TEST_URL", "http://authentication:8000")
run_id = uuid4().hex
password = f"V42Admin-{run_id}"


def register(client, name):
    email = f"{name}-{run_id}@example.com"
    response = client.post(
        "/xac-thuc/dang-ky",
        json={
            "email": email,
            "full_name": f"V42 {name}",
            "slug": f"{name}_{run_id[:16]}",
            "password": password,
            "agreed_to_terms": True,
        },
    )
    assert response.status_code == 201, response.text
    return email, response.json()["data"].get("id") or response.json()["data"]["_id"]


def login(client, email):
    response = client.post(
        "/xac-thuc/dang-nhap", data={"username": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


with httpx.Client(base_url=base_url, timeout=30) as client:
    admin_email, admin_id = register(client, "admin")
    user_email, user_id = register(client, "user")
    legacy_email, legacy_id = register(client, "legacy")
    mongo = MongoClient(os.environ["MONGODB_URI"])
    accounts = mongo[os.environ["AUTHENTICATION_DB_NAME"]].auth_credentials
    accounts.update_one(
        {"_id": admin_id}, {"$set": {"role": "admin", "system_role": "ADMIN"}}
    )
    accounts.update_one(
        {"_id": legacy_id}, {"$set": {"role": "admin", "system_role": "USER"}}
    )
    mongo.close()

    admin_headers = login(client, admin_email)
    legacy_headers = login(client, legacy_email)
    assert client.get("/api/admin/users", headers=legacy_headers).status_code == 403

    users = client.get("/api/admin/users", headers=admin_headers)
    assert users.status_code == 200, users.text
    assert user_id in {item["_id"] for item in users.json()["data"]}

    invited = client.post(
        "/api/admin/users",
        headers=admin_headers,
        json={
            "email": f"invited-{run_id}@example.com",
            "full_name": "V42 Invited",
            "slug": f"invited_{run_id[:16]}",
            "reason": "Kiểm tra luồng tạo và mời tài khoản V4.2",
        },
    )
    assert invited.status_code == 201, invited.text
    assert "password" not in invited.text.lower()

    detail = client.get(f"/api/admin/users/{user_id}", headers=admin_headers)
    assert detail.status_code == 200, detail.text
    assert "password_hash" not in detail.text
    assert "refresh_token_hash" not in detail.text

    user_headers = login(client, user_email)
    sessions = client.get(f"/api/admin/users/{user_id}/sessions", headers=admin_headers)
    assert sessions.status_code == 200, sessions.text
    assert "refresh_token_hash" not in sessions.text
    assert sessions.json()["data"]

    locked = client.post(
        f"/api/admin/users/{user_id}/lock",
        headers=admin_headers,
        json={"reason": "Kiểm tra khóa tài khoản V4.2"},
    )
    assert locked.status_code == 200, locked.text
    assert client.get("/xac-thuc/ca-nhan", headers=user_headers).status_code == 401
    assert (
        client.post(
            "/xac-thuc/dang-nhap", data={"username": user_email, "password": password}
        ).status_code
        == 403
    )

    unlocked = client.post(
        f"/api/admin/users/{user_id}/unlock",
        headers=admin_headers,
        json={"reason": "Kiểm tra mở khóa tài khoản V4.2"},
    )
    assert unlocked.status_code == 200, unlocked.text
    user_headers = login(client, user_email)

    promoted = client.patch(
        f"/api/admin/users/{user_id}/system-role",
        headers=admin_headers,
        json={"system_role": "ADMIN", "reason": "Kiểm tra cấp quyền quản trị V4.2"},
    )
    assert promoted.status_code == 200, promoted.text
    assert promoted.json()["data"]["system_role"] == "ADMIN"
    assert client.get("/xac-thuc/ca-nhan", headers=user_headers).status_code == 401

    demoted = client.patch(
        f"/api/admin/users/{user_id}/system-role",
        headers=admin_headers,
        json={"system_role": "USER", "reason": "Kiểm tra hạ quyền quản trị V4.2"},
    )
    assert demoted.status_code == 200, demoted.text
    assert demoted.json()["data"]["system_role"] == "USER"

    memberships = client.get(
        f"/api/admin/users/{user_id}/memberships", headers=admin_headers
    )
    assert memberships.status_code == 200, memberships.text
    assert "plain_text_projection" not in memberships.text

    audit = client.get(f"/api/admin/users/{user_id}/audit", headers=admin_headers)
    assert audit.status_code == 200, audit.text
    actions = {event["action"] for event in audit.json()["data"]}
    assert "ADMIN_USER_LOCKED" in actions
    assert "ADMIN_SYSTEM_ROLE_UPDATED" in actions

    health = client.get("/api/admin/health", headers=admin_headers)
    assert health.status_code == 200, health.text
    assert {item["service"] for item in health.json()["data"]["services"]} >= {
        "authentication",
        "testing",
        "worker",
        "ai",
        "mongodb",
    }

    jobs = client.get("/api/admin/operations/jobs", headers=admin_headers)
    assert jobs.status_code == 200, jobs.text

    auth_policy = client.patch(
        "/api/admin/security/auth-policy",
        headers=admin_headers,
        json={"values": {"registration_mode": "AUTHENTICATED", "refresh_ttl_days": 7}, "reason": "Kiểm tra chính sách bảo mật V4.2"},
    )
    assert auth_policy.status_code == 200, auth_policy.text
    assert auth_policy.json()["data"]["registration_mode"] == "AUTHENTICATED"
    integrations = client.patch(
        "/api/admin/integrations",
        headers=admin_headers,
        json={"values": {"webhook_enabled": False}, "reason": "Kiểm tra cấu hình tích hợp V4.2"},
    )
    assert integrations.status_code == 200, integrations.text
    storage = client.patch(
        "/api/admin/storage",
        headers=admin_headers,
        json={"values": {"provider": "r2", "secret_token": "must-not-leak"}, "reason": "Kiểm tra cấu hình lưu trữ V4.2"},
    )
    assert storage.status_code == 200, storage.text
    assert storage.json()["data"]["secret_token"] == "Đã cấu hình"
    registered_model = client.post(
        "/api/admin/ai/models",
        headers=admin_headers,
        json={"provider_id": "ollama", "model": f"integration-{run_id}", "version": "1", "capabilities": ["chat"], "reason": "Kiểm tra đăng ký mô hình AI V4.2"},
    )
    assert registered_model.status_code == 201, registered_model.text
    model_id = registered_model.json()["data"]["_id"]
    assert client.get("/api/admin/ai/models", headers=admin_headers).status_code == 200
    updated_model = client.patch(
        f"/api/admin/ai/models/{model_id}",
        headers=admin_headers,
        json={"values": {"enabled": False}, "reason": "Kiểm tra vô hiệu hóa mô hình AI V4.2"},
    )
    assert updated_model.status_code == 200, updated_model.text
    assert updated_model.json()["data"]["enabled"] is False

    policy = client.patch(
        "/api/admin/platform/project-policy",
        headers=admin_headers,
        json={
            "project_creation_policy": "ADMIN_ONLY",
            "reason": "Kiểm tra chính sách tạo dự án V4.2",
        },
    )
    assert policy.status_code == 200, policy.text
    with httpx.Client(base_url="http://testing:8000", timeout=30) as testing:
        project_payload = {
            "key": f"ADM{run_id[:12].upper()}",
            "name": "V4.2 Admin Policy",
            "description": "Project creation policy integration",
            "project_type": "web",
            "settings": {},
        }
        denied_project = testing.post(
            "/api/qa/projects",
            headers=legacy_headers,
            json=project_payload,
        )
        assert denied_project.status_code == 403, denied_project.text
        admin_project = testing.post(
            "/api/qa/projects",
            headers=admin_headers,
            json=project_payload,
        )
        assert admin_project.status_code == 201, admin_project.text
    restored_policy = client.patch(
        "/api/admin/platform/project-policy",
        headers=admin_headers,
        json={
            "project_creation_policy": "AUTHENTICATED",
            "reason": "Khôi phục chính sách sau kiểm thử V4.2",
        },
    )
    assert restored_policy.status_code == 200, restored_policy.text

    self_demote = client.patch(
        f"/api/admin/users/{admin_id}/system-role",
        headers=admin_headers,
        json={"system_role": "USER", "reason": "Kiểm tra bảo vệ quản trị viên hiện tại"},
    )
    assert self_demote.status_code == 422, self_demote.text

print("V4.2 system admin integration passed")
