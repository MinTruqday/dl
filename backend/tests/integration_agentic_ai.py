import asyncio
import json
import os
import urllib.error
import urllib.request
from unittest.mock import AsyncMock, patch

import jwt

from src.agents.routing import RouteAgent, SemanticRouterValidator
from src.schemas.auth import CurrentUser, Tier
from src.tools.http_client import check_system_access


SECRET_KEY = os.environ["SECRET_KEY"]


class FakeEmbedder:
    async def embed_query(self, text):
        lowered = text.lower()
        if "document" in lowered:
            return [1.0, 0.0, 0.0]
        if "hello" in lowered or "conversational" in lowered or "greeting" in lowered:
            return [0.0, 1.0, 0.0]
        return [0.0, 0.0, 1.0]


class FakeResponse:
    def __init__(self, status_code: int, data: dict):
        self.status_code = status_code
        self._data = data

    def json(self):
        return self._data


def call(method: str, path: str, body=None, internal: bool = False):
    headers = {"Content-Type": "application/json"}
    if internal:
        headers["X-Internal-Token"] = SECRET_KEY
    request = urllib.request.Request(
        f"http://127.0.0.1:8000{path}",
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        raw = error.read()
        return error.code, json.loads(raw) if raw else None


async def main():
    assert call("GET", "/health")[0] == 200
    status, readiness = call("GET", "/ready")
    assert status == 200, readiness
    assert all(value == "ready" for value in readiness["checks"].values())

    user = CurrentUser(_id="agentic-user", email="agentic@example.com")
    assert user.ai_tier is Tier.BASIC
    route_agent = RouteAgent()
    route_agent._get_embedder = lambda: FakeEmbedder()
    route = await route_agent.execute("hello there")
    assert route["route"] == "chat"
    greeting_agent = RouteAgent()
    greeting_agent._get_embedder = lambda: FakeEmbedder()
    greeting = await greeting_agent.execute("hello")
    assert greeting["route"] == "chat" and greeting["answer"] == ""

    validator = SemanticRouterValidator()
    validator._get_embedder = lambda: FakeEmbedder()
    nodes = [{"id": "one", "agent": "Unknown", "task": "search document"}]
    validated = await validator.validate_plan(nodes)
    assert validated[0]["agent"] == "Knowledge"

    admin_token = jwt.encode(
        {"uid": "admin", "sub": "admin@example.com", "role": "admin"},
        SECRET_KEY,
        algorithm="HS256",
    )
    reader_token = jwt.encode(
        {
            "uid": "reader",
            "sub": "reader@example.com",
            "role": "reader",
            "sid": "agentic-integration-session",
            "ai_tier": "BASIC",
        },
        SECRET_KEY,
        algorithm="HS256",
    )
    from src.core.infrastructure.redis import redis
    await redis.sadd("user_sessions:reader", "agentic-integration-session")
    assert check_system_access(f"Bearer {admin_token}") is True
    assert check_system_access(reader_token) is False
    assert check_system_access("invalid") is False

    status, premium_error = call(
        "POST",
        "/suy-luan/kiem-tra-ngu-phap",
        {"text": "DOCLIB_PRIVATE_SENTINEL"},
        internal=False,
    )
    assert status == 401, premium_error

    request = urllib.request.Request(
        "http://127.0.0.1:8000/suy-luan/kiem-tra-ngu-phap",
        data=json.dumps({"text": "DOCLIB_PRIVATE_SENTINEL"}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {reader_token}",
        },
        method="POST",
    )
    try:
        urllib.request.urlopen(request, timeout=30)
        raise AssertionError("Basic account unexpectedly accessed premium grammar check")
    except urllib.error.HTTPError as error:
        premium_error = json.loads(error.read())
        assert error.code == 403, premium_error
        assert premium_error["detail"] == {"code": "premium_tier_required"}

    drm_request = {
        "user_id": "agentic-drm-user",
        "document_id": "agentic-drm-document",
        "client_ip": "10.10.10.10",
        "user_tier": "BASIC",
        "document_type": "standard",
    }
    assert call("POST", "/drm-ai/danh-gia", drm_request)[0] == 403
    status, policy = call(
        "POST",
        "/drm-ai/danh-gia",
        drm_request,
        internal=True,
    )
    assert status == 200, policy
    assert policy["data"]["decision"] in {
        "LEVEL_0",
        "LEVEL_1",
        "LEVEL_2",
        "LEVEL_3",
        "BLOCKED",
    }

    from src.main import app

    schema = app.openapi()
    for path, method in [
        ("/tro-chuyen", "post"),
        ("/tro-chuyen/phat-truc-tiep", "post"),
        ("/tinh-chinh/tap-du-lieu", "post"),
        ("/toi-uu/cau-hinh", "patch"),
        ("/lich-su", "post"),
    ]:
        assert schema["paths"][path][method].get("security")

    from src.tools.editing import edit_document_text

    calls = []

    async def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        if method == "GET":
            return FakeResponse(
                200,
                {
                    "data": {
                        "content_format": "doclib",
                        "content": '{"blocks":[{"type":"paragraph","data":{"text":"old text"}}]}',
                    }
                },
            )
        return FakeResponse(200, {"data": {}})

    with (
        patch(
            "src.tools.http_client.make_api_request",
            side_effect=fake_request,
        ),
        patch(
            "src.tools.editing._broadcast_update",
            new=AsyncMock(),
        ) as broadcast,
    ):
        result = await edit_document_text.ainvoke(
            {
                "document_id": "agentic-edit-document",
                "old_string": "old text",
                "new_string": "new text",
                "replace_all": False,
            },
            config={"configurable": {"token": "Bearer integration"}},
        )
        assert json.loads(result) == {
            "status": "success",
            "document_id": "agentic-edit-document",
        }
        assert [item[0] for item in calls] == ["GET", "PUT"]
        assert calls[1][2]["json"]["content"].find("new text") >= 0
        broadcast.assert_awaited_once()

    print("agentic ai integration passed")


asyncio.run(main())
