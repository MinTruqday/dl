from core.database import db_client
from loguru import logger

class WalletRepository:
    
    @staticmethod
    async def log_db_operation(operation: str, collection: str):
        logger.debug(f"Database operational request for {collection} successfully logged by financial storage mechanism")