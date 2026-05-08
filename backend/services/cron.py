import asyncio
from loguru import logger
from services.subscription import SubscriptionService
from services.user import UserService

async def run_cron_jobs():
    logger.info("Cron Service: Starting background automation tasks")
    while True:
        try:
            expired_count = await SubscriptionService.check_and_expire_subscriptions()
            if expired_count > 0:
                logger.info(f"Cron Service: Expired {expired_count} subscriptions")

            unlocked_count = await UserService.unlock_accounts_task()
            if unlocked_count > 0:
                logger.info(f"Cron Service: Unlocked {unlocked_count} accounts")

        except Exception as e:
            logger.error(f"Cron Service Error: {str(e)}")
            
        await asyncio.sleep(3600)

def start_cron_service():
    asyncio.create_task(run_cron_jobs())
