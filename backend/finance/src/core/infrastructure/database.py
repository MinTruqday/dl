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
    await initialize_withdrawable_balances()
    await setup_indexes()


async def initialize_withdrawable_balances():
    db = database.mongodb[settings.FINANCE_DB_NAME]
    wallets = await db["wallets"].find(
        {"withdrawable_balance": {"$exists": False}}
    ).to_list(length=None)
    for wallet in wallets:
        rows = await db["transactions"].aggregate(
            [
                {
                    "$match": {
                        "user_id": str(wallet["_id"]),
                        "$or": [
                            {"type": {"$in": ["receive", "tip"]}},
                            {"type": "refund", "amount": {"$lt": 0}},
                            {"type": "withdraw", "amount": {"$lt": 0}},
                        ],
                    }
                },
                {"$group": {"_id": None, "amount": {"$sum": "$amount"}}},
            ]
        ).to_list(length=None)
        amount = max(0, int(rows[0]["amount"])) if rows else 0
        await db["wallets"].update_one(
            {"_id": wallet["_id"], "withdrawable_balance": {"$exists": False}},
            {"$set": {"withdrawable_balance": amount}},
        )


async def setup_indexes():
    db = database.mongodb[settings.FINANCE_DB_NAME]
    await db["purchases"].update_many(
        {"status": {"$exists": False}},
        {"$set": {"status": "ACTIVE"}},
    )
    await db["orders"].create_index("order_code", unique=True)
    await db["orders"].create_index([("user_id", 1), ("created_at", -1)])
    await db["transactions"].create_index([("user_id", 1), ("created_at", -1)])
    await db["transactions"].create_index("reference_id")
    await db["purchases"].create_index(
        [("user_id", 1), ("document_id", 1), ("item_type", 1)],
        name="active_purchase_unique",
        unique=True,
        partialFilterExpression={"status": "ACTIVE"},
    )
    await db["purchases"].create_index([("document_id", 1), ("purchased_at", -1)])
    await db["withdrawal_requests"].create_index([("status", 1), ("created_at", -1)])
    await db["withdrawal_requests"].create_index([("user_id", 1), ("created_at", -1)])
    await db["outbox_events"].create_index([("status", 1), ("next_attempt_at", 1)])
    logger.info("Finance database indexes initialized successfully")


async def close_db():
    if database.mongodb:
        database.mongodb.close()
        database.mongodb = None
