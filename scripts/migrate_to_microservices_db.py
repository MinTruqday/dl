import os
import sys
from pymongo import MongoClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://doclib_mongodb:27017/")
client = MongoClient(MONGO_URI)

SOURCE_DB_NAME = "doclib"

SERVICE_MAPPINGS = {
    "doclib_authentication": [
        "auth_credentials", "password_reset_tokens", "sessions"
    ],
    "doclib_management": [
        "users", "audit_logs", "profiles", "quotas"
    ],
    "doclib_finance": [
        "wallets", "transactions", "subscriptions", "payments"
    ],
    "doclib_content": [
        "documents", "folders", "tags", "comments", "document_versions"
    ],
    "doclib_messaging": [
        "conversations", "messages"
    ],
    "doclib_editor": [
        "document_drafts", "templates"
    ],
    "doclib_collector": [
        "crawled_data", "sources"
    ],
    "doclib_notification": [
        "notifications", "device_tokens"
    ],
    "doclib_agentic_ai": [
        "ai_logs", "finetune_jobs", "chat_histories"
    ]
}

def migrate():
    if SOURCE_DB_NAME not in client.list_database_names():
        logger.error(f"Không tìm thấy Database gốc: {SOURCE_DB_NAME}")
        return

    source_db = client[SOURCE_DB_NAME]
    existing_collections = source_db.list_collection_names()
    
    logger.info(f"Bắt đầu quá trình Migrate từ {SOURCE_DB_NAME} sang mô hình Microservices...")
    
    for target_db_name, collections in SERVICE_MAPPINGS.items():
        logger.info(f"--- Migrate sang: {target_db_name} ---")
        target_db = client[target_db_name]
        
        for coll_name in collections:
            if coll_name in existing_collections:
                documents = list(source_db[coll_name].find({}))
                if documents:
                    # Clear target collection first to avoid duplicates if run multiple times
                    target_db[coll_name].delete_many({})
                    target_db[coll_name].insert_many(documents)
                    logger.info(f"✅ Copy thành công {len(documents)} bản ghi từ bảng '{coll_name}'")
                else:
                    logger.info(f"⚠️ Bảng '{coll_name}' trống, bỏ qua.")
            else:
                logger.warning(f"❌ Không tìm thấy bảng '{coll_name}' trong db gốc.")
                
    logger.info("Hoàn tất Migrate.")

if __name__ == "__main__":
    migrate()
