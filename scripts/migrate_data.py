from pymongo import MongoClient
import os
from datetime import datetime, timezone

def migrate():
    # Connect to MongoDB
    mongo_url = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("MONGODB_DB_NAME", "doclib")
    client = MongoClient(mongo_url)
    db = client[db_name]
    
    users = db["users"].find({})
    
    migrated_wallets = 0
    migrated_content_profiles = 0
    migrated_auth = 0
    
    for user in users:
        user_id = str(user["_id"])
        email = user.get("email")
        
        # 1. Wallets
        if "wallet_balance" in user:
            db["wallets"].update_one(
                {"_id": user_id},
                {"$set": {
                    "balance": user.get("wallet_balance", 0),
                    "created_at": user.get("created_at", datetime.now(timezone.utc)),
                    "updated_at": datetime.now(timezone.utc)
                }},
                upsert=True
            )
            migrated_wallets += 1
            
        # 2. Content Profiles
        content_profile_update = {}
        if "bookmarks" in user:
            content_profile_update["bookmarks"] = user["bookmarks"]
        if "read_history" in user:
            content_profile_update["read_history"] = user["read_history"]
        if "stats" in user:
            content_profile_update["stats"] = user["stats"]
        if "pinned_documents" in user:
            content_profile_update["pinned_documents"] = user["pinned_documents"]
            
        if content_profile_update:
            db["user_content_profiles"].update_one(
                {"_id": user_id},
                {"$set": content_profile_update},
                upsert=True
            )
            migrated_content_profiles += 1
            
        # 3. Contact Profiles
        if "blocked_users" in user:
            db["user_contact_profiles"].update_one(
                {"_id": user_id},
                {"$set": {"blocked_users": user["blocked_users"]}},
                upsert=True
            )
            
        # 4. Auth Credentials
        if "password_hash" in user or "passkeys" in user:
            db["auth_credentials"].update_one(
                {"_id": user_id},
                {"$set": {
                    "email": email,
                    "password_hash": user.get("password_hash"),
                    "passkeys": user.get("passkeys", [])
                }},
                upsert=True
            )
            migrated_auth += 1

    print(f"Migration completed successfully.")
    print(f"- Migrated wallets: {migrated_wallets}")
    print(f"- Migrated content profiles: {migrated_content_profiles}")
    print(f"- Migrated auth credentials: {migrated_auth}")

if __name__ == "__main__":
    migrate()
