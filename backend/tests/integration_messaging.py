import asyncio
import os
import secrets
from datetime import datetime, timezone

import httpx
import jwt
import redis.asyncio as redis_async
from motor.motor_asyncio import AsyncIOMotorClient


async def run():
    suffix = secrets.token_hex(5)
    user_a = f"msg-usera-{suffix}"
    user_b = f"msg-userb-{suffix}"
    group_id = f"group-{suffix}"
    secret = os.environ["SECRET_KEY"]
    mongo = AsyncIOMotorClient(os.environ["MONGODB_URI"])
    db_name = os.getenv("MESSAGING_DB_NAME", "doclib")
    messaging_db = mongo[db_name]
    humanity_db = mongo[os.getenv("HUMANITY_DB_NAME", "doclib_humanity")]
    redis_client = redis_async.from_url(os.environ["REDIS_URI"], decode_responses=True)

    def token(user_id, email, role, session_id):
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

    sessions = {
        user_a: f"session-{user_a}",
        user_b: f"session-{user_b}",
    }
    for user_id, session_id in sessions.items():
        await redis_client.sadd(f"user_sessions:{user_id}", session_id)

    await humanity_db.users.insert_many(
        [
            {"_id": user_a, "email": f"{user_a}@example.com", "full_name": "User Alpha", "slug": user_a, "role": "reader", "is_active": True},
            {"_id": user_b, "email": f"{user_b}@example.com", "full_name": "User Beta", "slug": user_b, "role": "reader", "is_active": True},
        ]
    )

    headers_a = {"Authorization": f"Bearer {token(user_a, f'{user_a}@example.com', 'reader', sessions[user_a])}"}
    headers_b = {"Authorization": f"Bearer {token(user_b, f'{user_b}@example.com', 'reader', sessions[user_b])}"}

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            send_res = await client.post(
                "http://messaging:8000/tin-nhan/",
                json={"receiver_id": user_b, "content": "Xin chao tu Alpha"},
                headers=headers_a,
            )
            assert send_res.status_code == 201, send_res.text
            msg_data = send_res.json()["data"]
            msg_id = msg_data["_id"]

            edit_res = await client.put(
                f"http://messaging:8000/tin-nhan/{msg_id}",
                json={"content": "Xin chao tu Alpha cap nhat"},
                headers=headers_a,
            )
            assert edit_res.status_code == 200, edit_res.text
            assert edit_res.json()["data"]["is_edited"] is True

            pin_res = await client.post(
                f"http://messaging:8000/tin-nhan/{msg_id}/ghim",
                headers=headers_a,
            )
            assert pin_res.status_code == 200, pin_res.text

            search_res = await client.get(
                f"http://messaging:8000/tin-nhan/{user_b}/tim-kiem",
                params={"q": "Alpha"},
                headers=headers_a,
            )
            assert search_res.status_code == 200, search_res.text

            forward_res = await client.post(
                "http://messaging:8000/tin-nhan/chuyen-tiep",
                json={"message_id": msg_id, "receiver_ids": [user_b]},
                headers=headers_a,
            )
            assert forward_res.status_code == 200, forward_res.text

            poll_res = await client.post(
                "http://messaging:8000/tin-nhan/binh-chon",
                json={"receiver_id": user_b, "question": "Ban chon gi", "options": ["Option 1", "Option 2"]},
                headers=headers_a,
            )
            assert poll_res.status_code == 201, poll_res.text
            poll_msg_id = poll_res.json()["data"]["_id"]

            vote_res = await client.post(
                f"http://messaging:8000/tin-nhan/binh-chon/{poll_msg_id}/bo-phieu",
                json={"option_id": "opt_0"},
                headers=headers_b,
            )
            assert vote_res.status_code == 200, vote_res.text

            unread_res = await client.post(
                f"http://messaging:8000/tin-nhan/{user_a}/danh-dau-chua-doc",
                headers=headers_b,
            )
            assert unread_res.status_code == 200, unread_res.text

            disappear_res = await client.post(
                f"http://messaging:8000/tin-nhan/{user_b}/tu-xoa",
                json={"timer_seconds": 86400},
                headers=headers_a,
            )
            assert disappear_res.status_code == 200, disappear_res.text

            set_pin_res = await client.post(
                f"http://messaging:8000/tin-nhan/{user_b}/an-tin-nhan",
                json={"pin_code": "1234"},
                headers=headers_a,
            )
            assert set_pin_res.status_code == 200, set_pin_res.text
            participant_key = f"{min(user_a, user_b)}_{max(user_a, user_b)}"
            locked = await messaging_db.conversations.find_one(
                {"_id": participant_key}
            )
            assert "hidden_pin" not in locked or user_a not in locked["hidden_pin"]
            assert locked["hidden_pin_hash"][user_a] != "1234"
            for _ in range(5):
                invalid_pin_res = await client.post(
                    f"http://messaging:8000/tin-nhan/{user_b}/xac-thuc-pin",
                    json={"pin_code": "9999"},
                    headers=headers_a,
                )
                assert invalid_pin_res.status_code == 401, invalid_pin_res.text
            limited_pin_res = await client.post(
                f"http://messaging:8000/tin-nhan/{user_b}/xac-thuc-pin",
                json={"pin_code": "1234"},
                headers=headers_a,
            )
            assert limited_pin_res.status_code == 429, limited_pin_res.text
            await redis_client.delete(
                f"messaging:pin-attempts:{user_a}:{participant_key}"
            )
            valid_pin_res = await client.post(
                f"http://messaging:8000/tin-nhan/{user_b}/xac-thuc-pin",
                json={"pin_code": "1234"},
                headers=headers_a,
            )
            assert valid_pin_res.status_code == 200, valid_pin_res.text
            remove_pin_res = await client.post(
                f"http://messaging:8000/tin-nhan/{user_b}/xoa-ma-pin",
                json={"pin_code": "1234"},
                headers=headers_a,
            )
            assert remove_pin_res.status_code == 200, remove_pin_res.text

            recall_res = await client.delete(
                f"http://messaging:8000/tin-nhan/{msg_id}",
                headers=headers_a,
            )
            assert recall_res.status_code == 200, recall_res.text
            assert recall_res.json()["data"]["is_recalled"] is True

            print("messaging integration passed")
    finally:
        await messaging_db.messages.delete_many(
            {
                "$or": [
                    {"sender_id": {"$in": [user_a, user_b]}},
                    {"receiver_id": {"$in": [user_a, user_b]}},
                ]
            }
        )
        await messaging_db.conversations.delete_many(
            {"participants": {"$in": [user_a, user_b]}}
        )
        await messaging_db.conversations.delete_one(
            {"_id": f"{min(user_a, user_b)}_{max(user_a, user_b)}"}
        )
        await humanity_db.users.delete_many({"_id": {"$in": [user_a, user_b]}})
        for user_id in sessions:
            await redis_client.delete(f"user_sessions:{user_id}")
        await redis_client.aclose()
        mongo.close()


asyncio.run(run())
