import asyncio
from datetime import datetime, timezone
import sys
import os

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.security.access import get_password_hash

async def create_admin():
    from src.core.infrastructure.database import init_db
    await init_db()
    db = database.mongodb.get_default_database()
    
    email = "admin@doclib.com"
    password = "123456"
    
    # 1. Check if user already exists
    user_repo = db["users"]
    existing_user = await user_repo.find_one({"email": email})
    
    if existing_user:
        user_id = str(existing_user["_id"])
        print(f"User already exists with ID: {user_id}")
    else:
        # Create user profile in management
        from uuid6 import uuid7
        user_id = str(uuid7())
        user_doc = {
            "_id": user_id,
            "email": email,
            "full_name": "System Admin",
            "slug": "sys_admin",
            "role": "ADMIN",
            "is_active": True,
            "is_premium": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await user_repo.insert_one(user_doc)
        print(f"Created user document with ID: {user_id}")
        
    # 2. Check if auth credential exists
    auth_repo = db["auth_credentials"]
    existing_cred = await auth_repo.find_one({"email": email})
    
    hashed_password = get_password_hash(password)
    if existing_cred:
        await auth_repo.update_one(
            {"email": email},
            {"$set": {"password_hash": hashed_password}}
        )
        print("Updated auth credential password")
    else:
        auth_doc = {
            "_id": user_id,
            "email": email,
            "password_hash": hashed_password,
            "passkeys": [],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await auth_repo.insert_one(auth_doc)
        print("Created auth credential")

    print("Admin user created successfully.")

if __name__ == "__main__":
    asyncio.run(create_admin())
