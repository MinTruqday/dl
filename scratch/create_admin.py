import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
from datetime import datetime, timezone

async def create_admin():
    client = AsyncIOMotorClient("mongodb://mongodb:27017")
    
    # 1. Check if we can connect
    try:
        await client.admin.command('ping')
        print("Connected to MongoDB")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    # User data
    email = "admin@doclib.com"
    password = "123456"
    
    # Hash password (assuming bcrypt, which is standard in python fastapi apps)
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    user_doc = {
        "email": email,
        "full_name": "Admin System",
        "hashed_password": hashed_password,
        "role": "admin",
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    db = client.doclib_authentication
    users_collection = db.users # Replace with actual collection if different
    
    # Let's see what collection authentication uses. Wait, I should just check the code first!
    pass

if __name__ == "__main__":
    asyncio.run(create_admin())
