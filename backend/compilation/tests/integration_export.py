import asyncio
import os
import time
from uuid import uuid4

import httpx
import jwt
import redis.asyncio as aioredis
from motor.motor_asyncio import AsyncIOMotorClient


def token(user_id, role, session_id):
    return jwt.encode(
        {
            "uid": user_id,
            "sub": f"{user_id}@test.local",
            "sid": session_id,
            "role": role,
            "exp": int(time.time()) + 600,
        },
        os.environ["SECRET_KEY"],
        algorithm="HS256",
    )


async def main():
    run_id = uuid4().hex
    teacher_id = f"teacher-export-{run_id}"
    student_id = f"student-export-{run_id}"
    admin_id = f"admin-export-{run_id}"
    version_id = f"ASM-export-{run_id}-v1"
    question_id = f"Q-export-{run_id}-v1"
    mongo = AsyncIOMotorClient(os.environ["MONGODB_URI"])
    database = mongo[os.getenv("ASSESSMENT_DB_NAME", "assessment")]
    cache = aioredis.from_url(os.environ["REDIS_URI"], decode_responses=True)
    sessions = {
        teacher_id: f"session-teacher-{run_id}",
        student_id: f"session-student-{run_id}",
        admin_id: f"session-admin-{run_id}",
    }
    for user_id, session_id in sessions.items():
        await cache.sadd(f"user_sessions:{user_id}", session_id)
    await database.question_versions.insert_one(
        {
            "_id": question_id,
            "question_id": f"Q-export-{run_id}",
            "version": 1,
            "owner_id": teacher_id,
            "question_type": "single_choice",
            "stem_doc": {
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Hai cộng hai bằng bao nhiêu"}],
                    }
                ],
            },
            "options": [
                {
                    "id": "A",
                    "content_doc": {"type": "doc", "content": [{"type": "text", "text": "Ba"}]},
                },
                {
                    "id": "B",
                    "content_doc": {"type": "doc", "content": [{"type": "text", "text": "Bốn"}]},
                },
            ],
            "answer_key": {"option_id": "B"},
        }
    )
    await database.assessment_versions.insert_one(
        {
            "_id": version_id,
            "assessment_id": f"ASM-export-{run_id}",
            "version": 1,
            "owner_id": teacher_id,
            "title": "Đề kiểm tra Toán",
            "items": [{"question_version_id": question_id, "position": 1, "points": 1}],
        }
    )
    headers = {
        user_id: {"Authorization": f"Bearer {token(user_id, role, sessions[user_id])}"}
        for user_id, role in [(teacher_id, "author"), (student_id, "reader"), (admin_id, "admin")]
    }
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=30) as client:
        pdf = await client.post(
            f"/exports/assessment/{version_id}/pdf", headers=headers[teacher_id]
        )
        assert pdf.status_code == 200, pdf.text
        assert pdf.content.startswith(b"%PDF")
        assert pdf.headers["content-type"].startswith("application/pdf")
        docx = await client.post(
            f"/exports/assessment/{version_id}/docx", headers=headers[teacher_id]
        )
        assert docx.status_code == 200, docx.text
        assert docx.content.startswith(b"PK")
        forbidden = await client.post(
            f"/exports/assessment/{version_id}/pdf", headers=headers[student_id]
        )
        assert forbidden.status_code == 403
        admin = await client.post(
            f"/exports/assessment/{version_id}/pdf", headers=headers[admin_id]
        )
        assert admin.status_code == 200, admin.text
    await database.assessment_versions.delete_one({"_id": version_id})
    await database.question_versions.delete_one({"_id": question_id})
    for user_id, session_id in sessions.items():
        await cache.srem(f"user_sessions:{user_id}", session_id)
    await cache.aclose()
    mongo.close()


asyncio.run(main())

print("compilation export integration passed")
