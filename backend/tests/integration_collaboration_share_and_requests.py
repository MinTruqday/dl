import asyncio
import os
import secrets
from datetime import datetime, timezone
import httpx
import jwt
import redis.asyncio as redis_async
from motor.motor_asyncio import AsyncIOMotorClient


async def run():
    suffix = secrets.token_hex(4)
    owner_id = f"owner-{suffix}"
    user_a_id = f"user-a-{suffix}"
    user_b_id = f"user-b-{suffix}"
    user_c_id = f"user-c-{suffix}"

    secret = os.environ["SECRET_KEY"]
    mongo = AsyncIOMotorClient(os.environ["MONGODB_URI"])
    content_db = mongo[os.getenv("CONTENT_DB_NAME", "doclib_content")]
    collaboration_db = mongo[
        os.getenv("COLLABORATION_DB_NAME", "doclib_collaboration")
    ]
    humanity_db = mongo[os.getenv("HUMANITY_DB_NAME", "doclib_humanity")]
    redis_client = redis_async.from_url(os.environ["REDIS_URI"], decode_responses=True)

    def generate_token(user_id, email, role, session_id):
        return jwt.encode(
            {
                "sub": email,
                "uid": user_id,
                "sid": session_id,
                "role": role,
                "permissions": [],
                "ai_tier": "BASIC",
                "exp": datetime.now(timezone.utc).timestamp() + 1800,
            },
            secret,
            algorithm="HS256",
        )

    users = [
        {"_id": owner_id, "email": f"{owner_id}@example.com", "full_name": "Document Owner", "role": "author", "is_active": True},
        {"_id": user_a_id, "email": f"{user_a_id}@example.com", "full_name": "Joiner via Link", "role": "author", "is_active": True},
        {"_id": user_b_id, "email": f"{user_b_id}@example.com", "full_name": "Joiner via Request Accept", "role": "reader", "is_active": True},
        {"_id": user_c_id, "email": f"{user_c_id}@example.com", "full_name": "Joiner via Request Reject", "role": "reader", "is_active": True},
    ]
    await humanity_db.users.insert_many(users)

    sessions = {u["_id"]: f"session-{u['_id']}" for u in users}
    for uid, sid in sessions.items():
        await redis_client.sadd(f"user_sessions:{uid}", sid)

    owner_headers = {"Authorization": f"Bearer {generate_token(owner_id, f'{owner_id}@example.com', 'author', sessions[owner_id])}"}
    user_a_headers = {"Authorization": f"Bearer {generate_token(user_a_id, f'{user_a_id}@example.com', 'author', sessions[user_a_id])}"}
    user_b_headers = {"Authorization": f"Bearer {generate_token(user_b_id, f'{user_b_id}@example.com', 'reader', sessions[user_b_id])}"}
    user_c_headers = {"Authorization": f"Bearer {generate_token(user_c_id, f'{user_c_id}@example.com', 'reader', sessions[user_c_id])}"}

    doc_id = None
    share_token = None
    try:
        async with httpx.AsyncClient(base_url="http://traefik:8000", timeout=15.0) as client:
            create_resp = await client.post(
                "/tai-lieu",
                json={
                    "title": f"Collaborative Document {suffix}",
                    "description": "Doc for share link and request access testing",
                    "visibility": "private",
                },
                headers=owner_headers,
            )
            assert create_resp.status_code == 201, f"Failed to create doc: {create_resp.text}"
            doc_id = create_resp.json()["data"]["_id"]

            config_link_resp = await client.post(
                f"/cong-tac/tai-lieu/{doc_id}/lien-ket-chia-se",
                json={
                    "is_active": True,
                    "password": "SecurePass123",
                    "default_role": "editor",
                    "expires_in_hours": 24,
                },
                headers=owner_headers,
            )
            assert config_link_resp.status_code == 200, f"Configure share link failed: {config_link_resp.text}"
            link_data = config_link_resp.json()["data"]
            share_token = link_data["share_token"]
            assert link_data["is_password_protected"] is True
            assert link_data["default_role"] == "editor"

            get_config_resp = await client.get(
                f"/cong-tac/tai-lieu/{doc_id}/lien-ket-chia-se",
                headers=owner_headers,
            )
            assert get_config_resp.status_code == 200
            assert get_config_resp.json()["data"]["share_token"] == share_token

            info_resp = await client.get(
                f"/cong-tac/thong-tin-lien-ket/{share_token}"
            )
            assert info_resp.status_code == 200
            assert info_resp.json()["data"]["is_password_protected"] is True
            assert info_resp.json()["data"]["document_id"] == doc_id

            join_wrong_pw = await client.post(
                f"/cong-tac/tham-gia-lien-ket/{share_token}",
                json={"password": "WrongPassword"},
                headers=user_a_headers,
            )
            assert join_wrong_pw.status_code == 403, f"Expected 403 but got: {join_wrong_pw.status_code} {join_wrong_pw.text}"

            join_no_pw = await client.post(
                f"/cong-tac/tham-gia-lien-ket/{share_token}",
                json={"password": ""},
                headers=user_a_headers,
            )
            assert join_no_pw.status_code == 400, f"Expected 400 but got: {join_no_pw.status_code} {join_no_pw.text}"

            join_correct = await client.post(
                f"/cong-tac/tham-gia-lien-ket/{share_token}",
                json={"password": "SecurePass123"},
                headers=user_a_headers,
            )
            assert join_correct.status_code == 200, f"Join with correct password failed: {join_correct.text}"
            assert join_correct.json()["data"]["role"] == "editor"

            doc_after_join = await client.get(
                f"/tai-lieu/{doc_id}",
                headers=user_a_headers,
            )
            assert doc_after_join.status_code == 200, f"User A should have draft access: {doc_after_join.text}"

            req_b_resp = await client.post(
                f"/cong-tac/tai-lieu/{doc_id}/xin-quyen",
                json={
                    "requested_role": "commenter",
                    "message": "Xin phep vao doc va gop y",
                },
                headers=user_b_headers,
            )
            assert req_b_resp.status_code == 201, f"User B request failed: {req_b_resp.text}"
            req_b_id = req_b_resp.json()["data"]["request_id"]

            req_list_resp = await client.get(
                f"/cong-tac/tai-lieu/{doc_id}/yeu-cau-xin-quyen",
                headers=owner_headers,
            )
            assert req_list_resp.status_code == 200
            requests_list = req_list_resp.json()["data"]
            assert any(r["id"] == req_b_id for r in requests_list)

            accept_resp = await client.patch(
                f"/cong-tac/yeu-cau-xin-quyen/{req_b_id}",
                json={"status": "ACCEPTED"},
                headers=owner_headers,
            )
            assert accept_resp.status_code == 200, f"Accept request failed: {accept_resp.text}"

            doc_after_accept = await client.get(
                f"/tai-lieu/{doc_id}",
                headers=user_b_headers,
            )
            assert doc_after_accept.status_code == 200, f"User B should have draft access after acceptance: {doc_after_accept.text}"

            req_c_resp = await client.post(
                f"/cong-tac/tai-lieu/{doc_id}/xin-quyen",
                json={
                    "requested_role": "editor",
                    "message": "Cho minh xin lam editor",
                },
                headers=user_c_headers,
            )
            assert req_c_resp.status_code == 201
            req_c_id = req_c_resp.json()["data"]["request_id"]

            reject_resp = await client.patch(
                f"/cong-tac/yeu-cau-xin-quyen/{req_c_id}",
                json={"status": "REJECTED"},
                headers=owner_headers,
            )
            assert reject_resp.status_code == 200

            doc_after_reject = await client.get(
                f"/tai-lieu/{doc_id}",
                headers=user_c_headers,
            )
            assert doc_after_reject.status_code in (403, 404), f"User C should not have draft access after rejection: {doc_after_reject.text}"

            print("ALL COLLABORATION SHARE LINK & ACCESS REQUEST TESTS PASSED!")


    finally:
        for u in users:
            await humanity_db.users.delete_one({"_id": u["_id"]})
            await redis_client.delete(f"user_sessions:{u['_id']}")
        if doc_id:
            await content_db.documents.delete_one({"_id": doc_id})
            await collaboration_db.collaboration_invites.delete_many({"document_id": doc_id})
            await collaboration_db.collaboration_share_links.delete_many({"document_id": doc_id})
            await collaboration_db.collaboration_access_requests.delete_many({"document_id": doc_id})
            await collaboration_db.collaboration_activities.delete_many({"document_id": doc_id})
        await redis_client.aclose()
        mongo.close()


if __name__ == "__main__":
    asyncio.run(run())
