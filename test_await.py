import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    cursor = client.test.test.find()
    
    from motor.motor_asyncio import AsyncIOMotorCursor
    def _cursor_await(self):
        return self.to_list(length=None).__await__()
    AsyncIOMotorCursor.__await__ = _cursor_await
    
    print(await cursor)

asyncio.run(main())
