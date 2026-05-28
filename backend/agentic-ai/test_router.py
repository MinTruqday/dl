import asyncio
from src.agents.router import router_agent

async def main():
    res = await router_agent.execute("Nam Cao là ai")
    print("Router returned:", res)

asyncio.run(main())
