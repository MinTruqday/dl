import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def promote():
    client = AsyncIOMotorClient('mongodb://mongodb:27017/')
    db = client['doclib']
    res = await db.users.update_one({'email': 'admin@doclib.vn'}, {'$set': {'role': 'admin'}})
    print(f"Updated {res.modified_count} users to admin role.")

if __name__ == "__main__":
    asyncio.run(promote())
