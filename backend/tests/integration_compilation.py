import asyncio
import json
import os
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis


BASE_URL = os.getenv("COMPILATION_TEST_URL", "http://127.0.0.1:8000")
OWNER_ID = f"compilation-owner-{uuid.uuid4()}"
OUTSIDER_ID = f"compilation-outsider-{uuid.uuid4()}"
OWNER_SESSION = str(uuid.uuid4())
OUTSIDER_SESSION = str(uuid.uuid4())
DOCUMENT_ID = f"compilation-document-{uuid.uuid4()}"
SECRET_KEY = os.environ["SECRET_KEY"]


def token(user_id, session_id, role):
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": f"{user_id}@doclib.local",
            "uid": user_id,
            "sid": session_id,
            "role": role,
            "full_name": user_id,
            "iat": now,
            "exp": now + timedelta(minutes=15),
        },
        SECRET_KEY,
        algorithm="HS256",
    )


def call(method, path, bearer=None, body=None, timeout=45):
    headers = {"Content-Type": "application/json"}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content = response.read()
            content_type = response.headers.get_content_type()
            payload = json.loads(content) if content_type == "application/json" else content
            return response.status, payload, content_type
    except urllib.error.HTTPError as error:
        content = error.read()
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            payload = content.decode("utf-8", errors="replace")
        return error.code, payload, error.headers.get_content_type()


