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
    editor_id = f"editor-{suffix}"
    commenter_id = f"commenter-{suffix}"
    viewer_id = f"viewer-{suffix}"

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
        {"_id": owner_id, "email": f"{owner_id}@example.com", "full_name": "Doc Owner", "role": "author", "is_active": True},
        {"_id": editor_id, "email": f"{editor_id}@example.com", "full_name": "Doc Editor", "role": "author", "is_active": True},
        {"_id": commenter_id, "email": f"{commenter_id}@example.com", "full_name": "Doc Commenter", "role": "reader", "is_active": True},
        {"_id": viewer_id, "email": f"{viewer_id}@example.com", "full_name": "Doc Viewer", "role": "reader", "is_active": True},
    ]
    await humanity_db.users.insert_many(users)

    sessions = {u["_id"]: f"session-{u['_id']}" for u in users}
    for uid, sid in sessions.items():
        await redis_client.sadd(f"user_sessions:{uid}", sid)

    owner_headers = {"Authorization": f"Bearer {generate_token(owner_id, f'{owner_id}@example.com', 'author', sessions[owner_id])}"}
    editor_headers = {"Authorization": f"Bearer {generate_token(editor_id, f'{editor_id}@example.com', 'author', sessions[editor_id])}"}
    commenter_headers = {"Authorization": f"Bearer {generate_token(commenter_id, f'{commenter_id}@example.com', 'reader', sessions[commenter_id])}"}
    viewer_headers = {"Authorization": f"Bearer {generate_token(viewer_id, f'{viewer_id}@example.com', 'reader', sessions[viewer_id])}"}

    doc_id = None
    try:
        async with httpx.AsyncClient(base_url="http://traefik:8000", timeout=15.0) as client:
            create_resp = await client.post(
                "/tai-lieu",
                json={
                    "title": "Collab Roles Document",
                    "content": "Initial content from owner",
                    "content_format": "markdown",
                    "price_dl": 0,
                    "preview_pages": 1,
                    "visibility": "private",
                },
                headers=owner_headers,
            )
            assert create_resp.status_code == 201, create_resp.text
            doc_id = create_resp.json()["data"]["_id"]

            invite_commenter = await client.post(
                "/cong-tac/loi-moi",
                json={"document_id": doc_id, "email": f"{commenter_id}@example.com", "role": "commenter"},
                headers=owner_headers,
            )
            assert invite_commenter.status_code == 201, invite_commenter.text
            commenter_invite_id = invite_commenter.json()["data"]["invite_id"]

            accept_commenter = await client.patch(
                f"/cong-tac/loi-moi/{commenter_invite_id}",
                json={"status": "ACCEPTED"},
                headers=commenter_headers,
            )
            assert accept_commenter.status_code == 200, accept_commenter.text

            invite_editor = await client.post(
                "/cong-tac/loi-moi",
                json={"document_id": doc_id, "email": f"{editor_id}@example.com", "role": "editor"},
                headers=owner_headers,
            )
            assert invite_editor.status_code == 201, invite_editor.text
            editor_invite_id = invite_editor.json()["data"]["invite_id"]

            accept_editor = await client.patch(
                f"/cong-tac/loi-moi/{editor_invite_id}",
                json={"status": "ACCEPTED"},
                headers=editor_headers,
            )
            assert accept_editor.status_code == 200, accept_editor.text

            read_commenter = await client.get(f"/tai-lieu/{doc_id}", headers=commenter_headers)
            assert read_commenter.status_code == 200, read_commenter.text

            update_commenter = await client.put(
                f"/tai-lieu/{doc_id}/noi-dung",
                json={"content": "Hacked content by commenter", "content_format": "markdown"},
                headers=commenter_headers,
            )
            assert update_commenter.status_code == 403, f"Expected 403 for commenter update but got {update_commenter.status_code}: {update_commenter.text}"

            update_editor = await client.put(
                f"/tai-lieu/{doc_id}/noi-dung",
                json={"content": "Content updated by legit editor", "content_format": "markdown"},
                headers=editor_headers,
            )
            assert update_editor.status_code == 200, update_editor.text

            snapshot = await client.post(
                f"/cong-tac/tai-lieu/{doc_id}/phien-ban",
                json={"version_name": "integration"},
                headers=editor_headers,
            )
            assert snapshot.status_code == 201, snapshot.text
            snapshot_data = snapshot.json()["data"]["snapshot"]
            assert snapshot_data["content"] == "Content updated by legit editor"
            assert snapshot_data["created_by"] == ""

            task = await client.post(
                f"/cong-tac/tai-lieu/{doc_id}/cong-viec",
                json={"task_desc": "integration task", "assigned_to": editor_id},
                headers=owner_headers,
            )
            assert task.status_code == 201, task.text
            task_id = task.json()["data"]["task"]["_id"]
            task_comment = await client.post(
                f"/cong-tac/nhiem-vu/{task_id}/binh-luan",
                json={"comment_text": "integration comment"},
                headers=editor_headers,
            )
            assert task_comment.status_code == 201, task_comment.text
            assert task_comment.json()["data"]["comment"]["sender_name"] == ""

            invite_viewer = await client.post(
                "/cong-tac/loi-moi",
                json={"document_id": doc_id, "email": f"{viewer_id}@example.com", "role": "viewer"},
                headers=owner_headers,
            )
            assert invite_viewer.status_code == 201, invite_viewer.text
            viewer_invite_id = invite_viewer.json()["data"]["invite_id"]

            accept_viewer = await client.patch(
                f"/cong-tac/loi-moi/{viewer_invite_id}",
                json={"status": "ACCEPTED"},
                headers=viewer_headers,
            )
            assert accept_viewer.status_code == 200, accept_viewer.text

            update_viewer = await client.put(
                f"/tai-lieu/{doc_id}/noi-dung",
                json={"content": "Content edited by viewer", "content_format": "markdown"},
                headers=viewer_headers,
            )
            assert update_viewer.status_code == 403, f"Expected 403 for viewer update but got {update_viewer.status_code}: {update_viewer.text}"

            update_role = await client.patch(
                f"/cong-tac/{viewer_invite_id}/vai-tro",
                json={"role": "editor"},
                headers=owner_headers,
            )
            assert update_role.status_code == 200, update_role.text

            update_promoted = await client.put(
                f"/tai-lieu/{doc_id}/noi-dung",
                json={"content": "Content successfully edited after promotion to editor", "content_format": "markdown"},
                headers=viewer_headers,
            )
            assert update_promoted.status_code == 200, update_promoted.text

            lock_resp = await client.post(
                f"/cong-tac/tai-lieu/{doc_id}/khoa",
                headers=editor_headers,
            )
            assert lock_resp.status_code == 200, lock_resp.text

            status_resp = await client.get(
                f"/cong-tac/tai-lieu/{doc_id}/trang-thai-khoa",
                headers=editor_headers,
            )
            assert status_resp.status_code == 200, status_resp.text
            assert status_resp.json()["data"]["is_locked"] is True

            lock_conflict = await client.post(
                f"/cong-tac/tai-lieu/{doc_id}/khoa",
                headers=viewer_headers,
            )
            assert lock_conflict.status_code == 400, lock_conflict.text

            unlock_resp = await client.post(
                f"/cong-tac/tai-lieu/{doc_id}/mo-khoa",
                headers=editor_headers,
            )
            assert unlock_resp.status_code == 200, unlock_resp.text

            status_unlocked = await client.get(
                f"/cong-tac/tai-lieu/{doc_id}/trang-thai-khoa",
                headers=editor_headers,
            )
            assert status_unlocked.status_code == 200, status_unlocked.text
            assert status_unlocked.json()["data"]["is_locked"] is False

            collaborators = await client.get(
                f"/cong-tac/tai-lieu/{doc_id}",
                headers=owner_headers,
            )
            assert collaborators.status_code == 200, collaborators.text
            collaborator_rows = collaborators.json()["data"]
            commenter_row = next(
                row for row in collaborator_rows if row["user_id"] == commenter_id
            )
            assert commenter_row["_id"] == commenter_invite_id
            assert commenter_row["collaboration_id"] == commenter_invite_id
            remove_commenter = await client.delete(
                f"/cong-tac/{commenter_invite_id}",
                headers=owner_headers,
            )
            assert remove_commenter.status_code == 200, remove_commenter.text
            assert await collaboration_db.collaboration_invites.find_one(
                {"_id": commenter_invite_id}
            ) is None
            denied_after_removal = await client.get(
                f"/tai-lieu/{doc_id}",
                headers=commenter_headers,
            )
            assert denied_after_removal.status_code in {403, 404}, denied_after_removal.text

            print("collaboration roles integration test passed")
    finally:
        await humanity_db.users.delete_many({"_id": {"$in": [u["_id"] for u in users]}})
        for uid in sessions:
            await redis_client.delete(f"user_sessions:{uid}")
        if doc_id:
            await content_db.documents.delete_one({"_id": doc_id})
            await collaboration_db.collaboration_invites.delete_many({"document_id": doc_id})
            await collaboration_db.collaboration_locks.delete_many({"document_id": doc_id})
            await collaboration_db.collaboration_drafts.delete_many({"document_id": doc_id})
            await collaboration_db.collaboration_memos.delete_many({"document_id": doc_id})
            task_ids = [
                row["_id"]
                async for row in collaboration_db.collaboration_tasks.find(
                    {"document_id": doc_id}, {"_id": 1}
                )
            ]
            await collaboration_db.collaboration_tasks.delete_many({"document_id": doc_id})
            await collaboration_db.collaboration_task_comments.delete_many(
                {"task_id": {"$in": task_ids}}
            )
        mongo.close()
        await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(run())
