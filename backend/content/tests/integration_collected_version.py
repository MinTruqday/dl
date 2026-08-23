import asyncio
import os
import uuid

import httpx


async def request(payload):
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            "http://127.0.0.1:8000/tai-lieu/noi-bo/trao-doi",
            json=payload,
            headers={"X-Internal-Token": os.environ["SECRET_KEY"]},
        )
        response.raise_for_status()
        return response.json()["data"]


async def main():
    identity = f"https://nxbgd.test/{uuid.uuid4()}"
    base = {
        "title": "Toán 12",
        "slug": f"toan-12-{uuid.uuid4().hex[:10]}",
        "source_url": identity,
        "creator_id": "platform-system",
        "source_type": "curriculum",
        "authority": "official",
    }
    first = await request({"action": "upsert_collected", "document": {**base, "content_hash": "a" * 64}})
    duplicate = await request({"action": "upsert_collected", "document": {**base, "content_hash": "a" * 64}})
    second = await request(
        {
            "action": "upsert_collected",
            "document": {**base, "content_hash": "b" * 64},
        }
    )
    if first["document_id"] != duplicate["document_id"]:
        raise AssertionError("Exact content retry created a duplicate version")
    if first["document_id"] == second["document_id"]:
        raise AssertionError("Changed content did not create a new version")
    first_row = await request({"action": "get_document", "document_id": first["document_id"]})
    second_row = await request({"action": "get_document", "document_id": second["document_id"]})
    if first_row.get("source_is_current") is not False:
        raise AssertionError("Previous source version remained current")
    if first_row.get("superseded_by_document_id") != second["document_id"]:
        raise AssertionError("Previous source version does not link to the new version")
    if second_row.get("previous_version_id") != first["document_id"]:
        raise AssertionError("New source version does not link to the previous version")
    if second_row.get("source_revision") != 2:
        raise AssertionError("Source revision did not advance")


if __name__ == "__main__":
    asyncio.run(main())
