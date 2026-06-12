from bson import ObjectId
from datetime import datetime, timezone, timedelta
from core.database import db_client
from src.schemas.user import UserInDB
from typing import Optional, Dict, Any
import uuid
from uuid6 import uuid7
from loguru import logger

class TelemetryService:

    @staticmethod
    async def track_event(event_name: str, properties: Dict[str, Any], current_user: Optional[UserInDB]=None, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        telemetry_event = {'_id': str(uuid7()), 'event_name': event_name, 'properties': properties, 'user_id': str(current_user.id) if current_user else 'anonymous', 'timestamp': datetime.now(timezone.utc)}
        await db['telemetry'].insert_one(telemetry_event)
        logger.debug(f"Đã ghi nhận sự kiện hệ thống: {event_name} bởi người dùng {telemetry_event['user_id']}")
        return {'status': 'success'}

    @staticmethod
    async def get_activity_stats(days: int=7, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        since = datetime.now(timezone.utc) - timedelta(days=days)
        pipeline = [{'$match': {'timestamp': {'$gte': since}}}, {'$group': {'_id': '$event_name', 'count': {'$sum': 1}}}, {'$sort': {'count': -1}}]
        cursor = db['telemetry'].aggregate(pipeline)
        return await cursor.to_list(length=100)

    @staticmethod
    async def log_performance_metric(metric_name: str, value: float, current_user: Optional[UserInDB]=None, db=None):
        return await TelemetryService.track_event('performance_metric', {'metric': metric_name, 'value': value}, current_user)

    @staticmethod
    async def get_system_stats(db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        total_users = await db['users'].count_documents({})
        total_documents = await db['documents'].count_documents({})
        total_authors = await db['users'].count_documents({'role': 'AUTHOR'})
        return {'total_users': total_users, 'total_documents': total_documents, 'total_authors': total_authors, 'timestamp': datetime.now(timezone.utc)}

    @staticmethod
    async def get_sys_health(db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        try:
            await db.command('ping')
            mongo_status = 'healthy'
        except Exception:
            mongo_status = 'unhealthy'
        return {'status': 'online', 'mongodb': mongo_status, 'timestamp': datetime.now(timezone.utc)}

    @staticmethod
    async def get_moderator_activity_log(moderator_id: str, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        return await db['moderator_activity'].find({'moderator_id': moderator_id}).sort('timestamp', -1).to_list(length=100)