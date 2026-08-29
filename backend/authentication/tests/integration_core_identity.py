import os
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
import jwt
from pymongo import MongoClient


base_url = os.getenv("AUTHENTICATION_TEST_URL", "http://authentication:8000")
run_id = uuid4().hex
email = f"identity-{run_id}@example.com"
slug = f"identity_{run_id[:16]}"
password = f"StrongPassword-{run_id}"


with httpx.Client(base_url=base_url, timeout=30) as client:
    registered = client.post(
        "/xac-thuc/dang-ky",
        json={
            "email": email,
            "full_name": "Identity Test",
            "slug": slug,
            "password": password,
            "agreed_to_terms": True,
            "role": "admin",
        },
    )
    assert registered.status_code == 201, registered.text
    account = registered.json()["data"]
    assert account["role"] == "reader"
    account_id = account.get("id") or account["_id"]

    wrong_password = client.post(
        "/xac-thuc/dang-nhap", data={"username": email, "password": "WrongPassword-123"}
    )
    assert wrong_password.status_code == 401

    login = client.post("/xac-thuc/dang-nhap", data={"username": email, "password": password})
    assert login.status_code == 200, login.text
    token = login.json()["data"]["access_token"]
    claims = jwt.decode(token, os.environ["SECRET_KEY"], algorithms=["HS256"])
    assert claims["system_role"] == "USER"
    assert "project_role" not in claims
    original_refresh = client.cookies.get("veriq_refresh_token")
    assert original_refresh
    refreshed = client.post("/xac-thuc/lam-moi-phien")
    assert refreshed.status_code == 200, refreshed.text
    refreshed_token = refreshed.json()["data"]["access_token"]
    assert refreshed_token != token
    assert client.cookies.get("veriq_refresh_token") != original_refresh
    with httpx.Client(
        base_url=base_url, timeout=30, cookies={"veriq_refresh_token": original_refresh}
    ) as replay_client:
        replay = replay_client.post("/xac-thuc/lam-moi-phien")
        assert replay.status_code == 401
    token = refreshed_token
    bearer = {"Authorization": f"Bearer {token}"}
    me = client.get("/xac-thuc/ca-nhan", headers=bearer)
    assert me.status_code == 200, me.text
    assert me.json()["data"]["email"] == email
    assert me.json()["data"]["full_name"] == "Identity Test"
    assert "password_hash" not in me.json()["data"]

    internal = client.get(
        f"/xac-thuc/noi-bo/tai-khoan/{account_id}",
        headers={"X-Internal-Token": os.environ["SECRET_KEY"]},
    )
    assert internal.status_code == 200, internal.text
    assert internal.json()["data"]["storage_limit"] > 0

    managed_email = f"managed-{run_id}@example.com"
    managed_password = f"ManagedPassword-{run_id}"
    managed = client.post(
        "/xac-thuc/dang-ky",
        json={
            "email": managed_email,
            "full_name": "Managed Identity",
            "slug": f"managed_{run_id[:16]}",
            "password": managed_password,
            "agreed_to_terms": True,
        },
    )
    assert managed.status_code == 201, managed.text
    managed_id = managed.json()["data"].get("id") or managed.json()["data"]["_id"]
    mongo_client = MongoClient(os.environ["MONGODB_URI"])
    mongo_client[os.environ["AUTHENTICATION_DB_NAME"]].auth_credentials.update_one(
        {"_id": account_id}, {"$set": {"role": "admin", "system_role": "ADMIN"}}
    )
    mongo_client.close()

    logout = client.post("/xac-thuc/dang-xuat", headers=bearer)
    assert logout.status_code == 200, logout.text
    assert client.cookies.get("veriq_refresh_token") is None
    assert client.get("/xac-thuc/ca-nhan", headers=bearer).status_code == 401

    admin_login = client.post("/xac-thuc/dang-nhap", data={"username": email, "password": password})
    assert admin_login.status_code == 200, admin_login.text
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['data']['access_token']}"}
    admin_claims = jwt.decode(
        admin_login.json()["data"]["access_token"],
        os.environ["SECRET_KEY"],
        algorithms=["HS256"],
    )
    assert admin_claims["system_role"] == "ADMIN"
    accounts = client.get("/xac-thuc/quan-tri/tai-khoan", headers=admin_headers)
    assert accounts.status_code == 200, accounts.text
    assert managed_id in {row["_id"] for row in accounts.json()["data"]}
    disabled = client.patch(
        f"/xac-thuc/quan-tri/tai-khoan/{managed_id}",
        headers=admin_headers,
        json={"is_active": False, "reason": "Kiểm thử khóa tài khoản có kiểm toán"},
    )
    assert disabled.status_code == 200, disabled.text
    assert disabled.json()["data"]["is_active"] is False
    managed_login = client.post(
        "/xac-thuc/dang-nhap", data={"username": managed_email, "password": managed_password}
    )
    assert managed_login.status_code == 403
    audit = client.get("/xac-thuc/quan-tri/nhat-ky", headers=admin_headers)
    assert audit.status_code == 200, audit.text
    account_updates = [
        event
        for event in audit.json()["data"]
        if event["action"] == "ADMIN_ACCOUNT_UPDATED" and event.get("target_user_id") == managed_id
    ]
    assert account_updates
    assert account_updates[0]["reason"] == "Kiểm thử khóa tài khoản có kiểm toán"

    forgot = client.post("/xac-thuc/quen-mat-khau", json={"email": email})
    assert forgot.status_code == 200, forgot.text
    reset_token = f"reset-{run_id}"
    reset_hash = hmac.new(
        os.environ["SECRET_KEY"].encode("utf-8"), reset_token.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    mongo_client = MongoClient(os.environ["MONGODB_URI"])
    mongo_client[os.environ["AUTHENTICATION_DB_NAME"]].password_reset_tokens.insert_one(
        {
            "_id": f"reset-{run_id}",
            "email": email,
            "token_hash": reset_hash,
            "used": False,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
        }
    )
    mongo_client.close()
    verified = client.post("/xac-thuc/xac-nhan-ma", json={"token": reset_token})
    assert verified.status_code == 200, verified.text
    new_password = f"NewStrongPassword-{run_id}"
    reset = client.post(
        "/xac-thuc/dat-lai-mat-khau", json={"token": reset_token, "new_password": new_password}
    )
    assert reset.status_code == 200, reset.text
    assert (
        client.post(
            "/xac-thuc/dat-lai-mat-khau", json={"token": reset_token, "new_password": password}
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/xac-thuc/dang-nhap", data={"username": email, "password": new_password}
        ).status_code
        == 200
    )

print("authentication core identity integration passed")
