from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys
from src.core.infrastructure.configuration import settings

from src.api.mongo import router as mongo_router

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO",
)

app = FastAPI(title="DocLib Database", version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def setup_indexes():
    try:
        c = get_client()
        db = c["doclib"] # Default DB

        await db["documents"].create_index(
            [("title", "text"), ("description", "text"), ("author", "text")],
            background=True,
        )
        await db["documents"].create_index([("creator_id", 1)], background=True)
        await db["documents"].create_index(
            [("status", 1), ("is_deleted", 1), ("created_at", -1)], background=True
        )
        await db["documents"].create_index(
            [("status", 1), ("is_deleted", 1), ("views", -1)], background=True
        )
        await db["documents"].create_index(
            [("status", 1), ("is_deleted", 1), ("categories", 1), ("created_at", -1)],
            background=True,
        )
        await db["documents"].create_index(
            [("status", 1), ("is_deleted", 1), ("tags", 1), ("created_at", -1)],
            background=True,
        )
        await db["documents"].create_index([("slug", 1)], unique=True, background=True)

        await db["status_updates"].create_index([("created_at", -1)], background=True)
        await db["status_updates"].create_index([("user_id", 1)], background=True)
        await db["status_updates"].create_index(
            [("is_shadowbanned", 1)], background=True
        )

        await db["comments"].create_index(
            [("item_id", 1), ("item_type", 1)], background=True
        )
        await db["comments"].create_index([("path", 1)], background=True)

        await db["users"].create_index([("followers_count", -1)], background=True)
        await db["users"].create_index([("email", 1)], unique=True, background=True)

        await db["transactions"].create_index([("user_id", 1)], background=True)
        await db["reports"].create_index([("status", 1)], background=True)
        await db["reports"].create_index([("created_at", -1)], background=True)

        await db["editor_comments"].create_index(
            [("document_id", 1), ("block_id", 1)], background=True
        )
        await db["document_versions"].create_index(
            [("document_id", 1), ("created_at", -1)], background=True
        )

        await db["conversations"].create_index(
            [("participants", 1), ("updated_at", -1)], background=True
        )

        await db["messages"].create_index(
            [("sender_id", 1), ("receiver_id", 1), ("created_at", -1)], background=True
        )
        await db["messages"].create_index(
            [("sender_id", 1), ("receiver_id", 1), ("is_read", 1)], background=True
        )
        await db["messages"].create_index(
            [("sender_id", 1), ("receiver_id", 1), ("is_pinned", 1)], background=True
        )
        await db["messages"].create_index([("content", "text")], background=True)
        await db["messages"].create_index(
            [("self_destruct_at", 1)], expireAfterSeconds=0, background=True
        )

        await db["storage_items"].create_index(
            [("owner_id", 1), ("parent_id", 1), ("is_trashed", 1)], background=True
        )
        await db["storage_items"].create_index(
            [("shared_with.user_id", 1), ("parent_id", 1), ("is_trashed", 1)],
            background=True,
        )
        await db["storage_items"].create_index([("url", 1)], background=True)
        await db["storage_items"].create_index([("target_id", 1)], background=True)
        await db["storage_items"].create_index(
            [("owner_id", 1), ("is_trashed", 1), ("updated_at", -1)], background=True
        )

        logger.info("Hoàn tất tạo chỉ mục cơ sở dữ liệu")
    except Exception as e:
        logger.error(f"Lỗi tạo chỉ mục cơ sở dữ liệu: {e}")

app.include_router(mongo_router)

@app.on_event("startup")
async def startup_event():
    await setup_indexes()
    logger.info("Database Service đã sẵn sàng")

@app.on_event("shutdown")
async def shutdown_event():
    pass

@app.get("/health")
async def health_check():
    return {
        "status": "Database service is healthy"
    }
