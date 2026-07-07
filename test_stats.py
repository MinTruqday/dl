import asyncio
from src.core.infrastructure.database import init_db
from src.services.ingestion import get_collector_stats

async def main():
    await init_db()
    try:
        res = await get_collector_stats()
        print("SUCCESS:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
