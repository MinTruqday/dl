import asyncio
from loguru import logger
from services.subscription import SubscriptionService
from services.user import UserService

async def scheduled_publish_worker():
    from core.database import db_client
    from datetime import datetime, timezone
    db = db_client.mongodb.get_default_database()
    now = datetime.now(timezone.utc)
    query = {
        "scheduled_publish_at": {"$lte": now},
        "status": {"$in": ["draft", "compiling"]},
        "is_deleted": {"$ne": True}
    }
    pending = await db["documents"].find(query).to_list(length=50)
    published_count = 0
    for doc in pending:
        try:
            await db["documents"].update_one(
                {"_id": doc["_id"]},
                {"$set": {
                    "status": "published",
                    "published_at": now,
                    "updated_at": now,
                }, "$unset": {"scheduled_publish_at": ""}}
            )
            published_count += 1
            logger.info(f"Cron Service: Auto-published document {doc['_id']}")
        except Exception as e:
            logger.error(f"Cron Service: Failed to auto-publish {doc['_id']}: {e}")
    return published_count

async def integrity_monitor_worker():
    from core.database import db_client
    from services.storage import StorageService
    import httpx
    db = db_client.mongodb.get_default_database()
    logger.info("Cron Service: Running Integrity Monitoring Agent")
    items = await db["storage_items"].find({"is_folder": False, "ai_processed": True, "mime_type": {"$regex": "text/|application/pdf|application/x-tex"}}).to_list(length=100)
    checked_count = 0
    for item in items:
        broken_links = []
        if item.get("description") and "http" in item["description"]:
            try:
                from core.config import settings
                rag_url = getattr(settings, "AGENTIC_AI_URL", None)
                if rag_url:
                    resp = await httpx.AsyncClient().post(
                        f"{rag_url}/inference/kiem-tra-toan-ven",
                        json={"document_id": str(item["_id"]), "text": item.get("description", "")}
                    )
                    if resp.status_code == 200:
                        broken_links = resp.json().get("broken_links", [])
            except Exception as e:
                logger.error(f"Integrity Monitor check failed: {e}")

        if broken_links:
            await db["storage_items"].update_one(
                {"_id": item["_id"]},
                {"$set": {"broken_links": broken_links}}
            )
            logger.info(f"Integrity Monitor: Found broken links in {item.get('name')}")
        else:
            await db["storage_items"].update_one(
                {"_id": item["_id"]},
                {"$unset": {"broken_links": ""}}
            )
        checked_count += 1
    return checked_count

async def run_cron_jobs():
    logger.info("Cron Service: Starting background automation tasks")
    while True:
        try:
            expired_count = await SubscriptionService.check_and_expire_subscriptions()
            if expired_count > 0:
                logger.info(f"Cron Service: Expired {expired_count} subscriptions")

            unlocked_count = await UserService.unlock_accounts_task()
            if unlocked_count > 0:
                logger.info(f"Cron Service: Unlocked {unlocked_count} accounts")

            publish_count = await scheduled_publish_worker()
            if publish_count > 0:
                logger.info(f"Cron Service: Published {publish_count} scheduled documents")

            integrity_count = await integrity_monitor_worker()
            if integrity_count > 0:
                logger.info(f"Cron Service: Integrity Monitor checked {integrity_count} documents")

        except Exception as e:
            logger.error(f"Cron Service Error: {str(e)}")
            
        await asyncio.sleep(60)

def start_cron_service():
    asyncio.create_task(run_cron_jobs())
