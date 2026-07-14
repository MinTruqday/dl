import asyncio
from uuid6 import uuid7
from loguru import logger
import sys

from src.workflow.orchestration import supervisor

async def test_run():
    req_data = {
        "session_id": str(uuid7()),
        "query": "Write a secure python function to sort an array",
        "plan": [
            [{"agent": "SwarmAgent", "task": "Write and secure python function to sort an array"}]
        ]
    }
    
    logger.info("Starting test orchestration run inside Docker")
    
    try:
        iterations = 0
        async for chunk in supervisor.execute_plan(req_data):
            print(f"Yielded: {chunk}")
            iterations += 1
            if iterations > 3:
                break
        print("TEST PASSED: Orchestration stream initiated successfully")
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_run())
