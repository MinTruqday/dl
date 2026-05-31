import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
from core.security import get_password_hash
from datetime import datetime, timezone
from uuid6 import uuid7

async def seed_admin():
    mongo_uri = settings.MONGODB_URI
    client = AsyncIOMotorClient(mongo_uri)
    db = client[settings.MONGODB_DB_NAME]
    users_col = db["users"]
    
    admin_email = "admin@doclib.com"
    existing = await users_col.find_one({"email": admin_email})
    if existing:
        print("Admin already exists.")
        return
        
    admin_user = {
        "_id": str(uuid7()),
        "email": admin_email,
        "full_name": "System Administrator",
        "slug": "admin",
        "role": "admin",
        "password_hash": get_password_hash("admin"),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "is_active": True,
        "is_verified": True
    }
    
    await users_col.insert_one(admin_user)
    print(f"Admin user {admin_email} created successfully with password 'admin'.")
    
if __name__ == "__main__":
    asyncio.run(seed_admin())
