from core.database import db_client
from datetime import datetime
from loguru import logger

class AdminService:
    @staticmethod
    async def get_stats() -> dict:
        db = db_client.mongodb.get_default_database()
        total_users = await db["users"].count_documents({})
        total_documents = await db["documents"].count_documents({})
        total_authors = await db["users"].count_documents({"role": "AUTHOR"})
        return {
            "total_users": total_users,
            "total_documents": total_documents,
            "total_authors": total_authors,
            "timestamp": datetime.utcnow()
        }

    @staticmethod
    async def get_big_data_trends() -> dict:
        return {
            "trending_topics": ["AI", "Blockchain", "Mental Health"],
            "growth_rate": "12.5%",
            "active_users_daily": 450
        }

    @staticmethod
    async def get_decision_support() -> dict:
        return {
            "recommendation": "Tăng cường nội dung về kỹ năng sống",
            "confidence": 0.85
        }

    @staticmethod
    async def get_ai_gateway_stats() -> dict:
        return {
            "total_requests": 1500,
            "success_rate": "98.2%",
            "latency_ms": 250
        }
