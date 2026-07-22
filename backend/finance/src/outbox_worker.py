import asyncio
from datetime import datetime, timedelta, timezone

import httpx
from loguru import logger
from pymongo import ReturnDocument

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.mongo import mongo


async def process_outbox():
    logger.info("Finance outbox worker started successfully")
    while True:
        event = None
        try:
            now = datetime.now(timezone.utc)
            event = await mongo.get_db()["outbox_events"].find_one_and_update(
                {
                    "$or": [
                        {"status": "pending", "next_attempt_at": {"$lte": now}},
                        {"status": "pending", "next_attempt_at": {"$exists": False}},
                        {"status": "processing", "locked_at": {"$lt": now - timedelta(minutes=2)}},
                    ]
                },
                {
                    "$set": {"status": "processing", "locked_at": now},
                    "$inc": {"attempts": 1},
                },
                sort=[("created_at", 1)],
                return_document=ReturnDocument.AFTER,
            )
            if not event:
                await asyncio.sleep(2)
                continue
            if event.get("event_type") != "notification":
                raise ValueError("Unsupported outbox event type")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{settings.NOTIFICATION_URL}/thong-bao/gui-di",
                    json=event["payload"],
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                )
            response.raise_for_status()
            await mongo.update_one(
                "outbox_events",
                {"_id": event["_id"], "status": "processing"},
                {"$set": {"status": "done", "completed_at": datetime.now(timezone.utc)}},
            )
        except asyncio.CancelledError:
            raise
        except Exception as error:
            logger.exception("Finance outbox delivery failed")
            if event:
                attempts = int(event.get("attempts", 1))
                if attempts >= 10:
                    await mongo.update_one(
                        "outbox_events",
                        {"_id": event["_id"], "status": "processing"},
                        {"$set": {"status": "failed", "last_error": type(error).__name__}},
                    )
                    continue
                delay = min(300, 2 ** min(attempts, 8))
                await mongo.update_one(
                    "outbox_events",
                    {"_id": event["_id"], "status": "processing"},
                    {
                        "$set": {
                            "status": "pending",
                            "next_attempt_at": datetime.now(timezone.utc) + timedelta(seconds=delay),
                            "last_error": type(error).__name__,
                        }
                    },
                )
            await asyncio.sleep(2)
