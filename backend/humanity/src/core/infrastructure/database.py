from datetime import datetime, timezone

from loguru import logger

from src.core.infrastructure.configuration import settings


class DatabaseInfrastructure:
    def __init__(self):
        self.mongodb = None


database = DatabaseInfrastructure()


async def init_db():
    from motor.motor_asyncio import AsyncIOMotorClient

    database.mongodb = AsyncIOMotorClient(
        settings.MONGODB_URI,
        serverSelectionTimeoutMS=5000,
    )
    await database.mongodb.admin.command("ping")
    await reconcile_duplicate_users()
    await setup_indexes()


async def reconcile_duplicate_users():
    db = database.mongodb[settings.HUMANITY_DB_NAME]
    auth_db = database.mongodb[settings.AUTHENTICATION_DB_NAME]
    groups = await db["users"].aggregate(
        [
            {"$match": {"email": {"$type": "string"}}},
            {"$group": {"_id": {"$toLower": "$email"}, "users": {"$push": "$$ROOT"}, "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
        ]
    ).to_list(length=None)
    for group in groups:
        users = group["users"]
        credential = await auth_db["auth_credentials"].find_one({"email": group["_id"]})
        credential_id = str(credential["_id"]) if credential else None
        keeper = next((user for user in users if str(user["_id"]) == credential_id), None)
        keeper = keeper or sorted(users, key=lambda item: str(item["_id"]))[0]
        merged = dict(keeper)
        for user in users:
            for key, value in user.items():
                if key not in merged or merged[key] in (None, "", [], {}):
                    merged[key] = value
        merged["email"] = group["_id"]
        await db["users"].replace_one({"_id": keeper["_id"]}, merged)
        for user in users:
            if user["_id"] == keeper["_id"]:
                continue
            await db["user_duplicate_archive"].update_one(
                {"original_id": str(user["_id"])},
                {
                    "$setOnInsert": {
                        "original_id": str(user["_id"]),
                        "kept_user_id": str(keeper["_id"]),
                        "reason": "duplicate_email",
                        "archived_at": datetime.now(timezone.utc),
                        "document": user,
                    }
                },
                upsert=True,
            )
            await db["users"].delete_one({"_id": user["_id"]})
        logger.warning(f"Archived {len(users) - 1} duplicate user profiles for {group['_id']}")


async def setup_indexes():
    db = database.mongodb[settings.HUMANITY_DB_NAME]
    await db["users"].create_index(
        "email",
        name="email_unique",
        unique=True,
        partialFilterExpression={"email": {"$type": "string"}},
    )
    await db["users"].create_index(
        "slug",
        name="slug_unique",
        unique=True,
        partialFilterExpression={"slug": {"$type": "string"}},
    )
    await db["users"].create_index([("full_name", 1), ("slug", 1)])
    await db["users"].create_index([("role", 1), ("is_active", 1)])
    await db["users"].create_index("created_at")
    await db["user_duplicate_archive"].create_index("original_id", unique=True)
    logger.info("Humanity database indexes initialized")


async def close_db():
    if database.mongodb:
        database.mongodb.close()
        database.mongodb = None
