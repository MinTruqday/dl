import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import pymongo

async def migrate():
    uri = os.environ.get("MONGODB_URI", "mongodb://mongodb:27017")
    client = AsyncIOMotorClient(uri)
    db = client["doclib_cloud"]
    items = db.storage_items.find({"id": {"$exists": True}})
    count = 0
    async for item in items:
        old_id = item["_id"]
        str_id = item["id"]
        # check if old_id is ObjectId
        from bson import ObjectId
        if isinstance(old_id, ObjectId):
            # create new document with _id = str_id
            item["_id"] = str_id
            del item["id"]
            try:
                await db.storage_items.insert_one(item)
                await db.storage_items.delete_one({"_id": old_id})
                count += 1
            except pymongo.errors.DuplicateKeyError:
                await db.storage_items.delete_one({"_id": old_id})
    print(f"Migrated {count} items")

asyncio.run(migrate())
