import asyncio
import sys
import os

from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
from datetime import datetime, timezone

async def create_admin():
    client = AsyncIOMotorClient("mongodb://mongodb:27017")
    
    email = "admin@doclib.com"
    password = "123456"
    
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    user_id = "01942a03-75bf-73c8-a968-07b4617a26f6"
    now = datetime.now(timezone.utc)

    auth_db = client.doclib_authentication
    auth_coll = auth_db.auth_credentials
    
    existing_auth = await auth_coll.find_one({"email": email})
    if existing_auth:
        await auth_coll.update_one({"email": email}, {"$set": {"password_hash": hashed_password}})
        print("Updated existing user in auth")
        user_id = existing_auth["_id"]
    else:
        auth_doc = {
            "_id": user_id,
            "email": email,
            "password_hash": hashed_password,
            "created_at": now,
            "updated_at": now,
            "is_active": True,
            "is_kyc_verified": False,
            "passkeys": []
        }
        await auth_coll.insert_one(auth_doc)
        print("Created user in auth")
        
    hum_db = client.doclib_humanity
    hum_coll = hum_db.users
    
    existing_hum = await hum_coll.find_one({"email": email})
    if existing_hum:
        await hum_coll.update_one({"email": email}, {"$set": {"role": "admin", "is_active": True, "ai_tier": "PREMIUM"}})
        print("Updated user role in humanity")
    else:
        hum_doc = {
            "_id": user_id,
            "email": email,
            "full_name": "Admin System",
            "slug": "admin-system",
            "role": "admin",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
            "ai_tier": "PREMIUM"
        }
        await hum_coll.insert_one(hum_doc)
        print("Created user in humanity")

if __name__ == "__main__":
    asyncio.run(create_admin())
