import asyncio
import httpx
from datetime import datetime

async def create_admin():
    from passlib.context import CryptContext
    pwd_context =CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_pass = pwd_context.hash("123456")
    
    payload = {
        "db": "doclib",
        "collection": "users",
        "document": {
            "email": "admin@doclib.com",
            "hashed_password": hashed_pass,
            "role": "admin",
            "is_active": True,
            "username": "admin",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    }
    
    async with httpx.AsyncClient() as client:
        # Check if already exists
        check = await client.post("http://localhost:8800/mongo/find_one", json={"db": "doclib", "collection": "users", "query": {"email": "admin@doclib.com"}})
        if check.json().get("data"):
            print("Admin already exists")
            return

        res = await client.post("http://localhost:8800/mongo/insert_one", json=payload)
        print("Admin user created:", res.json())

asyncio.run(create_admin())
