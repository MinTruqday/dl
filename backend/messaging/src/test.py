import asyncio
from src.services.thread import ThreadService
from src.core.infrastructure.database import init_db

class DummyUser:
    def __init__(self):
        self.id = "11111111-1111-1111-1111-111111111111"

async def test():
    await init_db()
    res = await ThreadService.get_conversations(DummyUser())
    print("Conversations count:", len(res))
    if len(res) > 0:
        print("First convo:", res[0])

asyncio.run(test())
