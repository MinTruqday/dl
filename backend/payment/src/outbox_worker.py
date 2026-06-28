from src.core.infrastructure.database import database
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
                event = await mongo.get_db()["outbox_events"].find_one_and_update(
                    {"status": "pending"},
                    {"$set": {"status": "processing"}}
                )
                if event:
                    await mq.publish(event["queue_name"], event["payload"])
                    await mongo.update_one("outbox_events", 
                        {"_id": event["_id"]},
                        {"$set": {"status": "done"}}
                    )
                    continue # process next immediately
        except Exception as e:
            logger.exception("Lỗi quá trình đồng bộ hóa Outbox Worker")
            
        await asyncio.sleep(5)
