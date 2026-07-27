from loguru import logger

from src.core.infrastructure.database import database

class WalletRepository:
    @staticmethod
    async def log_db_operation(operation: str, collection: str):
        logger.debug("Storage request completed")
