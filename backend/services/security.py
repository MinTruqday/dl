from core.database import db_client
from datetime import datetime, timezone
from loguru import logger

class SecurityService:

    @staticmethod
    async def get_security_config(db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        config = await db['system_config'].find_one({'key': 'security_settings'})
        return config.get('value', {}) if config else {'mfa_required': False, 'session_timeout_minutes': 60, 'ip_whitelist_enabled': False}

    @staticmethod
    async def update_security_config(data: dict, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        await db['system_config'].update_one({'key': 'security_settings'}, {'$set': {'value': data, 'updated_at': datetime.now(timezone.utc)}}, upsert=True)
        logger.info(f'Security: System security settings updated.')
        return {'message': 'Đã cập nhật cấu hình bảo mật hệ thống.'}