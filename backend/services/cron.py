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

        except Exception as e:
            logger.error(f"Cron Service Error: {str(e)}")
            
        await asyncio.sleep(60)

def start_cron_service():
    asyncio.create_task(run_cron_jobs())