async def main():
    mongo = AsyncIOMotorClient(os.environ["MONGODB_URI"])
    cache = redis.from_url(os.environ["REDIS_URI"], decode_responses=True)
    content = mongo[os.getenv("CONTENT_DB_NAME", "doclib_content")]
    compilation = mongo[os.getenv("COMPILATION_DB_NAME", "doclib_compilation")]
    owner_token = token(OWNER_ID, OWNER_SESSION, "author")
    outsider_token = token(OUTSIDER_ID, OUTSIDER_SESSION, "reader")
    version_a = f"compilation-version-{uuid.uuid4()}"
    version_b = f"compilation-version-{uuid.uuid4()}"
    latex = "\\documentclass{article}\\begin{document}DocLib integration\\end{document}"
    editor = json.dumps(
        {
            "blocks": [
                {
                    "id": "heading",
                    "type": "header",
                    "data": {"text": "DocLib Integration", "level": 1},
                },
                {
                    "id": "body",
                    "type": "paragraph",
                    "data": {"text": "Original integration content"},
                },
            ]
        }
    )
    try:
        await cache.sadd(f"user_sessions:{OWNER_ID}", OWNER_SESSION)
        await cache.sadd(f"user_sessions:{OUTSIDER_ID}", OUTSIDER_SESSION)
        await content.documents.insert_one(
            {
                "_id": DOCUMENT_ID,
                "slug": f"compilation-integration-{uuid.uuid4()}",
                "title": "Original integration title",
                "description": "Original integration description",
                "content": json.loads(editor),
                "creator_id": OWNER_ID,
                "coauthors": [],
                "visibility": "private",
                "status": "draft",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
        )
        await content.document_versions.insert_many(
            [
                {
                    "_id": version_a,
                    "document_id": DOCUMENT_ID,
                    "snapshot": {"content": {"blocks": [{"data": {"text": "A"}}]}},
                    "created_at": datetime.now(timezone.utc),
                },
                {
                    "_id": version_b,
                    "document_id": DOCUMENT_ID,
                    "snapshot": {"content": {"blocks": [{"data": {"text": "B"}}]}},
                    "created_at": datetime.now(timezone.utc),
                },
            ]
        )

        assert call("GET", "/ready")[0] == 200
        assert call("GET", "/soan-thao/latex/ban-nhap")[0] == 401
        status, payload, media = call(
            "GET",
            "/soan-thao/latex/ban-nhap",
            owner_token,
        )
        assert status == 200 and payload["data"]["content"] is None, payload
        status, payload, media = call(
            "POST",
            "/soan-thao/latex/tu-dong-luu",
            owner_token,
            {"content": latex},
        )
        assert status == 200, payload
        status, payload, media = call(
            "GET",
            "/soan-thao/latex/ban-nhap",
            owner_token,
        )
        assert status == 200 and payload["data"]["content"] == latex, payload
        updated_latex = latex.replace("integration", "updated integration")
        status, payload, media = call(
            "POST",
            "/soan-thao/latex/tu-dong-luu",
            owner_token,
            {"content": updated_latex},
        )
        assert status == 200, payload
        status, payload, media = call(
            "GET",
            "/soan-thao/latex/ban-nhap",
            owner_token,
        )
        assert status == 200 and payload["data"]["content"] == updated_latex, payload
        assert call(
            "DELETE",
            "/soan-thao/latex/don-dep",
            owner_token,
        )[0] == 200
        status, payload, media = call(
            "GET",
            "/soan-thao/latex/ban-nhap",
            owner_token,
        )
        assert status == 200 and payload["data"]["content"] is None, payload
        from src.engines.editorjs import EditorjsEngine
        from src.engines.editorjs_capabilities import capability_manifest
        manifest = capability_manifest()
        assert len(manifest["features"]) == 2449
        assert manifest["microsoftInteractiveControlCount"] == 2005
        assert call(
            "GET",
            "/soan-thao/editorjs/capabilities",
        )[0] == 401
        status, payload, media = call(
            "GET",
            "/soan-thao/editorjs/capabilities?query=Copy&limit=10",
            owner_token,
        )
        assert status == 200 and payload["total"] > 0, payload
        copy_capability = next(
            item
            for item in payload["items"]
            if item["id"] == "DocLibCopy"
        )
        assert copy_capability["toolKey"] == "copy"
        assert copy_capability["mode"] == "Copy"
        assert copy_capability["product"] == "doclib"
        command_content = json.dumps(
            {
                "blocks": [
                    {
                        "type": "copy",
                        "data": {
                            "feature": "DocLibCopy",
                            "mode": "Copy",
                            "applied": True,
                        },
                    }
                ]
            }
        )
        assert EditorjsEngine._parse_content(command_content)[0]["type"] == "copy"
        invalid_command_content = json.dumps(
            {
                "blocks": [
                    {
                        "type": "copy",
                        "data": {
                            "feature": "DocLibCut",
                            "mode": "Copy",
                            "applied": True,
                        },
                    }
                ]
            }
        )
        try:
            EditorjsEngine._parse_content(invalid_command_content)
            raise AssertionError("Invalid command capability accepted")
        except ValueError:
            pass
        assert EditorjsEngine._safe_image_url("http://mongodb:27017/private") == ""
        assert EditorjsEngine._safe_link_url('javascript:alert("unsafe")') == ""
        rendered = EditorjsEngine._render_block(
            {
                "type": "image",
                "data": {
                    "url": "data:image/png;base64,AA==",
                    "caption": 'unsafe" onerror="alert(1)',
                },
            }
        )
        assert 'alt="unsafe" onerror=' not in rendered
        field_rendered = EditorjsEngine._render_block(
            {"type": "field", "data": {"code": "PAGE_COUNT"}}
        )
        assert "PAGE_COUNT" in field_rendered
        ole_rendered = EditorjsEngine._render_block(
            {"type": "oleObject", "data": {"objectId": "object-42"}}
        )
        assert "object-42" in ole_rendered
        sparkline_rendered = EditorjsEngine._render_block(
            {"type": "sparklines", "data": {"values": "1, 4, 2, 8"}}
        )
        assert "<polyline" in sparkline_rendered and "points=" in sparkline_rendered
        assert EditorjsEngine._render_block(
            {"type": "sparklines", "data": {"values": "invalid"}}
        ) == ""
        assert call("POST", "/soan-thao/latex/bien-dich", body={"content": latex})[0] == 401
        status, payload, media = call(
            "POST",
            "/soan-thao/latex/bien-dich",
            owner_token,
            {"content": "\\input{/etc/passwd}"},
        )
        assert status == 400, payload
        status, payload, media = call(
            "POST",
            "/soan-thao/latex/bien-dich",
            owner_token,
            {"content": latex},
        )
        assert status == 200 and media == "application/pdf" and payload.startswith(b"%PDF"), (status, media)
        status, payload, media = call(
            "POST",
            "/soan-thao/editorjs/bien-dich",
            owner_token,
            {"content": editor},
        )
        assert status == 200 and media == "application/pdf" and payload.startswith(b"%PDF"), (status, media)
        status, payload, media = call(
            "POST",
            "/soan-thao/editorjs/ket-xuat/docx",
            owner_token,
            {"content": editor},
        )
        assert status == 200 and payload.startswith(b"PK"), (status, media)
        assert call(
            "POST",
            "/soan-thao/editorjs/ket-xuat/executable",
            owner_token,
            {"content": editor},
        )[0] == 400

        status, payload, media = call(
            "POST",
            f"/soan-thao/{DOCUMENT_ID}/tu-dong-luu",
            outsider_token,
            {"content": json.loads(editor)},
        )
        assert status == 404, payload
        status, payload, media = call(
            "POST",
            f"/soan-thao/{DOCUMENT_ID}/tu-dong-luu",
            owner_token,
            {"content": json.loads(editor)},
        )
        assert status == 200 and payload["status"] == 200, payload
        stored = await content.documents.find_one({"_id": DOCUMENT_ID})
        assert stored["draft_content"]["blocks"][0]["id"] == "heading"
        editor_with_word_settings = json.loads(editor)
        editor_with_word_settings["wordSettings"] = {
            "commands": {
                "DocLibCopilotExplain": {
                    "mode": "CopilotExplain",
                    "category": "ai",
                    "appliedAt": 1,
                    "enabled": True,
                }
            }
        }
        status, payload, media = call(
            "POST",
            f"/soan-thao/{DOCUMENT_ID}/tu-dong-luu",
            owner_token,
            {"content": editor_with_word_settings},
        )
        assert status == 200 and payload["status"] == 200, payload
        stored = await content.documents.find_one({"_id": DOCUMENT_ID})
        assert (
            stored["draft_content"]["wordSettings"]["commands"][
                "DocLibCopilotExplain"
            ]["enabled"]
            is True
        )

        status, suggestion, media = call(
            "POST",
            f"/soan-thao/{DOCUMENT_ID}/goi-y",
            owner_token,
            {
                "selected_text": "Original",
                "suggested_text": "Updated",
                "comment": "integration",
            },
        )
        assert status == 200, suggestion
        suggestion_id = suggestion["data"]["_id"]
        status, resolved, media = call(
            "PUT",
            f"/soan-thao/goi-y/{suggestion_id}/giai-quyet",
            owner_token,
            {"action": "accepted"},
        )
        assert status == 200 and resolved["data"]["status"] == "accepted", resolved

        status, comment, media = call(
            "POST",
            f"/soan-thao/{DOCUMENT_ID}/binh-luan",
            owner_token,
            {"block_id": "body", "text": "Integration comment"},
        )
        assert status == 200, comment
        comment_id = comment["data"]["_id"]
        status, comments, media = call(
            "GET",
            f"/soan-thao/{DOCUMENT_ID}/binh-luan",
            owner_token,
        )
        assert status == 200 and any(item["_id"] == comment_id for item in comments["data"]), comments
        status, resolved_comment, media = call(
            "PUT",
            f"/soan-thao/binh-luan/{comment_id}/giai-quyet",
            owner_token,
        )
        assert status == 200 and resolved_comment["data"]["status"] == "resolved", resolved_comment

        status, pomodoro, media = call(
            "POST",
            "/soan-thao/dong-ho-pomodoro",
            owner_token,
            {"document_id": DOCUMENT_ID, "duration": 25, "words_written": 120},
        )
        assert status == 200 and pomodoro["data"]["status"] == "recorded", pomodoro
        status, diff, media = call(
            "POST",
            f"/soan-thao/{DOCUMENT_ID}/so-sanh-phien-ban",
            owner_token,
            {"version_id_a": version_a, "version_id_b": version_b},
        )
        assert status == 200 and diff["data"]["version_a"] != diff["data"]["version_b"], diff
        status, replaced, media = call(
            "POST",
            f"/soan-thao/{DOCUMENT_ID}/tim-va-thay-the",
            owner_token,
            {"search": "Original", "replace": "Updated", "match_case": True},
        )
        assert status == 200, replaced
        stored = await content.documents.find_one({"_id": DOCUMENT_ID})
        assert stored["title"] == "Updated integration title"
        assert stored["content"]["blocks"][1]["data"]["text"] == "Updated integration content"
        status, review, media = call(
            "POST",
            f"/soan-thao/{DOCUMENT_ID}/gui-danh-gia",
            owner_token,
        )
        assert status == 200 and review["data"]["status"] == "pending_review", review
        print("compilation integration passed")
    finally:
        await compilation.editor_suggestions.delete_many({"document_id": DOCUMENT_ID})
        await compilation.editor_comments.delete_many({"document_id": DOCUMENT_ID})
        await compilation.pomodoro_sessions.delete_many({"document_id": DOCUMENT_ID})
        await content.document_versions.delete_many({"document_id": DOCUMENT_ID})
        await content.documents.delete_many({"_id": DOCUMENT_ID})
        await cache.delete(
            f"user_sessions:{OWNER_ID}",
            f"user_sessions:{OUTSIDER_ID}",
            f"editor_snapshot:{DOCUMENT_ID}:{OWNER_ID}",
        )
        await cache.aclose()
        mongo.close()


asyncio.run(main())
