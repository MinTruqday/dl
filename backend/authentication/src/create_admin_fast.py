import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from argon2 import PasswordHasher
from uuid6 import uuid7
import datetime
from core.config import settings

async def create_admin():
    mongo_client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = mongo_client["doclib_auth"]
    db_prov = mongo_client["doclib_provision"]
    ph = PasswordHasher()
    
    user_id = str(uuid7())
    email = "admin@doclib.com"
    password = "123456"
    
    existing = await db_prov.users.find_one({"email": email})
    if existing:
        print("Admin already exists")
        return

    await db_prov.users.insert_one({
        "_id": user_id,
        "email": email,
        "full_name": "System Admin",
        "slug": "admin",
        "role": "admin",
        "is_active": True,
        "created_at": datetime.datetime.utcnow()
    })
    
    await db.credentials.insert_one({
        "_id": user_id,
        "email": email,
        "password_hash": ph.hash(password),
        "passkeys": []
    })
    print("Admin created successfully")
    mongo_client.close()

asyncio.run(create_admin())
