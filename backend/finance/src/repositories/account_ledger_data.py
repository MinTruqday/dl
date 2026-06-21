from loguru import logger

from core.infrastructure.database_client import db_client


class WalletRepository:
    @staticmethod
    async def log_db_operation(operation: str, collection: str):
        logger.debug("Ghi nhận yêu cầu lưu trữ thành công")
