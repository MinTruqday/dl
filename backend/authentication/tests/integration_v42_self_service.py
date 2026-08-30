import os
from uuid import uuid4

import httpx


base_url = os.getenv("AUTHENTICATION_TEST_URL", "http://authentication:8000")
run_id = uuid4().hex
email = f"self-{run_id}@example.com"
old_password = f"V42Self-{run_id}"
new_password = f"V42Changed-{run_id}"


def login(client, password):
    response = client.post(
        "/xac-thuc/dang-nhap",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


with httpx.Client(base_url=base_url, timeout=30) as client:
    registered = client.post(
        "/xac-thuc/dang-ky",
        json={
            "email": email,
            "full_name": "V42 Self Service",
            "slug": f"self_{run_id[:16]}",
            "password": old_password,
            "agreed_to_terms": True,
        },
    )
    assert registered.status_code == 201, registered.text
    first = login(client, old_password)
    second = login(client, old_password)

    profile = client.patch(
        "/xac-thuc/ca-nhan",
        headers=second,
        json={
            "full_name": "V42 Self Service Updated",
            "locale": "vi",
            "timezone": "Asia/Ho_Chi_Minh",
        },
    )
    assert profile.status_code == 200, profile.text
    assert profile.json()["data"]["full_name"] == "V42 Self Service Updated"
    assert "password_hash" not in profile.text
    settings = client.patch(
        "/xac-thuc/cai-dat",
        headers=second,
        json={"theme": "light", "notifications_enabled": True, "privacy_mode": True},
    )
    assert settings.status_code == 200, settings.text
    notifications = client.patch(
        "/xac-thuc/thong-bao",
        headers=second,
        json={"enable_comment_notifications": True, "enable_mention_notifications": False, "enable_system_notifications": True, "enable_email_digest": False},
    )
    assert notifications.status_code == 200, notifications.text

    sessions = client.get("/xac-thuc/phien", headers=second)
    assert sessions.status_code == 200, sessions.text
    values = sessions.json()["data"]
    assert len([item for item in values if item["revoked_at"] is None]) >= 2
    assert "refresh_token_hash" not in sessions.text
    other = next(item for item in values if not item["is_current"] and item["revoked_at"] is None)
    revoked = client.delete(f"/xac-thuc/phien/{other['_id']}", headers=second)
    assert revoked.status_code == 200, revoked.text
    assert client.get("/xac-thuc/ca-nhan", headers=first).status_code == 401

    changed = client.post(
        "/xac-thuc/doi-mat-khau",
        headers=second,
        json={"current_password": old_password, "new_password": new_password},
    )
    assert changed.status_code == 200, changed.text
    assert client.get("/xac-thuc/ca-nhan", headers=second).status_code == 200
    assert (
        client.post(
            "/xac-thuc/dang-nhap",
            data={"username": email, "password": old_password},
        ).status_code
        == 401
    )
    login(client, new_password)

print("V4.2 account self service integration passed")
