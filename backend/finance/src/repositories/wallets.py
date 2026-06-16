from core.database import db_client
from loguru import logger

class WalletRepository:
    
    @staticmethod
    async def log_db_operation(operation: str, collection: str):
        logger.debug(f"Yêu cầu cơ sở dữ liệu cho {collection} đã được ghi nhận")