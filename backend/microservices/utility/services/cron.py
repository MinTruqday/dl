import asyncio
from loguru import logger
from services.monetization import MonetizationService
from services.user import UserService
async def run_cron_jobs():
logger.info("Log message sanitized"))
    while True:
        try:
            expired_count = await MonetizationService.check_and_expire_subscriptions()
            if expired_count > 0:
logger.info("Log message sanitized"))
            unlocked_count = await UserService.unlock_accounts_task()
            if unlocked_count > 0:
logger.info("Log message sanitized"))
        except Exception as e:
logger.info("Log message sanitized"))
        await asyncio.sleep(3600)
def start_cron_service():
    asyncio.create_task(run_cron_jobs())
