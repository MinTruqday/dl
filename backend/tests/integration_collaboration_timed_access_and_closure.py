import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import jwt
import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorClient


SECRET_KEY = os.environ["SECRET_KEY"]


def token(user_id: str, email: str, session_id: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": email,
            "uid": user_id,
            "sid": session_id,
            "role": "author",
            "iat": now,
            "exp": now + timedelta(minutes=20),
        },
        SECRET_KEY,
        algorithm="HS256",
    )


async def run():
    mongo = AsyncIOMotorClient(os.environ["MONGODB_URI"])
    cache = redis.from_url(os.environ["REDIS_URI"], decode_responses=True)
    humanity = mongo[os.environ.get("HUMANITY_DB_NAME", "doclib_humanity")]
    content = mongo[os.environ.get("CONTENT_DB_NAME", "doclib_content")]
    collaboration = mongo[
        os.environ.get("COLLABORATION_DB_NAME", "doclib_collaboration")
    ]
    owner_id = f"timed-owner-{uuid.uuid4().hex[:8]}"
    editor_id = f"timed-editor-{uuid.uuid4().hex[:8]}"
    owner_session = f"session-{uuid.uuid4()}"
    editor_session = f"session-{uuid.uuid4()}"
    users = [
        {
            "_id": owner_id,
            "email": f"{owner_id}@example.com",
            "full_name": "Timed Owner",
            "role": "author",
            "is_active": True,
        },
        {
            "_id": editor_id,
            "email": f"{editor_id}@example.com",
            "full_name": "Timed Editor",
            "role": "author",
            "is_active": True,
        },
    ]
    await humanity.users.insert_many(users)
    await cache.sadd(f"user_sessions:{owner_id}", owner_session)
    await cache.sadd(f"user_sessions:{editor_id}", editor_session)
    owner_headers = {
        "Authorization": f"Bearer {token(owner_id, users[0]['email'], owner_session)}"
    }
    editor_headers = {
        "Authorization": f"Bearer {token(editor_id, users[1]['email'], editor_session)}"
    }
    document_id = None
    try:
        async with httpx.AsyncClient(
            base_url="http://traefik:8000", timeout=20.0
        ) as client:
            created = await client.post(
                "/tai-lieu",
                json={
                    "title": "Timed collaboration document",
                    "content": "Original content",
                    "content_format": "markdown",
                    "visibility": "private",
                },
                headers=owner_headers,
            )
            assert created.status_code == 201, created.text
            document_id = created.json()["data"]["_id"]
            invited = await client.post(
                "/cong-tac/loi-moi",
                json={
                    "document_id": document_id,
                    "email": users[1]["email"],
                    "role": "editor",
                },
                headers=owner_headers,
            )
            assert invited.status_code == 201, invited.text
            invitation_id = invited.json()["data"]["invite_id"]
            accepted = await client.patch(
                f"/cong-tac/loi-moi/{invitation_id}",
                json={"status": "ACCEPTED"},
                headers=editor_headers,
            )
            assert accepted.status_code == 200, accepted.text
            read_only = await client.post(
                f"/cong-tac/tai-lieu/{document_id}/che-do-truy-cap",
                json={"collaboration_mode": "READ_ONLY"},
                headers=owner_headers,
            )
            assert read_only.status_code == 200, read_only.text
            mode = await client.get(
                f"/cong-tac/tai-lieu/{document_id}/che-do-truy-cap",
                headers=editor_headers,
            )
            assert mode.status_code == 200, mode.text
            assert mode.json()["data"]["effective_status"]["can_edit"] is False
            denied = await client.put(
                f"/tai-lieu/{document_id}/noi-dung",
                json={"content": "Denied edit", "content_format": "markdown"},
                headers=editor_headers,
            )
            assert denied.status_code == 403, denied.text
            owner_edit = await client.put(
                f"/tai-lieu/{document_id}/noi-dung",
                json={"content": "Owner edit", "content_format": "markdown"},
                headers=owner_headers,
            )
            assert owner_edit.status_code == 200, owner_edit.text
            closed = await client.post(
                f"/cong-tac/tai-lieu/{document_id}/che-do-truy-cap",
                json={"collaboration_mode": "CLOSED"},
                headers=owner_headers,
            )
            assert closed.status_code == 200, closed.text
            closed_view = await client.get(
                f"/tai-lieu/{document_id}", headers=editor_headers
            )
            assert closed_view.status_code == 403, closed_view.text
            now = datetime.now(timezone.utc)
            scheduled = await client.post(
                f"/cong-tac/tai-lieu/{document_id}/lich-hen-gio",
                json={
                    "schedules": [
                        {
                            "title": "Active edit window",
                            "start_at": (now - timedelta(minutes=10)).isoformat(),
                            "end_at": (now + timedelta(minutes=50)).isoformat(),
                            "mode": "EDIT",
                            "fallback_mode": "READ_ONLY",
                            "is_active": True,
                        }
                    ]
                },
                headers=owner_headers,
            )
            assert scheduled.status_code == 200, scheduled.text
            schedule = await client.get(
                f"/cong-tac/tai-lieu/{document_id}/lich-hen-gio",
                headers=editor_headers,
            )
            assert schedule.status_code == 200, schedule.text
            assert schedule.json()["data"]["effective_status"]["can_edit"] is True
            allowed = await client.put(
                f"/tai-lieu/{document_id}/noi-dung",
                json={"content": "Scheduled edit", "content_format": "markdown"},
                headers=editor_headers,
            )
            assert allowed.status_code == 200, allowed.text
        print("collaboration timed access integration passed")
    finally:
        if document_id:
            await content.documents.delete_one({"_id": document_id})
            for name in [
                "collaboration_invites",
                "collaboration_activities",
                "collaboration_locks",
            ]:
                await collaboration[name].delete_many({"document_id": document_id})
        await humanity.users.delete_many({"_id": {"$in": [owner_id, editor_id]}})
        await cache.delete(
            f"user_sessions:{owner_id}", f"user_sessions:{editor_id}"
        )
        await cache.aclose()
        mongo.close()


asyncio.run(run())
