import asyncio
from loguru import logger
from src.core.infrastructure.mongo import mongo
from src.core.infrastructure.mq import mq

async def process_outbox():
    logger.info("Khởi động Outbox Worker")
    while True:
        try:
            db = mongo.get_db()
            if db is not None:
                event = await db["outbox_events"].find_one_and_update(
                    {"status": "pending"},
                    {"$set": {"status": "processing"}}
                )
                if event:
                    await mq.publish(event["queue_name"], event["payload"])
                    await db["outbox_events"].update_one(
                        {"_id": event["_id"]},
                        {"$set": {"status": "done"}}
                    )
                    continue # process next immediately
        except Exception as e:
            logger.error(f"Lỗi Outbox Worker: {e}")
            
        await asyncio.sleep(5)
