import asyncio
import base64
import json
import os
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
import websockets


BASE_HTTP = os.getenv("WEBSOCKET_TEST_HTTP", "http://127.0.0.1:8000")
BASE_WS = os.getenv("WEBSOCKET_TEST_WS", "ws://127.0.0.1:8000")
OWNER_ID = f"websocket-owner-{uuid.uuid4()}"
CONTACT_ID = f"websocket-contact-{uuid.uuid4()}"
OUTSIDER_ID = f"websocket-outsider-{uuid.uuid4()}"
OWNER_SESSION = str(uuid.uuid4())
CONTACT_SESSION = str(uuid.uuid4())
OUTSIDER_SESSION = str(uuid.uuid4())
DOCUMENT_ID = f"websocket-document-{uuid.uuid4()}"
SECRET_KEY = os.environ["SECRET_KEY"]


def token(user_id, session_id, role="reader"):
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": f"{user_id}@doclib.local",
            "uid": user_id,
            "sid": session_id,
            "role": role,
            "iat": now,
            "exp": now + timedelta(minutes=15),
        },
        SECRET_KEY,
        algorithm="HS256",
    )


def call(method, path, body=None, internal=False):
    headers = {"Content-Type": "application/json"}
    if internal:
        headers["X-Internal-Token"] = SECRET_KEY
    request = urllib.request.Request(
        f"{BASE_HTTP}{path}",
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


async def rejected(uri, protocols=None):
    try:
        async with websockets.connect(uri, subprotocols=protocols):
            return False
    except Exception:
        return True


async def receive_json(socket, timeout=5):
    return json.loads(await asyncio.wait_for(socket.recv(), timeout))


async def main():
    mongo = AsyncIOMotorClient(os.environ["MONGODB_URI"])
    cache = redis.from_url(os.environ["REDIS_URI"], decode_responses=True)
    content = mongo[os.getenv("CONTENT_DB_NAME", "doclib_content")]
    messaging = mongo[os.getenv("MESSAGING_DB_NAME", "doclib_messaging")]
    owner_token = token(OWNER_ID, OWNER_SESSION, "author")
    contact_token = token(CONTACT_ID, CONTACT_SESSION)
    outsider_token = token(OUTSIDER_ID, OUTSIDER_SESSION)
    conversation_id = f"websocket-conversation-{uuid.uuid4()}"
    sockets = []
    try:
        await cache.sadd(f"user_sessions:{OWNER_ID}", OWNER_SESSION)
        await cache.sadd(f"user_sessions:{CONTACT_ID}", CONTACT_SESSION)
        await cache.sadd(f"user_sessions:{OUTSIDER_ID}", OUTSIDER_SESSION)
        await content.documents.insert_one(
            {
                "_id": DOCUMENT_ID,
                "slug": f"websocket-integration-{uuid.uuid4()}",
                "title": "WebSocket Integration",
                "creator_id": OWNER_ID,
                "coauthors": [CONTACT_ID],
                "visibility": "private",
                "status": "draft",
                "created_at": datetime.now(timezone.utc),
            }
        )
        await messaging.conversations.insert_one(
            {
                "_id": conversation_id,
                "participant_key": f"{min(OWNER_ID, CONTACT_ID)}_{max(OWNER_ID, CONTACT_ID)}",
                "participants": [OWNER_ID, CONTACT_ID],
                "updated_at": datetime.now(timezone.utc),
            }
        )

        assert call("GET", "/ready")[0] == 200
        assert await rejected(f"{BASE_WS}/ws/{OWNER_ID}")
        assert await rejected(
            f"{BASE_WS}/ws/{OWNER_ID}",
            ["doclib", outsider_token],
        )
        assert await rejected(
            f"{BASE_WS}/ws/crdt/{DOCUMENT_ID}",
            ["doclib", outsider_token],
        )

        owner_message = await websockets.connect(
            f"{BASE_WS}/ws/{OWNER_ID}",
            subprotocols=["doclib", owner_token],
        )
        contact_message = await websockets.connect(
            f"{BASE_WS}/ws/{CONTACT_ID}",
            subprotocols=["doclib", contact_token],
        )
        sockets.extend([owner_message, contact_message])
        assert owner_message.subprotocol == "doclib"
        await owner_message.send(json.dumps({"action": "ping"}))
        assert (await receive_json(owner_message))["type"] == "pong"
        await owner_message.send("{invalid")
        assert (await receive_json(owner_message))["data"]["code"] == "invalid_json"
        await owner_message.send(
            json.dumps(
                {
                    "action": "typing_start",
                    "data": {"receiver_id": CONTACT_ID},
                }
            )
        )
        typing = await receive_json(contact_message)
        assert typing["type"] == "typing_start"
        assert typing["data"]["sender_id"] == OWNER_ID
        await owner_message.send(
            json.dumps(
                {
                    "action": "check_online",
                    "data": {"user_ids": [CONTACT_ID, OUTSIDER_ID]},
                }
            )
        )
        online = await receive_json(owner_message)
        assert online["type"] == "online_status"
        assert online["data"] == {CONTACT_ID: True}
        await cache.publish(
            f"message_delivery:{OWNER_ID}",
            json.dumps({"type": "integration_delivery", "data": {"value": 1}}),
        )
        delivered = await receive_json(owner_message)
        assert delivered["type"] == "integration_delivery"

        owner_crdt = await websockets.connect(
            f"{BASE_WS}/ws/crdt/{DOCUMENT_ID}",
            subprotocols=["doclib", owner_token],
        )
        contact_crdt = await websockets.connect(
            f"{BASE_WS}/ws/crdt/{DOCUMENT_ID}",
            subprotocols=["doclib", contact_token],
        )
        sockets.extend([owner_crdt, contact_crdt])
        frame = json.dumps({"type": "DOCUMENT_UPDATED", "content": "local"})
        await owner_crdt.send(frame)
        assert await asyncio.wait_for(contact_crdt.recv(), 5) == frame
        remote_frame = json.dumps({"type": "DOCUMENT_UPDATED", "content": "redis"})
        await cache.publish(
            f"composition_delivery:{DOCUMENT_ID}",
            json.dumps(
                {
                    "origin": "integration-instance",
                    "text": True,
                    "data": base64.b64encode(remote_frame.encode()).decode(),
                }
            ),
        )
        assert await asyncio.wait_for(owner_crdt.recv(), 5) == remote_frame
        assert call(
            "POST",
            "/ws/internal/broadcast",
            {"document_id": DOCUMENT_ID, "message": {"type": "blocked"}},
        )[0] == 403
        status, result = call(
            "POST",
            "/ws/internal/broadcast",
            {
                "document_id": DOCUMENT_ID,
                "message": {"type": "DOCUMENT_UPDATED", "content": "internal"},
            },
            internal=True,
        )
        assert status == 200 and result["status"] == "success"
        internal = await receive_json(owner_crdt)
        assert internal["content"] == "internal"

        await cache.srem(f"user_sessions:{OWNER_ID}", OWNER_SESSION)
        await owner_message.send(json.dumps({"action": "ping"}))
        revoked = False
        try:
            await asyncio.wait_for(owner_message.recv(), 5)
        except websockets.ConnectionClosed:
            revoked = True
        assert revoked
        print("websocket integration passed")
    finally:
        for socket in sockets:
            try:
                await socket.close()
            except Exception:
                continue
        await content.documents.delete_many({"_id": DOCUMENT_ID})
        await messaging.conversations.delete_many({"_id": conversation_id})
        keys = [
            f"user_sessions:{OWNER_ID}",
            f"user_sessions:{CONTACT_ID}",
            f"user_sessions:{OUTSIDER_ID}",
            f"user_online:{OWNER_ID}",
            f"user_online:{CONTACT_ID}",
            f"user_online:{OUTSIDER_ID}",
            f"user_last_active:{OWNER_ID}",
            f"user_last_active:{CONTACT_ID}",
            f"user_last_active:{OUTSIDER_ID}",
            f"ws_ban:{OWNER_ID}",
            f"ws_ban:{CONTACT_ID}",
            f"ws_ban:{OUTSIDER_ID}",
        ]
        async for key in cache.scan_iter(match="ws_presence:websocket-*"):
            keys.append(key)
        await cache.delete(*keys)
        await cache.aclose()
        mongo.close()


asyncio.run(main())
