import asyncio
import sys
import os

sys.path.append("/app")

from src.core.infrastructure.database import database, init_db
from src.core.security.access import get_password_hash
from src.core.infrastructure.configuration import settings
from datetime import datetime, timezone

async def create_admin():
    await init_db()
    db = database.mongodb[settings.AUTHENTICATION_DB_NAME]
    
    existing = await db.users.find_one({"email": "admin@doclib.com"})
    hashed_password = get_password_hash("123456")
    
    if existing:
        print("Admin user already exists, updating password.")
        await db.users.update_one({"email": "admin@doclib.com"}, {"$set": {"password": hashed_password}})
        print("Password updated.")
        return

    user = {
        "email": "admin@doclib.com",
        "password": hashed_password,
        "is_verified": True,
        "first_name": "Admin",
        "last_name": "DocLib",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "auth_providers": ["email"]
    }
    result = await db.users.insert_one(user)
    print(f"Created admin user with id: {result.inserted_id}")

if __name__ == "__main__":
    asyncio.run(create_admin())
